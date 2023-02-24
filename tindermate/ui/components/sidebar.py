from rich.console import RenderableType
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.reactive import watch
from textual.widgets import Checkbox, Static

from tindermate.configuration import Configuration

MESSAGE = """
I hope you enjoy using TinderMate.

[@click="app.open_link('https://github.com/borisrakovan/tindermate')"]TinderMate GitHub Repository[/]

Shout out to the awesome [@click="app.open_link('https://github.com/Textualize/textual')"]Textual TUI framework[/]
for making this UI possible.

Built with ♥ by [@click="app.open_link('https://github.com/borisrakovan')"]Boris Rakovan[/]

"""


class DarkSwitch(Horizontal):
    def compose(self) -> ComposeResult:
        yield Checkbox(value=self.app.dark)
        yield Static("Dark mode toggle", classes="label")

    def on_mount(self) -> None:
        watch(self.app, "dark", self.on_dark_change, init=False)

    def on_dark_change(self, dark: bool) -> None:
        self.query_one(Checkbox).value = self.app.dark

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        self.app.dark = event.value


class Title(Static):
    pass


class OptionGroup(Container):
    pass


class Message(Static):
    pass


class Version(Static):
    def render(self) -> RenderableType:
        return f"[b]v{Configuration.APP_VERSION}"


class Sidebar(Container):
    def compose(self) -> ComposeResult:
        yield Title("TinderMate")
        yield OptionGroup(Message(MESSAGE), Version())
        yield DarkSwitch()
