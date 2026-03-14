from ps.di import DI, Lifetime


class Logger:
    def __init__(self, name: str) -> None:
        self.name = name

    def log(self, message: str) -> None:
        print(f"[{self.name}] {message}")


class UserRepository:
    def __init__(self, logger: Logger) -> None:
        self.logger = logger

    def find(self, user_id: int) -> str:
        self.logger.log(f"Finding user {user_id}")
        return f"User-{user_id}"


def main() -> None:
    di = DI()

    # Register a singleton logger
    di.register(Logger).factory(Logger, "app")

    # Register a transient repository
    di.register(UserRepository, Lifetime.TRANSIENT).implementation(UserRepository)

    # Resolve services
    repo = di.resolve(UserRepository)
    assert repo is not None
    print(repo.find(42))

    # Spawn an object with automatic dependency injection
    another_repo = di.spawn(UserRepository)
    print(another_repo.find(99))


if __name__ == "__main__":
    main()
