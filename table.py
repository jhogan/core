# vim: set et ts=4 sw=4 fdm=marker
"""
MIT License

Copyright (c) 2016 Jesse Hogan

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
from entities import *

class table(entity):
    def __init__(self):
        self.rows = rows(self)

    def __iter__(self):
        for r in self.rows:
            yield r

    def count(self, fn):
        return self.where(fn).count

    def where(self, qry):
        if type(qry) == type:
            def fn(x): return type(x) == qry
        elif type(qry) == callable:
            fn = qry
                

        fs = fields()
        for r in self:
            for f in r:
                if fn(f.value):
                    fs += f
        return fs

class rows(entities):
    def __init__(self, tbl):
        self.table = tbl

    def append(self, r):
        r.table = self.table
        super().append(r)
        return r 

class row(entity):
    def __init__(self):
        self.fields = fields(self)

    def __iter__(self):
        for f in self.fields:
            yield f

class fields(entities):
    def __init__(self, row):
        self.row = row

    def append(self, f):
        f.table = self.row
        super().append(f)
        return f 

class field(entity):
    def __init__(self, v):
        self.value = v

    def __str__(self):
        return str(self.value)
