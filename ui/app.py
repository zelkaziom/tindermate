from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Static

from configuration import Configuration
from conversation.agent import ConversationAgent
from tinder.client import create_tinder_client
from ui import utils
from ui.components.body import Body
from ui.components.generic import AboveFold
from ui.components.sidebar import Sidebar
from ui.context import AppContext
from ui.tokens import InvalidTokenError, Tokens, validate_tokens


class LoadingScreen(Screen):
    def compose(self) -> ComposeResult:
        yield AboveFold(Static("The application is loading..."))


class AuthScreen(Screen):
    def compose(self) -> ComposeResult:
        tokens = Tokens.load()
        yield Container(
            Static("OpenAI token", classes="label"),
            Input(value=tokens.openai_token or "", placeholder="OpenAI token", id="openai-inp"),
            Static("Tinder token", classes="label"),
            Input(value=tokens.tinder_token or "", placeholder="Tinder token", id="tinder-inp"),
            Static(),
            Button("Submit", variant="primary", id="submit"),
            id="auth-form",
        )

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "submit":
            openai_token = self.query_one("#openai-inp", Input).value
            tinder_token = self.query_one("#tinder-inp", Input).value
            tokens = Tokens(openai_token=openai_token, tinder_token=tinder_token)
            try:
                await validate_tokens(tokens)
                tokens.save()
                self.app.push_screen(AppScreen())
            except InvalidTokenError as exc:
                message = Text.assemble(("ERROR: ", "bold red"), exc.args[0])
                utils.show_notification(self.app, message, delay=10)


class AppScreen(Screen):
    def __init__(self):
        super().__init__()
        tokens = Tokens.load()
        self.ctx = AppContext(
            agent=ConversationAgent(api_key=tokens.openai_token or ""),
            tinder=create_tinder_client(auth_token=tokens.tinder_token or ""),
        )

    def compose(self) -> ComposeResult:
        yield Body(self.ctx)


class Tindermate(App):
    BINDINGS = [
        ("ctrl+b", "toggle_sidebar", "Sidebar"),
        ("ctrl+t", "app.toggle_dark", "Toggle Dark mode"),
        # ("f1", "app.toggle_class('TextLog', '-hidden')", "Notes"),
        ("ctrl+c,ctrl+q", "app.quit", "Quit"),
    ]
    SCREENS = {"input": AuthScreen(), "body": AppScreen(), "loading": LoadingScreen()}
    CSS_PATH = Configuration.CSS_PATH

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Container(
            Sidebar(classes="-hidden"),
            Header(),
            Footer(),
        )

    async def on_mount(self) -> None:
        self.push_screen(LoadingScreen())
        try:
            tokens = Tokens.load()
            await validate_tokens(tokens)
            utils.show_notification(self, "The tokens are valid")
            self.push_screen(AppScreen())
        except InvalidTokenError as exc:
            utils.show_notification(self, exc.args[0])
            self.push_screen(AuthScreen())

    # async def on_input_changed(self, message: Input.Changed) -> None:

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark

    def action_toggle_sidebar(self) -> None:
        sidebar = self.query_one(Sidebar)
        self.set_focus(None)
        if sidebar.has_class("-hidden"):
            sidebar.remove_class("-hidden")
        else:
            if sidebar.query("*:focus"):
                self.screen.set_focus(None)
            sidebar.add_class("-hidden")

    def action_open_link(self, link: str) -> None:
        self.app.bell()
        import webbrowser

        webbrowser.open(link)
