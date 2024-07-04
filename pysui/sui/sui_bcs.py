#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Sui BCS Conversions [EXPERIMENTAL]."""

import base64
from typing import Union

from deprecated.sphinx import deprecated
from pysui.sui.sui_types import bcs
from pysui.sui.sui_clients.common import PreExecutionResult, SuiRpcResult

from pysui.sui.sui_clients.sync_client import SuiClient as SyncClient

_TKIND_INDEX: int = 1
_GAS_AND_BUDGET_BYTE_OFFSET: int = -155
FAKE_ADDRESS_OR_OBJECT: str = (
    "0x0000000000000000000000000000000000000000000000000000000000000000"
)


@deprecated(
    version="0.65.0", reason="Transition to pysui GraphQL SuiClients and QueryNodes"
)
def get_txkind_from_tx_bytes(tx_bytes: str) -> bytes:
    """get_txkind_from_tx_bytes extracts the TransactionKind bytes from tx_bytes.

    :param tx_bytes: base64 transaction bytes string
    :type tx_bytes: str
    :return: Transaction Kind as bytes.
    :rtype: bytes
    """
    raw_bytes = base64.b64decode(tx_bytes)
    return raw_bytes[:_GAS_AND_BUDGET_BYTE_OFFSET][_TKIND_INDEX:]


@deprecated(
    version="0.65.0", reason="Transition to pysui GraphQL SuiClients and QueryNodes"
)
def get_txkind_from_result_asb64(indata: SuiRpcResult) -> Union[str, SuiRpcResult]:
    """inspect_ready_txkind_from_result Return a serialized TransactionKind as base64 encoded string.

    Can be then used to submit to InspectTransaction

    :param indata: The result of calling a complex transaction prior to signing
    :type indata: SuiRpcResult
    :return: A base64 encoded serialized TransactionKind
    :rtype: str
    """
    if indata.is_ok():
        tx_result: PreExecutionResult = indata.result_data.pre_transaction_result
        raw_shredded = get_txkind_from_tx_bytes(tx_result.tx_bytes)
        return base64.b64encode(raw_shredded).decode()
    return indata


@deprecated(
    version="0.65.0", reason="Transition to pysui GraphQL SuiClients and QueryNodes"
)
def get_txkind_from_result(
    indata: SuiRpcResult,
) -> Union[bcs.TransactionKind, Exception]:
    """transaction_kind_from_rpcresult converts the transaction bytes into BCS TransactionKind struct.

    :param indata: The result of calling a complex transaction prior to signing
    :type indata: SuiRpcResult
    :raises ValueError: If the SuiRpcResult contains error
    :return: A TransactionKind structure represented in the SuiRpcResult base64 transaciton bytes
    :rtype: Union[bcs.TransactionKind, Exception]
    """
    if indata.is_ok():
        tx_result: PreExecutionResult = indata.result_data.pre_transaction_result
        raw_bytes = base64.b64decode(tx_result.tx_bytes)
        raw_shredded = raw_bytes[:_GAS_AND_BUDGET_BYTE_OFFSET][_TKIND_INDEX:]
        return bcs.TransactionKind.deserialize(raw_shredded)

    else:
        raise ValueError(f"RPC result is invalid {indata.result_string}")


if __name__ == "__main__":
    pass
