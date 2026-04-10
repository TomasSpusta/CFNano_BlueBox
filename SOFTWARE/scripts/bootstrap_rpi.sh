#!/usr/bin/env bash
set -euo pipefail

# Bootstrap a Raspberry Pi for bb-app Git-over-SSH deployments.
# Run from control host.
#
# Usage:
#   scripts/bootstrap_rpi.sh <ssh_target> [git_host]
#
# Example:
#   scripts/bootstrap_rpi.sh bb@100.66.18.133 github.com

SSH_TARGET="${1:-}"
GIT_HOST="${2:-github.com}"
REMOTE_KEY_PATH="/home/bb/.ssh/id_ed25519_bb_app"

if [[ -z "${SSH_TARGET}" ]]; then
  echo "Usage: $0 <ssh_target> [git_host]" >&2
  exit 1
fi

echo "[1/4] Preparing ~/.ssh on ${SSH_TARGET}"
ssh "${SSH_TARGET}" "set -euo pipefail
  mkdir -p /home/bb/.ssh
  chmod 700 /home/bb/.ssh
  chown bb:bb /home/bb/.ssh
"

echo "[2/4] Creating deploy key if missing"
ssh "${SSH_TARGET}" "set -euo pipefail
  if [[ ! -f '${REMOTE_KEY_PATH}' ]]; then
    sudo -u bb ssh-keygen -t ed25519 -N '' -f '${REMOTE_KEY_PATH}' -C 'bb-app@$(hostname)'
  fi
  sudo -u bb chmod 600 '${REMOTE_KEY_PATH}'
  sudo -u bb chmod 644 '${REMOTE_KEY_PATH}.pub'
"

echo "[3/4] Writing SSH config and known_hosts for ${GIT_HOST}"
ssh "${SSH_TARGET}" "set -euo pipefail
  sudo -u bb touch /home/bb/.ssh/known_hosts
  sudo -u bb chmod 600 /home/bb/.ssh/known_hosts
  sudo -u bb ssh-keyscan -H '${GIT_HOST}' >> /home/bb/.ssh/known_hosts 2>/dev/null || true

  cat > /tmp/bb_app_ssh_config <<CFG
Host ${GIT_HOST}
  HostName ${GIT_HOST}
  User git
  IdentityFile ${REMOTE_KEY_PATH}
  IdentitiesOnly yes
  StrictHostKeyChecking yes
CFG
  sudo mv /tmp/bb_app_ssh_config /home/bb/.ssh/config
  sudo chown bb:bb /home/bb/.ssh/config
  sudo chmod 600 /home/bb/.ssh/config
"

echo "[4/4] Key details + Git SSH auth check"
ssh "${SSH_TARGET}" "set -euo pipefail
  echo '--- Public key (add this as READ-ONLY deploy key) ---'
  sudo -u bb cat '${REMOTE_KEY_PATH}.pub'
  echo '--- Fingerprint ---'
  sudo -u bb ssh-keygen -lf '${REMOTE_KEY_PATH}.pub'
  echo '--- Auth probe (expected to fail until key is added to provider) ---'
  set +e
  sudo -u bb ssh -o BatchMode=yes -T git@'${GIT_HOST}'
  rc=\$?
  set -e
  if [[ \$rc -eq 0 || \$rc -eq 1 ]]; then
    echo 'Git host reachable. If key is registered, auth text should confirm.'
  else
    echo 'Git auth probe returned rc='\$rc
  fi
"

echo
echo "Bootstrap finished for ${SSH_TARGET}."
echo "Next: add the printed public key to your Git provider as read-only deploy key."
