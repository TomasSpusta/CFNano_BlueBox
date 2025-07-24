from states.base_state import State
from app_context import AppContext
from states.waiting_for_card_state import WaitingForCardState
from networking import safe_api_call
from datetime import datetime


class UserStopReservationState(State):
    """
    Responsible for stopping the reservation when user decides to end it.
    """

    async def run(self, context: AppContext) -> State:
        async with context.lock:
            await safe_api_call(
                context.api.stop_reservation,
                context=context,
                api_screens=context.screens,
                # api variables:
                reservation=context.reservation,
                instrument=context.instrument,
                token=context.token,
            )
        await context.screens.user_stop_reservation()
        await context.logger.make_log.recording_end(datetime.now(), "Ended by user")
        return WaitingForCardState()
