import json
from pathlib import Path

from fake_useragent import UserAgent


def read_session_profiles(sessions: list[str]) -> dict | None:
    file_path = Path("session_profile.json")
    if not file_path.exists():
        return None

    try:
        with file_path.open(encoding="utf-8") as file:
            data = json.load(file)
            return data if all(session in data and len(data[session]) >= 2 for session in sessions) else None
    except (OSError, json.JSONDecodeError):
        return None


def get_session_profiles(sessions: list[str]) -> dict:
    session_profiles = read_session_profiles(sessions)
    if session_profiles is None:
        session_profiles = {}
        ua_generator = UserAgent(browsers=["safari"], os=["ios"], platforms=["mobile", "tablet"])

        for session in sessions:
            inner = session_profiles.setdefault(session, [])
            inner.append({"User-Agent": ua_generator.random})
            inner.append({"proxy": None})

        with Path("session_profile.json").open("w", encoding="utf-8") as file:
            json.dump(session_profiles, file, ensure_ascii=False, indent=4)

    return session_profiles
