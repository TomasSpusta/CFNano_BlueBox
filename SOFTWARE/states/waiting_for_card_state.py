from states.base_state import State
from app_context import AppContext


class WaitingForCardState(State):
    """
    State responsible for waiting for a user to scan their RFID card.
    Displays a welcome screen and reads card input. If a card is scanned, transitions to VerifyUserState.
    """

    async def run(self, context: AppContext) -> State:
        await context.screens.welcome_screen(context.instrument.name)

        card_id = await context.rfid_reader.read_card()

        from states.verify_user import VerifyUserState

        if card_id:
            context.card_id = card_id
            return VerifyUserState()

        return self
