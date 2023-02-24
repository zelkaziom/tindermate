from dataclasses import dataclass

from conversation.agent import ConversationAgent
from tinder.client import TinderClient


@dataclass
class AppContext:
    tinder: TinderClient
    agent: ConversationAgent
