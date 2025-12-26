#!/bin/bash -e

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
export WP_CONFIG_DIR=$SNAP_DATA/config/wordpress
exec ${DIR}/php/bin/php.sh "$@"
