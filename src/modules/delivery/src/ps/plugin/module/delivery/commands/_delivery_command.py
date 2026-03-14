from cleo.commands.command import Command

from ps.plugin.sdk.project import Environment
from ps.plugin.sdk.di import DI

from ..stages import ResolvedProjectMetadata, resolve_environment_metadata, log_dependency_tree, log_publish_waves


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

        all_projects = list(environment.projects)
        environment_metadata = resolve_environment_metadata(
            io=io,
            input_version=None,
            host_project=environment.host_project,
            projects=all_projects,
        )

        filtered = [
            p for p in all_projects
            if (environment_metadata.projects.get(p.path) or ResolvedProjectMetadata()).deliver
        ]

        io.write_line("")
        log_dependency_tree(io, all_projects, environment_metadata)

        if not filtered:
            io.write_line("<comment>No deliverable projects.</comment>")
            return 0

        io.write_line("")
        log_publish_waves(io, filtered, environment_metadata)

        return 0
