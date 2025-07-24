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
    Show remaining reservation time.
    Button monitoring.

    """

    async def run(self, context: AppContext) -> State:
        warning_time = 5  # warning in minutes
        state_queue = asyncio.Queue()

        watcher_task = asyncio.create_task(button_watcher(context, state_queue))

        try:
            while (
                context.reservation.remaining_time > 0
                and not context.reservation.ended_by_user
            ):
                try:
                    new_state = await asyncio.wait_for(state_queue.get(), timeout=0.5)

                    if new_state == "stop":
                        return UserStopReservationState()
                    elif new_state == "extend":
                        return ExtendReservationState()
                except asyncio.TimeoutError:
                    pass

                if not context.button_lock.locked():
                    async with context.lock:
                        await context.screens.in_reservation(
                            context.reservation.remaining_time
                        )

                    await safe_api_call(
                        context.api.fetch_recording_info,
                        context=context,
                        api_screens=context.screens,
                        # api parameters
                        token=context.token,
                        reservation=context.reservation,
                    )
                    await asyncio.sleep(0.5)

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
            watcher_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await watcher_task

        return TimeOutState()
