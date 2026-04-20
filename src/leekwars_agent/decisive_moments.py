"""Decisive-moment detector for fight action logs (#0311).

v1 implements HP crossover — the turn where the eventual winner's HP ratio
first surpassed the eventual loser's, and stayed there. This is the moment
momentum flipped. More moment types (shield_depletion, tp_shackle,
range_lock, chip_exhaustion) can be layered on top of the same HP-ratio
trace.

Scope: 1v1 fights only (exactly 2 non-summon entities, one per team).
Multi-entity / BR fights are out of scope for v1 — their decisive-moment
semantics differ enough to warrant separate handling.

Storage: table `decisive_moments` in data/fights_meta.db, keyed on
(fight_id, turn, moment_type). Idempotent inserts via INSERT OR REPLACE.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .fight_parser import ActionType


DEFAULT_FIGHTS_DB = Path("data/fights_meta.db")

# Action codes that reduce HP.
_DAMAGE_CODES = {
    int(ActionType.LOST_LIFE),      # 101
    int(ActionType.NOVA_DAMAGE),    # 107
    int(ActionType.DAMAGE_RETURN),  # 108
    int(ActionType.LIFE_DAMAGE),    # 109
    int(ActionType.POISON_DAMAGE),  # 110
    int(ActionType.AFTEREFFECT),    # 111
}
# Action codes that restore HP.
_HEAL_CODES = {
    int(ActionType.HEAL),           # 103
    int(ActionType.VITALITY),       # 104
    int(ActionType.NOVA_VITALITY),  # 112
}


@dataclass(frozen=True)
class HPTrace:
    """Turn-by-turn HP for each entity in a 1v1 fight."""
    # entity_id -> list of (turn, hp) snapshots, end-of-turn ordered
    per_entity: dict[int, list[tuple[int, int]]]
    initial_hp: dict[int, int]
    winner_entity: int | None  # None if draw or cancelled


@dataclass(frozen=True)
class DecisiveMoment:
    fight_id: int
    turn: int
    moment_type: str
    actor: int | None        # entity_id responsible (or beneficiary)
    victim: int | None        # entity_id affected
    details: dict[str, object] = field(default_factory=dict)


def _extract_1v1_entities(data: dict) -> tuple[int, int, int, int] | None:
    """Return (entity_a, team_a, entity_b, team_b) for a 1v1, else None."""
    entities = [e for e in data.get("leeks", []) if not e.get("summon")]
    if len(entities) != 2:
        return None
    a, b = entities
    if a.get("team") == b.get("team"):
        return None
    return (a["id"], a["team"], b["id"], b["team"])


def build_hp_trace(fight_json: dict) -> HPTrace | None:
    """Replay the action log to reconstruct per-turn HP.

    Returns None if the fight is not a 1v1 or lacks required data.
    """
    fight = fight_json.get("fight", fight_json)
    data = fight.get("data", {})
    entity_info = _extract_1v1_entities(data)
    if entity_info is None:
        return None
    eid_a, team_a, eid_b, team_b = entity_info

    initial_hp: dict[int, int] = {}
    for entity in data.get("leeks", []):
        if entity.get("summon"):
            continue
        eid = entity.get("id")
        life = entity.get("life")
        if eid is not None and life is not None:
            initial_hp[eid] = int(life)
    if eid_a not in initial_hp or eid_b not in initial_hp:
        return None

    current_hp = dict(initial_hp)
    per_entity: dict[int, list[tuple[int, int]]] = {eid_a: [], eid_b: []}
    turn_num = 0
    saw_turn = False

    for raw in data.get("actions", []):
        if not raw:
            continue
        code = raw[0]
        if code == int(ActionType.NEW_TURN):
            # Snapshot end-of-previous-turn HP before moving on
            if saw_turn:
                for eid in per_entity:
                    per_entity[eid].append((turn_num, current_hp[eid]))
            turn_num = raw[1] if len(raw) > 1 else turn_num + 1
            saw_turn = True
        elif code in _DAMAGE_CODES:
            target = raw[1] if len(raw) > 1 else None
            amount = raw[2] if len(raw) > 2 else 0
            if target in current_hp and isinstance(amount, (int, float)):
                current_hp[target] = max(0, current_hp[target] - int(amount))
        elif code in _HEAL_CODES:
            target = raw[1] if len(raw) > 1 else None
            amount = raw[2] if len(raw) > 2 else 0
            if target in current_hp and isinstance(amount, (int, float)):
                # No explicit HP cap in the log; trust snapshots over-time
                current_hp[target] = current_hp[target] + int(amount)

    # Trailing snapshot after last action
    if saw_turn:
        for eid in per_entity:
            per_entity[eid].append((turn_num, current_hp[eid]))

    # Winner entity: the one still alive (hp > 0). Draw -> None.
    winner_team = fight.get("winner")
    winner_entity: int | None = None
    if winner_team == team_a:
        winner_entity = eid_a
    elif winner_team == team_b:
        winner_entity = eid_b
    return HPTrace(
        per_entity=per_entity,
        initial_hp=initial_hp,
        winner_entity=winner_entity,
    )


def detect_hp_crossover(
    fight_id: int, trace: HPTrace
) -> DecisiveMoment | None:
    """Identify the turn where the eventual winner first led on HP% and held.

    Algorithm:
      1. Compute per-turn HP ratios for winner and loser.
      2. A crossover is the first turn t where winner_ratio > loser_ratio,
         with the lead never reversed afterwards, AND the eventual loser
         was strictly ahead at some prior turn.
      3. If the loser was never strictly ahead (wire-to-wire win or
         permanent tie until first damage), return None.

    A winner that was never behind did not experience a momentum flip.
    """
    if trace.winner_entity is None:
        return None
    winner = trace.winner_entity
    loser = next(eid for eid in trace.per_entity if eid != winner)

    winner_series = trace.per_entity[winner]
    loser_series = trace.per_entity[loser]
    w_max = trace.initial_hp[winner] or 1
    l_max = trace.initial_hp[loser] or 1

    by_turn: dict[int, tuple[int, int]] = {}
    for t, hp in winner_series:
        by_turn[t] = (hp, by_turn.get(t, (None, None))[1] or 0)
    for t, hp in loser_series:
        existing = by_turn.get(t, (0, None))
        by_turn[t] = (existing[0] if existing[0] is not None else 0, hp)
    if not by_turn:
        return None
    sorted_turns = sorted(by_turn)

    winner_leads: list[bool] = []
    loser_leads: list[bool] = []
    for t in sorted_turns:
        w_hp, l_hp = by_turn[t]
        if w_hp is None or l_hp is None:
            winner_leads.append(False)
            loser_leads.append(False)
            continue
        w_r = w_hp / w_max
        l_r = l_hp / l_max
        winner_leads.append(w_r > l_r)
        loser_leads.append(l_r > w_r)

    try:
        first_winner_lead = winner_leads.index(True)
    except ValueError:
        return None

    # Must have had a prior turn where the loser was strictly ahead
    if not any(loser_leads[:first_winner_lead]):
        return None

    # Verify the lead holds (no reversal after the crossover)
    if not all(winner_leads[first_winner_lead:]):
        return None

    crossover_turn = sorted_turns[first_winner_lead]
    w_hp, l_hp = by_turn[crossover_turn]
    return DecisiveMoment(
        fight_id=fight_id,
        turn=crossover_turn,
        moment_type="hp_crossover",
        actor=winner,
        victim=loser,
        details={
            "winner_hp": w_hp, "winner_hp_max": w_max,
            "loser_hp": l_hp, "loser_hp_max": l_max,
            "winner_ratio": w_hp / w_max,
            "loser_ratio": l_hp / l_max,
        },
    )


def detect_moments(fight_id: int, fight_json: dict) -> list[DecisiveMoment]:
    """Run all v1 detectors on a fight. Returns flat list of moments."""
    trace = build_hp_trace(fight_json)
    if trace is None:
        return []
    moments: list[DecisiveMoment] = []
    crossover = detect_hp_crossover(fight_id, trace)
    if crossover is not None:
        moments.append(crossover)
    return moments


# ---------- Storage --------------------------------------------------------

_SCHEMA = """
CREATE TABLE IF NOT EXISTS decisive_moments (
    fight_id INTEGER NOT NULL,
    turn INTEGER NOT NULL,
    moment_type TEXT NOT NULL,
    actor INTEGER,
    victim INTEGER,
    details TEXT,
    computed_at TEXT NOT NULL,
    PRIMARY KEY (fight_id, turn, moment_type)
);
CREATE INDEX IF NOT EXISTS idx_moments_fight ON decisive_moments(fight_id);
CREATE INDEX IF NOT EXISTS idx_moments_type ON decisive_moments(moment_type);
"""


def ensure_schema(db: Path = DEFAULT_FIGHTS_DB) -> None:
    conn = sqlite3.connect(db)
    try:
        conn.executescript(_SCHEMA)
        conn.commit()
    finally:
        conn.close()


def save_moments(
    moments: Iterable[DecisiveMoment],
    db: Path = DEFAULT_FIGHTS_DB,
) -> int:
    ensure_schema(db)
    now = datetime.now(timezone.utc).isoformat()
    rows = [
        (m.fight_id, m.turn, m.moment_type, m.actor, m.victim,
         json.dumps(m.details), now)
        for m in moments
    ]
    if not rows:
        return 0
    conn = sqlite3.connect(db)
    try:
        conn.executemany(
            "INSERT OR REPLACE INTO decisive_moments "
            "(fight_id, turn, moment_type, actor, victim, details, computed_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            rows,
        )
        conn.commit()
        return len(rows)
    finally:
        conn.close()


def iter_candidate_fights(
    db: Path = DEFAULT_FIGHTS_DB,
    context: int = 2,
    limit: int | None = None,
    only_fight_type: int | None = 0,  # solo
) -> Iterable[tuple[int, dict]]:
    """Yield (fight_id, fight_json) for fights matching the filter.

    Default: solo matchmaking fights. fight_json is parsed from json_data.
    """
    conn = sqlite3.connect(db)
    try:
        sql = "SELECT fight_id, json_data FROM fights WHERE context = ?"
        params: list[object] = [context]
        if only_fight_type is not None:
            sql += " AND fight_type = ?"
            params.append(only_fight_type)
        sql += " ORDER BY fight_date DESC"
        if limit is not None:
            sql += " LIMIT ?"
            params.append(limit)
        for fight_id, json_data in conn.execute(sql, params):
            try:
                yield fight_id, json.loads(json_data)
            except json.JSONDecodeError:
                continue
    finally:
        conn.close()


def scan_and_save(
    db: Path = DEFAULT_FIGHTS_DB,
    context: int = 2,
    limit: int | None = None,
) -> dict[str, int]:
    """Scan fights, detect moments, and persist. Returns summary counts."""
    ensure_schema(db)
    total = 0
    fights_with_moments = 0
    fights_scanned = 0
    per_type: dict[str, int] = {}
    batch: list[DecisiveMoment] = []
    BATCH_SIZE = 200

    for fight_id, fight_json in iter_candidate_fights(db, context=context, limit=limit):
        fights_scanned += 1
        moments = detect_moments(fight_id, fight_json)
        if moments:
            fights_with_moments += 1
            for m in moments:
                per_type[m.moment_type] = per_type.get(m.moment_type, 0) + 1
            batch.extend(moments)
            total += len(moments)
            if len(batch) >= BATCH_SIZE:
                save_moments(batch, db)
                batch = []

    if batch:
        save_moments(batch, db)

    return {
        "fights_scanned": fights_scanned,
        "fights_with_moments": fights_with_moments,
        "moments_saved": total,
        **{f"type_{t}": n for t, n in per_type.items()},
    }
