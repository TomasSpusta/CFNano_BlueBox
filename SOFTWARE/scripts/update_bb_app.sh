#!/usr/bin/env bash
set -euo pipefail

# Update existing bb-app checkout on target Pi using SSH Git key.
# Run from control host.
#
# Usage:
#   scripts/update_bb_app.sh <ssh_target> [git_ref] [deploy_dir] [repo_subdir]

SSH_TARGET="${1:-}"
GIT_REF="${2:-main}"
DEPLOY_DIR="${3:-/home/bb/bb-app}"
REPO_SUBDIR="${4:-}"
APP_DIR="${DEPLOY_DIR}"

if [[ -n "${REPO_SUBDIR}" ]]; then
  APP_DIR="${DEPLOY_DIR}/${REPO_SUBDIR}"
fi

if [[ -z "${SSH_TARGET}" ]]; then
  echo "Usage: $0 <ssh_target> [git_ref] [deploy_dir] [repo_subdir]" >&2
  exit 1
fi

echo "[1/4] Updating repository to ${GIT_REF}"
ssh "${SSH_TARGET}" "set -euo pipefail
  test -d '${DEPLOY_DIR}/.git'
  if [[ -n '${REPO_SUBDIR}' ]]; then
    sudo -u bb git -C '${DEPLOY_DIR}' sparse-checkout init --cone
    sudo -u bb git -C '${DEPLOY_DIR}' sparse-checkout set '${REPO_SUBDIR}'
  fi
  sudo -u bb git -C '${DEPLOY_DIR}' fetch --tags --prune
  sudo -u bb git -C '${DEPLOY_DIR}' checkout '${GIT_REF}'
  sudo -u bb git -C '${DEPLOY_DIR}' pull --ff-only
  test -f '${APP_DIR}/bb-app-install.sh'
"

echo "[2/4] Re-running installer"
ssh "${SSH_TARGET}" "set -euo pipefail
  cd '${APP_DIR}'
  ./bb-app-install.sh
"

echo "[3/4] Verifying service"
ssh "${SSH_TARGET}" "set -euo pipefail
  sudo systemctl is-enabled bb-app.service >/dev/null
  sudo systemctl is-active bb-app.service >/dev/null
"

echo "[4/4] Logging deployed commit"
COMMIT="$(ssh "${SSH_TARGET}" "git -C '${DEPLOY_DIR}' rev-parse HEAD")"
TIMESTAMP="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
echo "${TIMESTAMP},${SSH_TARGET},${COMMIT},ok" >> logs/deployments.log

echo "Update succeeded: ${SSH_TARGET} @ ${COMMIT}"
