#!/usr/bin/env python3
"""Battle Royale daemon - persistent service that queues for BR every cycle.

Designed for systemctl: wakes every CYCLE_MINUTES, joins BR queue,
waits QUEUE_TIMEOUT for enough players, then sleeps again.

Usage:
    # Run directly
    poetry run python scripts/br_daemon.py

    # As systemd service (see systemd/priap-br.service)
    systemctl --user start priap-br

    # Override cycle/timeout
    BR_CYCLE_MINUTES=10 BR_QUEUE_TIMEOUT=600 poetry run python scripts/br_daemon.py
"""

import os
import sys
import signal
import json
import time
from datetime import datetime, date
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from leekwars_agent.auth import login_api
from leekwars_agent.battle_royale import BattleRoyaleClient, BattleRoyaleConfig

# Config (overridable via env)
LEEK_ID = 131321
CYCLE_MINUTES = int(os.environ.get("BR_CYCLE_MINUTES", "15"))
QUEUE_TIMEOUT = int(os.environ.get("BR_QUEUE_TIMEOUT", "600"))  # 10 min in queue
MAX_BR_PER_DAY = 10
LOG_FILE = Path(__file__).parent.parent / "logs" / "br_daemon.log"
STATE_FILE = Path(__file__).parent.parent / "data" / "br_state.json"

# Graceful shutdown
_shutdown = False


def handle_signal(signum, frame):
    global _shutdown
    _shutdown = True
    log(f"Received signal {signum}, shutting down gracefully...")


signal.signal(signal.SIGTERM, handle_signal)
signal.signal(signal.SIGINT, handle_signal)


def log(msg: str):
    """Log with timestamp to file and stdout."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line, flush=True)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}


def save_state(state: dict):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def get_today_count(state: dict) -> int:
    """How many BR fights we've done today."""
    today = date.today().isoformat()
    return state.get("daily", {}).get(today, 0)


def increment_today(state: dict) -> dict:
    today = date.today().isoformat()
    daily = state.get("daily", {})
    daily[today] = daily.get(today, 0) + 1
    state["daily"] = daily
    state["last_br"] = datetime.now().isoformat()
    return state


def get_ai_name(api) -> str:
    """Log which AI is currently deployed."""
    try:
        leek = api.get_leek(LEEK_ID)
        leek_data = leek.get("leek", leek)
        ai = leek_data.get("ai", {})
        if isinstance(ai, dict):
            return ai.get("name", "unknown")
        return f"ai_{ai}"
    except Exception:
        return "unknown"


def scrape_br_fight(api, fight_id: int):
    """Store BR fight in meta DB for analytics."""
    try:
        from leekwars_agent.scraper.scraper import FightScraper
        scraper = FightScraper(api)
        if scraper.process_fight(fight_id):
            log(f"  Scraped fight {fight_id} to meta DB")
        else:
            log(f"  Fight {fight_id} already in DB or failed to scrape")
    except Exception as e:
        log(f"  Scrape failed (non-fatal): {e}")


def attempt_br(api) -> bool:
    """Try to join and complete one BR. Returns True if fight happened."""
    config = BattleRoyaleConfig(timeout=QUEUE_TIMEOUT)
    client = BattleRoyaleClient(api, config)

    # Check readiness
    try:
        status = client.status(LEEK_ID)
    except Exception as e:
        log(f"  Status check failed: {e}")
        return False

    if not status["ready"]:
        log(f"  Not ready: enabled={status.get('enabled')}, "
            f"level_ok={status.get('leek_level_ok')}, "
            f"br_enabled={status.get('farmer_br_enabled')}")
        return False

    log(f"  Queuing for BR (timeout={QUEUE_TIMEOUT}s)...")
    result = client.join(LEEK_ID, timeout=QUEUE_TIMEOUT)

    if not result.success:
        if "Timeout" in (result.error or ""):
            log(f"  No BR started (queue empty or not enough players)")
        else:
            log(f"  BR failed: {result.error}")
        return False

    # BR started!
    log(f"  BR STARTED! Fight ID: {result.fight_id}, Players: {result.player_count}")

    # Wait for fight to complete then scrape
    time.sleep(5)
    scrape_br_fight(api, result.fight_id)

    # Get result
    try:
        fight_data = api.get_fight(result.fight_id)
        fight = fight_data.get("fight", fight_data)
        winner = fight.get("winner", "?")

        # Determine our result
        leeks1 = fight.get("leeks1", [])
        my_team = None
        for leek in leeks1:
            lid = leek.get("id") if isinstance(leek, dict) else leek
            if lid == LEEK_ID:
                my_team = 1
                break
        if my_team is None:
            for leek in fight.get("leeks2", []):
                lid = leek.get("id") if isinstance(leek, dict) else leek
                if lid == LEEK_ID:
                    my_team = 2
                    break

        if winner == my_team:
            log(f"  WIN! (team {my_team})")
        elif winner == 0:
            log(f"  DRAW")
        else:
            log(f"  LOSS (winner={winner}, our team={my_team})")
    except Exception as e:
        log(f"  Couldn't fetch result: {e}")

    return True


def main():
    log("=" * 50)
    log("BR DAEMON - Starting")
    log(f"  Cycle: {CYCLE_MINUTES}min | Queue timeout: {QUEUE_TIMEOUT}s | Max: {MAX_BR_PER_DAY}/day")

    api = None
    try:
        api = login_api()
        ai_name = get_ai_name(api)
        log(f"  Logged in as {api.farmer['name']} | AI: {ai_name}")
    except Exception as e:
        log(f"  LOGIN FAILED: {e}")
        sys.exit(1)

    state = load_state()

    while not _shutdown:
        today_count = get_today_count(state)

        if today_count >= MAX_BR_PER_DAY:
            log(f"Daily limit reached ({today_count}/{MAX_BR_PER_DAY}). Sleeping until midnight...")
            # Sleep until midnight + 1 min
            now = datetime.now()
            midnight = now.replace(hour=0, minute=1, second=0, microsecond=0)
            if midnight <= now:
                from datetime import timedelta
                midnight += timedelta(days=1)
            sleep_secs = (midnight - now).total_seconds()
            log(f"  Sleeping {sleep_secs/3600:.1f}h until {midnight.strftime('%H:%M')}")
            _interruptible_sleep(sleep_secs)
            state = load_state()  # Reload after sleep
            continue

        log(f"Cycle start ({today_count}/{MAX_BR_PER_DAY} BR today)")

        # Re-login if token might be stale (every hour)
        last_login = state.get("last_login", "")
        if not last_login or (datetime.now() - datetime.fromisoformat(last_login)).seconds > 3600:
            try:
                api.close()
                api = login_api()
                state["last_login"] = datetime.now().isoformat()
                save_state(state)
                log("  Re-authenticated")
            except Exception as e:
                log(f"  Re-auth failed: {e}, will retry next cycle")
                _interruptible_sleep(CYCLE_MINUTES * 60)
                continue

        if attempt_br(api):
            state = increment_today(state)
            save_state(state)
            log(f"  BR #{get_today_count(state)} done today")
        else:
            log(f"  No BR this cycle")

        if _shutdown:
            break

        log(f"  Sleeping {CYCLE_MINUTES}min until next attempt...")
        _interruptible_sleep(CYCLE_MINUTES * 60)

    log("BR DAEMON - Stopped")
    log("=" * 50)
    if api:
        api.close()


def _interruptible_sleep(seconds: float):
    """Sleep that responds to shutdown signal."""
    end = time.time() + seconds
    while time.time() < end and not _shutdown:
        time.sleep(min(5.0, end - time.time()))


if __name__ == "__main__":
    main()
