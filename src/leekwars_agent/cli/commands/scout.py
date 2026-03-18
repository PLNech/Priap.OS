"""Scout command — live recon of any leek's build."""

import click
from ..output import output_json, console, error
from leekwars_agent.auth import login_api
from leekwars_agent.scout import scout_leek, scout_batch


@click.group()
def scout():
    """Scout any leek's build from their recent fights.

    Fetches fight replays to reverse-engineer stats, chips, and weapons.

    Examples:
        leek scout leek 132055              # Scout PigDestoryer
        leek scout batch 132055 1971 2040   # Scout multiple leeks
    """
    pass


@scout.command("leek")
@click.argument("leek_id", type=int)
@click.option("-n", "--fights", type=int, default=5, help="Fights to analyze (default 5)")
@click.pass_context
def scout_one(ctx: click.Context, leek_id: int, fights: int) -> None:
    """Scout a single leek's build.

    Examples:
        leek scout leek 132055          # PigDestoryer
        leek scout leek 132055 -n 3     # Fewer fights (faster)
    """
    api = login_api()
    try:
        build = scout_leek(api, leek_id, max_fights=fights)

        if ctx.obj.get("json"):
            output_json(build.to_dict())
            return

        _print_build(build)

    finally:
        api.close()


@scout.command("batch")
@click.argument("leek_ids", nargs=-1, type=int, required=True)
@click.option("-n", "--fights", type=int, default=3, help="Fights per leek (default 3)")
@click.pass_context
def scout_many(ctx: click.Context, leek_ids: tuple[int, ...], fights: int) -> None:
    """Scout multiple leeks at once.

    Examples:
        leek scout batch 132055 1971 2040
        leek --json scout batch 132055 1971
    """
    api = login_api()
    try:
        builds = scout_batch(api, list(leek_ids), max_fights=fights)

        if ctx.obj.get("json"):
            output_json([b.to_dict() for b in builds])
            return

        for build in builds:
            _print_build(build)
            console.print()

    finally:
        api.close()


def _print_build(build) -> None:
    """Pretty-print a LeekBuild."""
    console.print(f"\n[bold cyan]═══ {build.name} ═══[/bold cyan]")
    console.print(f"  L{build.level} | T{build.talent} | {build.recent_wr}")

    if build.fights_analyzed == 0:
        error("No fight data found")
        return

    # Stats table
    console.print(f"\n  [bold]Stats[/bold]")
    console.print(f"    HP  [green]{build.life:<6}[/green]  TP  [cyan]{build.tp}[/cyan]  MP  [cyan]{build.mp}[/cyan]")
    console.print(f"    STR [yellow]{build.strength:<6}[/yellow]  RES [red]{build.resistance}[/red]")
    console.print(f"    AGI {build.agility:<6}  WIS {build.wisdom}")
    if build.science or build.magic:
        console.print(f"    SCI {build.science:<6}  MAG {build.magic}")
    console.print(f"    FRQ {build.frequency}")

    # Equipment
    if build.chips:
        console.print(f"\n  [bold]Chips[/bold] ({len(build.chips)})")
        for c in build.chips:
            console.print(f"    • {c}")

    if build.weapons:
        console.print(f"\n  [bold]Weapons[/bold] ({len(build.weapons)})")
        for w in build.weapons:
            console.print(f"    • {w}")

    if build.uses_summons:
        console.print(f"\n  [magenta]⚠ Uses summons[/magenta]")

    console.print(f"\n  [dim]({build.fights_analyzed} fights analyzed)[/dim]")
