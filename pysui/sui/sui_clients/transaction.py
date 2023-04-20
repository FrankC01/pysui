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
import os
from pathlib import Path
from typing import Any, Optional, Union
from deprecated.sphinx import versionadded, versionchanged
from pysui.sui.sui_builders.base_builder import SuiRequestType
from pysui.sui.sui_builders.exec_builders import ExecuteTransaction, InspectTransaction, PayAllSui
from pysui.sui.sui_builders.get_builders import GetFunction, GetReferenceGasPrice, GetMultipleObjects
from pysui.sui.sui_clients.common import SuiRpcResult
import pysui.sui.sui_clients.transaction_builder as tx_builder
from pysui.sui.sui_crypto import MultiSig, SuiPublicKey
from pysui.sui.sui_txresults.common import GenericRef
from pysui.sui.sui_txresults.complex_tx import TxInspectionResult
from pysui.sui.sui_txresults.single_tx import (
    AddressOwner,
    ImmutableOwner,
    ObjectNotExist,
    ObjectRead,
    SharedOwner,
    StakedSui,
    SuiCoinObject,
)
from pysui.sui.sui_types import bcs
from pysui.sui.sui_types.address import SuiAddress
from pysui.sui.sui_clients.sync_client import SuiClient
from pysui.sui.sui_types.collections import SuiArray
from pysui.sui.sui_types.scalars import ObjectID, SuiInteger, SuiIntegerType, SuiString, SuiTxBytes, SuiU8
from pysui.sui.sui_utils import publish_build

_SYSTEMSTATE_OBJECT: ObjectID = ObjectID("0x5")
_STAKE_REQUEST_TARGET: str = "0x3::sui_system::request_add_stake_mul_coin"
_UNSTAKE_REQUEST_TARGET: str = "0x3::sui_system::request_withdraw_stake"
_UPGRADE_CAP_TYPE: str = "0x2::package::UpgradeCap"
_SPLIT_AND_KEEP: str = "0x2::pay::divide_and_keep"
_PAY_GAS: int = 4000000


class SuiTransaction:
    """High level transaction builder."""

    _MC_RESULT_CACHE: dict = {}

    def __init__(
        self, client: SuiClient, sender: Union[str, SuiAddress] = None, merge_gas_budget: bool = False
    ) -> None:
        """Transaction initializer."""
        self.builder = tx_builder.ProgrammableTransactionBuilder()
        self.client = client
        self._sender: str = ""
        self._set_sender(sender)
        self._gasses: list[SuiCoinObject] = self._reset_gas(self._sender)
        self._merge_gas = merge_gas_budget
        self._executed = False
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

    @versionchanged(version="0.16.1", reason="Added returning SuiRpcResult if inspect transaction failed.")
    def inspect_all(self, for_sender: Union[str, SuiAddress] = None) -> Union[TxInspectionResult, SuiRpcResult]:
        """inspect_all Returns results of sui_devInspectTransactionBlock on the current Transaction.

        :param for_sender: Used for inspection. If not supplied, uses current Transaction sender, defaults to None
        :type for_sender: Union[str, SuiAddress], optional
        :return: The successful result or the SuiRpcResult if inspect transaction failed.
        :rtype: Union[TxInspectionResult, SuiRpcResult]
        """
        tx_bytes = self.build_for_inspection()
        if for_sender:
            for_sender = for_sender if isinstance(for_sender, str) else for_sender.address
        else:
            for_sender = self._sender
        result = self.client.execute(InspectTransaction(sender_address=for_sender, tx_bytes=tx_bytes))
        if result.is_ok():
            return result.result_data
        return result

    @versionchanged(version="0.16.1", reason="Added returning SuiRpcResult if inspect transaction failed.")
    def inspect_for_cost(self, for_sender: Union[str, SuiAddress] = None) -> Union[tuple[int, int, str], SuiRpcResult]:
        """inspect_for_cost Runs inspect transaction for cost summary.

        :param for_sender: Use for inspection. If not supplied, uses current Transaction sender, defaults to None
        :type for_sender: Union[str, SuiAddress], optional
        :return: If inspect did not fail, a tuple of gas_max, gas_min, gas object_id otherwise None
        :rtype: Union[tuple[int, int, str], SuiRpcResult]
        """
        ispec = self.inspect_all(for_sender)
        if ispec and isinstance(ispec, TxInspectionResult):
            gas_used = ispec.effects.gas_used
            gas_max = gas_used.total
            gas_min = gas_used.total_after_rebate
            return gas_max, gas_min, ispec.effects.gas_object.reference.object_id
        return SuiRpcResult

    def _gas_for_budget(self, sponsor: str, budget: int) -> SuiCoinObject:
        """Used internally to select a gas object to use in transaction."""
        balance_low_list: list = []
        balance_threshold: int = 0
        if sponsor != self._sender:
            use_gasses = self._reset_gas(sponsor)
        else:
            sponsor = self._sender
            use_gasses = self._gasses
        # If we only have one coin and it is being used in commands, fail
        if len(use_gasses) == 1 and use_gasses[0].coin_object_id in self.builder.objects_registry:
            raise ValueError(
                f"{sponsor} only has 1 gas object and it is being used in transaction. Consider splitting coin."
            )
        for gobj in use_gasses:
            if int(gobj.balance) > budget and gobj.coin_object_id not in self.builder.objects_registry:
                return gobj
            if gobj.coin_object_id not in self.builder.objects_registry and self._merge_gas:
                balance_low_list.append(ObjectID(gobj.coin_object_id))
                balance_threshold += int(gobj.balance)
                if balance_threshold > budget:
                    break
        # Here if can't find single coin to satisfy so if balance_threshold met, merge the coins
        if balance_threshold > budget + _PAY_GAS:
            result = self.client.execute(
                PayAllSui(
                    signer=sponsor,
                    input_coins=SuiArray(balance_low_list),
                    recipient=sponsor,
                    gas_budget=str(_PAY_GAS),
                )
            )
            if result.is_ok():
                return balance_low_list[0]
        raise ValueError(f"Available gas for {sponsor} does not satisfy budget of {budget}")

    # FIXME: Doesn't account for sponsor
    @versionchanged(version="0.17.0", reason="Only used internally.")
    def _build_for_execute(
        self,
        *,
        signer: Union[str, SuiAddress],
        gas: Optional[Union[str, ObjectID]] = None,
        gas_budget: Union[str, SuiString],
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
        gas_budget = gas_budget if isinstance(gas_budget, str) else gas_budget.value
        gas_budget = max(max_cost, int(gas_budget))

        # If a coin is not passed, we fetch one
        if not gas:
            gas: SuiCoinObject = self._gas_for_budget(signer, gas_budget)
        assert gas
        gas_object = bcs.GasData(
            [
                bcs.ObjectReference(
                    bcs.Address.from_str(gas.coin_object_id), int(gas.version), bcs.Digest.from_str(gas.digest)
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

    @versionchanged(version="0.16.1", reason="Added 'additional_signers' optional argument")
    def execute(
        self,
        *,
        signer: Union[str, SuiAddress],
        gas: Optional[Union[str, ObjectID]] = None,
        gas_budget: Union[str, SuiString],
        additional_signers: Optional[list[Union[str, SuiAddress]]] = None,
    ) -> SuiRpcResult:
        """execute Finalizes transaction and submits for execution on the chain.

        :param signer: The signer of transaction address
        :type signer: Union[str, SuiAddress]
        :param gas_budget: The gas budget to use. An introspection of the transaciton is performed
            and this method will use the larger of the two.
        :type gas_budget: Union[int, SuiInteger]
        :param gas: An gas coin object id. If not provided, one of the signers gas object will be used, defaults to None
        :type gas: Optional[Union[str, ObjectID]], optional
        :param additional_signers: When additional signatures are needed. Sponsor for example, defaults to None
        :type additional_signers: Optional[list[Union[str, SuiAddress]]], optional
        :return: Result of executing instruction
        :rtype: SuiRpcResult
        """
        assert not self._executed, "Transaction already executed"
        additional_signers = additional_signers if additional_signers else []
        additional_signers = [x if isinstance(x, SuiAddress) else SuiAddress(x) for x in additional_signers]
        signer, _, tx_data = self._build_for_execute(signer=signer, gas=gas, gas_budget=gas_budget)
        tx_b64 = base64.b64encode(tx_data.serialize()).decode()
        iresult = self.client.sign_and_submit(SuiAddress(signer), SuiTxBytes(tx_b64), SuiArray(additional_signers))
        self._executed = True
        return iresult

    @versionadded(version="0.16.1", reason="Support MultiSig transaction signing")
    def execute_with_multi_sig(
        self,
        *,
        signer: MultiSig,
        pub_keys: list[SuiPublicKey],
        gas: Optional[Union[str, ObjectID]] = None,
        gas_budget: Union[str, SuiString],
        additional_signers: Optional[list[Union[str, SuiAddress]]] = None,
    ) -> Union[SuiRpcResult, Exception]:
        """execute_with_multi_sig Finalizes transaction and submits for execution on the chain.

        :param signer: The MultiSig object to use as the signer of a transaction.
        :type signer: MultiSig
        :param pub_keys: The subset (or all) of the keys from the multi-sig
        :type pub_keys: Union[str, SuiString]
        :param gas_budget: The gas budget to use. An introspection of the transaciton is performed
            and this method will use the larger of the two.
        :type gas_budget: Union[int, SuiInteger]
        :param gas: An gas coin object id. If not provided, one of the signers gas object will be used, defaults to None
        :type gas: Optional[Union[str, ObjectID]], optional
        :param additional_signers: When additional signatures are needed. Sponsor for example, defaults to None
        :type additional_signers: Optional[list[Union[str, SuiAddress]]], optional
        :return: Result of executing instruction or ValueError
        :rtype: Union[SuiRpcResult, Exception]
        """
        assert not self._executed, "Transaction already executed"
        assert isinstance(signer, MultiSig), "Requires a MultiSig signer argument."
        for pkey in pub_keys:
            assert isinstance(pkey, SuiPublicKey)
        additional_signers = additional_signers if additional_signers else []
        additional_signers = [x if isinstance(x, SuiAddress) else SuiAddress(x) for x in additional_signers]
        _, _, tx_data = self._build_for_execute(signer=signer, gas=gas, gas_budget=gas_budget)
        tx_b64 = base64.b64encode(tx_data.serialize()).decode()
        # Get the multi-sig signature
        new_sig = signer.sign(tx_b64, pub_keys)

        sig_array = [new_sig]
        # Get any additional signatures
        if additional_signers:
            sig_array.extend([kpair.new_sign_secure(tx_b64) for kpair in additional_signers])
        exec_tx = ExecuteTransaction(
            tx_bytes=tx_b64,
            signatures=SuiArray(sig_array),
            request_type=SuiRequestType.WAITFORLOCALEXECUTION,
        )
        self._executed = True
        return self.client.execute(exec_tx)

    # Commands and helpers

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
                case "int" | "SuiInteger" | "str" | "SuiString" | "SuiAddress" | "bytes" | "OptionalU64":
                    items[index] = tx_builder.PureInput.as_input(items[index])
                case "Digest":
                    items[index] = bcs.BuilderArg("Pure", list(items[index].serialize()))
                # Need to fetch objects
                case "ObjectID":
                    objref_indexes.append(index)
                case "SuiCoinObject":
                    items[index] = ObjectID(item.object_id)
                    objref_indexes.append(index)
                # Tuple all ready to be set
                case "ObjectRead":
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
                if isinstance(item.owner, (AddressOwner, ImmutableOwner)):
                    obj_ref = GenericRef(item.object_id, item.version, item.digest)
                    b_obj_arg = bcs.ObjectArg("ImmOrOwnedObject", bcs.ObjectReference.from_generic_ref(obj_ref))
                elif isinstance(item.owner, SharedOwner):
                    b_obj_arg = bcs.ObjectArg("SharedObject", bcs.SharedObjectReference.from_object_read(item))
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

    def _mc_target_resolve(self, target: str) -> tuple[bcs.Address, str, str, int]:
        """."""
        if target in self._MC_RESULT_CACHE:
            return self._MC_RESULT_CACHE[target]
        package_id, module_id, function_id = target.split("::")
        result = self.client.execute(GetFunction(package=package_id, module_name=module_id, function_name=function_id))
        if result.is_ok():
            res_tup = (bcs.Address.from_str(package_id), module_id, function_id, len(result.result_data.returns))
            # res_cnt: int = len(result.result_data.returns)
            # package_id = bcs.Address.from_str(package_id)
            self._MC_RESULT_CACHE[target] = res_tup
            return res_tup
        raise ValueError(f"Unable to find target: {target}")

    @versionchanged(version="0.17.0", reason="Target uses 'package_id::module::function' only")
    def move_call(
        self,
        *,
        target: Union[str, SuiString],
        arguments: Union[list, SuiArray],
        type_arguments: Optional[Union[list, SuiArray]] = None,
        skip_arg_resolve: Optional[bool] = False,
    ) -> bcs.Argument:
        """move_call Creates a command to invoke a move contract call. May or may not return results.

        :param target: Target move call signature. Must be in form 'package_id::module::function'.
        :type target: Union[str, SuiString, ObjectID]
        :param arguments: Parameters that are passed to the move function
        :type arguments: Union[list, SuiArray]
        :param type_arguments: Optional list of type arguments for move function generics, defaults to None
        :type type_arguments: Optional[Union[list, SuiArray]], optional
        :param skip_arg_resolve: Used internally, defaults to False
        :type skip_arg_resolve: Optional[bool], optional
        :raises ValueError: If ommitting module and function but target is not compound.
        :return: The result which may or may not be used in subequent commands depending on the
            move method being called.
        :rtype: bcs.Argument
        """
        assert not self._executed, "Transaction already executed"
        assert isinstance(target, (str, SuiString))
        target = target if isinstance(target, str) else target.value
        target_id = None
        module_id = None
        function_id = None
        # Standardize the input parameters
        target_id, module_id, function_id, res_count = self._mc_target_resolve(target)
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
            target=target_id,
            arguments=arguments,
            type_arguments=type_arguments,
            module=module_id,
            function=function_id,
            res_count=res_count,
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
        :return: _description_
        :rtype: bcs.Argument
        """
        assert isinstance(target, (str, SuiString))
        # Standardize the input parameters
        target = target if isinstance(target, str) else target.value
        target_id, module_id, function_id, res_count = self._mc_target_resolve(target)

        type_arguments = type_arguments if isinstance(type_arguments, list) else []
        return self.builder.move_call(
            target=target_id,
            arguments=arguments,
            type_arguments=type_arguments,
            module=module_id,
            function=function_id,
            res_count=res_count,
        )

    def _to_bytes_from_str(self, inbound: Union[str, SuiString]) -> list[int]:
        """Utility to convert base64 string to bytes then as list of u8."""
        return list(base64.b64decode(inbound if isinstance(inbound, str) else inbound.value))

    def publish(
        self,
        *,
        project_path: str,
        with_unpublished_dependencies: bool = False,
        skip_fetch_latest_git_deps: bool = False,
        recipient: Optional[SuiAddress] = None,
    ) -> bcs.Argument:
        """publish Creates a publish command.

        :param project_path: path to project folder
        :type project_path: str
        :param with_unpublished_dependencies: Flag indicating inclusion of adding unpublished dependencies
            of package, defaults to False
        :type with_unpublished_dependencies: bool, optional
        :param skip_fetch_latest_git_deps: Flag indicating to skip compiliation fetch of
            package dependencies, defaults to False
        :type skip_fetch_latest_git_deps: bool, optional
        :param recipient: Address of who owns the published package. If None, active-address is used, defaults to None
        :type recipient: Optional[SuiAddress], optional
        :return: A command result that can used in subsequent commands
        :rtype: bcs.Argument
        """
        assert not self._executed, "Transaction already executed"
        src_path = Path(os.path.expanduser(project_path))
        compiled_package = publish_build(src_path, with_unpublished_dependencies, skip_fetch_latest_git_deps)
        modules = list(map(self._to_bytes_from_str, compiled_package.compiled_modules))
        dependencies = [
            bcs.Address.from_str(x if isinstance(x, str) else x.value) for x in compiled_package.dependencies
        ]
        if recipient:
            recipient = tx_builder.PureInput.as_input(recipient)
        else:
            recipient = tx_builder.PureInput.as_input(SuiAddress(self._sender))
        return self.builder.publish(modules, dependencies, recipient)

    def _verify_upgrade_cap(self, upgrade_cap: str) -> ObjectRead:
        """Verify that the upgrade cap is valid."""
        resp = self.client.get_object(upgrade_cap)
        if resp.is_ok() and not isinstance(resp.result_data, ObjectNotExist):
            upcap: ObjectRead = resp.result_data
            assert upcap.object_type == _UPGRADE_CAP_TYPE, f"Invalid upgrade_cap object {upcap}"
            return upcap

        raise ValueError(f"Error in finding UpgradeCap on {upgrade_cap}")

    def publish_upgrade(
        self,
        *,
        project_path: str,
        package_id: Union[str, ObjectID],
        upgrade_cap: Union[str, ObjectID, ObjectRead],
        with_unpublished_dependencies: bool = False,
        skip_fetch_latest_git_deps: bool = False,
        recipient: Optional[SuiAddress] = None,
    ) -> bcs.Argument:
        """publish_upgrade Publish upgrade of package command.

        :param project_path: path to project folder
        :type project_path: str
        :param upgrade_cap: The upgrade capability object
        :type upgrade_cap: Union[str, ObjectID, ObjectRead]
        :param with_unpublished_dependencies: Flag indicating inclusion of adding unpublished dependencies
            of package, defaults to False
        :type with_unpublished_dependencies: bool, optional
        :param skip_fetch_latest_git_deps: Flag indicating to skip compiliation fetch of
            package dependencies, defaults to False
        :type skip_fetch_latest_git_deps: bool, optional
        :param recipient: Address of who owns the published package. If None, active-address is used, defaults to None
        :type recipient: Optional[SuiAddress], optional
        :return: The Result Argument
        :rtype: bcs.Argument
        """
        assert not self._executed, "Transaction already executed"
        assert isinstance(upgrade_cap, (str, ObjectID, ObjectRead))
        assert isinstance(package_id, (str, ObjectID))
        # Compile the new package
        src_path = Path(os.path.expanduser(project_path))
        compiled_package = publish_build(src_path, with_unpublished_dependencies, skip_fetch_latest_git_deps)
        modules = list(map(self._to_bytes_from_str, compiled_package.compiled_modules))
        dependencies = [
            bcs.Address.from_str(x if isinstance(x, str) else x.value) for x in compiled_package.dependencies
        ]
        # Verify get/upgrade cap details
        if not isinstance(upgrade_cap, ObjectRead):
            upgrade_cap = upgrade_cap if isinstance(upgrade_cap, str) else upgrade_cap.value
            upgrade_cap = self._verify_upgrade_cap(upgrade_cap)
        else:
            assert upgrade_cap.object_type == _UPGRADE_CAP_TYPE, f"Invalid upgrade_cap object {upgrade_cap}"

        capability_arg = self._resolve_arguments(
            [
                upgrade_cap,
                SuiU8(upgrade_cap.content.fields["policy"]),
                bcs.Digest.from_bytes(compiled_package.package_digest),
            ]
        )

        # Trap the number of input_obj len:
        cap_arg = len(self.builder.inputs)
        # authorize
        auth_cmd = self.builder.authorize_upgrade(*capability_arg)
        package_id = bcs.Address.from_str(package_id if isinstance(package_id, str) else package_id.value)
        # Upgrade
        receipt = self.builder.publish_upgrade(modules, dependencies, package_id, auth_cmd)
        # Commit
        return self.builder.commit_upgrade(bcs.Argument("Input", cap_arg), receipt)

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
        assert not self._executed, "Transaction already executed"
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
        """unstake_coin Unstakes a Staked Sui Coin.

        :param staked_coin: The coin being unstaked
        :type staked_coin: Union[str, ObjectID, StakedSui]
        :raises ValueError: If the staked coin is still in 'pending' state
        :return: The Result argument
        :rtype: bcs.Argument
        """
        assert not self._executed, "Transaction already executed"
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

    @versionchanged(version="0.17.0", reason="Made 'amount' 'amounts' with list argument.")
    def split_coin(
        self,
        *,
        coin: Union[str, ObjectID, ObjectRead, SuiCoinObject, bcs.Argument],
        amounts: list[Union[int, SuiInteger]],
    ) -> Union[bcs.Argument, list[bcs.Argument]]:
        """split_coin Creates a new coin(s) with the defined amount(s), split from the provided coin.

        Note: Returns the result that it can be used in subsequent commands. If only one amount
        is provided, a standard Result can be used as a singular argument to another command.
        But if more than 1 amount. For example  you can index to get a singular value or use the whole
        list.

        .. code-block:: python

            # Transfer all coins to one recipient
            txer = SuiTransaction(client)
            scres = txer.split_coin(coin=primary_coin, amounts=[1000000000, 1000000000])
            txer.transfer_objects(transfers=scres, recipient=client.config.active_address)

            # OR only transfer less than all
            txer.transfer_objects(transfers=[scres[0]],recipient=client.config.active_address)

        :param coin: The coin address (object id) to split from.
        :type coin: Union[str, ObjectID, ObjectRead,SuiCoinObject, bcs.Argument]
        :param amounts: The amount or list of amounts to split the coin out to
        :type amounts: list[Union[int, SuiInteger]]
        :return: A result or list of results types to use in subsequent commands
        :rtype: Union[list[bcs.Argument],bcs.Argument]
        """
        assert not self._executed, "Transaction already executed"
        assert isinstance(coin, (str, ObjectID, ObjectRead, SuiCoinObject, bcs.Argument)), "invalid coin object type"
        amounts = amounts if isinstance(amounts, list) else [amounts]
        for amount in amounts:
            assert isinstance(amount, (int, SuiInteger))
        amounts = [tx_builder.PureInput.as_input(bcs.U64.encode(x)) if isinstance(x, int) else x.value for x in amounts]
        coin = coin if isinstance(coin, (ObjectID, ObjectRead, SuiCoinObject, bcs.Argument)) else ObjectID(coin)
        resolved = self._resolve_arguments([coin])
        return self.builder.split_coin(resolved[0], amounts)

    @versionadded(version="0.16.1", reason="Expand Transaction builder ease of use capability.")
    def split_coin_equal(
        self,
        *,
        coin: Union[str, ObjectID, ObjectRead, SuiCoinObject, bcs.Argument],
        split_count: Union[int, SuiInteger],
        coin_type: Optional[str] = "0x2::sui::SUI",
    ) -> bcs.Argument:
        """split_coin_equal Splits a Sui coin into equal parts and transfers to transaction signer.

        :param coin: The coin to split
        :type coin: Union[str, ObjectID, ObjectRead, SuiCoinObject, bcs.Argument]
        :param split_count: The number of parts to split coin into
        :type split_count: Union[int, SuiInteger]
        :param coin_type: The coin type, defaults to a Sui coin type
        :type coin_type: Optional[str], optional
        :return: The command result. Because all splits are automagically transferred to
            signer, the result is not usable as input to subseqent commands.
        :rtype: bcs.Argument
        """
        assert not self._executed, "Transaction already executed"
        assert isinstance(coin, (str, ObjectID, ObjectRead, SuiCoinObject, bcs.Argument)), "invalid coin object type"
        assert isinstance(split_count, (int, SuiInteger)), "invalid amount type"
        split_count = split_count if isinstance(split_count, int) else split_count.value
        coin = coin if isinstance(coin, (ObjectID, ObjectRead, SuiCoinObject, bcs.Argument)) else ObjectID(coin)
        resolved = self._resolve_arguments([coin, tx_builder.PureInput.as_input(bcs.U64.encode(split_count))])

        return self._move_call(
            target=_SPLIT_AND_KEEP,
            arguments=resolved,
            type_arguments=[bcs.TypeTag.type_tag_from(coin_type)],
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
        assert not self._executed, "Transaction already executed"
        assert isinstance(
            merge_to, (str, ObjectID, ObjectRead, SuiCoinObject, bcs.Argument)
        ), "Unsupported type for merge_to"
        merge_to = self._resolve_arguments([merge_to if not isinstance(merge_to, str) else ObjectID(merge_to)])[0]
        # Depper from_coin type verification
        assert isinstance(merge_from, (list, SuiArray)), "Unsupported merge_from collection type"
        parm_list: list = []
        merge_from = merge_from if isinstance(merge_from, list) else merge_from.coins
        for fcoin in merge_from:
            assert isinstance(
                fcoin, (str, ObjectID, ObjectRead, SuiCoinObject, bcs.Argument)
            ), "Unsupported entry in merge_from"
            parm_list.append(fcoin if not isinstance(fcoin, str) else ObjectID(fcoin))
        return self.builder.merge_coins(merge_to, self._resolve_arguments(parm_list))

    def transfer_objects(
        self,
        *,
        transfers: Union[bcs.Argument, list[Union[str, ObjectID, ObjectRead, SuiCoinObject, bcs.Argument]], SuiArray],
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
        assert not self._executed, "Transaction already executed"
        assert isinstance(transfers, (list, SuiArray, bcs.Argument)), "Unsupported trasfers collection type"
        assert isinstance(recipient, (ObjectID, SuiAddress)), "invalid recipient type"
        if isinstance(transfers, (list, SuiArray)):
            transfers = transfers if isinstance(transfers, list) else transfers.array
            coerced_transfers: list = []
            for txfer in transfers:
                assert isinstance(
                    txfer, (str, ObjectID, ObjectRead, SuiCoinObject, bcs.Argument)
                ), "Unsupported entry in transfers"
                if isinstance(txfer, str):
                    coerced_transfers.append(ObjectID(txfer))
                else:
                    coerced_transfers.append(txfer)
            transfers = self._resolve_arguments(coerced_transfers)
        return self.builder.transfer_objects(tx_builder.PureInput.as_input(recipient), transfers)

    def transfer_sui(
        self,
        *,
        recipient: Union[ObjectID, SuiAddress],
        from_coin: Union[str, ObjectID, ObjectRead, SuiCoinObject, bcs.Argument],
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
        assert not self._executed, "Transaction already executed"
        assert isinstance(recipient, (ObjectID, SuiAddress)), "invalid recipient type"
        if amount:
            assert isinstance(amount, (int, SuiInteger))
            amount = amount if isinstance(amount, int) else amount.value
            amount = tx_builder.PureInput.as_input(bcs.U64.encode(amount))
        if from_coin:
            if isinstance(from_coin, str):
                from_coin = ObjectID(from_coin)
            from_coin = self._resolve_arguments([from_coin])
        else:
            raise ValueError(f"Invalid 'from_coin' {from_coin}")
        return self.builder.transfer_sui(tx_builder.PureInput.as_input(recipient), *from_coin, amount)


if __name__ == "__main__":
    pass
