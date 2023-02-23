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
from functools import partial
from typing import Union
import canoser


# pylint:disable=wildcard-import,unused-wildcard-import
from pysui.sui.sui_types.bcs import *

# pylint:enable=wildcard-import,unused-wildcard-import
from pysui.abstracts.client_types import SuiScalarType
from pysui.sui.sui_types.address import SuiAddress
from pysui.sui.sui_utils import b64str_to_list, int_to_listu8
from pysui.sui.sui_clients.common import SuiRpcResult
from pysui.sui.sui_txresults.common import GenericRef
from pysui.sui.sui_txresults.single_tx import ObjectRawRead
from pysui.sui.sui_builders.get_builders import GetFunction, GetRawObject
from pysui.sui.sui_builders.exec_builders import (
    _MoveCallTransactionBuilder,
    MoveCall,
    MoveCallRequestParams,
    Pay,
    PayAllSui,
    PaySui,
    Publish,
    TransferObject,
    TransferObjectParams,
    TransferSui,
)

from pysui.sui.sui_clients.sync_client import SuiClient as SyncClient
from pysui.sui.sui_types.scalars import ObjectID, SuiString
from pysui.sui.sui_types.collections import SuiArray
from pysui.sui.sui_txresults.package_meta import (
    SuiMoveFunction,
    SuiMoveScalarArgument,
    SuiParameterReference,
    SuiParameterStruct,
)


_TKIND_INDEX: int = 0
_SUB_TKIND_INDEX: int = 1
_SKIP_KIND_AND_SINGLE: int = 2
_SKIP_KIND_AND_BATCH: int = 1
_GAS_AND_BUDGET_BYTE_OFFSET: int = -97
FAKE_ADDRESS_OR_OBJECT: str = "0x0000000000000000000000000000000000000000"


def _bcs_reference_for_oid(client: SyncClient, object_id: ObjectID) -> Union[BCSObjectReference, Exception]:
    """_bcs_reference_for_oid _summary_.

    :param client: Sui Client
    :type client: SyncClient
    :param object_id: The object being used for building an ObjectReference
    :type object_id: ObjectID
    :raises ValueError: If sui_getObject fails
    :return: The BCS ObjectReference
    :rtype: Union[BCSObjectReference, Exception]
    """
    bro_result = client.get_object(object_id)
    if bro_result.is_ok():
        return BCSObjectReference.from_generic_ref(bro_result.result_data.reference)
    raise ValueError(f"{bro_result.result_string} fetching object {object_id}")


def _bcs_objarg_for_oid(client: SyncClient, object_id: ObjectID) -> Union[ObjectArg, Exception]:
    """_bcs_objarg_for_oid generates an ObjectArg, used in CallArg, for object_id.

    :param client: Sui Client
    :type client: SyncClient
    :param object_id: The object being used for building an ObjectArg
    :type object_id: ObjectID
    :raises ValueError: if sui_getRawObject fails
    :return: The constructed ObjectArg
    :rtype: Union[ObjectArg, Exception]
    """
    bro_result = client.execute(GetRawObject(object_id))
    if bro_result.is_ok():
        raw_data: ObjectRawRead = bro_result.result_data
        if isinstance(raw_data.owner, str):
            if raw_data.owner == "Immutable":
                arg_type = "ImmOrOwnedObject"
        elif "AddressOwner" in raw_data.owner:
            arg_type = "ImmOrOwnedObject"
        else:
            arg_type = "SharedObject"
        return ObjectArg(arg_type, BCSObjectReference.from_generic_ref(raw_data.reference))
    raise ValueError(f"{bro_result.result_string} fetching object {object_id}")


def _bcs_call_arg_for_oid(client: SyncClient, object_id: ObjectID) -> Union[CallArg, Exception]:
    """_bcs_call_arg_for_oid generates a call argument for object_id.

    :param client: SUI Client
    :type client: SyncClient
    :param object_id: The object being used for call arg generation
    :type object_id: ObjectID
    :raises ValueError: If getting object information RPC fails
    :return: A CallArg structure of type "Object"
    :rtype: CallArg
    """
    return CallArg("Object", _bcs_objarg_for_oid(client, object_id))


def _bcs_callarg_from_scalar(meta_parm: SuiMoveScalarArgument, arg: SuiScalarType) -> Union[CallArg, Exception]:
    """_bcs_callarg_from_scalar converts scalar type to Pure Callarg.

    :param meta_parm: The scalar type from meta information
    :type meta_parm: SuiMoveScalarArgument
    :param arg: The scalar value
    :type arg: SuiScalarType
    :raises ValueError: If unhandled scalar type
    :return: Instance of Pure CallArg
    :rtype: Union[CallArg, Exception]
    """
    if meta_parm.scalar_type[0] == "A" or meta_parm.scalar_type[0] == "S":
        bcs_arg = CallArg("Pure", getattr(BCSAddress.from_str(arg.value), "Address"))
    elif meta_parm.scalar_type[0] == "U":
        bcs_arg = CallArg("Pure", int_to_listu8(int(meta_parm.scalar_type[1:]) / 8, arg.value))
    elif meta_parm.scalar_type[0] == "B":
        bcs_arg = CallArg("Pure", [1 if arg.value else 0])
    else:
        raise ValueError(f"Unhandled scalar type {meta_parm.scalar_type}")
    return bcs_arg


def _bcs_build_pure_array(vector_of: str, in_vector: SuiArray) -> Union[CallArg, Exception]:
    """_bcs_build_pure_array create a Pure CallArg from array.

    :param vector_of: What contract function is expecting
    :type vector_of: str
    :param in_vector: Array of scalars
    :type in_vector: SuiArray
    :raises ValueError: If expected type not handled
    :raises ValueError: If array is not homogeneous types
    :return: array of u8
    :rtype: Union[CallArg, Exception]
    """
    hmg_type = int
    call_site = None

    def ints_to_array(byte_count: int, in_el: list[int]) -> list[int]:
        res: list[int] = []
        for elem in in_el:
            res.extend(int_to_listu8(byte_count, elem))
        return res

    def bools_to_array(in_el: list[bool]) -> list[int]:
        return [1 if x else 0 for x in in_el]

    def sigoraddress_to_array(in_el: list[str]) -> list[int]:
        res: list[int] = []
        for elem in in_el:
            res.extend(getattr(BCSAddress.from_str(elem), "Address"))
        return res

    # Determine expectation of element types
    # Unsigned ints
    if vector_of[0] == "U":
        hmg_type = int
        call_site = partial(ints_to_array, int(vector_of[1:]) / 8)
    # Address and Signer
    elif vector_of[0] == "A" or vector_of[0] == "S":
        hmg_type = str
        call_site = sigoraddress_to_array
    # Bool
    elif vector_of[0] == "B":
        hmg_type = bool
        call_site = bools_to_array
    # Not handled
    else:
        raise ValueError(f"Unknown vector of type {vector_of}")

    hmg_list = []

    # check for homogenous types and get raw values
    for elem in in_vector.array:
        if isinstance(elem.value, hmg_type) is False:
            raise ValueError(f"{elem.value} of type {type(elem.value)} is not type {vector_of}")
        hmg_list.append(elem.value)
    bcs_array = [int.from_bytes(canoser.Uint32.serialize_uint32_as_uleb128(len(hmg_list)), "little")]
    bcs_array.extend(call_site(hmg_list))

    return CallArg("Pure", bcs_array)


def _bcs_call_arguments(
    client: SyncClient, package_oid: ObjectID, module: SuiString, function: SuiString, arguments: SuiArray
) -> list[CallArg]:
    """_bcs_call_arguments generates a list of BCS CallArgs used in Call BCS.

    :param client: SUI Client
    :type client: SyncClient
    :param package_oid: ID of published Package
    :type package_oid: ObjectID
    :param module: The module name in package
    :type module: SuiString
    :param function: The function name in package
    :type function: SuiString
    :param arguments: The module arguments list
    :type arguments: SuiArray
    :raises ValueError: If length of expected arguments does not match arguments list length
    :raises ValueError: If sclar argument type not handled
    :raises ValueError: If expected SuiArray but found other
    :raises NotImplementedError: If unrecognized function argument meta type
    :raises ValueError: If sui_getNormalizedMoveFunction fails
    :return: List of constructed CallArgs
    :rtype: list[CallArg]
    """
    fresult = client.execute(GetFunction(package=package_oid, module_name=module, function_name=function))
    if fresult.is_ok():
        arg_list = arguments.arguments
        func_meta: SuiMoveFunction = fresult.result_data
        if len(func_meta.parameters) > 0:
            last_one = func_meta.parameters[-1]
            meta_parm = last_one.__class__.__name__
            if meta_parm == "SuiParameterStruct" and last_one.name == "TxContext":
                func_meta.parameters.pop()
            elif meta_parm == "SuiParameterReference" and last_one.reference_to.name == "TxContext":
                func_meta.parameters.pop()
        if len(func_meta.parameters) != len(arg_list):
            raise ValueError(f"Function {function} takes {len(func_meta.parameters)} found {len(arg_list)}")
        call_args: list[CallArg] = []
        for index, arg in enumerate(arg_list):
            meta_parm = func_meta.parameters[index]
            match meta_parm.__class__.__name__:
                case "SuiParameterReference" | "SuiParameterStruct":
                    bcs_arg = _bcs_call_arg_for_oid(client, arg)
                case "SuiMoveScalarArgument":
                    bcs_arg = _bcs_callarg_from_scalar(meta_parm, arg)

                case "SuiMoveVector":
                    if isinstance(arg, SuiArray):
                        if isinstance(meta_parm.vector_of, (SuiParameterReference, SuiParameterStruct)):
                            bcs_arg = CallArg("ObjVec", [_bcs_objarg_for_oid(client, x) for x in arg.array])
                        else:
                            bcs_arg = _bcs_build_pure_array(meta_parm.vector_of, arg)
                    else:
                        raise ValueError(f"Expected SuiArray, found {arg.__class__.__name__}")
                case _:
                    raise NotImplementedError(f"{func_meta.parameters[index].__class__.__name__} not handled")
            call_args.append(bcs_arg)
        return call_args
    raise ValueError(f"Getting function {function} failed with {fresult.result_string}")


def _from_transfer_parms(parms: TransferObjectParams) -> TransferObject:
    """_from_transfer_parms convert a TransferObjectParams to TransferObject builder.

    :param parms: The TransferObjectParams object
    :type parms: TransferObjectParams
    :return: The TransferObject builder
    :rtype: TransferObject
    """
    return TransferObject(
        signer=FAKE_ADDRESS_OR_OBJECT,
        recipient=parms.receiver,
        object_id=parms.transfer_object,
        gas=FAKE_ADDRESS_OR_OBJECT,
        gas_budget=1,
    )


def _from_movecall_parms(parms: MoveCallRequestParams) -> MoveCall:
    """_from_movecall_parms convert a MoveCallRequestParams to MoveCall builder.

    :param parms: The MoveCallRequestParams object
    :type parms: MoveCallRequestParams
    :return: The MoveCall builder
    :rtype: MoveCall
    """
    return MoveCall(
        signer=FAKE_ADDRESS_OR_OBJECT,
        gas=FAKE_ADDRESS_OR_OBJECT,
        gas_budget=1,
        package_object_id=parms.package_object_id,
        module=parms.module,
        function=parms.function,
        type_arguments=SuiArray([SuiString(x) for x in parms.type_arguments.type_arguments]),
        arguments=SuiArray([SuiString(x) for x in parms.arguments.arguments]),
    )


# BCSSingleTransaction type from builders


def _bcs_for_transfer_object(client: SyncClient, builder: TransferObject) -> BCSSingleTransaction:
    """_bcs_for_transfer_object generates the TransferObject BCS Single Transaction from builder.

    :param client: SUI Client
    :type client: SyncClient
    :param builder: The TransferObject populated builder
    :type builder: TransferObject
    :return: An instance of BCSSingleTransaction
    :rtype: BCSSingleTransaction
    """
    recipient = BCSAddress.from_sui_address(builder.recipient)
    reference = _bcs_reference_for_oid(client, builder.object_id)
    return BCSSingleTransaction("TransferObject", BCSTransferObject(recipient, reference))


def _bcs_for_transfer_sui(client: SyncClient, builder: TransferSui) -> BCSSingleTransaction:
    """_bcs_for_transfer_sui generates the TransferSui BCS Single Transaction from builder.

    :param client: SUI Client
    :type client: SyncClient
    :param builder: The TransferSui populated builder
    :type builder: TransferSui
    :return: An instance of BCSSingleTransaction
    :rtype: BCSSingleTransaction
    """
    recipient = BCSAddress.from_sui_address(builder.recipient)
    amount = BCSOptionalU64(builder.amount.value)
    return BCSSingleTransaction("TransferSui", BCSTransferObject(recipient, amount))


def _bcs_for_pays(client: SyncClient, builder: Union[Pay, PaySui, PayAllSui]) -> BCSSingleTransaction:
    """_bcs_for_pays generates a BCS Single Transaction for the various Pay type builders.

    :param client: SUI Client
    :type client: SyncClient
    :param builder: One of the Pay type builders
    :type builder: Union[Pay, PaySui, PayAllSui]
    :return: An instance of BCSSingleTransaction
    :rtype: BCSSingleTransaction
    """
    coins = [_bcs_reference_for_oid(client, x.value) for x in builder.input_coins.coins]
    payload: BCSSingleTransaction = None

    if isinstance(builder, Pay):
        recipients = [BCSAddress.from_sui_address(x) for x in builder.recipients.recipients]
        amounts = [x.value for x in builder.amounts.amounts]
        payload = BCSSingleTransaction("Pay", BCSPay(coins, recipients, amounts))
    elif isinstance(builder, PaySui):
        recipients = [BCSAddress.from_sui_address(x) for x in builder.recipients.recipients]
        amounts = [x.value for x in builder.amounts.amounts]
        payload = BCSSingleTransaction("PaySui", BCSPaySui(coins, recipients, amounts))
    else:
        recipient = BCSAddress.from_sui_address(builder.recipient)
        payload = BCSSingleTransaction("PayAllSui", BCSPayAllSui(coins, recipient))
    return payload


def _bcs_for_publish(client: SyncClient, builder: Publish) -> BCSSingleTransaction:
    """_bcs_for_publish generates a BCS Single Transaction from a Publish builder.

    :param client: SUI Client
    :type client: SyncClient
    :param builder: A populated Publish builder
    :type builder: Publish
    :return: An instance of BCSSingleTransaction
    :rtype: BCSSingleTransaction
    """
    modules = [b64str_to_list(x.value) for x in builder.compiled_modules.compiled_modules]
    return BCSSingleTransaction("Publish", BCSPublish(modules))


def _bcs_for_call(client: SyncClient, builder: MoveCall) -> BCSSingleTransaction:
    """_bcs_for_call generates a BCS Single Transaction from a MoveCall builder.

    :param client: SUI Client
    :type client: SyncClient
    :param builder: A populated MoveCall builder
    :type builder: MoveCall
    :return: An instance of BCSSingleTransaction
    :rtype: BCSSingleTransaction
    """
    package = BCSAddress.from_str(builder.package_object_id.value)
    module = builder.module.value
    function = builder.function.value
    # Create list of Struct objects for any type_arguments
    type_args = [TypeTag("Struct", StructTag.from_type_str(x.value)) for x in builder.type_arguments.type_arguments]
    # Create list of Call args for any arguments
    arguments = _bcs_call_arguments(
        client, builder.package_object_id, builder.module, builder.function, builder.arguments
    )
    return BCSSingleTransaction("Call", BCSMoveCall(package, module, function, type_args, arguments))


def bcs_from_builder(client: SyncClient, builder: _MoveCallTransactionBuilder) -> Union[BCSTransactionKind, Exception]:
    """bcs_from_builder constructs a BCS TransactionKind from a Builder.

    The result can be serialized and used in sui_devInspectTransaction.
    """
    bname = builder.__class__.__name__
    tx_kind = "Single"

    if isinstance(builder, _MoveCallTransactionBuilder):
        match bname:
            case "TransferObject":
                payload = _bcs_for_transfer_object(client, builder)
            case "TransferSui":
                payload = _bcs_for_transfer_sui(client, builder)
            case "Pay" | "PaySui" | "PayAllSui":
                payload = _bcs_for_pays(client, builder)
            case "Publish":
                payload = _bcs_for_publish(client, builder)
            case "MoveCall":
                payload = _bcs_for_call(client, builder)
            case "BatchTransaction":
                tx_kind = "Batch"
                res_vector = []
                for parm_type in builder.single_transaction_params.array:
                    if isinstance(parm_type, TransferObjectParams):
                        out_parm = bcs_from_builder(client, _from_transfer_parms(parm_type))
                    elif isinstance(parm_type, MoveCallRequestParams):
                        out_parm = bcs_from_builder(client, _from_movecall_parms(parm_type))
                    else:
                        raise NotImplementedError(
                            "{parm_type.__class__.__name} batch transaction type not implemented yet"
                        )
                    res_vector.append(out_parm.value)
                payload = BCSBatchTransaction(res_vector)
            case _:
                raise TypeError(f"conversion from type {bname} builder not supported")
    return BCSTransactionKind(tx_kind, payload)


def bcs_base64_from_builder(client: SyncClient, builder: _MoveCallTransactionBuilder) -> Union[str, Exception]:
    """bcs_base64_from_builder converts a builder to BCS serialized TransactionKind as base64 string.

    Can be then used to submit to sui_devInspectTransaction

    :param client: The sui synch client
    :type client: pysui.sui.sui_clients.sync_client.SuiClient
    :param builder: The constructed builder
    :type builder: _MoveCallTransactionBuilder
    :return: If successful, a base64 string otherwise Exception
    :rtype: Union[str, Exception]
    """
    return base64.b64encode(bcs_from_builder(client, builder).serialize()).decode()


def bcs_txkind_from_result(indata: SuiRpcResult) -> Union[str, SuiRpcResult]:
    """tkind_from_result Return a BCS serialized TransactionKind as base64 encoded string.

    Can be then used to submit to sui_devInspectTransaction

    :param indata: The result of calling a complex transaction prior to signing
    :type indata: SuiRpcResult
    :return: A base64 encoded serialized BCS TransactionKind
    :rtype: str
    """
    if indata.is_ok():
        _, no_sign_tx_bytes = indata.result_data
        return base64.b64encode(base64.b64decode(no_sign_tx_bytes.value)[:_GAS_AND_BUDGET_BYTE_OFFSET]).decode()
    return indata


def bcs_from_rpcresult(no_sign_result: SuiRpcResult) -> Union[tuple[str, canoser.Struct], Exception]:
    """bcs_from_rpcresult converts the transaction bytes from an unsigned transaction result into BCS.

    :param no_sign_result: The result from calling (not signing) transaction
    :type no_sign_result: SuiRpcResult
    :raises NotImplementedError: If not implemented by pysui yet
    :raises AttributeError: Unrecognized TransactionKind
    :raises AttributeError: No deserialization for BCSSingleTransaction
    :raises ValueError: If no_sign_result success if False
    :return: The BCS decoded transaction kind (i.e. Pay, TransferSui, MoveCall, etc.)
    :rtype: Union[tuple[str, canoser.Struct], Exception]
    """
    if no_sign_result.is_ok():
        _, txbytes = no_sign_result.result_data
        tx_kind = base64.b64decode(txbytes.value)
        # The first byte is index of TransactionKind variant (enum)
        tkind_name, tkind_class = BCSTransactionKind.variant_for_index(tx_kind[_TKIND_INDEX])
        match tkind_name:
            case "Single":
                # The second byte is index into concrete transaction type enum
                tk_name, tx_type_class = tkind_class.variant_for_index(tx_kind[_SUB_TKIND_INDEX])
                if tx_type_class:
                    sheded = tx_kind[:_GAS_AND_BUDGET_BYTE_OFFSET]
                    sheded = sheded[_SKIP_KIND_AND_SINGLE:]
                    return tk_name, tx_type_class.deserialize(sheded)
                raise AttributeError(f"{tkind_name} has no deserialization entry in BCSSingleTransaction")
            case "Batch":
                sheded = tx_kind[:_GAS_AND_BUDGET_BYTE_OFFSET]
                sheded = sheded[_SKIP_KIND_AND_BATCH:]
                bdser = BCSBatchTransaction.deserialize(sheded)
                return "Batch", bdser
            case _:
                raise AttributeError(f"{tkind_name} is unknown TransactionKind")
    else:
        raise ValueError(f"RPC result is invalid {no_sign_result.result_string}")


if __name__ == "__main__":
    pass
