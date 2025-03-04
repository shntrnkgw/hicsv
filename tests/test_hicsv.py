# coding="utf-8"

import pytest
import hicsv
import os
import numpy as np

HEADER_DICT_SINGLES = {"test key 0": "test value 0", 
                       "テストキー1": "テスト値2"}

HEADER_DICT_LISTS = {"test key 2": [0.0, 0.1, 0.2], }

HEADER_DICT_DICTS = {"test key 3": {"inner test key 0": 0, 
                                    "inner test key 1": "内側テスト値1"}}

PATH_TEMP = "tests/temp.txt"

@pytest.mark.filterwarnings("error")
def test_no_table():
    
    # create test object and write to a file
    hc = hicsv.hicsv()
    hc.h.update(HEADER_DICT_SINGLES)
    hc.h.update(HEADER_DICT_LISTS)
    hc.h.update(HEADER_DICT_DICTS)
    hc.save(PATH_TEMP, encoding="utf-8")

    # read from a file and delete
    hc2 = hicsv.hicsv(PATH_TEMP, mode="r", encoding="utf-8")
    os.remove(PATH_TEMP)

    # test header
    for k, v in HEADER_DICT_SINGLES.items():
        assert hc2.h[k] == v
    
    for k, v in HEADER_DICT_LISTS.items():
        assert hc2.h[k] == v
    
    for k, v in HEADER_DICT_DICTS.items():
        assert hc2.h[k] == v

    # test other items
    assert hc2.h["hicsv-python version"] == hicsv.__version__
    assert hc2.h["hicsv version"] == hicsv.HICSV_VERSION

    # test exception for no columns
    with pytest.raises(IndexError):
        hc2.ga(0)

    with pytest.raises(KeyError):
        hc2.ga("this key does not exist")

@pytest.mark.filterwarnings("error")
def test_float_table():
    
    # create test object and write to a file
    hc = hicsv.hicsv()

    rng = np.random.default_rng()
    arr0 = rng.random(100)
    arr1 = rng.random(100)

    ck0 = "column key 0"
    ck1 = "カラムキー1"

    hc.append_column(ck0, arr0)
    hc.append_column(ck1, arr1)

    hc.save(PATH_TEMP, encoding="utf-8")

    # read from a file and delete
    hc2 = hicsv.hicsv(PATH_TEMP, encoding="utf-8")
    os.remove(PATH_TEMP)

    # test header
    assert hc2.h["hicsv-python version"] == hicsv.__version__
    assert hc2.h["hicsv version"] == hicsv.HICSV_VERSION

    arr0_read, arr1_read = hc2.ga(ck0, ck1)

    assert np.array_equal(arr0_read, arr0, equal_nan=True)
    assert np.array_equal(arr1_read, arr1, equal_nan=True)

@pytest.mark.filterwarnings("error")
def test_float_table_with_nan():
    
    # create test object and write to a file
    hc = hicsv.hicsv()

    rng = np.random.default_rng()
    arr0 = rng.random(100)
    arr1 = rng.random(100)

    arr0[0] = np.nan
    arr1[-1] = np.nan

    ck0 = "column start with nan"
    ck1 = "column ends with nan"

    hc.append_column(ck0, arr0)
    hc.append_column(ck1, arr1)

    hc.save(PATH_TEMP, encoding="utf-8")

    # read from a file and delete
    hc2 = hicsv.hicsv(PATH_TEMP, encoding="utf-8")
    os.remove(PATH_TEMP)

    # test header
    assert hc2.h["hicsv-python version"] == hicsv.__version__
    assert hc2.h["hicsv version"] == hicsv.HICSV_VERSION

    assert np.array_equal(hc2.ga(ck0), arr0, equal_nan=True)
    assert np.array_equal(hc2.ga(ck1), arr1, equal_nan=True)

@pytest.mark.filterwarnings("error")
def test_string_table():
    
    # create test object and write to a file
    hc = hicsv.hicsv()

    rng = np.random.default_rng()
    arr0 = np.array([f"s{i}" for i in range(100)])
    arr1 = rng.random(100).astype(str)

    ck0 = "string column"
    ck1 = "quoted float column"

    hc.append_column(ck0, arr0)
    hc.append_column(ck1, arr1)

    print(hc.cols)

    hc.save(PATH_TEMP, encoding="utf-8")

    # read from a file and delete
    hc2 = hicsv.hicsv(PATH_TEMP, encoding="utf-8")
    os.remove(PATH_TEMP)

    # test header
    assert hc2.h["hicsv-python version"] == hicsv.__version__
    assert hc2.h["hicsv version"] == hicsv.HICSV_VERSION

    print(arr0)

    # assert np.array_equal(hc2.ga(ck0), arr0)
    assert np.all(hc2.ga(ck0) == arr0)
    assert np.all(hc2.ga(ck1) == arr1.astype(float))