#!/bin/bash
# Copyright (c) Frank V. Castellucci
# License: Apache-2.0

# Setup target delivery
repo=""
if test "$1" = "test";
then
    repo="-r testpypi "
else
    repo=""
fi

base_dir=${PWD##*/}
if test "$base_dir" = "pysui";
then
    echo "Removing previous build artifacts... if any!"
    rm -rf "build"
    rm -rf "dist"
    rm -rf "pysui.egg-info"
    echo "Building pysui....."
    python3 -m build . --wheel
    tout=$(twine check "dist/*")
    if echo $tout | grep -q "PASSED"; then
        echo "Valid build... uploading to pypi"
        tout=$(twine upload ${repo} "dist/*")
        if echo $tout | grep -q "ERROR"; then
            echo "Failed upload..."
            echo $tout
        else
            echo "Upload passed!"
        fi
    fi
else
    echo "Command must run from pysui folder."
fi
