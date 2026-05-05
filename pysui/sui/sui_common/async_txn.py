#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Unified async Sui Transaction builder — protocol-agnostic (GQL and gRPC)."""

import base64
from typing import Any, Callable, Optional, Union
from deprecated.sphinx import versionchanged

from pysui.sui.sui_common.trxn_base import (
    _TransactionBase,
    _SuiTransactionBase as txbase,
    FundsSource,
)
from pysui.sui.sui_common.txb_signing import SignerBlock, SigningMultiSig
from pysui.sui.sui_bcs import bcs
from pysui.sui.sui_common.txb_pure import PureInput
from pysui.sui.sui_types.scalars import SuiU64
import pysui.sui.sui_pgql.pgql_validators as tv
import pysui.sui.sui_pgql.pgql_types as pgql_type
from pysui.sui.sui_common.txb_gas import (
    compute_gas_budget,
    async_get_gas_data as _async_get_gas_data,
)
import pysui.sui.sui_common.sui_commands as cmd
import pysui.sui.sui_grpc.suimsgs.sui.rpc.v2 as sui_prot
from pysui.sui.sui_common.txb_tx_argparse import TxnArgParse, TxnArgMode
from pysui.sui.sui_common.executors.cache import AsyncObjectCache
from pysui.sui.sui_common.async_funcs import AsyncLRU


class AsyncSuiTransaction(txbase):
    """Protocol-agnostic async transaction builder for Sui (GQL and gRPC)."""

    _BUILD_BYTE_STR: str = "tx_bytestr"
    _SIG_ARRAY: str = "sig_array"

    def __init__(self, **kwargs) -> None:
        """Initialize the asynchronous SuiTransaction.

        :param client: The async protocol client (GqlProtocolClient or GrpcProtocolClient)
        :type client: PysuiClient
        :param initial_sender: Address of the transaction sender, defaults to None
        :type initial_sender: Union[str, SigningMultiSig], optional
        :param initial_sponsor: Optional sponsor address, defaults to None
        :type initial_sponsor: Union[str, SigningMultiSig], optional
        :param compress_inputs: Reuse identical inputs, defaults to True
        :type compress_inputs: Optional[bool], optional
        :param merge_gas_budget: Use all available gas not in use for paying, defaults to False
        :type merge_gas_budget: Optional[bool], optional
        :param mode: Argument parsing mode, defaults to TxnArgMode.EAGER
        :type mode: TxnArgMode, optional
        :param object_cache: Optional object cache for argument resolution, defaults to None
        :type object_cache: Optional[AsyncObjectCache], optional
        """
        mode: TxnArgMode = kwargs.pop("mode", TxnArgMode.EAGER)
        object_cache: Optional[AsyncObjectCache] = kwargs.pop("object_cache", None)
        initial_sender = kwargs.pop("initial_sender", None)
        initial_sponsor = kwargs.pop("initial_sponsor", None)
        merge_gas_budget = kwargs.pop("merge_gas_budget", False)
        # Consumed but not used: fetched async at build time
        kwargs.pop("txn_constraints", None)
        kwargs.pop("gas_price", None)

        client = kwargs["client"]
        # Call grandparent directly to bypass _SuiTransactionBase's sync fallbacks
        # (client.protocol() and client.current_gas_price are sync on some clients).
        # gas_price and txn_constraints are resolved lazily during build.
        _TransactionBase.__init__(
            self,
            client=client,
            compress_inputs=kwargs.pop("compress_inputs", True),
            builder=kwargs.pop("builder", None),
            arg_parser=kwargs.pop("arg_parser", None),
            txn_constraints=None,
            gas_price=None,
        )
        self._sig_block = SignerBlock(
            sender=initial_sender or client.config.active_address,
            sponsor=initial_sponsor,
        )
        self._merge_gas = merge_gas_budget
        self._executed = False
        self._mode = mode
        self._object_cache = object_cache
        self._argparse = TxnArgParse(client)

    @AsyncLRU(maxsize=256)
    async def _function_meta_args(
        self, target: str
    ) -> tuple[bcs.Address, str, str, int, list[pgql_type.OpenMoveTypeGQL]]:
        """Return the argument summary of a target Sui Move function.

        :param target: The triplet target string (package::module::function)
        :type target: str
        :return: package address, module, function, return count, parameter types
        :rtype: tuple
        """
        from pysui.sui.sui_common.txn_arg_encoder import grpc_to_raw_parameters

        package, package_module, package_function = (
            tv.TypeValidator.check_target_triplet(target)
        )
        try:
            result = await self.client.execute(
                command=cmd.GetFunction(
                    package=package,
                    module_name=package_module,
                    function_name=package_function,
                )
            )
            if result.is_ok():
                mfunc: sui_prot.GetFunctionResponse = result.result_data
                return (
                    bcs.Address.from_str(package),
                    package_module,
                    package_function,
                    len(mfunc.function.returns),
                    grpc_to_raw_parameters(mfunc),
                )
        except ValueError as ve:
            raise ValueError(f"{target} {ve.args}")
        raise ValueError(f"Unresolvable target {target}")

    async def target_function_summary(
        self, target: str
    ) -> tuple[bcs.Address, str, str, int, list[pgql_type.OpenMoveTypeGQL]]:
        """Return the argument summary of a target Sui Move function."""
        return await self._function_meta_args(target)

    async def _build_txn_data_address_balance(
        self,
        gas_budget: Optional[int] = None,
        txn_expires_after: Optional[int] = None,
    ) -> bcs.TransactionData:
        """Build TransactionData using address account balance for gas (UC7).

        :param gas_budget: Budget override; simulated if not provided, defaults to None
        :type gas_budget: Optional[int], optional
        :param txn_expires_after: Epoch ID for expiration start; defaults to current epoch
        :type txn_expires_after: Optional[int], optional
        :return: TransactionData with empty payment and ValidDuring expiration
        :rtype: bcs.TransactionData
        """
        _res = await self.client.execute(
            command=cmd.GetBasicCurrentEpochInfo(), timeout=30.0
        )
        if _res.is_ok():
            _cei: sui_prot.Epoch = _res.result_data
            min_epoch = txn_expires_after or _cei.epoch
            tx_kind = self.builder.finish_for_inspect()
            result = await self.client.execute(
                command=cmd.GetChainIdentifier(), timeout=30.0
            )
            if result.is_ok():
                chain_id = result.result_data
            else:
                raise ValueError("Error getting chain id")
            pay_addy = self.signer_block.payer_address
            if gas_budget is None:
                _res = await self.client.execute(
                    command=cmd.SimulateTransactionKind(
                        tx_kind=tx_kind,
                        tx_meta={"sender": pay_addy},
                        gas_selection=True,
                    ),
                    timeout=60.0,
                )
                if _res.is_ok():
                    gas_used = (
                        _res.result_data.transaction.effects.gas_used
                        or sui_prot.GasCostSummary()
                    )
                    gas_budget = compute_gas_budget(
                        gas_used.computation_cost or 0,
                        gas_used.storage_cost or 0,
                        _cei.reference_gas_price,
                    )
                else:
                    raise ValueError(_res.result_string)
            gas_data = bcs.GasData(
                [],
                bcs.Address.from_str(pay_addy),
                _cei.reference_gas_price,
                gas_budget,
            )
            return bcs.TransactionData(
                "V1",
                bcs.TransactionDataV1(
                    tx_kind,
                    bcs.Address.from_str(self.signer_block.sender_str),
                    gas_data,
                    bcs.TransactionExpiration.gen_valid_during_expiration(
                        min_epoch, min_epoch + 1, chain_id
                    ),
                ),
            )
        raise ValueError(_res.result_string)

    async def _build_txn_data(
        self,
        gas_budget: Optional[int] = None,
        use_gas_objects: Optional[list[Union[str, sui_prot.Object]]] = None,
        txn_expires_after: Optional[int] = None,
        use_account_for_gas: bool = False,
    ) -> bcs.TransactionData:
        """Generate the TransactionData structure.

        Routes to pure address balance (UC7) or standard coin selection based on
        use_account_for_gas and PTB GasCoin inspection results.
        """
        if isinstance(gas_budget, str):
            gas_budget = int(gas_budget) if gas_budget else None

        if not self.builder.commands and not self.builder.inputs:
            raise ValueError("Empty Transaction.")

        uses_gas_coin, gas_source_draw = self._inspect_ptb_for_gas_coin()

        if use_account_for_gas:
            if uses_gas_coin:
                raise ValueError(
                    "Hybrid gas payment (txer.gas + address balance) not yet "
                    "implemented — use coin-only gas payment"
                )
            return await self._build_txn_data_address_balance(
                gas_budget, txn_expires_after
            )

        # Standard coin path — fetch gas price lazily at build time
        if self._current_gas_price is None:
            _epoch_res = await self.client.execute(
                command=cmd.GetBasicCurrentEpochInfo(), timeout=30.0
            )
            if _epoch_res.is_ok():
                self._current_gas_price = _epoch_res.result_data.reference_gas_price
            else:
                raise ValueError(_epoch_res.result_string)

        obj_in_use: set[str] = set(self.builder.objects_registry.keys())
        tx_kind = self.builder.finish_for_inspect()
        gas_data: bcs.GasData = await _async_get_gas_data(
            signing=self.signer_block,
            client=self.client,
            budget=gas_budget,
            use_coins=use_gas_objects,
            objects_in_use=obj_in_use,
            active_gas_price=self.gas_price,
            tx_kind=tx_kind,
            merge_gas=self._merge_gas,
            gas_source_draw=gas_source_draw,
        )
        return bcs.TransactionData(
            "V1",
            bcs.TransactionDataV1(
                tx_kind,
                bcs.Address.from_str(self.signer_block.sender_str),
                gas_data,
                bcs.TransactionExpiration(
                    "None"
                    if not txn_expires_after
                    else bcs.TransactionExpiration("Epoch", txn_expires_after)
                ),
            ),
        )

    async def transaction_data(
        self,
        *,
        gas_budget: Optional[int] = None,
        use_gas_objects: Optional[list[Union[str, sui_prot.Object]]] = None,
        txn_expires_after: Optional[int] = None,
        use_account_for_gas: bool = False,
    ) -> bcs.TransactionData:
        """Construct a BCS TransactionData object.

        If gas_budget not provided, pysui will simulate the transaction to calculate it.
        If use_gas_objects not used, pysui will determine which gas objects to use.

        :param gas_budget: Specify the amount of gas for the transaction budget, defaults to None
        :type gas_budget: Optional[int], optional
        :param use_gas_objects: Specify gas object(s) (by ID or sui_prot.Object), defaults to None
        :type use_gas_objects: Optional[list[Union[str, sui_prot.Object]]], optional
        :param txn_expires_after: Specify the transaction expiration epoch ID, defaults to None
        :type txn_expires_after: Optional[int], optional
        :param use_account_for_gas: Pay gas from address account balance, defaults to False
        :type use_account_for_gas: bool, optional
        :return: The TransactionData BCS structure
        :rtype: bcs.TransactionData
        """
        return await self._build_txn_data(
            gas_budget, use_gas_objects, txn_expires_after, use_account_for_gas
        )

    async def build(
        self,
        *,
        gas_budget: Optional[int] = None,
        use_gas_objects: Optional[list[Union[str, sui_prot.Object]]] = None,
        txn_expires_after: Optional[int] = None,
        use_account_for_gas: bool = False,
    ) -> str:
        """Serialize the BCS TransactionData to a base64 string.

        :param gas_budget: Specify the amount of gas for the transaction budget, defaults to None
        :type gas_budget: Optional[int], optional
        :param use_gas_objects: Specify gas object(s) (by ID or sui_prot.Object), defaults to None
        :type use_gas_objects: Optional[list[Union[str, sui_prot.Object]]], optional
        :param txn_expires_after: Specify the transaction expiration epoch ID, defaults to None
        :type txn_expires_after: Optional[int], optional
        :param use_account_for_gas: Pay gas from address account balance, defaults to False
        :type use_account_for_gas: bool, optional
        :return: Base64 encoded transaction bytes
        :rtype: str
        """
        txn_data = await self.transaction_data(
            gas_budget=gas_budget,
            use_gas_objects=use_gas_objects,
            txn_expires_after=txn_expires_after,
            use_account_for_gas=use_account_for_gas,
        )
        return base64.b64encode(txn_data.serialize()).decode()

    @versionchanged(version="0.64.0", reason="Return dict instead of tuple")
    async def build_and_sign(
        self,
        *,
        gas_budget: Optional[int] = None,
        use_gas_objects: Optional[list[Union[str, sui_prot.Object]]] = None,
        txn_expires_after: Optional[int] = None,
        use_account_for_gas: bool = False,
    ) -> dict:
        """Serialize the BCS TransactionData to base64, sign, and return both.

        :param gas_budget: Specify the amount of gas for the transaction budget, defaults to None
        :type gas_budget: Optional[int], optional
        :param use_gas_objects: Specify gas object(s) (by ID or sui_prot.Object), defaults to None
        :type use_gas_objects: Optional[list[Union[str, sui_prot.Object]]], optional
        :param txn_expires_after: Specify the transaction expiration epoch ID, defaults to None
        :type txn_expires_after: Optional[int], optional
        :param use_account_for_gas: Pay gas from address account balance, defaults to False
        :type use_account_for_gas: bool, optional
        :return: Dict with ``tx_bytestr`` (base64 transaction bytes) and ``sig_array`` (list of base64 signature bytes)
        :rtype: dict[str, str]
        """
        txn_kind = await self.transaction_data(
            gas_budget=gas_budget,
            use_gas_objects=use_gas_objects,
            txn_expires_after=txn_expires_after,
            use_account_for_gas=use_account_for_gas,
        )
        tx_bytes = base64.b64encode(txn_kind.serialize()).decode()
        sigs = self.signer_block.get_signatures(
            config=self.client.config, tx_bytes=tx_bytes
        )
        return {self._BUILD_BYTE_STR: tx_bytes, self._SIG_ARRAY: sigs}

    async def split_coin(
        self,
        *,
        coin: Union[str, sui_prot.Object, bcs.Argument],
        amounts: list[Union[int, bcs.Argument]],
    ) -> Union[bcs.Argument, list[bcs.Argument]]:
        """Create a new coin(s) with the defined amount(s), split from the provided coin.

        :param coin: The coin to split from.
        :type coin: Union[str, sui_prot.Object, bcs.Argument]
        :param amounts: The list of amounts to split the coin out to
        :type amounts: list[Union[int, bcs.Argument]]
        :return: A Result or list of NestedResults to use in subsequent commands
        :rtype: Union[list[bcs.Argument], bcs.Argument]
        """
        parms = await self._argparse.build_args(
            [coin],
            txbase._SPLIT_COIN[:1],
            mode=self._mode,
            object_cache=self._object_cache,
        )
        encoded_amounts = [
            a if isinstance(a, bcs.Argument) else PureInput.as_input(SuiU64(a))
            for a in amounts
        ]
        return self.builder.split_coin(parms[0], encoded_amounts)

    async def merge_coins(
        self,
        *,
        merge_to: Union[str, sui_prot.Object, bcs.Argument],
        merge_from: list[Union[str, sui_prot.Object, bcs.Argument]],
    ) -> bcs.Argument:
        """Merge one or more coins to a primary coin.

        :param merge_to: The coin to merge other coins to
        :type merge_to: Union[str, sui_prot.Object, bcs.Argument]
        :param merge_from: One or more coins to merge to primary 'merge_to' coin
        :type merge_from: list[Union[str, sui_prot.Object, bcs.Argument]]
        :return: The command result. Can not be used as input in subsequent commands.
        :rtype: bcs.Argument
        """
        parms = await self._argparse.build_args(
            [merge_to],
            txbase._MERGE_COINS[:1],
            mode=self._mode,
            object_cache=self._object_cache,
        )
        resolved = [
            c
            if isinstance(c, bcs.Argument)
            else await self._argparse.parse(
                c,
                mode=self._mode,
                object_cache=self._object_cache,
                is_receiving=False,
                is_mutable=False,
            )
            for c in merge_from
        ]
        return self.builder.merge_coins(parms[0], resolved)

    async def split_coin_equal(
        self,
        *,
        coin: Union[str, sui_prot.Object, bcs.Argument],
        split_count: int,
        coin_type: Optional[str] = "0x2::sui::SUI",
    ) -> bcs.Argument:
        """Split one coin into equal parts and transfer all to transaction signer.

        :param coin: The coin to split
        :type coin: Union[str, sui_prot.Object, bcs.Argument]
        :param split_count: The number of parts to split coin into
        :type split_count: int
        :param coin_type: The coin type, defaults to "0x2::sui::SUI"
        :type coin_type: Optional[str], optional
        :return: Null argument — result not usable in subsequent commands
        :rtype: bcs.Argument
        """
        package, package_module, package_function, retcount, ars = (
            await self._function_meta_args(self._SPLIT_AND_KEEP)
        )
        parms = await self._argparse.build_args(
            [coin, split_count],
            ars,
            mode=self._mode,
            object_cache=self._object_cache,
        )
        type_arguments = [bcs.TypeTag.type_tag_from(coin_type)]
        return self.builder.move_call(
            target=package,
            arguments=parms,
            type_arguments=type_arguments,
            module=package_module,
            function=package_function,
            res_count=retcount,
        )

    @versionchanged(version="0.72.0", reason="Support recipient passed as Argument")
    async def transfer_objects(
        self,
        *,
        transfers: list[Union[str, sui_prot.Object, bcs.Argument]],
        recipient: Union[str, bcs.Argument],
    ) -> bcs.Argument:
        """Transfer one or more objects to a recipient.

        :param transfers: A list of objects to transfer
        :type transfers: list[Union[str, sui_prot.Object, bcs.Argument]]
        :param recipient: The recipient address
        :type recipient: Union[str, bcs.Argument]
        :return: The command result. Can NOT be used as input in subsequent commands.
        :rtype: bcs.Argument
        """
        parms = await self._argparse.build_args(
            [recipient],
            txbase._TRANSFER_OBJECTS[:1],
            mode=self._mode,
            object_cache=self._object_cache,
        )
        resolved = [
            t
            if isinstance(t, bcs.Argument)
            else await self._argparse.parse(
                t,
                mode=self._mode,
                object_cache=self._object_cache,
                is_receiving=False,
                is_mutable=False,
            )
            for t in transfers
        ]
        return self.builder.transfer_objects(parms[0], resolved)

    async def transfer_sui(
        self,
        *,
        recipient: str,
        from_coin: Union[str, sui_prot.Object, bcs.Argument],
        amount: Optional[int] = None,
    ) -> bcs.Argument:
        """Transfer a Sui coin object to a recipient.

        :param recipient: The recipient address
        :type recipient: str
        :param from_coin: The Sui coin to take amount from and transfer
        :type from_coin: Union[str, sui_prot.Object, bcs.Argument]
        :param amount: Optional amount to transfer; entire coin if not specified, defaults to None
        :type amount: Optional[int], optional
        :return: The command result. Can NOT be used as input in subsequent commands.
        :rtype: bcs.Argument
        """
        parms = await self._argparse.build_args(
            [recipient, from_coin, amount],
            txbase._TRANSFER_SUI,
            mode=self._mode,
            object_cache=self._object_cache,
        )
        return self.builder.transfer_sui(*parms)

    async def public_transfer_object(
        self,
        *,
        object_to_send: Union[str, sui_prot.Object, bcs.Argument],
        recipient: str,
        object_type: str,
    ) -> bcs.Argument:
        """Public transfer of any object with KEY and STORE attributes.

        :param object_to_send: Object being transferred
        :type object_to_send: Union[str, sui_prot.Object, bcs.Argument]
        :param recipient: Address for recipient of object_to_send
        :type recipient: str
        :param object_type: Type arguments
        :type object_type: str
        :return: Result of command which is non-reusable
        :rtype: bcs.Argument
        """
        package, package_module, package_function = (
            tv.TypeValidator.check_target_triplet(self._PUBLIC_TRANSFER)
        )
        package = bcs.Address.from_str(package)
        return self.builder.move_call(
            target=package,
            arguments=await self._argparse.build_args(
                [object_to_send, recipient],
                txbase._PUBLIC_TRANSFER_OBJECTS,
                mode=self._mode,
                object_cache=self._object_cache,
            ),
            type_arguments=[bcs.TypeTag.type_tag_from(object_type)],
            module=package_module,
            function=package_function,
            res_count=0,
        )

    async def make_move_vector(
        self,
        *,
        items: list[Union[str, sui_prot.Object, bcs.ObjectArg]],
        item_type: Optional[str] = None,
    ) -> bcs.Argument:
        """Convert a list of objects to a Sui Move vector of item_type."""
        if all(isinstance(x, bcs.ObjectArg) for x in items):
            type_tag = (
                bcs.OptionalTypeTag(bcs.TypeTag.type_tag_from(item_type))
                if item_type
                else bcs.OptionalTypeTag()
            )
            return self.builder.make_move_vector(type_tag, items)

        resolved = [
            item
            if isinstance(item, bcs.Argument)
            else await self._argparse.parse(
                item,
                mode=self._mode,
                object_cache=self._object_cache,
                is_receiving=False,
                is_mutable=False,
            )
            for item in items
        ]
        type_tag = (
            bcs.OptionalTypeTag(bcs.TypeTag.type_tag_from(item_type))
            if item_type
            else bcs.OptionalTypeTag()
        )
        return self.builder.make_move_vector(type_tag, resolved)

    async def move_call(
        self,
        *,
        target: str,
        arguments: list[Any],
        type_arguments: Optional[list] = None,
    ) -> Union[bcs.Argument, list[bcs.Argument]]:
        """Invoke a Move contract call.

        :param target: String triple in form "package_object_id::module_name::function_name"
        :type target: str
        :param arguments: Arguments passed to the Move function
        :type arguments: list[Any]
        :param type_arguments: Optional list of type arguments for Move generics, defaults to None
        :type type_arguments: Optional[list], optional
        :return: Result(s) usable in subsequent commands depending on the function called
        :rtype: Union[bcs.Argument, list[bcs.Argument]]
        """
        type_arguments = type_arguments if type_arguments else []
        package, package_module, package_function, retcount, ars = (
            await self._function_meta_args(target)
        )
        type_arguments = [bcs.TypeTag.type_tag_from(x) for x in type_arguments]
        parms = await self._argparse.build_args(
            arguments,
            ars,
            mode=self._mode,
            object_cache=self._object_cache,
        )
        return self.builder.move_call(
            target=package,
            arguments=parms,
            type_arguments=type_arguments,
            module=package_module,
            function=package_function,
            res_count=retcount,
        )

    async def balance_from(
        self,
        *,
        amount: int,
        source: FundsSource = FundsSource.SENDER,
        coin_type: Optional[str] = None,
    ) -> bcs.Argument:
        """Withdraw Coin<T> from transaction source Sender or Sponsor account.

        :param amount: The amount of `coin_type` to withdraw from `source`
        :type amount: int
        :param source: Source of funds, defaults to FundsSource.SENDER
        :type source: FundsSource, optional
        :param coin_type: The package::module::type of coin; defaults to "0x2::sui::SUI"
        :type coin_type: Optional[str], optional
        :return: The Coin<T> argument — usable in subsequent commands
        :rtype: bcs.Argument
        """
        type_tag = (
            bcs.TypeTag.type_tag_from(coin_type)
            if coin_type
            else bcs.StructTag.sui_coin()
        )
        wdt = bcs.FundsWithdrawal(
            bcs.Reservation("Amount", amount),
            bcs.WithdrawalType("Balance", type_tag),
            bcs.WithdrawFrom(source.name),
        )
        return self.builder.move_call(
            target=bcs.Address.from_str("0x2"),
            module="coin",
            function="redeem_funds",
            arguments=[wdt],
            type_arguments=[type_tag],
        )

    async def optional_object(
        self,
        *,
        optional_object: Union[str, sui_prot.Object, bcs.Argument],
        is_receiving: Optional[bool] = False,
        is_shared_mutable: Optional[bool] = False,
        type_arguments: Optional[list] = None,
    ) -> bcs.Argument:
        """Wrap an object as a Move Option.

        :param optional_object: Object to wrap
        :type optional_object: Union[str, sui_prot.Object, bcs.Argument]
        :param is_receiving: True if this is a receiving type, defaults to False
        :type is_receiving: Optional[bool], optional
        :param is_shared_mutable: True if this is a shared mutable type, defaults to False
        :type is_shared_mutable: Optional[bool], optional
        :param type_arguments: Move type strings, defaults to None
        :type type_arguments: Optional[list], optional
        :return: Argument usable in subsequent commands (e.g. move_call arguments)
        :rtype: bcs.Argument
        """
        type_arguments = type_arguments if type_arguments else []
        function = "some"
        if isinstance(optional_object, bcs.Argument):
            parms = [optional_object]
        elif isinstance(optional_object, (str, sui_prot.Object)):
            parms = [
                await self._argparse.parse(
                    optional_object,
                    mode=self._mode,
                    object_cache=self._object_cache,
                    is_receiving=is_receiving,
                    is_mutable=is_shared_mutable,
                )
            ]
        elif not optional_object:
            function = "none"
            parms = []
        type_arguments = [bcs.TypeTag.type_tag_from(x) for x in type_arguments]
        return self.builder.move_call(
            target=self._STD_FRAMEWORK,
            arguments=parms,
            type_arguments=type_arguments,
            module="option",
            function=function,
            res_count=1,
        )

    async def stake_coin(
        self,
        *,
        coins: list[Union[str, sui_prot.Object, bcs.Argument]],
        validator_address: str,
        amount: Optional[int] = None,
    ) -> bcs.Argument:
        """Stake one or more coins to a specific validator.

        :param coins: One or more coins to stake
        :type coins: list[Union[str, sui_prot.Object, bcs.Argument]]
        :param validator_address: The validator to stake coins to
        :type validator_address: str
        :param amount: Amount from coins to stake; all coin if not stated, defaults to None
        :type amount: Optional[int], optional
        :return: The command result
        :rtype: bcs.Argument
        """
        package, package_module, package_function, retcount, ars = (
            await self._function_meta_args(self._STAKE_REQUEST_TARGET)
        )
        parms = await self._argparse.build_args(
            [self._SYSTEMSTATE_OBJECT.value, coins, amount, validator_address],
            ars,
            mode=self._mode,
            object_cache=self._object_cache,
        )
        parms[1] = await self.make_move_vector(
            items=parms[1], item_type="0x2::coin::Coin<0x2::sui::SUI>"
        )
        return self.builder.move_call(
            target=package,
            arguments=parms,
            type_arguments=[],
            module=package_module,
            function=package_function,
            res_count=retcount,
        )

    async def unstake_coin(
        self, *, staked_coin: Union[str, sui_prot.Object]
    ) -> bcs.Argument:
        """Unstake a Staked Sui Coin.

        :param staked_coin: The coin being unstaked
        :type staked_coin: Union[str, sui_prot.Object]
        :return: The Result argument
        :rtype: bcs.Argument
        """
        package, package_module, package_function, retcount, ars = (
            await self._function_meta_args(self._UNSTAKE_REQUEST_TARGET)
        )
        parms = await self._argparse.build_args(
            [self._SYSTEMSTATE_OBJECT.value, staked_coin],
            ars,
            mode=self._mode,
            object_cache=self._object_cache,
        )
        return self.builder.move_call(
            target=package,
            arguments=parms,
            type_arguments=[],
            module=package_module,
            function=package_function,
            res_count=retcount,
        )

    async def publish(
        self, *, project_path: str, args_list: Optional[list[str]] = None
    ) -> bcs.Argument:
        """Create a publish command.

        :param project_path: Path to project folder
        :type project_path: str
        :param args_list: Additional `sui move build` arguments, defaults to None
        :type args_list: Optional[list[str]], optional
        :return: A command result (UpgradeCap) to use in a subsequent transfer command
        :rtype: bcs.Argument
        """
        modules, dependencies, _digest = self._compile_source(project_path, args_list)
        return self.builder.publish(modules, dependencies)

    async def publish_upgrade(
        self,
        *,
        project_path: str,
        upgrade_cap: Union[str, sui_prot.Object],
        args_list: Optional[list[str]] = None,
    ) -> bcs.Argument:
        """Authorize, publish, and commit an upgrade of a package.

        :param project_path: Path to Move project
        :type project_path: str
        :param upgrade_cap: ID or sui_prot.Object of UpgradeCap
        :type upgrade_cap: Union[str, sui_prot.Object]
        :param args_list: Arguments for compilation of project, defaults to None
        :type args_list: Optional[list[str]], optional
        :raises ValueError: If fetching UpgradeCap has error or returns no data
        :raises ValueError: If object is not a valid UpgradeCap
        :return: Non-reusable result
        :rtype: bcs.Argument
        """
        args_list = args_list if args_list else []
        modules, dependencies, digest = self._compile_source(project_path, args_list)
        if isinstance(upgrade_cap, str):
            result = await self.client.execute(
                command=cmd.GetObject(object_id=upgrade_cap)
            )
            if result.is_err():
                raise ValueError(f"Validating upgrade cap: {result.result_string}")
            elif result.result_data is None or isinstance(
                result.result_data, pgql_type.NoopGQL
            ):
                raise ValueError(
                    f"Fetching upgrade cap {upgrade_cap} returned no data."
                )
            upgrade_cap = result.result_data
        _, _, package_struct = tv.TypeValidator.check_target_triplet(
            upgrade_cap.object_type
        )
        jdict = upgrade_cap.json.to_dict()
        if (
            jdict.keys() >= {"package", "version", "policy"}
            and package_struct == "UpgradeCap"
        ):
            cap_obj_arg, policy_arg = await self._argparse.build_args(
                [upgrade_cap, jdict["policy"]],
                txbase._PUBLISH_UPGRADE,
                mode=self._mode,
                object_cache=self._object_cache,
            )
            cap_arg = len(self.builder.inputs)
            auth_cmd = self.builder.authorize_upgrade(
                cap_obj_arg, policy_arg, PureInput.as_input(digest)
            )
            return self.builder.commit_upgrade(
                bcs.Argument("Input", cap_arg),
                self.builder.publish_upgrade(
                    modules,
                    dependencies,
                    bcs.Address.from_str(jdict["package"]),
                    auth_cmd,
                ),
            )
        else:
            raise ValueError("Not a valid upgrade cap.")

    async def custom_upgrade(
        self,
        *,
        project_path: str,
        package_id: str,
        upgrade_cap: str,
        authorize_upgrade_fn: Callable[
            ["AsyncSuiTransaction", Any, bcs.Digest], bcs.Argument
        ],
        commit_upgrade_fn: Callable[
            ["AsyncSuiTransaction", Any, bcs.Argument], bcs.Argument
        ],
        args_list: Optional[list[str]] = None,
    ) -> bcs.Argument:
        """Support for custom authorization and upgrade commitments.

        :param project_path: Path to project folder
        :type project_path: str
        :param package_id: The current package ID being upgraded
        :type package_id: str
        :param upgrade_cap: The upgrade capability object ID
        :type upgrade_cap: str
        :param authorize_upgrade_fn: Async callable that generates custom authorization move_call
        :type authorize_upgrade_fn: Callable[[AsyncSuiTransaction, Any, bcs.Digest], bcs.Argument]
        :param commit_upgrade_fn: Async callable that generates custom commitment move_call
        :type commit_upgrade_fn: Callable[[AsyncSuiTransaction, Any, bcs.Argument], bcs.Argument]
        :param args_list: Additional `sui move build` arguments, defaults to None
        :type args_list: Optional[list[str]], optional
        :return: The result argument
        :rtype: bcs.Argument
        """
        modules, dependencies, digest = self._compile_source(project_path, args_list)
        if isinstance(upgrade_cap, str):
            result = await self.client.execute(
                command=cmd.GetObject(object_id=upgrade_cap)
            )
            if result.is_err():
                raise ValueError(f"Validating upgrade cap: {result.result_string}")
            upgrade_cap = result.result_data
        _, _, package_struct = tv.TypeValidator.check_target_triplet(
            upgrade_cap.object_type
        )
        jdict = upgrade_cap.json.to_dict()
        if (
            jdict.keys() >= {"package", "version", "policy"}
            and package_struct == "UpgradeCap"
        ):
            upgrade_ticket = await authorize_upgrade_fn(self, upgrade_cap, digest)
            package_id = bcs.Address.from_str(package_id)
            receipt = self.builder.publish_upgrade(
                modules, dependencies, package_id, upgrade_ticket
            )
            return await commit_upgrade_fn(self, upgrade_cap, receipt)
        else:
            raise ValueError("Not a valid upgrade cap.")
