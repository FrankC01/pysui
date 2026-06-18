zkLogin and SEAL Installation
==============================

The zkLogin and SEAL optional features require the ``pysui-crypto`` optional extension,
which provides Rust-backed cryptographic primitives via PyO3.

Installing
----------

With Rust installed, install pysui with the ``zklogin-seal`` extra::

    pip install pysui[zklogin-seal]

This pulls in ``pysui-crypto``, a pre-built native wheel. If you do not have Rust
installed, first download the appropriate wheel for your platform from the
`pysui-crypto Releases <https://github.com/Suitters/pysui-crypto>`_ page, then run
the ``pip install pysui[zklogin-seal]`` command above. If Rust (stable) is available,
the package will be compiled from source automatically when no pre-built wheel is found.

Requirements
------------

* Python 3.10.6+
* pysui 1.1.0 or later
* Rust (stable) — only required if building ``pysui-crypto`` from source

For zkLogin
-----------

zkLogin requires credentials from an OAuth2 provider. The example in this
documentation uses Google. To obtain Google credentials, go to the Google Cloud Console,
create a project, enable the **Google Identity** API, and under **Credentials** create
an **OAuth 2.0 Client ID** of type **Desktop app**. Download the
``client_secret_*.json`` file — this is the ``--credentials`` argument used in the
examples.

For SEAL
--------

SEAL requires on-chain key servers. Default testnet key servers are bundled in the
configuration written to ``~/.pysui/ZkSealConfig.json`` on first use. No additional
setup is needed to run the examples.

See :doc:`zklogin_seal_config` for details on managing key server configuration.
