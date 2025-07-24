from states.base_state import State
from app_context import AppContext
from datetime import datetime

from networking import safe_api_call


class ExtendReservationState(State):
    """
    State dealing with extension of reservation.
    """

    async def run(self, context: AppContext) -> State:
        from states.in_reservation_state import InReservationState

        async with context.lock:
            if context.reservation.remaining_time >= 14:
                await context.screens.extend_not_yet()
                return InReservationState()
            await safe_api_call(
                context.api.start_extend_reservation,
                context=context,
                api_screens=context.screens,
                # api variables:
                user=context.user,
                instrument=context.instrument,
                token=context.token,
            )
        await context.screens.reservation_extended()
        await context.logger.make_log.recording_extended(
            datetime.now(), "Extended by user"
        )
        context.reservation.warning_sent = False
        # await asyncio.sleep(1)
        return InReservationState()
