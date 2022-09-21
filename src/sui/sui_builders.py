"""SUI Builders for RPC."""
from typing import Any
from abstracts import Builder


class BaseBuilder(Builder):
    """Base Builder Class."""

    def __init__(self) -> None:
        """Initialize Builder."""
        super().__init__()
        self._params = []
        self._method = ""

    @property
    def params(self) -> list[str]:
        """Return parameters mutable list."""
        return self._params

    def add_parameter(self, param: str) -> Any:
        """Append a parameter to end."""
        self.params.append(param)
        return self

    @property
    def data(self) -> dict:
        """Return copy of the current data state."""
        dcopy = self._data.copy()
        dcopy["params"] = self._params
        dcopy["method"] = self.method
        return dcopy

    @property
    def header(self) -> dict:
        """Return copy of the current header."""
        return self._header.copy()

    @property
    def method(self) -> str:
        """Inspect method."""
        return self._method


class GetObjectsOwnedByAddress(BaseBuilder):
    """Fetch Objects for Address."""

    def __init__(self) -> None:
        """Initialize Builder."""
        super().__init__()
        self._method = "sui_getObjectsOwnedByAddress"


class GetObjectsOwnedByObject(BaseBuilder):
    """Fetch Objects for Address."""

    def __init__(self) -> None:
        """Initialize Builder."""
        super().__init__()
        self._method = "sui_getObjectsOwnedByObject"


class GetObject(BaseBuilder):
    """Fetch Object detail for Object ID."""

    def __init__(self) -> None:
        """Initialize Builder."""
        super().__init__()
        self._method = "sui_getObject"


class GetPackage(BaseBuilder):
    """Fetch package definitions including modules and functions."""

    def __init__(self) -> None:
        """Initialize builder."""
        super().__init__()
        self._method = "sui_getNormalizedMoveModulesByPackage"


class GetRpcAPI(BaseBuilder):
    """Fetch the RPC API available for endpoint."""

    def __init__(self) -> None:
        """Initialize builder."""
        super().__init__()
        self._method = "rpc.discover"
