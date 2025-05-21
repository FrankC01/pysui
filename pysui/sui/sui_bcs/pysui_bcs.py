#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Pysui BCS Base abstraction supporting dataclass_json."""

import binascii
import dataclasses
from functools import partial
import json
from typing import Any, Optional

import canoser
import dataclasses_json


class BCS_Struct(canoser.Struct):
    pass

    @staticmethod
    def from_json(
        instance,
        json_in: str | bytes | bytearray,
    ):
        """Convert from json to Structure dataclass_json."""
        jres = json.loads(json_in)
        for key, value in jres.items():
            _ctype = BCS_BASE.classtype_from_name(instance.class_list, key)
            if not _ctype.list_depth:
                if _ctype.scalar:
                    pass
                else:
                    jres[key] = _ctype.bcs_class.from_json(json.dumps(value))
            else:
                if _ctype.scalar:
                    _vtype = type(value)
                    if _vtype != _ctype.bcs_class:
                        jres[key] = BCS_BASE.convert_to_list_type(_ctype, value, _vtype)
                else:
                    vdisp: list = []
                    for n in BCS_BASE.inner_list(value, _ctype.list_depth):
                        if n:
                            vdisp.append(_ctype.bcs_class.from_json(json.dumps(n)))
                        else:
                            vdisp.append(_ctype.bcs_class.from_json("null"))

                    jres[key] = BCS_BASE.wrap_list(vdisp, _ctype.list_depth)

        if isinstance(jres, dict):
            return instance.from_dict(jres)
        raise NotImplementedError(json_in)

    @classmethod
    def gen_dclass(cls, kvs: canoser.Struct, **kwargs):
        """Generate the dataclass_json analog of a BCS Structure type."""
        kvp_list: list[tuple[str, Any] | tuple[str, Any, Any]] = []
        type_class: list[_Classification] = []
        for enum_name, enum_value in kvs._fields:
            if enum_value == None:
                raise ValueError(f"Malformed field {enum_name}")
            else:
                typeclass: _Classification = BCS_BASE.classify(enum_name, enum_value)
                type_class.append(typeclass)
                kvp_list.append(
                    (enum_name, typeclass.dc_sig, dataclasses.field(default=None))
                )
        dc = dataclasses_json.dataclass_json(
            dataclasses.make_dataclass(kvs.__name__, kvp_list),
            undefined=dataclasses_json.Undefined.EXCLUDE,
        )
        dc.class_list = type_class
        dc.DCJ_JSON = dc.from_json
        dc.from_json = partial(cls.from_json, dc)
        return dc


class BCS_Enum(canoser.RustEnum):
    pass

    @staticmethod
    def from_json(
        instance,
        json_in: str | bytes | bytearray,
    ):
        """Convert from json to Enum dataclass_json."""

        jres = json.loads(json_in)
        if not isinstance(jres, dict) or isinstance(jres, list):
            _ctype = BCS_BASE.classtype_from_name(instance.class_list, jres)
            if not _ctype.bcs_class:
                jres = {jres: None}
        elif isinstance(jres, dict):
            key = next(iter(jres))
            _ctype = BCS_BASE.classtype_from_name(instance.class_list, key)
            if _ctype.scalar:
                pass
            else:
                value = jres[key]
                if not _ctype.list_depth:
                    jres[key] = _ctype.bcs_class.from_json(json.dumps(value))
                else:
                    if _ctype.scalar:
                        _vtype = type(value)
                        if _vtype != _ctype.bcs_class:
                            jres[key] = BCS_BASE.convert_to_list_type(
                                _ctype, value, _vtype
                            )
                    else:
                        vdisp = [
                            _ctype.bcs_class.from_json(json.dumps(n))
                            for n in BCS_BASE.inner_list(value, _ctype.list_depth)
                        ]
                        jres[key] = BCS_BASE.wrap_list(vdisp, _ctype.list_depth)
        elif isinstance(jres, list):
            raise NotImplementedError(f"Enum list handling {jres}")

        if isinstance(jres, dict):
            return instance.from_dict(jres)
        raise NotImplementedError(json_in)

    @classmethod
    def gen_dclass(cls, kvs: canoser.RustEnum, **kwargs):
        """Generate the dataclass_json analog of a BCS Enum type."""
        kvp_list: list[tuple[str, Any] | tuple[str, Any, Any]] = []
        type_class: list[_Classification] = []
        for enum_name, enum_value in kvs._enums:
            if enum_value == None:
                type_class.append(
                    _Classification(enum_name, Optional[Any], 0, False, None)
                )
                kvp_list.append(
                    (enum_name, Optional[Any], dataclasses.field(default=None))
                )
            else:
                typeclass: _Classification = BCS_BASE.classify(enum_name, enum_value)
                type_class.append(typeclass)
                kvp_list.append(
                    (
                        enum_name,
                        Optional[typeclass.dc_sig],
                        dataclasses.field(default=None),
                    )
                )
        dc = dataclasses_json.dataclass_json(
            dataclasses.make_dataclass(kvs.__name__, kvp_list),
            undefined=dataclasses_json.Undefined.EXCLUDE,
        )
        dc.class_list = type_class
        dc.DCJ_JSON = dc.from_json
        dc.from_json = partial(cls.from_json, dc)
        return dc


class BCS_Optional(canoser.RustOptional):

    pass

    @staticmethod
    def from_json(
        instance,
        json_in: str | bytes | bytearray,
    ):
        """Convert from json to Optional dataclass_json."""
        jres = json.loads(json_in)
        key = "value"
        value = jres
        jres = {}
        _ctype = BCS_BASE.classtype_from_name(instance.class_list, key)
        if not value or value and not isinstance(value, (dict, list)):
            jres[key] = value
        else:

            jres = {}
            if not _ctype.list_depth:
                if _ctype.scalar:
                    pass
                else:
                    jres[key] = _ctype.bcs_class.from_json(json.dumps(value))
            else:
                if _ctype.scalar:
                    _vtype = type(value)
                    if _vtype != _ctype.bcs_class:
                        jres[key] = BCS_BASE.convert_to_list_type(_ctype, value, _vtype)
                else:
                    vdisp: list = []
                    for n in BCS_BASE.inner_list(value, _ctype.list_depth):
                        if n:
                            vdisp.append(_ctype.bcs_class.from_json(json.dumps(n)))
                        else:
                            vdisp.append(_ctype.bcs_class.from_json("null"))

                jres[key] = BCS_BASE.wrap_list(vdisp, _ctype.list_depth)
        if isinstance(jres, dict):
            return instance.from_dict(jres)
        raise NotImplementedError(json_in)

    @classmethod
    def gen_dclass(cls, kvs: canoser.RustOptional, **kwargs):
        """Generate the dataclass_json analog of a BCS Optional type."""
        typeclass: _Classification = BCS_BASE.classify("value", kvs._type)
        kvp_list: list[tuple[str, Any] | tuple[str, Any, Any]] = [
            ("value", Optional[typeclass.dc_sig], dataclasses.field(default=None))
        ]

        dc = dataclasses_json.dataclass_json(
            dataclasses.make_dataclass(kvs.__name__, kvp_list),
            undefined=dataclasses_json.Undefined.EXCLUDE,
        )
        dc.class_list = [typeclass]
        dc.DCJ_JSON = dc.from_json
        dc.from_json = partial(cls.from_json, dc)
        return dc

    def to_json(self, sort_keys=False, indent=4):
        amap = self.to_json_serializable()
        return json.dumps(amap, sort_keys=sort_keys, indent=indent)


@dataclasses_json.dataclass_json
@dataclasses.dataclass
class _Classification:

    field_name: str
    dc_sig: Any
    list_depth: int
    scalar: bool
    scalar_type: Any
    bcs_class: Any


class BCS_BASE:
    """Base BCS Class."""

    @staticmethod
    def classtype_from_name(
        class_list: list[_Classification], name: str
    ) -> _Classification:
        """Fetch the _Classification from classified list."""
        for citem in class_list:
            if citem.field_name == name:
                return citem
        raise ValueError(f"{name} class type not found.")

    @staticmethod
    def inner_list(items: list, depth: int) -> list:
        """Retrieve the inner most list."""
        if items:
            if depth > 1:
                pass
            else:
                return items
        return items

    @staticmethod
    def wrap_list(items: list, depth: int) -> list:
        """Wrap the inner most list."""
        for _ in range(depth - 1):
            items = list(items)
        return items

    @staticmethod
    def convert_to_list_type(
        classtype: _Classification, in_value: Any, value_type: type
    ) -> Any:
        """Convert an inbound type value to expected kind as classified."""
        if value_type == str and classtype.scalar_type == int:
            return [int(n, base=16) for n in in_value]
        elif value_type == int and classtype.scalar_type == str:
            return "".join([hex(num)[2:] for num in in_value])
        raise NotImplementedError(
            f"{value_type} to {classtype.scalar_type} not supported yet."
        )

    @staticmethod
    def classify(in_name: str, in_arg: Any) -> Any:
        """Classify a property.."""
        ldepth = 0
        atype = in_arg

        while isinstance(atype, (list, canoser.ArrayT)):
            if isinstance(atype, canoser.ArrayT):
                atype = [atype.atype]
            else:
                atype = atype[0]
                ldepth += 1
        the_atype = atype.__name__
        iscalar = False
        iscalar_type = None
        match the_atype:
            case "str" | "StrT":
                iscalar = True
                iscalar_type = str
            case "int" | "float" | "bytes" | "bytearray" | "bool":
                iscalar = True
                iscalar_type = atype
            case "Uint8" | "Uint16" | "Uint32" | "Uint64" | "Uint128" | "Uint256":
                iscalar = True
                iscalar_type = int
            case _:
                if issubclass(atype, canoser.Struct):
                    atype = BCS_Struct.gen_dclass(atype)
                elif issubclass(atype, canoser.RustEnum):
                    atype = BCS_Enum.gen_dclass(atype)
                elif issubclass(atype, canoser.RustOptional):
                    atype = BCS_Optional.gen_dclass(atype)
                else:
                    raise NotImplementedError(f"{the_atype} not handled in classify")
        _class = _Classification(in_name, atype, ldepth, iscalar, iscalar_type, atype)
        for _ in range(ldepth):
            atype = list[atype]
        _class.dc_sig = atype
        return _class
