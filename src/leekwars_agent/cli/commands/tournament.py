"""Tournament commands - participate in LeekWars tournaments."""

import click
from ..output import output_json, success, error, console
from leekwars_agent.auth import login_api
from leekwars_agent.api import LeekWarsAPI


@click.group()
def tournament():
    """Tournament management - participate in tournaments.

    Tournaments are daily events with brackets (solo, farmer, team, BR).
    Register to participate and climb the ladder!

    Examples:
        leek tournament list              # Show available tournaments
        leek tournament register          # Register for tournament
        leek tournament status            # Check registration status
    """
    pass


@tournament.command("list")
@click.option("--json", is_flag=True, help="Output as JSON")
def tournament_list(json: bool) -> None:
    """Show your tournament eligibility (power range).

    Tournaments are auto-generated based on your power.
    Register to participate in the next tournament!
    """
    api = login_api()

    try:
        result = api.get_tournaments()

        if json:
            output_json(result)
            return

        power_range = result.get("tournament_range", result)
        min_power = power_range.get("min", "?")
        max_power = power_range.get("max", "?")

        console.print("[bold]Tournament Eligibility[/bold]\n")
        console.print(f"  Your power range: [cyan]{min_power}[/cyan] - [cyan]{max_power}[/cyan]")
        console.print(f"  Runs every 30 minutes during tournament phases.")
        console.print("\n  Register: [cyan]leek tournament register farmer[/cyan]")

    except Exception as e:
        error(f"Failed to fetch tournament range: {e}")


@tournament.command("register")
@click.argument("entity_type", type=click.Choice(["farmer", "leek"]), default="farmer")
@click.argument("entity_id", type=int, required=False)
@click.option("--json", is_flag=True, help="Output as JSON")
def tournament_register(entity_type: str, entity_id: int | None, json: bool) -> None:
    """Register for a tournament.

    ENTITY_TYPE is 'farmer' (you) or 'leek' (specific leek).
    ENTITY_ID is required for 'leek' type.

    Requirements:
    - Tournaments enabled for your account
    - 2+ leeks for farmer registration

    Examples:
        leek tournament register farmer        # Register yourself
        leek tournament register leek 131321   # Register a specific leek
    """
    api = login_api()

    if entity_type == "leek" and not entity_id:
        error("entity_id required for 'leek' registration")
        return

    try:
        result = api.register_tournament(entity_type, entity_id or 0)

        if json:
            output_json(result)
            return

        if result.get("success", True):
            success(f"Registered for tournament as {entity_type}!")
        else:
            error(f"Registration failed: {result.get('error', 'Unknown error')}")

    except Exception as e:
        # Check for common issues
        error_str = str(e)
        if "401" in error_str:
            error("Registration failed: Check requirements (2+ leeks needed for farmer tournaments)")
        else:
            error(f"Failed to register: {e}")


@tournament.command("unregister")
@click.argument("entity_type", type=click.Choice(["farmer", "leek"]), default="farmer")
@click.argument("entity_id", type=int, required=False)
@click.option("--json", is_flag=True, help="Output as JSON")
def tournament_unregister(entity_type: str, entity_id: int | None, json: bool) -> None:
    """Unregister from a tournament.

    ENTITY_TYPE is 'farmer' (you) or 'leek' (specific leek).
    ENTITY_ID is required for 'leek' type.

    Examples:
        leek tournament unregister farmer       # Unregister yourself
        leek tournament unregister leek 131321  # Unregister a specific leek
    """
    api = login_api()

    if entity_type == "leek" and not entity_id:
        error("entity_id required for 'leek' unregistration")
        return

    try:
        result = api.unregister_tournament(entity_type, entity_id or 0)

        if json:
            output_json(result)
            return

        if result.get("success", True):
            success(f"Unregistered from tournament as {entity_type}!")
        else:
            error(f"Unregistration failed: {result.get('error', 'Unknown error')}")

    except Exception as e:
        error(f"Failed to unregister: {e}")


@tournament.command("status")
@click.option("--json", is_flag=True, help="Output as JSON")
def tournament_status(json: bool) -> None:
    """Check tournament registration status."""
    api = login_api()

    try:
        farmer = api.get_farmer(api.farmer_id) if api.farmer_id else {}
        farmer_data = farmer.get("farmer", farmer)

        if json:
            output_json({
                "tournaments_enabled": farmer_data.get("tournaments_enabled", False),
                "registered": farmer_data.get("tournament", {}).get("registered", False),
                "current_tournament": farmer_data.get("tournament", {}).get("current", None),
            })
            return

        console.print("[bold]Tournament Status[/bold]\n")

        enabled = farmer_data.get("tournaments_enabled", False)
        registered = farmer_data.get("tournament", {}).get("registered", False)
        current = farmer_data.get("tournament", {}).get("current", None)

        status = "ENABLED" if enabled else "DISABLED"
        status_color = "green" if enabled else "yellow"
        console.print(f"  Tournaments: [{status_color}]{status}[/{status_color}]")

        reg_status = "REGISTERED" if registered else "Not registered"
        reg_color = "green" if registered else "red"
        console.print(f"  Registration: [{reg_color}]{reg_status}[/{reg_color}]")

        if current:
            console.print(f"  Current: [cyan]Tournament #{current}[/cyan]")
        else:
            console.print("  Current: None")

    except Exception as e:
        error(f"Failed to fetch status: {e}")


@tournament.command("view")
@click.argument("tournament_id", type=int)
@click.option("--json", is_flag=True, help="Output as JSON")
def tournament_view(tournament_id: int, json: bool) -> None:
    """View tournament details by ID.

    Shows tournament bracket, participants, and progress.
    Use this to check tournament status after registering.
    """
    api = login_api()

    try:
        tournament = api.get_tournament(tournament_id)

        if json:
            output_json(tournament)
            return

        console.print(f"[bold]Tournament #{tournament_id}[/bold]\n")

        t = tournament.get("tournament", tournament)
        console.print(f"  Type: {t.get('type', '?')} | Date: {t.get('date', '?')}")
        console.print(f"  Size: {t.get('size', '?')} | Finished: {t.get('finished', '?')}")
        console.print("\n  [cyan]View full bracket at:[/cyan] https://leekwars.com/tournament/{id}")

    except Exception as e:
        error(f"Failed to fetch tournament: {e}")