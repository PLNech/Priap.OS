import sys
import os
import random
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from leekwars_agent.simulator import Simulator

def run_random_fights(n=10):
    sim = Simulator()
    
    # Get available AIs from ais/ directory
    ais_dir = Path(__file__).parent.parent / "ais"
    leek_files = list(ais_dir.glob("*.leek"))
    
    if len(leek_files) < 2:
        print("Not enough AI files in ais/ directory")
        return

    print(f"Found {len(leek_files)} AI files.")
    
    # We need to copy them to tools/leek-wars-generator/ if they aren't there
    # or use relative paths from generator dir.
    # The Simulator class expects AI paths relative to generator_path.
    
    gen_path = Path(__file__).parent.parent / "tools" / "leek-wars-generator"
    
    results = []
    for i in range(n):
        ai1_path = random.choice(leek_files)
        ai2_path = random.choice(leek_files)
        
        # Copy to generator dir for simplicity (as Simulator seems to expect them there)
        target1 = gen_path / ai1_path.name
        target2 = gen_path / ai2_path.name
        
        if not target1.exists():
            target1.write_text(ai1_path.read_text())
        if not target2.exists():
            target2.write_text(ai2_path.read_text())
            
        print(f"Fight {i+1}/{n}: {ai1_path.name} vs {ai2_path.name}")
        
        outcome = sim.run_1v1(ai1_path.name, ai2_path.name, level=100)
        
        winner_name = "Draw"
        if outcome.winner == 1: winner_name = ai1_path.name
        elif outcome.winner == 2: winner_name = ai2_path.name
        
        print(f"  Winner: {winner_name} ({outcome.turns} turns, {outcome.duration_ms:.1f}ms)")
        results.append(outcome)

    total_time = sum(r.duration_ms for r in results)
    print(f"\nTotal simulation time: {total_time:.1f}ms")
    print(f"Average time per fight: {total_time/n:.1f}ms")

if __name__ == "__main__":
    run_random_fights(10)
