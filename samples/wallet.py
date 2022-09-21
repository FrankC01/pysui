"""Main driver primarily for demonstrating."""

import os
import sys
import pathlib
import pprint

PROJECT_DIR = pathlib.Path(os.path.dirname(__file__))
sys.path += [
    str(PROJECT_DIR),
    os.path.join(PROJECT_DIR.parent, "src"),
    os.path.join(PROJECT_DIR.parent, "src/sui"),
    os.path.join(PROJECT_DIR.parent, "src/abstracts"),
]
from src.sui import SuiConfig
from src.sui import GetPackage

from .faux_wallet import SuiWallet


def wallet_addresses(wallet: SuiWallet) -> None:
    """Print wallet information about addresses."""
    print()
    print(f"Active address {wallet.current_address}")
    print()
    print("Addresses")
    print("---------")
    for addy in wallet.addresses:
        print(addy)


def wallet_gas(wallet: SuiWallet, address: str = None) -> None:
    """Print address gas information."""
    print()
    print("Gas Objects for active address")
    print("------------------------------")
    gas_objects = wallet.gas_objects(address)
    for gas in gas_objects:
        print(f"{gas.identifer} | {gas.balance}")
    print(f"Total Gas = {wallet.total_gas(gas_objects)}")


def wallet_nfts(wallet: SuiWallet, address: str = None) -> None:
    """Print address NFT information."""
    print()
    print("NFT Objects for active address")
    print("------------------------------")
    nft_objects = wallet.nft_objects(address)
    for nft in nft_objects:
        print(f"{nft.identifer} | {nft.name} | {nft.url} | {nft.description}")


def wallet_data_definitions(wallet: SuiWallet, address: str = None) -> None:
    """Print address Data information."""
    print()
    print("Data Descriptors for active address")
    print("-----------------------------------")
    objects = wallet.get_data_descriptors(address)
    for obj in objects:
        print(f"Data Definition {obj.__dict__}")


def wallet_data_objects(wallet: SuiWallet, address: str = None) -> None:
    """Print address Data definitions."""
    print()
    print("Data Objects for active address")
    print("-------------------------------")
    objects = wallet.data_objects(address)
    for obj in objects:
        print(f"Data Definition {obj.data_definition}")
        print(f"Fields {obj.data}")


def wallet_package_objects(wallet: SuiWallet, _address: str = None) -> None:
    """Print data package information."""
    if len(wallet.package_ids) > 0:
        builder = GetPackage()
        if wallet.api_exists(builder.method):
            ids = list(wallet.package_ids)
            package = wallet.get_package(ids[1])
            print()
            print("References packages for active address")
            print("--------------------------------------")
            print(f"Package {ids} modules")
            print(package.__dict__)
        else:
            print(f"Method {builder.method} does not exist")


def main():
    """Entry point for demonstration."""
    wallet = SuiWallet(SuiConfig.default())
    # print(wallet.get_rpc_api_names())
    pprint.pprint(wallet.get_rpc_api())
    wallet.data_objects()
    wallet_package_objects(wallet)


if __name__ == "__main__":
    main()
