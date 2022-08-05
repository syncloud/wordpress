#!/bin/bash

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )

if [[ -z "$1" ]]; then
    echo "usage $0 [start]"
    exit 1
fi

case $1 in
start)
    exec $DIR/php/bin/php-fpm.sh -y /var/snap/wordpress/current/config/php-fpm.conf -c /var/snap/wordpress/current/config/php.ini
    ;;
post-start)
    timeout 5 /bin/bash -c 'until [ -S /var/snap/wordpress/current/php.sock ]; do echo "waiting for /var/snap/wordpress/current/php.sock"; sleep 1; done'
    ;;
*)
    echo "not valid command"
    exit 1
    ;;
esac
