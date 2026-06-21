#!/usr/bin/env python3
# Copyright (c), Frank V. Castellucci
# SPDX-License-Identifier: Apache-2.0
"""
ucs_seal_example.py

SEAL IBE encrypt/decrypt example using pysui SealClient.

Usage:
    python scratch/ucs_seal_example.py create [--name NAME]
    python scratch/ucs_seal_example.py add-address [--address ADDR]
    python scratch/ucs_seal_example.py demo --data TEXT [--out PATH]

Actors:
    Bob   — alias 'Primary'   — encryptor, allowlist owner
    Alice — alias 'Secondary' — decryptor, must be on allowlist

Testnet constants are hardcoded. Requires pysui[zklogin-seal] installed.
"""

import argparse
import asyncio
import sys


from pysui import (
    PysuiConfiguration,
    client_factory,
    AsyncClientBase,
    ExecuteTransaction,
)
from pysui.sui.sui_common.async_txn import AsyncSuiTransaction
from pysui.zklogin_seal.config import ZkSealConfig
from pysui.zklogin_seal.seal_client import SealClient
from pysui.zklogin_seal.types import SealDemType, SealEncryptedObject

# ── Testnet constants ─────────────────────────────────────────────────────────

SEAL_PACKAGE_ID = "0xdccbeb87767be2b2346af5575eb139807205e4c23ec53dc616f951fe1d814112"

ALLOWLIST_OBJECT_ID = (
    "0x06eff4946e9dc22bad0bf3e46c6285bfaeeffc28024de989e0f61fe6e20d4b8c"
)
CAP_OBJECT_ID = "0x479d48cc3d2db3bebe3e68555bcb27373592e523f36971d9755cdae9d6d51bdb"
DEMO_PACKAGE_ID = "0xc5ce2742cac46421b62028557f1d7aea8a4c50f651379a79afdf12cd88628807"

DEFAULT_ENCRYPTED_PATH = "/tmp/seal_encrypted.bin"


# ── Command handlers ──────────────────────────────────────────────────────────


async def cmd_create(
    *,
    seal_client: SealClient,
    args: argparse.Namespace,
) -> None:
    """Create a new allowlist and cap using the SEAL demo package (Bob becomes owner)."""
    print("\n--- create ---")

    txn: AsyncSuiTransaction = await seal_client.pysui_client.transaction()
    await txn.move_call(
        target=f"{DEMO_PACKAGE_ID}::allowlist::create_allowlist_entry",
        arguments=[args.name],
    )

    tx_dict: dict = await txn.build_and_sign()
    result = await seal_client.pysui_client.execute(
        command=ExecuteTransaction(**tx_dict)
    )
    if result.is_ok():
        print("  allowlist created OK")
        print(result.result_data.to_json(indent=2))
        print(
            "\n  Update ALLOWLIST_OBJECT_ID and CAP_OBJECT_ID constants with the IDs above."
        )
    else:
        print(f"  ERROR: {result.result_string}")


async def cmd_add_address(
    *,
    seal_client: SealClient,
    args: argparse.Namespace,
) -> None:
    """Add an address to the SEAL allowlist (Bob signs, owns the Cap)."""
    print("\n--- add-address ---")

    address_to_add = args.address
    print(f"  adding address : {address_to_add}")

    # Build PTB: allowlist::add(allowlist_obj, cap, address)
    txn: AsyncSuiTransaction = await seal_client.pysui_client.transaction()
    await txn.move_call(
        target=f"{DEMO_PACKAGE_ID}::allowlist::add",
        arguments=[ALLOWLIST_OBJECT_ID, CAP_OBJECT_ID, address_to_add],
    )

    # Sign and execute (Bob is active address / signer)
    tx_dict: dict = await txn.build_and_sign()
    result = await seal_client.pysui_client.execute(
        command=ExecuteTransaction(**tx_dict)
    )
    if result.is_ok():
        print("  address added OK")
        print(result.result_data.to_json(indent=2))
    else:
        print(f"  ERROR: {result.result_string}")


async def cmd_demo(
    *,
    bob_seal_client: SealClient,
    alice_seal_client: SealClient,
    args: argparse.Namespace,
) -> None:
    """Full SEAL IBE roundtrip: Bob encrypts, Alice decrypts."""
    print("\n--- demo (encrypt → decrypt) ---")

    # Refresh key server URLs from on-chain
    await bob_seal_client.config.refresh_all_server_urls(
        client=bob_seal_client.pysui_client
    )

    inner_id = bytes.fromhex(ALLOWLIST_OBJECT_ID.removeprefix("0x"))

    # ── Bob context: encrypt ──────────────────────────────────────────────────
    print(f"\n  [Bob] encrypting '{args.data}' ...")

    if args.committee:
        key_servers = [
            ("mysten-testnet", "mysten-testnet-1"),
            ("mysten-testnet-committee", "mysten-committee"),
        ]
        print("  mode            : mixed (1 non-committee + 1 committee)")
    else:
        key_servers = [
            ("mysten-testnet", "mysten-testnet-1", "mysten-testnet-2"),
            ("third-party", "ruby-nodes"),
        ]
        print("  mode            : all non-committee (3 servers, threshold 2)")

    encrypt_result = await bob_seal_client.encrypt(
        package_id=DEMO_PACKAGE_ID,
        inner_id=inner_id,
        key_servers=key_servers,
        threshold=2,
        data=args.data.encode(),
    )
    if not encrypt_result.is_ok():
        print(f"  ERROR (encrypt): {encrypt_result.result_string}")
        return

    encrypted_obj, _dem_key = encrypt_result.result_data
    print(f"  encrypted bytes : {len(encrypted_obj.as_bytes())} bytes")

    with open(args.out, "wb") as f:
        f.write(encrypted_obj.as_bytes())
    print(f"  saved to        : {args.out}")

    # ── Alice context: decrypt ────────────────────────────────────────────────
    print("\n  [Alice] decrypting ...")

    # Alice generates credentials from her own SealClient instance
    alice_creds = alice_seal_client.credentials()

    # Alice builds an unsigned seal_approve PTB — proof of eligibility for key servers
    # The key server prepends first_pkg_id; we pass just inner_id (allowlist object ID bytes)
    alice_txn: AsyncSuiTransaction = await alice_seal_client.pysui_client.transaction()
    await alice_txn.move_call(
        target=f"{DEMO_PACKAGE_ID}::allowlist::seal_approve",
        arguments=[inner_id, ALLOWLIST_OBJECT_ID],
    )
    ptb_raw: bytes = (await alice_txn.raw_kind()).serialize()

    decrypt_result = await alice_seal_client.decrypt(
        encrypted_object=encrypted_obj,
        transaction_kind=ptb_raw,
        credentials=alice_creds,
    )
    if not decrypt_result.is_ok():
        print(f"  ERROR (decrypt): {decrypt_result.result_string}")
        return

    plaintext: bytes = decrypt_result.result_data
    print(f"  decrypted       : {plaintext.decode()}")


# ── Entry point ───────────────────────────────────────────────────────────────


async def run(pysui_config: PysuiConfiguration, args: argparse.Namespace) -> None:
    # Bob's client (always)
    bob_pysui_client: AsyncClientBase = client_factory(pysui_config)
    seal_config = ZkSealConfig()
    bob_seal_client = SealClient(client=bob_pysui_client, config=seal_config)

    print(f"  network : {bob_seal_client.config.active_group.group_name}")
    print(f"  bob     : {pysui_config.active_address}")

    try:
        if args.command == "create":
            await cmd_create(
                seal_client=bob_seal_client,
                args=args,
            )
        elif args.command == "add-address":
            await cmd_add_address(
                seal_client=bob_seal_client,
                args=args,
            )
        elif args.command == "demo":
            # Alice's client — separate PysuiConfiguration with address=args.receiver
            alice_pysui_config = PysuiConfiguration(
                group_name=PysuiConfiguration.SUI_GRPC_GROUP,
                profile_name="testnet",
                address=args.receiver,
            )
            alice_pysui_client: AsyncClientBase = client_factory(alice_pysui_config)
            alice_seal_client = SealClient(
                client=alice_pysui_client, config=seal_config
            )
            print(f"  alice   : {alice_pysui_config.active_address}")
            try:
                await cmd_demo(
                    bob_seal_client=bob_seal_client,
                    alice_seal_client=alice_seal_client,
                    args=args,
                )
            finally:
                await alice_pysui_client.close()
    finally:
        await bob_pysui_client.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="pysui SEAL example — IBE encrypt/decrypt on testnet"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # create
    sub_create = subparsers.add_parser(
        "create", help="Create a new allowlist (Bob becomes owner)"
    )
    sub_create.add_argument(
        "--name",
        default="my-allowlist",
        metavar="NAME",
        help="Name for the new allowlist (default: my-allowlist)",
    )

    # add-address
    sub_add = subparsers.add_parser(
        "add-address", help="Add Alice's address to the SEAL allowlist"
    )
    sub_add.add_argument(
        "--address",
        required=True,
        metavar="ADDR",
        help="Address to add to the allowlist",
    )

    # demo
    sub_demo = subparsers.add_parser(
        "demo", help="Full roundtrip: Bob encrypts, Alice decrypts"
    )
    sub_demo.add_argument(
        "--data",
        required=True,
        metavar="TEXT",
        help="Plaintext string to encrypt",
    )
    sub_demo.add_argument(
        "--out",
        default=DEFAULT_ENCRYPTED_PATH,
        metavar="PATH",
        help=f"Intermediate file for encrypted bytes (default: {DEFAULT_ENCRYPTED_PATH})",
    )
    sub_demo.add_argument(
        "--committee",
        action="store_true",
        default=False,
        help="Use mixed key servers: 1 non-committee + 1 committee (default: 2 non-committee)",
    )
    sub_demo.add_argument(
        "--receiver",
        required=True,
        metavar="ADDR",
        help="Alice's Sui address (the decryptor)",
    )

    args = parser.parse_args()

    # Bob's configuration — Primary alias is default active address
    config = PysuiConfiguration(
        group_name=PysuiConfiguration.SUI_GRPC_GROUP,
        profile_name="testnet",
    )

    asyncio.run(run(config, args))


if __name__ == "__main__":
    # Uncomment one block to select the command to exercise; comment out the other.

    # ── create: create a new allowlist owned by Bob ───────────────────────────
    # sys.argv = ["ucs_seal_example.py", "create"]
    # sys.argv = ["ucs_seal_example.py", "create", "--name", "my-allowlist"]

    # ── add-address: add Alice to the allowlist ───────────────────────────────
    # (--address is optional; omit to default to ALICE_ALIAS)
    # sys.argv = ["ucs_seal_example.py", "add-address"]
    # sys.argv = [
    #     "ucs_seal_example.py",
    #     "add-address",
    #     "--address",
    #     "0xADDRESS_HERE",
    # ]

    # ── demo: full IBE roundtrip — Bob encrypts, Alice decrypts ──────────────
    # default: 2 non-committee key servers
    sys.argv = [
        "ucs_seal_example.py",
        "demo",
        "--data",
        "Monday I've got Friday on my Mind.",
        "--receiver",
        "0xa9fe7b9cab7ce187c768a9b16e95dbc5953a99ec461067a73a6b1c4288873e28",
    ]
    # sys.argv = ["ucs_seal_example.py", "demo", "--data", "hello from Bob", "--out", "/tmp/seal_encrypted.bin"]
    # mixed: 1 non-committee + 1 committee key server
    # sys.argv = [
    #     "ucs_seal_example.py",
    #     "demo",
    #     "--data",
    #     "The Man Who Sold The World",
    #     "--committee",
    # ]

    main()
