"""Parse effect formulas from the Java generator source (Effect.java + Effect*.java).

This is the SINGLE SOURCE OF TRUTH for combat formula metadata:
  - CRITICAL_FACTOR
  - Erosion rates (base, poison, critical bonus)
  - Per-effect formula metadata: scaling stat, power flag, etc.

NEVER hand-write these values. If the Java source changes, this parser picks it up.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

_EFFECT_DIR = (
    Path(__file__).resolve().parents[3]
    / "tools"
    / "leek-wars-generator"
    / "src"
    / "main"
    / "java"
    / "com"
    / "leekwars"
    / "generator"
    / "effect"
)

_EFFECT_JAVA = _EFFECT_DIR / "Effect.java"


# ── Data classes ────────────────────────────────────────────────────


@dataclass
class EffectFormula:
    """Parsed metadata for one effect type's value formula."""

    effect_id: int
    class_name: str  # e.g. "EffectDamage"
    primary_stat: str | None = None  # "strength", "magic", "science", "resistance", "wisdom", "agility", None
    max_zero_stat: bool = False  # whether Math.max(0, stat) is used
    has_power: bool = False  # whether * (1 + getPower()/100) is in formula
    has_target_count: bool = False  # whether * targetCount is in formula


@dataclass
class EffectConstants:
    """Parsed combat constants from Effect.java."""

    critical_factor: float = 1.3
    erosion_base: float = 0.05
    erosion_poison: float = 0.10
    erosion_crit_bonus: float = 0.10
    type_poison: int = 13  # TYPE_POISON from Effect.java


# ── Parsers ─────────────────────────────────────────────────────────


_constants_cache: EffectConstants | None = None
_formulas_cache: dict[int, EffectFormula] | None = None


def _parse_effect_java() -> EffectConstants:
    """Parse Effect.java for combat constants."""
    text = _EFFECT_JAVA.read_text()
    c = EffectConstants()

    # CRITICAL_FACTOR = 1.3
    m = re.search(r"CRITICAL_FACTOR\s*=\s*([0-9.]+)", text)
    if m:
        c.critical_factor = float(m.group(1))

    # erosionRate = id == TYPE_POISON ? 0.10 : 0.05
    m = re.search(r"erosionRate\s*=\s*id\s*==\s*TYPE_POISON\s*\?\s*([0-9.]+)\s*:\s*([0-9.]+)", text)
    if m:
        c.erosion_poison = float(m.group(1))
        c.erosion_base = float(m.group(2))

    # if (critical) effect.erosionRate += 0.10
    m = re.search(r"if\s*\(critical\)\s*effect\.erosionRate\s*\+=\s*([0-9.]+)", text)
    if m:
        c.erosion_crit_bonus = float(m.group(1))

    # TYPE_POISON = 13
    m = re.search(r"TYPE_POISON\s*=\s*(\d+)", text)
    if m:
        c.type_poison = int(m.group(1))

    return c


# Mapping: Java getter → stat name
_STAT_GETTERS = {
    "getStrength": "strength",
    "getScience": "science",
    "getMagic": "magic",
    "getResistance": "resistance",
    "getWisdom": "wisdom",
    "getAgility": "agility",
}


def _parse_effect_class(java_file: Path, effect_id: int) -> EffectFormula:
    """Parse a single Effect*.java file for formula metadata.

    Detects which stat scales the formula, whether power/targetCount are used.
    """
    text = java_file.read_text()
    class_name = java_file.stem

    # Find the formula line(s) — typically: value = ... or double d = ...
    # These are in the apply() method
    formula_lines = re.findall(
        r"(?:value|double\s+d)\s*=\s*\(.*?(?:value1|value2).*?;",
        text,
        re.DOTALL,
    )
    formula_text = " ".join(formula_lines) if formula_lines else text

    # Detect primary stat: caster.getXxx()
    primary_stat = None
    max_zero = False
    for getter, stat_name in _STAT_GETTERS.items():
        if f"caster.{getter}()" in formula_text:
            # Skip getPower — that's a separate multiplier, not the primary stat
            if getter == "getAgility" and "getAgility" in formula_text:
                # Agility as primary stat only in EffectDamageReturn
                if class_name == "EffectDamageReturn":
                    primary_stat = stat_name
            else:
                primary_stat = stat_name

            # Check if Math.max(0, ...) wraps this stat
            if re.search(rf"Math\.max\s*\(\s*0\s*,\s*caster\.{getter}", formula_text):
                max_zero = True
            break

    # Detect power multiplier: (1 + caster.getPower() / 100)
    has_power = "caster.getPower()" in formula_text

    # Detect targetCount multiplier
    has_target_count = "targetCount" in formula_text

    return EffectFormula(
        effect_id=effect_id,
        class_name=class_name,
        primary_stat=primary_stat,
        max_zero_stat=max_zero,
        has_power=has_power,
        has_target_count=has_target_count,
    )


def _parse_type_to_class_mapping() -> dict[int, str]:
    """Parse Effect.java's effects[] array to map TYPE_ID → class name.

    The array is 1-indexed: effects[0] = TYPE_1, effects[1] = TYPE_2, etc.
    """
    text = _EFFECT_JAVA.read_text()

    # Extract the effects array contents
    m = re.search(r"effects\s*=\s*\{(.*?)\}", text, re.DOTALL)
    if not m:
        return {}

    entries = m.group(1)
    mapping: dict[int, str] = {}
    for i, line in enumerate(entries.split("\n")):
        line = line.strip().rstrip(",")
        if not line or line.startswith("//"):
            continue
        # Match: EffectDamage.class, // 1
        cm = re.match(r"(\w+)\.class", line)
        if cm:
            # Extract the comment ID if present
            id_m = re.search(r"//\s*(\d+)", line)
            if id_m:
                eid = int(id_m.group(1))
                mapping[eid] = cm.group(1)

    return mapping


def _parse_all_formulas() -> dict[int, EffectFormula]:
    """Parse all Effect*.java files and return metadata per effect ID."""
    type_to_class = _parse_type_to_class_mapping()
    formulas: dict[int, EffectFormula] = {}

    for eid, class_name in type_to_class.items():
        java_file = _EFFECT_DIR / f"{class_name}.java"
        if java_file.exists():
            formulas[eid] = _parse_effect_class(java_file, eid)
        else:
            # Class referenced but file doesn't exist — skip
            formulas[eid] = EffectFormula(effect_id=eid, class_name=class_name)

    return formulas


# ── Public API ──────────────────────────────────────────────────────


def get_constants() -> EffectConstants:
    """Return parsed combat constants (CRITICAL_FACTOR, erosion rates)."""
    global _constants_cache
    if _constants_cache is None:
        _constants_cache = _parse_effect_java()
    return _constants_cache


def get_effect_formulas() -> dict[int, EffectFormula]:
    """Return parsed formula metadata per effect ID."""
    global _formulas_cache
    if _formulas_cache is None:
        _formulas_cache = _parse_all_formulas()
    return _formulas_cache


def get_formula(effect_id: int) -> EffectFormula | None:
    """Get formula metadata for a single effect ID."""
    return get_effect_formulas().get(effect_id)
