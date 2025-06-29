#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Abstract gRPC request."""

import abc
from dataclasses import Field
import enum
from inspect import getmembers
from typing import Callable, Optional

import betterproto2
from pysui.sui.sui_grpc.suimsgs.google.protobuf import FieldMask
import pysui.sui.sui_grpc.suimsgs.sui.rpc.v2beta2 as sui_prot
import pysui.version

CURRENT_VERSION = [int(x) for x in pysui.version.__version__.split(".")]


class Service(enum.IntEnum):
    LIVEDATA = 0
    LEDGER = 1
    TRANSACTION = 2
    MOVEPACKAGE = 3
    SUBSCRIPTION = 4
    SIGNATURE = 5


class PGRPC_Request(abc.ABC):
    """Base request class."""

    _SCALAR: list[str] = ["int", "bool", "str", "bytes"]
    _MODLIST = getmembers(sui_prot)

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
    def _field_mask(field_mask: list[str]) -> FieldMask:
        """Convert list of strings to FieldMask"""
        if field_mask:
            return FieldMask(field_mask)
        else:
            return None

    @staticmethod
    def _data_walker(field_dict: dict) -> dict:
        """Walk the response data field dictionary."""

        def handle_nest(fname: str, ftype: str):
            """Handle new dataclass loookup."""
            hit = list(filter(lambda e: e[0] == ftype, PGRPC_Request._MODLIST))
            if hit:
                if issubclass(hit[0][1], enum.Enum):
                    return fname, "ENUM"
                else:
                    return fname, {
                        hit[0][0]: PGRPC_Request._data_walker(
                            hit[0][1].__dataclass_fields__
                        ),
                    }
            return fname, "None"

        tname: str
        tvalue: Field
        res_dict: dict = {}
        for tname, tvalue in field_dict.items():
            ftypes = [f.strip() for f in tvalue.type.split("|")][0]
            if ftypes in PGRPC_Request._SCALAR:
                res_dict[tname] = ftypes
            elif ftypes.startswith("list"):
                inner_type = ftypes[ftypes.index("[") + 1 : ftypes.index("]")]
                if ftypes in PGRPC_Request._SCALAR:
                    res_dict[tname] = inner_type
                else:
                    fkey, fvalue = handle_nest(tname, inner_type)
                    res_dict[fkey] = fvalue
            else:
                fkey, fvalue = handle_nest(tname, ftypes)
                res_dict[fkey] = fvalue
        return res_dict

    @classmethod
    def result_fields(cls) -> dict:
        """Return the field dictionary defined in the result so as to support FieldMasks."""
        return cls._data_walker(cls.RESULT_TYPE.__dataclass_fields__)
