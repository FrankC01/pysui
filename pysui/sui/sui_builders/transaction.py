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

"""Sui Builders: Transactions, TransactionData and TransactionKind."""


import base64
import binascii
from math import ceil
from typing import Union
from functools import singledispatchmethod

import canoser
from pysui.sui.sui_types import bcs
from pysui.sui.sui_txresults.single_tx import ObjectRead
from pysui.sui.sui_types.address import SuiAddress
from pysui.sui.sui_types.scalars import ObjectID


class BuilderArg(canoser.RustEnum):
    """."""

    _enums = [("Object", bcs.Address), ("Pure", [canoser.Uint8]), ("ForcedNonUniquePure", None)]

    def __hash__(self) -> int:
        """."""
        hself = hash(str(self))
        return hself


class PureInput:
    """."""

    @singledispatchmethod
    @classmethod
    def pure(cls, arg):
        """."""
        return f"I'm converting {arg} pure."

    @pure.register
    @classmethod
    def _(cls, arg: int) -> list:
        """."""
        ccount = ceil(arg.bit_length() / 8.0)
        return list(int.to_bytes(arg, ccount, "little"))

    @pure.register
    @classmethod
    def _(cls, arg: str) -> list:
        """."""
        base_list = list(bytearray(arg, encoding="utf-8"))
        # base_list.insert(0, len(base_list))
        return base_list

    @pure.register
    @classmethod
    def _(cls, arg: bytes) -> list:
        """."""
        base_list = list(arg)
        # base_list.insert(0, len(base_list))
        return base_list

    @pure.register
    @classmethod
    def _(cls, arg: ObjectID) -> list:
        """."""
        # We want the 32 bytes with a count
        return cls.pure(binascii.unhexlify(arg.value[2:]))

    @pure.register
    @classmethod
    def _(cls, arg: SuiAddress) -> list:
        """."""
        return PureInput.pure(binascii.unhexlify(arg.address[2:]))

    @pure.register
    @classmethod
    def _(cls, arg: list) -> list:
        """."""
        raise NotImplementedError("PureInput for lists")

    @classmethod
    def as_input(cls, args) -> BuilderArg:
        """."""
        return BuilderArg("Pure", cls.pure(args))


class ProgrammableTransaction:
    """."""

    def __init__(self) -> None:
        """."""

    @classmethod
    def inputs_and_commands(cls, inputs: list[bcs.CallArg], commands: list[bcs.Command]) -> "ProgrammableTransaction":
        """."""
        return cls()


class ProgrammableTransactionBuilder:
    """ProgrammableTransactionBuilder core transaction construction."""

    def __init__(self) -> None:
        """Builder initializer."""
        self.inputs: dict[BuilderArg, bcs.CallArg] = {}
        self.commands: list[bcs.Command] = []

    def finish(self) -> bcs.ProgrammableTransaction:
        """."""
        return bcs.ProgrammableTransaction(list(self.inputs.values()), self.commands.copy())

    def input_pure(self, key: BuilderArg) -> bcs.Argument:
        """."""
        out_index = len(self.inputs)
        if key.enum_name == "Pure":  # _key = hash(input)
            self.inputs[key] = bcs.CallArg(key.enum_name, key.value)
        else:
            raise ValueError(f"Expected Pure builder arg, found {key.enum_name}")
        return bcs.Argument("Input", out_index)

    def input_obj(self, key: BuilderArg, object_arg: bcs.ObjectArg) -> bcs.Argument:
        """."""
        out_index = len(self.inputs)
        if key.enum_name == "Object" and isinstance(object_arg, bcs.ObjectArg):  # _key = hash(input)
            self.inputs[key] = bcs.CallArg(key.enum_name, object_arg)
        else:
            raise ValueError(f"Expected Object builder arg and ObjectArg, found {key.enum_name} and {type(object_arg)}")
        return bcs.Argument("Input", out_index)

    def transfer_object(self, recipient: Union[str, ObjectID, SuiAddress], object_ref: ObjectRead = None) -> None:
        """."""
        # recipient is pure type ensconsed in CallArg
        if isinstance(recipient, str):
            recipient = ObjectID(recipient)
        reciever_arg = self.input_pure(PureInput.as_input(recipient))
        print(f"Receiver {reciever_arg}")
        obj_arg = self.input_obj(
            BuilderArg("Object", bcs.Address.from_str(object_ref.object_id)),
            bcs.ObjectArg("ImmOrOwnedObject", bcs.ObjectReference.from_generic_ref(object_ref)),
        )
        self.commands.append(bcs.Command("TransferObjects", bcs.TransferObjects([obj_arg], reciever_arg)))
        print(f"object {obj_arg}")


if __name__ == "__main__":
    pt = ProgrammableTransactionBuilder()

    fauxread = ObjectRead(
        version=7,
        object_id="0x0a5ea085e8067cc692a142c51a6436c5c8425c0a21f333fd33c6147b06eba20a",
        digest="5n6WNXDxWe3PLp3TQfSPms5p6EZ6M9SQu5TMFWbMAr3N",
        previous_transaction=None,
        object_type=None,
        owner={"AddressOwner": "0xf71335eb1acb64d771f9ace089940d15835115703a5d9530ce2a1b4cfffe8a5d"},
    )
    pt.transfer_object("0x09cf04e07b9d12bee10d809920d4e7c94dcbcce59d10f15a708fd78089d75cc0", fauxread)
    tx_kind = bcs.TransactionKind("ProgrammableTransaction", pt.finish())
    print(tx_kind.to_json(indent=2))
    ser_bytes = tx_kind.serialize()
    print(base64.b64encode(ser_bytes).decode())
    tx_kind2 = bcs.TransactionKind.deserialize(ser_bytes)
    print(tx_kind2.to_json(indent=2))
