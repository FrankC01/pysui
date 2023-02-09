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

"""Move module byte reader class."""

import os
import base64
import binascii
from pathlib import Path
from typing import Any, Callable, Union
from pysui.sui_move.bin_reader.reader import BinaryReader
from pysui.sui_move.model.common_types import TableHeader, TableType


class ModuleReader(BinaryReader):
    """."""

    U32_BYTES: int = 4
    MAGIC_WORD: str = "a11ceb0b"
    TABLE_HEADER_START: int = U32_BYTES * 2

    def __init__(self, source: str, binary_data: bytes) -> None:
        """__init__ Instantiate ModuleReader.

        :param source: The original source
        :type source: str
        :param binary_data: A bytes string of module content
        :type binary_data: bytes
        :raises ValueError: If bytes content doesn't conform to move module standards.
        """
        super().__init__(source, binary_data)
        if self.length < 9 or self.read(self.U32_BYTES).hex() != self.MAGIC_WORD:
            raise ValueError("Invalid sui move binary file.")
        self.version = self.read_as_int(self.U32_BYTES)
        self._table_count = self.read_as_int()
        # Get the table header start position and module self index
        self._table_header_pos = self.move_to(-1, 2)
        self._module_self_index = self.read_uleb128()
        self.move_to(self._table_header_pos)
        # Next uleb is table count
        self._table_cross_ref: dict[TableType, TableHeader] = self._build_cross_reference(self._table_count)

    def _build_cross_reference(self, table_count: int) -> dict[TableType, TableHeader]:
        """_read_tblheaders_and_base Reads the table headers and establish table content offset.

        :param table_count: The number of expected table headers
        :type table_count: int
        :return: A dictionary of TableType -> TableHeader
        :rtype: dict[TableType, TableHeader]
        """
        headers: list[TableHeader] = []
        # Get table type headers
        for _ in range(table_count):
            headers.append(
                TableHeader(
                    TableType(self.read_as_int()),
                    self.read_uleb128(),
                    self.read_uleb128(),
                )
            )
        # Set convenience absolte position and gen cross-ref associations
        base = self.pos()
        cross_ref: dict[TableType, TableHeader] = {}
        for hdr in headers:
            hdr.pos = base + hdr.offset
            cross_ref[hdr.kind] = hdr
        return cross_ref

    @classmethod
    def read_from_file(cls, module: str) -> Union["ModuleReader", ValueError, IOError]:
        """read_from_file instantiates a module byte reader from a file path.

        :raises ValueError: If file does not exist
        :return: the instantiated ModuleReader
        :rtype: ModuleReader
        """
        fq_mp = Path(os.path.expanduser(module))
        if fq_mp.exists():
            return cls(fq_mp, fq_mp.read_bytes())
        raise ValueError(f"{module} file does not exist")

    @classmethod
    def read_from_base64(cls, in_base64: str) -> Union["ModuleReader", binascii.Error]:
        """read_from_base64 Instantiate a move binary table reader from base64 string.

        :return: the instantiated ModuleReader
        :rtype: ModuleReader
        """
        return cls(in_base64, base64.b64decode(in_base64))

    def has_table(self, table_type: TableType) -> bool:
        """has_table Test if TableType exists in byte code.

        :param table_type: The type of table to test for
        :type table_type: TableType
        :return: True if it exists, false otherwise
        :rtype: bool
        """
        return table_type in self.cross_reference

    def position_content_for(self, table_header: TableHeader) -> int:
        """position_content_for position the module byte read to a table.

        :param table_header: The TableHeader representing a table typel
        :type table_header: TableHeader
        :return: the position moved to
        :rtype: int
        """
        return self.move_to(table_header.pos)

    def build_content_for(
        self,
        table_type: TableType,
        handler: Callable[[TableHeader, "ModuleReader"], list],
    ) -> Union[list, None]:
        """build_content_for builds a decomposed content model for a table_type.

        :param table_type: The type of table to decompose from byte code stream
        :type table_type: TableType
        :param handler: Function that takes two arguments and returns a list.
            First argument is the TableType's TableHeader
            Second argument is this ModuleReader
        :type handler: Callable[[ModuleReader, dict[TableType, TableHeader]], list]
        :return: List of table type contents decomposed
        :rtype: Union[list, None]
        """
        if self.has_table(table_type):
            return handler(self.cross_reference[table_type], self)
        return None

    def build_model_list(self, handler: Callable[["ModuleReader"], Any]) -> list:
        """build_model_list reads a length encoded vector/list into a model component.

        :param handler: Function taking the module reader
        :type handler: Callable[[ModuleReader], Any]
        :return: a list of model types read from vector/list
        :rtype: list
        """
        count = self.read_uleb128()
        results = []
        for _ in range(count):
            results.append(handler(self))
        return results

    @property
    def self_index(self) -> int:
        """self_index Gets the index to the module as self.

        :return: The self module index
        :rtype: int
        """
        return self._module_self_index

    @property
    def table_count(self) -> int:
        """table_count Return table counts in module.

        :return: The number of byte code tables found in module header.
        :rtype: int
        """
        return self._table_count

    @property
    def cross_reference(self) -> dict[TableType, TableHeader]:
        """cross_reference Get the cross reference table.

        :return: Associative structure of TableType -> TableHeader
        :rtype: dict[TableType, TableHeader]
        """
        return self._table_cross_ref
