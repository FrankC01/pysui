#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Abstract base class for async clients."""

from abc import ABC, abstractmethod
from typing import Any


class AsyncClientBase(ABC):
    """Common async client interface for all pysui async clients.

    Defines the contract that all protocol-specific async clients must implement.
    Protocol-specific execute methods (e.g., execute_query_node for GQL,
    execute_grpc_request for gRPC) remain on concrete client classes and are
    not abstracted here.
    """

    @abstractmethod
    async def transaction(self, **kwargs) -> Any:
        """Construct a new async transaction builder.

        :param kwargs: Protocol-specific arguments
        :return: A transaction builder instance
        """

    @abstractmethod
    async def __aenter__(self) -> "AsyncClientBase":
        """Enter async context — client is ready to use."""

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context — release client resources."""

    @abstractmethod
    async def execute(
        self,
        *,
        command: "SuiCommand",
        timeout: float | None = None,
        headers: dict | None = None,
    ) -> "SuiRpcResult":
        """Execute a SuiCommand against this client's protocol.

        :param command: A SuiCommand instance describing the operation
        :param timeout: Optional timeout in seconds
        :param headers: Optional headers/metadata passed to the transport
        :return: SuiRpcResult wrapping the response or error
        """
