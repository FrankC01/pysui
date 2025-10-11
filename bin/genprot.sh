#! /bin/bash
set -euo pipefail
#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

base_dir=${PWD##*/}
if test "$base_dir" = "pysui";
then
    protoc -I./suiprot/ -I./suiprot/sui/rpc/v2beta2/ --python_betterproto2_opt=typing.310 --python_betterproto2_opt=client_generation=async --python_betterproto2_out=pysui/sui/sui_grpc/suimsgs ./suiprot/sui/rpc/v2beta2/*.proto    
    protoc -I./suiprot/ -I./suiprot/sui/rpc/v2/ --python_betterproto2_opt=typing.310 --python_betterproto2_opt=client_generation=async --python_betterproto2_out=pysui/sui/sui_grpc/suimsgs ./suiprot/sui/rpc/v2/*.proto    
else
    echo "Command must run from pysui folder."
fi
