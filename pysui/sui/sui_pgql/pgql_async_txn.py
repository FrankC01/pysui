#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Pysui Transaction builder that leverages Sui GraphQL."""

import base64
from typing import Any, Callable, Optional, Union
from deprecated.sphinx import versionchanged, versionadded, deprecated
from pysui.sui.sui_pgql.pgql_clients import SuiGQLClient
from pysui.sui.sui_common.trxn_base import _SuiTransactionBase as txbase
from pysui.sui.sui_common.trxn_base import FundsSource

from pysui.sui.sui_bcs import bcs
from pysui.sui.sui_common.txb_pure import PureInput
from pysui.sui.sui_types.scalars import SuiU64
import pysui.sui.sui_pgql.pgql_validators as tv
from pysui.sui.sui_common.txb_gas import compute_gas_budget, async_get_gas_data as _async_get_gas_data
import pysui.sui.sui_pgql.pgql_query as qn
import pysui.sui.sui_pgql.pgql_types as pgql_type
import pysui.sui.sui_common.sui_commands as cmd
import pysui.sui.sui_grpc.suimsgs.sui.rpc.v2 as sui_prot
from pysui.sui.sui_common.txb_tx_argparse import TxnArgParse, TxnArgMode
from pysui.sui.sui_common.executors.cache import AsyncObjectCache

from pysui.sui.sui_common.async_funcs import AsyncLRU


class AsyncSuiTransaction(txbase):
    """."""

    _BUILD_BYTE_STR: str = "tx_bytestr"
    _SIG_ARRAY: str = "sig_array"

    def __init__(
        self,
        **kwargs,
    ) -> None:
        """__init__ Initialize the asynchronous SuiTransaction.

        :param client: The asynchronous SuiGQLClient
        :type client: GqlProtocolClient
        :param initial_sender: The address of the sender of the transaction, defaults to None
        :type initial_sender: Union[str, SigningMultiSig], optional
        :param compress_inputs: Reuse identical inputs, defaults to False
        :type compress_inputs: bool,optional
        :param merge_gas_budget: If True will take available gas not in use for paying for transaction, defaults to False
        :type merge_gas_budget: bool, optional
        """
        mode: TxnArgMode = kwargs.pop("mode", TxnArgMode.EAGER)
        object_cache: Optional[AsyncObjectCache] = kwargs.pop("object_cache", None)
        super().__init__(**kwargs)
        self._mode = mode
        self._object_cache = object_cache
        self._argparse = TxnArgParse(self.client)

    @AsyncLRU(maxsize=256)
    async def _function_meta_args(
        self, target: str
    ) -> tuple[bcs.Address, str, str, int, list[pgql_type.OpenMoveTypeGQL]]:
        """_function_meta_args Returns the argument summary of a target sui move function

        :param target: The triplet target string
        :type target: str
        :return: The function parameters as OpenMoveTypeGQL list
        :rtype: list[pgql_type.OpenMoveTypeGQL]
        """
        package, package_module, package_function = (
            tv.TypeValidator.check_target_triplet(target)
        )

        from pysui.sui.sui_common.txn_arg_encoder import grpc_to_raw_parameters

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
        raise ValueError(f"Unresolvable target {target}")

    async def target_function_summary(
        self, target: str
    ) -> tuple[bcs.Address, str, str, int, list[pgql_type.OpenMoveTypeGQL]]:
        """Returns the argument summary of a target sui move function."""
        return await self._function_meta_args(target)

    async def _build_txn_data_address_balance(
        self,
        gas_budget: Optional[int] = None,
        txn_expires_after: Optional[int] = None,
    ) -> bcs.TransactionData:
        """Build TransactionData using address account balance for gas (UC7 — pure address balance).

        :param gas_budget: Budget override; simulated if not provided, defaults to None
        :type gas_budget: Optional[int], optional
        :param txn_expires_after: Epoch ID for expiration start; defaults to current epoch
        :type txn_expires_after: Optional[int], optional
        :return: TransactionData with empty payment and ValidDuring expiration
        :rtype: bcs.TransactionData
        """
        _res = await self.client.execute(
            command=cmd.GetBasicCurrentEpochInfo()
        )
        if _res.is_ok():
            _cei: sui_prot.Epoch = _res.result_data
            min_epoch = txn_expires_after or _cei.epoch
            tx_kind = self.builder.finish_for_inspect()
            chain_id = self.client.chain_id()
            pay_addy = self.signer_block.payer_address
            if gas_budget is None:
                _res = await self.client.execute(
                    command=cmd.SimulateTransactionKind(
                        tx_kind=tx_kind,
                        tx_meta={"sender": pay_addy},
                        gas_selection=True,
                    )
                )
                if _res.is_ok():
                    gas_used = (_res.result_data.transaction.effects.gas_used
                                or sui_prot.GasCostSummary())
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
        use_gas_objects: Optional[list[Union[str, pgql_type.SuiCoinObjectGQL]]] = None,
        txn_expires_after: Optional[int] = None,
        use_account_for_gas: bool = False,
    ) -> bcs.TransactionData:
        """Generate the TransactionData structure.

        Routes to pure address balance (UC7) or standard coin selection based on
        use_account_for_gas and PTB GasCoin inspection results.
        """
        # Backward compatibility: accept str gas_budget from callers not yet updated
        if isinstance(gas_budget, str):
            gas_budget = int(gas_budget) if gas_budget else None

        # Inspect PTB for GasCoin usage (routing) and gas-source draw (budget inflation)
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

        # Standard coin path
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
        use_gas_objects: Optional[list[Union[str, pgql_type.SuiCoinObjectGQL]]] = None,
        txn_expires_after: Optional[int] = None,
        use_account_for_gas: bool = False,
    ) -> bcs.TransactionData:
        """transaction_data Construct a BCS TransactionData object.

        If gas_budget not provided, pysui will simulate the transaction to calculate it.

        If use_gas_objects not used, pysui will determine which gas objects to use to
        pay for the transaction.

        :param gas_budget: Specify the amount of gas for the transaction budget, defaults to None
        :type gas_budget: Optional[int], optional
        :param use_gas_objects: Specify gas object(s) (by ID or SuiCoinObjectGQL), defaults to None
        :type use_gas_objects: Optional[list[Union[str, pgql_type.SuiCoinObjectGQL]]], optional
        :param txn_expires_after: Specify the transaction expiration epoch ID, defaults to None
        :type txn_expires_after: Optional[int],optional
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
        use_gas_objects: Optional[list[Union[str, pgql_type.SuiCoinObjectGQL]]] = None,
        txn_expires_after: Optional[int] = None,
        use_account_for_gas: bool = False,
    ) -> str:
        """build After creating the BCS TransactionData, serialize to base64 string and return.

        :param gas_budget: Specify the amount of gas for the transaction budget, defaults to None
        :type gas_budget: Optional[int], optional
        :param use_gas_objects: Specify gas object(s) (by ID or SuiCoinObjectGQL), defaults to None
        :type use_gas_objects: Optional[list[Union[str, pgql_type.SuiCoinObjectGQL]]], optional
        :param txn_expires_after: Specify the transaction expiration epoch ID, defaults to None
        :type txn_expires_after: Optional[int],optional
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
        use_gas_objects: Optional[list[Union[str, pgql_type.SuiCoinObjectGQL]]] = None,
        txn_expires_after: Optional[int] = None,
        use_account_for_gas: bool = False,
    ) -> dict:
        """build After creating the BCS TransactionKind, serialize to base64 string, create signatures and return.

        :param gas_budget: Specify the amount of gas for the transaction budget, defaults to None
        :type gas_budget: Optional[int], optional
        :param use_gas_objects: Specify gas object(s) (by ID or SuiCoinObjectGQL), defaults to None
        :type use_gas_objects: Optional[list[Union[str, pgql_type.SuiCoinObjectGQL]]], optional
        :param txn_expires_after: Specify the transaction expiration epoch ID, defaults to None
        :type txn_expires_after: Optional[int],optional
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
        coin: Union[str, pgql_type.ObjectReadGQL, bcs.Argument],
        amounts: list[Union[int, bcs.Argument]],
    ) -> Union[bcs.Argument, list[bcs.Argument]]:
        """split_coin Creates a new coin(s) with the defined amount(s), split from the provided coin.

        Note: Returns the result that it can be used in subsequent commands. If only one amount
        is provided, a standard Result can be used as a singular argument to another command.
        But if more than 1 amount. For example  you can index to get a singular value or use the whole
        list.

        .. code-block:: python

            # Transfer all coins to one recipient
            txer = client.transaction()
            scres = txer.split_coin(coin=primary_coin, amounts=[1000000000, 1000000000])
            txer.transfer_objects(transfers=scres, recipient=client.config.active_address)

            # OR only transfer less than all
            txer.transfer_objects(transfers=[scres[0]],recipient=client.config.active_address)

        :param coin: The coin address (object id) to split from.
        :type coin: Union[str, pgql_type.ObjectReadGQL, bcs.Argument]
        :param amounts: The amount or list of amounts to split the coin out to
        :type amounts: list[Union[int, bcs.Argument]]
        :return: A result or list of results types to use in subsequent commands
        :rtype: Union[list[bcs.Argument],bcs.Argument]
        """

        parms = await self._argparse.build_args(
            [coin], txbase._SPLIT_COIN[:1], mode=self._mode, object_cache=self._object_cache,
        )
        encoded_amounts = [
            a if isinstance(a, bcs.Argument)
            else PureInput.as_input(SuiU64(a))
            for a in amounts
        ]
        return self.builder.split_coin(parms[0], encoded_amounts)

    async def merge_coins(
        self,
        *,
        merge_to: Union[str, pgql_type.ObjectReadGQL, bcs.Argument],
        merge_from: list[Union[str, pgql_type.ObjectReadGQL, bcs.Argument]],
    ) -> bcs.Argument:
        """merge_coins Merges one or more coins to a primary coin.

        :param merge_to: The coin to merge other coins to
        :type merge_to: Union[str, pgql_type.ObjectReadGQL, bcs.Argument]
        :param merge_from: One or more coins to merge to primary 'merge_to' coin
        :type merge_from: list[Union[str, pgql_type.ObjectReadGQL, bcs.Argument]]
        :return: The command result. Can not be used as input in subsequent commands.
        :rtype: bcs.Argument
        """
        parms = await self._argparse.build_args(
            [merge_to], txbase._MERGE_COINS[:1], mode=self._mode, object_cache=self._object_cache,
        )
        resolved = [
            c if isinstance(c, bcs.Argument)
            else await self._argparse.parse(
                c, mode=self._mode, object_cache=self._object_cache,
                is_receiving=False, is_mutable=False,
            )
            for c in merge_from
        ]
        return self.builder.merge_coins(parms[0], resolved)

    async def split_coin_equal(
        self,
        *,
        coin: Union[str, pgql_type.ObjectReadGQL, bcs.Argument],
        split_count: int,
        coin_type: Optional[str] = "0x2::sui::SUI",
    ) -> bcs.Argument:
        """split_coin_equal Splits a Sui coin into equal parts and transfers to transaction signer.

        :param coin: The coin to split
        :type coin: Union[str, bcs.Argument]
        :param split_count: The number of parts to split coin into
        :type split_count: int
        :param coin_type: The coin type, defaults to a Sui coin type
        :type coin_type: Optional[str], optional
        :return: The command result. Because all splits are automagically transferred to
            signer, the result is not usable as input to subseqent commands.
        :rtype: bcs.Argument
        """
        package, package_module, package_function, retcount, ars = (
            await self._function_meta_args(self._SPLIT_AND_KEEP)
        )

        parms = await self._argparse.build_args(
            [coin, split_count], ars, mode=self._mode, object_cache=self._object_cache,
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
        transfers: list[Union[str, pgql_type.ObjectReadGQL, bcs.Argument]],
        recipient: Union[str, bcs.Argument],
    ) -> bcs.Argument:
        """transfer_objects Transfers one or more objects to a recipient.

        :param transfers: A list or SuiArray of objects to transfer
        :type transfers: list[Union[str, pgql_type.ObjectReadGQL, bcs.Argument]]
        :param recipient: The recipient address that will receive the objects being transfered
        :type recipient: Union[str, bcs.Argument]
        :return: The command result. Can NOT be used as input in subsequent commands.
        :rtype: bcs.Argument
        """
        parms = await self._argparse.build_args(
            [recipient], txbase._TRANSFER_OBJECTS[:1],
            mode=self._mode, object_cache=self._object_cache,
        )
        resolved = [
            t if isinstance(t, bcs.Argument)
            else await self._argparse.parse(
                t, mode=self._mode, object_cache=self._object_cache,
                is_receiving=False, is_mutable=False,
            )
            for t in transfers
        ]
        return self.builder.transfer_objects(parms[0], resolved)

    async def transfer_sui(
        self,
        *,
        recipient: str,
        from_coin: Union[str, pgql_type.ObjectReadGQL, bcs.Argument],
        amount: Optional[int] = None,
    ) -> bcs.Argument:
        """transfer_sui Transfers a Sui coin object to a recipient.

        :param recipient: The recipient address that will receive the Sui coin being transfered
        :type recipient: str
        :param from_coin: The Sui coin to transfer
        :type from_coin: Union[str, bcs.Argument]
        :param amount: Optional amount to transfer. Entire coin if not specified, defaults to None
        :type amount: Optional[int], optional
        :raises ValueError: If unable to fetch the from_coin
        :raises ValueError: If from_coin is invalid
        :return: The command result. Can NOT be used as input in subsequent commands.
        :rtype: bcs.Argument
        """
        parms = await self._argparse.build_args(
            [recipient, from_coin, amount], txbase._TRANSFER_SUI,
            mode=self._mode, object_cache=self._object_cache,
        )
        return self.builder.transfer_sui(*parms)

    async def public_transfer_object(
        self,
        *,
        object_to_send: Union[str, pgql_type.ObjectReadGQL, bcs.Argument],
        recipient: str,
        object_type: str,
    ) -> bcs.Argument:
        """public_transfer_object Public transfer of any object with KEY and STORE Attributes.

        :param object_to_send: Object being transferred
        :type object_to_send: Union[str, bcs.Argument]
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
        items: list[str, pgql_type.ObjectReadGQL, bcs.ObjectArg],
        item_type: Optional[str] = None,
    ) -> bcs.Argument:
        """Create a call to convert a list of objects to a Sui 'vector' of item_type."""
        if all(isinstance(x, bcs.ObjectArg) for x in items):
            if item_type:
                type_tag = bcs.OptionalTypeTag(bcs.TypeTag.type_tag_from(item_type))
            else:
                type_tag = bcs.OptionalTypeTag()
            return self.builder.make_move_vector(type_tag, items)

        resolved = [
            item if isinstance(item, bcs.Argument)
            else await self._argparse.parse(
                item, mode=self._mode, object_cache=self._object_cache,
                is_receiving=False, is_mutable=False,
            )
            for item in items
        ]
        if item_type:
            type_tag = bcs.OptionalTypeTag(bcs.TypeTag.type_tag_from(item_type))
        else:
            type_tag = bcs.OptionalTypeTag()
        return self.builder.make_move_vector(type_tag, resolved)

    async def move_call(
        self,
        *,
        target: str,
        arguments: list[Any],
        type_arguments: Optional[list] = None,
    ) -> Union[bcs.Argument, list[bcs.Argument]]:
        """move_call Creates a command to invoke a move contract call. May or may not return results.

        :param target: String triple in form "package_object_id::module_name::function_name"
        :type target: str
        :param arguments: Arguments that are passed to the move function
        :type arguments: list[Any]
        :param type_arguments: Optional list of type arguments for move function generics, defaults to None
        :type type_arguments: Optional[list], optional
        :return: The result which may or may not be used in subequent commands depending on the
            move method being called.
        :rtype: Union[bcs.Argument, list[bcs.Argument]]
        """
        type_arguments = type_arguments if type_arguments else []
        # Validate and get target meta arguments
        package, package_module, package_function, retcount, ars = (
            await self._function_meta_args(target)
        )
        type_arguments = [bcs.TypeTag.type_tag_from(x) for x in type_arguments]
        parms = await self._argparse.build_args(
            arguments, ars, mode=self._mode, object_cache=self._object_cache,
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
        """balance_from_sender Withdraws Coin<T> from transaction source Sender or Sponsor account.

        :param amount: The amount of `coin_type` to withdraw from `source`
        :type amount: int
        :param source: Source of funds, defaults to FundsSource.SENDER
        :type source: FundsSource, optional
        :param coin_type: The package::module::type of coin to withdraw fron, if None defaults to "0x2::sui::SUI"
        :type coin_type: _type_, optional
        :return: The argument result (representing the Coin<T>). Can be used in subsequent commands.
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
        optional_object: Union[str, pgql_type.ObjectReadGQL, bcs.Argument],
        is_receiving: Optional[bool] = False,
        is_shared_mutable: Optional[bool] = False,
        type_arguments: Optional[list] = None,
    ) -> bcs.Argument:
        """."""
        type_arguments = type_arguments if type_arguments else []
        function = "some"
        # Handle other than argument
        if isinstance(optional_object, bcs.Argument):
            parms = [optional_object]
        elif isinstance(optional_object, (str, pgql_type.ObjectReadGQL)):
            parms = [
                await self._argparse.parse(
                    optional_object, mode=self._mode, object_cache=self._object_cache,
                    is_receiving=is_receiving, is_mutable=is_shared_mutable,
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
        coins: list[Union[str, pgql_type.ObjectReadGQL, bcs.Argument]],
        validator_address: str,
        amount: Optional[int] = None,
    ) -> bcs.Argument:
        """stake_coin Stakes one or more coins to a specific validator.

        :param coins: One or more coins to stake.
        :type coins: list[str, pgql_type.ObjectReadGQL, bcs.Argument]
        :param validator_address: The validator to stake coins to
        :type validator_address: str
        :param amount: Amount from coins to stake. If not stated, all coin will be staked, defaults to None
        :type amount: Optional[int], optional
        :return: The command result.
        :rtype: bcs.Argument
        """
        # Fetch pre-build meta arg summary
        package, package_module, package_function, retcount, ars = (
            await self._function_meta_args(self._STAKE_REQUEST_TARGET)
        )
        # Validate arguments
        parms = await self._argparse.build_args(
            [self._SYSTEMSTATE_OBJECT.value, coins, amount, validator_address],
            ars,
            mode=self._mode,
            object_cache=self._object_cache,
        )
        # Create a move vector of coins
        parms[1] = await self.make_move_vector(
            items=parms[1], item_type="0x2::coin::Coin<0x2::sui::SUI>"
        )
        # Make the call
        return self.builder.move_call(
            target=package,
            arguments=parms,
            type_arguments=[],
            module=package_module,
            function=package_function,
            res_count=retcount,
        )

    async def unstake_coin(
        self, *, staked_coin: Union[str, pgql_type.SuiStakedCoinGQL]
    ) -> bcs.Argument:
        """unstake_coin Unstakes a Staked Sui Coin.

        :param staked_coin: The coin being unstaked
        :type staked_coin: Union[str, pgql_type.SuiStakedCoinGQL]
        :return: The Result argument
        :rtype: bcs.Argument
        """
        # Fetch pre-build meta arg summary
        package, package_module, package_function, retcount, ars = (
            await self._function_meta_args(self._UNSTAKE_REQUEST_TARGET)
        )
        # Validate arguments
        parms = await self._argparse.build_args(
            [
                self._SYSTEMSTATE_OBJECT.value,
                staked_coin,
            ],
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
        """publish Creates a publish command.

        :param project_path: path to project folder
        :type project_path: str
        :param args_list: Additional `sui move build` arguments, defaults to None
        :type args_list: Optional[list[str]], optional
        :return: A command result (UpgradeCap) that should used in a subsequent transfer commands
        :rtype: bcs.Argument
        """
        modules, dependencies, _digest = self._compile_source(project_path, args_list)
        return self.builder.publish(modules, dependencies)

    async def publish_upgrade(
        self,
        *,
        project_path: str,
        upgrade_cap: Union[str, pgql_type.ObjectReadGQL],
        args_list: Optional[list[str]] = None,
    ) -> bcs.Argument:
        """publish_upgrade Authorize, publish and commit upgrade of package.

        :param project_path: Path to move project
        :type project_path: str
        :param upgrade_cap: Id or ObjectRead of UpgradeCap
        :type upgrade_cap: Union[str, pgql_type.ObjectReadGQL]
        :param args_list: Arguments for compilation of project, defaults to None
        :type args_list: Optional[list[str]], optional
        :raises ValueError: If fetching UpgradeCap has error
        :raises ValueError: If can't verify UpgradeCap
        :return: Non reusable result
        :rtype: bcs.Argument
        """
        args_list = args_list if args_list else []
        # Compile Source
        modules, dependencies, digest = self._compile_source(project_path, args_list)
        # Resolve upgrade cap to ObjectRead if needed
        if isinstance(upgrade_cap, str):
            result = await self.client.execute(
                command=cmd.GetObject(object_id=upgrade_cap)
            )
            if result.is_err():
                raise ValueError(f"Validating upgrade cap: {result.result_string}")
            elif isinstance(result.result_data, pgql_type.NoopGQL):
                raise ValueError(
                    f"Fetching upgrade cap {upgrade_cap} returned no data."
                )

            upgrade_cap = result.result_data
        # Isolate the struct type from supposed UpgradeCap
        _, _, package_struct = tv.TypeValidator.check_target_triplet(
            upgrade_cap.object_type
        )
        # If all upgradecap items check out
        if (
            upgrade_cap.content.keys() >= {"package", "version", "policy"}
            and package_struct == "UpgradeCap"
        ):
            # Prep args
            cap_obj_arg, policy_arg = await self._argparse.build_args(
                [upgrade_cap, upgrade_cap.content["policy"]],
                txbase._PUBLISH_UPGRADE,
                mode=self._mode,
                object_cache=self._object_cache,
            )
            # Capture input offsets to preserve location of upgrade_cap ObjectArg
            cap_arg = len(self.builder.inputs)
            # Authorize, publish and commit the upgrade
            auth_cmd = self.builder.authorize_upgrade(
                cap_obj_arg, policy_arg, PureInput.as_input(digest)
            )
            return self.builder.commit_upgrade(
                bcs.Argument("Input", cap_arg),
                self.builder.publish_upgrade(
                    modules,
                    dependencies,
                    bcs.Address.from_str(upgrade_cap.content["package"]),
                    auth_cmd,
                ),
            )
        else:
            raise ValueError(f"Not a valid upgrade cap.")

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
        """custom_upgrade Support for custom authorization and commitments.

        :param project_path: path to project folder
        :type project_path: str
        :param package_id: The current package id that is being upgraded
        :type package_id: str
        :param upgrade_cap: The upgrade capability object
        :type upgrade_cap: str
        :param authorize_upgrade_fn: Function to be called that generates custom authorization 'move_call'
        :type authorize_upgrade_fn: Callable[[&quot;AsyncSuiTransaction&quot;, Any, bcs.Digest], bcs.Argument]
        :param commit_upgrade_fn: Function to be called that generates custom commitment 'move_call'
        :type commit_upgrade_fn: Callable[[&quot;AsyncSuiTransactions&quot;, Any, bcs.Argument], bcs.Argument]
        :param args_list: Additional `sui move build` arguments, defaults to None
        :type args_list: Optional[list[str]], optional
        :return: The result argument
        :rtype: bcs.Argument
        """
        modules, dependencies, digest = self._compile_source(project_path, args_list)
        # Resolve upgrade cap to ObjectRead if needed
        if isinstance(upgrade_cap, str):
            result = await self.client.execute(
                command=cmd.GetObject(object_id=upgrade_cap)
            )
            if result.is_err():
                raise ValueError(f"Validating upgrade cap: {result.result_string}")

            upgrade_cap = result.result_data
        # Isolate the struct type from supposed UpgradeCap
        _, _, package_struct = tv.TypeValidator.check_target_triplet(
            upgrade_cap.object_type
        )
        # If all upgradecap items check out
        if (
            upgrade_cap.content.keys() >= {"package", "version", "policy"}
            and package_struct == "UpgradeCap"
        ):
            upgrade_ticket = authorize_upgrade_fn(self, upgrade_cap, digest)
            # Extrack the auth_cmd cap input
            package_id = bcs.Address.from_str(package_id)
            # Upgrade
            receipt = self.builder.publish_upgrade(
                modules, dependencies, package_id, upgrade_ticket
            )
            return commit_upgrade_fn(self, upgrade_cap, receipt)
        else:
            raise ValueError(f"Not a valid upgrade cap.")
