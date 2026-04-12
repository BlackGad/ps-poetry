import re
from importlib.metadata import distributions
from pathlib import Path
from typing import Any

import tomlkit
from cleo.commands.command import Command

from ps.plugin.sdk.setup_extension_template import ExtensionTemplate, ExtensionTemplateQuestion
from ps.plugin.sdk.project import Environment

_VALID_NAME_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9_-]*$")


def _to_safe_name(name: str) -> str:
    return name.replace("-", "_").replace(".", "_")


def _to_snake_name(name: str) -> str:
    return _to_safe_name(name).lower()


def _to_pascal_name(name: str) -> str:
    parts = re.split(r"[-_.\s]+", name)
    return "".join(part.capitalize() for part in parts if part)


class SetupExtensionCommand(Command):
    name = "ps setup-extension"
    description = "Interactively create a new ps-plugin extension module."

    def __init__(self, environment: Environment, templates: list[ExtensionTemplate]) -> None:
        super().__init__()
        self._environment = environment
        self._templates = templates

    def handle(self) -> int:
        project = self._environment.host_project
        document = project.document

        if not self._check_package_mode(document):
            return 1

        extension_name = self._ask_extension_name()
        if extension_name is None:
            return 1

        snake_name = _to_snake_name(extension_name)

        if self._has_entry_point_collision(document, snake_name):
            self.line(
                f"<error>Entry point '{snake_name}' already exists in "
                f"[project.entry-points.\"ps.module\"]. Choose a different name.</error>"
            )
            return 1

        template = self._ask_template(self._templates)

        for dep in template.dependencies:
            self._ensure_dependency(dep)

        variables = self._ask_questions(template.questions)
        variables["name"] = extension_name
        variables["safe_name"] = _to_safe_name(extension_name)
        variables["snake_name"] = snake_name
        variables["pascal_name"] = _to_pascal_name(extension_name)

        variables = template.prepare_variables(variables)
        content = template.template.format_map(variables)

        project_dir = project.path.parent
        created_files = self._write_extension_file(project_dir, snake_name, content)

        self._update_entry_points(document, snake_name)
        self._update_modules_list(document, snake_name)
        project.save()

        self._print_summary(extension_name, snake_name, created_files, project.path)
        return 0

    def _check_package_mode(self, document: tomlkit.TOMLDocument) -> bool:
        tool = document.get("tool", {})
        poetry_section = tool.get("poetry", {}) if isinstance(tool, dict) else {}
        packages = poetry_section.get("packages") if isinstance(poetry_section, dict) else None

        if packages is not None:
            return True

        self.line("")
        self.line("<error>This project is not configured in package mode.</error>")
        self.line("")
        self.line(
            "Poetry package mode is required for ps-plugin extensions to work correctly."
        )
        self.line(
            "In package mode, Poetry uses the <info>[tool.poetry] packages</info> array to"
        )
        self.line("determine which Python packages to include in the distribution.")
        self.line("")
        self.line("To enable package mode, add the following to your <info>pyproject.toml</info>:")
        self.line("")
        self.line("  <comment>[tool.poetry]</comment>")
        self.line('  <comment>packages = [{ include = "your_package", from = "src" }]</comment>')
        self.line("")
        self.line(
            "Replace <info>your_package</info> with the actual package path you want to distribute."
        )
        self.line(
            "The <info>from</info> field is optional and specifies the source root directory."
        )
        self.line("")
        self.line(
            "After adding the packages configuration, run this command again."
        )
        return False

    def _ask_extension_name(self) -> str | None:
        name = self.ask("Extension name:")
        if not name or not name.strip():
            self.line("<error>Extension name cannot be empty.</error>")
            return None

        name = name.strip()
        if not _VALID_NAME_PATTERN.match(name):
            self.line(
                "<error>Invalid extension name. Use letters, digits, hyphens, and underscores. "
                "Must start with a letter.</error>"
            )
            return None

        return name

    def _has_entry_point_collision(self, document: tomlkit.TOMLDocument, module_name: str) -> bool:
        project = document.get("project", {})
        entry_points = project.get("entry-points", {}) if isinstance(project, dict) else {}
        ps_module = entry_points.get("ps.module", {}) if isinstance(entry_points, dict) else {}
        return module_name in ps_module if isinstance(ps_module, dict) else False

    def _ask_template(self, templates: list[ExtensionTemplate]) -> ExtensionTemplate:
        names = [t.name for t in templates]
        answer = self.choice("Template:", names)
        index = names.index(answer)
        return templates[index]

    def _ask_questions(self, questions: list[ExtensionTemplateQuestion]) -> dict[str, str]:
        variables: dict[str, str] = {}
        for question in questions:
            if question.options:
                default_index = (
                    question.options.index(question.default)
                    if question.default and question.default in question.options
                    else 0
                )
                answer = self.choice(question.prompt, question.options, default=default_index)
            else:
                answer = self.ask(question.prompt, default=question.default)

            if not answer or not answer.strip():
                raise ValueError(f"Answer for '{question.name}' cannot be empty")

            variables[question.name] = answer.strip()
        return variables

    def _ensure_dependency(self, package_name: str) -> None:
        if self._is_package_installed(package_name):
            return

        self.line(f"<info>Adding '{package_name}' via poetry add...</info>")
        ret = self.call("add", package_name)
        if ret != 0:
            self.line(f"<error>Failed to add '{package_name}'.</error>")

    @staticmethod
    def _is_package_installed(package_name: str) -> bool:
        normalized = _to_snake_name(package_name)
        return any(
            _to_snake_name(dist.metadata["Name"]) == normalized
            for dist in distributions()
        )

    def _write_extension_file(self, project_dir: Path, module_name: str, content: str) -> list[Path]:
        extensions_dir = project_dir / "extensions"
        created: list[Path] = []

        if not extensions_dir.exists():
            extensions_dir.mkdir(parents=True)

        init_file = extensions_dir / "__init__.py"
        if not init_file.exists():
            init_file.write_text("")
            created.append(init_file)

        ext_file = extensions_dir / f"{module_name}.py"
        if ext_file.exists():
            self.line(f"<comment>File already exists: {ext_file.relative_to(project_dir)}</comment>")
            if not self.confirm(f"Overwrite {ext_file.name}?", default=False):
                self.line("<comment>Skipped file creation.</comment>")
                return created
        ext_file.write_text(content)
        created.append(ext_file)
        return created

    def _update_entry_points(
        self,
        document: tomlkit.TOMLDocument,
        module_name: str,
    ) -> None:
        ps_module_table = self._get_entry_points_table(document)
        if module_name not in ps_module_table:
            ps_module_table[module_name] = f"extensions.{module_name}"

    def _get_entry_points_table(self, document: tomlkit.TOMLDocument) -> Any:
        project = self._get_or_create_table(document, "project")
        if "entry-points" not in project:
            project["entry-points"] = tomlkit.table()
        entry_points = project["entry-points"]
        if "ps.module" not in entry_points:
            entry_points["ps.module"] = tomlkit.table()
        return entry_points["ps.module"]

    def _update_modules_list(self, document: tomlkit.TOMLDocument, extension_name: str) -> None:
        ps_plugin = self._get_or_create_table(document, "tool", "ps-plugin")
        modules = ps_plugin.get("modules")
        if modules is None:
            ps_plugin["modules"] = tomlkit.array()
            ps_plugin["modules"].append(extension_name)
        else:
            if extension_name not in modules:
                modules.append(extension_name)

    def _get_or_create_table(self, document: tomlkit.TOMLDocument, *keys: str) -> Any:
        current: Any = document
        for key in keys:
            if key not in current:
                current[key] = tomlkit.table()
            current = current[key]
        return current

    def _print_summary(self, extension_name: str, module_name: str, created_files: list[Path], pyproject_path: Path) -> None:
        self.line("")
        self.line(f"<info>Extension '{extension_name}' created successfully!</info>")
        self.line("")

        if created_files:
            self.line("<comment>Created files:</comment>")
            project_dir = pyproject_path.parent
            for f in created_files:
                self.line(f"  - {f.relative_to(project_dir)}")
            self.line("")

        self.line("<comment>Updated pyproject.toml:</comment>")
        self.line(f'  - Added entry point: [project.entry-points."ps.module"] {module_name} = "extensions.{module_name}"')
        self.line(f'  - Added to modules list: [tool.ps-plugin] modules = [..., "{extension_name}"]')
        self.line("")
        self.line("Run <info>poetry install</info> to activate the extension.")
