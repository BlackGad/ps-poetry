from enum import Enum


class VersionConstraint(str, Enum):
    EXACT = "exact"
    MINIMUM_ONLY = "minimum-only"
    RANGE_NEXT_MAJOR = "range-next-major"
    RANGE_NEXT_MINOR = "range-next-minor"
    RANGE_NEXT_PATCH = "range-next-patch"
    COMPATIBLE = "compatible"
