#    Copyright Frank V. Castellucci
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#        http://www.apache.org/licenses/LICENSE-2.0
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

# -*- coding: utf-8 -*-

"""Sui BCS Conversions [EXPERIMENTAL]."""

import base64
from typing import Union


from pysui.sui.sui_types import bcs
from pysui.sui.sui_clients.common import PreExecutionResult, SuiRpcResult
from pysui.sui.sui_builders.exec_builders import (
    _MoveCallTransactionBuilder,
)

from pysui.sui.sui_clients.sync_client import SuiClient as SyncClient

_TKIND_INDEX: int = 1
_GAS_AND_BUDGET_BYTE_OFFSET: int = -155
FAKE_ADDRESS_OR_OBJECT: str = "0x0000000000000000000000000000000000000000000000000000000000000000"


# TODO: Move to SuiTransaction when ready


def get_txkind_from_tx_bytes(tx_bytes: str) -> bytes:
    """get_txkind_from_tx_bytes extracts the TransactionKind bytes from tx_bytes.

    :param tx_bytes: base64 transaction bytes string
    :type tx_bytes: str
    :return: Transaction Kind as bytes.
    :rtype: bytes
    """
    raw_bytes = base64.b64decode(tx_bytes)
    return raw_bytes[:_GAS_AND_BUDGET_BYTE_OFFSET][_TKIND_INDEX:]


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
        # raw_bytes = base64.b64decode(tx_result.tx_bytes)
        # raw_shredded = raw_bytes[:_GAS_AND_BUDGET_BYTE_OFFSET][_TKIND_INDEX:]
        return base64.b64encode(raw_shredded).decode()
    return indata


# TODO: Move to SuiTransaction when ready


def get_txkind_from_result(indata: SuiRpcResult) -> Union[bcs.TransactionKind, Exception]:
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
