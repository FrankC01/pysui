"""SUI Builders for RPC."""

from abc import abstractmethod
from abstracts import Builder
from sui.sui_types import SuiType, ObjectInfo, ObjectID
from sui.sui_crypto import SuiAddress


class SuiBaseBuilder(Builder):
    """Base Builder Class."""

    def __init__(self, method: str, txn_required: bool) -> None:
        """Initialize Builder."""
        super().__init__()
        self._method = method
        self._arguments = []
        self._txn_required = txn_required
        self._arguments_required = False

    @abstractmethod
    def _collect_parameters(self) -> list[SuiType]:
        """Collect the call parameters."""

    @property
    def params(self) -> list[SuiType]:
        """Return parameters list."""
        return self._collect_parameters()

    @property
    def arguments(self) -> list[SuiType]:
        """Return arguments list."""
        return self._arguments

    def add_argument(self, arg: SuiType) -> Builder:
        """Append an argument to end."""
        self._arguments.append(arg)
        return self

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

    @property
    def args_required(self) -> bool:
        """Get arguments required flag."""
        return self._arguments_required


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

    def _collect_parameters(self) -> list[SuiType]:
        """Collect the call parameters."""
        return [self.object_id]


class GetPackage(_NativeTransactionBuilder):
    """Fetch package definitions including modules and functions."""

    def __init__(self, package: SuiType = None) -> None:
        """Initialize builder."""
        super().__init__("sui_getNormalizedMoveModulesByPackage")
        self.package = package

    def set_package(self, package: SuiType) -> "GetPackage":
        """Set the package to retrieve."""
        self.package = package
        return self

    def _collect_parameters(self) -> list[SuiType]:
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


class _MoveCallTransactionBuilder(SuiBaseBuilder):
    """Builders that must be processed, signed then executed."""

    def __init__(self, method: str) -> None:
        """Initialize builder."""
        super().__init__(method, True)


class TransferSui(_MoveCallTransactionBuilder):
    """Transfers Sui coin from one recipient to the other."""

    def __init__(self) -> None:
        """Initialize builder."""
        super().__init__("sui_transferSui")

    def _collect_parameters(self) -> list[SuiType]:
        """Collect the call parameters."""
        raise NotImplementedError
