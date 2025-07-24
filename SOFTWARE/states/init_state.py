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
    Initialize application.
    Verify token (or request new one).
    Fetch Instrument data.
    """

    async def run(self, context: AppContext) -> State:
        await context.screens.starting_screen()
        context.network_status = await check_internet_connection()

        token: Token = await safe_api_call(
            lambda: verify_token(context),
            context=context,
            api_screens=context.screens,
            logger=context.logger,
        )

        if token:
            context.token = token
        else:
            return self

        ip = await fetch_ip()
        mac = await fetch_mac()

        instrument: Instrument = await safe_api_call(
            context.api.fetch_instrument_data,
            context=context,
            api_screens=context.screens,
            # api parameters
            mac=mac,
            ip=ip,
        )

        if instrument:
            context.instrument = instrument
            context.logger = Logger(
                context.instrument.mac_address, context.instrument.name
            )
            await context.screens.initial_logs(
                time=datetime.now,
                ip=context.instrument.ip,
                instrument=context.instrument.name,
            )
            await context.logger.initialize()
            await context.logger.check_headers()
            await context.logger.insert_new_row()

            await context.logger.make_log.log_entry(datetime.now())
            await context.logger.make_log.ip(context.instrument.ip)
            await context.logger.make_log.instrument(context.instrument.name)

        else:
            return self
        return WaitingForCardState()
