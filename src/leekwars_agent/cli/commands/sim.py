"""Simulation commands - test AIs offline with real specs."""

import json
import subprocess
import sys
import click
from pathlib import Path
from ..output import output_json, success, error, console
from ..constants import LEEK_ID
from leekwars_agent.auth import login_api

# Default chips (from GROUND_TRUTH.md)
DEFAULT_CHIPS = [4, 5, 6, 8, 14, 15]  # CURE, FLAME, FLASH, PROTEIN, BOOTS, MOTIVATION
CHIP_NAMES = {4: "CURE", 5: "FLAME", 6: "FLASH", 8: "PROTEIN", 14: "BOOTS", 15: "MOTIVATION"}


@click.group()
def sim():
    """Simulation - test AIs offline with real leek specs."""
    pass


@sim.command("specs")
@click.pass_context
def show_specs(ctx: click.Context) -> None:
    """Show your leek's specs as simulator args.

    Outputs the exact command to test AIs with your real stats.
    """
    api = login_api()
    try:
        data = api.get_leek(LEEK_ID)
        leek = data.get("leek", data)

        specs = {
            "level": leek.get("level", 1),
            "life": leek.get("life", 100),
            "tp": leek.get("tp", 10),
            "mp": leek.get("mp", 3),
            "strength": leek.get("strength", 0),
            "agility": leek.get("agility", 0),
            "frequency": leek.get("frequency", 100),
            "wisdom": leek.get("wisdom", 0),
            "resistance": leek.get("resistance", 0),
            "science": leek.get("science", 0),
            "magic": leek.get("magic", 0),
        }

        # Get chip template IDs
        chips = [c.get("template") for c in leek.get("chips", [])]
        chips_str = ",".join(str(c) for c in chips) if chips else ""

        # Get weapon template IDs
        weapons = [w.get("template") for w in leek.get("weapons", [])]

        if ctx.obj.get("json"):
            output_json({
                "specs": specs,
                "chips": chips,
                "weapons": weapons,
            })
            return

        console.print("[bold]Your Leek Specs for Simulation[/bold]\n")

        # Show as CLI args
        args = []
        args.append(f"--level {specs['level']}")
        args.append(f"--str1 {specs['strength']} --str2 {specs['strength']}")
        args.append(f"--agi1 {specs['agility']} --agi2 {specs['agility']}")
        args.append(f"--life1 {specs['life']} --life2 {specs['life']}")
        args.append(f"--tp1 {specs['tp']} --tp2 {specs['tp']}")
        args.append(f"--mp1 {specs['mp']} --mp2 {specs['mp']}")
        if chips_str:
            args.append(f"--chips1 {chips_str} --chips2 {chips_str}")

        console.print("[cyan]Copy-paste command:[/cyan]")
        console.print(f"  poetry run python scripts/compare_ais.py ai1.leek ai2.leek -n 100 \\")
        for arg in args[:-1]:
            console.print(f"    {arg} \\")
        console.print(f"    {args[-1]}")

        console.print(f"\n[dim]Chips: {chips}[/dim]")
        console.print(f"[dim]Weapons: {weapons}[/dim]")

    finally:
        api.close()


@sim.command("compare")
@click.argument("ai1", type=click.Path(exists=True))
@click.argument("ai2", type=click.Path(exists=True))
@click.option("-n", "--num-fights", type=int, default=100, help="Number of fights")
@click.option("--real-specs/--no-real-specs", default=True, help="Use your leek's real stats")
@click.pass_context
def compare(ctx: click.Context, ai1: str, ai2: str, num_fights: int, real_specs: bool) -> None:
    """Compare two AIs using your real leek specs.

    By default, loads your leek's actual stats, chips, and level.

    Examples:
        leek sim compare ais/fighter_v10.leek ais/fighter_v6.leek
        leek sim compare v10.leek v6.leek -n 500
        leek sim compare v10.leek v6.leek --no-real-specs  # Level 1, no stats
    """
    import subprocess
    import sys

    # Build command
    cmd = [
        sys.executable, "scripts/compare_ais.py",
        ai1, ai2,
        "-n", str(num_fights),
    ]

    if real_specs:
        api = login_api()
        try:
            data = api.get_leek(LEEK_ID)
            leek = data.get("leek", data)

            level = leek.get("level", 1)
            strength = leek.get("strength", 0)
            agility = leek.get("agility", 0)
            frequency = leek.get("frequency", 100)
            wisdom = leek.get("wisdom", 0)
            resistance = leek.get("resistance", 0)
            science = leek.get("science", 0)
            magic = leek.get("magic", 0)
            life = leek.get("life", 100)
            tp = leek.get("tp", 10)
            mp = leek.get("mp", 3)

            chips = [c.get("template") for c in leek.get("chips", [])]
            chips_str = ",".join(str(c) for c in chips) if chips else ""

            # Add to command
            cmd.extend(["--level", str(level)])
            cmd.extend(["--str1", str(strength), "--str2", str(strength)])
            cmd.extend(["--agi1", str(agility), "--agi2", str(agility)])
            cmd.extend(["--freq1", str(frequency), "--freq2", str(frequency)])
            cmd.extend(["--wis1", str(wisdom), "--wis2", str(wisdom)])
            cmd.extend(["--res1", str(resistance), "--res2", str(resistance)])
            cmd.extend(["--sci1", str(science), "--sci2", str(science)])
            cmd.extend(["--mag1", str(magic), "--mag2", str(magic)])
            cmd.extend(["--life1", str(life), "--life2", str(life)])
            cmd.extend(["--tp1", str(tp), "--tp2", str(tp)])
            cmd.extend(["--mp1", str(mp), "--mp2", str(mp)])
            if chips_str:
                cmd.extend(["--chips1", chips_str, "--chips2", chips_str])

            console.print(f"[bold]Simulating with real specs:[/bold] L{level} STR={strength} AGI={agility}")
            console.print(f"[dim]Chips: {chips}[/dim]\n")

        finally:
            api.close()
    else:
        console.print("[bold]Simulating with base stats (L1, no chips)[/bold]\n")

    # Run simulation
    result = subprocess.run(cmd, capture_output=False)

    if result.returncode != 0:
        error("Simulation failed")
        raise SystemExit(1)


@sim.command("debug")
@click.argument("ai1", type=click.Path(exists=True))
@click.argument("ai2", type=click.Path(exists=True))
@click.option("--real-specs/--no-real-specs", default=True, help="Use your leek's real stats")
@click.pass_context
def debug_fight(ctx: click.Context, ai1: str, ai2: str, real_specs: bool) -> None:
    """Run a single fight with verbose output for debugging.

    Shows turn-by-turn actions and AI debug() output.
    """
    import subprocess
    import sys

    cmd = [sys.executable, "scripts/debug_fight.py", ai1, ai2]

    if real_specs:
        api = login_api()
        try:
            data = api.get_leek(LEEK_ID)
            leek = data.get("leek", data)

            level = leek.get("level", 1)
            strength = leek.get("strength", 0)

            chips = [c.get("template") for c in leek.get("chips", [])]
            chips_str = ",".join(str(c) for c in chips) if chips else ""

            cmd.extend(["--level", str(level)])
            cmd.extend(["--str1", str(strength), "--str2", str(strength)])
            if chips_str:
                cmd.extend(["--chips1", chips_str, "--chips2", chips_str])

            console.print(f"[bold]Debug fight with real specs:[/bold] L{level} STR={strength}")
            console.print(f"[dim]Chips: {chips}[/dim]\n")

        finally:
            api.close()

    result = subprocess.run(cmd, capture_output=False)

    if result.returncode != 0:
        error("Debug fight failed")
        raise SystemExit(1)


@sim.command("chips")
@click.option("-v", "--verbose", is_flag=True, help="Show detailed chip loading info")
@click.pass_context
def test_chips(ctx: click.Context, verbose: bool) -> None:
    """Test that chips load correctly in the simulator.

    Validates that getChips() returns the expected chips during offline simulation.
    This is a diagnostic tool to verify the simulator setup.

    Examples:
        leek sim chips           # Quick validation
        leek sim chips --verbose # Detailed output
    """
    cmd = [sys.executable, "scripts/test_chips.py"]
    if verbose:
        cmd.append("--verbose")

    console.print("[bold]Testing chip loading in simulator...[/bold]\n")
    result = subprocess.run(cmd, capture_output=False)

    if result.returncode != 0:
        error("Chip test failed - see output above")
        raise SystemExit(1)
    else:
        success("Chip loading validated!")
