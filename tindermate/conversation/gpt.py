import openai
from openai.error import AuthenticationError

from tindermate.configuration import Configuration
from tindermate.type_aliases import AnyDict
from tindermate.filecache import file_cache


class OpenAIAuthError(Exception):
    pass


class GPTClient:
    def __init__(self, model: str):
        self.model = model

    async def complete_text(
        self,
        prompt: str,
        num_choices: int,
        max_tokens: int,
        temperature: float,
        stop_words: list[str] | None = None,
    ) -> list[str]:
        if len(stop_words or []) > 4:
            raise ValueError("Provide maximum of 4 stopwords")

        try:
            resp = await openai.Completion.acreate(
                model=self.model,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=1,
                # how much to penalize the new tokens based on their existing appearance in the text so far
                frequency_penalty=0.1,
                # higher values increase the model tendency to talk about new topics
                presence_penalty=0.6,
                # up to 4 sequences where the API will stop generating further tokens
                stop=stop_words,
                prompt=prompt,
                n=num_choices,
            )
        except AuthenticationError as exc:
            raise OpenAIAuthError() from exc

        return self.parse_response(resp)

    def parse_response(self, response: AnyDict) -> list[str]:
        for choice in response["choices"]:
            if (reason := choice["finish_reason"]) != "stop":
                print(f"Generation {choice['index']} finished before the end token was reached, {reason=}")

        return [choice["text"].strip() for choice in response["choices"]]


class ChatGPTClient(GPTClient):
    def __init__(self):
        super().__init__("text-chat-davinci-002-20221122")

    def parse_response(self, response: AnyDict) -> list[str]:
        for choice in response["choices"]:
            if (reason := choice["finish_details"]["type"]) != "stop":
                print(f"Generation {choice['index']} finished before the end token was reached, {reason=}")

        return [choice["text"].strip() for choice in response["choices"]]


class CachingGPTClient(GPTClient):
    """GPT client that caches the requests in order to avoid unnecessary charges"""

    def __init__(self, delegate: GPTClient):
        super().__init__(delegate.model)
        self._num_requests = 0
        self._delegate = delegate

    @file_cache("gpt", is_method=True)
    async def complete_text(
        self,
        prompt: str,
        num_choices: int,
        max_tokens: int,
        temperature: float,
        stop_words: list[str] | None = None,
    ) -> list[str]:
        if self._num_requests > 20:
            raise Exception("Too many requests, exiting to prevent accidental infinite loop")
        self._num_requests += 1
        return await self._delegate.complete_text(prompt, num_choices, max_tokens, temperature, stop_words)


def create_gpt_client(api_key: str, model: str) -> GPTClient:
    openai.api_key = api_key
    client = GPTClient(model)
    return client if not Configuration.DEBUG else CachingGPTClient(client)
