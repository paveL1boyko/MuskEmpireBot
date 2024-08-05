from typing import Any

from pydantic import AliasPath, BaseModel, Field, field_validator

from bot.core.upgrader import Calculator


class SkillLevel(BaseModel):
    level: int
    title: str
    requiredSkills: dict | list
    requiredHeroLevel: int
    requiredFriends: int
    desc: str


class DbSkill(BaseModel):
    key: str
    title: str
    category: str
    subCategory: str
    priceBasic: int
    priceFormula: str
    priceFormulaK: int
    profitBasic: int
    profitFormula: str
    profitFormulaK: int
    maxLevel: int
    timeBasic: str
    timeFormula: str
    timeFormulaK: str
    desc: str
    special: str
    levels: list[SkillLevel]
    next_level: int = 1
    skill_profit: int = 0
    skill_price: int = 0
    weight: int = 0

    def __init__(self, /, **data: Any) -> None:
        super().__init__(**data)
        self._calculator = Calculator()

    def get_level_by_skill_level(self, level: int) -> SkillLevel | None:
        if not self.levels or self.levels[0].level > level:
            return None

        for index, skill_level in enumerate(self.levels):
            if skill_level.level <= level:
                if index + 1 == len(self.levels):
                    return skill_level
                if self.levels[index + 1].level > level:
                    return skill_level

        return None

    def calculate_profit(self, level: int) -> int:
        return self._calculator.get_profit(self, level)

    def price_for_level(self, level: int) -> int:
        return self._calculator.get_price(self, level)


class DbSkills(BaseModel):
    dbSkills: list[DbSkill]


class ProfileData(BaseModel):
    user_id: int = Field(validation_alias=AliasPath("profile", "id"))
    money: int = Field(validation_alias=AliasPath("hero", "money"))
    level: int = Field(validation_alias=AliasPath("hero", "level"))
    money_per_hour: int = Field(validation_alias=AliasPath("hero", "moneyPerHour"))
    offline_bonus: int = Field(validation_alias=AliasPath("hero", "offlineBonus"))
    daily_rewards: dict = Field(validation_alias=AliasPath("dailyRewards"))
    quests: list = Field(validation_alias=AliasPath("quests"))
    friends: list = Field(validation_alias=AliasPath("friends"))
    skills: dict | list = Field(
        description="all user learned skills",
        examples=[
            {"desks": {"level": 6, "lastUpgradeDate": "2024-07-30 19:20:32", "finishUpgradeDate": None}},
            {
                "empathy": {
                    "level": 6,
                    "lastUpgradeDate": "2024-07-30 19:21:36",
                    "finishUpgradeDate": "2024-07-30 19:22:13",
                }
            },
        ],
    )

    @field_validator("skills")
    @classmethod
    def check_skills(cls, v: Any) -> dict:
        return v or {}


class Profile(BaseModel):
    money_per_tap: int = Field(validation_alias=AliasPath("hero", "earns", "task", "moneyPerTap"))
    limit: int = Field(validation_alias=AliasPath("hero", "earns", "task", "limit"))
    energy: int = Field(validation_alias=AliasPath("hero", "earns", "task", "energy"))
    energy_recovery: int = Field(validation_alias=AliasPath("hero", "earns", "task", "recoveryPerSecond"))

    money: int = Field(validation_alias=AliasPath("hero", "money"))
    level: int = Field(validation_alias=AliasPath("hero", "level"))
    money_per_hour: int = Field(validation_alias=AliasPath("hero", "moneyPerHour"))


class Fight(BaseModel):
    league: str
    moneyProfit: int
    player1: int
    moneyContract: int
    player1Strategy: str
    player1Level: int
    player1Rewarded: bool
    player2: int
    player2Strategy: str
    player2Rewarded: bool
    winner: int


class PvpData(BaseModel):
    opponent: dict | None
    fight: Fight | None


class QuizHelper(BaseModel):
    quiz: str = ""
    funds: list = Field(default_factory=list)
    rebus: str = ""


class Skills(BaseModel):
    skills: dict


if __name__ == "__main__":
    data = {
        "hero": {
            "id": 1092379081,
            "level": 12,
            "exp": 207156950,
            "money": 8154952,
            "moneyUpdateDate": "2024-08-05 07:02:28",
            "lastOfflineBonusDate": "2024-08-05 07:02:28",
            "moneyPerHour": 7943050,
            "energyUpdateDate": "2024-08-05 07:02:28",
            "tax": 20,
            "pvpMatch": 1143,
            "pvpWin": 646,
            "pvpLose": 497,
            "pvpMatchesDaily": 123,
            "pvpMatchesDailyDay": "2024-08-04",
            "earns": {
                "task": {"moneyPerTap": 21, "limit": 9500, "energy": 9500, "recoveryPerSecond": 14},
                "sell": {"moneyPerTap": 20, "limit": 6600, "energy": 6600, "recoveryPerSecond": 14},
            },
            "dailyRewardLastDate": "2024-08-04 11:15:56",
            "dailyRewardLastIndex": 7,
            "onboarding": [
                "9040",
                "41",
                "30",
                "40",
                "9000",
                "90",
                "70",
                "10720",
                "9020",
                "10015",
                "9010",
                "80",
                "50",
                "10700",
                "60",
                "9030",
                "20",
                "51",
                "1",
            ],
            "updateDate": "2024-07-19 16:39:56.91573",
            "userId": 1092379081,
        },
        "fight": {
            "id": "08999015-6835-44ed-b00e-3ac529b62285",
            "league": "bronze",
            "moneyContract": 6600,
            "moneyProfit": None,
            "searchTime": None,
            "player1": 1092379081,
            "player1Strategy": "aggressive",
            "player1Level": 12,
            "player1Rewarded": False,
            "player2": None,
            "player2Strategy": None,
            "player2Rewarded": False,
            "winner": None,
            "draw": [],
            "updateDate": None,
            "creationDate": "2024-08-05 07:02:35",
        },
        "opponent": None,
    }
    PvpData(**data)
