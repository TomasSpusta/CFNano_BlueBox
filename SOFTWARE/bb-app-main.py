import asyncio
import contextlib
import signal
import aiohttp
from states.init_state import InitState
from app_context import AppContext
from screen_manager import Screens
from lcd_display import LCDController
from rfid_reader import RFIDReader
from api_client import APIClient
from gpiozero import Button
from networking import network_monitor
from http_config import REQUEST_TIMEOUT


async def main():
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        with contextlib.suppress(NotImplementedError):
            loop.add_signal_handler(sig, stop_event.set)

    context = AppContext()  # Shared app context passed to all states
    context.state = InitState()  # Start in InitState (loads config, token, etc.)
    context.screens = Screens(
        LCDController()
    )  # LCD controller wrapped by screen manager

    # Define GPIO buttons with pin numbers and debounce/hold times
    context.stop_btn = Button(21, hold_time=0.1, bounce_time=0.05)
    context.extend_btn = Button(13, hold_time=0.1, bounce_time=0.05)
    context.rfid_reader = RFIDReader()  # RFID input (hardware abstraction)

    # Global async lock for shared state (e.g. logging)
    context.lock = asyncio.Lock()

    network_task = None
    try:
        async with aiohttp.ClientSession(timeout=REQUEST_TIMEOUT) as session:
            context.api = APIClient(session=session)  # API handler (auth, user, reservation)

            # Start network monitor as background task (e.g. to update UI or trigger OfflineState)
            network_task = asyncio.create_task(network_monitor(context.screens, context))

            # Main control loop: executes and transitions between states
            while not stop_event.is_set():
                state_task = asyncio.create_task(context.state.run(context))
                stop_task = asyncio.create_task(stop_event.wait())

                done, pending = await asyncio.wait(
                    [state_task, stop_task],
                    return_when=asyncio.FIRST_COMPLETED,
                )

                for task in pending:
                    task.cancel()
                    with contextlib.suppress(asyncio.CancelledError):
                        await task

                if stop_task in done:
                    state_task.cancel()
                    with contextlib.suppress(asyncio.CancelledError):
                        await state_task
                    break

                context.state = state_task.result()
    finally:
        if network_task is not None:
            network_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await network_task

        if context.stop_btn is not None:
            context.stop_btn.close()
        if context.extend_btn is not None:
            context.extend_btn.close()


if __name__ == "__main__":
    asyncio.run(main())
