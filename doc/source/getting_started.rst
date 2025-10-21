
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
    on the same machine: `Install Sui Readme <https://docs.sui.io/build/install#install-sui-binaries>`_.

    Specifically, the binaries are required if...

    * You want to use the publish Sui package builder, and/or...
    * You want to use the Sui generated configuration for keystores and active
      environents


#. Install pysui

    Regardless, you can install ``pysui`` from PyPi:

    ``pip install pysui``



#. Follow the steps in the section **First time instantiation** on the :doc:`PysuiConfiguration <pyconfig>` page.

  If you have not previously setup ``pysui``, this creates the base PysuiConfiguration for GraphQL
  and gRPC protocols.


#. Test install
    Having setup your environment, you can verify all is well with a sample
    scripts included in the ``pysui`` distribution. From the command line:

    * ``async-gas`` This will display Sui gas for each address found in the
      SUI configuration
    * ``wallet`` This emulates a number of the ``sui client ...`` operations
