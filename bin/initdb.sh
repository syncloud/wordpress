#!/bin/bash -e

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )

export LD_LIBRARY_PATH=${DIR}/mariadb/lib

exec ${DIR}/mariadb/scripts/mysql_install_db "$@"
 