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

"""Move module byte code deserializer."""

from dataclasses import dataclass, field
from typing import Union
from enum import IntEnum, auto
from pysui.sui_move.bin_reader.module_reader import ModuleReader
from pysui.sui_move.model.bytecode_tables import (
    Address,
    Constant,
    FunctionHandle,
    FunctionDefinition,
    FunctionInstantiation,
    Identifier,
    ModuleHandle,
    Signature,
    StructDefinition,
    StructHandle,
    StructInstantiation,
    FieldHandle,
    FieldInstantiation,
    Friend,
)
from pysui.sui_move.model.common_types import TableType
from pysui.sui_move.module.base_deserializers import (
    deserialize_addresses,
    deserialize_constants,
    deserialize_function_handles,
    deserialize_function_definition,
    deserialize_function_instantiations,
    deserialize_identifiers,
    deserialize_module_handles,
    deserialize_signatures,
    deserialize_structure_instantiations,
    deserialize_stuct_definition,
    deserialize_stuct_handles,
    deserialize_structure_field_handles,
    deserialize_structure_field_instantiations,
    deserialize_friends,
)


class Deserialize(IntEnum):
    """Deserialize degree of deserialization invariants."""

    MODULE_HANDLES = auto()
    MTS_HANDLES = auto()
    ALL = auto()


# pylint:disable=too-many-instance-attributes
@dataclass
class RawModuleContent:
    """RawModuleContent contains table collections in raw form.

    For each table type, the collection of types have immediate data or indexes
    in to other content table collections.

    :ivar magic: Contains the Move magic signature at beginning of byte code
    :ivar type magic: str

    :ivar version: The compiler version
    :ivar type version: int

    :ivar module_self: ModuleHandle index for self (i.e. the module itself)
    :ivar type module_self: int

    :ivar signatures: List of Signatures or empty list if none found
    :ivar type signatures: list[Signature]

    :ivar identifiers: List of Identifiers or empty list if none found
    :ivar type identifiers: list[Identifier]

    :ivar addresses: List of Addresses or empty list if none found
    :ivar type addresses: list[Address]

    :ivar constants: List of Constants or empty list if none found
    :ivar type constants: list[Constant]

    :ivar module_handles: List of ModuleHandle or empty list if none found
    :ivar type module_handles: list[ModuleHandle]

    :ivar structure_handles: List of StructHandles or empty list if none found
    :ivar type structure_handles: list[StructHandle]

    :ivar structure_definitions: List of StructDefinitions or empty list if none found
    :ivar type structure_definitions: list[StructDefinition]

    :ivar structure_instantiations: List of StructInstantiations or empty list if none found
    :ivar type structure_instantiations: list[StructInstantiation]

    :ivar field_handles: List of FieldHandles or empty list if none found
    :ivar type field_handles: list[FieldHandle]

    :ivar field_instantiations: List of FieldInstantiations or empty list if none found
    :ivar type field_instantiations: list[FieldInstantiation]

    :ivar function_handles: List of FunctionHandles or empty list if none found
    :ivar type function_handles: list[FunctionHandle]

    :ivar function_definitions: List of FunctionDefinition or empty list if none found
    :ivar type function_definitions: list[FunctionDefinition]

    :ivar function_instantiations: List of FunctionInstantiation or empty list if none found
    :ivar type function_instantiations: list[FunctionInstantiation]

    :ivar friends: List of Friends or empty list if none found
    :ivar type friends: list[Friend]
    """

    magic: str
    version: int
    module_self: int
    signatures: list[Signature] = field(default_factory=list)
    identifiers: list[Identifier] = field(default_factory=list)
    addresses: list[Address] = field(default_factory=list)
    constants: list[Constant] = field(default_factory=list)
    module_handles: list[ModuleHandle] = field(default_factory=list)
    structure_handles: list[StructHandle] = field(default_factory=list)
    structure_definitions: list[StructDefinition] = field(default_factory=list)
    structure_instantiations: list[StructInstantiation] = field(default_factory=list)
    field_handles: list[FieldHandle] = field(default_factory=list)
    field_instantiations: list[FieldInstantiation] = field(default_factory=list)
    function_handles: list[FunctionHandle] = field(default_factory=list)
    function_definitions: list[FunctionDefinition] = field(default_factory=list)
    function_instantiations: list[FunctionInstantiation] = field(default_factory=list)
    friends: list[Friend] = field(default_factory=list)


# pylint:enable=too-many-instance-attributes

_DESERIALIZE_JUMP: dict = {
    TableType.ModuleHandles: (deserialize_module_handles, "module_handles"),
    TableType.StructHandles: (deserialize_stuct_handles, "structure_handles"),
    TableType.FunctionHandles: (deserialize_function_handles, "function_handles"),
    TableType.FunctionInstance: (deserialize_function_instantiations, "function_instantiations"),
    TableType.Signatures: (deserialize_signatures, "signatures"),
    TableType.ConstantPool: (deserialize_constants, "constants"),
    TableType.Identifiers: (deserialize_identifiers, "identifiers"),
    TableType.AddressIdentifiers: (deserialize_addresses, "addresses"),
    TableType.StructDefinitions: (deserialize_stuct_definition, "structure_definitions"),
    TableType.StructDefInstances: (deserialize_structure_instantiations, "structure_instantiations"),
    TableType.FunctionDefinitions: (deserialize_function_definition, "function_definitions"),
    TableType.FieldHandles: (deserialize_structure_field_handles, "field_handles"),
    TableType.FieldInstances: (deserialize_structure_field_instantiations, "field_instantiations"),
    TableType.FriendDeclarations: (deserialize_friends, "friends"),
    TableType.MetaData: (None, None),
}


def _deserialize_raw_type(reader: ModuleReader, table_type: TableType, collector: RawModuleContent) -> None:
    """_deserialize_raw_type invokes the deserialization handler for table_type.

    :param reader: Byte reader
    :type reader: ModuleReader
    :param table_type: Identifies the table type to deserialize
    :type table_type: TableType
    :param collector: Inventory of tables deserialized
    :type collector: RawModuleContent
    :raises ValueError: If table_type is not a valid one
    """
    if table_type in _DESERIALIZE_JUMP:
        des_fn, att = _DESERIALIZE_JUMP[table_type]
        setattr(collector, att, reader.build_content_for(table_type, des_fn))
    else:
        raise ValueError(f"Uknown table type key {table_type.name}")


def deserialize(reader: ModuleReader, form: Deserialize) -> Union[RawModuleContent, Exception]:
    """deserialize decomposes a move compiled module file into constituent table parts.

    :param reader: Byte reader
    :type reader: ModuleReader
    :param form: Granularity of tables to deserialize to
    :type form: Deserialize
    :raises ValueError: If there is no module_handles in the move file
    :return: Itemized table layout
    :rtype: Union[RawModuleContent, Exception]
    """
    if reader.has_table(TableType.ModuleHandles):
        contents = RawModuleContent(reader.MAGIC_WORD, reader.version, reader.self_index)
        match form:
            case Deserialize.MODULE_HANDLES:
                _deserialize_raw_type(reader, TableType.AddressIdentifiers, contents)
                _deserialize_raw_type(reader, TableType.Identifiers, contents)
                _deserialize_raw_type(reader, TableType.ModuleHandles, contents)
            case Deserialize.MTS_HANDLES:
                _deserialize_raw_type(reader, TableType.AddressIdentifiers, contents)
                _deserialize_raw_type(reader, TableType.Identifiers, contents)
                _deserialize_raw_type(reader, TableType.ModuleHandles, contents)
                _deserialize_raw_type(reader, TableType.FunctionHandles, contents)
                _deserialize_raw_type(reader, TableType.StructHandles, contents)
            case Deserialize.ALL:
                for tt_key in reader.cross_reference.keys():
                    _deserialize_raw_type(reader, tt_key, contents)

        return contents

    raise ValueError("No module byte code defined in file")


def from_file(module: str, form: Deserialize = Deserialize.ALL) -> Union[RawModuleContent, Exception]:
    """from_file Deserialize the content of a module from file system.

    :param module: The sui module file path
    :type module: str
    :param form: Defines how many tables to walk from module, defaults to Deserialize.ALL
    :type form: Deserialize, optional
    :return: Container of deserialized tables
    :rtype: Union[RawModuleContent, Exception]
    """
    return deserialize(ModuleReader.read_from_file(module), form)


def from_base64(in_base64: str, form: Deserialize = Deserialize.ALL) -> Union[RawModuleContent, Exception]:
    """from_base64 Deserialize the content of a module base64 representation.

    :param in_base64: The sui module base64 string
    :type in_base64: str
    :param form: Defines how many tables to walk from module, defaults to Deserialize.ALL
    :type form: Deserialize, optional
    :return: Container of deserialized tables
    :rtype: Union[RawModuleContent, Exception]
    """
    return deserialize(ModuleReader.read_from_base64(in_base64), form)


if __name__ == "__main__":
    content = from_file("~/frankc01/sui-track/build/SuiTrack/bytecode_modules/base.mv")
    print(content.version)
