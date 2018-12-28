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
WORDPRESS_VERSION=5.0.1
ARCH=$(uname -m)
SNAP_ARCH=$(dpkg --print-architecture)
VERSION=$2

DOWNLOAD_URL=http://artifact.syncloud.org/3rdparty

apt install -y php-cli

rm -rf ${DIR}/build
BUILD_DIR=${DIR}/build/${NAME}
mkdir -p ${BUILD_DIR}

cd ${DIR}/build

coin --to ${BUILD_DIR} raw ${DOWNLOAD_URL}/nginx-${ARCH}.tar.gz
coin --to ${BUILD_DIR} raw ${DOWNLOAD_URL}/mariadb-${ARCH}.tar.gz
coin --to ${BUILD_DIR} raw ${DOWNLOAD_URL}/php7-${ARCH}.tar.gz
coin --to ${BUILD_DIR} raw ${DOWNLOAD_URL}/python-${ARCH}.tar.gz

mv ${BUILD_DIR}/php7 ${BUILD_DIR}/php

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
wget https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar

cd ${BUILD_DIR}/bin
phar extract -f wp-cli.phar phar
rm wp-cli.phar
cd phar/vendor/wp-cli/wp-cli/php
patch -p0 < ${DIR}/patches/wp-cli.patch
cd ${BUILD_DIR}/bin
phar pack -f wp-cli.phar phar/*
cp wp-cli.phar ${BUILD_DIR}/bin/wp-cli.phar

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
