#!/bin/bash -ex

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}
apt update
apt install -y libltdl7 libnss3

BUILD_DIR=${DIR}/../build/snap/mariadb
docker ps -a -q --filter ancestor=mariadb:syncloud --format="{{.ID}}" | xargs docker stop | xargs docker rm || true
docker rmi mariadb:syncloud || true
docker build -t mariadb:syncloud .
docker create --name=mariadb mariadb:syncloud
mkdir -p ${BUILD_DIR}
cd ${BUILD_DIR}
docker export mariadb -o app.tar
docker ps -a -q --filter ancestor=mariadb:syncloud --format="{{.ID}}" | xargs docker stop | xargs docker rm || true
docker rmi mariadb:syncloud || true
tar xf app.tar
rm -rf app.tar
cp ${DIR}/mariadb.sh ${BUILD_DIR}/bin/
mv ${BUILD_DIR}/usr/bin/resolveip ${BUILD_DIR}/usr/bin/resolveip.bin
cp ${DIR}/resolveip ${BUILD_DIR}/usr/bin