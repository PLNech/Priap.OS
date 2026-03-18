"""Scout module — live recon of any leek's build from recent fight data.

Fetches a leek's fight history, then inspects fight replays to extract:
- Stats: HP, STR, RES, TP, MP, AGI, WIS, frequency
- Chips used (decoded via CHIP_REGISTRY)
- Weapons used (decoded via WEAPON_REGISTRY)
- Summon usage

The key insight: leek profiles don't expose builds, but fight replays do.
Stats come from data.leeks; chips/weapons from USE_CHIP (action 12) and
USE_WEAPON (action 16) in the action log.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from leekwars_agent.api import LeekWarsAPI
from leekwars_agent.models.equipment import CHIP_REGISTRY, WEAPON_REGISTRY


@dataclass
class LeekBuild:
    """Reconstructed build for a scouted leek."""

    leek_id: int
    name: str
    level: int
    talent: int

    # Stats (from fight data.leeks)
    life: int = 0
    strength: int = 0
    resistance: int = 0
    agility: int = 0
    wisdom: int = 0
    frequency: int = 0
    tp: int = 0
    mp: int = 0
    science: int = 0
    magic: int = 0

    # Equipment (decoded names, aggregated across fights)
    chips: list[str] = field(default_factory=list)
    weapons: list[str] = field(default_factory=list)
    uses_summons: bool = False

    # Meta
    fights_analyzed: int = 0
    recent_wr: str = ""  # e.g. "3W-2L/5"

    def to_dict(self) -> dict[str, Any]:
        return {
            "leek_id": self.leek_id,
            "name": self.name,
            "level": self.level,
            "talent": self.talent,
            "life": self.life,
            "strength": self.strength,
            "resistance": self.resistance,
            "agility": self.agility,
            "wisdom": self.wisdom,
            "frequency": self.frequency,
            "tp": self.tp,
            "mp": self.mp,
            "science": self.science,
            "magic": self.magic,
            "chips": self.chips,
            "weapons": self.weapons,
            "uses_summons": self.uses_summons,
            "fights_analyzed": self.fights_analyzed,
            "recent_wr": self.recent_wr,
        }


def _extract_equipment_from_actions(
    actions: list, leek_entity_idx: int
) -> tuple[set[int], set[int]]:
    """Parse fight actions to find chips/weapons used by a specific entity.

    Action codes (from FightConstants.java):
        7  = START_TURN(entity_id) — sets current actor
        12 = USE_CHIP(chip_template, cell, target, success)
        13 = SET_WEAPON(weapon_template) — equips a weapon
        16 = USE_WEAPON(cell, target) — fires currently equipped weapon

    Weapons are identified from SET_WEAPON (code 13), NOT USE_WEAPON (code 16).
    USE_WEAPON's second arg is the target cell, not a weapon template.
    """
    chips = set()
    weapons = set()
    current_entity = None

    for action in actions:
        if not isinstance(action, list) or not action:
            continue
        code = action[0]
        if code == 7:  # START_TURN
            current_entity = action[1] if len(action) > 1 else None
        elif code == 12 and current_entity == leek_entity_idx:
            if len(action) > 1:
                chips.add(action[1])
        elif code == 13 and current_entity == leek_entity_idx:
            # SET_WEAPON: [13, weapon_template]
            if len(action) > 1:
                weapons.add(action[1])

    return chips, weapons


def _decode_templates(templates: set[int], registry) -> list[str]:
    """Convert template IDs to human-readable names."""
    names = []
    for t in sorted(templates):
        try:
            obj = registry.by_template(t)
            names.append(obj.name if obj else f"template#{t}")
        except Exception:
            names.append(f"template#{t}")
    return names


def scout_leek(
    api: LeekWarsAPI,
    leek_id: int,
    max_fights: int = 5,
    solo_only: bool = True,
    delay: float = 0.3,
) -> LeekBuild:
    """Scout a leek by analyzing their recent fights.

    Args:
        api: Authenticated API instance
        leek_id: Target leek ID
        max_fights: Max fights to inspect for equipment (default 5)
        solo_only: Only consider solo garden fights (type=0, context=2)
        delay: Delay between API calls (be polite)

    Returns:
        LeekBuild with reconstructed stats and equipment
    """
    # Step 1: Get leek profile for name/level/talent
    leek_data = api.get_leek(leek_id)
    leek = leek_data.get("leek", leek_data)
    name = leek.get("name", f"leek#{leek_id}")
    level = leek.get("level", 0)
    talent = leek.get("talent", 0)

    build = LeekBuild(leek_id=leek_id, name=name, level=level, talent=talent)

    # Step 2: Get fight history
    time.sleep(delay)
    hist = api.get_leek_history(leek_id)
    fights = hist.get("fights", [])

    if solo_only:
        fights = [f for f in fights if f.get("type") == 0 and f.get("context") == 2]

    # Win rate from recent solo fights
    recent = fights[:10]
    wins = sum(1 for f in recent if f.get("result") == "victory")
    losses = sum(1 for f in recent if f.get("result") == "defeat")
    build.recent_wr = f"{wins}W-{losses}L/{len(recent)}"

    # Step 3: Fetch fight replays to extract stats + equipment
    all_chips: set[int] = set()
    all_weapons: set[int] = set()
    stats_found = False

    for fight in fights[:max_fights]:
        time.sleep(delay)
        try:
            fd = api.get_fight(fight["id"])
        except Exception:
            continue

        data = fd.get("data", {})
        leeks = data.get("leeks", [])
        actions = data.get("actions", [])

        # Find our target in data.leeks
        entity_idx = None
        for i, lk in enumerate(leeks):
            if not isinstance(lk, dict):
                continue
            if lk.get("name") == name and not lk.get("summon"):
                entity_idx = i
                # Extract stats from most recent fight only
                if not stats_found:
                    build.life = lk.get("life", 0)
                    build.strength = lk.get("strength", 0)
                    build.resistance = lk.get("resistance", 0)
                    build.agility = lk.get("agility", 0)
                    build.wisdom = lk.get("wisdom", 0)
                    build.frequency = lk.get("frequency", 0)
                    build.tp = lk.get("tp", 0)
                    build.mp = lk.get("mp", 0)
                    build.science = lk.get("science", 0)
                    build.magic = lk.get("magic", 0)
                    stats_found = True
                break

            # Check for summons owned by this leek
            if lk.get("summon") and lk.get("farmer") == leek.get("farmer"):
                build.uses_summons = True

        if entity_idx is not None:
            chips, weapons = _extract_equipment_from_actions(actions, entity_idx)
            all_chips |= chips
            all_weapons |= weapons

        build.fights_analyzed += 1

    # Step 4: Decode template IDs to names
    build.chips = _decode_templates(all_chips, CHIP_REGISTRY)
    build.weapons = _decode_templates(all_weapons, WEAPON_REGISTRY)

    return build


def scout_batch(
    api: LeekWarsAPI,
    leek_ids: list[int],
    max_fights: int = 3,
    delay: float = 0.3,
) -> list[LeekBuild]:
    """Scout multiple leeks."""
    results = []
    for lid in leek_ids:
        try:
            build = scout_leek(api, lid, max_fights=max_fights, delay=delay)
            results.append(build)
        except Exception as e:
            results.append(
                LeekBuild(leek_id=lid, name=f"ERROR: {e}", level=0, talent=0)
            )
    return results
