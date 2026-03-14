from enum import IntEnum


class Lifetime(IntEnum):
    UNKNOWN = 0
    SINGLETON = 1
    TRANSIENT = 2


class Priority(IntEnum):
    LOW = 0
    MEDIUM = 1
    HIGH = 2
