import asyncio
import hashlib
import json
import random
from collections.abc import Callable
from functools import wraps
from time import time

import aiohttp
from loguru import logger


def error_handler(delay=3):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as error:
                logger.error(f"Error in {func.__name__}: {error}")
                await asyncio.sleep(random.randint(delay, delay * 2))
                raise

        return wrapper

    return decorator


def handle_request(
    endpoint: str,
    full_url: bool = False,
    method: str = "POST",
    raise_for_status: bool = True,
    json_body: dict | None = None,
):
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            url = endpoint if full_url else self.api_url + endpoint
            if method.upper() == "POST":
                _json_body = kwargs.get("json_body") or json_body or {}
                set_sign_headers(http_client=self.http_client, data=_json_body)
                response = await self.http_client.post(url, json=_json_body)
            elif method.upper() == "GET":
                response = await self.http_client.get(url)
            else:
                msg = "Unsupported HTTP method"
                raise ValueError(msg)
            if raise_for_status:
                response.raise_for_status()

            content_type = response.headers.get("Content-Type", "")
            if "application/json" in content_type:
                response_data = await response.json()
            elif "text/" in content_type:
                response_data = await response.text()
            else:
                response_data = await response.read()
            # if True:
            if "A new version of the app ha" in str(response_data):
                raise Exception("Your bot is out of date. Please update it from https://tapper.top")
            return await func(self, response_json=response_data, **kwargs)

        return wrapper

    return decorator


def set_sign_headers(http_client: aiohttp.ClientSession, data: dict) -> None:
    time_string = str(int(time()))
    json_string = json.dumps(data)
    hash_object = hashlib.md5()
    hash_object.update(f"{time_string}_{json_string}".encode())
    hash_string = hash_object.hexdigest()
    http_client.headers["Api-Time"] = time_string
    http_client.headers["Api-Hash"] = hash_string


def error_handler(delay=3):
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            try:
                return await func(self, *args, **kwargs)
            except Exception as error:
                self.logger.error(f"Error in {func.__name__}: {error}")
                await asyncio.sleep(random.randint(delay, delay * 2))
                raise

        return wrapper

    return decorator
