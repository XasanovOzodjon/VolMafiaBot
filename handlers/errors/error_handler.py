import logging

from telegram import Update
from telegram.error import BadRequest, Forbidden, RetryAfter, TelegramError
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    err = context.error
    if err is None:
        return
    try:
        raise err
    except Forbidden:
        logger.warning("Forbidden: %s", err)
    except BadRequest:
        logger.warning("BadRequest: %s", err)
    except RetryAfter:
        logger.warning("RetryAfter: %s", err)
    except TelegramError:
        logger.exception("TelegramError: %s | update=%s", err, update)
    except Exception:
        logger.exception("Update: %s", update)
