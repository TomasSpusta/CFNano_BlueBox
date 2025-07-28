from states.base_state import State
from app_context import AppContext
from datetime import datetime

from networking import safe_api_call


class ExtendReservationState(State):
    """
    State dealing with extension of reservation.
    """

    async def run(self, context: AppContext) -> State:
        # Import the next possible state to transition to
        from states.in_reservation_state import InReservationState

        async with context.lock:
            # Prevent extension if there's still enough remaining time (15 min)
            if context.reservation.remaining_time >= 14:
                await context.screens.extend_not_yet()
                return InReservationState()

            # Attempt to extend the reservation
            await safe_api_call(
                context.api.start_extend_reservation,
                context=context,
                api_screens=context.screens,
                # api variables:
                user=context.user,
                instrument=context.instrument,
                token=context.token,
            )

        # Notify the user that reservation was successfully extended
        await context.screens.reservation_extended()

        # Log the extension event
        await context.logger.make_log.recording_extended(
            datetime.now(), "Extended by user"
        )
        # Reset warning flag so user can be warned again near the new end time
        context.reservation.warning_sent = False

        # Return to main reservation state
        return InReservationState()
