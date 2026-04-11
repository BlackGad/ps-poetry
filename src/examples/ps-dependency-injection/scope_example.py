from ps.di import DI


class Logger:
    def __init__(self, name: str) -> None:
        self.name = name

    def log(self, message: str) -> None:
        print(f"[{self.name}] {message}")


class RequestContext:
    def __init__(self, request_id: str) -> None:
        self.request_id = request_id


class RequestHandler:
    def __init__(self, logger: Logger, context: RequestContext) -> None:
        self.logger = logger
        self.context = context

    def handle(self) -> str:
        self.logger.log(f"Handling request {self.context.request_id}")
        return f"response-{self.context.request_id}"


def main() -> None:
    # Root container with application-level singletons
    di = DI()
    di.register(Logger).factory(Logger, "app")

    # Per-request scope: adds request-specific registrations
    with di.scope() as request_scope:
        request_scope.register(RequestContext).factory(RequestContext, "req-42")

        handler = request_scope.spawn(RequestHandler)
        print(handler.handle())

        # Logger comes from the parent scope
        logger = request_scope.resolve(Logger)
        assert logger is not None
        logger.log("Request complete")

    # Scoped registrations are cleared after the with block
    assert request_scope.resolve(RequestContext) is None

    # Parent container is unaffected
    assert di.resolve(Logger) is not None


if __name__ == "__main__":
    main()
