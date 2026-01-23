"""Fight visualizer for debugging and analysis.

Provides text-based replay and simple graphical visualization.
"""

import json
from dataclasses import dataclass, field
from typing import Any


# Action type constants (from generator Action.java)
ACTION_START_FIGHT = 0
ACTION_END_FIGHT = 4
ACTION_PLAYER_DEAD = 5
ACTION_NEW_TURN = 6
ACTION_ENTITY_TURN = 7
ACTION_END_TURN = 8
ACTION_SUMMON = 9
ACTION_MOVE_TO = 10
ACTION_KILL = 11
ACTION_USE_CHIP = 12
ACTION_SET_WEAPON = 13
ACTION_STACK_EFFECT = 14
ACTION_CHEST_OPENED = 15
ACTION_USE_WEAPON = 16

# Effect/buff actions (100+)
ACTION_LOST_PT = 100
ACTION_DAMAGE = 101
ACTION_HEAL = 102
# ... more effect types

ACTION_NAMES = {
    0: "START_FIGHT",
    4: "END_FIGHT",
    5: "PLAYER_DEAD",
    6: "NEW_TURN",
    7: "ENTITY_TURN",
    8: "END_TURN",
    9: "SUMMON",
    10: "MOVE_TO",
    11: "KILL",
    12: "USE_CHIP",
    13: "SET_WEAPON",
    14: "STACK_EFFECT",
    15: "CHEST_OPENED",
    16: "USE_WEAPON",
    100: "LOST_PT",
    101: "DAMAGE",
    102: "HEAL",
}


@dataclass
class EntityState:
    """Current state of an entity."""
    id: int
    name: str
    team: int
    life: int
    max_life: int
    tp: int
    mp: int
    cell: int
    alive: bool = True

    def __str__(self):
        status = "ALIVE" if self.alive else "DEAD"
        return f"{self.name}[{self.id}] T{self.team} HP:{self.life}/{self.max_life} TP:{self.tp} MP:{self.mp} @{self.cell} {status}"


@dataclass
class FightState:
    """Complete state of a fight at a point in time."""
    entities: dict[int, EntityState] = field(default_factory=dict)
    turn: int = 0
    current_entity: int = -1

    def get_entity(self, entity_id: int) -> EntityState | None:
        return self.entities.get(entity_id)


class FightReplayer:
    """Replays and visualizes fight data."""

    def __init__(self, fight_data: dict[str, Any]):
        """
        Initialize with fight data.

        Args:
            fight_data: Either the full API response or just the data/fight portion
        """
        # Handle different data formats
        if "fight" in fight_data:
            # Local generator format
            self.data = fight_data["fight"]
            self.winner = fight_data.get("winner", -1)
        elif "data" in fight_data:
            # API response format
            self.data = fight_data["data"]
            self.winner = fight_data.get("winner", -1)
        else:
            # Direct data format
            self.data = fight_data
            self.winner = -1

        self.actions = self.data.get("actions", [])
        self.leeks = self.data.get("leeks", [])
        self.map_data = self.data.get("map", {})

        # Initialize entity states
        self.initial_states: dict[int, EntityState] = {}
        for leek in self.leeks:
            entity = EntityState(
                id=leek["id"],
                name=leek["name"],
                team=leek["team"],
                life=leek["life"],
                max_life=leek["life"],
                tp=leek["tp"],
                mp=leek["mp"],
                cell=leek["cellPos"],
            )
            self.initial_states[leek["id"]] = entity

    def replay_text(self, verbose: bool = True) -> list[str]:
        """
        Generate text-based replay of the fight.

        Returns:
            List of log lines describing the fight
        """
        lines = []
        state = FightState()

        # Initialize entities
        for eid, entity in self.initial_states.items():
            state.entities[eid] = EntityState(**vars(entity))

        lines.append("=" * 60)
        lines.append("FIGHT START")
        lines.append("=" * 60)

        for entity in state.entities.values():
            lines.append(f"  {entity}")

        lines.append("")

        # Process actions
        for action in self.actions:
            if not isinstance(action, list) or len(action) == 0:
                continue

            action_type = action[0]
            line = self._format_action(action, state)

            # Update state based on action
            self._apply_action(action, state)

            if line and (verbose or action_type in [ACTION_USE_WEAPON, ACTION_DAMAGE, ACTION_PLAYER_DEAD, ACTION_NEW_TURN]):
                lines.append(line)

        # Final summary
        lines.append("")
        lines.append("=" * 60)
        lines.append(f"FIGHT END - Winner: Team {self.winner}")
        lines.append("=" * 60)

        for entity in state.entities.values():
            lines.append(f"  {entity}")

        return lines

    def _format_action(self, action: list, state: FightState) -> str | None:
        """Format an action as human-readable text."""
        if len(action) == 0:
            return None

        action_type = action[0]

        if action_type == ACTION_START_FIGHT:
            return None

        elif action_type == ACTION_NEW_TURN:
            turn = action[1] if len(action) > 1 else state.turn + 1
            return f"\n--- Turn {turn} ---"

        elif action_type == ACTION_ENTITY_TURN:
            entity_id = action[1] if len(action) > 1 else -1
            entity = state.get_entity(entity_id)
            name = entity.name if entity else f"Entity{entity_id}"
            return f"  [{name}'s turn]"

        elif action_type == ACTION_END_TURN:
            return None

        elif action_type == ACTION_MOVE_TO:
            # [10, entity_id, dest_cell, path]
            entity_id = action[1] if len(action) > 1 else -1
            dest = action[2] if len(action) > 2 else -1
            path = action[3] if len(action) > 3 else []
            entity = state.get_entity(entity_id)
            name = entity.name if entity else f"Entity{entity_id}"
            return f"    {name} moves to cell {dest} (path: {len(path)} steps)"

        elif action_type == ACTION_SET_WEAPON:
            weapon_id = action[1] if len(action) > 1 else -1
            return f"    Set weapon #{weapon_id}"

        elif action_type == ACTION_USE_WEAPON:
            # [16, target_cell, success]
            target_cell = action[1] if len(action) > 1 else -1
            success = action[2] if len(action) > 2 else 0
            result = "HIT" if success else "MISS"
            return f"    -> Attack cell {target_cell}: {result}"

        elif action_type == ACTION_USE_CHIP:
            # [12, chip_id, target_cell, success]
            chip_id = action[1] if len(action) > 1 else -1
            target_cell = action[2] if len(action) > 2 else -1
            success = action[3] if len(action) > 3 else 0
            result = "SUCCESS" if success else "FAIL"
            return f"    -> Use chip #{chip_id} on cell {target_cell}: {result}"

        elif action_type == ACTION_DAMAGE:
            # [101, target_id, damage, damage_type]
            target_id = action[1] if len(action) > 1 else -1
            damage = action[2] if len(action) > 2 else 0
            entity = state.get_entity(target_id)
            name = entity.name if entity else f"Entity{target_id}"
            return f"       {name} takes {damage} damage"

        elif action_type == ACTION_HEAL:
            # [102, target_id, heal_amount]
            target_id = action[1] if len(action) > 1 else -1
            heal = action[2] if len(action) > 2 else 0
            entity = state.get_entity(target_id)
            name = entity.name if entity else f"Entity{target_id}"
            return f"       {name} heals for {heal}"

        elif action_type == ACTION_PLAYER_DEAD:
            # [5, entity_id, killer_id]
            entity_id = action[1] if len(action) > 1 else -1
            killer_id = action[2] if len(action) > 2 else -1
            entity = state.get_entity(entity_id)
            killer = state.get_entity(killer_id)
            name = entity.name if entity else f"Entity{entity_id}"
            killer_name = killer.name if killer else f"Entity{killer_id}"
            return f"    *** {name} KILLED by {killer_name} ***"

        else:
            name = ACTION_NAMES.get(action_type, f"ACTION_{action_type}")
            return f"    [{name}] {action[1:]}"

    def _apply_action(self, action: list, state: FightState) -> None:
        """Apply action to update state."""
        if len(action) == 0:
            return

        action_type = action[0]

        if action_type == ACTION_NEW_TURN:
            state.turn = action[1] if len(action) > 1 else state.turn + 1

        elif action_type == ACTION_ENTITY_TURN:
            state.current_entity = action[1] if len(action) > 1 else -1

        elif action_type == ACTION_MOVE_TO:
            entity_id = action[1] if len(action) > 1 else -1
            dest = action[2] if len(action) > 2 else -1
            entity = state.get_entity(entity_id)
            if entity:
                entity.cell = dest

        elif action_type == ACTION_DAMAGE:
            target_id = action[1] if len(action) > 1 else -1
            damage = action[2] if len(action) > 2 else 0
            entity = state.get_entity(target_id)
            if entity:
                entity.life = max(0, entity.life - damage)

        elif action_type == ACTION_HEAL:
            target_id = action[1] if len(action) > 1 else -1
            heal = action[2] if len(action) > 2 else 0
            entity = state.get_entity(target_id)
            if entity:
                entity.life = min(entity.max_life, entity.life + heal)

        elif action_type == ACTION_PLAYER_DEAD:
            entity_id = action[1] if len(action) > 1 else -1
            entity = state.get_entity(entity_id)
            if entity:
                entity.alive = False

        elif action_type == ACTION_END_TURN:
            # [8, entity_id, tp_left, mp_left]
            entity_id = action[1] if len(action) > 1 else -1
            tp = action[2] if len(action) > 2 else 10
            mp = action[3] if len(action) > 3 else 3
            entity = state.get_entity(entity_id)
            if entity:
                entity.tp = tp
                entity.mp = mp


def replay_fight(fight_data: dict[str, Any], verbose: bool = False) -> None:
    """Print a text replay of a fight."""
    replayer = FightReplayer(fight_data)
    lines = replayer.replay_text(verbose=verbose)
    for line in lines:
        print(line)


@dataclass
class EntityStats:
    """Detailed statistics for one entity."""
    name: str
    team: int
    level: int = 1
    damage_inflicted: int = 0
    damage_received: int = 0
    heal_casted: int = 0
    heal_received: int = 0
    kills: int = 0
    tp_used: int = 0
    mp_used: int = 0
    turns_played: int = 0
    shoots: int = 0
    chips_used: int = 0
    criticals: int = 0
    alive: bool = True
    life_history: list[int] = field(default_factory=list)


@dataclass
class FightReport:
    """Complete fight report matching site format."""
    turns: int = 0
    winner_team: int = -1
    seed: int = 0
    entity_stats: dict[str, EntityStats] = field(default_factory=dict)
    action_log: list[str] = field(default_factory=list)

    def print_report(self):
        """Print formatted fight report."""
        print("=" * 70)
        print("FIGHT REPORT")
        print("=" * 70)

        # Winners and Losers - based on who's alive
        winners = [e for e in self.entity_stats.values() if e.alive]
        losers = [e for e in self.entity_stats.values() if not e.alive]

        # If no one died, use winner_team
        if not losers and self.winner_team > 0:
            winners = [e for e in self.entity_stats.values() if e.team == self.winner_team]
            losers = [e for e in self.entity_stats.values() if e.team != self.winner_team]

        print("\nWinners:")
        print(f"{'Leek':<15} {'Level':<6} {'Damage':<10} {'Kills':<6}")
        for e in winners:
            print(f"{e.name:<15} {e.level:<6} {e.damage_inflicted:<10} {e.kills:<6}")

        print("\nLosers:")
        print(f"{'Leek':<15} {'Level':<6} {'Damage':<10} {'Kills':<6}")
        for e in losers:
            print(f"{e.name:<15} {e.level:<6} {e.damage_inflicted:<10} {e.kills:<6}")

        print(f"\nSeed: {self.seed}")
        print(f"Turns: {self.turns}")

        # Statistics table
        print("\n" + "=" * 70)
        print("STATISTICS")
        print("=" * 70)
        print(f"{'Leek':<12} {'Dmg In':<8} {'Dmg Rec':<8} {'Heal':<6} {'Kills':<6} {'TP':<5} {'MP':<5} {'Turns':<6} {'Shoots':<7} {'Chips':<6}")
        print("-" * 70)

        for team_num in sorted(set(e.team for e in self.entity_stats.values())):
            print(f"Team {team_num}:")
            for e in self.entity_stats.values():
                if e.team == team_num:
                    print(f"  {e.name:<10} {e.damage_inflicted:<8} {e.damage_received:<8} {e.heal_casted:<6} {e.kills:<6} {e.tp_used:<5} {e.mp_used:<5} {e.turns_played:<6} {e.shoots:<7} {e.chips_used:<6}")

        # Life evolution
        print("\n" + "=" * 70)
        print("LIFE EVOLUTION")
        print("=" * 70)
        max_turns = max(len(e.life_history) for e in self.entity_stats.values()) if self.entity_stats else 0
        if max_turns > 0:
            for e in self.entity_stats.values():
                history = e.life_history + [e.life_history[-1]] * (max_turns - len(e.life_history)) if e.life_history else []
                print(f"{e.name}: {' -> '.join(map(str, history[:10]))}" + ("..." if len(history) > 10 else ""))

        # Action log
        print("\n" + "=" * 70)
        print("ACTION LOG")
        print("=" * 70)
        for line in self.action_log:
            print(line)


def analyze_fight(fight_data: dict[str, Any]) -> dict[str, Any]:
    """Analyze a fight and return statistics."""
    replayer = FightReplayer(fight_data)

    stats = {
        "turns": 0,
        "total_damage": {},
        "total_attacks": {},
        "total_moves": {},
        "winner": replayer.winner,
    }

    for entity in replayer.initial_states.values():
        stats["total_damage"][entity.name] = 0
        stats["total_attacks"][entity.name] = 0
        stats["total_moves"][entity.name] = 0

    current_entity_id = -1

    for action in replayer.actions:
        if not isinstance(action, list) or len(action) == 0:
            continue

        action_type = action[0]

        if action_type == ACTION_NEW_TURN:
            stats["turns"] = action[1] if len(action) > 1 else stats["turns"] + 1

        elif action_type == ACTION_ENTITY_TURN:
            current_entity_id = action[1] if len(action) > 1 else -1

        elif action_type == ACTION_MOVE_TO:
            entity = replayer.initial_states.get(current_entity_id)
            if entity:
                stats["total_moves"][entity.name] += 1

        elif action_type == ACTION_USE_WEAPON:
            entity = replayer.initial_states.get(current_entity_id)
            if entity:
                stats["total_attacks"][entity.name] += 1

        elif action_type == ACTION_DAMAGE:
            # Damage is done by current entity
            entity = replayer.initial_states.get(current_entity_id)
            damage = action[2] if len(action) > 2 else 0
            if entity:
                stats["total_damage"][entity.name] += damage

    return stats


def generate_fight_report(fight_data: dict[str, Any]) -> FightReport:
    """Generate a detailed fight report matching site format."""
    replayer = FightReplayer(fight_data)
    report = FightReport()

    # Get seed from raw data
    if "fight" in fight_data:
        report.seed = fight_data.get("seed", 0)
    elif "seed" in fight_data:
        report.seed = fight_data["seed"]

    report.winner_team = replayer.winner

    # Initialize entity stats
    for entity in replayer.initial_states.values():
        stats = EntityStats(
            name=entity.name,
            team=entity.team,
            level=1,  # Could get from fight data
        )
        stats.life_history.append(entity.life)
        report.entity_stats[entity.name] = stats

    # Entity ID to name mapping
    id_to_name = {e.id: e.name for e in replayer.initial_states.values()}

    # Current state for tracking
    current_entity_id = -1
    current_turn = 0
    entity_lives = {e.id: e.life for e in replayer.initial_states.values()}

    for action in replayer.actions:
        if not isinstance(action, list) or len(action) == 0:
            continue

        action_type = action[0]
        name = id_to_name.get(current_entity_id, "Unknown")

        if action_type == ACTION_NEW_TURN:
            current_turn = action[1] if len(action) > 1 else current_turn + 1
            report.turns = current_turn
            report.action_log.append(f"\nTurn {current_turn}")

            # Record life at turn start
            for eid, life in entity_lives.items():
                ename = id_to_name.get(eid)
                if ename and ename in report.entity_stats:
                    report.entity_stats[ename].life_history.append(life)

        elif action_type == ACTION_ENTITY_TURN:
            current_entity_id = action[1] if len(action) > 1 else -1
            name = id_to_name.get(current_entity_id, f"Entity{current_entity_id}")
            if name in report.entity_stats:
                report.entity_stats[name].turns_played += 1
            report.action_log.append(f"  {name}'s turn")

        elif action_type == ACTION_SET_WEAPON:
            weapon_id = action[1] if len(action) > 1 else -1
            # Weapon names from FightConstants.java (item IDs, not template IDs!)
            weapon_names = {
                37: "Pistol", 38: "Machine Gun", 39: "Double Gun",
                40: "Destroyer", 41: "Shotgun", 42: "Laser",
                43: "Grenade Launcher", 44: "Electrisor", 45: "Magnum",
                46: "Flame Thrower", 47: "M-Laser", 48: "Gazor",
            }
            weapon_name = weapon_names.get(weapon_id, f"Weapon#{weapon_id}")
            report.action_log.append(f"    {name} takes weapon {weapon_name} (1 TP)")
            if name in report.entity_stats:
                report.entity_stats[name].tp_used += 1

        elif action_type == ACTION_MOVE_TO:
            entity_id = action[1] if len(action) > 1 else current_entity_id
            path = action[3] if len(action) > 3 else []
            mp_cost = len(path)
            ename = id_to_name.get(entity_id, name)
            report.action_log.append(f"    {ename} moves ({mp_cost} MP)")
            if ename in report.entity_stats:
                report.entity_stats[ename].mp_used += mp_cost

        elif action_type == ACTION_USE_WEAPON:
            success = action[2] if len(action) > 2 else 0
            if success:
                report.action_log.append(f"    {name} attacks with Pistol (3 TP)")
            else:
                report.action_log.append(f"    {name} attacks with Pistol (3 TP) - MISS")
            if name in report.entity_stats:
                report.entity_stats[name].shoots += 1
                report.entity_stats[name].tp_used += 3

        elif action_type == ACTION_USE_CHIP:
            chip_id = action[1] if len(action) > 1 else -1
            report.action_log.append(f"    {name} uses chip #{chip_id}")
            if name in report.entity_stats:
                report.entity_stats[name].chips_used += 1

        elif action_type == ACTION_DAMAGE:
            target_id = action[1] if len(action) > 1 else -1
            damage = action[2] if len(action) > 2 else 0
            target_name = id_to_name.get(target_id, f"Entity{target_id}")
            report.action_log.append(f"      {target_name} loses {damage} HP")

            # Update stats
            if name in report.entity_stats:
                report.entity_stats[name].damage_inflicted += damage
            if target_name in report.entity_stats:
                report.entity_stats[target_name].damage_received += damage
                entity_lives[target_id] = max(0, entity_lives.get(target_id, 0) - damage)

        elif action_type == ACTION_HEAL:
            target_id = action[1] if len(action) > 1 else -1
            heal = action[2] if len(action) > 2 else 0
            target_name = id_to_name.get(target_id, f"Entity{target_id}")
            report.action_log.append(f"      {target_name} gains {heal} HP")

            if name in report.entity_stats:
                report.entity_stats[name].heal_casted += heal
            if target_name in report.entity_stats:
                report.entity_stats[target_name].heal_received += heal
                # Update life tracking
                initial_life = replayer.initial_states.get(target_id)
                if initial_life:
                    entity_lives[target_id] = min(initial_life.life, entity_lives.get(target_id, 0) + heal)

        elif action_type == ACTION_PLAYER_DEAD:
            entity_id = action[1] if len(action) > 1 else -1
            killer_id = action[2] if len(action) > 2 else -1
            dead_name = id_to_name.get(entity_id, f"Entity{entity_id}")
            killer_name = id_to_name.get(killer_id, f"Entity{killer_id}")
            report.action_log.append(f"    {dead_name} is dead!")

            if dead_name in report.entity_stats:
                report.entity_stats[dead_name].alive = False
            if killer_name in report.entity_stats:
                report.entity_stats[killer_name].kills += 1

    report.action_log.append("\nEnd of fight!")
    return report


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(__file__).rsplit("/", 2)[0])

    from leekwars_agent.simulator import Simulator

    print("Running local fight...")
    sim = Simulator()
    outcome = sim.run_1v1("fighter_v1.leek", "fighter_v1.leek", level=1, seed=42)

    # Generate detailed report
    report = generate_fight_report(outcome.raw_output)
    report.print_report()
