"""Market commands - browse and buy items."""

import click
from ..output import output_json, success, error, console
from ..constants import LEEK_ID
from ..items_loader import get_market_items, get_item, ITEM_TYPE_CHIP, ITEM_TYPE_WEAPON
from leekwars_agent.auth import login_api


@click.group()
def market():
    """Market operations - browse and buy items."""
    pass


@market.command("list")
@click.option("--type", "item_type", type=click.Choice(["all", "chips", "weapons"]), default="all")
@click.option("--max-level", type=int, default=None, help="Filter by max level")
@click.pass_context
def list_items(ctx: click.Context, item_type: str, max_level: int | None) -> None:
    """List items available in the market.

    Shows chips and weapons you can buy with habs.
    """
    api = login_api()
    try:
        inv = api.get_inventory()
        habs = inv.get("habs", 0)
        leek = api.get_leek(LEEK_ID)
        level = leek.get("level", 1)

        if max_level is None:
            max_level = level

        # Get items from dynamic loader
        type_filter = None
        if item_type == "chips":
            type_filter = ITEM_TYPE_CHIP
        elif item_type == "weapons":
            type_filter = ITEM_TYPE_WEAPON

        market_items = get_market_items(max_level=max_level, item_type=type_filter)
        items = [
            {"id": item_id, **item, "affordable": item["price"] <= habs}
            for item_id, item in market_items.items()
        ]

        items.sort(key=lambda x: (x["type"], x["level"]))

        if ctx.obj.get("json"):
            output_json({"items": items, "habs": habs, "level": level})
            return

        console.print(f"[bold]Market[/bold] (L{level}, {habs:,} habs)\n")

        # Chips
        chips = [i for i in items if i["type"] == 2]
        if chips and item_type in ["all", "chips"]:
            console.print("[cyan]Chips[/cyan]")
            for item in chips:
                status = "[green]✓[/green]" if item["affordable"] else "[red]✗[/red]"
                console.print(f"  {status} #{item['id']:3d} L{item['level']:2d} {item['name']:25s} {item['price']:,} habs")

        # Weapons
        weapons = [i for i in items if i["type"] == 1]
        if weapons and item_type in ["all", "weapons"]:
            console.print("\n[cyan]Weapons[/cyan]")
            for item in weapons:
                status = "[green]✓[/green]" if item["affordable"] else "[red]✗[/red]"
                console.print(f"  {status} #{item['id']:3d} L{item['level']:2d} {item['name']:25s} {item['price']:,} habs")

    finally:
        api.close()


@market.command("buy")
@click.argument("item_id", type=int)
@click.option("--quantity", "-n", type=int, default=1, help="Quantity to buy")
@click.option("--dry-run", is_flag=True, help="Check if affordable without buying")
@click.pass_context
def buy(ctx: click.Context, item_id: int, quantity: int, dry_run: bool) -> None:
    """Buy an item from the market.

    ITEM_ID is the item number (use 'leek market list' to see available).

    Examples:
        leek market buy 6      # Buy chip_flash
        leek market buy 45     # Buy weapon_magnum (NOT 40 - that's destroyer!)
        leek market buy 1 -n 2 # Buy 2x chip_shock
    """
    item = get_item(item_id)
    if not item:
        error(f"Unknown item #{item_id}. Use 'leek market list' to see available items.")
        raise SystemExit(1)
    total_price = item["price"] * quantity

    api = login_api()
    try:
        inv = api.get_inventory()
        habs = inv.get("habs", 0)

        if habs < total_price:
            error(f"Not enough habs: need {total_price:,}, have {habs:,}")
            raise SystemExit(1)

        if dry_run:
            success(f"Can buy {quantity}x {item['name']} for {total_price:,} habs (dry run)")
            if ctx.obj.get("json"):
                output_json({"can_buy": True, "item": item, "total_price": total_price})
            return

        # Actually buy
        result = api.buy_item(item_id, quantity)

        if ctx.obj.get("json"):
            output_json(result)
        else:
            success(f"Bought {quantity}x {item['name']} for {total_price:,} habs!")
            new_habs = habs - total_price
            console.print(f"  Remaining: {new_habs:,} habs")

    finally:
        api.close()


@market.command("equip")
@click.argument("item_id", type=int)
@click.pass_context
def equip(ctx: click.Context, item_id: int) -> None:
    """Equip an owned chip or weapon to your leek.

    ITEM_ID is the inventory item ID (not template ID).
    Use 'leek craft inventory' to see owned items with their IDs.
    """
    api = login_api()
    try:
        # Determine if chip or weapon based on template
        inv = api.get_inventory()

        # Find item in inventory
        found = None
        item_type = None
        for chip in inv.get("chips", []):
            if chip.get("id") == item_id:
                found = chip
                item_type = "chip"
                break
        for weapon in inv.get("weapons", []):
            if weapon.get("id") == item_id:
                found = weapon
                item_type = "weapon"
                break

        if not found:
            error(f"Item #{item_id} not found in inventory")
            raise SystemExit(1)

        if item_type == "chip":
            result = api.add_chip(LEEK_ID, item_id)
        else:
            result = api.add_weapon(LEEK_ID, item_id)

        if ctx.obj.get("json"):
            output_json(result)
        else:
            template = found.get("template", 0)
            item_data = get_item(template)
            name = item_data["name"] if item_data else f"item_{template}"
            success(f"Equipped {name} to leek!")

    finally:
        api.close()
