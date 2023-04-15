
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

In the utils module the main tool for retrieving the contract to publish use :py:meth:`pysui.sui.sui_utils.publish_build`

.. code-block:: Python

    from pathlib import Path
    from pysui.sui.sui_clients.sync_client import SuiClient
    from pysui.sui.sui_utils import publish_build
    from pysui.sui.sui_builders.exec_builders import Publish

    # Open up client
    client = SuiClient(SuiConfig.default_config())

    # Identify the path to the smart-contract project
    expanded_path:Path = Path(os.path.expanduser("~/frankc01/sui-two/parent"))

    # Compile project and fetch list of base64 encoded contract module(s)
    # As well as any ObjectIDs of published modules that the project depends on.
    pub_cfg: CompiledPackage = publish_build(expanded_path)

    # Setup the Publish builder
    builder = Publish(
        sender=<SUI ADDRESS OF PUBLISHING SIGNER>,
        compiled_modules=pub_cfg.compiled_modules,
        dependencies=pub_cfg.dependencies,
        gas=<OBJECT ID OF GAS OBJECT TO PAY FOR PUBLISHING>,
        gas_budget="20000000",
    )
    result = client.execute(builder=builder)
    if result.is_ok():
        print(result.result_data.to_json(indent=2))
    else:
        print(result.result_string)
