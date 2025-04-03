#! /bin/bash

#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

base_dir=${PWD##*/}
if test "$base_dir" = "pysui";
then
    protoc -I./suiprot/ -I./suiprot/sui/types/ -I./suiprot/sui/node/v2/ --python_betterproto_opt=typing.310 --python_betterproto_out=pysui/sui/sui_grpc/suimsgs node_service.proto
    protoc -I./suiprot/ -I./suiprot/sui/types/ -I./suiprot/sui/rpc/v2beta/ --python_betterproto_opt=typing.310 --python_betterproto_out=pysui/sui/sui_grpc/suimsgs ./suiprot/sui/rpc/v2beta/*.proto

else
    echo "Command must run from pysui folder."
fi
