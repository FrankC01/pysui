"""SUI Builders for RPC."""

from abc import abstractmethod
from enum import IntEnum
from abstracts import Builder, PublicKey, SignatureScheme
from sui.sui_types import (
    SuiType,
    ObjectInfo,
    ObjectID,
    SuiNumber,
    SuiTxBytes,
    SuiSignature,
    SuiArray,
    SuiAddress,
    SuiBaseType,
)


class SuiRequestType(IntEnum):
    """Key encoding scheme variations."""

    IMMEDIATERETURN = 0
    WAITFORTXCERT = 1
    WAITFOREFFECTSCERT = 2
    WAITFORLOCALEXECUTION = 3

    def as_str(self) -> str:
        """Get scheme as string."""
        if self is SuiRequestType.IMMEDIATERETURN:
            return "ImmediateReturn"
        if self is SuiRequestType.WAITFORTXCERT:
            return "WaitForTxCert"
        if self is SuiRequestType.WAITFOREFFECTSCERT:
            return "WaitForEffectsCert"
        if self is SuiRequestType.WAITFORLOCALEXECUTION:
            return "WaitForLocalExecution"
        raise TypeError(f"Unknown request type {self.name}")

    @property
    def request_type(self) -> str:
        """Satisfy transaction verification."""
        return self.as_str()


class SuiBaseBuilder(Builder):
    """
    Base Sui API Builder Class.

    Subclasses must identify public vars that are
    required by Sui RPC API.
    """

    def __init__(self, method: str, txn_required: bool) -> None:
        """Initialize Builder."""
        super().__init__()
        self._method = method
        self._txn_required = txn_required

    @abstractmethod
    def _collect_parameters(self) -> list[SuiType]:
        """Collect the call parameters."""

    @property
    def params(self) -> list[SuiType]:
        """Return parameters list."""
        return self._collect_parameters()

    @property
    def header(self) -> dict:
        """Return copy of the current header."""
        return self._header

    @property
    def method(self) -> str:
        """Return method."""
        return self._method

    @property
    def txn_required(self) -> bool:
        """Get transaction required flag."""
        return self._txn_required

    def _pull_vars(self) -> list[SuiType]:
        var_map = vars(self)
        return [val for key, val in var_map.items() if key[0] != "_"]


class _NativeTransactionBuilder(SuiBaseBuilder):
    """Builders for simple single parameter transactions."""

    def __init__(self, method: str) -> None:
        """Initialize builder."""
        super().__init__(method, False)


class GetObjectsOwnedByAddress(_NativeTransactionBuilder):
    """Fetch Objects for Address."""

    def __init__(self, address: SuiAddress = None) -> None:
        """Initialize Builder."""
        super().__init__("sui_getObjectsOwnedByAddress")
        self.address = address

    def set_address(self, address: SuiAddress) -> "GetObjectsOwnedByAddress":
        """Set the address to fetch objects owned by."""
        self.address = address
        return self

    def _collect_parameters(self) -> list[SuiAddress]:
        """Collect the call parameters."""
        return [self.address]


class GetObjectsOwnedByObject(_NativeTransactionBuilder):
    """Fetch Objects for Address."""

    def __init__(self, sui_object: ObjectInfo = None) -> None:
        """Initialize Builder."""
        super().__init__("sui_getObjectsOwnedByObject")
        self.object_id = sui_object

    def set_object(self, sui_object: ObjectInfo) -> "GetObjectsOwnedByObject":
        """Set the object to fetch objects owned by."""
        self.object_id = sui_object
        return self

    def _collect_parameters(self) -> list[ObjectInfo]:
        """Collect the call parameters."""
        return [self.object_id]


class GetObject(_NativeTransactionBuilder):
    """Fetch Object detail for Object ID."""

    def __init__(self, sui_object: ObjectInfo = None) -> None:
        """Initialize Builder."""
        super().__init__("sui_getObject")
        self.object_id = sui_object

    def set_object(self, sui_object: ObjectInfo) -> "GetObjectsOwnedByObject":
        """Set the object to fetch objects owned by."""
        self.object_id = sui_object
        return self

    def _collect_parameters(self) -> list[ObjectInfo]:
        """Collect the call parameters."""
        return [self.object_id]


class GetRawPackage(_NativeTransactionBuilder):
    """Fetch package onject information."""

    def __init__(self, package_id: ObjectID = None) -> None:
        """Initialize builder."""
        super().__init__("sui_getObject")
        self.object_id = package_id

    def set_object_id(self, package_id: ObjectID) -> "GetRawPackage":
        """Set the package object id to retrieve."""
        self.object_id = package_id
        return self

    def _collect_parameters(self) -> list[ObjectID]:
        """Collect the call parameters."""
        return [self.object_id]


class GetPackage(_NativeTransactionBuilder):
    """Fetch package definitions including modules and functions."""

    def __init__(self, package: ObjectID = None) -> None:
        """Initialize builder."""
        super().__init__("sui_getNormalizedMoveModulesByPackage")
        self.package: ObjectID = package

    def set_package(self, package: ObjectID) -> "GetPackage":
        """Set the package to retrieve."""
        self.package: ObjectID = package
        return self

    def _collect_parameters(self) -> list[ObjectID]:
        """Collect the call parameters."""
        return [self.package]


class GetRpcAPI(_NativeTransactionBuilder):
    """Fetch the RPC API available for endpoint."""

    def __init__(self) -> None:
        """Initialize builder."""
        super().__init__("rpc.discover")

    def _collect_parameters(self) -> list[SuiType]:
        """Collect the call parameters."""
        return []


class ExecuteTransaction(_NativeTransactionBuilder):
    """Submit a signed transaction to Sui."""

    def __init__(self) -> None:
        """Initialize builder."""
        super().__init__("sui_executeTransaction")
        self.tx_bytes: SuiTxBytes = None
        self.sig_scheme: SignatureScheme = None
        self.signature: SuiSignature = None
        self.pub_key: PublicKey = None
        self.request_type: SuiRequestType = None

    def set_tx_bytes(self, tbyteb64: SuiTxBytes) -> "ExecuteTransaction":
        """Set the transaction base64 string."""
        self.tx_bytes = tbyteb64
        return self

    def set_sig_scheme(self, sig: SignatureScheme) -> "ExecuteTransaction":
        """Set the transaction base64 string."""
        self.sig_scheme = sig
        return self

    def set_signature(self, sigb64: SuiSignature) -> "ExecuteTransaction":
        """Set the signed transaction base64 string."""
        self.signature = sigb64
        return self

    def set_pub_key(self, pubkey: PublicKey) -> "ExecuteTransaction":
        """Set the public key base64 string."""
        self.pub_key = pubkey
        return self

    def set_request_type(self, rtype: SuiRequestType) -> "ExecuteTransaction":
        """Set the request type for execution."""
        self.request_type = rtype
        return self

    def _collect_parameters(self) -> list[SuiBaseType]:
        """Collect the call parameters."""
        return self._pull_vars()


class DryRunTransaction(_NativeTransactionBuilder):
    """Dry run a signed transaction to Sui."""

    def __init__(self) -> None:
        """Initialize builder."""
        super().__init__("sui_dryRunTransaction")
        self.tx_bytes: SuiTxBytes = None
        self.sig_scheme: SignatureScheme = None
        self.signature: SuiSignature = None
        self.pub_key: PublicKey = None

    def set_tx_bytes(self, tbyteb64: SuiTxBytes) -> "DryRunTransaction":
        """Set the transaction base64 string."""
        self.tx_bytes = tbyteb64
        return self

    def set_sig_scheme(self, sig: SignatureScheme) -> "DryRunTransaction":
        """Set the transaction base64 string."""
        self.sig_scheme = sig
        return self

    def set_signature(self, sigb64: SuiSignature) -> "DryRunTransaction":
        """Set the signed transaction base64 string."""
        self.signature = sigb64
        return self

    def set_pub_key(self, pubkey: PublicKey) -> "DryRunTransaction":
        """Set the public key base64 string."""
        self.pub_key = pubkey
        return self

    def _collect_parameters(self) -> list[SuiBaseType]:
        """Collect the call parameters."""
        return self._pull_vars()


class _MoveCallTransactionBuilder(SuiBaseBuilder):
    """Builders that must be processed, signed then executed."""

    def __init__(self, method: str) -> None:
        """Initialize builder."""
        super().__init__(method, True)


class TransferObject(_MoveCallTransactionBuilder):
    """Transfers Sui object from one recipient to the other."""

    def __init__(self) -> None:
        """Initialize builder."""
        super().__init__("sui_transferObject")
        raise NotImplementedError

    def _collect_parameters(self) -> list[SuiBaseType]:
        """Collect the call parameters."""
        return self._pull_vars()


class TransferSui(_MoveCallTransactionBuilder):
    """Transfers Sui coin from one recipient to the other."""

    transfer_kwords: set[str] = {"signer", "gas_object", "gas_budget", "recipient", "amount"}

    def __init__(self, **kwargs: dict) -> None:
        """Initialize builder."""
        super().__init__("sui_transferSui")
        self.signer: SuiAddress = None
        self.gas_object: ObjectID = None
        self.gas_budget: SuiNumber = None
        self.recipient: SuiAddress = None
        self.mists: SuiNumber = None
        for key, value in kwargs.items():
            match key:
                case "signer":
                    self.signer = value
                case "gas_object":
                    self.gas_object = value
                case "gas_budget":
                    self.gas_budget = value
                case "recipient":
                    self.recipient = value
                case "amount":
                    self.mists = value
                case _:
                    raise ValueError(f"Unknown TransferSui bulder type {key}")

    def set_signer(self, address: SuiAddress) -> "TransferSui":
        """Set the gas owner signer."""
        self.signer = address
        return self

    def set_gas_object(self, obj: ObjectID) -> "TransferSui":
        """Set sui object gas object."""
        self.gas_object = obj
        return self

    def set_gas_budget(self, obj: SuiNumber) -> "TransferSui":
        """Set the amount for transaction payment."""
        self.gas_budget: SuiNumber = obj
        return self

    def set_recipient(self, obj: SuiAddress) -> "TransferSui":
        """Set the address for the receiver."""
        self.recipient: SuiAddress = obj
        return self

    def set_mists(self, obj: SuiNumber) -> "TransferSui":
        """Set the amount to transfer to recipient."""
        self.mists: SuiNumber = obj
        return self

    def _collect_parameters(self) -> list[SuiBaseType]:
        """Collect the call parameters."""
        return self._pull_vars()


class Pay(_MoveCallTransactionBuilder):
    """Transfer, split and merge SUI coins."""

    pay_kwords: set[str] = {"signer", "input_coins", "recipients", "amounts", "gas_object", "gas_budget"}

    def __init__(self, **kwargs: dict) -> None:
        """Initialize builder."""
        super().__init__("sui_pay")
        self.signer: SuiAddress = None
        self.input_coins: SuiArray[ObjectID] = None
        self.recipients: SuiArray[SuiAddress] = None
        self.amounts: SuiArray[SuiNumber] = None
        self.gas_object: ObjectID = None
        self.gas_budget: SuiNumber = None
        for key, value in kwargs.items():
            match key:
                case "signer":
                    self.signer = value
                case "input_coins":
                    self.input_coins = SuiArray[ObjectID](value)
                case "recipients":
                    self.recipients = SuiArray[SuiAddress](value)
                case "amounts":
                    self.amounts = SuiArray[SuiNumber](value)
                case "gas_object":
                    self.gas_object = value
                case "gas_budget":
                    self.gas_budget = value
                case _:
                    raise ValueError(f"Unknown TransferSui bulder type {key}")

    def set_signer(self, address: SuiAddress) -> "Pay":
        """Set the gas owner signer."""
        self.signer: SuiAddress = address
        return self

    def set_input_coins(self, obj: list[ObjectID]) -> "Pay":
        """Set sui object gas object."""
        self.input_coins: SuiArray[ObjectID] = SuiArray[ObjectID](obj)
        return self

    def set_recipients(self, obj: list[SuiAddress]) -> "Pay":
        """Set the address for the receiver."""
        self.recipients: SuiArray[SuiAddress] = SuiArray[SuiAddress](obj)
        return self

    def set_amounts(self, obj: list[SuiNumber]) -> "Pay":
        """Set the amount to transfer to recipient."""
        self.amounts: SuiArray[SuiNumber] = SuiArray[SuiNumber](obj)
        return self

    def set_gas_object(self, obj: ObjectID) -> "Pay":
        """Set sui object gas object."""
        self.gas_object: ObjectID = obj
        return self

    def set_gas_budget(self, obj: SuiNumber) -> "Pay":
        """Set the amount for transaction payment."""
        self.gas_budget: SuiNumber = obj
        return self

    def _collect_parameters(self) -> list[SuiBaseType]:
        """Collect the call parameters."""
        return self._pull_vars()


class MergeCoin(_MoveCallTransactionBuilder):
    """Merge two coins together."""

    merge_kwords: set[str] = {"signer", "gas_object", "gas_budget", "primary_coin", "coin_to_merge"}

    def __init__(self, **kwargs: dict) -> None:
        """Initialize builder."""
        super().__init__("sui_mergeCoins")
        self.signer: SuiAddress = None
        self.primary_coin: ObjectID = None
        self.coin_to_merge: ObjectID = None
        self.gas_object: ObjectID = None
        self.gas_budget: SuiNumber = None
        for key, value in kwargs.items():
            match key:
                case "signer":
                    self.signer = value
                case "gas_object":
                    self.gas_object = value
                case "gas_budget":
                    self.gas_budget = value
                case "primary_coin":
                    self.primary_coin = value
                case "coin_to_merge":
                    self.coin_to_merge = value
                case _:
                    raise ValueError(f"Unknown TransferSui bulder type {key}")

    def set_signer(self, address: SuiAddress) -> "MergeCoin":
        """Set the gas owner signer."""
        self.signer = address
        return self

    def set_gas_object(self, obj: ObjectID) -> "MergeCoin":
        """Set sui object gas object."""
        self.gas_object = obj
        return self

    def set_gas_budget(self, obj: SuiNumber) -> "MergeCoin":
        """Set the amount for transaction payment."""
        self.gas_budget: SuiNumber = obj
        return self

    def set_coin_to_merge(self, obj: ObjectID) -> "MergeCoin":
        """Set the address for the receiver."""
        self.coin_to_merge: ObjectID = obj
        return self

    def set_primary_coin(self, obj: ObjectID) -> "MergeCoin":
        """Set the primary coin to merge into."""
        self.primary_coin: ObjectID = obj
        return self

    def _collect_parameters(self) -> list[SuiBaseType]:
        """Collect the call parameters."""
        return self._pull_vars()


class SplitCoin(_MoveCallTransactionBuilder):
    """Split a coin into a one or more new coins."""

    split_kwords: set[str] = {"signer", "gas_object", "gas_budget", "coin_object_id", "split_amounts"}

    def __init__(self, **kwargs: dict) -> None:
        """Initialize builder."""
        super().__init__("sui_splitCoin")
        self.signer: SuiAddress = None
        self.coin_object_id: ObjectID = None
        self.split_amounts: SuiArray[SuiNumber] = None
        self.gas_object: ObjectID = None
        self.gas_budget: SuiNumber = None
        for key, value in kwargs.items():
            match key:
                case "signer":
                    self.signer: SuiAddress = value
                case "gas_object":
                    self.gas_object: ObjectID = value
                case "gas_budget":
                    self.gas_budget: SuiNumber = value
                case "split_amounts":
                    self.split_amounts = SuiArray[SuiNumber](value)
                case "coin_object_id":
                    self.coin_object_id: ObjectID = value
                case _:
                    raise ValueError(f"Unknown TransferSui bulder type {key}")

    def set_signer(self, address: SuiAddress) -> "SplitCoin":
        """Set the gas owner signer."""
        self.signer = address
        return self

    def set_gas_object(self, obj: ObjectID) -> "SplitCoin":
        """Set sui object gas object."""
        self.gas_object = obj
        return self

    def set_gas_budget(self, obj: SuiNumber) -> "SplitCoin":
        """Set the amount for transaction payment."""
        self.gas_budget: SuiNumber = obj
        return self

    def set_coin_object_id(self, obj: ObjectID) -> "SplitCoin":
        """Set the object ID for the coin being split."""
        self.coin_object_id: ObjectID = obj
        return self

    def set_split_amounts(self, obj: list[SuiNumber]) -> "SplitCoin":
        """Set the amounts to split the coin into."""
        self.split_amounts: SuiArray[SuiNumber] = SuiArray[SuiNumber](obj)
        return self

    def _collect_parameters(self) -> list[SuiBaseType]:
        """Collect the call parameters."""
        return self._pull_vars()
