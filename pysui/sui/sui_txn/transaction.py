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

"""Sui high level Transaction Builder supports generation of TransactionKind and TransactionData."""

import base64
import os
from pathlib import Path
from typing import Optional, Union
import logging
from deprecated.sphinx import versionadded

from pysui import SuiAddress, ObjectID

from pysui.sui.sui_builders.base_builder import (
    _NativeTransactionBuilder,
    sui_builder,
)
from pysui.sui.sui_txn.signing_ms import SignerBlock, SigningMultiSig
import pysui.sui.sui_txn.transaction_builder as tx_builder
from pysui.sui.sui_txresults.single_tx import (
    TransactionConstraints,
)
from pysui.sui.sui_types import bcs
from pysui.sui.sui_types.collections import SuiArray
from pysui.sui.sui_types.scalars import (
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
            # handler_cls=TxInspectionResult,
            # handler_func="factory",
        )


@versionadded(version="0.26.0", reason="Refactor to support Async")
@versionadded(version="0.30.0", reason="Moved to transaction package.")
class _SuiTransactionBase:
    """."""

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
        client,
        merge_gas_budget: bool = False,
        initial_sender: Union[SuiAddress, SigningMultiSig] = False,
    ) -> None:
        """."""
        self.builder = tx_builder.ProgrammableTransactionBuilder()
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

    @versionadded(
        version="0.30.0", reason="Observing Sui ProtocolConfig constraints"
    )
    def verify_transaction(
        self,
    ) -> tuple[TransactionConstraints, TransactionConstraints]:
        """Verify TransactionKind values against protocol constraints.

        Returns both the current constraints and violations (if any)
        """
        return self.builder.verify_transaction(self.constraints)

    @versionadded(
        version="0.18.0", reason="Reuse for argument nested list recursion."
    )
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
                    if nest_depth >= bcs.TYPETAG_VECTOR_DEPTH_MAX:
                        raise ValueError(
                            f"vector is constrained to max {bcs.TYPETAG_VECTOR_DEPTH_MAX} depth. Found {nest_depth}."
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

    def _to_bytes_from_str(self, inbound: Union[str, SuiString]) -> list[int]:
        """Utility to convert base64 string to bytes then as list of u8."""
        return list(
            base64.b64decode(
                inbound if isinstance(inbound, str) else inbound.value
            )
        )

    def _compile_source(
        self,
        project_path: str,
        with_unpublished_dependencies: bool,
        skip_fetch_latest_git_deps: bool,
        legacy_digest: bool,
    ) -> tuple[list[str], list[str], bcs.Digest]:
        """."""
        src_path = Path(os.path.expanduser(project_path))
        compiled_package = publish_build(
            src_path,
            with_unpublished_dependencies,
            skip_fetch_latest_git_deps,
            legacy_digest,
        )
        modules = list(
            map(self._to_bytes_from_str, compiled_package.compiled_modules)
        )
        dependencies = [
            bcs.Address.from_str(x if isinstance(x, str) else x.value)
            for x in compiled_package.dependencies
        ]
        digest = bcs.Digest.from_bytes(compiled_package.package_digest)
        return modules, dependencies, digest


if __name__ == "__main__":
    pass
