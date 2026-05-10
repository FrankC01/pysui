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

from pysui.sui.sui_common.config import PysuiConfiguration
from pysui.abstracts.async_client import AsyncClientBase
from pysui.sui.sui_common.factory import client_factory
from pysui.sui.sui_common.sui_commands import GetMoveDataType as GetMoveDataTypeSC
from pysui.sui.sui_utils import hexstring_to_sui_id
import pysui.sui.sui_grpc.suimsgs.sui.rpc.v2 as sui_prot
import pysui.sui.sui_common.bcs_ast as bcs_ast
from pysui.sui.sui_common.bcs_ast import BcsAst
import pysui.sui.sui_common.mtobcs_types as mtypes
import pysui.sui.sui_bcs.bcs_stnd as bcse


def _normalize_fq_type(fq: str) -> str:
    """Pad the package address in a fully-qualified Move type to 32 bytes."""
    parts = fq.split("::")
    if len(parts) == 3:
        parts[0] = hexstring_to_sui_id(parts[0])
    return "::".join(parts)

_PROTO_SCALAR_BODY_TYPES: frozenset = frozenset({
    sui_prot.OpenSignatureBodyType.ADDRESS,
    sui_prot.OpenSignatureBodyType.BOOL,
    sui_prot.OpenSignatureBodyType.U8,
    sui_prot.OpenSignatureBodyType.U16,
    sui_prot.OpenSignatureBodyType.U32,
    sui_prot.OpenSignatureBodyType.U64,
    sui_prot.OpenSignatureBodyType.U128,
    sui_prot.OpenSignatureBodyType.U256,
})

_PROTO_SCALAR_REFS: dict = {
    sui_prot.OpenSignatureBodyType.U8: "bcse.U8",
    sui_prot.OpenSignatureBodyType.U16: "bcse.U16",
    sui_prot.OpenSignatureBodyType.U32: "bcse.U32",
    sui_prot.OpenSignatureBodyType.U64: "bcse.U64",
    sui_prot.OpenSignatureBodyType.U128: "bcse.U128",
    sui_prot.OpenSignatureBodyType.U256: "bcse.U256",
    sui_prot.OpenSignatureBodyType.ADDRESS: "bcse.Address",
    sui_prot.OpenSignatureBodyType.BOOL: "bool",
}

logger = logging.getLogger("mtobcs")


class MoveFieldNode(bcs_ast.Node):
    """Generic Structure Field node"""

    def __init__(self, ident: str, data: Any, children: Optional[list] = None):
        super().__init__(ident, data, children)


class MoveScalarField(MoveFieldNode):
    """Move scalar type field descriptor."""

    def __init__(self, ident: str, data: Any, children: Optional[list] = None):
        super().__init__(ident, data, children)


class MoveVectorField(MoveFieldNode):
    """Move vector type field descriptor."""

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
    """Move standard library type field descriptor."""

    def __init__(self, ident: str, data: Any, children: Optional[list] = None):
        super().__init__(ident, data, children)


class MoveStructureField(MoveFieldNode):
    """Move structure type field descriptor."""

    def __init__(self, ident: str, data: Any, children: Optional[list] = None):
        super().__init__(ident, data, children)


class MoveOptionalField(MoveFieldNode):
    """Move optional type field descriptor."""

    def __init__(
        self,
        *,
        ident,
        data,
        children=None,
    ):
        super().__init__(ident, data, children)


class MoveVariantField(MoveFieldNode):
    """Move enum variant field descriptor."""

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

    _FETCH_DECL: str = "fetch_declaration"
    _DECL_PARMS: str = "decl_paramtypes"
    _DECL_TYPE_NAME: str = "decl_type_name"

    def __init__(
        self,
        *,
        cfg: Optional[PysuiConfiguration] = None,
        client: Optional[AsyncClientBase] = None,
        target: mtypes.GenericStructure | mtypes.Structure,
    ):
        """Initialize"""
        if not cfg and not client:
            raise ValueError("One of cfg or client must be set")
        if client:
            self.client = client
        else:
            self.client: AsyncClientBase = client_factory(cfg)
        self.target = target
        self.python_stub = (
            Path(inspect.getfile(inspect.currentframe())).parent / "mtobcs_pre.py"
        )
        self.children: list[bcs_ast.Node] = []
        self._parsed: bool = False
        self._generated: Any = None
        self._compiled: Any = None

    def _handle_simple(self, fname: str, fval: Any) -> MoveFieldNode:
        """Convert scalars and simples. Accepts str (legacy root path) or OpenSignatureBody (proto path)."""
        if isinstance(fval, str):
            if sfield := bcse.MOVE_STD_SCALAR_REFS.get(fval):
                return MoveStandardField(fname, sfield)
            return MoveScalarField(fname, fval)
        # OpenSignatureBody scalar
        if ref := _PROTO_SCALAR_REFS.get(fval.type):
            return MoveStandardField(fname, ref)
        return MoveScalarField(fname, str(fval.type))

    def _type_param_name(self, body: sui_prot.OpenSignatureBody) -> str:
        """Extract short name from a concrete type param body for name mangling."""
        if body.type in _PROTO_SCALAR_BODY_TYPES:
            ref = _PROTO_SCALAR_REFS.get(body.type, str(body.type))
            return ref.split(".")[-1] if "." in ref else ref
        elif body.type == sui_prot.OpenSignatureBodyType.DATATYPE:
            return body.type_name.split("::")[-1]
        return str(body.type)

    def _build_parmed_assets(
        self, s_field: MoveFieldNode, fetch_decl: dict, parm_list: list
    ):
        """."""
        name_list = [fetch_decl[self._DECL_TYPE_NAME]]
        if len(fetch_decl[self._DECL_PARMS]) == len(parm_list):
            for tparm in parm_list:
                name_list.append(self._type_param_name(tparm))
            new_name = "_".join(name_list)
            fetch_decl[self._DECL_TYPE_NAME] = new_name
            fetch_decl[self._DECL_PARMS] = parm_list
            s_field.data = new_name

    def _resolve_vector_type_param(
        self, fname: str, idx: int, type_parms: Any
    ) -> tuple:
        """Resolve a TYPE_PARAMETER index to a concrete field when inside a vector."""
        if not (type_parms and isinstance(type_parms, list) and idx < len(type_parms)):
            raise NotImplementedError(f"Vector of TYPE_PARAMETER {idx} without type_parms for '{fname}'.")
        concrete = type_parms[idx]
        if concrete.type in _PROTO_SCALAR_BODY_TYPES:
            return self._handle_simple(fname, concrete), []
        if concrete.type == sui_prot.OpenSignatureBodyType.DATATYPE:
            return self._handle_reference(fname, concrete)
        raise NotImplementedError(f"Vector of concrete type {concrete.type} not handled for '{fname}'.")

    def _handle_vector(
        self, fname: str, fbody: sui_prot.OpenSignatureBody, type_parms: Any
    ) -> tuple[MoveFieldNode, list]:
        """Capture vector information."""
        depth_level: int = 0
        current = fbody
        voft = False
        while current.type == sui_prot.OpenSignatureBodyType.VECTOR:
            depth_level += 1
            current = current.type_parameter_instantiation[0]
        if current.type in _PROTO_SCALAR_BODY_TYPES:
            s_field = self._handle_simple(fname, current)
            s_fetch = []
        elif current.type == sui_prot.OpenSignatureBodyType.DATATYPE:
            voft = True
            s_field, s_fetch = self._handle_reference(fname, current)
            if s_fetch and type_parms:
                self._build_parmed_assets(s_field, s_fetch[0], type_parms)
        elif current.type == sui_prot.OpenSignatureBodyType.TYPE_PARAMETER:
            s_field, s_fetch = self._resolve_vector_type_param(fname, current.type_parameter, type_parms)
            if not isinstance(s_field, MoveScalarField):
                voft = True
        else:
            raise NotImplementedError(f"Vector of {current.type} not handled.")
        return (
            MoveVectorField(
                ident=fname,
                levels=depth_level,
                of_type=voft,
                base_data=s_field,
            ),
            s_fetch,
        )

    def _process_typeparm_fortype(self, fbody: sui_prot.OpenSignatureBody) -> list[dict]:
        """Return fetch entries for the first DATATYPE type param of an Optional."""
        tparms = fbody.type_parameter_instantiation
        if tparms and tparms[0].type == sui_prot.OpenSignatureBodyType.DATATYPE:
            fq = _normalize_fq_type(tparms[0].type_name)
            if fq in bcse.MOVE_STD_STRUCT_REFS:
                return []
            return [{self._FETCH_DECL: fq}]
        return []

    @staticmethod
    def _build_parm_names(type_parameter_instantiation) -> list[str]:
        """Build mangled name components from type parameter instantiation."""
        parm_names = []
        for tp in type_parameter_instantiation:
            if tp.type in _PROTO_SCALAR_BODY_TYPES:
                ref = _PROTO_SCALAR_REFS.get(tp.type, str(tp.type))
                parm_names.append(ref.split(".")[-1] if "." in ref else ref)
            elif tp.type == sui_prot.OpenSignatureBodyType.DATATYPE:
                parm_names.append(tp.type_name.split("::")[-1])
        return parm_names

    def _handle_reference(
        self,
        fname: str,
        fbody: sui_prot.OpenSignatureBody,
        type_info: Optional[dict] = None,
    ) -> tuple[MoveFieldNode, list[dict]]:
        """Resolve datatype references."""
        if fbody.type == sui_prot.OpenSignatureBodyType.TYPE_PARAMETER:
            return MoveScalarField(fname, fbody.type_parameter), []
        targ = _normalize_fq_type(fbody.type_name)
        f_field = None
        f_fetch: list[dict] = []
        if t_str := bcse.MOVE_STD_STRUCT_REFS.get(targ):
            f_field = MoveStructureField(fname, t_str)
        elif targ == bcse.MOVE_OPTIONAL_TYPE:
            f_fetch.extend(self._process_typeparm_fortype(fbody))
            f_field = MoveOptionalField(ident=fname, data=fbody)
        else:
            _, _, type_name = targ.split("::")
            parm_names = self._build_parm_names(fbody.type_parameter_instantiation)
            mangled = BcsAst.struct_field_type_proto(type_name, parm_names)
            f_field = MoveStructureField(fname, mangled)
            f_fetch.append(
                {
                    self._FETCH_DECL: targ,
                    self._DECL_PARMS: fbody.type_parameter_instantiation,
                    self._DECL_TYPE_NAME: mangled,
                }
            )
        return f_field, f_fetch

    def _dispatch_field(
        self,
        fname: str,
        fbody: sui_prot.OpenSignatureBody,
        type_parms: dict | None = None,
    ) -> tuple:
        """Dispatch a single field body to the appropriate handler."""
        if fbody.type in _PROTO_SCALAR_BODY_TYPES:
            return self._handle_simple(fname, fbody), []
        if fbody.type == sui_prot.OpenSignatureBodyType.DATATYPE:
            return self._handle_reference(fname, fbody)
        if fbody.type == sui_prot.OpenSignatureBodyType.VECTOR:
            vec_parms = type_parms.get(self._DECL_PARMS) if type_parms else None
            return self._handle_vector(fname, fbody, vec_parms)
        if fbody.type == sui_prot.OpenSignatureBodyType.TYPE_PARAMETER:
            idex = fbody.type_parameter
            if type_parms and (dparm := type_parms.get(self._DECL_PARMS)):
                if isinstance(dparm, list) and idex < len(dparm):
                    of_type = dparm[idex]
                    if of_type.type in _PROTO_SCALAR_BODY_TYPES:
                        return self._handle_simple(fname, of_type), []
                    return self._handle_reference(fname, of_type)
            logger.warning(f"TYPE_PARAMETER {idex} with no concrete params for field '{fname}'")
            return None, []
        logger.warning(f"Unhandled field type {fbody.type} for '{fname}'")
        return None, []

    def _process_structure(
        self,
        type_decl: str,
        struc_name: str,
        descriptor: sui_prot.DatatypeDescriptor,
        type_parms: dict | None = None,
    ) -> tuple[MoveStructureNode, list[dict]]:
        """."""
        if type_parms and type_parms.get(self._DECL_TYPE_NAME):
            struc_name = type_parms.get(self._DECL_TYPE_NAME)
        direct_fields: list[MoveFieldNode] = []
        fetch_fields: list[dict] = []

        for field in descriptor.fields:
            s_field, s_fetch = self._dispatch_field(field.name, field.type, type_parms)
            if s_field:
                direct_fields.append(s_field)
            if s_fetch:
                fetch_fields.extend(s_fetch)
        return MoveStructureNode(struc_name, direct_fields, type_decl), fetch_fields

    def _process_enum(
        self,
        type_decl: str,
        enum_name: str,
        descriptor: sui_prot.DatatypeDescriptor,
        type_parms: dict | None = None,
    ) -> tuple[MoveEnumNode, list]:
        """."""
        direct_variants: list[MoveVariantField] = []
        fetch_fields: list = []
        for variant in descriptor.variants:
            vname = variant.name
            variant_members: list = []
            for field in variant.fields:
                s_field, s_fetch = self._dispatch_field(field.name, field.type)
                if s_field:
                    variant_members.append(s_field)
                if s_fetch:
                    fetch_fields.extend(s_fetch)
            direct_variants.append(MoveVariantField(vname, variant_members))
        return MoveEnumNode(enum_name, direct_variants, type_decl), fetch_fields

    async def _fetch_type(
        self, *, client: AsyncClientBase, move_type_decl: dict
    ) -> tuple[bcs_ast.Node, list]:
        """Fetch a Move structure declaration and dependencies."""
        type_decl = move_type_decl[self._FETCH_DECL]
        addy, mod, type_name = type_decl.split("::")
        logger.info(f"Fetching '{type_decl}' definition")
        result = await client.execute(
            command=GetMoveDataTypeSC(package=addy, module_name=mod, type_name=type_name)
        )
        if result.is_ok():
            response: sui_prot.GetDatatypeResponse = result.result_data
            descriptor = response.datatype
            if descriptor.kind == sui_prot.DatatypeDescriptorDatatypeKind.STRUCT:
                return self._process_structure(type_decl, type_name, descriptor, move_type_decl)
            return self._process_enum(type_decl, type_name, descriptor, move_type_decl)
        else:
            raise ValueError(result.result_string)

    def _root_process(
        self, initial_target: mtypes.GenericStructure | mtypes.Structure
    ) -> tuple[str, list, MoveStructureNode | None]:
        """."""
        more_fetch = []
        children: list = []
        if isinstance(initial_target, mtypes.Structure):
            return initial_target.value_type, more_fetch, None
        dystruct: mtypes.GenericStructure = initial_target
        name_list: list = ["GenericStructure"]
        first_field = None
        for key, value in dystruct.properties.items():
            if bcse.MOVE_STD_SCALAR_REFS.get(value):
                name_list.append(value)
                children.append(self._handle_simple(key, value))
            else:
                _, _, ftype = value.split("::")
                name_list.append(ftype)
                children.append(self._handle_simple(key, ftype))
                if first_field:
                    more_fetch.append({self._FETCH_DECL: value})
                else:
                    first_field = value
        last_child = MoveStructureNode("_".join(name_list), children)
        return first_field, more_fetch, last_child

    async def _process_fetch_queue(self, more_fetch: list, handled: set) -> None:
        """Process the growing dependency queue, fetching each unresolved type."""
        def _growing_len(xs):
            i = 0
            while i < len(xs):
                yield xs[i]
                i += 1

        for x in _growing_len(more_fetch):
            decl = x[self._FETCH_DECL]
            decl_type_name = x.get(self._DECL_TYPE_NAME, decl)
            if decl_type_name.count(":"):
                decl_type_name = decl_type_name.split("::")[-1]
            if decl_type_name not in handled:
                type_node, _more_fetch = await self._fetch_type(
                    client=self.client, move_type_decl=x
                )
                self.children.insert(0, type_node)
                if decl_type_name == decl:
                    decl_type_name = type_node.ident
                handled.add(decl_type_name)
                if _more_fetch:
                    more_fetch.extend(_more_fetch)

    async def parse_move_target(self) -> str:
        """Parse the move target creating an IR and returning entry point classname.

        :return: Entry point class name
        :rtype: str
        """
        if not self._parsed:
            # Initialize with primary data type
            init_target, more_fetch, last_child = self._root_process(self.target)
            handled: set[str] = set()
            type_node, add_fetch = await self._fetch_type(
                client=self.client,
                move_type_decl={
                    self._FETCH_DECL: init_target,
                    self._DECL_PARMS: {},
                },  # type_decl=self.target
            )
            self.children.append(type_node)
            handled.add(type_node.ident)
            if add_fetch:
                more_fetch.extend(add_fetch)

            await self._process_fetch_queue(more_fetch, handled)

            if last_child:
                self.children.append(last_child)
            self._parsed = True
        return self.children[-1].ident

    async def compile_bcs(self, force: Optional[bool] = False) -> dict:
        """Compile the target and return executable ast."""
        if force:
            self._generated = False
            self._compiled = False
        if not self._compiled:
            if not self._generated:
                _ = await self.emit_bcs_source()

            self._compiled = {}
            comped_module = compile(
                ast.unparse(self._generated.ast_module), filename="blah", mode="exec"
            )
            exec(comped_module, self._compiled)
        return self._compiled

    async def emit_bcs_source(self) -> str:
        """Emit BCS python module."""
        if not self._generated:
            walker = _BCSGenerator(
                children=self.children,
                ast_module=ast.parse(self.python_stub.read_text(encoding="utf8")),
            )
            walker._walk()
            self._generated = walker

        return ast.unparse(self._generated.ast_module)


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
            self.put(
                ast.Tuple(
                    [ast.Constant(field.ident, str, lineno=0)], ast.Load, lineno=0
                )
            )
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

    def _resolve_optional_vector_field(self, opt_name: str, type_parm) -> ast.expr:
        """Resolve a vector type parameter inside an Optional field to an ast type expression."""
        depth_level = 0
        current = type_parm
        while current.type == sui_prot.OpenSignatureBodyType.VECTOR:
            depth_level += 1
            current = current.type_parameter_instantiation[0]
        if current.type in _PROTO_SCALAR_BODY_TYPES:
            inner_field = MoveScalarField(opt_name, _PROTO_SCALAR_REFS.get(current.type, str(current.type)))
        elif current.type == sui_prot.OpenSignatureBodyType.DATATYPE:
            fq_ref = current.type_name
            _, _, short_name = fq_ref.split("::")
            inner_field = MoveStructureField(opt_name, bcse.MOVE_STD_STRUCT_REFS.get(fq_ref, short_name))
        else:
            raise NotImplementedError(f"Option<vector<{current.type}>> not handled.")
        vec_node = MoveVectorField(ident=opt_name, levels=depth_level, base_data=inner_field)
        return BcsAst.generate_nested_vector(depth_level, self, vec_node)

    def visit_MoveOptionalField(self, node: MoveOptionalField):
        """Generate an unknown ref."""
        # From the immediate class, get the classname
        # class ClassName_optional_ident(canoser.RustOptional):
        #   _type = Any
        cdef: ast.ClassDef = self.first_from_top(ast.ClassDef)
        opt_name: str = f"{cdef.name}_optional_{node.ident}"
        logger.info(
            f"Generating '{opt_name}' optional type for '{cdef.name}' field '{node.ident}'"
        )
        # node.data is an OpenSignatureBody for the Option<T> field
        type_parm = node.data.type_parameter_instantiation[0]
        ast_type: ast.Name = ast.Name("Any", ast.Load())
        cdoc: str = None
        if type_parm.type in _PROTO_SCALAR_BODY_TYPES:
            ref = _PROTO_SCALAR_REFS.get(type_parm.type, str(type_parm.type))
            ast_type = ast.Name(ref, ast.Load())
        elif type_parm.type == sui_prot.OpenSignatureBodyType.DATATYPE:
            fq_ref = _normalize_fq_type(type_parm.type_name)
            _, _, short_name = fq_ref.split("::")
            if std_ref := bcse.MOVE_STD_STRUCT_REFS.get(fq_ref):
                ast_type = ast.Name(std_ref, ast.Load())
            else:
                if depedendent := self._needs_processing(cdef.name, fq_ref):
                    self.visit(depedendent)
                ast_type = ast.Name(short_name, ast.Load())
        elif type_parm.type == sui_prot.OpenSignatureBodyType.VECTOR:
            ast_type = self._resolve_optional_vector_field(opt_name, type_parm)
        elif type_parm.type == sui_prot.OpenSignatureBodyType.TYPE_PARAMETER:
            logger.warning(f"`{opt_name}` Optional class may require fixup.")
            cdoc = "_type Any MUST be replaced with concrete type."
        else:
            raise NotImplementedError(f"Unknown optional type {type_parm.type}")

        optdef: ast.ClassDef = BcsAst.optional_type(self, opt_name, ast_type, cdoc)
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
            iename = f"{cdef.name}_{node.ident}"
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
