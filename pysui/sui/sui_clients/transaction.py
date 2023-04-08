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
from typing import Any, Optional, Union
from pysui.sui.sui_builders.exec_builders import InspectTransaction
from pysui.sui.sui_builders.get_builders import GetReferenceGasPrice, GetMultipleObjects
from pysui.sui.sui_clients.common import SuiRpcResult
import pysui.sui.sui_clients.transaction_builder as tx_builder
from pysui.sui.sui_txresults.common import GenericRef
from pysui.sui.sui_txresults.complex_tx import TxInspectionResult
from pysui.sui.sui_txresults.single_tx import AddressOwner, ObjectRead, SharedOwner, StakedSui, SuiCoinObject
from pysui.sui.sui_types import bcs
from pysui.sui.sui_types.address import SuiAddress
from pysui.sui.sui_clients.sync_client import SuiClient
from pysui.sui.sui_types.collections import SuiArray
from pysui.sui.sui_types.scalars import ObjectID, SuiInteger, SuiIntegerType, SuiString, SuiTxBytes, SuiU64

_SYSTEMSTATE_OBJECT: ObjectID = ObjectID("0x5")
_STAKE_REQUEST_TARGET: str = "0x3::sui_system::request_add_stake_mul_coin"
_UNSTAKE_REQUEST_TARGET: str = "0x3::sui_system::request_withdraw_stake"


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
        :param gas_budget: The gas budget to use. An introspection of the transaciton is performed
            and this method will use the larger of the two.
        :type gas_budget: Union[int, SuiInteger]
        :param gas: An gas coin object id. If not provided, one of the signers gas object will be used, defaults to None
        :type gas: Optional[Union[str, ObjectID]], optional
        :return: The result of signing and executing the transaction
        :rtype: SuiRpcResult
        """
        signer, _, tx_data = self.build_for_execute(signer=signer, gas=gas, gas_budget=gas_budget)
        tx_b64 = base64.b64encode(tx_data.serialize()).decode()
        iresult = self.client.sign_and_submit(SuiAddress(signer), SuiTxBytes(tx_b64), SuiArray([]))
        return iresult

    # TODO: Add method for MultiSig signing and execution

    # Commands and helpers
    # TODO: Remove the asserts at some point
    # TODO: This is way too much code, refactor when stable

    def _resolve_reference(
        self, item: Union[str, ObjectID, ObjectRead, SuiCoinObject, bcs.Argument]
    ) -> Union[bcs.Argument, tuple[bcs.BuilderArg, bcs.ObjectArg]]:
        """Resolve an input item to either a pure Argument type or an object reference tuple."""
        assert item, "None type found for item"
        assert isinstance(item, (str, ObjectID, ObjectRead, SuiCoinObject, bcs.Argument)), "Type not valid for item"
        # bcs.Arguments fall through as it is ready to go
        match item.__class__.__name__:
            # Resolve the object on chain then convert to a tuple BuilderArg,ObjectArg
            # FIXME: Not handling shared objects yet
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
            # FIXME: Not handling shared objects yet
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
        """Resolve a list of items to it's respect pure or object reference tuples."""
        return [self._resolve_reference(x) for x in items]

    def _resolve_arguments(self, items: list) -> list:
        """Process list intended as 'params' in move call."""
        objref_indexes: list[int] = []
        objtup_indexes: list[int] = []
        # Separate the index based on conversion types
        for index, item in enumerate(items):
            clz_name = item.__class__.__name__
            # TODO: Can simplify with sets
            match clz_name:
                # Pure conversion Types
                case "SuiU8" | "SuiU16" | "SuiU32" | "SuiU64" | "SuiU128" | "SuiU256":
                    items[index] = tx_builder.PureInput.as_input(items[index].to_bytes())
                # Pure conversion Types
                case "int" | "SuiInteger" | "str" | "SuiString" | "SuiAddress":
                    items[index] = tx_builder.PureInput.as_input(items[index])
                case "OptionalU64":
                    items[index] = tx_builder.PureInput.as_input(items[index])
                # Need to get objects to generics
                case "ObjectID":
                    objref_indexes.append(index)
                # Need to extract generics
                case "ObjectRead" | "SuiCoinObject":
                    objtup_indexes.append(index)
                # Direct passthroughs
                case "Argument" | "BuilderArg" | "tuple":
                    pass
                case _:
                    raise ValueError(f"Uknown class type handler {clz_name}")
        # Result object ID to tuple candidate
        if objref_indexes:
            res = self.client.execute(GetMultipleObjects(object_ids=[items[x] for x in objref_indexes]))
            if res.is_ok():
                res_list = res.result_data
                if len(res_list) != len(objref_indexes):
                    raise ValueError(f"Unable to find object in set {[items[x] for x in objref_indexes]}")
                # Update items list and register tuple conversion
                for index, result in enumerate(res_list):
                    items[objref_indexes[index]] = result
                    objtup_indexes.append(objref_indexes[index])
            else:
                raise ValueError(f"{res.result_string}")
        # Convert tuple candidates to tuples
        if objtup_indexes:
            for tindex in objtup_indexes:
                item: ObjectRead = items[tindex]
                if isinstance(item.owner, AddressOwner):
                    obj_ref = GenericRef(item.object_id, item.version, item.digest)
                    b_obj_arg = bcs.ObjectArg("ImmOrOwnedObject", bcs.ObjectReference.from_generic_ref(obj_ref))
                elif isinstance(item.owner, SharedOwner):
                    b_obj_arg = bcs.ObjectArg("SharedObject", bcs.SharedObjectReference.from_object_read(item))

                # FIXME: Not handling shared objects yet
                items[tindex] = (
                    bcs.BuilderArg("Object", bcs.Address.from_str(item.object_id)),
                    b_obj_arg,
                )

        return items

    def make_move_vector(self, items: list[Any]) -> bcs.Argument:
        """Create a call to convert a list of items to a Sui 'vector' type."""
        # Sample first for type
        def _first_non_argument_type(inner_list: list) -> Any:
            """."""
            result = None
            for inner_item in inner_list:
                if not isinstance(inner_item, bcs.Argument):
                    result = inner_item
                    break
            return result

        type_tag = bcs.OptionalTypeTag()
        if items:
            first_item = _first_non_argument_type(items)
            if first_item:
                # If not all arguments, ensure the remaining are consistent
                first_class = first_item.__class__.__name__
                for item in items:
                    item_class = item.__class__.__name__
                    if item_class == "Argument":
                        pass
                    else:
                        assert item_class == first_class, f"Expected {first_class} found {item_class}"
                match first_class:
                    case "int":
                        suit = SuiIntegerType.to_best_fit_integer_type(first_item)
                        type_tag = bcs.OptionalTypeTag(bcs.TypeTag(suit.type_tag_name))
                    case "str":
                        type_tag = bcs.OptionalTypeTag(bcs.TypeTag.type_tag_from("u8"))
                    case "SuiAddress":
                        type_tag = bcs.OptionalTypeTag(bcs.TypeTag("Address"))
                    # type_tag = bcs.OptionalTypeTag(bcs.TypeTag.type_tag_from(first_item.address))
                    case _:
                        pass
            return self.builder.make_move_vector(type_tag, self._resolve_arguments(items))
        raise ValueError("make_vector requires a non-empty list")

    def move_call(
        self,
        *,
        target: Union[str, SuiString, ObjectID],
        arguments: Union[list, SuiArray],
        type_arguments: Optional[Union[list, SuiArray]] = None,
        module: Optional[Union[str, SuiString]] = None,
        function: Optional[Union[str, SuiString]] = None,
        skip_arg_resolve: Optional[bool] = False,
    ) -> bcs.Argument:
        """move_call Creates a command to invoke a move contract call. May or may not return results.

        :param target: Target move call signature.
            Can be just the package id or in str form 'package_id::module::function'.
        :type target: Union[str, SuiString, ObjectID]
        :param arguments: Parameters that are passed to the move function
        :type arguments: Union[list, SuiArray]
        :param type_arguments: Optional list of type arguments for move function generics, defaults to None
        :type type_arguments: Optional[Union[list, SuiArray]], optional
        :param module: Module name, defaults to None.
            If not used, target is expected to be in form 'package_id::module::function'.
        :type module: Optional[Union[str, SuiString]], optional
        :param function: Function name, defaults to None
            If not used, target is expected to be in form 'package_id::module::function'.
        :type function: Optional[Union[str, SuiString]], optional
        :param skip_arg_resolve: Used internally, defaults to False
        :type skip_arg_resolve: Optional[bool], optional
        :raises ValueError: If ommitting module and function but target is not compound.
        :return: The result which may or may not be used in subequent commands depending on the
            move method being called.
        :rtype: bcs.Argument
        """
        target_id = None
        module_id = None
        function_id = None
        # Standardize the input parameters
        if isinstance(target, ObjectID) and (module is None or function is None):
            raise ValueError("If target is only ObjectID, you must fill in both 'module' and 'function' fields")
        if isinstance(target, (str, SuiString)):
            target = target if isinstance(target, str) else target.value
            target_id, module_id, function_id = target.split("::")
            target_id = bcs.Address.from_str(target_id)
        elif isinstance(target, ObjectID):
            target_id = target_id = bcs.Address.from_str(target.value)
            module_id = module if isinstance(module, str) else module.value
            function_id = function if isinstance(function, str) else function.value
        # Standardize the arguments to list
        if arguments and not skip_arg_resolve:
            arguments = arguments if isinstance(arguments, list) else arguments.array
            arguments = self._resolve_arguments(arguments)
        elif arguments and skip_arg_resolve:
            pass
        else:
            arguments = []
        # Standardize the type_arguments to list
        if type_arguments:
            type_arguments = type_arguments if isinstance(type_arguments, list) else type_arguments.array
            type_arguments = [bcs.TypeTag.type_tag_from(x) for x in type_arguments]
        else:
            type_arguments = []

        return self.builder.move_call(
            target=target_id, arguments=arguments, type_arguments=type_arguments, module=module_id, function=function_id
        )

    def _move_call(
        self,
        *,
        target: Union[str, SuiString],
        arguments: list[Union[bcs.Argument, tuple[bcs.BuilderArg, bcs.ObjectArg]]],
        type_arguments: Optional[list[bcs.TypeTag]] = None,
    ) -> bcs.Argument:
        """_move_call Internal move call when arguments and type_arguments already prepared.

        :param target: String triple in form "package_object_id::module_name::function_name"
        :type target: Union[str, SuiString]
        :param arguments: List of resolved bcs.Argument (pure) or tuple (object)
        :type arguments: list[Union[bcs.Argument, tuple[bcs.BuilderArg, bcs.ObjectArg]]]
        :param type_arguments: List of resolved type tags, defaults to None
        :type type_arguments: Optional[list[bcs.TypeTag]], optional
        :raises ValueError: if not well formed target
        :return: _description_
        :rtype: bcs.Argument
        """
        type_arguments = type_arguments if isinstance(type_arguments, list) else []
        # Standardize the input parameters
        if isinstance(target, (str, SuiString)):
            target = target if isinstance(target, str) else target.value
            target_id, module_id, function_id = target.split("::")
            target_id = bcs.Address.from_str(target_id)
        else:
            raise ValueError(f"Expected target 'package_id::module::function' found {target.__class__.__name__}")
        return self.builder.move_call(
            target=target_id, arguments=arguments, type_arguments=type_arguments, module=module_id, function=function_id
        )

    def _to_bytes_from_str(self, inbound: Union[str, SuiString]) -> list[int]:
        """."""
        return list(base64.b64decode(inbound if isinstance(inbound, str) else inbound.value))

    def publish(
        self,
        *,
        modules: list[str, SuiString],
        dependencies: list[str, ObjectID],
        recipient: Optional[SuiAddress] = None,
    ) -> bcs.Argument:
        """."""
        assert isinstance(modules, list), "modules requires a list"
        assert isinstance(dependencies, list), "dependencies requires a list"
        modules = list(map(self._to_bytes_from_str, modules))
        dependencies = [bcs.Address.from_str(x if isinstance(x, str) else x.value) for x in dependencies]
        if recipient:
            recipient = tx_builder.PureInput.as_input(recipient)
        else:
            recipient = tx_builder.PureInput.as_input(SuiAddress(self._sender))
        return self.builder.publish(modules, dependencies, recipient)

    # def publish_immutable(
    #     self,
    #     *,
    #     modules: list[str, SuiString],
    #     dependencies: list[str, ObjectID],
    #     recipient: Optional[SuiAddress] = None,
    # ) -> bcs.Argument:
    #     """."""
    #     assert isinstance(modules, list), "modules requires a list"
    #     assert isinstance(dependencies, list), "dependencies requires a list"
    #     modules = list(map(self._to_bytes_from_str, modules))
    #     dependencies = [bcs.Address.from_str(x if isinstance(x, str) else x.value) for x in dependencies]
    #     if recipient:
    #         recipient = tx_builder.PureInput.as_input(recipient)
    #     else:
    #         recipient = tx_builder.PureInput.as_input(SuiAddress(self._sender))
    #     return self.builder.publish_immutable(modules, dependencies, recipient)

    # TODO: Verify results expectation
    def stake_coin(
        self,
        *,
        coins: list[ObjectID],
        validator_address: Union[str, SuiAddress],
        amount: Optional[Union[int, SuiInteger]] = None,
    ) -> bcs.Argument:
        """stake_coin Stakes one or more coins to a specific validator.

        :param coins: One or more coins to stake.
        :type coins: list[ObjectID]
        :param validator_address: The validator to stake coins to
        :type validator_address: Union[str, SuiAddress]
        :param amount: Amount from coins to stake. If not stated, all coin will be staked, defaults to None
        :type amount: Optional[Union[int, SuiInteger]], optional
        :return: The command result.
        :rtype: bcs.Argument
        """
        params: list = []
        params.append(_SYSTEMSTATE_OBJECT)
        params.append(self.make_move_vector(coins))
        if amount:
            amount = amount if isinstance(amount, int) else amount.value
            params.append(bcs.OptionalU64(amount))
        else:
            params.append(bcs.OptionalU64())
        params.append(validator_address if isinstance(validator_address, SuiAddress) else SuiAddress(validator_address))
        return self._move_call(target=_STAKE_REQUEST_TARGET, arguments=self._resolve_arguments(params))

    def unstake_coin(self, *, staked_coin: Union[str, ObjectID, StakedSui]) -> bcs.Argument:
        """."""
        params: list = []
        params.append(_SYSTEMSTATE_OBJECT)
        if isinstance(staked_coin, str):
            params.append(ObjectID(staked_coin))
        elif isinstance(staked_coin, StakedSui):
            if staked_coin.status != "Pending":
                params.append(ObjectID(staked_coin.staked_sui_id))
            else:
                raise ValueError(f"Can not unstake non-activated staked coin {staked_coin}")
        else:
            params.append(staked_coin)
        return self._move_call(target=_UNSTAKE_REQUEST_TARGET, arguments=self._resolve_arguments(params))

    def split_coin(self, *, coin: Union[str, ObjectID, ObjectRead], amount: Union[int, SuiInteger]) -> bcs.Argument:
        """split_coin Creates a new coin with the defined amount, split from the provided coin.

        Note: Returns the coin so that it can be used in subsequent commands.

        :param coin: The coin address (object id) to split from.
        :type coin: Union[str, ObjectID, ObjectRead]
        :param amount: The amount to split out from coin
        :type amount: Union[int, SuiInteger]
        :raises ValueError: if the coin object can not be found on the chain.
        :return: The result that can be used in subsequent commands.
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

    # TODO: Verify results expectation
    def split_coin_equally(
        self, *, coin: Union[str, ObjectID, ObjectRead], parts: Union[int, SuiInteger]
    ) -> bcs.Argument:
        """split_coin_equally takes coin and breaks it up into n parts returning vector of coin result.

        :param coin: The coin targeted to split
        :type coin: Union[str, ObjectID, ObjectRead]
        :param parts: The number of equal parts to split into
        :type parts: Union[int, SuiInteger]
        :raises ValueError: If parts is less than two
        :raises ValueError: If the coin can not be validated
        :return: The result object.
        :rtype: bcs.Argument
        """
        assert isinstance(coin, (str, ObjectID, ObjectRead)), "invalid coin object type"
        assert isinstance(parts, (int, SuiInteger)), "invalid parts type"
        parts = parts if isinstance(parts, int) else parts.value
        if parts < 2:
            raise ValueError(f"Parts must be at least 2, found {parts}")
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
        type_arguments = [bcs.TypeTag.type_tag_from("0x2::sui::SUI")]
        return self._move_call(
            target="0x2::coin::divide_into_n", type_arguments=type_arguments, arguments=[coin_ref, SuiU64(parts)]
        )

    def merge_coins(
        self,
        *,
        merge_to: Union[str, ObjectID, ObjectRead, SuiCoinObject, bcs.Argument],
        merge_from: Union[list[Union[str, ObjectID, ObjectRead, SuiCoinObject, bcs.Argument]], SuiArray],
    ) -> bcs.Argument:
        """merge_coins Merges one or more coins to a primary coin.

        :param merge_to: The coin to merge other coins to
        :type merge_to: Union[str, ObjectID, ObjectRead, SuiCoinObject, bcs.Argument]
        :param merge_from: One or more coins to merge to primary 'merge_to' coin
        :type merge_from: Union[list[Union[str, ObjectID, ObjectRead, SuiCoinObject, bcs.Argument]], SuiArray]
        :return: The command result. Can be used as input in subsequent commands.
        :rtype: bcs.Argument
        """
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

    def transfer_objects(
        self,
        *,
        transfers: Union[list[Union[str, ObjectID, ObjectRead, SuiCoinObject, bcs.Argument]], SuiArray],
        recipient: Union[ObjectID, SuiAddress],
    ) -> bcs.Argument:
        """transfer_objects Transfers one or more objects to a recipient.

        :param transfers: A list or SuiArray of objects to transfer
        :type transfers: Union[list[Union[str, ObjectID, ObjectRead, SuiCoinObject, bcs.Argument]], SuiArray]
        :param recipient: The recipient address that will receive the objects being transfered
        :type recipient: Union[ObjectID, SuiAddress]
        :return: The command result. Can NOT be used as input in subsequent commands.
        :rtype: bcs.Argument
        """
        assert isinstance(transfers, (list, SuiArray)), "Unsupported trasfers collection type"
        assert isinstance(recipient, (ObjectID, SuiAddress)), "invalid recipient type"
        transfers = transfers if isinstance(transfers, list) else transfers.array
        for txfer in transfers:
            assert isinstance(
                txfer, (str, ObjectID, ObjectRead, SuiCoinObject, bcs.Argument)
            ), "Unsupported entry in transfers"
        transfers = self._resolve_references(transfers)
        return self.builder.transfer_objects(tx_builder.PureInput.as_input(recipient), transfers)

    def transfer_sui(
        self,
        *,
        recipient: Union[ObjectID, SuiAddress],
        from_coin: Union[str, ObjectID, ObjectRead, SuiCoinObject],
        amount: Optional[Union[int, SuiInteger]] = None,
    ) -> bcs.Argument:
        """transfer_sui Transfers a Sui coin object to a recipient.

        :param recipient: The recipient address that will receive the Sui coin being transfered
        :type recipient: Union[ObjectID, SuiAddress]
        :param from_coin: The Sui coin to transfer
        :type from_coin: Union[str, ObjectID, ObjectRead, SuiCoinObject]
        :param amount: Optional amount to transfer. Entire coin if not specified, defaults to None
        :type amount: Optional[Union[int, SuiInteger]], optional
        :raises ValueError: If unable to fetch the from_coin
        :raises ValueError: If from_coin is invalid
        :return: The command result. Can NOT be used as input in subsequent commands.
        :rtype: bcs.Argument
        """
        assert isinstance(recipient, (ObjectID, SuiAddress)), "invalid recipient type"
        if amount:
            assert isinstance(amount, (int, SuiInteger))
            amount = amount if isinstance(amount, int) else amount.value
            amount = tx_builder.PureInput.as_input(bcs.U64.encode(amount))
        if from_coin:
            if not isinstance(from_coin, (ObjectRead, SuiCoinObject)):
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
            raise ValueError(f"Invalid 'from_coin' {from_coin}")
        return self.builder.transfer_sui(tx_builder.PureInput.as_input(recipient), from_coin_ref, amount)


if __name__ == "__main__":
    pass
