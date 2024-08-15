import asyncio

from bot import launcher
from bot.config.logger import log


async def main() -> None:
    await launcher.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Bot stopped by user")
