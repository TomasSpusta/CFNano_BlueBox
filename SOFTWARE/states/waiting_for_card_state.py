from states.base_state import State
from app_context import AppContext


class WaitingForCardState(State):
    """
    State responsible for waiting for a user to scan their RFID card.
    Displays a welcome screen and reads card input. If a card is scanned, transitions to VerifyUserState.
    """

    async def run(self, context: AppContext) -> State:
        # Display welcome screen with instrument name (e.g., "Welcome to Microscope XYZ")
        await context.screens.welcome_screen(context.instrument.name)
        # Wait for the user to scan their RFID card
        card_id = await context.rfid_reader.read_card()

        from states.verify_user import VerifyUserState

        if card_id:
            # If a card was successfully scanned, store it in context
            context.card_id = card_id
            # Move to user verification state
            return VerifyUserState()
        # No card detected — remain in this state and wait again
        return self
