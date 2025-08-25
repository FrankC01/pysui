#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Abstract gRPC request."""

import abc
from dataclasses import Field
import enum
from inspect import getmembers
from types import GeneratorType
from typing import Callable, Optional

import betterproto2
from pysui.sui.sui_grpc.suimsgs.google.protobuf import FieldMask
import pysui.sui.sui_grpc.suimsgs.sui.rpc.v2beta2 as sui_prot
import pysui.sui.sui_grpc.suimsgs.google.protobuf as goog_prot


class Service(enum.IntEnum):
    LIVEDATA = 0
    LEDGER = 1
    TRANSACTION = 2
    MOVEPACKAGE = 3
    SUBSCRIPTION = 4
    SIGNATURE = 5
    NAMESERVICE = 6


class PGRPC_Request(abc.ABC):
    """Base request class."""

    _SCALAR: list[str] = ["int", "bool", "str", "bytes", "float"]
    _MODLIST = getmembers(sui_prot)
    _GOOGMODLIST = getmembers(goog_prot)
    _MODLIST += _GOOGMODLIST

    def __init__(self, service: Service):
        """Initializer."""
        self._service: Service = service

    @property
    def service(self) -> Service:
        """Return request service type."""
        return self._service

    @abc.abstractmethod
    def to_request(
        self,
        *,
        stub: betterproto2.ServiceStub,
        field_mask: Optional[list] = None,
    ) -> tuple[
        Callable[[betterproto2.Message], betterproto2.Message], betterproto2.Message
    ]:
        """Retrieve the function of the service and request object."""
        pass

    @staticmethod
    def _field_mask(field_mask: list[str]) -> FieldMask | None:
        """Convert list of strings to FieldMask"""
        if field_mask:
            return FieldMask(field_mask)
        else:
            return None

    @classmethod
    def result_fields(cls) -> dict:
        """Return the field dictionary defined in the result so as to support FieldMasks."""
        mb: MessageBuilder = MessageBuilder()
        return mb.build_result(cls.RESULT_TYPE)  # type: ignore


class Visited:
    _VISITED: dict[str, dict] = {}

    def __init__(self):
        if hit := list(filter(lambda e: e[0] == "Value", PGRPC_Request._MODLIST)):
            vdict = hit[0][1].__dataclass_fields__
            vnames: list[str] = []
            for vn in vdict.keys():
                vnames.append(vn)
            self.put("Value", {"of_types": vnames})

    @classmethod
    def register_enum(cls, enum_name: str, enum_cls: betterproto2.Enum) -> None:
        """Register the name,value dict of an enum type

        :param enum_cls: The Enum declaration
        :type enum_cls: betterproto2.Enum
        """
        if not cls.get(enum_name):
            defn: dict = {data.name: data.value for data in enum_cls}  # type: ignore
            # defn: dict = {
            #     name: member.value for name, member in enum_cls.__members__.items()
            # }
            sorted_by_values = dict(
                sorted(defn.items(), key=lambda item: item[1], reverse=False)
            )
            cls.put(enum_name, sorted_by_values)

    @classmethod
    def get(cls, type_name: str):
        return cls._VISITED.get(type_name)

    @classmethod
    def put(cls, type_name: str, defn: dict):
        cls._VISITED[type_name] = defn


class FieldFetch:

    def __init__(
        self,
        fname: str,
        tname: str,
        stack: list,
        message_class: Optional[betterproto2.Message] = None,
    ):
        self.field_name: str = fname
        self.type_name: str = tname
        self.message_class: betterproto2.Message | None = message_class
        self.stack = stack

    def resolve(self) -> tuple[str, dict | str]:
        """."""
        if not self.message_class:
            return self.field_name, self.type_name

        if vdict := Visited.get(self.type_name):
            return self.field_name, vdict

        fetch_list = MessageBuilder.evaluate(self.message_class)
        res_dict: dict[str, dict | str] = {}
        field: FieldFetch
        for field in fetch_list:
            key, value = field.resolve()
            res_dict[key] = value
        Visited.put(self.type_name, res_dict)

        return (self.field_name, res_dict)


class MessageBuilder:
    """."""

    def __init__(self):
        _ = Visited()

    def build_result(self, ptype: betterproto2.Message) -> dict:
        """."""
        main_plan: list[FieldFetch] = MessageBuilder.evaluate(ptype)
        res_dict: dict[str, dict | str] = {}
        field: FieldFetch
        for field in main_plan:
            key, value = field.resolve()
            res_dict[key] = value
        return res_dict

    @classmethod
    def evaluate(cls, ptype: betterproto2.Message) -> list[FieldFetch]:
        """."""

        field_dict: dict = ptype.__dataclass_fields__  # type: ignore
        cls_name = str(ptype).split(".")[-1].split("'")[0]

        result_list: list[FieldFetch] = []

        tname: str
        tvalue: Field
        for tname, tvalue in field_dict.items():
            ftypes: str = [f.strip() for f in tvalue.type.split("|")][0]
            if ftypes.count("."):
                ftypes = ftypes.split(".")[1]
            if ftypes in PGRPC_Request._SCALAR:
                result_list.append(FieldFetch(tname, ftypes, []))
            elif ftypes.startswith("list"):
                inner_type = ftypes[ftypes.index("[") + 1 : ftypes.index("]")]
                if inner_type in PGRPC_Request._SCALAR:
                    result_list.append(FieldFetch(tname, inner_type, []))
                else:
                    if inner_type == cls_name:
                        result_list.append(FieldFetch(tname, f"Self({cls_name})", []))
                    elif hit := list(
                        filter(lambda e: e[0] == inner_type, PGRPC_Request._MODLIST)
                    ):
                        if issubclass(hit[0][1], enum.Enum):
                            Visited.register_enum(inner_type, hit[0][1])  # type: ignore
                        result_list.append(FieldFetch(tname, inner_type, [], hit[0][1]))  # type: ignore
                    else:
                        raise ValueError(f"Unknown type {inner_type}")
            elif ftypes.startswith("dict"):
                result_list.append(FieldFetch(tname, ftypes, []))
            else:
                if hit := list(
                    filter(lambda e: e[0] == ftypes, PGRPC_Request._MODLIST)
                ):
                    if issubclass(hit[0][1], enum.Enum):
                        Visited.register_enum(ftypes, hit[0][1])  # type: ignore
                    result_list.append(FieldFetch(tname, ftypes, [], hit[0][1]))  # type: ignore
                else:
                    raise ValueError(f"Unknown type {ftypes}")
        return result_list
