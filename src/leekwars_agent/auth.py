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
from pathlib import Path

from dotenv import load_dotenv

# Auto-load .env from project root
_project_root = Path(__file__).parent.parent.parent
_env_file = _project_root / ".env"
if _env_file.exists():
    load_dotenv(_env_file)


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


def login_api(max_retries: int = 3):
    """Create and login to LeekWars API with retry on rate limit.

    Args:
        max_retries: Max login attempts on 429 rate limit

    Returns:
        Authenticated LeekWarsAPI instance
    """
    import time
    import httpx
    from leekwars_agent.api import LeekWarsAPI

    username, password = get_credentials()
    api = LeekWarsAPI()

    for attempt in range(max_retries):
        try:
            api.login(username, password)
            return api
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                wait_time = 10 * (2 ** attempt)  # 10s, 20s, 40s
                print(f"Rate limited on login, waiting {wait_time}s (attempt {attempt+1}/{max_retries})...")
                time.sleep(wait_time)
                continue
            raise

    # Final attempt without catching
    api.login(username, password)
    return api
