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
    """
    Represents the columns (log fields) used in the Google Sheet.
    Each field maps to a human-readable column name.
    """

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
    """Returns a list of column headers from the LogSchema dataclass."""
    return [f.default for f in fields(LogSchema)]


def get_column_index(field_name: str) -> int:
    """Returns 1-based index of a column given the schema field name."""
    return [f.name for f in fields(LogSchema)].index(field_name) + 1


class _LoggerInterface:
    """
    A proxy that dynamically creates async logging functions like:
    await logger.make_log.token("abc") → writes to the TOKEN column
    """

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
    Handles:
    - Opening or creating a Google Sheet per device
    - Writing log rows and individual log fields
    - Fallback logging to a local text file
    - Dynamic log functions via self.make_log
    """

    def __init__(self, mac_address, instrument_name):
        self.sh_name = f"{mac_address}_{instrument_name}"  # Unique name for the sheet
        self.headers = get_headers_from_schema()
        self.gc = None
        self.sheet: Spreadsheet = None
        self.current_log_row = (
            2  # Always write to row 2, so logs are new (top) ---> old (bot)
        )
        self.make_log = _LoggerInterface(self)  # Exposes async logging methods

    async def initialize(self):
        """Authenticate and open or create the Google Sheet."""
        try:
            self.gc = await asyncio.to_thread(
                gspread.service_account,
                filename=config.LOGGER_JSON,
            )
            self.sheet = await self._open_or_create_sheet()

        except Exception as e:
            await self.write_local_log(f"Error initialize logger: {e}")

    async def _open_or_create_sheet(self):
        try:
            # Try to open the existing sheet
            spreadsheet = await asyncio.to_thread(self.gc.open, self.sh_name)
            return spreadsheet.sheet1

        except gspread.SpreadsheetNotFound:
            # Sheet not found → create and initialize new one
            sheet = await asyncio.to_thread(self.gc.create, self.sh_name)
            # Share sheet to google disc
            await asyncio.to_thread(
                sheet.share,
                config.LOGGER_ACC,
                perm_type="user",
                role="writer",
                notify=True,
            )
            # Prepare headers according to the LogSchema
            await self._prepare_headers(sheet.sheet1)
            return sheet.sheet1

        except Exception as e:
            print(f"Error in _open_or_create_sheet: {e}")
            await self.write_local_log(f"Error in _open_or_create_sheet: {e}")
            raise

    async def check_headers(self):
        """Checks if the sheet already has headers; initializes them if missing."""
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
        """Writes column headers to row 1."""
        headers_range = f"A1:{chr(64 + len(self.headers))}1"
        await asyncio.to_thread(ws.update, headers_range, [self.headers])

    async def insert_new_row(self):
        """Inserts an empty row at position 2 for a new session/log event."""
        if not self.sheet:
            await self.write_local_log("Insert row failed: Sheet not initialized")
            return

        try:
            await asyncio.to_thread(self.sheet.insert_row, [], 2)
            self.current_log_row = 2
        except Exception as e:
            await self.write_local_log(f"Error inserting new log row: {str(e)}")

    async def write_log(self, column, log_msg, log_note=None):
        """Writes a message to a given column in the current log row."""
        try:
            if not self.sheet:
                raise Exception("Google sheet not initialized")

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
        """Writes a log message to a fallback local text file."""
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
