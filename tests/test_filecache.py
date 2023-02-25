import asyncio
import pytest

from typing import AsyncIterator

from filecache import file_cache, file_cache_custom_key, make_key


@pytest.fixture(scope="function")
def cache_dir(tmp_path):
    path = tmp_path / "cache"
    path.mkdir(exist_ok=True)
    return path


def test_sync_function_cache(cache_dir):

    @file_cache_custom_key(key="haha", namespace="module", cache_dir=cache_dir)
    def add_numbers(a: int, b: int) -> int:
        return a + b

    assert add_numbers(2, 3) == 5
    assert add_numbers(2, 3) == 5  # should come from cache

    key = make_key(add_numbers, (2, 3), {})
    assert (cache_dir / "module" / f"{key}.txt").exists() is True


def test_async_function_cache(cache_dir):

    @file_cache(cache_dir=cache_dir, namespace="module.submodule")
    async def multiply_numbers(a: int, b: int) -> int:
        return a * b

    assert asyncio.run(multiply_numbers(2, 3)) == 6
    assert asyncio.run(multiply_numbers(2, 3)) == 6  # should come from cache

    assert asyncio.run(multiply_numbers(2, 4)) == 8  # should not come from cache

    key = make_key(multiply_numbers, (2, 3), {})
    assert (cache_dir / "module" / "submodule" / f"{key}.txt").exists() is True


def test_sync_generator_cache(cache_dir):

    @file_cache(cache_dir=cache_dir)
    def repeat_word(word: str, n: int) -> str:
        for i in range(n):
            yield word

    gen = repeat_word("hello", 3)
    assert list(gen) == ["hello", "hello", "hello"]

    gen = repeat_word("hello", 3)
    assert list(gen) == ["hello", "hello", "hello"]  # should come from cache

    key = make_key(repeat_word, ("hello", 3), {})
    assert (cache_dir / f"{key}.txt").exists() is True


@pytest.mark.asyncio
async def test_async_generator_cache(cache_dir):

    @file_cache(cache_dir=cache_dir)
    async def async_gen(n: int) -> AsyncIterator[int]:
        for i in range(n):
            # await asyncio.sleep(0)
            yield i

    gen = [item async for item in async_gen(3)]
    assert list(gen) == [0, 1, 2]

    gen = [item async for item in async_gen(3)]
    assert list(gen) == [0, 1, 2]  # should come from cache

    key = make_key(async_gen, (3,), {})
    assert (cache_dir / f"{key}.txt").exists() is True


@pytest.fixture
def cache_test_cls(cache_dir):
    class CacheTestClass:
        @file_cache(cache_dir=cache_dir, is_method=True)
        def instance_method(self, x: int, y: int) -> int:
            return x + y

        @classmethod
        @file_cache(cache_dir=cache_dir, is_method=True)
        def class_method(cls, x: int, y: int) -> int:
            return x * y

    return CacheTestClass


# TODO

def test_file_cache_instance_method(cache_test_cls, cache_dir):
    obj = cache_test_cls()
    result1 = obj.instance_method(2, 3)
    result2 = obj.instance_method(2, 3)
    assert result1 == result2
    key = make_key(obj.instance_method, (2, 3), {})
    assert (cache_dir / f"{key}.txt").exists() is True


def test_file_cache_class_method(cache_test_cls, cache_dir):
    result1 = cache_test_cls.class_method(2, 3)
    result2 = cache_test_cls.class_method(2, 3)
    assert result1 == result2
    key = make_key(cache_test_cls.class_method, (2, 3), {})
    assert (cache_dir / f"{key}.txt").exists() is True
