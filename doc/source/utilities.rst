Utilities
=========

If installing **pysui** via PyPI the following utilities are ready to use from the command line.
If cloning the pysui repository and running ``pip install -r requirements.txt``, they are located
in ``samples/`` and can be invoked with:

.. list-table::
   :header-rows: 1
   :widths: 20 50

   * - PyPI command
     - Clone invocation
   * - ``wallet``
     - ``python samples/walletg.py``
   * - ``mtobcs``
     - ``python samples/mtobcs.py``
   * - ``async-gas``
     - ``python samples/async_gasg.py``
   * - ``sgqls``
     - ``python samples/sgqls.py``
   * - ``smash``
     - ``python samples/smash.py``
   * - ``splay``
     - ``python samples/splay.py``

Wallet (wallet)
---------------

The ``wallet`` CLI is the Swiss-army-knife companion to the ``sui client`` command. It covers
chain inspection, address and alias management, coin operations, Move package publishing and
calling, transaction simulation, and pre-signed transaction submission. It works with both
**GRAPHQL** and **GRPC** groups via the ``--group`` flag.

.. code-block:: console

    usage: walletg.py [options] command [--command_options]

    options:
      -h, --help            show this help message and exit
      --config CONFIG_NAME  The Pysui Configuration folder to use. Default to '~/.pysui'
      --group {sui_json_config,sui_gql_config,sui_grpc_config}
                            The active group to use. Default to 'sui_gql_config'
      --profile {devnet,testnet,mainnet}
                            The profile node to use.
      -v, --version         Sets flag to show version. Optional.

    commands:
      chain-id              Show current chain identifier
      txns                  Show transaction information (subcommands: count, txn)
      gas                   Show gas objects and total mist
      coins                 Show coin type balances
      object                Show object by id
      objects               Show all objects
      package               Show normalized package information
      active-address        Show active address
      addresses             Show all addresses
      new-address           Generate new address and keypair
      aliases               Sui address alias management (subcommands: list, rename)
      transfer-object       Transfer an object to another address
      transfer-sui          Transfer SUI mists to a Sui address
      pay                   Send coin of any type to recipient(s)
      merge-coin            Merge two coins together
      split-coin            Split coin into one or more coins by amount
      split-coin-equally    Split coin into one or more coins equally
      publish               Publish a SUI package
      call                  Call a Move contract function
      simulate              Simulate a transaction (TransactionData base64 bytes)
      execute-tx            Execute a signed transaction on blockchain
      version               Show pysui SDK version

*   --config      Path to a ``PysuiConfiguration`` folder. Defaults to ``~/.pysui``.
*   --group       Protocol group to use (``sui_json_config``, ``sui_gql_config``, or ``sui_grpc_config``).
*   --profile     Node endpoint within the chosen group (``devnet``, ``testnet``, ``mainnet``).

**Owner resolution:** Most commands accept ``-o/--owner`` (a Sui address) or ``-a/--alias``
(an alias name) to identify the acting address. These are mutually exclusive. If neither is
supplied the active address from the configuration is used.

Chain commands
**************

``chain-id``
    Show the current chain identifier for the connected node.

``txns count``
    Return the total network transaction count from the server.

``txns txn``
    Return detailed transaction information by digest.

.. code-block:: console

    wallet chain-id
    wallet txns count
    wallet txns txn --digest <DIGEST>

Read commands
*************

``gas``
    Show all SUI gas coins and the total balance for an address.

``coins``
    Show all coin-type balances for an address.

``objects``
    Show all objects owned by an address.

``object``
    Show a single object by its object ID.

``package``
    Show normalized Move package information by package ID.

.. code-block:: console

    wallet gas --alias Primary
    wallet coins --alias Primary
    wallet objects --alias Primary
    wallet object --id 0x<OBJECT_ID>
    wallet package --id 0x<PACKAGE_ID>

Account commands
****************

``active-address``
    Print the currently active Sui address from the configuration.

``addresses``
    List all addresses stored in the configuration.

``new-address``
    Generate a new keypair and Sui address.

``aliases list``
    List all aliases and their associated Sui addresses.

``aliases rename``
    Rename an existing alias.

.. code-block:: console

    wallet active-address
    wallet addresses
    wallet aliases list
    wallet aliases rename --alias OldName --new-alias NewName

Operations commands
*******************

All operations build a PTB via the pysui transaction builder and execute it on-chain.
``--budget`` (mists) and ``--gas`` (gas object ID) are optional for every operation;
if omitted, gas is selected and budgeted automatically by simulation.

``transfer-sui``
    Split a mist amount from a source gas coin and transfer it to a recipient.

.. code-block:: console

    wallet transfer-sui --alias Primary \
        --takes 0x<COIN_ID> --mists 1000000 --recipient 0x<ADDRESS>

``transfer-object``
    Transfer any object to a recipient address.

.. code-block:: console

    wallet transfer-object --alias Primary \
        --transfer 0x<OBJECT_ID> --recipient 0x<ADDRESS>

``pay``
    Split and send mist amounts from one or more input coins to one or more recipients.
    The ``--input-coins``, ``--mists``, and ``--recipients`` lists must be the same length.

.. code-block:: console

    wallet pay --alias Primary \
        --input-coins 0x<COIN_ID> --mists 500000 --recipients 0x<ADDRESS>

``merge-coin``
    Merge one coin into another (primary). To merge *all* coins to one, use ``smash`` instead.

.. code-block:: console

    wallet merge-coin --alias Primary \
        --primary-coin 0x<PRIMARY_ID> --coin-to-merge 0x<SOURCE_ID>

``split-coin``
    Split a coin into one or more new coins by explicit mist amounts.

.. code-block:: console

    wallet split-coin --alias Primary \
        --coin 0x<COIN_ID> --amounts 1000000 2000000

``split-coin-equally``
    Split a coin into *N* equal parts.

.. code-block:: console

    wallet split-coin-equally --alias Primary \
        --coin 0x<COIN_ID> --count 4

``publish``
    Build and publish a Move package from a project path.

.. code-block:: console

    wallet publish --alias Primary --project-path ./my_package

``call``
    Call a Move package function with typed arguments.

.. code-block:: console

    wallet call --alias Primary \
        --package 0x<PKG_ID> --module my_module --function my_fn \
        --type-arguments 0x2::sui::SUI \
        --args 0x<OBJ_ID> 42

Transaction commands
********************

``simulate``
    Decode a Base64-encoded ``TransactionData`` blob and simulate it on-chain.
    ``--checks-enabled`` (default ``True``) and ``--gas-selection`` (default ``True``)
    control simulation behaviour.

.. code-block:: console

    wallet simulate --txb <BASE64_BYTES>
    wallet simulate --txb <BASE64_BYTES> --checks-enabled False

``execute-tx``
    Submit pre-built Base64 transaction bytes together with one or more pre-assembled
    signatures. Equivalent to ``sui client execute-signed-tx``.

.. code-block:: console

    wallet execute-tx --txb <BASE64_BYTES> \
        --signatures <SIG1> [<SIG2> ...]

Info commands
*************

``version``
    Print the pysui SDK version.

.. code-block:: console

    wallet version

Move to BCS (mtobcs)
--------------------

The ``mtobcs`` utility converts Move structures, enums, and parameterized containers to Python BCS classes for deserialization.

.. code-block:: console

    usage: mtobcs [options]

    Generate python module of BCS classes from JSON. Supports GRAPHQL and GRPC groups.

    options:
    -h, --help            show this help message and exit
    --config CONFIG_NAME  The Pysui Configuration folder to use.
    --group {sui_gql_config,sui_grpc_config}
                            The GraphQL groups. Default to 'sui_gql_config'
    --profile {devnet,testnet,mainnet}
                            The GraphQL profile node. Default to 'devnet' from 'sui_gql_config'
    -v, --version         Sets flag to show version. Optional.
    -m MOVE_TARGETS, --move-target-file MOVE_TARGETS
                            JSON file containing directives of move package, module and types to convert to BCS structures.
    -o TARGET_OUTPUT_FOLDER, --output-folder TARGET_OUTPUT_FOLDER
                            The folder where the Python BCS module is written to. Default to current folder.

*   --config   Path to a ``PysuiConfiguration`` folder. Defaults to ``~/.pysui``. Pass a custom path to use an alternate configuration (e.g. ``--config /path/to/myconfig``).
*   --group    Selects the active group. Only GRAPHQL and GRPC groups are shown as valid choices.
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

Async Gas (async-gas)
---------------------

The ``async-gas`` utility reports all SUI coin balances for every address in the active
configuration group. It works with both **GRAPHQL** and **GRPC** groups; the ``--group``
flag is filtered to show only those two protocol types.

.. code-block:: console

    usage: async-gas [options]

    Report SUI gas for active address. Supports GRAPHQL and GRPC groups.

    options:
      -h, --help            show this help message and exit
      --config CONFIG_NAME  The Pysui Configuration folder to use.
      --group {sui_gql_config,sui_grpc_config}
                            The configuration group to use. Only GRAPHQL and GRPC
                            groups are listed. Default: active group.
      --profile {devnet,testnet,mainnet}
                            The profile (node endpoint) within the group.
                            Default: active profile.
      -v, --version         Show version and exit.

*   --config  Path to a ``PysuiConfiguration`` folder. Defaults to ``~/.pysui``. Pass a custom path to use an alternate configuration (e.g. ``--config /path/to/myconfig``).
*   --group   The group to query. Only GRAPHQL and GRPC groups appear as choices; custom-named groups with a supported protocol are also listed.
*   --profile The node endpoint within the chosen group.

Example: default active group
******************************

.. code-block:: console

    async-gas

Example: explicit gRPC group and testnet profile
*************************************************

.. code-block:: console

    async-gas --group sui_grpc_config --profile testnet

Sui GraphQL Schema Persist (sgqls)
-----------------------------------

The ``sgqls`` utility fetches and persists the GraphQL schema for each profile in a
**GRAPHQL** group to the project root. Only GRAPHQL groups are offered as choices.

.. code-block:: console

    usage: sgqls.py [options] command [--command_options]

    Persist Sui GraphQL schemas

    options:
      -h, --help            show this help message and exit
      --group {sui_gql_config}
                            The GraphQL group. Only GRAPHQL groups are listed.
                            Default to 'sui_gql_config'
      --profile {all,devnet,testnet,mainnet} [{all,devnet,testnet,mainnet} ...]
                            GraphQL profile(s) to generate schemas for. Defaults
                            to 'all'

*   --group    The GRAPHQL group whose profiles will have schemas persisted. Custom-named GRAPHQL groups also appear as choices.
*   --profile  One or more profile names to fetch schemas for. Use ``all`` (default) to fetch every profile in the group.

Example: persist schemas for all profiles (default)
****************************************************

.. code-block:: console

    sgqls

Example: persist schema for a single profile
*********************************************

.. code-block:: console

    sgqls --profile testnet

Example: explicit group and targeted profiles
*********************************************

.. code-block:: console

    sgqls --group sui_gql_config --profile devnet mainnet

Smash (smash)
-------------

The ``smash`` utility merges multiple SUI gas coins for an address into a single coin.
It works with both **GRAPHQL** and **GRPC** groups; the ``--group`` flag is filtered to
show only those two protocol types.

.. code-block:: console

    usage: smash [options]

    Smash (merge) addresses sui coins to one.

    options:
      -h, --help            show this help message and exit
      --config CONFIG_NAME  The Pysui Configuration folder to use.
      --group {sui_gql_config,sui_grpc_config}
                            The configuration group to use. Only GRAPHQL and GRPC
                            groups are listed. Default: active group.
      --profile {devnet,testnet,mainnet}
                            The profile (node endpoint) within the group.
                            Default: active profile.
      -o OWNER, --owner OWNER
                            Sui address of gas owner. Mutually exclusive with
                            '-a/--alias'.
      -a ALIAS, --alias ALIAS
                            Alias of owner address. Mutually exclusive with
                            '-o/--owner'.
      -i INCLUDE, --include INCLUDE
                            Restrict the merge to these coin object IDs only.
                            One or more IDs can be specified.
      -e EXCLUDE, --exclude EXCLUDE
                            Exclude these coin object IDs from the merge.
                            One or more IDs can be specified.
      -w, --wait            Wait for transaction checkpoint inclusion before
                            returning. Optional.
      -v, --version         Show version and exit.

*   --config    Path to a ``PysuiConfiguration`` folder. Defaults to ``~/.pysui``. Pass a custom path to use an alternate configuration (e.g. ``--config /path/to/myconfig``).
*   --group     The group to use. Only GRAPHQL and GRPC groups appear as choices; custom-named groups with a supported protocol are also listed.
*   --profile   The node endpoint within the chosen group.
*   --owner     The Sui address of the coin owner. Mutually exclusive with ``--alias``.
*   --alias     An alias name for the owner address. Mutually exclusive with ``--owner``.
*   --include   One or more coin object IDs to merge together. If specified, only these coins are candidates for merge.
*   --exclude   One or more coin object IDs to exclude from merge. If specified, all other coins are candidates.
*   --wait      Poll the transaction until checkpoint inclusion before returning.

**Combining --include and --exclude:** These flags are **not** mutually exclusive.
When both are provided, ``--exclude`` is applied first (filtering out named coins),
then ``--include`` is applied to the remaining set (selecting only named coins).
If a coin ID appears in both arguments, the exclude takes precedence.

Example: merge all coins
*************************

.. code-block:: console

    smash

Example: merge with custom address
************************************

.. code-block:: console

    smash --owner 0x123456abcdef...

Example: merge only specific coins
***********************************

.. code-block:: console

    smash --include 0xaaa... 0xbbb... 0xccc...

Example: merge all except specific coins
*****************************************

.. code-block:: console

    smash --exclude 0xstaking... 0xreserve...

Example: combine include and exclude
*************************************

.. code-block:: console

    smash --include 0xaaa... 0xbbb... 0xccc... --exclude 0xbbb...

This merges coins ``0xaaa...`` and ``0xccc...`` (``0xbbb...`` is excluded despite being
in the include list).

Splay (splay)
-------------

The ``splay`` utility merges all SUI gas coins for an address into one coin, then
spreads (splays) the balance evenly to itself as *N* new coins or to one or more
recipient addresses. It works with both **GRAPHQL** and **GRPC** groups; the
``--group`` flag is filtered to show only those two protocol types.

.. code-block:: console

    usage: splay [options].

    splay spreads all, selected coins or count evenly to itself or other addresses.

    options:
      -h, --help            show this help message and exit
      --config CONFIG_NAME  The Pysui Configuration folder to use.
      --group {sui_gql_config,sui_grpc_config}
                            The configuration group to use. Only GRAPHQL and GRPC
                            groups are listed. Default: active group.
      --profile {devnet,testnet,mainnet}
                            The profile (node endpoint) within the group.
                            Default: active profile.
      -o OWNER, --owner OWNER
                            Sui address of gas owner. Mutually exclusive with
                            '-a/--alias'.
      -a ALIAS, --alias ALIAS
                            Alias of owner address. Mutually exclusive with
                            '-o/--owner'.
      -i INCLUDE [INCLUDE ...], --include INCLUDE [INCLUDE ...]
                            Restrict the merge step to these coin object IDs only.
                            One or more IDs can be specified.
      -e EXCLUDE [EXCLUDE ...], --exclude EXCLUDE [EXCLUDE ...]
                            Exclude these coin object IDs from the merge step.
                            One or more IDs can be specified.
      -m MIST, --mist MIST  Amount per split coin. Express as raw mists (e.g.
                            ``500000``) or as Sui (e.g. ``1S`` or ``1s``).
      -n NUMBER, --number NUMBER
                            Splay into N coins sent back to the signing address.
                            Must be >= 2. Mutually exclusive with '-r/--recipients'.
      -r RECIPIENTS [RECIPIENTS ...], --recipients RECIPIENTS [RECIPIENTS ...]
                            Splay evenly to these recipient addresses.
                            Mutually exclusive with '-n/--number'.
      --dry-run             Parse and display the routing decision without
                            executing. Optional.
      -v, --version         Show version and exit.

*   --config      Path to a ``PysuiConfiguration`` folder. Defaults to ``~/.pysui``.
*   --group       The group to use. Only GRAPHQL and GRPC groups appear as choices.
*   --profile     The node endpoint within the chosen group.
*   --owner       The Sui address of the coin owner. Mutually exclusive with ``--alias``.
*   --alias       An alias name for the owner address. Mutually exclusive with ``--owner``.
*   --include     One or more coin object IDs to restrict the merge step to.
*   --exclude     One or more coin object IDs to exclude from the merge step.
*   --mist        Amount per output coin. Omit to split the available balance evenly across all outputs.
*   --number      Number of coins to create and send to the signing address (>= 2). Mutually exclusive with ``--recipients``.
*   --recipients  One or more recipient addresses to receive one split coin each. Mutually exclusive with ``--number``.
*   --dry-run     Print the routing decision (address, recipients/count, mist, include/exclude) without executing any transaction.

**Gas budget:** ``splay`` does not accept an explicit budget argument. The gas cost is
determined automatically by transaction simulation. If the split amount plus the
simulated gas cost would exceed the available coin balance, the transaction is
rejected before submission.

**Routing rules:**

*   ``-n`` and ``-r`` are mutually exclusive.
*   ``-n`` must be >= 2 (splaying to self requires at least two output coins).
*   If neither ``-n`` nor ``-r`` is given, recipients are taken from all other
    addresses in the active configuration group. If no such addresses exist, splay
    exits with an error.

Example: splay to self (5 coins)
**********************************

.. code-block:: console

    splay -n 5

Example: splay to self with explicit amount
*********************************************

.. code-block:: console

    splay -n 5 -m 2S

Example: splay to recipients
*****************************

.. code-block:: console

    splay -r 0xrecipient1... 0xrecipient2...

Example: splay to one recipient with explicit amount
*****************************************************

.. code-block:: console

    splay -r 0xrecipient1... -m 10S

Example: splay with custom owner
**********************************

.. code-block:: console

    splay -o 0x123456abcdef... -r 0xrecipient1...

Example: dry run to preview routing
*************************************

.. code-block:: console

    splay -n 3 --dry-run
