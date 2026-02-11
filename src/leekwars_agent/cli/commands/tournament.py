"""Tournament commands - participate in LeekWars tournaments."""

import click
from ..output import output_json, success, error, console
from ..constants import LEEK_ID
from leekwars_agent.auth import login_api


@click.group()
def tournament():
    """Tournament management - register and track tournaments.

    Tournaments are daily bracket events (solo leek, farmer, team).
    Register to participate and earn ranking points!

    Examples:
        leek tournament status            # Check registration status
        leek tournament register          # Register our leek (solo)
        leek tournament register farmer   # Register as farmer
    """
    pass


@tournament.command("list")
@click.pass_context
def tournament_list(ctx: click.Context) -> None:
    """Show your tournament eligibility (power range)."""
    api = login_api()

    try:
        result = api.get_tournaments()

        if ctx.obj.get("json"):
            output_json(result)
            return

        power_range = result.get("tournament_range", result)
        min_power = power_range.get("min", "?")
        max_power = power_range.get("max", "?")

        console.print("[bold]Tournament Eligibility[/bold]\n")
        console.print(f"  Your power range: [cyan]{min_power}[/cyan] - [cyan]{max_power}[/cyan]")
        console.print("\n  Register: [cyan]leek tournament register[/cyan]")

    except Exception as e:
        error(f"Failed to fetch tournament range: {e}")


@tournament.command("register")
@click.argument("entity_type", type=click.Choice(["farmer", "leek"]), default="leek")
@click.argument("entity_id", type=int, required=False)
@click.pass_context
def tournament_register(ctx: click.Context, entity_type: str, entity_id: int | None) -> None:
    """Register for a tournament.

    ENTITY_TYPE is 'leek' (solo, default) or 'farmer' (requires 2+ leeks).
    ENTITY_ID defaults to our leek for 'leek' type.

    Examples:
        leek tournament register              # Register our leek (solo)
        leek tournament register leek         # Same as above
        leek tournament register farmer       # Register as farmer
    """
    api = login_api()

    if entity_type == "leek" and not entity_id:
        entity_id = LEEK_ID

    try:
        result = api.register_tournament(entity_type, entity_id or 0)

        if ctx.obj.get("json"):
            output_json(result)
            return

        err = result.get("error")
        if err == "already_registered":
            success(f"Already registered for tournament as {entity_type}!")
        elif err:
            error(f"Registration failed: {err}")
        else:
            success(f"Registered for tournament as {entity_type}!")

    except Exception as e:
        error(f"Failed to register: {e}")


@tournament.command("unregister")
@click.argument("entity_type", type=click.Choice(["farmer", "leek"]), default="leek")
@click.argument("entity_id", type=int, required=False)
@click.pass_context
def tournament_unregister(ctx: click.Context, entity_type: str, entity_id: int | None) -> None:
    """Unregister from a tournament.

    ENTITY_TYPE is 'leek' (default) or 'farmer'.
    ENTITY_ID defaults to our leek for 'leek' type.

    Examples:
        leek tournament unregister             # Unregister our leek
        leek tournament unregister farmer      # Unregister as farmer
    """
    api = login_api()

    if entity_type == "leek" and not entity_id:
        entity_id = LEEK_ID

    try:
        result = api.unregister_tournament(entity_type, entity_id or 0)

        if ctx.obj.get("json"):
            output_json(result)
            return

        err = result.get("error")
        if err:
            error(f"Unregistration failed: {err}")
        else:
            success(f"Unregistered from tournament as {entity_type}!")

    except Exception as e:
        error(f"Failed to unregister: {e}")


@tournament.command("status")
@click.pass_context
def tournament_status(ctx: click.Context) -> None:
    """Check tournament registration status (leek + farmer)."""
    api = login_api()

    try:
        leek_data = api.get_leek(LEEK_ID)
        leek = leek_data.get("leek", leek_data)
        leek_tournament = leek.get("tournament", {})

        farmer = api.get_farmer(api.farmer_id) if api.farmer_id else {}
        farmer_data = farmer.get("farmer", farmer)
        enabled = farmer_data.get("tournaments_enabled", False)

        if ctx.obj.get("json"):
            output_json({
                "tournaments_enabled": enabled,
                "leek": {
                    "registered": leek_tournament.get("registered", False),
                    "current": leek_tournament.get("current"),
                },
                "farmer": {
                    "registered": farmer_data.get("tournament", {}).get("registered", False),
                    "current": farmer_data.get("tournament", {}).get("current"),
                },
            })
            return

        console.print("[bold]Tournament Status[/bold]\n")

        status_color = "green" if enabled else "yellow"
        console.print(f"  Tournaments: [{status_color}]{'ENABLED' if enabled else 'DISABLED'}[/{status_color}]")

        # Leek (solo) tournament
        leek_reg = leek_tournament.get("registered", False)
        leek_cur = leek_tournament.get("current")
        reg_icon = "[green]✓[/green]" if leek_reg else "[red]✗[/red]"
        cur_str = f" → [cyan]#{leek_cur}[/cyan]" if leek_cur else ""
        console.print(f"  Solo (leek):  {reg_icon}{cur_str}")

        # Farmer tournament
        farmer_reg = farmer_data.get("tournament", {}).get("registered", False)
        farmer_cur = farmer_data.get("tournament", {}).get("current")
        reg_icon = "[green]✓[/green]" if farmer_reg else "[yellow]- (needs 2+ leeks)[/yellow]"
        cur_str = f" → [cyan]#{farmer_cur}[/cyan]" if farmer_cur else ""
        console.print(f"  Farmer:       {reg_icon}{cur_str}")

    except Exception as e:
        error(f"Failed to fetch status: {e}")


@tournament.command("view")
@click.argument("tournament_id", type=int)
@click.pass_context
def tournament_view(ctx: click.Context, tournament_id: int) -> None:
    """View tournament details by ID."""
    api = login_api()

    try:
        data = api.get_tournament(tournament_id)

        if ctx.obj.get("json"):
            output_json(data)
            return

        console.print(f"[bold]Tournament #{tournament_id}[/bold]\n")

        t = data.get("tournament", data)
        console.print(f"  Type: {t.get('type', '?')} | Date: {t.get('date', '?')}")
        console.print(f"  Size: {t.get('size', '?')} | Finished: {t.get('finished', '?')}")

    except Exception as e:
        error(f"Failed to fetch tournament: {e}")
