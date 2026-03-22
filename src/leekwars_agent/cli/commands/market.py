"""Market commands - browse and buy items."""

import click
from ..output import output_json, success, error, console
from ..constants import LEEK_ID  # unused but kept for backward compat
from ..items_loader import get_market_items, get_item, ITEM_TYPE_CHIP, ITEM_TYPE_WEAPON
from leekwars_agent.auth import login_api
from leekwars_agent.api import LeekWarsError


def _resolve_equipped_item(leek_data: dict, identifier: str) -> tuple[dict, str] | None:
    """Resolve a name, template ID, or instance ID to an equipped item.

    Accepts: chip/weapon name (e.g. "motivation"), template ID (e.g. "15"),
    or instance ID (e.g. "2435822").

    Returns (item_dict, item_type) or None if not found.
    """
    chips = leek_data.get("chips", [])
    weapons = leek_data.get("weapons", [])

    # Try by name first (case-insensitive, matches with or without chip_/weapon_ prefix)
    identifier_lower = identifier.lower().replace(" ", "_")
    for chip in chips:
        tmpl = chip.get("template", 0)
        item_data = get_item(tmpl)
        if item_data:
            name = item_data["name"].lower().replace(" ", "_")
            short = name.removeprefix("chip_").removeprefix("weapon_")
            if identifier_lower in (name, short) or name.startswith(identifier_lower) or short.startswith(identifier_lower):
                return chip, "chip"
    for weapon in weapons:
        tmpl = weapon.get("template", 0)
        item_data = get_item(tmpl)
        if item_data:
            name = item_data["name"].lower().replace(" ", "_")
            short = name.removeprefix("chip_").removeprefix("weapon_")
            if identifier_lower in (name, short) or name.startswith(identifier_lower) or short.startswith(identifier_lower):
                return weapon, "weapon"

    # Try numeric: template ID first, then instance ID
    try:
        num_id = int(identifier)
    except ValueError:
        return None

    # Template ID match
    for chip in chips:
        if chip.get("template") == num_id:
            return chip, "chip"
    for weapon in weapons:
        if weapon.get("template") == num_id:
            return weapon, "weapon"

    # Instance ID match (fallback)
    for chip in chips:
        if chip.get("id") == num_id:
            return chip, "chip"
    for weapon in weapons:
        if weapon.get("id") == num_id:
            return weapon, "weapon"

    return None


def _resolve_inventory_item(inv_data: dict, identifier: str) -> tuple[dict, str] | None:
    """Resolve a name, template ID, or instance ID to an inventory item.

    Same resolution logic as _resolve_equipped_item but searches inventory.
    """
    chips = inv_data.get("chips", [])
    weapons = inv_data.get("weapons", [])

    identifier_lower = identifier.lower().replace(" ", "_")
    for chip in chips:
        tmpl = chip.get("template", 0)
        item_data = get_item(tmpl)
        if item_data:
            name = item_data["name"].lower().replace(" ", "_")
            short = name.removeprefix("chip_").removeprefix("weapon_")
            if identifier_lower in (name, short) or name.startswith(identifier_lower) or short.startswith(identifier_lower):
                return chip, "chip"
    for weapon in weapons:
        tmpl = weapon.get("template", 0)
        item_data = get_item(tmpl)
        if item_data:
            name = item_data["name"].lower().replace(" ", "_")
            short = name.removeprefix("chip_").removeprefix("weapon_")
            if identifier_lower in (name, short) or name.startswith(identifier_lower) or short.startswith(identifier_lower):
                return weapon, "weapon"

    try:
        num_id = int(identifier)
    except ValueError:
        return None

    for chip in chips:
        if chip.get("template") == num_id:
            return chip, "chip"
    for weapon in weapons:
        if weapon.get("template") == num_id:
            return weapon, "weapon"

    for chip in chips:
        if chip.get("id") == num_id:
            return chip, "chip"
    for weapon in weapons:
        if weapon.get("id") == num_id:
            return weapon, "weapon"

    return None


def _list_equipped(leek_data: dict) -> str:
    """Format equipped items for error hints."""
    items = []
    for chip in leek_data.get("chips", []):
        tmpl = chip.get("template", 0)
        item_data = get_item(tmpl)
        name = (item_data["name"].removeprefix("chip_") if item_data else f"#{tmpl}")
        items.append(name)
    for weapon in leek_data.get("weapons", []):
        tmpl = weapon.get("template", 0)
        item_data = get_item(tmpl)
        name = (item_data["name"].removeprefix("weapon_") if item_data else f"#{tmpl}")
        items.append(name)
    return ", ".join(items)


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
    leek_id = ctx.obj["leek_id"]
    api = login_api()
    try:
        inv = api.get_inventory()
        habs = inv.get("habs", 0)
        leek = api.get_leek(leek_id)
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
        try:
            result = api.buy_item(item_id, quantity)
        except LeekWarsError as e:
            error(f"Purchase failed: {e.error}")
            raise SystemExit(1)

        if ctx.obj.get("json"):
            output_json(result)
        else:
            success(f"Bought {quantity}x {item['name']} for {total_price:,} habs!")
            new_habs = habs - total_price
            console.print(f"  Remaining: {new_habs:,} habs")

    finally:
        api.close()


@market.command("sell")
@click.argument("item_id", type=int)
@click.option("--dry-run", is_flag=True, help="Show sell price without selling")
@click.pass_context
def sell(ctx: click.Context, item_id: int, dry_run: bool) -> None:
    """Sell an item from inventory for habs.

    ITEM_ID is the item template ID (use 'leek market list' to see IDs).

    Examples:
        leek market sell 40     # Sell Destroyer
        leek market sell 42 --dry-run  # Check Laser sell price
    """
    item = get_item(item_id)
    if not item:
        error(f"Unknown item #{item_id}. Use 'leek market list' to see items.")
        raise SystemExit(1)

    api = login_api()
    try:
        inv = api.get_inventory()
        habs = inv.get("habs", 0)

        if dry_run:
            console.print(f"[yellow]Would sell {item['name']} (#{item_id})[/yellow]")
            console.print(f"  Sell price: {item.get('price', '?'):,} habs (buy price)")
            console.print(f"  Current habs: {habs:,}")
            if ctx.obj.get("json"):
                output_json({"item": item, "habs": habs})
            return

        try:
            result = api.sell_item(item_id)
        except LeekWarsError as e:
            error(f"Sell failed: {e.error}")
            raise SystemExit(1)

        if ctx.obj.get("json"):
            output_json(result)
        else:
            success(f"Sold {item['name']}!")
            new_habs = api.get_inventory().get("habs", 0)
            console.print(f"  Habs: {habs:,} → {new_habs:,} (+{new_habs - habs:,})")

    finally:
        api.close()


@market.command("equip")
@click.argument("identifier")
@click.pass_context
def equip(ctx: click.Context, identifier: str) -> None:
    """Equip an owned chip or weapon to your leek.

    IDENTIFIER can be a name (e.g. "ferocity"), template ID, or instance ID.

    Examples:
        leek market equip ferocity    # By name
        leek market equip 102         # By template ID
        leek market equip 2476095     # By instance ID
    """
    api = login_api()
    try:
        inv = api.get_inventory()
        result_pair = _resolve_inventory_item(inv, identifier)

        if not result_pair:
            error(f"'{identifier}' not found in inventory")
            console.print("  [dim]Hint: use 'leek craft inventory' to see owned items[/dim]")
            raise SystemExit(1)

        found, item_type = result_pair
        instance_id = found["id"]
        leek_id = ctx.obj["leek_id"]

        try:
            if item_type == "chip":
                result = api.add_chip(leek_id, instance_id)
            else:
                result = api.add_weapon(leek_id, instance_id)
        except LeekWarsError as e:
            error(f"Equip failed: {e.error}")
            raise SystemExit(1)

        if ctx.obj.get("json"):
            output_json(result)
        else:
            template = found.get("template", 0)
            item_data = get_item(template)
            name = item_data["name"] if item_data else f"item_{template}"
            success(f"Equipped {name} to leek!")

    finally:
        api.close()


@market.command("unequip")
@click.argument("identifier")
@click.pass_context
def unequip(ctx: click.Context, identifier: str) -> None:
    """Unequip a chip or weapon from your leek.

    IDENTIFIER can be a name (e.g. "motivation"), template ID, or instance ID.

    Examples:
        leek market unequip motivation   # By name
        leek market unequip 15           # By template ID
        leek market unequip 2435822      # By instance ID
    """
    leek_id = ctx.obj["leek_id"]
    api = login_api()
    try:
        leek = api.get_leek(leek_id)
        result_pair = _resolve_equipped_item(leek, identifier)

        if not result_pair:
            equipped = _list_equipped(leek)
            error(f"'{identifier}' not equipped on leek")
            console.print(f"  [dim]Equipped: {equipped}[/dim]")
            raise SystemExit(1)

        found, item_type = result_pair
        instance_id = found["id"]

        try:
            if item_type == "chip":
                result = api.remove_chip(leek_id, instance_id)
            else:
                result = api.remove_weapon(instance_id)
        except LeekWarsError as e:
            error(f"Unequip failed: {e.error}")
            raise SystemExit(1)

        template = found.get("template", 0)
        item_data = get_item(template)
        name = item_data["name"] if item_data else f"item_{template}"

        if ctx.obj.get("json"):
            output_json(result)
        else:
            success(f"Unequipped {name} from leek!")

    finally:
        api.close()
