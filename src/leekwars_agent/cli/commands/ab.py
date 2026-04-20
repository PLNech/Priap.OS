"""A/B test framework CLI — compare v14 vs v15 on live matchmaking fights."""

from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import click

from ..constants import LEEK_ID
from ..output import console, output_json
from ... import ab_framework as ab


# Default AI files per variant. Override via --ai-file on deploy.
VARIANT_FILES = {
    "v14": Path("ais/fighter_v14_flat.leek"),
    "v15": Path("ais/fighter_v15_flat.leek"),
}


@click.group("ab")
def ab_cli() -> None:
    """Real v14 vs v15 A/B test framework.

    Commands:
      status     — current active variant + cumulative stats
      schedule   — which variant should run today (alternating)
      deploy     — deploy a variant and record in the ledger
      evaluate   — compute per-arm W-L-D, CI, stop decision
    """


@ab_cli.command("status")
@click.option("--leek-id", type=int, default=LEEK_ID)
@click.option("--ledger", type=click.Path(), default=str(ab.DEFAULT_LEDGER))
@click.option("--fights-db", type=click.Path(), default=str(ab.DEFAULT_FIGHTS_DB))
@click.pass_context
def status(ctx: click.Context, leek_id: int, ledger: str, fights_db: str) -> None:
    """Show current deploy and running per-arm totals."""
    deploys = ab.load_deploys(Path(ledger))
    current = ab.current_variant(leek_id, deploys)
    latest = next((r for r in reversed(deploys) if r.leek_id == leek_id), None)
    atts = ab.attribute_fights(leek_id, deploys, fights_db=Path(fights_db))
    result = ab.evaluate(atts)

    if ctx.obj.get("json"):
        output_json({
            "leek_id": leek_id,
            "current_variant": current,
            "latest_deploy": {
                "ts": latest.ts.isoformat(),
                "variant": latest.variant,
                "ai_file": latest.ai_file,
                "sha1": latest.sha1,
            } if latest else None,
            "v14": {"n": result.v14.n, "w": result.v14.wins,
                    "l": result.v14.losses, "d": result.v14.draws,
                    "wr": result.v14.wr},
            "v15": {"n": result.v15.n, "w": result.v15.wins,
                    "l": result.v15.losses, "d": result.v15.draws,
                    "wr": result.v15.wr},
            "delta": result.delta, "ci_low": result.ci_low, "ci_high": result.ci_high,
            "n_per_arm": result.n_per_arm, "decision": result.decision,
        })
        return

    console.print(f"[bold]A/B Status — leek {leek_id}[/bold]")
    if current is None:
        console.print("  No deploys recorded yet.")
    else:
        console.print(f"  Current variant: [bold]{current}[/bold]")
        assert latest is not None
        console.print(f"  Last deploy: {latest.ts.isoformat()} "
                      f"(sha1={latest.sha1[:10]})")
    console.print()
    console.print(f"  v14: {result.v14.wins}W-{result.v14.losses}L-{result.v14.draws}D "
                  f"(n={result.v14.n}, WR={result.v14.wr*100:.1f}%)")
    console.print(f"  v15: {result.v15.wins}W-{result.v15.losses}L-{result.v15.draws}D "
                  f"(n={result.v15.n}, WR={result.v15.wr*100:.1f}%)")
    console.print(f"  Δ: {result.delta*100:+.2f}pp  "
                  f"[CI @ α={result.alpha}: {result.ci_low*100:+.2f}..{result.ci_high*100:+.2f}pp]")
    console.print(f"  Decision: [bold]{result.decision}[/bold] "
                  f"(n_per_arm={result.n_per_arm})")


@ab_cli.command("schedule")
@click.option("--leek-id", type=int, default=LEEK_ID)
@click.option("--today", default=None, help="ISO date for planning (default: today UTC)")
@click.pass_context
def schedule_cmd(ctx: click.Context, leek_id: int, today: str | None) -> None:
    """Print which variant SHOULD be active today. Does not deploy."""
    now = datetime.fromisoformat(today) if today else None
    if now is not None and now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    target = ab.schedule_today(leek_id, today=now)

    if ctx.obj.get("json"):
        output_json({"leek_id": leek_id, "target_variant": target,
                     "as_of": (now or datetime.now(timezone.utc)).isoformat()})
        return
    console.print(f"Leek {leek_id} — today should run: [bold]{target}[/bold]")


@ab_cli.command("deploy")
@click.argument("variant", type=click.Choice(["v14", "v15"]))
@click.option("--leek-id", type=int, default=LEEK_ID)
@click.option("--ai-file", type=click.Path(exists=True), default=None,
              help="Override the AI file for this variant")
@click.option("--ledger", type=click.Path(), default=str(ab.DEFAULT_LEDGER))
@click.option("--note", default=None, help="Free-text note for this deploy")
@click.option("--apply", is_flag=True,
              help="Actually run `leek ai deploy` and append to ledger. Without this flag, "
                   "only prints what would happen (dry-run).")
@click.pass_context
def deploy(ctx: click.Context, variant: str, leek_id: int, ai_file: str | None,
           ledger: str, note: str | None, apply: bool) -> None:
    """Deploy a variant and append a record to the ledger.

    Without --apply, runs as a dry-run. With --apply, invokes
    `leek ai deploy <file>` and then appends the ledger line.
    """
    path = Path(ai_file) if ai_file else VARIANT_FILES[variant]
    if not path.exists():
        raise click.ClickException(f"AI file not found: {path}")

    console.print(f"[bold]A/B deploy[/bold] — variant={variant} leek={leek_id}")
    console.print(f"  File: {path}")
    console.print(f"  Sha1: {ab.sha1_file(path)[:10]}")

    if not apply:
        console.print("[yellow]Dry-run. Pass --apply to actually deploy + record.[/yellow]")
        return

    # Defer to existing `leek ai deploy` via subprocess. Clean separation:
    # deploy succeeds -> append ledger; deploy fails -> bail, no ledger entry.
    result = subprocess.run(
        ["leek", "ai", "deploy", str(path)],
        capture_output=True, text=True,
    )
    sys.stdout.write(result.stdout)
    sys.stderr.write(result.stderr)
    if result.returncode != 0:
        raise click.ClickException(f"leek ai deploy failed (rc={result.returncode})")

    rec = ab.append_deploy(
        variant=variant, ai_file=path, leek_id=leek_id,
        note=note, ledger=Path(ledger),
    )
    console.print(f"[green]✓ Recorded deploy[/green] at {rec.ts.isoformat()}")


@ab_cli.command("evaluate")
@click.option("--leek-id", type=int, default=LEEK_ID)
@click.option("--ledger", type=click.Path(), default=str(ab.DEFAULT_LEDGER))
@click.option("--fights-db", type=click.Path(), default=str(ab.DEFAULT_FIGHTS_DB))
@click.option("--write", "out_path", type=click.Path(), default=None,
              help="Write markdown report to this path")
@click.option("--min-per-arm", type=int, default=ab.DEFAULT_MIN_PER_ARM)
@click.option("--max-per-arm", type=int, default=ab.DEFAULT_MAX_PER_ARM)
@click.pass_context
def evaluate_cmd(ctx: click.Context, leek_id: int, ledger: str, fights_db: str,
                 out_path: str | None, min_per_arm: int, max_per_arm: int) -> None:
    """Compute per-arm W-L-D, CI, and stopping decision."""
    deploys = ab.load_deploys(Path(ledger))
    atts = ab.attribute_fights(leek_id, deploys, fights_db=Path(fights_db))
    result = ab.evaluate(atts, min_per_arm=min_per_arm, max_per_arm=max_per_arm)

    md = ab.render_markdown(result, leek_id=leek_id)

    if ctx.obj.get("json"):
        output_json({
            "leek_id": leek_id,
            "v14": {"n": result.v14.n, "w": result.v14.wins,
                    "l": result.v14.losses, "d": result.v14.draws,
                    "wr": result.v14.wr},
            "v15": {"n": result.v15.n, "w": result.v15.wins,
                    "l": result.v15.losses, "d": result.v15.draws,
                    "wr": result.v15.wr},
            "delta": result.delta,
            "ci_low": result.ci_low, "ci_high": result.ci_high, "alpha": result.alpha,
            "n_per_arm": result.n_per_arm, "decision": result.decision,
        })
        return

    console.print(md)
    if out_path:
        p = Path(out_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(md + "\n")
        console.print(f"\n[green]Wrote[/green] {out_path}")
