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
    def __init__(self, x=None, y=None, initval=None):
        self.rows = rows(self)

        # If we have y, we can initialize the table using y, x and initval
        if y != None:
            x = y if x == None else x
            for _ in range(y):
                r = self.newrow()
                for _ in range(x):
                    r.newfield(initval)

    def __iter__(self):
        for r in self.rows:
            yield r

    def __getitem__(self, ix):
        return self.rows[ix]

    def __call__(self, y, x):
        return self[y][x]

    def newrow(self):
        r = row()
        self.rows += r
        r.rows = self.rows
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

    @property
    def fields(self):
        # This can be cached and the cache can be invalidated by onadd,
        # onremove  and onchange events.
        fs = fields()
        for r in self:
            for f in r:
                fs += f
        return fs
        
    def count(self, o):
        
        return self.where(o).count

    def where(self, v, limit=None):
        """
        Return a fields collection where each field in the table matches v.
        """
        if type(v) == type:
            # If v is a type object, search the type index
            raise NotImplementedError()

        elif callable(v) and not isinstance(v, entity) \
                         and not isinstance(v, entities):
            
            # If v is a callable, a scan is necessary
            ls = []
            for r in self:
                for f in r:
                    if v(f.value):
                        ls.append(f)
                        if limit != None and len(ls) >= limit:
                            break 
                else:
                    continue
                break
        else:
            # If v is an arbitrary value, use the value index.
            raise NotImplementedError()

        return fields(initial=ls)

    def remove(self, values):
        # TODO Use fieldvalueindex
        for r in self:
            for f in r:
                if any(v is f.value for v in values):
                    f.value = None
    
    def slice(self, center=None, radius=None):
        if radius == None:
            raise NotImplementedError("'radius' must be provided")
        else:
            if type(radius) != int:
                raise TypeError("'radius' must be an integer")
            if center == None or type(center) != field:
                raise TypeError("'center' must be a field")

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
                r.newfield(f.value)
                f = f.right
            else:
                f = leftmost = leftmost.below
                if not f or f.row.index - center.row.index  > radius:
                    return tbl
                else:
                    r = tbl.newrow()

        return tbl

    def __str__(self, f=None):
        Reverse='\033[07m'
        Endc = '\033[0m'

        R = ''

        if self.rows.isempty:
            return R

        widths = self.columns.widths

        b = '-' * (sum(widths) + len(widths) + (len(widths) * 2) - 1)

        R += '+' + b + '+'

        for i, r in enumerate(self):
            R += '\n'
            for j, f1 in enumerate(r):
                R += '| ' if j == 0 else ''

                if f != None and f1 is f:
                    R += Reverse
                    
                R += str(f1).ljust(widths[j])

                if f != None and f1 is f:
                    R += Endc

                R += ' |'
                if j < r.fields.ubound:
                    R += ' '

            if i < self.rows.ubound:
                R += '\n|' + b + '|'

        R += '\n+' + b + '+\n'
        return R
                
class columns(entities):
    @property
    def widths(self):
        return [c.width for c in self]

class column(entity):
    def __init__(self):
        super().__init__()
        self.fields = fields()

    def __iter__(self):
        for f in self.fields:
            yield f

    @property
    def width(self):
        return max([len(str(f.value)) for f in self])
        
class rows(entities):
    def __init__(self, tbl, initial=None):
        super().__init__(initial=initial)
        self.table = tbl

class row(entity):
    def __init__(self):
        super().__init__()
        self.fields = fields(self)

    def __getitem__(self, ix):
        return self.fields[ix]

    def __setitem__(self, ix, item):
        self.fields[ix] = item

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
        ix = self.index
        if ix == 0:
            return None
        return self.rows(ix - 1)

    @property
    def below(self):
        ix = self.index
        if ix == self.rows.ubound:
            return None
        return self.rows(ix + 1)

    def newfield(self, v):
        f, fs = field(v), self.fields
        fs += f
        f.fields = fs
        return f

class fields(entities):
    def __init__(self, row=None, initial=None):
        if row:
            self.row = row
        super().__init__(initial=initial)

    @property
    def table(self):
        return self.row.table if self.row else None

    @property
    def values(self):
        return [x.value for x in self]

class field(entity):
    def __init__(self, v, initial=None):
        super().__init__()
        self._v = v

    @property
    def value(self):
        return self._v

    @value.setter
    def value(self, v):
        if v != self.value:
            self._v = v

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
        return self.fields.row.table if self.fields.row else None

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
        ix = self.index
        if ix == 0:
            return None
        return self.row.fields(ix - 1)

    @property
    def right(self):
        ix = self.index
        if ix == self.row.fields.ubound:
            return None
        return self.row.fields(ix + 1)

    @property
    def aboveleft(self):
        f = self.above
        return f.left if f else None

    @property
    def belowleft(self):
        f = self.below
        return f.left if f else None

    @property
    def aboveright(self):
        f = self.above
        return f.right if f else None

    @property
    def belowright(self):
        f = self.below
        return f.right if f else None

    def getabove(self, number, closest=False):
        return self.getneighbor('above', number, closest)

    def getbelow(self, number, closest=False):
        return self.getneighbor('below', number, closest)

    def getleft(self, number, closest=False):
        return self.getneighbor('left', number, closest)

    def getright(self, number, closest=False):
        return self.getneighbor('right', number, closest)

    def getaboveleft(self, number, closest=False):
        return self.getneighbor('aboveleft', number, closest)

    def getbelowleft(self, number, closest=False):
        return self.getneighbor('belowleft', number, closest)

    def getaboveright(self, number, closest=False):
        return self.getneighbor('aboveright', number, closest)

    def getbelowright(self, number, closest=False):
        return self.getneighbor('belowright', number, closest)

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

        if number == 0:
            return self

        f = self
        for i in range(number):
            neighbor = getattr(f, direction)
            if not neighbor:
                return f if closest else None
            f = neighbor
        return neighbor

    def __str__(self, table=False):
        if table:
            return self.table.__str__(self)
        return str(self.value)

    @property
    def pt(self):
        """ 
        Print table and highlight this field.

        This property is merely intended for debugging purposes.
        """
        print(self.__str__(table=True))
