"""Allow running as: python -m src.mcp_freshbooks"""

import os


def _load_apify_input() -> None:
    """Load credentials from Apify actor input when running on the platform."""
    token = os.environ.get("APIFY_TOKEN", "")
    store_id = os.environ.get("APIFY_DEFAULT_KEY_VALUE_STORE_ID", "")
    if not (token and store_id):
        return

    import httpx

    try:
        resp = httpx.get(
            f"https://api.apify.com/v2/key-value-stores/{store_id}/records/INPUT",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("freshbooksClientId"):
                os.environ["FRESHBOOKS_CLIENT_ID"] = data["freshbooksClientId"]
            if data.get("freshbooksClientSecret"):
                os.environ["FRESHBOOKS_CLIENT_SECRET"] = data["freshbooksClientSecret"]
            if data.get("freshbooksRedirectUri"):
                os.environ["FRESHBOOKS_REDIRECT_URI"] = data["freshbooksRedirectUri"]
    except Exception:
        pass


if os.environ.get("ACTOR_STANDBY_PORT"):
    _load_apify_input()

from src.mcp_freshbooks.server import main

main()
