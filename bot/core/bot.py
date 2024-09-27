import asyncio
import math
import random
import time
from collections.abc import Generator
from datetime import datetime
from enum import Enum

import aiohttp
from aiohttp_proxy import ProxyConnector
from aiohttp_socks import ProxyConnector as SocksProxyConnector
from pyrogram import Client
from pytz import UTC

from bot.config.headers import headers
from bot.config.logger import log
from bot.config.settings import Strategy, config
from bot.core.api_js_helpers.bet_counter import BetCounter

from .api import CryptoBotApi
from .errors import TapsError
from .models import DbSkill, DbSkills, Profile, ProfileData, SessionData, SkillLevel
from .utils import load_codes_from_files, num_prettier


class CryptoBot(CryptoBotApi):
    def __init__(self, tg_client: Client, additional_data: dict) -> None:
        super().__init__(tg_client)
        self.temporary_stop_taps_time = 0
        self.bet_calculator = BetCounter(self)
        self.pvp_count = config.PVP_COUNT
        self.authorized = False
        self.settings_was_set = False
        self.sleep_time = config.BOT_SLEEP_TIME
        self.additional_data: SessionData = SessionData.model_validate(
            {k: v for d in additional_data for k, v in d.items()}
        )

    async def claim_daily_reward(self) -> None:
        for day, status in self.data_after.daily_rewards.items():
            if status == "canTake":
                await self.daily_reward(json_body={"data": str(day)})
                self.logger.success("Daily reward claimed")
                return

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
                    "data": {
                        "data": {"task": {"amount": earned_money, "currentEnergy": energy}},
                        "seconds": seconds,
                    }
                }
                energy = await self.api_perform_taps(json_body=json_data)
                self.logger.success(
                    f"Earned money: <y>+{num_prettier(earned_money)}</y> | Energy left: <blue>{num_prettier(energy)}</blue>"
                )
            except TapsError as e:
                self.logger.warning(f"Taps stopped (<red>{e.message}</red>)")
                self.temporary_stop_taps_time = time.monotonic() + 60 * 60 * 3
                break

    async def execute_and_claim_daily_quest(self) -> None:
        helper_data = await self.get_helper()
        helper_data.youtube.update(load_codes_from_files())
        all_daily_quests = await self.all_daily_quests()
        for key, value in all_daily_quests.items():
            desc = value.get("description") or value.get("title") or value.get("key") or "Unknown Quest"
            try:
                if value["type"] == "youtube":
                    if not value["isRewarded"]:
                        code = helper_data.youtube.get(desc)
                        if code is not None:
                            await self.daily_quest_reward(json_body={"data": {"quest": key, "code": str(code)}})
                            self.logger.info(f"Quest <g>{desc}</g> claimed")
                        else:
                            self.logger.warning(f"No code found for quest: {desc}")
                    else:
                        self.logger.info(f"Quest <g>{desc}</g> already rewarded")
                elif not value["isRewarded"]:
                    self.logger.info(f"Quest not executed: \n<r>{desc}</r>")
                else:
                    self.logger.info(f"Quest <g>{desc}</g> already rewarded")
            except Exception as e:
                self.logger.error(f"Error processing quest {desc}: {e}")

    async def claim_all_executed_quest(self) -> None:
        for i in self.data_after.quests:
            if not i["isRewarded"]:
                if config.SKIP_IMPROVE_DISCIPLINE_BUG and i["key"] == "improve_discipline":
                    continue
                await self.quest_reward_claim(json_body={"data": [i["key"], None]})
                self.logger.info(f'Quest <g>{i["key"]}</g> claimed ')

    def random_pvp_count(self) -> int:
        return random.randint(config.PVP_COUNT, config.PVP_COUNT * 2)

    async def _perform_pvp(self, league: dict, strategy: str) -> None:
        self.pvp_count = self.random_pvp_count()
        self.logger.info(
            f"PvP negotiations started | League: <blue>{league['key']}</blue> | Strategy: <g>{strategy}</g>"
        )
        res = await self.get_pvp_info()
        await self.sleeper()
        if res.get("fight"):
            await self.get_pvp_claim()
            await self.sleeper()
        current_strategy = strategy
        money = 0
        while self.pvp_count > 0:
            if self.balance < int(league["maxContract"]):
                money_str = (
                    f"Profit: <y>+{num_prettier(money)}</y>"
                    if money >= 0
                    else f"Loss: <red>-{num_prettier(money)}</red>"
                )
                self.logger.info(f"PvP negotiations stopped (<red>not enough money</red>). Pvp profit: {money_str}")
                break

            if strategy == "random":
                current_strategy = random.choice(self.strategies)
            self.logger.info("Searching opponent...")
            current_strategy = current_strategy.value if isinstance(current_strategy, Enum) else current_strategy
            json_data = {"data": {"league": league["key"], "strategy": current_strategy}}
            response_json = await self.get_pvp_fight(json_body=json_data)
            if response_json is None:
                await self.sleeper(delay=10, additional_delay=5)
                continue

            fight = response_json.fight
            opponent_strategy = (
                fight.player2Strategy if fight.player1 == self.user_profile.user_id else fight.player1Strategy
            )
            if fight.winner == self.user_profile.user_id:
                money += fight.moneyProfit
                log_part = f"You <g>WIN</g> (<y>+{num_prettier(fight.moneyProfit)})</y>"
            else:
                money -= fight.moneyContract
                log_part = f"You <red>LOSE</red> (<y>-{num_prettier(fight.moneyProfit)}</y>)"
            self.logger.success(
                f"Contract sum: <y>{num_prettier(fight.moneyContract)}</y> | "
                f"Your strategy: <c>{current_strategy}</c> | "
                f"Opponent strategy: <blue>{opponent_strategy}</blue> | "
                f"{log_part}"
            )
            await self.sleeper(additional_delay=10)
            await self.get_pvp_claim()
            self.pvp_count -= 1
            await self.sleeper()

        self.logger.info(
            "Total money after all pvp:"
            + (f"<i><g>+{num_prettier(money)}</g></i>" if money >= 0 else f"<i><red>{num_prettier(money)}</red></i>")
        )
        self.pvp_count = config.PVP_COUNT

    async def get_friend_reward(self) -> None:
        for friend in [friend for friend in self.data_after.friends if friend["bonusToTake"] > 0]:
            await self.friend_reward(json_body={"data": friend["id"]})
            self.logger.info(
                f"Friend <g>{friend['name']}</g> claimed money <y>{num_prettier(friend['bonusToTake'])}</y>"
            )
            await self.sleeper()

    async def solve_quiz_and_rebus(self) -> None:
        for quest in self.dbs["dbQuests"]:
            quest_key = quest["key"]
            if quest["requiredLevel"] > self.user_profile.level:
                continue
            if "t.me" in (link := quest.get("actionUrl")) and not self._is_event_solved(quest_key):
                if len(link.split("/")) > 4 or "muskempire" in link:
                    continue
                if quest["checkType"] != "fakeCheck":
                    link = link if "/+" in link else link.split("/")[-1]
                    await self.join_and_archive_channel(link)
                await self.quest_check(json_body={"data": [quest_key]})
                self.logger.info(
                    f'Claimed <g>{quest["title"]}</g> Reward: <y>+{num_prettier(quest["rewardMoney"])}</y>quest'
                )
            if any(i in quest_key for i in ("riddle", "rebus", "tg_story")) and not self._is_event_solved(quest_key):
                await self.quest_check(json_body={"data": [quest_key, quest["checkData"]]})
                self.logger.info(f"Was solved <g>{quest['title']}</g>")

    def _is_event_solved(self, quest_key: str) -> bool:
        return self.data_after.quests and any(i["key"] == quest_key for i in self.data_after.quests)

    async def set_funds(self) -> None:
        helper_data = await self.get_helper()
        if helper_data.funds:
            current_invest = await self.get_funds_info()
            already_funded = {i["fundKey"] for i in current_invest["funds"]}
            for fund in list(helper_data.funds - already_funded)[: 3 - len(already_funded)]:
                if self.balance > (amount := self.bet_calculator.calculate_bet()):
                    self.logger.info(f"Investing <y>{num_prettier(amount)}</y> to  fund <blue>{fund}</blue>")
                    await self.invest(json_body={"data": {"fund": fund, "money": amount}})
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
                    if Strategy.random == config.PVP_STRATEGY or config.PVP_STRATEGY in self.strategies:
                        await self._perform_pvp(
                            league=league_data,
                            strategy=config.PVP_STRATEGY.value,
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
        available_skill = list(self._get_available_skills())
        if config.AUTO_UPGRADE_HERO:
            await self._upgrade_hero_skill(available_skill)
        if config.AUTO_UPGRADE_MINING:
            await self._upgrade_mining_skill(available_skill)

    async def get_box_rewards(self) -> None:
        boxes = await self.get_box_list()
        for key, box_count in boxes.items():
            for _ in range(box_count):
                res = await self.box_open(json_body={"data": key})
                self.logger.info(f"Box <g>{key}</g> Was looted: <y>{res['loot']}</y>")

    async def _upgrade_mining_skill(self, available_skill: list[DbSkill]) -> None:
        for skill in [skill for skill in available_skill if skill.category == "mining"]:
            if (
                    skill.key in config.MINING_ENERGY_SKILLS
                    and skill.next_level <= config.MAX_MINING_ENERGY_RECOVERY_UPGRADE_LEVEL
                    or (
                    skill.next_level <= config.MAX_MINING_UPGRADE_LEVEL
                    or skill.skill_price <= config.MAX_MINING_UPGRADE_COSTS
            )
            ):
                await self._upgrade_skill(skill)

    def _is_enough_money_for_upgrade(self, skill: DbSkill) -> bool:
        return (self.balance - skill.skill_price) >= config.MONEY_TO_SAVE

    async def _upgrade_hero_skill(self, available_skill: list[DbSkill]) -> None:
        for skill in sorted(
                [skill for skill in available_skill if skill.weight],
                key=lambda x: x.weight,
                reverse=True,
        ):
            if skill.title in config.SKIP_TO_UPGRADE_SKILLS:
                continue
            # if skill.weight >= config.SKILL_WEIGHT or skill.skill_price <= config.MAX_SKILL_UPGRADE_COSTS:
            if skill.weight >= config.SKILL_WEIGHT:
                await self._upgrade_skill(skill)

    async def _upgrade_skill(self, skill: DbSkill) -> None:
        if self._is_enough_money_for_upgrade(skill):
            try:
                await self.skills_improve(json_body={"data": skill.key})
                self.logger.info(
                    f"Skill: <blue>{skill.title}</blue> upgraded to level: <c>{skill.next_level}</c> "
                    f"Profit: <y>{num_prettier(skill.skill_profit)}</y> "
                    f"Costs: <blue>{num_prettier(skill.skill_price)}</blue> "
                    f"Money stay: <y>{num_prettier(self.balance)}</y> "
                    f"Skill weight <magenta>{skill.weight:.5f}</magenta>"
                )
                await self.sleeper()
            except ValueError:
                self.logger.exception(f"Failed to upgrade skill: {skill}")
                raise

    def _get_available_skills(self) -> Generator[DbSkill, None, None]:
        for skill in DbSkills(**self.dbs).dbSkills:
            self._calkulate_skill_requirements(skill)
            if self._is_available_to_upgrade_skills(skill):
                yield skill

    def _calkulate_skill_requirements(self, skill: DbSkill) -> None:
        skill.next_level = (
            self.data_after.skills[skill.key]["level"] + 1 if self.data_after.skills.get(skill.key) else 1
        )
        skill.skill_profit = skill.calculate_profit(skill.next_level)
        skill.skill_price = skill.price_for_level(skill.next_level)
        skill.weight = skill.skill_profit / skill.skill_price
        skill.progress_time = skill.get_skill_time(self.data_after)

    def _is_available_to_upgrade_skills(self, skill: DbSkill) -> bool:
        # check the current skill is still in the process of improvement
        if skill.progress_time and skill.progress_time.timestamp() + 60 > datetime.now(UTC).timestamp():
            return False
        if skill.next_level > skill.maxLevel:
            return False
        skill_requirements = skill.get_level_by_skill_level(skill.next_level)
        if not skill_requirements:
            return True
        return (
                len(self.data_after.friends) >= skill_requirements.requiredFriends
                and self.user_profile.level >= skill_requirements.requiredHeroLevel
                and self._is_can_learn_skill(skill_requirements)
        )

    def _is_can_learn_skill(self, level: SkillLevel) -> bool:
        if not level.requiredSkills:
            return True
        for skill, level in level.requiredSkills.items():
            if skill not in self.data_after.skills:
                return False
            if self.data_after.skills[skill]["level"] >= level:
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
        proxy = proxy or self.additional_data.proxy
        if proxy and "socks" in proxy:
            proxy_conn = SocksProxyConnector.from_url(proxy)
        elif proxy:
            proxy_conn = ProxyConnector.from_url(proxy)
        else:
            proxy_conn = None

        async with aiohttp.ClientSession(
                headers=headers,
                connector=proxy_conn,
                timeout=aiohttp.ClientTimeout(total=60),
        ) as http_client:
            self.http_client = http_client
            if proxy:
                await self.check_proxy(proxy=proxy)

            while True:
                if self.errors >= config.ERRORS_BEFORE_STOP:
                    self.logger.error("Bot stopped (too many errors)")
                    break
                try:
                    if await self.login_to_app(proxy):
                        # if not self.settings_was_set:
                        #     await self.sent_eng_settings()
                        data = await self.get_profile_full()
                        self.dbs = data["dbData"]
                        await self.get_box_rewards()

                        self.user_profile: ProfileData = ProfileData(**data)
                        if self.user_profile.offline_bonus > 0:
                            await self.get_offline_bonus()

                    profile = await self.syn_hero_balance()

                    config.MONEY_TO_SAVE = self.bet_calculator.max_bet()
                    self.logger.info(f"Max bet for funds saved: <y>{num_prettier(config.MONEY_TO_SAVE)}</y>")

                    self.data_after = await self.user_data_after()

                    await self.claim_daily_reward()

                    await self.execute_and_claim_daily_quest()

                    await self.syn_hero_balance()

                    await self.get_friend_reward()

                    if config.TAPS_ENABLED and profile.energy and time.monotonic() > self.temporary_stop_taps_time:
                        await self.perform_taps(profile)

                    await self.set_funds()
                    await self.solve_quiz_and_rebus()

                    await self.claim_all_executed_quest()

                    await self.syn_hero_balance()

                    await self.upgrade_hero()

                    if config.PVP_ENABLED:
                        await self.starting_pvp()
                    await self.syn_hero_balance()
                    sleep_time = random.randint(*config.BOT_SLEEP_TIME)
                    self.logger.info(f"Sleep minutes {sleep_time // 60} minutes")
                    await asyncio.sleep(sleep_time)

                except RuntimeError as error:
                    raise error from error
                except Exception:
                    self.errors += 1
                    self.authorized = False
                    self.logger.exception("Unknown error")
                    await self.sleeper(additional_delay=self.errors * 8)
                else:
                    self.errors = 0
                    self.authorized = False


async def run_bot(tg_client: Client, proxy: str | None, additional_data: dict) -> None:
    try:
        await CryptoBot(tg_client=tg_client, additional_data=additional_data).run(proxy=proxy)
    except RuntimeError:
        log.bind(session_name=tg_client.name).exception("Session error")
