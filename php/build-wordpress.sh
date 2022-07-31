#!/bin/bash -ex

DIR=/
BUILD_DIR=/

apt update
apt -y install patch

cd ${BUILD_DIR}/wordpress

patch -p0 < ${DIR}/patches/wp-load.patch

cd ${DIR}/build/

# cli
sed -i 's/;phar.readonly = On/phar.readonly = Off/g' /etc/php5/cli/php.ini
php wp-cli.phar --allow-root cli info
phar extract -f wp-cli.phar -i utils.php phar
cd phar/vendor/wp-cli/wp-cli/php
patch -p0 < ${DIR}/patches/wp-cli.patch

cd ${DIR}/build/
phar list -f wp-cli.phar -i utils.php
phar delete -f wp-cli.phar -e vendor/wp-cli/wp-cli/php/utils.php
phar add -f wp-cli.phar phar 
phar list -f wp-cli.phar -i utils.php

php wp-cli.phar --allow-root cli info

cp wp-cli.phar ${BUILD_DIR}/bin/wp-cli.phar

# ldap
cd ldap-login-for-intranet-sites
patch -p0 < ${DIR}/patches/ldap.patch
cd ..
mv ldap-login-for-intranet-sites ${BUILD_DIR}/wordpress/wp-content/plugins/

mv ${BUILD_DIR}/wordpress/wp-content ${BUILD_DIR}/wp-content.template
ln -sf /var/snap/wordpress/common/wp-content ${BUILD_DIR}/wordpress/wp-content