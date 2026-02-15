from typing import Optional

from .base_resolver import BaseResolver, TokenValue


class NoneResolver(BaseResolver):
    def __init__(self):
        super().__init__(None)

    def __call__(self, args: list[str]) -> Optional[TokenValue]:
        return ""
