import asyncio
from states.base_state import State
from app_context import AppContext


class OfflineState(State):
    """
    State shown when the device is offline.
    Displays a "no connection" message and repeatedly checks for reconnection.
    Once online again, it transitions back to WaitingForCardState.
    """

    async def run(self, context: AppContext) -> State:
        # Import the next state to transition to once connection is restored
        from states.waiting_for_card_state import WaitingForCardState

        # Show "no connection" screen to the user
        await context.screens.no_connection()

        # Loop forever, checking if connection has been restored
        while True:
            # Wait 1 second before retrying
            await asyncio.sleep(1)
            if await context.api.check_connection():
                # If reconnected, show a confirmation screen
                await context.screens.connection_restored()
                # Transition back to normal waiting state
                return WaitingForCardState()
