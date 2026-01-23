"""Test scenario commands - unlimited server-side fights for AI validation."""

import time
import click
from ..output import output_json, success, error, console
from leekwars_agent.auth import login_api


@click.group()
def test():
    """Test scenarios - unlimited server-side fights.

    Run AI tests without burning daily fight quota!
    """
    pass


@test.command("list")
@click.pass_context
def list_scenarios(ctx: click.Context) -> None:
    """List saved test scenarios."""
    api = login_api()
    try:
        data = api.get_test_scenarios()
        scenarios = data.get("scenarios", {})
        leeks = data.get("leeks", [])
        maps = data.get("maps", {})

        if ctx.obj.get("json"):
            output_json({
                "scenarios": scenarios,
                "leeks": leeks,
                "maps": maps,
            })
            return

        console.print(f"[bold]Test Scenarios[/bold] ({len(scenarios)} saved)\n")

        for sid, scen in scenarios.items():
            name = scen.get("name", "Unnamed")
            stype = scen.get("type", -1)
            type_name = {0: "Solo", 1: "Farmer", 2: "Team", 3: "BR"}.get(stype, "Custom")
            t1 = len(scen.get("team1", []))
            t2 = len(scen.get("team2", []))
            console.print(f"  [cyan]{sid}[/cyan] {name} ({type_name}) - {t1}v{t2}")

        if leeks:
            console.print(f"\n[bold]Test Leeks[/bold] ({len(leeks)} custom)")
            for leek in leeks[:5]:  # Show first 5
                console.print(f"  [dim]{leek.get('id')}[/dim] {leek.get('name', '?')}")
            if len(leeks) > 5:
                console.print(f"  [dim]... and {len(leeks) - 5} more[/dim]")

    finally:
        api.close()


@test.command("run")
@click.argument("scenario_id", type=int)
@click.option("--ai", "-a", type=int, help="AI ID to test (default: current deployed)")
@click.option("--wait/--no-wait", default=True, help="Wait for fight to complete")
@click.pass_context
def run_test(ctx: click.Context, scenario_id: int, ai: int | None, wait: bool) -> None:
    """Run a test fight using a scenario.

    No daily limit - run as many as you want!

    Examples:
        leek test run 37863           # Run with deployed AI
        leek test run 37863 --ai 123  # Run with specific AI
    """
    api = login_api()
    try:
        # Get AI ID if not specified
        if ai is None:
            # Use first AI from farmer's list
            ais = api.get_farmer_ais().get("ais", [])
            if not ais:
                error("No AIs found")
                raise SystemExit(1)
            ai = ais[0]["id"]
            ai_name = ais[0]["name"]
        else:
            ai_data = api.get_ai(ai)
            ai_name = ai_data.get("ai", {}).get("name", f"AI {ai}")

        console.print(f"Running test fight...")
        console.print(f"  Scenario: [cyan]{scenario_id}[/cyan]")
        console.print(f"  AI: [cyan]{ai_name}[/cyan] (id={ai})")

        # Run the fight
        result = api.run_test_fight(scenario_id, ai)
        fight_id = result.get("fight")

        if not fight_id:
            error(f"Failed to start fight: {result}")
            raise SystemExit(1)

        console.print(f"  Fight ID: [green]{fight_id}[/green]")

        if wait:
            console.print("  Waiting for result...", end=" ")
            time.sleep(3)  # Fights usually complete in 2-3 seconds

            fight_data = api.get_fight(fight_id)
            fight = fight_data.get("fight", fight_data)
            winner = fight.get("winner", 0)

            winner_str = "Draw" if winner == 0 else f"Team {winner}"
            color = "yellow" if winner == 0 else ("green" if winner == 1 else "red")
            console.print(f"[{color}]{winner_str}[/{color}]")

        console.print(f"\n  [link=https://leekwars.com/fight/{fight_id}]View fight →[/link]")

        if ctx.obj.get("json"):
            output_json({
                "fight_id": fight_id,
                "scenario_id": scenario_id,
                "ai_id": ai,
                "winner": winner if wait else None,
                "url": f"https://leekwars.com/fight/{fight_id}",
            })

    finally:
        api.close()


@test.command("create")
@click.argument("name")
@click.pass_context
def create_scenario(ctx: click.Context, name: str) -> None:
    """Create a new test scenario.

    After creating, add leeks with 'leek test add-leek'.
    """
    api = login_api()
    try:
        result = api.create_test_scenario(name)
        scenario_id = result.get("id")

        if ctx.obj.get("json"):
            output_json({"id": scenario_id, "name": name})
        else:
            success(f"Created scenario '{name}' (id={scenario_id})")

    finally:
        api.close()


@test.command("add-leek")
@click.argument("scenario_id", type=int)
@click.argument("leek_id", type=int)
@click.option("--team", "-t", type=int, default=0, help="Team (0=team1, 1=team2)")
@click.option("--ai", "-a", type=int, help="AI override for this leek")
@click.pass_context
def add_leek(ctx: click.Context, scenario_id: int, leek_id: int, team: int, ai: int | None) -> None:
    """Add a leek to a test scenario.

    Examples:
        leek test add-leek 37863 131321 --team 0
        leek test add-leek 37863 131321 --team 1 --ai 455823
    """
    api = login_api()
    try:
        result = api.add_leek_to_scenario(scenario_id, leek_id, team, ai)

        if ctx.obj.get("json"):
            output_json(result)
        else:
            team_name = "Team 1" if team == 0 else "Team 2"
            success(f"Added leek {leek_id} to {team_name} in scenario {scenario_id}")

    finally:
        api.close()
