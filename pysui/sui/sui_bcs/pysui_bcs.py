#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Pysui BCS Base abstraction supporting dataclass_json."""

import json
import canoser


class BCS_Struct(canoser.Struct):
    pass


class BCS_Enum(canoser.RustEnum):
    pass


class BCS_Optional(canoser.RustOptional):

    def to_json(self, sort_keys=False, indent=4):
        amap = self.to_json_serializable()
        return json.dumps(amap, sort_keys=sort_keys, indent=indent)
