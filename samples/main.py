"""Main driver primarily for demonstrating."""

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
from src.sui import SuiConfig
from .sample_wallet import SuiWallet


def main():
    """Entry point for demonstration."""
    wallet = SuiWallet(SuiConfig.default())

    print()
    print(f"Active address {wallet.current_address}")
    print()
    print("Addresses")
    print("---------")
    for addy in wallet.addresses:
        print(addy)
    print()
    print("Gas Objects for active address")
    print("------------------------------")
    gas_objects = wallet.gas_objects()
    for gas in gas_objects:
        print(f"{gas.identifer} | {gas.balance}")
    print(f"Total Gas = {wallet.total_gas(gas_objects)}")
    print()
    print("NFT Objects for active address")
    print("------------------------------")
    nft_objects = wallet.nft_objects()
    for nft in nft_objects:
        print(f"{nft.identifer} | {nft.name} | {nft.url} | {nft.description}")
    print()
    print("Data Descriptors for active address")
    print("-----------------------------------")
    objects = wallet.get_data_descriptors()
    for obj in objects:
        print(f"Data Definition {obj.__dict__}")
    print()
    print("Data Objects for active address")
    print("-------------------------------")
    objects = wallet.data_objects()
    for obj in objects:
        print(f"Data Definition {obj.data_definition}")
        print(f"Fields {obj.data}")

    if len(wallet.package_ids) > 0:
        print()
        print("References packages for active address")
        print("--------------------------------------")
        package = wallet.get_package(list(wallet.package_ids)[0])
        print(package.__dict__)


if __name__ == "__main__":
    main()
