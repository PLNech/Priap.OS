"""AI commands - manage and deploy AI scripts."""

import re
import time
import click
from pathlib import Path
from ..output import output_json, success, error, console
from ..constants import LEEK_ID  # unused but kept for backward compat
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


def get_or_create_ai(api, name: str, ais_cache: dict) -> str:
    """Get existing AI path by name or create new one.

    Post-April-2026 migration: AIs are keyed by `path` (string name), not
    numeric ID. Returns the path. `ais_cache` now maps name -> path.
    """
    if name in ais_cache:
        return ais_cache[name]

    # Populate cache from login response (no extra API call)
    if not ais_cache:
        for f in api.list_farmer_ais():
            p = f.get("path")
            if p:
                ais_cache[p] = p

    if name in ais_cache:
        return ais_cache[name]

    # Create new AI; response carries the assigned path
    result = api.create_ai(name=name)
    ai_path = result.get("path") or name
    ais_cache[ai_path] = ai_path
    return ai_path


def upload_ai_with_deps(
    api,
    file_path: Path,
    name: str,
    ais_cache: dict,
    uploaded: set,
    console,
    dry_run: bool = False
) -> tuple[str | None, bool]:
    """Upload an AI file and all its dependencies recursively.

    Returns (ai_path, is_valid). Post-April-2026: AIs are keyed by path.
    """
    # Avoid re-uploading
    if name in uploaded:
        return ais_cache.get(name, name), True

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
        return name, True  # Path placeholder for dry-run

    # Get or create AI for this file (returns path)
    ai_path = get_or_create_ai(api, name, ais_cache)
    if not ai_path:
        console.print(f"  [red]✗ Failed to get/create AI: {name}[/red]")
        return None, False

    # Rate limit before save
    time.sleep(API_DELAY_SECONDS)

    # Save code with retry on 429
    for attempt in range(3):
        try:
            save_result = api.write_ai(ai_path, code)
            break
        except Exception as e:
            if "429" in str(e) and attempt < 2:
                console.print(f"  [yellow]Rate limited, waiting 10s...[/yellow]")
                time.sleep(10)
            else:
                raise
    uploaded.add(name)

    # Check validity. /ai/write returns {"result": {path: errors[]}, "modified": ts}.
    # An empty error list means clean compile.
    result_data = save_result.get("result", {})
    path_errors = result_data.get(ai_path, []) if isinstance(result_data, dict) else []
    is_valid = isinstance(path_errors, list) and len(path_errors) == 0

    status = "[green]✓[/green]" if is_valid else "[red]✗[/red]"
    console.print(f"  {status} {name} (path={ai_path})")

    return ai_path, is_valid


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
        ais = api.list_farmer_ais()

        if ctx.obj.get("json"):
            output_json({"ais": ais})
            return

        console.print("[bold]Your AIs[/bold]\n")
        for ai_item in ais:
            path = ai_item.get("path", "?")
            valid = "✓" if ai_item.get("valid") else "✗"
            lines = ai_item.get("total_lines", 0)
            entry = "↪" if ai_item.get("entrypoint") else " "
            console.print(f"  [{valid}] {entry} {path:30s} ({lines} lines)")

    finally:
        api.close()


SOTA_SYMLINK = Path(__file__).resolve().parents[4] / "ais" / "current"


def _get_local_sota() -> tuple[str | None, Path | None]:
    """Read ais/current symlink. Returns (target_name, resolved_path) or (None, None)."""
    if not SOTA_SYMLINK.is_symlink():
        return None, None
    target = Path(SOTA_SYMLINK.readlink())
    resolved = SOTA_SYMLINK.parent / target
    return target.stem, resolved if resolved.exists() else None


def _update_sota_symlink(file_path: Path) -> None:
    """Update ais/current symlink to point at the deployed file."""
    SOTA_SYMLINK.unlink(missing_ok=True)
    # Relative symlink within ais/
    SOTA_SYMLINK.symlink_to(file_path.name)


@ai.command("status")
@click.pass_context
def status(ctx: click.Context) -> None:
    """Show deployed AI status: server state + local SOTA pointer."""
    leek_id = ctx.obj["leek_id"]
    api = login_api()
    try:
        data = api.get_leek(leek_id)
        leek = data.get("leek", data)
        ai_info = leek.get("ai", {})

        server_name = ai_info.get("name", "None")
        ai_id = ai_info.get("id", "?")
        is_valid = ai_info.get("valid", False)
        lines = ai_info.get("total_lines", 0)

        local_name, local_path = _get_local_sota()
        local_lines = len(local_path.read_text().splitlines()) if local_path else 0

        # Check sync
        in_sync = local_name == server_name if local_name else False

        if ctx.obj.get("json"):
            output_json({
                "server": {"name": server_name, "id": ai_id, "valid": is_valid, "lines": lines},
                "local": {"name": local_name, "file": str(local_path) if local_path else None, "lines": local_lines},
                "in_sync": in_sync,
            })
            return

        valid_icon = "[green]✓[/green]" if is_valid else "[red]✗[/red]"
        sync_icon = "[green]✓ synced[/green]" if in_sync else "[red]✗ out of sync[/red]"

        console.print(f"[bold]AI Status[/bold]")
        console.print(f"  Server: {server_name} (#{ai_id}) {valid_icon} — {lines} lines")
        if local_name:
            console.print(f"  Local:  ais/current → {local_name}.leek — {local_lines} lines")
        else:
            console.print(f"  Local:  [yellow]no ais/current symlink[/yellow]")
        console.print(f"  Sync:   {sync_icon}")

    finally:
        api.close()


@ai.command("current")
@click.pass_context
def current_ai(ctx: click.Context) -> None:
    """Show which AI is currently deployed to your leek."""
    leek_id = ctx.obj["leek_id"]
    api = login_api()
    try:
        data = api.get_leek(leek_id)
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
        ais_cache = {}  # name -> path cache (post-April-2026: path == name)
        uploaded = set()

        if includes and not no_deps:
            # Multi-file upload with dependencies
            ai_path, is_valid = upload_ai_with_deps(
                api, path, name, ais_cache, uploaded, console, dry_run
            )

            if dry_run:
                success(f"\nDry run complete: would upload {len(uploaded)} files")
                return

            if not ai_path:
                error("Failed to upload AI")
                raise SystemExit(1)

            if not is_valid:
                error("AI has compilation errors (check includes)")
                raise SystemExit(1)
        else:
            # Simple single-file upload
            ai_path = get_or_create_ai(api, name, ais_cache)

            if not ai_path:
                error(f"Failed to get/create AI: {name}")
                raise SystemExit(1)

            if dry_run:
                console.print(f"[yellow]Would upload {name} ({len(code)} chars)[/yellow]")
                return

            save_result = api.write_ai(ai_path, code)
            result_data = save_result.get("result", {})
            path_errors = result_data.get(ai_path, []) if isinstance(result_data, dict) else []
            is_valid = isinstance(path_errors, list) and len(path_errors) == 0

            if not is_valid and path_errors:
                console.print(f"[red]Compilation errors:[/red]")
                for err in path_errors[:5]:
                    if isinstance(err, list) and len(err) > 7:
                        line, col = err[2], err[4]
                        detail = err[7] if len(err) > 7 else ""
                        console.print(f"  Line {line}:{col} - {detail}")
                error("AI has compilation errors")
                raise SystemExit(1)

            status = "[green]✓[/green]"
            console.print(f"  {status} {name} (path={ai_path})")

        if dry_run:
            return

        # Assign to leek by path
        leek_id = ctx.obj["leek_id"]
        api.set_leek_ai(leek_id, ai_path)

        _update_sota_symlink(path)
        success(f"\nDeployed '{name}' to leek!")

        if ctx.obj.get("json"):
            output_json({
                "ai_path": ai_path,
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
