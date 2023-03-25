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

"""Sui low level Transaction Builder supports generation of TransactionKind."""


import binascii
from math import ceil
from typing import Union
from functools import singledispatchmethod

from pysui.sui.sui_types import bcs
from pysui.sui.sui_txresults.single_tx import ObjectRead
from pysui.sui.sui_types.address import SuiAddress
from pysui.sui.sui_types.scalars import ObjectID

_SUI_PACKAGE_ID: bcs.Address = bcs.Address.from_str("0x2")
_SUI_PACKAGE_MODULE: str = "package"
_SUI_PACKAGE_MAKE_IMMUTABLE: str = "make_immutable"


class PureInput:
    """."""

    @singledispatchmethod
    @classmethod
    def pure(cls, arg):
        """Template dispatch method."""
        return f"I'm converting {arg} pure."

    @pure.register
    @classmethod
    def _(cls, arg: int) -> list:
        """Convert int to minimal list of bytes."""
        ccount = ceil(arg.bit_length() / 8.0)
        return list(int.to_bytes(arg, ccount, "little"))

    @pure.register
    @classmethod
    def _(cls, arg: str) -> list:
        """Convert str to list of bytes."""
        base_list = list(bytearray(arg, encoding="utf-8"))
        return base_list

    @pure.register
    @classmethod
    def _(cls, arg: bytes) -> list:
        """Bytes to list."""
        base_list = list(arg)
        return base_list

    @pure.register
    @classmethod
    def _(cls, arg: ObjectID) -> list:
        """Convert ObjectID to list of bytes."""
        return cls.pure(binascii.unhexlify(arg.value[2:]))

    @pure.register
    @classmethod
    def _(cls, arg: SuiAddress) -> list:
        """Convert SuiAddress to list of bytes."""
        return PureInput.pure(binascii.unhexlify(arg.address[2:]))

    @pure.register
    @classmethod
    def _(cls, arg: list) -> list:
        """."""
        raise NotImplementedError("PureInput for lists")

    @classmethod
    def as_input(cls, args) -> bcs.BuilderArg:
        """Convert scalars and ObjectIDs to a Pure BuilderArg."""
        return bcs.BuilderArg("Pure", cls.pure(args))


class ProgrammableTransactionBuilder:
    """ProgrammableTransactionBuilder core transaction construction."""

    def __init__(self) -> None:
        """Builder initializer."""
        self.inputs: dict[bcs.BuilderArg, bcs.CallArg] = {}
        self.commands: list[bcs.Command] = []

    def finish(self) -> bcs.ProgrammableTransaction:
        """finish returns ProgrammableTransaction structure.

        :return: The resulting ProgrammableTransaction structure
        :rtype: bcs.ProgrammableTransaction
        """
        return bcs.ProgrammableTransaction(list(self.inputs.values()), self.commands.copy())

    def finish_for_inspect(self) -> bcs.TransactionKind:
        """finish_for_inspect returns TransactionKind structure.

        For inspection, serializing this return and converting to base64 is enough
        for sui_devInspectTransaction

        :return: The resulting TransactionKind structure
        :rtype: bcs.TransactionKind
        """
        return bcs.TransactionKind("ProgrammableTransaction", self.finish())

    def input_pure(self, key: bcs.BuilderArg) -> bcs.Argument:
        """."""
        out_index = len(self.inputs)
        if key.enum_name == "Pure":  # _key = hash(input)
            self.inputs[key] = bcs.CallArg(key.enum_name, key.value)
        else:
            raise ValueError(f"Expected Pure builder arg, found {key.enum_name}")
        return bcs.Argument("Input", out_index)

    def input_obj(self, key: bcs.BuilderArg, object_arg: bcs.ObjectArg) -> bcs.Argument:
        """."""
        out_index = len(self.inputs)
        if key.enum_name == "Object" and isinstance(object_arg, bcs.ObjectArg):  # _key = hash(input)
            self.inputs[key] = bcs.CallArg(key.enum_name, object_arg)
        else:
            raise ValueError(f"Expected Object builder arg and ObjectArg, found {key.enum_name} and {type(object_arg)}")
        return bcs.Argument("Input", out_index)

    def command(self, command_obj: bcs.Command) -> bcs.Argument:
        """."""
        out_index = len(self.commands)
        self.commands.append(command_obj)
        return bcs.Argument("Result", out_index)

    def split_coin(self, *, amount: int, from_coin: Union[bcs.Argument, ObjectRead] = None) -> bcs.Argument:
        """."""
        # coin_arg: bcs.Argument = None
        if from_coin:
            if isinstance(from_coin, ObjectRead):
                coin_arg = self.input_obj(
                    bcs.BuilderArg("Object", bcs.Address.from_str(from_coin.object_id)),
                    bcs.ObjectArg("ImmOrOwnedObject", bcs.ObjectReference.from_generic_ref(from_coin)),
                )
            elif isinstance(from_coin, bcs.Argument):
                if from_coin.enum_name == "GasCoin":
                    coin_arg = from_coin
        else:
            coin_arg = bcs.Argument("GasCoin")
        return self.command(
            bcs.Command(
                "SplitCoin",
                bcs.SplitCoin(coin_arg, self.input_pure(PureInput.as_input(bcs.U64.encode(amount)))),
            )
        )

    def transfer_object(self, *, recipient: Union[str, ObjectID, SuiAddress], object_ref: ObjectRead) -> bcs.Argument:
        """."""
        if isinstance(recipient, str):
            recipient = ObjectID(recipient)
        reciever_arg = self.input_pure(PureInput.as_input(recipient))
        obj_arg = self.input_obj(
            bcs.BuilderArg("Object", bcs.Address.from_str(object_ref.object_id)),
            bcs.ObjectArg("ImmOrOwnedObject", bcs.ObjectReference.from_generic_ref(object_ref)),
        )
        return self.command(bcs.Command("TransferObjects", bcs.TransferObjects([obj_arg], reciever_arg)))

    def transfer_sui(self, *, recipient: Union[str, ObjectID, SuiAddress], amount: int = None) -> bcs.Argument:
        """."""
        if isinstance(recipient, str):
            recipient = ObjectID(recipient)
        reciever_arg = self.input_pure(PureInput.as_input(recipient))
        coin_arg = None
        if amount:
            coin_arg = self.split_coin(amount=amount)
        else:
            coin_arg = bcs.Argument("GasCoin")
        return self.command(bcs.Command("TransferObjects", bcs.TransferObjects([coin_arg], reciever_arg)))

    def pay_all_sui(self, *, recipient: Union[str, ObjectID, SuiAddress]) -> bcs.Argument:
        """."""
        if isinstance(recipient, str):
            recipient = ObjectID(recipient)
        reciever_arg = self.input_pure(PureInput.as_input(recipient))
        return self.command(
            bcs.Command("TransferObjects", bcs.TransferObjects([bcs.Argument("GasCoin")], reciever_arg))
        )

    def pay_sui(self, *, recipients: list[Union[str, ObjectID, SuiAddress]], amounts: list[int]) -> bcs.Argument:
        """."""
        raise NotImplementedError("pay_sui")

    def pay(
        self, *, coins: list[ObjectRead], recipients: list[Union[str, ObjectID, SuiAddress]], amounts: list[int]
    ) -> bcs.Argument:
        """."""
        raise NotImplementedError("pay")

    def publish(self, *, modules: list[list[int]]) -> bcs.Argument:
        """."""
        return self.command(bcs.Command("Publish", bcs.Publish(modules)))

    def publish_immutable(self, *, modules: list[list[int]]) -> bcs.Argument:
        """."""
        cap = self.publish(modules=modules)
        return self.command(
            bcs.Command(
                "MoveCall",
                bcs.ProgrammableMoveCall(_SUI_PACKAGE_ID, _SUI_PACKAGE_MODULE, _SUI_PACKAGE_MAKE_IMMUTABLE, [], [cap]),
            )
        )


if __name__ == "__main__":
    pass
