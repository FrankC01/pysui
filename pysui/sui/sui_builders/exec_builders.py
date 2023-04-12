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
# pylint: disable=too-many-instance-attributes

"""Sui Builders: Complex transaction."""

from abc import abstractmethod
from typing import Final, Optional
from pysui.abstracts.client_types import SuiBaseType
from pysui.sui.sui_builders.base_builder import (
    _NativeTransactionBuilder,
    SuiRequestType,
    SuiBaseBuilder,
    SuiTransactionBuilderMode,
    sui_builder,
)
from pysui.sui.sui_types.scalars import SuiNullType, SuiTxBytes, SuiSignature, ObjectID, SuiString
from pysui.sui.sui_types.collections import SuiArray, SuiMap
from pysui.sui.sui_types.address import SuiAddress
from pysui.sui.sui_txresults.complex_tx import DryRunTxResult, TransactionBytes, TxResponse, TxInspectionResult

from pysui.sui import sui_utils


class ExecuteTransaction(_NativeTransactionBuilder):
    """Submit a signed transaction to Sui."""

    _DEFAULT_EXECUTE_TX_OPTIONS: Final[dict] = {
        "showBalanceChanges": True,
        "showEffects": True,
        "showEvents": True,
        "showInput": True,
        "showObjectChanges": True,
        "showRawInput": True,
    }

    @sui_builder()
    def __init__(
        self,
        *,
        tx_bytes: SuiTxBytes,
        signatures: SuiArray[SuiSignature],
        options: Optional[SuiMap] = None,
        request_type: SuiRequestType,
    ) -> None:
        """__init__ Initialize builder.

        :param tx_bytes: BCS serialized transaction data bytes without its type tag, as base-64 encoded string
        :type tx_bytes: SuiTxBytes
        :param signatures: Array of `flag || signature || pubkey` bytes, as base-64 encoded string,
            signatures are committed to the intent message of the transaction data,
            as base-64 encoded string wrapped in SuiSignatures.
        :type signatures: SuiArray[SuiSignature]
        :param request_type: The request type
        :type request_type: SuiRequestType
        """
        super().__init__("sui_executeTransactionBlock", handler_cls=TxResponse, handler_func="from_dict")
        if options is None or isinstance(options, SuiNullType):
            self.options = sui_utils.as_sui_map(self._DEFAULT_EXECUTE_TX_OPTIONS.copy())
        else:
            self.options = sui_utils.as_sui_map(options)


class DryRunTransaction(_NativeTransactionBuilder):
    """Dry run a signed transaction to Sui."""

    @sui_builder()
    def __init__(
        self,
        *,
        tx_bytes: SuiTxBytes,
    ) -> None:
        """Initialize builder."""
        super().__init__("sui_dryRunTransactionBlock", handler_cls=DryRunTxResult, handler_func="from_dict")


class InspectTransaction(_NativeTransactionBuilder):
    """InspectTransaction when executed, return dev-inpsect results of the transaction.

    Includes both the transaction effects and return values of the transaction.
    """

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

        :param sender_address: The sender/signer of transaction bytes
        :type tx_bytes: SuiAddress
        :param tx_bytes: BCS serialize base64 encoded string of TransactionKind
        :type tx_bytes: SuiString
        :param gas_price: Gas is not charged, but gas usage is still calculated. Default to use reference gas price
        :type gas_price: Optional[SuiString]
        :param epoch: The epoch to perform the call. Will be set from the system state object if not provided
        :type epoch: Optional[SuiString]
        """
        super().__init__("sui_devInspectTransactionBlock", handler_cls=TxInspectionResult, handler_func="factory")


class _MoveCallTransactionBuilder(SuiBaseBuilder):
    """Builders that must be processed, signed then executed."""

    def __init__(self, method: str) -> None:
        """Initialize builder."""
        super().__init__(method, True, handler_cls=TransactionBytes, handler_func="from_dict")

    @property
    def authority(self) -> SuiAddress:
        """Fetch the authority."""
        if hasattr(self, "signer"):
            return getattr(self, "signer")
        if hasattr(self, "signers"):
            return getattr(self, "signers")
        if hasattr(self, "sender"):
            return getattr(self, "sender")
        if hasattr(self, "sender_address"):
            return getattr(self, "sender_address")
        raise ValueError(f"Object {self.__class__.__name__} has no authority property set")


class TransferObject(_MoveCallTransactionBuilder):
    """TransferObject When executed, transfer an object from one address to another.

    The object's type must allow public transfers
    """

    @sui_builder()
    def __init__(
        self,
        *,
        signer: SuiAddress,
        object_id: ObjectID,
        gas: ObjectID,
        gas_budget: SuiString,
        recipient: SuiAddress,
    ) -> None:
        """__init__ TransferObject Builder initializer.

        :param signer: the transaction signer's Sui address
        :type signer: SuiAddress
        :param object_id: the ObjectID of the object to be transferred
        :type object_id: ObjectID
        :param gas: gas object to be used in this transaction
        :type gas: ObjectID
        :param gas_budget: the gas budget, the transaction will fail if the gas cost exceed the budget
        :type gas_budget: SuiString
        :param recipient: the recipient's Sui address
        :type recipient: SuiAddress
        """
        super().__init__("unsafe_transferObject")


class TransferSui(_MoveCallTransactionBuilder):
    """TransferSui When executud, send SUI coin object to a Sui address.

    The SUI object is also used as the gas object.
    """

    @sui_builder()
    def __init__(
        self,
        *,
        signer: SuiAddress,
        sui_object_id: ObjectID,
        gas_budget: SuiString,
        recipient: SuiAddress,
        amount: SuiString,
    ) -> None:
        """__init__ TransferSui Builder initializer.

        :param signer: the transaction signer's Sui address
        :type signer: SuiAddress
        :param sui_object_id: the Sui coin object to be used in this transaction
        :type sui_object_id: ObjectID
        :param gas_budget: the gas budget, the transaction will fail if the gas cost exceed the budget
        :type gas_budget: SuiString
        :param recipient: the recipient's Sui address
        :type recipient: SuiAddress
        :param amount: the amount to be split out and transferred
        :type amount: SuiInteger
        """
        super().__init__("unsafe_transferSui")


class Pay(_MoveCallTransactionBuilder):
    """Pay When executed, send Coin<T> to a list of addresses.

    Where `T` can be any coin type following a list of amounts.

    The object specified in the `gas` field will be used to pay the gas fee for the transaction.
    The gas object can not appear in `input_coins`.
    """

    @sui_builder()
    def __init__(
        self,
        *,
        signer: SuiAddress,
        input_coins: SuiArray[ObjectID],
        recipients: SuiArray[SuiAddress],
        amounts: SuiArray[SuiString],
        gas: ObjectID,
        gas_budget: SuiString,
    ) -> None:
        """__init__ Pay Builder initializer.

        :param signer: the transaction signer's Sui address
        :type signer: SuiAddress
        :param input_coins: the Sui coins to be used in this transaction
        :type input_coins: SuiArray[ObjectID]
        :param recipients: the recipients' addresses, the length of this vector must be the same as amounts
        :type recipients: SuiArray[SuiAddress]
        :param amounts: the amounts to be transferred to recipients, following the same order
        :type amounts: SuiArray[SuiString]
        :param gas: gas object to be used in this transaction
        :type gas: ObjectID
        :param gas_budget: the gas budget, the transaction will fail if the gas cost exceed the budget
        :type gas_budget: SuiString
        """
        super().__init__("unsafe_pay")


class PaySui(_MoveCallTransactionBuilder):
    """PaySui When executed, sends SUI coins to a list of addresses, following a list of amounts.

    This is for SUI coin only and does not require a separate gas coin object.
    Specifically, what pay_sui does is:

    1. debit each input_coin to create new coin following the order of amounts and assign it to
        the corresponding recipient.
    2. accumulate all residual SUI from input coins left and deposit all SUI to the first input coin,
        then use the first input coin as the gas coin object.
    3. the balance of the first input coin after tx is sum(input_coins) - sum(amounts) - actual_gas_cost
    4. all other input coints other than the first one are deleted.
    """

    @sui_builder()
    def __init__(
        self,
        *,
        signer: SuiAddress,
        input_coins: SuiArray[ObjectID],
        recipients: SuiArray[SuiAddress],
        amounts: SuiArray[SuiString],
        gas_budget: SuiString,
    ) -> None:
        """__init__ PaySui Builder initializer.

        :param signer: the transaction signer's Sui address
        :type signer: SuiAddress
        :param input_coins: the Sui coins to be used in this transaction
        :type input_coins: SuiArray[ObjectID]
        :param recipients: the recipients' addresses, the length of this vector must be the same as amounts
        :type recipients: SuiArray[SuiAddress]
        :param amounts: the amounts to be transferred to recipients, following the same order,
        :type amounts: SuiArray[SuiString]
        :param gas_budget: the gas budget, the transaction will fail if the gas cost exceed the budget
        :type gas_budget: SuiString
        """
        super().__init__("unsafe_paySui")


class PayAllSui(_MoveCallTransactionBuilder):
    """PayAllSui When executed, Send all SUI coins to one recipient.

    This is for SUI coin only and does not require a separate gas coin object.
    Specifically, what pay_all_sui does is:

    1. accumulate all SUI from input coins and deposit all SUI to the first input coin
    2. transfer the updated first coin to the recipient and also use this first coin as gas coin object.
    3. the balance of the first input coin after tx is sum(input_coins) - actual_gas_cost.
    4. all other input coins other than the first are deleted.
    """

    @sui_builder()
    def __init__(
        self,
        *,
        signer: SuiAddress,
        input_coins: SuiArray[ObjectID],
        recipient: SuiAddress,
        gas_budget: SuiString,
    ) -> None:
        """__init__ PayAllSui Builder initializer.

        :param signer: the transaction signer's Sui address
        :type signer: SuiAddress
        :param input_coins: the Sui coins to be used in this transaction, including the coin for gas payment.
        :type input_coins: SuiArray[ObjectID]
        :param recipient: the recipient Sui address
        :type recipient: SuiAddress
        :param gas_budget: the gas budget, the transaction will fail if the gas cost exceed the budget
        :type gas_budget: SuiString
        """
        super().__init__("unsafe_payAllSui")


class MergeCoin(_MoveCallTransactionBuilder):
    """MergeCoin When executed, merge multiple coins into one coin."""

    @sui_builder()
    def __init__(
        self,
        *,
        signer: SuiAddress,
        primary_coin: ObjectID,
        coin_to_merge: ObjectID,
        gas: ObjectID,
        gas_budget: SuiString,
    ) -> None:
        """__init__ MergeCoin Builder initializer.

        :param signer: the transaction signer's Sui address
        :type signer: SuiAddress
        :param primary_coin: the coin object to merge into, this coin will remain after the transaction
        :type primary_coin: ObjectID
        :param coin_to_merge: the coin object to be merged, this coin will be destroyed,
            the balance will be added to `primary_coin`
        :type coin_to_merge: ObjectID
        :param gas: gas object to be used in this transaction
        :type gas_object: ObjectID
        :param gas_budget: the gas budget, the transaction will fail if the gas cost exceed the budget
        :type gas_budget: SuiString
        """
        super().__init__("unsafe_mergeCoins")


class SplitCoin(_MoveCallTransactionBuilder):
    """SplitCoin When executed, split a coin object into multiple coins."""

    @sui_builder()
    def __init__(
        self,
        *,
        signer: SuiAddress,
        coin_object_id: ObjectID,
        split_amounts: SuiArray[SuiString],
        gas_object: ObjectID,
        gas_budget: SuiString,
    ) -> None:
        """__init__ SplitCoin Builder initializer.

        :param signer: the transaction signer's Sui address
        :type signer: SuiAddress
        :param coin_object_id: the coin object to be spilt
        :type coin_object_id: ObjectID
        :param split_amounts: the amounts to split out from the coin
        :type split_amounts: SuiArray[SuiString]
        :param gas_object: gas object to be used in this transaction
        :type gas_object: ObjectID
        :param gas_budget: the gas budget, the transaction will fail if the gas cost exceed the budget
        :type gas_budget: SuiString
        """
        super().__init__("unsafe_splitCoin")


class SplitCoinEqually(_MoveCallTransactionBuilder):
    """SplitCoinEqually When executed, splits a coin object into multiple equal-size coins."""

    @sui_builder()
    def __init__(
        self,
        *,
        signer: SuiAddress,
        coin_object_id: ObjectID,
        split_count: SuiString,
        gas: ObjectID,
        gas_budget: SuiString,
    ) -> None:
        """__init__ SplitCoinEqually Builder initializer.

        :param signer: the transaction signer's Sui address
        :type signer: SuiAddress
        :param coin_object_id: the coin object to be spilt
        :type coin_object_id: ObjectID
        :param split_count: the number of coins to split into
        :type split_count: SuiString
        :param gas: gas object to be used in this transaction
        :type gas: ObjectID
        :param gas_budget: the gas budget, the transaction will fail if the gas cost exceed the budget
        :type gas_budget: SuiString
        """
        super().__init__("unsafe_splitCoinEqual")


# Batch Transaction. Do not use @sui_builder


class BatchParameter(SuiMap):
    """BatchParameter is abstraction for TransferObjectParams and MoveCallRequestParams."""

    @abstractmethod
    def realize_parameters(self) -> dict:
        """Satisfied by subclasses."""


class TransferObjectParams(BatchParameter):
    """For submitting transfer in a batch transaction."""

    def __init__(self, *, receiver: SuiAddress, transfer_object: ObjectID) -> None:
        """Initialize transfer properties."""
        self.receiver: SuiAddress = receiver
        self.transfer_object: ObjectID = transfer_object
        super().__init__("transferObjectRequestParams", {})

    def realize_parameters(self) -> dict:
        """Satisfied by subclasses."""
        out_dict = self.map["transferObjectRequestParams"]
        out_dict["recipient"] = self.receiver.address
        out_dict["objectId"] = self.transfer_object.value
        return self.map


class MoveCallRequestParams(BatchParameter):
    """For submitting transfer in a batch transaction."""

    def __init__(
        self,
        *,
        package_object: ObjectID,
        module_str: SuiString,
        function_str: SuiString,
        type_arguments: SuiArray[SuiString],
        arguments: SuiArray[SuiString],
    ):
        """__init__ Initialize parameters."""
        self.package_object_id: ObjectID = sui_utils.as_object_id(package_object)
        self.module: SuiString = module_str
        self.function: SuiString = function_str
        self.type_arguments: SuiArray[str] = SuiArray([x.value for x in type_arguments.array])
        self.arguments: SuiArray[str] = SuiArray([x.value for x in arguments.array])
        super().__init__("moveCallRequestParams", {})

    def realize_parameters(self) -> dict:
        """Satisfied by subclasses."""
        out_dict = self.map["moveCallRequestParams"]
        out_dict["arguments"] = self.arguments.array
        out_dict["function"] = self.function.value
        out_dict["module"] = self.module.value
        out_dict["packageObjectId"] = self.package_object_id.value
        out_dict["typeArguments"] = self.type_arguments.array
        return self.map


# pylint: disable=too-many-arguments
class BatchTransaction(_MoveCallTransactionBuilder):
    """BatchTransaction When executed, runs transactions included in the batch."""

    def __init__(
        self,
        signer: SuiAddress,
        transaction_params: SuiArray[BatchParameter],
        gas: ObjectID,
        gas_budget: SuiString,
        txn_builder_mode: SuiTransactionBuilderMode = SuiTransactionBuilderMode.COMMIT,
    ) -> None:
        """__init__ BatchTransaction Builder initializer.

        :param signer: the transaction signer's Sui address
        :type signer: SuiAddress
        :param transaction_params: list of transaction BatchParameter objects
        :type transaction_params: SuiArray[BatchParameter]
        :param gas: gas object to be used in this transaction
        :type gas: ObjectID
        :param gas_budget: the gas budget, the transaction will fail if the gas cost exceed the budget
        :type gas_budget: SuiString
        :raises ValueError: _description_
        """
        super().__init__("unsafe_batchTransaction")
        self.signer: SuiAddress = signer
        self.single_transaction_params = None
        self.gas: ObjectID = sui_utils.as_object_id(gas)
        self.gas_budget = gas_budget
        self.txn_builder_mode = txn_builder_mode

        for item in transaction_params.array:
            if not isinstance(item, BatchParameter):
                raise ValueError(f"{item} is not of type BatchParameter")
        self.single_transaction_params = transaction_params

    @property
    def params(self) -> list[SuiBaseType]:
        """Collect the call parameters."""
        collection = []
        for item in self.single_transaction_params.array:
            collection.append(item.realize_parameters())
        self.single_transaction_params = SuiArray(collection)
        return self._pull_vars()


# Publish and call


class Publish(_MoveCallTransactionBuilder):
    """Publish When executed, Publish a Move package to the SUI blockchain."""

    @sui_builder()
    def __init__(
        self,
        *,
        sender: SuiAddress,
        compiled_modules: SuiArray[SuiString],
        dependencies: SuiArray[ObjectID],
        gas: ObjectID,
        gas_budget: SuiString,
    ) -> None:
        """__init__ Publish Builder initializer.

        :param sender: the transaction signer's Sui address defaults to None
        :type sender: SuiAddress, optional
        :param compiled_modules: the compiled bytes of a move package's modules, defaults to None
        :type compiled_modules: SuiArray[SuiString], optional
        :param gas: gas object to be used in this transaction, defaults to None
        :type gas: ObjectID, optional
        :param gas_budget: the gas budget, the transaction will fail if the gas cost exceed the budget
        :type gas_budget: SuiString
        """
        super().__init__("unsafe_publish")


class MoveCall(_MoveCallTransactionBuilder):
    """MoveCall When executed, executes a Move call on the network.

    Calling the specified function in the module of a given package.
    """

    @sui_builder()
    def __init__(
        self,
        *,
        signer: SuiAddress,
        package_object_id: ObjectID,
        module: SuiString,
        function: SuiString,
        type_arguments: SuiArray[SuiString],
        arguments: SuiArray[SuiString],
        gas: ObjectID,
        gas_budget: SuiString,
        execution_mode: Optional[SuiTransactionBuilderMode] = SuiTransactionBuilderMode.COMMIT,
    ) -> None:
        """__init__ MoveCall Builder initializer.

        :param signer: the transaction signer's Sui address, defaults to None
        :type signer: SuiAddress, optional
        :param package_object_id: the Move package ID, e.g. `0x2`, defaults to None
        :type package_object_id: ObjectID, optional
        :param module: the Move module name, e.g. `devnet_nft`, defaults to None
        :type module: SuiString, optional
        :param function: the move function name, e.g. `mint`, defaults to None
        :type function: SuiString, optional
        :param type_arguments: the type arguments of the Move function, defaults to None
        :type type_arguments: SuiArray[SuiString], optional
        :param arguments: the arguments to be passed into the Move function, defaults to None
        :type arguments: SuiArray[SuiString], optional
        :param gas: gas object to be used in this transaction, defaults to None
        :type gas: ObjectID, optional
        :param gas_budget: the gas budget, the transaction will fail if the gas cost exceed the budget
        :type gas_budget: SuiString
        :param execution_mode: Whether this is a Normal transaction or a Dev Inspect Transaction.
            Default to be `SuiTransactionBuilderMode::Commit`
        :type execution_mode: SuiTransactionBuilderMode, optional
        """
        super().__init__("unsafe_moveCall")


# Stake and Delegation


class RequestAddStake(_MoveCallTransactionBuilder):
    """RequestAddStake add delegated stake to a validator's staking pool using multiple coins and amount."""

    @sui_builder()
    def __init__(
        self,
        *,
        signer: SuiAddress,
        coins: SuiArray[ObjectID],
        amount: Optional[SuiString],
        validator: SuiAddress,
        gas: ObjectID,
        gas_budget: SuiString,
    ):
        """__init__ Initialize builder.

        :param signer: the transaction signer's Sui address
        :type signer: SuiAddress
        :param coins: Coin<SUI> or LockedCoin<SUI> object to delegate
        :type coins: SuiArray
        :param amount: stake amount
        :type amount: Optional[SuiString]
        :param validator: the validator's Sui address
        :type validator: SuiAddress
        :param gas: gas object to be used in this transaction
        :type gas: ObjectID
        :param gas_budget: the gas budget, the transaction will fail if the gas cost exceed the budget
        :type gas_budget: SuiString
        """
        super().__init__("unsafe_requestAddStake")


class RequestWithdrawStake(_MoveCallTransactionBuilder):
    """RequestWithdrawStake Withdraw some portion of a stake from a validator's staking pool."""

    @sui_builder()
    def __init__(
        self,
        *,
        signer: SuiAddress,
        delegation: ObjectID,
        staked_sui: ObjectID,
        gas: ObjectID,
        gas_budget: SuiString,
    ):
        """__init__ Initialize builder.

        :param signer: the transaction signer's Sui address
        :type signer: SuiAddress
        :param delegation: Delegation object ID
        :type delegation: ObjectID
        :param staked_sui: staked Sui object ID
        :type staked_sui: ObjectID
        :param gas: gas object to be used in this transaction
        :type gas: ObjectID
        :param gas_budget: the gas budget, the transaction will fail if the gas cost exceed the budget
        :type gas_budget: SuiString
        """
        super().__init__("unsafe_requestWithdrawDelegation")
