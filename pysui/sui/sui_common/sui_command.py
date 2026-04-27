#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Protocol-neutral SuiCommand abstract base class."""

from abc import ABC, abstractmethod
from typing import ClassVar


class SuiCommand(ABC):
    """Protocol-neutral argument collector for Sui operations.

    Subclasses are dataclasses whose ``__init__`` accepts only the user-facing
    arguments for the operation. The two ``ClassVar`` fields (``gql_class``,
    ``grpc_class``) are static class-level protocol bindings invisible to the
    dataclass constructor.

    The concrete client calls exactly one of ``gql_node()`` or
    ``grpc_request()`` depending on its protocol. Commands that have no
    implementation for a given protocol raise ``NotImplementedError`` from
    that method — the client translates this into a
    ``SuiRpcResult(False, "Command not supported by <protocol>", None)``.
    """

    gql_class: ClassVar[type] = None
    grpc_class: ClassVar[type] = None
    gql_requires_paging: ClassVar[bool] = False

    @abstractmethod
    def gql_node(self) -> "PGQL_QueryNode":
        """Return a ready-to-execute GQL query node for this command."""

    @abstractmethod
    def grpc_request(self) -> "PGRPC_Request":
        """Return a ready-to-execute gRPC request for this command."""
