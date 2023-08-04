#!/bin/sh -ex

DIR=$( cd "$( dirname "$0" )" && pwd )
cd ${DIR}

BUILD_DIR=${DIR}/../build/snap/mariadb
while ! docker build -t mariadb:syncloud . ; do
  echo "retry docker"
  sleep 3
done
docker create --name=mariadb mariadb:syncloud
mkdir -p ${BUILD_DIR}
cd ${BUILD_DIR}
docker export mariadb -o app.tar
tar xf app.tar
rm -rf app.tar
mv ${BUILD_DIR}/usr/bin/resolveip ${BUILD_DIR}/usr/bin/resolveip.bin
mv ${BUILD_DIR}/usr/bin/my_print_defaults ${BUILD_DIR}/usr/bin/my_print_defaults.bin
mv ${BUILD_DIR}/usr/bin/mysqld ${BUILD_DIR}/usr/bin/mysqld.bin
mv ${BUILD_DIR}/usr/bin/mysql ${BUILD_DIR}/usr/bin/mysql.bin
cp ${DIR}/bin/* ${BUILD_DIR}/usr/bin

