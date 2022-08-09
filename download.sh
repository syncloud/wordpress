#!/bin/bash -xe

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
DOWNLOAD_URL=https://github.com/syncloud/3rdparty/releases/download
WORDPRESS_VERSION=6.0.1
WORDPRESS_LDAP_VERSION=4.0
WORDPRESS_CLI_VERSION=2.6.0
ARCH=$(uname -m)
rm -rf ${DIR}/build
BUILD_DIR=${DIR}/build/snap
mkdir -p ${BUILD_DIR}

cd ${DIR}/build

apt update
apt -y install wget unzip

wget --progress=dot:giga ${DOWNLOAD_URL}/nginx/nginx-${ARCH}.tar.gz
tar xf nginx-${ARCH}.tar.gz
mv nginx ${BUILD_DIR}

mkdir $DIR/php/build

wget https://wordpress.org/wordpress-${WORDPRESS_VERSION}.tar.gz --progress dot:giga
tar xf wordpress-${WORDPRESS_VERSION}.tar.gz
mv wordpress $DIR/php/build

wget https://github.com/wp-cli/wp-cli/releases/download/v${WORDPRESS_CLI_VERSION}/wp-cli-${WORDPRESS_CLI_VERSION}.phar --progress dot:giga
mv wp-cli-${WORDPRESS_CLI_VERSION}.phar $DIR/php/build/wp-cli.phar

wget https://downloads.wordpress.org/plugin/ldap-login-for-intranet-sites.${WORDPRESS_LDAP_VERSION}.zip --progress dot:giga
unzip ldap-login-for-intranet-sites.${WORDPRESS_LDAP_VERSION}.zip
mv ldap-login-for-intranet-sites $DIR/php/build
