import asyncio
import functools
import hashlib
import inspect
import pickle
import time
from collections.abc import Callable
from typing import ParamSpec, TypeVar

from configuration import Configuration


def hash_string(string: str) -> str:
    return hashlib.sha256(string.encode("utf-8")).hexdigest()


R = TypeVar("R")
P = ParamSpec("P")


class FileCache:

    def __init__(self, resource_name: str, key: str) -> None:
        self.resource_name = resource_name
        self.key_hash = hash_string(key)
        self.cache_file = Configuration.CACHE_DIR / resource_name / (self.key_hash + ".txt")

    def read(self) -> R:
        with self.cache_file.open("rb") as f:
            content = pickle.load(f)
        print(f"Resource {self.resource_name} with key {self.key_hash} loaded from cache")
        return content

    def write(self, content: R) -> None:
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with self.cache_file.open(mode="wb") as f:
                pickle.dump(content, f)
            print(f"Resource {self.resource_name} with key {self.key_hash} saved to cache")
        except Exception as exc:
            print(f"Failed to write to cache: {str(exc)}")

    async def async_wrapper(self, func: Callable[P, R], *args, **kwargs) -> R:
        """Wrapper for async functions"""
        if self.cache_file.exists():
            return self.read()
        content = await func(*args, **kwargs)
        self.write(content)
        return content

    async def async_gen_wrapper(self, func: Callable[P, R], *args, **kwargs) -> R:
        """Wrapper for async generators"""
        if self.cache_file.exists():
            for item in self.read():
                yield item
            return
        content = []
        async for item in func(*args, **kwargs):
            content.append(item)
        self.write(content)
        for item in content:
            yield item

    def sync_wrapper(self, func: Callable[P, R], *args, **kwargs) -> R:
        """Wrapper for sync functions"""
        if self.cache_file.exists():
            return self.read()
        content = func(*args, **kwargs)
        self.write(content)
        return content

    def __call__(self, func: Callable[P, R]) -> Callable[P, R]:
        """Create async or sync wrapper based on the type of the wrapped function"""
        if asyncio.iscoroutinefunction(func):
            wrapper = self.async_wrapper
        elif inspect.isasyncgenfunction(func):
            wrapper = self.async_gen_wrapper
        else:
            wrapper = self.sync_wrapper

        return functools.wraps(func)(functools.partial(wrapper, func))


def arg_key_file_cache(resource_name: str, is_method: bool = False) -> Callable[P, R]:
    """Decorator to cache the result of a function call based on its unique arguments"""
    def decorator(func: Callable[P, R]):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # ignore the self argument of a method
            key_args = args[1:] if is_method else args
            key_parts = [
                '_'.join(str(arg) for arg in key_args),
                '_'.join(f"{k}={v}" for k, v in kwargs.items())
            ]
            # each function call is uniquely identified by its name and the argument it was called with
            key = func.__name__ + "__".join(kp for kp in key_parts if kp)
            return FileCache(resource_name, key)(func)(*args, **kwargs)
        return wrapper
    return decorator


def time_sleep(secs: float) -> None:
    print(f"sleep({secs})")
    time.sleep(secs)
