#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Abstract base class for async clients."""

import functools
from abc import ABC, abstractmethod
from typing import Any, ClassVar


class AsyncClientBase(ABC):
    """Common async client interface for all pysui async clients.

    Defines the contract that all protocol-specific async clients must implement.
    Protocol-specific execute methods (e.g., execute_query_node for GQL,
    execute_grpc_request for gRPC) remain on concrete client classes and are
    not abstracted here.
    """

    _protocol: ClassVar[str] = ""

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

    async def execute_for_all(
        self,
        *,
        command: "SuiCommand",
        timeout: float | None = None,
        headers: dict | None = None,
    ) -> "SuiRpcResult":
        """Execute a pageable SuiCommand and accumulate all pages into one result.

        For non-pageable commands delegates to execute() unchanged. For pageable
        commands loops until next_page_token is None, extending the items list
        in place on the first page's result, then returns that accumulated result
        with next_page_token cleared.

        The caller's command instance is not mutated — a shallow copy is used
        internally to carry the page token between iterations.

        :param command: A SuiCommand instance describing the operation (not mutated)
        :param timeout: Per-page timeout in seconds (applied per page, not total)
        :param headers: Optional headers/metadata passed to the transport
        :return: SuiRpcResult with fully accumulated result_data
        """
        import copy
        from pysui import SuiRpcResult  # lazy — avoids circular import at module load

        is_pageable = getattr(command, f"is_pageable_{self._protocol}", False)
        if not is_pageable:
            return await self.execute(command=command, timeout=timeout, headers=headers)

        items_path: tuple[str, ...] = getattr(
            command, f"paginated_field_path_{self._protocol}"
        )
        if not items_path:
            return SuiRpcResult(
                False,
                f"paginated_field_path_{self._protocol} is not set on {type(command).__name__}",
                None,
            )

        command = copy.copy(command)
        parent_path, items_field = items_path[:-1], items_path[-1]

        def _walk(obj, path):
            return functools.reduce(getattr, path, obj)

        accumulator = None
        while True:
            result = await self.execute(command=command, timeout=timeout, headers=headers)
            if not result.is_ok():
                return result
            page = result.result_data
            try:
                if accumulator is None:
                    accumulator = page
                else:
                    getattr(_walk(accumulator, parent_path), items_field).extend(
                        getattr(_walk(page, parent_path), items_field)
                    )
                parent_obj = _walk(page, parent_path)
                token = getattr(parent_obj, "next_page_token", None)
            except AttributeError as exc:
                return SuiRpcResult(
                    False,
                    f"Paging path misconfigured for {type(command).__name__}: {exc}",
                    None,
                )
            if token is None:
                break
            command.next_page_token = token

        _walk(accumulator, parent_path).next_page_token = None
        return SuiRpcResult(True, "", accumulator)
