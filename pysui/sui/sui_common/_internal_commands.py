#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Internal SuiCommand subclasses — infrastructure-only, not part of the public API."""

from dataclasses import dataclass, field
from typing import ClassVar

from pysui.sui.sui_common.sui_command import SuiCommand
import pysui.sui.sui_grpc.pgrpc_requests as rn


@dataclass(kw_only=True)
class _FetchObjectsForResolution(SuiCommand):
    """Fetch objects and normalize to list[ObjectCacheEntry] for the executor resolver.

    Used internally by _BaseCachingExecutor._resolve_object_inputs. Not for external use.
    gRPC: delegates to _GetMultipleObjectsResolvedSC whose render() returns list[ObjectCacheEntry].
    GQL: delegates to _GetMultipleObjectsResolvedGQL whose encode_fn() returns list[ObjectCacheEntry].
    """

    grpc_class: ClassVar[type] = rn._GetMultipleObjectsResolvedSC
    gql_class: ClassVar[type] = None  # resolved lazily; see gql_node()

    object_ids: list[str] = field(default_factory=list)

    def gql_node(self):
        """Return GQL query node that normalizes the response to list[ObjectCacheEntry]."""
        from pysui.sui.sui_pgql.pgql_query import _GetMultipleObjectsResolvedSC
        return _GetMultipleObjectsResolvedSC(object_ids=self.object_ids)

    def grpc_request(self) -> rn._GetMultipleObjectsResolvedSC:
        """Return internal gRPC request that normalizes the response via render()."""
        return self.grpc_class(object_ids=self.object_ids)
