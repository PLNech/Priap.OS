"""Battle Royale automation - free fights via WebSocket."""

import json
import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Optional
from urllib.parse import urlparse

import websocket

from leekwars_agent.api import LeekWarsAPI
from leekwars_agent.cli.constants import FARMER_ID

logger = logging.getLogger(__name__)

# WebSocket message IDs
MSG_BR_REGISTER = 28
MSG_BR_UPDATE = 29
MSG_BR_START = 30
MSG_BR_LEAVE = 31
MSG_BR_CHAT = 32


@dataclass
class BattleRoyaleConfig:
    """Configuration for Battle Royale client."""
    host: str = "leekwars.com"
    secure: bool = True
    timeout: float = 30.0  # seconds to wait for BR to start


@dataclass
class BattleRoyaleResult:
    """Result of a Battle Royale session."""
    success: bool
    fight_id: Optional[int] = None
    xp_gained: int = 0
    error: Optional[str] = None
    player_count: int = 0


class BattleRoyaleClient:
    """WebSocket client for Battle Royale automation.

    Usage:
        client = BattleRoyaleClient(api)
        result = client.join(leek_id=131321)
        print(f"Fight: {result.fight_id}, XP: {result.xp_gained}")
    """

    def __init__(self, api: LeekWarsAPI, config: Optional[BattleRoyaleConfig] = None):
        """
        Initialize BR client.

        Args:
            api: Authenticated LeekWarsAPI for token and garden state
            config: Optional configuration overrides
        """
        self.api = api
        self.config = config or BattleRoyaleConfig()

        self._ws: Optional[websocket.WebSocket] = None
        self._result: Optional[BattleRoyaleResult] = None
        self._lock = threading.Lock()
        self._connected = threading.Event()
        self._started = threading.Event()

    def get_ws_url(self) -> str:
        """Get WebSocket URL based on environment."""
        scheme = "wss" if self.config.secure else "ws"
        return f"{scheme}://{self.config.host}/ws"

    def status(self, leek_id: Optional[int] = None) -> dict:
        """
        Check if Battle Royale is available.

        Args:
            leek_id: Leek ID to check (uses default if None)

        Returns:
            dict with keys:
                - enabled: bool (server-side BR flag)
                - leek_level_ok: bool (leek >= 20)
                - farmer_verified: bool
                - farmer_br_enabled: bool
                - ready: bool (all conditions met)
        """
        from leekwars_agent.cli.constants import LEEK_ID
        leek_id = leek_id or LEEK_ID

        garden = self.api.get_garden()
        garden_data = garden.get("garden", garden)

        leek = self.api.get_leek(leek_id)
        leek_data = leek.get("leek", leek)

        farmer = self.api.get_farmer(FARMER_ID)
        farmer_data = farmer.get("farmer", farmer)

        return {
            "enabled": garden_data.get("battle_royale_enabled", False),
            "leek_level": leek_data.get("level", 0),
            "leek_level_ok": leek_data.get("level", 0) >= 20,
            "farmer_verified": farmer_data.get("verified", False),
            "farmer_br_enabled": farmer_data.get("br_enabled", False),
            "ready": (
                garden_data.get("battle_royale_enabled", False) and
                leek_data.get("level", 0) >= 20 and
                farmer_data.get("verified", False) and
                farmer_data.get("br_enabled", False)
            ),
        }

    def join(self, leek_id: int, timeout: float = 60.0) -> BattleRoyaleResult:
        """
        Join a Battle Royale and wait for it to start.

        Blocks until:
        - Battle Royale starts (returns fight_id)
        - Connection fails
        - Timeout reached

        Args:
            leek_id: Leek ID to register for BR
            timeout: Max seconds to wait for BR to start

        Returns:
            BattleRoyaleResult with fight_id or error
        """
        self._result = None
        self._connected.clear()
        self._started.clear()

        # Get auth token
        token = self.api.token
        if not token:
            return BattleRoyaleResult(success=False, error="Not authenticated")

        # Connect WebSocket
        ws_url = self.get_ws_url()
        logger.info(f"Connecting to {ws_url}...")

        try:
            self._ws = websocket.create_connection(
                ws_url,
                timeout=10.0,
                subprotocols=["leek-wars", token],
            )
        except Exception as e:
            return BattleRoyaleResult(success=False, error=f"WS connect failed: {e}")

        # Start listener thread
        listener = threading.Thread(target=self._listen, args=(timeout,), daemon=True)
        listener.start()

        # Wait for connection
        if not self._connected.wait(timeout=10.0):
            self._cleanup()
            return BattleRoyaleResult(success=False, error="Connection timeout")

        # Register for BR
        logger.info(f"Registering leek {leek_id} for Battle Royale...")
        try:
            self._ws.send(json.dumps([MSG_BR_REGISTER, leek_id]))
        except Exception as e:
            self._cleanup()
            return BattleRoyaleResult(success=False, error=f"Failed to register: {e}")

        # Wait for BR to start
        logger.info("Waiting for Battle Royale to start...")
        if not self._started.wait(timeout):
            self._cleanup()
            return BattleRoyaleResult(
                success=False,
                error=f"Timeout waiting for BR to start ({timeout}s)"
            )

        result = self._result
        self._cleanup()

        return result or BattleRoyaleResult(success=False, error="No result received")

    def _listen(self, timeout: float):
        """WebSocket listener thread."""
        try:
            while self._ws and self._ws.connected:
                msg = self._ws.recv()
                if not msg:
                    continue

                data = json.loads(msg)
                msg_id = data[0] if isinstance(data, list) else None

                if msg_id == MSG_BR_UPDATE:
                    # Update with player count
                    players = data[1] if len(data) > 1 else []
                    logger.debug(f"BR update: {len(players)} players in queue")

                elif msg_id == MSG_BR_START:
                    # Battle starting!
                    fight_id = data[1] if len(data) > 1 else None
                    logger.info(f"Battle Royale starting! Fight ID: {fight_id}")
                    self._result = BattleRoyaleResult(
                        success=True,
                        fight_id=fight_id,
                        player_count=data[2] if len(data) > 2 else 0,
                    )
                    self._started.set()
                    break

                elif msg_id == MSG_BR_CHAT:
                    # Chat message, ignore
                    pass

        except Exception as e:
            logger.error(f"WS listener error: {e}")
            if not self._started.is_set():
                self._result = BattleRoyaleResult(success=False, error=str(e))
                self._started.set()  # Unblock join()

    def _cleanup(self):
        """Clean up WebSocket connection."""
        if self._ws:
            try:
                self._ws.close()
            except Exception:
                pass
            self._ws = None
        self._connected.clear()
        self._started.clear()


def run_br_session(
    api: LeekWarsAPI,
    leek_id: int,
    timeout: float = 60.0,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> BattleRoyaleResult:
    """
    Convenience function to run a single BR session.

    Args:
        api: Authenticated API client
        leek_id: Leek ID to use
        timeout: Max seconds to wait
        progress_callback: Optional callback for status updates

    Returns:
        BattleRoyaleResult
    """
    client = BattleRoyaleClient(api)

    # Check status first
    status = client.status()
    if progress_callback:
        progress_callback(f"BR enabled: {status['enabled']}")

    if not status["ready"]:
        reasons = []
        if not status["enabled"]:
            reasons.append("BR disabled on server")
        if not status["leek_level_ok"]:
            reasons.append(f"Leek L{status['leek_level']} < 20")
        if not status["farmer_verified"]:
            reasons.append("Farmer not verified")
        if not status["farmer_br_enabled"]:
            reasons.append("BR disabled for farmer")
        return BattleRoyaleResult(success=False, error=f"Not ready: {'; '.join(reasons)}")

    if progress_callback:
        progress_callback("Joining Battle Royale...")

    return client.join(leek_id, timeout=timeout)


def get_fight_result(api: LeekWarsAPI, fight_id: int) -> dict:
    """
    Get fight result and XP gained.

    Args:
        api: Authenticated API client
        fight_id: Fight ID to query

    Returns:
        dict with fight result, XP, etc.
    """
    fight = api.get_fight(fight_id)
    fight_data = fight.get("fight", fight)

    # Extract relevant info
    return {
        "fight_id": fight_id,
        "winner": fight_data.get("winner"),
        "duration": fight_data.get("report", {}).get("duration"),
        "our_team": 1 if fight_data.get("leeks1") else 2,
    }


def run_full_br_session(
    api: LeekWarsAPI,
    leek_id: int,
    timeout: float = 60.0,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> dict:
    """
    Run a complete BR session: join, wait, get results.

    Args:
        api: Authenticated API client
        leek_id: Leek ID to use
        timeout: Max seconds to wait for BR to start
        progress_callback: Optional callback for status updates

    Returns:
        dict with:
            - success: bool
            - fight_id: int or None
            - error: str or None
            - fight_result: dict or None
    """
    client = BattleRoyaleClient(api)

    # Check readiness
    status = client.status()
    if progress_callback:
        progress_callback(f"Status: enabled={status['enabled']}, ready={status['ready']}")

    if not status["ready"]:
        return {
            "success": False,
            "error": f"Not ready: enabled={status['enabled']}, level_ok={status['leek_level_ok']}",
            "fight_id": None,
            "fight_result": None,
        }

    # Join and wait
    result = client.join(leek_id, timeout=timeout)
    if progress_callback:
        if result.success:
            progress_callback(f"Fight started! ID: {result.fight_id}")
        else:
            progress_callback(f"Failed: {result.error}")

    if not result.success:
        return {
            "success": False,
            "error": result.error,
            "fight_id": None,
            "fight_result": None,
        }

    # Get fight result (XP not directly available, but we can track it)
    fight_result = get_fight_result(api, result.fight_id)

    return {
        "success": True,
        "fight_id": result.fight_id,
        "fight_result": fight_result,
        "error": None,
    }