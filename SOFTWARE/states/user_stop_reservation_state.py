from states.base_state import State
from app_context import AppContext
from states.waiting_for_card_state import WaitingForCardState
from networking import safe_api_call
from datetime import datetime


class UserStopReservationState(State):
    """
    State that handles user-initiated termination of the reservation.
    Calls the backend to stop the recording, updates the screen, and logs the action.
    """

    async def run(self, context: AppContext) -> State:
        # Ensure exclusive access while interacting with shared state and API
        async with context.lock:
            # Attempt to stop the reservation using safe API wrapper
            await safe_api_call(
                context.api.stop_reservation,
                context=context,
                api_screens=context.screens,
                # api variables:
                reservation=context.reservation,
                instrument=context.instrument,
                token=context.token,
            )

        # Inform the user that the reservation was successfully stopped
        await context.screens.user_stop_reservation()

        # Log the end of the reservation as user-initiated
        await context.logger.make_log.recording_end(datetime.now(), "Ended by user")

        # Return to the idle state, waiting for the next card scan
        return WaitingForCardState()
