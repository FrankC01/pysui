#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Move Datatypes shell for BCS generation, DO NOT MODIFY."""

from typing import Any
import json
import canoser
import pysui.sui.sui_types.bcs_stnd as bcse


class _OptionalStub(canoser.RustOptional):
    """This is removed during generation."""

    def to_json(self, sort_keys=False, indent=4):
        amap = self.to_json_serializable()
        return json.dumps(amap, sort_keys=sort_keys, indent=indent)
