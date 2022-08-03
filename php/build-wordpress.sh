#!/bin/bash -ex

DIR=/
BUILD_DIR=/build
OUT_DIR=/
apt update
apt -y install patch

# ldap
cd ${DIR}/build
cd ldap-login-for-intranet-sites
patch -p0 < ${DIR}/patches/ldap.patch
cd ..
mv ldap-login-for-intranet-sites ${BUILD_DIR}/wordpress/wp-content/plugins

# wordpress
cd ${BUILD_DIR}/wordpress
patch -p0 < ${DIR}/patches/wp-load.patch
mv ${BUILD_DIR}/wordpress/wp-content ${BUILD_DIR}/wordpress/wp-content.template
ln -sf /var/snap/wordpress/common/wp-content ${BUILD_DIR}/wordpress/wp-content
mv ${BUILD_DIR}/wordpress ${OUT_DIR}

# cli
cd ${DIR}/build
ls  /usr/local/etc/php
echo 'phar.readonly = Off' > /usr/local/etc/php/conf.d/php.ini
php wp-cli.phar --allow-root cli info
phar extract -f wp-cli.phar -i utils.php phar
cd phar/vendor/wp-cli/wp-cli/php
patch -p0 < ${DIR}/patches/wp-cli.patch

cd ${DIR}/build
phar list -f wp-cli.phar -i utils.php
phar delete -f wp-cli.phar -e vendor/wp-cli/wp-cli/php/utils.php
phar add -f wp-cli.phar phar 
phar list -f wp-cli.phar -i utils.php

php wp-cli.phar --allow-root cli info

cp wp-cli.phar ${OUT_DIR}/bin/wp-cli.phar

