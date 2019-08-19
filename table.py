# vim: set et ts=4 sw=4 fdm=marker

# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2019

from entities import *

class table(entity):
    def __init__(self, x=None, y=None, initval=None, border=('-', '|', '+') ):
        # TODO Write test for different border values
        self.rows = rows(tbl=self)
        self._fields = fields()

        self.rows.onfieldadd += self._fields_onadd
        self.rows.onfieldremove += self._fields_onremove

        # If we have y, we can initialize the table using y, x and initval
        if y != None:
            x = y if x == None else x
            for _ in range(y):
                r = self.newrow()
                for _ in range(x):
                    r.newfield(initval)

        self.border = border

    def _fields_onadd(self, src, eargs):
        f = eargs.entity
        self._fields += f

        # We are capturing the field being added to the table so use this
        # opportunity to subscribe to the field's on*valuechange events
        f.onbeforevaluechange += self._field_onbeforevaluechange

        f.onaftervaluechange += self._field_onaftervaluechange

    def _fields_onremove(self, src, eargs):
        f = eargs.entity
        self._fields -= f

        # Since the field is no longer a part of the table, remove our
        # subscription to its on*valuechange event
        f.onbeforevaluechange -= self._field_onbeforevaluechange
        f.onaftervaluechange -= self._field_onaftervaluechange

    def _field_onbeforevaluechange(self, src, eargs):
        for ix in self._fields.indexes:
            ix.remove(eargs.entity)

    def _field_onaftervaluechange(self, src, eargs):
        for ix in self._fields.indexes:
            ix.append(eargs.entity)

    def __iter__(self):
        for r in self.rows:
            yield r

    def __getitem__(self, ix):
        return self.rows[ix]

    def __call__(self, y, x):
        return self[y][x]

    def add(self, e):
        for r in e:
            self.rows += r

        return self

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
        return self._fields
        
    def count(self, o):
        return self.where(o).count

    def where(self, v, limit=None):
        """
        Return a fields collection where each field in the table matches v.
        """
        if type(v) == type:
            return self.fields.indexes['type'](v, limit=limit)

        elif callable(v) and not isinstance(v, entity) \
                         and not isinstance(v, entities):
            
            # If v is a callable, a scan is necessary
            ls = []
            for r in self:
                for f in r:
                    if v(f.value):
                        if limit != None and len(ls) >= limit:
                            break 
                        ls.append(f)
                else:
                    continue
                break
        else:
            # If v is an arbitrary value, use the value index.
            return self.fields.indexes['value'](v, limit=limit)

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

        if self.border:
            # horizontal (-), vertical (|), corner (+)
            h, v, c = self.border
        else:
            h = v = c = ''


        b = h * (sum(widths) + len(widths) + (len(widths) * 2) - 1)

        R += c + b + c

        if R:
            R += '\n'

        for i, r in enumerate(self):
            if i:
                R += '\n'
            for j, f1 in enumerate(r):
                R += v + ' ' if v and j == 0 else ''

                if f != None and f1 is f:
                    R += Reverse
                    
                R += str(f1).ljust(widths[j])

                if f != None and f1 is f:
                    R += Endc

                R += ' ' + v
                if j < r.fields.ubound:
                    R += ' '

            if i < self.rows.ubound:
                if h:
                    R += '\n'
                R += v + b + v

        if b:
            R += '\n' + c + b + c + '\n'
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
    def __init__(self, initial=None, tbl=None):
        super().__init__(initial=initial)
        self.table = tbl

        # Events
        self.onfieldadd = event()
        self.onfieldremove = event()

    def _self_onremove(self, src, eargs):
        """ Whenever a row is removed from a rows collection, ensure that all
        field objects are removed first. This ensure the fields objects'
        onremove events are raised which is important for indexing, cache
        invalidation and so forth. """

        eargs.entity.fields.clear()

class row(entity):
    def __init__(self):
        super().__init__()
        self.fields = fields(row=self)

        self.fields.onadd += self._fields_onadd
        self.fields.onremove += self._fields_onremove

    def _fields_onadd(self, src, eargs):
        self.rows.onfieldadd(src, eargs)

    def _fields_onremove(self, src, eargs):
        self.rows.onfieldremove(src, eargs)

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

    def newfields(self, *vs):
        for v in vs:
            self.newfield(v)

    def __repr__(self):
        tbl = table()
        r = tbl.newrow()

        for f in self:
            r.newfield(f)

        return str(tbl)

class fields(entities):
    def __init__(self, initial=None, row=None):

        # Create index on the type of value
        self.indexes += index(name='type', keyfn=lambda f: type(f.value))

        # Create index on the value
        self.indexes += index(name='value', keyfn=lambda f: f.value)

        if row:
            self.row = row

        # Ensure that each element in 'initial' is a field object. If not,
        # append a new field object using the element as the field's value.
        if initial != None:
            fs = fields()
            for v in initial:
                if isinstance(v, field):
                    fs += v
                else:
                    fs += field(v)

            initial = fs
            
        super().__init__(initial=initial)

    @property
    def table(self):
        return self.row.table if self.row else None

    @property
    def values(self):
        return [x.value for x in self]

class field(entity):
    def __init__(self, v):
        super().__init__()
        self._v = v

    @property
    def value(self):
        return self._v

    @value.setter
    def value(self, v):
        # TODO Using 'dummy' works here but None doesn't. This needs
        # research.
        self._setvalue('_v', v, 'dummy')

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
