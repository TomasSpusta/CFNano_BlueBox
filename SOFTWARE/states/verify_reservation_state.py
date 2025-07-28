# 5. states/starting_session.py
from states.base_state import State
from app_context import AppContext
from datetime import datetime
from model_classes import Reservation
from networking import safe_api_call


class VerifyReservationState(State):
    """
    State responsible for verifying if a reservation exists and is valid.
    Based on the result, it transitions to either InReservationState or WaitingForCardState.
    """

    async def run(self, context: AppContext) -> State:
        # Import possible next states to transition to
        from states.waiting_for_card_state import WaitingForCardState
        from states.in_reservation_state import InReservationState

        # Display a "checking reservation" screen
        await context.screens.checking_reservation()

        # Call the API to verify and run or extend the reservation
        reservation: Reservation = await safe_api_call(
            context.api.start_extend_reservation,
            context=context,
            api_screens=context.screens,
            # api parameters:
            user=context.user,
            instrument=context.instrument,
            token=context.token,
        )

        if reservation:
            # If a reservation was returned successfully
            # Store the reservation in the context
            context.reservation = reservation

            # Notify user that reservation is OK
            await context.screens.reservation_ok()
            # Log the reservation start
            await context.logger.make_log.recording_start(
                datetime.now(), context.reservation.reservation_id
            )
            # Transition to the InReservationState
            return InReservationState()
        else:
            # If the reservation was not found or invalid
            await context.screens.reservation_nok()
            # Transition back to waiting for card input
            return WaitingForCardState()
