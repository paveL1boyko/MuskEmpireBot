import json
from functools import lru_cache
from pathlib import Path


def try_to_get_code(title: str) -> str | None:
    title = title.lower().replace(" ", "")
    codes = _load_codes_from_files()
    ordered_keyes = sorted(
        codes, key=lambda x: int(key) if (key := "".join(x for x in x if x.isdigit())) else 0, reverse=True
    )
    for key in ordered_keyes:
        if key in title:
            return codes.get(key, None)
    return None


@lru_cache
def _load_codes_from_files() -> dict:
    with Path("youtube.json").open("r", encoding="utf-8") as file:
        return json.load(file)
