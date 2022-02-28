# vim: set et ts=4 sw=4 fdm=marker

# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2022

""" Contains classes to model a table, i.e., a two dimensional matrix of
values.

Tables are convenient for representing things like spreadsheet
workbooks, board games such a chess, and results from a database query.
Tables can also be created and their results pretty-printed. This can be
useful for displaying two dimensional lists of data to a user.
"""

# NOTE It is currently under consideration that this class be removed
# and its functionality moved to dom.table.

from entities import *

class table(entity):
    """ Represents a table, i.e., a two dimensional matrix of
    values.
    """
    def __init__(
        self, x=None, y=None, initval=None, border=('-', '|', '+') 
    ):
        """ Create a table

        :param: x int: If specified, the table will be initialized with
        x number of columns/fields.

        :param: x int: If specified, the table will be initialized with
        y number of rows.

        :param: initval object: If specified, this value will be the
        default value for all the cells in the table.

        :param: border tuple<str>:  A tuple of three string values used
        to create the borders. The default is '-', '|', '+'. This hyphen
        is used to create the horizontal lines of a table, the pipe
        symbol is used to create the vertical lines of the table, and
        the + is used to create the corners.

            >>> import table
            >>> # Use default border
            >>> print(table.table(2, 2, 'XYZ'))
            +-----------+
            | XYZ | XYZ |
            |-----------|
            | XYZ | XYZ |
            +-----------+

        :abbr: tbl
        """

        # TODO Write test for different border values

        # Init rowes and fields collection
        self.rows = rows(tbl=self)
        self._fields = fields()

        # Subscribe to events
        self.rows.onfieldadd += self._fields_onadd
        self.rows.onfieldremove += self._fields_onremove

        # If we have y, we can initialize the table using y, x and
        # initval
        if y != None:
            x = y if x == None else x
            for _ in range(y):
                r = self.newrow()
                for _ in range(x):
                    r.newfield(initval)

        # Set border. We will use this later for pretty-printing and
        # stuff
        self.border = border

    def _fields_onadd(self, src, eargs):
        """ An event handler to capture the moment a field is added to a
        row.
        """
        f = eargs.entity
        self._fields += f

        # We are capturing the field being added to the table so use
        # this opportunity to subscribe to the field's on*valuechange
        # events
        f.onbeforevaluechange += self._field_onbeforevaluechange

        f.onaftervaluechange += self._field_onaftervaluechange

    def _fields_onremove(self, src, eargs):
        """ An event handler to capture the moment a field is removed
        from a row.
        """
        f = eargs.entity
        self._fields -= f

        # Since the field is no longer a part of the table, remove our
        # subscription to its on*valuechange event
        f.onbeforevaluechange -= self._field_onbeforevaluechange
        f.onaftervaluechange -= self._field_onaftervaluechange

    def _field_onbeforevaluechange(self, src, eargs):
        """ An event handler to capture the moment before a fields value
        is changed.
        """

        # Remove the fields value it's indexes
        for ix in self._fields.indexes:
            ix.remove(eargs.entity)

    def _field_onaftervaluechange(self, src, eargs):
        """ An event handler to capture the moment after a fields value
        has changed.
        """
        # Add the fields value it's indexes
        for ix in self._fields.indexes:
            ix.append(eargs.entity)

    def __iter__(self):
        """ When iterating over a table, we want to iterate over its
        rows collection.

        This override of __iter__ makes the following two iterations the
        same::
            tbl = table()

            for r in tbl
                ...

            for r in tbl.rows:
                ...
        """
        for r in self.rows:
            yield r

    def __getitem__(self, ix):
        """ Delegate the table's indexer to the rows indexer::
            
            tbl = table(4, 4, 'X')

            assert type(tbl[1]) is table.row
            assert tbl[1] is tbl.rows[1]
        """
        return self.rows[ix]

    def __call__(self, y, x):
        """ Allow indexing on row and column using parenthesis
        operator::

            tbl = table(4, 4, 'X')

            # Get second row in table
            r = tbl[1]

            # Get third field in row
            fld = r[2]

            # Get the same field that we got above by using the
            # parenthesis operator
            fld1 = tbl(1,2)
            assert fld is fld1
        """
        return self[y][x]

    def add(self, e):
        """ Add a collection of rows to the table.

        :param: e table.rows|sequence<row>: A collection of rows.
        """
        for r in e:
            self.rows += r

        return self

    def newrow(self):
        """ Create a new row, append it to self's row collection and
        return it.
        """

        # TODO This should be renamed `row`. 
        r = row()
        self.rows += r
        r.rows = self.rows
        return r

    @property
    def columns(self):
        """ Return a new collection of column objects for this table.
        
        Note that tables aren't really constructed of columns; they are
        constructed of rows which themselves are constructed of fields.
        This property returns a columns collection based on the
        collection of rows and fields to make certain operations easier.
        For example, this property is used by the __str__ method to see
        how many columns the table contains. 
        """
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
        """ The table's private collection of fields.

        Fields are stored in row objects. However, the table object
        keeps its own reference to these field objects when they are
        added to the rows so index searched can be performed on them.
        """
        return self._fields
        
    def count(self, o):
        """ Return the number of fields that match o. See the ``where``
        method.
        """
        return self.where(o).count

    def where(self, v, limit=None):
        """ Return a fields collection where each field in the table
        matches v.

        :param v type|callable: If v is type, return only fields where
        the object is the same type as v. If v is a callable the invoke
        the callable on each fields' value. Only return the fields where
        the invocation returns True. If the type is neither `type` or
        callable, return the fields whose value equals v.

        :param: limit int: Limit the number of fields returned by this
        number.
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
        """ Set any field's value to None if the field's value is in the
        values sequence.

        :param: values sequence: A sequence to test for nullifying the
        field values.
        """
        # TODO Use fieldvalueindex
        for r in self:
            for f in r:
                if any(v is f.value for v in values):
                    f.value = None
    
    def slice(self, center=None, radius=None):
        """ Return a new table object that contains a slice (a subset)
        of this table starting at the `center` and extending to the
        radius.

        :param: center field: The center field.

        :param: radius int: The number of fields above, below, left and
        right of the center field that should be included in nthe slice.
        """
        if radius is None:
            raise ValueError("'radius' must be provided")
        else:
            if type(radius) is not int:
                raise TypeError("'radius' must be an integer")
            if center is None or type(center) is not field:
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
        """ Returns a pretty-printed string of the table. 
        """
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
    """ Represents a collection of table columns.

    :abbr: cols
    """
    @property
    def widths(self):
        """ Return a list of each column's width in the collection.
        """
        return [c.width for c in self]

class column(entity):
    """ Represents a table column.

    Note that columns aren't used in the construction of tables; rows
    and fileds make up tables. However, column objects can be derived
    from these actual structures. Column structures are useful for
    reading data about the table sometimes instead. However, it would be
    a mistake to mutate a column and expect the change to alter the
    actual table. Columns are read-only abstractions.

    :abbr: col
    """
    def __init__(self):
        """ Create a column object.
        """
        super().__init__()
        self.fields = fields()

    def __iter__(self):
        """ To iterate over a column is to iterate over its fields.
        """
        for f in self.fields:
            yield f

    @property
    def width(self):
        """ Return the maximum width the column must expand to in order
        to accomidate all the fields' values it its fields collection.
        This is an important property for determining how to
        pretty-print the table.
        """
        return max([len(str(f.value)) for f in self])
        
class rows(entities):
    """ A collection of row objects.

    Tables can largely be thought of merely as collections of rows.
    """
    def __init__(self, initial=None, tbl=None):
        """ Create a rows collection.

        :param: initial iterable: See entities.__super__.

        :param: tbl table: A reference to the actual table object to
        which this rows collection belongs.
        """
        super().__init__(initial=initial)

        self.table = tbl

        # Events
        self.onfieldadd = event()
        self.onfieldremove = event()

    def _self_onremove(self, src, eargs):
        """ An event handler to ensure that whenever a row is removed
        from a rows collection, ensure that all field objects are
        removed first. This ensure the fields objects' onremove events
        are raised which is important for indexing, cache invalidation
        and so forth. 
        """
        eargs.entity.fields.clear()

class row(entity):
    """ Represents a row in a table.

    A table contains a collection of row objects while a row contains a
    collection of field objects.
    """
    def __init__(self):
        """ Create a row.
        """
        super().__init__()

        # Create the fields collection
        self.fields = fields(row=self)

        # Set up som event handlare
        self.fields.onadd += self._fields_onadd
        self.fields.onremove += self._fields_onremove

    def _fields_onadd(self, src, eargs):
        """ A handler that captures when a field is added to this row.
        """

        # Propogate the event to the rows collection's onfieldadd event 
        self.rows.onfieldadd(src, eargs)

    def _fields_onremove(self, src, eargs):
        # Propogate the event to the rows collection's onfieldadd event 
        self.rows.onfieldremove(src, eargs)

    def __getitem__(self, ix):
        """ Delegate the rows indexer to the fields collection indexer.
        This makes the the following lines synonymous where `r` is a row
        object::

            x = r[123]

            x = r.fields[123]
        """
        return self.fields[ix]

    def __setitem__(self, ix, item):
        """ Delegate the default setter to the fields collection default
        setter.  This makes the the following lines synonymous where `r`
        is a row object::

            r[123] = x

            r.fields[123] = x
        """
        self.fields[ix] = item

    @property
    def index(self):
        return self.rows.getindex(self)

    @property
    def table(self):
        """ Return the table object that this row is a part of.
        """
        return self.rows.table

    def __iter__(self):
        """ Make iterating over this row object the same as iterating
        over its fields collection. This makes the follwing to looping
        constructs the synonymous::

            # Where r is a row
            for f in r:
                assert isinstance(f, field)

            for f in r.fields:
                assert isinstance(f, field)
        """
        for f in self.fields:
            yield f

    @property
    def above(self):
        """ The row immediately above this row.
        """
        ix = self.index
        if ix == 0:
            return None
        return self.rows(ix - 1)

    @property
    def below(self):
        """ The row immediately below this row.
        """
        ix = self.index
        if ix == self.rows.ubound:
            return None
        return self.rows(ix + 1)

    def newfield(self, v):
        """ Create a new field with `v` as its value, append the field
        to this row's fields collection, and return the field.
        """
        f, fs = field(v), self.fields
        fs += f
        f.fields = fs
        return f

    def newfields(self, *vs):
        """ Create new fields for each value in *vs, append each field
        to this row's fields collection.
        """
        for v in vs:
            self.newfield(v)

    def __repr__(self):
        """ Return a string representation of this row object.
        """
        tbl = table()
        r = tbl.newrow()

        for f in self:
            r.newfield(f)

        return str(tbl)

class fields(entities):
    """ A collection of fields. 

    Tables are collection of rows, and each row maintains a collection
    of fields.
    """
    def __init__(self, initial=None, row=None):
        """ Create the fields collection.

        :param: initial sequence: A collection of fields or field
        values. Used to create the fields for the collection.

        :param: row row: The parent row for this fields collection.
        """
        self.index = True

        # Create index on the type of value
        self.indexes += index(
            name = 'type', keyfn = lambda f: type(f.value)
        )

        # Create index on the value
        self.indexes += index(
            name = 'value', keyfn = lambda f: f.value
        )

        if row:
            self.row = row

        # Ensure that each element in 'initial' is a field object. If
        # not, append a new field object using the element as the
        # field's value.
        if initial is not None:
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
        """ Return the root table object of this field collection.
        """
        return self.row.table if self.row else None

    @property
    def values(self):
        """ Return a list of all the values in this fields collection.
        """
        return [x.value for x in self]

class field(entity):
    """ Represents a field in a table.

    Fields are the cells of a table. Each field object has a `value`
    property that contains the value for the field. When the table is
    rendered visually, the the `value` property is stringified (run
    through str()) to produce the rendered value of the field.
    """
    def __init__(self, v):
        """ Create the field object.

        :param: v object: The value of the field. The value will be
        stringified with str() to when the table is rendered for visual
        consumption.
        """
        super().__init__()
        self._v = v

    @property
    def value(self):
        """ Return the value of the field. Note that the return type
        could be any object.
        """
        return self._v

    @value.setter
    def value(self, v):
        # TODO Using 'dummy' works here but None doesn't. This needs
        # research.
        self._setvalue('_v', v, 'dummy')

    def clone(self):
        """ Return a new field based on the self.
        """
        return field(self.value)

    @property
    def column(self):
        """ Return a column object for the field.
        """
        return column(self.index)

    @property
    def index(self):
        """ Return the zero-based ordinal position of this field within
        its fields collection.
        """
        return self.fields.getindex(self)

    @property
    def table(self):
        """ Return the root table object for this field object.
        """
        return self.fields.row.table if self.fields.row else None

    @property
    def row(self):
        """ Return the root row object for this field object.
        """
        return self.fields.row

    @property
    def above(self):
        """ Return the field immediately above this field. Return None
        if there is no field.
        """
        r = self.row.above

        if not r:
            return None

        return r.fields(self.index)

    @property
    def below(self):
        """ Return the field immediately below this field. Return None
        if there is no field.
        """
        r = self.row.below

        if not r:
            return None

        return r.fields(self.index)

    @property
    def left(self):
        """ Return the field immediately to the left of this field.
        Return None if there is no field.
        """
        ix = self.index
        if ix == 0:
            return None
        return self.row.fields(ix - 1)

    @property
    def right(self):
        """ Return the field immediately to the right of this field.
        Return None if there is no field.
        """
        ix = self.index
        if ix == self.row.fields.ubound:
            return None
        return self.row.fields(ix + 1)

    @property
    def aboveleft(self):
        """ Return the field immediately above and to the left of this
        field.  Return None if there is no field.
        """
        f = self.above
        return f.left if f else None

    @property
    def belowleft(self):
        """ Return the field immediately below and to the left of this
        field.  Return None if there is no field.
        """
        f = self.below
        return f.left if f else None

    @property
    def aboveright(self):
        """ Return the field immediately above and to the right of this
        field.  Return None if there is no field.
        """
        f = self.above
        return f.right if f else None

    @property
    def belowright(self):
        """ Return the field immediately below and to the right of this
        field.  Return None if there is no field.
        """
        f = self.below
        return f.right if f else None

    def getabove(self, number, closest=False):
        """ Get a field above this field.

        :param str direction: The direction of the neigbor: 'above',
        'below', 'left', 'right', 'aboveleft', 'aboveright',
        'belowleft', 'belowright', 'aboveright' and 'belowright'.
        
        :param int number: The number of cells to skip in the given
        direction to get to the desired neigbor

        :param bool closest: If True, return the closest field that can be
        found given the direction and number. If False, return None if a
        neigbor can't be found with those conditions.
        """
        return self.getneighbor('above', number, closest)

    def getbelow(self, number, closest=False):
        """ Get a field below this field.

        :param str direction: The direction of the neigbor: 'above',
        'below', 'left', 'right', 'aboveleft', 'aboveright',
        'belowleft', 'belowright', 'aboveright' and 'belowright'.
        
        :param int number: The number of cells to skip in the given
        direction to get to the desired neigbor

        :param bool closest: If True, return the closest field that can be
        found given the direction and number. If False, return None if a
        neigbor can't be found with those conditions.
        """
        return self.getneighbor('below', number, closest)

    def getleft(self, number, closest=False):
        """ Get a field to the left of this field.

        :param str direction: The direction of the neigbor: 'above',
        'below', 'left', 'right', 'aboveleft', 'aboveright',
        'belowleft', 'belowright', 'aboveright' and 'belowright'.
        
        :param int number: The number of cells to skip in the given
        direction to get to the desired neigbor

        :param bool closest: If True, return the closest field that can be
        found given the direction and number. If False, return None if a
        neigbor can't be found with those conditions.
        """
        return self.getneighbor('left', number, closest)

    def getright(self, number, closest=False):
        """ Get a field to the right of this field.

        :param str direction: The direction of the neigbor: 'above',
        'below', 'left', 'right', 'aboveleft', 'aboveright',
        'belowleft', 'belowright', 'aboveright' and 'belowright'.
        
        :param int number: The number of cells to skip in the given
        direction to get to the desired neigbor

        :param bool closest: If True, return the closest field that can be
        found given the direction and number. If False, return None if a
        neigbor can't be found with those conditions.
        """
        return self.getneighbor('right', number, closest)

    def getaboveleft(self, number, closest=False):
        """ Get a field diagonally, north-west of this field.

        :param int number: The number of cells to skip in the given
        direction to get to the desired neigbor

        :param bool closest: If True, return the closest field that can be
        found given the direction and number. If False, return None if a
        neigbor can't be found with those conditions.
        """
        return self.getneighbor('aboveleft', number, closest)

    def getbelowleft(self, number, closest=False):
        """ Get a field diagonally, south-west of this field.

        :param int number: The number of cells to skip in the given
        direction to get to the desired neigbor

        :param bool closest: If True, return the closest field that can be
        found given the direction and number. If False, return None if a
        neigbor can't be found with those conditions.
        """
        return self.getneighbor('belowleft', number, closest)

    def getaboveright(self, number, closest=False):
        """ Get a field diagonally, north-east of this field.

        :param int number: The number of cells to skip in the given
        direction to get to the desired neigbor

        :param bool closest: If True, return the closest field that can be
        found given the direction and number. If False, return None if a
        neigbor can't be found with those conditions.
        """
        return self.getneighbor('aboveright', number, closest)

    def getbelowright(self, number, closest=False):
        """ Get a field diagonally, north-west of this field.

        :param int number: The number of cells to skip in the given
        direction to get to the desired neigbor

        :param bool closest: If True, return the closest field that can be
        found given the direction and number. If False, return None if a
        neigbor can't be found with those conditions.
        """
        return self.getneighbor('belowright', number, closest)

    def getneighbor(self, direction, number, closest):
        """ Get a neigboring field.

        :param str direction: The direction of the neigbor: 'above',
        'below', 'left', 'right', 'aboveleft', 'aboveright',
        'belowleft', 'belowright', 'aboveright' and 'belowright'.
        
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
        """ Print table and highlight this field.

        Note that this property is merely intended for debugging
        purposes.
        """
        print(self.__str__(table=True))
