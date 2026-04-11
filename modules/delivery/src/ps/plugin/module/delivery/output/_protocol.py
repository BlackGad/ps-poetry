from abc import abstractmethod
from typing import Protocol, runtime_checkable

from ._models import DependencyNode, ProjectResolution, PublishWave


@runtime_checkable
class DeliveryRenderer(Protocol):
    @abstractmethod
    def render_resolution(self, title: str, resolutions: list[ProjectResolution]) -> None: ...

    @abstractmethod
    def render_dependency_tree(self, title: str, roots: list[DependencyNode]) -> None: ...

    @abstractmethod
    def render_publish_waves(self, title: str, waves: list[PublishWave]) -> None: ...

    @abstractmethod
    def render_message(self, text: str) -> None: ...

    @abstractmethod
    def flush(self) -> None: ...
