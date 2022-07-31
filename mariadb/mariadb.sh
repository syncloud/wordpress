#!/bin/bash -e
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )

LIBS=${DIR}/lib
LIBS=$LIBS:${DIR}/usr/lib
${DIR}/lib/ld-musl-*.so* --library-path $LIBS ${DIR}/usr/b8n/mysqld "$@"