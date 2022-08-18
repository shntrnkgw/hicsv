# hicsv-python
Python implementation of the I/O interface for the Header-Included Comma-Separated Values (hicsv) file format. 

## What is *hicsv*?
Header-included comma-separated values (*hicsv* or *hi-csv* in short)
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

## Example of *hicsv* format

```
#{
#    "some metadata entry": "some metadata",
#    "it can be anything": {
#        "that": "can be made into a JSON file",
#        "for example": "a dictionary"
#    },
#    "もちろん": "ユニコード文字もOK",
#    "hicsv-python version": "0.0.0",
#    "hicsv version": "20220812"
#}
#"first column"     ,"2nd column","column 3","四番目のカラム"
0.391006442374058   ,0           ,"string"  ,"いち"     
0.6943031206081407  ,1           ,"is"      ,"に"      
0.03433735164688634 ,2           ,"also"    ,"さん"     
0.015028457129899642,3           ,"OK"      ,"よん"     
0.5900201005940872  ,4           ,"!"       ,"ご"      
```

## Scope of this package

The ``hicsv`` package is a minimal implementation of the I/O interface 
to the *hicsv*-formatted files. 
It, therefore, does not have (or aim for) any advanced functionalities. 
Please use ``numpy`` and/or other useful packages for anything beyond I/O. 

## Example

To read a hicsv-formatted text file,
```python
import hicsv
d = hicsv.hicsv("foo.txt")
```
Or you can just create an empty object to which 
you can add columns and header info. 
```python
e = hicsv.hicsv()
```
You can get one or more columns. 
```python
c1, c2 = d.ga("column 1", "column 2")
```

The header info is stored as a dictionary. 
You can set and get information at any time::
```python
d.h["new header entry"] = "some value"
print(d.h["new header entry"])
```
If you need to create a hicsv-formatted file from scratch::
```python
out = hicsv()
```
To add a column::
```python
out.append_column("column 1", arr)
```

Here ``arr`` should be a 1-d numpy array. 
Note that all columns must be of the same length, 
so adding an array with different length will cause error. 
Then you can write into a hicsv-formatted text file like::

```python
out.save("new hicsv file.txt")
```

## Note
Some users may find the following behavior of this package unexpected. 

1. The parser deletes the spaces at the beginning and at the end of each cell. 
   This is true even if the cell content is double-quoted. 
   For example, the two cells

        "spam", "  spam  "

   results in identical strings. 
