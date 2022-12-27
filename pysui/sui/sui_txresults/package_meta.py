#    Copyright 2022 Frank V. Castellucci
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

"""Sui Package Meta Deta types."""

from dataclasses import dataclass, field
from typing import Any, Union
from dataclasses_json import DataClassJsonMixin, config

# Sui Normalized Data Types


class SuiMoveType:
    """SuiMoveType is a factory of generalized Normalized types."""

    @classmethod
    def resolve(cls, parm: Union[str, dict]) -> DataClassJsonMixin:
        """resolve Dispatches data loaders based on parm dictionary.

        :param parm: A dictionary containing a SuiMoveNormalizedType
        :type parm: dict
        :raises ValueError: Type signature is an unknown type
        :return: A pysui Sui data object
        :rtype: DataClassJsonMixin
        """
        if isinstance(parm, str):
            return SuiMoveScalarArgument.from_dict({"scalar_type": parm})
        match_key = list(parm.keys())[0]
        match match_key:
            case "Reference" | "MutableReference":
                parm["reference_type"] = match_key
                parm["reference_to"] = parm[match_key]
                parm.pop(match_key)
                result = SuiParameterReference.from_dict(parm)
            case "Struct":
                result = SuiParameterStruct.from_dict(parm[match_key])
            case "TypeParameter":
                result = SuiMoveParameterType.from_dict(parm)
            case "Vector":
                vmapper = {"vector_of": parm[match_key]}
                result = SuiMoveVector.from_dict(vmapper)
            case _:
                raise ValueError(f"Unknown handler for {match_key}")
        return result


@dataclass
class SuiMoveField(DataClassJsonMixin):
    """From getNormalized."""

    name: str
    type_: Union[str, dict]  # = field(default_factory=list)

    def __post_init__(self):
        """Post init processing for field_type."""
        if isinstance(self.type_, dict):
            self.type_ = SuiMoveType.resolve(self.type_)


@dataclass
class SuiMoveAbilitySet(DataClassJsonMixin):
    """From getNormalized."""

    abilities: list[str]

    def __post_init__(self):
        """Post init processing for field_type."""


@dataclass
class SuiMoveStructTypeParameter(DataClassJsonMixin):
    """From getNormalized."""

    constraints: SuiMoveAbilitySet
    is_phantom: bool = False


@dataclass
class SuiMoveStruct(DataClassJsonMixin):
    """From getNormalized."""

    abilities: SuiMoveAbilitySet
    fields: list[SuiMoveField]
    type_parameters: list[SuiMoveStructTypeParameter]

    def __post_init__(self):
        """Post init processing for type parameters."""

    @classmethod
    def ingest_data(cls, indata: dict) -> "SuiMoveStruct":
        """ingest_data Ingest results of direct call to `sui_getNormalizedMoveStruct`.

        :param indata: Dictionary containing structure defintion
        :type indata: dict
        :return: Instance of SuiMoveStruct
        :rtype: SuiMoveFunction
        """
        return SuiMoveStruct.from_dict(indata)


@dataclass
class SuiMoveVector(DataClassJsonMixin):
    """From getNormalized."""

    vector_of: Union[str, dict]  # list[str] = field(default_factory=list)

    def __post_init__(self):
        """Post init."""
        if isinstance(self.vector_of, dict):
            self.vector_of = SuiMoveType.resolve(self.vector_of)


@dataclass
class SuiMoveParameterType(DataClassJsonMixin):
    """From getNormalized."""

    type_parameters_index: int = field(metadata=config(field_name="TypeParameter"), default_factory=None)


@dataclass
class SuiParameterStruct(DataClassJsonMixin):
    """From getNormalize."""

    address: str
    module: str
    name: str
    type_arguments: list[Any]

    def __post_init__(self):
        """Post init."""
        if self.type_arguments:
            new_type_ars = []
            for type_arg in self.type_arguments:
                new_type_ars.append(SuiMoveType.resolve(type_arg))
            self.type_arguments = new_type_ars


@dataclass
class SuiParameterReference(DataClassJsonMixin):
    """From getNormalize."""

    reference_type: str
    reference_to: Union[str, dict]
    is_mutable: bool = False

    def __post_init__(self):
        """Post init."""
        self.is_mutable = self.reference_type == "MutableReference"
        if self.reference_to:
            if isinstance(self.reference_to, dict):
                self.reference_to = SuiMoveType.resolve(self.reference_to)


@dataclass
class SuiMoveScalarArgument(DataClassJsonMixin):
    """From getNormalized."""

    scalar_type: str


@dataclass
class SuiMoveFunctionArgumentTypes(DataClassJsonMixin):
    """From getNormalized."""

    arg_list: list[Union[str, dict[str, str]]]

    @classmethod
    def ingest_data(cls, indata: list) -> "SuiMoveFunctionArgumentTypes":
        """ingest_data Ingest results of calling `sui_getMoveFunctionArgTypes`.

        :param indata: list containing function argument types
        :type indata: list
        :return: Instance of SuiMoveFunctionArgumentTypes
        :rtype: SuiMoveFunctionArgumentTypes
        """
        return SuiMoveFunctionArgumentTypes.from_dict({"arg_list": indata})


@dataclass
class SuiMoveFunction(DataClassJsonMixin):
    """From getNormalized."""

    visibility: str
    is_entry: bool
    type_parameters: list[SuiMoveAbilitySet]
    parameters: list[Union[str, dict]]
    returns: list[Union[str, dict]] = field(metadata=config(field_name="return_"), default_factory=list)

    def __post_init__(self):
        """Post init processing for parameters and returns."""
        # Transition parameters
        new_parms = []
        for parm in self.parameters:
            new_parms.append(SuiMoveType.resolve(parm))
            # if isinstance(parm, dict):
            #     new_parms.append(SuiMoveType.resolve(parm))
            # else:
            #     new_parms.append(parm)
        self.parameters = new_parms
        # Transition returns
        new_rets = []
        for parm in self.returns:
            new_rets.append(SuiMoveType.resolve(parm))
            # if isinstance(parm, dict):
            #     new_rets.append(SuiMoveType.resolve(parm))
            # else:
            #     new_rets.append(parm)
        self.returns = new_rets

    @classmethod
    def ingest_data(cls, indata: dict) -> "SuiMoveFunction":
        """ingest_data Ingest results of calling `sui_getNormalizedMoveFunction`.

        :param indata: Dictionary containing function defintion
        :type indata: dict
        :return: Instance of SuiMoveFunction
        :rtype: SuiMoveFunction
        """
        return SuiMoveFunction.from_dict(indata)


# Module module information type
@dataclass
class SuiMoveModuleId(DataClassJsonMixin):
    """MoveModuleId Is a reference to a module's address and name.

    Found in a modules 'friends' list
    """

    address: str
    name: str


@dataclass
class SuiMoveModule(DataClassJsonMixin):
    """From getNormalized."""

    name: str
    address: str
    file_format_version: int
    friends: list[SuiMoveModuleId]
    structs: dict[str, SuiMoveStruct]
    exposed_functions: dict[str, SuiMoveFunction]

    def __post_init__(self):
        """Post init processing for parameters."""

    @classmethod
    def ingest_data(cls, indata: dict) -> "SuiMoveModule":
        """ingest_data Ingest results of calling `sui_getNormalizedMoveModule`.

        :param indata: Dictionary containing module defintion
        :type indata: dict
        :return: Instance of SuiMoveModule
        :rtype: SuiMoveModule
        """
        return SuiMoveModule.from_dict(indata)


@dataclass
class SuiMovePackage(DataClassJsonMixin):
    """From getNormalized."""

    modules: dict

    def __post_init__(self):
        """Post init processing for parameters."""
        self.modules = {x: SuiMoveModule.from_dict(y) for x, y in self.modules.items()}

    @classmethod
    def ingest_data(cls, indata: dict) -> "SuiMovePackage":
        """Ingest from external call."""
        # print(indata)
        new_mods = {}
        for mod_key, mod_value in indata.items():
            new_mods[mod_key] = mod_value
        indata["modules"] = new_mods
        return SuiMovePackage.from_dict(indata)
