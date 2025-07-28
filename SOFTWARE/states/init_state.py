from states.base_state import State
from app_context import AppContext
from states.waiting_for_card_state import WaitingForCardState
from networking import fetch_ip, fetch_mac
from model_classes import Instrument, Token
from networking import safe_api_call, check_internet_connection
from token_handler import verify_token
from logger import Logger
from datetime import datetime


class InitState(State):
    """
    Initial application state.
    - Shows starting screen
    - Verifies or fetches a new token
    - Fetches instrument metadata (MAC/IP)
    - Initializes logger
    - Transitions to WaitingForCardState on success
    """

    async def run(self, context: AppContext) -> State:
        # Show splash/loading screen while initializing
        await context.screens.starting_screen()

        # Check if device has internet access
        context.network_status = await check_internet_connection()

        # Validate current token or fetch a new one
        token: Token = await safe_api_call(
            lambda: verify_token(context),
            context=context,
            api_screens=context.screens,
            logger=context.logger,
        )

        if token:
            context.token = token  # Store valid token in context
        else:
            return self  # Stay in InitState (retry later)

        # Get device IP and MAC address
        ip = await fetch_ip()
        mac = await fetch_mac()

        instrument: Instrument = await safe_api_call(
            context.api.fetch_instrument_data,
            context=context,
            api_screens=context.screens,
            # api parameters:
            mac=mac,
            ip=ip,
        )

        # Fetch instrument information using MAC address, store IP
        if instrument:
            # Store instrument metadata in context
            context.instrument = instrument

            # Initialize logging with MAC and instrument name
            context.logger = Logger(
                context.instrument.mac_address, context.instrument.name
            )
            # Display diagnostic/logging info on screen
            await context.screens.initial_logs(
                time=datetime.now(),
                ip=context.instrument.ip,
                instrument=context.instrument.name,
            )
            # Initialize and prepare logging sheet
            await context.logger.initialize()
            await context.logger.check_headers()
            await context.logger.insert_new_row()

            # Initial log (date+time, ip to remote connection, insturment name)
            await context.logger.make_log.log_entry(datetime.now())
            await context.logger.make_log.ip(context.instrument.ip)
            await context.logger.make_log.instrument(context.instrument.name)

        else:
            # Retry if instrument fetch failed
            return self

        # Initialization complete, go to card scanning state
        return WaitingForCardState()
