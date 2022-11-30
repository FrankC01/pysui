#!/bin/bash
# Copyright (c) Frank V. Castellucci
# License: Apache-2.0

# Generator preps and optionally delivers pysui and/or documentation

error_return() {
    echo "Error received during '$1' execution. Log:"
    while IFS= read line; do
        echo " $line "
    done <<< $2
}

doc_build() {
    echo "Building documentation"
    if docbuild=$(bin/doc-build.sh); then
        echo "Documentation built!"
    else
        error_return "build_doc" "$docbuild"
    fi
}

package_build() {
    echo "Building package"
    if distbuild=$(bin/package-build.sh); then
        echo "Package distribution built!"
    else
        error_return "package_build" "$distbuild"
    fi
}
package_publish_prod() {
    package_build
    echo "publishing package to production PyPi"
    if distpub=$(bin/package-publish.sh); then
        echo "Package distribution uploaded to pypi!"
    else
        error_return "package_publish" "$distpub"
    fi
}

package_publish_test() {
    # package_build
    echo "Publishing to testpypi"
    if distpubtest=$(bin/package-publish-test.sh); then
        echo "Package distribution uploaded to testpypi!"
    else
        error_return "package_publish_test" "$distpubtest"
    fi
}

build_all() {
    doc_build
    package_build
    package_publish_prod
    echo "All built and published!"
}
usage_help() {
    echo
    echo "Usage 'bin/generate.sh all | doc | build | pub-test | pub-prod"
    echo -e "\tall - Command builds pysui documentation, pysui distribution package and publishes to Production PyPi"
    echo -e "\tdoc - Command only builds pysui documentation and exits"
    echo -e "\tbuild - Command only builds pysui distribution package and exits"
    echo -e "\tpub-prod - Builds pysui distribution package and publishes to Production PyPi"
    echo -e "\tpub-test - Builds pysui distribution package and publishes to Test PyPi (i.e. twine upload -r testpypi ...)"
    echo
}

base_dir=${PWD##*/}
if test "$base_dir" = "pysui";
then
    if [ $# -eq 0 ]; then
        usage_help
    elif [ $# -ge 2 ]; then
        usage_help
    else
        case $1 in
            all)
                build_all
                ;;
            doc)
                doc_build
                ;;
            build)
                package_build
                ;;
            pub-prod)
                package_publish_prod
                ;;
            pub-test)
                package_publish_test
                ;;
            *)
                echo "Unknown command: $1"
                ;;
        esac
    fi
else
    echo "Command must run from pysui folder."
fi
