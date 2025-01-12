#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-
# pylint: disable=too-many-instance-attributes

"""Sui low level caching Transaction Builder supports generation of TransactionKind."""

import logging
from typing import Optional, Set, Union
from deprecated.sphinx import versionchanged, versionadded

from pysui.sui.sui_common.txb_pure import PureInput
from pysui.sui.sui_types import bcs
from pysui.sui.sui_utils import hexstring_to_sui_id
from pysui.sui.sui_types.scalars import (
    SuiU64,
)


# Well known aliases
_SUI_PACKAGE_ID: bcs.Address = bcs.Address.from_str("0x2")
_SUI_PACKAGE_MODULE: str = "package"
_SUI_PACAKGE_AUTHORIZE_UPGRADE: str = "authorize_upgrade"
_SUI_PACAKGE_COMMIt_UPGRADE: str = "commit_upgrade"

# Standard library logging setup
logger = logging.getLogger("serial_exec")


@versionadded(version="0.73.0", reason="Support serialzed and parallel executions")
class CachingTransactionBuilder:
    """CachingTransactionBuilder supports defered objectref resolutions."""

    def __init__(self, *, compress_inputs: bool = False) -> None:
        """Builder initializer."""
        self.inputs: dict[bcs.BuilderArg, bcs.CallArg] = {}
        self.commands: list[bcs.Command] = []
        self.objects_registry: dict[str, str] = {}
        self.compress_inputs: bool = compress_inputs
        self.compress_pure_inputs = True

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

    def get_unresolved_inputs(
        self,
    ) -> dict[str, bcs.UnresolvedObjectArg]:
        """Retrieve unresolved objects in input list.

        :return: A dict of input index (key) and UnresolveObjectArg spec
        :rtype: dict[int, bcs.UnresolvedObjectArg]
        """
        # Use for loop as faster for small dictionaries
        res: dict[str, bcs.UnresolvedObjectArg] = {}
        for idx, (barg, carg) in enumerate(self.inputs.items()):
            if barg.enum_name == "Unresolved":
                res[idx] = carg.value
        # Return unresolved
        return res

    def resolved_object_inputs(
        self, entries: dict[int, tuple[bcs.BuilderArg, bcs.CallArg]]
    ):
        """."""
        new_inputs: dict[bcs.BuilderArg, bcs.CallArg] = {}
        for idx, (barg, carg) in enumerate(self.inputs.items()):
            if barg.enum_name == "Unresolved":
                rbarg, rcarg = entries[idx]
                new_inputs[rbarg] = rcarg
            else:
                new_inputs[barg] = carg
        self.inputs = new_inputs

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
            if self.compress_pure_inputs:
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
            raise ValueError(f"Expected Pure builder argument, found {key.enum_name}")
        logger.debug(f"New pure input created at index {out_index}")
        return bcs.Argument("Input", out_index)

    def input_obj(
        self,
        key: bcs.BuilderArg,
        object_arg: Union[bcs.ObjectArg, bcs.UnresolvedObjectArg],
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
            self.objects_registry[key.value.to_address_str()] = object_arg.enum_name
        elif key.enum_name == "Unresolved" and isinstance(
            object_arg, bcs.UnresolvedObjectArg
        ):
            carg = bcs.CallArg("UnresolvedObject", object_arg)
            # self.inputs.update({key: object_arg})
            self.inputs[key] = carg
            self.objects_registry[key.value] = object_arg
        else:
            raise ValueError(
                f"Expected Object builder arg and ObjectArg, found {key.enum_name} and {type(object_arg)}"
            )
        # self.objects_registry[key.value.to_address_str()] = object_arg.enum_name
        # self.objects_registry.add(key.value.to_address_str())
        logger.debug(f"New object input created at index {out_index}")
        return bcs.Argument("Input", out_index)

    @versionadded(version="0.73.0", reason="Support stand-alone Unresolved objects")
    def input_obj_from_unresolved_object(
        self, object_arg: bcs.UnresolvedObjectArg
    ) -> bcs.Argument:
        """."""
        object_arg.ObjectStr = hexstring_to_sui_id(object_arg.ObjectStr)
        barg = bcs.BuilderArg("Unresolved", object_arg.ObjectStr)
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

    def make_move_vector(
        self,
        vtype: bcs.OptionalTypeTag,
        items: list[
            Union[
                bcs.Argument,
                bcs.UnresolvedObjectArg,
                tuple[bcs.BuilderArg, bcs.UnresolvedObjectArg],
            ]
        ],
    ) -> bcs.Argument:
        """Create a call to convert a list of items to a Sui 'vector' type."""
        # Sample first for type
        logger.debug("MakeMoveVec transaction")
        argrefs: list[bcs.Argument] = []
        for arg in items:
            if isinstance(arg, bcs.BuilderArg):
                argrefs.append(self.input_pure(arg))
            elif isinstance(arg, bcs.UnresolvedObjectArg):
                argrefs.append(self.input_obj_from_unresolved_object(arg))
            elif isinstance(arg, tuple):
                barg, oarg = arg
                if isinstance(oarg, bcs.UnresolvedObjectArg):
                    argrefs.append(self.input_obj(barg, oarg))
                else:
                    raise NotImplementedError("Found ObjectArg in make_move_vector")
            elif isinstance(arg, bcs.Argument):
                argrefs.append(arg)
            else:
                raise ValueError(f"Unknown arg in movecall {arg.__class__.__name__}")

        return self.command(bcs.Command("MakeMoveVec", bcs.MakeMoveVec(vtype, argrefs)))

    def move_call(
        self,
        *,
        target: bcs.Address,
        arguments: list[
            Union[
                bcs.Argument,
                bcs.UnresolvedObjectArg,
                bcs.Optional,
                bcs.UnresolvedOptional,
                tuple[bcs.BuilderArg, bcs.UnresolvedObjectArg],
            ]
        ],
        type_arguments: list[bcs.TypeTag],
        module: str,
        function: str,
        res_count: int = 1,
    ) -> Union[bcs.Argument, list[bcs.Argument]]:
        """Setup a MoveCall command and return it's result Argument."""
        logger.debug("MoveCall transaction")
        argrefs: list[bcs.Argument] = []
        for arg in arguments:
            if isinstance(arg, bcs.BuilderArg):
                argrefs.append(self.input_pure(arg))
            elif isinstance(arg, bcs.UnresolvedObjectArg):
                argrefs.append(self.input_obj_from_unresolved_object(arg))
            elif isinstance(arg, bcs.UnresolvedOptional):
                pass
            elif isinstance(arg, bcs.Optional):
                argrefs.append(self.input_pure(PureInput.as_input(arg)))
            elif isinstance(arg, tuple):
                barg, oarg = arg
                if isinstance(oarg, bcs.UnresolvedObjectArg):
                    argrefs.append(self.input_obj(barg, oarg))
                else:
                    raise NotImplementedError("Found ObjectArg in make_move_vector")
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

    def split_coin(
        self,
        from_coin: Union[
            bcs.Argument,
            bcs.UnresolvedObjectArg,
            tuple[bcs.BuilderArg, bcs.UnresolvedObjectArg],
        ],
        amounts: list[bcs.BuilderArg],
    ) -> bcs.Argument:
        """Setup a SplitCoin command and return it's result Argument."""
        logger.debug("SplitCoin transaction")
        amounts_arg = []
        for amount in amounts:
            if isinstance(amount, bcs.Argument):
                amounts_arg.append(amount)
            else:
                amounts_arg.append(self.input_pure(amount))
        if isinstance(from_coin, bcs.UnresolvedObjectArg):
            from_coin = self.input_obj_from_unresolved_object(from_coin)
        elif isinstance(from_coin, bcs.Argument):
            pass
        elif isinstance(from_coin, tuple):
            barg, oarg = from_coin
            if isinstance(oarg, bcs.UnresolvedObjectArg):
                from_coin = self.input_obj(*from_coin)
            else:
                raise NotImplementedError("Found ObjectArg in make_move_vector")
        else:
            raise ValueError(f"Unknown arg in movecall {from_coin.__class__.__name__}")
        return self.command(
            bcs.Command("SplitCoin", bcs.SplitCoin(from_coin, amounts_arg)),
            len(amounts_arg),
        )

    def merge_coins(
        self,
        to_coin: Union[
            bcs.Argument,
            bcs.UnresolvedObjectArg,
            tuple[bcs.BuilderArg, bcs.UnresolvedObjectArg],
        ],
        from_coins: list[
            Union[
                bcs.Argument,
                bcs.UnresolvedObjectArg,
                tuple[bcs.BuilderArg, bcs.UnresolvedObjectArg],
            ]
        ],
    ) -> bcs.Argument:
        """Setup a MergeCoins command and return it's result Argument."""
        logger.debug("MergeCoins transaction")

        if isinstance(to_coin, bcs.UnresolvedObjectArg):
            to_coin = self.input_obj_from_unresolved_object(to_coin)
        elif isinstance(to_coin, tuple):
            barg, oarg = to_coin
            if isinstance(oarg, bcs.UnresolvedObjectArg):
                to_coin = self.input_obj(barg, oarg)
            else:
                raise NotImplementedError("Found ObjectArg in merge_coins to_coin")
        from_args: list[bcs.Argument] = []
        for fcoin in from_coins:
            if isinstance(fcoin, bcs.ObjectArg):
                raise NotImplementedError("Found ObjectArg in merge_coins from list")
            elif isinstance(fcoin, bcs.UnresolvedObjectArg):
                fcoin = self.input_obj_from_unresolved_object(fcoin)
            elif isinstance(fcoin, tuple):
                barg, oarg = fcoin
                if isinstance(oarg, bcs.UnresolvedObjectArg):
                    fcoin = self.input_obj(barg, oarg)
                else:
                    raise NotImplementedError(
                        "Found ObjectArg in merge_coins from_coin"
                    )
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
                    bcs.UnresolvedObjectArg,
                    tuple[bcs.BuilderArg, bcs.ObjectArg],
                ]
            ],
        ],
    ) -> bcs.Argument:
        """Setup a TransferObjects command and return it's result Argument."""
        logger.debug("TransferObjects transaction")
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
                    raise NotImplementedError("Found ObjectArg in transfer_objects")
                elif isinstance(fcoin, bcs.UnresolvedObjectArg):
                    fcoin = self.input_obj_from_unresolved_object(fcoin)
                elif isinstance(fcoin, tuple):
                    barg, oarg = fcoin
                    if isinstance(oarg, bcs.UnresolvedObjectArg):
                        fcoin = self.input_obj(barg, oarg)
                    else:
                        raise NotImplementedError(
                            "Found ObjectArg in merge_coins from_coin"
                        )
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
        from_coin: Union[bcs.Argument, tuple[bcs.BuilderArg, bcs.UnresolvedObjectArg]],
        amount: Optional[Union[bcs.BuilderArg, bcs.OptionalU64]] = None,
    ) -> bcs.Argument:
        """Setup a TransferObjects for Sui Coins.

        First uses the SplitCoins result, then returns the TransferObjects result Argument.
        """
        logger.debug("TransferSui transaction")
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
        elif isinstance(from_coin, bcs.Argument):
            coin_arg = from_coin
        else:
            # TODO: Validate unresolved type
            barg, oarg = from_coin
            if isinstance(oarg, bcs.UnresolvedObjectArg):
                coin_arg = self.input_obj(barg, oarg)
            else:
                raise NotImplementedError("Found ObjectArg in merge_coins from_coin")
        return self.command(
            bcs.Command(
                "TransferObjects",
                bcs.TransferObjects([coin_arg], reciever_arg),
            )
        )

    def publish(
        self, modules: list[list[bcs.U8]], dep_ids: list[bcs.Address]
    ) -> bcs.Argument:
        """Setup a Publish command and return it's result Argument."""
        logger.debug("Publish transaction")
        # result = self.command(bcs.Command("Publish", bcs.Publish(modules, dep_ids)))
        return self.command(bcs.Command("Publish", bcs.Publish(modules, dep_ids)))

    def authorize_upgrade(
        self,
        upgrade_cap: Union[bcs.ObjectArg, tuple[bcs.BuilderArg, bcs.ObjectArg]],
        policy: bcs.BuilderArg,
        digest: bcs.BuilderArg,
    ) -> bcs.Argument:
        """Setup a Authorize Upgrade MoveCall and return it's result Argument."""
        logger.debug("UpgradeAuthorization transaction")
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
        logger.debug("PublishUpgrade transaction")
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
        logger.debug("UpgradeCommit transaction")
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
