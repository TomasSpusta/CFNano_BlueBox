from pathlib import Path
import gspread
from gspread import Spreadsheet
from datetime import datetime
import asyncio
from config import config
import gspread.utils
from dataclasses import dataclass, fields
#

# sh_name = config.mac_address


@dataclass
class LogSchema:
    log_entry: str = "LOG ENTRY"
    ip: str = "IP"
    token: str = "TOKEN"
    instrument: str = "INSTRUMENT"
    user_info: str = "USER INFO"
    recording_start: str = "RECORDING START"
    recording_extended: str = "RECORDING EXTENDED"
    recording_end: str = "RECORDING END"
    error: str = "ERROR"
    github_branch: str = "GITHUB BRANCH"


def get_headers_from_schema() -> list[str]:
    return [f.default for f in fields(LogSchema)]


def get_column_index(field_name: str) -> int:
    return [f.name for f in fields(LogSchema)].index(field_name) + 1


class _LoggerInterface:
    def __init__(self, logger: "Logger"):
        self._logger = logger

    def __dir__(self):
        return [f.name for f in fields(LogSchema)]

    def __getattr__(self, attr):
        try:
            col = get_column_index(attr)
            col_name = getattr(LogSchema(), attr)
        except ValueError:
            raise AttributeError(f"[Logger] No such log field: {attr}")

        async def log_fun(value, note=None):
            print(f"[Logger] Writing log in column {col} with name '{col_name}'")
            await self._logger.write_log(col, value, note)

        return log_fun


class Logger:
    """
    HEADERS = [
        "BOOT UP",
        "LAN IP",
        "WLAN IP",
        "GITHUB BRANCH",
        "INSTRUMENT",
        "MAIN SCRIPT",
        "CARD SWIPE",
        "USER INFO",
        "TOKEN",
        "RECORDING START",
        "RECORDING END",
        "ERROR",
    ]"""

    def __init__(self, mac_address, instrument_name):
        self.sh_name = f"{mac_address}_{instrument_name}"
        self.headers = get_headers_from_schema()
        self.gc = None
        self.sheet: Spreadsheet = None
        self.current_log_row = 2  # <- this has to be tested, so logs are writen in row 2 and do not erase previous logs
        self.make_log = _LoggerInterface(self)

    async def initialize(self):
        try:
            self.gc = await asyncio.to_thread(
                gspread.service_account,
                filename=config.LOGGER_JSON,
            )
            self.sheet = await self._open_or_create_sheet()

        except Exception as e:
            # print(f"Error initialize logger: {e}")
            await self.write_local_log(f"Error initialize logger: {e}")

    async def _open_or_create_sheet(self):
        try:
            # print("Sheet found - Opening sheet...")
            spreadsheet = await asyncio.to_thread(self.gc.open, self.sh_name)
            return spreadsheet.sheet1

        except gspread.SpreadsheetNotFound:
            sheet = await asyncio.to_thread(self.gc.create, self.sh_name)
            # print("Sharing sheet...")
            await asyncio.to_thread(
                sheet.share,
                config.LOGGER_ACC,
                perm_type="user",
                role="writer",
                notify=True,
            )
            # print("Preapring headers...")
            await self._prepare_headers(sheet.sheet1)
            return sheet.sheet1

        except Exception as e:
            print(f"Error in _open_or_create_sheet: {e}")
            await self.write_local_log(f"Error in _open_or_create_sheet: {e}")
            raise

    async def check_headers(self):
        if not self.sheet:
            await self.write_local_log("Header check failed: sheet not initialized")
            return

        try:
            a1_cell = await asyncio.to_thread(self.sheet.cell, 1, 1)
            if not a1_cell or not a1_cell.value or not a1_cell.value.strip():
                print("[Logger] Headers not found — initializing...")
                await self._prepare_headers(self.sheet)
            else:
                print("[Logger] Headers already exist.")
        except Exception as e:
            await self.write_local_log(f"Header check error: {e}")

    async def _prepare_headers(self, ws):
        headers_range = f"A1:{chr(64 + len(self.headers))}1"
        await asyncio.to_thread(ws.update, headers_range, [self.headers])

    async def insert_new_row(self):
        """Insert a new row below the headers for a new card swipe."""
        if not self.sheet:
            await self.write_local_log("Insert row failed: Sheet not initialized")
            return

        try:
            await asyncio.to_thread(self.sheet.insert_row, [], 2)
            self.current_log_row = 2
        except Exception as e:
            await self.write_local_log(f"Error inserting new log row: {str(e)}")

    async def write_log(self, column, log_msg, log_note=None):
        try:
            if not self.sheet:
                raise Exception("Google sheet not initialized")

            # print(f"Writing log in column {column}")

            await asyncio.to_thread(
                self.sheet.update_cell, self.current_log_row, column, str(log_msg)
            )

            if log_note:
                note_cell = gspread.utils.rowcol_to_a1(self.current_log_row, column)
                await asyncio.to_thread(
                    self.sheet.update_note, note_cell, str(log_note)
                )
        except Exception as e:
            print(f"Error in write log: {e}")
            await self.write_local_log(f"Error in write log: {str(e)}")

    async def write_local_log(self, message: str):
        local_log_path = Path("/home/bluebox/log_local.txt")
        try:
            await asyncio.to_thread(
                local_log_path.write_text,
                f"{datetime.now().isoformat()} - {message}\n",
                encoding="utf-8",
                append=True if local_log_path.exists() else False,
            )
        except Exception as e:
            print(f"Failed to write local log:{e}, message: {message}")
