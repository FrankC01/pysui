#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Sample module for incremental buildout of Async Sui gRPC for Pysui 1.0.0."""

import asyncio

from pysui import PysuiConfiguration, SuiRpcResult, GrpcProtocolClient, client_factory
from pysui.sui.sui_common.client import PysuiClient
import pysui.sui.sui_grpc.pgrpc_requests as rn


async def _protocol_version_for(profile_name: str):
    """Extract the protocol version for the particular profile."""
    try:
        client: PysuiClient = client_factory(
            PysuiConfiguration(
                group_name=PysuiConfiguration.SUI_GRPC_GROUP, profile_name=profile_name
            )
        )
        prtcl_cfg = await client.protocol()
        if client:
            client.close()
        return f"{profile_name} protocol version = {prtcl_cfg.transaction_constraints.protocol_version}"
    except ValueError as ve:
        ve_s = ve.args
        return f"{profile_name} protocol version = {ve_s[0]}"
    finally:
        pass


async def main():
    """Example main."""

    try:
        pysui_config = PysuiConfiguration(
            group_name=PysuiConfiguration.SUI_GRPC_GROUP,  # Default gRPC group
        )
        _coros = [
            asyncio.create_task(_protocol_version_for(_prof))
            for _prof in pysui_config.profile_names()
        ]

        _coros_res = await asyncio.gather(*_coros, return_exceptions=True)
        print()
        for x in _coros_res:
            print(x)
    except (ValueError, NotImplementedError) as ve:
        print(ve)
    finally:
        pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (ValueError, asyncio.CancelledError, Exception) as rte:
        print(rte)
