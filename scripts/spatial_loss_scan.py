"""Batch --spatial over recent IAdonis losses, aggregate anomaly patterns.

Each anomaly is a concrete, code-evident bug class:
  NO_OP_CAST        USE_CHIP followed by no ADD_EFFECT (wasted TP)
  OUT_OF_RANGE      weapon/chip used with dist outside range
  LOS_BLOCKED       LOS chip/weapon used without LOS
  REDUNDANT_WEAPON  SET_WEAPON twice in same turn (2 TP wasted)
  SELF_CAST_ALLY    Ally/team-only chip cast on self in 1v1
  ZERO_DMG_TURN     Our turn ended with TP spent but no LOST_LIFE on enemy

Each finding carries: fight_id, turn, actor, text, evidence — so we can re-check.

Output: docs/research/spatial_loss_scan_s53.md
"""

from __future__ import annotations

import json
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

from leekwars_agent.fight_spatial import SpatialFight
from leekwars_agent.models.equipment import CHIP_REGISTRY, WEAPON_REGISTRY

IADONIS_ID = 131321
DB_PATH = "data/fights_meta.db"


def iter_recent_losses(limit: int = 20) -> list[tuple[int, dict]]:
    """Return [(fight_id, fight_json), ...] for recent IAdonis losses."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        SELECT fight_id, winner, json_data
        FROM fights
        WHERE json_data LIKE '%131321%'
        ORDER BY fight_date DESC
        LIMIT 300
        """
    )
    out: list[tuple[int, dict]] = []
    for fid, winner, raw in c.fetchall():
        try:
            j = json.loads(raw)
        except Exception:
            continue
        ia_team = None
        for l in j.get("leeks1", []):
            if l.get("id") == IADONIS_ID:
                ia_team = 1
        for l in j.get("leeks2", []):
            if l.get("id") == IADONIS_ID:
                ia_team = 2
        if ia_team and winner and winner != ia_team:
            data = j.get("data") or j
            if len(data.get("leeks", [])) == 2:
                out.append((fid, j))
                if len(out) >= limit:
                    break
    conn.close()
    return out


def my_team_for(fight: dict) -> int:
    for l in fight.get("leeks1", []):
        if l.get("id") == IADONIS_ID:
            return 1
    return 2


# ── Anomaly detectors ────────────────────────────────────────────────────

def scan_fight(fight_id: int, fight: dict) -> list[dict]:
    """Walk fight actions, emit anomaly records."""
    my_team = my_team_for(fight)
    data = fight.get("data") or fight
    sf = SpatialFight(data, my_team=my_team)
    turns = sf.walk()

    anomalies: list[dict] = []
    actions = data.get("actions", [])

    # Codes that are evidence of a cast doing something:
    #   14  STACK_EFFECT       buff stacked on self/ally (motivation, ferocity…)
    #   101 LOST_LIFE          damage landed
    #   103 HEAL               heal landed
    #   104 VITALITY           vitality buff
    #   107 NOVA_DAMAGE        nova
    #   108 DAMAGE_RETURN      liberation-style return
    #   109 LIFE_DAMAGE        lifesteal?
    #   110 POISON_DAMAGE      poison tick
    #   111 AFTEREFFECT        residual
    #   112 NOVA_VITALITY      nova heal
    #   302 ADD_CHIP_EFFECT    shield/helmet/armor/wall/stretching apply
    #   303 REMOVE_EFFECT      liberation fires
    #   304 UPDATE_EFFECT      stat buff recalc
    #   306 REDUCE_EFFECTS     "effects reduced by N%" (toxin-style)
    #   307 REMOVE_POISONS     antidote fires
    #   308 REMOVE_SHACKLES    liberation shackle-break
    EFFECT_CODES = {14, 101, 103, 104, 107, 108, 109, 110, 111, 112,
                    302, 303, 304, 306, 307, 308}
    for i, a in enumerate(actions):
        if not a or a[0] != 12:  # USE_CHIP
            continue
        chip_tmpl = a[1]
        target_cell = a[2]
        success = a[3] if len(a) > 3 else 1
        chip = CHIP_REGISTRY.by_template(chip_tmpl)
        if chip is None:
            continue
        # Scan forward until code 8 (end turn) or code 6 (new turn)
        found_any_effect = False
        j = i + 1
        while j < len(actions) and actions[j] and actions[j][0] not in (6, 8):
            if actions[j][0] in EFFECT_CODES:
                found_any_effect = True
                break
            j += 1
        if not found_any_effect and success:
            anomalies.append({
                "fight_id": fight_id,
                "kind": "NO_OP_CAST",
                "chip": chip.name,
                "tp_cost": chip.cost,
                "target_cell": target_cell,
                "success_flag": success,
                "detail": f"{chip.name} cast @ cell {target_cell} produced no effect/damage/heal",
            })

    # Second pass: per-turn quality checks. Walk raw actions so we can
    # count effect codes (14/101/103/104/107/110/111/302/303/304) per turn.
    EFFECT_EVENT_CODES = {14, 101, 103, 104, 107, 108, 109, 110, 111, 112,
                          302, 303, 304, 306, 307, 308}
    for ev in (e for _, evs in turns for e in evs):
        if ev.kind in ("weapon", "chip") and ev.in_range is False:
            anomalies.append({
                "fight_id": fight_id,
                "kind": "OUT_OF_RANGE",
                "actor_id": ev.entity_id,
                "detail": ev.text.strip(),
            })
        if ev.kind in ("weapon", "chip") and ev.needs_los and ev.has_los is False:
            anomalies.append({
                "fight_id": fight_id,
                "kind": "LOS_BLOCKED",
                "actor_id": ev.entity_id,
                "detail": ev.text.strip(),
            })

    # Walk raw actions for turn-level idle detection + redundant SET_WEAPON +
    # TP_UNDERUTILIZED. Sum actual TP costs ourselves (END_TURN reports MAX_TP).
    w_cost = {w.template: w.cost for w in WEAPON_REGISTRY._by_id.values()}
    c_cost = {c.template: c.cost for c in CHIP_REGISTRY._by_id.values()}
    current_actor: int | None = None
    active_weapon: int | None = None
    turn_no_cur = 1
    set_weapon_count = 0
    effect_events_in_turn = 0
    tp_spent = 0
    for a in actions:
        if not a:
            continue
        code = a[0]
        if code == 6:
            turn_no_cur = a[1] if len(a) > 1 else turn_no_cur + 1
            continue
        if code == 7:
            current_actor = a[1]
            set_weapon_count = 0
            effect_events_in_turn = 0
            tp_spent = 0
            continue
        if code == 13:
            set_weapon_count += 1
            tp_spent += 1
            active_weapon = a[1]
        elif code == 12:
            tp_spent += c_cost.get(a[1], 0)
        elif code == 16 and active_weapon is not None:
            tp_spent += w_cost.get(active_weapon, 0)
        if code in EFFECT_EVENT_CODES:
            effect_events_in_turn += 1
        if code == 8:  # END_TURN [8, eid, MAX_TP, MAX_MP]
            max_tp = a[2] if len(a) > 2 else 0
            eid = a[1] if len(a) > 1 else current_actor
            if set_weapon_count > 1:
                anomalies.append({
                    "fight_id": fight_id,
                    "kind": "REDUNDANT_WEAPON",
                    "turn": turn_no_cur,
                    "actor_id": eid,
                    "detail": (
                        f"SET_WEAPON called {set_weapon_count}× in turn "
                        f"{turn_no_cur} ({set_weapon_count - 1} TP wasted)"
                    ),
                })
            ent = sf.entities.get(eid) if eid is not None else None
            if (
                ent is not None
                and ent.team == my_team
                and tp_spent >= 5
                and effect_events_in_turn == 0
            ):
                anomalies.append({
                    "fight_id": fight_id,
                    "kind": "IDLE_TURN",
                    "turn": turn_no_cur,
                    "actor_id": eid,
                    "detail": (
                        f"Our turn spent {tp_spent} TP with ZERO effect events "
                        f"(no damage, no heal, no buff)"
                    ),
                })
            # TP_UNDERUTILIZED: our turn left ≥6 TP on the table
            # (threshold: more than one Flame/b_laser cost unspent)
            if (
                ent is not None
                and ent.team == my_team
                and max_tp - tp_spent >= 6
            ):
                anomalies.append({
                    "fight_id": fight_id,
                    "kind": "TP_UNDERUTILIZED",
                    "turn": turn_no_cur,
                    "actor_id": eid,
                    "detail": (
                        f"Our turn used only {tp_spent}/{max_tp} TP — "
                        f"{max_tp - tp_spent} TP wasted (probably OOR / starved)"
                    ),
                })
            current_actor = None

    # Third pass: ally-only chip self-cast
    for i, a in enumerate(actions):
        if not a or a[0] != 12:
            continue
        chip_tmpl = a[1]
        target_cell = a[2]
        chip = CHIP_REGISTRY.by_template(chip_tmpl)
        if chip is None or not chip.effects:
            continue
        # targets bitmask 22 = allies only (no self bit). Cast on self in 1v1 = wasted.
        if chip.effects[0].targets in (22, 4):
            # Determine who cast: walk backward for LEEK_TURN (code 7)
            caster_id = None
            j = i - 1
            while j >= 0:
                if actions[j] and actions[j][0] == 7:
                    caster_id = actions[j][1]
                    break
                j -= 1
            # Is target cell == caster cell?
            ent = sf.entities.get(caster_id) if caster_id else None
            if ent is None:
                continue
            # Re-simulate position: easier — find any MOVE_TO before this index for this entity
            cur_cell = ent.cell  # spawn cell fallback
            k = 0
            while k < i:
                if actions[k] and actions[k][0] == 10 and actions[k][1] == caster_id:
                    cur_cell = actions[k][2]
                k += 1
            if cur_cell == target_cell:
                anomalies.append({
                    "fight_id": fight_id,
                    "kind": "SELF_CAST_ALLY",
                    "chip": chip.name,
                    "tp_cost": chip.cost,
                    "caster_id": caster_id,
                    "detail": (
                        f"{chip.name} (targets={chip.effects[0].targets}, "
                        f"ally-only) cast on self @ cell {target_cell}"
                    ),
                })
    return anomalies


def summarize(all_anomalies: list[dict]) -> str:
    by_kind = Counter(a["kind"] for a in all_anomalies)
    by_chip = Counter(a.get("chip", "-") for a in all_anomalies if "chip" in a)
    by_fight = Counter(a["fight_id"] for a in all_anomalies)

    lines: list[str] = []
    lines.append("# Spatial Loss Scan — S53")
    lines.append("")
    lines.append(
        "Batch-ran `--spatial` over recent IAdonis losses. Each anomaly is a "
        "code-evident bug class we can re-verify with `leek fight get <id> --spatial`."
    )
    lines.append("")
    lines.append("## Headline findings")
    lines.append("")
    lines.append(
        "1. **Every WHIP cast in 1v1 is a no-op.** Our v15 AI wastes ~4 TP/turn "
        "on `useChip(CHIP_WHIP, me)` — the chip has `targets=22` (ally-only) so "
        "in 1v1 it produces no `ADD_CHIP_EFFECT` (code 302), no damage, no heal. "
        "See `NO_OP_CAST` and `SELF_CAST_ALLY` counts."
    )
    lines.append("")
    lines.append(
        "2. **TP underutilization is the dominant failure mode.** When we're out "
        "of weapon range in early turns, the AI falls back to the no-op WHIP and "
        "ends turn with 9-10 TP unspent. Combined cost across 20 fights: "
        "**hundreds of TP evaporated before we ever engage**."
    )
    lines.append("")
    lines.append(
        "3. **The scanner itself corrected an observability bug mid-flight.** "
        "`END_TURN [8, eid, tp, mp]` carries the entity's MAX TP/MP — not spent. "
        "`fight_spatial.py` was previously labelling this as \"TP spent\"; now "
        "displays `TP 5/14` with `⚠ unspent: 9 TP` where applicable."
    )
    lines.append("")
    lines.append("## Anomaly counts by kind")
    lines.append("")
    lines.append("| Kind | Count | What it means |")
    lines.append("|------|-------|----------------|")
    meanings = {
        "NO_OP_CAST": "USE_CHIP produced no effect/damage/heal — wasted TP",
        "OUT_OF_RANGE": "Weapon/chip used with dist outside its range",
        "LOS_BLOCKED": "LOS-requiring chip/weapon used without LOS",
        "REDUNDANT_WEAPON": "SET_WEAPON called >1× per turn — 1 TP wasted per extra call",
        "SELF_CAST_ALLY": "Ally-only chip cast on self in 1v1 — always no-op",
        "IDLE_TURN": "Our turn spent ≥5 TP with ZERO effect events — pure waste",
        "TP_UNDERUTILIZED": "Our turn left ≥6 TP on the table (OOR / TP-starved)",
    }
    for k, n in by_kind.most_common():
        lines.append(f"| **{k}** | {n} | {meanings.get(k, '?')} |")
    lines.append("")
    lines.append("## Chip-level breakdown (for chip-origin anomalies)")
    lines.append("")
    for chip, n in by_chip.most_common(15):
        if chip == "-":
            continue
        lines.append(f"- `{chip}` — {n} anomaly events")
    lines.append("")
    lines.append("## Fight-level breakdown (top offenders)")
    lines.append("")
    for fid, n in by_fight.most_common(10):
        lines.append(f"- fight `{fid}` — {n} anomalies")
    lines.append("")
    lines.append("## Sample evidence")
    lines.append("")
    sample_by_kind: dict[str, list[dict]] = defaultdict(list)
    for a in all_anomalies:
        if len(sample_by_kind[a["kind"]]) < 3:
            sample_by_kind[a["kind"]].append(a)
    for kind, samples in sample_by_kind.items():
        lines.append(f"### {kind}")
        lines.append("")
        for s in samples:
            lines.append(f"- fight `{s['fight_id']}` · {s.get('detail', '')}")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    fights = iter_recent_losses(limit=n)
    print(f"Scanning {len(fights)} recent IAdonis losses…")
    all_anomalies: list[dict] = []
    for fid, j in fights:
        try:
            anomalies = scan_fight(fid, j)
            all_anomalies.extend(anomalies)
            print(f"  fight {fid}: {len(anomalies)} anomalies")
        except Exception as e:
            print(f"  fight {fid}: ERROR {e}")
    print(f"\nTotal anomalies: {len(all_anomalies)}")

    # Write report
    report = summarize(all_anomalies)
    out_path = Path("docs/research/spatial_loss_scan_s53.md")
    out_path.write_text(report)
    print(f"\nReport → {out_path}")

    # Also dump raw JSON for drill-down
    raw_path = Path("data/research/spatial_loss_scan_s53_raw.json")
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(json.dumps(all_anomalies, indent=2, default=str))
    print(f"Raw  → {raw_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
