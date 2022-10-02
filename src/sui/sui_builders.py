"""SUI Builders for RPC."""

from abstracts import Builder
from sui.sui_types import SuiType


class BaseBuilder(Builder):
    """Base Builder Class."""

    def __init__(self, method: str, txn_required: bool) -> None:
        """Initialize Builder."""
        super().__init__()
        self._method = method
        self._params = []
        self._arguments = []
        self._txn_required = txn_required
        self._arguments_required = False

    @property
    def params(self) -> list[SuiType]:
        """Return parameters list."""
        return self._params

    def add_parameter(self, param: SuiType) -> Builder:
        """Append a parameter to end."""
        self._params.append(param)
        return self

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


class _RawParameterBuilder(BaseBuilder):
    """Builders for simple single parameter transactions."""

    def __init__(self, method: str) -> None:
        """Initialize builder."""
        super().__init__(method, False)


class GetObjectsOwnedByAddress(_RawParameterBuilder):
    """Fetch Objects for Address."""

    def __init__(self) -> None:
        """Initialize Builder."""
        super().__init__("sui_getObjectsOwnedByAddress")


class GetObjectsOwnedByObject(_RawParameterBuilder):
    """Fetch Objects for Address."""

    def __init__(self) -> None:
        """Initialize Builder."""
        super().__init__("sui_getObjectsOwnedByObject")


class GetObject(_RawParameterBuilder):
    """Fetch Object detail for Object ID."""

    def __init__(self) -> None:
        """Initialize Builder."""
        super().__init__("sui_getObject")


class GetPackage(_RawParameterBuilder):
    """Fetch package definitions including modules and functions."""

    def __init__(self) -> None:
        """Initialize builder."""
        super().__init__("sui_getNormalizedMoveModulesByPackage")


class GetRpcAPI(_RawParameterBuilder):
    """Fetch the RPC API available for endpoint."""

    def __init__(self) -> None:
        """Initialize builder."""
        super().__init__("rpc.discover")


class _TransactionBasedBuilder(BaseBuilder):
    """Builders that must be processed, signed then executed."""

    def __init__(self, method: str) -> None:
        """Initialize builder."""
        super().__init__(method, True)


class TransferSui(_TransactionBasedBuilder):
    """Transfers Sui coin from one recipient to the other."""

    def __init__(self) -> None:
        """Initialize builder."""
        super().__init__("sui_transferSui")
