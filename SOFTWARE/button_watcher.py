import asyncio
from app_context import AppContext
from gpiozero import Button

HOLD_DURATION = 1.8  # seconds


async def button_watcher(context: AppContext, state_queue: asyncio.Queue):
    """
    Watches hardware buttons and handles long-press detection.
    Queues a state change only if button is held for HOLD_DURATION and conditions are met.
    """
    loop = asyncio.get_running_loop()

    def on_pressed(button: Button, label, state_name):
        """
        Callback triggered when button is initially pressed.
        Starts monitoring only if not locked and network is available.
        """
        if not context.button_lock.locked() and context.network_status:
            asyncio.run_coroutine_threadsafe(
                monitor_button(button, label, state_name), loop
            )
        else:
            print(f"[{label}] Ignored — offline or locked")

    async def monitor_button(button: Button, label, state_name):
        """
        Debounces and monitors the button hold duration.
        Displays progress and enqueues a state change if hold is valid.
        """
        if context.button_lock.locked():
            print(f"[{label}] Ignored — another button active")
            return

        async with context.button_lock:
            print(f"[{label}] Button pressed — checking if really held...")
            await asyncio.sleep(0.1)  # ⏳ debounce grace period

            if not button.is_held:
                print(f"[{label}] False press — not actually held")
                return

            print(f"[{label}] Started monitoring...")
            step = 0.1
            total_steps = int(HOLD_DURATION / step)

            for i in range(total_steps):
                if not button.is_held:
                    print(f"[{label}] Released early — cancel")
                    return  # button released before full hold
                bar = "[" + "#" * (i + 1) + " " * (total_steps - i - 1) + "]"
                await context.screens.loading_screen_step(label, bar)
                await asyncio.sleep(step)

            print(f"[{label}] Held full duration! Transitioning to {state_name}")
            await state_queue.put(state_name)

    context.stop_btn.when_pressed = lambda: on_pressed(
        context.stop_btn, "Stopping...", "stop"
    )
    context.extend_btn.when_pressed = lambda: on_pressed(
        context.extend_btn, "Extending...", "extend"
    )

    try:
        while True:
            await asyncio.sleep(0.1)
    except asyncio.CancelledError:
        print("[Watcher] Cancelled — unbinding buttons")
        context.stop_btn.when_pressed = None
        context.extend_btn.when_pressed = None
        raise
