#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Sui high level Transaction Builder supports generation of TransactionKind and TransactionData."""


import base64
import os
from pathlib import Path
from typing import Any, Optional, Union
import logging


from pysui import SuiAddress, ObjectID

from pysui.sui.sui_txresults.single_tx import (
    TransactionConstraints,
)

from pysui.sui.sui_pgql.pgql_clients import BaseSuiGQLClient
from pysui.sui.sui_pgql.pgql_txb_signing import SignerBlock, SigningMultiSig
import pysui.sui.sui_txn.transaction_builder as tx_builder
import pysui.sui.sui_pgql.pgql_types as pgql_type
from pysui.sui.sui_types import bcs
from pysui.sui.sui_types.scalars import SuiString
from pysui.sui.sui_utils import publish_buildg

# Standard library logging setup
logger = logging.getLogger()


class _TransactionBase:
    """."""

    _TRANSACTION_GAS_ARGUMENT: bcs.Argument = bcs.Argument("GasCoin")
    _SYSTEMSTATE_OBJECT: ObjectID = ObjectID("0x5")
    _STAKE_REQUEST_TARGET: str = "0x3::sui_system::request_add_stake_mul_coin"
    _UNSTAKE_REQUEST_TARGET: str = "0x3::sui_system::request_withdraw_stake"
    _STANDARD_UPGRADE_CAP_TYPE: str = "0x2::package::UpgradeCap"
    _UPGRADE_CAP_SUFFIX: str = "UpgradeCap"
    _SPLIT_AND_KEEP: str = "0x2::pay::divide_and_keep"
    _STD_FRAMEWORK: bcs.Address = bcs.Address.from_str("0x1")
    _PUBLIC_TRANSFER: str = "0x2::transfer::public_transfer"
    _PAY_GAS: int = 4000000
    _BUILD_BYTE_STR: str = "tx_bytestr"
    _SIG_ARRAY: str = "sig_array"

    _SPLIT_COIN = pgql_type.MoveArgSummary(
        [],
        [
            pgql_type.MoveObjectRefArg(
                pgql_type.RefType.MUT_REF, "0x2", "sui", "SUI", [], False, False, False
            ),
            pgql_type.MoveListArg(
                pgql_type.RefType.NO_REF,
                pgql_type.MoveScalarArg(pgql_type.RefType.NO_REF, "u64"),
            ),
        ],
    )

    _MERGE_COINS = pgql_type.MoveArgSummary(
        [],
        [
            pgql_type.MoveObjectRefArg(
                pgql_type.RefType.MUT_REF, "0x2", "sui", "SUI", [], False, False, False
            ),
            pgql_type.MoveListArg(
                pgql_type.RefType.NO_REF,
                pgql_type.MoveObjectRefArg(
                    pgql_type.RefType.MUT_REF,
                    "0x2",
                    "sui",
                    "SUI",
                    [],
                    False,
                    False,
                    False,
                ),
            ),
        ],
    )

    _TRANSFER_OBJECTS = pgql_type.MoveArgSummary(
        [],
        [
            pgql_type.MoveScalarArg(pgql_type.RefType.NO_REF, "address"),
            pgql_type.MoveListArg(
                pgql_type.RefType.NO_REF,
                pgql_type.MoveObjectRefArg(
                    pgql_type.RefType.MUT_REF,
                    "0x2",
                    "sui",
                    "SUI",
                    [],
                    False,
                    False,
                    False,
                ),
            ),
        ],
    )

    _TRANSFER_SUI = pgql_type.MoveArgSummary(
        [],
        [
            pgql_type.MoveScalarArg(pgql_type.RefType.NO_REF, "address"),
            pgql_type.MoveObjectRefArg(
                pgql_type.RefType.MUT_REF, "0x2", "sui", "SUI", [], False, False, False
            ),
            pgql_type.MoveObjectRefArg(
                pgql_type.RefType.MUT_REF,
                "0x2",
                "sui",
                "SUI",
                [pgql_type.MoveScalarArg(pgql_type.RefType.NO_REF, "u64")],
                True,
                False,
                False,
            ),
        ],
    )

    _PUBLIC_TRANSFER_OBJECTS = pgql_type.MoveArgSummary(
        [],
        [
            pgql_type.MoveObjectRefArg(
                pgql_type.RefType.MUT_REF, "0x2", "sui", "SUI", [], False, False, False
            ),
            pgql_type.MoveScalarArg(pgql_type.RefType.NO_REF, "address"),
        ],
    )

    _MAKE_MOVE_VEC = pgql_type.MoveArgSummary(
        [],
        [
            pgql_type.MoveVectorArg(
                pgql_type.RefType.NO_REF,
                pgql_type.MoveObjectRefArg(
                    pgql_type.RefType.MUT_REF,
                    "0x2",
                    "sui",
                    "SUI",
                    [],
                    False,
                    False,
                    False,
                ),
            )
        ],
    )

    _PUBLISH_UPGRADE = pgql_type.MoveArgSummary(
        [],
        [
            pgql_type.MoveObjectRefArg(
                pgql_type.RefType.MUT_REF, "0x2", "sui", "SUI", [], False, False, False
            ),
            pgql_type.MoveScalarArg(pgql_type.RefType.NO_REF, "u8"),
        ],
    )

    def __init__(
        self,
        *,
        client: BaseSuiGQLClient,
        compress_inputs: Optional[bool] = True,
        builder: Optional[Any] = None,
        arg_parser: Optional[Any] = None,
    ):
        """."""
        self.builder = builder or tx_builder.ProgrammableTransactionBuilder(
            compress_inputs=compress_inputs
        )
        self._argparse = arg_parser
        self.client = client
        self.constraints: TransactionConstraints = (
            client.protocol().transaction_constraints
        )
        self._current_gas_price = client.current_gas_price()

    @property
    def gas(self) -> bcs.Argument:
        """Enables use of gas reference as parameters in commands."""
        return self._TRANSACTION_GAS_ARGUMENT

    @property
    def gas_price(self) -> int:
        """Returns the current gas price for the chain."""
        return self._current_gas_price

    @gas_price.setter
    def gas_price(self, new_price: int):
        """Set the gas price."""
        self._current_gas_price = new_price


class _SuiTransactionBase(_TransactionBase):
    """SuiTransaction GQL base object."""

    def __init__(
        self,
        *,
        client: BaseSuiGQLClient,
        compress_inputs: Optional[bool] = True,
        initial_sender: Union[str, SigningMultiSig] = None,
        initial_sponsor: Union[str, SigningMultiSig] = None,
        builder: Optional[Any] = None,
        arg_parser: Optional[Any] = None,
        merge_gas_budget: Optional[bool] = False,
    ) -> None:
        """."""
        super().__init__(
            client=client,
            compress_inputs=compress_inputs,
            builder=builder,
            arg_parser=arg_parser,
        )
        self._sig_block = SignerBlock(
            sender=initial_sender or client.config.active_address,
            sponsor=initial_sponsor,
        )
        self._merge_gas = merge_gas_budget
        self._executed = False

    @property
    def signer_block(self) -> SignerBlock:
        """Returns the signers block."""
        return self._sig_block

    def raw_kind(self) -> bcs.TransactionKind:
        """Returns the TransactionKind object hierarchy of inputs, returns and commands.

        This is useful for reviewing the transaction that will be executed or inspected.
        """
        return self.builder.finish_for_inspect()

    def build_for_dryrun(self) -> str:
        """Returns a base64 string that can be used in dry running transaction.

        :return: base64 string representation of underlying TransactionKind
        :rtype: str
        """
        return base64.b64encode(self.raw_kind().serialize()).decode()

    def verify_transaction(
        self, ser_kind: Optional[bytes] = None
    ) -> tuple[TransactionConstraints, Union[dict, None]]:
        """Verify TransactionKind values against protocol constraints.

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

    def _compile_source(
        self,
        project_path: str,
        args_list: list[str],
    ) -> tuple[list[str], list[str], bcs.Digest]:
        """Invokes `sui move build` to build source project as part of publishing

        :param project_path: The sui move project path
        :type project_path: str
        :param args_list: Arguments to pass to `sui move build [args...]`
        :type args_list: list[str]
        :return: Returns base64 modules, dependencies and BCS Digest
        :rtype: tuple[list[str], list[str], bcs.Digest]
        """
        src_path = Path(os.path.expanduser(project_path))
        args_list = args_list if args_list else []
        compiled_package = publish_buildg(
            self.client.config.model.sui_binary,
            src_path,
            args_list,
        )
        dependencies = [
            bcs.Address.from_str(x if isinstance(x, str) else x.value)
            for x in compiled_package.dependencies
        ]
        digest = bcs.Digest.from_bytes(compiled_package.package_digest)
        return compiled_package.compiled_modules, dependencies, digest


if __name__ == "__main__":
    pass
