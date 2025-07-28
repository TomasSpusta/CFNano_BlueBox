import asyncio
from states.base_state import State
from app_context import AppContext
from button_watcher import button_watcher
import contextlib
from networking import safe_api_call
from states.time_out_state import TimeOutState
from states.extend_reservation_state import ExtendReservationState
from states.user_stop_reservation_state import UserStopReservationState


class InReservationState(State):
    """
    Active state while a reservation is ongoing.
    Continuously displays remaining time, monitors button input, and triggers warnings near the end.
    """

    async def run(self, context: AppContext) -> State:
        warning_time = 5  # Time in minutes before end to trigger warning
        state_queue = asyncio.Queue()  # Queue for button-triggered state transitions

        # Launch button watcher as background task
        watcher_task = asyncio.create_task(button_watcher(context, state_queue))

        try:
            # Main loop: runs as long as reservation is valid and not manually ended
            while (
                context.reservation.remaining_time > 0
                and not context.reservation.ended_by_user
            ):
                try:
                    # Wait (up to 0.5s - to eliminate false presses) for button press that requests a state change
                    new_state = await asyncio.wait_for(state_queue.get(), timeout=0.5)

                    if new_state == "stop":
                        return UserStopReservationState()
                    elif new_state == "extend":
                        return ExtendReservationState()
                except asyncio.TimeoutError:
                    # No button press — continue with status update
                    pass

                # Only update screen if no button is being handled
                if not context.button_lock.locked():
                    async with context.lock:
                        # Show current reservation time
                        await context.screens.in_reservation(
                            context.reservation.remaining_time
                        )

                    # Update remaining time of reservation
                    await safe_api_call(
                        context.api.fetch_recording_info,
                        context=context,
                        api_screens=context.screens,
                        # api parameters:
                        token=context.token,
                        reservation=context.reservation,
                    )
                    await asyncio.sleep(0.5)

                    # Show warning, that reservation in comming to the end, pass if already warned
                    if (
                        context.reservation.remaining_time <= warning_time
                        and not context.reservation.warning_sent
                        and not context.reservation.ended_by_user
                    ):
                        async with context.lock:
                            await context.screens.reservation_end_warning(
                                context.reservation.remaining_time
                            )
                            context.reservation.warning_sent = True

        finally:
            # Ensure button watcher is cancelled properly on exit
            watcher_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await watcher_task
        # Reservation timed out — transition to end state
        return TimeOutState()
