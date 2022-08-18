# coding="utf-8"

if __name__ == "__main__":

    import hicsv
    import numpy as np

    # empty file test 1
    d1 = hicsv.hicsv()

    d1.save("no header contents, no keys, novalues.txt", add_version_info=False)

    d2 = hicsv.hicsv("no header contents, no keys, novalues.txt")
    print(d2)
    print(repr(d2))

    # empty file test 2
    d3 = hicsv.hicsv()
    d3.append_column("", np.array([]))

    d3.save("no header contents, single blank key, novalues.txt", add_version_info=False)

    d4 = hicsv.hicsv("no header contents, single blank key, novalues.txt")
    print(d4)
    print(repr(d4))

    # empty file test 3
    d5 = hicsv.hicsv()
    d5.append_column("key1", np.array([]))
    d5.append_column("key2", np.array([]))

    d5.save("no header contents, multiple keys, novalues.txt", add_version_info=False)

    d6 = hicsv.hicsv("no header contents, multiple keys, novalues.txt")
    print(d6)
    print(repr(d6))

    # empty file test 4
    d7 = hicsv.hicsv()
    d7.append_column("key1", np.array([]))
    d7.append_column("key2", np.array([]))

    d7.save("multiple keys, novalues.txt")

    d7 = hicsv.hicsv("multiple keys, novalues.txt")
    print(d7)
    print(repr(d7))
