import asyncio
import random
from argparse import ArgumentParser
from itertools import cycle
from pathlib import Path

from better_proxy import Proxy
from pyrogram import Client

from bot.config.logger import log
from bot.config.settings import config, logo
from bot.core.bot import run_bot

start_text = (
    logo
    + """
Select an action:
    1. Create session
    2. Run bot
"""
)


def get_session_names() -> list[str]:
    session_path = Path("sessions")
    session_files = session_path.glob("*.session")
    return [file.stem for file in session_files]


async def register_sessions() -> None:
    session_name = input("\nEnter the session name (press Enter to exit): ")
    if not session_name:
        return

    sessions_path = Path("sessions")
    if not sessions_path.exists():
        sessions_path.mkdir()

    session = Client(name=session_name, api_id=config.API_ID, api_hash=config.API_HASH, workdir="sessions/")

    async with session:
        user_data = await session.get_me()
    log.success(
        f"Session added successfully: {user_data.username or user_data.id} | "
        f"{user_data.first_name or ''} {user_data.last_name or ''}"
    )


def get_proxies() -> list:
    if config.USE_PROXY_FROM_FILE:
        with Path("proxies.txt").open() as file:
            return [Proxy.from_str(proxy=row.strip()).as_url for row in file if row.strip()]
    return []


async def get_tg_clients() -> list[Client]:
    session_names = get_session_names()

    if not session_names:
        raise FileNotFoundError("Not found session files")

    return [
        Client(
            name=session_name,
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            workdir="sessions/",
        )
        for session_name in session_names
    ]


async def run_bot_with_delay(tg_client, proxy, delay):
    if delay > 0:
        log.bind(session_name=tg_client.name).info(f"Wait {delay} seconds before start")
        await asyncio.sleep(delay)
    await run_bot(tg_client=tg_client, proxy=proxy)


async def run_clients(tg_clients: list[Client]):
    proxies = get_proxies()
    proxies_cycle = cycle(proxies) if proxies else cycle([None])
    tasks = []
    delay = 0
    for index, tg_client in enumerate(tg_clients):
        if index > 0:
            delay = random.randint(*config.SLEEP_BETWEEN_START)
        proxy = next(proxies_cycle)
        task = asyncio.create_task(run_bot_with_delay(tg_client=tg_client, proxy=proxy, delay=delay))
        tasks.append(task)
    await asyncio.gather(*tasks)


async def start() -> None:
    if not config:
        log.warning("Please fix the above errors in the .env file")
        return
    parser = ArgumentParser()
    parser.add_argument("-a", "--action", type=int, choices=[1, 2], help="Action to perform  (1 or 2)")
    log.info(f"Detected {len(get_session_names())} sessions | {len(get_proxies())} proxies")
    action = parser.parse_args().action

    if not action:
        print(start_text)
        while True:
            action = input("> ").strip()
            if action.isdigit() and action in ["1", "2"]:
                action = int(action)
                break
            log.warning("Action must be a number (1 or 2)")

    if action == 1:
        await register_sessions()
    elif action == 2:
        tg_clients = await get_tg_clients()
        await run_clients(tg_clients=tg_clients)
