"""Main driver primarily for testing."""

import os
import sys
import httpx

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__)))
sys.path.append(PROJECT_ROOT)
print(sys.path)
from sui import SuiConfig


def main():
    """Entry point for test driving."""
    dconf = SuiConfig()
    client = httpx.Client()
    data = {
        "jsonrpc": "2.0",
        "id": 1,
    }
    data["method"] = "sui_getObjectsOwnedByAddress"
    data["params"] = [dconf.active_address]
    headers = {"Content-Type": "application/json"}
    client = httpx.Client(headers=headers)
    try:
        result = client.post(dconf.url, json=data)
        for sui_object in result.json()["result"]:
            print(sui_object)
    except httpx.RequestError as exc:
        print(f"An error occurred while requesting {exc.request.url!r}.")


if __name__ == "__main__":
    main()
