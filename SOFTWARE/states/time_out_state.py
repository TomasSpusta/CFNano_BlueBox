from states.base_state import State
from app_context import AppContext
from datetime import datetime


class TimeOutState(State):
    """
    State entered when a reservation ends due to timeout.
    Displays a message to the user and logs the event.
    """

    async def run(self, context: AppContext) -> State:
        from states.waiting_for_card_state import WaitingForCardState

        # Acquire the context lock to ensure exclusive access to shared state
        async with context.lock:
            # Notify user that the session has ended due to timeout
            await context.screens.session_ended_by_timeout()
            # Log the timeout event with a timestamp and reason
            await context.logger.make_log.recording_end(
                datetime.now(), "Ended by timeout"
            )
        # Transition back to the beginning, waiting for a new user/card
        return WaitingForCardState()
