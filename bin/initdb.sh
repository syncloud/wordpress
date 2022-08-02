#!/bin/bash -e
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )

LIBS=${DIR}/mariadb/lib
LIBS=$LIBS:${DIR}/mariadb/usr/lib
exec ${DIR}/mariadb/lib/ld-musl-*.so* --library-path $LIBS ${DIR}/mariadb/usr/bin/mysql_install_db "$@"
