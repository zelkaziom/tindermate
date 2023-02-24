import asyncio
from contextlib import contextmanager
from enum import Enum

from rich.console import RenderableType
from rich.markdown import Markdown
from rich.text import Text
from textual.app import ComposeResult
from textual.css.query import NoMatches
from textual.reactive import reactive
from textual.widgets import Static, Button

from conversation.prompts import FirstMessagePrompt, MessageReplyPrompt, Prompt
from tinder.schemas import MatchDetail, CurrentUser, Match
from ui import utils
from ui.components.generic import Section, Row, SubTitle
from ui.context import AppContext
from ui.utils import render_link, render_markdown_info_list, random_delay


class MatchInfo(Static):

    def on_match_info_loaded(self, match: MatchDetail) -> None:
        match_info = {
            "Age": match.person.age,
            "Interests": ', '.join(match.person.interests),
            "City": city.name if (city := match.person.city) else None,
            "School": match.person.school,
            "Job": match.person.job,
            "Bio": match.person.bio_oneline,
        }
        if len(match.messages) > 0:
            last_message = match.messages[-1]
            match_info["Last message"] = f"{utils.format_datetime(last_message.sent_date)} " \
                                         f"({'them' if last_message.from_ == match.person.id else 'you'})"
        self.update(render_markdown_info_list(match_info))


class MatchView(Enum):
    DEFAULT = "DEFAULT"
    PROMPT = "PROMPT"
    RESULT = "RESULT"


class TinderMatch(Static):

    result: RenderableType | None = reactive(None)
    current_view: MatchView = reactive(MatchView.DEFAULT, init=False)

    def __init__(self, context: AppContext, match: Match, current_user: CurrentUser, batch: int):
        super().__init__()
        self.ctx = context
        self.match = match
        self.current_user = current_user
        self.match_detail: MatchDetail | None = None
        self.batch = batch

    def compose(self) -> ComposeResult:
        """Create child widgets of a match"""

        yield Section(
            Row(
                SubTitle(
                    render_link(link=self.match.open_messages_link, label=self.match.person.name.upper())
                ),
                Static(f"Matched {utils.format_datetime(self.match.created_date)}", classes="right")
            ),
            MatchInfo(classes="pad"),
            Row(
                Button("Generate", id="generate", variant="success"),
                Button("Show prompt", id="show-prompt", variant="primary"),
                id=MatchView.DEFAULT.value,
            ),
            Row(
                Button("Generate", id="generate", variant="success"),
                Button("Discard", id="discard", variant="error"),
                id=MatchView.PROMPT.value,
                classes="hidden",
            ),
            Row(
                Button("Regenerate", id="regenerate", variant="primary"),
                Button("Discard", id="discard", variant="error"),
                id=MatchView.RESULT.value,
                classes="hidden",
            ),
        )
        yield Static("Loading data...", id="loading-data", classes="hidden text-row")
        yield Section(
            Static(id="results"), id="results-container"
        )

    async def on_mount(self) -> None:
        # offset the request, so we don't fire all requests at once
        task = asyncio.create_task(random_delay(self.get_match_detail(), (self.batch, self.batch + 1)))
        task.add_done_callback(self.app.notify_task_error)

    async def get_match_detail(self) -> MatchDetail:
        if self.match_detail is None:
            self.match_detail = await self.ctx.tinder.fetch_detail_for(self.match)
            # populate the match info on the first load
            try:
                self.query_one(MatchInfo).on_match_info_loaded(self.match_detail)
            except NoMatches:
                pass

        return self.match_detail

    @contextmanager
    def loading_data(self):
        loading = self.query_one("#loading-data")
        loading.remove_class("hidden")
        yield
        loading.add_class("hidden")
        loading.refresh()

    async def handle_generation(self) -> None:
        with self.loading_data():
            result = await self.ctx.agent.complete_text(await self.get_prompt())
            self.result = self.render_result(result)
        self.app.show_notification(
            Text.assemble(
                "Messages for ",
                (f"'{self.match.person.name}'", "bold green"),
                " successfully generated"
            )
        )

    async def handle_show_prompt(self) -> None:
        with self.loading_data():
            prompt = await self.get_prompt()
            lines = ["**Prompt**".upper(), "", prompt.render().replace("\n", "\n\n")]
            self.result = Markdown("\n".join(lines))
        self.app.show_notification(
            Text.assemble(
                "Prompt for ",
                (f"'{self.match.person.name}'", "bold green"),
                " successfully generated"
            )
        )

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id in ["generate", "regenerate"]:
            self.app.fire_task(self.handle_generation())
            self.current_view = MatchView.RESULT

        elif event.button.id == "show-prompt":
            self.app.fire_task(self.handle_show_prompt())
            self.current_view = MatchView.PROMPT

        elif event.button.id == "discard":
            self.result = None
            self.current_view = MatchView.DEFAULT

    def watch_current_view(self, current_view: MatchView):
        """Replace the rendered buttons with a new set"""
        other_views = [f"#{view.value}" for view in list(MatchView) if view != current_view]
        self.query(", ".join(other_views)).add_class("hidden")
        print(f"Remounting buttons to {current_view}")
        self.query(f"#{current_view.value}").remove_class("hidden")

    def watch_result(self, result: RenderableType | None) -> None:
        if result is None:
            self.remove_class("expanded")
            try:
                self.query_one("#results").update("")
            except NoMatches:
                pass
        else:
            self.add_class("expanded")
            self.query_one("#results").update(result)

    async def get_prompt(self) -> Prompt:
        raise NotImplementedError()

    def render_result(self, result: list[str]) -> RenderableType:
        raise NotImplementedError()


class NewTinderMatch(TinderMatch):

    async def get_prompt(self) -> FirstMessagePrompt:
        return FirstMessagePrompt(
            current_user=self.current_user,
            matched_user=(await self.get_match_detail()).person
        )

    def render_result(self, result: list[str]) -> RenderableType:
        lines = ["**Message suggestions**".upper()]
        for idx, text in enumerate(result):
            lines.append("")
            lines.append(f"{idx + 1}. {text}")
        return Markdown("\n".join(lines))


class MessagedTinderMatch(TinderMatch):

    async def get_prompt(self) -> MessageReplyPrompt:
        await self.ctx.tinder.fetch_messages_for(self.match)
        return MessageReplyPrompt(
            current_user=self.current_user,
            matched_user=(await self.get_match_detail()).person,
            message_history=self.match.messages
        )

    def render_result(self, result: list[str]) -> RenderableType:
        lines = ["**Message suggestions**".upper()]
        for idx, text in enumerate(result):
            lines.append("")
            lines.append(f"{idx + 1}. {text}")
        return Markdown("\n".join(lines))
