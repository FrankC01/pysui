#!/usr/bin/env python3
# Copyright (c), Frank V. Castellucci
# SPDX-License-Identifier: Apache-2.0
"""
scratch/ucs_zklogin_example.py

zkLogin flow using ZkClient / ZkSession from pysui.zklogin_seal.

Usage:
    python scratch/ucs_zklogin_example.py \
        --credentials ~/Downloads/client_secret.json \
        [--salt <decimal-string>] \
        [--max-epoch <int>]

Opens a browser for Google sign-in, catches the OAuth callback on localhost,
exchanges the auth code for an id_token, then drives the full zkLogin flow
through ZkClient / ZkSession.

NOTE: --salt should be stored between runs — the same salt produces the same
zkLogin Sui address. Omitting it generates a new random salt each run.
"""

import argparse
import asyncio
import http.server
import json
import httpx
import urllib.parse
import webbrowser

from pysui.sui.sui_common.async_txn import AsyncSuiTransaction
from pysui.zklogin_seal.config import ZkSealConfig
from pysui.zklogin_seal.zklogin_client import ZkClient, ZkSession, generate_user_salt

from pysui import (
    client_factory,
    AsyncClientBase,
    GetBasicCurrentEpochInfo,
    ExecuteTransaction,
    PysuiConfiguration,
)

OAUTH_PORT = 8085


def get_id_token(credentials_path: str, nonce: str) -> str:
    """Perform Google OAuth flow and return the id_token with nonce embedded."""
    with open(credentials_path, encoding="utf-8") as f:
        creds = json.load(f)

    installed = creds.get("installed", creds)
    client_id = installed["client_id"]
    client_secret = installed["client_secret"]
    redirect_uri = f"http://localhost:{OAUTH_PORT}"

    auth_params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email",
        "nonce": nonce,
    }
    auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(
        auth_params
    )

    auth_code: list[str] = []

    class CallbackHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # pylint: disable=invalid-name
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)
            if "code" in params:
                auth_code.append(params["code"][0])
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Auth complete. You can close this tab.")

        def log_message(self, fmt: str, *args: object) -> None:
            pass  # suppress server logs

    server = http.server.HTTPServer(("localhost", OAUTH_PORT), CallbackHandler)
    webbrowser.open(auth_url)
    print(f"  Opened browser for Google sign-in. Waiting on port {OAUTH_PORT}...")
    server.handle_request()
    server.server_close()

    if not auth_code:
        raise RuntimeError("No auth code received from OAuth callback")

    resp = httpx.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": auth_code[0],
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        },
    )
    resp.raise_for_status()
    token_data = resp.json()

    return token_data["id_token"]


async def run(
    pysui_client: AsyncClientBase,
    credentials_path: str,
    salt: str,
    max_epoch: int,
) -> None:
    # Step 1: Load config and create ZkClient
    print("\n--- Step 1: Load config and create ZkClient ---")
    cfg = ZkSealConfig()
    zk_client = ZkClient(config=cfg, salt=salt)
    print(f"  active group : {cfg.active_group.group_name}")
    print(f"  salt         : {zk_client.salt}")

    result = await pysui_client.execute(command=GetBasicCurrentEpochInfo())
    if result.is_ok():
        current_epoch = result.result_data.epoch
        max_epoch = current_epoch + max_epoch
    else:
        raise RuntimeError(result.result_string)

    # Step 2: Create session — generates ephemeral keypair and nonce
    print("\n--- Step 2: Create ZkSession (provider=google) ---")
    session: ZkSession = zk_client.session(
        provider="google",
        current_epoch=current_epoch,
        max_epoch=max_epoch,
    )
    print(f"  nonce        : {session.nonce}")

    # Step 3: Google OAuth → id_token with nonce embedded
    print("\n--- Step 3: Google OAuth → id_token ---")
    jwt = get_id_token(credentials_path, session.nonce)
    print(f"  id_token     : {jwt[:60]}...")

    # Step 4: Extract claims, verify nonce, derive zkLogin address
    print("\n--- Step 4: process_jwt() ---")
    address = session.process_jwt(jwt=jwt)
    print(f"  address      : {address}")

    # Step 5: Fetch ZK proof from prover service (async)
    print("\n--- Step 5: get_proof() ---")
    result = await session.get_proof()
    if not result.is_ok():
        print(f"  ERROR: {result.result_string}")
        return
    print("  ZK proof obtained OK")

    # Step 6: ZkLoginKeyPair is now available for signing
    print("\n--- Step 6: ZkLoginKeyPair ready ---")
    kp = session.keypair
    print(f"  ephemeral scheme : {kp.ephemeral_scheme}")
    print(f"  sui address      : {session.address}")
    print()
    print("Done.")

    # Step 7: Create a transaction with the emphemeral address
    txer: AsyncSuiTransaction = await pysui_client.transaction(
        initial_sender=session.address
    )
    scoin = await txer.split_coin(txer.gas, amounts=[1_000_000])
    await txer.transfer_objects([scoin], pysui_client.config.active_address)

    # Step 8: Sign and execute transaction
    # COMMENTED OUT DUE TO LACK OF SUPPORT IN PYSUI SIGNING
    # tx_dict: dict = await txer.build_and_sign()
    # result = await pysui_client.execute(command=ExecuteTransaction(**tx_dict))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="pysui zkLogin example — full Google OAuth flow"
    )
    parser.add_argument(
        "--credentials",
        required=True,
        metavar="PATH",
        help="Path to GCP Desktop app credentials JSON (client_secret_*.json)",
    )
    parser.add_argument(
        "--salt",
        default=None,
        metavar="DECIMAL",
        help="zkLogin user salt (128-bit decimal string). Generated randomly if omitted — store it!",
    )
    parser.add_argument(
        "--max-epoch",
        type=int,
        default=5,
        metavar="INT",
        help="Number of epochs the ephemeral keypair remains valid (max 30, default: 5)",
    )
    args = parser.parse_args()

    salt = args.salt if args.salt else generate_user_salt()
    if not args.salt:
        print(f"[NOTE] Generated salt: {salt}")
        print(
            "       Store this value — same salt produces the same zkLogin address.\n"
        )

    client_init: AsyncClientBase = client_factory(
        PysuiConfiguration(
            group_name=PysuiConfiguration.SUI_GRPC_GROUP,
            profile_name="devnet",
        )
    )

    asyncio.run(run(client_init, args.credentials, salt, args.max_epoch))


if __name__ == "__main__":
    main()
