"""AI commands - manage and deploy AI scripts."""

import re
import time
import click
from pathlib import Path
from ..output import output_json, success, error, console
from ..constants import LEEK_ID
from leekwars_agent.auth import login_api

# Rate limit: wait between API calls to avoid 429
API_DELAY_SECONDS = 1.0


def parse_includes(code: str) -> list[str]:
    """Extract include file names from LeekScript code.

    Matches: include("file.leek") or include('file.leek')
    """
    pattern = r'include\s*\(\s*["\']([^"\']+)["\']\s*\)'
    return re.findall(pattern, code)


def resolve_include_path(include_name: str, base_dir: Path) -> Path | None:
    """Resolve include name to actual file path.

    Searches in: base_dir, ais/, ais/modules/
    """
    search_dirs = [
        base_dir,
        Path("ais"),
        Path("ais/modules"),
        base_dir / "modules",
    ]

    for search_dir in search_dirs:
        candidate = search_dir / include_name
        if candidate.exists():
            return candidate

    return None


def get_or_create_ai(api, name: str, ais_cache: dict) -> int:
    """Get existing AI ID by name or create new one.

    Returns AI ID. Uses ais_cache to avoid repeated API calls.
    """
    if name in ais_cache:
        return ais_cache[name]

    # Fetch all AIs if cache is empty
    if not ais_cache:
        ais_data = api.get_farmer_ais()
        for ai_item in ais_data.get("ais", []):
            ais_cache[ai_item.get("name")] = ai_item.get("id")

    if name in ais_cache:
        return ais_cache[name]

    # Create new AI
    result = api.create_ai(name=name)
    ai_id = result.get("ai", {}).get("id") or result.get("id")
    if ai_id:
        ais_cache[name] = ai_id
    return ai_id


def upload_ai_with_deps(
    api,
    file_path: Path,
    name: str,
    ais_cache: dict,
    uploaded: set,
    console,
    dry_run: bool = False
) -> tuple[int | None, bool]:
    """Upload an AI file and all its dependencies recursively.

    Returns (ai_id, is_valid).
    """
    # Avoid re-uploading
    if name in uploaded:
        return ais_cache.get(name, 0), True

    code = file_path.read_text()
    includes = parse_includes(code)

    # Upload dependencies first
    for include_name in includes:
        dep_path = resolve_include_path(include_name, file_path.parent)
        if dep_path is None:
            console.print(f"  [yellow]⚠ Include not found: {include_name}[/yellow]")
            continue

        dep_name = dep_path.stem
        console.print(f"  → Uploading dependency: {dep_name}")

        dep_id, dep_valid = upload_ai_with_deps(
            api, dep_path, dep_name, ais_cache, uploaded, console, dry_run
        )
        if not dep_valid and not dry_run:
            console.print(f"  [red]✗ Dependency {dep_name} has errors[/red]")

    # In dry-run mode, skip API calls
    if dry_run:
        console.print(f"  [yellow]Would upload {name} ({len(code)} chars)[/yellow]")
        uploaded.add(name)
        return 0, True  # Fake ID for dry-run

    # Get or create AI for this file
    ai_id = get_or_create_ai(api, name, ais_cache)
    if not ai_id:
        console.print(f"  [red]✗ Failed to get/create AI: {name}[/red]")
        return None, False

    # Rate limit before save
    time.sleep(API_DELAY_SECONDS)

    # Save code with retry on 429
    for attempt in range(3):
        try:
            save_result = api.save_ai(ai_id, code)
            break
        except Exception as e:
            if "429" in str(e) and attempt < 2:
                console.print(f"  [yellow]Rate limited, waiting 10s...[/yellow]")
                time.sleep(10)
            else:
                raise
    uploaded.add(name)

    # Check validity
    result_data = save_result.get("result", {})
    # Result can be {ai_id: errors} or {"valid": true}
    is_valid = result_data.get("valid", False)
    if not is_valid and isinstance(result_data, dict):
        # Check if it's error format: {ai_id: [[errors]]}
        for key, val in result_data.items():
            if key != "valid" and isinstance(val, list) and len(val) > 0:
                is_valid = False
                break
        else:
            # No errors found in dict
            is_valid = True if not result_data.get(str(ai_id)) else False

    status = "[green]✓[/green]" if is_valid else "[red]✗[/red]"
    console.print(f"  {status} {name} (#{ai_id})")

    return ai_id, is_valid


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
@click.option("--no-deps", is_flag=True, help="Skip uploading include dependencies")
@click.pass_context
def deploy(ctx: click.Context, file_path: str, name: str | None, dry_run: bool, no_deps: bool) -> None:
    """Deploy a local AI file to your leek.

    Automatically uploads include dependencies (use --no-deps to skip).

    FILE_PATH is the path to your .leek file.

    Examples:
        leek ai deploy ais/fighter_v9.leek          # Upload with all deps
        leek ai deploy ais/fighter_v10.leek         # Self-contained AI
        leek ai deploy ais/test.leek --name "Test"  # Custom name
        leek ai deploy ais/new.leek --dry-run       # Preview only
        leek ai deploy ais/main.leek --no-deps      # Skip dependencies
    """
    path = Path(file_path)

    if name is None:
        name = path.stem  # filename without extension

    # Check for includes
    code = path.read_text()
    includes = parse_includes(code)

    if includes and not no_deps:
        console.print(f"[bold]Deploying {name} with {len(includes)} dependencies[/bold]\n")
    else:
        console.print(f"[bold]Deploying {name}[/bold]\n")

    api = login_api()
    try:
        ais_cache = {}  # name -> id cache
        uploaded = set()  # track uploaded files

        if includes and not no_deps:
            # Multi-file upload with dependencies
            ai_id, is_valid = upload_ai_with_deps(
                api, path, name, ais_cache, uploaded, console, dry_run
            )

            if dry_run:
                success(f"\nDry run complete: would upload {len(uploaded)} files")
                return

            if not ai_id:
                error("Failed to upload AI")
                raise SystemExit(1)

            if not is_valid:
                error("AI has compilation errors (check includes)")
                raise SystemExit(1)
        else:
            # Simple single-file upload (original logic)
            ai_id = get_or_create_ai(api, name, ais_cache)

            if not ai_id:
                error(f"Failed to get/create AI: {name}")
                raise SystemExit(1)

            if dry_run:
                console.print(f"[yellow]Would upload {name} ({len(code)} chars)[/yellow]")
                return

            save_result = api.save_ai(ai_id, code)
            result_data = save_result.get("result", {})
            is_valid = result_data.get("valid", False)

            # Check for error format: {ai_id: [[errors]]}
            if not is_valid and str(ai_id) in result_data:
                errors = result_data[str(ai_id)]
                if errors:
                    console.print(f"[red]Compilation errors:[/red]")
                    for err in errors[:5]:  # Show first 5 errors
                        if isinstance(err, list) and len(err) > 7:
                            line, col, err_type = err[2], err[4], err[6]
                            detail = err[7] if len(err) > 7 else ""
                            console.print(f"  Line {line}:{col} - {detail}")
                    error("AI has compilation errors")
                    raise SystemExit(1)

            status = "[green]✓[/green]" if is_valid else "[yellow]?[/yellow]"
            console.print(f"  {status} {name} (#{ai_id})")

        if dry_run:
            return

        # Set as leek's AI
        api.set_leek_ai(LEEK_ID, ai_id)
        success(f"\nDeployed '{name}' to leek!")

        if ctx.obj.get("json"):
            output_json({
                "ai_id": ai_id,
                "name": name,
                "deployed": True,
                "dependencies": list(uploaded - {name}) if not no_deps else []
            })

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
