# Bluebox Software

Async Python control software for a hardware reservation terminal:
- reads RFID cards
- controls a 20x4 I2C LCD
- handles GPIO buttons for stop/extend actions
- calls backend APIs for user/reservation flow
- writes operational logs to Google Sheets

## Overview

Main execution starts in `main.py` and runs an async state machine from `states/`.

State flow:
1. `InitState`
2. `WaitingForCardState`
3. `VerifyUserState`
4. `VerifyReservationState`
5. `InReservationState`
6. `UserStopReservationState` or `ExtendReservationState` or `TimeOutState`
7. Back to `WaitingForCardState`

## Repository Structure

- `main.py`: app bootstrap and dependency wiring
- `app_context.py`: shared runtime context passed between states
- `states/`: state machine implementation
- `api_client.py`: backend API integration
- `networking.py`: connectivity checks + safe API wrapper
- `token_handler.py`: token persistence/refresh logic
- `rfid_reader.py`: MFRC522 card reader abstraction
- `lcd_display.py`: LCD adapter
- `screen_manager.py`: LCD screen text templates
- `button_watcher.py`: GPIO button hold detection
- `logger.py`: Google Sheets logging
- `model_classes.py`: domain data models
- `requirements.txt`: Python dependencies
- `improvements.md`: architecture improvement roadmap

## Requirements

Hardware/runtime expectations:
- Raspberry Pi (or compatible Linux SBC)
- MFRC522 RFID reader
- 20x4 I2C LCD with PCF8574 backpack
- 2 GPIO buttons (stop/extend)
- Internet connection for backend + Google Sheets logging

Software:
- Python 3.11+ recommended
- System access to GPIO, I2C, SPI as required by your OS image

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuration

`config/*` is ignored in git. Create local config files manually.

Create `config/config.py` with an exported object named `config` containing at least:

```python
from pathlib import Path


class Config:
    # API
    API_KEY = "<your-api-key>"
    FETCH_TOKEN = "https://.../token"
    EQUIPMENT_BY_MAC = "https://.../equipment/by-mac"
    CONTACT_BY_RFID = "https://.../contact/by-rfid"
    RECORDING_START = "https://.../recording/start"
    RECORDING_INFO = "https://.../recording/{reservation_id}"
    RECORDING_STOP = "https://.../recording/stop"

    # Token persistence
    TOKEN_FILE = Path("/home/bluebox/token.json")

    # Google logger
    LOGGER_JSON = "/home/bluebox/service-account.json"
    LOGGER_ACC = "logs-owner@example.com"


config = Config()
```

Notes:
- `LOGGER_JSON` must point to a valid Google service-account JSON file.
- Ensure file permissions are restricted for secrets and token files.
- If paths differ on your device, update values accordingly.

## GPIO Pin Mapping

Current defaults in `main.py`:
- Stop button: GPIO `21`
- Extend button: GPIO `13`

If your wiring differs, update button pin numbers in `main.py`.

## Running

```bash
python main.py
```

The process:
- initializes screen + RFID + API client
- starts background network monitor
- enters infinite async state loop

## Logging

- Primary logs: Google Sheets (`logger.py`)
- Fallback local log: `/home/bluebox/log_local.txt`

If Google logging fails, check:
- service account file path
- sharing permissions for `LOGGER_ACC`
- internet connectivity

## Troubleshooting

### App stuck on offline screen
- Verify internet on device (`ping 1.1.1.1`)
- Verify DNS/network routing
- Check API endpoint availability

### RFID cards not detected
- Verify MFRC522 wiring and SPI enabled
- Confirm process has required permissions
- Check reader cooldown behavior in `rfid_reader.py`

### Buttons do not trigger actions
- Verify GPIO pin wiring and pull-up/pull-down setup
- Confirm hold duration behavior in `button_watcher.py`
- Ensure app is in `InReservationState` (buttons are monitored there)

### LCD does not display
- Verify I2C enabled and address (`0x27` by default)
- Run `i2cdetect` to confirm device visibility
- Confirm LCD dimensions and compatibility with `RPLCD`

## Development Notes

- The codebase is async-first; avoid introducing blocking I/O in state logic.
- Prefer one module for button watching (`button_watcher.py`) to avoid duplication with `button_handler.py`.
- See `improvements.md` for prioritized architecture refactor plan.

## Safety

Do not commit:
- API keys
- token files
- Google service-account credentials
- device-specific local config
