"""Market commands - browse and buy items."""

import click
from ..output import output_json, success, error, console
from ..constants import LEEK_ID
from leekwars_agent.auth import login_api

# Item data extracted from tools/leek-wars/src/model/items.ts
# Format: {id: {name, type, level, price}}
# type: 1=weapon, 2=chip
MARKET_ITEMS = {
    # Chips (type 2) - sorted by level
    1: {"name": "chip_shock", "type": 2, "level": 2, "price": 1780},
    3: {"name": "chip_bandage", "type": 2, "level": 3, "price": 2000},
    7: {"name": "chip_pebble", "type": 2, "level": 4, "price": 3290},
    8: {"name": "chip_protein", "type": 2, "level": 6, "price": 3520},
    2: {"name": "chip_ice", "type": 2, "level": 9, "price": 1830},
    9: {"name": "chip_helmet", "type": 2, "level": 10, "price": 2200},
    10: {"name": "chip_rock", "type": 2, "level": 13, "price": 7400},
    11: {"name": "chip_motivation", "type": 2, "level": 14, "price": 3560},
    12: {"name": "chip_stretching", "type": 2, "level": 17, "price": 6000},
    13: {"name": "chip_wall", "type": 2, "level": 18, "price": 8700},
    14: {"name": "chip_spark", "type": 2, "level": 19, "price": 2910},
    4: {"name": "chip_cure", "type": 2, "level": 20, "price": 3710},
    15: {"name": "chip_leather_boots", "type": 2, "level": 22, "price": 3800},
    6: {"name": "chip_flash", "type": 2, "level": 24, "price": 4890},
    5: {"name": "chip_flame", "type": 2, "level": 29, "price": 5560},
    16: {"name": "chip_knowledge", "type": 2, "level": 32, "price": 14890},
    # Weapons (type 1)
    37: {"name": "weapon_pistol", "type": 1, "level": 1, "price": 900},
    38: {"name": "weapon_machine_gun", "type": 1, "level": 8, "price": 3080},
    41: {"name": "weapon_neutrino", "type": 1, "level": 12, "price": 8250},
    39: {"name": "weapon_shotgun", "type": 1, "level": 16, "price": 6800},
    40: {"name": "weapon_magnum", "type": 1, "level": 27, "price": 7510},
    42: {"name": "weapon_broadsword", "type": 1, "level": 30, "price": 9950},
}


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

        # Filter items
        items = []
        for item_id, item in MARKET_ITEMS.items():
            if item["level"] > max_level:
                continue
            if item_type == "chips" and item["type"] != 2:
                continue
            if item_type == "weapons" and item["type"] != 1:
                continue
            items.append({"id": item_id, **item, "affordable": item["price"] <= habs})

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
        leek market buy 40     # Buy weapon_magnum
        leek market buy 1 -n 2 # Buy 2x chip_shock
    """
    if item_id not in MARKET_ITEMS:
        error(f"Unknown item #{item_id}. Use 'leek market list' to see available items.")
        raise SystemExit(1)

    item = MARKET_ITEMS[item_id]
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
            template = found.get("template", "?")
            name = MARKET_ITEMS.get(template, {}).get("name", f"item_{template}")
            success(f"Equipped {name} to leek!")

    finally:
        api.close()
