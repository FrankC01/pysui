#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-
# pylint: disable=too-many-instance-attributes

"""Sui low level Transaction Builder supports generation of TransactionKind."""

import logging
import binascii
from math import ceil
from typing import Optional, Set, Union
from functools import singledispatchmethod

from deprecated.sphinx import versionchanged, versionadded
from pysui.sui.sui_txresults.single_tx import TransactionConstraints

from pysui.sui.sui_types import bcs
from pysui.sui.sui_types.address import SuiAddress
from pysui.sui.sui_types.scalars import (
    ObjectID,
    SuiBoolean,
    SuiInteger,
    SuiString,
    SuiU128,
    SuiU16,
    SuiU256,
    SuiU32,
    SuiU64,
    SuiU8,
)
from pysui.sui.sui_utils import serialize_uint32_as_uleb128

# Well known aliases
_SUI_PACKAGE_ID: bcs.Address = bcs.Address.from_str("0x2")
_SUI_PACKAGE_MODULE: str = "package"
_SUI_PACAKGE_AUTHORIZE_UPGRADE: str = "authorize_upgrade"
_SUI_PACAKGE_COMMIt_UPGRADE: str = "commit_upgrade"

# Standard library logging setup
logger = logging.getLogger()


@versionchanged(version="0.17.0", reason="Support bool arguments")
@versionchanged(version="0.18.0", reason="Support for lists and unsigned ints")
class PureInput:
    """Pure inputs processing."""

    @singledispatchmethod
    @classmethod
    def pure(cls, arg):
        """Template dispatch method."""
        return f"I'm converting {arg} pure."

    @pure.register
    @classmethod
    def _(cls, arg: bool) -> list:
        """."""
        logger.debug(f"bool->pure {arg}")
        return list(int(arg is True).to_bytes(1, "little"))

    @pure.register
    @classmethod
    def _(cls, arg: SuiBoolean) -> list:
        """."""
        return cls.pure(arg.value)

    @pure.register
    @classmethod
    def _(cls, arg: int) -> list:
        """Convert int to minimal list of bytes."""
        logger.debug(f"int->pure {arg}")
        ccount = ceil(arg.bit_length() / 8.0)
        return list(int.to_bytes(arg, ccount, "little"))

    @pure.register
    @classmethod
    def _(cls, arg: bcs.Optional) -> list:
        """Convert OptionalU8 to list of bytes."""
        logger.debug(f"Optional {arg}")
        return list(arg.serialize())

    @pure.register
    @classmethod
    def _(cls, arg: SuiInteger) -> list:
        """Convert int to minimal list of bytes."""
        return cls.pure(arg.value)

    @pure.register
    @classmethod
    def _(cls, arg: SuiU8) -> list:
        """Convert unsigned int to bytes."""
        logger.debug(f"u8->pure {arg.value}")
        return list(arg.to_bytes())

    @pure.register
    @classmethod
    def _(cls, arg: bcs.OptionalU8) -> list:
        """Convert OptionalU8 to list of bytes."""
        logger.debug(f"Optional<u8> {arg}")
        return list(arg.serialize())

    @pure.register
    @classmethod
    def _(cls, arg: SuiU16) -> list:
        """Convert unsigned int to bytes."""
        logger.debug(f"u16->pure {arg.value}")
        return list(arg.to_bytes())

    @pure.register
    @classmethod
    def _(cls, arg: bcs.OptionalU16) -> list:
        """Convert OptionalU16 to list of bytes."""
        logger.debug(f"Optional<u16> {arg}")
        return list(arg.serialize())

    @pure.register
    @classmethod
    def _(cls, arg: SuiU32) -> list:
        """Convert unsigned int to bytes."""
        logger.debug(f"u32->pure {arg.value}")
        return list(arg.to_bytes())

    @pure.register
    @classmethod
    def _(cls, arg: bcs.OptionalU32) -> list:
        """Convert OptionalU32 to list of bytes."""
        logger.debug(f"Optional<u32> {arg}")
        return list(arg.serialize())

    @pure.register
    @classmethod
    def _(cls, arg: SuiU64) -> list:
        """Convert unsigned int to bytes."""
        logger.debug(f"u64->pure {arg.value}")
        return list(arg.to_bytes())

    @pure.register
    @classmethod
    def _(cls, arg: bcs.OptionalU64) -> list:
        """Convert OptionalU64 to list of bytes."""
        logger.debug(f"Optional<u64> {arg}")
        return list(arg.serialize())

    @pure.register
    @classmethod
    def _(cls, arg: SuiU128) -> list:
        """Convert unsigned int to bytes."""
        logger.debug(f"u128->pure {arg.value}")
        return list(arg.to_bytes())

    @pure.register
    @classmethod
    def _(cls, arg: bcs.OptionalU128) -> list:
        """Convert OptionalU128 to list of bytes."""
        logger.debug(f"Optional<u128> {arg}")
        return list(arg.serialize())

    @pure.register
    @classmethod
    def _(cls, arg: SuiU256) -> list:
        """Convert unsigned int to bytes."""
        logger.debug(f"u256->pure {arg.value}")
        return list(arg.to_bytes())

    @pure.register
    @classmethod
    def _(cls, arg: bcs.OptionalU256) -> list:
        """Convert OptionalU256 to list of bytes."""
        logger.debug(f"Optional<u256> {arg}")
        return list(arg.serialize())

    @pure.register
    @classmethod
    def _(cls, arg: str) -> list:
        """Convert str to list of bytes."""
        logger.debug(f"str->pure {arg}")
        byte_list = list(bytearray(arg, encoding="utf-8"))
        length_prefix = list(bytearray(serialize_uint32_as_uleb128(len(byte_list))))
        return length_prefix + byte_list

    @pure.register
    @classmethod
    def _(cls, arg: SuiString) -> list:
        """Convert int to minimal list of bytes."""
        return cls.pure(arg.value)

    @pure.register
    @classmethod
    def _(cls, arg: bytes) -> list:
        """Bytes to list."""
        logger.debug(f"bytes->pure {arg}")
        base_list = list(arg)
        return base_list

    @pure.register
    @classmethod
    def _(cls, arg: ObjectID) -> list:
        """Convert ObjectID to list of bytes."""
        logger.debug(f"ObjectID->pure {arg.value}")
        return cls.pure(binascii.unhexlify(arg.value[2:]))

    @pure.register
    @classmethod
    def _(cls, arg: SuiAddress) -> list:
        """Convert SuiAddress to list of bytes."""
        logger.debug(f"SuiAddress->pure {arg.address}")
        addy = bcs.Address.from_sui_address(arg)
        return list(addy.serialize())

    @pure.register
    @classmethod
    def _(cls, arg: bcs.Address) -> list:
        """Convert bcs.Address to list of bytes."""
        logger.debug(f"bcs.Address->pure {arg.to_json()}")
        return list(arg.serialize())

    @pure.register
    @classmethod
    def _(cls, arg: bcs.Digest) -> list:
        """Convert bcs,Digest to list of bytes."""
        logger.debug(f"bcs.Digest->pure {arg.to_json()}")
        return list(arg.serialize())

    @pure.register
    @classmethod
    def _(cls, arg: bcs.Variable) -> list:
        """Convert bcs,Variable to list of bytes."""
        logger.debug(f"bcs.Variable->pure {arg.to_json()}")
        return list(arg.serialize())

    @pure.register
    @classmethod
    def _(cls, arg: list) -> list:
        """."""
        logger.debug(f"list->pure {arg}")
        stage_list = [PureInput.pure(x) for x in arg]
        res_list = list(serialize_uint32_as_uleb128(len(stage_list)))
        for stage_pure in stage_list:
            res_list.extend(stage_pure)
        return res_list

    @classmethod
    def as_input(cls, args) -> bcs.BuilderArg:
        """Convert scalars and ObjectIDs to a Pure BuilderArg."""
        return bcs.BuilderArg("Pure", cls.pure(args))


@versionchanged(version="0.31.0", reason="Added command type frequency")
class ProgrammableTransactionBuilder:
    """ProgrammableTransactionBuilder core transaction construction."""

    def __init__(self, *, compress_inputs: bool = False) -> None:
        """Builder initializer."""
        self.inputs: dict[bcs.BuilderArg, bcs.CallArg] = {}
        self.commands: list[bcs.Command] = []
        self.objects_registry: dict[str, str] = {}
        self.compress_inputs: bool = compress_inputs

        self.command_frequency = {
            "MoveCall": 0,
            "TransferObjects": 0,
            "SplitCoin": 0,
            "MergeCoins": 0,
            "Publish": 0,
            "MakeMoveVec": 0,
            "Upgrade": 0,
        }
        logger.debug("TransactionBuilder initialized")

    def _finish(self) -> bcs.ProgrammableTransaction:
        """finish returns ProgrammableTransaction structure.

        :return: The resulting ProgrammableTransaction structure
        :rtype: bcs.ProgrammableTransaction
        """
        return bcs.ProgrammableTransaction(
            list(self.inputs.values()), self.commands.copy()
        )

    def finish_for_inspect(self) -> bcs.TransactionKind:
        """finish_for_inspect returns TransactionKind structure.

        For inspection, serializing this return and converting to base64 is enough
        for sui_devInspectTransaction

        :return: The resulting TransactionKind structure
        :rtype: bcs.TransactionKind
        """
        return bcs.TransactionKind("ProgrammableTransaction", self._finish())

    @versionchanged(version="0.20.0", reason="Check for duplication. See bug #99")
    @versionchanged(version="0.30.2", reason="Remove reuse of identical pure inputs")
    def input_pure(self, key: bcs.BuilderArg) -> bcs.Argument:
        """input_pure registers a pure input argument in the inputs collection.

        :param key: Becomes the 'key' in the inputs dictionary cotaining the input index
        :type key: bcs.BuilderArg
        :raises ValueError: If the key arg BuilderArg is not "Pure" variant
        :return: The input Argument encapsulating it's input index
        :rtype: bcs.Argument
        """
        logger.debug("Adding pure input")
        out_index = len(self.inputs)
        if key.enum_name == "Pure":
            if self.compress_inputs:
                e_index = 0
                for _ekey, evalue in self.inputs.items():
                    if key.value == evalue.value:
                        logger.debug(
                            f"Duplicate object input found at index {e_index}, reusing"
                        )
                        return bcs.Argument("Input", e_index)
                    e_index += 1
            self.inputs[key] = bcs.CallArg(key.enum_name, key.value)
        else:
            raise ValueError(f"Expected Pure builder arg, found {key.enum_name}")
        logger.debug(f"New pure input created at index {out_index}")
        return bcs.Argument("Input", out_index)

    @versionchanged(version="0.20.0", reason="Check for duplication. See bug #99")
    def input_obj(
        self,
        key: bcs.BuilderArg,
        object_arg: bcs.ObjectArg,
    ) -> bcs.Argument:
        """."""
        logger.debug("Adding object input")
        out_index = len(self.inputs)
        if key.enum_name == "Object" and isinstance(
            object_arg, bcs.ObjectArg
        ):  # _key = hash(input)
            if self.compress_inputs:
                e_index = 0
                for _ekey, evalue in self.inputs.items():
                    if object_arg == evalue.value:
                        logger.debug(
                            f"Duplicate object input found at index {e_index}, reusing"
                        )
                        return bcs.Argument("Input", e_index)
                    e_index += 1
            self.inputs[key] = bcs.CallArg(key.enum_name, object_arg)
        else:
            raise ValueError(
                f"Expected Object builder arg and ObjectArg, found {key.enum_name} and {type(object_arg)}"
            )
        self.objects_registry[key.value.to_address_str()] = object_arg.enum_name
        # self.objects_registry.add(key.value.to_address_str())
        logger.debug(f"New object input created at index {out_index}")
        return bcs.Argument("Input", out_index)

    @versionadded(version="0.54.0", reason="Support stand-alone ObjectArg")
    def input_obj_from_objarg(
        self, object_arg: Union[bcs.ObjectArg, bcs.Optional]
    ) -> bcs.Argument:
        """."""
        if isinstance(object_arg, bcs.Optional):
            object_arg = object_arg.value
            # oval = object_arg.value.value.ObjectID
        # else:
        oval: bcs.Address = object_arg.value.ObjectID
        barg = bcs.BuilderArg("Object", oval)
        return self.input_obj(barg, object_arg)

    def command(
        self, command_obj: bcs.Command, nresults: int = 1
    ) -> Union[bcs.Argument, list[bcs.Argument]]:
        """command adds a new command to the list of commands.

        :param command_obj: The Command type
        :type command_obj: bcs.Command
        :return: A result argument to be potentially used in other commands
        :rtype: bcs.Argument
        """
        self.command_frequency[command_obj.enum_name] += 1
        out_index = len(self.commands)
        logger.debug(f"Adding command {out_index}")
        self.commands.append(command_obj)
        if nresults > 1:
            logger.debug(f"Creating nested result return for {nresults} elements")
            nreslist: list[bcs.Argument] = []
            for nrindex in range(nresults):
                nreslist.append(bcs.Argument("NestedResult", (out_index, nrindex)))
            return nreslist
        logger.debug("Creating single result return")
        return bcs.Argument("Result", out_index)

    @versionchanged(
        version="0.54.0",
        reason="Accept bcs.ObjectArg(s) support GraphQL implementation.",
    )
    def make_move_vector(
        self,
        vtype: bcs.OptionalTypeTag,
        items: list[
            Union[
                bcs.Argument,
                bcs.BuilderArg,
                bcs.ObjectArg,
                tuple[bcs.BuilderArg, bcs.ObjectArg],
            ]
        ],
    ) -> bcs.Argument:
        """Create a call to convert a list of items to a Sui 'vector' type."""
        # Sample first for type
        logger.debug("Creating MakeMoveVec transaction")
        argrefs: list[bcs.Argument] = []
        for arg in items:
            if isinstance(arg, bcs.BuilderArg):
                argrefs.append(self.input_pure(arg))
            elif isinstance(arg, bcs.ObjectArg):
                argrefs.append(self.input_obj_from_objarg(arg))
            elif isinstance(arg, tuple):
                argrefs.append(self.input_obj(*arg))
            elif isinstance(arg, bcs.Argument):
                argrefs.append(arg)
            else:
                raise ValueError(f"Unknown arg in movecall {arg.__class__.__name__}")

        return self.command(bcs.Command("MakeMoveVec", bcs.MakeMoveVec(vtype, argrefs)))

    @versionchanged(version="0.17.0", reason="Add result count for correct arg return.")
    def move_call(
        self,
        *,
        target: bcs.Address,
        arguments: list[
            Union[
                bcs.Argument,
                bcs.ObjectArg,
                bcs.Optional,
                tuple[bcs.BuilderArg, bcs.ObjectArg],
            ]
        ],
        type_arguments: list[bcs.TypeTag],
        module: str,
        function: str,
        res_count: int = 1,
    ) -> Union[bcs.Argument, list[bcs.Argument]]:
        """Setup a MoveCall command and return it's result Argument."""
        logger.debug("Creating MakeCall transaction")
        argrefs: list[bcs.Argument] = []
        for arg in arguments:
            if isinstance(arg, bcs.BuilderArg):
                argrefs.append(self.input_pure(arg))
            elif isinstance(arg, bcs.ObjectArg):
                argrefs.append(self.input_obj_from_objarg(arg))
            elif isinstance(arg, bcs.Optional) and isinstance(arg.value, bcs.ObjectArg):
                argrefs.append(self.input_obj_from_objarg(arg))
            elif isinstance(arg, bcs.Optional) and not isinstance(
                arg.value, bcs.ObjectArg
            ):
                argrefs.append(self.input_pure(PureInput.as_input(arg)))
            elif isinstance(arg, tuple):
                argrefs.append(self.input_obj(*arg))
            elif isinstance(arg, bcs.Argument):
                argrefs.append(arg)
            elif isinstance(arg, tuple(bcs.OPTIONAL_SCALARS)):
                argrefs.append(self.input_pure(PureInput.as_input(arg)))
            elif isinstance(arg, list):
                argrefs.append(self.input_pure(PureInput.as_input(arg)))
            elif isinstance(arg, bcs.Variable):
                argrefs.append(self.input_pure(PureInput.as_input(arg)))
            else:
                raise ValueError(f"Unknown arg in movecall {arg.__class__.__name__}")

        return self.command(
            bcs.Command(
                "MoveCall",
                bcs.ProgrammableMoveCall(
                    target, module, function, type_arguments, argrefs
                ),
            ),
            res_count,
        )

    @versionchanged(version="0.17.0", reason="Extend to take list of amounts")
    @versionchanged(
        version="0.33.0", reason="Accept bcs.Argument (i.e. Result) as amount"
    )
    @versionchanged(
        version="0.54.0", reason="Accept bcs.ObjectArg support GraphQL implementation."
    )
    def split_coin(
        self,
        from_coin: Union[
            bcs.Argument, bcs.ObjectArg, tuple[bcs.BuilderArg, bcs.ObjectArg]
        ],
        amounts: list[bcs.BuilderArg],
    ) -> bcs.Argument:
        """Setup a SplitCoin command and return it's result Argument."""
        logger.debug("Creating SplitCoin transaction")
        amounts_arg = []
        for amount in amounts:
            if isinstance(amount, bcs.Argument):
                amounts_arg.append(amount)
            else:
                amounts_arg.append(self.input_pure(amount))
        if isinstance(from_coin, bcs.ObjectArg):
            from_coin = self.input_obj_from_objarg(from_coin)
        elif isinstance(from_coin, tuple):
            from_coin = self.input_obj(*from_coin)
        return self.command(
            bcs.Command("SplitCoin", bcs.SplitCoin(from_coin, amounts_arg)),
            len(amounts_arg),
        )

    @versionchanged(
        version="0.54.0",
        reason="Accept bcs.ObjectArg(s) support GraphQL implementation.",
    )
    def merge_coins(
        self,
        to_coin: Union[
            bcs.Argument, bcs.ObjectArg, tuple[bcs.BuilderArg, bcs.ObjectArg]
        ],
        from_coins: list[
            Union[bcs.Argument, bcs.ObjectArg, tuple[bcs.BuilderArg, bcs.ObjectArg]]
        ],
    ) -> bcs.Argument:
        """Setup a MergeCoins command and return it's result Argument."""
        logger.debug("Creating MergeCoins transaction")

        if isinstance(to_coin, bcs.ObjectArg):
            to_coin = self.input_obj_from_objarg(to_coin)
        elif isinstance(to_coin, tuple):
            to_coin = self.input_obj(*to_coin)
        from_args: list[bcs.Argument] = []
        for fcoin in from_coins:
            if isinstance(fcoin, bcs.ObjectArg):
                fcoin = self.input_obj_from_objarg(fcoin)
            elif isinstance(fcoin, tuple):
                fcoin = self.input_obj(*fcoin)
            from_args.append(fcoin)
        return self.command(
            bcs.Command("MergeCoins", bcs.MergeCoins(to_coin, from_args))
        )

    def transfer_objects(
        self,
        recipient: Union[bcs.BuilderArg, bcs.Argument],
        object_ref: Union[
            bcs.Argument,
            list[
                Union[
                    bcs.Argument,
                    bcs.ObjectArg,
                    tuple[bcs.BuilderArg, bcs.ObjectArg],
                ]
            ],
        ],
    ) -> bcs.Argument:
        """Setup a TransferObjects command and return it's result Argument."""
        logger.debug("Creating TransferObjects transaction")
        receiver_arg = (
            recipient
            if isinstance(recipient, bcs.Argument)
            else self.input_pure(recipient)
        )
        # receiver_arg = self.input_pure(recipient)
        from_args: list[bcs.Argument] = []
        if isinstance(object_ref, list):
            for fcoin in object_ref:
                if isinstance(fcoin, bcs.ObjectArg):
                    fcoin = self.input_obj_from_objarg(fcoin)
                elif isinstance(fcoin, tuple):
                    fcoin = self.input_obj(*fcoin)
                from_args.append(fcoin)
        else:
            from_args.append(object_ref)
        return self.command(
            bcs.Command("TransferObjects", bcs.TransferObjects(from_args, receiver_arg))
        )

    @versionchanged(
        version="0.76.0", reason="https://github.com/FrankC01/pysui/issues/261"
    )
    def transfer_sui(
        self,
        recipient: bcs.BuilderArg,
        from_coin: Union[bcs.Argument, tuple[bcs.BuilderArg, bcs.ObjectArg]],
        amount: Optional[Union[bcs.BuilderArg, bcs.OptionalU64]] = None,
    ) -> bcs.Argument:
        """Setup a TransferObjects for Sui Coins.

        First uses the SplitCoins result, then returns the TransferObjects result Argument.
        """
        logger.debug("Creating TransferSui transaction")
        reciever_arg = self.input_pure(recipient)
        if amount and isinstance(amount, bcs.BuilderArg):
            coin_arg = self.split_coin(from_coin=from_coin, amounts=[amount])
        elif isinstance(amount, bcs.OptionalU64):
            if amount.value:
                coin_arg = self.split_coin(
                    from_coin=from_coin,
                    amounts=[
                        PureInput.as_input(SuiU64(bcs.U64.int_safe(amount.value)))
                    ],
                )
            else:
                coin_arg = from_coin
        else:
            coin_arg = from_coin
        if isinstance(coin_arg, bcs.Argument):
            pass
        elif isinstance(coin_arg, bcs.ObjectArg):
            coin_arg = self.input_obj_from_objarg(coin_arg)
        else:
            coin_arg = self.input_obj(*from_coin)
        return self.command(
            bcs.Command(
                "TransferObjects",
                bcs.TransferObjects([coin_arg], reciever_arg),
            )
        )

    @versionchanged(
        version="0.20.0",
        reason="Removed UpgradeCap auto transfer as per Sui best practices.",
    )
    def publish(
        self, modules: list[list[bcs.U8]], dep_ids: list[bcs.Address]
    ) -> bcs.Argument:
        """Setup a Publish command and return it's result Argument."""
        logger.debug("Creating Publish transaction")
        # result = self.command(bcs.Command("Publish", bcs.Publish(modules, dep_ids)))
        return self.command(bcs.Command("Publish", bcs.Publish(modules, dep_ids)))

    def authorize_upgrade(
        self,
        upgrade_cap: Union[bcs.ObjectArg, tuple[bcs.BuilderArg, bcs.ObjectArg]],
        policy: bcs.BuilderArg,
        digest: bcs.BuilderArg,
    ) -> bcs.Argument:
        """Setup a Authorize Upgrade MoveCall and return it's result Argument."""
        logger.debug("Creating UpgradeAuthorization transaction")
        if isinstance(upgrade_cap, bcs.ObjectArg):
            ucap = self.input_obj_from_objarg(upgrade_cap)
        else:
            ucap = self.input_obj(*upgrade_cap)
        return self.command(
            bcs.Command(
                "MoveCall",
                bcs.ProgrammableMoveCall(
                    _SUI_PACKAGE_ID,
                    _SUI_PACKAGE_MODULE,
                    _SUI_PACAKGE_AUTHORIZE_UPGRADE,
                    [],
                    [
                        ucap,
                        self.input_pure(policy),
                        self.input_pure(digest),
                    ],
                ),
            )
        )

    def publish_upgrade(
        self,
        modules: list[list[bcs.U8]],
        dep_ids: list[bcs.Address],
        package_id: bcs.Address,
        upgrade_ticket: bcs.Argument,
    ) -> bcs.Argument:
        """Setup a Upgrade Command and return it's result Argument."""
        logger.debug("Creating PublishUpgrade transaction")
        return self.command(
            bcs.Command(
                "Upgrade",
                bcs.Upgrade(modules, dep_ids, package_id, upgrade_ticket),
            )
        )

    def commit_upgrade(
        self, upgrade_cap: bcs.Argument, receipt: bcs.Argument
    ) -> bcs.Argument:
        """Setup a Commit Upgrade MoveCall and return it's result Argument."""
        logger.debug("Creating UpgradeCommit transaction")
        return self.command(
            bcs.Command(
                "MoveCall",
                bcs.ProgrammableMoveCall(
                    _SUI_PACKAGE_ID,
                    _SUI_PACKAGE_MODULE,
                    _SUI_PACAKGE_COMMIt_UPGRADE,
                    [],
                    [upgrade_cap, receipt],
                ),
            )
        )


if __name__ == "__main__":
    pass
