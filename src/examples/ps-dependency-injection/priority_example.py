from typing import List

from ps.di import DI, Priority


class NotificationService:
    def __init__(self, name: str) -> None:
        self.name = name

    def notify(self, message: str) -> None:
        print(f"[{self.name}] {message}")


def main() -> None:
    di = DI()

    # Register services with different priorities
    di.register(NotificationService, priority=Priority.LOW).factory(NotificationService, "email")
    di.register(NotificationService, priority=Priority.HIGH).factory(NotificationService, "sms")
    di.register(NotificationService, priority=Priority.MEDIUM).factory(NotificationService, "push")

    # resolve returns the highest-priority registration
    primary = di.resolve(NotificationService)
    assert primary is not None
    print(f"Primary: {primary.name}")  # sms

    # resolve_many returns all registrations ordered by priority
    all_services: List[NotificationService] = di.resolve_many(NotificationService)
    for svc in all_services:
        svc.notify("Hello")


if __name__ == "__main__":
    main()
