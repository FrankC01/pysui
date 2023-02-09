#    Copyright (c) Frank V. Castellucci
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

"""Move byte code table contents."""

from dataclasses import dataclass, field
from typing import Any

from pysui.sui_move.model.common_types import AbilitySet, Flags, OpCode, SignatureType, StructTag, Visibility


@dataclass
class Signature:
    """."""

    sig_tokens: list


@dataclass
class Identifier:
    """."""

    identifier: str


@dataclass
class Address:
    """."""

    address: str


@dataclass
class Constant:
    """."""

    constant_type: SignatureType
    constant_length: int
    serialized_value: bytes


@dataclass
class ModuleHandle:
    """ModuleHandle represents a Module in the ModuleHanles byte code table.

    :ivar address: Index of address entry in Address table
    :ivar type address: int
    :ivar identifer: Index of ascii name in Identifier table
    :ivar type identifer: int
    """

    address_index: int
    identifier_index: int


@dataclass
class StructTypeParameter:
    """StructTypeParameter is a type parameter used in the StructureHandle.

    :ivar abilities: The type parameter constraints
    :ivar type abliities: AbilitySet
    :ivar is_phantom: Whether the parameter is declared as phantom.
    :ivar type is_phantom: bool
    """

    constraints: AbilitySet
    is_phantom: bool


@dataclass
class StructHandle:
    """StuctHandle represents a Structure in the StructureHanles byte code table.

    :ivar module: Index of Module entry in ModuleHandles table
    :ivar type module: int
    :ivar identifer: Index of ascii name in Identifier table
    :ivar type identifer: str
    :ivar abilities: abilities enum for this Structure
    :ivar type abliities: Ability
    :ivar type_parameters:
    """

    module_handle_index: int
    identifier_index: int
    abilities: AbilitySet
    type_parameters: list[StructTypeParameter]


@dataclass
class StructField:
    """."""

    identifier_index: int
    field_type: list = field(default_factory=list)


@dataclass
class StructDefinition:
    """."""

    struct_handle_index: int
    tag: StructTag
    field_count: int = 0
    fields: list[StructField] = field(default_factory=list)


@dataclass
class StructInstantiation:
    """."""

    struct_handle_index: int
    signature_index: int


@dataclass
class FieldHandle:
    """."""

    structure_definition_index: int
    field_index: int


@dataclass
class FieldInstantiation:
    """."""

    field_handle_index: int
    signature_index: list[int]


@dataclass
class FunctionHandle:
    """."""

    module_handle_index: int
    identifier_index: int
    parameters_signature_index: int
    returns_signature_index: int
    type_params: list = field(default_factory=list)


@dataclass
class FunctionDefinition:
    """."""

    function_handle_index: int
    visibility: Visibility
    flag: Flags
    aquires_global_resources: list[Any]
    locals_cnt: int = 0
    code_units: tuple[int, list[tuple[OpCode, Any]]] = field(default_factory=tuple)


@dataclass
class FunctionInstantiation:
    """."""

    function_handle_index: int
    signature_index: int


@dataclass
class Friend:
    """."""

    address_index: int
    identifier_index: int
