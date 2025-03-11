#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Move to BCS module."""

import ast
from typing import Any
from pysui import PysuiConfiguration, AsyncGqlClient
import pysui.sui.sui_pgql.pgql_query as qn
import pysui.sui.sui_pgql.pgql_types as qtype
import pysui.sui.sui_types.bcs_stnd as bcse


async def _fetch_structure(
    *, client: AsyncGqlClient, struct_decl: str
) -> qtype.MoveStructureGQL:
    """Fetch a Move structure declaration and depedencies."""
    addy, mod, struc = struct_decl.split("::")
    result = await client.execute_query_node(
        with_node=qn.GetStructure(package=addy, module_name=mod, structure_name=struc)
    )
    if result.is_ok():
        return result.result_data
    else:
        raise ValueError(result.result_string)


class MoveNode:
    """Generic Node."""

    def __init__(self, ident: str, data: Any):
        """Node Initializer."""
        self.ident: str = ident
        self.data: Any = data


class MoveFieldNode(MoveNode):
    """Generic Structure Field node"""

    def __init__(self, ident: str, data: Any):
        super().__init__(ident, data)


class MoveStandardField(MoveFieldNode):

    def __init__(self, ident: str, data: Any):
        super().__init__(ident, data)


class MoveStructureField(MoveFieldNode):

    def __init__(self, ident: str, data: Any):
        super().__init__(ident, data)


class MoveStructureNode(MoveNode):
    """Generic Structure node"""

    def __init__(self, ident: str, data: Any):
        super().__init__(ident, data)


class MoveStructureTree:
    """Tree of Sui Move structures."""

    def __init__(self, *, cfg: PysuiConfiguration, target: str):
        """Initialize"""
        self.client: AsyncGqlClient = AsyncGqlClient(pysui_config=cfg)
        self.target: str = target
        self.dependencies: list[str] = []
        self.children: list[MoveStructureNode] = []

    async def build(self):
        """Build the tree."""
        targ = await _fetch_structure(client=self.client, struct_decl=self.target)
        print()
