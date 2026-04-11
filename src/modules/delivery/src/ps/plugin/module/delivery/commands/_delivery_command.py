from cleo.commands.command import Command
from cleo.io.inputs.option import Option

from ps.di import DI
from ..output import DeliveryRenderer, FormattedDeliveryRenderer, JsonDeliveryRenderer
from ps.plugin.sdk.project import Environment

from ..stages import (
    DeliverableType,
    ResolvedProjectMetadata,
    build_dependency_tree,
    build_publish_waves,
    resolve_environment_metadata,
)


class DeliveryCommand(Command):
    name = "delivery"
    description = "Display the workspace delivery plan."
    arguments = []
    options = [
        Option("--json", flag=True, description="Output as JSON"),
        Option("--publish-order", flag=True, description="Show publish order"),
        Option("--dependency-tree", flag=True, description="Show dependency tree"),
        Option("--projects", flag=True, description="Show projects"),
    ]

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

        renderer: DeliveryRenderer = JsonDeliveryRenderer(io) if self.option("json") else FormattedDeliveryRenderer(io)
        show_publish_order = self.option("publish-order")
        show_dependency_tree = self.option("dependency-tree")
        show_projects = self.option("projects")
        has_filter = show_publish_order or show_dependency_tree or show_projects

        if not has_filter or show_projects:
            renderer.render_resolution("Projects", environment_metadata.resolutions)

        if not has_filter or show_dependency_tree:
            nodes = build_dependency_tree(all_projects, environment, environment_metadata)
            renderer.render_dependency_tree("Dependency tree", nodes)

        if not has_filter or show_publish_order:
            if not filtered:
                renderer.render_message("<comment>No deliverable projects.</comment>")
            else:
                waves = build_publish_waves(filtered, environment, environment_metadata)
                renderer.render_publish_waves("Publish order", waves)

        renderer.flush()
        return 0
