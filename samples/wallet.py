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
    os.path.join(PROJECT_DIR.parent, "pysui"),
    os.path.join(PROJECT_DIR.parent, "pysui/sui"),
    os.path.join(PROJECT_DIR.parent, "pysui/abstracts"),
]

from pysui.abstracts import SignatureScheme
from pysui.sui import SuiConfig
from pysui.sui.sui_rpc import SuiRpcResult

# from src.sui.sui_constants import SUI_ADDRESS_STRING_LEN, SUI_HEX_ADDRESS_STRING_LEN
from pysui.sui.sui_crypto import SuiAddress
from pysui.sui.sui_types import ObjectID, SuiPackageObject, SuiNumber
from .faux_wallet import SuiWallet


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

    def _detail_gas(gas_objects: SuiRpcResult):
        if gas_objects.is_ok():
            for gasobj in gas_objects.result_data:
                print(f"{gasobj.identifier} | {gasobj.balance}")
            print(f"Total Gas = {wallet.total_gas(gas_objects.result_data)}")
        else:
            print(f"{gas_objects}")

    _detail_gas(wallet.gas_objects(args.address))


def sui_new_address(wallet: SuiWallet, args: argparse.Namespace) -> None:
    """Generate a new SUI address."""
    if args.ed25519:
        print(wallet.create_new_keypair_and_address(SignatureScheme.ED25519))
    else:
        print(wallet.create_new_keypair_and_address(SignatureScheme.SECP256K1))


def sui_package(wallet: SuiWallet, args: argparse.Namespace) -> None:
    """Get a package object."""
    result: SuiRpcResult = wallet.get_package(args.id)
    if result.is_ok():
        print(result.result_data)
        print()
    else:
        print(f"{result.result_string}")


def sui_package_object(wallet: SuiWallet, args: argparse.Namespace) -> None:
    """Get a package object."""
    result: SuiRpcResult = wallet.get_package_object(args.id)
    if result.is_ok():
        package: SuiPackageObject = result.result_data
        print()
        print("Package")
        print(f"id: {str(package.identifier)} owner: {package.owner}")
        print()
        print("Modules")
        modules: dict = package.modules
        for mod in modules.keys():
            print(f"-> {mod}")
            if args.src:
                print(modules[mod])
        print()
    else:
        print(f"{result.result_string}")


def sui_object(wallet: SuiWallet, args: argparse.Namespace) -> None:
    """Show specific object."""
    sobject = wallet.get_object(args.id)
    # print("Object Descriptor")
    # print(sobject.descriptor.json_pretty())
    if sobject.is_ok():
        print("Object")
        print(sobject.result_data.json_pretty())
    else:
        print(f"{sobject.result_string}")


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

    def _object_type(args: argparse.Namespace) -> SuiRpcResult:
        """Get objects of type from Namespace."""
        if args.nft:
            return wallet.nft_objects(args.address)
        elif args.data:
            return wallet.data_objects(args.address)
        else:
            return wallet.get_objects(args.address)

    result = _object_type(args)
    if result.is_ok():
        if args.json:
            for desc in result:
                print(desc.json_pretty())
        else:
            _objects_header_print()
            for desc in result.result_data:
                print(f"{desc.identifier} |      {desc.version}    | {desc.digest} | {desc.type_signature}")
    else:
        print(f"{result.result_string}")


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


def transfer_sui(wallet: SuiWallet, args: argparse.Namespace) -> None:
    """Transfer gas object."""
    args.from_address = args.from_address if args.from_address else wallet.current_address
    # print(args)
    result = wallet.transfer_sui(args.from_address, args.mist_amount, args.gas_object, args.to_address, args.gas_budget)
    if result.is_ok():
        print(result.result_data)
    else:
        print(f"Error: {result.result_string}")


def check_positive(value: str) -> int:
    """Check for positive integers."""
    ivalue = int(value)
    if ivalue <= 0:
        raise argparse.ArgumentTypeError(f"{value} is an invalid positive int value")
    return SuiNumber(ivalue)


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
    subp.add_argument("--address", required=False, help="Gas for address", action=ValidateAddress)
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
    # Package Object
    subp = subparser.add_parser("package-object", help="Get raw package object with Move assembly source")
    subp.add_argument("--id", required=True, help="package ID", action=ValidateObjectID)
    subp.add_argument("--src", required=False, help="Display package module(s) src", action="store_true")
    subp.set_defaults(func=sui_package_object)
    # Normalized Package
    subp = subparser.add_parser("package", help="Get package definition")
    subp.add_argument("--id", required=True, help="package ID", action=ValidateObjectID)
    subp.set_defaults(func=sui_package)
    # RPC information
    subp = subparser.add_parser("rpcapi", help="Display Sui RPC API information")
    subp.add_argument("-n", "--name", required=False, help="Display details for named Sui RPC API")
    subp.set_defaults(func=sui_api)
    # Transfer SUI
    subp = subparser.add_parser("transfer-sui", help="Transfer SUI gas to recipient")
    subp.add_argument(
        "-a",
        "--mist-amount",
        required=True,
        help="Specify amount of MIST to transfer.",
        type=check_positive,
    )
    subp.add_argument(
        "-o", "--gas-object", required=True, help="Specify gas object to transfer from", action=ValidateObjectID
    )
    subp.add_argument(
        "-t",
        "--to-address",
        required=True,
        help="Specify address to send gas to",
        action=ValidateAddress,
    )
    subp.add_argument(
        "-g",
        "--gas-budget",
        required=True,
        help="Specify transfer transaction budget",
        type=check_positive,
    )
    subp.add_argument(
        "-f",
        "--from-address",
        required=False,
        help="Specify gas owner address. Default to active address",
        action=ValidateAddress,
    )
    subp.set_defaults(func=transfer_sui)
    return parser


def main():
    """Entry point for demonstration."""
    command = build_parser().parse_args(args=None if sys.argv[1:] else ["--help"])
    command.func(SuiWallet(SuiConfig.default()), command)


if __name__ == "__main__":
    main()
