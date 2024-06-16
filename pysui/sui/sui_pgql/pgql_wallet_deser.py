#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Pysui DeSertializtion from Sui Wallet JSON standard to dataclasses."""

from datetime import datetime
from dataclasses import dataclass, field
from typing import Any, Optional, Union
from dataclasses_json import dataclass_json, LetterCase, config
from marshmallow import fields


# Pylint false positive
# pylint: disable=E1101:no-member


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class SuiObjectCallArg:
    """Object Argument."""

    ref_type: str
    object_id: str
    digest: Optional[str] = None
    version: Optional[str] = None
    initial_shared_version: Optional[int] = None
    mutable: Optional[bool] = None


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class SuiUnresolvedObjectCallArg:
    """Unresolved Object Argument."""

    object_id: str


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class SuiPureCallArg:
    """Pure Argument."""

    pure_bytes: str


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class SuiUnresolvedPureCallArg:
    """Unresolved Pure Argument."""

    value: Any


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class SuiGasCoinArg:
    """GasCoin as argument."""

    used: Optional[bool] = True


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class SuiCallArgIndex:
    """Input index as argument."""

    index: int


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class SuiCmdResultIndex:
    """Command index as argument."""

    result: int


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class SuiCmdNestedResultIndex:
    """GasCoin as argument."""

    nested_result: list[list]


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class SuiGasData:
    """GasData repr."""

    budget: Optional[Union[str, int]]
    owner: Optional[str]
    payment: Optional[list[dict]]
    price: Optional[Union[str, int]]

    def __post_init__(self):
        """."""
        if self.payment:
            pay_objs = []
            for pay in self.payment:
                pay["ref_type"] = "ImmOrOwnedObject"
                pay_objs.append(SuiObjectCallArg.from_dict(pay))
            self.payment = pay_objs


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class SuiMoveCall:
    """MoveCall repr."""

    package: str
    module: str
    function: str
    arguments: list
    type_arguments: list[str]
    command: Optional[str] = field(default="MoveCall")

    def __post_init__(self):
        """Result CallArgs to type."""
        self.arguments = CommandInputFactory.inputs_from_list(self.arguments)


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class SuiSplitCoins:
    """SplitCoins repr."""

    amounts: list
    coin: dict
    command: Optional[str] = field(default="SplitCoins")

    def __post_init__(self):
        """Result CallArgs to type."""
        self.amounts = CommandInputFactory.inputs_from_list(self.amounts)
        self.coin = CommandInputFactory.inputs_from_dict(self.coin)


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class SuiTransferObjects:
    """TransferObjects repr."""

    objects: list
    address: dict
    command: Optional[str] = field(default="TransferObjects")

    def __post_init__(self):
        """Result CallArgs to type."""
        self.objects = CommandInputFactory.inputs_from_list(self.objects)
        self.address = CommandInputFactory.inputs_from_dict(self.address)


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class SuiMergeCoins:
    """MergeCoins repr."""

    sources: list
    destination: Optional[Union[None, str]]
    command: Optional[str] = field(default="MergeCoins")

    def __post_init__(self):
        """Result CallArgs to type."""
        self.sources = CommandInputFactory.inputs_from_list(self.sources)
        self.destination = CommandInputFactory.inputs_from_dict(self.destination)


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class SuiMakeMoveVec:
    """MakeMoveVec repr."""

    elements: list
    vec_type: Optional[Union[None, str]] = field(metadata=config(field_name="type"))
    command: Optional[str] = field(default="MakeMoveVec")

    def __post_init__(self):
        """Result CallArgs to type."""
        self.elements = CommandInputFactory.inputs_from_list(self.elements)


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class SuiPublish:
    """Publish repr."""

    modules: list[str]
    dependencies: list[str]
    command: Optional[str] = field(default="Publish")


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class SuiUpgrade:
    """Upgrade repr."""

    modules: list[str]
    dependencies: list[str]
    package: str
    ticket: dict
    command: Optional[str] = field(default="Upgrade")

    def __post_init__(self):
        """Result CallArgs to type."""
        self.ticket = CommandInputFactory.inputs_from_dict(self.ticket)


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class SuiIntent:
    """$Intent repr."""

    name: str
    inputs: list
    data: dict


# pylint: disable=too-few-public-methods


class CommandInputFactory:
    """Process Call Arg Inputs."""

    @classmethod
    def inputs_from_list(cls, input_data: list) -> list[Any]:
        """Iterate through list and resolve inputs."""
        if input_data:
            results = []
            for element in input_data:
                key, value = element.popitem()
                match key:
                    case "GasCoin":
                        results.append(SuiGasCoinArg())
                    case "Input":
                        results.append(SuiCallArgIndex(value))
                    case "Result":
                        results.append(SuiCmdResultIndex(value))
                    case "NestedResult":
                        results.append(SuiCmdNestedResultIndex(value))
            return results
        return input_data

    @classmethod
    def inputs_from_dict(cls, input_data: dict) -> Any:
        """Resolve single input."""

        if input_data:
            return cls.inputs_from_list([input_data])[0]
        return input_data


class CallArgFactory:
    """Process Call Arg Inputs."""

    @classmethod
    def callargs_from_list(cls, inputs: list) -> list[Any]:
        """Iterate through list and resolve call arg structures."""
        if inputs:
            results: list = []
            for arg in inputs:
                key, value = arg.popitem()
                match key:
                    case "Object":
                        okey, ovalue = value.popitem()
                        ovalue["ref_type"] = okey
                        results.append(SuiObjectCallArg.from_dict(ovalue))
                    case "Pure":
                        faux_pure: dict = {}
                        faux_pure["pure_bytes"] = value["bytes"]
                        results.append(SuiPureCallArg.from_dict(faux_pure))
                    case "UnresolvedObject":
                        results.append(SuiUnresolvedObjectCallArg.from_dict(value))
                    case "UnresolvedPure":
                        results.append(SuiUnresolvedPureCallArg.from_dict(value))
            return results
        return []


class CommandFactory:
    """Process Commands."""

    @classmethod
    def commands_from_list(cls, inputs: list) -> list[Any]:
        """Iterate through list and resolve command structures."""
        if inputs:
            results: list = []
            for arg in inputs:
                key, value = arg.popitem()
                match key:
                    case "MoveCall":
                        results.append(SuiMoveCall.from_dict(value))
                    case "SplitCoins":
                        results.append(SuiSplitCoins.from_dict(value))
                    case "MergeCoins":
                        results.append(SuiMergeCoins.from_dict(value))
                    case "TransferObjects":
                        results.append(SuiTransferObjects.from_dict(value))
                    case "MakeMoveVec":
                        results.append(SuiMakeMoveVec.from_dict(value))
                    case "Publish":
                        results.append(SuiPublish.from_dict(value))
                    case "Upgrade":
                        results.append(SuiUpgrade.from_dict(value))
                    case "$Intent":
                        results.append(SuiIntent.from_dict(value))
            return results
        return inputs


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class PysuiData:
    """Pysui data for ixchg."""

    pysui_version: str
    xchng_version: int
    sdk_source: str = "pysui_sdk"
    creation_date: datetime = field(
        default=datetime.now(),
        metadata=config(
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,
            mm_field=fields.DateTime(format="iso"),
        ),
    )


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class PysuiExtension:
    """Pysui extension for ixchg."""

    pysui: PysuiData


def null_gas_data() -> SuiGasData:
    """."""
    return SuiGasData(budget=None, owner=None, payment=[], price=None)


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class SuiBuilder:
    """Sui Transaciton Block Wallet Standard."""

    sender: Optional[str] = None
    expiration: Optional[str] = None
    version: int = field(default=2)
    gas_data: Optional[SuiGasData] = field(default_factory=null_gas_data)
    inputs: Optional[list[dict]] = field(default_factory=list)
    commands: Optional[list[dict]] = field(default_factory=list)
    extensions: Optional[dict] = field(default_factory=dict)

    def __post_init__(self):
        """."""
        self.inputs = CallArgFactory.callargs_from_list(self.inputs)
        self.commands = CommandFactory.commands_from_list(self.commands)
        if not self.extensions:
            self.extensions = PysuiExtension(
                pysui=PysuiData(pysui_version="", xchng_version=1)
            )
        elif self.extensions.get("pysui"):
            expysuival = self.extensions.get("pysui")
            self.extensions["pysui"] = PysuiExtension.from_dict({"pysui": expysuival})


def deserialize_from_wallet_standard(*, wallet_json: str) -> SuiBuilder:
    """Deserialize from the Sui Wallet Transaction Standard to dataclasses."""
    return SuiBuilder.from_json(wallet_json)
