#!/bin/bash -ex

DIR=$( cd "$( dirname "$0" )" && pwd )
cd ${DIR}

BUILD_DIR=${DIR}/../build/snap/php
WORDPRESS_VERSION=$1
WORDPRESS_LDAP_VERSION=4.1.7
WORDPRESS_CLI_VERSION=2.8.1

apt update
apt -y install patch

mkdir ${DIR}/build

# wordpress
cd ${DIR}/build
wget https://wordpress.org/wordpress-${WORDPRESS_VERSION}.tar.gz --progress dot:giga
tar xf wordpress-${WORDPRESS_VERSION}.tar.gz
cd wordpress
patch -p0 < ${DIR}/patches/wp-load.patch
cd ..
mv wordpress ${BUILD_DIR}

# ldap
cd ${DIR}/build
wget https://downloads.wordpress.org/plugin/ldap-login-for-intranet-sites.${WORDPRESS_LDAP_VERSION}.zip --progress dot:giga
unzip ldap-login-for-intranet-sites.${WORDPRESS_LDAP_VERSION}.zip
cd ldap-login-for-intranet-sites
patch -p0 < ${DIR}/patches/ldap.patch
cd ..
mkdir ${BUILD_DIR}/wordpress/wp-content/mu-plugins
mv ldap-login-for-intranet-sites ${BUILD_DIR}/wordpress/wp-content/mu-plugins
cp $DIR/ldap-login-for-intranet-sites.php ${BUILD_DIR}/wordpress/wp-content/mu-plugins

# cli
cd ${DIR}/build
wget https://github.com/wp-cli/wp-cli/releases/download/v${WORDPRESS_CLI_VERSION}/wp-cli-${WORDPRESS_CLI_VERSION}.phar --progress dot:giga
mv wp-cli-${WORDPRESS_CLI_VERSION}.phar wp-cli.phar
#ls  /usr/local/etc/php
echo 'phar.readonly = Off' > /usr/local/etc/php/php.ini
#export PHP_INI_SCAN_DIR=php.ini
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

cp wp-cli.phar ${BUILD_DIR}/bin/wp-cli.phar

mv ${BUILD_DIR}/wordpress/wp-content ${BUILD_DIR}/wordpress/wp-content.template
ln -sf /var/snap/wordpress/common/wp-content ${BUILD_DIR}/wordpress/wp-content
