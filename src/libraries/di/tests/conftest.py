from typing import List, Optional

import pytest

from ps.di import DI


class Counter:
    def __init__(self) -> None:
        self.value = 0

    def increment(self) -> None:
        self.value += 1


class Service:
    def __init__(self, name: str) -> None:
        self.name = name


class DependentService:
    def __init__(self, service: Service) -> None:
        self.service = service


class ComplexService:
    def __init__(
        self,
        name: str,
        service: Service,
        counter: Optional[Counter] = None,
        services: Optional[List[Service]] = None,
        default_value: str = "default",
    ) -> None:
        self.name = name
        self.service = service
        self.counter = counter
        self.services = services or []
        self.default_value = default_value


@pytest.fixture
def di() -> DI:
    return DI()
