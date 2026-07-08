#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Confidential Transfer (private funds) example command-line tool.

Exercises pysui private-transfer support (configuration, id derivation, and — as
they are added — registration and rekey) for validation and clarification ahead
of a live Confidential Transfer deployment.  Commands are added incrementally;
the first, ``validate_config``, resolves and validates a
:class:`PrivateFundsConfig` against the active ``PysuiConfiguration`` profile.
"""

import argparse
import asyncio
import base64
import json
import sys
from pathlib import Path

from pysui import (
    PysuiConfiguration,
    SuiRpcResult,
    client_factory,
    SimulateTransactionKind,
    ExecuteTransaction,
)
from pysui.private_transfer import utils
from pysui.private_transfer._ext import (
    generate_twisted_elgamal_keypair,
    raise_for_crypto,
)
from pysui.private_transfer.config import PrivateFundsConfig

# ---------------------------------------------------------------------------
# Fixed example parameters
# ---------------------------------------------------------------------------

#: Confidential-token coin type ``T`` this example operates on.  The example is
#: fixed to a single known token type; set this to the deployed devnet token
#: type before running ``register_accounts``.
TOKEN_TYPE = "0xb0eaf410ca6c030f450fb0ab96e497c6007c7284f688674e78aedd1c495bd760::pysui_token::PYSUI_TOKEN"

#: Sidecar file name, persisted under the ``--path`` directory (default
#: ``~/.pysui``).  Holds SELF CT identities only, keyed
#: ``network -> sender -> token_type -> {current, history}``.
SIDECAR_FILENAME = "PrivateFundsSidecar.json"


def validate_config(*, args: argparse.Namespace, pysui_config: PysuiConfiguration) -> None:
    """Validate a PrivateFundsConfig against the active PysuiConfiguration profile.

    :param args: Parsed command arguments (uses ``args.path``)
    :type args: argparse.Namespace
    :param pysui_config: The shared pysui configuration driving group resolution
    :type pysui_config: PysuiConfiguration
    """
    try:
        pfconfig = PrivateFundsConfig(pysui_config=pysui_config, from_cfg_path=args.path)
    except ValueError as exc:
        print(f"PrivateFundsConfig validation FAILED: {exc}")
        return
    group = pfconfig.active_group
    print(f"PrivateFundsConfig validated for profile '{pysui_config.active_profile}':")
    print(f"  group name:      {group.name}")
    print(f"  packageId:       {group.package_id}")
    print(f"  tokenRegistry:   {group.token_registry}")
    print(f"  accountRegistry: {group.account_registry}")


def _sidecar_file(*, path: str | None) -> Path:
    """Resolve the sidecar JSON file path.

    :param path: Optional directory (default: ``~/.pysui``)
    :type path: str | None
    :returns: Full path to the sidecar JSON file
    :rtype: Path
    """
    base = Path(path).expanduser() if path else Path("~/.pysui").expanduser()
    return base / SIDECAR_FILENAME


def _load_sidecar(*, sidecar_file: Path) -> dict:
    """Load the sidecar JSON, returning an empty mapping when absent.

    :param sidecar_file: Path to the sidecar JSON file
    :type sidecar_file: Path
    :returns: The parsed sidecar mapping (empty if the file does not exist)
    :rtype: dict
    """
    if sidecar_file.exists():
        return json.loads(sidecar_file.read_text())
    return {}


def _save_sidecar(*, sidecar_file: Path, data: dict) -> None:
    """Persist the sidecar JSON, creating the parent directory as needed.

    :param sidecar_file: Path to the sidecar JSON file
    :type sidecar_file: Path
    :param data: The sidecar mapping to serialise
    :type data: dict
    """
    sidecar_file.parent.mkdir(parents=True, exist_ok=True)
    sidecar_file.write_text(json.dumps(data, indent=2))


def register_accounts(*, args: argparse.Namespace, pysui_config: PysuiConfiguration) -> None:
    """Generate CT keypairs and create sidecar entries for one or more addresses.

    For each address supplied on the command line this:

    * confirms the address is known to the active ``PysuiConfiguration`` group,
    * derives the account id and generates a Twisted-ElGamal CT keypair,
    * writes a new sidecar entry, skipping any address already registered for
      :data:`TOKEN_TYPE` (never overwriting an existing keypair).

    No on-chain transaction is submitted; entries are built entirely from
    client-side derivation and local keypair generation.

    :param args: Parsed command arguments (uses ``args.addresses`` and ``args.path``)
    :type args: argparse.Namespace
    :param pysui_config: The shared pysui configuration driving group resolution
    :type pysui_config: PysuiConfiguration
    """
    raise_for_crypto()
    try:
        pfconfig = PrivateFundsConfig(pysui_config=pysui_config, from_cfg_path=args.path)
    except ValueError as exc:
        print(f"PrivateFundsConfig validation FAILED: {exc}")
        return

    group = pfconfig.active_group
    network = pysui_config.active_profile
    known = pysui_config.active_group.address_list

    sidecar_file = _sidecar_file(path=args.path)
    sidecar = _load_sidecar(sidecar_file=sidecar_file)
    net_entry = sidecar.setdefault(network, {})

    print(f"register_accounts on '{network}' for token type '{TOKEN_TYPE}':")
    changed = False
    for address in args.addresses:
        if address not in known:
            print(f"  {address}: NOT in PysuiConfiguration group — skipping")
            continue
        addr_entry = net_entry.setdefault(address, {})
        if TOKEN_TYPE in addr_entry:
            print(f"  {address}: already registered for token type — skipping")
            continue
        acct_id = utils.account_id(
            package_id=group.package_id,
            account_registry_id=group.account_registry,
            owner=address,
        )
        keypair = generate_twisted_elgamal_keypair()
        addr_entry["account_id"] = acct_id
        addr_entry[TOKEN_TYPE] = {
            "current": {
                "pf_private": base64.b64encode(keypair["private_key"]).decode("ascii"),
                "pf_public": base64.b64encode(keypair["public_key"]).decode("ascii"),
                "registered_auditor_version": None,
            },
            "history": [],
        }
        changed = True
        print(f"  {address}: registered (account_id={acct_id})")

    if changed:
        _save_sidecar(sidecar_file=sidecar_file, data=sidecar)
        print(f"Sidecar updated: {sidecar_file}")
    else:
        print(f"No changes; sidecar not written ({sidecar_file}).")


def handle_result(result: SuiRpcResult) -> SuiRpcResult:
    """Print an execution or simulation result and return it unchanged.

    :param result: The result returned from ``client.execute``.
    :type result: SuiRpcResult
    :returns: The same result, unchanged.
    :rtype: SuiRpcResult
    """
    if result.is_ok():
        if hasattr(result.result_data, "to_json"):
            print(result.result_data.to_json(indent=2))
        else:
            print(result.result_data)
    else:
        print(result.result_string)
        if result.result_data and hasattr(result.result_data, "to_json"):
            print(result.result_data.to_json(indent=2))
        else:
            print(result.result_data)
    return result


async def register_private_funds(*, args: argparse.Namespace, pysui_config: PysuiConfiguration) -> None:
    """Register a single address on-chain for Confidential Transfers.

    Resolves the address's Twisted-ElGamal public key from the sidecar (which
    ``register_accounts`` must have populated), builds the registration PTB via
    :meth:`PrivateFundsTransaction.register_private_funds`, then either simulates
    or executes it per ``--mode``.

    :param args: Parsed CLI arguments (``address``, ``token_type``, ``mode``, ``path``).
    :type args: argparse.Namespace
    :param pysui_config: The shared pysui configuration.
    :type pysui_config: PysuiConfiguration
    """
    address = args.address
    coin_type = args.token_type
    network = pysui_config.active_profile
    sidecar_file = _sidecar_file(path=args.path)
    sidecar = _load_sidecar(sidecar_file=sidecar_file)
    entry = sidecar.get(network, {}).get(address, {}).get(coin_type, {}).get("current", {})
    pf_public = entry.get("pf_public")
    if not pf_public:
        raise SystemExit(
            f"No sidecar entry with a public key for address {address} "
            f"(network {network}, token {coin_type}) in {sidecar_file}. "
            f"Run the 'register_accounts' command first."
        )
    elgamal_public_key = base64.b64decode(pf_public)

    client = client_factory(pysui_config)
    txn = await client.transaction(private_fund=True)
    await txn.register_private_funds(coin_type=coin_type, owner=address, elgamal_public_key=elgamal_public_key)

    if args.mode == "simulate":
        handle_result(
            await client.execute(
                command=SimulateTransactionKind(
                    tx_kind=await txn.raw_kind(),
                    tx_meta={"sender": address},
                    gas_selection=True,
                )
            )
        )
    else:
        txdict = await txn.build_and_sign()
        handle_result(await client.execute(command=ExecuteTransaction(**txdict)))


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser and register all subcommands.

    :returns: The configured argument parser
    :rtype: argparse.ArgumentParser
    """
    parser = argparse.ArgumentParser(
        prog="ucs_private_funds_example",
        description="Confidential Transfer (private funds) example commands.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate = subparsers.add_parser(
        "validate_config",
        help="Validate PrivateFundsConfig against the active PysuiConfiguration profile.",
    )
    validate.add_argument(
        "--path",
        default=None,
        help="Optional directory containing PrivateFundsConfig.json (default: ~/.pysui).",
    )
    register = subparsers.add_parser(
        "register_accounts",
        help="Generate CT keypairs and create sidecar entries for one or more addresses.",
    )
    register.add_argument(
        "addresses",
        nargs="+",
        help="One or more Sui addresses (each must exist in the active PysuiConfiguration group).",
    )
    register.add_argument(
        "--path",
        default=None,
        help="Optional directory for PrivateFundsConfig.json and the sidecar (default: ~/.pysui).",
    )
    register_pf = subparsers.add_parser(
        "register_private_funds",
        help="Register a single address on-chain for Confidential Transfers (simulate or execute).",
    )
    register_pf.add_argument(
        "address",
        help="The Sui address to register (must have a sidecar entry from 'register_accounts').",
    )
    register_pf.add_argument(
        "token_type",
        help="The confidential coin type (T) to register for; must match a sidecar entry for the address.",
    )
    register_pf.add_argument(
        "--mode",
        choices=["simulate", "execute"],
        default="simulate",
        help="Simulate (default) or execute the registration transaction.",
    )
    register_pf.add_argument(
        "--path",
        default=None,
        help="Optional directory containing the sidecar (default: ~/.pysui).",
    )
    return parser


async def main(*, pysui_config: PysuiConfiguration) -> None:
    """Parse arguments and dispatch to the selected command.

    :param pysui_config: The shared pysui configuration
    :type pysui_config: PysuiConfiguration
    """
    args = build_parser().parse_args()
    if args.command == "validate_config":
        validate_config(args=args, pysui_config=pysui_config)
    elif args.command == "register_accounts":
        register_accounts(args=args, pysui_config=pysui_config)
    elif args.command == "register_private_funds":
        await register_private_funds(args=args, pysui_config=pysui_config)
    # Future async commands dispatch with await, e.g.:
    # elif args.command == "transfer":
    #     await transfer(args=args, pysui_config=pysui_config)


if __name__ == "__main__":
    # Optionally force a specific command + arguments (uncomment one):
    # sys.argv = ["ucs_private_funds_example.py", "validate_config"]
    # sys.argv = [
    #     "ucs_private_funds_example.py",
    #     "validate_config",
    #     "--path",
    #     "~/.pwallet",
    # ]
    # sys.argv = [
    #     "ucs_private_funds_example.py",
    #     "register_accounts",
    #     "0xa9e2db385f055cc0215a3cde268b76270535b9443807514f183be86926c219f4",
    #     "0xa9fe7b9cab7ce187c768a9b16e95dbc5953a99ec461067a73a6b1c4288873e28",
    # ]
    sys.argv = [
        "ucs_private_funds_example.py",
        "register_private_funds",
        "0xa9e2db385f055cc0215a3cde268b76270535b9443807514f183be86926c219f4",
        "0xb0eaf410ca6c030f450fb0ab96e497c6007c7284f688674e78aedd1c495bd760::pysui_token::PYSUI_TOKEN",
        # "--mode",
        # "execute",
    ]
    # sys.argv = [
    #     "ucs_private_funds_example.py",
    #     "register_accounts",
    #     "0xADDRESS_ONE",
    #     "--path",
    #     "~/.pwallet",
    # ]

    _pysui_config = PysuiConfiguration(
        # Uncomment one group:
        group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP,
        # group_name=PysuiConfiguration.SUI_GRPC_GROUP,
        profile_name="devnet",
        # profile_name="testnet",
        # profile_name="mainnet",
    )
    asyncio.run(main(pysui_config=_pysui_config))
