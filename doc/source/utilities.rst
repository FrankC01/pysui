Utilities
=========

Move to BCS (mtobcs)
--------------------

The ``mtobcs`` utility converts Move structures, enums, and parameterized containers to Python BCS classes for deserialization.

.. code-block:: console

    usage: mtobcs.py [options] command [--command_options]

    Generate python module of BCS classes from JSON.

    options:
    -h, --help            show this help message and exit
    --config CONFIG_PATH  The Pysui Configuration folder to use.
    --group {user,sui_json_config,sui_gql_config}
                            The configuration groups. Default to 'sui_gql_config'
    --profile {devnet,testnet,mainnet}
                            The configuration group profile node. Default to 'devnet' from 'sui_gql_config'
    -v, --version         Sets flag to show version. Optional.
    -m MOVE_TARGETS, --move-target-file MOVE_TARGETS
                            JSON file containing directives of move package, module and types to convert to BCS structures.
    -o TARGET_OUTPUT_FOLDER, --output-folder TARGET_OUTPUT_FOLDER
                            The folder where the Python BCS module is written to. Default to current folder.

*   --config   This identifies the locaiton of the PysuiConfiguration file containing groups and profiles. Defaults to ``~/.pysui``
*   --group    The group within the configuration file to set as active
*   --profile  The profile within the group to set as active
*   -m         The ``mtobcs`` directive json file (see below)
*   -o         The output folder where to place the resulting python BCS class declarations. The filename is set in the json directive file 

JSON Configuration File 
***********************

This json file identifies targets for python BCS generation. The primary object in the file is ``targets`` which contains 
one or more maps of key/value pairs.

**Structure** - The most straight forward example is for retrieving a structure declaration. ``mtobcs`` will fetch the identified
structure and all it's propery dependencies.

This example from ``devnet`` shows one target of a move Structure with it's fully qualified address (package::module::type). ``mtobcs`` will create 
the file with name specified in the ``out_file`` and will place it in the command line ``-o`` argument folder or default location.

.. code-block:: json 

    {
        "targets" : [
            {
                "type": "Structure",
                "value":"0x0ea617f94df345f7179bdf0853874182ba8afecad1cf2c6ac97db971f5bd4aef::parms::ParmObject",
                "out_file": "parm_object.py"
            }
        ]
    }

**GenericStructure** - Use a generic structure target when you move struct is declared with them. As an example
here is the ``dynamic_field.move`` struct declaration:

.. code-block:: rust 
    
    public struct Field<Name: copy + drop + store, Value: store> has key {
        /// Determined by the hash of the object ID, the field name value and it's type,
        /// i.e. hash(parent.id || name || Name)
        id: UID,
        /// The value for the name of this field
        name: Name,
        /// The value bound to this field
        value: Value,
    }


The corresponding target from ``mainnet`` looks like this:

.. code-block:: json

    {
        "targets" : [
            {
                "type": "GenericStructure",
                "id": "address",
                "name": "u64",
                "value":"0xfdc88f7d7cf30afab2f82e8380d11ee8f70efb90e863d1de8616fae1bb09ea77::system_state_inner::SystemStateInnerV1",
                "out_file": "system_state_internal.py"
            }
        ]
    }

**RULES FOR ALL TARGETS**

#. Where a JSON key value is a fully qualified address (as shown for ``value`` above), the package portion is the move module address in a particular network (e.g. devnet, testnet or mainnet)


**RULES FOR GENERICSTRUCTURE TARGETS**

#. The field identifiers MUST follow the order in the move structure declarations, do NOT intermingle ``type`` or ``out_file``.
#. Field values are in quotes (strings).
#. Field values can either be standard move types (u8 to u256, address or string).

Example 1: Command Line usage (GraphQL)
***************************************

This example, from ``mainnet``, uses the GenericStructure target above assuming it sits in a json file called ``mainnet_test.json``.

From the command line:

.. code-block:: console

    mtobcs --profile mainnet -m mainnet_test.json

This will produce ``system_state_internal.py`` in the current directory. The following script will fetch the object, deserialize it
using the generated Python BCS file and print out JSON formatted data. Save it to a file called ``demo_bcs.py``.

.. code-block:: python

    #    Copyright Frank V. Castellucci
    #    SPDX-License-Identifier: Apache-2.0

    # -*- coding: utf-8 -*-

    """Sample deserialization of Sui object to json output."""

    import asyncio
    from pysui import AsyncClientBase, PysuiConfiguration, client_factory
    import pysui.sui.sui_common.sui_commands as cmd

    import system_state_internal as sys1


    async def main():
        """Demo."""
        cfg = PysuiConfiguration(
            group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP,
            profile_name="mainnet",
        )
        async with client_factory(cfg) as client:
            result = await client.execute(
                command=cmd.GetObjectContent(
                    object_id="0xc5e430c7c517e99da14e67928b360f3260de47cb61f55338cdd9119f519c282c"
                )
            )
            if result.is_ok():
                ser_po = result.result_data.as_bytes()
                pool_obj = sys1.GenericStructure_address_u64_SystemStateInnerV1.deserialize(
                    ser_po
                )
                print(pool_obj.to_json(indent=2))


    if __name__ == "__main__":
        asyncio.run(main())

Example 2: Programmatically (GraphQL)
*************************************

To perform building the python BCS module (emphemerally) and deserializing a move object requires
an async loop for execution. This is one contrived example

.. code-block:: python

    #    Copyright Frank V. Castellucci
    #    SPDX-License-Identifier: Apache-2.0

    # -*- coding: utf-8 -*-

    """Sample interactive mtobcs."""

    import asyncio
    import json
    from pathlib import Path
    from typing import Any

    from pysui import PysuiConfiguration, AsyncClientBase, client_factory
    import pysui.sui.sui_common.sui_commands as cmd
    from pysui.sui.sui_common.move_to_bcs import MoveDataType
    import pysui.sui.sui_common.mtobcs_types as mtypes


    async def resolve_bcs_class(
        client: AsyncClientBase, target: mtypes.GenericStructure
    ) -> Any:
        """Resolve Move target and return base python BCS class."""

        mdt: MoveDataType = MoveDataType(client=client, target=target)
        root_class_name: str = await mdt.parse_move_target()
        namespace = await mdt.compile_bcs()
        return namespace[root_class_name]


    async def get_object_content(client: AsyncClientBase, object_id: str) -> bytes:
        """Fetch an object's BCS content."""

        result = await client.execute(
            command=cmd.GetObjectContent(object_id=object_id)
        )
        if result.is_ok():
            return result.result_data.as_bytes()
        else:
            raise ValueError(f"Fetch failed with {result.result_string}")


    async def _execute():
        """Demo execution potential"""

        async with client_factory(
            PysuiConfiguration(
                group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP,
                profile_name="mainnet",
            )
        ) as client:
            # Load the mtobcs target structure (dataclass) from json
            target_decl = Path("mainnet_test.json")
            package_targets: mtypes.Targets = mtypes.Targets.load_declarations(
                json.loads(target_decl.read_text(encoding="utf8"))
            )
            # Schedule tasks and await results
            results = await asyncio.gather(
                resolve_bcs_class(client, package_targets.targets[0]),
                get_object_content(
                    client, "0xc5e430c7c517e99da14e67928b360f3260de47cb61f55338cdd9119f519c282c"
                ),
            )
            print(results[0].deserialize(results[1]).to_json(indent=2))


    if __name__ == "__main__":
        asyncio.run(_execute())

Parameterized Containers: VecMap and VecSet
*******************************************

``mtobcs`` generates concrete, fully-typed BCS subclasses for ``VecMap<K,V>`` and
``VecSet<T>`` fields encountered during a type walk. These containers are serialized
**inline** in BCS (not as dynamic-field child objects), so a concrete subclass is
required for correct deserialization. Earlier versions mapped them to opaque stubs
with no fields, silently consuming zero bytes and producing corrupted results.

When ``mtobcs`` encounters a ``VecMap<Address, U64>`` field it emits:

.. code-block:: python

    class Entry_Address_U64(BCS_Struct):
        _fields = [("key", bcse.Address), ("value", bcse.U64)]

    class VecMap_Address_U64(BCS_Struct):
        _fields = [("contents", [Entry_Address_U64, None, True])]

Nested parameterization (e.g. ``VecMap<Address, VecSet<Address>>``) is also handled —
the ``VecSet_Address`` entry type is generated first, then the ``Entry`` and ``VecMap``
wrappers that reference it.

Example 3: Sui System State (bundled)
**************************************

A ready-made directive file for the Sui framework types is bundled at
``samples/mtobcs_sysstate.json``. It targets ``SuiSystemStateInnerV2``,
``ValidatorSet``, and ``Validator`` from package ``0x3``. Running it against any
network regenerates ``pysui/sui/sui_bcs/sui_system_bcs.py``:

.. code-block:: console

    mtobcs -m samples/mtobcs_sysstate.json -o pysui/sui/sui_bcs/

The two new SuiCommand subclasses — ``GetLatestSuiSystemState`` and
``GetCurrentValidators`` — use the generated ``sui_system_bcs.py`` classes directly:

.. code-block:: python

    import asyncio
    from pysui import AsyncClientBase, PysuiConfiguration, client_factory
    import pysui.sui.sui_common.sui_commands as cmd


    async def main():
        cfg = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP)
        async with client_factory(cfg) as client:
            # Full system state (SuiSystemStateInnerV2)
            state_result = await client.execute(command=cmd.GetLatestSuiSystemState())
            if state_result.is_ok():
                print(state_result.result_data.to_json(indent=2))

            # Active validator list only
            val_result = await client.execute(command=cmd.GetCurrentValidators())
            if val_result.is_ok():
                for v in val_result.result_data:
                    print(v.metadata.name, v.voting_power)


    if __name__ == "__main__":
        asyncio.run(main())
