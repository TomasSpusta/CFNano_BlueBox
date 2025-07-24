import asyncio
from states.init_state import InitState

# from states.test_state import TestState
from app_context import AppContext
from screen_manager import Screens
from lcd_display import LCDController
from rfid_reader import RFIDReader
from api_client import APIClient
from gpiozero import Button
from networking import network_monitor


async def main():
    context = AppContext()
    context.state = InitState()
    context.screens = Screens(LCDController())
    context.rfid_reader = RFIDReader()
    context.api = APIClient()
    context.stop_btn = Button(21, hold_time=0.1, bounce_time=0.05)
    context.extend_btn = Button(13, hold_time=0.1, bounce_time=0.05)
    context.lock = asyncio.Lock()

    asyncio.create_task(network_monitor(context.screens, context))

    while True:
        context.state = await context.state.run(context)


if __name__ == "__main__":
    asyncio.run(main())
