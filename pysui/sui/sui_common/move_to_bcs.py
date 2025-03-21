#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Move to BCS module."""

import ast
import inspect
from typing import Any, Optional, Union
from pathlib import Path
import uuid
import logging

from pysui import PysuiConfiguration, AsyncGqlClient
import pysui.sui.sui_common.bcs_ast as bcs_ast
from pysui.sui.sui_common.bcs_ast import BcsAst
import pysui.sui.sui_pgql.pgql_query as qn
import pysui.sui.sui_pgql.pgql_types as qtype
import pysui.sui.sui_types.bcs_stnd as bcse

logger = logging.getLogger("mtobcs")


class MoveFieldNode(bcs_ast.Node):
    """Generic Structure Field node"""

    def __init__(self, ident: str, data: Any, children: Optional[list] = None):
        super().__init__(ident, data, children)


class MoveScalarField(MoveFieldNode):

    def __init__(self, ident: str, data: Any, children: Optional[list] = None):
        super().__init__(ident, data, children)


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

    def __init__(self, ident: str, data: Any, children: Optional[list] = None):
        super().__init__(ident, data, children)


class MoveStructureField(MoveFieldNode):

    def __init__(self, ident: str, data: Any, children: Optional[list] = None):
        super().__init__(ident, data, children)


class MoveOptionalField(MoveFieldNode):

    def __init__(self, ident, data, children=None):
        super().__init__(ident, data, children)


class MoveVariantField(MoveFieldNode):

    def __init__(
        self,
        ident: str,
        children: list[MoveFieldNode],
        data: Optional[Any] = None,
    ):
        super().__init__(ident, data, children)


class MoveStructureNode(bcs_ast.Node):
    """Generic Structure node"""

    def __init__(
        self, ident: str, children: list[MoveFieldNode], data: Optional[Any] = None
    ):
        self.processed = False
        super().__init__(ident, data, children)


class MoveEnumNode(bcs_ast.Node):
    """Generic Enum node"""

    def __init__(
        self, ident: str, children: list[MoveVariantField], data: Optional[Any] = None
    ):
        self.processed = False
        super().__init__(ident, data, children)


class MoveDataType:
    """Tree of Sui Move structures."""

    def __init__(self, *, cfg: PysuiConfiguration, target: str):
        """Initialize"""
        self.client: AsyncGqlClient = AsyncGqlClient(pysui_config=cfg)
        self.target: str = target
        self.python_stub = (
            Path(inspect.getfile(inspect.currentframe())).parent / "mtobcs_pre.py"
        )
        self.children: list[bcs_ast.Node] = []

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
        # targ = "::".join([fval["package"], fval["module"], fval["type"]])
        targ = BcsAst.fully_qualified_reference(fval)
        f_field = None
        f_fetch = None
        if t_str := bcse.MOVE_STD_STRUCT_REFS.get(targ):
            f_field = MoveStructureField(fname, t_str)
        elif targ == bcse.MOVE_OPTIONAL_TYPE:
            f_field = MoveOptionalField(fname, fval)
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
    ) -> tuple[bcs_ast.Node, list]:
        """Fetch a Move structure declaration and depedencies."""
        addy, mod, type_name = type_decl.split("::")
        logger.info(f"Fetching '{type_decl}' definition")
        # print(f"Fetching: {type_decl}")
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

    async def emit(self, *, pre_includes: Optional[list[str]] = None) -> str:
        """Emit BCS python module."""
        walker = _BCSGenerator(
            children=self.children,
            ast_module=ast.parse(self.python_stub.read_text(encoding="utf8")),
        )
        walker._walk()

        return ast.unparse(walker.ast_module)


class _BCSGenerator(bcs_ast.NodeVisitor):
    """Generates the BCS associated with Move constructs."""

    def __init__(
        self,
        *,
        children: list,
        ast_module: ast.Module,
        pre_includes: Optional[list[str]] = None,
    ):
        super().__init__(ast_module)
        self.children: list = children
        self.pre_includes: list[str] = pre_includes or []
        for pre_i in self.pre_includes:
            pass

    def _needs_processing(
        self, current_cdef: str, depend_cdef: str
    ) -> Union[bcs_ast.Node, None]:
        """Check to see if node is yet to be processed."""
        base_index = -1
        depend_index = -1
        for idx, child in enumerate(self.children):
            if child.ident == current_cdef:
                base_index = idx
            elif child.ident == depend_cdef or child.data == depend_cdef:
                if not child.processed:
                    depend_index = idx
        return self.children[depend_index] if depend_index > base_index else None

    def _walk(self):
        """Walks the primary Move constructs."""
        for child in self.children:
            # If already processed, skip
            if child.processed:
                continue
            self.visit(child)

    def visit_MoveStructureNode(self, node: MoveStructureNode):
        """Generate a BCS structue class and it's fields."""
        field_targets: ast.List = ast.List([], ast.Load)
        logger.info(f"Generating '{node.ident}' structure type.")
        _ctxt = BcsAst.structure_base(
            node.ident, field_targets, f"Generated from {node.data}"
        )
        self.put(_ctxt)
        self.put(field_targets)
        for field in node.children:
            self.put(ast.Tuple([ast.Constant(field.ident, str)], ast.Load))
            self.visit(field)
            field_targets.elts.append(self.get())
        # Pop fields
        _ = self.get()
        # Pop class def
        _ = self.get()
        self.ast_module.body.append(_ctxt)
        node.processed = True

    def visit_MoveEnumNode(self, node: MoveEnumNode):
        """Generate a BCS enum class and it's variants."""
        field_targets: ast.List = ast.List([], ast.Load)
        logger.info(f"Generating '{node.ident}' enum type.")
        _ctxt = BcsAst.enum_base(
            node.ident, field_targets, f"Generated from {node.data}"
        )
        self.put(_ctxt)
        self.put(field_targets)

        for field in node.children:
            self.visit(field)
        # Pop fields
        _ = self.get()
        # Pop class def
        _ = self.get()
        self.ast_module.body.append(_ctxt)
        node.processed = True

    def visit_MoveScalarField(self, node: MoveScalarField):
        """Generate a reference to a scalar type."""
        expr = ast.parse(f"{node.data}").body[0].value
        container = self.peek_first()
        container.elts.append(expr)

    def visit_MoveStandardField(self, node: MoveStandardField):
        """Generate a reference to a scalar type."""
        expr = ast.parse(f"{node.data}").body[0].value
        container = self.peek_first()
        container.elts.append(expr)

    def visit_MoveStructureField(self, node: MoveStructureField):
        """Generate a reference to a struct type."""
        current_cdef = self.first_from_top(ast.ClassDef).name
        # Check if the structure, as a depedency, has already been processed
        # If not, generate it first
        if depedendent := self._needs_processing(current_cdef, node.data):
            self.visit(depedendent)
        # Resume
        expr = ast.parse(f"{node.data}").body[0].value
        container = self.peek_first()
        container.elts.append(expr)

    def visit_MoveOptionalField(self, node: MoveOptionalField):
        """Generate an unknown ref."""
        # From the immediate class, get the classname
        # class ClassName_optional_ident(canoser.RustOptional):
        #   _type = Any
        # Resolve any typeParameters in node.data
        cdef: ast.ClassDef = self.first_from_top(ast.ClassDef)
        opt_name: str = f"{cdef.name}_optional_{node.ident}"
        logger.info(
            f"Generating '{opt_name}' optional type for '{cdef.name}' field '{node.ident}'"
        )
        type_parm = node.data["typeParameters"][0]
        ast_type: ast.Name = ast.Name("Any", ast.Load())
        cdoc: str = None
        # A straight up scalar type?
        if isinstance(type_parm, str):
            ast_type = ast.Name(
                bcse.MOVE_STD_SCALAR_REFS.get(type_parm, type_parm), ast.Load()
            )
        # A reference to another structure - Use structure 'type' name as type
        elif (
            isinstance(type_parm, dict)
            and type_parm.get("datatype")
            and type_parm["datatype"].get("package")
        ):
            type_parm = type_parm["datatype"]
            fq_ref = BcsAst.fully_qualified_reference(type_parm)
            # Process dependent if found
            if depedendent := self._needs_processing(cdef.name, fq_ref):
                self.visit(depedendent)
            ast_type = ast.Name(type_parm["type"], ast.Load())
        # A unknown generic reference - Use Any as type
        elif isinstance(type_parm, dict) and next(iter(type_parm)) == "typeParameter":
            logger.warning(f"`{opt_name}` Optional class may require fixup.")
            cdoc = "_type Any MUST be replaced with concrete type."
            pass
        else:
            raise NotImplementedError(f"Unknown optional type {type_parm}")

        optdef: ast.ClassDef = BcsAst.optional_type(self, opt_name, ast_type, cdoc)
        # optdef: ast.Classdef = BcsAst.optional_base(opt_name, ast_type)
        self.ast_module.body.append(optdef)
        expr = ast.parse(opt_name).body[0].value
        container = self.peek_first()
        container.elts.append(expr)

    def visit_MoveVectorField(self, node: MoveVectorField):
        """Generate a vector of n depth."""
        self.peek_first().elts.append(
            BcsAst.generate_nested_vector(node.levels, self, node)
        )

    def visit_MoveVariantField(self, node: MoveVariantField):
        """Generate the variant field of an enum class."""
        cname = ast.Constant(node.ident, str)
        tuple_ast = ast.Tuple([cname], ast.Load)
        self.put(tuple_ast)
        # If there is more than one field we lift a new enum
        if len(node.children) > 1:
            cdef = self.first_from_top(ast.ClassDef)
            iename = f"{cdef.name}_{uuid.uuid4().hex}"
            field_targets: ast.List = ast.List([], ast.Load)
            _ctxt = BcsAst.enum_base(iename, field_targets)

            self.put(field_targets)
            for field in node.children:
                mvar = MoveVariantField(field.ident, [field])
                self.visit(mvar)
            _ = self.get()
            self.ast_module.body.append(_ctxt)
            expr: ast.Expr = ast.parse(iename).body[0]
            tuple_ast.elts.append(expr.value)

        else:
            self.visit(node.children[0])
        # Pop the variant tuple
        _ = self.get()
        self.peek_first().elts.append(tuple_ast)
