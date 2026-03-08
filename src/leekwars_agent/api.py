"""LeekWars API client."""

import json
import logging
import time

import httpx
from typing import Any

logger = logging.getLogger(__name__)

# Business errors that should NOT be retried (LeekWars returns 401 for these)
BUSINESS_ERRORS = frozenset({
    "not_enough_habs", "not_enough_crystals",
    "too_much_chips", "too_much_weapons",
    "already_registered", "not_registered",
    "wrong_method", "not_found",
    "max_chips", "max_weapons",
    "invalid_chip", "invalid_weapon",
    "not_enough_capital",
})


class LeekWarsError(Exception):
    """Business logic error from LeekWars API (not a transport/auth error)."""

    def __init__(self, error: str, status_code: int = 401, path: str = ""):
        self.error = error
        self.status_code = status_code
        self.path = path
        super().__init__(f"{error} (HTTP {status_code} on {path})")


class LeekWarsAPI:
    """HTTP client for LeekWars API."""

    BASE_URL = "https://leekwars.com/api"

    def __init__(self, token: str | None = None):
        self.token = token
        self.farmer: dict[str, Any] | None = None
        self.farmer_id: int | None = None
        # Use a client that persists cookies
        self._client = httpx.Client(
            base_url=self.BASE_URL,
            timeout=30.0,
            follow_redirects=True,
        )

    def _headers(self) -> dict[str, str]:
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _request(self, method: str, path: str, retries: int = 3, **kwargs) -> httpx.Response:
        """Make an HTTP request with smart error handling.

        LeekWars uses HTTP 401 for BOTH auth failures AND business logic errors
        (not_enough_habs, too_much_chips, etc.). This method distinguishes them:
        - Business errors: raise LeekWarsError immediately (no retry)
        - Rate limits (429): retry with backoff
        - Auth failures (401 without JSON body): retry with backoff
        """
        for attempt in range(retries):
            response = self._client.request(method.upper(), path, **kwargs)

            if response.status_code == 401:
                # Parse body to distinguish business vs auth errors
                error_key = self._parse_error(response)
                if error_key and error_key in BUSINESS_ERRORS:
                    raise LeekWarsError(error_key, 401, path)
                if error_key:
                    # Unknown 401 error — might be business, don't retry blindly
                    raise LeekWarsError(error_key, 401, path)
                # No parseable error = likely auth issue, retry
                if attempt < retries - 1:
                    wait = 3 * (2 ** attempt)
                    logger.debug(f"Auth 401 on {path}, retry in {wait}s (attempt {attempt+1})")
                    time.sleep(wait)
                    continue

            if response.status_code == 429:
                if attempt < retries - 1:
                    wait = 3 * (2 ** attempt)
                    logger.debug(f"Rate limited on {path}, retry in {wait}s")
                    time.sleep(wait)
                    continue

            response.raise_for_status()
            return response
        response.raise_for_status()
        return response  # unreachable, but satisfies type checker

    @staticmethod
    def _parse_error(response: httpx.Response) -> str | None:
        """Extract error string from a LeekWars error response."""
        try:
            body = response.json()
            if isinstance(body, dict) and "error" in body:
                return body["error"]
        except (json.JSONDecodeError, ValueError):
            pass
        return None

    def _browser_headers(self, referer: str | None = None) -> dict[str, str]:
        """Return headers that mimic browser XHR requests."""
        headers = self._headers()
        headers["Content-Type"] = "application/json; charset=UTF-8"
        headers["Origin"] = "https://leekwars.com"
        headers["Accept"] = "application/json, text/plain, */*"
        headers["User-Agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        if referer:
            headers["Referer"] = f"https://leekwars.com{referer}"
        headers["X-Requested-With"] = "XMLHttpRequest"
        return headers

    def login(self, username: str, password: str, keep_connected: bool = True) -> dict[str, Any]:
        """Login and store token. Returns farmer data on success."""
        # Login uses raw client — auth errors here ARE real auth errors
        response = self._client.post(
            "/farmer/login",
            data={
                "login": username,
                "password": password,
                "keep_connected": str(keep_connected).lower(),
            },
        )
        response.raise_for_status()
        data = response.json()

        # Extract JWT token from cookies
        for cookie in response.cookies.jar:
            if cookie.name == "token":
                self.token = cookie.value
                break

        # Store farmer data
        if "farmer" in data:
            self.farmer = data["farmer"]
            self.farmer_id = self.farmer.get("id")

        return data

    def logout(self) -> dict[str, Any]:
        """Logout and clear token."""
        response = self._request("post", "/farmer/disconnect", headers=self._headers())
        self.token = None
        return response.json()

    def get_farmer(self, farmer_id: int) -> dict[str, Any]:
        """Get public farmer data."""
        return self._request("get", f"/farmer/get/{farmer_id}").json()

    def get_leek(self, leek_id: int) -> dict[str, Any]:
        """Get public leek data."""
        return self._request("get", f"/leek/get/{leek_id}").json()

    def get_garden(self) -> dict[str, Any]:
        """Get garden state (authenticated)."""
        return self._request("get", "/garden/get", headers=self._headers()).json()

    def get_leek_opponents(self, leek_id: int) -> dict[str, Any]:
        """Get solo fight opponents for a leek."""
        return self._request("get", f"/garden/get-leek-opponents/{leek_id}", headers=self._headers()).json()

    def get_farmer_opponents(self) -> dict[str, Any]:
        """Get farmer fight opponents."""
        return self._request("get", "/garden/get-farmer-opponents", headers=self._headers()).json()

    def start_solo_fight(self, leek_id: int, target_id: int) -> dict[str, Any]:
        """Start a solo fight."""
        return self._request(
            "post", "/garden/start-solo-fight",
            headers=self._headers(), data={"leek_id": leek_id, "target_id": target_id},
        ).json()

    def start_farmer_fight(self, target_id: int) -> dict[str, Any]:
        """Start a farmer fight."""
        return self._request(
            "post", "/garden/start-farmer-fight",
            headers=self._headers(), data={"target_id": target_id},
        ).json()

    def get_fight(self, fight_id: int) -> dict[str, Any]:
        """Get fight data."""
        return self._request("get", f"/fight/get/{fight_id}").json()

    def get_leek_history(self, leek_id: int) -> dict[str, Any]:
        """Get leek fight history.

        Source: tools/leek-wars/src/component/history/history.vue:163
        Returns all fights (no pagination), plus entity info.
        """
        return self._request("get", f"/history/get-leek-history/{leek_id}", headers=self._headers()).json()

    def get_constants(self) -> dict[str, Any]:
        """Get game constants."""
        return self._request("get", "/constant/get-all").json()

    def get_chips(self) -> dict[str, Any]:
        """Get all chips data."""
        return self._request("get", "/chip/get-all").json()

    def get_weapons(self) -> dict[str, Any]:
        """Get all weapons data."""
        return self._request("get", "/weapon/get-all").json()

    def get_functions(self) -> dict[str, Any]:
        """Get all LeekScript functions."""
        return self._request("get", "/function/get-all").json()

    # AI Management
    def get_ai(self, ai_id: int) -> dict[str, Any]:
        """Get AI code and metadata."""
        return self._request("get", f"/ai/get/{ai_id}", headers=self._headers()).json()

    def get_farmer_ais(self) -> dict[str, Any]:
        """Get all farmer's AIs."""
        return self._request("get", "/ai/get-farmer-ais", headers=self._headers()).json()

    def save_ai(self, ai_id: int, code: str) -> dict[str, Any]:
        """Save AI code."""
        return self._request(
            "post", "/ai/save", headers=self._headers(), data={"ai_id": ai_id, "code": code},
        ).json()

    def rename_ai(self, ai_id: int, name: str) -> dict[str, Any]:
        """Rename an AI."""
        return self._request(
            "post", "/ai/rename", headers=self._headers(), data={"ai_id": ai_id, "name": name},
        ).json()

    def create_ai(self, name: str = "NewAI", folder_id: int = 0, version: int = 4) -> dict[str, Any]:
        """Create a new AI.

        Source: tools/leek-wars/src/component/editor/editor-explorer.vue:351
        """
        return self._request(
            "post", "/ai/new-name", headers=self._headers(),
            data={"name": name, "folder_id": folder_id, "version": version},
        ).json()

    def set_leek_ai(self, leek_id: int, ai_id: int) -> dict[str, Any]:
        """Set which AI a leek uses."""
        return self._request(
            "post", "/leek/set-ai", headers=self._headers(), data={"leek_id": leek_id, "ai_id": ai_id},
        ).json()

    # Market operations
    def buy_fights(self, quantity: int = 1) -> dict[str, Any]:
        """Buy fight packs from market (50 fights per pack)."""
        return self._request(
            "post", "/market/buy-habs-quantity",
            headers=self._browser_headers("/market"),
            json={"item_id": "50fights", "quantity": quantity},
        ).json()

    def get_market(self) -> dict[str, Any]:
        """Get market items and prices."""
        return self._request("get", "/market/get-item-templates", headers=self._headers()).json()

    def buy_item(self, item_id: int, quantity: int = 1) -> dict[str, Any]:
        """Buy an item from the market with habs.

        Args:
            item_id: The item template ID (e.g., 6 for chip_flash)
            quantity: Number to buy (default 1)

        Raises:
            LeekWarsError: not_enough_habs, etc.
        """
        return self._request(
            "post", "/market/buy-habs-quantity",
            headers=self._browser_headers("/market"),
            json={"item_id": item_id, "quantity": quantity},
        ).json()

    def sell_item(self, item_id: int) -> dict[str, Any]:
        """Sell an item from inventory for habs.

        Source: tools/leek-wars/src/component/market/market.vue:484
        POST market/sell-habs {item_id: template_id}

        Args:
            item_id: The item template ID (same as buy)

        Raises:
            LeekWarsError: not_found, etc.
        """
        return self._request(
            "post", "/market/sell-habs",
            headers=self._browser_headers("/market"),
            json={"item_id": item_id},
        ).json()

    # Inventory & Crafting
    def get_inventory(self) -> dict[str, Any]:
        """Get farmer's inventory (all items, resources, components).

        Inventory is part of farmer data from get-from-token endpoint.

        Returns dict with inventory lists + habs/crystals balance.
        """
        data = self._request("get", "/farmer/get-from-token", headers=self._headers()).json()
        farmer = data.get("farmer", data)
        return {
            "weapons": farmer.get("weapons", []),
            "chips": farmer.get("chips", []),
            "potions": farmer.get("potions", []),
            "hats": farmer.get("hats", []),
            "resources": farmer.get("resources", []),
            "components": farmer.get("components", []),
            "schemes": farmer.get("schemes", []),
            "habs": farmer.get("habs", 0),
            "crystals": farmer.get("crystals", 0),
        }

    def craft_item(self, scheme_id: int) -> dict[str, Any]:
        """Craft an item using a scheme (recipe).

        Raises:
            LeekWarsError: If missing ingredients or other error
        """
        return self._request(
            "post", "/item/craft", headers=self._headers(), data={"scheme_id": scheme_id},
        ).json()

    def get_schemes(self) -> dict[str, Any]:
        """Get all crafting schemes (recipes)."""
        return self._request("get", "/item/get-schemes", headers=self._headers()).json()

    def get_items(self) -> dict[str, Any]:
        """Get all item templates (weapons, chips, resources, etc)."""
        return self._request("get", "/item/get-templates", headers=self._headers()).json()

    # Leek equipment
    def add_chip(self, leek_id: int, chip_id: int) -> dict[str, Any]:
        """Equip a chip to a leek.

        Args:
            leek_id: The leek to equip
            chip_id: The chip item ID (from inventory, not template)

        Raises:
            LeekWarsError: too_much_chips, max_chips, etc.
        """
        return self._request(
            "post", "/leek/add-chip", headers=self._headers(),
            data={"leek_id": leek_id, "chip_id": chip_id},
        ).json()

    def remove_chip(self, leek_id: int, chip_id: int) -> dict[str, Any]:
        """Remove a chip from a leek. Note: uses DELETE method."""
        return self._request(
            "delete", "/leek/remove-chip", headers=self._headers(),
            data={"leek_id": leek_id, "chip_id": chip_id},
        ).json()

    def spend_capital(self, leek_id: int, characteristics: dict[str, int]) -> dict[str, Any]:
        """Spend capital points on stats.

        Source: tools/leek-wars/src/component/leek/capital-dialog.vue:221

        Args:
            leek_id: Leek ID
            characteristics: Dict of stat_name -> points, e.g. {"strength": 50}
        """
        response = self._request(
            "post",
            "/leek/spend-capital",
            headers=self._headers(),
            data={"leek_id": leek_id, "characteristics": json.dumps(characteristics)},
        )
        return response.json()

    def add_weapon(self, leek_id: int, weapon_id: int) -> dict[str, Any]:
        """Equip a weapon to a leek."""
        response = self._request(
            "post",
            "/leek/add-weapon",
            headers=self._headers(),
            data={"leek_id": leek_id, "weapon_id": weapon_id},
        )
        return response.json()

    def remove_weapon(self, weapon_id: int) -> dict[str, Any]:
        """Unequip a weapon from a leek.

        Source: tools/leek-wars/src/component/leek/leek.vue:1243
        Frontend sends DELETE with JSON body (not query params).
        """
        headers = self._headers()
        headers["content-type"] = "application/json"
        response = self._request(
            "delete",
            "/leek/remove-weapon",
            headers=headers,
            content=json.dumps({"weapon_id": weapon_id}),
        )
        return response.json()

    # =========================================================================
    # Test Scenarios - UNLIMITED server-side fights for AI validation
    # Discovered from: tools/leek-wars/src/component/editor/editor-test.vue
    # =========================================================================

    def get_test_scenarios(self) -> dict[str, Any]:
        """Get all saved test scenarios."""
        return self._request("get", "/test-scenario/get-all", headers=self._headers()).json()

    def create_test_scenario(self, name: str) -> dict[str, Any]:
        """Create a new test scenario."""
        return self._request(
            "post", "/test-scenario/new", headers=self._headers(), data={"name": name},
        ).json()

    def update_test_scenario(self, scenario_id: int, data: dict) -> dict[str, Any]:
        """Update test scenario configuration."""
        return self._request(
            "post", "/test-scenario/update", headers=self._headers(),
            data={"id": scenario_id, "data": json.dumps(data)},
        ).json()

    def add_leek_to_scenario(
        self, scenario_id: int, leek_id: int, team: int, ai_id: int | None = None
    ) -> dict[str, Any]:
        """Add a leek to a test scenario."""
        return self._request(
            "post", "/test-scenario/add-leek", headers=self._headers(),
            data={"scenario_id": scenario_id, "leek": leek_id, "team": team, "ai": ai_id if ai_id else ""},
        ).json()

    def run_test_fight(self, scenario_id: int, ai_id: int) -> dict[str, Any]:
        """Run a test fight using a scenario - NO DAILY LIMIT!"""
        return self._request(
            "post", "/ai/test-scenario", headers=self._headers(),
            data={"scenario_id": scenario_id, "ai_id": ai_id},
        ).json()

    def create_test_leek(self, name: str) -> dict[str, Any]:
        """Create a custom test leek with configurable stats."""
        return self._request(
            "post", "/test-leek/new", headers=self._headers(), data={"name": name},
        ).json()

    def update_test_leek(self, leek_id: int, data: dict) -> dict[str, Any]:
        """Update test leek configuration (stats, chips, weapons)."""
        return self._request(
            "post", "/test-leek/update", headers=self._headers(),
            data={"id": leek_id, "data": json.dumps(data)},
        ).json()

    def create_test_map(self, name: str) -> dict[str, Any]:
        """Create a custom test map."""
        return self._request("post", "/test-map/new", headers=self._headers(), data={"name": name}).json()

    def update_test_map(self, map_id: int, data: dict) -> dict[str, Any]:
        """Update test map configuration."""
        return self._request(
            "post", "/test-map/update", headers=self._headers(),
            data={"id": map_id, "data": json.dumps(data)},
        ).json()

    # --- Tournament Methods ---

    def get_tournaments(self, power: int | None = None) -> dict[str, Any]:
        """Get available tournaments for farmer.

        Source: tools/leek-wars/src/component/farmer/farmer.vue:930
        """
        if power is None:
            farmer = self.get_farmer(self.farmer_id) if self.farmer_id else {}
            farmer_data = farmer.get("farmer", farmer)
            leeks = farmer_data.get("leeks", {})
            power = sum(l.get("level", 1) ** 1.1 for l in leeks.values())

        return self._request("get", f"/tournament/range-farmer/{round(power)}", headers=self._headers()).json()

    def get_tournament(self, tournament_id: int) -> dict[str, Any]:
        """Get tournament details."""
        return self._request("get", f"/tournament/get/{tournament_id}", headers=self._headers()).json()

    def register_tournament(self, entity_type: str, entity_id: int) -> dict[str, Any]:
        """Register for a tournament. Returns result or raises LeekWarsError."""
        if entity_type == "farmer":
            return self._request("post", "/farmer/register-tournament", headers=self._headers()).json()
        elif entity_type == "leek":
            return self._request(
                "post", "/leek/register-tournament", headers=self._headers(), data={"leek_id": entity_id},
            ).json()
        raise ValueError(f"Unknown entity type: {entity_type}")

    def unregister_tournament(self, entity_type: str, entity_id: int) -> dict[str, Any]:
        """Unregister from a tournament."""
        if entity_type == "farmer":
            return self._request("post", "/farmer/unregister-tournament", headers=self._headers()).json()
        elif entity_type == "leek":
            return self._request(
                "post", "/leek/unregister-tournament", headers=self._headers(), data={"leek_id": entity_id},
            ).json()
        raise ValueError(f"Unknown entity type: {entity_type}")

    def close(self):
        """Close HTTP client."""
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
