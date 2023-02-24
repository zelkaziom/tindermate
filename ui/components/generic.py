from rich.console import RenderableType
from textual._types import MessageTarget
from textual.containers import Container
from textual.message import Message
from textual.widgets import Static


class Column(Container):
    ...


class Section(Container):
    ...


class SubTitle(Static):
    ...


class Row(Container):
    ...


class AboveFold(Container):
    ...


class Tab(Static):
    class Selected(Message):
        """Color selected message."""

        def __init__(self, sender: MessageTarget, tab_key: str) -> None:
            self.tab_key = tab_key
            super().__init__(sender)

    def __init__(self, label: str, key: str):
        super().__init__(label)
        self.label = label
        self.key = key

    async def on_click(self) -> None:
        # The emit method sends an event to a widget's parent
        await self.emit(self.Selected(self, self.key))


class Notification(Static):
    def __init__(self, renderable: RenderableType, delay: int):
        super().__init__(renderable)
        self.delay = delay

    def on_mount(self) -> None:
        if self.delay != -1:
            self.set_timer(self.delay, self.remove)

    def on_click(self) -> None:
        self.remove()
