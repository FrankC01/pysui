#

"""Stuff"""

import canoser


class FirstClass(canoser.Struct):
    """Flimsy."""

    _fields = [
        ("a", canoser.Uint8),
        ("b", [canoser.Uint8]),
        ("c", (canoser.Uint8, canoser.Uint16)),
        ("d", canoser.ArrayT(canoser.Uint8, 32, False)),
        ("e", {bytes: [canoser.Uint8]}),
    ]


class MyEnum(canoser.RustEnum):
    """."""

    _enums = [
        ("One", FirstClass),
        ("Two", canoser.Uint8),
        ("Three", False),
    ]


class U8Optional(canoser.RustOptional):
    """."""

    _type = canoser.Uint8


if __name__ == "__main__":
    pass
    # sc= SecondClass(a=FirstClass(Goober=16))
    # print(sc.to_json(indent=2))
