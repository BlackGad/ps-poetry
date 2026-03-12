import os

from ps.token_expressions import ExpressionFactory


class AppConfig:
    def __init__(self) -> None:
        self.name = "MyApp"
        self.version = "1.0.0"
        self.tags: list[str] = ["production", "stable"]


def env_resolver(arg: str) -> str | None:
    return os.getenv(arg) if arg else None


def main() -> None:
    config = {"build": 456, "environment": "production"}

    factory = ExpressionFactory([
        ("app", AppConfig()),
        ("config", config),
        ("env", env_resolver),
    ])

    conn_str = factory.materialize("App: {app:name} v{app:version} (build {config:build})")
    print(conn_str)  # App: MyApp v1.0.0 (build 456)

    build = factory.materialize("{env:BUILD_NUMBER<unknown>}")
    print(build)  # unknown (if BUILD_NUMBER is not set)

    if factory.match("{env:DEBUG<0>}"):
        print("Debug mode enabled")

    if factory.match("'production' in {app:tags}"):
        print("Running in production mode")

    if factory.match("'stable' in {app:tags} and not {env:DEBUG<0>}"):
        print("Stable production build")


if __name__ == "__main__":
    main()
