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
from pysui.sui.sui_clients.common import SuiRpcResult, handle_result
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
from pysui.sui.sui_types.scalars import ObjectID, SuiInteger, SuiIntegerType, SuiSignature, SuiString, SuiU8
from pysui.sui.sui_utils import publish_build

_SYSTEMSTATE_OBJECT: ObjectID = ObjectID("0x5")
_STAKE_REQUEST_TARGET: str = "0x3::sui_system::request_add_stake_mul_coin"
_UNSTAKE_REQUEST_TARGET: str = "0x3::sui_system::request_withdraw_stake"
_UPGRADE_CAP_TYPE: str = "0x2::package::UpgradeCap"
_SPLIT_AND_KEEP: str = "0x2::pay::divide_and_keep"
_PAY_GAS: int = 4000000


@versionadded(version="0.17.0", reason="Standardize on signing permutations")
class SigningMultiSig:
    """Wraps the mutli-sig along with pubkeys to use in SuiTransaction."""

    def __init__(self, msig: MultiSig, pub_keys: list[SuiPublicKey]):
        """."""
        self.multi_sig = msig
        self.pub_keys = pub_keys


@versionadded(version="0.17.0", reason="Standardize on signing permutations")
class SignerBlock:
    """Manages the potential signers and resolving the gas object for paying."""

    def __init__(
        self,
        *,
        sender: Optional[Union[SuiAddress, SigningMultiSig]] = None,
        sponsor: Optional[Union[SuiAddress, SigningMultiSig]] = None,
        additional_signers: Optional[list[Union[SuiAddress, SigningMultiSig]]] = None,
    ):
        """."""
        self._sender = sender
        self._sponsor = sponsor
        self._additional_signers = additional_signers if additional_signers else []

    @property
    def sender(self) -> Union[SuiAddress, SigningMultiSig]:
        """Return the current sender used in signing."""
        return self._sender

    @sender.setter
    def sender(self, new_sender: Union[SuiAddress, SigningMultiSig]):
        """Set the sender to use in signing the transaction."""
        assert isinstance(new_sender, (SuiAddress, SigningMultiSig))
        self._sender = new_sender

    @property
    def sponsor(self) -> Union[SuiAddress, SigningMultiSig]:
        """Return the current sponsor (may be None) used as payer of transaction."""
        return self._sponsor

    @sponsor.setter
    def sponser(self, new_sponsor: Union[SuiAddress, SigningMultiSig]):
        """Set the sponsor to used to pay for transaction. This also signs the transaction."""
        assert isinstance(new_sponsor, (SuiAddress, SigningMultiSig))
        self._sponsor = new_sponsor

    @property
    def additional_signers(self) -> list[Union[SuiAddress, SigningMultiSig]]:
        """Gets the list of additional signers although Sui doesn't seem to support at the moment."""
        return self._additional_signers

    @additional_signers.setter
    def additional_signers(self, new_additional_signers: list[Union[SuiAddress, SigningMultiSig]]):
        """sets the list of additional signers although Sui doesn't seem to support at the moment."""
        new_additional_signers = new_additional_signers if new_additional_signers else []
        for additional_signer in new_additional_signers:
            assert isinstance(additional_signer, (SuiAddress, SigningMultiSig))
        self._additional_signers = new_additional_signers

    def add_additioinal_signer(self, additional_signer: Union[SuiAddress, SigningMultiSig]):
        """Add another signer to the additional_signers list."""
        assert isinstance(additional_signer, (SuiAddress, SigningMultiSig))
        self._additional_signers.append(additional_signer)

    def _get_potential_signatures(self) -> list[Union[SuiAddress, SigningMultiSig]]:
        """Internal flattening of signers."""
        result_list = []
        if self.sender:
            result_list.append(self.sender)
        if self.sponsor:
            result_list.append(self._sponsor)
        result_list.extend(self.additional_signers)
        return result_list

    def get_signatures(self, *, client: SuiClient, tx_bytes: str) -> SuiArray[SuiSignature]:
        """Get all the signatures needed for the transaction."""
        sig_list: list[SuiSignature] = []
        for signer in self._get_potential_signatures():
            if isinstance(signer, SuiAddress):
                sig_list.append(client.config.keypair_for_address(signer).new_sign_secure(tx_bytes))
            else:
                sig_list.append(signer.multi_sig.sign(tx_bytes, signer.pub_keys))
        return SuiArray(sig_list)

    def get_gas_object(
        self, *, client: SuiClient, budget: int, objects_in_use: list, merge_coin: bool, gas_price: int
    ) -> bcs.GasData:
        """Produce a gas object from either the sponsor or the sender."""
        # Either a sponsor (priority) or sender will pay for this
        who_pays = self._sponsor if self._sponsor else self._sender
        # If both not set, Fail
        if not who_pays:
            raise ValueError("Both SuiTransaction sponor and sender are null. Complete those before execute.")
        who_pays = who_pays if isinstance(who_pays, SuiAddress) else who_pays.multi_sig.as_sui_address
        owner_coins: list[SuiCoinObject] = handle_result(client.get_gas(who_pays)).data
        # Get whatever gas objects below to whoever is paying
        # and filter those not in use
        use_coin: SuiCoinObject = None
        owner_gas: list[SuiCoinObject] = [
            x for x in owner_coins if x.coin_object_id not in objects_in_use and int(x.balance) >= budget
        ]
        # Find that which satisfies budget
        # If we have a result of the main filter, use first
        if owner_gas:
            use_coin = owner_gas[0]
        # Otherwise if we can merge
        elif merge_coin:
            alt_gas: list[SuiCoinObject] = [x for x in owner_coins if x.coin_object_id not in objects_in_use]
            if alt_gas:
                enh_budget = budget + _PAY_GAS
                to_pay: list[str] = []
                accum_pay: int = 0
                for ogas in alt_gas:
                    to_pay.append(ogas)
                    accum_pay += int(ogas.balance)
                    if accum_pay >= enh_budget:
                        break
                if accum_pay >= enh_budget:
                    handle_result(
                        client.execute(
                            PayAllSui(
                                signer=who_pays,
                                input_coins=SuiAddress([ObjectID(x.coin_object_id) for x in to_pay]),
                                recipient=who_pays,
                                gas_budget=str(_PAY_GAS),
                            )
                        )
                    )
                    use_coin = to_pay[0]
        # If we have a coin to use, return the GasDataObject
        if use_coin:
            return bcs.GasData(
                [
                    bcs.ObjectReference(
                        bcs.Address.from_str(use_coin.coin_object_id),
                        int(use_coin.version),
                        bcs.Digest.from_str(use_coin.digest),
                    )
                ],
                bcs.Address.from_str(who_pays.address),
                gas_price,
                budget,
            )
        raise ValueError(f"{who_pays} has nothing to pay with.")


class SuiTransaction:
    """High level transaction builder."""

    _MC_RESULT_CACHE: dict = {}

    def __init__(self, client: SuiClient, merge_gas_budget: bool = False) -> None:
        """Transaction initializer."""
        self.builder = tx_builder.ProgrammableTransactionBuilder()
        self.client = client
        self._sig_block = SignerBlock(sender=client.config.active_address)
        self._merge_gas = merge_gas_budget
        self._executed = False
        self._current_gas_price = self._gas_price()

    def _reset_gas(self, for_owner: Union[SuiAddress, MultiSig]) -> list:
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

    @gas_price.setter
    def gas_price(self, new_price: int):
        """Set the gas price."""
        self._current_gas_price = new_price

    @property
    def signer_block(self) -> SignerBlock:
        """Returns the signers block."""
        return self._sig_block

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
    def inspect_all(self) -> Union[TxInspectionResult, SuiRpcResult]:
        """inspect_all Returns results of sui_devInspectTransactionBlock on the current Transaction.

        :param for_sender: Used for inspection. If not supplied, uses current Transaction sender, defaults to None
        :type for_sender: Union[str, SuiAddress], optional
        :return: The successful result or the SuiRpcResult if inspect transaction failed.
        :rtype: Union[TxInspectionResult, SuiRpcResult]
        """
        tx_bytes = self.build_for_inspection()
        if self.signer_block.sender:
            for_sender = self.signer_block.sender
        else:
            for_sender = self.client.config.active_address
        result = self.client.execute(InspectTransaction(sender_address=for_sender, tx_bytes=tx_bytes))
        if result.is_ok():
            return result.result_data
        return result

    @versionchanged(version="0.16.1", reason="Added returning SuiRpcResult if inspect transaction failed.")
    def inspect_for_cost(self) -> Union[tuple[int, int, str], SuiRpcResult]:
        """inspect_for_cost Runs inspect transaction for cost summary.

        :param for_sender: Use for inspection. If not supplied, uses current Transaction sender, defaults to None
        :type for_sender: Union[str, SuiAddress], optional
        :return: If inspect did not fail, a tuple of gas_max, gas_min, gas object_id otherwise None
        :rtype: Union[tuple[int, int, str], SuiRpcResult]
        """
        ispec = self.inspect_all()
        if ispec and isinstance(ispec, TxInspectionResult):
            gas_used = ispec.effects.gas_used
            gas_max = gas_used.total
            gas_min = gas_used.total_after_rebate
            return gas_max, gas_min, ispec.effects.gas_object.reference.object_id
        return SuiRpcResult

    @versionchanged(version="0.17.0", reason="Only used internally.")
    @versionchanged(version="0.17.0", reason="Reworked using SignerBlock gas resolution.")
    def _build_for_execute(
        self,
        gas_budget: Union[str, SuiString],
    ) -> bcs.TransactionData:
        """build_for_execute Generates the TransactionData object.

        Note: If wanting to execute, this structure needs to be serialized to a base64 string. See
        the execute method below

        :param gas_budget: The gas budget to use. An introspection of the transaciton is performed and
            and this method will use the larger of the two.
        :type gas_budget: Union[int, SuiInteger]
        :return: TransactionData object replete with all required fields for execution
        :rtype: bcs.TransactionData
        """
        # Get the transaction body
        tx_kind = self.raw_kind()
        # We already have gas price
        max_cost, _, _ = self.inspect_for_cost()
        gas_budget = gas_budget if isinstance(gas_budget, str) else gas_budget.value
        gas_budget = max(max_cost, int(gas_budget))

        # Fetch the payment
        gas_object = self._sig_block.get_gas_object(
            client=self.client,
            budget=max_cost,
            objects_in_use=self.builder.objects_registry,
            merge_coin=self._merge_gas,
            gas_price=self._current_gas_price,
        )
        if isinstance(self.signer_block.sender, SuiAddress):
            who_sends = self.signer_block.sender.address
        else:
            who_sends = self.signer_block.sender.multi_sig.address
        return bcs.TransactionData(
            "V1",
            bcs.TransactionDataV1(
                tx_kind,
                bcs.Address.from_str(who_sends),
                gas_object,
                bcs.TransactionExpiration("None"),
            ),
        )

    @versionadded(version="0.17.0", reason="Convenience for serializing and dry-running.")
    def get_transaction_data(self, *, gas_budget) -> bcs.TransactionData:
        """."""
        return self._build_for_execute(gas_budget)

    @versionchanged(version="0.16.1", reason="Added 'additional_signers' optional argument")
    @versionchanged(version="0.17.0", reason="Revamped for all signature potentials and types.")
    def execute(self, *, gas_budget: Union[str, SuiString]) -> SuiRpcResult:
        """execute Finalizes transaction and submits for execution on the chain.

        :param gas_budget: The gas budget to use. An introspection of the transaciton is performed
            and this method will use the larger of the two.
        :type gas_budget: Union[int, SuiInteger]
        :return: Result of executing instruction
        :rtype: SuiRpcResult
        """
        assert not self._executed, "Transaction already executed"
        tx_b64 = base64.b64encode(self._build_for_execute(gas_budget).serialize()).decode()
        exec_tx = ExecuteTransaction(
            tx_bytes=tx_b64,
            signatures=self.signer_block.get_signatures(client=self.client, tx_bytes=tx_b64),
            request_type=SuiRequestType.WAITFORLOCALEXECUTION,
        )
        iresult = self.client.execute(exec_tx)
        self._executed = True
        return iresult

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
                case "bool":
                    items[index] = tx_builder.PureInput.as_input(items[index])
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

    # TODO: Investigate functools LRU
    def _move_call_target_cache(self, target: str) -> tuple[bcs.Address, str, str, int]:
        """Used to resolve information regarding a move call target.

        This caches the result of a GetFunction meta-data information essention to setting up
        the proper command return types.
        """
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

    @versionchanged(version="0.17.0", reason="Target uses 'package_id::module::function' construct only")
    def move_call(
        self,
        *,
        target: Union[str, SuiString],
        arguments: Union[list, SuiArray],
        type_arguments: Optional[Union[list, SuiArray]] = None,
    ) -> Union[bcs.Argument, list[bcs.Argument]]:
        """move_call Creates a command to invoke a move contract call. May or may not return results.

        :param target: String triple in form "package_object_id::module_name::function_name"
        :type target: Union[str, SuiString]
        :param arguments: Parameters that are passed to the move function
        :type arguments: Union[list, SuiArray]
        :param type_arguments: Optional list of type arguments for move function generics, defaults to None
        :type type_arguments: Optional[Union[list, SuiArray]], optional
        :return: The result which may or may not be used in subequent commands depending on the
            move method being called.
        :rtype: Union[bcs.Argument, list[bcs.Argument]]
        """
        assert not self._executed, "Transaction already executed"
        assert isinstance(target, (str, SuiString))
        target = target if isinstance(target, str) else target.value
        target_id = None
        module_id = None
        function_id = None
        # Standardize the input parameters
        target_id, module_id, function_id, res_count = self._move_call_target_cache(target)
        # Standardize the arguments to list
        if arguments:
            arguments = arguments if isinstance(arguments, list) else arguments.array
            arguments = self._resolve_arguments(arguments)
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
    ) -> Union[bcs.Argument, list[bcs.Argument]]:
        """_move_call Internal move call when arguments and type_arguments already prepared.

        :param target: String triple in form "package_object_id::module_name::function_name"
        :type target: Union[str, SuiString]
        :param arguments: List of resolved bcs.Argument (pure) or tuple (object)
        :type arguments: list[Union[bcs.Argument, tuple[bcs.BuilderArg, bcs.ObjectArg]]]
        :param type_arguments: List of resolved type tags, defaults to None
        :type type_arguments: Optional[list[bcs.TypeTag]], optional
        :return: The result which may or may not be used in subequent commands depending on the
            move method being called.
        :rtype: Union[bcs.Argument, list[bcs.Argument]]
        """
        assert isinstance(target, (str, SuiString))
        # Standardize the input parameters
        target = target if isinstance(target, str) else target.value
        target_id, module_id, function_id, res_count = self._move_call_target_cache(target)

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
            recipient = tx_builder.PureInput.as_input(self.signer_block.sender)
        return self.builder.publish(modules, dependencies, recipient)

    def _verify_upgrade_cap(self, upgrade_cap: str) -> ObjectRead:
        """Verify that the upgrade cap is valid."""
        resp = self.client.get_object(upgrade_cap)
        if resp.is_ok() and not isinstance(resp.result_data, ObjectNotExist):
            upcap: ObjectRead = resp.result_data
            assert upcap.object_type == _UPGRADE_CAP_TYPE, f"Invalid upgrade_cap object {upcap}"
            return upcap
        raise ValueError(f"Error in finding UpgradeCap on {upgrade_cap}")

    @versionchanged(version="0.17.0", reason="Dropped recipient as the resulting UpgradeCap goes to main signer.")
    def publish_upgrade(
        self,
        *,
        project_path: str,
        package_id: Union[str, ObjectID],
        upgrade_cap: Union[str, ObjectID, ObjectRead],
        with_unpublished_dependencies: bool = False,
        skip_fetch_latest_git_deps: bool = False,
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
