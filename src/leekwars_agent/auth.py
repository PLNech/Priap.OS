"""Centralized authentication for LeekWars API.

NEVER hardcode credentials. Always use environment variables.

Setup:
    export LEEKWARS_USER="your_email"
    export LEEKWARS_PASS="your_password"

Or create a .env file (gitignored):
    LEEKWARS_USER=your_email
    LEEKWARS_PASS=your_password
"""

import os
import sys


def get_credentials() -> tuple[str, str]:
    """Get LeekWars credentials from environment.

    Returns:
        Tuple of (username, password)

    Raises:
        SystemExit if credentials not found
    """
    username = os.environ.get("LEEKWARS_USER")
    password = os.environ.get("LEEKWARS_PASS")

    if not username or not password:
        print("ERROR: LeekWars credentials not found!", file=sys.stderr)
        print("Set environment variables:", file=sys.stderr)
        print("  export LEEKWARS_USER='your_email'", file=sys.stderr)
        print("  export LEEKWARS_PASS='your_password'", file=sys.stderr)
        print("Or create a .env file with these values.", file=sys.stderr)
        sys.exit(1)

    return username, password


def login_api():
    """Create and login to LeekWars API.

    Returns:
        Authenticated LeekWarsAPI instance
    """
    from leekwars_agent.api import LeekWarsAPI

    username, password = get_credentials()
    api = LeekWarsAPI()
    api.login(username, password)
    return api
