#!/usr/bin/env bash
set -euo pipefail

# Clone/update bb-app on a target Pi and install service.
# Run from control host.
#
# Usage:
#   scripts/deploy_bb_app.sh <ssh_target> <git_repo_ssh> <secrets_dir> [git_ref] [deploy_dir] [repo_subdir]
#
# secrets_dir must contain:
#   config.py
#   service_account.json

SSH_TARGET="${1:-}"
GIT_REPO_SSH="${2:-}"
SECRETS_DIR="${3:-}"
GIT_REF="${4:-main}"
DEPLOY_DIR="${5:-/home/bb/bb-app}"
REPO_SUBDIR="${6:-}"
APP_DIR="${DEPLOY_DIR}"

if [[ -n "${REPO_SUBDIR}" ]]; then
  APP_DIR="${DEPLOY_DIR}/${REPO_SUBDIR}"
fi

REMOTE_CONFIG_DIR="${APP_DIR}/config"

if [[ -z "${SSH_TARGET}" || -z "${GIT_REPO_SSH}" || -z "${SECRETS_DIR}" ]]; then
  echo "Usage: $0 <ssh_target> <git_repo_ssh> <secrets_dir> [git_ref] [deploy_dir] [repo_subdir]" >&2
  exit 1
fi

if [[ ! -f "${SECRETS_DIR}/config.py" || ! -f "${SECRETS_DIR}/service_account.json" ]]; then
  echo "Secrets dir must contain config.py and service_account.json: ${SECRETS_DIR}" >&2
  exit 1
fi

echo "[1/6] Verifying deploy-key auth on ${SSH_TARGET}"
ssh "${SSH_TARGET}" "set -euo pipefail
  sudo -u bb test -f /home/bb/.ssh/id_ed25519_bb_app
  set +e
  auth_out=\$(sudo -u bb ssh -o BatchMode=yes -T git@\$(echo '${GIT_REPO_SSH}' | sed -E 's#.+@([^:/]+).*#\\1#') 2>&1)
  auth_rc=\$?
  set -e
  echo \"\$auth_out\"
  if [[ \$auth_rc -ne 0 && \$auth_rc -ne 1 ]]; then
    echo 'Git SSH authentication failed before clone/update.' >&2
    exit 1
  fi
"

echo "[2/6] Installing git if needed"
ssh "${SSH_TARGET}" "set -euo pipefail
  command -v git >/dev/null 2>&1 || { sudo apt-get update; sudo apt-get install -y git; }
"

echo "[3/6] Clone or update repository"
ssh "${SSH_TARGET}" "set -euo pipefail
  if [[ ! -d '${DEPLOY_DIR}/.git' ]]; then
    if [[ -n '${REPO_SUBDIR}' ]]; then
      sudo -u bb git clone --filter=blob:none --no-checkout '${GIT_REPO_SSH}' '${DEPLOY_DIR}'
      sudo -u bb git -C '${DEPLOY_DIR}' sparse-checkout init --cone
      sudo -u bb git -C '${DEPLOY_DIR}' sparse-checkout set '${REPO_SUBDIR}'
    else
      sudo -u bb git clone '${GIT_REPO_SSH}' '${DEPLOY_DIR}'
    fi
  fi

  if [[ -n '${REPO_SUBDIR}' ]]; then
    sudo -u bb git -C '${DEPLOY_DIR}' sparse-checkout init --cone
    sudo -u bb git -C '${DEPLOY_DIR}' sparse-checkout set '${REPO_SUBDIR}'
  fi

  sudo -u bb git -C '${DEPLOY_DIR}' fetch --tags --prune
  sudo -u bb git -C '${DEPLOY_DIR}' checkout '${GIT_REF}'
  sudo -u bb git -C '${DEPLOY_DIR}' pull --ff-only

  test -f '${APP_DIR}/bb-app-install.sh'
"

echo "[4/6] Pushing runtime secrets"
ssh "${SSH_TARGET}" "set -euo pipefail; sudo -u bb mkdir -p '${REMOTE_CONFIG_DIR}'"
scp "${SECRETS_DIR}/config.py" "${SSH_TARGET}:${REMOTE_CONFIG_DIR}/config.py"
scp "${SECRETS_DIR}/service_account.json" "${SSH_TARGET}:${REMOTE_CONFIG_DIR}/service_account.json"
ssh "${SSH_TARGET}" "set -euo pipefail
  sudo chown bb:bb '${REMOTE_CONFIG_DIR}/config.py' '${REMOTE_CONFIG_DIR}/service_account.json'
  sudo chmod 600 '${REMOTE_CONFIG_DIR}/config.py' '${REMOTE_CONFIG_DIR}/service_account.json'
"

echo "[5/6] Running installer"
ssh "${SSH_TARGET}" "set -euo pipefail
  cd '${APP_DIR}'
  chmod +x ./bb-app-install.sh
  ./bb-app-install.sh
"

echo "[6/6] Verifying service + recording deployed commit"
COMMIT="$(ssh "${SSH_TARGET}" "git -C '${DEPLOY_DIR}' rev-parse HEAD")"
TIMESTAMP="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
ssh "${SSH_TARGET}" "sudo systemctl is-enabled bb-app.service >/dev/null && sudo systemctl is-active bb-app.service >/dev/null"

echo "${TIMESTAMP},${SSH_TARGET},${COMMIT},ok" >> logs/deployments.log

echo "Deployment succeeded: ${SSH_TARGET} @ ${COMMIT}"
echo "Log entry appended to logs/deployments.log"
