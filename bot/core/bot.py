import asyncio
import math
import random
import time
from collections.abc import Generator
from datetime import datetime

import aiohttp
from aiohttp_proxy import ProxyConnector
from pyrogram import Client
from pytz import UTC

from bot.config.headers import headers
from bot.config.logger import log
from bot.config.settings import config

from .api import CryptoBotApi
from .bet_counter import BetCounter
from .errors import TapsError
from .models import DbSkill, DbSkills, Profile, ProfileData, QuizHelper, SkillLevel


class CryptoBot(CryptoBotApi):
    def __init__(self, tg_client: Client):
        super().__init__(tg_client)
        self.temporary_stop_taps_time = 0
        self.bet_calculator = BetCounter(self)
        self.authorized = False

    async def claim_daily_reward(self) -> None:
        daily_index = None
        for day, status in self.user_profile.daily_rewards.items():
            if status == "canTake":
                daily_index = day
                break
        if daily_index is not None:
            self.logger.info("Daily reward available")
            daily_claimed = await self.daily_reward(json_body={"data": str(daily_index)})
            if daily_claimed:
                self.logger.success("Daily reward claimed")
                self.errors = 0
        else:
            self.logger.info("Daily reward not available")

    async def perform_taps(self, profile: Profile) -> None:
        self.logger.info("Taps started")
        energy = profile.energy
        while True:
            taps_per_second = random.randint(*config.TAPS_PER_SECOND)
            seconds = random.randint(5, 8)
            earned_money = profile.money_per_tap * taps_per_second * seconds
            energy_spent = math.ceil(earned_money / 2)
            energy -= energy_spent
            if energy < 0:
                self.logger.info("Taps stopped (not enough energy)")
                break
            await asyncio.sleep(delay=seconds)
            try:
                json_data = {
                    "data": {"data": {"task": {"amount": earned_money, "currentEnergy": energy}}, "seconds": seconds}
                }
                energy = await self.api_perform_taps(json_body=json_data)
                self.logger.success(
                    f"Earned money: <yellow>+{earned_money}</yellow> | Energy left: <blue>{energy}</blue>"
                )
            except TapsError as e:
                self.logger.warning(f"Taps stopped (<red>{e.message}</red>)")
                self.temporary_stop_taps_time = time.monotonic() + 60 * 60 * 3
                break

    async def _perform_pvp(self, league: dict, strategy: str, count: int) -> None:
        self.logger.info(
            f"PvP negotiations started | League: <blue>{league['key']}</blue> | Strategy: <green>{strategy}</green>"
        )
        await self.get_pvp_info()
        await self.get_pvp_claim()
        await self.sleeper()
        current_strategy = strategy
        money = 0
        while count > 0:
            if self.balance < int(league["maxContract"]):
                money_str = f"Profit: <yellow>+{money}</yellow>" if money >= 0 else f"Loss: <red>-{money}</red>"
                self.logger.info(f"PvP negotiations stopped (<red>not enough money</red>). Pvp profit: {money_str}")
                break

            if strategy == "random":
                current_strategy = random.choice(self.strategies)
            self.logger.info("Searching opponent...")
            json_data = {"data": {"league": league["key"], "strategy": current_strategy}}
            response_json = await self.get_pvp_fight(json_body=json_data)
            if response_json is None:
                await self.sleeper(delay=10, additional_delay=5)
                continue

            await self.sleeper()
            count -= 1

            fight = response_json.fight
            opponent_strategy = (
                fight.player2Strategy if fight.player1 == self.user_profile.user_id else fight.player1Strategy
            )
            if fight.winner == self.user_id:
                money += fight.moneyProfit
                log_part = f"You WIN (<yellow>+{fight.moneyProfit})</yellow>"
            else:
                money -= fight.moneyContract
                log_part = f"You <red>LOSE</red> (<yellow>-{fight.moneyProfit}</yellow>)"
            self.logger.success(
                f"Contract sum: <yellow>{fight.moneyContract}</yellow> | "
                f"Your strategy: <cyan>{current_strategy}</cyan> | "
                f"Opponent strategy: <blue>{opponent_strategy}</blue> | "
                f"{log_part}"
            )

            await self.get_pvp_claim()

            await self.sleeper()
            money_str = f"Profit: +{money}" if money > 0 else (f"Loss: {money}" if money < 0 else "Profit: 0")
        self.logger.info(f"PvP negotiations finished. {money_str}")

    async def get_friend_reward(self) -> None:
        unrewarded_friends = [friend for friend in self.user_profile.friends if friend["bonusToTake"] > 0]
        if unrewarded_friends:
            self.logger.info("Reward for friends available")
            for friend in unrewarded_friends:
                await self.friend_reward(json_body={"data": friend["id"]})

    async def solve_quiz_and_rebus(self) -> None:
        for quest in self.dbs["dbQuests"]:
            quest_key = quest["key"]
            if any(i in quest_key for i in ("riddle", "rebus")) and not self._is_event_solved(quest_key):
                await self.solve_rebus(json_body={"data": [quest_key, quest["checkData"]]})
                self.logger.info(f"Was solved <green>{quest['title']}</green>")

    def _is_event_solved(self, quest_key: str) -> bool:
        return any(i["key"] == quest_key for i in self.user_profile.quests)

    async def set_funds(self, helper: QuizHelper) -> None:
        if helper.funds:
            current_invest = await self.get_funds_info()
            already_funded = {i["fundKey"] for i in current_invest["funds"]}
            for fund in list(helper.funds - already_funded)[: 3 - len(already_funded)]:
                if self.balance > (amount := self.bet_calculator.calculate_bet()):
                    await self.invest({"data": {"fund": fund, "money": amount}})
                else:
                    self.logger.info("Not enough money for invest")

    async def starting_pvp(self) -> None:
        if self.dbs:
            league_data = None
            for league in self.dbs["dbNegotiationsLeague"]:
                if league["key"] == config.PVP_LEAGUE:
                    league_data = league
                    break

            if league_data is not None:
                if self.level >= int(league_data["requiredLevel"]):
                    self.strategies = [strategy["key"] for strategy in self.dbs["dbNegotiationsStrategy"]]
                    if config.PVP_STRATEGY == "random" or config.PVP_STRATEGY in self.strategies:
                        await self._perform_pvp(
                            league=league_data, strategy=config.PVP_STRATEGY, count=config.PVP_COUNT
                        )
                    else:
                        config.PVP_ENABLED = False
                        self.logger.warning("PVP_STRATEGY param is invalid. PvP negotiations disabled.")
                else:
                    config.PVP_ENABLED = False
                    self.logger.warning(
                        f"Your level is too low for the {config.PVP_LEAGUE} league. PvP negotiations disabled."
                    )
            else:
                config.PVP_ENABLED = False
                self.logger.warning("PVP_LEAGUE param is invalid. PvP negotiations disabled.")
        else:
            self.logger.warning("Database is missing. PvP negotiations will be skipped this time.")

    async def upgrade_hero(self) -> None:
        skills = sorted(self._get_available_skills(), key=lambda x: x.weight, reverse=True)
        for skill in skills:
            if (self.balance - skill.skill_price) >= config.MONEY_TO_SAVE:
                await self.skills_improve(json_body={"data": skill.key})
                self.logger.info(
                    f"Skill: <blue>{skill.title}</blue> upgraded to level: <cyan>{skill.next_level}</cyan> "
                    f"Profit: <yellow>{skill.skill_profit}</yellow> "
                    f"Costs: <blue>{skill.skill_price}</blue> "
                    f"Money stay: <yellow>{self.balance}</yellow> "
                    f"Skill weight <magenta>{skill.weight:.5f}</magenta>"
                )
                await self.sleeper()

    def _get_available_skills(self) -> Generator[DbSkill, None, None]:
        for skill in DbSkills(**self.dbs).dbSkills:
            if self._is_available_to_upgrade(skill):
                yield skill

    def _is_available_to_upgrade(self, skill: DbSkill) -> bool:
        skill.next_level = (
            self.user_profile.skills[skill.key]["level"] + 1 if self.user_profile.skills.get(skill.key) else 1
        )
        skill.skill_profit = skill.calculate_profit(skill.next_level)
        skill.skill_price = skill.price_for_level(skill.next_level)
        skill.weight = skill.skill_profit / skill.skill_price
        # check the current skill is still in the process of improvement
        if (finsh_time := self.user_profile.skills.get(skill.key, {}).get("finishUpgradeDate")) and datetime.now(
            UTC
        ) > datetime.strptime(finsh_time, "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC):
            return False
        skill_requirements = skill.get_level_by_skill_level(skill.next_level)
        if not skill_requirements:
            return True
        return (
            len(self.user_profile.friends) >= skill_requirements.requiredFriends
            and self.user_profile.level >= skill_requirements.requiredHeroLevel
            and self._is_can_learn_skill(skill_requirements)
            and skill.weight >= config.SKILL_WEIGHT
        )

    def _is_can_learn_skill(self, level: SkillLevel) -> bool:
        if not level.requiredSkills:
            return True
        for skill, level in level.requiredSkills.items():
            if skill not in self.user_profile.skills:
                return False
            if self.user_profile.skills[skill]["level"] >= level:
                return True
        return False

    async def login_to_app(self, proxy: str | None) -> bool:
        if self.authorized:
            return True
        tg_web_data = await self.get_tg_web_data(proxy=proxy)
        self.http_client.headers["Api-Key"] = tg_web_data.hash
        if await self.login(json_body=tg_web_data.request_data):
            self.authorized = True
            return True
        return False

    async def run(self, proxy: str | None) -> None:
        proxy_conn = ProxyConnector().from_url(proxy) if proxy else None

        async with aiohttp.ClientSession(headers=headers, connector=proxy_conn) as http_client:
            self.http_client = http_client
            if proxy:
                await self.check_proxy(proxy=proxy)

            while True:
                if self.errors >= config.ERRORS_BEFORE_STOP:
                    self.logger.error("Bot stopped (too many errors)")
                    break
                try:
                    if await self.login_to_app(proxy):
                        self.dbs = await self.get_dbs()

                        self.user_profile: ProfileData = await self.get_profile_full()
                        if self.user_profile.offline_bonus > 0:
                            await self.get_offline_bonus()
                    else:
                        continue

                    profile = await self.syn_hero_balance()

                    config.MONEY_TO_SAVE = self.bet_calculator.max_bet()

                    if config.PVP_ENABLED:
                        await self.starting_pvp()

                    if config.AUTO_UPGRADE:
                        await self.upgrade_hero()

                    await self.claim_daily_reward()

                    await self.get_friend_reward()

                    if config.TAPS_ENABLED and profile.energy and time.monotonic() > self.temporary_stop_taps_time:
                        await self.perform_taps(profile)

                    if helper := await self.get_helper():
                        await self.set_funds(helper)
                        await self.solve_quiz_and_rebus()

                    await self.syn_hero_balance()

                    sleep_time = random.randint(*config.BOT_SLEEP_TIME)
                    self.logger.info(f"Sleep minutes {sleep_time // 60} minutes")
                    await asyncio.sleep(sleep_time)

                except RuntimeError as error:
                    raise error from error
                except Exception:
                    self.errors += 1
                    self.logger.exception("Unknown error")
                    await self.sleeper()
                else:
                    self.authorized = False
                    self.errors = 0


async def run_bot(tg_client: Client, proxy: str | None) -> None:
    try:
        await CryptoBot(tg_client=tg_client).run(proxy=proxy)
    except RuntimeError:
        log.bind(session_name=tg_client.name).exception("Session error")
