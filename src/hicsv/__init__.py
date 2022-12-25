# coding="utf-8"
"""I/O interface for hicsv (header-included comma-separated values) format. 

Header-included comma-separated values (*hicsv* or hi-csv in short)
is a text file format consisting of a header (metadata) 
and a tabulated values, both in a human-readable and editable form. 

CSV is a great universal format that can store a table of values 
in a human-readable way. 
Many instruments and softwares can export data in CSV. 
We can then avoid dealing with the proprietary binary formats 
whose specifications are often not disclosed to consumers. 

However, there is no commonly accepted method to store metadata
along with a table of values. 
Metadata such as experimental conditions, author, etc. 
are often essential in science. 
People can easily lose track of these metadata when the CSV file
only contains the table part. 

There are some formats or conventions that (try to) treat a table 
and metadata nicely (e.g. Tabular Data Package
https://specs.frictionlessdata.io/tabular-data-package/#introduction). 
But, to the best of the author's knowledge, there is no text-based 
generic format that *combines* a table and metadata in a single file. 

It is very important to combine the metadata and the table 
because it would be difficult to force everyone to 
always keep two separate files together. 

Binary formats such as HDF5 can store metadata in addition to 
image or array data. But again, there is no text-based, 
human-readable format with embedded metadata. 

*hicsv* format has been developed as a solution to the above problem. 
It is basically just a CSV table with a JSON header part attached 
at the top. The rough, tentative specification of *hicsv* is as follows. 

1. It should be a Unicode text file. 

2. It starts with consequtive lines starting with ``#``. 

3. The last one of the ``#``-capped lines represents the "keys" of each column 
   in the table. 

4. The rest of the ``#``-capped lines are an indented JSON which represents
   the dictionary of metadata. 

5. The lines not starting with ``#`` are the CSV table. 
   The CSV part follows the generally accepted conventions
   (mostly RFC 4180 but may not be strict)
   except for following additional restrictions. 

6. The columns in the CSV table should always be of the same length. 

7. Each column must consist of only one type. 

The ``hicsv`` package is a minimal implementation of the I/O interface 
to the *hicsv*-formatted files. 
It, therefore, does not have (or aim for) any advanced functionalities. 
Please use ``numpy`` and/or other useful packages for anything beyond I/O. 

Example:
    To read a hicsv-formatted text file,

        >>> import hicsv
        >>> d = hicsv.hicsv("foo.txt")
    
    Or you can just create an empty object to which 
    you can add columns and header info. 

        >>> e = hicsv.hicsv()

    You can get one or more columns. 

        >>> c1, c2 = d.ga("column 1", "column 2")
    
    The header info is stored as a dictionary. 
    You can set and get information at any time::

        >>> d.h["new header entry"] = "some value"
        >>> print(d.h["new header entry"])
        
    If you need to create a hicsv-formatted file from scratch::

        >>> out = hicsv()
    
    To add a column::

        >>> out.append_column("column 1", arr)
    
    Here ``arr`` should be a 1-d numpy array. 
    Note that all columns must be of the same length, 
    so adding an array with different length will cause error. 
    Then you can write into a hicsv-formatted text file like::

        >>> out.save("new hicsv file.txt", encoding="utf-8")

Note:
    Some users may find the following behavior of this package unexpected. 

    1. The parser deletes the spaces at the beginning and at the end of each cell. 
       This is true even if the cell content is double-quoted. 
       For example, the two cells

            "spam", "  spam  "
       
       results in identical strings. 
"""

from typing import List, IO, Any
import json, csv, io

import numpy as np

__version__ = "1.0.0"
HICSV_VERSION = "20220812"

HEADER_STARTSWITH: str = "#"
DELIMITER:         str = ","

class hicsv(object):
    """Container/writer class for a hicsv file. 

    Args:
        fp: File-like object or path to the file. 
            If an empty string, an empty object will be created. 
            If a string or a file-like object is given, 
            the file will be loaded as the object. 
            Defaults to ``""`` (empty string) which creates an empty object. 
        **kwargs: Arguments of built-in function ``open()``. (`New in 1.0.0.`)

    Attributes:
        keys: column keys. a list of strings. 
        cols: columns. a list of 1-d numpy arrays. 
        h: header. 

    Example:

        >>> import numpy as np
        >>> import hicsv
        >>> d = hicsv.hicsv() # create empty object
        >>> d.h["a new header entry"] = 1    # add an entry to the header
        >>> print(d.h["a new header entry"]) # access the header entry
        1
        >>> d.append_column("the first column", np.array([0.0, 1.0, 2.0]))  # add column
        >>> d.append_column("the second column", np.array(["a", "b", "c"])) # add another column
        >>> print(d.ga("the first column")) # access the column
        [0. 1. 2.]
        >>> print(d.ga("the first column", "the second column")) # access two columns at once
        [array([0., 1., 2.]), array(['a', 'b', 'c'], dtype='<U1')]
        >>> d.save("spam.txt") # save to a text file
        >>> d2 = hicsv.hicsv("spam.txt") # load from a file

    """

    def __init__(self, fp: str|IO = "", **kwargs: Any) -> None:
        """initializer
        """
        self.keys: List[str]        = []
        self.cols: List[np.ndarray] = []
        self.h:    dict             = {}

        if fp:
            if isinstance(fp, str):
                with open(fp, **kwargs) as f:
                    self._fromfile(f)
            else:
                self._fromfile(fp)

    def fromfile(self, fp: str|IO) -> None:
        """ Loads a hicsv file and updates the stored headers & columns. 
        
        Args:
            fp: file-like object or path to the file. 

        Note:
            It overwrites the header ``h`` and appends the loaded columns to
            the exsting ``cols`` by using ``append_column()``. 
            Therefore, if ``append_column()`` fails for any of the new columns, 
            this will not work. 
        """
        if isinstance(fp, str):
            with open(fp, "r") as f:
                self._fromfile(f)
        else:
            return self._fromfile(fp)

    def _fromfile(self, fp: IO) -> None:
        """Internal function to load a text file into a ``hicsv`` object. 
        
        Args:
            fp: file-like object. 
        """
        lines: List[str] = []
        lines_header: List[str] = []
        lines_table: List[str] = []
        i: int = 0
        ln_table_start: int = 0
        line_keys: str = ""
        keys: List[str] = []
        rows_str: List[List[str]] = []
        cols_str: List[List[str]] = []
        num_rows: int = 0
        num_cols: int = 0

        lines = fp.readlines()

        # find the start of data table (the first line without #)
        ln_table_start = 0
        for i, line in enumerate(lines):
            if not line.startswith(HEADER_STARTSWITH):
                ln_table_start = i
                break
        
        # if the line without # is not found, 
        # it's quite likely that the file does not have a table part. 
        if ln_table_start == 0:

            # first, try parsing all the lines as JSON
            try:
                hstr = "".join([l[1:] for l in lines])
                h = json.loads(hstr)
            except json.decoder.JSONDecodeError:
                pass
            else:
                # if it succeeds, then there's no keys no values. 
                self.h.update(h)

                return # no further processes!
            
            # if the first trial fails, 
            # try parsing all the lines except for the last one as JSON
            try:
                hstr = "".join([l[1:] for l in lines[:-1]])
                h = json.loads(hstr)
            except json.decoder.JSONDecodeError:
                pass
            else:
                # if it succeeds, then there's no values (only keys exist)
                line_keys = lines[-1][1:] # remove the first char (#)

                for row in csv.reader([line_keys, ], delimiter=DELIMITER):
                    keys = row
                
                self.h.update(h)
                for key in keys:
                    self.append_column(key, np.array([]))
                
                return # no further processes!

        # if ln_table_start is not zero, then it is a truly non-empty file. 
        lines_header = lines[:ln_table_start-1]
        line_keys    = lines[ln_table_start-1][1:] # remove the first char (#)
        lines_table  = lines[ln_table_start:]

        # parse header
        hstr = "".join([l[1:] for l in lines_header])
        h = json.loads(hstr)

        # parse single line for column keys
        for row in csv.reader([line_keys, ], delimiter=DELIMITER):
            keys = row

        keys = [k.strip(" ") for k in keys] # spaces at the beginning and the end are omitted

        # parse data lines
        for row in csv.reader(lines_table, delimiter=DELIMITER):
            if row:
                rows_str.append([e.strip() for e in row]) # spaces are omitted

        num_rows = len(rows_str)
        num_cols = len(keys)
        cols_str = [[rows_str[i][j] for i in range(num_rows)] for j in range(num_cols)] # same as list(zip(*row_str))

        # detect type and store arrays
        for key, col_str in zip(keys, cols_str):
            # check if it's int
            if col_str[0].isdigit():
                self.append_column(key, np.array(col_str).astype(int))
            else:
                # if not, check if it's float
                try:
                    float(col_str[0])
                except ValueError:
                    # if not, then it is stored as string
                    self.append_column(key, np.array(col_str))
                    # if it's not an int or string, then it must be a float. 
                else:
                    self.append_column(key, np.array(col_str).astype(float))
        
        self.h.update(h)
    
    def _get_column_index(self, col:int|str) -> int:
        """Internal function to convert column name (or index) into a column index

        Args:
            col: column name or index. 
        
        Returns:
            column index. 
        """
        if isinstance(col, int):
            if col < len(self.keys):
                return col
            else:
                raise IndexError("column index out of range: max. {0} but {1} given".format(len(self.keys), col))
        elif isinstance(col, str):
            try:
                return self.keys.index(col)
            except ValueError:
                raise KeyError("column key not found: '{0}'".format(col))

    def _get_column_as_array(self, col: int|str) -> np.ndarray:
        """Gets a single column by a column name or column index. 

        Args:
            col: column name or index. 

        Returns:
            a 1-d numpy array of the column. 
        """
        cid: int = self._get_column_index(col)
        return self.cols[cid]

    def get_columns_as_arrays(self, *cols: int|str) -> np.ndarray | List[np.ndarray]:
        """Gets a single column or multiple columns by column names or column indices. 

        Args:
            *cols: column names or indices. str and int can be mixed. 

        Returns:
            if one column name/index is given, a 1-d numpy array. 
            if two or more names/indices are given, a list of 1-d numpy arrays. 
        
        Example:
            >>> a1 = d.get_columns_as_arrays("column 1")
            >>> a2, a3 = d.get_columns_as_arrays("column two", "third column")
        """
        if len(cols) == 1:
            return self._get_column_as_array(cols[0])
        else:
            return [self._get_column_as_array(col) for col in cols]

    def ga(self, *cols: int|str) -> np.ndarray | List[np.ndarray]:
        """Alias for `get_columns_as_arrays()`. 

        Args:
            *cols: column names or indices. str and int can be mixed. 

        Returns:
            if one column name/index is given, a 1-d numpy array. 
            if two or more names/indices are given, a list of 1-d numpy arrays. 

        Example:
            >>> a1 = d.ga("column 1")
            >>> a2, a3 = d.ga("column two", "third column")
        """
        return self.get_columns_as_arrays(*cols)

    def insert_column(self, pos: int, key: str, arr: np.ndarray) -> None:
        """Inserts a single column into the table. 

        Args:
            pos: 
                Position of the new column. 
            key: 
                Identifier for the new column. 
                Keys already in use are not allowed. 
            arr: 
                A 1-d numpy array of the new column. 
                
                If it's the first column to be inserted, 
                it can be of any length. 
                However, if there is previously inserted column(s), 
                the new column must be of the same length as the 
                already-existing columns. 

                The dtype of the column must be the sub-type of
                ``numpy.integer``, ``numpy.floating``, or ``numpy.str_``. 

        Raises:
            ValueError: If the array dimension is not 1
                or if the array length does not match 
                that of the already existing column(s). 
            KeyError: If the key is already in use. 
            TypeError: If ``dtype`` of ``arr`` is not 
                the subtype of ``numpy.integer``, ``numpy.floating``, or ``numpy.str_``. 
        """
        ok: bool = False
        
        if arr.ndim != 1:
            raise ValueError("expected 1-d numpy array: got {0}-d array".format(arr.ndim))
        elif not (np.issubdtype(arr.dtype, np.integer) or 
                  np.issubdtype(arr.dtype, np.floating) or 
                  np.issubdtype(arr.dtype, np.str_)):
            raise TypeError("expected numpy array with the sub-dtype of numpy.integer, numpy.floating, or numpy.str_: got <{0}>".format(arr.dtype))
        elif (not self.keys) and pos==0: # first column!
            ok = True
        elif key in self.keys:
            raise KeyError("column key {0} already exists. ".format(key))
        elif self.cols[0].shape[0] != arr.shape[0]:
            raise ValueError("expected array length is {0}: got {1}".format(self.cols[0].shape[0], arr.shape[0]))
        else:
            ok = True

        if ok:
            self.keys.insert(pos, key)
            self.cols.insert(pos, arr)
    
    def append_column(self, key: str, arr: np.ndarray) -> None:
        """Appends a single column to the table. 

        Args:
            key: 
                Identifier for the new column. 
                Keys already in use are not allowed. 
            arr: 
                A 1-d numpy array of the new column. 
                
                If it's the first column to be inserted, 
                it can be of any length. 
                However, if there is previously inserted column(s), 
                the new column must be of the same length as the 
                already-existing columns. 

                The dtype of the column must be the sub-type of
                ``numpy.integer``, ``numpy.floating``, or ``numpy.str_``. 

        Raises:
            ValueError: If the array dimension is not 1
                or if the array length does not match 
                that of the already existing column(s). 
            KeyError: If the key is already in use. 
            TypeError: If ``dtype`` of ``arr`` is not 
                the subtype of ``numpy.integer``, ``numpy.floating``, or ``numpy.str_``. 

        Example:
            >>> d = hicsv.hicsv()
            >>> d.append_column("first column", np.arange(5))
            >>> d.append_column("second column", np.linspace(0.0, 1.0, 5))
            >>> d.append_column("third column", np.array(["one", "two", "three", "four", "five"]))
            >>> d.append_column("fourth column", np.array([0.0])) # this will fail due to length mismatch
        """
        self.insert_column(len(self.keys), key, arr)

    def replace_column(self, col: int|str, arr: np.ndarray) -> None:
        """Replaces the content of an existing column.

        Args:
            col: column name or index. 
            arr: 
                A 1-d numpy array of the new column. 

                It must be of the same length as the already-existing columns. 

                The dtype of the column must be the sub-type of
                ``numpy.integer``, ``numpy.floating``, or ``numpy.str_``. 

        Example:
            >>> d = hicsv.hicsv()
            >>> d.append_column("first column", np.arange(5))
            >>> d.append_column("second column", np.linspace(0.0, 1.0, 5))
            >>> print(d.ga("first column"))
            [0 1 2 3 4]
            >>> d.replace_column("first column", np.array(["one", "two", "three", "four", "five"]))
            >>> print(d.ga("first column"))
            ['one' 'two' 'three' 'four' 'five']
        """
        if arr.ndim != 1:
            raise ValueError("expected 1-d numpy array: got {0}-d array".format(arr.ndim))

        cid: int = self._get_column_index(col)
        self.cols[cid] = arr
    
    def remove_column(self, col: int|str) -> None:
        """Removes a column from the object. 

        Args:
            col: column name or index. 
        """
        cid: int = self._get_column_index(col)
        self.keys.pop(cid)
        self.cols.pop(cid)
    
    def _save(self, fp: IO, prettify: bool = True, add_version_info: bool = True) -> None:
        """Internal function to save the hicsv file. 
        
        Args:
            fp: file-like object of the destination. 
            prettify: True to turn on pretty formatting. 
            add_version_info: If True, automatically adds the current versions
                of the module and the hicsv format specification. 
        """
        h: dict = {}
        scols: List[List[str]] = []
        scol: List[str] = []

        scols_pretty: List[List[str]] = []

        hstr: str = ""
        hlines: List[str] = []
        maxwidth: int = 0
        columnwidth: int = 0

        # header
        h = {k: v for k, v in self.h.items()}
        if add_version_info:
            h["hicsv-python version"] = __version__
            h["hicsv version"] = HICSV_VERSION
        
        hstr = json.dumps(h, indent=4, ensure_ascii=False)
        hlines = hstr.split("\n")
        hlines = [HEADER_STARTSWITH + l.strip("\r\n") + "\r\n" for l in hlines]
        hstr = "".join(hlines)
    
        fp.write(hstr)

        # special case: no keys
        if not self.keys:
            return
        
        # list of list of strings for each column
        for key, col in zip(self.keys, self.cols):
            scol = []
            scol.append("\"" + key.replace("\"", "\"\"") + "\"")

            if np.issubdtype(col.dtype, np.str_): # special case for strings
                for value in col:
                    # escape double quotation and embrace with triple-double quotation
                    scol.append("\"" + value.replace("\"", "\"\"") + "\"") 
            for value in col:
                scol.append(repr(value))

            scols.append(scol)
        
        # put # at the linehead of the key column
        scols[0][0] = HEADER_STARTSWITH + scols[0][0]

        if prettify:
            for scol in scols:
                maxwidth = max([len(s) for s in scol])
                columnwidth = maxwidth
                scols_pretty.append([s + " "*(columnwidth - len(s)) for s in scol])
            scols = scols_pretty
        
        fp.write("\r\n".join([DELIMITER.join(row) for row in zip(*scols)]))

    def save(self, fp: str|IO, prettify: bool = True, add_version_info: bool = True, **kwargs: Any) -> None:
        """Saves the object content to a hicsv-formatted text file. 
        
        Args:
            fp: file-like object of the destination. 
            prettify: True to turn on pretty formatting. 
            add_version_info: If True, automatically adds the current versions
                of the module and the hicsv format specification. 
            **kwargs: Arguments of built-in ``open()``. Used only when ``fp`` is a string. 
                The ``mode`` parameter is set to "w" by default. (`New in 1.0.0.`)
        
        Example:
            >>> d = hicsv.hicsv()
            >>> d.append_column("first column", np.arange(5))
            >>> d.append_column("second column", np.linspace(0.0, 1.0, 5))
            >>> d.append_column("third column", np.array(["one", "two", "three", "four", "five"]))
            >>> d.save("spam.txt")

            Or, 

            >>> with open("spam.txt", "w") as fp:
            >>>     d.save(fp)
        """
        if isinstance(fp, str):
            _kwargs: dict = {}
            _kwargs["mode"] = "w"
            _kwargs.update(**kwargs)
            with open(fp, "w", **_kwargs) as f:
                return self._save(f, prettify, add_version_info)
        else:
            return self._save(fp, prettify, add_version_info)
    
    def __str__(self) -> str:
        return "<hicsv.hicsv object at {0}, {1} header entries, {2} keys: {3}>".format(hex(id(self)), len(self.h), len(self.keys), ", ".join(self.keys))
    
    def __repr__(self) -> str:
        with io.StringIO() as fp:
            self.save(fp, add_version_info=False)
            return fp.getvalue()



def txt2hicsv(fp: IO|str, sep: str = ",", ignore_lines: List[int] = [], key_line: int|None = None, keys: List[str] = [], **kwargs: Any) -> hicsv:
    '''Reads a generic delimited text file and converts it into a hicsv object. 

    This is a convenient function to import simple text data file into a hicsv object. 
    It is also an example of the usage of `hicsv` class. 
    
    Args:
        fp: string or file-like object of the input file. 
        sep: Delimiter character of the input file. Defaults to comma. 
        ignore_lines: List of line numbers to ignore. Defaults to empty list
        key_line: Line number of the column key. If `None`, keys will be automatically 
            named as "0", "1", "2", etc. 
        keys: List of column keys. It's useful if you know the table structure exactly. 
            This must match the number of columns in the input file. 
            When `keys` is specified, `key_line` will be ignored. 
        **kwargs: Arguments of built-in ``open()``. Used only when ``fp`` is a string. (`New in 1.0.0.`)
    '''

    lines: List[str] = []
    lines_table: List[str] = []
    rows_str: List[List[str]] = []
    _ignore_lines: List[int] = ignore_lines
    i: int = 0
    _keys: List[str] = []
    length: int = 0

    if isinstance(fp, str):
        with open(fp, **kwargs) as f:
            lines = f.readlines()
    else:
        lines = fp.readlines()

    # if keys are provided, use that. 
    if keys:
        _keys = keys
    # if not provided and the key_line is provided (as int), 
    # try to read the keys from that line
    elif isinstance(key_line, int):
        for row in csv.reader([lines[key_line], ], delimiter=sep): # just one line
            _keys = [k.strip(" ") for k in row]

        # this line should also be ignored
        _ignore_lines.append(key_line)

    # ignore the specified lines
    lines_table = [l for i, l in enumerate(lines) if i not in ignore_lines]

    # parse data lines
    for row in csv.reader(lines_table, delimiter=sep):
        if row:
            rows_str.append([e.strip() for e in row]) # spaces are omitted

    length = len(rows_str)

    cols_str = [*zip(*rows_str)]

    # if the keys are not specified and not found, 
    if len(cols_str) > 0 and not _keys:
        _keys = [str(j) for j in range(len(cols_str))] # auto generate the column keys
    elif len(cols_str) != len(_keys):
        raise ValueError("column key number does not match the actual number of columns")

    out = hicsv()

    # detect type and store arrays
    for key, col_str in zip(_keys, cols_str):
        # check if it's int
        if col_str[0].isdigit():
            out.append_column(key, np.array(col_str).astype(int))
        else:
            # if not, check if it's float
            try:
                float(col_str[0])
            except ValueError:
                # if not, then it is stored as string
                out.append_column(key, np.array(col_str))
                # if it's not an int or string, then it must be a float. 
            else:
                out.append_column(key, np.array(col_str).astype(float))
    
    return out
    
if __name__ == "__main__":
    d = hicsv()
    d.append_column("c1", np.arange(5))
    d.append_column("c2", np.random.rand(5))
    d.append_column("c3,3", np.random.rand(5))
    d.append_column("c4\"", np.array([1.0, 2.0, np.nan, 4.0, 5.0]))
    d.append_column("c5 --- \"---\"", np.array(["a\"", "\"b", "c", "d", "e, f"]))
    d.h["some header"] = "some value"
    d.h["it can be as complex as you want"] = {"foo": "bar", "one": 1}

    with open("test.txt", "w") as fp:
        d._save(fp)

    a1, a2 = d.ga("c1", "c2")

    with open("test.txt", "r") as fp:
        o = hicsv(fp)

    import csv

    with open("csvtest.txt", "w") as f:
        writer = csv.writer(f)
        writer.writerows([["A1\"", "A2"]])

    print(o.keys)

    with open("test2.txt", "w") as fp:
        o._save(fp)

    o.replace_column("c1", np.arange(5, 10))

    o.save("test3.txt")

    o.remove_column("c3,3")
    o.save("test4.txt")

    r = hicsv("SN_P03-21_C6F6_10mgmL.txt")
    r.save("rewrite.txt")