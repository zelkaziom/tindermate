import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(os.path.abspath(__file__)).parent

load_dotenv(BASE_DIR / ".env")


def path_to(*parts: str) -> Path:
    path = Path(BASE_DIR).joinpath(*parts)
    path.mkdir(parents=True, exist_ok=True)
    return path


def env2bool(value: str, default: bool | None = None) -> bool:
    if not value and default is not None:
        return default

    if value in {"off", "False", "false", "0", "-", "n/a", "N/A"}:
        return False

    return bool(value)


class OpenAIConfiguration:
    MODEL = os.getenv("OPENAI_MODEL", "text-davinci-003")
    MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", 100))
    TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", 0.8))
    NUM_CHOICES = int(os.getenv("OPENAI_NUM_CHOICES", 3))
    PRESENCE_PENALTY = float(os.getenv("OPENAI_PRESENCE_PENALTY", 0.6))
    FREQUENCY_PENALTY = float(os.getenv("OPENAI_FREQUENCY_PENALTY", 0.1))


class Configuration:
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    TINDER_AUTH_TOKEN = os.getenv("TINDER_AUTH_TOKEN")
    DEBUG: bool = env2bool(os.getenv("DEBUG"), default=False)

    CACHE_DIR = path_to("data", "cache")
    LOG_DIR = path_to("data", "cache")
    APP_VERSION = "0.0.1"
    CSS_PATH = path_to("ui/static/") / "styles.css"

    TOKEN_FILE = BASE_DIR / ".tokens"

    OPENAI_CONFIG = OpenAIConfiguration()

    # PROMPTS
    MESSAGE_REPLY_PROMPT_TEMPLATE = os.getenv("MESSAGE_REPLY_PROMPT_TEMPLATE", "message_reply.txt")
    FIRST_MESSAGE_PROMPT_TEMPLATE = os.getenv("FIRST_MESSAGE_PROMPT_TEMPLATE", "first_message.txt")


Configuration.TOKEN_FILE.touch()
