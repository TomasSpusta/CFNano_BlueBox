import asyncio
from states.init_state import InitState
from app_context import AppContext
from screen_manager import Screens
from lcd_display import LCDController
from rfid_reader import RFIDReader
from api_client import APIClient
from gpiozero import Button
from networking import network_monitor


async def main():
    context = AppContext()  # Shared app context passed to all states
    context.state = InitState()  # Start in InitState (loads config, token, etc.)
    context.screens = Screens(
        LCDController()
    )  # LCD controller wrapped by screen manager
    context.rfid_reader = RFIDReader()  # RFID input (hardware abstraction)
    context.api = APIClient()  # API handler (auth, user, reservation)

    # Define GPIO buttons with pin numbers and debounce/hold times
    context.stop_btn = Button(21, hold_time=0.1, bounce_time=0.05)
    context.extend_btn = Button(13, hold_time=0.1, bounce_time=0.05)

    # Global async lock for shared state (e.g. logging)
    context.lock = asyncio.Lock()

    # Start network monitor as background task (e.g. to update UI or trigger OfflineState)
    asyncio.create_task(network_monitor(context.screens, context))

    # Main control loop: executes and transitions between states
    while True:
        context.state = await context.state.run(context)


if __name__ == "__main__":
    asyncio.run(main())
