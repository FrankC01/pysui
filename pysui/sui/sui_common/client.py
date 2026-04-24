#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Pysui generic client abstraction."""

from abc import ABC, abstractmethod
from typing import Any, Optional
from pysui import PysuiConfiguration
from pysui.sui.sui_common.types import TransactionConstraints


class PysuiClient(ABC):
    """Abstract async client base shared by GraphQL and gRPC protocol layers."""

    def __init__(
        self,
        *,
        pysui_config: PysuiConfiguration,
        default_header: Optional[dict] = None,
    ):
        """."""
        self._pysui_config: PysuiConfiguration = pysui_config
        self._default_header = default_header if default_header else {}

    @property
    def config(self) -> PysuiConfiguration:
        """Fetch the Pysui configuration."""
        return self._pysui_config

    @property
    @abstractmethod
    def current_gas_price(self) -> int:
        """Fetch the current epoch gas price."""
        pass

    @abstractmethod
    def protocol(
        self, for_version: Optional[str] = None
    ) -> TransactionConstraints:
        """Fetch the protocol constraint block."""
        pass

    @abstractmethod
    def transaction(self, **kwargs) -> Any:
        """Return a transaction builder for this client's protocol."""
        pass

    def close(self) -> None:
        """Release resources held by this client. Override if cleanup is needed."""
        pass
