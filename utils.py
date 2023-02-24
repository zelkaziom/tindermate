import asyncio
import errno
import functools
import hashlib
import inspect
import pickle
import time
from pathlib import Path
from typing import Callable, TypeVar, ParamSpec

from configuration import Configuration


def hash_string(string: str) -> str:
    return hashlib.sha256(string.encode("utf-8")).hexdigest()


def safe_open(filename: Path, **kwargs):
    dirname = filename.parent.resolve()
    if not dirname.exists():
        try:
            dirname.mkdir(parents=True, exist_ok=True)
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

    return open(filename, **kwargs)


R = TypeVar("R")
P = ParamSpec("P")


def file_cache(resource_name: str, key: str) -> Callable[P, R]:

    directory = Configuration.CACHE_DIR / resource_name

    key_hash = hash_string(key)

    def read(file: Path) -> R:
        with file.open("rb") as f:
            content = pickle.load(f)
        print(f"Resource {resource_name} with key {key_hash} loaded from cache")
        return content

    def write(file: Path, content: R) -> None:
        try:
            with safe_open(file, mode="wb") as f:
                pickle.dump(content, f)
            print(f"Resource {resource_name} with key {key_hash} saved to cache")
        except Exception as exc:
            print(f"Failed to write to cache: {str(exc)}")

    def decorator(func: Callable[P, R]) -> Callable[P, R]:

        filename: Path = directory / (key_hash + ".txt")

        # create async of sync wrapper based on the type of the wrapped function

        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                if filename.exists():
                    return read(filename)
                content = await func(*args, **kwargs)
                write(filename, content)
                return content
        elif inspect.isasyncgenfunction(func):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                if filename.exists():
                    for item in read(filename):
                        yield item
                    return
                content = []
                async for item in func(*args, **kwargs):
                    content.append(item)
                write(filename, content)
                for item in content:
                    yield item
        else:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                if filename.exists():
                    return read(filename)
                content = func(*args, **kwargs)
                write(filename, content)
                return content

        return wrapper

    return decorator


def arg_key_file_cache(resource_name: str, is_method: bool = False) -> Callable[P, R]:
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
            return file_cache(resource_name, key)(func)(*args, **kwargs)
        return wrapper
    return decorator


def time_sleep(secs: float) -> None:
    print(f"sleep({secs})")
    time.sleep(secs)
