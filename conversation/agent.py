from configuration import Configuration
from conversation.gpt import GPTClient, create_gpt_client
from conversation.prompts import Prompt


class ConversationAgent:
    def __init__(self, api_key: str, ai_client: GPTClient | None = None):
        self._config = Configuration.OPENAI_CONFIG
        self._ai_client = ai_client or create_gpt_client(api_key, self._config.MODEL)

    async def complete_text(self, prompt: Prompt) -> list[str]:
        """Return a list of generated completions for the given prompt"""
        print("Calling GPT")
        return await self._ai_client.complete_text(
            prompt=prompt.render(),
            num_choices=self._config.NUM_CHOICES,
            max_tokens=self._config.MAX_TOKENS,
            temperature=self._config.TEMPERATURE,
            stop_words=prompt.stop_words(),
        )

    async def test_connection(self) -> None:
        """Raise an exception if the api key is not valid"""
        print("Testing OpenAI connection")
        await self._ai_client.complete_text(
            prompt="This is a connection test",
            num_choices=1,
            max_tokens=10,
            temperature=0.1,
        )
