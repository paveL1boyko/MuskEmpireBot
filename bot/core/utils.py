import json
from functools import lru_cache
from pathlib import Path


@lru_cache
def load_codes_from_files() -> dict:
    with Path("youtube.json").open("r", encoding="utf-8") as file:
        return json.load(file)


def num_prettier(num: int) -> str:
    number = abs(num)
    if number >= (comparer := 1e12):
        prettier_num = f"{number / comparer:.1f}T"
    elif number >= (comparer := 1e9):
        prettier_num = f"{number / comparer:.1f}B"
    elif number >= (comparer := 1e6):
        prettier_num = f"{number / comparer:.1f}M"
    elif number >= (comparer := 1e3):
        prettier_num = f"{number / comparer:.1f}k"
    else:
        prettier_num = str(number)
    return f"-{prettier_num}" if num < 0 else prettier_num
