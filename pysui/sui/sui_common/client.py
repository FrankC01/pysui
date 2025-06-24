#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Pysui generic client abstraction."""

from abc import ABC, abstractmethod
from typing import Optional
from pysui import PysuiConfiguration
import pysui.sui.sui_pgql.pgql_types as pgql_type


class PysuiClient(ABC):
    """Abstract Client."""

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
    ) -> pgql_type.TransactionConstraints:
        """Fetch the protocol constraint block."""
