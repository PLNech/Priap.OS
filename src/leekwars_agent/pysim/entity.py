"""PySim entity — leek/summon model with stats, effects, cooldowns, damage."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ActiveEffect:
    """A timed buff/debuff on an entity."""

    effect_type: str  # 'abs_shield', 'rel_shield', 'tp_shackle', 'tp_buff', 'str_buff', 'poison', etc.
    value: float
    remaining_turns: int
    source_entity: int = 0


class Entity:
    """A fight participant (leek or summon) with stats, equipment, and effects."""

    def __init__(
        self,
        id: int,
        name: str,
        team: int,
        farmer: int,
        level: int,
        life: int,
        tp: int,
        mp: int,
        strength: int = 0,
        agility: int = 0,
        resistance: int = 0,
        wisdom: int = 0,
        magic: int = 0,
        frequency: int = 100,
        weapons: list | None = None,
        chips: list | None = None,
    ):
        # Identity
        self.id = id
        self.name = name
        self.team = team
        self.farmer = farmer
        self.level = level

        # Vitals
        self.base_life = life
        self.life = life
        self.max_life = life

        # Base resources (before buffs/debuffs)
        self.base_tp = tp
        self.base_mp = mp

        # Stats
        self.strength = strength
        self.agility = agility
        self.resistance = resistance
        self.wisdom = wisdom
        self.magic = magic
        self.frequency = frequency

        # Equipment
        self.weapons: list = weapons or []
        self.chips: list = chips or []

        # Fight state
        self.cell: int = 0
        self.current_weapon: dict | None = weapons[0] if weapons else None
        self.effects: list[ActiveEffect] = []
        self.cooldowns: dict[int, int] = {}  # chip_template -> turns remaining
        self.chip_fight_uses: dict[int, int] = {}  # chip_template -> total uses this fight
        self.tp_used: int = 0
        self.mp_used: int = 0
        self.dead: bool = False
        self.is_summon: bool = False

    # ── derived stats ─────────────────────────────────────────────────

    @property
    def tp(self) -> int:
        """Current TP = base + buffs - shackles - used."""
        total = self.base_tp
        for e in self.effects:
            if e.effect_type == "tp_buff":
                total += int(e.value)
            elif e.effect_type == "tp_shackle":
                total -= int(e.value)
        return max(0, total - self.tp_used)

    @property
    def mp(self) -> int:
        """Current MP = base - used."""
        return max(0, self.base_mp - self.mp_used)

    @property
    def effective_strength(self) -> int:
        """Strength including active buffs (e.g. Ferocity)."""
        bonus = sum(
            int(e.value) for e in self.effects if e.effect_type == "str_buff"
        )
        return self.strength + bonus

    @property
    def abs_shield(self) -> float:
        """Total absolute shield from active effects."""
        return sum(e.value for e in self.effects if e.effect_type == "abs_shield")

    @property
    def rel_shield(self) -> float:
        """Total relative shield from active effects."""
        return sum(e.value for e in self.effects if e.effect_type == "rel_shield")

    # ── turn lifecycle ────────────────────────────────────────────────

    def start_turn(self) -> None:
        """Called at start of entity's turn. Reset TP/MP used, tick cooldowns."""
        self.tp_used = 0
        self.mp_used = 0

        # Tick down cooldowns, remove expired
        expired: list[int] = []
        for chip_id, turns in self.cooldowns.items():
            if turns <= 1:
                expired.append(chip_id)
            else:
                self.cooldowns[chip_id] = turns - 1
        for chip_id in expired:
            del self.cooldowns[chip_id]

    def end_turn(self) -> None:
        """Called at end of entity's turn. Tick effects, remove expired."""
        self.effects = [e for e in self.effects if self._tick_effect(e)]

    @staticmethod
    def _tick_effect(e: ActiveEffect) -> bool:
        """Tick effect duration down by one. Returns True if still active."""
        e.remaining_turns -= 1
        return e.remaining_turns > 0

    # ── combat ────────────────────────────────────────────────────────

    def take_damage(self, raw_damage: float) -> int:
        """Apply damage after shields. Returns actual damage dealt.

        Formula: final = max(0, raw * (1 - rel_shield/100) - abs_shield)
        Erosion: 5% of final damage reduces max HP permanently.
        """
        rel = self.rel_shield
        abs_s = self.abs_shield
        after_rel = raw_damage * (1 - rel / 100) if rel > 0 else raw_damage
        final = int(max(0, after_rel - abs_s))

        # Erosion: 5% of final damage permanently reduces max HP
        erosion = int(final * 0.05)
        self.max_life = max(1, self.max_life - erosion)

        self.life = max(0, self.life - final)
        if self.life <= 0:
            self.dead = True
        return final

    def heal(self, amount: float) -> int:
        """Heal up to max_life. Returns actual healing applied."""
        amount_int = int(amount)
        actual = min(amount_int, self.max_life - self.life)
        self.life += actual
        return actual

    def add_effect(self, effect: ActiveEffect) -> None:
        """Append a new active effect."""
        self.effects.append(effect)

    # ── display ───────────────────────────────────────────────────────

    def __repr__(self) -> str:
        return (
            f"Entity({self.name!r}, id={self.id}, team={self.team}, "
            f"HP={self.life}/{self.max_life}, TP={self.tp}, MP={self.mp})"
        )
