import asyncio
import random
from http import HTTPStatus
from operator import attrgetter
from typing import Any

import aiohttp
from aiohttp import ClientResponseError

from configuration import Configuration
from tinder.exception import TinderAuthError
from tinder.schemas import CurrentUser, LikedUserResult, Match, MatchDetail, Message, UserDetail
from utils import arg_key_file_cache


class TinderClient:
    _BASE_URL = "https://api.gotinder.com"
    _FAKE_HEADERS = {
        "accept": "application/json",
        "accept-language": "en,en-US",
        "origin": "https://tinder.com",
        "platform": "web",
        "referer": "https://tinder.com/",
        "tinder-version": "4.2.0",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/109.0.0.0 Safari/537.36",
        "x-supported-image-formats": "webp,jpeg",
    }
    _FETCH_MATCHES_LIMIT = 100
    _FETCH_MESSAGES_LIMIT = 100

    def __init__(self, auth_token: str, sleep_between_requests: int = 3):
        self._auth_token = auth_token
        # by default, we avoid firing many instant requests to imitate human-like behaviour
        self._sleep_between_requests = sleep_between_requests

    def _headers(self) -> dict[str, Any]:
        return {
            **self._FAKE_HEADERS,
            "x-auth-token": self._auth_token,
        }

    async def _sleep(self) -> None:
        secs = self._sleep_between_requests * random.random()
        await asyncio.sleep(secs)

    async def _get_v2(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return (await self._get(f"/v2{path}", params))["data"]

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{self._BASE_URL}{path}"
        params = {"locale": "en"} | (params or {})

        print(f"GET {url}")
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=self._headers()) as resp:
                try:
                    resp.raise_for_status()
                except ClientResponseError as exc:
                    if resp.status == HTTPStatus.UNAUTHORIZED:
                        raise TinderAuthError("Unauthorized user") from exc
                    raise
                return await resp.json()

    async def _messages(self, match_id: str) -> list[Message]:
        params = {"count": self._FETCH_MESSAGES_LIMIT}
        results = (await self._get_v2(f"/matches/{match_id}/messages", params=params))["messages"]
        return sorted([Message.parse_obj(res) for res in results], key=attrgetter("timestamp"))

    async def _user_detail(self, user_id: str) -> UserDetail:
        result = (await self._get(f"/user/{user_id}"))["results"]
        return UserDetail.parse_obj(result)

    async def matches(self, messaged: bool) -> list[Match]:
        params = {"count": self._FETCH_MATCHES_LIMIT, "message": 1 if messaged else 0}
        results = (await self._get_v2("/matches", params=params))["matches"]
        return [Match.parse_obj(res) for res in results]

    async def fetch_detail_for(self, match: Match) -> MatchDetail:
        user_detail = await self._user_detail(match.person.id)
        return MatchDetail.parse_obj(match.dict() | {"person": user_detail.dict()})

    async def fetch_messages_for(self, match: Match) -> None:
        """Update the match with all the exchanged messages"""
        match.messages = await self._messages(match.id)

    async def my_likes(self) -> list[LikedUserResult]:
        results = (await self._get_v2("/my-likes"))["results"]
        return [LikedUserResult.parse_obj(res) for res in results]

    async def current_user_info(self) -> CurrentUser:
        resp = (await self._get_v2("/profile", params={"include": "user"}))["user"]
        return CurrentUser.parse_obj(resp)


_tinder_cache = arg_key_file_cache("tinder", is_method=True)


class CachingTinderClient(TinderClient):
    """Tinder client that caches the response payloads in order to avoid unnecessary requests while debugging"""

    def __init__(self, auth_token: str):
        super().__init__(auth_token, sleep_between_requests=2)

    @_tinder_cache
    async def matches(self, messaged: bool) -> list[Match]:
        return await super().matches(messaged)

    @_tinder_cache
    async def current_user_info(self) -> CurrentUser:
        return await super().current_user_info()

    @_tinder_cache
    async def my_likes(self) -> list[LikedUserResult]:
        return await super().my_likes()

    @_tinder_cache
    async def _messages(self, match_id: str) -> list[Message]:
        return await super()._messages(match_id)

    @_tinder_cache
    async def fetch_detail_for(self, match: Match) -> MatchDetail:
        return await super().fetch_detail_for(match)


def create_tinder_client(auth_token: str) -> TinderClient:
    return CachingTinderClient(auth_token) if Configuration.DEBUG else TinderClient(auth_token)
