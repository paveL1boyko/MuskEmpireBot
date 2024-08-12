import sys

from loguru import logger

logger.remove()

logger.level("DEBUG", color="<blue>")
logger.level("INFO", color="<green>")
logger.level("WARNING", color="<yellow>")
logger.level("ERROR", color="<red>")
logger.level("CRITICAL", color="<bg #FF0000><white>")

logger_str_format = (
    "<white>{time:YYYY-MM-DD HH:mm:ss}</white> | "
    "<level>{level: <8}</level> | "
    "<cyan><b>{line: <5}</b></cyan>| "
    "<cyan><b>{extra[session_name]: <7}</b></cyan> | "
    "<white><b>{message}</b></white>"
)
logger.add(sink=sys.stdout, format=logger_str_format, colorize=True)
log = logger.bind(session_name="GLOBAL").opt(colors=True)
