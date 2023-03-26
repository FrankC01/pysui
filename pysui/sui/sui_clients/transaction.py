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

"""Sui high level Transaction Builder supports generation of TransactionKind and TransactionData."""

import base64
from typing import Optional, Union
import pysui.sui.sui_clients.transaction_builder as tx_builder
from pysui.sui.sui_txresults.single_tx import ObjectRead, SuiCoinObject
from pysui.sui.sui_types import bcs
from pysui.sui.sui_types.address import SuiAddress
from pysui.sui.sui_clients.sync_client import SuiClient
from pysui.sui.sui_types.scalars import ObjectID, SuiInteger


class SuiTransaction:
    """High level transaction builder."""

    def __init__(self, client: SuiClient, sender: SuiAddress = None) -> None:
        """Transaction initializer."""
        self.builder = tx_builder.ProgrammableTransactionBuilder()
        self.client = client
        self._gasses: list[SuiCoinObject] = []
        self._set_sender(sender)

    def _set_sender(self, sender: SuiAddress = None) -> None:
        """_set_sender Change the active sender and gas objects.

        If sender is None, sets sender to the current active address
        :param sender: A SuiAddress to set as current, defaults to None
        :type sender: SuiAddress, optional
        :raises ValueError: If sender provided but not class SuiAddress
        """
        if sender:
            if isinstance(sender, SuiAddress):
                self.sender = sender
            else:
                raise ValueError(f"Expected class SuiAddress for sender, found {sender.__class__.__name__}")
        else:
            self.sender = self.client.config.active_address
        self._gasses.clear()
        result = self.client.get_gas(self.sender)
        if result.is_ok():
            for coin_object in result.result_data.data:
                setattr(coin_object, "owner", self.sender.address)
                self._gasses.append(coin_object)

    @property
    def gasses(self) -> list:
        """."""
        return self._gasses

    def set_sender(self, sender: SuiAddress) -> None:
        """Set the Transaction Sender."""
        self._set_sender(sender)

    def raw_kind(self) -> bcs.TransactionKind:
        """."""
        return self.builder.finish_for_inspect()

    def build_for_inspection(self) -> str:
        """build_for_inspection returns a base64 string that can be used in inspecting transaction.

        :return: base64 string representation of underlying TransactionKind
        :rtype: str
        """
        return base64.b64encode(self.raw_kind().serialize()).decode()

    def final(self) -> str:
        """final returns a base64 string that can be used to sign and execute a transaction.

        :return: base64 string representation of TransactionData
        :rtype: str
        """
        _tx_kind: bcs.TransactionKind = self.raw_kind()
        raise NotImplementedError("final")

    def transfer_object(
        self, *, transfer: Union[str, ObjectID, ObjectRead], recipient: Union[ObjectID, SuiAddress]
    ) -> bcs.Argument:
        """."""
        assert isinstance(transfer, (str, ObjectID, ObjectRead)), "invalid object id type"
        assert isinstance(recipient, (ObjectID, SuiAddress)), "invalid recipient type"
        if not isinstance(transfer, ObjectRead):
            result = self.client.get_object(transfer)
            if result.is_ok():
                transfer = result.result_data
            else:
                raise ValueError(f"Fetching object {transfer.object_id} failed")
        transfer_ref = (
            bcs.BuilderArg("Object", bcs.Address.from_str(transfer.object_id)),
            bcs.ObjectArg("ImmOrOwnedObject", bcs.ObjectReference.from_generic_ref(transfer)),
        )
        return self.builder.transfer_object(tx_builder.PureInput.as_input(recipient), transfer_ref)

    def transfer_sui(
        self, *, recipient: Union[ObjectID, SuiAddress], amount: Optional[Union[int, SuiInteger]] = None
    ) -> bcs.Argument:
        """."""
        assert isinstance(recipient, (ObjectID, SuiAddress)), "invalid recipient type"
        if amount:
            assert isinstance(amount, (int, SuiInteger))
            amount = amount if isinstance(amount, int) else amount.value
            amount = tx_builder.PureInput.as_input(bcs.U64.encode(amount))
        return self.builder.transfer_sui(tx_builder.PureInput.as_input(recipient), amount)

    def split_coin(self, *, coin: Union[str, ObjectID, ObjectRead], amount: Union[int, SuiInteger]) -> bcs.Argument:
        """."""
        assert isinstance(coin, (str, ObjectID, ObjectRead)), "invalid coin object type"
        assert isinstance(amount, (int, SuiInteger)), "invalid amount type"
        amount = amount if isinstance(amount, int) else amount.value
        if not isinstance(coin, ObjectRead):
            result = self.client.get_object(coin)
            if result.is_ok():
                coin = result.result_data
            else:
                raise ValueError(f"Fetching object {coin.object_id} failed")
        coin_ref = (
            bcs.BuilderArg("Object", bcs.Address.from_str(coin.object_id)),
            bcs.ObjectArg("ImmOrOwnedObject", bcs.ObjectReference.from_generic_ref(coin)),
        )
        return self.builder.split_coin(coin_ref, tx_builder.PureInput.as_input(bcs.U64.encode(amount)))

    def pay_all_sui(self, *, recipient: Union[ObjectID, SuiAddress]) -> bcs.Argument:
        """."""
        assert isinstance(recipient, (ObjectID, SuiAddress)), "invalid recipient type"
        return self.builder.pay_all_sui(tx_builder.PureInput.as_input(recipient))
