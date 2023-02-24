from dataclasses import dataclass

from tindermate.conversation.agent import ConversationAgent
from tindermate.tinder.client import TinderClient


@dataclass
class AppContext:
    tinder: TinderClient
    agent: ConversationAgent
