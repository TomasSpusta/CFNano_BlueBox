from typing import Optional
from model_classes import User, Instrument, Reservation, Token
import config
import unidecode
import aiohttp


class APIClient:
    async def fetch_instrument_data(self, mac: str, ip: str) -> Optional[Instrument]:
        print("Instrument data: Fetching...")
        url = config.EQUIPMENT_BY_MAC

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json={"mac_address": mac}) as response:
                    if response.status != 200:
                        print(f"Response status {response.status}")
                        error_content = await response.json()
                        print(f"Error content {error_content}")
                        error_message = error_content.get("message")
                        print(f"Message: {error_message}")
                        return None

                    response_json = await response.json()
                    # print(f"Response from instrument: {response_json}")

                    if not response_json:
                        print("Empty response from api")
                        return None

                    instrument = Instrument(
                        id=response_json[0]["equipmentid"],
                        name=response_json[0]["alias"],
                        mac_address=mac,
                        ip=ip,
                    )
                    print("Instrument data: Fetched.")
                    return instrument

        except Exception:
            print("Error in fetch instrument")
            return None

    async def fetch_token(self) -> Optional[Token]:
        api_key = config.API_KEY
        url = config.FETCH_TOKEN

        try:
            print("Token API call")
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json={"apiKey": api_key}) as response:
                    if response.status != 200:
                        print(f"Response status {response.status}")
                        error_content = await response.json()
                        print(f"Error content {error_content}")
                        error_message = error_content.get("message")
                        print(f"Message: {error_message}")
                        return None

                    response_json = await response.json()

                    if not response_json:
                        print("Empty response from api")
                        return None

                    token = Token(
                        string=response_json["accessToken"],
                        expiration=response_json["expiresAt"],
                    )
                    # print("New token recieved")
                    return token

        except Exception:
            print("Error in fetch_token")
            return None

    async def fetch_user_data(self, card_id) -> Optional[User]:
        print("User data: Fetching...")
        url = config.CONTACT_BY_RFID

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json={"rfid": card_id}) as response:
                    if response.status != 200:
                        print(f"Response status {response.status}")
                        error_content = await response.json()
                        print(f"Error content {error_content}")
                        error_message = error_content.get("message")
                        print(f"Message: {error_message}")
                        return None

                    response_json = await response.json()
                    # print(f"Response from user: {response_json}")

                    if not response_json:
                        print("Empty response from api")
                        return None

                    name = response_json[0]["firstname"]
                    full_name = response_json[0]["full_name"]
                    name_non_dia = unidecode.unidecode(name)
                    user = User(
                        id=response_json[0]["contactid"],
                        name=name_non_dia,
                        card_id=card_id,
                        full_name=full_name,
                    )
                print("User data: Fetched.")
                return user

        except Exception:
            print("Error in fetch user")
            return None

    async def start_extend_reservation(
        self,
        user: User,
        instrument: Instrument,
        token: Token,  # session: Session
    ) -> Optional[Reservation]:
        print("Recording START/EXTEND: API Call...")
        payload = {"contactId": user.id, "equipmentId": instrument.id}
        headers = {"Authorization": "Bearer " + token.string}
        url = config.RECORDING_START
        try:
            async with aiohttp.ClientSession() as http_session:
                async with http_session.post(
                    url=url, json=payload, headers=headers
                ) as response:
                    if response.status != 200:
                        error_content = await response.json()
                        error_message = error_content.get("status")
                        print(f"Message: {error_message}")
                        return None
                    else:
                        response_content = await response.json()

                        session = Reservation(
                            recording_id=response_content["recording"],
                            reservation_id=response_content["reservation"],
                            remaining_time=int(response_content["timetoend"]),
                        )
                        print("Recording START/EXTEND: Started/Extended.")
                        print(f"Message: {response_content}")
                        return session

        except aiohttp.ClientError:
            print("Error in start_recording")

    async def fetch_recording_info(
        self, token: Token, reservation: Reservation
    ) -> Optional[Reservation]:
        # print("Recording Info: API Call...")
        headers = {"Authorization": "Bearer " + token.string}
        url = config.RECORDING_INFO.format(reservation_id=reservation.reservation_id)
        try:
            async with aiohttp.ClientSession() as http_session:
                async with http_session.get(url=url, headers=headers) as response:
                    if response.status != 200:
                        error_content = await response.json()
                        error_message = error_content.get("status")
                        print(
                            f"Recording info status {error_content}, message: {error_message}"
                        )
                    else:
                        response_content = await response.json()
                        reservation.remaining_time = int(response_content["timetoend"])

                        return reservation

        except aiohttp.ClientError:
            print("Error in fetch_recording_info")

    async def stop_reservation(
        self, reservation: Reservation, instrument: Instrument, token: Token
    ):
        print("Recording STOP: API Call...")

        payload = {
            "serviceAppointmentId": reservation.reservation_id,
            "equipmentId": instrument.id,
        }
        headers = {"Authorization": "Bearer " + token.string}
        url = config.RECORDING_STOP

        try:
            async with aiohttp.ClientSession() as http_session:
                async with http_session.post(
                    url=url, json=payload, headers=headers
                ) as response:
                    if response.status != 200:
                        error_content = await response.json()
                        error_message = error_content.get("status")
                        print(f"Message: {error_message}")
                        return None
                    else:
                        # response_content = await response.json()
                        # status_message = response_content.get("status")
                        # print(f"Stop reservation Message: {status_message}")
                        print("Recording STOP: Recording Stopped.")

        except aiohttp.ClientError:
            print("Error in stop_recording")
