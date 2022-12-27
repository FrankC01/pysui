#    Copyright 2022 Frank V. Castellucci
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

"""Sui Builders: Complex transaction."""

from abc import abstractmethod
from pysui.abstracts.client_types import SuiBaseType
from pysui.abstracts.client_keypair import SignatureScheme, PublicKey
from pysui.sui.sui_builders.base_builder import _NativeTransactionBuilder, SuiRequestType, SuiBaseBuilder
from pysui.sui.sui_types.scalars import SuiTxBytes, SuiSignature, ObjectID, SuiInteger, SuiString
from pysui.sui.sui_types.collections import SuiArray, SuiMap
from pysui.sui.sui_types.address import SuiAddress
from pysui.sui.sui_txresults.single_tx import SuiGas
from pysui.sui.sui_txresults.complex_tx import TxEffectResult, Effects

from pysui.sui import sui_utils


class ExecuteTransaction(_NativeTransactionBuilder):
    """Submit a signed transaction to Sui."""

    def __init__(
        self,
        *,
        tx_bytes: SuiTxBytes = None,
        sig_scheme: SignatureScheme = None,
        signature: SuiSignature = None,
        pub_key: PublicKey = None,
        request_type: SuiRequestType = None,
    ) -> None:
        """Initialize builder."""
        super().__init__("sui_executeTransaction", handler_cls=TxEffectResult, handler_func="from_dict")
        self.tx_bytes: SuiTxBytes = tx_bytes
        self.sig_scheme: SignatureScheme = sig_scheme
        self.signature: SuiSignature = signature
        self.pub_key: PublicKey = pub_key
        self.request_type: SuiRequestType = request_type

    def set_tx_bytes(self, tbyteb64: SuiTxBytes) -> "ExecuteTransaction":
        """Set the transaction base64 string."""
        self.tx_bytes: SuiTxBytes = tbyteb64
        return self

    def set_sig_scheme(self, sig: SignatureScheme) -> "ExecuteTransaction":
        """Set the transaction base64 string."""
        self.sig_scheme: SignatureScheme = sig
        return self

    def set_signature(self, sigb64: SuiSignature) -> "ExecuteTransaction":
        """Set the signed transaction base64 string."""
        self.signature: SuiSignature = sigb64
        return self

    def set_pub_key(self, pubkey: PublicKey) -> "ExecuteTransaction":
        """Set the public key base64 string."""
        self.pub_key: PublicKey = pubkey
        return self

    def set_request_type(self, rtype: SuiRequestType) -> "ExecuteTransaction":
        """Set the request type for execution."""
        self.request_type: SuiRequestType = rtype
        return self

    def _collect_parameters(self) -> list[SuiBaseType]:
        """Collect the call parameters."""
        return self._pull_vars()


class ExecuteSerializedTransaction(_NativeTransactionBuilder):
    """Submit a signed transaction to Sui."""

    def __init__(
        self,
        *,
        tx_bytes: SuiTxBytes = None,
        signature: SuiSignature = None,
        request_type: SuiRequestType = None,
    ) -> None:
        """__init__ When executed, runs the transaction.

        This can replace ExecuteTransaction and is preferred if RPC version > 0.17.0

        :param tx_bytes: Submitted transaction base64 SuiTxBytes, defaults to None
        :type tx_bytes: SuiTxBytes, optional
        :param signature: The key_scheme,signed tx_bytes and signer pubkey serialized to Base64, defaults to None
        :type signature: SuiSignature, optional
        :param request_type: The type of request to use in submitting transaction, defaults to None
        :type request_type: SuiRequestType, optional
        """
        super().__init__("sui_executeTransactionSerializedSig", handler_cls=TxEffectResult, handler_func="from_dict")
        self.tx_bytes: SuiTxBytes = tx_bytes
        self.signature: SuiSignature = signature
        self.request_type: SuiRequestType = request_type

    def set_tx_bytes(self, tbyteb64: SuiTxBytes) -> "ExecuteTransaction":
        """Set the transaction base64 string."""
        self.tx_bytes: SuiTxBytes = tbyteb64
        return self

    def set_signature(self, sigb64: SuiSignature) -> "ExecuteTransaction":
        """Set the signed transaction base64 string."""
        self.signature: SuiSignature = sigb64
        return self

    def set_request_type(self, rtype: SuiRequestType) -> "ExecuteTransaction":
        """Set the request type for execution."""
        self.request_type: SuiRequestType = rtype
        return self

    def _collect_parameters(self) -> list[SuiBaseType]:
        """Collect the call parameters."""
        return self._pull_vars()


class DryRunTransaction(_NativeTransactionBuilder):
    """Dry run a signed transaction to Sui."""

    def __init__(
        self,
        *,
        tx_bytes: SuiTxBytes = None,
    ) -> None:
        """Initialize builder."""
        super().__init__("sui_dryRunTransaction", handler_cls=Effects, handler_func="from_dict")
        self.tx_bytes: SuiTxBytes = tx_bytes

    def set_tx_bytes(self, tbyteb64: SuiTxBytes) -> "DryRunTransaction":
        """Set the transaction base64 string."""
        self.tx_bytes: SuiTxBytes = tbyteb64
        return self

    def _collect_parameters(self) -> list[SuiBaseType]:
        """Collect the call parameters."""
        return [self.tx_bytes]


class _MoveCallTransactionBuilder(SuiBaseBuilder):
    """Builders that must be processed, signed then executed."""

    def __init__(self, method: str) -> None:
        """Initialize builder."""
        super().__init__(method, True)

    @property
    def authority(self) -> SuiAddress:
        """Fetch the authority."""
        if hasattr(self, "signer"):
            return getattr(self, "signer")
        if hasattr(self, "sender"):
            return getattr(self, "sender")
        raise ValueError(f"Object {self.__class__.__name__} has no authority property set")


class TransferObject(_MoveCallTransactionBuilder):
    """TransferObject When executed, transfer an object from one address to another.

    The object's type must allow public transfers
    """

    transferobject_kwords: set[str] = {"signer", "object_id", "gas", "gas_budget", "recipient"}

    def __init__(
        self,
        *,
        signer: SuiAddress = None,
        object_id: ObjectID = None,
        gas: ObjectID = None,
        gas_budget: SuiInteger = None,
        recipient: SuiAddress = None,
    ) -> None:
        """__init__ TransferObject Builder initializer.

        :param signer: the transaction signer's Sui address, defaults to None
        :type signer: SuiAddress, optional
        :param object_id: the ObjectID of the object to be transferred, defaults to None
        :type object_id: ObjectID, optional
        :param gas: gas object to be used in this transaction, defaults to None
        :type gas: ObjectID, optional
        :param gas_budget: the gas budget, the transaction will fail if the gas cost exceed the budget,
            defaults to None
        :type gas_budget: SuiInteger, optional
        :param recipient: the recipient's Sui address, defaults to None
        :type recipient: SuiAddress, optional
        """
        inargs = locals().copy()
        super().__init__("sui_transferObject")
        self.signer: SuiAddress = None
        self.object_id: ObjectID = None
        self.gas: ObjectID = None
        self.gas_budget: SuiInteger = None
        self.recipient: SuiAddress = None
        for hit in self.transferobject_kwords & set(inargs.keys()):
            setattr(self, hit, inargs[hit])

    def set_object_id(self, obj: ObjectID) -> "TransferObject":
        """Set the object to transfer."""
        self.object_id: ObjectID = sui_utils.as_object_id(obj)
        return self

    def set_signer(self, address: SuiAddress) -> "TransferObject":
        """Set the gas owner signer."""
        self.signer: SuiAddress = address
        return self

    def set_gas(self, obj: ObjectID) -> "TransferObject":
        """Set sui object gas object."""
        self.gas: ObjectID = sui_utils.as_object_id(obj)
        return self

    def set_gas_budget(self, obj: SuiInteger) -> "TransferObject":
        """Set the amount for transaction payment."""
        self.gas_budget: SuiInteger = obj
        return self

    def set_recipient(self, obj: SuiAddress) -> "TransferObject":
        """Set the address for the receiver."""
        self.recipient: SuiAddress = obj
        return self

    def _collect_parameters(self) -> list[SuiBaseType]:
        """Collect the call parameters."""
        return self._pull_vars()


class TransferSui(_MoveCallTransactionBuilder):
    """TransferSui When executud, send SUI coin object to a Sui address.

    The SUI object is also used as the gas object.
    """

    transfersui_kwords: set[str] = {"signer", "sui_object_id", "gas_budget", "recipient", "amount"}

    def __init__(
        self,
        *,
        signer: SuiAddress = None,
        sui_object_id: ObjectID = None,
        gas_budget: SuiInteger = None,
        recipient: SuiAddress = None,
        amount: SuiInteger = None,
    ) -> None:
        """__init__ TransferSui Builder initializer.

        :param signer: the transaction signer's Sui address, defaults to None
        :type signer: SuiAddress, optional
        :param sui_object_id: the Sui coin object to be used in this transaction, defaults to None
        :type sui_object_id: ObjectID, optional
        :param gas_budget: the gas budget, the transaction will fail if the gas cost exceed the budget,
            defaults to None
        :type gas_budget: SuiInteger, optional
        :param recipient: the recipient's Sui address, defaults to None
        :type recipient: SuiAddress, optional
        :param amount: the amount to be split out and transferred, defaults to None
        :type amount: SuiInteger, optional
        """
        inargs = locals().copy()
        super().__init__("sui_transferSui")
        self.signer: SuiAddress = None
        self.sui_object_id: ObjectID = None
        self.gas_budget: SuiInteger = None
        self.recipient: SuiAddress = None
        self.amount: SuiInteger = None
        for hit in self.transfersui_kwords & set(inargs.keys()):
            setattr(self, hit, inargs[hit])

    def set_signer(self, address: SuiAddress) -> "TransferSui":
        """Set the gas owner signer."""
        self.signer: SuiAddress = address
        return self

    def set_sui_object_id(self, obj: ObjectID) -> "TransferSui":
        """Set sui object gas object."""
        self.sui_object_id: ObjectID = sui_utils.as_object_id(obj)
        return self

    def set_gas_budget(self, obj: SuiInteger) -> "TransferSui":
        """Set the amount for transaction payment."""
        self.gas_budget: SuiInteger = obj
        return self

    def set_recipient(self, obj: SuiAddress) -> "TransferSui":
        """Set the address for the receiver."""
        self.recipient: SuiAddress = obj
        return self

    def set_amount(self, obj: SuiInteger) -> "TransferSui":
        """Set the amount to transfer to recipient."""
        self.amount: SuiInteger = obj
        return self

    def _collect_parameters(self) -> list[SuiBaseType]:
        """Collect the call parameters."""
        return self._pull_vars()


class Pay(_MoveCallTransactionBuilder):
    """Pay When executed, send Coin<T> to a list of addresses.

    Where `T` can be any coin type following a list of amounts.

    The object specified in the `gas` field will be used to pay the gas fee for the transaction.
    The gas object can not appear in `input_coins`.
    """

    pay_kwords: set[str] = {"signer", "input_coins", "recipients", "amounts", "gas", "gas_budget"}
    _pay_array_keys: set[str] = {"input_coins", "recipients", "amounts"}

    def __init__(
        self,
        *,
        signer: SuiAddress = None,
        input_coins: SuiArray[ObjectID] = None,
        recipients: SuiArray[SuiAddress] = None,
        amounts: SuiArray[SuiInteger] = None,
        gas: ObjectID = None,
        gas_budget: SuiInteger = None,
    ) -> None:
        """__init__ Pay Builder initializer.

        :param signer: the transaction signer's Sui address, defaults to None
        :type signer: SuiAddress, optional
        :param input_coins: the Sui coins to be used in this transaction, defaults to None
        :type input_coins: SuiArray[ObjectID], optional
        :param recipients: the recipients' addresses, the length of this vector must be the same as amounts,
            defaults to None
        :type recipients: SuiArray[SuiAddress], optional
        :param amounts: the amounts to be transferred to recipients, following the same order, defaults to None
        :type amounts: SuiArray[SuiInteger], optional
        :param gas: gas object to be used in this transaction, defaults to None
        :type gas: ObjectID, optional
        :param gas_budget: the gas budget, the transaction will fail if the gas cost exceed the budget, defaults to None
        :type gas_budget: SuiInteger, optional
        """
        inargs = locals().copy()
        super().__init__("sui_pay")
        self.signer: SuiAddress = None
        self.input_coins: SuiArray[ObjectID] = None
        self.recipients: SuiArray[SuiAddress] = None
        self.amounts: SuiArray[SuiInteger] = None
        self.gas: ObjectID = None
        self.gas_budget: SuiInteger = None
        for hit in self.pay_kwords & set(inargs.keys()):
            if hit in self._pay_array_keys and isinstance(inargs[hit], list):
                setattr(self, hit, SuiArray(inargs[hit]))
            else:
                setattr(self, hit, inargs[hit])

    def set_signer(self, address: SuiAddress) -> "Pay":
        """Set the gas owner signer."""
        self.signer: SuiAddress = address
        return self

    def set_input_coins(self, obj: list[ObjectID]) -> "Pay":
        """Set sui object gas object."""
        self.input_coins: SuiArray[ObjectID] = SuiArray[ObjectID](obj)
        return self

    def set_recipients(self, obj: list[SuiAddress]) -> "Pay":
        """Set the addresses for the receivers."""
        self.recipients: SuiArray[SuiAddress] = SuiArray[SuiAddress](obj)
        return self

    def set_amounts(self, obj: list[SuiInteger]) -> "Pay":
        """Set the amount(s) to transfer to recipient."""
        self.amounts: SuiArray[SuiInteger] = SuiArray[SuiInteger](obj)
        return self

    def set_gas(self, obj: ObjectID) -> "Pay":
        """Set sui object gas object for paying transaction."""
        self.gas: ObjectID = sui_utils.as_object_id(obj)
        return self

    def set_gas_budget(self, obj: SuiInteger) -> "Pay":
        """Set the amount for transaction payment."""
        self.gas_budget: SuiInteger = obj
        return self

    def _collect_parameters(self) -> list[SuiBaseType]:
        """Collect the call parameters."""
        return self._pull_vars()


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

    paysui_kwords: set[str] = {"signer", "input_coins", "recipients", "amounts", "gas_budget"}
    _paysui_array_keys: set[str] = {"input_coins", "recipients", "amounts"}

    def __init__(
        self,
        *,
        signer: SuiAddress = None,
        input_coins: SuiArray[ObjectID] = None,
        recipients: SuiArray[SuiAddress] = None,
        amounts: SuiArray[SuiInteger] = None,
        gas_budget: SuiInteger = None,
    ) -> None:
        """__init__ PaySui Builder initializer.

        :param signer: the transaction signer's Sui address, defaults to None
        :type signer: SuiAddress, optional
        :param input_coins: the Sui coins to be used in this transaction, including the coin for gas payment,
            defaults to None
        :type input_coins: SuiArray[ObjectID], optional
        :param recipients: the recipients' addresses, the length of this vector must be the same as amounts,
            defaults to None
        :type recipients: SuiArray[SuiAddress], optional
        :param amounts: the amounts to be transferred to recipients, following the same order,
            defaults to None
        :type amounts: SuiArray[SuiInteger], optional
        :param gas_budget: the gas budget, the transaction will fail if the gas cost exceed the budget, defaults to None
        :type gas_budget: SuiInteger, optional
        """
        inargs = locals().copy()
        super().__init__("sui_paySui")
        self.signer: SuiAddress = None
        self.input_coins: SuiArray[ObjectID] = None
        self.recipients: SuiArray[SuiAddress] = None
        self.amounts: SuiArray[SuiInteger] = None
        self.gas_budget: SuiInteger = None
        for hit in self.paysui_kwords & set(inargs.keys()):
            if hit in self._paysui_array_keys and isinstance(inargs[hit], list):
                setattr(self, hit, SuiArray(inargs[hit]))
            else:
                setattr(self, hit, inargs[hit])

    def set_signer(self, address: SuiAddress) -> "PaySui":
        """Set the gas owner signer."""
        self.signer: SuiAddress = address
        return self

    def set_input_coins(self, obj: list[ObjectID]) -> "PaySui":
        """Set sui object gas object."""
        self.input_coins: SuiArray[ObjectID] = SuiArray[ObjectID](obj)
        return self

    def set_recipients(self, obj: list[SuiAddress]) -> "PaySui":
        """Set the addresses for the receivers."""
        self.recipients: SuiArray[SuiAddress] = SuiArray[SuiAddress](obj)
        return self

    def set_amounts(self, obj: list[SuiInteger]) -> "PaySui":
        """Set the amount(s) to transfer to recipient."""
        self.amounts: SuiArray[SuiInteger] = SuiArray[SuiInteger](obj)
        return self

    def set_gas_budget(self, obj: SuiInteger) -> "PaySui":
        """Set the amount for transaction payment."""
        self.gas_budget: SuiInteger = obj
        return self

    def _collect_parameters(self) -> list[SuiBaseType]:
        """Collect the call parameters."""
        return self._pull_vars()


class PayAllSui(_MoveCallTransactionBuilder):
    """PayAllSui When executed, Send all SUI coins to one recipient.

    This is for SUI coin only and does not require a separate gas coin object.
    Specifically, what pay_all_sui does is:

    1. accumulate all SUI from input coins and deposit all SUI to the first input coin
    2. transfer the updated first coin to the recipient and also use this first coin as gas coin object.
    3. the balance of the first input coin after tx is sum(input_coins) - actual_gas_cost.
    4. all other input coins other than the first are deleted.
    """

    payallsui_kwords: set[str] = {"signer", "input_coins", "recipient", "gas_budget"}

    def __init__(
        self,
        *,
        signer: SuiAddress = None,
        input_coins: SuiArray[ObjectID] = None,
        recipient: SuiAddress = None,
        gas_budget: SuiInteger = None,
    ) -> None:
        """__init__ PayAllSui Builder initializer.

        :param signer: the transaction signer's Sui address, defaults to None
        :type signer: SuiAddress, optional
        :param input_coins: the Sui coins to be used in this transaction, including the coin for gas payment.,
            defaults to None
        :type input_coins: SuiArray[ObjectID], optional
        :param recipient: the recipient Sui address, defaults to None
        :type recipient: SuiAddress, optional
        :param gas_budget: the gas budget, the transaction will fail if the gas cost exceed the budget, defaults to None
        :type gas_budget: SuiInteger, optional
        """
        inargs = locals().copy()
        super().__init__("sui_payAllSui")
        self.signer: SuiAddress = None
        self.input_coins: SuiArray[ObjectID] = None
        self.recipient: SuiAddress = None
        self.gas_budget: SuiInteger = None
        for hit in self.payallsui_kwords & set(inargs.keys()):
            if hit == "input_coins" and isinstance(inargs[hit], list):
                setattr(self, hit, SuiArray(inargs[hit]))
            else:
                setattr(self, hit, inargs[hit])

    def set_signer(self, address: SuiAddress) -> "PayAllSui":
        """Set the gas owner signer."""
        self.signer: SuiAddress = address
        return self

    def set_input_coins(self, obj: list[ObjectID]) -> "PayAllSui":
        """Set input coin array."""
        self.input_coins: SuiArray[ObjectID] = SuiArray[ObjectID](obj)
        return self

    def set_recipient(self, obj: SuiAddress) -> "PayAllSui":
        """Set the address for the receiver."""
        self.recipient: SuiAddress = obj
        return self

    def set_gas_budget(self, obj: SuiInteger) -> "PayAllSui":
        """Set the amount for transaction payment."""
        self.gas_budget: SuiInteger = obj
        return self

    def _collect_parameters(self) -> list[SuiBaseType]:
        """Collect the call parameters."""
        return self._pull_vars()


class MergeCoin(_MoveCallTransactionBuilder):
    """MergeCoin When executed, merge multiple coins into one coin."""

    merge_kwords: set[str] = {"signer", "gas_object", "gas_budget", "primary_coin", "coin_to_merge"}

    def __init__(
        self,
        *,
        signer: SuiAddress = None,
        primary_coin: ObjectID = None,
        coin_to_merge: ObjectID = None,
        gas: ObjectID = None,
        gas_budget: SuiInteger = None,
    ) -> None:
        """__init__ MergeCoin Builder initializer.

        :param signer: the transaction signer's Sui address, defaults to None
        :type signer: SuiAddress, optional
        :param primary_coin: the coin object to merge into, this coin will remain after the transaction,
            defaults to None
        :type primary_coin: ObjectID, optional
        :param coin_to_merge: the coin object to be merged, this coin will be destroyed,
            the balance will be added to `primary_coin`, defaults to None
        :type coin_to_merge: ObjectID, optional
        :param gas: gas object to be used in this transaction, defaults to None
        :type gas_object: ObjectID, optional
        :param gas_budget: the gas budget, the transaction will fail if the gas cost exceed the budget, defaults to None
        :type gas_budget: SuiInteger, optional
        """
        inargs = locals().copy()
        super().__init__("sui_mergeCoins")
        self.signer: SuiAddress = None
        self.primary_coin: ObjectID = None
        self.coin_to_merge: ObjectID = None
        self.gas: ObjectID = None
        self.gas_budget: SuiInteger = None
        for hit in self.merge_kwords & set(inargs.keys()):
            setattr(self, hit, inargs[hit])

    def set_signer(self, address: SuiAddress) -> "MergeCoin":
        """Set the gas owner signer."""
        self.signer: SuiAddress = address
        return self

    def set_gas_object(self, obj: ObjectID) -> "MergeCoin":
        """Set sui object gas object."""
        self.gas: ObjectID = sui_utils.as_object_id(obj)
        return self

    def set_gas_budget(self, obj: SuiInteger) -> "MergeCoin":
        """Set the amount for transaction payment."""
        self.gas_budget: SuiInteger = obj
        return self

    def set_coin_to_merge(self, obj: ObjectID) -> "MergeCoin":
        """Set the address for the receiver."""
        self.coin_to_merge: ObjectID = sui_utils.as_object_id(obj)
        return self

    def set_primary_coin(self, obj: ObjectID) -> "MergeCoin":
        """Set the primary coin to merge into."""
        self.primary_coin: ObjectID = sui_utils.as_object_id(obj)
        return self

    def _collect_parameters(self) -> list[SuiBaseType]:
        """Collect the call parameters."""
        return self._pull_vars()


class SplitCoin(_MoveCallTransactionBuilder):
    """SplitCoin When executed, split a coin object into multiple coins."""

    split_kwords: set[str] = {"signer", "gas_object", "gas_budget", "coin_object_id", "split_amounts"}

    def __init__(
        self,
        *,
        signer: SuiAddress = None,
        coin_object_id: ObjectID = None,
        split_amounts: SuiArray[SuiInteger] = None,
        gas_object: ObjectID = None,
        gas_budget: SuiInteger = None,
    ) -> None:
        """__init__ SplitCoin Builder initializer.

        :param signer: the transaction signer's Sui address, defaults to None
        :type signer: SuiAddress, optional
        :param coin_object_id: the coin object to be spilt, defaults to None
        :type coin_object_id: ObjectID, optional
        :param split_amounts: the amounts to split out from the coin, defaults to None
        :type split_amounts: SuiArray[SuiInteger], optional
        :param gas_object: gas object to be used in this transaction, defaults to None
        :type gas_object: ObjectID, optional
        :param gas_budget: the gas budget, the transaction will fail if the gas cost exceed the budget, defaults to None
        :type gas_budget: SuiInteger, optional
        """
        inargs = locals().copy()
        super().__init__("sui_splitCoin")
        self.signer: SuiAddress = None
        self.coin_object_id: ObjectID = None
        self.split_amounts: SuiArray[SuiInteger] = None
        self.gas_object: ObjectID = None
        self.gas_budget: SuiInteger = None
        for hit in self.split_kwords & set(inargs.keys()):
            setattr(self, hit, inargs[hit])

    def set_signer(self, address: SuiAddress) -> "SplitCoin":
        """Set the gas owner signer."""
        self.signer: SuiAddress = address
        return self

    def set_gas_object(self, obj: ObjectID) -> "SplitCoin":
        """Set sui object gas object."""
        self.gas_object: ObjectID = sui_utils.as_object_id(obj)
        return self

    def set_gas_budget(self, obj: SuiInteger) -> "SplitCoin":
        """Set the amount for transaction payment."""
        self.gas_budget: SuiInteger = obj
        return self

    def set_coin_object_id(self, obj: ObjectID) -> "SplitCoin":
        """Set the object ID for the coin being split."""
        self.coin_object_id: ObjectID = sui_utils.as_object_id(obj)
        return self

    def set_split_amounts(self, obj: list[SuiInteger]) -> "SplitCoin":
        """Set the amounts to split the coin into."""
        self.split_amounts: SuiArray[SuiInteger] = SuiArray[SuiInteger](obj)
        return self

    def _collect_parameters(self) -> list[SuiBaseType]:
        """Collect the call parameters."""
        return self._pull_vars()


class SplitCoinEqually(_MoveCallTransactionBuilder):
    """SplitCoinEqually When executed, splits a coin object into multiple equal-size coins."""

    splite_kwords: set[str] = {"signer", "gas", "gas_budget", "coin_object_id", "split_count"}

    def __init__(
        self,
        *,
        signer: SuiAddress = None,
        coin_object_id: ObjectID = None,
        split_count: SuiInteger = None,
        gas: ObjectID = None,
        gas_budget: SuiInteger = None,
    ) -> None:
        """__init__ SplitCoinEqually Builder initializer.

        :param signer: the transaction signer's Sui address, defaults to None
        :type signer: SuiAddress, optional
        :param coin_object_id: the coin object to be spilt, defaults to None
        :type coin_object_id: ObjectID, optional
        :param split_count: the number of coins to split into, defaults to None
        :type split_count: SuiInteger, optional
        :param gas: gas object to be used in this transaction, defaults to None
        :type gas: ObjectID, optional
        :param gas_budget: the gas budget, the transaction will fail if the gas cost exceed the budget, defaults to None
        :type gas_budget: SuiInteger, optional
        """
        inargs = locals().copy()
        super().__init__("sui_splitCoinEqual")
        self.signer: SuiAddress = None
        self.coin_object_id: ObjectID = None
        self.split_count: SuiInteger = None
        self.gas: ObjectID = None
        self.gas_budget: SuiInteger = None
        for hit in self.splite_kwords & set(inargs.keys()):
            setattr(self, hit, inargs[hit])

    def set_signer(self, address: SuiAddress) -> "SplitCoin":
        """Set the gas owner signer."""
        self.signer: SuiAddress = address
        return self

    def set_gas_object(self, obj: ObjectID) -> "SplitCoin":
        """Set sui object gas object."""
        self.gas: ObjectID = sui_utils.as_object_id(obj)
        return self

    def set_gas_budget(self, obj: SuiInteger) -> "SplitCoin":
        """Set the amount for transaction payment."""
        self.gas_budget: SuiInteger = obj
        return self

    def set_coin_object_id(self, obj: ObjectID) -> "SplitCoin":
        """Set the object ID for the coin being split."""
        self.coin_object_id: ObjectID = sui_utils.as_object_id(obj)
        return self

    def set_split_count(self, obj: SuiInteger) -> "SplitCoin":
        """Set the amounts to split the coin into."""
        self.split_count: SuiInteger = obj
        return self

    def _collect_parameters(self) -> list[SuiBaseType]:
        """Collect the call parameters."""
        return self._pull_vars()


class BatchParameter(SuiMap):
    """BatchParameter is abstraction for TransferObjectParams and MoveCallRequestParams."""

    @abstractmethod
    def realize_parameters(self) -> dict:
        """Satisfied by subclasses."""


class TransferObjectParams(BatchParameter):
    """For submitting transfer in a batch transaction."""

    def __init__(self, *, receiver: SuiAddress, transfer_object: SuiGas) -> None:
        """Initialize transfer properties."""
        self.receiver: SuiAddress = receiver
        self.transfer_object: SuiGas = transfer_object
        super().__init__("transferObjectRequestParams", {})

    def realize_parameters(self) -> dict:
        """Satisfied by subclasses."""
        out_dict = self.map["transferObjectRequestParams"]
        out_dict["recipient"] = self.receiver.address
        out_dict["objectId"] = self.transfer_object.identifier.value
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


class BatchTransaction(_MoveCallTransactionBuilder):
    """BatchTransaction When executed, runs transactions included in the batch."""

    def __init__(
        self, signer: SuiAddress, transaction_params: SuiArray[BatchParameter], gas: ObjectID, gas_budget: SuiInteger
    ) -> None:
        """__init__ BatchTransaction Builder initializer.

        :param signer: the transaction signer's Sui address
        :type signer: SuiAddress
        :param transaction_params: list of transaction BatchParameter objects
        :type transaction_params: SuiArray[BatchParameter]
        :param gas: gas object to be used in this transaction
        :type gas: ObjectID
        :param gas_budget: the gas budget, the transaction will fail if the gas cost exceed the budget
        :type gas_budget: SuiInteger
        :raises ValueError: _description_
        """
        super().__init__("sui_batchTransaction")
        self.signer: SuiAddress = signer
        self.single_transaction_params = None
        self.gas: ObjectID = sui_utils.as_object_id(gas)
        self.gas_budget = gas_budget

        for item in transaction_params.array:
            if not isinstance(item, BatchParameter):
                raise ValueError(f"{item} is not of type BatchParameter")
        self.single_transaction_params = transaction_params

    def _collect_parameters(self) -> list[SuiBaseType]:
        """Collect the call parameters."""
        collection = []
        for item in self.single_transaction_params.array:
            collection.append(item.realize_parameters())
        self.single_transaction_params = SuiArray(collection)
        return self._pull_vars()


class Publish(_MoveCallTransactionBuilder):
    """Publish When executed, Publish a Move package to the SUI blockchain."""

    publish_kwords = {"sender", "compiled_modules", "gas", "gas_budget"}

    def __init__(
        self,
        *,
        sender: SuiAddress = None,
        compiled_modules: SuiArray[SuiString] = None,
        gas: ObjectID = None,
        gas_budget: SuiInteger = None,
    ) -> None:
        """__init__ Publish Builder initializer.

        :param sender: the transaction signer's Sui address defaults to None
        :type sender: SuiAddress, optional
        :param compiled_modules: the compiled bytes of a move package's modules, defaults to None
        :type compiled_modules: SuiArray[SuiString], optional
        :param gas: gas object to be used in this transaction, defaults to None
        :type gas: ObjectID, optional
        :param gas_budget: the gas budget, the transaction will fail if the gas cost exceed the budget, defaults to None
        :type gas_budget: SuiInteger, optional
        """
        inargs = locals().copy()
        super().__init__("sui_publish")
        self.sender: SuiAddress = None
        self.compiled_modules: SuiArray[SuiString] = None
        self.gas: ObjectID = None
        self.gas_budget: SuiInteger = None
        for hit in self.publish_kwords & set(inargs.keys()):
            if hit == "compiled_modules" and isinstance(inargs[hit], list):
                setattr(self, hit, SuiArray(inargs[hit]))
            else:
                setattr(self, hit, inargs[hit])

    def set_sender(self, obj: SuiAddress) -> "Publish":
        """Set the publisher address."""
        self.sender: SuiAddress = obj
        return self

    def set_compiled_modules(self, obj: SuiArray[SuiString]) -> "Publish":
        """Set the publishing package base64 modules string array."""
        self.compiled_modules: SuiArray[SuiString] = obj
        return self

    def set_gas_object(self, obj: ObjectID) -> "Publish":
        """Set sui object gas object."""
        self.gas: ObjectID = sui_utils.as_object_id(obj)
        return self

    def set_gas_budget(self, obj: SuiInteger) -> "Publish":
        """Set the amount for transaction payment."""
        self.gas_budget: SuiInteger = obj
        return self

    def _collect_parameters(self) -> list[SuiBaseType]:
        """Collect the call parameters."""
        return self._pull_vars()


class MoveCall(_MoveCallTransactionBuilder):
    """MoveCall When executed, executes a Move call on the network.

    Calling the specified function in the module of a given package.
    """

    move_kwords: set[str] = {
        "signer",
        "package_object_id",
        "module",
        "function",
        "type_arguments",
        "arguments",
        "gas",
        "gas_budget",
    }
    _movecall_array_keys: set[str] = {
        "type_arguments",
        "arguments",
    }

    def __init__(
        self,
        *,
        signer: SuiAddress = None,
        package_object_id: ObjectID = None,
        module: SuiString = None,
        function: SuiString = None,
        type_arguments: SuiArray[SuiString] = None,
        arguments: SuiArray[SuiString] = None,
        gas: ObjectID = None,
        gas_budget: SuiInteger = None,
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
        :param gas_budget: the gas budget, the transaction will fail if the gas cost exceed the budget, defaults to None
        :type gas_budget: SuiInteger, optional
        """
        inargs = locals().copy()
        super().__init__("sui_moveCall")
        self.signer: SuiAddress = None
        self.package_object_id: ObjectID = None
        self.module: SuiString = None
        self.function: SuiString = None
        self.type_arguments: SuiArray[SuiString] = SuiArray[SuiString]([])
        self.arguments: SuiArray[SuiString] = SuiArray[SuiString]([])
        self.gas: ObjectID = None
        self.gas_budget: SuiInteger = None
        for hit in self.move_kwords & set(inargs.keys()):
            if hit in self._movecall_array_keys:
                if inargs[hit]:
                    setattr(self, hit, SuiArray(inargs[hit]))
                else:
                    setattr(self, hit, SuiArray([]))
            else:
                setattr(self, hit, inargs[hit])

    def set_signer(self, obj: SuiAddress) -> "MoveCall":
        """Set signers address."""
        self.signer: SuiAddress = obj
        return self

    def set_module(self, obj: SuiString) -> "MoveCall":
        """Set sui move module name."""
        self.module: SuiString = obj
        return self

    def set_function(self, obj: SuiString) -> "MoveCall":
        """Set sui move function name."""
        self.function: SuiString = obj
        return self

    def set_types(self, obj: SuiArray[SuiString]) -> "MoveCall":
        """Set sui generic types (if any)."""
        self.type_arguments: SuiArray[SuiString] = obj
        return self

    def set_arguments(self, obj: SuiArray[SuiString]) -> "MoveCall":
        """Set sui move call arguments (if any)."""
        self.arguments: SuiArray[SuiString] = obj
        return self

    def set_gas_object(self, obj: ObjectID) -> "MoveCall":
        """Set sui object gas object."""
        self.gas: ObjectID = sui_utils.as_object_id(obj)
        return self

    def set_gas_budget(self, obj: SuiInteger) -> "MoveCall":
        """Set the amount for transaction payment."""
        self.gas_budget: SuiInteger = obj
        return self

    def _collect_parameters(self) -> list[SuiBaseType]:
        """Collect the call parameters."""
        return self._pull_vars()
