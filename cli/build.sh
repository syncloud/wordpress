#!/bin/bash -e

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd "${DIR}"

BUILD_DIR=${DIR}/../build/snap
mkdir -p "${BUILD_DIR}/meta/hooks" "${BUILD_DIR}/bin"

go test ./...

for hook in install configure pre-refresh post-refresh; do
    CGO_ENABLED=0 go build -o "${BUILD_DIR}/meta/hooks/${hook}" "./cmd/${hook}"
done
CGO_ENABLED=0 go build -o "${BUILD_DIR}/bin/cli" ./cmd/cli
