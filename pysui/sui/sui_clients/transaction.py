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
from pysui.sui.sui_txresults.common import GenericRef
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
        """Retrieve the current gas price from the chain during initialization."""
        result = self.client.execute(GetReferenceGasPrice())
        if result.is_ok():
            return int(result.result_data)
        raise ValueError(f"Failed calling chain for gas price {result.result_string}")

    @property
    def gas_price(self) -> int:
        """Returns the current gas price for the chain."""
        return self._current_gas_price

    @property
    def gasses(self) -> list:
        """Returns the list of gas (coin objects) of current sender."""
        return self._gasses

    def set_sender(self, sender: Union[str, SuiAddress]) -> None:
        """Set the Transaction Sender.

        This will also reset the coin object list if the sender is different from current sender
        """
        if self._set_sender(sender):
            self._gasses = self._reset_gas(self._sender)

    def raw_kind(self) -> bcs.TransactionKind:
        """Returns the TransactionKind object hierarchy of inputs, returns and commands.

        This is useful for reviewing the transaction that will be executed or inspected.
        """
        return self.builder.finish_for_inspect()

    def build_for_inspection(self) -> str:
        """build_for_inspection returns a base64 string that can be used in inspecting transaction.

        :return: base64 string representation of underlying TransactionKind
        :rtype: str
        """
        return base64.b64encode(self.raw_kind().serialize()).decode()

    def inspect_all(self, for_sender: Union[str, SuiAddress] = None) -> Union[TxInspectionResult, None]:
        """inspect_all Returns results of sui_devInspectTransactionBlock on the current Transaction.

        :param for_sender: Used for inspection. If not supplied, uses current Transaction sender, defaults to None
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

    # FIXME: Not complete, used for testing WIP
    def _gas_for_budget(self, owner: str, budget: int) -> SuiCoinObject:
        """Used internally to select a gas object to use in transaction."""
        if owner == self._sender:
            for gobj in self._gasses:
                if gobj.balance > budget and gobj.coin_object_id not in self.builder.objects_registry:
                    return gobj
        else:
            coin_objs = self._reset_gas(owner)
            for gobj in coin_objs:
                if gobj.balance > budget and gobj.coin_object_id not in self.builder.objects_registry:
                    return gobj
        return None

    #    signer: SuiAddress,
    #     object_id: ObjectID,
    #     gas: Option<ObjectID>,
    #     gas_budget: u64,
    #     recipient: SuiAddress,

    def build_for_execute(
        self,
        *,
        signer: Union[str, SuiAddress],
        gas: Optional[Union[str, ObjectID]] = None,
        gas_budget: Union[int, SuiInteger],
    ) -> tuple[str, SuiCoinObject, bcs.TransactionData]:
        """build_for_execute Generates the TransactionData object.

        Note: If wanting to execute, this structure needs to be serialized to a base64 string. See
        the execute method below

        :param signer: The signer of transaction address
        :type signer: Union[str, SuiAddress]
        :param gas_budget: The gas budget to use. An introspection of the transaciton is performed and
        and this method will use the larger of the two.
        :type gas_budget: Union[int, SuiInteger]
        :param gas: An gas coin object id. If not provided, one of the signers gas object sill be used, defaults to None
        :type gas: Optional[Union[str, ObjectID]], optional
        :return: A tuple containing the resolved sender address, the resolved gas coin object and
        the TransactionData object replete with all required fields for execution
        :rtype: tuple[str, SuiCoinObject, bcs.TransactionData]
        """
        # Get the transaction body
        tx_kind = self.raw_kind()
        # We already have gas price
        # Manage the signer and if it is our own
        signer = signer if signer else self._sender
        signer = signer if isinstance(signer, str) else signer.address
        max_cost, _, _ = self.inspect_for_cost(signer)

        gas_budget = gas_budget if isinstance(gas_budget, int) else gas_budget.value
        gas_budget = max(max_cost, gas_budget)
        # FIXME Clean this up
        if signer == self._sender:
            if not gas:
                gas: SuiCoinObject = self._gas_for_budget(signer, gas_budget)
            else:
                for gasobj in self._gasses:
                    if gasobj.balance > gas_budget and gasobj.coin_object_id not in self.builder.objects_registry:
                        gas: SuiCoinObject = gasobj
                        break
        else:
            gas: SuiCoinObject = self._gas_for_budget(signer, gas_budget)
        assert gas
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
        return (
            signer,
            gas,
            bcs.TransactionData(
                "V1",
                bcs.TransactionDataV1(
                    tx_kind, bcs.Address.from_str(signer), gas_object, bcs.TransactionExpiration("None")
                ),
            ),
        )

    def execute(
        self,
        *,
        signer: Union[str, SuiAddress],
        gas: Optional[Union[str, ObjectID]] = None,
        gas_budget: Union[int, SuiInteger],
    ) -> SuiRpcResult:
        """execute Finalizes transaction and submits for execution on the chain.

        :param signer: The signer of transaction address
        :type signer: Union[str, SuiAddress]
        :param gas_budget: The gas budget to use. An introspection of the transaciton is performed and
        and this method will use the larger of the two.
        :type gas_budget: Union[int, SuiInteger]
        :param gas: An gas coin object id. If not provided, one of the signers gas object sill be used, defaults to None
        :type gas: Optional[Union[str, ObjectID]], optional
        :return: The result of signing and executing the transaction
        :rtype: SuiRpcResult
        """
        signer, _, tx_data = self.build_for_execute(signer=signer, gas=gas, gas_budget=gas_budget)
        tx_b64 = base64.b64encode(tx_data.serialize()).decode()
        iresult = self.client.sign_and_submit(SuiAddress(signer), SuiTxBytes(tx_b64), SuiArray([]))
        return iresult

    # TODO: Add method for MultiSig signing and execution

    # Commands

    def _resolve_reference(
        self, item: Union[str, ObjectID, ObjectRead, SuiCoinObject, bcs.Argument]
    ) -> Union[bcs.Argument, tuple[bcs.BuilderArg, bcs.ObjectArg]]:
        """."""
        assert item, "None type found for item"
        assert isinstance(item, (str, ObjectID, ObjectRead, SuiCoinObject, bcs.Argument)), "Type not valid for item"
        # bcs.Arguments fall through as it is ready to go
        match item.__class__.__name__:
            # Resolve the object on chain then convert to a tuple BuilderArg,ObjectArg
            case "str" | "ObjectID":
                result = self.client.get_object(item)
                item = item if isinstance(item, str) else item.value
                if result.is_ok():
                    obj_data = result.result_data
                    obj_ref = GenericRef(obj_data.object_id, obj_data.version, obj_data.digest)
                    item = (
                        bcs.BuilderArg("Object", bcs.Address.from_str(obj_data.object_id)),
                        bcs.ObjectArg("ImmOrOwnedObject", bcs.ObjectReference.from_generic_ref(obj_ref)),
                    )
                else:
                    raise ValueError(f"Error attempting to get {item} from chain")
            # convert to a tuple BuilderArg,ObjectArg
            case "ObjectRead" | "SuiCoinObject":
                obj_ref = GenericRef(item.object_id, item.version, item.digest)
                item = (
                    bcs.BuilderArg("Object", bcs.Address.from_str(item.object_id)),
                    bcs.ObjectArg("ImmOrOwnedObject", bcs.ObjectReference.from_generic_ref(obj_ref)),
                )
        return item

    def _resolve_references(
        self, items: list[Union[str, ObjectID, ObjectRead, SuiCoinObject, bcs.Argument]]
    ) -> list[bcs.Argument]:
        """."""
        return [self._resolve_reference(x) for x in items]

    def split_coin(self, *, coin: Union[str, ObjectID, ObjectRead], amount: Union[int, SuiInteger]) -> bcs.Argument:
        """split_coin Creates a split coin command.

        Note: In execution, at some point in the transaction commands, you must transfer the result
        otherwise, upon inspection or execution, you will get and error similar to this:
        "UnusedValueWithoutDrop { result_idx: 0, secondary_idx: 0 }

        :param coin: The coin address (object id) to split from.
        :type coin: Union[str, ObjectID, ObjectRead]
        :param amount: The amount to split out from coin
        :type amount: Union[int, SuiInteger]
        :raises ValueError: if the coin object can not be found on the chain.
        :return: The command result that can be used in subsequent commands.
        :rtype: bcs.Argument
        """
        assert isinstance(coin, (str, ObjectID, ObjectRead)), "invalid coin object type"
        assert isinstance(amount, (int, SuiInteger)), "invalid amount type"
        amount = amount if isinstance(amount, int) else amount.value
        if not isinstance(coin, ObjectRead):
            result = self.client.get_object(coin)
            if result.is_ok():
                coin = result.result_data
                coin = GenericRef(coin.object_id, coin.version, coin.digest)
            else:
                raise ValueError(f"Fetching object {coin.object_id} failed")
        coin_ref = (
            bcs.BuilderArg("Object", bcs.Address.from_str(coin.object_id)),
            bcs.ObjectArg("ImmOrOwnedObject", bcs.ObjectReference.from_generic_ref(coin)),
        )
        return self.builder.split_coin(coin_ref, tx_builder.PureInput.as_input(bcs.U64.encode(amount)))

    def merge_coins(
        self,
        *,
        merge_to: Union[str, ObjectID, ObjectRead, SuiCoinObject, bcs.Argument],
        merge_from: Union[list[Union[str, ObjectID, ObjectRead, SuiCoinObject, bcs.Argument]], SuiArray],
    ):
        """."""
        assert isinstance(
            merge_to, (str, ObjectID, ObjectRead, SuiCoinObject, bcs.Argument)
        ), "Unsupported type for merge_to"
        assert isinstance(merge_from, (list, SuiArray)), "Unsupported merge_from collection type"
        # Depper from_coin type verification
        merge_from = merge_from if isinstance(merge_from, list) else merge_from.coins
        for fcoin in merge_from:
            assert isinstance(
                fcoin, (str, ObjectID, ObjectRead, SuiCoinObject, bcs.Argument)
            ), "Unsupported entry in merge_from"
        merge_to = self._resolve_reference(merge_to)
        merge_from = self._resolve_references(merge_from)
        return self.builder.merge_coins(merge_to, merge_from)

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
        self,
        *,
        recipient: Union[ObjectID, SuiAddress],
        from_coin: Union[str, ObjectID, ObjectRead, SuiCoinObject] = None,
        amount: Optional[Union[int, SuiInteger]] = None,
    ) -> bcs.Argument:
        """."""
        assert isinstance(recipient, (ObjectID, SuiAddress)), "invalid recipient type"
        if amount:
            assert isinstance(amount, (int, SuiInteger))
            amount = amount if isinstance(amount, int) else amount.value
            amount = tx_builder.PureInput.as_input(bcs.U64.encode(amount))
        if from_coin:
            if not isinstance(from_coin, ObjectRead) and not isinstance(from_coin, SuiCoinObject):
                result = self.client.get_object(from_coin)
                if result.is_ok():
                    from_coin = result.result_data
                else:
                    raise ValueError(f"Fetching object {from_coin.object_id} failed")
            elif isinstance(from_coin, SuiCoinObject):
                from_coin = GenericRef(from_coin.object_id, from_coin.version, from_coin.digest)
            from_coin_ref = (
                bcs.BuilderArg("Object", bcs.Address.from_str(from_coin.object_id)),
                bcs.ObjectArg("ImmOrOwnedObject", bcs.ObjectReference.from_generic_ref(from_coin)),
            )
        else:
            from_coin_ref = bcs.Argument("GasCoin")
        return self.builder.transfer_sui(tx_builder.PureInput.as_input(recipient), from_coin_ref, amount)

    def pay_all_sui(self, *, recipient: Union[ObjectID, SuiAddress]) -> bcs.Argument:
        """."""
        assert isinstance(recipient, (ObjectID, SuiAddress)), "invalid recipient type"
        return self.builder.pay_all_sui(tx_builder.PureInput.as_input(recipient))
