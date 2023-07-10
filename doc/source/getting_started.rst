
Getting Started
###############

Whether you are writing a new client application, extending pysui, or both,
there are a few setup steps required:

Setup
*****

#. Install Sui Binaries
    For certain capabilities, ``pysui`` requires the Sui binaries are installed
    on the same machine: `Install Sui Readme <https://docs.sui.io/build/install#install-sui-binaries>`_.

    Specifically, the binaries are required if...

    * You want to use the publish SUi package builder, and/or...
    * You want to use the Sui generated configuration



#. Install pysui
    While not required, it is common to create Python virtual environments and then
    install packages from PyPi.

    Regardless, you can install ``pysui`` from PyPi:

    ``pip install pysui``

#. Test install
    Having setup your environment, you can verify all is well with a sample scripts
    included in the ``pysui`` distribution. From the command line:

    * ``async-gas`` This will display Sui gas for each address found in the SUI configuration
    * ``async-sub`` This runs a sample event subscription
    * ``async-sub-txn`` This runs a sample transaction subscription
    * ``wallet`` This emulates a number of the ``sui client ...`` operations