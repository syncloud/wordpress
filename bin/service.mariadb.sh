#!/bin/bash -e

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )

if [[ -z "$1" ]]; then
    echo "usage $0 [start]"
    exit 1
fi


case $1 in
start)
    export MYSQL_HOME=/var/snap/wordpress/current/config
    exec ${DIR}/mariadb/usr/bin/mysqld --basedir=$SNAP/mariadb/usr --datadir=$SNAP_COMMON/database --plugin-dir=$SNAP/mariadb/lib/plugin --pid-file=$SNAP_COMMON/database/mariadb.pid
    ;;

*)
    echo "not valid command"
    exit 1
    ;;
esac
