#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Move Datatypes for BCS deserialization."""

from typing import Any
import json
import pysui.sui.sui_bcs.bcs_stnd as bcse
import pysui.sui.sui_bcs.pysui_bcs as pbcsbase


class _OptionalStub(pbcsbase.BCS_Optional):
    """This is removed during generation."""

    def to_json(self, sort_keys=False, indent=4):
        """Serialize the optional value to a JSON string."""
        amap = self.to_json_serializable()
        return json.dumps(amap, sort_keys=sort_keys, indent=indent)
