#!/bin/bash -ex

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}

if [[ -z "$2" ]]; then
    echo "usage $0 app version"
    exit 1
fi

export TMPDIR=/tmp
export TMP=/tmp

NAME=$1
WORDPRESS_VERSION=5.7.1
WORDPRESS_LDAP_VERSION=3.6.4
WORDPRESS_CLI_VERSION=2.4.0
ARCH=$(uname -m)
SNAP_ARCH=$(dpkg --print-architecture)
VERSION=$2

rm -rf ${DIR}/build
BUILD_DIR=${DIR}/build/${NAME}
mkdir -p ${BUILD_DIR}

cd ${DIR}/build

wget --progress=dot:giga https://github.com/syncloud/3rdparty/releases/download/1/nginx-${ARCH}.tar.gz
tar xf nginx-${ARCH}.tar.gz
mv nginx ${BUILD_DIR}
wget --progress=dot:giga https://github.com/syncloud/3rdparty/releases/download/1/mariadb-${ARCH}.tar.gz
tar xf mariadb-${ARCH}.tar.gz
mv mariadb ${BUILD_DIR}
wget --progress=dot:giga https://github.com/syncloud/3rdparty/releases/download/1/php7-${ARCH}.tar.gz
tar xf php7-${ARCH}.tar.gz
mv php7 ${BUILD_DIR}/php
wget --progress=dot:giga https://github.com/syncloud/3rdparty/releases/download/1/python3-${ARCH}.tar.gz
tar xf python3-${ARCH}.tar.gz
mv python3 ${BUILD_DIR}/python

${BUILD_DIR}/python/bin/pip install -r ${DIR}/requirements.txt

cd ${DIR}/build
wget https://wordpress.org/wordpress-${WORDPRESS_VERSION}.tar.gz --progress dot:giga
tar xf wordpress-${WORDPRESS_VERSION}.tar.gz -C ${BUILD_DIR}
cd ${BUILD_DIR}/wordpress

patch -p0 < ${DIR}/patches/wp-load.patch

cd ${DIR}

cp -r ${DIR}/bin ${BUILD_DIR}
cp -r ${DIR}/config ${BUILD_DIR}/config.templates
cp -r ${DIR}/hooks ${BUILD_DIR}

cd ${DIR}/build/
wget https://github.com/wp-cli/wp-cli/releases/download/v${WORDPRESS_CLI_VERSION}/wp-cli-${WORDPRESS_CLI_VERSION}.phar --progress dot:giga
mv wp-cli-${WORDPRESS_CLI_VERSION}.phar wp-cli.phar
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

wget https://downloads.wordpress.org/plugin/ldap-login-for-intranet-sites.${WORDPRESS_LDAP_VERSION}.zip --progress dot:giga
unzip ldap-login-for-intranet-sites.${WORDPRESS_LDAP_VERSION}.zip
cd ldap-login-for-intranet-sites
patch -p0 < ${DIR}/patches/ldap.patch
cd ..
mv ldap-login-for-intranet-sites ${BUILD_DIR}/wordpress/wp-content/plugins/

mv ${BUILD_DIR}/wordpress/wp-content ${BUILD_DIR}/wp-content.template
ln -sf /var/snap/wordpress/common/wp-content ${BUILD_DIR}/wordpress/wp-content
mkdir ${DIR}/build/${NAME}/META
echo ${NAME} >> ${DIR}/build/${NAME}/META/app
echo ${VERSION} >> ${DIR}/build/${NAME}/META/version

echo "snapping"
SNAP_DIR=${DIR}/build/snap
ARCH=$(dpkg-architecture -q DEB_HOST_ARCH)
rm -rf ${DIR}/*.snap
mkdir ${SNAP_DIR}
cp -r ${BUILD_DIR}/* ${SNAP_DIR}/
cp -r ${DIR}/snap/meta ${SNAP_DIR}/
cp ${DIR}/snap/snap.yaml ${SNAP_DIR}/meta/snap.yaml
echo "version: $VERSION" >> ${SNAP_DIR}/meta/snap.yaml
echo "architectures:" >> ${SNAP_DIR}/meta/snap.yaml
echo "- ${ARCH}" >> ${SNAP_DIR}/meta/snap.yaml

PACKAGE=${NAME}_${VERSION}_${ARCH}.snap
echo ${PACKAGE} > ${DIR}/package.name
mksquashfs ${SNAP_DIR} ${DIR}/${PACKAGE} -noappend -comp xz -no-xattrs -all-root

