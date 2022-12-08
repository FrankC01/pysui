#    Copyright 2022 Frank V. Castellucci
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#        http://www.apache.org/licenses/LICENSE-2.0
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

# -*- coding: utf-8 -*-

"""Sui RPC API Descriptor."""

from abc import ABC
import json
from dataclasses import dataclass
from dataclasses_json import dataclass_json, DataClassJsonMixin
from .sui_excepts import SuiApiDefinitionInvalid, SuiParamSchemaInvalid

# T = TypeVar("T", str, float, int, list)


class SuiJsonType(ABC):
    """Sui Json Type."""


@dataclass(frozen=True)
class SuiJsonNull(DataClassJsonMixin, SuiJsonType):
    """Sui Json Null Value."""

    type: str
    type_path: list[str]


@dataclass(frozen=True)
class SuiJsonValue(DataClassJsonMixin, SuiJsonType):
    """Sui Json Value."""

    type: str
    type_path: list[str]


@dataclass(frozen=True)
class SuiJsonString(DataClassJsonMixin, SuiJsonType):
    """Sui Json String."""

    type: str
    type_path: list[str]


@dataclass(frozen=True)
class SuiJsonBoolean(DataClassJsonMixin, SuiJsonType):
    """Sui Json Boolean."""

    type: bool
    type_path: list[str]


@dataclass(frozen=True)
class SuiJsonInteger(DataClassJsonMixin, SuiJsonType):
    """Sui Json Integer."""

    type: str
    type_path: list[str]
    format: str
    minimum: float


@dataclass(frozen=True)
class SuiJsonArray(DataClassJsonMixin, SuiJsonType):
    """Sui Json Array."""

    type: str
    type_path: list[str]
    items: SuiJsonType


# pylint: disable=invalid-name
@dataclass(frozen=True)
class SuiJsonTuple(DataClassJsonMixin, SuiJsonType):
    """Sui Json Tuple."""

    type: str
    type_path: list[str]
    items: SuiJsonType
    minItems: int = None
    maxItems: int = None


# pylint: enable=invalid-name
@dataclass(frozen=True)
class SuiJsonEnum(DataClassJsonMixin, SuiJsonType):
    """Sui Json Enum."""

    type: str
    type_path: list[str]
    enum: list[str]


@dataclass(frozen=True)
class SuiJsonObject(DataClassJsonMixin, SuiJsonType):
    """Sui Json Enum."""

    type: str
    type_path: list[str]


@dataclass_json
@dataclass
class SuiApiParam:
    """Sui API Parameter Data Class."""

    name: str
    schema: dict | SuiJsonType
    required: bool = False
    description: str = ""


@dataclass_json
@dataclass
class SuiApiResult:
    """Sui API Result Data Class."""

    name: str
    required: bool
    schema: dict | SuiJsonType


@dataclass(frozen=True)
class SuiApi(DataClassJsonMixin):
    """Sui API Data Class."""

    name: str
    params: list[SuiApiParam]
    result: SuiApiResult
    description: str = ""


def _resolve_param_type(schema_dict: dict, indata: dict, tpath: list) -> SuiJsonType:
    """Find the sui type base."""
    if "type" in indata:
        ptype = indata.get("type")
        tpath.append(ptype)
        dcp = indata.copy()
        dcp["type_path"] = tpath
        match ptype:
            case "string":
                if "enum" in dcp:
                    return SuiJsonEnum.from_dict(dcp)
                return SuiJsonString.from_dict(dcp)
            case "integer":
                return SuiJsonInteger.from_dict(dcp)
            case "enum":
                return SuiJsonEnum.from_dict(dcp)
            case "array":
                apath = []
                if isinstance(dcp["items"], dict):
                    dcp["items"] = _resolve_param_type(schema_dict, dcp.get("items"), apath)
                    return SuiJsonArray.from_dict(dcp)
                elif isinstance(dcp["items"], list):
                    dcp["type"] = "tuple"
                    vitems = []
                    for item in dcp["items"]:
                        ipath = []
                        vitems.append(_resolve_param_type(schema_dict, item, ipath))
                    dcp["items"] = vitems
                    dcp["type_path"] = ["tuple"]
                    return SuiJsonTuple.from_dict(dcp)
            case "object":
                return SuiJsonObject.from_dict(dcp)
            case "null":
                return SuiJsonNull.from_dict(dcp)
            case "boolean":
                return SuiJsonBoolean.from_dict(dcp)
            case _:
                raise NotImplementedError("ptype")
        return ptype
    if "$ref" in indata:
        last = indata.get("$ref").split("/")[-1]
        tpath.append(last)
        return _resolve_param_type(schema_dict, schema_dict.get(last), tpath)
    if "oneOf" in indata:
        head = indata.get("oneOf")[0]
        return _resolve_param_type(schema_dict, head, tpath)
    if "allOf" in indata:
        head = indata.get("allOf")[0]
        last = head["$ref"].split("/")[-1]
        tpath.append(last)
        return _resolve_param_type(schema_dict, schema_dict.get(last), tpath)

    if bool(indata) is False:
        dcp = indata.copy()
        dcp["type_path"] = tpath
        dcp["type"] = "SuiJsonValue"
        return SuiJsonValue.from_dict(dcp)

    raise SuiParamSchemaInvalid(indata)


def build_api_descriptors(indata: dict) -> tuple[str, dict, dict]:
    """Build the schema dictionary then API call dictionary."""
    # Validate the inbound data. Keys are present in valid response
    # from rpc.discover

    if (
        isinstance(indata["result"], dict)
        and "methods" in indata["result"]
        and "components" in indata["result"]
        and "schemas" in indata["result"]["components"]
    ):
        rpc_version = indata["result"]["info"]["version"]

        # Construct and write out the scheme denoted by version
        # fname = f"./apidefn{rpc_version}.json"
        # with open(fname, "w", encoding="utf8") as inner_file:
        #     inner_file.write(json.dumps(indata, indent=2))

        mdict: dict = {}
        schema_dict: dict = indata["result"]["components"]["schemas"]
        for rpc_api in indata["result"]["methods"]:
            mdict[rpc_api["name"]] = SuiApi.from_dict(rpc_api)
        for _api_name, api_def in mdict.items():
            for inparams in api_def.params:
                tpath: list = []
                inparams.schema = _resolve_param_type(schema_dict, inparams.schema, tpath)
            tpath: list = []
            api_def.result.schema = _resolve_param_type(schema_dict, api_def.result.schema, tpath)

        return (rpc_version, mdict, schema_dict)
    raise SuiApiDefinitionInvalid(indata)
