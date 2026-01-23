"""Trophy commands - check and hunt trophies."""

import click
from ..output import output_json, console
from ..constants import FARMER_ID
from leekwars_agent.auth import login_api


# Enigma trophies with known unlock methods
ENIGMA_TROPHIES = {
    113: {"code": "konami", "habs": 40000, "hint": "Konami code: ↑↑↓↓←→←→BA"},
    234: {"code": "you_can_see_me", "habs": 2500, "hint": "Toggle SFW mode in settings"},
    92: {"code": "lucky", "habs": 90000, "hint": "Click clovers when they appear"},
    325: {"code": "eagle", "habs": 0, "hint": "Click 100 clovers total"},
    87: {"code": "mathematician", "habs": 250000, "hint": "Walk on 50 PRIME cells in fights"},
    323: {"code": "lost", "habs": 810000, "hint": "??? (Only 37 players have it!)"},
    188: {"code": "xii", "habs": 810000, "hint": "Consume 12 12 12 12 12 ops in one fight"},
    231: {"code": "9_34", "habs": 360000, "hint": "??? Platform 9¾"},
    187: {"code": "shhh", "habs": 250000, "hint": "??? Secret..."},
    51: {"code": "serge", "habs": 40000, "hint": "??? Who is Serge?"},
    112: {"code": "fish", "habs": 0, "hint": "April Fools (April 1st)"},
}


@click.group()
def trophy():
    """Trophy status and enigma hunting."""
    pass


@trophy.command("status")
@click.pass_context
def trophy_status(ctx: click.Context) -> None:
    """Check your enigma trophy status."""
    api = login_api()
    try:
        # Get trophy data
        resp = api._client.get(f"/trophy/get-farmer-trophies/{FARMER_ID}/en")
        data = resp.json()
        trophies = data.get("trophies", [])

        # Build lookup
        trophy_lookup = {t["id"]: t for t in trophies}

        total_available = 0
        total_earned = 0

        results = []
        for tid, info in sorted(ENIGMA_TROPHIES.items(), key=lambda x: -x[1]["habs"]):
            t = trophy_lookup.get(tid, {})
            unlocked = t.get("unlocked", False)
            habs = info["habs"]

            if unlocked:
                total_earned += habs
            else:
                total_available += habs

            results.append({
                "id": tid,
                "code": info["code"],
                "habs": habs,
                "unlocked": unlocked,
                "hint": info["hint"],
            })

        if ctx.obj.get("json"):
            output_json({
                "trophies": results,
                "earned": total_earned,
                "available": total_available,
            })
            return

        # Pretty output
        console.print("[bold cyan]═══ Enigma Trophy Status ═══[/bold cyan]\n")

        for r in results:
            status = "[green]✅[/green]" if r["unlocked"] else "[red]❌[/red]"
            habs_str = f"{r['habs']:>7,}" if r["habs"] > 0 else "      0"
            hint = "" if r["unlocked"] else f" - {r['hint']}"
            console.print(f"  {status} {r['code']:20} {habs_str} habs{hint}")

        console.print(f"\n[bold]Earned:[/bold]    [green]{total_earned:>10,}[/green] habs")
        console.print(f"[bold]Available:[/bold] [yellow]{total_available:>10,}[/yellow] habs")

        # Get current balance
        inv = api.get_inventory()
        current_habs = inv.get("habs", 0)
        console.print(f"\n[bold]Current balance:[/bold] {current_habs:,} habs")

        # Tips
        console.print("\n[dim]Quick wins:[/dim]")
        console.print("[dim]  • Konami: Press ↑↑↓↓←→←→BA anywhere[/dim]")
        console.print("[dim]  • SFW: Toggle Safe-For-Work in /settings[/dim]")

    finally:
        api.close()


@trophy.command("list")
@click.option("-c", "--category", type=str, help="Filter by category")
@click.pass_context
def trophy_list(ctx: click.Context, category: str) -> None:
    """List all trophies (warning: long output)."""
    api = login_api()
    try:
        resp = api._client.get(f"/trophy/get-farmer-trophies/{FARMER_ID}/en")
        data = resp.json()

        count = data.get("count", 0)
        total = data.get("total", 0)
        trophies = data.get("trophies", [])

        # Calculate habs from unlocked
        habs_earned = sum(t.get("habs", 0) for t in trophies if t.get("unlocked"))

        if ctx.obj.get("json"):
            output_json({
                "count": count,
                "total": total,
                "habs_earned": habs_earned,
                "trophies": trophies if not category else [
                    t for t in trophies if str(t.get("category")) == category
                ],
            })
            return

        console.print(f"[bold]Trophies:[/bold] {count}/{total} unlocked")
        console.print(f"[bold]Habs earned from trophies:[/bold] {habs_earned:,}\n")

        # Group by category
        from collections import defaultdict
        by_cat = defaultdict(list)
        for t in trophies:
            by_cat[t.get("category", 0)].append(t)

        cat_names = {
            1: "General", 2: "Code", 3: "Fight", 4: "Fun",
            5: "Social", 6: "Bonus", 7: "Shopping", 8: "Tournament", 9: "Boss"
        }

        for cat_id, cat_trophies in sorted(by_cat.items()):
            if category and str(cat_id) != category:
                continue
            unlocked = sum(1 for t in cat_trophies if t.get("unlocked"))
            console.print(f"[bold]{cat_names.get(cat_id, f'Cat {cat_id}')}:[/bold] {unlocked}/{len(cat_trophies)}")

    finally:
        api.close()
