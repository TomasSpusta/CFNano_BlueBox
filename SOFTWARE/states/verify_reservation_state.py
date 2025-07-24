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
        from states.waiting_for_card_state import WaitingForCardState
        from states.in_reservation_state import InReservationState

        await context.screens.checking_reservation()

        reservation: Reservation = await safe_api_call(
            context.api.start_extend_reservation,
            context=context,
            api_screens=context.screens,
            # api parameters
            user=context.user,
            instrument=context.instrument,
            token=context.token,
        )

        if reservation:
            context.reservation = reservation
            await context.screens.reservation_ok()
            # await context.logger.write_log(10, context.reservation.reservation_id)
            await context.logger.make_log.recording_start(
                datetime.now(), context.reservation.reservation_id
            )
            return InReservationState()
        else:
            await context.screens.reservation_nok()
            return WaitingForCardState()
