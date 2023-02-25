import asyncio
import pytest

from typing import AsyncIterator

from filecache import file_cache


@pytest.fixture(scope="function")
def cache_dir(tmp_path):
    path = tmp_path / "cache"
    path.mkdir(exist_ok=True)
    return path


def test_sync_function_cache(cache_dir):

    @file_cache(namespace="module", cache_dir=cache_dir)
    def add_numbers(a: int, b: int) -> int:
        return a + b

    assert add_numbers(2, 3) == 5
    assert add_numbers(2, 3) == 5  # should come from cache
    assert add_numbers.hits == add_numbers.misses == 1

    assert (cache_dir / "module" / "3b3f94fa.txt").exists() is True


def test_async_function_cache(cache_dir):

    @file_cache(cache_dir=cache_dir, namespace="module.submodule")
    async def multiply_numbers(a: int, b: int) -> int:
        return a * b

    assert asyncio.run(multiply_numbers(2, 3)) == 6
    assert asyncio.run(multiply_numbers(2, 3)) == 6  # should come from cache
    assert multiply_numbers.hits == multiply_numbers.misses == 1

    assert asyncio.run(multiply_numbers(2, 4)) == 8  # should not come from cache
    assert multiply_numbers.hits == 1
    assert multiply_numbers.misses == 2

    assert (cache_dir / "module" / "submodule" / "c2f2e4b4.txt").exists() is True


def test_sync_generator_cache(cache_dir):

    @file_cache(cache_dir=cache_dir)
    def repeat_word(word: str, n: int) -> str:
        for i in range(n):
            yield word

    gen = repeat_word("hello", 3)
    assert list(gen) == ["hello", "hello", "hello"]

    gen = repeat_word("hello", 3)
    assert list(gen) == ["hello", "hello", "hello"]  # should come from cache
    assert repeat_word.hits == repeat_word.misses == 1

    assert (cache_dir / "8a828f09.txt").exists() is True


def test_async_generator_cache(cache_dir):

    @file_cache(cache_dir=cache_dir)
    async def async_gen(n: int) -> AsyncIterator[int]:
        for i in range(n):
            # await asyncio.sleep(0)
            yield i

    async def func(n: int):
        async for _ in async_gen(n):
            pass

    gen = asyncio.run(func(3))
    assert list(gen) == [0, 1, 2]

    gen = asyncio.run(func(3))
    assert list(gen) == [0, 1, 2]  # should come from cache
    assert async_gen.hits == async_gen.misses == 1

    assert (cache_dir / "a9c5d5e5.txt").exists() is True


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


def test_file_cache_instance_method(cache_test_cls):
    obj = cache_test_cls()
    result1 = obj.instance_method(2, 3)
    result2 = obj.instance_method(2, 3)
    assert obj.instance_method.misses == obj.instance_method.hits == 1
    assert result1 == result2


def test_file_cache_class_method(cache_test_cls):
    result1 = cache_test_cls.class_method(2, 3)
    result2 = cache_test_cls.class_method(2, 3)
    assert cache_test_cls.class_method.misses == cache_test_cls.class_method.hits == 1
    assert result1 == result2
