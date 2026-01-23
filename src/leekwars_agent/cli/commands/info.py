"""Info commands - view leek and farmer data."""

import json
import click
from pathlib import Path
from ..output import output_json, output_kv, success, console
from ..constants import LEEK_ID, FARMER_ID
from leekwars_agent.auth import login_api


@click.group()
def info():
    """View leek and farmer information."""
    pass


@info.command("leek")
@click.argument("leek_id", type=int, default=LEEK_ID)
@click.pass_context
def leek_info(ctx: click.Context, leek_id: int) -> None:
    """Show leek information.

    LEEK_ID defaults to your leek (IAdonis).
    """
    api = login_api()
    try:
        data = api.get_leek(leek_id)
        leek = data.get("leek", data)

        if ctx.obj.get("json"):
            output_json(leek)
        else:
            # Format chips and weapons
            chips = leek.get("chips", [])
            weapons = leek.get("weapons", [])
            chip_ids = [str(c.get("template", c.get("id", "?"))) for c in chips]
            weapon_ids = [str(w.get("template", w.get("id", "?"))) for w in weapons]

            output_kv({
                "Name": leek.get("name"),
                "Level": leek.get("level"),
                "Talent": leek.get("talent"),
                "Capital": leek.get("capital", 0),
                "Strength": leek.get("strength"),
                "Agility": leek.get("agility"),
                "Frequency": leek.get("frequency"),
                "Wisdom": leek.get("wisdom"),
                "Resistance": leek.get("resistance"),
                "Science": leek.get("science"),
                "Magic": leek.get("magic"),
                "Life": leek.get("life"),
                "TP": leek.get("tp"),
                "MP": leek.get("mp"),
                "Chips": f"{len(chips)} ({', '.join(chip_ids)})" if chips else "0",
                "Weapons": f"{len(weapons)} ({', '.join(weapon_ids)})" if weapons else "0",
            }, title=f"Leek #{leek_id}")
    finally:
        api.close()


@info.command("farmer")
@click.argument("farmer_id", type=int, default=FARMER_ID)
@click.pass_context
def farmer_info(ctx: click.Context, farmer_id: int) -> None:
    """Show farmer information.

    FARMER_ID defaults to your account (PriapOS).
    """
    api = login_api()
    try:
        data = api.get_farmer(farmer_id)
        farmer = data.get("farmer", data)

        if ctx.obj.get("json"):
            output_json(farmer)
        else:
            leeks = farmer.get("leeks", {})
            leek_names = [l.get("name", "?") for l in leeks.values()]

            output_kv({
                "Name": farmer.get("name"),
                "Level": farmer.get("total_level"),
                "Talent": farmer.get("talent"),
                "Habs": farmer.get("habs"),
                "Crystals": farmer.get("crystals"),
                "Leeks": ", ".join(leek_names) if leek_names else "None",
            }, title=f"Farmer #{farmer_id}")
    finally:
        api.close()


@info.command("garden")
@click.pass_context
def garden_info(ctx: click.Context) -> None:
    """Show garden status (fights remaining)."""
    api = login_api()
    try:
        data = api.get_garden()
        garden = data.get("garden", data)

        if ctx.obj.get("json"):
            output_json(garden)
        else:
            fights = garden.get("fights", 0)
            max_fights = garden.get("max_fights", 100)
            console.print(f"[bold]Garden Status[/bold]")
            console.print(f"  Fights: [green]{fights}[/green] / {max_fights}")
    finally:
        api.close()


@info.command("constants")
@click.option("--save/--no-save", default=False, help="Save to data/ directory")
@click.pass_context
def constants_info(ctx: click.Context, save: bool) -> None:
    """Fetch game constants (weapons, chips, functions).

    Examples:
        leek info constants           # Display summary
        leek info constants --save    # Save to data/*.json
        leek --json info constants    # Full JSON output
    """
    api = login_api()
    try:
        data_dir = Path("data")

        console.print("[bold]Fetching game constants...[/bold]")

        weapons = api.get_weapons()
        chips = api.get_chips()
        constants = api.get_constants()
        functions = api.get_functions()

        weapon_count = len(weapons.get("weapons", weapons))
        chip_count = len(chips.get("chips", chips))
        func_count = len(functions.get("functions", functions))

        if save:
            data_dir.mkdir(exist_ok=True)
            (data_dir / "weapons.json").write_text(json.dumps(weapons, indent=2))
            (data_dir / "chips.json").write_text(json.dumps(chips, indent=2))
            (data_dir / "constants.json").write_text(json.dumps(constants, indent=2))
            (data_dir / "functions.json").write_text(json.dumps(functions, indent=2))
            success(f"Saved to data/")

        if ctx.obj.get("json"):
            output_json({
                "weapons": weapons,
                "chips": chips,
                "constants": constants,
                "functions": functions,
            })
            return

        console.print(f"  Weapons: {weapon_count}")
        console.print(f"  Chips: {chip_count}")
        console.print(f"  Functions: {func_count}")

    finally:
        api.close()
