from states.base_state import State
from app_context import AppContext
from model_classes import User
from networking import safe_api_call
from datetime import datetime


class VerifyUserState(State):
    """
    State responsible for verifying whether the scanned card belongs to a known user.
    If the user is found, proceeds to verify reservation.
    If not, displays an error and returns to waiting for card.
    """

    async def run(self, context: AppContext) -> State:
        # Import next possible states
        from states.verify_reservation_state import VerifyReservationState
        from states.waiting_for_card_state import WaitingForCardState

        # Show "checking user" feedback on screen
        await context.screens.checking_user()

        # Attempt to fetch user data based on the card ID
        user: User = await safe_api_call(
            context.api.fetch_user_data,
            context=context,
            api_screens=context.screens,
            # api parameters:
            card_id=context.card_id,
        )
        # Insert a new row into the log (e.g. to start a new session entry)
        await context.logger.insert_new_row()
        # Log the time of entry (user scan time)
        await context.logger.make_log.log_entry(datetime.now())
        # Log token expiration time for debugging or tracking
        await context.logger.make_log.token(context.token.expiration)

        if user:
            # If a user was found for the scanned card
            # Store user info in the context
            context.user = user
            # Log user full name
            await context.logger.make_log.user_info(context.user.full_name)
            # Proceed to verify the reservation
            return VerifyReservationState()
        else:
            # If no user found for the card ID
            await context.screens.user_not_in_database()
            # Log the unknown card ID instead of user name
            await context.logger.make_log.user_info(context.card_id)
            # Return to waiting for the next card scan
            return WaitingForCardState()
