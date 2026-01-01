#!/usr/bin/env python3
"""Test API authentication formats."""

import httpx

USERNAME = "leek@nech.pl"
PASSWORD = "REDACTED_PASSWORD"
BASE = "https://leekwars.com/api"

# Login and get token from cookies
print("=== LOGIN ===")
response = httpx.post(
    f"{BASE}/farmer/login",
    data={"login": USERNAME, "password": PASSWORD, "keep_connected": "true"},
)
print(f"Status: {response.status_code}")

# Extract token from cookies
token = None
for cookie in response.cookies.jar:
    print(f"Cookie: {cookie.name} = {cookie.value[:50] if len(cookie.value) > 50 else cookie.value}...")
    if cookie.name == "token":
        token = cookie.value

print(f"\nToken: {token[:60]}..." if token else "No token!")

# Test garden with different auth methods
print("\n=== GARDEN ENDPOINT TESTS ===")

# Method 1: Token in URL (old style)
print("\n[1] Token in URL path:")
r = httpx.get(f"{BASE}/garden/get/{token}")
print(f"    Status: {r.status_code}")
if r.status_code == 200:
    print(f"    Keys: {list(r.json().keys())[:5]}")
else:
    print(f"    Error: {r.text[:100]}")

# Method 2: Authorization header
print("\n[2] Authorization: Bearer header:")
r = httpx.get(f"{BASE}/garden/get", headers={"Authorization": f"Bearer {token}"})
print(f"    Status: {r.status_code}")
if r.status_code == 200:
    print(f"    Keys: {list(r.json().keys())[:5]}")
else:
    print(f"    Error: {r.text[:100]}")

# Method 3: Cookie-based (reuse session)
print("\n[3] Cookie-based (session):")
client = httpx.Client()
# Login with client to persist cookies
r = client.post(
    f"{BASE}/farmer/login",
    data={"login": USERNAME, "password": PASSWORD, "keep_connected": "true"},
)
print(f"    Login status: {r.status_code}")

# Now try garden
r = client.get(f"{BASE}/garden/get")
print(f"    Garden status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"    Keys: {list(data.keys())[:5]}")
    if "garden" in data:
        g = data["garden"]
        print(f"    Solo fights: {g.get('solo_fights')}")
        print(f"    Farmer fights: {g.get('farmer_fights')}")
else:
    print(f"    Error: {r.text[:100]}")

# Test opponents
print("\n=== OPPONENTS TEST ===")
r = client.get(f"{BASE}/garden/get-leek-opponents/131321")
print(f"Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"Keys: {list(data.keys())}")
    if "opponents" in data:
        for opp in data["opponents"][:3]:
            print(f"  - {opp.get('name')} L{opp.get('level')} T{opp.get('talent')}")
else:
    print(f"Error: {r.text[:200]}")

client.close()
