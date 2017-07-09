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
        self.onfieldappend = event()
        self.onfieldchange = event()

        self.onfieldappend += self.self_onfieldappend
        self.onfieldchange += self.self_onfieldchange

        self.fieldvalueindex = index()
        self.fieldtypeindex = index()
        self.rows = rows(self)

        # If we have x, we can initialize the table using x, y and initval
        if x != None:
            y = x if y == None else y
            for _ in range(x):
                r = self.newrow()
                for _ in range(y):
                    r.newfield(initval)

    def self_onfieldappend(self, src, eargs):
        f = eargs.entity
        self.fieldvalueindex.append(f.value, f)
        self.fieldtypeindex.append(type(f.value), f)

    def self_onfieldchange(self, src, eargs):
        f = eargs.entity
        oldval, newval = eargs.values

        self.fieldvalueindex.remove(oldval, f)
        self.fieldvalueindex.append(newval, f)

        self.fieldtypeindex.remove(type(oldval), f)
        self.fieldtypeindex.append(type(newval), f)


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
        
    def count(self, o):
        return self.where(o).count

    def where(self, v, limit=None):
        """
        Return a fields collection where each field in the table matches v.
        """
        if type(v) == type:
            # If v is a type object, search the type index
            ls = self.fieldtypeindex(v)
        elif type(v) == callable:
            
            # If v is a callable, a scan is necessary
            for r in self:
                for f in r:
                    if fn(f.value):
                        ls.append(f)
                        if limit != None and len(ls) >= limit:
                            break 
                else:
                    continue
                break
        else:
            # If v is an arbitrary value, use the value index.
            ls = self.fieldvalueindex(v)

        # Create and return a fields collection based on ls.

        # TODO This should be done in one line:
        #    return fields(ls)
        # However, field.append's interface is incorrect and the
        # assigncollection parameter default's to True so that the row
        # property of the fields gets set to None
        fs = fields()
        for i, f in enumerate(ls):
            if limit != None and i == limit:
                break
            fs.append(f, assigncollection=False)
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

    def newfield(self, v):
        f, fs = field(v), self.fields

        # NOTE Set assigncollection to False here. As we progress, we need to
        # write the append() signatures so they conform to a standard. There
        # shouldn't be specialized parameters like assigncollection. We 
        # will handle assigning this new field's fields collection proprety
        # to row.fields in this routine.
        fs.append(f, r=None, assigncollection=False)
        f.fields = fs

class fields(entities):
    def __init__(self, o=None):
        if type(o) == row:
            self.row = o
        else:
            self.row = None
            super().__init__(o)

    def getrandomized(self):
        """ Return a randomized version of self."""
        fs = type(self)()
        ls = sample(self._ls, self.count)
        for f in ls:
            fs.append(f, assigncollection=False)
        return fs

    def append(self, o, r=None, assigncollection=True):
        # o will usually be a field object. However, it could be
        # anything supported by super().append() such as an iterable.
        if type(o) == field:
            if assigncollection:
                o.fields = self

            # If this field collection is associated with table, raise the
            # onfieldappend event on the table object.

            # TODO Ideally we should raise an onfieldappend event on the `row`
            # object where it would propagate to the `rows` objects then the
            # `table` object.
            if self.table:
                eargs = appendeventargs(o)
                self.table.onfieldappend(self, eargs)

        return super().append(o)

    @property
    def table(self):
        return self.row.table if self.row else None

    @property
    def values(self):
        return [x.value for x in self]

class field(entity):
    def __init__(self, v):
        self._v = v

    @property
    def value(self):
        return self._v

    @value.setter
    def value(self, v):
        if v != self.value:
            eargs = valuechangeeventargs(self, self.value, v)
            self.table.onfieldchange(self, eargs)
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
        return self.row.fields(self.index - 1)

    @property
    def right(self):
        return self.row.fields(self.index + 1)

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
