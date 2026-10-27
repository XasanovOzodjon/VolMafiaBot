from pathlib import Path

from environs import Env

env = Env()
env.read_env()

BOT_TOKEN = env.str("BOT_TOKEN")
ADMINS = env.list("ADMINS", default=[])
REDIS_URL = env.str("REDIS_URL", "redis://localhost:6379/0")
DATABASE_URL = env.str(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/volmafia",
)
PLAY_GROUP_URL = env.str("PLAY_GROUP_URL", "")

MIN_PLAYERS = env.int("MIN_PLAYERS", 5)
MAX_PLAYERS = env.int("MAX_PLAYERS", 21)
TEST_MIN_PLAYERS = 4
TEST_MAX_PLAYERS = 21

REGISTRATION_SECONDS = env.int("REGISTRATION_SECONDS", 90)
NIGHT_SECONDS = env.int("NIGHT_SECONDS", 45)
DAY_SECONDS = env.int("DAY_SECONDS", 30)
VOTE_SECONDS = env.int("VOTE_SECONDS", 45)

MEDIA_DIR = Path(__file__).resolve().parent / "media"
NIGHT_GIF = env.str("NIGHT_GIF", str(MEDIA_DIR / "night.gif"))
DAY_GIF = env.str("DAY_GIF", str(MEDIA_DIR / "day.gif"))
CONFIRM_SECONDS = env.int("CONFIRM_SECONDS", 25)
LYNCH_REVEAL_SECONDS = env.int("LYNCH_REVEAL_SECONDS", 5)
YAKUDZA_SECONDS = env.int("YAKUDZA_SECONDS", 20)
EXTEND_SECONDS = env.int("EXTEND_SECONDS", 30)

PANEL_HOST = env.str("PANEL_HOST", "127.0.0.1")
PANEL_PORT = env.int("PANEL_PORT", 8080)
PANEL_LOGIN = env.str("PANEL_LOGIN", "admin")
PANEL_PASSWORD = env.str("PANEL_PASSWORD", "mafia")
PANEL_PUBLIC_URL = env.str("PANEL_PUBLIC_URL", "")
DEBUG = env.bool("DEBUG", False)


def set_public_url(url: str) -> None:
    global PANEL_PUBLIC_URL
    PANEL_PUBLIC_URL = (url or "").rstrip("/")


def public_https_base() -> str:
    url = (PANEL_PUBLIC_URL or "").rstrip("/")
    return url if url.startswith("https://") else ""


def market_webapp_url(page: str = "") -> str:
    base = public_https_base()
    if not base:
        return ""
    page = (page or "").strip()
    if page in ("profile", "topup", "market"):
        return f"{base}/market?page={page}"
    return f"{base}/market"
