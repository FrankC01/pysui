
gRPC
""""

MystenLab has exposed a lower level data protcol using Google Protobuffs.
This change is part of the transitions from JSON RPC node interactions which
is planned to sunset in 2026.

``pysui`` has added support for interacting with the Sui gRPC node. This is
currently in beta and only available on testnet and mainnet.

At the time of this writing, there are limitations to Sui gRPC and only offers
simple data fetch and transaction execution interfaces.

====================
Subject to Change
====================

pysui's gRPC implementation, class names, etc. subject to change.
This implementation is not production ready and should
be considered experiemental.

===================
pysui gRPC services
===================

There are currently 2 gRPC services partially (testnet and mainnet only)
available in pysui:

#. Ledger
    Provides basic data query methods
#. Transaction
    Provides methods to submit transactions

These clients are encapsulated by the main pysui gRPC client.
See gRPC Requests for more details.



Notes:

#. All service clients are asynchronus
#. All gRPC calls return a ``SuiRpcResult``
#. All data results are of type ``dataclass``
