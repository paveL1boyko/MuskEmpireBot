from enum import Enum

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

logo = """

███    ███ ██    ██ ███████ ██   ██     ███████ ███    ███ ██████  ██ ██████  ███████
████  ████ ██    ██ ██      ██  ██      ██      ████  ████ ██   ██ ██ ██   ██ ██
██ ████ ██ ██    ██ ███████ █████       █████   ██ ████ ██ ██████  ██ ██████  █████
██  ██  ██ ██    ██      ██ ██  ██      ██      ██  ██  ██ ██      ██ ██   ██ ██
██      ██  ██████  ███████ ██   ██     ███████ ██      ██ ██      ██ ██   ██ ███████

"""


class Strategy(str, Enum):
    flexible = "flexible"
    protective = "protective"
    aggressive = "aggressive"
    random = "random"


class League(str, Enum):
    bronze = "bronze"
    silver = "silver"
    gold = "gold"
    platina = "platina"
    diamond = "diamond"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True, extra="allow")

    API_ID: int
    API_HASH: str

    LOGIN_TIMEOUT: int = 3600

    TAPS_ENABLED: bool = True
    TAPS_PER_SECOND: list[int] = [20, 30]
    AUTO_UPGRADE_HERO: bool = True
    PVP_ENABLED: bool = True
    PVP_LEAGUE: League = League.bronze
    PVP_STRATEGY: Strategy = Strategy.random
    PVP_COUNT: int = 5

    SLEEP_BETWEEN_START: list[int] = [10, 20]
    SESSION_AC_DELAY: int = 10
    ERRORS_BEFORE_STOP: int = 5
    USE_PROXY_FROM_FILE: bool = False
    ADD_LOCAL_MACHINE_AS_IP: bool = False

    RANDOM_SLEEP_TIME: int = 8
    SKILL_WEIGHT: float = 0

    MONEY_TO_SAVE: int = 1_000_000

    AUTO_UPGRADE_MINING: bool = True
    MAX_MINING_UPGRADE_LEVEL: int = 30
    MAX_MINING_ENERGY_RECOVERY_UPGRADE_LEVEL: int = 60
    MINING_ENERGY_SKILLS: list[str] = ["energy_capacity", "energy_recovery", "profit_per_tap_power"]
    MAX_MINING_UPGRADE_COSTS: int = 5_000_000

    SKIP_IMPROVE_DISCIPLINE_BUG: bool = Field(
        default=False,
        description="Skip improve discipline bug for eror "
        "{'success': False, 'error': 'invalid key improve_discipline'}",
    )
    SKIP_TO_UPGRADE_SKILLS: list = Field([], description='Skip upgrade skills. For example: ["Уборщик", "Рекрутер,HR"]')

    BOT_SLEEP_TIME: list[int] = [3000, 3500]
    REF_ID: str = "hero1092379081"
    base_url: str = "https://game.muskempire.io/"
    bot_name: str = "empirebot"


config = Settings()
