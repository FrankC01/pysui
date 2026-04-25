#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Caching transaction executor for gRPC."""

import logging
from typing import Optional

from pysui.sui.sui_common.executors.base_caching_executor import _BaseCachingExecutor
from pysui.sui.sui_common.txb_signing import SignerBlock

logger = logging.getLogger(__name__)


class GrpcCachingTransactionExecutor(_BaseCachingExecutor):
    """Caching executor for gRPC transactions.

    Unlike the GraphQL caching executor, this implementation does not
    resolve unresolved object references or cache gas coins — the gRPC
    AsyncSuiTransaction handles its own gas selection internally.
    """

    def __init__(self, client, gas_owner: Optional[str] = None) -> None:
        super().__init__(gas_owner=gas_owner)
        self._client = client

    async def build_transaction(
        self,
        txn,
        signer_block: SignerBlock,
        default_gas_budget: int = 50_000_000,
    ) -> str:
        """Build the transaction and return a base64-encoded transaction string.

        :param txn: gRPC AsyncSuiTransaction to build
        :param signer_block: Signer block (unused; sender is baked into txn at creation)
        :param default_gas_budget: Gas budget to use if not already set
        :return: Base64-encoded serialized TransactionData
        :rtype: str
        """
        return await txn.build(gas_budget=default_gas_budget)
