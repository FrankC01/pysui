#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Pysui BCS Base abstraction supporting dataclass_json."""

import json
from dataclasses import make_dataclass, dataclass
from enum import IntEnum
from functools import singledispatchmethod
from types import SimpleNamespace
from typing import Any, Optional, Union

from dataclasses_json import dataclass_json

# import canoser.array_t
import canoser

# import canoser.str_t
# import canoser.bool_t
# import canoser.bytes_t
# import canoser.int_type


# BCS_Struct = canoser.Struct
BCS_Enum = canoser.RustEnum


class BCS_Struct(canoser.Struct):
    pass


class BCS_Optional(canoser.RustOptional):

    def to_json(self, sort_keys=False, indent=4):
        amap = self.to_json_serializable()
        return json.dumps(amap, sort_keys=sort_keys, indent=indent)


class _ClassType(IntEnum):
    BCS_CLASS_BASED = 0
    BCS_OPTION_BASED = 1
    BCS_ENUM_BASED = 2
    BCS_ARRAYT_BASED = 3
    BCS_OTHER_BASED = 4


@dataclass
class _Classified:
    _ctype: _ClassType
    _ftype: Any
    _clistdepth: int


class _DeclarationNameSpace:
    def __init__(self):
        self.namespace = SimpleNamespace(name="example")

    def get_declaration(self, name: str) -> Any:
        """Get a declaration from namespace by name."""
        return getattr(self.namespace, name, False)

    def add_declaration(self, name: str, decls: list[tuple[str, Any]]) -> Any:
        """Add a dataclass_json to the namespace."""
        if not self.get_declaration(name):
            setattr(self.namespace, name, dataclass_json(make_dataclass(name, decls)))
        return self.get_declaration(name)


class BCS_DC_BASE:
    _DATA_CLASS_ID: str = "bcstodc"
    _MODULE: _DeclarationNameSpace = None

    @classmethod
    def _initialize_ns(cls):
        cls._MODULE = _DeclarationNameSpace()

    @singledispatchmethod
    @classmethod
    def to_dataclass(cls, arg: Any, arb: bool = False) -> Any:
        """Default handler."""
        if issubclass(arg, canoser.int_type.IntType):
            return int
        elif issubclass(arg, canoser.bool_t.BoolT):
            return bool
        elif issubclass(arg, canoser.bytes_t.BytesT):
            return bytes
        elif issubclass(arg, canoser.str_t.StrT):
            return str
        elif arg is str:
            return str
        raise NotImplementedError(arg)

    @to_dataclass.register
    @classmethod
    def _(cls, arg: canoser.array_t.ArrayT, arb: bool = False) -> Any:
        """Arrays are list[of_type]."""
        return list[cls.to_dataclass(arg.atype)]

    @staticmethod
    def classify_type(ftype) -> _Classified:
        """Determine disposition of type."""
        # If list, get contained type
        list_depth = 0
        while isinstance(ftype, list):
            ftype = ftype[0]
            list_depth += 1

        # Determine if enabled type or other
        try:
            # Struct
            if hasattr(ftype, "_fields"):
                return _Classified(_ClassType.BCS_CLASS_BASED, ftype, list_depth)
            # Option
            elif hasattr(ftype, "_type"):
                return _Classified(_ClassType.BCS_OPTION_BASED, ftype, list_depth)
            # Enum
            elif hasattr(ftype, "_enums"):
                return _Classified(_ClassType.BCS_ENUM_BASED, ftype, list_depth)
            # ArrayT type
            elif (
                hasattr(ftype, "atype")
                and hasattr(ftype, "fixed_len")
                and hasattr(ftype, "encode_len")
            ):
                attype_depth = 1 if not list_depth else list_depth + 1
                while isinstance(ftype.atype, canoser.array_t.ArrayT):
                    attype_depth += 1
                    ftype = ftype.atype
                attype_base: _Classified = BCS_DC_BASE.classify_type(ftype.atype)
                attype_base._clistdepth = attype_depth
                return attype_base
            else:
                return _Classified(_ClassType.BCS_OTHER_BASED, ftype, list_depth)
        except Exception:
            return _Classified(_ClassType.BCS_OTHER_BASED, ftype, list_depth)

    @staticmethod
    def _get_struct_decl(
        struct_name: str,
        struct_def: canoser.Struct,
    ) -> tuple[str, list[tuple[str, Any]]]:
        """."""
        idecl_list: list[tuple[str, Any]] = []
        for fname, field in struct_def._fields:
            pass

    @staticmethod
    def _get_option_decl(
        option_name: str,
        option_def: canoser.RustOptional,
    ) -> tuple[str, list[tuple[str, Any]]]:
        """."""
        idecl_list: list[tuple[str, Any]] = []
        classified = BCS_DC_BASE.classify_type(option_def._type)
        if classified._ctype == _ClassType.BCS_OTHER_BASED:
            base_decl = BCS_DC_BASE.to_dataclass(classified._ftype)
            if classified._clistdepth:
                _, base_decl = BCS_DC_BASE._get_list_decl(
                    option_name, base_decl, classified._clistdepth
                )
            return option_name, Optional[base_decl]

    @staticmethod
    def _get_emum_decl(
        enum_name: str, enum_def: canoser.RustEnum, enum_val_dict: dict = None
    ) -> tuple[str, list[tuple[str, Any]]]:
        """."""
        # dc_name: str = type(enum_def).__name__
        dc_name = enum_name
        idecl_list: list[tuple[str, Any]] = []

        for pname, ptype in enum_def._enums:
            gen_name = dc_name + "_" + pname
            if ptype == None:
                idecl_list.append(
                    BCS_DC_BASE._MODULE.add_declaration(
                        gen_name, [(pname, Optional[Any])]
                    )
                )
            else:
                classified = BCS_DC_BASE.classify_type(ptype)
                if classified._ctype == _ClassType.BCS_OTHER_BASED:
                    pass
                else:
                    inner_val = (
                        ptype
                        if not classified._clistdepth
                        else BCS_DC_BASE._get_list_value(ptype)
                    )
                    cname = str(inner_val)[:-2].rsplit(".", 1)[-1]
                    if classified._ctype == _ClassType.BCS_CLASS_BASED:
                        idecl = BCS_DC_BASE._get_struct_decl(cname, inner_val)
                        idecl_list.append()
                    elif classified._ctype == _ClassType.BCS_OPTION_BASED:
                        _, idecl = BCS_DC_BASE._get_option_decl(cname, inner_val)
                        if classified._clistdepth:
                            _, idecl = BCS_DC_BASE._get_list_decl(
                                "", idecl, classified._clistdepth
                            )
                        idecl_list.append(idecl)
                    elif classified._ctype == _ClassType.BCS_ENUM_BASED:
                        _, idecl = BCS_DC_BASE._get_emum_decl(cname, inner_val)
                        print()

        decl_list = [("enums", Union[tuple(idecl_list)])]

        return dc_name, decl_list

    @staticmethod
    def _get_list_decl(fname, ctype: Any, list_depth: int) -> tuple[str, Any]:
        """Prepare list 'types' for dataclass property."""
        type_info = list[ctype]
        list_depth -= 1
        for _ in range(list_depth):
            type_info = list[type_info]
        return fname, type_info

    @staticmethod
    def _get_list_value(list_container) -> Any:
        """Retreive the inner most list type instance."""
        current = list_container
        while isinstance(current, list):
            current = current[0]
        return current

    @staticmethod
    def _get_property_value_decl(
        type_ref: _Classified, prop_name: str, prop_val, dec_fn
    ):
        """."""
        if isinstance(prop_val, list) and prop_val:
            inner_fetch = BCS_DC_BASE._dispatch(
                type_ref._ctype, BCS_DC_BASE._get_list_value(prop_val), True
            )
            _, decl = BCS_DC_BASE._get_list_decl(
                prop_name, inner_fetch, type_ref._clistdepth
            )
            if dec_fn:
                decl = dec_fn(decl)
        else:
            decl = BCS_DC_BASE._dispatch(type_ref._ctype, prop_val, True)

        return decl

    @staticmethod
    def _struct_spec(arg: BCS_Struct, nested: Optional[bool] = False) -> Any:
        """Process a BCS Structure type."""
        dc_name: str = type(arg).__name__
        print(f"Processing {dc_name}")
        dc_spec: list[tuple[str, Any]] = []
        tss = arg.to_json_serializable()
        for fname, ftype in arg._fields:
            classified = BCS_DC_BASE.classify_type(ftype)
            match classified._ctype:
                case (
                    _ClassType.BCS_CLASS_BASED
                    | _ClassType.BCS_ENUM_BASED
                    | _ClassType.BCS_OPTION_BASED
                ):
                    represents = getattr(arg, fname)
                    decl = BCS_DC_BASE._get_property_value_decl(
                        classified, fname, represents, None
                    )
                    dc_spec.append((fname, decl))
                case _ClassType.BCS_OTHER_BASED:
                    tss[fname] = getattr(arg, fname)
                    base_type = BCS_DC_BASE.to_dataclass(classified._ftype)
                    if classified._clistdepth:
                        dc_spec.append(
                            BCS_DC_BASE._get_list_decl(
                                fname, base_type, classified._clistdepth
                            )
                        )
                    else:
                        dc_spec.append((fname, base_type))
                case _:
                    raise ValueError("_struct_spec Unknown class type")
        if nested:
            return BCS_DC_BASE._MODULE.add_declaration(dc_name, dc_spec)
        else:
            decl = BCS_DC_BASE._MODULE.add_declaration(dc_name, dc_spec)
            return decl.from_dict(tss)

    @staticmethod
    def _optional_spec(arg: BCS_Optional, nested: Optional[bool] = False) -> Any:
        """Process a BCS Optional type."""
        dc_name: str = type(arg).__name__
        dc_spec: list[tuple[str, Any]] = []
        tss = arg.to_json_serializable()
        classified = BCS_DC_BASE.classify_type(arg.value_type)
        _ofclass = None
        match classified._ctype:
            case _ClassType.BCS_CLASS_BASED | _ClassType.BCS_OPTION_BASED:
                represents = arg.value
                _ofclass = BCS_DC_BASE._get_property_value_decl(
                    classified, "value", represents, lambda x: Optional[x]
                )
                dc_spec.append(("value", _ofclass))

            case _ClassType.BCS_ENUM_BASED:
                represents = arg.value
                _ofclass = BCS_DC_BASE._get_property_value_decl(
                    classified, "value", represents, lambda x: Optional[x]
                )
                dc_spec.append(("value", _ofclass))
            case _ClassType.BCS_OTHER_BASED:
                _ofclass = Optional[classified._ftype]
                dc_spec.append(("value", BCS_DC_BASE.to_dataclass(classified._ftype)))
        if nested:
            return _ofclass
        else:
            tss = {"value": tss}
            decl = BCS_DC_BASE._MODULE.add_declaration(dc_name, dc_spec)
            return decl.from_dict(tss)

    @staticmethod
    def _enum_spec(arg: BCS_Enum, nested: Optional[bool] = False) -> Any:
        """Process a BCS Enum type."""
        enum_name = arg.__class__.__name__
        tss = arg.to_json_serializable()
        nname, decls = BCS_DC_BASE._get_emum_decl(enum_name, arg, tss)
        dc_name: str = type(arg).__name__
        dc_spec: list[tuple[str, Any]] = []

        classified = BCS_DC_BASE.classify_type(arg.value_type)
        match classified._ctype:
            case (
                _ClassType.BCS_CLASS_BASED
                | _ClassType.BCS_OPTION_BASED
                | _ClassType.BCS_ENUM_BASED
            ):
                represents = arg.value
                _ofclass = BCS_DC_BASE._get_property_value_decl(
                    classified, arg.enum_name, represents, None
                )
                dc_spec.append((arg.enum_name, _ofclass))
            case _ClassType.BCS_OTHER_BASED:
                if not arg.value_type:
                    _ofclass = Optional[Any]
                    dc_spec.append((arg.enum_name, _ofclass))
                    tss = {arg.enum_name, None}
                else:
                    _ofclass = arg.value_type
                    dc_spec.append(
                        ("value", BCS_DC_BASE.to_dataclass(classified._ftype))
                    )
        if nested:
            return BCS_DC_BASE._MODULE.add_declaration(dc_name, dc_spec)
        else:
            decl = BCS_DC_BASE._MODULE.add_declaration(dc_name, dc_spec)
            return decl.from_dict(tss)

    @staticmethod
    def _dispatch(ctype: _ClassType, instance: Any, nested: bool = False):
        """Dispatch on BCS ClassType."""
        match ctype:
            case _ClassType.BCS_CLASS_BASED:
                return BCS_DC_BASE._struct_spec(instance, nested)
            case _ClassType.BCS_OPTION_BASED:
                return BCS_DC_BASE._optional_spec(instance, nested)
            case _ClassType.BCS_ENUM_BASED:
                return BCS_DC_BASE._enum_spec(instance, nested)

    @classmethod
    def bcstodc(cls, self_obj: "BCS_DC_BASE", nested: bool = False) -> any:
        """Converts BCS object to python 'dataclass_json."""
        _classified = cls.classify_type(self_obj)
        if not nested:
            cls._initialize_ns()
            res = cls._dispatch(_classified._ctype, _classified._ftype)
        if nested:
            return cls._dispatch(_classified._ctype, _classified._ftype)
        else:
            return res
