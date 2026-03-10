from ps.version import Version, VersionStandard


def main() -> None:
    version = Version.parse("1.2.3-alpha.1+build.42")
    assert version is not None

    print(version.major)   # 1
    print(version.minor)   # 2
    print(version.patch)   # 3
    if version.pre is not None:
        print(version.pre.name)    # alpha
        print(version.pre.number)  # 1
    print(str(version.metadata))  # build.42

    v1 = Version.parse("1.2.3")
    v2 = Version.parse("1.2.4")
    assert v1 is not None
    assert v2 is not None
    print(v1 < v2)   # True
    print(v1 == v2)  # False

    pep = Version.parse("1.2.3a1")
    assert pep is not None
    print(pep.format(VersionStandard.SEMVER))   # 1.2.3-alpha.1 (if pre name is alpha)
    print(pep.format(VersionStandard.PEP440))   # 1.2.3a1


if __name__ == "__main__":
    main()
