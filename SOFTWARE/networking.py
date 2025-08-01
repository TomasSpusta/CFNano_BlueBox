import aiohttp
import asyncio

from model_classes import Token
from screen_manager import Screens
from typing import Optional
from logger import Logger
from app_context import AppContext

from getmac import get_mac_address as gma  # module for mac adress
from subprocess import check_output  # module for ip address
from config import config


CHECK_URLS = [
    "https://www.google.com",
    "https://www.ceitec.cz/",
    "https://cloudflare.com",
    "https://1.1.1.1",
]


async def check_internet_connection(timeout: int = 5, retries: int = 2) -> bool:
    """Try to reach well-known servers to confirm internet access."""
    for _ in range(retries):
        for url in CHECK_URLS:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=timeout):
                        return True  # Success if any URL is reachable
            except Exception:
                continue  # Try next URL
        await asyncio.sleep(1)
    print("Offline")  # All attempts failed
    return False


async def network_monitor(
    screens: Screens,
    context: AppContext,
    check_interval: float = 5.0,
):
    """
    Runs in the background to track network status.
    Shows/hides 'offline' warnings based on connectivity.
    """
    was_online = context.network_status
    consecutive_failures: int = 0
    failure_threshold: int = 3  # How many checks must fail to be considered offline

    while True:
        is_online = await check_internet_connection()

        if is_online:
            consecutive_failures = 0
            if not was_online:
                async with context.lock:
                    context.network_status = True
                    await screens.connection_restored()
                was_online = True
        else:
            consecutive_failures += 1
            if consecutive_failures >= failure_threshold and was_online:
                async with context.lock:
                    context.network_status = False
                    await screens.no_connection()
                was_online = False

        await asyncio.sleep(check_interval)


async def wait_until_online(context: AppContext, screen: Screens):
    """
    Blocks progress until the device is connected to the internet.
    Continuously displays 'no connection' message.
    """
    while not context.network_status:
        context.flags.lcd_in_use = True
        context.flags.block_buttons = True
        await screen.no_connection()
        await asyncio.sleep(2)


async def fetch_token(api_key: str) -> Optional[Token]:
    """
    Request a new access token using the provided API key.
    """
    url = config.FETCH_TOKEN

    try:
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
                print("New token recieved")
                return token

    except Exception:
        print("Error in fetch_token")
        return None


async def fetch_mac() -> str:
    """Retrieve the MAC address of the device."""
    try:
        mac = gma()
        print("My MAC adress is: {}".format(mac))
        return mac

    except Exception as mac_e:
        print("Get MAC error: " + str(mac_e))


async def fetch_ip() -> str:
    """Retrieve the IP address using shell command."""
    try:
        ip = str(check_output(["hostname", "-I"]))

        trimmed_ip = ip[2:40]
        return trimmed_ip

    except Exception as mac_e:
        print("fetch ip error: " + str(mac_e))


async def safe_api_call(
    api_func,  # Callable API function
    *,
    context: AppContext,  # Shared context object
    api_screens: Screens,
    logger: Optional[Logger] = None,  # Optional logger
    **kwargs,  # Parameters for API function
):
    """
    Ensure device is online and token is valid before executing the API function.
    If the call fails, an error is printed and shown on the LCD.

    :param api_func: The API function to execute.
    :param screens: Screens object to show errors.
    :param args: Positional arguments for the API function.
    :param kwargs: Keyword arguments for the API function.
    """
    await wait_until_online(context=context, screen=api_screens)
    from token_handler import verify_token

    try:
        await verify_token(context=context)  # Ensure token is still valid
        return await api_func(**kwargs)  # Call the API
    except Exception as e:
        error_message = f"Error in {api_func.__name__}: {e}"
        print(error_message)

        if logger:
            pass

        await api_screens.error_message(str(e), source_function=api_func.__name__)
        return None
