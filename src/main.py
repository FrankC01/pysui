"""Main driver primarily for testing."""

import os
import sys
import httpx

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__)))
sys.path.append(PROJECT_ROOT)

from sui import ObjectsForAddress, SuiConfig, SuiClient
from sui import parse_sui_object_descriptors


def main():
    """Entry point for test driving."""
    dconf = SuiConfig()
    client = SuiClient(dconf)
    builder = ObjectsForAddress().add_parameter(dconf.active_address)
    try:
        result = client.execute(builder)
        for sui_object in result.json()["result"]:
            sui_type = parse_sui_object_descriptors(sui_object)
            print(f"{sui_type.__class__.__name__} {sui_type.__dict__}")
    except httpx.RequestError as exc:
        print(f"An error occurred while requesting {exc.request.url!r}.")


if __name__ == "__main__":
    main()
