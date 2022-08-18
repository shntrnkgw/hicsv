# coding="utf-8"

import hicsv

if __name__ == "__main__":
    
    out = hicsv.txt2hicsv("non hicsv csv.csv", ignore_lines=[0, 1, 2, 6], key_line=2, keys=["a", "b", "c", "d"])

    print(out)
    print(repr(out))

    tsv = hicsv.txt2hicsv("tab separated values.txt", ignore_lines=[0, 1, 2], key_line=3, sep="\t")

    print(tsv)
    print(repr(tsv))
