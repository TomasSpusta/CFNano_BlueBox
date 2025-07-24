import asyncio
from dataclasses import dataclass, field
from typing import TYPE_CHECKING
from model_classes import Instrument, Reservation, Token, User
from screen_manager import Screens
from rfid_reader import RFIDReader
from logger import Logger
from api_client import APIClient
from gpiozero import Button

if TYPE_CHECKING:
    from states.base_state import State


@dataclass
class AppFlags:
    """
    Flags responsible for lcd and buttons behaviour
    """

    lcd_in_use: bool = False  # True: another courutine is using the lcd
    screen_needs_refresh: bool = False
    block_buttons: bool = (
        False  # True: Buttons are disabled (e.g in case of offline status)
    )


@dataclass
class AppContext:
    """
    Variables connected with app
    """

    state: "State" = None  # <- Forward reference string
    token: Token = None
    instrument: Instrument = None
    user: User = None
    reservation: Reservation = None
    logger: Logger = None
    card_id: str = None
    flags: AppFlags = field(default_factory=AppFlags)
    screens: Screens = None
    rfid_reader: RFIDReader = None
    api: APIClient = None
    stop_btn: Button = None
    extend_btn: Button = None
    network_status: bool = True  # True: Device is online, False: Device is offline
    lock = None
    counter = 100
    button_lock = asyncio.Lock()
