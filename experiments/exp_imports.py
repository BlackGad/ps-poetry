# ruff: noqa F401
def import1():
    import ps
    print(ps)

    import ps.plugin
    print(ps.plugin)


def import2():
    import ps.plugin.core
    print(ps.plugin.core)


import1()
import2()
