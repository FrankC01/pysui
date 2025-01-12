#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Splay (spread) coins to self or other addresses."""

import asyncio
import base64
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
import pysui.sui.sui_pgql.pgql_query as qn
from pysui.sui.sui_constants import SUI_COIN_DENOMINATOR
from pysui import PysuiConfiguration, AsyncGqlClient, __version__, SuiRpcResult
from pysui.sui.sui_pgql.pgql_async_txn import AsyncSuiTransaction
from samples.cmd_argsg import build_splay_parser


def sdk_version():
    """Dispay version(s)."""
    print(f"splay version: {_splay_version} SDK version: {__version__}")


async def merge_for_gas(
    client: AsyncGqlClient,
    merge_includes: Optional[str],
    merge_excludes: Optional[str],
    wait: Optional[bool] = False,
):
    """Merge coins for playing to one (1) coin which becomes gas."""
    task_result = await asyncio.gather(
        asfn.merge_sui(
            client=client,
            address=client.config.active_address,
            merge_only=merge_includes,
            exclude=merge_excludes,
            wait=wait,
        ),
        return_exceptions=True,
    )
    if isinstance(task_result[0], tuple):
        merge_status, effects, master_coin, _ = cast(
            tuple[
                asfn.OperationStatus,
                bcst.TransactionEffects,
                pgql_type.SuiCoinObjectGQL,
                pgql_type.TransactionResultGQL,
            ],
            task_result[0],
        )
        # Quick exit with fail
        if merge_status == asfn.OperationStatus.OPS_FAIL:
            raise ValueError(effects)
        # No merge, balance is good
        elif merge_status == asfn.OperationStatus.ONE_COIN_NO_MERGE:
            return master_coin
        # Otherwise a merge occured so get a coin refresh
        res = await client.execute_query_node(
            with_node=qn.GetCoinSummary(
                owner=client.config.active_address,
                coin_id=master_coin.coin_object_id,
            )
        )
        if res.is_ok():
            return res.result_data
        else:
            return ValueError(res.result_string)
    raise task_result[0]


async def splay_n_to_self(
    client: AsyncGqlClient,
    mgas: asyncio.Task,
    explicit_count: int,
    budget: int,
    amount_per: Optional[int] = None,
):
    """."""
    task_result = await mgas
    if isinstance(
        task_result, (pgql_type.SuiCoinObjectGQL, pgql_type.SuiCoinObjectSummaryGQL)
    ):

        r_balance = int(task_result.balance)
        balance = r_balance - budget
        distro = amount_per if amount_per else int(balance / explicit_count)
        total_distro = distro * explicit_count
        if balance >= total_distro:
            txn = AsyncSuiTransaction(client=client)
            amounts = [distro for x in range(explicit_count)]
            r_coins = await txn.split_coin(coin=txn.gas, amounts=amounts)
            await txn.transfer_objects(
                transfers=r_coins, recipient=client.config.active_address
            )
            results = await client.execute_query_node(
                with_node=qn.ExecuteTransaction(
                    **await txn.build_and_sign(
                        gas_budget=budget, use_gas_objects=[task_result]
                    )
                )
            )
            tx_effects = bcst.TransactionEffects.deserialize(
                base64.b64decode(results.result_data.bcs)
            ).value
            if tx_effects.status.enum_name != "Success":
                logger.info(f"Merge gas failed {tx_effects.status.to_json(indent=2)}")
                return ValueError(f"Splay transaction failed{tx_effects.status.value}")
            else:
                return "Success"
            # if wait:
            #     res: SuiRpcResult = await client.wait_for_transaction(
            #         digest=tx_effects.transactionDigest.to_digest_str()
            #     )
            #     if res.is_err():
            #         raise ValueError(
            #             f"Merge transaction `{res.result_data.digest}` failed."
            #         )
            #     return (OperationStatus.MERGE, tx_effects, use_as_gas, res.result_data)

        else:
            return ValueError(
                f"Splay total {total_distro} exceeds available coin balance of {balance}"
            )
    else:
        return task_result


async def split_n_to_others(
    client: AsyncGqlClient,
    amounts: list[int],
    recipients: list[str],
    mgas: asyncio.Task,
):
    """."""
    task_result = await mgas
    if isinstance(task_result, pgql_type.SuiCoinObjectGQL):
        pass
    else:
        raise task_result


# TT
# o/a - Not valid
# o/a/n - Split to self for count
# o/a/r - Split to recipient(s) that represent count


def _reconcille_args(
    *,
    client: AsyncGqlClient,
    budget: int,
    send_to: Optional[list[str]] = None,
    merge_only: Optional[str] = None,
    exclude_from_merge: Optional[str] = None,
    explicit_count: Optional[int] = 0,
    mist: Optional[str] = None,
    wait_for_commit: Optional[bool] = False,
):
    """Validate coherent args."""
    # if no recipients, we are splaying for owner
    send_to = send_to or []
    merge_only = merge_only or []
    exclude_from_merge = exclude_from_merge or []
    # Validate mist if sent
    if mist:
        if mist.endswith(("S", "s")):
            mist = mist[:-1]
            if mist.count("."):
                mist = SUI_COIN_DENOMINATOR * float(mist)
            else:
                mist = SUI_COIN_DENOMINATOR * int(mist)
        mist = int(mist)

    if not send_to and (not explicit_count or explicit_count < 2):
        raise ValueError(f"splaying to self must specify -n >= 1")
    if explicit_count:
        return splay_n_to_self(
            client,
            asyncio.create_task(
                merge_for_gas(client, merge_only, exclude_from_merge, True),
                name="merger",
            ),
            explicit_count,
            budget,
            mist,
        )


async def main_run(
    *,
    client: AsyncGqlClient,
    budget: int,
    send_to: Optional[list[str]] = None,
    merge_only: Optional[str] = None,
    exclude_from_merge: Optional[str] = None,
    explicit_count: Optional[int] = 0,
    mist: Optional[str] = None,
    wait_for_commit: Optional[bool] = False,
):
    """Main splay asynchronous entry point."""
    routine = _reconcille_args(
        client=client,
        budget=budget,
        send_to=send_to,
        merge_only=merge_only,
        exclude_from_merge=exclude_from_merge,
        explicit_count=explicit_count,
        mist=mist,
        wait_for_commit=wait_for_commit,
    )

    res = await asyncio.gather(routine)
    print(res[0])
    await client.close()


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
    print(
        f"splaying coins for alias: {cfg.active_address_alias} with address: {cfg.active_address}"
    )
    arpc = AsyncGqlClient(pysui_config=cfg)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(
            main_run(
                client=arpc,
                budget=parsed.budget,
                send_to=parsed.recipients,
                merge_only=parsed.include,
                exclude_from_merge=parsed.exclude,
                explicit_count=parsed.number,
                mist=parsed.mist,
                wait_for_commit=parsed.wait,
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
