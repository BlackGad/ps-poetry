from tomlkit import TOMLDocument

from ..project._toml_value import TomlValue
from ._settings import PluginSettings


def parse_plugin_settings_from_document(document: TOMLDocument) -> PluginSettings:
    project_toml = document
    settings_section = TomlValue.locate(project_toml, [f"tool.{PluginSettings.NAME}"]).value
    if settings_section is None:
        return PluginSettings(enabled=False)
    result = PluginSettings.model_validate(settings_section, by_alias=True)
    if result.enabled is None:
        result.enabled = True
    return result
