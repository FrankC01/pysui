#!/bin/bash
set -euo pipefail
# Copyright (c) Frank V. Castellucci
# License: Apache-2.0


base_dir=${PWD##*/}
if test "$base_dir" = "pysui";
then
    echo "Removing previous documentation artifacts... if any!"
    # Delete old (if any) rst files
    rm -f -- doc/source/modules.rst
    rm -f -- doc/source/pysui.rst
    rm -f -- doc/source/pysui.abstracts.rst
    rm -f -- doc/source/pysui.sui.rst
    rm -f -- doc/source/pysui.sui.sui_txresults.rst
    rm -f -- doc/source/pysui.sui.sui_builders.rst
    rm -f -- doc/source/pysui.sui.sui_clients.rst
    rm -f -- doc/source/pysui.sui.sui_types.rst
    # Generate rst files
    echo "Generating rst files"
    sphinx-apidoc -o doc/source pysui/
    # Generate html docs
    cd doc
    echo "Building HTML"
    if make html >/dev/null 2>&1; then
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
