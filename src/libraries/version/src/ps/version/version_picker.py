from typing import Any, Callable, Iterable, Optional, Sequence, Tuple, Union

from .expression_factory import ExpressionFactory
from .models import Version
from .version_functions import pick_version


TokenValue = Union[str, int, bool]
TokenResolver = Callable[[list[str]], Optional[TokenValue]]
TokenResolverEntry = Tuple[str, Union[TokenResolver, Any]]


class VersionPicker:
    def __init__(self, token_resolvers: Sequence[TokenResolverEntry]) -> None:
        self._factory = ExpressionFactory(token_resolvers)

    def pick(self, inputs: Iterable[str]) -> Version:
        return pick_version(inputs, self._factory)

    def materialize(self, value: str) -> str:
        return self._factory.materialize(value)

    def match(self, condition: str) -> bool:
        return self._factory.match(condition)
