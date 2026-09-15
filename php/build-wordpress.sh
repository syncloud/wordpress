#!/bin/bash -ex

DIR=$( cd "$( dirname "$0" )" && pwd )
cd ${DIR}

BUILD_DIR=${DIR}/../build/snap/php
WORDPRESS_VERSION=$1
WORDPRESS_OIDC_VERSION=$2
WORDPRESS_CLI_VERSION=$3

${DIR}/../ci/apt.sh unzip wget ca-certificates

mkdir ${DIR}/build

# wordpress
cd ${DIR}/build
wget https://wordpress.org/wordpress-${WORDPRESS_VERSION}.tar.gz --progress dot:giga
tar xf wordpress-${WORDPRESS_VERSION}.tar.gz
mv wordpress ${BUILD_DIR}
ln -sf /var/snap/wordpress/current/config/wordpress/wp-config.php ${BUILD_DIR}/wordpress/wp-config.php

# openid connect
cd ${DIR}/build
${DIR}/../ci/download.sh \
    https://downloads.wordpress.org/plugin/daggerhart-openid-connect-generic.${WORDPRESS_OIDC_VERSION}.zip \
    oidc.zip
unzip oidc.zip
mkdir ${BUILD_DIR}/wordpress/wp-content/mu-plugins
mv daggerhart-openid-connect-generic ${BUILD_DIR}/wordpress/wp-content/mu-plugins
cp $DIR/openid-connect-generic.php ${BUILD_DIR}/wordpress/wp-content/mu-plugins

# cli
cd ${DIR}/build
wget https://github.com/wp-cli/wp-cli/releases/download/v${WORDPRESS_CLI_VERSION}/wp-cli-${WORDPRESS_CLI_VERSION}.phar --progress dot:giga
mv wp-cli-${WORDPRESS_CLI_VERSION}.phar wp-cli.phar
#ls  /usr/local/etc/php
php wp-cli.phar --allow-root cli info
cp wp-cli.phar ${BUILD_DIR}/bin/wp-cli.phar

mv ${BUILD_DIR}/wordpress/wp-content ${BUILD_DIR}/wordpress/wp-content.template
ln -sf /var/snap/wordpress/common/wp-content ${BUILD_DIR}/wordpress/wp-content
