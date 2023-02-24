from rich.console import RenderableType
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.reactive import watch
from textual.widgets import Static, Checkbox

from configuration import Configuration


# TODO
MESSAGE = """
We hope you enjoy using Textual.

Here are some links. You can click these!

[@click="app.open_link('https://textual.textualize.io')"]Textual Docs[/]

[@click="app.open_link('https://github.com/Textualize/textual')"]Textual GitHub Repository[/]

[@click="app.open_link('https://github.com/Textualize/rich')"]Rich GitHub Repository[/]


Built with ♥ by [@click="app.open_link('https://www.textualize.io')"]Textualize.io[/]

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
        yield Title("Textual Demo")
        yield OptionGroup(Message(MESSAGE), Version())
        yield DarkSwitch()
