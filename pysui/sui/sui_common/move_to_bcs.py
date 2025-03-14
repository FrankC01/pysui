#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Move to BCS module."""

import ast
from typing import Any, Optional, Union
from pysui import PysuiConfiguration, AsyncGqlClient
import pysui.sui.sui_pgql.pgql_query as qn
import pysui.sui.sui_pgql.pgql_types as qtype
import pysui.sui.sui_types.bcs_stnd as bcse


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


class MoveScalarField(MoveFieldNode):

    def __init__(self, ident: str, data: Any):
        super().__init__(ident, data)


class MoveVectorField(MoveFieldNode):

    def __init__(
        self,
        *,
        ident: str,
        levels: int,
        of_type: Optional[bool] = False,
        base_data: Optional[Any] = None,
    ):
        self.levels = levels
        self.vofclz = of_type

        super().__init__(ident, base_data)


class MoveStandardField(MoveFieldNode):

    def __init__(self, ident: str, data: Any):
        super().__init__(ident, data)


class MoveStructureField(MoveFieldNode):

    def __init__(self, ident: str, data: Any):
        super().__init__(ident, data)


class MoveVariantField(MoveFieldNode):

    def __init__(
        self,
        ident: str,
        variant_members: list[MoveFieldNode],
        data: Optional[Any] = None,
    ):
        self.variant_members: list[MoveFieldNode] = variant_members
        super().__init__(ident, data)


class MoveStructureNode(MoveNode):
    """Generic Structure node"""

    def __init__(
        self, ident: str, fields: list[MoveFieldNode], data: Optional[Any] = None
    ):
        self.fields: list[MoveFieldNode] = fields
        super().__init__(ident, data)


class MoveEnumNode(MoveNode):
    """Generic Enum node"""

    def __init__(
        self, ident: str, variants: list[MoveVariantField], data: Optional[Any] = None
    ):
        self.variants: list[MoveVariantField] = variants
        super().__init__(ident, data)


class MoveStructureTree:
    """Tree of Sui Move structures."""

    def __init__(self, *, cfg: PysuiConfiguration, target: str):
        """Initialize"""
        self.client: AsyncGqlClient = AsyncGqlClient(pysui_config=cfg)
        self.target: str = target
        self.children: list[MoveNode] = []

    def _handle_simple(self, fname: str, fval: str) -> MoveFieldNode:
        """Convert scalars and simples."""
        if sfield := bcse.MOVE_STD_SCALAR_REFS.get(fval):
            return MoveStandardField(fname, sfield)
        else:
            return MoveScalarField(fname, fval)

    def _handle_vector(
        self, fname: str, fval: Any
    ) -> tuple[MoveFieldNode, Union[str, None]]:
        """Capture vector information."""
        depth_level: int = 0
        i_val = fval
        voft = False
        while isinstance(i_val, dict):
            if i_val.get("vector"):
                depth_level += 1
                i_val = i_val["vector"]
            else:
                break
        # TODO: Proper resolution if inner information
        if isinstance(i_val, str):
            s_field = self._handle_simple(fname, i_val)
            s_fetch = None
        elif isinstance(i_val, dict) and i_val.get("datatype"):
            voft = True
            s_field, s_fetch = self._handle_reference(fname, i_val.get("datatype"))
        else:
            raise NotImplementedError(f"Vector of {i_val} not handled.")
        return (
            MoveVectorField(
                ident=fname,
                levels=depth_level,
                of_type=voft,
                base_data=s_field,
            ),
            s_fetch,
        )

    def _handle_reference(
        self, fname: str, fval: dict
    ) -> tuple[MoveFieldNode, Union[str, None]]:
        """Resolve datatype references."""
        targ = "::".join([fval["package"], fval["module"], fval["type"]])
        f_field = None
        f_fetch = None
        if t_str := bcse.MOVE_STD_STRUCT_REFS.get(targ):
            f_field = MoveStructureField(fname, t_str)
        else:
            f_field = MoveStructureField(fname, fval["type"])
            f_fetch = targ
        return f_field, f_fetch

    def _process_structure(
        self,
        type_decl: str,
        struc_name: str,
        mstrut: qtype.MoveStructureGQL,
    ) -> tuple[MoveStructureNode, list]:
        """."""
        direct_fields: list[MoveFieldNode] = []
        fetch_fields: list = []

        for field in mstrut.fields:
            fname = field["field_name"]
            fbody = field["field_type"]["signature"]["body"]
            if isinstance(fbody, str):
                direct_fields.append(self._handle_simple(fname, fbody))
            else:
                if fbody.get("datatype"):
                    s_field, s_fetch = self._handle_reference(fname, fbody["datatype"])
                    direct_fields.append(s_field)
                    if s_fetch:
                        fetch_fields.append(s_fetch)
                elif fbody.get("vector"):
                    s_field, s_fetch = self._handle_vector(fname, fbody)
                    direct_fields.append(s_field)
                    if s_fetch:
                        fetch_fields.append(s_fetch)
                else:
                    print(fbody)
        return MoveStructureNode(struc_name, direct_fields, type_decl), fetch_fields

    def _process_enum(
        self, type_decl: str, enum_name: str, menum: qtype.MoveEnumGQL
    ) -> tuple[MoveEnumNode, list]:
        """."""
        direct_variants: list[MoveVariantField] = []
        fetch_fields: list = []
        for variant in menum.variants:
            vname = variant.variant_name
            variant_members: list = []
            for field_member in variant.fields:
                fname = field_member["field_name"]
                fbody = field_member["field_type"]["signature"]["body"]
                if isinstance(fbody, str):
                    variant_members.append(self._handle_simple(fname, fbody))
                #     direct_fields
                else:
                    if fbody.get("datatype"):
                        s_field, s_fetch = self._handle_reference(
                            fname, fbody["datatype"]
                        )
                        variant_members.append(s_field)
                        if s_fetch:
                            fetch_fields.append(s_fetch)
                    elif fbody.get("vector"):
                        variant_members.append(self._handle_vector(fname, fbody))

            direct_variants.append(MoveVariantField(vname, variant_members))
        return MoveEnumNode(enum_name, direct_variants, type_decl), fetch_fields

    async def _fetch_type(
        self, *, client: AsyncGqlClient, type_decl: str
    ) -> tuple[MoveNode, list]:
        """Fetch a Move structure declaration and depedencies."""
        addy, mod, type_name = type_decl.split("::")
        result = await client.execute_query_node(
            with_node=qn.GetMoveDataType(
                package=addy, module_name=mod, data_type_name=type_name
            )
        )
        if result.is_ok():
            if isinstance(result.result_data, qtype.MoveStructureGQL):
                return self._process_structure(type_decl, type_name, result.result_data)
            return self._process_enum(type_decl, type_name, result.result_data)
        else:
            raise ValueError(result.result_string)

    async def build(self):
        """Build the tree by walking move data types."""
        # Initialize with primary data type
        handled: set[str] = set()
        type_node, more_fetch = await self._fetch_type(
            client=self.client, type_decl=self.target
        )
        self.children.append(type_node)
        handled.add(self.target)

        def _growing_len(xs):
            """Generator for potentially growing list of dependencies"""
            i = 0
            while i < len(xs):
                yield xs[i]
                i += 1

        # For each predecessor (growing list)
        for x in _growing_len(more_fetch):
            # Build predecessor data type
            if x not in handled:
                type_node, _more_fetch = await self._fetch_type(
                    client=self.client, type_decl=x
                )
                self.children.insert(0, type_node)
                handled.add(x)
                # Found more predecessors
                if _more_fetch:
                    more_fetch.extend(_more_fetch)

        return

    async def emit(self, base_ast: ast.Module):
        """Emit BCS module."""
