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

    def close(self):
        """Close HTTP client."""
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
