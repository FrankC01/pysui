#!/bin/bash
set -euo pipefail
# Copyright (c) Frank V. Castellucci
# License: Apache-2.0

# Setup target delivery

base_dir=${PWD##*/}
if test "$base_dir" = "pysui";
then
    echo "Publishing to PyPi"
    if twine check "dist/*"; then
        echo "Valid build... uploading to pypi"
        if twine upload "dist/*"; then
            echo "Upload passed!"
            exit 0
        else
            echo "Publish failed. Fix errors and rerun"
            exit 1
        fi
    fi
else
    echo "Command must run from pysui folder."
fi
