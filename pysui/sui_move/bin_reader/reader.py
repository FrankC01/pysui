#    Copyright (c) Frank V. Castellucci
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

"""Byte reader class."""


import io
from typing import Union


class BinaryReader:
    """BinaryReader manages loading and accessing areas of binary file."""

    def __init__(self, source: str, data: bytes) -> None:
        """__init__ Initialize reader.

        :param binary_file: The path and file name to load
        :type binary_file: str
        """
        self.length = len(data)
        self.reader = io.BytesIO(data)
        self.source = source

    def pos(self) -> int:
        """pos Report the current reader position.

        :return: Current positiion of reader
        :rtype: int
        """
        return self.reader.tell()

    def move_to(self, location: int, relative_to: int = 0) -> Union[int, ValueError]:
        """move_to Positions the reader to stream location.

        :param location: The location in the stream to position at, may be negative
        :type location: int
        :param relative_to: 0 from beginning, 1 for current and 2 for end, defaults to 0
        :type relative_to: int, optional
        :raises ValueError: location is invalid
        :return: the previous location
        :rtype: Union[int, ValueError]
        """
        current_loc = self.pos()
        fail: bool = False
        match relative_to:
            case 0:
                if location < 0 or location > self.length:
                    fail = True
            case 1:
                repos = current_loc + location
                if repos < 0 or repos > self.length:
                    fail = True
            case 2:
                repos = self.length + location
                if repos < 0 or repos > self.length:
                    fail = True
            case _:
                fail = True
        if fail:
            raise ValueError(f"Invalid location {location}. Max position is {self.length}")
        self.reader.seek(location, relative_to)
        return current_loc

    def read(self, size: int = None) -> bytes:
        """."""
        size = size or 1
        return self.reader.read(size)

    def read_as_int(self, size: int = None) -> int:
        """read_as_int Read in size bytes and convert to int.

        :param size: The number of bytes to read, defaults to None
        :type size: int, optional
        :return: The read bytes converted to little endien int
        :rtype: int
        """
        return int.from_bytes(self.read(size), "little")

    def read_as_bool(self) -> bool:
        """."""
        return self.read_as_int() == 1

    def read_uleb128(self) -> int:
        """read_uleb128 reads a uleb128 value from stream."""

        def _decode(barray: bytearray) -> int:
            """Decode the unsigned uleb128 expanded bytearray."""
            res = 0
            for i, value in enumerate(barray):
                res = res + ((value & 0x7F) << (i * 7))
            return res

        array = bytearray()
        while True:
            inb = ord(self.read())
            array.append(inb)
            if (inb & 0x80) == 0:
                break
        return _decode(array)

    def read_from_uleb_array(self) -> bytes:
        """read_from_uleb_array reads vector with uleb128 count.

        :return: The bytes read into based on array size
        :rtype: bytes
        """
        content_size = self.read_uleb128()
        if content_size == 0:
            return None
        return self.read(content_size)


# if __name__ == "__main__":
#     reader = BinaryReader("~/frankc01/sui-track/build/SuiTrack/bytecode_modules/base.mv")
#     val = reader.read()
#     print(val)
