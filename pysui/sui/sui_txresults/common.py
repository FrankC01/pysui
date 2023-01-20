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

"""Sui Common Result Type classes."""


from abc import ABC
from dataclasses import dataclass, field
from typing import Union
from dataclasses_json import DataClassJsonMixin, LetterCase, config

from pysui.sui.sui_types import ObjectID


@dataclass
class GenericRef(DataClassJsonMixin):
    """Generic object reference."""

    object_id: ObjectID = field(metadata=config(letter_case=LetterCase.CAMEL))
    version: int
    digest: str


@dataclass
class CoinRef(GenericRef):
    """Coin representation."""


@dataclass
class PackageRef(GenericRef):
    """Package representation."""


class SuiTxReturnType(ABC):
    """Abstraction for all return objects."""


@dataclass
class GenericOwnerRef(SuiTxReturnType, DataClassJsonMixin):
    """Owned coin referenece."""

    reference: GenericRef  # = None
    owner: Union[dict, str] = field(default_factory=str)

    def __post_init__(self):
        """Post init processing.

        Convert owner to Address (based on result)
        """
        if self.owner:
            if isinstance(self.owner, str):
                self.owner = self.owner
            else:
                if "AddressOwner" in self.owner:
                    self.owner = self.owner["AddressOwner"]
                if "ObjectOwner" in self.owner:
                    self.owner = self.owner["ObjectOwner"]
                if "Shared" in self.owner:
                    self.owner = self.owner["Shared"]
