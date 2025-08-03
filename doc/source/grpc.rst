
====
gRPC
====

MystenLab has exposed a lower level data protocol using Google Protobuffs.
This change is part of the transitions from JSON RPC node interactions which
is planned to sunset in 2026.

``pysui`` has added support for interacting with the Sui gRPC node. This is
currently in beta and is available on devnet, testnet and mainnet. However;
devnet is not fully supported at this time.

Subject to Change
--------------------

pysui's gRPC implementation, class names, etc. subject to change.
This implementation is not production ready and should
be considered experiemental.

pysui gRPC services
--------------------

Mysten Labs exposed the following  `Services  <https://docs.sui.io/concepts/grpc-overview#grpc-on-sui>`_

Notes:

#. All service clients are asynchronus
#. All gRPC calls return a ``SuiRpcResult``
#. All data results are of type ``dataclass``
