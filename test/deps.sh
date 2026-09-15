#!/bin/bash -e

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
"${DIR}/../ci/apt.sh" sshpass openssh-client wget
pip install -q -r "${DIR}/requirements.txt"
