
Logging
#######

The ``pysui`` package has logging enabled. However; it is up to the application(s) using the SDK
to setup logging configuration. If this is not done, ``pysui`` logging information is lost.

Module Logging
--------------

Select ``pysui`` modules are setup for logging and have the following construct:

.. code-block:: Python

    logger = logging.getLogger("pysui.MODULE_NAME")
    if not logging.getLogger().handlers:
        logger.addHandler(logging.NullHandler())
        logger.propagate = False

As you can see, if a root logger is not setup, ``pysui`` log messages go to the NullHandler (no-op)

With this construct, the root logger (in application) **must** be configured prior to the
inclusion of ``pysui`` modules. For example:

.. code-block:: Python

    import logging

    logging.basicConfig(
        filename="myapplication.log",
        filemode="w",
        encoding="utf-8",
        format="%(asctime)s %(module)s %(levelname)s %(message)s",
        level=logging.DEBUG,
    )

    from pysui.sui.sui_config import SuiConfig
    from pysui.sui.sui_clients.sync_client import SuiClient

    def main():
        """Main entry point for application."""
        client = SuiClient(SuiConfig.default_config())

        # etc.

    if __name__ == "__main__":
        main()


Log Enabled Modules
-------------------

Not every module in ``pysui`` is log enabled and adding logging and logging messages is an ongoing effort. The
following have been enabled and have various degrees of logging messages:

+------------------------------------+
|     Module                         |
+====================================+
| pysui.sui.sui_config               |
+------------------------------------+
| pysui.sui.sui_clients.sync_client  |
+------------------------------------+
| pysui.sui.sui_clients.async_client |
+------------------------------------+
| pysui.sui.sui_clients.subscribe    |
+------------------------------------+
| pysui.sui.sui_clients.transaction  |
+------------------------------------+
