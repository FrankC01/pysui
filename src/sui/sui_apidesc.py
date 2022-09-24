"""Sui RPC API Descriptor."""

from dataclasses import dataclass
from dataclasses_json import dataclass_json

# T = TypeVar("T", str, float, int, list)


@dataclass_json
@dataclass(frozen=True)
class SuiApiParam:
    """Sui API Parameter Data Class."""

    name: str
    description: str
    schema: dict
    required: bool = False


@dataclass_json
@dataclass(frozen=True)
class SuiApiResult:
    """Sui API Result Data Class."""

    name: str
    required: bool
    schema: dict


@dataclass_json
@dataclass(frozen=True)
class SuiApi:
    """Sui API Data Class."""

    name: str
    description: str
    params: list[SuiApiParam]
    result: SuiApiResult


def from_json_api(indata: dict) -> SuiApi:
    """Convert return from rpc.discover to data object."""
    return SuiApi.from_dict(indata)


if __name__ == "__main__":
    sample = {
        "name": "sui_getObject",
        "tags": [{"name": "Read API"}],
        "description": "Return the object information for a specified object",
        "params": [
            {
                "name": "object_id",
                "description": "the ID of the queried object",
                "required": True,
                "schema": {"$ref": "#/components/schemas/ObjectID"},
            }
        ],
        "result": {
            "name": "GetObjectDataResponse",
            "required": True,
            "schema": {"$ref": "#/components/schemas/ObjectRead"},
        },
    }
    print(SuiApi.from_dict(sample))
