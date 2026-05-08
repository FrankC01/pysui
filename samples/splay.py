#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Splay (spread) coins to self or other addresses."""

import asyncio
import os
import pathlib
import sys
from typing import Optional

PROJECT_DIR = pathlib.Path(os.path.dirname(__file__))
PARENT = PROJECT_DIR.parent

sys.path.insert(0, str(PROJECT_DIR))
sys.path.insert(0, str(PARENT))
sys.path.insert(0, str(os.path.join(PARENT, "pysui")))

_splay_version = "1.1.0"

import logging

logger = logging.getLogger()
logging.basicConfig(
    filename="splay.log",
    filemode="a",
    encoding="utf-8",
    format="%(asctime)s %(module)s %(levelname)s %(message)s",
    level=logging.INFO,
)

logger.info("Initializing splay.")

import pysui.sui.sui_common.async_funcs as asfn
import pysui.sui.sui_common.sui_commands as cmd
import pysui.sui.sui_grpc.suimsgs.sui.rpc.v2 as sui_prot
from pysui.sui.sui_constants import SUI_COIN_DENOMINATOR
from pysui import PysuiConfiguration, PysuiClient, client_factory, __version__, SuiRpcResult
from pysui.sui.sui_common.async_txn import AsyncSuiTransaction
from samples.cmd_argsg import build_splay_parser, pre_config_pull


def sdk_version():
    """Dispay version(s)."""
    print(f"splay version: {_splay_version} SDK version: {__version__}")


async def merge_for_gas(
    client: PysuiClient,
    merge_includes: Optional[str],
    merge_excludes: Optional[str],
) -> sui_prot.Object:
    """Merge coins to one (1) coin which becomes gas."""
    task_result = await asyncio.gather(
        asfn.merge_sui(
            client=client,
            address=client.config.active_address,
            merge_only=merge_includes,
            exclude=merge_excludes,
            wait=False,
        ),
        return_exceptions=True,
    )
    if isinstance(task_result[0], tuple):
        merge_status, effects, master_coin_id, _ = task_result[0]
        if merge_status == asfn.OperationStatus.OPS_FAIL:
            raise ValueError(effects)
        res = await client.execute(command=cmd.GetCoinSummary(coin_id=master_coin_id))
        if res.is_ok():
            return res.result_data
        raise ValueError(res.result_string)
    raise task_result[0]


async def _process_txn(
    client: PysuiClient,
    txn: AsyncSuiTransaction,
    gas_coin: sui_prot.Object,
) -> sui_prot.ExecutedTransaction:
    """Execute the transaction.

    :param client: Sui node client
    :type client: PysuiClient
    :param txn: The transaction to sign and execute
    :type txn: AsyncSuiTransaction
    :param gas_coin: The coin to use for transaction gas
    :type gas_coin: sui_prot.Object
    :return: Executed transaction result or ValueError on failure
    :rtype: sui_prot.ExecutedTransaction
    """
    build_result = await txn.build_and_sign(use_gas_objects=[gas_coin])
    result = await client.execute(command=cmd.ExecuteTransaction(**build_result))
    if result.is_ok():
        executed = result.result_data
        if not executed.effects.status.success:
            logger.info(f"Splay failed {executed.effects.status}")
            return ValueError(f"Splay transaction failed: {executed.effects.status}")
        return executed
    return ValueError(result.result_string)


async def splay_n_to_self(
    client: PysuiClient,
    mgas: asyncio.Task,
    explicit_count: int,
    amount_per: Optional[int] = None,
) -> sui_prot.ExecutedTransaction:
    """Splays coins from and to signing address.

    :param client: Sui node client
    :type client: PysuiClient
    :param mgas: Merge coin task
    :type mgas: asyncio.Task
    :param explicit_count: The number of coins created and sent to signing address
    :type explicit_count: int
    :param amount_per: Explicit amount per coin, defaults to None
    :type amount_per: Optional[int], optional
    :return: Executed transaction result or ValueError on failure
    :rtype: sui_prot.ExecutedTransaction
    """
    task_result = await mgas
    if isinstance(task_result, sui_prot.Object):
        r_balance = int(task_result.balance)
        distro = amount_per if amount_per else int(r_balance / explicit_count)
        total_distro = distro * explicit_count
        if r_balance >= total_distro:
            txn: AsyncSuiTransaction = await client.transaction()
            amounts = [distro for x in range(explicit_count)]
            r_coins = await txn.split_coin(coin=txn.gas, amounts=amounts)
            await txn.transfer_objects(
                transfers=r_coins, recipient=client.config.active_address
            )
            return await _process_txn(client, txn, task_result)
        else:
            return ValueError(
                f"Splay total {total_distro} exceeds available coin balance of {r_balance}"
            )
    else:
        return task_result


async def splay_n_to_others(
    client: PysuiClient,
    recipients: list[str],
    mgas: asyncio.Task,
    amount_per: Optional[int] = None,
) -> sui_prot.ExecutedTransaction:
    """Splays coins to recipients.

    :param client: Sui node client
    :type client: PysuiClient
    :param recipients: List of recipients to receive splayed coins
    :type recipients: list[str]
    :param mgas: Merge gas task
    :type mgas: asyncio.Task
    :param amount_per: Explicit amount per coin, defaults to None
    :type amount_per: Optional[int], optional
    :return: Executed transaction result or ValueError on failure
    :rtype: sui_prot.ExecutedTransaction
    """
    task_result = await mgas
    if isinstance(task_result, sui_prot.Object):
        r_count = len(recipients)
        r_balance = int(task_result.balance)
        distro = amount_per if amount_per else int(r_balance / r_count)
        total_distro = distro * r_count
        if r_balance >= total_distro:
            txn: AsyncSuiTransaction = await client.transaction()
            if r_count == 1:
                r_coins = await txn.split_coin(coin=txn.gas, amounts=[distro])
                await txn.transfer_objects(transfers=[r_coins], recipient=recipients[0])
            else:
                amounts = [distro for x in range(r_count)]
                r_coins = await txn.split_coin(coin=txn.gas, amounts=amounts)
                for idx in range(r_count):
                    await txn.transfer_objects(
                        transfers=[r_coins[idx]], recipient=recipients[idx]
                    )
            return await _process_txn(client, txn, task_result)
        else:
            return ValueError(
                f"Splay total {total_distro} exceeds available coin balance of {r_balance}"
            )
    else:
        return task_result


# TT
# o/a - Not valid
# o/a/n - Split to self for count
# o/a/r - Split to recipient(s) that represent count


def _reconcille_args(
    *,
    client: PysuiClient,
    send_to: Optional[list[str]] = None,
    merge_only: Optional[str] = None,
    exclude_from_merge: Optional[str] = None,
    explicit_count: Optional[int] = 0,
    mist: Optional[str] = None,
):
    """Validate coherent args."""
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

    # Resolve recipients from config if none supplied and not self-splaying
    if not send_to and not explicit_count:
        my_addy = client.config.active_address
        send_to = [x for x in client.config.active_group.address_list if x != my_addy]

    # Validate: must have a destination
    if not send_to and not explicit_count:
        raise ValueError("No recipients and no count specified")
    if explicit_count and explicit_count < 2:
        raise ValueError("splaying to self must specify -n >= 2")

    smasher = asyncio.create_task(
        merge_for_gas(client, merge_only, exclude_from_merge),
        name="smasher",
    )

    if explicit_count:
        return splay_n_to_self(client, smasher, explicit_count, mist)
    else:
        return splay_n_to_others(client, send_to, smasher, mist)


async def main_run(
    *,
    client: PysuiClient,
    send_to: Optional[list[str]] = None,
    merge_only: Optional[str] = None,
    exclude_from_merge: Optional[str] = None,
    explicit_count: Optional[int] = 0,
    mist: Optional[str] = None,
):
    """Main splay asynchronous entry point."""
    try:
        routine = _reconcille_args(
            client=client,
            send_to=send_to,
            merge_only=merge_only,
            exclude_from_merge=exclude_from_merge,
            explicit_count=explicit_count,
            mist=mist,
        )
        res = await asyncio.gather(routine)
        print(res[0])
    finally:
        await client.close()


def main():
    """Entry point for splay utility."""
    cfg, arg_line = pre_config_pull(sys.argv[1:].copy())
    parsed = build_splay_parser(arg_line, cfg)
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
        f"splaying coins for alias: {cfg.active_address_alias} with address: {cfg.active_address}"
    )
    if parsed.dry_run:
        send_to = parsed.recipients or []
        explicit_count = parsed.number or 0
        if not send_to and not explicit_count:
            my_addy = cfg.active_address
            send_to = [x for x in cfg.active_group.address_list if x != my_addy]
        print(f"  number    : {parsed.number}")
        print(f"  recipients: {parsed.recipients}")
        print(f"  mist      : {parsed.mist}")
        print(f"  include   : {parsed.include}")
        print(f"  exclude   : {parsed.exclude}")
        if not send_to and not explicit_count:
            print("  route     : ERROR — No recipients and no count specified")
        elif explicit_count and explicit_count < 2:
            print("  route     : ERROR — splaying to self must specify -n >= 2")
        elif explicit_count:
            print(f"  route     : splay_n_to_self(count={explicit_count})")
        else:
            print(f"  route     : splay_n_to_others(recipients={send_to})")
        return
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    arpc = client_factory(cfg)
    try:
        loop.run_until_complete(
            main_run(
                client=arpc,
                send_to=parsed.recipients,
                merge_only=parsed.include,
                exclude_from_merge=parsed.exclude,
                explicit_count=parsed.number,
                mist=parsed.mist,
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
