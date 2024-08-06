from enum import StrEnum

from pydantic_settings import BaseSettings, SettingsConfigDict

logo = """

███    ███ ██    ██ ███████ ██   ██     ███████ ███    ███ ██████  ██ ██████  ███████
████  ████ ██    ██ ██      ██  ██      ██      ████  ████ ██   ██ ██ ██   ██ ██
██ ████ ██ ██    ██ ███████ █████       █████   ██ ████ ██ ██████  ██ ██████  █████
██  ██  ██ ██    ██      ██ ██  ██      ██      ██  ██  ██ ██      ██ ██   ██ ██
██      ██  ██████  ███████ ██   ██     ███████ ██      ██ ██      ██ ██   ██ ███████

"""


class Strategy(StrEnum):
    flexible = "flexible"
    protective = "protective"
    aggressive = "aggressive"
    random = "random"


class League(StrEnum):
    bronze = "bronze"
    silver = "silver"
    gold = "gold"
    platina = "platina"
    diamond = "diamond"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True, extra="allow")

    API_ID: int
    API_HASH: str

    TAPS_ENABLED: bool = True
    TAPS_PER_SECOND: list[int] = [20, 30]
    PVP_ENABLED: bool = True
    PVP_LEAGUE: League = League.bronze
    PVP_STRATEGY: Strategy = Strategy.random
    PVP_COUNT: int = 10

    SLEEP_BETWEEN_START: list[int] = [20, 360]
    ERRORS_BEFORE_STOP: int = 3
    USE_PROXY_FROM_FILE: bool = False

    RANDOM_SLEEP_TIME: int = 5
    SKILL_WEIGHT: float = 0.00005

    MONEY_TO_SAVE: int = 1_000_000

    BOT_SLEEP_TIME: list[int] = [20, 360]

    base_url: str = "https://game.muskempire.io/"
    bot_name: str = "muskempire_bot"


config = Settings()
