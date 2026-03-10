from ps.version import Version, VersionConstraint


def main() -> None:
    version = Version.parse("1.2.3")
    assert version is not None

    print(version.get_constraint(VersionConstraint.EXACT))            # ==1.2.3
    print(version.get_constraint(VersionConstraint.MINIMUM_ONLY))     # >=1.2.3
    print(version.get_constraint(VersionConstraint.RANGE_NEXT_MAJOR))  # >=1.2.3,<2.0.0
    print(version.get_constraint(VersionConstraint.RANGE_NEXT_MINOR))  # >=1.2.3,<1.3.0
    print(version.get_constraint(VersionConstraint.RANGE_NEXT_PATCH))  # >=1.2.3,<1.2.4
    print(version.get_constraint(VersionConstraint.COMPATIBLE))       # >=1.2.3,<2.0.0


if __name__ == "__main__":
    main()
