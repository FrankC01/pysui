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

"""Move byte code common enums and types."""

from dataclasses import dataclass
from enum import IntEnum, IntFlag, auto

# pylint:disable=invalid-name
class OpCode(IntEnum):
    """Move byte code instructions."""

    Pop = 0x01
    Ret = 0x02
    BrTrue = 0x03
    BrFalse = 0x04
    Branch = 0x05
    LdU64 = 0x06
    LdConst = 0x07
    LdTrue = 0x08
    LdFalse = 0x09
    CopyLoc = 0x0A
    MoveLoc = 0x0B
    StLoc = 0x0C
    MutBorrowLoc = 0x0D
    ImmBorrowLoc = 0x0E
    MutBorrowField = 0x0F
    ImmBorrowField = 0x10
    Call = 0x11
    Pack = 0x12
    Unpack = 0x13
    ReadRef = 0x14
    WriteRef = 0x15
    Add = 0x16
    Sub = 0x17
    Mul = 0x18
    Mod = 0x19
    Div = 0x1A
    BitOr = 0x1B
    BitAnd = 0x1C
    Xor = 0x1D
    Or = 0x1E
    And = 0x1F
    Not = 0x20
    Eq = 0x21
    Neq = 0x22
    Lt = 0x23
    Gt = 0x24
    Le = 0x25
    Ge = 0x26
    Abort = 0x27
    Nop = 0x28
    Exists = 0x29
    MutBorrowGlobal = 0x2A
    ImmBorrowGlobal = 0x2B
    MoveFrom = 0x2C
    MoveTo = 0x2D
    FreezeRef = 0x2E
    Shl = 0x2F
    Shr = 0x30
    LdU8 = 0x31
    LdU128 = 0x32
    CastU8 = 0x33
    CastU64 = 0x34
    CastU128 = 0x35
    MutBorrowFieldGeneric = 0x36
    ImmBorrowFieldGeneric = 0x37
    CallGeneric = 0x38
    PackGeneric = 0x39
    UnpackGeneric = 0x3A
    ExistsGeneric = 0x3B
    MutBorrowGlobalGeneric = 0x3C
    ImmBorrowGlobalGeneric = 0x3D
    MoveFromGeneric = 0x3E
    MoveToGeneric = 0x3F

    VecPack = 0x40
    VecLen = 0x41
    VecImmBorrow = 0x42
    VecMutBorrow = 0x43
    VecPushBack = 0x44
    VecPopBack = 0x45
    VecUnpack = 0x46
    VecSwap = 0x47

    LdU16 = 0x48
    LdU32 = 0x49
    LdU256 = 0x4A
    CastU16 = 0x4B
    CastU32 = 0x4C
    CastU256 = 0x4D


class TableType(IntEnum):
    """Move byte code file tables."""

    ModuleHandles = 0x1
    StructHandles = 0x2
    FunctionHandles = 0x3
    FunctionInstance = 0x4
    Signatures = 0x5
    ConstantPool = 0x6
    Identifiers = 0x7
    AddressIdentifiers = 0x8
    StructDefinitions = 0xA
    StructDefInstances = 0xB
    FunctionDefinitions = 0xC
    FieldHandles = 0xD
    FieldInstances = 0xE
    FriendDeclarations = 0xF
    MetaData = 0x10


class Ability(IntFlag):
    """Move structure abilities."""

    Copy = auto()  # 0x1
    Drop = auto()  # 0x2
    Store = auto()  # 0x3
    Key = auto()  # 0x4


class SignatureType(IntEnum):
    """Move function parameter types."""

    boolean = 0x1
    u8 = 0x2
    u64 = 0x3
    u128 = 0x4
    Address = 0x5
    Reference = 0x6
    MutableReference = 0x7
    Struct = 0x8
    TypeParameter = 0x9
    Vector = 0xA
    StructInstantiation = 0xB
    Signer = 0xC
    u16 = 0xD
    u32 = 0xE
    u256 = 0xF


class Visibility(IntEnum):
    """."""

    Private = 0x0
    Public = 0x1
    Script = 0x2
    FriendPrivate = 0x3


class StructTag(IntEnum):
    """."""

    Native = 0x1
    HasFields = 0x2


@dataclass
class TableHeader:
    """."""

    kind: TableType
    offset: int
    length: int
    pos: int = 0


# pylint:enable=invalid-name


class Flags(int):
    """."""

    Native = 2
    Entry = 4

    def is_native(self) -> bool:
        """."""
        return self & self.Native

    def is_entry(self) -> bool:
        """."""
        return self & self.Entry


# pylint:disable=too-few-public-methods
class AbilitySet:
    """."""

    def __init__(self, ability_set: int):
        """."""
        self._ability_set = ability_set
        self._abilities: list[Ability] = []
        if ability_set & Ability.Key:
            self._abilities.append(Ability.Key)
        if ability_set & Ability.Copy:
            self._abilities.append(Ability.Copy)
        if ability_set & Ability.Drop:
            self._abilities.append(Ability.Drop)
        if ability_set & Ability.Store:
            self._abilities.append(Ability.Store)

    @property
    def as_list(self) -> list[Ability]:
        """."""
        return self._abilities

    @property
    def as_bitset(self) -> int:
        """."""
        return self._ability_set


# pylint:enable=too-few-public-methods
