from collections.abc import Generator
from typing import Any, TypeAlias

AnyDict: TypeAlias = dict[str, Any]

EmptyGenerator: TypeAlias = Generator[None, None, None]
