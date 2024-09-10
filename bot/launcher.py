import asyncio
import random
from argparse import ArgumentParser
from itertools import cycle
from pathlib import Path
from typing import NamedTuple

from better_proxy import Proxy
from pyrogram import Client

from bot.config.logger import log
from bot.config.settings import config, logo
from bot.core.bot import run_bot
from bot.utils import get_session_profiles

start_text = """
    Select an action:
        1. Create session
        2. Run bot
    """


class SessionData(NamedTuple):
    tg_client: Client
    session_data: dict


def get_session_names() -> list[str]:
    return [file.stem for file in sorted(Path("sessions").glob("*.session"))]


async def register_sessions() -> None:
    session_name = input("\nEnter the session name (press Enter to exit): ")
    if not session_name:
        return

    sessions_path = Path("sessions")
    if not sessions_path.exists():
        sessions_path.mkdir()

    session = Client(
        name=session_name,
        api_id=config.API_ID,
        api_hash=config.API_HASH,
        workdir="sessions/",
    )

    async with session:
        user_data = await session.get_me()
    log.success(
        f"Session added successfully: {user_data.username or user_data.id} | "
        f"{user_data.first_name or ''} {user_data.last_name or ''}"
    )


def get_proxies() -> [str | None]:
    if config.USE_PROXY_FROM_FILE:
        with Path("proxies.txt").open(encoding="utf-8") as file:
            return [Proxy.from_str(proxy=row.strip()).as_url for row in file if row.strip()]
    return None


async def get_tg_clients() -> list[SessionData]:
    session_names = get_session_names()

    if not session_names:
        msg = "Not found session files"
        raise FileNotFoundError(msg)
    session_profiles = get_session_profiles(session_names)
    return [
        SessionData(
            tg_client=Client(
                name=session_name,
                api_id=config.API_ID,
                api_hash=config.API_HASH,
                workdir="sessions/",
            ),
            session_data=session_profiles[session_name],
        )
        for session_name in session_names
    ]


async def run_bot_with_delay(tg_client: Client, proxy: str | None, additional_data: dict, session_index: int) -> None:
    delay = session_index * config.SESSION_AC_DELAY + random.randint(*config.SLEEP_BETWEEN_START)
    log.bind(session_name=tg_client.name).info(f"Wait {delay} seconds before start")
    await asyncio.sleep(delay)
    await run_bot(tg_client=tg_client, proxy=proxy, additional_data=additional_data)


async def run_clients(session_data: list[SessionData]) -> None:
    proxies = get_proxies() or [None]
    if config.ADD_LOCAL_MACHINE_AS_IP:
        proxies.append(None)
    proxy_cycle = cycle(proxies)
    await asyncio.gather(
        *[
            run_bot_with_delay(
                tg_client=s_data.tg_client,
                proxy=next(proxy_cycle),
                additional_data=s_data.session_data,
                session_index=index,
            )
            for index, s_data in enumerate(session_data)
        ]
    )


async def start() -> None:
    print(logo)
    parser = ArgumentParser()
    parser.add_argument("-a", "--action", type=int, choices=[1, 2], help="Action to perform  (1 or 2)")
    log.info(f"Detected {len(get_session_names())} sessions | {len(proxy) if (proxy := get_proxies()) else 0} proxies")
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
        session_data = await get_tg_clients()
        await run_clients(session_data=session_data)
