from dataclasses import dataclass


@dataclass
class User:
    id: str = ""
    name: str = ""
    full_name: str = ""
    card_id: str = ""


@dataclass
class Instrument:
    id: str = ""
    name: str = ""
    mac_address: str = ""
    ip: str = ""


@dataclass
class Reservation:
    remaining_time: int = 0
    recording_id: str = ""
    reservation_id: str = ""
    warning_sent = False
    ended_by_user = False
    ended_by_time = False


class Token:
    def __init__(self, string: str, expiration: str):
        self.string = string
        self.expiration = expiration

    def to_dict(self):
        return {"string": self.string, "expiration": self.expiration}
