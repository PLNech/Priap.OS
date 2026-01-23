"""LeekWars CLI - main entry point."""

import click
from .commands import info, craft, fight, market, ai, build, sim, trophy, test
from .output import console
from .constants import LEEK_ID
from leekwars_agent.auth import login_api


@click.group()
@click.option("--json", "json_output", is_flag=True, help="Output as JSON (for automation)")
@click.version_option(version="0.2.0", prog_name="leek")
@click.pass_context
def cli(ctx: click.Context, json_output: bool) -> None:
    """LeekWars CLI - fight, craft, and manage your leek.

    Use --json flag with any command for machine-readable output.

    Examples:

        leek status                       # Quick overview of everything

        leek info leek                    # Show your leek's stats

        leek build show                   # View stat allocation
        leek build spend str 50           # Spend 50 capital on STR

        leek ai deploy ais/fighter_v10.leek  # Deploy an AI

        leek market list                  # Browse items
        leek market buy 45                # Buy weapon_magnum

        leek fight run -n 5               # Run 5 fights
    """
    ctx.ensure_object(dict)
    ctx.obj["json"] = json_output


@cli.command()
@click.pass_context
def status(ctx: click.Context) -> None:
    """Quick status overview - fights, habs, capital, AI."""
    api = login_api()
    try:
        # Get all data in parallel (well, sequentially but fast)
        leek_data = api.get_leek(LEEK_ID)
        garden_data = api.get_garden()
        inv = api.get_inventory()

        leek = leek_data.get("leek", leek_data)
        garden = garden_data.get("garden", garden_data)

        # Extract key info
        level = leek.get("level", 1)
        talent = leek.get("talent", 0)
        capital = leek.get("capital", 0)
        strength = leek.get("strength", 0)
        agility = leek.get("agility", 0)

        habs = inv.get("habs", 0)

        solo_fights = garden.get("solo_fights", [])
        total_solo = garden.get("total_solo_fights", 0)
        max_solo = garden.get("max_solo_fights", 30)

        ai_info = leek.get("ai", {})
        ai_name = ai_info.get("name", "None")

        chips_equipped = len(leek.get("chips", []))
        weapons_equipped = len(leek.get("weapons", []))

        # Recent fight results
        fights = leek.get("fights", [])[:5]
        results = [f.get("result", "?")[0].upper() for f in fights]  # W/L/D
        recent = "".join(results) if results else "N/A"

        if ctx.obj.get("json"):
            from .output import output_json
            output_json({
                "level": level,
                "talent": talent,
                "capital": capital,
                "habs": habs,
                "fights_remaining": max_solo - total_solo,
                "ai": ai_name,
                "recent": recent,
            })
            return

        # Pretty output
        console.print("[bold cyan]═══ PriapOS Status ═══[/bold cyan]\n")

        # Fights
        remaining = max_solo - total_solo
        fight_color = "green" if remaining > 0 else "red"
        console.print(f"[bold]Fights:[/bold] [{fight_color}]{remaining}[/{fight_color}]/{max_solo} remaining")

        # Resources
        console.print(f"[bold]Habs:[/bold] {habs:,}")
        if capital > 0:
            console.print(f"[bold]Capital:[/bold] [yellow]{capital} unspent![/yellow]")
        else:
            console.print(f"[bold]Capital:[/bold] [green]All spent[/green]")

        # Build summary
        console.print(f"\n[bold]Build:[/bold] L{level} | T{talent} | STR {strength} / AGI {agility}")
        console.print(f"[bold]Equipment:[/bold] {chips_equipped}/6 chips, {weapons_equipped}/2 weapons")

        # AI
        valid = "[green]✓[/green]" if ai_info.get("valid") else "[red]✗[/red]"
        console.print(f"[bold]AI:[/bold] {ai_name} {valid}")

        # Recent fights
        colored_recent = recent.replace("W", "[green]W[/green]").replace("L", "[red]L[/red]").replace("D", "[yellow]D[/yellow]")
        console.print(f"[bold]Recent:[/bold] {colored_recent}")

        # Warnings
        if capital > 0:
            console.print(f"\n[yellow]💡 Tip: leek build spend str {capital}[/yellow]")
        if remaining == 0:
            console.print("\n[yellow]💡 No fights left today![/yellow]")
        if habs >= 7510 and weapons_equipped < 2:
            console.print("\n[yellow]💡 Can afford magnum: leek market buy 45[/yellow]")

    finally:
        api.close()


# Register command groups
cli.add_command(info.info)
cli.add_command(craft.craft)
cli.add_command(fight.fight)
cli.add_command(market.market)
cli.add_command(ai.ai)
cli.add_command(build.build)
cli.add_command(sim.sim)
cli.add_command(trophy.trophy)
cli.add_command(test.test)


def main() -> None:
    """Entry point for CLI."""
    cli()


if __name__ == "__main__":
    main()
