
Publish
=======

General
-------
**Sui** supports building and publishing of smart contracts.

* It requires installing the `sui binaries` to compile smart contracts.
* `pysui` does not have a move compiler and relies on the `sui binaries` to do a clean compile before publishing.


Publishing utility and builder
------------------------------

In ``pysui`` there are *two* modules specifically for publishing:

#. :py:mod:`pysui.sui.sui_utils` - This module contains the utilities for compiling and retrieving contract binaries.
#. :py:mod:`pysui.sui.sui_builders.exec_builders` - This module contains the ``Publish`` builder to push contract to the chain.

To ``Publish`` to the Sui block chain you first have to retreive the base64 encoded content from compiled contract source.

In the utils module the main tool for retrieving the contract to publish use :py:meth:`pysui.sui.sui_utils.build_b64_modules`

.. code-block:: Python

    from pathlib import Path
    from pysui.sui.sui_clients.sync_client import SuiClient
    from pysui.sui.sui_utils import build_b64_modules
    from pysui.sui.sui_builders.exec_builders import Publish

    # Identify the path to the smart-contract project
    expanded_path = Path(os.path.expanduser("~/frankc01/sui-two/parent"))

    # Compile project and fetch list of base64 encoded contract module(s)
    modules: list[str] = build_b64_modules(expanded_path)

    # Setup the Publish builder
    builder = Publish(
        sender=<SUI ADDRESS OF PUBLISHING SIGNER>,
        compiled_modules=modules,
        gas=<OBJECT ID OF GAS OBJECT TO PAY FOR PUBLISHING>,
        gas_budget=2000,
    )
    result = client.execute(builder=builder)
    if result.is_ok():
        print(result.result_data.to_json(indent=2))
    else:
        print(result.result_string)
