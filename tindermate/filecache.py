# mypy: ignore-errors
import asyncio
import functools
import hashlib
import inspect
import pickle
from collections.abc import Callable
from pathlib import Path
from typing import Generic, ParamSpec, TypeVar

from configuration import Configuration


def _hash_string(string: str) -> str:
    return hashlib.sha256(string.encode("utf-8")).hexdigest()


P = ParamSpec("P")
R = TypeVar("R")
FileCacheDecorator = Callable[P, R]

CACHE_DIR: str | Path | None = Configuration.CACHE_DIR


class file_cache_custom_key(Generic[P, R]):
    """Decorator for caching function results to file based on an arbitrary key"""

    def __init__(self, key: str, cache_dir: str | Path | None = None, namespace: str | None = None):
        self.namespace = namespace
        self.key = key
        cache_dir = cache_dir or CACHE_DIR

        if cache_dir is None:
            raise ValueError("Cache directory not specified")

        if not isinstance(cache_dir, Path):
            cache_dir = Path(cache_dir)

        if not cache_dir.exists():
            raise ValueError(f"Cache directory {cache_dir} does not exist")

        if namespace is not None and (parts := namespace.split(".")):
            cache_dir = cache_dir.joinpath(*parts)
        self.cache_file = cache_dir / (_hash_string(key) + ".txt")
        self.hits = self.misses = 0

    def read(self) -> R:
        with self.cache_file.open("rb") as f:
            content = pickle.load(f)
        self.hits += 1
        print(f"Resource {self.key} loaded from cache")
        return content

    def write(self, content: R) -> None:
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with self.cache_file.open(mode="wb") as f:
                pickle.dump(content, f)
            self.misses += 1
            print(f"Resource {self.key} saved to cache")
        except Exception as exc:
            print(f"Failed to write to cache: {str(exc)}")

    def sync_wrapper(self, func: Callable[P, R], *args: P.args, **kwargs: P.kwargs) -> R:
        """Wrapper for sync functions"""
        if self.cache_file.exists():
            return self.read()
        content = func(*args, **kwargs)
        self.write(content)
        return content

    def sync_gen_wrapper(self, func: Callable[P, R], *args: P.args, **kwargs: P.kwargs) -> R:
        """Wrapper for sync generators"""
        if self.cache_file.exists():
            yield from self.read()
        else:
            content = []
            for item in func(*args, **kwargs):
                content.append(item)
                yield item
            self.write(content)

    async def async_wrapper(self, func: Callable[P, R], *args: P.args, **kwargs: P.kwargs) -> R:
        """Wrapper for async functions"""
        if self.cache_file.exists():
            return self.read()
        content = await func(*args, **kwargs)
        self.write(content)
        return content

    async def async_gen_wrapper(self, func: Callable[P, R], *args: P.args, **kwargs: P.kwargs) -> R:
        """Wrapper for async generators"""
        if self.cache_file.exists():
            for item in self.read():
                yield item
            return
        content = []
        async for item in func(*args, **kwargs):
            content.append(item)
            yield item
        self.write(content)

    def __call__(self, func: Callable[P, R]) -> Callable[P, R]:
        """Create async or sync wrapper based on the type of the wrapped function"""
        if asyncio.iscoroutinefunction(func):
            wrapper = self.async_wrapper
        elif inspect.isasyncgenfunction(func):
            wrapper = self.async_gen_wrapper
        elif inspect.isgeneratorfunction(func):
            wrapper = self.sync_gen_wrapper
        else:
            wrapper = self.sync_wrapper

        return functools.wraps(func)(functools.partial(wrapper, func))


def file_cache(
    cache_dir: str | None = None, namespace: str | None = None, is_method: bool = False
) -> FileCacheDecorator:
    """Decorator to cache the result of a function call based on its unique arguments"""

    def decorator(func: Callable[P, R]):
        # @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            # ignore the self argument of a method
            key_args = args[1:] if is_method else args
            key = _make_key(func, key_args, kwargs)
            return file_cache_custom_key[P, R](key, cache_dir, namespace)(func)(*args, **kwargs)

        return wrapper

    return decorator


def _make_key(func: Callable, args: tuple, kwargs: dict) -> str:
    """
    Create a unique key for a function call.
    Each function call is uniquely identified by its name and the arguments it was called with.
    """
    key_parts = [
        func.__name__,
        "_".join(str(arg) for arg in args),
        "_".join(f"{k}={v}" for k, v in kwargs.items()),
    ]
    return ":".join(kp for kp in key_parts if kp)
