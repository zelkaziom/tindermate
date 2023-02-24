import asyncio
import random
from datetime import datetime
from typing import Coroutine

from rich.markdown import Markdown


def render_link(link: str, label: str) -> str:
    return f"[@click=\"app.open_link('{link}')\"]{label}[/]"


def render_markdown_info_list(info: dict[str, str]) -> Markdown:
    lines = [f"- **{key}**: {val}" for key, val in info.items() if val]
    return Markdown("\n".join(lines))


async def random_delay(coro: Coroutine, interval: tuple[int, int]) -> None:
    """Coroutine that will start another coroutine after a random delay in the specified interval"""
    # suspend for a time limit in seconds
    lb, ub = interval
    seconds = lb + (ub - lb) * random.random()
    await asyncio.sleep(seconds)
    # execute the other coroutine
    await coro


def format_datetime(dt: datetime) -> str:
    return dt.date().isoformat()
