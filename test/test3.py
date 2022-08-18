# coding="utf-8"

if __name__ == "__main__":
    
    import numpy as np
    import hicsv

    d = hicsv.hicsv("test2.txt")

    print(d)
    print(repr(d))

    d.remove_column("ユニコード文字列カラム")

    print(d)
    print(repr(d))

    d.append_column("additional column", np.array([100, 200, 300, 400]))

    print(d)
    print(repr(d))

    d.insert_column(1, "inserted column", np.array([1000, 2000, 3000, 4000]))

    print(d)
    print(repr(d))


    d.remove_column(0) # specify by index

    print(d)
    print(repr(d))


    d.replace_column("str column", np.array(["one", "two", "three", "four"]))

    print(d)
    print(repr(d))
