#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

# dataclasses_json + dataclasses.dataclass decorator stacking confuses mypy's overload resolution for dataclass_json() — verified false positive, see Task #107 handoff (.claude/session-handoff-task107.md)
# mypy: disable-error-code="call-overload"

"""Shared result types used across GQL and gRPC protocol implementations."""

import dataclasses
import dataclasses_json

# Max object ids accepted by a single multiGetObjects (GQL) / BatchGetObjects (gRPC)
# request — confirmed 50 on both protocols (2026-09-12, GitHub #412). Enforced
# client-side so an oversized batch fails with a clear message instead of a bare
# TransportQueryError from the GQL service.
MAX_MULTI_OBJECT_FETCH: int = 50


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class ObjectSummary:
    """Thin object reference: id, version, digest, and ownership metadata."""

    objectId: str
    version: str
    digest: str
    owner: str | None = None
    initialSharedVersion: str | None = None


@dataclasses_json.dataclass_json
@dataclasses.dataclass
class ObjectSummaryList:
    """Container for a list of ObjectSummary results."""

    objects: list[ObjectSummary] = dataclasses.field(default_factory=list)
