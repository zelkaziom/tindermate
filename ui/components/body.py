from collections.abc import Callable, Coroutine
from contextlib import contextmanager
from operator import attrgetter

from textual.app import ComposeResult
from textual.containers import Container
from textual.reactive import Reactive, reactive
from textual.widgets import Static

from tinder.schemas import CurrentUser
from ui.components.generic import Column, Row, SubTitle, Tab
from ui.components.sidebar import Title
from ui.components.tinder_match import MessagedTinderMatch, NewTinderMatch, TinderMatch
from ui.context import AppContext
from ui.utils import render_link, render_markdown_info_list


class UserProfile(Container):

    def on_user_loaded(self, user: CurrentUser) -> None:
        user_info = {
            "Gender": user.gender_str,
            "Age": user.age,
            "Interests": ', '.join(user.interests),
            "School": user.school,
            "Job": user.job,
            "Age filter": f"{user.age_filter_min}-{user.age_filter_max}",
            "Distance filter": user.distance_filter,
            "Gender filter": user.gender_filter_str,
            "Location": f"{user.pos_info.country.name} ({user.pos_info.timezone})",
            "Discoverable": user.discoverable
        }
        self.mount(
            SubTitle(render_link(link=user.profile_link, label=user.name.upper())),
            Static(render_markdown_info_list(user_info), classes="pad"),
        )


class ErrorMessage(Static):
    ...


class Body(Static):
    _TAB_CONTENT_MAX_ITEMS = 10
    """How many past matches to display at most"""

    active_tab: Reactive[str | None] = reactive("new")

    def __init__(self, context: AppContext):
        super().__init__()
        self.ctx = context
        self._current_user: CurrentUser | None = None

    def compose(self) -> ComposeResult:
        yield UserProfile(Title("Your profile"))
        yield Row(Tab("New matches", "new"), Tab("Messaged matches", "messaged"))
        yield Static("Your matches are loading...", id="loading-matches", classes="hidden text-row")
        yield Column(id="content")

    async def get_current_user(self) -> CurrentUser:
        if self._current_user is None:
            self._current_user = await self.ctx.tinder.current_user_info()

        return self._current_user

    async def on_mount(self) -> None:
        current_user = await self.get_current_user()
        self.query_one(UserProfile).on_user_loaded(current_user)

    def on_tab_selected(self, message: Tab.Selected) -> None:
        self.active_tab = message.tab_key

    def watch_active_tab(self, active_tab: str) -> None:
        print(f"handling it {active_tab}")
        tabs = self.query(Tab)
        tabs.remove_class("active")
        next(tab for tab in tabs if tab.key == active_tab).add_class("active")

        # unmount current content
        self.query("#content *").remove()

        # fetch new content
        if active_tab == "new":
            task = self.fetch_new_matches()
        elif active_tab == "messaged":
            task = self.fetch_messaged_matches()
        else:
            raise ValueError(f"Unknown tab {active_tab}")
        self.app.fire_task(task)

    @contextmanager
    def loading_data(self):
        loading = self.query_one("#loading-matches")
        loading.remove_class("hidden")
        yield
        loading.add_class("hidden")
        loading.refresh()

    async def fetch_new_matches(self) -> None:
        await self.fetch_tab_content(
            self.ctx.tinder.matches(messaged=False),
            NewTinderMatch,
            sort_key=attrgetter("created_date")
        )

    async def fetch_messaged_matches(self) -> None:
        await self.fetch_tab_content(
            self.ctx.tinder.matches(messaged=True),
            MessagedTinderMatch,
            sort_key=lambda m: m.messages[-1].sent_date
        )

    async def fetch_tab_content(self, fetch_coro: Coroutine, widget_cls: type[TinderMatch], sort_key: Callable) -> None:
        with self.loading_data():
            matches = list(await fetch_coro)
            current_user = await self.get_current_user()
            sorted_matches = sorted(matches, key=sort_key, reverse=True)
            sliced_matches = sorted_matches[:self._TAB_CONTENT_MAX_ITEMS]
            widgets = []
            for idx, match in enumerate(sliced_matches):
                widgets.append(widget_cls(self.ctx, match, current_user, batch=idx))

            if (num_hidden := len(matches) - len(sliced_matches)) > 0:
                widgets.append(Static(f"... ({num_hidden} more hidden)", classes="text-row"))

            await self.query_one("#content").mount(*widgets)

        # display the number of list items in the tab name
        active_tab = next(tab for tab in self.query(Tab) if tab.key == self.active_tab)
        active_tab.update(active_tab.label + f" ({len(matches)})")
