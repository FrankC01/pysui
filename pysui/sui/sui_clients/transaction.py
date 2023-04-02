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
from pysui.sui.sui_builders.exec_builders import InspectTransaction
from pysui.sui.sui_builders.get_builders import GetReferenceGasPrice
from pysui.sui.sui_clients.common import SuiRpcResult
import pysui.sui.sui_clients.transaction_builder as tx_builder
from pysui.sui.sui_txresults.complex_tx import TxInspectionResult
from pysui.sui.sui_txresults.single_tx import ObjectRead, SuiCoinObject
from pysui.sui.sui_types import bcs
from pysui.sui.sui_types.address import SuiAddress
from pysui.sui.sui_clients.sync_client import SuiClient
from pysui.sui.sui_types.collections import SuiArray
from pysui.sui.sui_types.scalars import ObjectID, SuiInteger, SuiTxBytes


class SuiTransaction:
    """High level transaction builder."""

    def __init__(self, client: SuiClient, sender: Union[str, SuiAddress] = None) -> None:
        """Transaction initializer."""
        self.builder = tx_builder.ProgrammableTransactionBuilder()
        self.client = client
        self._sender: str = ""
        self._set_sender(sender)
        self._gasses: list[SuiCoinObject] = self._reset_gas(self._sender)
        self._current_gas_price = self._gas_price()

    def _set_sender(self, sender: Union[str, SuiAddress]) -> bool:
        """_set_sender Change the active sender and gas objects.

        If sender is None, sets sender to the current active address
        :param sender: A SuiAddress to set as current, defaults to None
        :type sender: SuiAddress, optional
        """
        if sender:
            sender = sender if isinstance(sender, str) else sender.address
            if sender != self._sender:
                self._sender = sender
                return True
        else:
            self._sender = self.client.config.active_address.address
            return True
        return False

    def _reset_gas(self, for_owner: str) -> list:
        """_reset_gas Returns gas objects imbued with owners."""
        result = self.client.get_gas(for_owner)
        out_list = []
        if result.is_ok():
            for coin_object in result.result_data.data:
                setattr(coin_object, "owner", for_owner)
                out_list.append(coin_object)
        return out_list

    def _gas_price(self) -> int:
        """."""
        result = self.client.execute(GetReferenceGasPrice())
        if result.is_ok():
            return int(result.result_data)
        raise ValueError(f"Failed calling host for gas price {result.result_string}")

    @property
    def gas_price(self) -> int:
        """."""
        return self._current_gas_price

    @property
    def gasses(self) -> list:
        """Returns the list of gas (coin objects) of current sender."""
        return self._gasses

    def set_sender(self, sender: Union[str, SuiAddress]) -> None:
        """Set the Transaction Sender."""
        if self._set_sender(sender):
            self._gasses = self._reset_gas(self._sender)

    def raw_kind(self) -> bcs.TransactionKind:
        """."""
        return self.builder.finish_for_inspect()

    def build_for_inspection(self) -> str:
        """build_for_inspection returns a base64 string that can be used in inspecting transaction.

        :return: base64 string representation of underlying TransactionKind
        :rtype: str
        """
        return base64.b64encode(self.raw_kind().serialize()).decode()

    def inspect_all(self, for_sender: Union[str, SuiAddress] = None) -> Union[TxInspectionResult, None]:
        """inspect_all Returns results of InspectTransaction on the current Transaction.

        :param for_sender: Use for inspection. If not supplied, uses current Transaction sender, defaults to None
        :type for_sender: Union[str, SuiAddress], optional
        :return: The successful result or None if inspect transaction failed.
        :rtype: Union[TxInspectionResult, None]
        """
        tx_bytes = self.build_for_inspection()
        if for_sender:
            for_sender = for_sender if isinstance(for_sender, str) else for_sender.address
        else:
            for_sender = self._sender
        result = self.client.execute(InspectTransaction(sender_address=for_sender, tx_bytes=tx_bytes))
        if result.is_ok():
            return result.result_data
        return None

    def inspect_for_cost(self, for_sender: Union[str, SuiAddress] = None) -> Union[tuple[int, int, str], None]:
        """inspect_for_cost Runs inspect transaction for cost summary.

        :param for_sender: Use for inspection. If not supplied, uses current Transaction sender, defaults to None
        :type for_sender: Union[str, SuiAddress], optional
        :return: If inspect did not fail, a tuple of gas_max, gas_min, gas object_id otherwise None
        :rtype: Union[tuple[int, int, str], None]
        """
        ispec = self.inspect_all(for_sender)
        if ispec:
            gas_used = ispec.effects.gas_used
            gas_max = gas_used.total
            gas_min = gas_used.total_after_rebate
            return gas_max, gas_min, ispec.effects.gas_object.reference.object_id
        return None

    def final(self) -> str:
        """final returns a base64 string that can be used to sign and execute a transaction.

        :return: base64 string representation of TransactionData
        :rtype: str
        """
        _tx_kind: bcs.TransactionKind = self.raw_kind()
        raise NotImplementedError("final")

    #    signer: SuiAddress,
    #     object_id: ObjectID,
    #     gas: Option<ObjectID>,
    #     gas_budget: u64,
    #     recipient: SuiAddress,

    def _gas_for_budget(self, owner: str, budget: int) -> SuiCoinObject:
        """."""
        if owner == self._sender:
            for gobj in self._gasses:
                if gobj.balance > budget:
                    return gobj
        else:
            coin_objs = self._reset_gas(owner)
            for gobj in coin_objs:
                if gobj.balance > budget:
                    return gobj
        return None

    def execute(
        self,
        *,
        signer: Union[str, SuiAddress],
        gas: Optional[Union[str, ObjectID]] = None,
        gas_budget: Union[int, SuiInteger],
    ) -> SuiRpcResult:
        """."""
        # Get the transaction body
        tx_kind = self.raw_kind()
        # We already have gas price
        # Manage the signer and if it is our own
        signer = signer if signer else self._sender
        signer = signer if isinstance(signer, str) else signer.address
        max_cost, _, _ = self.inspect_for_cost(signer)

        gas_budget = gas_budget if isinstance(gas_budget, int) else gas_budget.value
        if gas_budget < max_cost:
            gas_budget = max_cost
        if signer == self._sender:
            if not gas:
                gas: SuiCoinObject = self._gas_for_budget(signer, gas_budget)
            else:
                for gasobj in self._gasses:
                    if gasobj.balance > gas_budget:
                        gas: SuiCoinObject = gasobj
                        break
        else:
            gas: SuiCoinObject = self._gas_for_budget(signer, gas_budget)
        gas_object = bcs.GasData(
            [
                bcs.ObjectReference(
                    bcs.Address.from_str(gas.coin_object_id), gas.version, bcs.Digest.from_str(gas.digest)
                )
            ],
            bcs.Address.from_str(gas.owner),
            self._current_gas_price,
            gas_budget,
        )
        # If budget not provided, get high end cost
        tx_data = bcs.TransactionData(
            "V1",
            bcs.TransactionDataV1(tx_kind, bcs.Address.from_str(signer), gas_object, bcs.TransactionExpiration("None")),
        )
        tx_b64 = base64.b64encode(tx_data.serialize()).decode()
        iresult = self.client.sign_and_submit(SuiAddress(signer), SuiTxBytes(tx_b64), SuiArray([]))
        return iresult

    # Commands

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
