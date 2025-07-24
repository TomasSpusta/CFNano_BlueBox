from states.base_state import State
from app_context import AppContext
from datetime import datetime


class TimeOutState(State):
    """
    Display message for user when reservation ended by timeout.
    """

    async def run(self, context: AppContext) -> State:
        from states.waiting_for_card_state import WaitingForCardState

        async with context.lock:
            await context.screens.session_ended_by_timeout()
            await context.logger.make_log.recording_end(
                datetime.now(), "Ended by timeout"
            )

        return WaitingForCardState()
