from typing import Any, Optional

from ._base_resolver import BaseResolver, TokenResolver, TokenValue


class NoneResolver(BaseResolver):
    @staticmethod
    def resolve_factory(source: Any) -> Optional[TokenResolver]:
        if source is None:
            return NoneResolver()
        return None

    def __call__(self, args: list[str]) -> Optional[TokenValue]:
        return ""
