from lcd_display import LCDController
import inspect
import random
from model_classes import Instrument


class Screens:
    def __init__(self, lcd_controller: LCDController):
        self.lcd = lcd_controller

    async def starting_screen(self):
        await self.lcd.message(
            "Starting...",
            display_time=0.1,
        )

    async def initial_logs(self, time: str, ip: str, instrument: Instrument):
        await self.lcd.message(
            "Initial logs:",
            f"{time}",
            f"{ip}",
            f"{instrument}",
            display_time=2,
        )

    async def no_connection(self):
        await self.lcd.message("Device is OFFLINE.", "Please wait.", "Reconnecting...")

    async def connection_restored(self):
        await self.lcd.message(
            "Device is ONLINE.", "Resuming session...", display_time=2
        )

    async def welcome_screen(self, instrument_name: str):
        await self.lcd.message(
            "Welcome at",
            f"{instrument_name}",
            "Please log in",
            "with your card",
            # display_time=0.1,
        )

    # User
    async def checking_user(self):
        await self.lcd.message(
            "Checking user...",
            # display_time=0.5,
        )

    async def user_ok(self, user_name: str):
        phrases = [
            "Push the boundaries!",
            "Unleash your genius!",
            "Answers lie ahead!",
            "Discovery awaits!",
            "Keep exploring!",
            "Truth is out there!",
            "Find the unknown!",
        ]

        async def random_phase() -> str:
            phrase = random.choice(phrases)
            return phrase

        await self.lcd.message(
            f"Hi {user_name}",
            f"{await random_phase()}",
            # display_time=0.5,
        )

    async def user_not_in_database(self):
        await self.lcd.message(
            "Card not registered.",
            "Please register it.",
            # display_time=0.1,
        )

    # Reservation
    async def checking_reservation(self):
        await self.lcd.message(
            "Checking reservation",
            # display_time=0.1,
        )

    async def reservation_ok(self):
        await self.lcd.message(
            "Reservation found.",
            "Starting session...",
            "",
            "",
            # display_time=0.1,
        )

    async def reservation_nok(self):
        await self.lcd.message(
            "No reservation",
            "in next 30 minutes.",
            "Please make one.",
            # display_time=0.1,
        )

    # Session

    async def in_reservation(self, remaining_session_time: int):
        await self.lcd.message(
            "Remaining time:",
            f"{remaining_session_time} minutes",
            "Extend -> Hold Green",
            "Stop -> Hold Red",
            display_time=5,
            backlight=False,
        )

    async def loading_screen(self, label: str, duration: int = 5, char: str = "#"):
        for i in range(duration):
            bar = "[" + char * (i + 1) + " " * (duration - i - 1) + "]"
            await self.lcd.message(label, bar, "", "", display_time=1)

    async def show_stopped(self):
        await self.lcd.message("Stopped!")

    async def show_reloaded(self):
        await self.lcd.message("Reloaded")

    async def session_ended_by_timeout(self):
        await self.lcd.message(
            "Your session ended.",
            "See you next time.",
            display_time=2,
        )

    async def user_stop_reservation(self):
        await self.lcd.message(
            "Your session ended.",
            "See you next time.",
            display_time=2,
        )

    async def want_to_end_session(self):
        await self.lcd.message(
            "Hold RED button", "for 3 seconds", "to end reservation."
        )

    async def reservation_end_warning(self, remaining_session_time: int):
        await self.lcd.flashing(0.3, 5)
        await self.lcd.message(
            "Session will end in",
            f"{remaining_session_time} minutes.",
            "Extend -> Hold green",
            "Stop -> Hold red",
            display_time=5,
        )

    async def returning(self):
        await self.lcd.message("Returning...")

    async def want_to_extend_reservation(self):
        await self.lcd.message(
            "Hold GREEN button", "for 3 seconds", "to extend your", "reservation."
        )

    async def reservation_extended(self):
        await self.lcd.message(
            "Your session", "was extended", "by 15 minutes.", display_time=5
        )

    # Error
    async def error_message(self, error: str, source_function="Unknown"):
        await self.lcd.message(
            f"F:{source_function[:18]}",
            error[:20],
            error[20:],
            display_time=5,
        )
        # sys.exit("Critical Error. Stopping the program.")

    # Button menu
    async def button_menu(
        self,
        selected_row,
    ):
        # Format the display with '>' at the selected row
        options = ["Back", "Extend session", "Supervisor mode", "End session"]
        display_lines = []
        for i, option in enumerate(options):
            if i == selected_row:
                display_lines.append(f"> {option}")
            else:
                display_lines.append(f"  {option}")

        await self.lcd.message(
            display_lines[0],
            display_lines[1],
            display_lines[2],
            display_lines[3],
            display_time=0.1,
        )

    async def button_menu_extend(self):
        await self.lcd.message(
            "Scan your card",
            "to extend session",
            "by 15 minutes.",
            "Waiting...",
            display_time=0.1,
        )

    async def button_menu_extend_ok(self):
        await self.lcd.message(
            "Session extended",
            "by 15 minutes.",
            # display_time=0.1,
        )

    async def extend_not_yet(self):
        await self.lcd.message(
            "Session can be",
            "extended only",
            "15 minutes",
            "before its end.",
            # display_time=0.1,
        )

    async def button_menu_extend_bad_card(self):
        await self.lcd.message(
            "Unauthorized user",
            "Session not extended",
            "Returning to session",
            # display_time=0.1,
        )

    async def button_menu_end_confirmation(self):
        await self.lcd.message(
            "Press button",
            "to confirm",
            "session end.",
            # display_time=0.1,
        )

    async def run_all_screens(self):
        """Programmatically run all screen display methods for testing."""
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if callable(attr) and attr_name not in ["run_all_screens", "__init__"]:
                if inspect.iscoroutinefunction(attr):
                    params = inspect.signature(attr).parameters
                    args = []

                    # Generate default arguments for each parameter
                    for param in params.values():
                        if param.default != inspect.Parameter.empty:
                            args.append(
                                param.default
                            )  # Use the default value if it exists
                        elif param.annotation is int:
                            args.append(0)  # Default int
                        elif param.annotation is float:
                            args.append(0.0)  # Default float
                        elif param.annotation is str:
                            args.append("TEST INPUT")  # Default string
                        else:
                            args.append(None)  # Default fallback

                    await attr(*args)

    async def counting_screen(self, counter: int):
        await self.lcd.message(f"{counter}")

    async def counter_done(self):
        await self.lcd.message("Done!")

    async def loading_screen_step(self, label: str, bar: str):
        await self.lcd.message(label, bar, "", "", display_time=0.1)
