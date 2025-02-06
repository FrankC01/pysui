#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Smash (merge) addresses sui coins to one."""

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

_smash_version = "1.0.0"

import logging

logger = logging.getLogger()
logging.basicConfig(
    filename="smash.log",
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
from samples.cmd_argsg import build_smash_parser


def sdk_version():
    """Dispay version(s)."""
    print(f"smash version: {_smash_version} SDK version: {__version__}")


async def main_run(
    *,
    client: AsyncGqlClient,
    includes: list[str],
    excludes: list[str],
    wait: bool,
):
    """Main smash asynchronous entry point."""
    task_result = await asyncio.gather(
        asfn.merge_sui(
            client=client,
            address=client.config.active_address,
            merge_only=includes,
            exclude=excludes,
            wait=wait,
        ),
        return_exceptions=True,
    )
    if isinstance(task_result[0], tuple):
        merge_status, effects, master_coin, wait_result = cast(
            tuple[
                asfn.OperationStatus,
                bcst.TransactionEffects,
                pgql_type.SuiCoinObjectGQL,
                pgql_type.TransactionResultGQL,
            ],
            task_result[0],
        )
        # effects, master_coin = task_result[0]
        if merge_status == asfn.OperationStatus.MERGE:
            print(f"Succesful smash to coin {master_coin.coin_object_id}")
        elif merge_status == asfn.OperationStatus.ONE_COIN_NO_MERGE:
            print(
                f"No merge, only 1 Sui coin for address {client.config.active_address}"
            )
        await client.close()
    else:
        await client.close()
        raise task_result[0]


def _group_pull(cli_arg: list, config: PysuiConfiguration) -> list:
    """Check for group and set accordingly."""

    if cli_arg.count("--group"):
        ndx = cli_arg.index("--group")
        nvl: str = cli_arg[ndx + 1]
        config.make_active(group_name=nvl)

    return cli_arg


def main():
    """Entry point for smash utility."""

    cfg = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP)
    arg_line = _group_pull(sys.argv[1:].copy(), cfg)
    parsed = build_smash_parser(arg_line, cfg)
    if parsed.version:
        sdk_version()
        return
    cfg.make_active(
        group_name=parsed.group_name,
        profile_name=parsed.profile_name,
        address=parsed.owner,
        alias=parsed.alias,
        persist=False,
    )
    print(
        f"Smashing coins for alias: {cfg.active_address_alias} with address: {cfg.active_address}"
    )
    arpc = AsyncGqlClient(pysui_config=cfg)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(
            main_run(
                client=arpc,
                includes=parsed.include,
                excludes=parsed.exclude,
                wait=parsed.wait,
            )
        )
    except ValueError as ve:
        print(ve)
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()


if __name__ == "__main__":
    main()
