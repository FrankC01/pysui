#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Abstract base class for async clients."""

import functools
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, ClassVar, Optional

import pysui.sui.sui_grpc.suimsgs.sui.rpc.v2 as sui_prot

if TYPE_CHECKING:
    from pysui import SuiRpcResult
    from pysui.sui.sui_common.config import PysuiConfiguration
    from pysui.sui.sui_common.sui_command import SuiCommand


class AsyncClientBase(ABC):
    """Common async client interface for all pysui async clients.

    Defines the contract that all protocol-specific async clients must implement.
    Protocol-specific execute methods (e.g., execute_query_node for GQL,
    execute_grpc_request for gRPC) remain on concrete client classes and are
    not abstracted here.
    """

    _protocol: ClassVar[str] = ""
    _protocol_config: Optional[sui_prot.ProtocolConfig] = None
    """Cached protocol configuration, fetched on first gasless eligibility check."""

    @property
    @abstractmethod
    def config(self) -> "PysuiConfiguration":
        """Fetch the Pysui configuration."""

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
            result = await self.execute(command=command, timeout=timeout, headers=headers)
            return await self._apply_compound(command, result, timeout=timeout, headers=headers)

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
        return await self._apply_compound(
            command, SuiRpcResult(True, "", accumulator), timeout=timeout, headers=headers
        )

    async def _apply_compound(
        self,
        command: Any,
        result: "SuiRpcResult",
        *,
        timeout: float | None = None,
        headers: dict | None = None,
    ) -> "SuiRpcResult":
        """Drive sub-collection fetches declared in compound_sub_collections_{protocol}."""
        if not result.is_ok():
            return result
        data = result.result_data
        specs = getattr(command, f"compound_sub_collections_{self._protocol}", None)
        if specs:
            for has_next_attr, sub_cmd_class, sub_src_field, parent_field in specs:
                if not getattr(data, has_next_attr, False):
                    continue
                sub_cmd = sub_cmd_class(
                    package=command.package, module_name=command.module_name
                )
                sub_result = await self.execute_for_all(
                    command=sub_cmd, timeout=timeout, headers=headers
                )
                if not sub_result.is_ok():
                    return sub_result
                setattr(data, parent_field, getattr(sub_result.result_data, sub_src_field))
        item_specs = getattr(command, f"compound_items_{self._protocol}", None)
        if item_specs:
            for item_path, item_cmd_class, item_key_attr, cmd_kwarg, trunc_attrs in item_specs:
                *parent_path, items_field = item_path
                parent = functools.reduce(getattr, parent_path, data)
                items = getattr(parent, items_field, [])
                for i, item in enumerate(items):
                    if not any(getattr(item, attr, False) for attr in trunc_attrs):
                        continue
                    key_val = getattr(item, item_key_attr)
                    sub_cmd = item_cmd_class(
                        package=command.package, **{cmd_kwarg: key_val}
                    )
                    sub_result = await self.execute_for_all(
                        command=sub_cmd, timeout=timeout, headers=headers
                    )
                    if sub_result.is_ok():
                        items[i] = sub_result.result_data
        return result

    async def gasless_for(self, *, coin_tokens: list[str]) -> bool:
        """Determine whether a set of coin types are eligible for gasless transactions.

        Fetches and caches the protocol configuration on first use. Returns
        False when gasless is disabled at the protocol level, when the
        allowlist is absent from the protocol configuration (the GraphQL
        protocol does not expose it), or when any of the coin types is not
        allowlisted. A PTB may reference more than one stablecoin type; all
        of them must be allowlisted for the PTB to qualify.

        :param coin_tokens: Canonical Move type strings of the coins, for
            example ``0x...::usdc::USDC``
        :type coin_tokens: list[str]
        :returns: True if every coin type is eligible for gasless transactions
        :rtype: bool
        """
        import pysui.sui.sui_common.sui_commands as cmd

        if self._protocol_config is None:
            _result = await self.execute(command=cmd.GetProtocolConfig())
            if not _result.is_ok():
                raise ValueError(_result.result_string)
            self._protocol_config = _result.result_data
        _configs = self._protocol_config.configs
        _enabled = _configs.get("enable_gasless")
        if _enabled is None or _enabled.bool_value is not True:
            return False
        _allowed = _configs.get("gasless_allowed_token_types")
        if _allowed is None:
            return False
        _allowed_types = {_entry[0] for _entry in _allowed.to_dict()}
        return all(_token in _allowed_types for _token in coin_tokens)
