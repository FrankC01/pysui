#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Sui high level Transaction Builder supports generation of TransactionKind and TransactionData."""


import base64
import hashlib
import os
from enum import IntEnum
from pathlib import Path
from typing import Any, Optional, Union, cast
import logging

import base58

from pysui.sui.sui_common.types import TransactionConstraints

from .client import PysuiClient

from pysui.sui.sui_common.txn_signing import SignerBlock, SigningMultiSig
import pysui.sui.sui_common.txn_transaction_builder as tx_builder
import pysui.sui.sui_pgql.pgql_types as pgql_type
from pysui.sui.sui_bcs import bcs
from pysui.sui.sui_utils import publish_buildg2
from pysui.sui.sui_common.instrumentation import instrumented, sync_instrumented

# Standard library logging setup
logger = logging.getLogger(__name__)


class _TransactionBase:
    """."""

    _TRANSACTION_GAS_ARGUMENT: bcs.Argument = bcs.Argument("GasCoin")
    _SYSTEMSTATE_OBJECT: str = "0x5"
    _STAKE_REQUEST_TARGET: str = "0x3::sui_system::request_add_stake_mul_coin"
    _UNSTAKE_REQUEST_TARGET: str = "0x3::sui_system::request_withdraw_stake"
    _STANDARD_UPGRADE_CAP_TYPE: str = "0x2::package::UpgradeCap"
    _UPGRADE_CAP_SUFFIX: str = "UpgradeCap"
    _SPLIT_AND_KEEP: str = "0x2::pay::divide_and_keep"
    _SEND_FUNDS_TARGET: str = "0x2::coin::send_funds"
    _STD_FRAMEWORK: bcs.Address = bcs.Address.from_str("0x1")

    _FUND_ADDRESS_ACCUMULATOR = [
        pgql_type.OpenMoveTypeGQL(
            signature=pgql_type.OpenMoveTypeSignatureGQL(
                ref=None,
                body=pgql_type.OpenMoveDatatypeBodyGQL(
                    package="0x2", module="coin", type_name="Coin", type_parameters=[]
                ),
            ),
            repr="",
        ),
        pgql_type.OpenMoveTypeGQL(
            signature=pgql_type.OpenMoveTypeSignatureGQL(
                ref=None,
                body=pgql_type.OpenMoveScalarBodyGQL(scalar_type="address"),
            ),
            repr="",
        ),
    ]
    _PUBLIC_TRANSFER: str = "0x2::transfer::public_transfer"
    _PAY_GAS: int = 4000000
    _BUILD_BYTE_STR: str = "tx_bytestr"
    _SIG_ARRAY: str = "sig_array"

    _SPLIT_COIN = [
        pgql_type.OpenMoveTypeGQL(
            signature=pgql_type.OpenMoveTypeSignatureGQL(
                ref="&mut",
                body=pgql_type.OpenMoveDatatypeBodyGQL(
                    package="0x2", module="sui", type_name="SUI", type_parameters=[]
                ),
            ),
            repr="",
        ),
        pgql_type.OpenMoveTypeGQL(
            signature=pgql_type.OpenMoveTypeSignatureGQL(
                ref=None,
                body=pgql_type.OpenMoveVectorBodyGQL(
                    inner=pgql_type.OpenMoveScalarBodyGQL(scalar_type="u64")
                ),
            ),
            repr="",
        ),
    ]

    _MERGE_COINS = [
        pgql_type.OpenMoveTypeGQL(
            signature=pgql_type.OpenMoveTypeSignatureGQL(
                ref="&mut",
                body=pgql_type.OpenMoveDatatypeBodyGQL(
                    package="0x2", module="sui", type_name="SUI", type_parameters=[]
                ),
            ),
            repr="",
        ),
        pgql_type.OpenMoveTypeGQL(
            signature=pgql_type.OpenMoveTypeSignatureGQL(
                ref=None,
                body=pgql_type.OpenMoveVectorBodyGQL(
                    inner=pgql_type.OpenMoveDatatypeBodyGQL(
                        package="0x2", module="sui", type_name="SUI", type_parameters=[]
                    )
                ),
            ),
            repr="",
        ),
    ]

    _TRANSFER_OBJECTS = [
        pgql_type.OpenMoveTypeGQL(
            signature=pgql_type.OpenMoveTypeSignatureGQL(
                ref=None,
                body=pgql_type.OpenMoveScalarBodyGQL(scalar_type="address"),
            ),
            repr="",
        ),
        pgql_type.OpenMoveTypeGQL(
            signature=pgql_type.OpenMoveTypeSignatureGQL(
                ref=None,
                body=pgql_type.OpenMoveVectorBodyGQL(
                    inner=pgql_type.OpenMoveDatatypeBodyGQL(
                        package="0x2", module="sui", type_name="SUI", type_parameters=[]
                    )
                ),
            ),
            repr="",
        ),
    ]

    _TRANSFER_SUI = [
        pgql_type.OpenMoveTypeGQL(
            signature=pgql_type.OpenMoveTypeSignatureGQL(
                ref=None,
                body=pgql_type.OpenMoveScalarBodyGQL(scalar_type="address"),
            ),
            repr="",
        ),
        pgql_type.OpenMoveTypeGQL(
            signature=pgql_type.OpenMoveTypeSignatureGQL(
                ref="&mut",
                body=pgql_type.OpenMoveDatatypeBodyGQL(
                    package="0x2", module="sui", type_name="SUI", type_parameters=[]
                ),
            ),
            repr="",
        ),
        pgql_type.OpenMoveTypeGQL(
            signature=pgql_type.OpenMoveTypeSignatureGQL(
                ref=None,
                body=pgql_type.OpenMoveScalarBodyGQL(scalar_type="u64"),
            ),
            repr="",
        ),
    ]

    _PUBLIC_TRANSFER_OBJECTS = [
        pgql_type.OpenMoveTypeGQL(
            signature=pgql_type.OpenMoveTypeSignatureGQL(
                ref="&mut",
                body=pgql_type.OpenMoveDatatypeBodyGQL(
                    package="0x2", module="sui", type_name="SUI", type_parameters=[]
                ),
            ),
            repr="",
        ),
        pgql_type.OpenMoveTypeGQL(
            signature=pgql_type.OpenMoveTypeSignatureGQL(
                ref=None,
                body=pgql_type.OpenMoveScalarBodyGQL(scalar_type="address"),
            ),
            repr="",
        ),
    ]

    _MAKE_MOVE_VEC = [
        pgql_type.OpenMoveTypeGQL(
            signature=pgql_type.OpenMoveTypeSignatureGQL(
                ref=None,
                body=pgql_type.OpenMoveVectorBodyGQL(
                    inner=pgql_type.OpenMoveDatatypeBodyGQL(
                        package="0x2", module="sui", type_name="SUI", type_parameters=[]
                    )
                ),
            ),
            repr="",
        ),
    ]

    _PUBLISH_UPGRADE = [
        pgql_type.OpenMoveTypeGQL(
            signature=pgql_type.OpenMoveTypeSignatureGQL(
                ref="&mut",
                body=pgql_type.OpenMoveDatatypeBodyGQL(
                    package="0x2", module="sui", type_name="SUI", type_parameters=[]
                ),
            ),
            repr="",
        ),
        pgql_type.OpenMoveTypeGQL(
            signature=pgql_type.OpenMoveTypeSignatureGQL(
                ref=None,
                body=pgql_type.OpenMoveScalarBodyGQL(scalar_type="u8"),
            ),
            repr="",
        ),
    ]

    @sync_instrumented("pysui.sui.sui_common.txn_base._TransactionBase.__init__")
    def __init__(
        self,
        *,
        client: PysuiClient,
        compress_inputs: Optional[bool] = True,
        builder: Optional[Any] = None,
        arg_parser: Optional[Any] = None,
        txn_constraints: Optional[TransactionConstraints] = None,
        gas_price: Optional[int] = None,
    ):
        """."""
        self.builder = builder or tx_builder.ProgrammableTransactionBuilder(
            compress_inputs=compress_inputs if compress_inputs is not None else True
        )
        self._argparse = arg_parser
        self.client = client
        self.constraints = txn_constraints
        self._current_gas_price = gas_price

    @property
    @sync_instrumented("pysui.sui.sui_common.txn_base._TransactionBase.gas")
    def gas(self) -> bcs.Argument:
        """Enables use of gas reference as parameters in commands."""
        return self._TRANSACTION_GAS_ARGUMENT

    @property
    @sync_instrumented("pysui.sui.sui_common.txn_base._TransactionBase.gas_price")
    def gas_price(self) -> Optional[int]:
        """Returns the current gas price for the chain."""
        return self._current_gas_price

    @gas_price.setter
    @sync_instrumented("pysui.sui.sui_common.txn_base._TransactionBase.gas_price")
    def gas_price(self, new_price: int):
        """Set the gas price."""
        self._current_gas_price = new_price

    @staticmethod
    @sync_instrumented("pysui.sui.sui_common.txn_base._TransactionBase._any_arg_is_gas_coin")
    def _any_arg_is_gas_coin(args) -> bool:
        return any(a.enum_name == "GasCoin" for a in args)

    @sync_instrumented("pysui.sui.sui_common.txn_base._TransactionBase._accumulate_split_coin_draw")
    def _accumulate_split_coin_draw(self, cmd_val, inputs_list: list) -> tuple[bool, int]:
        """Process SplitCoin command for GasCoin usage and gas draw amount."""
        if cmd_val.FromCoin.enum_name != "GasCoin":
            return self._any_arg_is_gas_coin(cmd_val.Amount), 0
        _log = logging.getLogger(__name__)
        draw = 0
        for amount_arg in cmd_val.Amount:
            if amount_arg.enum_name != "Input":
                _log.warning(
                    "Dynamic amount in SplitCoin(GasCoin): "
                    "gas-source draw not tracked for this amount"
                )
                continue
            idx = amount_arg.value
            if idx >= len(inputs_list):
                continue
            call_arg = inputs_list[idx]
            if call_arg.enum_name != "Pure":
                _log.warning(
                    "Non-pure input in SplitCoin(GasCoin): "
                    "gas-source draw not tracked for this amount"
                )
                continue
            draw += int.from_bytes(bytes(call_arg.value), "little")
        return True, draw

    @sync_instrumented("pysui.sui.sui_common.txn_base._TransactionBase._inspect_ptb_for_gas_coin")
    def _inspect_ptb_for_gas_coin(self) -> tuple[bool, int]:
        """Inspect builder commands for GasCoin usage and accumulate gas-source draw.

        :return: (uses_gas_coin, gas_source_draw) where uses_gas_coin is True if any
            argument in any command references Argument::GasCoin, and gas_source_draw
            is the sum of pure-int amounts from SplitCoin(GasCoin, ...) commands.
        :rtype: tuple[bool, int]
        """
        uses_gas_coin = False
        gas_source_draw = 0
        inputs_list = list(self.builder.inputs.values())

        for cmd in self.builder.commands:
            cmd_name = cmd.enum_name
            cmd_val = cmd.value
            if cmd_name == "SplitCoin":
                used, draw = self._accumulate_split_coin_draw(cmd_val, inputs_list)
                uses_gas_coin = uses_gas_coin or used
                gas_source_draw += draw
            elif cmd_name == "MergeCoins":
                uses_gas_coin = uses_gas_coin or cmd_val.ToCoin.enum_name == "GasCoin" or self._any_arg_is_gas_coin(cmd_val.FromCoins)
            elif cmd_name == "TransferObjects":
                uses_gas_coin = uses_gas_coin or self._any_arg_is_gas_coin(cmd_val.Objects) or cmd_val.Address.enum_name == "GasCoin"
            elif cmd_name == "MoveCall":
                uses_gas_coin = uses_gas_coin or self._any_arg_is_gas_coin(cmd_val.Arguments)
            elif cmd_name == "MakeMoveVec":
                uses_gas_coin = uses_gas_coin or self._any_arg_is_gas_coin(cmd_val.Vector)

        return uses_gas_coin, gas_source_draw


class FundsSource(IntEnum):
    """Enumeration of Sender or Sponser funds source."""

    SENDER = 0
    SPONSOR = 1


class _SuiTransactionBase(_TransactionBase):
    """SuiTransaction GQL base object."""

    @sync_instrumented("pysui.sui.sui_common.txn_base._SuiTransactionBase.__init__")
    def __init__(
        self,
        *,
        client: PysuiClient,
        compress_inputs: Optional[bool] = True,
        initial_sender: Optional[Union[str, SigningMultiSig]] = None,
        initial_sponsor: Optional[Union[str, SigningMultiSig]] = None,
        builder: Optional[Any] = None,
        arg_parser: Optional[Any] = None,
        txn_constraints: Optional[TransactionConstraints] = None,
        gas_price: Optional[int] = None,
    ) -> None:
        """__init__ Initialize transaction base.

        :param client: protocol client
        :type client: PysuiClient
        :param compress_inputs: reuse same inputs, defaults to True
        :type compress_inputs: Optional[bool], optional
        :param initial_sender: initial sender of transactions, defaults to None
        :type initial_sender: Union[str, SigningMultiSig], optional
        :param initial_sponsor: initial sponser of transactions, defaults to None
        :type initial_sponsor: Union[str, SigningMultiSig], optional
        :param builder: move call parameter builder, defaults to None
        :type builder: Optional[Any], optional
        :param arg_parser: transaction command argument parser validator, defaults to None
        :type arg_parser: Optional[Any], optional
        :param txn_constraints: set transaction constraints, defaults to None
        :type txn_constraints: Optional[TransactionConstraints], optional
        :param gas_price: set gas price, defaults to None
        :type gas_price: Optional[int], optional
        """
        super().__init__(
            client=client,
            compress_inputs=compress_inputs,
            builder=builder,
            arg_parser=arg_parser,
            txn_constraints=txn_constraints
            or client.protocol().transaction_constraints,  # type: ignore[attr-defined]
            gas_price=gas_price or client.current_gas_price,
        )
        self._sig_block = SignerBlock(
            sender=initial_sender or client.config.active_address,
            sponsor=initial_sponsor,
        )
        self._executed = False

    @property
    @sync_instrumented("pysui.sui.sui_common.txn_base._SuiTransactionBase.signer_block")
    def signer_block(self) -> SignerBlock:
        """Returns the signers block."""
        return self._sig_block

    @classmethod
    @sync_instrumented("pysui.sui.sui_common.txn_base._SuiTransactionBase.digest_from_bytes")
    def digest_from_bytes(cls, transaction_data_bytes: bytes) -> str:
        """Return the base58 encoded digest from transaction byte string.

        :param transaction_data_bytes: Bytes from serialized TransactionData
        :type transaction_data_bytes: bytes
        :return: Sui transaction digest
        :rtype: str
        """
        return base58.b58encode(
            hashlib.blake2b(
                b"TransactionData::" + transaction_data_bytes,
                digest_size=32,
            ).digest()
        ).decode()

    @classmethod
    @sync_instrumented("pysui.sui.sui_common.txn_base._SuiTransactionBase.digest_from_b64str")
    def digest_from_b64str(cls, transaction_data_bytes_str: str) -> str:
        """Return the base58 encoded digest from transaction base64 encoded string.

        :param transaction_data_bytes_str: Base64 encoded serialized TransactionData
        :type transaction_data_bytes_str: str
        :return: Sui transaction digest
        :rtype: str
        """
        return cls.digest_from_bytes(base64.b64decode(transaction_data_bytes_str))

    @sync_instrumented("pysui.sui.sui_common.txn_base._SuiTransactionBase.raw_kind")
    def raw_kind(self) -> bcs.TransactionKind:
        """Returns the TransactionKind object hierarchy of inputs, returns and commands.

        This is useful for reviewing the transaction that will be executed or inspected.
        """
        return self.builder.finish_for_inspect()

    @sync_instrumented("pysui.sui.sui_common.txn_base._SuiTransactionBase.build_for_dryrun")
    def build_for_dryrun(self) -> str:
        """Returns a base64 string that can be used in dry running transaction.

        :return: base64 string representation of underlying TransactionKind
        :rtype: str
        """
        return base64.b64encode(self.raw_kind().serialize()).decode()

    @sync_instrumented("pysui.sui.sui_common.txn_base._SuiTransactionBase._compile_source")
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
        assert self.client.config.model.sui_binary is not None
        compiled_package = publish_buildg2(
            self.client.config.model.sui_binary,
            src_path,
            args_list,
            self.client.config.active_profile,
        )
        if isinstance(compiled_package, Exception):
            err: BaseException = compiled_package
            raise err
        dependencies = [
            bcs.Address.from_str(x if isinstance(x, str) else x.value)
            for x in compiled_package.dependencies
        ]
        digest = bcs.Digest.from_bytes(compiled_package.package_digest)
        return compiled_package.compiled_modules, dependencies, digest  # type: ignore[return-value]


if __name__ == "__main__":
    pass
