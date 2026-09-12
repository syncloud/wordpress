#!/bin/bash -e
# usage: run.sh <artifact-subdir> <spec>
DIR=$(cd "$(dirname "$0")" && pwd)
cd "$DIR"

ARTIFACT_SUBDIR=$1
SPEC=$2

export PLAYWRIGHT_FULL_DOMAIN=${PLAYWRIGHT_FULL_DOMAIN:-bookworm.com}
export PLAYWRIGHT_APP_DOMAIN=${PLAYWRIGHT_APP_DOMAIN:-wordpress.${PLAYWRIGHT_FULL_DOMAIN}}
export PLAYWRIGHT_DEVICE_HOST=${PLAYWRIGHT_DEVICE_HOST:-${PLAYWRIGHT_APP_DOMAIN}}
export PLAYWRIGHT_DEVICE_USER=${PLAYWRIGHT_DEVICE_USER:-user}
export PLAYWRIGHT_DEVICE_PASSWORD=${PLAYWRIGHT_DEVICE_PASSWORD:-Password1}
export PLAYWRIGHT_SSH_USER=${PLAYWRIGHT_SSH_USER:-root}
export PLAYWRIGHT_SSH_PASSWORD=${PLAYWRIGHT_SSH_PASSWORD:-Password1}
export PLAYWRIGHT_PROJECT=${PLAYWRIGHT_PROJECT:-desktop}
export PLAYWRIGHT_ARTIFACT_DIR=/drone/src/artifact/${ARTIFACT_SUBDIR}

"${DIR}/../../ci/apt.sh" sshpass openssh-client curl
"${DIR}/wait-app.sh" "${PLAYWRIGHT_APP_DOMAIN}"
npm ci --no-audit --no-fund
npx playwright test --project=desktop "$SPEC"
