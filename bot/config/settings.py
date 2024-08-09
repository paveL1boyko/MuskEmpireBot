from enum import Enum

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
    PVP_COUNT: int = 10

    SLEEP_BETWEEN_START: list[int] = [4, 20]
    ERRORS_BEFORE_STOP: int = 3
    USE_PROXY_FROM_FILE: bool = False

    RANDOM_SLEEP_TIME: int = 5
    SKILL_WEIGHT: float = 0

    MONEY_TO_SAVE: int = 1_000_000

    AUTO_UPGRADE_MINING: bool = True
    MAX_MINING_UPGRADE_LEVEL: int = 30
    MAX_MINING_ENERGY_RECOVERY_UPGRADE_LEVEL: int = 50
    MAX_MINING_UPGRADE_COSTS: int = 5_000_000

    BOT_SLEEP_TIME: list[int] = [2000, 3500]
    REF_ID: str = "hero7092030432"
    base_url: str = "https://game.muskempire.io/"
    bot_name: str = "muskempire_bot"


config = Settings()
