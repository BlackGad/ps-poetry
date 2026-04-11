from cleo.io.io import IO

from ._models import DependencyNode, DependencyResolution, ProjectResolution, PublishWave
from ._protocol import DeliveryRenderer


class FormattedDeliveryRenderer(DeliveryRenderer):
    def __init__(self, io: IO) -> None:
        self._io = io

    def render_resolution(self, title: str, resolutions: list[ProjectResolution]) -> None:
        self._io.write_line("")
        self._io.write_line(f"<fg=magenta>{title}:</>")
        for r in resolutions:
            self._io.write_line(f"<fg=magenta>Resolving project:</> <fg=blue>{r.name}</> [<fg=dark_gray>{r.path}</>]")

            if r.deliver == "Enabled":
                deliver_label = "<fg=green>Enabled</>"
            elif r.deliver == "DisabledByPackageMode":
                deliver_label = "<fg=red>Disabled (package-mode)</>"
            else:
                deliver_label = "<fg=red>Disabled (deliver option)</>"
            self._io.write_line(f"  - Deliverable: {deliver_label}")

            if self._io.is_debug():
                for i, pr in enumerate(r.pattern_results, 1):
                    self._io.write_line(f"  <fg=dark_gray>- Version pattern [{i}]: '<fg=cyan>{pr.pattern}</>'</>")
                    if pr.condition and pr.condition_matched is not None:
                        if pr.errors:
                            self._io.write_line(f"  <fg=dark_gray>- Version: Condition '<fg=cyan>{pr.condition}</> did not match (validation failed).</>")
                            for error in pr.errors:
                                self._io.write_line(f"    <fg=dark_gray>- <fg=red>{error}</></>")
                        elif not pr.condition_matched:
                            self._io.write_line(f"  <fg=dark_gray>- Version: Condition '<fg=cyan>{pr.condition}</> evaluated to false.</>")
                        else:
                            self._io.write_line(f"  <fg=dark_gray>- Version: Condition '<fg=cyan>{pr.condition}</> evaluated to true.</>")
                    if not pr.matched and pr.resolved_raw:
                        self._io.write_line(f"  <fg=dark_gray>- Version pattern '<fg=cyan>{pr.pattern}</> resolved to '<fg=yellow>{pr.resolved_raw}</> but is not a valid version.</>")
                    elif not pr.matched and pr.errors and not pr.condition:
                        self._io.write_line(f"  <fg=dark_gray>- Version pattern '<fg=cyan>{pr.pattern}</> is invalid.</>")
                        for error in pr.errors:
                            self._io.write_line(f"    <fg=dark_gray>- <fg=red>{error}</></>")

            if r.version:
                if self._io.is_verbose():
                    self._io.write_line(f"  - Version: <fg=green>{r.version}</> (Pattern: '<fg=cyan>{r.matched_pattern}</>', Pinning rule: <fg=cyan>{r.pinning}</>)")
                else:
                    self._io.write_line(f"  - Version: <fg=green>{r.version}</>")

            self._render_dependencies(r.dependencies)

    def render_dependency_tree(self, title: str, roots: list[DependencyNode]) -> None:
        self._io.write_line("")
        self._io.write_line(f"<fg=magenta>{title}:</>")
        for i, root in enumerate(roots):
            is_last = i == len(roots) - 1
            self._print_node(
                root,
                "  " + ("└── " if is_last else "├── "),
                "  " + ("    " if is_last else "│   "),
            )

    def _print_node(self, node: DependencyNode, prefix: str, child_prefix: str) -> None:
        self._io.write_line(f"{prefix}<fg=blue>{node.name}</> <fg=green>{node.version}</>")
        for i, child in enumerate(node.children):
            is_last = i == len(node.children) - 1
            self._print_node(
                child,
                child_prefix + ("└── " if is_last else "├── "),
                child_prefix + ("    " if is_last else "│   "),
            )

    def render_publish_waves(self, title: str, waves: list[PublishWave]) -> None:
        self._io.write_line("")
        self._io.write_line(f"<fg=magenta>{title}:</>")
        for i, wave in enumerate(waves):
            is_last_wave = i == len(waves) - 1
            wave_prefix = "└── " if is_last_wave else "├── "
            child_prefix = "    " if is_last_wave else "│   "
            self._io.write_line(f"  {wave_prefix}<fg=magenta>Wave {wave.index}</>")
            for j, p in enumerate(wave.projects):
                is_last_item = j == len(wave.projects) - 1
                item_prefix = "└── " if is_last_item else "├── "
                self._io.write_line(f"  {child_prefix}{item_prefix}<fg=blue>{p.name}</> <fg=green>{p.version}</>")

    def _render_dependencies(self, dependencies: list[DependencyResolution]) -> None:
        for dep in dependencies:
            if dep.is_project:
                base_line = f"  - Project dependency '<fg=cyan>{dep.name}</>'"
                if self._io.is_verbose() and dep.path:
                    self._io.write_line(f"{base_line} [<fg=dark_gray>{dep.path}</>]")
                else:
                    self._io.write_line(base_line)
            elif dep.source == "skipped":
                if self._io.is_debug():
                    self._io.write_line(f"  <fg=dark_gray>- Dependency '<fg=cyan>{dep.name}</> skipped (no version constraint).</>")
            else:
                base_line = f"  - Dependency '<fg=cyan>{dep.name}</>': <fg=green>{dep.constraint}</>"
                detail = None
                if dep.source == "host":
                    detail = f"Resolved from <fg=cyan>host</>: <fg=green>{dep.constraint}</>"
                elif dep.source in ("host-no-constraint", "not-found"):
                    detail = f"from <fg=cyan>{dep.source}</>"
                elif dep.source == "direct" and self._io.is_debug():
                    detail = "<fg=dark_gray>direct</>"

                if detail and self._io.is_verbose():
                    self._io.write_line(f"{base_line} ({detail})")
                elif not self._io.is_debug() or detail:
                    self._io.write_line(base_line)

    def render_message(self, text: str) -> None:
        self._io.write_line(text)

    def flush(self) -> None:
        pass
