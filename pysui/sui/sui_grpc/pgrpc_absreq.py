#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Abstract gRPC request."""

import abc
from enum import IntEnum
from typing import Callable, Optional

import betterproto2
from pysui.sui.sui_grpc.suimsgs.google.protobuf import FieldMask
import pysui.version

CURRENT_VERSION = [int(x) for x in pysui.version.__version__.split(".")]


class Service(IntEnum):
    LIVEDATA = 0
    LEDGER = 1
    TRANSACTION = 2
    MOVEPACKAGE = 3
    SUBSCRIPTION = 4
    SIGNATURE = 5


class PGRPC_Request(abc.ABC):
    """Base request class."""

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

    @classmethod
    def result_fields(cls) -> list[str]:
        """Return the fields defined in the result so as to support FieldMasks."""
        return list(cls.RESULT_TYPE.__dataclass_fields__.keys())
