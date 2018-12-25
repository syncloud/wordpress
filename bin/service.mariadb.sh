#!/bin/bash -e

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )

if [[ -z "$1" ]]; then
    echo "usage $0 [start]"
    exit 1
fi

case $1 in
start)
    exec ${DIR}/mariadb/mysqld --basedir=$SNAP/mariadb --datadir=$SNAP_COMMON/database --plugin-dir=$SNAP/mariadb/lib/plugin --log-error=$SNAP_COMMON/log/mariadb.err.log --pid-file=$SNAP_COMMON/database/mariadb.pid
    ;;

*)
    echo "not valid command"
    exit 1
    ;;
esac