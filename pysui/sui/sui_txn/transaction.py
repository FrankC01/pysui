#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Sui high level Transaction Builder supports generation of TransactionKind and TransactionData."""


import base64
import os
from pathlib import Path
from typing import Final, Optional, Union
import logging


from deprecated.sphinx import versionadded, versionchanged, deprecated

from pysui import SuiAddress, ObjectID
from pysui.sui import sui_utils

from pysui.sui.sui_builders.base_builder import (
    _NativeTransactionBuilder,
    sui_builder,
)
from pysui.sui.sui_clients.common import ClientMixin
from pysui.sui.sui_txn.signing_ms import SignerBlock, SigningMultiSig
import pysui.sui.sui_txn.transaction_builder as tx_builder
from pysui.sui.sui_txn.txn_deser import (
    deser_sender_and_sponsor,
    deser_transaction_builder,
    ser_sender_and_sponsor,
    ser_transaction_builder,
)
from pysui.sui.sui_txresults.package_meta import (
    SuiParameterReference,
    SuiParameterStruct,
)
from pysui.sui.sui_txresults.single_tx import (
    TransactionConstraints,
)
from pysui.sui.sui_types import bcs
from pysui.sui.sui_types.collections import SuiArray, SuiMap
from pysui.sui.sui_types.scalars import (
    SuiNullType,
    SuiString,
)
from pysui.sui.sui_utils import publish_build

# Standard library logging setup
logger = logging.getLogger("pysui.transaction")
if not logging.getLogger().handlers:
    logger.addHandler(logging.NullHandler())
    logger.propagate = False


class _DebugInspectTransaction(_NativeTransactionBuilder):
    """_DebugInspectTransaction added for malformed inspection results."""

    @sui_builder()
    def __init__(
        self,
        *,
        sender_address: SuiAddress,
        tx_bytes: SuiString,
        gas_price: Optional[SuiString] = None,
        epoch: Optional[SuiString] = None,
        additional_args: Optional[SuiMap] = None,
    ) -> None:
        """__init__ Initialize builder.

        This is for Debugging only

        :param sender_address: The sender/signer of transaction bytes
        :type tx_bytes: SuiAddress
        :param tx_bytes: BCS serialize base64 encoded string of TransactionKind
        :type tx_bytes: SuiString
        :param gas_price: Gas is not charged, but gas usage is still calculated. Default to use reference gas price
        :type gas_price: Optional[SuiString]
        :param epoch: The epoch to perform the call. Will be set from the system state object if not provided
        :type epoch: Optional[SuiString]
        """
        super().__init__(
            "sui_devInspectTransactionBlock",
        )

        if additional_args is None or isinstance(additional_args, SuiNullType):
            self.additional_args = sui_utils.as_sui_map({})
        else:
            self.additional_args = sui_utils.as_sui_map(additional_args)


@versionadded(version="0.26.0", reason="Refactor to support Async")
@versionadded(version="0.30.0", reason="Moved to transaction package.")
@versionadded(version="0.32.0", reason="Abstracting and adding serialization support.")
@versionchanged(
    version="0.40.1", reason="Default 'compress_inputs' on SuiTransaction to True"
)
@deprecated(version="0.54.0", reason="Transitioning to sui_pgql")
class _SuiTransactionBase:
    """SuiTransaction base object."""

    _MC_RESULT_CACHE: dict = {}
    _PURE_CANDIDATES: set[str] = {
        "bool",
        "SuiBoolean",
        "SuiU8",
        "SuiU16",
        "SuiU32",
        "SuiU64",
        "SuiU128",
        "SuiU256",
        "OptionalU8",
        "OptionalU16",
        "OptionalU32",
        "OptionalU64",
        "OptionalU128",
        "OptionalU256",
        "int",
        "SuiInteger",
        "str",
        "SuiString",
        "SuiAddress",
        "bytes",
        "Digest",
        "Address",
    }

    _TRANSACTION_GAS_ARGUMENT: bcs.Argument = bcs.Argument("GasCoin")
    _SYSTEMSTATE_OBJECT: ObjectID = ObjectID("0x5")
    _STAKE_REQUEST_TARGET: str = "0x3::sui_system::request_add_stake_mul_coin"
    _UNSTAKE_REQUEST_TARGET: str = "0x3::sui_system::request_withdraw_stake"
    _STANDARD_UPGRADE_CAP_TYPE: str = "0x2::package::UpgradeCap"
    _UPGRADE_CAP_SUFFIX: str = "UpgradeCap"
    _SPLIT_AND_KEEP: str = "0x2::pay::divide_and_keep"
    _SPLIT_AND_RETURN: str = "0x2::coin::divide_into_n"
    _PUBLIC_TRANSFER: str = "0x2::transfer::public_transfer"
    _VECTOR_REMOVE_INDEX: str = "0x1::vector::remove"
    _VECTOR_DESTROY_EMPTY: str = "0x1::vector::destroy_empty"
    _PAY_GAS: int = 4000000

    def __init__(
        self,
        *,
        client: ClientMixin,
        compress_inputs: bool = True,
        initial_sender: Union[SuiAddress, SigningMultiSig] = None,
        merge_gas_budget: bool = False,
        deserialize_from: Union[str, bytes] = None,
    ) -> None:
        """."""
        self.builder = tx_builder.ProgrammableTransactionBuilder(
            compress_inputs=compress_inputs
        )
        self.client = client
        self._sig_block = SignerBlock(
            sender=initial_sender or client.config.active_address
        )
        self._merge_gas = merge_gas_budget
        self._executed = False
        self.constraints: TransactionConstraints = (
            client.protocol.transaction_constraints
        )
        self._current_gas_price = client.current_gas_price
        if deserialize_from:
            if isinstance(deserialize_from, str):
                deserialize_from = base64.b64decode(deserialize_from)
            elif isinstance(deserialize_from, bytes):
                pass
            else:
                raise ValueError("deserialize_from must be a base64 string or bytes")
            self.deserialize(deserialize_from)

    @property
    def gas_price(self) -> int:
        """Returns the current gas price for the chain."""
        return self._current_gas_price

    @gas_price.setter
    def gas_price(self, new_price: int):
        """Set the gas price."""
        self._current_gas_price = new_price

    @property
    def signer_block(self) -> SignerBlock:
        """Returns the signers block."""
        return self._sig_block

    @property
    @versionadded(
        version="0.20.3",
        reason="Simplify using a gas object to resolve at execution time.",
    )
    def gas(self) -> bcs.Argument:
        """Enables use of gas reference as parameters in commands."""
        return self._TRANSACTION_GAS_ARGUMENT

    def raw_kind(self) -> bcs.TransactionKind:
        """Returns the TransactionKind object hierarchy of inputs, returns and commands.

        This is useful for reviewing the transaction that will be executed or inspected.
        """
        return self.builder.finish_for_inspect()

    def build_for_inspection(self) -> str:
        """build_for_inspection returns a base64 string that can be used in inspecting transaction.

        :return: base64 string representation of underlying TransactionKind
        :rtype: str
        """
        return base64.b64encode(self.raw_kind().serialize()).decode()

    @versionadded(version="0.30.0", reason="Observing Sui ProtocolConfig constraints")
    @versionchanged(version="0.31.0", reason="Validating against all PTB constraints")
    @versionchanged(version="0.34.0", reason="Fixed Command argument evaluation")
    def verify_transaction(
        self, ser_kind: Optional[bytes] = None
    ) -> tuple[TransactionConstraints, Union[dict, None]]:
        """verify_transaction Verify TransactionKind values against protocol constraints.

        :return: Returns the current constraints thresholds and violation dictionary (if any)
        :rtype: tuple[TransactionConstraints, Union[dict, None]]
        """
        # All set to 0
        result_err = TransactionConstraints()

        # Partition pure from objects
        max_pure_inputs = 0
        obj_inputs = []
        for i_key in self.builder.inputs.keys():
            if i_key.enum_name == "Pure":
                ilen = len(i_key.value)
                max_pure_inputs = ilen if ilen > max_pure_inputs else max_pure_inputs
            else:
                obj_inputs.append(i_key)

        # Validate max pure size
        if max_pure_inputs >= self.constraints.max_pure_argument_size:
            result_err.max_pure_argument_size = max_pure_inputs

        # Check input objects (objs + move calls)
        obj_count = len(obj_inputs) + self.builder.command_frequency["MoveCall"]
        if obj_count > self.constraints.max_input_objects:
            result_err.max_input_objects = obj_count

        # Check arguments
        total_args = 0
        for prog_txn in self.builder.commands:
            args_one = 0
            type_args_one = 0
            match prog_txn.enum_name:
                case "MoveCall":
                    args_one = len(prog_txn.value.Arguments)
                    type_args_one = len(prog_txn.value.Type_Arguments)
                case "TransferObjects":
                    args_one = len(prog_txn.value.Objects)
                case "MergeCoins":
                    args_one = len(prog_txn.value.FromCoins)
                case "SplitCoin":
                    args_one = len(prog_txn.value.Amount)
                case "MakeMoveVec":
                    args_one = len(prog_txn.value.Vector)
                case "Publish" | "Upgrade":
                    args_one = len(prog_txn.value.Modules)
                case _:
                    pass
            if args_one > self.constraints.max_arguments:
                result_err.max_arguments = args_one
            if type_args_one > self.constraints.max_type_arguments:
                result_err.max_type_arguments = type_args_one
            total_args += args_one

        # Check max_num_transferred_move_object_ids
        if total_args > self.constraints.max_num_transferred_move_object_ids:
            result_err.max_num_transferred_move_object_ids = total_args

        # Check max_programmable_tx_commands
        if len(self.builder.commands) > self.constraints.max_programmable_tx_commands:
            result_err.max_programmable_tx_commands = len(self.commands)

        # Check size of transaction bytes
        # Build faux gas as needed
        if not ser_kind:
            reuse_addy = bcs.Address.from_str("0x0")
            ser_txdata = bcs.TransactionData(
                "V1",
                bcs.TransactionDataV1(
                    self.raw_kind(),
                    reuse_addy,
                    bcs.GasData(
                        [
                            bcs.ObjectReference(
                                reuse_addy,
                                int(0),
                                bcs.Digest.from_str(
                                    "ByumsdYUAQWJfwYgowsme7hm5vE8d2mXik3rGaNC9R4W"
                                ),
                            )
                        ],
                        reuse_addy,
                        int(self._current_gas_price),
                        self._PAY_GAS,
                    ),
                    bcs.TransactionExpiration("None"),
                ),
            )
            ser_kind = ser_txdata.serialize()

        if len(ser_kind) > self.constraints.max_tx_size_bytes:
            result_err.max_tx_size_bytes = len(ser_kind)

        var_map = vars(result_err)
        err_dict: dict = {x: y for (x, y) in var_map.items() if y != 0}
        err_dict.pop("feature_dict")
        return self.constraints, err_dict if err_dict else None

    @versionadded(version="0.18.0", reason="Reuse for argument nested list recursion.")
    @versionadded(
        version="0.19.0",
        reason="Broaden types in _PURE_CANDIDATES with set of Optional<Ux> types",
    )
    def _resolve_item(
        self,
        index: int,
        items: list,
        refs: list,
        tuples: list,
        nest_depth: int = 0,
    ):
        """Resolve the appropriate bcs type for argument item."""
        item = items[index]
        clz_name = item.__class__.__name__
        if clz_name in self._PURE_CANDIDATES:
            items[index] = tx_builder.PureInput.as_input(items[index])
        else:
            match clz_name:
                case "list" | "SuiArray":
                    # Have exceeded limit/constraint

                    if nest_depth >= self.constraints.max_type_argument_depth:
                        raise ValueError(
                            f"vector is constrained to max {self.constraints.max_type_argument_depth} depth. Found {nest_depth}."
                        )

                    # Generalize to list
                    litems = item if isinstance(item, list) else item.array
                    objref_indexes: list[int] = []
                    objtup_indexes: list[int] = []
                    # Keep drilling if next is list
                    if litems and isinstance(litems[0], (list, SuiArray)):
                        self._resolve_item(
                            0,
                            litems,
                            objref_indexes,
                            objtup_indexes,
                            nest_depth + 1,
                        )
                        items[index] = litems
                    # Else check for type consistency and convert to LCD
                    elif litems:
                        item_clz_name = litems[0].__class__.__name__
                        res_items: list = []
                        for i_item in litems:
                            inner_clz_name = i_item.__class__.__name__
                            assert (
                                inner_clz_name == item_clz_name
                            ), f"Expected {item_clz_name} found {inner_clz_name}"
                            assert (
                                inner_clz_name in self._PURE_CANDIDATES
                            ), f"Nested argument lists must be of type {self._PURE_CANDIDATES}"
                            res_items.append(i_item)
                        items[index] = res_items
                    else:
                        items[index] = litems
                # Need to fetch objects
                case "ObjectID":
                    refs.append(index)
                case "SuiCoinObject":
                    if hasattr(item, "owner"):
                        tuples.append(index)
                    else:
                        items[index] = ObjectID(item.object_id)
                        refs.append(index)
                # Tuple all ready to be set
                case "ObjectRead":
                    tuples.append(index)
                # Direct passthroughs
                case "Argument" | "BuilderArg" | "tuple":
                    pass
                case _:
                    raise ValueError(f"Uknown class type handler {clz_name}")

    @versionchanged(
        version="0.50.0",
        reason="Removed with_unpublished_dependencies and skip_fetch_latest_git_deps replace with `args_list`",
    )
    def _compile_source(
        self,
        project_path: str,
        args_list: list[str],
    ) -> tuple[list[str], list[str], bcs.Digest]:
        """."""
        src_path = Path(os.path.expanduser(project_path))
        args_list = args_list if args_list else []
        compiled_package = publish_build(
            src_path,
            args_list,
        )
        dependencies = [
            bcs.Address.from_str(x if isinstance(x, str) else x.value)
            for x in compiled_package.dependencies
        ]
        digest = bcs.Digest.from_bytes(compiled_package.package_digest)
        return compiled_package.compiled_modules, dependencies, digest

    def _receiving_parm(self, parm) -> bool:
        """."""
        arg_is_receiving = False
        if isinstance(parm, SuiParameterStruct) and parm.name == "Receiving":
            arg_is_receiving = True
        elif (
            isinstance(parm, SuiParameterReference)
            and hasattr(parm.reference_to, "name")
            and parm.reference_to.name == "Receiving"
        ):
            arg_is_receiving = True
        return arg_is_receiving

    @versionadded(
        version="0.37.0",
        reason="Process arguments for Receiving object decoration",
    )
    def _receiving_feature(self, arguments: list, parameters: list) -> list:
        """."""
        for index, arg in enumerate(arguments):
            parm = parameters[index]
            # Is parameter type a transfer::Receiving kind
            is_receiving = self._receiving_parm(parm)
            is_receiving_supported = self.constraints.feature_dict.get(
                "receive_objects", False
            )
            if is_receiving and not self.constraints.feature_dict.get(
                "receive_objects", False
            ):
                raise ValueError(f"Receiving not supported in Sui current environment")
            # If type is a CallArg object (imm/shared/receive)
            if isinstance(arg, tuple):
                if is_receiving:
                    if is_receiving_supported:
                        arguments[index] = (
                            arg[0],
                            bcs.ObjectArg("Receiving", arg[1].value),
                        )
                        arg = arguments[index]
                        # arg[1] = bcs.ObjectArg("Receiving", arg[1].value)
                    else:
                        pass
                if hasattr(parm, "is_mutable") and parm.is_mutable:
                    r_arg: bcs.ObjectArg = arg[1]
                    r_arg.value.Mutable = True
        return arguments

    @versionadded(
        version="0.32.0",
        reason="Serialize transaction builder",
    )
    @versionchanged(version="0.33.0", reason="Removed abstraction made private")
    def _serialize(self, include_sender_sponsor) -> bcs.SuiTransaction:
        """serialize Returns a BCS representation of SuiTransaction state.

        :return: BCS representation of SuiTransaction state
        :rtype: bcs.SuiTransaction
        """
        # Sender and Sponsor
        if include_sender_sponsor:
            sender, sponsor = ser_sender_and_sponsor(
                self.signer_block, self.client.config
            )
        else:
            sender = bcs.TxSender("NotSet")
            sponsor = bcs.TxSender("NotSet")

        # Finalize with builder data
        return bcs.SuiTransaction(
            "1.0.0",
            bcs.SuiTransactionDataV1(
                sender, sponsor, ser_transaction_builder(self.builder)
            ),
        )

    @versionadded(
        version="0.33.0",
        reason="Serialize transaction builder to bytes",
    )
    @versionadded(
        version="0.35.0",
        reason="Option to omit sender/sponsor",
    )
    @deprecated(
        version="0.64.0", reason="Use GraphQL serialize_to_wallet_standard function"
    )
    def serialize(self, include_sender_sponsor: Optional[bool] = True) -> bytes:
        """."""
        tbuilder = self._serialize(include_sender_sponsor)
        # print(tbuilder.to_json(indent=2))
        return tbuilder.serialize()

    @versionadded(
        version="0.32.0",
        reason="DeSerialize transaction builder state",
    )
    @deprecated(
        version="0.64.0", reason="Use GraphQL deserialize_to_transaction function"
    )
    def deserialize(self, state_ser: bytes):
        """."""
        tx_state = bcs.SuiTransaction.deserialize(state_ser)
        # Set signature block
        self._sig_block = deser_sender_and_sponsor(
            tx_state.value.TxSender,
            tx_state.value.TxSponsor,
            self.client.config,
        )
        # Setup the builder
        deser_transaction_builder(
            tx_state.value.TxTransaction, self.builder, self.client.config
        )


if __name__ == "__main__":
    pass
