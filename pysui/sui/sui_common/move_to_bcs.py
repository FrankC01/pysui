#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Move to BCS module."""

from pysui import PysuiConfiguration, AsyncGqlClient


class MoveNode:
    """Generic Node."""

    def __init__(self, data):
        """Node Initializer."""
        self.data = data


class MoveFieldNode(MoveNode):
    """Generic Structure Field node"""

    def __init__(self, data):
        super().__init__(data)


class MoveStructureNode(MoveNode):
    """Generic Structure node"""

    def __init__(self, data):
        super().__init__(data)


class MoveStructureTree:
    """Tree of Sui Move structures."""

    def __init__(self, cfg, target: str):
        """Initialize"""
        self.client = AsyncGqlClient(pysui_config=cfg)
        self.target = target

    async def build(self):
        """Build the tree."""
        pass
