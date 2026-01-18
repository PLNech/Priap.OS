#!/usr/bin/env python3
"""Visualize a fight with map, positions, and action log.

Produces ASCII visualization of the fight turn-by-turn.

Usage:
    poetry run python scripts/visualize_fight.py 50529694
    poetry run python scripts/visualize_fight.py 50529694 --turn 3
"""

import argparse
import json
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).parent.parent / "fights_light.db"

# Action codes
class ActionCode:
    START_FIGHT = 0
    END_FIGHT = 4
    PLAYER_DEAD = 5
    NEW_TURN = 6
    LEEK_TURN = 7
    END_TURN = 8
    SUMMON = 9
    MOVE_TO = 10
    KILL = 11
    USE_CHIP = 12
    SET_WEAPON = 13
    USE_WEAPON = 16
    LOST_TP = 100
    LOST_LIFE = 101
    LOST_MP = 102
    HEAL = 103


@dataclass
class LeekState:
    """Current state of a leek during fight replay."""
    id: int
    name: str
    team: int
    cell: int
    life: int
    max_life: int
    tp: int
    mp: int
    strength: int
    agility: int
    dead: bool = False


@dataclass
class FightReplay:
    """Full fight replay with map and states."""
    fight_id: int
    winner: int
    map_width: int
    map_height: int
    obstacles: dict[int, int]  # cell -> obstacle_type
    leeks: dict[int, LeekState]  # id -> state
    actions: list[list]

    def get_cell_count(self) -> int:
        """Calculate total cells in diamond map.

        Formula: (width * 2 - 1) * width - (width - 1)
        For width=18: 35 * 18 - 17 = 613 cells
        """
        w = self.map_width
        return (w * 2 - 1) * w - (w - 1)

    def cell_to_xy(self, cell: int) -> tuple[int, int]:
        """Convert cell ID to x,y coordinates.

        From leek-wars-generator Cell.java:
        ```java
        int x = id % (width * 2 - 1);
        int y = id / (width * 2 - 1);
        this.y = y - x % width;
        this.x = (id - (width - 1) * this.y) / width;
        ```
        """
        w = self.map_width
        stride = w * 2 - 1  # 35 for width=18

        x_temp = cell % stride
        y_temp = cell // stride

        y = y_temp - (x_temp % w)
        x = (cell - (w - 1) * y) // w

        return (x, y)

    def xy_to_cell(self, x: int, y: int) -> int:
        """Convert x,y coordinates back to cell ID."""
        w = self.map_width
        return x * w + y * (w - 1)


def load_fight(fight_id: int) -> FightReplay | None:
    """Load fight from database."""
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT json_data FROM fights WHERE fight_id = ?", [fight_id]).fetchone()
    conn.close()

    if not row:
        return None

    fight_data = json.loads(row[0])
    data = fight_data.get("data", {})
    map_data = data.get("map", {})

    # Parse obstacles
    obstacles = {}
    for cell_str, obs_type in map_data.get("obstacles", {}).items():
        obstacles[int(cell_str)] = obs_type

    # Parse leeks
    leeks = {}
    for leek in data.get("leeks", []):
        leeks[leek["id"]] = LeekState(
            id=leek["id"],
            name=leek["name"],
            team=leek["team"],
            cell=leek["cellPos"],
            life=leek["life"],
            max_life=leek["life"],
            tp=leek["tp"],
            mp=leek["mp"],
            strength=leek.get("strength", 0),
            agility=leek.get("agility", 0),
        )

    return FightReplay(
        fight_id=fight_id,
        winner=fight_data.get("winner", 0),
        map_width=map_data.get("width", 18),
        map_height=map_data.get("height", 18),
        obstacles=obstacles,
        leeks=leeks,
        actions=data.get("actions", []),
    )


def render_map(replay: FightReplay, positions: dict[int, int], highlight_cells: set[int] = None) -> str:
    """Render ASCII map with current positions.

    The LeekWars map is an 18x18 diamond grid. We render it rotated 45° so it
    appears as a square in the terminal.

    Args:
        replay: Fight replay data
        positions: leek_id -> cell mapping
        highlight_cells: Cells to highlight (e.g., weapon range, path)
    """
    w = replay.map_width
    highlight_cells = highlight_cells or set()

    # Build cell -> content mapping
    cell_content = {}

    # Mark obstacles
    for cell, obs_type in replay.obstacles.items():
        cell_content[cell] = "##" if obs_type == 1 else "&&"

    # Mark leek positions (override obstacles)
    for leek_id, cell in positions.items():
        leek = replay.leeks.get(leek_id)
        if leek and not leek.dead:
            marker = leek.name[0].upper()
            if leek.team == 1:
                cell_content[cell] = f"\033[92m{marker}1\033[0m"  # Green
            else:
                cell_content[cell] = f"\033[91m{marker}2\033[0m"  # Red

    # Build coordinate lookup
    all_cells = list(range(replay.get_cell_count()))
    xy_to_cell = {}
    for cell in all_cells:
        x, y = replay.cell_to_xy(cell)
        xy_to_cell[(x, y)] = cell

    # Find bounds
    all_xy = list(xy_to_cell.keys())
    min_x = min(c[0] for c in all_xy)
    max_x = max(c[0] for c in all_xy)
    min_y = min(c[1] for c in all_xy)
    max_y = max(c[1] for c in all_xy)

    # Render as a simple grid (x across, y down)
    lines = []
    for y in range(min_y, max_y + 1):
        row = []
        for x in range(min_x, max_x + 1):
            if (x, y) in xy_to_cell:
                cell = xy_to_cell[(x, y)]
                if cell in cell_content:
                    row.append(cell_content[cell])
                elif cell in highlight_cells:
                    row.append("><")
                else:
                    row.append("··")
            else:
                row.append("  ")  # Empty space (not a valid cell)
        lines.append(" ".join(row))

    return "\n".join(lines)


def format_action(action: list, leeks: dict[int, LeekState], current_entity: int | None) -> str | None:
    """Format a single action as human-readable string."""
    code = action[0]

    def get_name(entity_id: int) -> str:
        return leeks.get(entity_id, LeekState(entity_id, f"E{entity_id}", 0, 0, 0, 0, 0, 0, 0, 0)).name

    if code == ActionCode.NEW_TURN:
        turn_num = action[1] if len(action) > 1 else "?"
        return f"\n{'='*50}\n  TURN {turn_num}\n{'='*50}"

    elif code == ActionCode.LEEK_TURN:
        entity = action[1] if len(action) > 1 else None
        name = get_name(entity) if entity is not None else "?"
        team = leeks.get(entity, LeekState(0, "", 0, 0, 0, 0, 0, 0, 0, 0)).team
        return f"\n  [{name}]'s turn (Team {team})"

    elif code == ActionCode.MOVE_TO:
        # [10, entity_id, dest_cell, path]
        entity = action[1] if len(action) > 1 else None
        dest = action[2] if len(action) > 2 else "?"
        path = action[3] if len(action) > 3 and isinstance(action[3], list) else []
        name = get_name(entity) if entity is not None else "?"
        return f"    → MOVE {name}: {' → '.join(map(str, path))} (dest: {dest})"

    elif code == ActionCode.USE_WEAPON:
        # [16, target_cell, weapon_id]
        target_cell = action[1] if len(action) > 1 else "?"
        weapon_id = action[2] if len(action) > 2 else "?"
        return f"    ⚔ WEAPON at cell {target_cell} (weapon #{weapon_id})"

    elif code == ActionCode.USE_CHIP:
        # [12, chip_id, target_cell, level?]
        chip_id = action[1] if len(action) > 1 else "?"
        target_cell = action[2] if len(action) > 2 else "?"
        return f"    ✦ CHIP #{chip_id} at cell {target_cell}"

    elif code == ActionCode.LOST_LIFE:
        # [101, target_id, damage, source_id?]
        target = action[1] if len(action) > 1 else "?"
        damage = action[2] if len(action) > 2 else 0
        name = get_name(target) if isinstance(target, int) else "?"
        return f"    💔 {name} takes {damage} damage"

    elif code == ActionCode.HEAL:
        # [103, target_id, amount, ???]
        target = action[1] if len(action) > 1 else "?"
        amount = action[2] if len(action) > 2 else 0
        name = get_name(target) if isinstance(target, int) else "?"
        return f"    💚 {name} heals {amount}"

    elif code == ActionCode.PLAYER_DEAD:
        entity = action[1] if len(action) > 1 else "?"
        name = get_name(entity) if isinstance(entity, int) else "?"
        return f"    💀 {name} DIES!"

    elif code == ActionCode.SET_WEAPON:
        # [13, weapon_id]
        weapon = action[1] if len(action) > 1 else "?"
        return f"    🔧 Set weapon #{weapon}"

    elif code == ActionCode.END_TURN:
        return None  # Skip

    elif code == ActionCode.END_FIGHT:
        return f"\n{'='*50}\n  FIGHT ENDS\n{'='*50}"

    # Effect codes (300+)
    elif code >= 300:
        return None  # Skip effect details for cleaner output

    return None  # Skip unknown actions


def replay_fight(replay: FightReplay, stop_at_turn: int | None = None, show_map_every_turn: bool = True):
    """Replay fight with visualization."""

    print(f"\n{'#'*60}")
    print(f"  FIGHT {replay.fight_id}")
    print(f"  Winner: Team {replay.winner}")
    print(f"{'#'*60}")

    # Print leek info
    print("\n  COMBATANTS:")
    for leek in replay.leeks.values():
        team_color = "\033[92m" if leek.team == 1 else "\033[91m"
        print(f"  {team_color}[Team {leek.team}]\033[0m {leek.name}")
        print(f"          HP: {leek.life}  STR: {leek.strength}  AGI: {leek.agility}")
        print(f"          TP: {leek.tp}  MP: {leek.mp}  Start cell: {leek.cell}")

    # Initial positions
    positions = {leek.id: leek.cell for leek in replay.leeks.values()}

    print("\n  INITIAL MAP:")
    print(render_map(replay, positions))

    # Track state
    current_turn = 0
    current_entity = None

    for action in replay.actions:
        code = action[0]

        # Update turn tracking
        if code == ActionCode.NEW_TURN:
            current_turn = action[1] if len(action) > 1 else current_turn + 1
            if stop_at_turn and current_turn > stop_at_turn:
                break

        elif code == ActionCode.LEEK_TURN:
            current_entity = action[1] if len(action) > 1 else None

        # Update positions on move
        elif code == ActionCode.MOVE_TO:
            entity = action[1] if len(action) > 1 else None
            dest = action[2] if len(action) > 2 else None
            if entity is not None and dest is not None:
                positions[entity] = dest

        # Update life on damage
        elif code == ActionCode.LOST_LIFE:
            target = action[1] if len(action) > 1 else None
            damage = action[2] if len(action) > 2 else 0
            if target in replay.leeks:
                replay.leeks[target].life -= damage

        # Mark dead
        elif code == ActionCode.PLAYER_DEAD:
            entity = action[1] if len(action) > 1 else None
            if entity in replay.leeks:
                replay.leeks[entity].dead = True

        # Format and print action
        formatted = format_action(action, replay.leeks, current_entity)
        if formatted:
            print(formatted)

            # Show map after significant actions
            if show_map_every_turn and code in [ActionCode.NEW_TURN]:
                print("\n  MAP STATE:")
                print(render_map(replay, positions))

                # Show HP status
                print("\n  HP STATUS:")
                for leek in replay.leeks.values():
                    bar_len = 20
                    filled = int(bar_len * max(0, leek.life) / leek.max_life)
                    bar = "█" * filled + "░" * (bar_len - filled)
                    status = "DEAD" if leek.dead else f"{leek.life}/{leek.max_life}"
                    team_color = "\033[92m" if leek.team == 1 else "\033[91m"
                    print(f"    {team_color}{leek.name}\033[0m [{bar}] {status}")

    # Final state
    print("\n  FINAL MAP:")
    print(render_map(replay, positions))

    print(f"\n  RESULT: Team {replay.winner} wins!")


def main():
    parser = argparse.ArgumentParser(description="Visualize a fight")
    parser.add_argument("fight_id", type=int, help="Fight ID to visualize")
    parser.add_argument("--turn", type=int, help="Stop at specific turn")
    parser.add_argument("--no-map", action="store_true", help="Don't show map each turn")
    args = parser.parse_args()

    if not DB_PATH.exists():
        print(f"Database not found: {DB_PATH}")
        return

    replay = load_fight(args.fight_id)
    if not replay:
        print(f"Fight {args.fight_id} not found")
        return

    replay_fight(replay, stop_at_turn=args.turn, show_map_every_turn=not args.no_map)


if __name__ == "__main__":
    main()
