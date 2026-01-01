#!/usr/bin/env python3
"""Validate LeekScript code without running fights."""

import sys
import os
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from leekwars_agent import LeekWarsAPI
from leekwars_agent.validator import validate_code, format_validation_report

USERNAME = "leek@nech.pl"
PASSWORD = "REDACTED_PASSWORD"
AI_ID = 453627


def main():
    parser = argparse.ArgumentParser(description="Validate LeekScript code")
    parser.add_argument("ai_file", help="Path to AI file")
    parser.add_argument("-v", "--verbose", action="store_true",
                       help="Show full code on success")
    args = parser.parse_args()

    # Load code
    if not os.path.exists(args.ai_file):
        print(f"File not found: {args.ai_file}")
        sys.exit(1)

    with open(args.ai_file) as f:
        code = f.read()

    print(f"Validating {args.ai_file} ({len(code)} chars)...")

    # Connect and validate
    api = LeekWarsAPI()
    try:
        api.login(USERNAME, PASSWORD)

        is_valid, errors = validate_code(api, AI_ID, code)

        print()
        print(format_validation_report(code, errors))

        if is_valid:
            print("\nAI is VALID and ready to deploy!")
            if args.verbose:
                print("\n=== CODE ===")
                print(code)
            sys.exit(0)
        else:
            print("\nAI has ERRORS - fix before deploying")
            sys.exit(1)

    finally:
        api.close()


if __name__ == "__main__":
    main()
