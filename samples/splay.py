#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Splay (spread) coins to self or other addresses."""

import asyncio
import os
import pathlib
import sys
from typing import Optional, cast

PROJECT_DIR = pathlib.Path(os.path.dirname(__file__))
PARENT = PROJECT_DIR.parent

sys.path.insert(0, str(PROJECT_DIR))
sys.path.insert(0, str(PARENT))
sys.path.insert(0, str(os.path.join(PARENT, "pysui")))

_splay_version = "1.0.0"

import logging

logger = logging.getLogger()
logging.basicConfig(
    filename="splay.log",
    filemode="a",
    encoding="utf-8",
    format="%(asctime)s %(module)s %(levelname)s %(message)s",
    level=logging.INFO,
)

logger.info("Initializing smash.")

import pysui.sui.sui_common.async_funcs as asfn
import pysui.sui.sui_types.bcs_txne as bcst
import pysui.sui.sui_pgql.pgql_types as pgql_type
from pysui import PysuiConfiguration, AsyncGqlClient, __version__, SuiRpcResult
from samples.cmd_argsg import build_splay_parser


def sdk_version():
    """Dispay version(s)."""
    print(f"splay version: {_splay_version} SDK version: {__version__}")


async def main_run(
    *,
    client: AsyncGqlClient,
    recipient: str,
    coins: Optional[str] = None,
    self_num: Optional[int] = 0,
    wait: Optional[bool] = False,
):
    """Main splay asynchronous entry point."""
    coins = coins or []
    task_result = await asyncio.gather(
        asfn.split_to_distribution(client=client, address=client.config.active_address),
        return_exceptions=True,
    )
    if isinstance(task_result[0], tuple):
        merge_status, effects, master_coin = cast(
            tuple[
                asfn.MergeStatus, bcst.TransactionEffects, pgql_type.SuiCoinObjectGQL
            ],
            task_result[0],
        )
        # effects, master_coin = task_result[0]
        if merge_status == asfn.MergeStatus.MERGE:
            if wait:
                res: SuiRpcResult = await client.wait_for_transaction(
                    digest=effects.transactionDigest.to_digest_str()
                )
                if res.is_err():
                    print(f"Transaction `{res.result_data.digest}` failed.")
            print(f"Succesful smash to {master_coin.coin_object_id}")
        elif merge_status == asfn.MergeStatus.ONE_COIN_NO_MERGE:
            print(
                f"No merge, only 1 Sui coin for address {client.config.active_address}"
            )
        await client.close()
    else:
        await client.close()
        raise task_result[0]


# TT
# o/a - Not valid
# o/a/n - Split to self for count
# o/a/r - Split to recipient(s)


def _reconcille_args(
    *,
    address: str,
    send_to: Optional[list[str]] = None,
    merge_only: Optional[str] = None,
    explicit_count: Optional[int] = 0,
    wait_for_commit: Optional[bool] = False,
) -> dict:
    """Validate coherent args."""
    # if no recipients, we are splaying for owner
    send_to = send_to or []
    merge_only = merge_only or []

    if not send_to and not explicit_count or explicit_count <= 1:
        raise ValueError(f"splaying to self must specify -n > 1")
    if explicit_count:
        send_to = [address]

    return {
        "address": address,
        "send_to": send_to,
        "merge_only": merge_only,
        "exclude": [],
        "explicit_count": explicit_count,
        "merge_wait": wait_for_commit,
    }


def main():
    """Entry point for splay utility."""
    arg_line = sys.argv[1:].copy()
    cfg = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP)
    parsed = build_splay_parser(arg_line, cfg)
    if parsed.version:
        sdk_version()
        return
    cfg.make_active(
        profile_name=parsed.profile_name,
        address=parsed.owner,
        alias=parsed.alias,
        persist=False,
    )
    wf_args = _reconcille_args(
        address=cfg.active_address,
        send_to=parsed.recipients,
        merge_only=parsed.coins,
        explicit_count=parsed.number,
        wait_for_commit=parsed.wait,
    )
    print(
        f"splaying coins for alias: {cfg.active_address_alias} with address: {cfg.active_address}"
    )
    # arpc = AsyncGqlClient(pysui_config=cfg)
    # loop = asyncio.new_event_loop()
    # asyncio.set_event_loop(loop)
    # try:
    #     loop.run_until_complete(main_run(client=arpc, wait=parsed.wait))
    # except ValueError as ve:
    #     print(ve)
    # except KeyboardInterrupt:
    #     pass
    # finally:
    #     loop.close()


if __name__ == "__main__":
    main()
