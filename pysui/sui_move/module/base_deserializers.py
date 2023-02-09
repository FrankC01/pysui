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

"""Move module byte code raw deserializer."""

from pysui.sui_move.bin_reader.module_reader import ModuleReader
from pysui.sui_move.model.common_types import (
    Flags,
    OpCode,
    SignatureType,
    StructTag,
    TableHeader,
    AbilitySet,
    Visibility,
)
from pysui.sui_move.model.bytecode_tables import (
    Address,
    Constant,
    FieldHandle,
    FieldInstantiation,
    FunctionDefinition,
    FunctionHandle,
    FunctionInstantiation,
    Identifier,
    ModuleHandle,
    Signature,
    StructDefinition,
    StructField,
    StructHandle,
    StructInstantiation,
    StructTypeParameter,
    Friend,
)


def sig_walk(reader: ModuleReader) -> list:
    """sig_walk Walks data for signatures.

    :param reader: Byte stream reader
    :type reader: ModuleReader
    :raises NotImplementedError: If SignatureType not recognized
    :return: Signature list. First is always SignatureType
    :rtype: list
    """
    control = reader.read_as_int()
    match control:
        case (
            SignatureType.boolean
            | SignatureType.u8
            | SignatureType.u16
            | SignatureType.u32
            | SignatureType.u64
            | SignatureType.u128
            | SignatureType.u256
            | SignatureType.Address
            | SignatureType.Signer
        ):
            result = [SignatureType(control)]
        case SignatureType.Reference | SignatureType.MutableReference | SignatureType.Vector:
            result = [SignatureType(control), sig_walk(reader)]
        case SignatureType.Struct | SignatureType.TypeParameter:
            result = [SignatureType(control), reader.read_uleb128()]
        case SignatureType.StructInstantiation:
            result = [SignatureType(control), reader.read_uleb128()]
            subtok = reader.read_uleb128()
            for _ in range(subtok):
                result.append(sig_walk(reader))
        case _:
            raise NotImplementedError(SignatureType(control).name)
    return result


def read_op_code(reader: ModuleReader) -> tuple[OpCode, list]:
    """read_op_code Disassembles byte code instructions.

    :param reader: Stream reader
    :type reader: ModuleReader
    :return: Tuple of OpCode followed by zero or more operands
    :rtype: tuple[OpCode, list]
    """
    opcode = OpCode(reader.read_as_int())
    operand: list = []
    match opcode:
        case (
            OpCode.BrTrue
            | OpCode.BrFalse
            | OpCode.Branch
            | OpCode.LdConst
            | OpCode.CopyLoc
            | OpCode.MoveLoc
            | OpCode.StLoc
            | OpCode.MutBorrowLoc
            | OpCode.ImmBorrowLoc
            | OpCode.MutBorrowField
            | OpCode.ImmBorrowField
            | OpCode.Call
            | OpCode.Pack
            | OpCode.Unpack
            | OpCode.Exists
            | OpCode.MutBorrowGlobal
            | OpCode.ImmBorrowGlobal
            | OpCode.MoveFrom
            | OpCode.MoveTo
            | OpCode.MutBorrowFieldGeneric
            | OpCode.ImmBorrowFieldGeneric
            | OpCode.CallGeneric
            | OpCode.PackGeneric
            | OpCode.UnpackGeneric
            | OpCode.ExistsGeneric
            | OpCode.MutBorrowGlobalGeneric
            | OpCode.ImmBorrowGlobalGeneric
            | OpCode.MoveFromGeneric
            | OpCode.MoveToGeneric
            | OpCode.VecLen
            | OpCode.VecImmBorrow
            | OpCode.VecMutBorrow
            | OpCode.VecPushBack
            | OpCode.VecPopBack
            | OpCode.VecSwap
        ):
            operand.append(reader.read_uleb128())
        case OpCode.LdU8:
            operand.append(reader.read_as_int())
        case OpCode.LdU16:
            operand.append(reader.read_as_int(2))
        case OpCode.LdU32:
            operand.append(reader.read_as_int(4))
        case OpCode.LdU64:
            operand.append(reader.read_as_int(8))
        case OpCode.LdU128:
            operand.append(reader.read_as_int(16))
        case OpCode.LdU256:
            operand.append(reader.read_as_int(32))
        case OpCode.VecPack | OpCode.VecUnpack:
            ulong_s = reader.read_uleb128()
            element_len = reader.read_as_int(8)
            operand.extend([ulong_s, element_len])
        case _:
            pass
    return opcode, operand


def read_code_units(reader: ModuleReader) -> tuple[int, list[tuple[OpCode, list]]]:
    """read_code_units Disassembles a functions byte code instructions.

    :param reader: Stream reader
    :type reader: ModuleReader
    :return: Tuple of opcode count for function and list of instructions
    :rtype: tuple[int, list[tuple[OpCode, list]]]
    """
    op_codes_count = reader.read_uleb128()
    instructions = []
    for _ in range(op_codes_count):
        instructions.append(read_op_code(reader))
    return op_codes_count, instructions


def deserialize_signatures(
    table_header: TableHeader,
    reader: ModuleReader,
) -> list[Signature]:
    """deserialize_signatures builds collection of Signatures from it's table content.

    :param table_header: TableHeader for Signatures
    :type table_header: TableHeader
    :param reader: Stream reader
    :type reader: ModuleReader
    :return: All Signatures found in Signature content
    :rtype: list[Signature]
    """
    # Point reader to my content area
    _ = reader.position_content_for(table_header)
    max_pos = table_header.pos + table_header.length
    sigs: list[Signature] = []
    while reader.pos() < max_pos:
        sigcnt = reader.read_as_int()
        inner = []
        for _ in range(sigcnt):
            inner.append(sig_walk(reader))
        sigs.append(Signature(inner))
    return sigs


def deserialize_identifiers(
    table_header: TableHeader,
    reader: ModuleReader,
) -> list[Identifier]:
    """deserialize_identifiers builds collection of Identifiers from it's table content.

    :param table_header: TableHeader for Signatures
    :type table_header: TableHeader
    :param reader: Stream reader
    :type reader: ModuleReader
    :return: All Identifiers found in Identifier content
    :rtype: list[Identifier]
    """
    # Point reader to my content area
    _ = reader.position_content_for(table_header)
    max_pos = table_header.pos + table_header.length
    identities: list[Identifier] = []
    while reader.pos() < max_pos:
        identities.append(Identifier(str(reader.read_from_uleb_array(), "utf-8")))
    return identities


def deserialize_addresses(
    table_header: TableHeader,
    reader: ModuleReader,
) -> list[Address]:
    """deserialize_addresses builds collection of Addresses from it's table content.

    :param table_header: TableHeader for Signatures
    :type table_header: TableHeader
    :param reader: Stream reader
    :type reader: ModuleReader
    :return: All Addresses found in Address content
    :rtype: list[Address]
    """
    # Point reader to my content area
    _ = reader.position_content_for(table_header)
    max_pos = table_header.pos + table_header.length
    addresses: list[Address] = []
    address_len = 20
    while reader.pos() < max_pos:
        addresses.append(Address(reader.read(address_len).hex()))
    return addresses


def deserialize_constants(
    table_header: TableHeader,
    reader: ModuleReader,
) -> list[Constant]:
    """deserialize_constants builds collection of Constants from it's table content.

    :param table_header: TableHeader for Signatures
    :type table_header: TableHeader
    :param reader: Stream reader
    :type reader: ModuleReader
    :return: All Constants found in Address content
    :rtype: list[Constant]
    """
    # Point reader to my content area
    _ = reader.position_content_for(table_header)
    max_pos = table_header.pos + table_header.length
    constants: list[Constant] = []
    while reader.pos() < max_pos:
        sig_type = SignatureType(reader.read_as_int())
        alen = reader.read_as_int()
        val = reader.read(alen)
        match sig_type:
            case (
                SignatureType.boolean
                | SignatureType.u8
                | SignatureType.u16
                | SignatureType.u32
                | SignatureType.u64
                | SignatureType.u128
                | SignatureType.u256
            ):
                val = int.from_bytes(val, "little")
            case SignatureType.Vector:
                val = reader.read(list(val)[1])
            case _:
                raise NotImplementedError(f"{sig_type.name}")
        constants.append(Constant(sig_type, alen, val))
    return constants


def deserialize_module_handles(
    table_header: TableHeader,
    reader: ModuleReader,
) -> list[ModuleHandle]:
    """deserialize_module_handles builds collection of ModuleHandles from it's table content.

    :param table_header: TableHeader for ModuleHandles
    :type table_header: TableHeader
    :param reader: Stream reader
    :type reader: ModuleReader
    :return: All ModuleHandles found in ModuleHandle content
    :rtype: list[ModuleHandle]
    """
    # Point reader to my content area
    _ = reader.position_content_for(table_header)
    max_pos = table_header.pos + table_header.length
    modules: list[ModuleHandle] = []
    while reader.pos() < max_pos:
        modules.append(ModuleHandle(reader.read_uleb128(), reader.read_uleb128()))
    return modules


def deserialize_stuct_handles(
    table_header: TableHeader,
    reader: ModuleReader,
) -> list[StructHandle]:
    """deserialize_stuct_handles builds collection of StructHandles from it's table content.

    :param table_header: TableHeader for ModuleHandles
    :type table_header: TableHeader
    :param reader: Stream reader
    :type reader: ModuleReader
    :return: All StructHandles found in StructHandle content
    :rtype: list[StructHandle]
    """

    def type_parameters(sub_read: ModuleReader) -> StructTypeParameter:
        """."""
        return StructTypeParameter(AbilitySet(sub_read.read_as_int()), sub_read.read_as_bool())

    _ = reader.position_content_for(table_header)
    max_pos = table_header.pos + table_header.length
    structs: list[StructHandle] = []

    while reader.pos() < max_pos:
        structs.append(
            StructHandle(
                reader.read_uleb128(),
                reader.read_uleb128(),
                AbilitySet(reader.read_as_int()),
                reader.build_model_list(type_parameters),
            )
        )
    return structs


def deserialize_stuct_definition(
    table_header: TableHeader,
    reader: ModuleReader,
) -> list[StructDefinition]:
    """deserialize_stuct_definition builds collection of StructDefinition from it's table content.

    :param table_header: TableHeader for ModuleHandles
    :type table_header: TableHeader
    :param reader: Stream reader
    :type reader: ModuleReader
    :return: All StructDefinitions found in StructDefinition content
    :rtype: list[StructDefinition]
    """

    def field_parameters(sub_read: ModuleReader) -> StructField:
        """."""
        i_index = sub_read.read_uleb128()
        s_flds = sig_walk(sub_read)
        return StructField(i_index, s_flds)

    _ = reader.position_content_for(table_header)
    max_pos = table_header.pos + table_header.length
    structs: list[StructDefinition] = []

    while reader.pos() < max_pos:
        i_index = reader.read_uleb128()
        tag = StructTag(reader.read_as_int())
        s_fields = reader.build_model_list(field_parameters)
        structs.append(StructDefinition(i_index, tag, len(s_fields), s_fields))

    return structs


def deserialize_structure_instantiations(
    table_header: TableHeader,
    reader: ModuleReader,
) -> list[StructInstantiation]:
    """deserialize_structure_instantiations builds collection of StructInstantiation from it's table content.

    :param table_header: TableHeader for ModuleHandles
    :type table_header: TableHeader
    :param reader: Stream reader
    :type reader: ModuleReader
    :return: All StructInstantiation found in StructInstantiation content
    :rtype: list[StructInstantiation]
    """
    # Point reader to my content area
    _ = reader.position_content_for(table_header)
    max_pos = table_header.pos + table_header.length
    struct_inst: list[StructInstantiation] = []
    while reader.pos() < max_pos:
        struct_inst.append(StructInstantiation(reader.read_uleb128(), reader.read_uleb128()))
    return struct_inst


def deserialize_structure_field_handles(
    table_header: TableHeader,
    reader: ModuleReader,
) -> list[FieldHandle]:
    """deserialize_structure_field_handles builds collection of FieldHandles from it's table content.

    :param table_header: TableHeader for ModuleHandles
    :type table_header: TableHeader
    :param reader: Stream reader
    :type reader: ModuleReader
    :return: All FieldHandles found in FieldHandle content
    :rtype: list[FieldHandle]
    """
    # Point reader to my content area
    _ = reader.position_content_for(table_header)
    max_pos = table_header.pos + table_header.length
    field_handles: list[FieldHandle] = []
    while reader.pos() < max_pos:
        field_handles.append(FieldHandle(reader.read_uleb128(), reader.read_uleb128()))
    return field_handles


def deserialize_structure_field_instantiations(
    table_header: TableHeader,
    reader: ModuleReader,
) -> list[FieldInstantiation]:
    """deserialize_structure_field_instantiations builds collection of FieldInstantiations from it's table content.

    :param table_header: TableHeader for ModuleHandles
    :type table_header: TableHeader
    :param reader: Stream reader
    :type reader: ModuleReader
    :return: All FieldInstantiations found in FieldInstantiation content
    :rtype: list[FieldInstantiation]
    """
    # Point reader to my content area
    _ = reader.position_content_for(table_header)
    max_pos = table_header.pos + table_header.length
    field_inst: list[FieldHandle] = []
    while reader.pos() < max_pos:
        field_inst.append(FieldInstantiation(reader.read_uleb128(), reader.read_uleb128()))
    return field_inst


def deserialize_function_handles(
    table_header: TableHeader,
    reader: ModuleReader,
) -> list[FunctionHandle]:
    """deserialize_function_handles builds collection of FunctionHandles from it's table content.

    :param table_header: TableHeader for ModuleHandles
    :type table_header: TableHeader
    :param reader: Stream reader
    :type reader: ModuleReader
    :return: All FunctionHandles found in FunctionHandle content
    :rtype: list[FunctionHandle]
    """
    # Point reader to my content area
    _ = reader.position_content_for(table_header)
    max_pos = table_header.pos + table_header.length
    funcs: list[FunctionHandle] = []
    while reader.pos() < max_pos:
        funcs.append(
            FunctionHandle(
                reader.read_uleb128(),
                reader.read_uleb128(),
                reader.read_uleb128(),
                reader.read_uleb128(),
                reader.read_from_uleb_array(),
            )
        )
    return funcs


def deserialize_function_definition(
    table_header: TableHeader,
    reader: ModuleReader,
) -> list[FunctionDefinition]:
    """deserialize_function_definition builds collection of FunctionDefinition types from it's table content.

    :param table_header: TableHeader for ModuleHandles
    :type table_header: TableHeader
    :param reader: Stream reader
    :type reader: ModuleReader
    :return: All FunctionDefinitions found in StructDefinition content
    :rtype: list[FunctionDefinition]
    """
    _ = reader.position_content_for(table_header)
    max_pos = table_header.pos + table_header.length
    funcs: list[FunctionDefinition] = []

    while reader.pos() < max_pos:
        f_index = reader.read_uleb128()
        visibility = Visibility(reader.read_as_int())
        flag = Flags(reader.read_as_int())
        aquires = reader.read_from_uleb_array()
        if aquires:
            aquires = list(aquires)
        else:
            aquires = []
        if flag.is_native():
            funcs.append(FunctionDefinition(f_index, visibility, flag, aquires))
            continue
        funcs.append(
            FunctionDefinition(f_index, visibility, flag, aquires, reader.read_as_int(), read_code_units(reader))
        )

    return funcs


def deserialize_function_instantiations(
    table_header: TableHeader,
    reader: ModuleReader,
) -> list[FunctionInstantiation]:
    """_deserialize_module_handles builds collection of ModuleHandles from it's table content.

    :param table_header: TableHeader for ModuleHandles
    :type table_header: TableHeader
    :param reader: Stream reader
    :type reader: ModuleReader
    :return: All FunctionInstantiations found in FunctionInstantiation content
    :rtype: list[FunctionInstantiation]
    """
    # Point reader to my content area
    _ = reader.position_content_for(table_header)
    max_pos = table_header.pos + table_header.length
    func_inst: list[FunctionInstantiation] = []
    while reader.pos() < max_pos:
        func_inst.append(FunctionInstantiation(reader.read_uleb128(), reader.read_uleb128()))
    return func_inst


def deserialize_friends(
    table_header: TableHeader,
    reader: ModuleReader,
) -> list[Friend]:
    """deserialize_friends builds collection of Friend from it's table content.

    :param table_header: TableHeader for ModuleHandles
    :type table_header: TableHeader
    :param reader: Stream reader
    :type reader: ModuleReader
    :return: All Friends found in Friend content
    :rtype: list[Friend]
    """
    # Point reader to my content area
    _ = reader.position_content_for(table_header)
    max_pos = table_header.pos + table_header.length
    friends: list[Friend] = []
    while reader.pos() < max_pos:
        friends.append(Friend(reader.read_uleb128(), reader.read_uleb128()))
    return friends
