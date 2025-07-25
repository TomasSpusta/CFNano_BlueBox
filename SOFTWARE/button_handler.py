import asyncio
from app_context import AppContext


async def button_watcher(context: AppContext, state_queue: asyncio.Queue):
    """
    Watches for button presses and enqueues state transition signals accordingly.
    Intended to run as a background task and respond to hardware button events.

    Args:
        context (AppContext): Application context containing hardware buttons.
        state_queue (asyncio.Queue): Queue to signal state transitions ("stop", "reset", etc.).
    """
    loop = asyncio.get_running_loop()

    def queue_put(state_name):
        print(f"Queued state change: {state_name}")
        asyncio.run_coroutine_threadsafe(state_queue.put(state_name), loop)

    # Using lambda inside asyncio.create_task to not block main thread
    context.stop_btn.when_held = lambda: queue_put("stop")
    context.extend_btn.when_held = lambda: queue_put("extend")

    try:
        while True:
            await asyncio.sleep(0.1)
    except asyncio.CancelledError:
        pass
