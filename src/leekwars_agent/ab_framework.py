"""A/B framework — compare v14 vs v15 on live matchmaking fights.

Three mechanisms:

1. Deploy ledger. Append-only JSONL at data/ab_deploys.jsonl. One line per
   deploy event: {ts, leek_id, variant, ai_file, sha1, note}. The CLI is
   responsible for actually deploying the AI (via `leek ai deploy`) — this
   module only records what happened and when.

2. Scheduler. Given UTC date and a start anchor, returns which variant SHOULD
   be active today. Alternating (even days = control "v14", odd days = "v15").

3. Evaluator. Joins fights_meta.db to the ledger by timestamp: a fight belongs
   to deploy D iff D.ts <= fight.fight_date < next_deploy.ts for the same leek.
   Emits per-arm W-L-D, delta, normal-approx CI on the difference, and a
   sequential stopping decision.

Stopping rule (kept intentionally simple):
  - CI excludes 0 AND n_per_arm >= MIN_PER_ARM -> stop-significant
  - n_per_arm >= MAX_PER_ARM AND CI still straddles 0 -> stop-futile
  - else continue
  - Interim peeks (n < MAX_PER_ARM) use alpha=0.01 to avoid repeated-look
    type-1 inflation; final look at MAX_PER_ARM uses alpha=0.05.
"""

from __future__ import annotations

import hashlib
import json
import math
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

Variant = Literal["v14", "v15"]

DEFAULT_LEDGER = Path("data/ab_deploys.jsonl")
DEFAULT_FIGHTS_DB = Path("data/fights_meta.db")
DEFAULT_MIN_PER_ARM = 100
DEFAULT_MAX_PER_ARM = 500
INTERIM_ALPHA = 0.01
FINAL_ALPHA = 0.05
CONTEXT_MATCHMAKING = 2


@dataclass(frozen=True)
class DeployRecord:
    ts: datetime
    leek_id: int
    variant: Variant
    ai_file: str
    sha1: str
    note: str | None = None

    def to_json_line(self) -> str:
        return json.dumps({
            "ts": self.ts.isoformat(),
            "leek_id": self.leek_id,
            "variant": self.variant,
            "ai_file": self.ai_file,
            "sha1": self.sha1,
            "note": self.note,
        })

    @classmethod
    def from_json_line(cls, line: str) -> "DeployRecord":
        d = json.loads(line)
        return cls(
            ts=datetime.fromisoformat(d["ts"]),
            leek_id=d["leek_id"],
            variant=d["variant"],
            ai_file=d["ai_file"],
            sha1=d["sha1"],
            note=d.get("note"),
        )


def sha1_file(path: Path) -> str:
    return hashlib.sha1(path.read_bytes()).hexdigest()


def append_deploy(
    variant: Variant,
    ai_file: Path,
    leek_id: int,
    note: str | None = None,
    ledger: Path = DEFAULT_LEDGER,
    ts: datetime | None = None,
) -> DeployRecord:
    record = DeployRecord(
        ts=ts or datetime.now(timezone.utc),
        leek_id=leek_id,
        variant=variant,
        ai_file=str(ai_file),
        sha1=sha1_file(ai_file),
        note=note,
    )
    ledger.parent.mkdir(parents=True, exist_ok=True)
    with ledger.open("a") as f:
        f.write(record.to_json_line() + "\n")
    return record


def load_deploys(ledger: Path = DEFAULT_LEDGER) -> list[DeployRecord]:
    if not ledger.exists():
        return []
    records = [
        DeployRecord.from_json_line(line)
        for line in ledger.read_text().splitlines()
        if line.strip()
    ]
    return sorted(records, key=lambda r: r.ts)


def current_variant(leek_id: int, deploys: list[DeployRecord]) -> Variant | None:
    for r in reversed(deploys):
        if r.leek_id == leek_id:
            return r.variant
    return None


def schedule_today(
    leek_id: int,  # reserved for future per-leek schedules
    today: datetime | None = None,
    start_date: datetime | None = None,
) -> Variant:
    """Alternating schedule. Even days from start_date -> v14 (control)."""
    now = today or datetime.now(timezone.utc)
    anchor = start_date or datetime(2026, 4, 21, tzinfo=timezone.utc)
    days = (now.date() - anchor.date()).days
    return "v14" if days % 2 == 0 else "v15"


@dataclass(frozen=True)
class FightAttribution:
    fight_id: int
    fight_date: int
    leek_id: int
    variant: Variant
    won: bool
    draw: bool


def attribute_fights(
    leek_id: int,
    deploys: list[DeployRecord],
    fights_db: Path = DEFAULT_FIGHTS_DB,
    context: int = CONTEXT_MATCHMAKING,
) -> list[FightAttribution]:
    leek_deploys = [d for d in deploys if d.leek_id == leek_id]
    if not leek_deploys:
        return []
    start_ts = int(leek_deploys[0].ts.timestamp())

    conn = sqlite3.connect(fights_db)
    try:
        rows = conn.execute(
            """
            SELECT f.fight_id, f.fight_date, f.winner, lo.won
            FROM fights f
            JOIN leek_observations lo ON lo.fight_id = f.fight_id
            WHERE lo.leek_id = ? AND f.context = ? AND f.fight_date >= ?
            ORDER BY f.fight_date ASC
            """,
            (leek_id, context, start_ts),
        ).fetchall()
    finally:
        conn.close()

    boundaries = [(int(d.ts.timestamp()), d.variant) for d in leek_deploys]
    out: list[FightAttribution] = []
    for fight_id, fight_date, winner, won in rows:
        variant: Variant | None = None
        for b_ts, b_var in reversed(boundaries):
            if b_ts <= fight_date:
                variant = b_var
                break
        if variant is None:
            continue
        out.append(FightAttribution(
            fight_id=fight_id,
            fight_date=fight_date,
            leek_id=leek_id,
            variant=variant,
            won=bool(won),
            draw=(winner == 0),
        ))
    return out


@dataclass(frozen=True)
class ArmStats:
    variant: Variant
    n: int
    wins: int
    losses: int
    draws: int

    @property
    def decisive(self) -> int:
        return self.wins + self.losses

    @property
    def wr(self) -> float:
        return self.wins / self.decisive if self.decisive else 0.0


@dataclass(frozen=True)
class ABResult:
    v14: ArmStats
    v15: ArmStats
    delta: float
    ci_low: float
    ci_high: float
    alpha: float
    decision: Literal["stop-significant", "stop-futile", "continue"]
    n_per_arm: int


def _inv_cdf_normal(p: float) -> float:
    """Beasley-Springer-Moro approximation for standard normal inverse CDF."""
    a = [-3.969683028665376e+01, 2.209460984245205e+02,
         -2.759285104469687e+02, 1.383577518672690e+02,
         -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02,
         -1.556989798598866e+02, 6.680131188771972e+01,
         -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01,
         -2.400758277161838e+00, -2.549732539343734e+00,
         4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01,
         2.445134137142996e+00, 3.754408661907416e+00]
    plow = 0.02425
    phigh = 1 - plow
    if p < plow:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
               ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    if p <= phigh:
        q = p - 0.5
        r = q*q
        return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / \
               (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)
    q = math.sqrt(-2 * math.log(1 - p))
    return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
            ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)


def _wr_diff_ci(p1: float, n1: int, p2: float, n2: int, alpha: float) -> tuple[float, float]:
    if n1 == 0 or n2 == 0:
        return (-1.0, 1.0)
    delta = p2 - p1
    se = math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    z = _inv_cdf_normal(1 - alpha / 2)
    return (delta - z * se, delta + z * se)


def evaluate(
    attributions: list[FightAttribution],
    min_per_arm: int = DEFAULT_MIN_PER_ARM,
    max_per_arm: int = DEFAULT_MAX_PER_ARM,
    final_alpha: float = FINAL_ALPHA,
    interim_alpha: float = INTERIM_ALPHA,
) -> ABResult:
    def build(variant: Variant) -> ArmStats:
        sub = [a for a in attributions if a.variant == variant]
        wins = sum(1 for a in sub if a.won and not a.draw)
        draws = sum(1 for a in sub if a.draw)
        losses = len(sub) - wins - draws
        return ArmStats(variant=variant, n=len(sub), wins=wins, losses=losses, draws=draws)

    v14 = build("v14")
    v15 = build("v15")
    n = min(v14.decisive, v15.decisive)
    use_alpha = final_alpha if n >= max_per_arm else interim_alpha
    delta = v15.wr - v14.wr
    lo, hi = _wr_diff_ci(v14.wr, v14.decisive, v15.wr, v15.decisive, use_alpha)

    decision: Literal["stop-significant", "stop-futile", "continue"]
    if n >= min_per_arm and (lo > 0 or hi < 0):
        decision = "stop-significant"
    elif n >= max_per_arm:
        decision = "stop-futile"
    else:
        decision = "continue"

    return ABResult(
        v14=v14, v15=v15,
        delta=delta, ci_low=lo, ci_high=hi, alpha=use_alpha,
        decision=decision, n_per_arm=n,
    )


def render_markdown(result: ABResult, leek_id: int | None = None) -> str:
    def fmt_arm(a: ArmStats) -> str:
        return (f"- **{a.variant}**: {a.wins}W-{a.losses}L-{a.draws}D  "
                f"(n={a.n}, decisive={a.decisive}, WR={a.wr*100:.1f}%)")
    header = f"# A/B Evaluation"
    if leek_id is not None:
        header += f" — leek {leek_id}"
    return "\n".join([
        header,
        "",
        fmt_arm(result.v14),
        fmt_arm(result.v15),
        "",
        f"Δ (v15 − v14): **{result.delta*100:+.2f}pp**",
        f"CI @ α={result.alpha:.2f}: [{result.ci_low*100:+.2f}pp, {result.ci_high*100:+.2f}pp]",
        f"n_per_arm: {result.n_per_arm}",
        "",
        f"**Decision**: `{result.decision}`",
    ])
