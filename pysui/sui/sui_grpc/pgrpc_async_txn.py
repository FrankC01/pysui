#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Pysui Transaction builder that leverages Sui gRPC."""

import base64
from typing import Any, Callable, Optional, Union
from pysui.sui.sui_common.trxn_base import _SuiTransactionBase as txbase
from pysui.sui.sui_common.txb_pure import PureInput
import pysui.sui.sui_pgql.pgql_types as pgql_type
from pysui.sui.sui_bcs import bcs
import pysui.sui.sui_pgql.pgql_validators as tv
import pysui.sui.sui_grpc.pgrpc_requests as rn
from pysui.sui.sui_common.async_funcs import AsyncLRU

# TODO: gRPC argbase implementation
import pysui.sui.sui_grpc.pgrpc_txn_async_argb as argbase

import pysui.sui.sui_grpc.pgrpc_txb_gas as gd
import pysui.sui.sui_grpc.pgrpc_utils as utils
import pysui.sui.sui_grpc.suimsgs.sui.rpc.v2beta2 as sui_prot


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
        :type client: SuiGrpcClient
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
        :param merge_gas_budget: global gas budget for each transaction, defaults to False
        :type merge_gas_budget: Optional[bool], optional
        :param txn_constraints: set transaction constraints, defaults to None
        :type txn_constraints: Optional[TransactionConstraints], optional
        :param gas_price: set gas price, defaults to None
        :type gas_price: Optional[int], optional
        """
        super().__init__(**kwargs)
        self._argparse = argbase.AsyncResolvingArgParser(self.client)

    @AsyncLRU(maxsize=256)
    async def _function_meta_args(
        self, target: str
    ) -> tuple[bcs.Address, str, str, int, pgql_type.MoveArgSummary]:
        """_function_meta_args Returns the argument summary of a target sui move function

        :param target: The triplet target string
        :type target: str
        :return: The meta function argument summary
        :rtype: pgql_type.MoveArgSummary
        """
        package, package_module, package_function = (
            tv.TypeValidator.check_target_triplet(target)
        )

        try:
            result = await self.client.execute(
                request=rn.GetFunction(
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
                    utils.normalize_move_func(mfunc),
                )
        except ValueError as ve:
            raise ValueError(f"{target} {ve.args}")

    async def target_function_summary(
        self, target: str
    ) -> tuple[bcs.Address, str, str, int, pgql_type.MoveArgSummary]:
        """Returns the argument summary of a target sui move function."""
        return await self._function_meta_args(target)

    async def _build_txn_data(
        self,
        gas_budget: str = "",
        use_gas_objects: Optional[list[Union[str, sui_prot.Object]]] = None,
        txn_expires_after: Optional[int] = None,
    ) -> Union[bcs.TransactionData, ValueError]:
        """Generate the TransactionData structure."""
        if not self.builder.commands and not self.builder.inputs:
            raise ValueError("Empty Transaction.")

        obj_in_use: set[str] = set(self.builder.objects_registry.keys())
        tx_kind = self.builder.finish_for_inspect()
        gas_data: bcs.GasData = await gd.async_get_gas_data(
            signing=self.signer_block,
            client=self.client,
            budget=gas_budget if not gas_budget else int(gas_budget),
            use_coins=use_gas_objects,
            objects_in_use=obj_in_use,
            active_gas_price=self.gas_price,
            tx_kind=tx_kind,
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
        gas_budget: Optional[str] = None,
        use_gas_objects: Optional[list[Union[str, sui_prot.Object]]] = None,
        txn_expires_after: Optional[int] = None,
    ) -> bcs.TransactionData:
        """transaction_data Construct a BCS TransactionData object.

        If gas_budget not provided, pysui will call DryRunTransactionBlock to calculate.

        If use_gas_objects not used, pysui will determine which gas objects to use to
        pay for the transaction.

        :param gas_budget: Specify the amount of gas for the transaction budget, defaults to None
        :type gas_budget: Optional[str], optional
        :param use_gas_objects: Specify gas object(s) (by ID or sui_prot.Object), defaults to None
        :type use_gas_objects: Optional[list[Union[str, sui_prot.Object]]], optional
        :param txn_expires_after: Specify the transaction expiration epoch ID, defaults to None
        :type txn_expires_after: Optional[int],optional
        :return: The TransactionData BCS structure
        :rtype: bcs.TransactionData
        """
        return await self._build_txn_data(
            gas_budget, use_gas_objects, txn_expires_after
        )

    async def build(
        self,
        *,
        gas_budget: Optional[str] = None,
        use_gas_objects: Optional[list[Union[str, sui_prot.Object]]] = None,
        txn_expires_after: Optional[int] = None,
    ) -> str:
        """build After creating the BCS TransactionData, serialize to base64 string and return.

        :param gas_budget: Specify the amount of gas for the transaction budget, defaults to None
        :type gas_budget: Optional[str], optional
        :param use_gas_objects: Specify gas object(s) (by ID or sui_prot.Object), defaults to None
        :type use_gas_objects: Optional[list[Union[str, sui_prot.Object]]], optional
        :param txn_expires_after: Specify the transaction expiration epoch ID, defaults to None
        :type txn_expires_after: Optional[int],optional
        :return: Base64 encoded transaction bytes
        :rtype: str
        """
        txn_data = await self.transaction_data(
            gas_budget=gas_budget,
            use_gas_objects=use_gas_objects,
            txn_expires_after=txn_expires_after,
        )
        return base64.b64encode(txn_data.serialize()).decode()

    async def build_and_sign(
        self,
        *,
        gas_budget: Optional[str] = None,
        use_gas_objects: Optional[list[Union[str, sui_prot.Object]]] = None,
        txn_expires_after: Optional[int] = None,
    ) -> dict:
        """build After creating the BCS TransactionKind, serialize to base64 string, create signatures and return.

        :param gas_budget: Specify the amount of gas for the transaction budget, defaults to None
        :type gas_budget: Optional[str], optional
        :param use_gas_objects: Specify gas object(s) (by ID or sui_prot.Object), defaults to None
        :type use_gas_objects: Optional[list[Union[str, sui_prot.Object]]], optional
        :param txn_expires_after: Specify the transaction expiration epoch ID, defaults to None
        :type txn_expires_after: Optional[int],optional
        :return: Dict of
            {
                "tx_bytestr": base64 encoded transaction bytes,
                "sig_array": array of base64 encoded signature bytes

            }
        :rtype: dict[str, str]
        """
        txn_kind = await self.transaction_data(
            gas_budget=gas_budget,
            use_gas_objects=use_gas_objects,
            txn_expires_after=txn_expires_after,
        )
        tx_bytes = base64.b64encode(txn_kind.serialize()).decode()
        sigs = self.signer_block.get_signatures(
            config=self.client.config, tx_bytes=tx_bytes
        )
        return {self._BUILD_BYTE_STR: tx_bytes, self._SIG_ARRAY: sigs}

    async def split_coin(
        self,
        *,
        coin: str | sui_prot.Object | bcs.Argument,
        amounts: list[Union[int, bcs.Argument]],
    ) -> bcs.Argument | list[bcs.Argument]:
        """split_coin Creates a new coin(s) with the defined amount(s), split from the provided coin.

        Note: Returns the result that it can be used in subsequent commands. If only one amount
        is provided, a standard Result can be used as a singular argument to another command.
        But if more than 1 amount. For example  you can index to get a singular value or use the whole
        list.

        .. code-block:: python

            # Transfer all coins to one recipient
            txer = SuiTransaction(client)
            scres = await txer.split_coin(coin=txer.gas, amounts=[1000000000, 1000000000])
            await txer.transfer_objects(transfers=scres, recipient=client.config.active_address)

            # OR only transfer less than all
            await txer.transfer_objects(transfers=[scres[0]],recipient=client.config.active_address)

        If the amount list contains only one element then a single Result argument is returned, otherwise
        a list of NestedResult arguments are returned.

        :param coin: The coin to split from.
        :type coin: Union[str, sui_prot.Object, bcs.Argument]
        :param amounts: The list of amounts to split the coin out to
        :type amounts: list[Union[int, bcs.Argument]]
        :return: A Result or list of  NestedResults types to use in subsequent commands
        :rtype: Union[list[bcs.Argument],bcs.Argument]
        """
        parms = await self._argparse.build_args([coin, amounts], txbase._SPLIT_COIN)
        return self.builder.split_coin(parms[0], parms[1:][0])

    async def split_coin_equal(
        self,
        *,
        coin: str | sui_prot.Object | bcs.Argument,
        split_count: int,
        coin_type: Optional[str] = "0x2::sui::SUI",
    ) -> bcs.Argument:
        """split_coin_equal Split one coin to equal amounts

        :param coin: Identies the coin object or generic gas argument to split from.
        :type coin: str | sui_prot.Object | bcs.Argument
        :param split_count: how many coins to split `coin` into
        :type split_count: int
        :param coin_type: Type move type of coin being split, defaults to "0x2::sui::SUI"
        :type coin_type: str, optional
        :return: Null argument. Can not be used in subsequent commands.
        :rtype: bcs.Argument
        """
        package, package_module, package_function, retcount, ars = (
            await self._function_meta_args(self._SPLIT_AND_KEEP)
        )

        parms = await self._argparse.build_args([coin, split_count], ars)

        type_arguments = [bcs.TypeTag.type_tag_from(coin_type)]
        return self.builder.move_call(
            target=package,
            arguments=parms,
            type_arguments=type_arguments,
            module=package_module,
            function=package_function,
            res_count=retcount,
        )

    async def merge_coins(
        self,
        *,
        merge_to: str | sui_prot.Object | bcs.Argument,
        merge_from: list[str | sui_prot.Object | bcs.Argument],
    ) -> bcs.Argument:
        """merge_coins Merges one or more coins to a primary coin.

        :param merge_to: The coin to merge other coins to
        :type merge_to: Union[str, sui_prot.Object, bcs.Argument]
        :param merge_from: One or more coins to merge to primary 'merge_to' coin
        :type merge_from: list[Union[str, sui_prot.Object, bcs.Argument]]
        :return: The command result. Can not be used as input in subsequent commands.
        :rtype: bcs.Argument
        """
        parms = await self._argparse.build_args(
            [merge_to, merge_from], txbase._MERGE_COINS
        )

        return self.builder.merge_coins(parms[0], parms[1:][0])

    async def transfer_objects(
        self,
        *,
        transfers: list[str | sui_prot.Object | bcs.Argument],
        recipient: Union[str, bcs.Argument],
    ) -> bcs.Argument:
        """transfer_objects Transfers one or more objects to a recipient.

        :param transfers: A list or SuiArray of objects to transfer
        :type transfers: list[Union[str, sui_prot.Object,  bcs.Argument]]
        :param recipient: The recipient address that will receive the objects being transfered
        :type recipient: Union[str, bcs.Argument]
        :return: The command result. Can NOT be used as input in subsequent commands.
        :rtype: bcs.Argument
        """
        parms = await self._argparse.build_args(
            [recipient, transfers], txbase._TRANSFER_OBJECTS
        )
        return self.builder.transfer_objects(parms[0], parms[1:][0])

    async def transfer_sui(
        self,
        *,
        recipient: str,
        from_coin: str | sui_prot.Object | bcs.Argument,
        amount: Optional[int] = None,
    ) -> bcs.Argument:
        """transfer_sui Transfers a Sui coin object to a recipient.

        :param recipient: The recipient address that will receive the Sui coin being transfered
        :type recipient: str
        :param from_coin: The Sui coin to take amount from and transfer
        :type from_coin: Union[str, sui_prot.Object, bcs.Argument]
        :param amount: Optional amount to transfer. Entire coin if not specified, defaults to None
        :type amount: Optional[int], optional
        :raises ValueError: If unable to fetch the from_coin
        :raises ValueError: If from_coin is invalid
        :return: The command result. Can NOT be used as input in subsequent commands.
        :rtype: bcs.Argument
        """
        parms = await self._argparse.build_args(
            [recipient, from_coin, amount], txbase._TRANSFER_SUI
        )
        return self.builder.transfer_sui(*parms)

    async def public_transfer_object(
        self,
        *,
        object_to_send: Union[str, sui_prot.Object, bcs.Argument],
        recipient: str,
        object_type: str,
    ) -> bcs.Argument:
        """public_transfer_object Public transfer of any object with KEY and STORE Attributes.

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
            ),
            type_arguments=[bcs.TypeTag.type_tag_from(object_type)],
            module=package_module,
            function=package_function,
            res_count=0,
        )

    async def make_move_vector(
        self,
        *,
        items: list[str | sui_prot.Object | bcs.ObjectArg],
        item_type: Optional[str] = None,
    ) -> bcs.Argument:
        """Create a call to convert a list of objects to a Sui 'vector' of item_type."""
        if all(isinstance(x, bcs.ObjectArg) for x in items):
            if item_type:
                type_tag = bcs.OptionalTypeTag(bcs.TypeTag.type_tag_from(item_type))
            else:
                type_tag = bcs.OptionalTypeTag()
            return self.builder.make_move_vector(type_tag, items)

        parms = await self._argparse.build_args([items], txbase._MAKE_MOVE_VEC)
        if item_type:
            type_tag = bcs.OptionalTypeTag(bcs.TypeTag.type_tag_from(item_type))
        else:
            type_tag = bcs.OptionalTypeTag()

        return self.builder.make_move_vector(type_tag, parms[0])

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
        parms = await self._argparse.build_args(arguments, ars)
        return self.builder.move_call(
            target=package,
            arguments=parms,
            type_arguments=type_arguments,
            module=package_module,
            function=package_function,
            res_count=retcount,
        )

    async def optional_object(
        self,
        *,
        optional_object: Union[str, sui_prot.Object, bcs.Argument],
        is_receiving: Optional[bool] = False,
        is_shared_mutable: Optional[bool] = False,
        type_arguments: Optional[list] = None,
    ) -> bcs.Argument:
        """optional_object Wrap object as move Option

        :param optional_object: Object to wrap
        :type optional_object: Union[str, sui_prot.Object, bcs.Argument]
        :param is_receiving: True if this a receiving type, defaults to False
        :type is_receiving: Optional[bool], optional
        :param is_shared_mutable: True if this is a shared mutable type, defaults to False
        :type is_shared_mutable: Optional[bool], optional
        :param type_arguments: Move type string, defaults to None
        :type type_arguments: Optional[list], optional
        :return: Argument that can be used in subsequent commands (e.g. move_call arguments)
        :rtype: bcs.Argument
        """
        type_arguments = type_arguments if type_arguments else []
        function = "some"
        # Handle other than argument
        if isinstance(optional_object, bcs.Argument):
            parms = [optional_object]
        elif isinstance(optional_object, (str, sui_prot.Object)):
            parms = [
                await self._argparse.fetch_or_transpose_object(
                    optional_object, is_receiving, is_shared_mutable
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
        """stake_coin Stakes one or more coins to a specific validator.

        :param coins: One or more coins to stake.
        :type coins: list[str, sui_prot.Object, bcs.Argument]
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
        self, *, staked_coin: Union[str, sui_prot.Object]
    ) -> bcs.Argument:
        """unstake_coin Unstakes a Staked Sui Coin.

        :param staked_coin: The coin being unstaked
        :type staked_coin: Union[str, sui_prot.Object]
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
        upgrade_cap: Union[str, sui_prot.Object],
        args_list: Optional[list[str]] = None,
    ) -> bcs.Argument:
        """publish_upgrade Authorize, publish and commit upgrade of package.

        :param project_path: Path to move project
        :type project_path: str
        :param upgrade_cap: Id or sui_prot.Object of UpgradeCap
        :type upgrade_cap: Union[str, sui_prot.Object]
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
                request=rn.GetObject(object_id=upgrade_cap)
            )
            if result.is_err():
                raise ValueError(f"Validating upgrade cap: {result.result_string}")
            elif isinstance(result.result_data, pgql_type.NoopGQL):
                raise ValueError(
                    f"Fetching upgrade cap {upgrade_cap} returned no data."
                )

            upgrade_cap: sui_prot.Object = result.result_data.object
        # Isolate the struct type from supposed UpgradeCap
        _, _, package_struct = tv.TypeValidator.check_target_triplet(
            upgrade_cap.object_type
        )
        # If all upgradecap items check out
        jdict = upgrade_cap.json.to_dict()["structValue"]["fields"]
        if (
            jdict.keys() >= {"package", "version", "policy"}
            and package_struct == "UpgradeCap"
        ):
            # Prep args
            cap_obj_arg, policy_arg = await self._argparse.build_args(
                [upgrade_cap, jdict["policy"]["numberValue"]],
                txbase._PUBLISH_UPGRADE,
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
                    bcs.Address.from_str(jdict["package"]["stringValue"]),
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
        :param authorize_upgrade_fn: Async function to be called that generates custom authorization 'move_call'
        :type authorize_upgrade_fn: Callable[[&quot;AsyncSuiTransaction&quot;, Any, bcs.Digest], bcs.Argument]
        :param commit_upgrade_fn: Async function to be called that generates custom commitment 'move_call'
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
                request=rn.GetObject(object_id=upgrade_cap)
            )
            if result.is_err():
                raise ValueError(f"Validating upgrade cap: {result.result_string}")

            upgrade_cap: sui_prot.Object = result.result_data.object
        # Isolate the struct type from supposed UpgradeCap
        _, _, package_struct = tv.TypeValidator.check_target_triplet(
            upgrade_cap.object_type
        )
        # If all upgradecap items check out
        jdict = upgrade_cap.json.to_dict()["structValue"]["fields"]
        if (
            jdict.keys() >= {"package", "version", "policy"}
            and package_struct == "UpgradeCap"
        ):
            upgrade_ticket = await authorize_upgrade_fn(self, upgrade_cap, digest)
            # Extrack the auth_cmd cap input
            package_id = bcs.Address.from_str(package_id)
            # Upgrade
            receipt = self.builder.publish_upgrade(
                modules, dependencies, package_id, upgrade_ticket
            )
            return await commit_upgrade_fn(self, upgrade_cap, receipt)
        else:
            raise ValueError(f"Not a valid upgrade cap.")
