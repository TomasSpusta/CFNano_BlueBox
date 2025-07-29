from RPLCD.i2c import CharLCD
import asyncio
from typing import Optional


# initialize the LCD display, (expander chip, port)
class LCDController:
    """
    Asynchronous controller for an I²C character LCD using the RPLCD library.
    Supports non-blocking message display, backlight control, and flashing effects.
    """

    def __init__(
        self,
        address=0x27,  # Default I²C address for many LCD backpacks
        chip="PCF8574",  # Common I²C GPIO expander used on LCD adapters
    ):
        # Initialize the LCD
        self.lcd = CharLCD(chip, address)
        # Ensure exclusive LCD access for concurrent tasks
        self.lock = asyncio.Lock()

    async def _write(self, text, row):
        if text:
            # Set cursor to specified row, column 0 (1-indexed row)
            await asyncio.to_thread(setattr, self.lcd, "cursor_pos", (row - 1, 0))
            # Write the text to that position
            await asyncio.to_thread(self.lcd.write_string, text)

    async def message(
        self,
        line1: Optional[str] = None,
        line2: Optional[str] = None,
        line3: Optional[str] = None,
        line4: Optional[str] = None,
        backlight: bool = True,
        clear: bool = True,
        display_time: int = 2,
    ):
        async with self.lock:
            # Turn backlight on/off
            await asyncio.to_thread(setattr, self.lcd, "backlight_enabled", backlight)

            # Optionally clear the LCD before writing new message
            if clear is True:
                await asyncio.to_thread(self.lcd.clear)

            # Write provided lines to rows 1–4
            if line1 is not None:
                await self._write(line1, 1)
            if line2 is not None:
                await self._write(line2, 2)
            if line3 is not None:
                await self._write(line3, 3)
            if line4 is not None:
                await self._write(line4, 4)
        # Keep the message visible for a defined duration
        await asyncio.sleep(display_time)

    async def _backlight(self, status: bool):
        await asyncio.to_thread(setattr, self.lcd, "backlight_enabled", status)

    async def _clear(self):
        await asyncio.to_thread(self.lcd.clear)

    # Flashing screen for alarm or notification
    async def flashing(self, interval, number_of_flashes):
        for _ in range(number_of_flashes):
            await asyncio.sleep(interval)
            await asyncio.to_thread(setattr, self.lcd, "backlight_enabled", True)
            await asyncio.sleep(interval)
            await asyncio.to_thread(setattr, self.lcd, "backlight_enabled", False)

    async def cleanup(self):
        # Clear screen
        await asyncio.to_thread(self.lcd.clear)
        # Turn off backlight
        await asyncio.to_thread(setattr, self.lcd, "backlight_enabled", False)
