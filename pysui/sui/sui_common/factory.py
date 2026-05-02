#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Client factory for protocol-agnostic pysui client construction."""

from typing import Optional

from pysui.abstracts.async_client import AsyncClientBase
from pysui.sui.sui_common.config import PysuiConfiguration
from pysui.sui.sui_common.config.confgroup import GroupProtocol


def client_factory(
    pysui_config: PysuiConfiguration,
    *,
    group_name: Optional[str] = None,
    protocol: Optional[GroupProtocol] = None,
) -> AsyncClientBase:
    """Construct the appropriate async client for the active or specified group.

    When called with only ``pysui_config``, the factory inspects the
    configuration's active group and returns the matching client.

    When ``group_name`` is provided (e.g. a third-party or custom provider
    group), ``protocol`` is **required** because non-standard groups may not
    carry a recognised ``GroupProtocol`` value.  The named group is made
    active on ``pysui_config`` (without persisting to disk) before the client
    is constructed.

    :param pysui_config: Loaded pysui configuration.
    :type pysui_config: PysuiConfiguration
    :param group_name: Name of the group to activate, defaults to None
        (uses currently active group).
    :type group_name: Optional[str]
    :param protocol: Protocol to use when ``group_name`` is supplied.
        Must be ``GroupProtocol.GRAPHQL`` or ``GroupProtocol.GRPC``.
    :type protocol: Optional[GroupProtocol]
    :raises ValueError: If ``group_name`` is provided without ``protocol``.
    :raises NotImplementedError: If the resolved protocol is not GRAPHQL or GRPC.
    :return: An async client bound to the resolved group and protocol.
    :rtype: AsyncClientBase
    """
    if group_name is not None:
        if protocol is None:
            raise ValueError(
                "protocol is required when group_name is provided. "
                "Pass GroupProtocol.GRAPHQL or GroupProtocol.GRPC."
            )
        pysui_config.make_active(group_name=group_name, persist=False)
        resolved_protocol = protocol
    else:
        resolved_protocol = pysui_config.active_group.group_protocol

    if resolved_protocol == GroupProtocol.GRAPHQL:
        from pysui.sui.sui_pgql.pgql_clients import GqlProtocolClient

        return GqlProtocolClient(pysui_config=pysui_config)

    if resolved_protocol == GroupProtocol.GRPC:
        from pysui.sui.sui_grpc.pgrpc_clients import GrpcProtocolClient

        return GrpcProtocolClient(pysui_config=pysui_config)

    raise NotImplementedError(
        f"No client implementation for protocol '{resolved_protocol}'. "
        "Use GroupProtocol.GRAPHQL or GroupProtocol.GRPC."
    )
