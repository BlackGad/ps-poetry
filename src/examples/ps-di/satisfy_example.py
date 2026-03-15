from ps.di import DI, REQUIRED


class Logger:
    def __init__(self, name: str) -> None:
        self.name = name

    def log(self, message: str) -> None:
        print(f"[{self.name}] {message}")


def format_log(logger: Logger, message: str, level: str = "INFO") -> str:
    return f"[{level}] {logger.name}: {message}"


def main() -> None:
    di = DI()
    di.register(Logger).factory(Logger, "app")

    # satisfy resolves logger from DI; message must be provided at call time
    log_message = di.satisfy(format_log, message=REQUIRED)

    print(log_message(message="Application started"))
    print(log_message(message="Low disk space", level="WARNING"))

    # Override a DI-resolved dependency at call time
    debug_logger = Logger("debug")
    print(log_message(message="Debug trace", logger=debug_logger))


if __name__ == "__main__":
    main()
