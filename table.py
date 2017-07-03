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

    def newrow(self):
        r = row()
        self.rows += r
        return r

    @property
    def columns(self):
        cs = columns()

        for r in self:
            for i, f in enumerate(r):
                c = cs(i)
                if not c:
                    c = column()
                    cs += c
                c.fields += f

        return cs
        
    def count(self, fn):
        return self.where(fn).count

    def where(self, v):
        """
        Return a fields collection where the field in the table matches v.
        """
        if type(v) == type:
            def fn(x): 
                return type(x) == v
        elif type(v) == callable:
            fn = v
        else:
            def fn(x):
                return x is v

        fs = fields()
        for r in self:
            for f in r:
                if fn(f.value):
                    fs.append(f, assignCollection=False)
        return fs

    def remove(self, values):
        for r in self:
            for f in r:
                if any(v is f.value for v in values):
                    f.value = None
    
    def slice(self, center=None, radius=None):
        if radius == None:
            raise NotImplementedError("'radius' must be provided")
        else:
            if type(radius) != int:
                raise ValueError("'radius' must be an integer")
            elif center == None or type(center) != field:
                raise ValueError("'center' must be a field")

        # Return a <table> object. If <table> has been subclassed, return the
        # subclassed version of the table.
        tbl = type(self)()

        # Get top-most, left-most field of slice
        top = center.getabove(radius, closest=True)
        leftmost = top.getleft(radius, closest=True)

        f = leftmost
        r = tbl.newrow()
        while True: 
            if f and f.index - center.index <= radius:
                r.fields += f.clone()
                f = f.right
            else:
                f = leftmost = leftmost.below
                if not f or f.row.index - center.row.index  > radius:
                    return tbl
                else:
                    r = tbl.newrow()

        return tbl

    def __str__(self):
        # Untested
        def P(s): print(s, end='')

        maxes = self.columns.maxlengths

        for i, r in enumerate(self):
            for j, f in enumerate(r):
                if j == 0:
                    P('+', )
                P(('-' * maxes[j]) + '+')

            for j, f in enumerate(r):
                if j == 0:
                    P('|')
                P(str(f).rjust(maxes[j]) + '|')
                
class columns(entities):
    
    def maxlengths(self):
        return [c.maxlength for c in self]

class column(entity):
    
    def __init__(self):
        self.fields = fields()

    def __iter__(self):
        for f in self.fields:
            yield f

    @property
    def maxlength(self):
        return max(self, lambda f: len(str(f)))
        
class rows(entities):
    def __init__(self, tbl):
        self.table = tbl

    @property
    def index(self):
        return self.table.rows.getindex(self)

    def append(self, r):
        r.rows = self
        super().append(r)
        return r 

class row(entity):
    def __init__(self):
        self.fields = fields(self)

    @property
    def index(self):
        return self.rows.getindex(self)

    @property
    def table(self):
        return self.rows.table

    def __iter__(self):
        for f in self.fields:
            yield f

    @property
    def above(self):
        return self.rows(self.index - 1)

    @property
    def below(self):
        return self.rows(self.index + 1)

class fields(entities):
    def __init__(self, row=None):
        self.row = row

    def append(self, f, assignCollection=True):
        if assignCollection:
            f.fields = self
        super().append(f)
        return f 

    @property
    def values(self):
        return [x.value for x in self]

class field(entity):
    def __init__(self, v):
        self.value = v

    def clone(self):
        return field(self.value)

    @property
    def column(self):
        return column(self.index)

    @property
    def index(self):
        return self.fields.getindex(self)

    @property
    def table(self):
        return self.fields.row.table

    @property
    def row(self):
        return self.fields.row

    @property
    def above(self):
        r = self.row.above

        if not r:
            return None

        return r.fields(self.index)

    @property
    def below(self):
        r = self.row.below

        if not r:
            return None

        return r.fields(self.index)

    @property
    def left(self):
        return self.row.fields(self.index - 1)

    @property
    def right(self):
        return self.row.fields(self.index + 1)

    def getabove(self, number, closest=False):
        return self.getneighbor('above', number, closest)

    def getbelow(self, number, closest=False):
        return self.getneighbor('below', number, closest)

    def getleft(self, number, closest=False):
        return self.getneighbor('left', number, closest)

    def getright(self, number, closest=False):
        return self.getneighbor('right', number, closest)

    def getneighbor(self, direction, number, closest):
        """
        Get a neigboring field.

        :param str direction: The direction of the neigbor
        
        :param int number: The number of cells to skip in the given
        direction to get to the desired neigbor

        :param bool closest: If True, return the closest field that can be
        found given the direction and number. If False, return None if a
        neigbor can't be found with those conditions.
        """

        f = self
        for i in range(number):
            neighbor = getattr(f, direction)
            if not neighbor:
                return f if closest else None
            f = neighbor
        return neighbor

    def getradialdistance(self, f):
        return f.row - self.row

    def __str__(self, table=False):
        if table:
            return self.table.__str__(self)
        return str(self.value)

    @property
    def pt(self):
        """ 
        Print table and highligh this field.

        This is a proprety with a very short name to make it easier for
        debugging.
        """
        print(self.__str__(table=True))
