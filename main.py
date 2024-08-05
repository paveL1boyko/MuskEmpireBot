import asyncio

from bot.config.logger import log
from bot.core import launcher


async def main() -> None:
    await launcher.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Bot stopped by user")
