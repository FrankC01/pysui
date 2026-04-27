
###############
Getting Started
###############

Whether you are writing a new client application, extending pysui, or both,
there are a few setup steps required:

Setup
-----

While not required, it is common to create Python virtual environments
and then install packages into it.

#. Install Rust
    Rust is required to install the Sui binaries as well as `pysui-fastcrypto`

    ``curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh``

    **Note**: If you want to forego installing Rust, you will need to
    install a `pysui-fastcrypto <https://github.com/FrankC01/pysui-fastcrypto>`_ wheel for your environement from the
    lastest release on github.

#. Install Sui Binaries
    For certain capabilities, ``pysui`` requires the Sui binaries are installed
    on the same machine: `Install Sui <https://docs.sui.io/guides/developer/getting-started/sui-install>`_.

    Specifically, the binaries are required if...

    * You want to use the publish Sui package builder, and/or...
    * You want to use the Sui generated configuration for keystores and active
      environments


#. Install pysui

    Regardless, you can install ``pysui`` from PyPi:

    ``pip install pysui`` if first time install or 
    ``pip install -U --upgrade-strategy eager pysui`` if upgrading.


#. Follow the steps in the section **First time instantiation** on the :doc:`PysuiConfiguration <pyconfig>` page.

  If you have not previously setup ``pysui``, this creates the base PysuiConfiguration for GraphQL
  and gRPC protocols.


#. Test install
    Having setup your environment, you can verify all is well with a sample
    scripts included in the ``pysui`` distribution. From the command line:

    * ``async-gas`` This will display Sui gas for each address found in the
      SUI configuration
    * ``wallet`` This emulates a number of the ``sui client ...`` operations

Quick Start — Unified Client Interface
--------------------------------------

The recommended way to interact with Sui is through the **Unified Client Interface
(UCI)**: a single ``await client.execute(command=...)`` call that works
transparently with any configured transport (GraphQL or gRPC).  Switching
transports requires only a configuration change — no application code changes.

.. code-block:: python
   :linenos:

    import asyncio
    import pysui.sui.sui_common.sui_commands as cmd
    from pysui import PysuiConfiguration, client_factory, handle_result

    async def main():
        # Use SUI_GRPC_GROUP to target gRPC instead
        cfg = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP)
        async with client_factory(cfg) as client:
            result = await client.execute(
                command=cmd.GetGas(owner=client.config.active_address)
            )
            handle_result(result)

    if __name__ == "__main__":
        asyncio.run(main())

See :doc:`sui_commands` for the full list of available commands.
