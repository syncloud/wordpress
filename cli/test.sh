#!/bin/bash -xe

DIR=$( cd "$( dirname "$0" )" && pwd )
BUILD_DIR=${DIR}/../build/snap

for hook in install configure pre-refresh post-refresh; do
    ${BUILD_DIR}/meta/hooks/${hook} --help
done
${BUILD_DIR}/bin/cli --help
