from mfrc522 import SimpleMFRC522
import asyncio
import time


class RFIDReader:
    def __init__(self) -> None:
        # Initialize the RFID reader hardware
        self.reader = SimpleMFRC522()

        # Cache of the last read card ID to avoid duplicates
        self.last_card_id = None

        # Timestamp of the last successful card read
        self._last_read_time = 0

        # Minimum time (in seconds) between reads of the same card
        self._cooldown = 2

    async def read_card(self) -> str | None:
        """
        Reads an RFID card and returns the corrected card ID.
        Applies a cooldown and filters out duplicate reads.
        """
        try:
            # Blocking read from RFID reader
            card_id, _ = self.reader.read()
            now = time.time()

            # Only accept new card or if cooldown has passed
            if (
                card_id != self.last_card_id
                or (now - self._last_read_time) > self._cooldown
            ):
                self._last_read_time = now
                self.last_card_id = card_id
                return await self._process_card(card_id)

            # Ignore duplicate reads during cooldown
            return None

        except Exception as e:
            print(f"RFID read error: {e}")
            return None

    async def _process_card(self, card_id: int) -> str:
        """
        Processes the card ID, applying corrections and converting to string.
        """
        corrected_card_id = await self.card_id_correction(card_id)
        return str(corrected_card_id)

    async def card_id_correction(self, card_id: int) -> str:
        """
        Converts a 32-bit card ID to a consistent format:
        - Converts to hexadecimal
        - Reverses byte order
        - Converts back to zero-padded string

        Example:
            card_id = 12345678
            hex     = '00BC614E'
            reversed= '4E61BC00'
            result  = '1311766528'
        """

        hex_num = hex(card_id)[2:].zfill(8)  # Hex without '0x', zero-padded to 8 chars
        reversed_hex = hex_num[6:8] + hex_num[4:6] + hex_num[2:4] + hex_num[0:2]
        corrected = str(int(reversed_hex, 16)).zfill(10)  # Convert to int and pad
        return corrected


'''
To be deleted:
    async def stop(self):
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def clear_queue(self):
        """
        Clears any remaining items in the internal card queue.
        Again, assumes a self.queue is present — not shown here.
        """
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
                self.queue.task_done()
            except asyncio.QueueEmpty:
                break
'''
