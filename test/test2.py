# coding="utf-8"

if __name__ == "__main__":

    import hicsv
    import numpy as np

    # empty file test 1
    d1 = hicsv.hicsv()

    d1.append_column("int column", np.array([0, 1, 2, 3]))
    d1.append_column("float column", np.array([0.0, 1.0, 2.0, 3.0]))
    d1.append_column("str column", np.array(["0.0", "1.0", "2.0", "3.0"]))
    d1.append_column("ユニコード文字列カラム", np.array(["零", "いち", "に", "さん"]))
    d1.h["some metadata"] = "spam"
    d1.h["ユニコードもOK"] = "です"
    d1.save("test2.txt")

    d2 = hicsv.hicsv("test2.txt")
    print(d2)
    print(repr(d2))

    print(d2.ga("int column"))
    print(d2.ga("int column", "float column"))
    print(d2.ga(3, "float column")) # specify by index

    try:
        print(d2.ga("存在しないカラム"))
    except KeyError as e:
        print(repr(e))

    # example
    d3 = hicsv.hicsv()
    d3.h["some metadata entry"] = "some metadata"
    d3.h["it can be anything"] = {"that": "can be made into a JSON file", "for example": "a dictionary"}
    d3.h["もちろん"] = "ユニコード文字もOK"

    d3.append_column("first column", np.random.rand(5))
    d3.append_column("2nd column", np.arange(5))
    d3.append_column("column 3", np.array(["string", "is", "also", "OK", "!"]))
    d3.append_column("四番目のカラム", np.array(["いち", "に", "さん", "よん", "ご"]))

    d3.save("example.txt")