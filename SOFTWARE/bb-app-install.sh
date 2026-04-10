#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="bb-app.service"
SERVICE_PATH="/etc/systemd/system/${SERVICE_NAME}"
SERVICE_USER="bb"
SERVICE_GROUP="bb"
REBOOT_REQUIRED=0

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/.venv"
PYTHON_BIN="${VENV_DIR}/bin/python"
PIP_BIN="${VENV_DIR}/bin/pip"
ENTRYPOINT="${SCRIPT_DIR}/bb-app-main.py"
REQUIREMENTS_FILE="${SCRIPT_DIR}/requirements.txt"
APT_PACKAGES=(
  python3
  python3-venv
  python3-pip
  python3-smbus
  python3-rpi.gpio
  python3-spidev
  i2c-tools
  build-essential
)

enable_interface() {
  local iface="$1"
  local get_cmd="get_${iface}"
  local set_cmd="do_${iface}"
  local before=""

  if sudo raspi-config nonint "${get_cmd}" >/dev/null 2>&1; then
    before="$(sudo raspi-config nonint "${get_cmd}")"
  fi

  sudo raspi-config nonint "${set_cmd}" 0

  if [[ -n "${before}" && "${before}" != "0" ]]; then
    REBOOT_REQUIRED=1
  elif [[ -z "${before}" ]]; then
    # Conservative default if prior state cannot be read.
    REBOOT_REQUIRED=1
  fi
}

if [[ ! -f "${ENTRYPOINT}" ]]; then
  echo "Entrypoint not found: ${ENTRYPOINT}" >&2
  exit 1
fi

if [[ ! -f "${REQUIREMENTS_FILE}" ]]; then
  echo "Requirements file not found: ${REQUIREMENTS_FILE}" >&2
  exit 1
fi

echo "Installing system dependencies with apt"
sudo apt-get update
sudo apt-get install -y "${APT_PACKAGES[@]}"

echo "Ensuring ${SERVICE_USER} belongs to gpio/i2c/spi groups"
for group in gpio i2c spi; do
  if id -nG "${SERVICE_USER}" | grep -qw "${group}"; then
    echo "User ${SERVICE_USER} already in group ${group}"
  else
    sudo usermod -aG "${group}" "${SERVICE_USER}"
    echo "Added ${SERVICE_USER} to ${group}"
    REBOOT_REQUIRED=1
  fi
done

if command -v raspi-config >/dev/null 2>&1; then
  echo "Enabling Raspberry Pi interfaces (I2C/SPI)"
  enable_interface "i2c"
  enable_interface "spi"
else
  echo "raspi-config not found, skipping I2C/SPI auto-enable" >&2
  echo "Install raspi-config or enable I2C/SPI manually." >&2
fi

echo "Creating virtual environment in ${VENV_DIR}"
python3 -m venv "${VENV_DIR}"

"${PIP_BIN}" install --upgrade pip
"${PIP_BIN}" install -r "${REQUIREMENTS_FILE}"

echo "Running preflight dependency checks"
python3 -c "import smbus; print('System smbus import OK')"
python3 -c "import RPi.GPIO; print('System RPi.GPIO import OK')"
"${PYTHON_BIN}" -c "import smbus2; print('Venv smbus2 import OK')"
"${PYTHON_BIN}" -c "from RPLCD.i2c import CharLCD; print('RPLCD CharLCD import OK')"

if sudo systemctl cat "${SERVICE_NAME}" 2>/dev/null | grep -q "GPIOZERO_PIN_FACTORY="; then
  echo "Warning: Existing ${SERVICE_NAME} has GPIOZERO_PIN_FACTORY override."
  echo "This deployment expects default gpiozero backend (rpigpio)." >&2
fi

echo "Installing ${SERVICE_NAME} to ${SERVICE_PATH}"
sudo tee "${SERVICE_PATH}" >/dev/null <<SERVICE_EOF
[Unit]
Description=Bluebox App Service
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
User=${SERVICE_USER}
Group=${SERVICE_GROUP}
WorkingDirectory=${SCRIPT_DIR}
ExecStart=${PYTHON_BIN} ${ENTRYPOINT}
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
SERVICE_EOF

sudo systemctl daemon-reload
sudo systemctl enable --now "${SERVICE_NAME}"

echo
echo "Installation completed."
echo "Check service status with: sudo systemctl status ${SERVICE_NAME}"
echo "Follow logs with: sudo journalctl -u ${SERVICE_NAME} -f"

if [[ "${REBOOT_REQUIRED}" -eq 1 ]]; then
  echo
  echo "A reboot is required for interface/group changes to fully apply."
  if [[ -t 0 ]]; then
    read -r -p "Reboot now? [y/N]: " reply
    if [[ "${reply}" =~ ^[Yy]$ ]]; then
      sudo reboot
    else
      echo "Please reboot manually before relying on hardware access."
    fi
  else
    echo "Non-interactive shell detected. Please reboot manually."
  fi
fi
