from cleo.commands.command import Command

from ps.plugin.sdk.project import Environment
from ps.di import DI

from ..stages import (
    DeliverableType,
    ResolvedProjectMetadata,
    log_dependency_tree,
    log_publish_waves,
    resolve_environment_metadata,
)


class DeliveryCommand(Command):
    name = "delivery"
    description = "Display the workspace delivery plan."
    arguments = []
    options = []

    def __init__(self, di: DI) -> None:
        super().__init__()
        self._di = di

    def handle(self) -> int:
        io = self.io
        environment = self._di.resolve(Environment)
        assert environment is not None

        environment_metadata = self._di.satisfy(resolve_environment_metadata)()
        all_projects = list(environment.projects)
        filtered = [
            p for p in all_projects
            if (environment_metadata.projects.get(p.path) or ResolvedProjectMetadata()).deliver == DeliverableType.ENABLED
        ]

        io.write_line("")
        log_dependency_tree(io, all_projects, environment_metadata)

        if not filtered:
            io.write_line("<comment>No deliverable projects.</comment>")
            return 0

        io.write_line("")
        log_publish_waves(io, filtered, environment_metadata)

        return 0
