"""Battle Royale commands - free fights via WebSocket."""

import click
from ..output import output_json, success, error, warning, console
from leekwars_agent.auth import login_api
from leekwars_agent.battle_royale import BattleRoyaleClient, run_full_br_session


@click.group()
def br():
    """Battle Royale automation - free fights!

    Battle Royale is a free-for-all mode with 10 leeks.
    10 free fights/day = faster leveling without using fight budget.

    Examples:
        leek br status              # Check if BR is available
        leek br join                # Join and wait for a BR to start
    """
    pass


@br.command("status")
@click.option("--db", type=str, default="data/fights_meta.db", help="Database path")
@click.pass_context
def br_status(ctx: click.Context, db: str) -> None:
    """Check if Battle Royale is available.

    Shows:
    - Whether BR is enabled on the server
    - Your leek's level (must be >= 20)
    - Your farmer's verification and BR status
    - Overall readiness

    Examples:
        leek br status              # Full status
    """
    api = login_api()

    try:
        client = BattleRoyaleClient(api)
        status = client.status()

        if ctx.obj.get("json"):
            output_json(status)
            return

        console.print("[bold]Battle Royale Status[/bold]\n")

        # Server status
        if status["enabled"]:
            console.print("  Server: [green]ENABLED[/green]")
        else:
            console.print("  Server: [red]DISABLED[/red]")

        # Leek status
        level = status["leek_level"]
        if level >= 20:
            console.print(f"  Leek: [green]L{level}[/green] (meets L20 requirement)")
        else:
            console.print(f"  Leek: [red]L{level}[/red] (needs L20)")

        # Farmer status
        if status["farmer_verified"]:
            console.print("  Farmer: [green]Verified[/green]")
        else:
            console.print("  Farmer: [yellow]Not verified[/yellow]")

        if status["farmer_br_enabled"]:
            console.print("  Farmer BR: [green]Enabled[/green]")
        else:
            console.print("  Farmer BR: [red]Disabled[/red]")

        console.print()

        # Overall
        if status["ready"]:
            console.print("[green]✓ Ready to join Battle Royale![/green]")
            console.print("  Run: [cyan]leek br join[/cyan]")
        else:
            reasons = []
            if not status["enabled"]:
                reasons.append("BR disabled on server")
            if not status["leek_level_ok"]:
                reasons.append(f"Leek L{level} < 20")
            if not status["farmer_verified"]:
                reasons.append("Farmer not verified")
            if not status["farmer_br_enabled"]:
                reasons.append("BR disabled for farmer")

            console.print("[red]✗ Cannot join[/red]")
            for reason in reasons:
                console.print(f"  - {reason}")

    finally:
        api.close()


@br.command("join")
@click.argument("leek_id", type=int, default=None)
@click.option("--timeout", "-t", type=float, default=60.0, help="Max seconds to wait for BR to start")
@click.option("--get-result/--no-get-result", default=True, help="Get fight result after BR starts")
@click.pass_context
def br_join(ctx: click.Context, leek_id: int | None, timeout: float, get_result: bool) -> None:
    """Join a Battle Royale and wait for it to start.

    Blocks until the Battle Royale begins, then returns the fight ID.
    Use --no-get-result for fire-and-forget mode.

    Args:
        leek_id: Leek ID to use (defaults to your main leek)

    Examples:
        leek br join                       # Join with default leek
        leek br join 131321               # Specific leek
        leek br join -t 120               # Wait up to 2 minutes
    """
    api = login_api()

    # Use default leek if not specified
    if leek_id is None:
        from leekwars_agent.cli.constants import LEEK_ID
        leek_id = LEEK_ID

    def progress(msg: str):
        console.print(f"  [dim]{msg}[/dim]")

    try:
        console.print(f"[bold]Battle Royale[/bold] - Leek {leek_id}")

        # Run full session
        result = run_full_br_session(
            api=api,
            leek_id=leek_id,
            timeout=timeout,
            progress_callback=progress,
        )

        if ctx.obj.get("json"):
            output_json(result)
            return

        if result["success"]:
            success(f"Fight started: [cyan]{result['fight_id']}[/cyan]")

            if get_result and result["fight_result"]:
                fr = result["fight_result"]
                winner = fr.get("winner")
                duration = fr.get("duration")
                console.print(f"  Winner: {winner}")
                if duration:
                    console.print(f"  Duration: {duration} turns")

            console.print("\n  Run [cyan]leek fight history[/cyan] to see results")
        else:
            error(f"Failed: {result['error']}")

    finally:
        api.close()


@br.command("run")
@click.argument("leek_id", type=int, default=None)
@click.option("--count", "-n", type=int, default=5, help="Number of BRs to run")
@click.option("--delay", "-d", type=float, default=5.0, help="Seconds between BRs")
@click.option("--timeout", "-t", type=float, default=60.0, help="Max seconds per BR")
@click.pass_context
def br_run(ctx: click.Context, leek_id: int | None, count: int, delay: float, timeout: float) -> None:
    """Run multiple Battle Royales in sequence.

    Args:
        leek_id: Leek ID to use (defaults to main leek)
        count: Number of BRs to run
        delay: Seconds between each BR
        timeout: Max seconds to wait for each BR to start

    Examples:
        leek br run -n 10           # Run 10 BRs
        leek br run -n 5 --delay 10  # Slower pace
    """
    api = login_api()

    if leek_id is None:
        from leekwars_agent.cli.constants import LEEK_ID
        leek_id = LEEK_ID

    try:
        console.print(f"[bold]Battle Royale Batch[/bold] - {count} fights, Leek {leek_id}\n")

        wins = 0
        losses = 0
        errors = 0
        started = 0

        for i in range(count):
            console.print(f"[{i+1}/{count}] ", end="")

            result = run_full_br_session(
                api=api,
                leek_id=leek_id,
                timeout=timeout,
                progress_callback=lambda m: console.print(f"  [dim]{m}[/dim]", end=" "),
            )

            if result["success"]:
                started += 1
                console.print(f"[green]Started[/green] (fight {result['fight_id']})")
            else:
                errors += 1
                console.print(f"[red]Failed[/red]: {result['error']}")

            if i < count - 1 and delay > 0:
                time.sleep(delay)

        console.print(f"\n[bold]Summary:[/bold] {started} started, {errors} errors")

    finally:
        api.close()