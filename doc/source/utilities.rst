Utilities
=========

Move to BCS (mtobcs)
--------------------

**BETA** - Potential for many changes. Currenly it handles more straight forward constructs.

The ``mtobcs`` utility converts move structures, enums, etc. to python BCS classes for deserialization.

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

Example
*******

Assumes you have ``pysui 0.82.0`` (or above) installed in a virtual environment

This example, from ``mainnet`` uses the GenericStructure target above assuming it sits in a json file called ``mainnet_test.json``. 

From the command line

.. code-block:: console

    mtobcs --profile mainnet -m mainnet_test.json

This will produce ``system_state_internal.py`` in the current directory. The following script will fetch the object, deserialize it 
using the python BCS file created and print out json formatted data. Save it to a file called ``demo_bcs.py``

.. code-block:: python

    #    Copyright Frank V. Castellucci
    #    SPDX-License-Identifier: Apache-2.0

    # -*- coding: utf-8 -*-

    """Sample deserialization of Sui object to json output."""

    from pysui import SyncGqlClient, PysuiConfiguration
    from pysui.sui.sui_pgql.pgql_query import GetObjectContent

    import system_state_internal as sys1


    def main():
        """Demo."""
        # Set mainnet url
        cfg = PysuiConfiguration(
            group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP,
            profile_name="mainnet",
        )

        # Get the GraphQL client
        client_init = SyncGqlClient(write_schema=False, pysui_config=cfg)

        # Fetch the BCS string for the object
        qn = GetObjectContent(
            object_id="0xc5e430c7c517e99da14e67928b360f3260de47cb61f55338cdd9119f519c282c"
        )
        result = client_init.execute_query_node(with_node=qn)

        # Deserialize
        if result.is_ok():
            ser_po = result.result_data.as_bytes()
            pool_obj = sys1.GenericStructure_address_u64_SystemStateInnerV1.deserialize(
                ser_po
            )
            print(pool_obj.to_json(indent=2))


    if __name__ == "__main__":
        main()


This script can be run from command line with 

.. code-block:: console

    python -m demo_bcs