"""Craft commands - inventory and item crafting."""

import click
from ..output import output_json, output_table, success, error, warning, console
from ..constants import ItemType, ITEM_TYPE_NAMES
from leekwars_agent.auth import login_api

# Crafting recipes (extracted from leek-wars/src/model/schemes.ts)
# Format: {scheme_id: {"result": item_id, "items": [[item_id, qty], ...], "name": str, "qty": int}}
SCHEMES = {
    1: {"result": 290, "items": [[215, 1], [193, 12], [233, 6], [203, 3]], "name": "core", "qty": 1},
    13: {"result": 302, "items": [[193, 9], [232, 1], [204, 2]], "name": "fan", "qty": 1},
    15: {"result": 304, "items": [[203, 3], [191, 16], [233, 4], [236, 2]], "name": "cd", "qty": 1},
    24: {"result": 313, "items": [[238, 1], [204, 4], [196, 4]], "name": "ram", "qty": 1},
    28: {"result": 317, "items": [[204, 10], [192, 1], [232, 1], [215, 1]], "name": "propulsor", "qty": 1},
    30: {"result": 319, "items": [[231, 4], [206, 2], [203, 2], [377, 4]], "name": "morus", "qty": 1},
    32: {"result": 321, "items": [[231, 1], [193, 5], [191, 4]], "name": "apple", "qty": 1},
    41: {"result": 237, "items": [[236, 9]], "name": "salt", "qty": 1},
    53: {"result": 376, "items": [[188, 1], [231, 1], [202, 1], [233, 20]], "name": "pear", "qty": 1},
    60: {"result": 233, "items": [[194, 4], [195, 4]], "name": "sand", "qty": 1},
}

# Item template names (subset - expand as needed)
ITEM_NAMES = {
    191: "water", 192: "oil", 193: "electricity", 194: "earth", 195: "fire",
    196: "plastic", 203: "wood", 204: "metal", 206: "leaves", 207: "roots",
    231: "sugar", 232: "glass", 233: "sand", 236: "sea_water", 237: "salt",
    290: "core", 302: "fan", 304: "cd", 313: "ram", 317: "propulsor",
    319: "morus", 321: "apple", 376: "pear",
}


@click.group()
def craft():
    """Crafting operations - view inventory and craft items."""
    pass


@craft.command("inventory")
@click.option("--type", "item_type", type=click.Choice(["all", "resources", "components", "chips"]), default="all")
@click.pass_context
def inventory(ctx: click.Context, item_type: str) -> None:
    """List owned items and resources.

    Filter by type: resources, components, chips, or all (default).
    """
    api = login_api()
    try:
        inv = api.get_inventory()

        if ctx.obj.get("json"):
            if item_type == "all":
                output_json(inv)
            else:
                output_json(inv.get(item_type, []))
            return

        # Human-readable output
        console.print("[bold]Inventory[/bold]")
        console.print(f"  Habs: [yellow]{inv.get('habs', 0):,}[/yellow]")

        types_to_show = (
            ["resources", "components", "chips", "weapons"]
            if item_type == "all"
            else [item_type]
        )

        for t in types_to_show:
            items = inv.get(t, [])
            if items:
                console.print(f"\n  [cyan]{t.title()}[/cyan]")
                for item in items:
                    template_id = item.get("template", item.get("id"))
                    name = ITEM_NAMES.get(template_id, f"item_{template_id}")
                    qty = item.get("quantity", 1)
                    console.print(f"    {name}: x{qty}")
    finally:
        api.close()


@craft.command("list")
@click.option("--all", "show_all", is_flag=True, help="Show all recipes, not just craftable")
@click.pass_context
def list_craftable(ctx: click.Context, show_all: bool) -> None:
    """List craftable items based on current inventory.

    Shows recipes you have ingredients for. Use --all to see all recipes.
    """
    api = login_api()
    try:
        inv = api.get_inventory()

        # Build inventory lookup: {template_id: quantity}
        owned = {}
        # Also count habs (item 148)
        owned[148] = inv.get("habs", 0)

        for category in ["resources", "components"]:
            for item in inv.get(category, []):
                template_id = item.get("template", item.get("id"))
                qty = item.get("quantity", 1)
                owned[template_id] = owned.get(template_id, 0) + qty

        # Check each scheme
        craftable = []
        for scheme_id, scheme in SCHEMES.items():
            can_craft = True
            missing = []
            for item_id, needed in scheme["items"]:
                have = owned.get(item_id, 0)
                if have < needed:
                    can_craft = False
                    name = ITEM_NAMES.get(item_id, f"item_{item_id}")
                    missing.append(f"{name} ({have}/{needed})")

            if can_craft or show_all:
                craftable.append({
                    "id": scheme_id,
                    "name": scheme["name"],
                    "result": scheme["result"],
                    "can_craft": can_craft,
                    "missing": missing,
                })

        if ctx.obj.get("json"):
            output_json(craftable)
            return

        # Human-readable
        console.print("[bold]Craftable Recipes[/bold]\n")

        for recipe in craftable:
            status = "[green]✓[/green]" if recipe["can_craft"] else "[red]✗[/red]"
            console.print(f"  {status} [cyan]#{recipe['id']}[/cyan] {recipe['name']} → item #{recipe['result']}")
            if recipe["missing"]:
                console.print(f"      Missing: {', '.join(recipe['missing'])}")

        craftable_count = sum(1 for r in craftable if r["can_craft"])
        console.print(f"\n  [bold]{craftable_count}[/bold] recipes ready to craft")

    finally:
        api.close()


@craft.command("make")
@click.argument("scheme_id", type=int)
@click.option("--dry-run", is_flag=True, help="Check if craftable without actually crafting")
@click.pass_context
def make(ctx: click.Context, scheme_id: int, dry_run: bool) -> None:
    """Craft an item using a recipe.

    SCHEME_ID is the recipe number (use 'leek craft list' to see available).
    """
    if scheme_id not in SCHEMES:
        error(f"Unknown scheme #{scheme_id}. Use 'leek craft list --all' to see recipes.")
        raise SystemExit(1)

    scheme = SCHEMES[scheme_id]
    api = login_api()

    try:
        # Check inventory first
        inv = api.get_inventory()

        owned = {}
        owned[148] = inv.get("habs", 0)  # Habs (currency)

        for category in ["resources", "components"]:
            for item in inv.get(category, []):
                template_id = item.get("template", item.get("id"))
                qty = item.get("quantity", 1)
                owned[template_id] = owned.get(template_id, 0) + qty

        # Verify we have ingredients
        missing = []
        for item_id, needed in scheme["items"]:
            have = owned.get(item_id, 0)
            if have < needed:
                name = ITEM_NAMES.get(item_id, f"item_{item_id}")
                missing.append(f"{name} ({have}/{needed})")

        if missing:
            error(f"Cannot craft {scheme['name']}: missing {', '.join(missing)}")
            raise SystemExit(1)

        if dry_run:
            success(f"Can craft {scheme['name']} (dry run - not crafting)")
            if ctx.obj.get("json"):
                output_json({"can_craft": True, "scheme": scheme})
            return

        # Actually craft
        result = api.craft_item(scheme_id)

        if ctx.obj.get("json"):
            output_json(result)
        else:
            success(f"Crafted {scheme['name']}!")
            console.print(f"  Result: item #{result.get('template', '?')}")

    finally:
        api.close()
