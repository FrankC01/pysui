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
import math
from typing import Union
import canoser

# pylint:disable=wildcard-import,unused-wildcard-import
from pysui.sui.sui_types.bcs import *

# pylint:enable=wildcard-import,unused-wildcard-import
from pysui.sui.sui_types.address import SuiAddress
from pysui.sui.sui_utils import hexstring_to_list, b58str_to_list, b64str_to_list
from pysui.sui.sui_clients.common import SuiRpcResult
from pysui.sui.sui_txresults.common import GenericRef
from pysui.sui.sui_txresults.single_tx import ObjectRawRead
from pysui.sui.sui_builders.get_builders import GetFunction, GetRawObject
from pysui.sui.sui_builders.exec_builders import (
    _MoveCallTransactionBuilder,
    MoveCall,
    MoveCallRequestParams,
    TransferObject,
    TransferObjectParams,
)

from pysui.sui.sui_clients.sync_client import SuiClient as SyncClient
from pysui.sui.sui_types.scalars import ObjectID, SuiString
from pysui.sui.sui_types.collections import SuiArray
from pysui.sui.sui_txresults.package_meta import SuiMoveFunction, SuiParameterReference, SuiParameterStruct


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
            byte_res = math.ceil(elem.bit_length() / 8)
            if byte_res == byte_count:
                res.extend(list(elem.to_bytes(byte_res, "little")))
            else:
                raise ValueError(f"Expected byte count {byte_count} found byte count {byte_res}")
        return res

    def bools_to_array(in_el: list[bool]) -> list[int]:
        return [1 if x else 0 for x in in_el]

    def strs_to_array(in_el: list[str]) -> list[int]:
        res: list[int] = []
        for elem in in_el:
            res.extend([ord(x) for x in f"{elem}"])
        return res

    # Determine expectation of element types
    if vector_of[0] == "U":
        hmg_type = int
        call_site = partial(ints_to_array, int(vector_of[1:]) / 8)
    elif vector_of[0] == "s":
        hmg_type = str
        call_site = strs_to_array
    elif vector_of[0] == "b":
        hmg_type = bool
        call_site = bools_to_array
    else:
        raise ValueError(f"Unknown vector type {vector_of}")

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
    :raises ValueError: If expected vector but found other
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
                    bcs_arg = CallArg("Pure", [ord(x) for x in f"{arg}"])
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


def bcs_from_builder(client: SyncClient, builder: _MoveCallTransactionBuilder) -> Union[BCSTransactionKind, Exception]:
    """bcs_from_builder constructs a Transaction kind from a Builder.

    The result can be serialized and used in sui_devInspectTransaction.
    """
    bname = builder.__class__.__name__
    tx_kind = "Single"

    if isinstance(builder, _MoveCallTransactionBuilder):
        match bname:
            case "TransferObject":
                recipient = BCSAddress.from_sui_address(builder.recipient)
                reference = _bcs_reference_for_oid(client, builder.object_id)
                payload = BCSSingleTransaction(bname, BCSTransferObject(recipient, reference))
            case "TransferSui":
                recipient = BCSAddress.from_sui_address(builder.recipient)
                amount = BCSOptionalU64(builder.amount.value)
                payload = BCSSingleTransaction(bname, BCSTransferSui(recipient, amount))
            case "Pay" | "PaySui":
                coins = [_bcs_reference_for_oid(client, x.value) for x in builder.input_coins.coins]
                amounts = [x.value for x in builder.amounts.amounts]
                recipients = [BCSAddress.from_sui_address(x) for x in builder.recipients.recipients]
                if bname == "Pay":
                    payload = BCSSingleTransaction(bname, BCSPay(coins, recipients, amounts))
                else:
                    payload = BCSSingleTransaction(bname, BCSPaySui(coins, recipients, amounts))
            case "PayAllSui":
                coins = [_bcs_reference_for_oid(client, x.value) for x in builder.input_coins.coins]
                recipient = BCSAddress.from_sui_address(builder.recipient)
                payload = BCSSingleTransaction(bname, BCSPayAllSui(coins, recipient))
            case "Publish":
                modules = [b64str_to_list(x.value) for x in builder.compiled_modules.compiled_modules]
                payload = BCSSingleTransaction(bname, BCSPublish(modules))
            case "MoveCall":
                # Create call site basics from package_object_id,module and function name
                package = BCSAddress.from_str(builder.package_object_id.value)
                module = builder.module.value
                function = builder.function.value
                # Create list of Struct objects for any type_arguments
                type_args = [
                    TypeTag("Struct", StructTag.from_type_str(x.value)) for x in builder.type_arguments.type_arguments
                ]
                # Create list of Call args for any arguments
                arguments = _bcs_call_arguments(
                    client, builder.package_object_id, builder.module, builder.function, builder.arguments
                )
                payload = BCSSingleTransaction("Call", BCSMoveCall(package, module, function, type_args, arguments))
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
    """bcs_base64_from_builder converts a builder to BCS serialized base64 string.

    Can be then used to submit to sui_devInspectTransaction

    :param client: The sui synch client
    :type client: pysui.sui.sui_clients.sync_client.SuiClient
    :param builder: The constructed builder
    :type builder: _MoveCallTransactionBuilder
    :return: If successful, a base64 string otherwise Exception
    :rtype: Union[str, Exception]
    """
    return base64.b64encode(bcs_from_builder(client, builder).serialize()).decode()


def tkind_from_result(indata: SuiRpcResult) -> Union[str, SuiRpcResult]:
    """tkind_from_result Return a BCS serialized kind as base64 encoded string.

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
