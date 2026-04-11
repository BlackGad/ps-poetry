import json
from typing import Any

from cleo.io.io import IO

from ._models import DependencyNode, ProjectResolution, PublishWave
from ._protocol import DeliveryRenderer


class JsonDeliveryRenderer(DeliveryRenderer):
    def __init__(self, io: IO) -> None:
        self._io = io
        self._data: dict[str, Any] = {}

    def render_resolution(self, title: str, resolutions: list[ProjectResolution]) -> None:
        self._data[self._key(title)] = [
            {
                "name": r.name,
                "path": r.path,
                "version": r.version,
                "deliver": r.deliver,
                "pinning": r.pinning,
                "matched_pattern": r.matched_pattern,
                "pattern_results": [
                    {
                        "pattern": pr.pattern,
                        "condition": pr.condition,
                        "condition_matched": pr.condition_matched,
                        "resolved_raw": pr.resolved_raw,
                        "matched": pr.matched,
                        "errors": pr.errors,
                    }
                    for pr in r.pattern_results
                ],
                "dependencies": [
                    {
                        "name": d.name,
                        "constraint": d.constraint,
                        "is_project": d.is_project,
                        "path": d.path,
                        "source": d.source,
                    }
                    for d in r.dependencies
                ],
            }
            for r in resolutions
        ]

    def render_dependency_tree(self, title: str, roots: list[DependencyNode]) -> None:
        self._data[self._key(title)] = [self._node_to_dict(n) for n in roots]

    def render_publish_waves(self, title: str, waves: list[PublishWave]) -> None:
        self._data[self._key(title)] = [
            {
                "wave": w.index,
                "projects": [{"name": p.name, "version": p.version} for p in w.projects],
            }
            for w in waves
        ]

    def render_message(self, text: str) -> None:
        pass

    def flush(self) -> None:
        self._io.write_line(json.dumps(self._data, indent=2))
        self._data = {}

    def _node_to_dict(self, node: DependencyNode) -> dict:
        result: dict[str, Any] = {"name": node.name, "version": node.version}
        if node.children:
            result["children"] = [self._node_to_dict(c) for c in node.children]
        return result

    @staticmethod
    def _key(title: str) -> str:
        return title.lower().replace(" ", "_")
