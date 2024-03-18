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

"""Pysui Transaction builder that leverages Sui GraphQL."""

import base64
from typing import Any, Callable, Optional, Union
from functools import cache
from pysui.sui.sui_pgql.pgql_txb_signing import SignerBlock
from pysui.sui.sui_txn.transaction import _SuiTransactionBase
from pysui.sui.sui_types import bcs
from pysui.sui.sui_txn.transaction_builder import PureInput
import pysui.sui.sui_pgql.pgql_txb_gas as gd
import pysui.sui.sui_pgql.pgql_validators as tv
import pysui.sui.sui_pgql.pgql_query as qn
import pysui.sui.sui_pgql.pgql_types as pgql_type
import pysui.sui.sui_pgql.pgql_txn_argb as ab
from pysui.sui.sui_types.scalars import SuiU64

# Well known parameter constructs

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
                pgql_type.RefType.MUT_REF, "0x2", "sui", "SUI", [], False, False, False
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
                pgql_type.RefType.MUT_REF, "0x2", "sui", "SUI", [], False, False, False
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
                pgql_type.RefType.MUT_REF, "0x2", "sui", "SUI", [], False, False, False
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


class SuiTransaction(_SuiTransactionBase):
    """."""

    # Prebuild functions

    _STAKE_REQUEST_TUPLE: tuple = None
    _UNSTAKE_REQUEST_TUPLE: tuple = None
    _SPLIT_AND_KEEP_TUPLE: tuple = None
    _SPLIT_AND_RETURN_TUPLE: tuple = None
    _PUBLISH_AUTHORIZE_UPGRADE_TUPLE: tuple = None

    def __init__(
        self,
        **kwargs,
    ) -> None:
        """__init__ Initialize the synchronous SuiTransaction.

        :param client: The synchronous SuiGQLClient
        :type client: SuiGQLClient
        :param initial_sender: The address of the sender of the transaction, defaults to None
        :type initial_sender: Union[str, SigningMultiSig], optional
        :param compress_inputs: Reuse identical inputs, defaults to False
        :type compress_inputs: bool,optional
        :param merge_gas_budget: If True will take available gas not in use for paying for transaction, defaults to False
        :type merge_gas_budget: bool, optional
        :param deserialize_from: Will rehydrate SuiTransaction state from serialized base64 str or bytes, defaults to None
        :type deserialize_from: Union[str, bytes], optional
        """
        super().__init__(**kwargs)
        # Force new signer block
        self._sig_block = SignerBlock(
            sender=kwargs.get(
                "initial_sender", self.client.config.active_address.address
            )
        )
        # Preload
        self._STAKE_REQUEST_TUPLE = self._function_meta_args(self._STAKE_REQUEST_TARGET)
        self._UNSTAKE_REQUEST_TUPLE = self._function_meta_args(
            self._UNSTAKE_REQUEST_TARGET
        )
        self._SPLIT_AND_KEEP_TUPLE = self._function_meta_args(self._SPLIT_AND_KEEP)
        self._SPLIT_AND_RETURN_TUPLE = self._function_meta_args(self._SPLIT_AND_RETURN)

    @cache
    def _function_meta_args(
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
        result = self.client.execute_query(
            with_query_node=qn.GetFunction(
                package=package,
                module_name=package_module,
                function_name=package_function,
            )
        )
        if result.is_ok() and not isinstance(result.result_data, pgql_type.NoopGQL):
            mfunc: pgql_type.MoveFunctionGQL = result.result_data
            return (
                bcs.Address.from_str(package),
                package_module,
                package_function,
                len(mfunc.returns),
                mfunc.arg_summary(),
            )
        raise ValueError(f"Unresolvable target {target}")

    def _build_txn_data(
        self,
        gas_budget: str = "",
        use_gas_objects: Optional[list[Union[str, pgql_type.SuiCoinObjectGQL]]] = None,
    ) -> Union[bcs.TransactionData, ValueError]:
        """Generate the TransactionData structure."""
        obj_in_use: set[str] = set(self.builder.objects_registry.keys())
        tx_kind = self.builder.finish_for_inspect()
        gas_data: bcs.GasData = gd.get_gas_data(
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
                bcs.TransactionExpiration("None"),
            ),
        )

    def transaction_data(
        self,
        *,
        gas_budget: Optional[str] = None,
        use_gas_objects: Optional[list[Union[str, pgql_type.SuiCoinObjectGQL]]] = None,
    ) -> bcs.TransactionData:
        """transaction_data Construct a BCS TransactionData object.

        If gas_budget not provided, pysui will call DryRunTransactionBlock to calculate.

        If use_gas_objects not used, pysui will determine which gas objects to use to
        pay for the transaction.

        :param gas_budget: Specify the amount of gas for the transaction budget, defaults to None
        :type gas_budget: Optional[str], optional
        :param use_gas_objects: Specify gas object(s) (by ID or SuiCoinObjectGQL), defaults to None
        :type use_gas_objects: Optional[list[Union[str, pgql_type.SuiCoinObjectGQL]]], optional
        :return: The TransactionData BCS structure
        :rtype: bcs.TransactionData
        """
        return self._build_txn_data(gas_budget, use_gas_objects)

    def build(
        self,
        *,
        gas_budget: Optional[str] = None,
        use_gas_objects: Optional[list[Union[str, pgql_type.SuiCoinObjectGQL]]] = None,
    ) -> str:
        """build After creating the BCS TransactionKind, serialize to base64 string and return.

        :param gas_budget: Specify the amount of gas for the transaction budget, defaults to None
        :type gas_budget: Optional[str], optional
        :param use_gas_objects: Specify gas object(s) (by ID or SuiCoinObjectGQL), defaults to None
        :type use_gas_objects: Optional[list[Union[str, pgql_type.SuiCoinObjectGQL]]], optional
        :return: Base64 encoded transaction bytes
        :rtype: str
        """
        txn_kind = self.transaction_data(
            gas_budget=gas_budget, use_gas_objects=use_gas_objects
        )
        return base64.b64encode(txn_kind.serialize()).decode()

    def split_coin(
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
            txer = SuiTransaction(client)
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

        parms = ab.build_args(self.client, [coin, amounts], _SPLIT_COIN)
        return self.builder.split_coin(parms[0], parms[1:][0])

    def merge_coins(
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
        parms = ab.build_args(self.client, [merge_to, merge_from], _MERGE_COINS)
        return self.builder.merge_coins(parms[0], parms[1:][0])

    def split_coin_equal(
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
            self._SPLIT_AND_KEEP_TUPLE
        )

        parms = ab.build_args(self.client, [coin, split_count], ars)
        type_arguments = [bcs.TypeTag.type_tag_from(coin_type)]
        return self.builder.move_call(
            target=package,
            arguments=parms,
            type_arguments=type_arguments,
            module=package_module,
            function=package_function,
            res_count=retcount,
        )

    def split_coin_and_return(
        self,
        *,
        coin: Union[str, pgql_type.ObjectReadGQL, bcs.Argument],
        split_count: int,
        coin_type: Optional[str] = "0x2::sui::SUI",
    ) -> bcs.Argument:
        """split_coin_and_return Splits a Sui coin into equal parts and returns array of split_count-1 for user to transfer.

        :param coin: The coin to split
        :type coin: Union[str, ObjectID, ObjectRead, SuiCoinObject, bcs.Argument]
        :param split_count: The number of parts to split coin into
        :type split_count: Union[int, SuiInteger]
        :param coin_type: The coin type, defaults to a Sui coin type
        :type coin_type: Optional[str], optional
        :return: The command result which is a vector of coins split out and may be used in subsequent commands.
        :rtype: bcs.Argument
        """
        package, package_module, package_function, retcount, ars = (
            self._SPLIT_AND_RETURN_TUPLE
        )
        parms = ab.build_args(self.client, [coin, split_count], ars)
        type_arguments = [bcs.TypeTag.type_tag_from(coin_type)]
        result_vector = self.builder.move_call(
            target=package,
            arguments=parms,
            type_arguments=type_arguments,
            module=package_module,
            function=package_function,
            res_count=retcount,
        )
        # Adjust type if needed
        if coin_type.count("<") == 0:
            type_arguments = [
                bcs.TypeTag.type_tag_from(f"0x2::coin::Coin<{coin_type}>")
            ]
        # We only want the new coins
        package, package_module, package_function = (
            tv.TypeValidator.check_target_triplet(self._VECTOR_REMOVE_INDEX)
        )
        package = bcs.Address.from_str(package)

        nreslist: list[bcs.Argument] = []
        for nrindex in range(split_count - 1):
            nreslist.append(
                self.builder.move_call(
                    target=package,
                    arguments=[
                        result_vector,
                        PureInput.as_input(SuiU64(0)),
                    ],
                    type_arguments=type_arguments,
                    module=package_module,
                    function=package_function,
                    res_count=1,
                )
            )
        package, package_module, package_function = (
            tv.TypeValidator.check_target_triplet(self._VECTOR_DESTROY_EMPTY)
        )
        package = bcs.Address.from_str(package)
        self.builder.move_call(
            target=package,
            arguments=[
                result_vector,
            ],
            type_arguments=type_arguments,
            module=package_module,
            function=package_function,
            res_count=1,
        )

        return nreslist

    def transfer_objects(
        self,
        *,
        transfers: list[Union[str, pgql_type.ObjectReadGQL, bcs.Argument]],
        recipient: str,
    ) -> bcs.Argument:
        """transfer_objects Transfers one or more objects to a recipient.

        :param transfers: A list or SuiArray of objects to transfer
        :type transfers: list[Union[str, pgql_type.ObjectReadGQL, bcs.Argument]]
        :param recipient: The recipient address that will receive the objects being transfered
        :type recipient: str
        :return: The command result. Can NOT be used as input in subsequent commands.
        :rtype: bcs.Argument
        """
        parms = ab.build_args(self.client, [recipient, transfers], _TRANSFER_OBJECTS)
        return self.builder.transfer_objects(parms[0], parms[1:][0])

    def transfer_sui(
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
        return self.builder.transfer_sui(
            *ab.build_args(self.client, [recipient, from_coin, amount], _TRANSFER_SUI)
        )

    def public_transfer_object(
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
            arguments=ab.build_args(
                self.client, [object_to_send, recipient], _PUBLIC_TRANSFER_OBJECTS
            ),
            type_arguments=[bcs.TypeTag.type_tag_from(object_type)],
            module=package_module,
            function=package_function,
            res_count=0,
        )

    def make_move_vector(
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

        parms = ab.build_args(self.client, [items], _MAKE_MOVE_VEC)
        if item_type:
            type_tag = bcs.OptionalTypeTag(bcs.TypeTag.type_tag_from(item_type))
        else:
            type_tag = bcs.OptionalTypeTag()

        return self.builder.make_move_vector(type_tag, parms[0])

    def move_call(
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
        # Validate and get target meta arguments
        package, package_module, package_function, retcount, ars = (
            self._function_meta_args(target)
        )
        type_arguments = [bcs.TypeTag.type_tag_from(x) for x in type_arguments]
        parms = ab.build_args(self.client, arguments, ars)
        return self.builder.move_call(
            target=package,
            arguments=parms,
            type_arguments=type_arguments,
            module=package_module,
            function=package_function,
            res_count=retcount,
        )

    def stake_coin(
        self,
        *,
        coins: list[Union[str, pgql_type.ObjectReadGQL]],
        validator_address: str,
        amount: Optional[int] = None,
    ) -> bcs.Argument:
        """stake_coin Stakes one or more coins to a specific validator.

        :param coins: One or more coins to stake.
        :type coins: list[str, pgql_type.ObjectReadGQL]
        :param validator_address: The validator to stake coins to
        :type validator_address: str
        :param amount: Amount from coins to stake. If not stated, all coin will be staked, defaults to None
        :type amount: Optional[int], optional
        :return: The command result.
        :rtype: bcs.Argument
        """
        # Fetch pre-build meta arg summary
        package, package_module, package_function, retcount, ars = (
            self._STAKE_REQUEST_TUPLE
        )
        # Validate arguments
        parms = ab.build_args(
            self.client,
            [self._SYSTEMSTATE_OBJECT.value, coins, amount, validator_address],
            ars,
        )
        # Create a move vector of coins
        parms[1] = self.make_move_vector(
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

    def unstake_coin(
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
            self._UNSTAKE_REQUEST_TUPLE
        )
        # Validate arguments
        parms = ab.build_args(
            self.client,
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

    def publish(
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

    def publish_upgrade(
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
            result = self.client.execute_query(
                with_query_node=qn.GetObject(object_id=upgrade_cap)
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
            # Prep args
            cap_obj_arg, policy_arg = ab.build_args(
                self.client,
                [upgrade_cap, upgrade_cap.content["policy"]],
                _PUBLISH_UPGRADE,
            )
            # Capture input offsets to preserve location of upgrade_cap ObjectArg
            cap_arg = len(self.builder.inputs)
            # Authorize, publish and commit the upgrade
            return self.builder.commit_upgrade(
                bcs.Argument("Input", cap_arg),
                self.builder.publish_upgrade(
                    modules,
                    dependencies,
                    bcs.Address.from_str(upgrade_cap.content["package"]),
                    self.builder.authorize_upgrade(
                        *ab.build_args(
                            self.client,
                            [upgrade_cap, upgrade_cap.content["policy"]],
                            _PUBLISH_UPGRADE,
                        ),
                        PureInput.as_input(digest),
                    ),
                ),
            )
        else:
            raise ValueError(f"Not a valid upgrade cap.")

    def custom_upgrade(
        self,
        *,
        project_path: str,
        package_id: str,
        upgrade_cap: str,
        authorize_upgrade_fn: Callable[
            ["SuiTransaction", Any, bcs.Digest], bcs.Argument
        ],
        commit_upgrade_fn: Callable[
            ["SuiTransaction", Any, bcs.Argument], bcs.Argument
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
        :type authorize_upgrade_fn: Callable[[&quot;SuiTransaction&quot;, Any, bcs.Digest], bcs.Argument]
        :param commit_upgrade_fn: Function to be called that generates custom commitment 'move_call'
        :type commit_upgrade_fn: Callable[[&quot;SuiTransaction&quot;, Any, bcs.Argument], bcs.Argument]
        :param args_list: Additional `sui move build` arguments, defaults to None
        :type args_list: Optional[list[str]], optional
        :return: The result argument
        :rtype: bcs.Argument
        """
        modules, dependencies, digest = self._compile_source(project_path, args_list)
        # Resolve upgrade cap to ObjectRead if needed
        if isinstance(upgrade_cap, str):
            result = self.client.execute_query(
                with_query_node=qn.GetObject(object_id=upgrade_cap)
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
