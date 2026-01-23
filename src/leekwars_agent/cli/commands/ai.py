"""AI commands - manage and deploy AI scripts."""

import click
from pathlib import Path
from ..output import output_json, success, error, console
from ..constants import LEEK_ID
from leekwars_agent.auth import login_api


@click.group()
def ai():
    """AI management - list, deploy, and test AI scripts."""
    pass


@ai.command("list")
@click.pass_context
def list_ais(ctx: click.Context) -> None:
    """List all farmer's AIs on the server."""
    api = login_api()
    try:
        data = api.get_farmer_ais()
        ais = data.get("ais", [])

        if ctx.obj.get("json"):
            output_json({"ais": ais})
            return

        console.print("[bold]Your AIs[/bold]\n")
        for ai_item in ais:
            ai_id = ai_item.get("id", "?")
            name = ai_item.get("name", "?")
            valid = "✓" if ai_item.get("valid") else "✗"
            lines = ai_item.get("total_lines", 0)
            console.print(f"  [{valid}] #{ai_id:6d} {name:20s} ({lines} lines)")

    finally:
        api.close()


@ai.command("current")
@click.pass_context
def current_ai(ctx: click.Context) -> None:
    """Show which AI is currently deployed to your leek."""
    api = login_api()
    try:
        data = api.get_leek(LEEK_ID)
        leek = data.get("leek", data)
        ai_info = leek.get("ai", {})

        if ctx.obj.get("json"):
            output_json(ai_info)
            return

        name = ai_info.get("name", "None")
        ai_id = ai_info.get("id", "?")
        valid = "[green]✓[/green]" if ai_info.get("valid") else "[red]✗[/red]"
        lines = ai_info.get("total_lines", 0)

        console.print(f"[bold]Current AI[/bold]: {name}")
        console.print(f"  ID: {ai_id}")
        console.print(f"  Valid: {valid}")
        console.print(f"  Lines: {lines}")

    finally:
        api.close()


@ai.command("deploy")
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--name", "-n", help="Name for the AI (defaults to filename)")
@click.option("--dry-run", is_flag=True, help="Validate without deploying")
@click.pass_context
def deploy(ctx: click.Context, file_path: str, name: str | None, dry_run: bool) -> None:
    """Deploy a local AI file to your leek.

    FILE_PATH is the path to your .leek file.

    Examples:
        leek ai deploy ais/fighter_v10.leek
        leek ai deploy ais/test.leek --name "Experimental"
        leek ai deploy ais/new.leek --dry-run
    """
    path = Path(file_path)
    code = path.read_text()

    if name is None:
        name = path.stem  # filename without extension

    api = login_api()
    try:
        # Find existing AI with same name or create new
        ais_data = api.get_farmer_ais()
        ais = ais_data.get("ais", [])

        existing = None
        for ai_item in ais:
            if ai_item.get("name") == name:
                existing = ai_item
                break

        if existing:
            ai_id = existing.get("id")
            console.print(f"Updating existing AI '{name}' (#{ai_id})...")
        else:
            # Create new AI
            if dry_run:
                console.print(f"[yellow]Would create new AI '{name}'[/yellow]")
                return

            result = api.create_ai(name=name)
            ai_id = result.get("ai", {}).get("id") or result.get("id")
            if not ai_id:
                error(f"Failed to create AI: {result}")
                raise SystemExit(1)
            console.print(f"Created new AI '{name}' (#{ai_id})")

        if dry_run:
            console.print(f"[yellow]Would update AI #{ai_id} with {len(code)} chars[/yellow]")
            return

        # Save code
        save_result = api.save_ai(ai_id, code)

        # Check if valid
        if save_result.get("result") and save_result["result"].get("valid"):
            success(f"AI '{name}' saved and valid!")
        else:
            error(f"AI saved but has errors: {save_result}")
            raise SystemExit(1)

        # Set as leek's AI
        api.set_leek_ai(LEEK_ID, ai_id)
        success(f"Deployed '{name}' to leek!")

        if ctx.obj.get("json"):
            output_json({"ai_id": ai_id, "name": name, "deployed": True})

    finally:
        api.close()


@ai.command("local")
@click.option("--path", "-p", default="ais", help="Directory to scan")
@click.pass_context
def local_ais(ctx: click.Context, path: str) -> None:
    """List local AI files in the ais/ directory."""
    ai_dir = Path(path)
    if not ai_dir.exists():
        error(f"Directory not found: {path}")
        raise SystemExit(1)

    files = list(ai_dir.glob("*.leek"))
    files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

    if ctx.obj.get("json"):
        output_json({"files": [str(f) for f in files]})
        return

    console.print(f"[bold]Local AIs[/bold] ({path}/)\n")
    for f in files:
        size = f.stat().st_size
        lines = len(f.read_text().splitlines())
        console.print(f"  {f.name:25s} ({lines:4d} lines, {size:5d} bytes)")
