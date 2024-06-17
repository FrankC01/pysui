#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Sui Transaction Wallet Standard serialization."""

import base64
from dataclasses import dataclass, field
from typing import Optional, Union, Any
from dataclasses_json import config, DataClassJsonMixin

import base58
import pysui.version as ver
from pysui.sui.sui_pgql.pgql_sync_txn import SuiTransaction
from pysui.sui.sui_txn.transaction_builder import ProgrammableTransactionBuilder
import pysui.sui.sui_types.bcs as bcs
from pysui.sui.sui_pgql.pgql_wallet_deser import SuiBuilder

# pylint: disable=C0103:invalid-name


# Misc


@dataclass
class GasData(DataClassJsonMixin):
    """GasData repr."""

    budget: Optional[Union[str, int]] = None
    owner: Optional[str] = None
    payment: Optional[list[dict]] = None
    price: Optional[Union[str, int]] = None


# Inputs


@dataclass
class OIDStr:
    """Object ID for Unresolved Object."""

    objectId: str


@dataclass
class PBytes:
    """Pure Bytes."""

    pbytes: str = field(metadata=config(field_name="bytes"))


@dataclass
class PValue:
    """Unresolve Pure Value."""

    value: Any


@dataclass
class BaseObject:
    """Base Object Fields."""

    objectId: str
    digest: Optional[str] = None
    version: Optional[str] = None


@dataclass
class SObject:
    """Shared Object."""

    objectId: str
    initialSharedVersion: Optional[int] = None
    mutable: Optional[bool] = None

    def __post__(self):
        """Prefix with 0x"""
        self.objectId = (
            self.objectId if self.objectId.startswith("0x") else "0x" + self.objectId
        )


@dataclass
class ImmObject(DataClassJsonMixin):
    """Immutable or Owned Object."""

    ImmOrOwnedObject: BaseObject


@dataclass
class RecievingObject(DataClassJsonMixin):
    """Receiving Object."""

    Receiving: BaseObject


@dataclass
class ShrObject(DataClassJsonMixin):
    """Share Object Wrapper."""

    SharedObject: SObject


@dataclass
class UnResObj(DataClassJsonMixin):
    """Unresolved Object Wrapper."""

    UnresolvedObject: OIDStr


@dataclass
class Object(DataClassJsonMixin):
    """Object."""

    Object: Union[ImmObject, RecievingObject, ShrObject]


@dataclass
class PureArg(DataClassJsonMixin):
    """Pure Argument Wrapper."""

    Pure: PBytes


@dataclass
class UnResPureArg(DataClassJsonMixin):
    """Unresolved Pure Argument Wrapper."""

    UnresolvedPureArg: PValue


@dataclass
class CallArg(DataClassJsonMixin):
    """CallArg collection."""

    inputs: list[Union[Object, UnResObj, PureArg, UnResPureArg]]


# Arguments
@dataclass
class InputIndex(DataClassJsonMixin):
    """Input Argument"""

    Input: int


@dataclass
class ResultIndex(DataClassJsonMixin):
    """Input Argument"""

    Result: int


@dataclass
class NestedResultIndex(DataClassJsonMixin):
    """Input Argument"""

    NestedResult: list[int, int]


@dataclass
class GasUsed(DataClassJsonMixin):
    """GasCoin Argument."""

    GasCoin: bool


# Commands


@dataclass
class SplitPayload(DataClassJsonMixin):
    """SplitCoins."""

    coin: Union[GasUsed, InputIndex, ResultIndex, NestedResultIndex]
    amounts: list[Union[InputIndex, ResultIndex, NestedResultIndex]]


@dataclass
class SplitCommand(DataClassJsonMixin):
    """SplitCoins Command."""

    SplitCoins: SplitPayload


@dataclass
class MergePayload(DataClassJsonMixin):
    """MergeCoins."""

    destination: Union[InputIndex, ResultIndex, NestedResultIndex]
    sources: list[Union[InputIndex, ResultIndex, NestedResultIndex]]


@dataclass
class MergeCommand(DataClassJsonMixin):
    """MergeCoins Command."""

    MergeCoins: MergePayload


@dataclass
class TransferPayload(DataClassJsonMixin):
    """TransferObjects."""

    address: Union[InputIndex, ResultIndex, NestedResultIndex]
    objects: list[Union[InputIndex, ResultIndex, NestedResultIndex]]


@dataclass
class TransferCommand(DataClassJsonMixin):
    """TransferObjects Command."""

    TransferObjects: TransferPayload


@dataclass
class MakeVecPayload(DataClassJsonMixin):
    """MakeMoveVec."""

    elements: list[Union[InputIndex, ResultIndex, NestedResultIndex]]
    etype: list[str] = field(metadata=config(field_name="type"))


@dataclass
class MakeVecCommand(DataClassJsonMixin):
    """MakeMoveVec Command."""

    MakeMoveVec: MakeVecPayload


@dataclass
class PublishPayload(DataClassJsonMixin):
    """Publish."""

    modules: list[str]
    dependencies: list[str]


@dataclass
class PublishCommand(DataClassJsonMixin):
    """Publish Command."""

    Publish: PublishPayload


@dataclass
class UpgradePayload(DataClassJsonMixin):
    """Upgrade."""

    package: str
    ticket: Union[InputIndex, ResultIndex, NestedResultIndex]
    modules: list[str]
    dependencies: list[str]


@dataclass
class UpgradeCommand(DataClassJsonMixin):
    """Upgrade Command."""

    Upgrade: UpgradePayload


@dataclass
class MovePayload(DataClassJsonMixin):
    """MoveCall."""

    package: str
    module: str
    function: str
    arguments: list[Union[InputIndex, ResultIndex, NestedResultIndex]]
    typeArguments: list[str]


@dataclass
class MoveCallCommand(DataClassJsonMixin):
    """MoveCall Command."""

    MoveCall: MovePayload


@dataclass
class Command(DataClassJsonMixin):
    """Command collection."""

    commands: list[
        Union[
            MoveCallCommand,
            SplitCommand,
            MergeCommand,
            TransferCommand,
            MakeVecCommand,
            PublishCommand,
            UpgradeCommand,
        ]
    ]


def _serialize_inputs(
    builder: ProgrammableTransactionBuilder, unrealize_objs: bool = False
) -> list:
    """Serializes the transaction input."""
    call_args = CallArg([])
    for item, carg in builder.inputs.items():
        match item.enum_name:
            case "Pure":
                call_args.inputs.append(
                    PureArg(PBytes(base64.b64encode(bytearray(item.value)).decode()))
                )
            case "Object":
                objarg: bcs.ObjectArg = carg.value
                objref: bcs.ObjectReference = objarg.value
                obj_id = "0x" + bytearray(objref.ObjectID.Address).hex()
                if unrealize_objs:
                    call_args.inputs.append(UnResObj(UnresolvedObject=OIDStr(obj_id)))
                else:
                    # digest = base64.b64encode(objref.ObjectDigest.serialize()).decode()
                    match objarg.enum_name:
                        case "ImmOrOwnedObject":
                            digest = base58.b58encode(
                                bytearray(objref.ObjectDigest.Digest)
                            ).decode()
                            call_args.inputs.append(
                                Object(
                                    ImmObject(
                                        BaseObject(
                                            obj_id,
                                            digest,
                                            objref.SequenceNumber,
                                        )
                                    )
                                )
                            )
                        case "Receiving":
                            digest = base58.b58encode(
                                bytearray(objref.ObjectDigest.Digest)
                            ).decode()
                            call_args.inputs.append(
                                Object(
                                    RecievingObject(
                                        BaseObject(
                                            obj_id,
                                            digest,
                                            objref.SequenceNumber,
                                        )
                                    )
                                )
                            )
                        case "SharedObject":
                            objref: bcs.SharedObjectReference = objarg.value
                            call_args.inputs.append(
                                Object(
                                    ShrObject(
                                        SObject(
                                            obj_id,
                                            objref.SequenceNumber,
                                            objref.Mutable,
                                        )
                                    )
                                )
                            )
                        case _:
                            raise ValueError(
                                f"Unrecognized object type {objarg.enum_name}"
                            )
            case _:
                raise ValueError(f"Unrecognized input type {item.enum_name}")
    return call_args.inputs


def _argument_type(arg: bcs.Argument) -> Any:
    """Serializes Argument."""
    arg_type = None
    if arg.enum_name == "GasCoin":
        arg_type = GasUsed(True)
    elif arg.enum_name == "Input":
        arg_type = InputIndex(arg.value)
    elif arg.enum_name == "Result":
        arg_type = ResultIndex(arg.value)
    elif arg.enum_name == "NestedResult":
        arg_type = NestedResultIndex(list(arg.value))
    return arg_type


def _argument_types(args: list[bcs.Argument]) -> list[Any]:
    """Serializes a list of Arguments."""
    return [_argument_type(x) for x in args]


def _type_tags(ttags: list[bcs.TypeTag]) -> list[str]:
    """Serializes TypeTags."""
    tags: list[str] = []
    for tag in ttags:
        if isinstance(tag, bcs.OptionalTypeTag):
            if tag.value:
                tags.append(_type_tags([tag.value])[0])
        elif tag.enum_name == "Struct":
            strtag: bcs.StructTag = tag.value
            addy = (
                "0x"
                + bytearray(strtag.address.Address).hex()
                + "::"
                + strtag.module
                + "::"
                + strtag.name
            )
            if strtag.type_parameters:

                tags.append(
                    addy
                    + "<"
                    + ",".join([_type_tags([x])[0] for x in strtag.type_parameters])
                    + ">"
                )
            else:
                tags.append(addy)
        # TODO: Make recursive
        elif tag.enum_name == "Vector":
            pass
        else:
            tags.append(tag.enum_name)

    return tags


def _serialize_commands(builder: ProgrammableTransactionBuilder) -> list:
    """Serialize the transaction commands."""
    cmds = Command([])
    for cmd in builder.commands:
        match cmd.enum_name:
            case "MoveCall":
                mcall: bcs.ProgrammableMoveCall = cmd.value
                addy = "0x" + bytearray(mcall.Package.Address).hex()
                args = _argument_types(mcall.Arguments)
                tags = _type_tags(mcall.Type_Arguments)
                cmds.commands.append(
                    MoveCallCommand(
                        MovePayload(addy, mcall.Module, mcall.Function, args, tags)
                    )
                )
            case "SplitCoin":
                scoin: bcs.SplitCoin = cmd.value
                cmds.commands.append(
                    SplitCommand(
                        SplitPayload(
                            _argument_type(scoin.FromCoin),
                            _argument_types(scoin.Amount),
                        )
                    )
                )
            case "MergeCoins":
                mcoin: bcs.MergeCoins = cmd.value
                cmds.commands.append(
                    MergeCommand(
                        MergePayload(
                            _argument_type(mcoin.ToCoin),
                            _argument_types(mcoin.FromCoins),
                        )
                    )
                )
            case "TransferObjects":
                trf: bcs.TransferObjects = cmd.value
                cmds.commands.append(
                    TransferCommand(
                        TransferPayload(
                            _argument_type(trf.Address), _argument_types(trf.Objects)
                        )
                    )
                )
            case "MakeMoveVec":
                mmv: bcs.MakeMoveVec = cmd.value
                tags = _type_tags([mmv.TypeTag])
                cmds.commands.append(
                    MakeVecCommand(MakeVecPayload(_argument_types(mmv.Vector), tags))
                )
            case "Publish":
                pblsh: bcs.Publish = cmd.value
                modules = [base64.b64encode(bytes(x)).decode() for x in pblsh.Modules]
                dependencies = [
                    "0x" + bytearray(x.Address).hex() for x in pblsh.Dependents
                ]
                cmds.commands.append(
                    PublishCommand(PublishPayload(modules, dependencies))
                )
            case "Upgrade":
                upgrd: bcs.Upgrade = cmd.value
                modules = [base64.b64encode(bytes(x)).decode() for x in upgrd.Modules]
                dependencies = [
                    "0x" + bytearray(x.Address).hex() for x in upgrd.Dependents
                ]
                addy = "0x" + bytearray(upgrd.Package.Address).hex()
                cmds.commands.append(
                    UpgradeCommand(
                        UpgradePayload(
                            addy,
                            _argument_type(upgrd.UpgradeTicket),
                            modules,
                            dependencies,
                        )
                    )
                )

            case _:
                pass

    return cmds.commands


def serialize_to_wallet_standard(*, transaction: SuiTransaction, **kwargs) -> str:
    """Serialize pysui transaction to Sui wallet standard JSON.

    Keyword arguments:
        json_indent [int]: JSON indentation level, defaults to 2

        unrealize_objs [bool]: Only includes object IDs in inputs and not object references

        include_sender [bool]: Includes the transaction sender address in output

        epoch_expiration [int]: Specify the transaction expiration epoch

        gas_data [dict]: Specify transaction gas payment options...

            budget [str, int]: Specify the transaction budget, defaults to None

            owner [str]: Specifies the owner address paying for the transaction, defaults to None

            price [str, int]: Specify the gas cost, defaults to None

            payment list[dict]: A list of one or more object references, defaults to None

    :param transaction: Transaction to serialize
    :type transaction: SuiTransaction
    :param \**kwargs:
    :type \**kwargs: dict
    :return: JSON representation of transactiom
    :rtype: str
    """
    # Setup builder
    builder = SuiBuilder()
    builder.extensions.pysui.pysui_version = ver.__version__
    # Get Inputs
    builder.inputs = _serialize_inputs(
        transaction.builder, kwargs.get("unrealize_objs", False)
    )
    # Get Commands
    builder.commands = _serialize_commands(transaction.builder)
    # Include or repress sender
    builder.sender = (
        transaction.signer_block.sender if kwargs.get("include_sender") else None
    )
    # Include or repress gas_data
    gas_data: dict = (
        kwargs.get("gas_data") if isinstance(kwargs.get("gas_data"), dict) else None
    )
    if gas_data:
        builder.gas_data = GasData.from_dict(gas_data)
    # Epoch expiration
    builder.expiration = kwargs.get("epoch_expiration", None)
    return builder.to_json(indent=kwargs.get("json_indent", 2))
