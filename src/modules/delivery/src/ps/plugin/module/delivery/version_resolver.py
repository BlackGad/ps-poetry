from datetime import datetime


def _resolve_version(pattern: str) -> str:

    now = datetime.now()
    version = pattern.replace("{year}", now.strftime("%Y"))
    version = version.replace("{month}", now.strftime("%m"))
    version = version.replace("{day}", now.strftime("%d"))
    version = version.replace("{hour}", now.strftime("%H"))
    version = version.replace("{minute}", now.strftime("%M"))
    version = version.replace("{second}", now.strftime("%S"))
    return version
