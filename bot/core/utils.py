import json
import re
from functools import lru_cache
from pathlib import Path


def try_to_get_code(title: str) -> str | None:
    title = title.lower()
    codes = _load_codes_from_files()
    if video_code_title := re.search(r"эпизод\s*\d+", title):
        return codes.get(video_code_title.group().replace(" ", ""), None)
    if "бутерин" in title:
        return codes.get("бутерин", None)
    return None


@lru_cache
def _load_codes_from_files() -> dict:
    with Path("youtube.json").open("r", encoding="utf-8") as file:
        return json.load(file)
