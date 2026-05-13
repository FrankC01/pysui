#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Shared result types used across GQL and gRPC protocol implementations."""

import dataclasses
import dataclasses_json


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class ObjectSummary:
    """Thin object reference: id, version, digest, and ownership metadata."""

    objectId: str
    version: str
    digest: str
    owner: str | None = None
    initialSharedVersion: str | None = None
