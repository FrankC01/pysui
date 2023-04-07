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
from typing import Optional, Set, Union
from functools import singledispatchmethod

from pysui.sui.sui_types import bcs
from pysui.sui.sui_txresults.single_tx import ObjectRead
from pysui.sui.sui_types.address import SuiAddress
from pysui.sui.sui_types.scalars import ObjectID, SuiInteger, SuiString

# Well known aliases
_SUI_PACKAGE_ID: bcs.Address = bcs.Address.from_str("0x2")
_SUI_PACKAGE_MODULE: str = "package"
_SUI_PACKAGE_MAKE_IMMUTABLE: str = "make_immutable"

# Command aliases


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
    def _(cls, arg: SuiInteger) -> list:
        """Convert int to minimal list of bytes."""
        return cls.pure(arg.value)

    @pure.register
    @classmethod
    def _(cls, arg: str) -> list:
        """Convert str to list of bytes."""
        base_list = list(bytearray(arg, encoding="utf-8"))
        return base_list

    @pure.register
    @classmethod
    def _(cls, arg: SuiString) -> list:
        """Convert int to minimal list of bytes."""
        return cls.pure(arg.value)

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
    def _(cls, arg: bcs.OptionalU64) -> list:
        """Convert SuiAddress to list of bytes."""
        return list(arg.serialize())

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
        self.objects_registry: Set[str] = set()

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
        self.objects_registry.add(key.value.to_address_str())
        return bcs.Argument("Input", out_index)

    # def obj(self, obj_arg: bcs.ObjectArg) -> bcs.Argument:
    #     """."""
    #     for index, (key, value) in enumerate(self.inputs.values()):
    #         # Check callarg (value) content with inbound
    #         carg_val = value.value
    #         # If collected is ObjectArg and we have equal values
    #         if value.index == 1 and carg_val == obj_arg:
    #             # If both are SharedObject
    #             if carg_val.index == 1 and obj_arg.index == 1:
    #                 pass

    def command(self, command_obj: bcs.Command) -> bcs.Argument:
        """."""
        out_index = len(self.commands)
        self.commands.append(command_obj)
        return bcs.Argument("Result", out_index)

    def make_move_vector(
        self,
        vtype: bcs.OptionalTypeTag,
        items: list[Union[bcs.Argument, bcs.BuilderArg, tuple[bcs.BuilderArg, bcs.ObjectArg]]],
    ) -> bcs.Argument:
        """Create a call to convert a list of items to a Sui 'vector' type."""
        # Sample first for type
        argrefs: list[bcs.Argument] = []
        for arg in items:
            if isinstance(arg, bcs.BuilderArg):
                argrefs.append(self.input_pure(arg))
            elif isinstance(arg, tuple):
                argrefs.append(self.input_obj(*arg))
            elif isinstance(arg, bcs.Argument):
                argrefs.append(arg)
            else:
                raise ValueError(f"Unknown arg in movecall {arg.__class__.__name__}")
        return self.command(bcs.Command("MakeMoveVec", bcs.MakeMoveVec(vtype, argrefs)))

    def move_call(
        self,
        *,
        target: bcs.Address,
        arguments: list[Union[bcs.Argument, tuple[bcs.BuilderArg, bcs.ObjectArg]]],
        type_arguments: list[bcs.TypeTag],
        module: str,
        function: str,
    ) -> bcs.Argument:
        """."""
        argrefs: list[bcs.Argument] = []
        for arg in arguments:
            if isinstance(arg, bcs.BuilderArg):
                argrefs.append(self.input_pure(arg))
            elif isinstance(arg, tuple):
                argrefs.append(self.input_obj(*arg))
            elif isinstance(arg, bcs.Argument) or isinstance(arg, bcs.OptionalU64):
                argrefs.append(arg)
            else:
                raise ValueError(f"Unknown arg in movecall {arg.__class__.__name__}")
        return self.command(
            bcs.Command(
                "MoveCall",
                bcs.ProgrammableMoveCall(target, module, function, type_arguments, argrefs),
            )
        )

    def split_coin(
        self,
        from_coin: Union[bcs.Argument, tuple[bcs.BuilderArg, bcs.ObjectArg]],
        amount: bcs.BuilderArg,
    ) -> bcs.Argument:
        """."""
        amount_arg = self.input_pure(amount)
        if isinstance(from_coin, bcs.Argument):
            coin_arg = from_coin
        else:
            coin_arg = self.input_obj(*from_coin)
        return self.command(
            bcs.Command(
                "SplitCoin",
                bcs.SplitCoin(coin_arg, [amount_arg]),
            )
        )

    def merge_coins(
        self,
        to_coin: Union[bcs.Argument, tuple[bcs.BuilderArg, bcs.ObjectArg]],
        from_coins: list[bcs.Argument, tuple[bcs.BuilderArg, bcs.ObjectArg]],
    ) -> bcs.Argument:
        """."""
        to_coin = to_coin if isinstance(to_coin, bcs.Argument) else self.input_obj(*to_coin)
        from_args: list[bcs.Argument] = []
        for fcoin in from_coins:
            from_args.append(fcoin if isinstance(fcoin, bcs.Argument) else self.input_obj(*fcoin))
        return self.command(bcs.Command("MergeCoins", bcs.MergeCoins(to_coin, from_args)))

    def transfer_objects(
        self,
        recipient: bcs.BuilderArg,
        object_ref: list[Union[bcs.Argument, tuple[bcs.BuilderArg, bcs.ObjectArg]]],
    ) -> bcs.Argument:
        """."""
        receiver_arg = self.input_pure(recipient)
        # object_ref = object_ref if isinstance(object_ref, bcs.Argument) else self.input_obj(*object_ref)
        from_args: list[bcs.Argument] = []
        for fcoin in object_ref:
            from_args.append(fcoin if isinstance(fcoin, bcs.Argument) else self.input_obj(*fcoin))
        return self.command(bcs.Command("TransferObjects", bcs.TransferObjects(from_args, receiver_arg)))

    def transfer_sui(
        self,
        recipient: bcs.BuilderArg,
        from_coin: Union[bcs.Argument, tuple[bcs.BuilderArg, bcs.ObjectArg]],
        amount: Optional[bcs.BuilderArg] = None,
    ) -> bcs.Argument:
        """."""
        reciever_arg = self.input_pure(recipient)
        if amount:
            coin_arg = self.split_coin(from_coin=from_coin, amount=amount)
        else:
            coin_arg = self.input_obj(*from_coin)
        return self.command(bcs.Command("TransferObjects", bcs.TransferObjects([coin_arg], reciever_arg)))

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
