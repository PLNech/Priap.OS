"""Spatial fight observability — turn-by-turn view with grid semantics.

"Move 4 cells" tells you what happened; it doesn't tell you if it was a *good* move.
This module enriches each action with spatial context:
  - cell coordinates (from → to)
  - distance to enemy (before / after moves)
  - weapon/chip range fit (in-range? out-of-range?)
  - line-of-sight check (obstacle-blocked?)

Parses the fight JSON (cells + actions + map.obstacles), drives a PySim `Grid` for
LOS/distance, cross-references `WEAPON_REGISTRY`/`CHIP_REGISTRY` for ranges.

Usage:
    from leekwars_agent.fight_spatial import SpatialFight
    sf = SpatialFight(fight_data)
    sf.render(console)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from rich.console import Console

from leekwars_agent.models.equipment import CHIP_REGISTRY, WEAPON_REGISTRY
from leekwars_agent.pysim.grid import Grid


@dataclass
class Entity:
    id: int
    name: str
    team: int
    cell: int
    hp: int
    hp_max: int
    level: int
    weapon_template: int | None = None  # current equipped weapon


@dataclass
class SpatialEvent:
    """One enriched action — spatial context attached where meaningful."""
    kind: str                    # 'turn_start', 'set_weapon', 'move', 'weapon', 'chip',
                                 # 'damage', 'heal', 'dead', 'end_turn'
    entity_id: int | None = None
    text: str = ""               # rendered human-readable line
    # Spatial metadata (optional)
    from_cell: int | None = None
    to_cell: int | None = None
    target_cell: int | None = None
    distance: int | None = None
    range_min: int | None = None
    range_max: int | None = None
    in_range: bool | None = None
    needs_los: bool = False
    has_los: bool | None = None
    notes: list[str] = field(default_factory=list)  # diagnostic flags


class SpatialFight:
    """Drives through a fight action stream, maintaining entity positions + HP.

    Emits per-turn blocks with both entity snapshots and enriched actions.
    """

    def __init__(self, fight_data: dict[str, Any], my_team: int = 1):
        self.my_team = my_team
        self.data = fight_data
        m = fight_data.get("map", {})
        raw_obs = m.get("obstacles", {}) or {}
        obstacles = {int(c) for c in raw_obs.keys()}
        self.grid = Grid(
            width=m.get("width", 18),
            height=m.get("height", 18),
            obstacles=obstacles,
        )
        # Entities by id
        self.entities: dict[int, Entity] = {}
        for leek in fight_data.get("leeks", []):
            eid = leek.get("id", 0)
            self.entities[eid] = Entity(
                id=eid,
                name=leek.get("name", f"E{eid}"),
                team=leek.get("team", 0),
                cell=leek.get("cellPos", 0),
                hp=leek.get("life", 0),
                hp_max=leek.get("life", 0),
                level=leek.get("level", 0),
            )
        self.actions = fight_data.get("actions", [])

    # ── helpers ────────────────────────────────────────────────────────

    def _enemy_of(self, eid: int) -> Entity | None:
        me = self.entities.get(eid)
        if me is None:
            return None
        for e in self.entities.values():
            if e.team != me.team:
                return e
        return None

    def _dist(self, c1: int, c2: int) -> int:
        return self.grid.distance(c1, c2)

    def _los(self, c1: int, c2: int) -> bool:
        # Treat other entities as blockers (chips with LOS use cells of alive leeks)
        blockers = {e.cell for e in self.entities.values()
                    if e.cell not in (c1, c2) and e.hp > 0}
        return self.grid.line_of_sight(c1, c2, blocking_entities=blockers)

    # ── main walk ──────────────────────────────────────────────────────

    def walk(self) -> list[tuple[int, list[SpatialEvent]]]:
        """Return [(turn_no, [events, ...]), ...]."""
        turns: list[tuple[int, list[SpatialEvent]]] = []
        # LW convention: fight opens on turn 1 without an explicit NEW_TURN; the
        # first code-6 event carries turn=2.
        current_turn = 1
        current_events: list[SpatialEvent] = [
            self._snapshot_event(e) for e in self.entities.values()
        ]
        current_entity: int | None = None
        # Per-turn TP/MP accounting (re-derived from action costs; END_TURN
        # reports MAX values, not spent — we sum the costs ourselves).
        tp_spent_this_turn = 0
        mp_spent_this_turn = 0

        for action in self.actions:
            if not action:
                continue
            code = action[0]

            if code == 6:  # NEW_TURN [6, turn_number]
                if current_events:
                    turns.append((current_turn, current_events))
                current_turn = action[1] if len(action) > 1 else current_turn + 1
                current_events = []
                # Snapshot both entities at turn start
                for e in self.entities.values():
                    current_events.append(self._snapshot_event(e))

            elif code == 7:  # LEEK_TURN [7, entity_id]
                current_entity = action[1]
                tp_spent_this_turn = 0
                mp_spent_this_turn = 0
                ent = self.entities.get(current_entity)
                if ent is None:
                    continue
                enemy = self._enemy_of(ent.id)
                dist = self._dist(ent.cell, enemy.cell) if enemy else None
                text = f"▸ {ent.name}'s turn — cell {ent.cell}"
                if enemy is not None and dist is not None:
                    text += f" | dist to {enemy.name}: {dist}"
                current_events.append(SpatialEvent(
                    kind="turn_start", entity_id=ent.id, text=text,
                    from_cell=ent.cell, distance=dist,
                ))

            elif code == 13:  # SET_WEAPON [13, weapon_template]
                if current_entity is None:
                    continue
                tmpl = action[1]
                w = WEAPON_REGISTRY.by_template(tmpl)
                name = w.name.upper() if w else f"W#{tmpl}"
                self.entities[current_entity].weapon_template = tmpl
                tp_spent_this_turn += 1
                current_events.append(SpatialEvent(
                    kind="set_weapon", entity_id=current_entity,
                    text=f"  SET_WEAPON {name}  (-1 TP)",
                ))

            elif code == 10:  # MOVE_TO [10, entity_id, dest, path]
                eid = action[1]
                dest = action[2]
                path = action[3] if len(action) > 3 and isinstance(action[3], list) else []
                ent = self.entities.get(eid)
                if ent is None:
                    continue
                from_cell = ent.cell
                mp_used = len(path) if path else self._dist(from_cell, dest)
                if eid == current_entity:
                    mp_spent_this_turn += mp_used
                enemy = self._enemy_of(ent.id)
                dist_before = self._dist(from_cell, enemy.cell) if enemy else None
                dist_after = self._dist(dest, enemy.cell) if enemy else None
                ent.cell = dest
                arrow = "↓"
                if enemy is not None and dist_before is not None and dist_after is not None:
                    if dist_after < dist_before:
                        arrow = "→ (closer)"
                    elif dist_after > dist_before:
                        arrow = "← (further)"
                    else:
                        arrow = "↔ (no Δ)"
                text = f"  MOVE {from_cell} → {dest}  [{mp_used} MP]"
                if enemy is not None:
                    text += f"  dist {dist_before}→{dist_after} {arrow}"
                current_events.append(SpatialEvent(
                    kind="move", entity_id=eid, text=text,
                    from_cell=from_cell, to_cell=dest,
                    distance=dist_after,
                ))

            elif code == 16:  # USE_WEAPON [16, target_cell, target_entity]
                if current_entity is None:
                    continue
                target_cell = action[1]
                target_entity = action[2] if len(action) > 2 else None
                ent = self.entities[current_entity]
                tmpl = ent.weapon_template
                w = WEAPON_REGISTRY.by_template(tmpl) if tmpl else None
                if w is not None:
                    tp_spent_this_turn += w.cost
                current_events.append(self._range_event(
                    kind="weapon",
                    actor=ent,
                    name=w.name.upper() if w else f"W#{tmpl}",
                    target_cell=target_cell,
                    range_min=w.min_range if w else None,
                    range_max=w.max_range if w else None,
                    needs_los=w.los if w else False,
                ))

            elif code == 12:  # USE_CHIP [12, chip_template, cell, success]
                if current_entity is None:
                    continue
                chip_tmpl = action[1]
                target_cell = action[2]
                chip = CHIP_REGISTRY.by_template(chip_tmpl)
                ent = self.entities[current_entity]
                if chip is not None:
                    tp_spent_this_turn += chip.cost
                current_events.append(self._range_event(
                    kind="chip",
                    actor=ent,
                    name=chip.name.upper() if chip else f"CHIP#{chip_tmpl}",
                    target_cell=target_cell,
                    range_min=chip.min_range if chip else None,
                    range_max=chip.max_range if chip else None,
                    needs_los=chip.los if chip else False,
                ))

            elif code == 101:  # LOST_LIFE [101, target_entity, amount, ...]
                target = action[1]
                dmg = action[2] if len(action) > 2 else 0
                ent = self.entities.get(target)
                if ent is not None:
                    ent.hp = max(0, ent.hp - dmg)
                    current_events.append(SpatialEvent(
                        kind="damage", entity_id=target,
                        text=f"    ✖ {ent.name} -{dmg} HP  (→ {ent.hp})",
                    ))

            elif code == 103:  # HEAL [103, entity, amount]
                target = action[1]
                heal = action[2] if len(action) > 2 else 0
                ent = self.entities.get(target)
                if ent is not None:
                    ent.hp = min(ent.hp_max, ent.hp + heal)
                    current_events.append(SpatialEvent(
                        kind="heal", entity_id=target,
                        text=f"    ♥ {ent.name} +{heal} HP  (→ {ent.hp})",
                    ))

            elif code == 5:  # PLAYER_DEAD [5, entity]
                target = action[1]
                ent = self.entities.get(target)
                if ent is not None:
                    ent.hp = 0
                    current_events.append(SpatialEvent(
                        kind="dead", entity_id=target,
                        text=f"    💀 {ent.name} DIED",
                    ))

            elif code == 8:  # END_TURN [8, eid, MAX_TP, MAX_MP]
                # action[2]/[3] are the entity's MAX TP/MP (not spent).
                # We sum actual costs through the turn ourselves.
                eid = action[1] if len(action) > 1 else current_entity
                max_tp = action[2] if len(action) > 2 else 0
                max_mp = action[3] if len(action) > 3 else 0
                if eid is not None and eid in self.entities:
                    name = self.entities[eid].name
                    tp_unspent = max_tp - tp_spent_this_turn
                    mp_unspent = max_mp - mp_spent_this_turn
                    tail = ""
                    if tp_unspent > 0 or mp_unspent > 0:
                        tail = f"  ⚠ unspent: {tp_unspent} TP, {mp_unspent} MP"
                    current_events.append(SpatialEvent(
                        kind="end_turn", entity_id=eid,
                        text=(
                            f"  ◂ {name} ends turn  "
                            f"(TP {tp_spent_this_turn}/{max_tp}, "
                            f"MP {mp_spent_this_turn}/{max_mp}){tail}"
                        ),
                    ))

            elif code == 14:  # STACK_EFFECT — buff stacks (motivation, ferocity, etc.)
                target = action[1] if len(action) > 1 else None
                eff_id = action[2] if len(action) > 2 else -1
                val = action[3] if len(action) > 3 else 0
                turns_left = action[4] if len(action) > 4 else 0
                tname = self.entities[target].name if target in self.entities else f"E{target}"
                current_events.append(SpatialEvent(
                    kind="effect", entity_id=target,
                    text=f"    ⚑ STACK_EFFECT on {tname}: id={eff_id} val={val} ({turns_left}t)",
                ))

            elif code == 301:  # ADD_WEAPON_EFFECT — weapon passive fires
                target = action[1] if len(action) > 1 else None
                eff_id = action[2] if len(action) > 2 else -1
                val = action[3] if len(action) > 3 else 0
                tname = self.entities[target].name if target in self.entities else f"E{target}"
                current_events.append(SpatialEvent(
                    kind="effect", entity_id=target,
                    text=f"    ⚑ weapon-effect on {tname}: id={eff_id} val={val}",
                ))

            elif code == 302:  # ADD_CHIP_EFFECT — shield/helmet/armor/etc. apply
                target = action[1] if len(action) > 1 else None
                eff_id = action[2] if len(action) > 2 else -1
                tname = self.entities[target].name if target in self.entities else f"E{target}"
                current_events.append(SpatialEvent(
                    kind="effect", entity_id=target,
                    text=f"    ⚑ chip-effect on {tname}: id={eff_id}",
                ))

            elif code == 303:  # REMOVE_EFFECT [303, target, effect_id]
                target = action[1] if len(action) > 1 else None
                eff_id = action[2] if len(action) > 2 else -1
                tname = self.entities[target].name if target in self.entities else f"E{target}"
                current_events.append(SpatialEvent(
                    kind="effect", entity_id=target,
                    text=f"    ⚐ effect ends on {tname}: id={eff_id}",
                ))

            elif code == 304:  # UPDATE_EFFECT — stat buff recalc
                target = action[1] if len(action) > 1 else None
                eff_id = action[2] if len(action) > 2 else -1
                tname = self.entities[target].name if target in self.entities else f"E{target}"
                current_events.append(SpatialEvent(
                    kind="effect", entity_id=target,
                    text=f"    ⚑ update-effect on {tname}: id={eff_id}",
                ))

        if current_events:
            turns.append((current_turn, current_events))
        return turns

    def _snapshot_event(self, e: Entity) -> SpatialEvent:
        marker = "→" if e.team == self.my_team else " "
        text = (
            f"{marker} {e.name}: cell {e.cell}, "
            f"HP {e.hp}/{e.hp_max}"
        )
        return SpatialEvent(kind="snapshot", entity_id=e.id, text=text)

    def _range_event(
        self,
        kind: str,
        actor: Entity,
        name: str,
        target_cell: int,
        range_min: int | None,
        range_max: int | None,
        needs_los: bool,
    ) -> SpatialEvent:
        dist = self._dist(actor.cell, target_cell)
        in_range = None
        if range_min is not None and range_max is not None:
            in_range = range_min <= dist <= range_max
        los_ok: bool | None = None
        if needs_los:
            los_ok = self._los(actor.cell, target_cell)

        tag = f"✓" if (in_range and (los_ok is None or los_ok)) else "✗"
        if in_range is None:
            tag = "·"
        # Use parens/pipes, never square brackets — Rich interprets them as markup.
        parts = [f"  USE {name} @ cell {target_cell}  (dist {dist}"]
        if range_min is not None and range_max is not None:
            parts.append(f" | range {range_min}-{range_max} {tag}")
        if needs_los:
            parts.append(f" | LOS {'✓' if los_ok else '✗'}")
        elif range_min is not None:
            parts.append(" | no-LOS")
        parts.append(")")
        text = "".join(parts)
        notes: list[str] = []
        if in_range is False:
            notes.append(f"OUT-OF-RANGE (dist {dist} vs {range_min}-{range_max})")
        if needs_los and los_ok is False:
            notes.append("BLOCKED BY OBSTACLE/ENTITY")
        if notes:
            text += "  ⚠ " + " · ".join(notes)

        return SpatialEvent(
            kind=kind, entity_id=actor.id, text=text,
            from_cell=actor.cell, target_cell=target_cell,
            distance=dist, range_min=range_min, range_max=range_max,
            in_range=in_range, needs_los=needs_los, has_los=los_ok,
            notes=notes,
        )

    # ── rendering ──────────────────────────────────────────────────────

    def render(self, console: Console) -> None:
        """Print rich turn-by-turn spatial view."""
        # Map summary
        w, h = self.grid.width, self.grid.height
        obs = len(self.grid.obstacles)
        console.print(
            f"\n[bold]Spatial Walk[/bold]  (grid {w}×{h}, {obs} obstacles)"
        )
        for e in self.entities.values():
            mark = "[cyan]→[/cyan]" if e.team == self.my_team else " "
            console.print(
                f"  {mark} {e.name} L{e.level} team {e.team}  spawn cell {e.cell}  HP {e.hp}"
            )
        # Initial distance
        ids = list(self.entities)
        if len(ids) == 2:
            d0 = self._dist(self.entities[ids[0]].cell, self.entities[ids[1]].cell)
            console.print(f"  Initial distance: {d0}")

        # Turn-by-turn
        for turn_no, events in self.walk():
            console.print(f"\n[bold yellow]═══ Turn {turn_no} ═══[/bold yellow]")
            for ev in events:
                style = self._style_for(ev)
                console.print(f"  {ev.text}", style=style)

    @staticmethod
    def _style_for(ev: SpatialEvent) -> str:
        if ev.notes:
            return "red"
        if ev.kind == "turn_start":
            return "cyan"
        if ev.kind == "damage":
            return "red"
        if ev.kind == "heal":
            return "green"
        if ev.kind == "dead":
            return "bold red"
        if ev.kind == "end_turn":
            return "dim"
        if ev.kind == "snapshot":
            return "dim cyan"
        return ""
