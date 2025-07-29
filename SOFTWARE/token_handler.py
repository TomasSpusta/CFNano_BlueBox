from model_classes import Token
from app_context import AppContext
from datetime import datetime, timedelta
from pathlib import Path
from networking import fetch_token
import json

# from typing import Optional
from config import config

TOKEN_FILE = config.TOKEN_FILE  # Path to JSON file that stores the token
API_KEY = config.API_KEY  # API key used to fetch token


async def load_token(TOKEN_FILE: Path) -> Token | None:
    """
    Load a saved token from disk. Returns a Token object if successful, otherwise None.
    """

    if TOKEN_FILE.exists():
        try:
            data = json.loads(TOKEN_FILE.read_text())
            return Token(string=data["string"], expiration=data["expiration"])
        except Exception as e:
            print(f"[TokenHandler] Error loading token: {e}")
    return None


async def save_token(token: Token, TOKEN_FILE: Path):
    """
    Save a token object as a JSON file on disk.
    """
    try:
        TOKEN_FILE.write_text(json.dumps(token.to_dict()))
        print("[TokenHandler] New token saved.")
    # print("Saving token...")
    except Exception as e:
        print(f"[TokenHandler] Failed to save token: {e}")


async def verify_token(context: AppContext) -> Token:
    """
    Verifies whether the current token is valid and updates it in the application context.
    If no valid token is found, fetches a new one.
    """
    token = await load_token(TOKEN_FILE)

    needs_refresh = token is None or not await check_expiration(token)

    if needs_refresh:
        print("[TokenHandler] Token missing or expired — fetching new one.")
        token = await fetch_token(API_KEY)
        await save_token(token, TOKEN_FILE)

    context.token = token
    return token


async def check_expiration(token: Token) -> bool:
    """
    Checks if a token is expired or close to expiration (5 min buffer).
    """
    try:
        time_now_with_buffer = datetime.now() + timedelta(minutes=5)
        token_expiration_formated = datetime.fromisoformat(token.expiration)

        if token_expiration_formated < time_now_with_buffer:
            print("Token Expired")
            return False
        else:
            return True

    except Exception as e:
        print("Error in checking_token: " + str(e))
        return False
