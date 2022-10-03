"""Main driver primarily for demonstrating."""

import argparse
import os
import pathlib
import sys
from typing import Any, Sequence


PROJECT_DIR = pathlib.Path(os.path.dirname(__file__))

sys.path += [
    str(PROJECT_DIR),
    os.path.join(PROJECT_DIR.parent, "samples"),
    os.path.join(PROJECT_DIR.parent, "src"),
    os.path.join(PROJECT_DIR.parent, "src/sui"),
    os.path.join(PROJECT_DIR.parent, "src/abstracts"),
]

from src.abstracts import SignatureScheme
from src.sui import SuiConfig
from src.sui import GetPackage

# from src.sui.sui_constants import SUI_ADDRESS_STRING_LEN, SUI_HEX_ADDRESS_STRING_LEN
from src.sui.sui_crypto import SuiAddress
from src.sui.sui_types import ObjectID
from .faux_wallet import SuiWallet, ObjectRead


def wallet_package_objects(wallet: SuiWallet, _address: str = None) -> None:
    """Print data package information."""
    # TODO Fix so that packages won't rely on data objects
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


def sui_active_address(wallet: SuiWallet, _args: argparse.Namespace) -> None:
    """Print active address."""
    print()
    print(f"Active address = {wallet.current_address.identifier}")


def sui_addresses(wallet: SuiWallet, _args: argparse.Namespace) -> None:
    """Print all address."""
    print()
    print("Addresses")
    print("---------")
    for addy in wallet.addresses:
        if addy == wallet.current_address:
            print(f"{addy} <-- active")
        else:
            print(addy)


def sui_gas(wallet: SuiWallet, args: argparse.Namespace) -> None:
    """Print gas information."""

    def _detail_gas(gas_objects):
        for gasobj in gas_objects:
            print(f"{gasobj.identifer} | {gasobj.balance}")
        print(f"Total Gas = {wallet.total_gas(gas_objects)}")

    if args.address is None and args.id is None:
        _detail_gas(wallet.gas_objects())
    elif args.address:
        _detail_gas(wallet.gas_objects(args.address))
    elif args.id:
        print("Gas for Object ID not implemented yet")


def sui_new_address(wallet: SuiWallet, args: argparse.Namespace) -> None:
    """Generate a new SUI address."""
    if args.ed25519:
        print(wallet.create_new_keypair_and_address(SignatureScheme.ED25519))
    else:
        #   TODO: Implement support
        print("secp256k1 not implemented yet.")


def sui_object(wallet: SuiWallet, args: argparse.Namespace) -> None:
    """Show specific object."""
    sobject = wallet.get_object(args.id)
    print("Object Descriptor")
    print(sobject.descriptor.json_pretty())
    print("Object")
    print(sobject.json_pretty())


def _objects_header_print() -> None:
    """Print non-json object header."""
    # TODO: Clean this up with formatted strings
    print("        Object ID                          ", end=" ")
    print("  Version  ", end=" ")
    print("                    Digest                    ", end=" ")
    print("    Object Type")
    print("--------------------------------------------", end="")
    print("------------", end="")
    print("-------------------------------------------------------------------------")


def sui_objects(wallet: SuiWallet, args: argparse.Namespace) -> None:
    """Show specific object."""

    def _object_type(args: argparse.Namespace) -> list[ObjectRead]:
        """Get objects of type from Namespace."""
        if args.nft:
            return wallet.nft_objects(args.address)
        elif args.data:
            return wallet.data_objects(args.address)
        else:
            return wallet.get_objects(args.address)

    result = _object_type(args)
    if args.json:
        for desc in result:
            print(desc.json_pretty())
    else:
        _objects_header_print()
        for desc in result:
            print(f"{desc.identifier} |      {desc.version}    | {desc.digest} | {desc.type_signature}")


def sui_api(wallet: SuiWallet, args: argparse.Namespace) -> None:
    """Display information about Sui RPC API."""
    rpcapi = wallet.get_rpc_api()

    if args.name:
        if rpcapi.get(args.name, None):
            namedef = rpcapi[args.name]
            print()
            print(f"{namedef.name} - {namedef.description}")
            print("Parameters")
            for parm in namedef.params:
                print(f"    {parm.name:<20} => required: {parm.required} type: {parm.schema}")
            print()
            print("Returns")
            print(f"    {namedef.result.name:<20} => type: {namedef.result.schema}")
        else:
            print(f"Sui RPC API does not contain {args.name}")

    else:
        for api_name in rpcapi:
            print(api_name)


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser structure."""

    class ValidateAddress(argparse.Action):
        """Address validator."""

        def __call__(
            self,
            parser: argparse.ArgumentParser,
            namespace: argparse.Namespace,
            values: str | Sequence[Any] | None,
            option_string: str | None = ...,
        ) -> None:
            try:
                values = SuiAddress.from_hex_string(values)
            except ValueError:
                parser.error(f"'{values}' is not valid address.")
                sys.exit(-1)
            setattr(namespace, self.dest, values)

    class ValidateObjectID(argparse.Action):
        """Address validator."""

        def __call__(
            self,
            parser: argparse.ArgumentParser,
            namespace: argparse.Namespace,
            values: str | Sequence[Any] | None,
            option_string: str | None = ...,
        ) -> None:
            try:
                values = ObjectID(values)
            except ValueError:
                parser.error(f"'{values}' is not valid address.")
                sys.exit(-1)
            setattr(namespace, self.dest, values)

    # Base menu
    parser = argparse.ArgumentParser(add_help=True)
    subparser = parser.add_subparsers(title="commands")
    # Address
    subp = subparser.add_parser("active-address", help="Shows active address")
    subp.set_defaults(func=sui_active_address)
    # Addresses
    subp = subparser.add_parser("addresses", help="Shows all addresses")
    subp.set_defaults(func=sui_addresses)
    # Gas
    subp = subparser.add_parser("gas", help="Shows gas objects")
    gas_arg_group = subp.add_mutually_exclusive_group()
    gas_arg_group.add_argument("--address", help="Gas for address")
    gas_arg_group.add_argument("--id", help="Gas for gas object id", action=ValidateAddress)
    subp.set_defaults(func=sui_gas)
    # New address
    subp = subparser.add_parser("new-address", help="Generate new address and keypair")
    addy_arg_group = subp.add_mutually_exclusive_group(required=True)
    addy_arg_group.add_argument("-e", "--ed25519", help="Generate using ed25519 scheme", action="store_true")
    addy_arg_group.add_argument("-s", "--secp256k1", help="Generate using secp256k1 scheme", action="store_true")
    subp.set_defaults(func=sui_new_address)
    # Object
    subp = subparser.add_parser("object", help="Show object by id")
    subp.add_argument("--id", required=True, action=ValidateObjectID)
    subp.add_argument("--json", required=False, help="Display output as json", action="store_true")
    subp.set_defaults(func=sui_object)
    # Objects
    subp = subparser.add_parser("objects", help="Show all objects")
    subp.add_argument("--address", required=False, help="Objects for address", action=ValidateAddress)
    subp.add_argument("--json", required=False, help="Display output as json", action="store_true")
    obj_arg_group = subp.add_mutually_exclusive_group()
    obj_arg_group.add_argument("--nft", help="Only show NFT objects", action="store_true")
    obj_arg_group.add_argument("--data", help="Only show data objects", action="store_true")
    subp.set_defaults(func=sui_objects)
    # RPC information
    subp = subparser.add_parser("rpcapi", help="Display Sui RPC API information")
    subp.add_argument("-n", "--name", required=False, help="Display details for named Sui RPC API")
    subp.set_defaults(func=sui_api)
    return parser


def main():
    """Entry point for demonstration."""
    command = build_parser().parse_args(args=None if sys.argv[1:] else ["--help"])
    command.func(SuiWallet(SuiConfig.default()), command)


if __name__ == "__main__":
    main()
