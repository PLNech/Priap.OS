"""Info commands - view leek and farmer data."""

import click
from ..output import output_json, output_kv, console
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
