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

"""Pysui Transaction builder that works with GraphQL connection."""


from typing import Any, Callable, Optional, Union
from functools import cache
from pysui.sui.sui_txn.transaction import _SuiTransactionBase
from pysui.sui.sui_types import bcs
import pysui.sui.sui_pgql.pgql_validators as tv
import pysui.sui.sui_pgql.pgql_query as qn
import pysui.sui.sui_pgql.pgql_types as pgql_type
import pysui.sui.sui_pgql.pgql_txn_argb as ab

# Well known constructs

_TRANSACTION_GAS_ARGUMENT: bcs.Argument = bcs.Argument("GasCoin")
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

_TRANSFER_OBJECTS = [
    pgql_type.MoveListArg(
        pgql_type.RefType.NO_REF,
        pgql_type.MoveObjectRefArg(
            pgql_type.RefType.MUT_REF, "0x2", "sui", "SUI", [], False, False, False
        ),
    ),
    pgql_type.MoveScalarArg(pgql_type.RefType.NO_REF, "address"),
]

_MAKE_MOVE_VEC = [
    pgql_type.MoveVectorArg(
        pgql_type.RefType.NO_REF,
        pgql_type.MoveObjectRefArg(
            pgql_type.RefType.MUT_REF, "0x2", "sui", "SUI", [], False, False, False
        ),
    )
]


class SuiTransaction(_SuiTransactionBase):
    """."""

    def __init__(
        self,
        **kwargs,
    ) -> None:
        """__init__ Initialize the synchronous SuiTransaction.

        :param client: The synchronous SuiGQLClient
        :type client: SuiGQLClient
        :param initial_sender: The address of the sender of the transaction, defaults to None
        :type initial_sender: Union[SuiAddress, SigningMultiSig], optional
        :param compress_inputs: Reuse identical inputs, defaults to False
        :type compress_inputs: bool,optional
        :param merge_gas_budget: If True will take available gas not in use for paying for transaction, defaults to False
        :type merge_gas_budget: bool, optional
        :param deserialize_from: Will rehydrate SuiTransaction state from serialized base64 str or bytes, defaults to None
        :type deserialize_from: Union[str, bytes], optional
        """
        super().__init__(**kwargs)

    @cache
    def _function_meta_args(self, target: str) -> pgql_type.MoveArgSummary:
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
            return result.result_data.arg_summary()
        raise ValueError(f"Unresolvable target {target}")

    def split_coin(
        self,
        *,
        coin: Union[str, bcs.Argument],
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
        :type coin: Union[str, bcs.Argument]
        :param amounts: The amount or list of amounts to split the coin out to
        :type amounts: list[Union[int, bcs.Argument]]
        :return: A result or list of results types to use in subsequent commands
        :rtype: Union[list[bcs.Argument],bcs.Argument]
        """
        ars = [coin, amounts]
        parms = ab.build_args(self.client, ars, _SPLIT_COIN)
        pcoin = parms[0]
        print(pcoin)
        pamounts = parms[1:][0]
        print(pamounts)
        return self.builder.split_coin(pcoin, pamounts)

    def merge_coins(
        self,
        *,
        merge_to: Union[str, bcs.Argument],
        merge_from: list[Union[str, bcs.Argument]],
    ) -> bcs.Argument:
        """merge_coins Merges one or more coins to a primary coin.

        :param merge_to: The coin to merge other coins to
        :type merge_to: Union[str, ObjectID, ObjectRead, SuiCoinObject, bcs.Argument]
        :param merge_from: One or more coins to merge to primary 'merge_to' coin
        :type merge_from: list[Union[str bcs.Argument]]
        :return: The command result. Can not be used as input in subsequent commands.
        :rtype: bcs.Argument
        """
        ars = [merge_to, merge_from]
        parms = ab.build_args(self.client, ars, _MERGE_COINS)
        pcoin = parms[0]
        print(pcoin)
        pamounts = parms[1:]
        print(pamounts)

    def make_move_vector(
        self, items: list[Any], item_type: Optional[str] = None
    ) -> bcs.Argument:
        """Create a call to convert a list of objects to a Sui 'vector' of item_type."""

    def move_call(
        self,
        *,
        target: str,
        arguments: list,
        type_arguments: Optional[list] = None,
    ) -> Union[bcs.Argument, list[bcs.Argument]]:
        """move_call Creates a command to invoke a move contract call. May or may not return results.

        :param target: String triple in form "package_object_id::module_name::function_name"
        :type target: str
        :param arguments: Parameters that are passed to the move function
        :type arguments: list
        :param type_arguments: Optional list of type arguments for move function generics, defaults to None
        :type type_arguments: Optional[list], optional
        :return: The result which may or may not be used in subequent commands depending on the
            move method being called.
        :rtype: Union[bcs.Argument, list[bcs.Argument]]
        """

    def stake_coin(
        self,
        *,
        coins: list[str],
        validator_address: str,
        amount: Optional[int] = None,
    ) -> bcs.Argument:
        """stake_coin Stakes one or more coins to a specific validator.

        :param coins: One or more coins to stake.
        :type coins: list[str]
        :param validator_address: The validator to stake coins to
        :type validator_address: str
        :param amount: Amount from coins to stake. If not stated, all coin will be staked, defaults to None
        :type amount: Optional[int], optional
        :return: The command result.
        :rtype: bcs.Argument
        """

    def unstake_coin(self, *, staked_coin: str) -> bcs.Argument:
        """unstake_coin Unstakes a Staked Sui Coin.

        :param staked_coin: The coin being unstaked
        :type staked_coin: str
        :raises ValueError: If the staked coin is still in 'pending' state
        :return: The Result argument
        :rtype: bcs.Argument
        """

    def split_coin_equal(
        self,
        *,
        coin: Union[str, bcs.Argument],
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

    def split_coin_and_return(
        self,
        *,
        coin: Union[str, bcs.Argument],
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

    def public_transfer_object(
        self,
        *,
        object_to_send: Union[str, bcs.Argument],
        recipient: str,
        object_type: str,
    ) -> bcs.Argument:
        """public_transfer_object Public transfer of any object.

        :param object_to_send: Object being transferred
        :type object_to_send: Union[str, bcs.Argument]
        :param recipient: Address for recipient of object_to_send
        :type recipient: str
        :param object_type: Type arguments
        :type object_type: str
        :return: Result of command which is non-reusable
        :rtype: bcs.Argument
        """

    def transfer_objects(
        self,
        *,
        transfers: list[Union[str, bcs.Argument]],
        recipient: str,
    ) -> bcs.Argument:
        """transfer_objects Transfers one or more objects to a recipient.

        :param transfers: A list or SuiArray of objects to transfer
        :type transfers: list[Union[str,  bcs.Argument]]
        :param recipient: The recipient address that will receive the objects being transfered
        :type recipient: str
        :return: The command result. Can NOT be used as input in subsequent commands.
        :rtype: bcs.Argument
        """

    def transfer_sui(
        self,
        *,
        recipient: str,
        from_coin: Union[str, bcs.Argument],
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

    def publish_upgrade(
        self,
        *,
        project_path: str,
        package_id: str,
        upgrade_cap: str,
        args_list: Optional[list[str]],
    ) -> bcs.Argument:
        """publish_upgrade Authorize, publish and commit upgrade of package.

        :param project_path: path to project folder
        :type project_path: str
        :param package_id: The current package id that is being upgraded
        :type package_id: str
        :param upgrade_cap: The upgrade capability object
        :type upgrade_cap: str
        :param args_list: Additional `sui move build` arguments, defaults to None
        :type args_list: Optional[list[str]], optional
        :return: The Result Argument
        :rtype: bcs.Argument
        """

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