from enum import Enum
from ps.plugin.sdk.models.settings import PluginSettings
from pydantic import BaseModel


class MonorepoProjectMode(Enum):
    DISABLED = "disabled"
    HOST = "host"
    CHILD = "child"


class MonorepoSettings(BaseModel):
    monorepo: MonorepoProjectMode = MonorepoProjectMode.DISABLED

    @staticmethod
    def get_mode(plugin_settings: PluginSettings) -> MonorepoProjectMode:
        if plugin_settings.model_extra is None:
            return MonorepoProjectMode.DISABLED
        return plugin_settings.model_extra.get("monorepo", MonorepoProjectMode.DISABLED)
