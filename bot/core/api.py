import asyncio
import json
import random
from datetime import datetime
from typing import NamedTuple
from urllib.parse import parse_qs

import aiohttp
from aiocache import Cache, cached
from better_proxy import Proxy
from pyrogram import Client, errors
from pyrogram.errors import AuthKeyUnregistered, Unauthorized, UserDeactivated
from pyrogram.raw.functions.messages import RequestAppWebView
from pyrogram.raw.types import InputBotAppShortName
from pytz import UTC

from bot.config.logger import log
from bot.config.settings import config
from bot.helper.utils import error_handler, handle_request

from .errors import TapsError
from .models import FundHelper, Profile, ProfileData, PvpData, UserDataAfter
from .utils import num_prettier


class TgWebData(NamedTuple):
    hash: str
    request_data: dict


class CryptoBotApi:
    def __init__(self, tg_client: Client):
        self.session_name = tg_client.name
        self.tg_client = tg_client
        self.user_id = None
        self.api_url = "https://api.muskempire.io"
        self.need_quiz = False
        self.need_rebus = False
        self.rebus_key = ""
        self.errors = 0
        self.logger = log.bind(session_name=self.session_name)

    async def connect_to_tg_client(self):
        if not self.tg_client.is_connected:
            try:
                await self.tg_client.connect()
            except (Unauthorized, UserDeactivated, AuthKeyUnregistered) as error:
                raise RuntimeError(str(error)) from error

    async def get_tg_web_data(self, proxy: str | None) -> TgWebData:
        if proxy:
            proxy = Proxy.from_str(proxy)
            proxy_dict = {
                "scheme": proxy.protocol,
                "hostname": proxy.host,
                "port": proxy.port,
                "username": proxy.login,
                "password": proxy.password,
            }
        else:
            proxy_dict = None

        self.tg_client.proxy = proxy_dict

        try:
            await self.connect_to_tg_client()

            peer = await self.tg_client.resolve_peer(config.bot_name)

            web_view = await self.tg_client.invoke(
                RequestAppWebView(
                    peer=peer,
                    app=InputBotAppShortName(bot_id=peer, short_name="Game"),
                    platform="android",
                    write_allowed=True,
                    start_param=config.REF_ID,
                )
            )
            tg_web_data = parse_qs(web_view.url.split("#")[1]).get("tgWebAppData")[0]
            query_params = parse_qs(tg_web_data)
            await self.tg_client.disconnect()
            return TgWebData(
                request_data={
                    "data": {
                        "chatId": "",
                        "chatInstance": tg_web_data,
                        "chatType": query_params.get("chat_type")[0],
                        "initData": tg_web_data,
                        "platform": "android",
                        "startParam": config.REF_ID,
                    },
                },
                hash=query_params.get("hash")[0],
            )

        except RuntimeError as error:
            raise error from error

        except Exception as error:
            log.error(f"{self.session_name} | Authorization error: {error}")
            await asyncio.sleep(delay=3)

    async def join_and_archive_channel(self, channel_name: str) -> None:
        try:
            await self.connect_to_tg_client()

            chat = await self.tg_client.join_chat(channel_name)
            self.logger.info(f"Successfully joined to  <g>{chat.title}</g> successfully archived")
            await self.tg_client.archive_chats(chat_ids=[chat.id])
            self.logger.info(f"Channel <g>{chat.title}</g> successfully archived")

        except errors.FloodWait as e:
            self.logger.error(f"Waiting {e.value} seconds before the next attempt.")

            await asyncio.sleep(e.value)  # Wait before retrying

        except Exception as e:
            self.logger.error(f"An error occurred: {e}")

    async def sleeper(self, delay: int = config.RANDOM_SLEEP_TIME, additional_delay: int = 0) -> None:
        await asyncio.sleep(random.random() * delay + additional_delay)

    @error_handler()
    @handle_request("/telegram/auth")
    async def login(self, *, response_json: dict, json_body: dict) -> bool:
        if response_json.get("success", False):
            self.logger.success("Login successful")
            return True
        return False

    @error_handler()
    @handle_request("/dbs", json_body={"data": {"dbs": ["all"]}})
    async def get_dbs(self, *, response_json: dict) -> dict:
        return response_json["data"]

    @error_handler()
    @handle_request("/hero/balance/sync", json_body={"data": {}})
    async def syn_hero_balance(self, *, response_json: dict) -> Profile:
        self._update_money_balance(response_json)
        self.logger.info(
            f"Level: <blue>{self.level}</blue> | "
            f"Balance: <y>{num_prettier(self.balance)}</y> | "
            f"Money per hour: <g>{num_prettier(self.mph)}</g>"
        )
        return Profile(**response_json["data"])

    @error_handler()
    @handle_request("/user/data/all", json_body={"data": {}})
    async def get_profile_full(self, *, response_json: dict) -> ProfileData:
        return ProfileData(**response_json["data"])

    @error_handler()
    @handle_request("/user/data/after", json_body={"data": {"lang": "ru"}})
    async def user_data_after(self, *, response_json: dict) -> UserDataAfter:
        return UserDataAfter(**response_json["data"])

    @error_handler()
    @handle_request("/hero/bonus/offline/claim")
    async def get_offline_bonus(self, *, response_json: dict) -> None:
        self._update_money_balance(response_json)
        self.logger.success(f"Offline bonus claimed: <y>+{num_prettier(self.user_profile.offline_bonus)}</y>")

    @error_handler()
    @handle_request("/quests/daily/claim")
    async def daily_reward(self, *, response_json: dict, json_body: dict) -> None:
        self._update_money_balance(response_json)

    @error_handler()
    @handle_request("/quests/claim")
    async def quest_reward_claim(self, *, response_json: dict, json_body: dict) -> bool:
        self._update_money_balance(response_json)
        return True

    @error_handler()
    @handle_request("/quests/daily/progress/claim")
    async def daily_quest_reward(self, *, response_json: dict, json_body: dict) -> None:
        self._update_money_balance(response_json)

    @error_handler()
    @handle_request("/quests/daily/progress/all")
    async def all_daily_quests(self, *, response_json: dict) -> dict:
        return response_json["data"]

    @error_handler()
    @handle_request("/quests/check")
    async def quest_check(self, *, response_json: dict, json_body: dict) -> bool:
        await self.sleeper()
        await self.quest_reward_claim(json_body=json_body)

    @error_handler()
    @handle_request("/friends/claim")
    async def friend_reward(self, *, response_json: dict, json_body: dict) -> None:
        self._update_money_balance(response_json)

    @error_handler()
    @handle_request("/hero/action/tap")
    async def api_perform_taps(self, *, response_json: dict, json_body: dict) -> int:
        if (error_msg := response_json.get("error")) and "take some rest" in error_msg:
            raise TapsError(error_msg)
        data = self._update_money_balance(response_json)
        self.tapped_today = data.get("tappedToday", 0)
        return int(data["hero"]["earns"]["task"]["energy"])

    @cached(ttl=6 * 60 * 60, cache=Cache.MEMORY)
    @error_handler()
    @handle_request(
        "https://raw.githubusercontent.com/testingstrategy/musk_daily/main/daily.json",
        method="GET",
        full_url=True,
    )
    async def get_helper(self, *, response_json: str) -> FundHelper | dict:
        response_json = json.loads(response_json)
        return FundHelper(
            funds=response_json.get(str(datetime.now(UTC).date()), {}).get("funds", set()),
            **response_json,
        )

    @error_handler()
    @handle_request("/fund/info")
    async def get_funds_info(self, *, response_json: dict) -> dict:
        return response_json["data"]

    @error_handler()
    @handle_request("/box/list", json_body={})
    async def get_box_list(self, *, response_json: dict) -> dict:
        return response_json["data"] or {}

    @error_handler()
    @handle_request("/box/open")
    async def box_open(self, *, response_json: dict, json_body: dict) -> list:
        return response_json["data"]

    @error_handler()
    @handle_request("/pvp/info")
    async def get_pvp_info(self, *, response_json: dict) -> dict:
        return response_json["data"]

    @error_handler()
    @handle_request("/pvp/fight")
    async def get_pvp_fight(self, *, response_json: dict, json_body: dict) -> PvpData | None:
        if response_json["data"].get("opponent"):
            return PvpData(**response_json["data"])
        return None

    @error_handler()
    @handle_request("/pvp/claim")
    async def get_pvp_claim(self, *, response_json: dict) -> None:
        if response_json.get("success"):
            self._update_money_balance(response_json)

    @error_handler()
    @handle_request(
        "/settings/save",
        json_body={
            "data": {
                "id": None,
                "music": False,
                "sound": True,
                "vibrate": True,
                "animations": True,
                "darkTheme": True,
                "lang": "en",
            }
        },
    )
    async def sent_eng_settings(self, *, response_json: dict) -> None: ...

    @error_handler()
    @handle_request("/fund/invest")
    async def invest(self, *, response_json: dict, json_body: dict) -> None:
        data = self._update_money_balance(response_json)
        for fnd in data["funds"]:
            if fnd["fundKey"] == json_body["data"]["fund"]:
                money = fnd["moneyProfit"]
                money_str = f"Win: <y>+{money}</y>" if money > 0 else f"Loss: <red>{money}</red>"
                self.logger.success(f"Invest completed: {money_str}")
                break

    @error_handler()
    @handle_request("/skills/improve")
    async def skills_improve(self, *, response_json: dict, json_body: dict) -> None:
        self._update_money_balance(response_json)

    async def check_proxy(self, proxy: Proxy) -> None:
        try:
            response = await self.http_client.get(url="https://httpbin.org/ip", timeout=aiohttp.ClientTimeout(10))
            ip = (await response.json()).get("origin")
            self.logger.info(f"Proxy IP: {ip}")
        except Exception:
            self.logger.exception(f"Proxy: {proxy}")

    def _update_money_balance(self, response_json: dict) -> dict:
        response_json = response_json["data"]
        self.balance = int(response_json["hero"]["money"])
        self.level = int(response_json["hero"]["level"])
        self.mph = int(response_json["hero"]["moneyPerHour"])
        return response_json
