from RPLCD.i2c import CharLCD
import asyncio
from typing import Optional


# initialize the LCD display, (expander chip, port)
class LCDController:
    def __init__(
        self,
        address=0x27,
        chip="PCF8574",  # , default_message: Optional[list[str]] = None
    ):
        self.lcd = CharLCD(chip, address)
        self.message_queue = asyncio.PriorityQueue()
        self.current_message = None
        self.lock = asyncio.Lock()
        # self.default_message = default_message

    async def _write(self, text, row):
        if text:
            # await asyncio.to_thread(self.lcd.cursor_pos.__setattr__,(row-1, 0))
            await asyncio.to_thread(setattr, self.lcd, "cursor_pos", (row - 1, 0))
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
            await asyncio.to_thread(setattr, self.lcd, "backlight_enabled", backlight)
            if clear is True:
                await asyncio.to_thread(self.lcd.clear)
            if line1 is not None:
                await self._write(line1, 1)
            if line2 is not None:
                await self._write(line2, 2)
            if line3 is not None:
                await self._write(line3, 3)
            if line4 is not None:
                await self._write(line4, 4)
        await asyncio.sleep(display_time)
        #

    async def _backlight(self, status: bool):
        await asyncio.to_thread(setattr, self.lcd, "backlight_enabled", status)

    async def _clear(self):
        await asyncio.to_thread(self.lcd.clear)

    async def flashing(self, interval, number_of_flashes):
        for _ in range(number_of_flashes):
            await asyncio.sleep(interval)
            await asyncio.to_thread(setattr, self.lcd, "backlight_enabled", True)
            await asyncio.sleep(interval)
            await asyncio.to_thread(setattr, self.lcd, "backlight_enabled", False)

    async def cleanup(self):
        await asyncio.to_thread(self.lcd.clear)
        await asyncio.to_thread(setattr, self.lcd, "backlight_enabled", False)
