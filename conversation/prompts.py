from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from jinja2 import Environment, PackageLoader, select_autoescape

from configuration import Configuration
from tinder.schemas import CurrentUser, Message, UserDetail
from tinder.utils import calculate_age


@dataclass
class Grammar:
    noun: str  # guy
    # subject pronoun
    psubj: str  # he
    # object pronoun
    pobj: str  # him
    # possessive adjective
    apos: str  # his

    @classmethod
    def for_gender(cls, gender: int) -> "Grammar":
        if gender == 0:
            return Grammar(noun="guy", psubj="he", pobj="him", apos="his")
        else:
            return Grammar(noun="girl", psubj="she", pobj="her", apos="her")

    @property
    def message_mark(self) -> str:
        return f"{self.pobj.upper()}: "


class Prompt(ABC):
    def __init__(self, template: str):
        self._template = template
        self._template_env = Environment(
            loader=PackageLoader("conversation", "templates"),
            autoescape=select_autoescape(),
        )

    @abstractmethod
    def get_template_vars(self) -> dict[str, Any]:
        ...

    @abstractmethod
    def stop_words(self) -> list[str]:
        ...

    def render(self) -> str:
        """Interpolates the variables into the prompt template and renders it into a string"""
        template = self._template_env.get_template(self._template)
        return template.render(self.get_template_vars()).replace("\n\n", "\n")


class MessageReplyPrompt(Prompt):
    def __init__(
        self,
        current_user: CurrentUser,
        matched_user: UserDetail,
        message_history: list[Message],
        history_limit: int = 10,
    ):
        super().__init__(Configuration.MESSAGE_REPLY_PROMPT_TEMPLATE)
        self._current_user = current_user
        self._matched_user = matched_user
        self._message_history = message_history
        self._history_limit = history_limit

        self._grammar_1 = Grammar.for_gender(self._current_user.gender)
        other_gender = (
            self._matched_user.gender if self._matched_user.gender is not None else self._current_user.gender_filter
        )
        self._grammar_2 = Grammar.for_gender(other_gender)

    def get_template_vars(self) -> dict[str, Any]:
        message_history = self._message_history[-self._history_limit :]
        num_hidden_messages = max(0, len(self._message_history) - self._history_limit)

        message_history = [(message.from_ == self._current_user.id, message.message) for message in message_history]

        return {
            "message_history": message_history,
            "num_hidden_messages": num_hidden_messages,
            "_1": self._grammar_1,
            "_2": self._grammar_2,
        }

    def stop_words(self) -> list[str]:
        """Stop if generation reaches the message mark of the other user"""
        return [self._grammar_2.message_mark]


class FirstMessagePrompt(Prompt):
    def __init__(self, current_user: CurrentUser, matched_user: UserDetail):
        super().__init__(Configuration.FIRST_MESSAGE_PROMPT_TEMPLATE)
        self._current_user = current_user
        self._matched_user = matched_user
        self._grammar_1 = Grammar.for_gender(self._current_user.gender)
        other_gender = (
            self._matched_user.gender if self._matched_user.gender is not None else self._current_user.gender_filter
        )
        self._grammar_2 = Grammar.for_gender(other_gender)

    def get_template_vars(self) -> dict[str, Any]:
        return {
            "name": self._matched_user.name,
            "bio": None if not (bio := self._matched_user.bio) else bio.replace("\n", " "),
            "city": None if (city := self._matched_user.city) is None else city.name,
            "age": calculate_age(self._matched_user.birth_date),
            "school": self._matched_user.school,
            "job": self._matched_user.job,
            "interests": [
                (interest, interest in self._current_user.interests) for interest in self._matched_user.interests
            ],
            "_1": self._grammar_1,
            "_2": self._grammar_2,
        }

    def stop_words(self) -> list[str]:
        """Stop if generation reaches the message mark of the other user"""
        return [self._grammar_2.message_mark]
