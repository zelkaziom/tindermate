from dataclasses import dataclass

from conversation.agent import ConversationAgent
from tinder.client import TinderClient
from tinder.schemas import CurrentUser


@dataclass
class AppContext:
    tinder: TinderClient
    agent: ConversationAgent
