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
        science: int = 0,
        power: int = 0,
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
        self.science = science
        self.power = power
        self.frequency = frequency

        # Equipment
        self.weapons: list = weapons or []
        self.chips: list = chips or []

        # Fight state
        self.cell: int = 0
        self.current_weapon: dict | None = weapons[0] if weapons else None
        self.effects: list[ActiveEffect] = []
        self.cooldowns: dict[int, int] = {}  # chip_template -> turns remaining
        # Initial cooldowns: some chips start the fight on cooldown
        for c in self.chips:
            ic = c.get("initial_cooldown", 0)
            if ic and ic > 0:
                self.cooldowns[c["template"]] = ic
        self.chip_fight_uses: dict[int, int] = {}  # chip_template -> total uses this fight
        self.tp_used: int = 0
        self.mp_used: int = 0
        self.dead: bool = False
        self.is_summon: bool = False
        self.states: set[int] = set()  # active entity states (INVINCIBLE=3, ROOTED=9, etc.)

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
        """Current MP = base + buffs - shackles - used."""
        total = self.base_mp
        for e in self.effects:
            if e.effect_type == "mp_buff":
                total += int(e.value)
            elif e.effect_type == "mp_shackle":
                total -= int(e.value)
        return max(0, total - self.mp_used)

    @property
    def effective_strength(self) -> int:
        """Strength including active buffs/shackles."""
        bonus = sum(int(e.value) for e in self.effects if e.effect_type == "str_buff")
        shackle = sum(int(e.value) for e in self.effects if e.effect_type == "str_shackle")
        return max(0, self.strength + bonus - shackle)

    @property
    def effective_agility(self) -> int:
        """Agility including buffs/shackles."""
        shackle = sum(int(e.value) for e in self.effects if e.effect_type == "agi_shackle")
        return max(0, self.agility - shackle)

    @property
    def effective_wisdom(self) -> int:
        """Wisdom including buffs/shackles."""
        buff = sum(int(e.value) for e in self.effects if e.effect_type == "wis_buff")
        shackle = sum(int(e.value) for e in self.effects if e.effect_type == "wis_shackle")
        return max(0, self.wisdom + buff - shackle)

    @property
    def effective_magic(self) -> int:
        """Magic including shackles."""
        shackle = sum(int(e.value) for e in self.effects if e.effect_type == "mag_shackle")
        return max(0, self.magic - shackle)

    @property
    def effective_science(self) -> int:
        """Science stat (no known buffs/shackles currently)."""
        return self.science

    @property
    def effective_power(self) -> int:
        """Power including raw power buffs."""
        buff = sum(int(e.value) for e in self.effects if e.effect_type == "pow_buff")
        return self.power + buff

    def stat_dict(self) -> dict[str, int]:
        """All effective stats as a dict — for use with calc_effect_value()."""
        return {
            "strength": self.effective_strength,
            "agility": self.effective_agility,
            "resistance": self.resistance,
            "wisdom": self.effective_wisdom,
            "magic": self.effective_magic,
            "science": self.effective_science,
            "power": self.effective_power,
        }

    @property
    def abs_shield(self) -> float:
        """Total absolute shield, reduced by absolute vulnerability."""
        shield = sum(e.value for e in self.effects if e.effect_type == "abs_shield")
        vuln = sum(e.value for e in self.effects if e.effect_type == "abs_vulnerability")
        return max(0, shield - vuln)

    @property
    def rel_shield(self) -> float:
        """Total relative shield, reduced by relative vulnerability."""
        shield = sum(e.value for e in self.effects if e.effect_type == "rel_shield")
        vuln = sum(e.value for e in self.effects if e.effect_type == "rel_vulnerability")
        return max(0, shield - vuln)

    @property
    def damage_return(self) -> float:
        """Total damage return percentage from active effects."""
        return sum(e.value for e in self.effects if e.effect_type == "damage_return")

    @property
    def is_invincible(self) -> bool:
        return 3 in self.states

    @property
    def is_rooted(self) -> bool:
        return 9 in self.states

    @property
    def is_petrified(self) -> bool:
        return 10 in self.states

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
        surviving = []
        for e in self.effects:
            e.remaining_turns -= 1
            if e.remaining_turns > 0:
                surviving.append(e)
            elif e.effect_type.startswith("state_"):
                # Remove entity state when the state effect expires
                state_id = int(e.value)
                self.states.discard(state_id)
        self.effects = surviving

    # ── combat ────────────────────────────────────────────────────────

    def take_damage(self, raw_damage: float, erosion_rate: float = 0.05) -> int:
        """Apply damage after shields. Returns actual damage dealt.

        Formula (Java EffectDamage.java):
            after_shields = raw - raw*(rel_shield/100) - abs_shield
            final = max(0, after_shields)
            erosion = round(final * erosion_rate)

        Erosion rates (parsed from Effect.java:206-207):
            Normal damage: 5%
            Poison damage: 10%
            +10% if critical hit
        """
        if self.is_invincible:
            return 0
        rel = self.rel_shield
        abs_s = self.abs_shield
        after_rel = raw_damage * (1 - rel / 100) if rel > 0 else raw_damage
        final = int(max(0, after_rel - abs_s))

        # Cap at current life (Java: if (target.getLife() < value) value = target.getLife())
        if self.life < final:
            final = self.life

        # Erosion: permanently reduces max HP
        erosion = int(round(final * erosion_rate))
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
