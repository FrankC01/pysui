
#######
Logging
#######

The ``pysui`` package has logging enabled. However; it is up to the
application(s) using the SDK to setup logging configuration. If this
is not done, ``pysui`` logging information is lost.

Module Logging
--------------

Select ``pysui`` modules are setup for logging and have the following
construct:

.. code-block:: Python

    logger = logging.getLogger("pysui.MODULE_NAME")
    if not logging.getLogger().handlers:
        logger.addHandler(logging.NullHandler())
        logger.propagate = False

As you can see, if a root logger is not setup, ``pysui`` log messages
go to the NullHandler (no-op)

With this construct, the root logger (in application) **must** be configured
prior to the inclusion of ``pysui`` modules. For example:

.. code-block:: Python

    import logging

    logging.basicConfig(
        filename="myapplication.log",
        filemode="w",
        encoding="utf-8",
        format="%(asctime)s %(module)s %(levelname)s %(message)s",
        level=logging.DEBUG,
    )

    import asyncio
    from pysui import PysuiConfiguration, client_factory

    async def main():
        """Main entry point for application."""
        cfg = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP)
        client = client_factory(cfg)
        # etc.

    if __name__ == "__main__":
        asyncio.run(main())
