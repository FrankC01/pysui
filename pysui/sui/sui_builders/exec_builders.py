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
# pylint: disable=too-many-instance-attributes

"""Sui Builders: Complex transaction."""

from abc import abstractmethod
from typing import Final, Optional
from deprecated.sphinx import deprecated
from pysui.abstracts.client_types import SuiBaseType
from pysui.sui.sui_builders.base_builder import (
    _NativeTransactionBuilder,
    SuiRequestType,
    SuiBaseBuilder,
    SuiTransactionBuilderMode,
    sui_builder,
)
from pysui.sui.sui_types.scalars import (
    SuiNullType,
    SuiTxBytes,
    SuiSignature,
    ObjectID,
    SuiString,
)
from pysui.sui.sui_types.collections import SuiArray, SuiMap
from pysui.sui.sui_types.address import SuiAddress
from pysui.sui.sui_txresults.complex_tx import (
    DryRunTxResult,
    TransactionBytes,
    TxResponse,
    TxInspectionResult,
)

from pysui.sui import sui_utils


class ExecuteTransaction(_NativeTransactionBuilder):
    """Submit a signed transaction to Sui."""

    _DEFAULT_EXECUTE_TX_OPTIONS: Final[dict] = {
        "showBalanceChanges": True,
        "showEffects": True,
        "showEvents": True,
        "showInput": True,
        "showObjectChanges": True,
        "showRawInput": True,
    }

    @sui_builder()
    def __init__(
        self,
        *,
        tx_bytes: SuiTxBytes,
        signatures: SuiArray,
        options: Optional[SuiMap] = None,
        request_type: SuiRequestType,
    ) -> None:
        """__init__ Initialize builder.

        :param tx_bytes: BCS serialized transaction data bytes without its type tag, as base-64 encoded string
        :type tx_bytes: SuiTxBytes
        :param signatures: Array of `flag || signature || pubkey` bytes, as base-64 encoded string,
            signatures are committed to the intent message of the transaction data,
            as base-64 encoded string wrapped in SuiSignatures.
        :type signatures: SuiArray[SuiSignature]
        :param request_type: The request type
        :type request_type: SuiRequestType
        """
        super().__init__(
            "sui_executeTransactionBlock",
            handler_cls=TxResponse,
            handler_func="from_dict",
        )
        if options is None or isinstance(options, SuiNullType):
            self.options = sui_utils.as_sui_map(
                self._DEFAULT_EXECUTE_TX_OPTIONS.copy()
            )
        else:
            self.options = sui_utils.as_sui_map(options)


class DryRunTransaction(_NativeTransactionBuilder):
    """Dry run a signed transaction to Sui."""

    @sui_builder()
    def __init__(
        self,
        *,
        tx_bytes: SuiTxBytes,
    ) -> None:
        """Initialize builder."""
        super().__init__(
            "sui_dryRunTransactionBlock",
            handler_cls=DryRunTxResult,
            handler_func="from_dict",
        )


class InspectTransaction(_NativeTransactionBuilder):
    """InspectTransaction when executed, return dev-inpsect results of the transaction.

    Includes both the transaction effects and return values of the transaction.
    """

    @sui_builder()
    def __init__(
        self,
        *,
        sender_address: SuiAddress,
        tx_bytes: SuiString,
        gas_price: Optional[SuiString] = None,
        epoch: Optional[SuiString] = None,
    ) -> None:
        """__init__ Initialize builder.

        :param sender_address: The sender/signer of transaction bytes
        :type tx_bytes: SuiAddress
        :param tx_bytes: BCS serialize base64 encoded string of TransactionKind
        :type tx_bytes: SuiString
        :param gas_price: Gas is not charged, but gas usage is still calculated. Default to use reference gas price
        :type gas_price: Optional[SuiString]
        :param epoch: The epoch to perform the call. Will be set from the system state object if not provided
        :type epoch: Optional[SuiString]
        """
        super().__init__(
            "sui_devInspectTransactionBlock",
            handler_cls=TxInspectionResult,
            handler_func="factory",
        )


class _MoveCallTransactionBuilder(SuiBaseBuilder):
    """Builders that must be processed, signed then executed."""

    def __init__(self, method: str) -> None:
        """Initialize builder."""
        super().__init__(
            method,
            True,
            handler_cls=TransactionBytes,
            handler_func="from_dict",
        )

    @property
    def authority(self) -> SuiAddress:
        """Fetch the authority."""
        if hasattr(self, "signer"):
            return getattr(self, "signer")
        if hasattr(self, "signers"):
            return getattr(self, "signers")
        if hasattr(self, "sender"):
            return getattr(self, "sender")
        if hasattr(self, "sender_address"):
            return getattr(self, "sender_address")
        raise ValueError(
            f"Object {self.__class__.__name__} has no authority property set"
        )
