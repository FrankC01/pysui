"""Main driver primarily for testing."""

import os
import sys
import pathlib

PROJECT_DIR = pathlib.Path(os.path.dirname(__file__))
sys.path += [
    str(PROJECT_DIR),
    os.path.join(PROJECT_DIR.parent, "src"),
    os.path.join(PROJECT_DIR.parent, "src/sui"),
    os.path.join(PROJECT_DIR.parent, "src/abstracts"),
]

from samples.sample_wallet import SuiWallet
from src.sui import SuiConfig


def main():
    """Entry point for test driving."""
    wallet = SuiWallet(SuiConfig.default())

    print("Gas Objects")
    print("-----------")
    gas_objects = wallet.gas_objects()
    for gas in gas_objects:
        print(f"{gas.identifer} | {gas.balance}")
    print(f"Total Gas = {wallet.total_gas(gas_objects)}")
    print()
    print("NFT Objects")
    print("-----------")
    nft_objects = wallet.nft_objects()
    for nft in nft_objects:
        print(f"{nft.identifer} | {nft.name} | {nft.url} | {nft.description}")
    print()
    print("Data Objects")
    print("------------")
    objects = wallet.data_objects()
    for obj in objects:
        print(f"Data Definition {obj.data_definition}")
        print(f"Fields {obj.data}")
        wallet.data_object_children(obj)


if __name__ == "__main__":
    main()
