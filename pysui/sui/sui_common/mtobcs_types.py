##    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-


"""Data classes for mtobcs directives."""
from typing import Union
import dataclasses
import dataclasses_json


@dataclasses_json.dataclass_json(
    letter_case=dataclasses_json.LetterCase.CAMEL,
    undefined=dataclasses_json.Undefined.INCLUDE,
)
@dataclasses.dataclass
class GenericStructure:
    """mtobcs directive declaring a dynamic generic structure to generate."""

    dynamic_type: str = dataclasses.field(
        metadata=dataclasses_json.config(field_name="type")
    )
    out_file: str
    properties: dataclasses_json.CatchAll


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class Structure:
    """mtobcs directive declaring a Move structure to generate."""

    struct_type: str = dataclasses.field(
        metadata=dataclasses_json.config(field_name="type")
    )
    value_type: str = dataclasses.field(
        metadata=dataclasses_json.config(field_name="value")
    )
    out_file: str


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class Targets:
    """mtobcs directive container holding the list of generation targets."""

    targets: list[Structure | GenericStructure]

    @classmethod
    def load_declarations(cls, in_data):
        """."""
        targlist: list = []
        if in_data:
            for target in in_data.get("targets"):
                match target["type"]:
                    case "Structure":
                        targlist.append(Structure.from_dict(target))
                    case "GenericStructure":
                        targlist.append(GenericStructure.from_dict(target))
                    case _:
                        raise ValueError("Uknown type in mtobcs declarations.")
            return cls(targlist)
        raise ValueError("Missing mtobcs declarations.")
