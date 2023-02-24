import asyncio
import functools
import random
from collections.abc import Coroutine
from datetime import datetime
from typing import Any

from rich.console import RenderableType
from rich.markdown import Markdown
from rich.text import Text
from textual.app import App

from tindermate.type_aliases import AnyDict
from tindermate.ui.components.generic import Notification

# we have to store tasks due to https://twitter.com/willmcgugan/status/1624419352211603461
_TASKS: list[asyncio.Task] = []


def render_link(link: str, label: str) -> str:
    return f"[@click=\"app.open_link('{link}')\"]{label}[/]"


def render_markdown_info_list(info: AnyDict) -> Markdown:
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


def fire_task(
    app: App, coro: Coroutine[None, None, Any], delay_interval: tuple[int, int] | None = None
) -> asyncio.Task:
    if delay_interval is not None:
        coro = random_delay(coro, delay_interval)
    task = asyncio.create_task(coro)
    task.add_done_callback(functools.partial(notify_task_error, app))
    _TASKS.append(task)
    return task


def notify_task_error(app: App, task: asyncio.Task) -> None:
    if task.cancelled():
        print(f"Task {task.get_name()} cancelled")
        return
    try:
        task.result()
    except Exception as exc:
        message = Text.assemble(("ERROR:", "bold red"), f" Error while fetching data: {str(exc)}")
        show_notification(app, message, delay=10)
        raise exc


def show_notification(app: App, text: RenderableType, delay: int = 3) -> None:
    app.query(Notification).remove()
    app.screen.mount(Notification(text, delay))
