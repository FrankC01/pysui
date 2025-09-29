#!/bin/bash
set -euo pipefail
# Copyright (c) Frank V. Castellucci
# License: Apache-2.0

# Setup target delivery

base_dir=${PWD##*/}
if test "$base_dir" = "pysui";
then
    echo "Publishing to testpypi"
    tout=$(twine check "dist/*")
    if echo $tout | grep -q "PASSED"; then
        echo "Valid build... uploading to pypi"
        tout=$(twine upload -r testpypi "dist/*")
        if echo $tout | grep -q "ERROR"; then
            echo "Publish failed. Fix errors and rerun"
            exit 1
        else
            echo "Upload passed!"
            exit 0
        fi
    fi
else
    echo "Command must run from pysui folder."
fi
