#!/usr/bin/env python3
"""Fetch game constants from LeekWars API.

Saves weapons, chips, constants to data/ directory.
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from leekwars_agent.api import LeekWarsAPI

DATA_DIR = Path(__file__).parent.parent / "data"


def main():
    DATA_DIR.mkdir(exist_ok=True)

    api = LeekWarsAPI()

    print("Fetching game constants...")

    # Weapons
    print("  - Weapons...")
    weapons = api.get_weapons()
    (DATA_DIR / "weapons.json").write_text(json.dumps(weapons, indent=2))
    print(f"    Saved {len(weapons.get('weapons', weapons))} weapons")

    # Chips
    print("  - Chips...")
    chips = api.get_chips()
    (DATA_DIR / "chips.json").write_text(json.dumps(chips, indent=2))
    print(f"    Saved {len(chips.get('chips', chips))} chips")

    # Constants
    print("  - Constants...")
    constants = api.get_constants()
    (DATA_DIR / "constants.json").write_text(json.dumps(constants, indent=2))
    print(f"    Saved constants")

    # Functions (LeekScript API)
    print("  - Functions...")
    functions = api.get_functions()
    (DATA_DIR / "functions.json").write_text(json.dumps(functions, indent=2))
    print(f"    Saved {len(functions.get('functions', functions))} functions")

    api.close()
    print("\nDone! Data saved to data/")


if __name__ == "__main__":
    main()
