#!/bin/bash
set -euo pipefail
# Copyright (c) Frank V. Castellucci
# License: Apache-2.0


base_dir=${PWD##*/}
if test "$base_dir" = "pysui";
then
    echo "Removing previous documentation artifacts... if any!"
    rm -f doc/source/pysui*.rst doc/source/modules.rst

    echo "Generating QueryNode and Request table RSTs"
    python3 gen_doc_qnode.py
    python3 gen_doc_reqs.py

    echo "Generating module RSTs"
    sphinx-apidoc -o doc/source pysui/ pysui/sui/sui_grpc/suimsgs

    cd doc
    echo "Building HTML"
    if make html; then
        echo "Docs build success"
        cd ..
        exit 0
    else
        echo "Build failed"
        cd ..
        exit 1
    fi
else
    echo "Command must run from pysui folder."
fi
