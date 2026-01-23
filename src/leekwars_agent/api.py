"""LeekWars API client."""

import httpx
from typing import Any


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

    def login(self, username: str, password: str, keep_connected: bool = True) -> dict[str, Any]:
        """Login and store token. Returns farmer data on success."""
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
        response = self._client.post(
            "/farmer/disconnect",
            headers=self._headers(),
        )
        response.raise_for_status()
        self.token = None
        return response.json()

    def get_farmer(self, farmer_id: int) -> dict[str, Any]:
        """Get public farmer data."""
        response = self._client.get(f"/farmer/get/{farmer_id}")
        response.raise_for_status()
        return response.json()

    def get_leek(self, leek_id: int) -> dict[str, Any]:
        """Get public leek data."""
        response = self._client.get(f"/leek/get/{leek_id}")
        response.raise_for_status()
        return response.json()

    def get_garden(self) -> dict[str, Any]:
        """Get garden state (authenticated)."""
        response = self._client.get("/garden/get", headers=self._headers())
        response.raise_for_status()
        return response.json()

    def get_leek_opponents(self, leek_id: int) -> dict[str, Any]:
        """Get solo fight opponents for a leek."""
        response = self._client.get(
            f"/garden/get-leek-opponents/{leek_id}",
            headers=self._headers(),
        )
        response.raise_for_status()
        return response.json()

    def get_farmer_opponents(self) -> dict[str, Any]:
        """Get farmer fight opponents."""
        response = self._client.get(
            "/garden/get-farmer-opponents",
            headers=self._headers(),
        )
        response.raise_for_status()
        return response.json()

    def start_solo_fight(self, leek_id: int, target_id: int) -> dict[str, Any]:
        """Start a solo fight."""
        response = self._client.post(
            "/garden/start-solo-fight",
            headers=self._headers(),
            data={"leek_id": leek_id, "target_id": target_id},
        )
        response.raise_for_status()
        return response.json()

    def start_farmer_fight(self, target_id: int) -> dict[str, Any]:
        """Start a farmer fight."""
        response = self._client.post(
            "/garden/start-farmer-fight",
            headers=self._headers(),
            data={"target_id": target_id},
        )
        response.raise_for_status()
        return response.json()

    def get_fight(self, fight_id: int) -> dict[str, Any]:
        """Get fight data."""
        response = self._client.get(f"/fight/get/{fight_id}")
        response.raise_for_status()
        return response.json()

    def get_leek_history(self, leek_id: int, page: int = 0, count: int = 50) -> dict[str, Any]:
        """Get leek fight history."""
        response = self._client.get(
            f"/leek/get-history/{leek_id}/{page}/{count}",
            headers=self._headers(),
        )
        response.raise_for_status()
        return response.json()

    def get_constants(self) -> dict[str, Any]:
        """Get game constants."""
        response = self._client.get("/constant/get-all")
        response.raise_for_status()
        return response.json()

    def get_chips(self) -> dict[str, Any]:
        """Get all chips data."""
        response = self._client.get("/chip/get-all")
        response.raise_for_status()
        return response.json()

    def get_weapons(self) -> dict[str, Any]:
        """Get all weapons data."""
        response = self._client.get("/weapon/get-all")
        response.raise_for_status()
        return response.json()

    def get_functions(self) -> dict[str, Any]:
        """Get all LeekScript functions."""
        response = self._client.get("/function/get-all")
        response.raise_for_status()
        return response.json()

    # AI Management
    def get_ai(self, ai_id: int) -> dict[str, Any]:
        """Get AI code and metadata."""
        response = self._client.get(f"/ai/get/{ai_id}", headers=self._headers())
        response.raise_for_status()
        return response.json()

    def get_farmer_ais(self) -> dict[str, Any]:
        """Get all farmer's AIs."""
        response = self._client.get("/ai/get-farmer-ais", headers=self._headers())
        response.raise_for_status()
        return response.json()

    def save_ai(self, ai_id: int, code: str) -> dict[str, Any]:
        """Save AI code."""
        response = self._client.post(
            "/ai/save",
            headers=self._headers(),
            data={"ai_id": ai_id, "code": code},
        )
        response.raise_for_status()
        return response.json()

    def rename_ai(self, ai_id: int, name: str) -> dict[str, Any]:
        """Rename an AI."""
        response = self._client.post(
            "/ai/rename",
            headers=self._headers(),
            data={"ai_id": ai_id, "name": name},
        )
        response.raise_for_status()
        return response.json()

    def create_ai(self, name: str = "NewAI", folder_id: int = 0) -> dict[str, Any]:
        """Create a new AI."""
        response = self._client.post(
            "/ai/new",
            headers=self._headers(),
            data={"name": name, "folder_id": folder_id},
        )
        response.raise_for_status()
        return response.json()

    def set_leek_ai(self, leek_id: int, ai_id: int) -> dict[str, Any]:
        """Set which AI a leek uses."""
        response = self._client.post(
            "/leek/set-ai",
            headers=self._headers(),
            data={"leek_id": leek_id, "ai_id": ai_id},
        )
        response.raise_for_status()
        return response.json()

    # Market operations
    def buy_fights(self, quantity: int = 1) -> dict[str, Any]:
        """Buy fight packs from market (50 fights per pack)."""
        headers = self._headers()
        headers["Content-Type"] = "application/json; charset=UTF-8"
        response = self._client.post(
            "/market/buy-habs-quantity",
            headers=headers,
            json={"item_id": "50fights", "quantity": quantity},
        )
        response.raise_for_status()
        return response.json()

    def get_market(self) -> dict[str, Any]:
        """Get market items and prices."""
        response = self._client.get("/market/get-item-templates", headers=self._headers())
        response.raise_for_status()
        return response.json()

    def buy_item(self, item_id: int, quantity: int = 1) -> dict[str, Any]:
        """Buy an item from the market with habs.

        Args:
            item_id: The item template ID (e.g., 6 for chip_flash)
            quantity: Number to buy (default 1)

        Returns:
            Purchase result with new item data
        """
        headers = self._headers()
        headers["Content-Type"] = "application/json; charset=UTF-8"
        response = self._client.post(
            "/market/buy-habs-quantity",
            headers=headers,
            json={"item_id": item_id, "quantity": quantity},
        )
        response.raise_for_status()
        return response.json()

    # Inventory & Crafting
    def get_inventory(self) -> dict[str, Any]:
        """Get farmer's inventory (all items, resources, components).

        Inventory is part of farmer data from get-from-token endpoint.

        Returns dict with inventory lists:
        - weapons, chips, potions, hats, resources, components, schemes
        Each item has: id, template, quantity, time
        """
        response = self._client.get("/farmer/get-from-token", headers=self._headers())
        response.raise_for_status()
        data = response.json()
        farmer = data.get("farmer", data)

        # Extract inventory categories
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

        Args:
            scheme_id: The recipe ID (1-60, see schemes.ts for full list)

        Returns:
            Crafted item data: {id, template, time, quantity}

        Raises:
            HTTPStatusError: If missing ingredients or other error
        """
        response = self._client.post(
            "/item/craft",
            headers=self._headers(),
            data={"scheme_id": scheme_id},
        )
        response.raise_for_status()
        return response.json()

    def get_schemes(self) -> dict[str, Any]:
        """Get all crafting schemes (recipes).

        Returns dict with 'schemes' containing recipe definitions.
        Each scheme has: id, items (ingredients), result, quantity
        """
        response = self._client.get("/item/get-schemes", headers=self._headers())
        response.raise_for_status()
        return response.json()

    def get_items(self) -> dict[str, Any]:
        """Get all item templates (weapons, chips, resources, etc).

        Returns dict with item template definitions.
        """
        response = self._client.get("/item/get-templates", headers=self._headers())
        response.raise_for_status()
        return response.json()

    # Leek equipment
    def add_chip(self, leek_id: int, chip_id: int) -> dict[str, Any]:
        """Equip a chip to a leek.

        Args:
            leek_id: The leek to equip
            chip_id: The chip item ID (from inventory, not template)
        """
        response = self._client.post(
            "/leek/add-chip",
            headers=self._headers(),
            data={"leek_id": leek_id, "chip_id": chip_id},
        )
        response.raise_for_status()
        return response.json()

    def remove_chip(self, leek_id: int, chip_id: int) -> dict[str, Any]:
        """Remove a chip from a leek."""
        response = self._client.post(
            "/leek/remove-chip",
            headers=self._headers(),
            data={"leek_id": leek_id, "chip_id": chip_id},
        )
        response.raise_for_status()
        return response.json()

    def add_weapon(self, leek_id: int, weapon_id: int) -> dict[str, Any]:
        """Equip a weapon to a leek."""
        response = self._client.post(
            "/leek/add-weapon",
            headers=self._headers(),
            data={"leek_id": leek_id, "weapon_id": weapon_id},
        )
        response.raise_for_status()
        return response.json()

    def close(self):
        """Close HTTP client."""
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
