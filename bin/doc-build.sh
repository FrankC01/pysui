#!/bin/bash
# Copyright (c) Frank V. Castellucci
# License: Apache-2.0


base_dir=${PWD##*/}
if test "$base_dir" = "pysui";
then
    echo "Removing previous documentation artifacts... if any!"
    # Delete old (if any) rst files
    for X in doc/source/*.rst; do
        if [ "$X" != "doc/source/index.rst" ]; then
            rm $X
        fi
    done
    # Generate rst files
    echo "Generating rst files"
    sphinx-apidoc -o doc/source pysui/
    # Generate html docs
    cd doc
    echo "Building HTML"
    gen_html=$(make html)
    cd ..
    if echo $gen_html | grep -q "build succeeded"; then
        echo "Docs build success"
        exit 0
    else
        echo $gen_html
        echo "Fix errors and rerun"
        exit -1
    fi
else
    echo "Command must run from pysui folder."
fi
