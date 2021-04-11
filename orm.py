# vim: set et ts=4 sw=4 fdm=marker

########################################################################
# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2021
########################################################################

"Simplicity is complexity resolved." 
# Constantin Brancusi

"Most people overestimate what they can do in one year and "
"underestimate what they can do in ten years."
# Bill Gates

""" This module contains all classes related to object-relational
mapping.

TODOs:
    FIXME:6028ce62 Allow entitymappings to be set to None (see 6028ce62
    for more.)

    TODO Raise error if a subclass of ``association`` does not have a
    subclass of ``associations``. Strange bugs happen when this mistake
    is made.

    TODO Add bytes(n) as datatype. Having to type `bytes, 16, 16` is not
    fun.
    
    FIXME:1de11dc0 There is an issue with the way superentities
    collections are accessed as attributes of orm.entity object. 
    
    The issue can be seen in the differente ways `rapper` (from test.py)
    and `product.measuer` access their superentities attributes. For
    example: `rapper` is able to access the `concerts` attribute because
    `rapper`'s superentity is `singer` and `singer` has a `concerts`
    attribute. 
    
    So far so good, but in the case of `product.measure`, which has a
    constituents collection `dimensions`, we would expect to be able to
    access a `features` attribute of `product.measure` because
    `dimensions` is a subentity of `features`. However, since
    `product.measure` has no superentity, we can not arrive at the
    `feature` attribute because of the way the ORM code is written. We
    instead get an AttributeError.
    
    This may or may not be important. So far, the need to access
    superentities attributes has not come up. However, if the need arises,
    we will want to correct this.
    
    TODO I think text attributes should be None by default and this
    should not be a validation error. We can create a
    fieldmapping.istextalias to determine if the attribute field would
    be created as a longtext in the database. If so, allow None to be be
    a value. This is just a hunch at the moment. It just seems like a
    lot of fields that are of type text (field names like description,
    comment, instructions, etc.) should by default be optional.)
    
    TODO:9b700e9a When an entity reference exist, we should create an
    entities collection on the referent. For example, given:
    
        class party(orm.entity):
            pass
    
        class timesheets:
            party = party.party
    
    we should be able to access ``timesheets`` off a party instance:
    
        for ts in party(id).timesheets:
            ...
    
    TODO:abf324b4 Do we really need pseudocollections? In the ~200 classes
    so far in the GEM, none have really needed or would seem to benefit
    from pseudocollections. Let's reflect on how valuable they are going
    forward. If after the code has been in production serving web pages
    for some while, and pseudocollections have not proven themselves to be
    worthy, I think we should rip out the pseudocollection logic. This
    logic is tedious to maintain and may be slowing down execution time.
    
    TODO In the GEM, change all date and datetime attributes to past
    tense, e.g., s/acquiredat/acquired/
    
    TODO:8cc3bfdc We should have a @property of the ``orm`` called
    ``sub``.  ``sub`` would be antonymous to ``orm.super``. It should do
    the following:

        * Lazy-load and return the immediate subentity of the current
        entity::
            
            art = artist(sng.id)
            assert type(art.orm.sub) is singer

        * If called on a class, should return an AttributeError::

            try:
                artist.orm.sub
            except AttributeError:
                assert True
            else:
                assert False
        
        We could have an attribute called ``subs`` for this since an
        entity class can have zero or more subentity classes::

            subs = file.inodes.subs.sorted('__class__.__name__')
            assert subs.first is file.directory
            assert subs.second is file.file

        * The sub should be connected as much possible to the graph so
        * that ``.save()`` and ``.brokenrules`` work as expected::

            art.orm.super.orm.sub is art
            art.orm.sub.orm.super is art

    TODO:055e5c02 make FK name's fully qualified. grep 055e5c02 for
    more.

    TODO:349f4355 Support saving recursive entites with subentities.
    grep for 349f4355 for clarification.

    TODO Create orm.reload() to complement orm.reloaded(). It should
    reload the data from the db into self.

    FIXME:acad30cc Broken rules currently has an issue. grep acad30cc
    for more clarification.

    TODO datespans and timespans that refer to a timeframe for which an
    association is valid should be named 'valid':
        
        s/span = (time|date)span/valid = \1span/

    TODO There should be a standard for association class names that makes
    them predictable. Perhaps they should be alphabetical. For example,
    given an association that associates an ``effort`` and an ``item``,
    the name should be ``effort_item`` instead of ``item_effort``, since
    the former is alphabetized. This would help to locate them faster and
    to use them in code more efficiently.

    TODO Reflexive associations currently can currently be loaded only
    by the subject-side of the association. For example, if the
    'director' hr.position has direct reports (accessible through
    hr.position_position), we can discover them like this::

        assert director.position_positions.ispopulated

    However, the inverse is not true::

        direct_report = director.position_positions.first

        # This will fail; we can't discover who the manager of the
        # direct_report is.
        assert direct_report.position_positions.ispopulated

    TODO Instead of ``decimal``, we may want to create a ``currency``
    datatype. Currently, it's assumed that the values stored in decimal
    attributes are dollars, but obviously this will not always be the
    case.

    TODO:8210b80c There should be a way to get at constituents in a
    configured way:

        # Get the collection of users with the name `name` belonging to
        # the site `ws`. Iterating over ws.users may take too long
        # and consume too much RAM because a site can have thousands of
        # users.
        usrs = ws.get_users(name=name)

        # Configure the getter with a stream.
        for usr in ws.get_users(orm.allstream):
            ...
"""

from MySQLdb.constants.ER import BAD_TABLE_ERROR, TABLE_EXISTS_ERROR
from collections.abc import Iterable
from contextlib import suppress, contextmanager
from datetime import datetime, date
from dbg import B
from difflib import SequenceMatcher
from entities import classproperty
from enum import Enum, unique
from func import enumerate
from pprint import pprint
from shlex import shlex
from table import table
from types import ModuleType
from uuid import uuid4, UUID
import MySQLdb
import _mysql_exceptions
import builtins
import dateutil
import db
import decimal
import entities as entitiesmod
import func
import gc
import inflect
import inspect
import itertools
import os
import primative
import re
import sys
import textwrap

class AttributeError(builtins.AttributeError):
    def __init__(self, msg):
        self.inner = builtins.AttributeError(msg)

@unique
class types(Enum):
    """ An ``Enum`` contanining members which represent the basic data
    types supported by the ORM such as ``str``, ``int``, ``datetime`` as
    well as ``pk`` (primary key) and ``fk`` (foreign key).  
    """
    pk        =  0
    fk        =  1
    str       =  2
    int       =  3
    datetime  =  4
    bool      =  5
    float     =  6
    decimal   =  7
    bytes     =  8
    date      =  9
    timespan  =  10

class alias:
    """ An abstract class to create data type aliases. See ``text`` for
    an concrete implementation.
    """
    type = None
    min = None
    max = None

class text(alias):
    """ An alias for:

            str, 1, 65535

    Many entity objects in the GEM simply want what would be
    equivalent to a MySQL ``text`` date type. This alias allows a
    GEM author to say::

        class person(orm.entity):
            name = str
            bio = orm.text

    instead of::

        class person(orm.entity):
            name = str
            bio = str, 1, 65535

    """
    type = str
    min = 1
    max = 65535

    def __iter__(self):
        yield self.type
        yield self.min
        yield self.max

class char():
    @staticmethod
    def expand(body):
        """ A staticmethod to find chr fields in the body of a class and
        convert them to str fields. For example, the ``isbn`` field in
        the book class::

            class book(orm.entity):
                isbn = chr(1)

        will be translated into a str map with a minimum length and
        maximum length of 10. 
        
        Note that the ORM sees str maps with equal minimun and maximun
        lengths as ``char`` database datatypes, so using the ``chr``
        function above for the isbn amounts to declaring a database char
        type with a length of 10. The lower-level alternative

            class book(orm.entity):
                isbn = str, 10, 10

        does the same thing, but is less straightforward in its
        intention.
        """

        for k, v in body.items():
            if isinstance(v, str) and \
               len(v) == 1        and \
               ord(v) in range(0, 256):

                len1 = ord(v)
                body[k] = str, len1, len1

class span:
    """ An abstract class for spans of time. 
    
    Many entities in the General Entity Model (GEM) require date(time)
    fields with names like ``begin`` and ``end`` to record the time an
    entity has been in a certain state. For example::

        class user(orm.entity):
            # The date the user became active
            beginactive = date

            # The date the user became inactive
            endactive   = date

    The span classes allow us to write the above with only two lines::

        class user(orm.entity):
            active = datespan(suffix='active')

    The user class will now expose three attributes:

        u = user()
        assert type(u.beginactive) is primative date
        assert type(u.endactive) is primative date
        assert type(u.active) is datespan

    The `active` atttribute is a ``datespan`` object that exposes the
    `begin` and `end` attribute as well as doing other nice things like
    telling you whether a given date is within the datespan.

        assert type(u.active.begin) is primative date
        assert type(u.active.end) is primative date

        if '2020-02-02' in u.active:
            # 2020-02-02 must come after u.active.begin and before
            # u.active.end if we are here.
            ...

    Note that activebegin and endactive will still be date fields in the
    the table and these attributes will act just like any other date
    field on the entity.

    The above used the ``datespan`` subclass. A ``timespan`` subclass is
    similar but uses a datetime datatype instead of a date datatype to
    include the time.
    """
    
    def __init__(self, prefix=None, suffix=None, e=None):
        """ Instantiate a (date|time)span.

        :param: prefix str: The prefix of the span attribute.

        :param: suffix str: The suffix of the span attribute.

        :param: suffix orm.entity: The entity corresponding to span.
        entity.__getattribute__ will pass this into the `.clone` method
        to make it aware of its entity. This is important for the
        `.begin` and `.end` methods.
        """
        self.entity = e
        self._prefix = prefix
        self._suffix = suffix

    @property
    def isstatic(self):
        """``span``'s are static if they have no entity. The entity would
        be provide by the clone method when an instance is available to
        associate with the ``span``.
        """
        return not bool(self.entity)

    @classmethod
    def expand(cls, body):
        """ A class method to scan the ``body`` ``dict`` for spans. If
        found, `begin`, `end` and a `span` object are added to the
        ``body`` ``dict``.  

        :param: body dict The dict used by the ``entity``'s metaclass
        (entitymeta.__new__).
        """
        mods = list()
        for k, v in body.items():
            if hasattr(v, 'mro'):
                if timespan in v.mro():
                    v = timespan()
                elif datespan in v.mro():
                    v = datespan()

            if isinstance(v, cls):
                mods.append((k, v))

        for k, v in mods:
            if builtins.type(v) is timespan:
                type = types.datetime
            elif builtins.type(v) is datespan:
                type = types.date
            else:
                raise TypeError('Invalid span type')

            begin = v.str_begin
            end   = v.str_end

            for fld in (begin, end):
                if fld in body:
                    raise ValueError(
                        'Span wants to create existing field "%s"' % fld
                    )

            body[begin] = fieldmapping(type, span=v)
            body[end]   = fieldmapping(type, span=v)
            body[k]     = v

    def clone(self, e):
        """ Clone the ``span`` with an entity (``e``).

        :param: e orm.entity: The entity instance that this span belongs
        to.
        """
        return type(self)(
            prefix=self.prefix, 
            suffix=self.suffix, 
            e=e
        )

    @property
    def suffix(self):
        return self._suffix

    @property
    def str_begin(self):
        """ Returns the name of the *begin* method. By default this will
        be 'begin', however the prefix and suffix will change this if
        they exist.
        """
        begin = 'begin'
        if self.prefix:
            begin = self.prefix + begin

        if self.suffix:
            begin += self.suffix

        return begin
        # TODO Make this private by adding an underscore. Same with
        # str_end.

    @property
    def str_end(self):
        """ Returns the name of the *end* method. By default this will
        be 'end', however the prefix and suffix will change this if
        they exist.
        """
        end = 'end'
        if self.prefix:
            end = self.prefix + end

        if self.suffix:
            end += self.suffix

        return end 

    @property
    def prefix(self):
        return self._prefix

    @property
    def begin(self):
        """ Return the date/datetime value for 'begin'.
        """
        return getattr(self.entity, self.str_begin)

    @begin.setter
    def begin(self, v):
        setattr(self.entity, self.str_begin, v)

    @property
    def end(self):
        """ Return the date/datetime value for 'end'.
        """
        return getattr(self.entity, self.str_end)

    @end.setter
    def end(self, v):
        setattr(self.entity, self.str_end, v)

    def __contains__(self, dt):
        """ Answers the qustion: is ``dt`` within this timespan. If
        true, return True; False otherwise.

        :param: dt datetime: The datetime in question.
        """
        if type(self) is timespan:
            dt = primative.datetime(dt)
        elif type(self) is datespan:
            dt = primative.date(dt)
        else:
            raise TypeError('Invalid span')

        return (self.begin is None or dt >= self.begin) and \
               (self.end   is None or dt <= self.end)

    def iscurrent(self):
        """ Returns True if the current time, in UTC, is within this
        timespan.
        """
        return primative.utcnow in self

    def __repr__(self):
        name = type(self).__name__
        begin, end = self.str_begin, self.str_end
        return '%s(begin=%s, end=%s)' % (name, begin, end)

class datespan(span):
    """ A time span where that begins with a date datatype and ends with
    a date datatype. See the super class ``span`` for more.
    """

class timespan(span):
    """ A time span where that begins with a datetime datatype and ends
    with a datetime datatype. See the super class ``span`` for more.
    """

class undef:
    """ 
    A class which indicates a value has not been set.:

        x = orm.undef

        if x is orm.undef:
            x = None

    Indicating a variable or property is undef is useful for situations
    where ``None`` has a specific meaning. For example, an instance of
    `fieldmapping` may have a ``value`` property equal to None which
    would mean its corresponding field in the database is (or will be)
    ``null``. However, there are still times when its ``value`` property
    will need to be set to ``undef`` such as to indicate that it has not
    yet been set by the code - cases which ``None`` is typically used
    for.
    """
    pass

class stream(entitiesmod.entity):
    """ ``stream`` objects are used to configure ``entities``. Passing a
    ``stream`` object to an ``entities`` ``__init__`` method instructs
    the `entities` object to function in streaming/chunking mode. 

    Streaming entities behaves like non-streaming entities for the most
    part.  Property invocation and iteration behave the same::

        # Create a streaming entity for all male artists
        arts = artists(orm.stream, gender='male')

        # Executiton of SQL statements begins here - on iteration. 
        # ``arts``'s __iter__ will fetch only 100 records at a time from
        # the database to prevent memory over-consumption.
        for art in arts:
            ...

        Calling properties and methods have the same, seemless
        behavior::

        arts = artists(orm.stream, gender='male')
        
        # Get the count of male artists form the database
        cnt = arts.count

    The number of records that are fetched at a time default to 100. To
    change this, we can pass in a ``chunksize`` value::

            stm = orm.stream(chunksize=10)
            arts = artists(stm, gender='male')

            # Only 10 artist rows will be pulled from the database at a
            # time.
            for art inn arts::
                ...

    """

    def __init__(self, chunksize=100):
        """ Sets the chunksize of the stream object.

        :param: int chunksize: The number of records to load (or chunk)
        at a time.
        """
        self.cursor = self.cursor(self)
        self.chunksize = chunksize
        self.orderby = ''

    class chunk:
        """ A simple class used to pass to an entites collection to
        indicate it is a chunk.
        """

    class cursor(entitiesmod.entity):
        def __init__(self, stm, start=0, stop=0):
            self.stream = stm
            self._chunk = None
            self._start = start
            self._stop = stop

        def __repr__(self):
            r = type(self).__name__ + ': '
            for prop in 'start', 'stop', 'limit', 'size', 'offset':
                r += '%s=%s ' % (prop, str(getattr(self, prop)))
            return r
        
        @property
        def chunk(self):
            """ Return an orm.entities collection that represents a
            chunk of the stream.
            """

            # Memoize
            if self._chunk is None:
                
                # Get the where object from the streaming entities
                # collection so we can pass it to the chunked entities
                # collection.
                wh = self.entities.orm.where
                if wh: # :=
                    args1 = [str(wh.predicate), wh.args]
                else:
                    args1 = list()

                # Make the entities collection aware that it is a chunk
                args1.append(stream.chunk)

                # Instantiate the chunked entities collection passing in
                # the streaming entities collection's predicate and
                # arguments.
                self._chunk = type(self.entities)(*args1)

            return self._chunk

        @property
        def entities(self):
            return self.stream.entities

        def __contains__(self, slc):
            slc = self.normalizedslice(slc)
            return self.start <= slc.start and \
                   self.stop  >= slc.stop

        def advance(self, slc):
            """ Advance the cursor in accordance with the ``slice``
            argument's ``start`` and ``stop`` properties. If the slice
            calls for data not currently loaded in the ``chunk``
            collecion, the ``chunk`` is cleared and loaded with new data
            from the database.

            :param: slice slc: The ``start`` and ``stop`` properties of
            the slice indicate which rows in the stream to which the
            cursor should be advanced.
            """

            # Convert int to a slice
            if isinstance(slc, int):
                slc = slice(slc, slc + 1)

            if slc.start is None:
                slc = slice(int(), slc.stop)

            if slc.stop is None:
                slc = slice(slc.stop, int())

            # Return an empty collection if start >= stop
            if slc.start >= slc.stop:
                if slc.stop < 0:
                    # TODO es[3:3] or es[3:2] will produce empty results
                    # like lists do. However, es[3:-1] should produces a
                    # non-empty result (also like lists). However, this
                    # case is currently unimplemented.
                    msg = 'Negative stops not implemented'
                    raise NotImplementedError(msg)
                return self.chunk[0:0]

            # Does the chunk need to be reloaded to get the data
            # requested by the slice?
            if slc not in self or not self.chunk.orm.isloaded:
                self._start = slc.start
                self._stop = slc.stop

                self.chunk.orm.reload(
                    self.stream.orderby, self.limit, self.offset
                )

                self.chunk.orm.isloaded = True

            return self.chunk[self.getrelativeslice(slc)]

        def __iter__(self):
            # TODO To make this object a proper iterable, shouldn't we
            # override the __next__()?
            slc= slice(0, self.stream.chunksize)
            self.advance(slc)
            yield self.chunk

            while True:
                size = self.stream.chunksize
                slc = slice(slc.start + size, slc.stop + size)

                if slc.start >= self.entities.count:
                    raise StopIteration()

                gc.collect()
                yield self.advance(slc)

        def getrelativeslice(self, slc):
            slc = self.normalizedslice(slc)
            
            start = slc.start - self.offset
            stop  = slc.stop  - self.offset
            return slice(start, stop)

        def normalizedslice(self, slc):
            # Normalize negatives
            cnt = self.stream.entities.count   

            if slc.start < 0:
                slc = slice(slc.start + cnt, slc.stop)

            if slc.stop <= 0:
                slc = slice(slc.start, slc.stop + cnt)

            return slc
            
        @property
        def start(self):
            # I.e., offset
            start = self._start

            # Deal with negatives
            if start < 0:
                start += self.stream.entities.count

            return start

        @property
        def stop(self):
            if self._stop < 0:
                self._stop += self.stream.entities.count

            if self.stream.chunksize < self._stop - self.start:
                self._stop = self._stop
            else:
                self._stop = self.start + self.stream.chunksize

            return self._stop

        @property
        def size(self):
            # I.e., 'limit'
            return self.stop - self.start 

        @property
        def limit(self):
            return self.size

        @property
        def offset(self):
            return self.start

class joins(entitiesmod.entities):
    """ A collection of ``join`` classes. Join classes are used by
    ``entities`` to construct INNER and OUTER joins.
    """
    def __init__(self, initial=None, es=None):
        # NOTE In order to conform to the
        # entitiesmod.entities.__init__'s signature, we have to make
        # es=None by default. However, we actually don't want es to have
        # a default, so we simulate the behavior here.
        if es is None:
            raise TypeError(
                "__init__() missing 1 required keyword argument: 'es'"
            )

        self.entities = es
        super().__init__(initial=initial)

    # TODO:1d1e17dc s/table/tablename
    @property
    def table(self):
        """
        Return the table name for this ``joins`` collection

        :rtype: str
        :returns: The name of the table for this ``joins`` collection.
        """
        return self.entities.orm.table

    @property
    def abbreviation(self):
        """ Returns the entities' abbreviation 
        """
        return self.entities.orm.abbreviation

    @property
    def wheres(self):
        return wheres(initial=[x.where for x in self if x.where])

    def __contains__(self, key):
        if entities in key.mro():
            for j in self:
                if type(j.entities) is key:
                    return True
            else:
                return False

        return super().__contains__(key)

class join(entitiesmod.entity):
    """ Represents an SQL JOIN clause. 
    
    An entities collection class can have zero or more join objects in
    its ``joins`` collection. These are used to generate the JOIN
    portion of its SELECT statement (``entities.orm.sql``).
    """
    
    # Constants for the types of a join. Currently, only INNER JOINS are
    # supported.
    Inner = 0
    Outer = 1

    def __init__(self, es, type):
        """ Sets the initial properties of the join. 

        :param: entities es: The :class:`entities` that this join
        corresponds to.

        :param: int type: The type of join (e.g., INNER, OUTER, etc.)
        """

        if es.orm.isstreaming:
            raise InvalidStream(
                'Entities cannot be joined to streaming entities'
            )
            
        self.entities = es
        self.type = type # inner, outer, etc.

    @property
    def table(self):
        """ Returns the table name for the join. This is the same as the
        table name for the entities' table.
        """
        return self.entities.orm.table

    @property
    def keywords(self):
        """ Get the SQL keyword for the join type. 
        """

        if self.type == join.Inner:
            return 'INNER JOIN'
        elif self.type == join.Outer:
            return 'LEFT OUTER JOIN'
        else:
            raise ValueError('Invalid join type')

    def __repr__(self):
        """ Returns a representation of the ``join`` object useful for
        debugging.
        """
        name = type(self.entities).__name__
        typ = ['INNER', 'OUTER'][self.type == self.Outer]
        return 'join(%s, %s)' % (name, typ)

class wheres(entitiesmod.entities):
    """ A collection of ``where`` objects """

class where(entitiesmod.entity):
    """ Represents a WHERE clause of an SQL statement. """

    def __init__(self, es, pred, args):
        """ Sets the initial propreties for the ``where`` object. 
        
        :param:  entities  es: The ``entities`` collection associated
        with this ``where`` object.

        :param:  str or predicate pred: A str or ``predicate`` object
        associated with this ``where`` object

        :param:  list      args:        A list of arguments associated
        with this ``where`` object.
        """

        self.entities     =  es
        self.predicate    =  None

        if not pred:
            raise ValueError('where objects must have predicates')

        if isinstance(pred, predicate):
            self.predicate = pred
        elif isinstance(pred, str):
            pred = orm.introduce(pred, args)
            self.predicate = predicate(pred, wh=self)
        else:
            raise TypeError()

        self.args = args

    def clone(self):
        """ Create a clone of the ``where`` object.
        """
        wh = type(self)(
            self.entities, 
            self.predicate.clone(),
            self.args.copy()
        )

        wh.predicate.where = wh

        return wh

    def demandvalid(self):
        def demand(col, exists=False, ft=False):
            for map in self.entities.orm.mappings.all:
                if not isinstance(map, fieldmapping):
                    continue

                if map.name == col:
                    if ft and type(map.index) is not fulltext:
                        msg = 'MATCH column "%s" must be have a fulltext index'
                        msg %= col
                        raise InvalidColumn(msg)
                    break
            else:
                e = self.entities.orm.entity.__name__
                msg = 'Field "%s" does not exist in entity "%s": "%s"'
                msg %= (col, e, str(pred))
                raise InvalidColumn(msg)

        for pred in self.predicate:
            if pred.match:
                for col in pred.match.columns:
                    demand(col, exists=True, ft=True)
                continue

            for op in pred.operands:
                if predicate.iscolumn(op):
                    demand(op, exists=True)

    def __repr__(self):
        return '%s\n%s' % (self.predicate, self.args)
    
class predicates(entitiesmod.entities):
    pass

class predicate(entitiesmod.entity):
    Isalphanum_ = re.compile(r'^[A-Za-z0-9_]+$')
    Specialops = '=', '==', '<', '<=', '>', '>=', '<>'
    Wordops = 'LIKE', 'NOT', 'NOT LIKE', 'IS', 'IS NOT', 'IN', 'NOT IN', \
              'BETWEEN', 'NOT BETWEEN'
    Constants = 'TRUE', 'FALSE', 'NULL'
    Ops = Specialops + Wordops
    Introducers = '_binary',
    
    def __init__(self, expr, junctionop=None, wh=None):
        self._operator      =  ''
        self.operands       =  list()
        self.match          =  None
        self._junction      =  None
        self._junctionop    =  junctionop
        self.startparen     =  0
        self.endparen       =  0
        self.lhsintroducer  =  ''
        self.rhsintroducer  =  ''
        self.where          =  wh

        if expr:
            if isinstance(expr, shlex):
                lex = expr
            elif expr is not None:
                lex = shlex(expr, posix=False, punctuation_chars='!=<>')

            self._parse(lex)
        else:
            # When cloning, we want to pass in a None expr
            pass

    def clone(self):
        pred = predicate(None, self.junctionop, wh=self.where)

        if self.operands is None:
            pred.operands = None
        else:
            pred.operands       =  self.operands.copy()

        pred.operator       =  self.operator
        pred.startparen     =  self.startparen
        pred.endparen       =  self.endparen
        pred.lhsintroducer  =  self.lhsintroducer
        pred.rhsintroducer  =  self.rhsintroducer

        if self.junction:
            pred.junction = self.junction.clone()

        if self.match:
            pred.match = self.match.clone()

        return pred

    def __iter__(self):
        yield self
        if self.match and self.match.junction:
            for pred in self.match.junction:
                yield pred 

        if self.junction:
            for pred in self.junction:
                yield pred

        raise StopIteration

    @property
    def junction(self):
        return self._junction

    @junction.setter
    def junction(self, v):
        self._junction = v

    @property
    def junctionop(self):
        if self._junctionop:
            return self._junctionop.strip().upper()
        return None

    @property
    def columns(self):
        return [op for op in self.operands if self.iscolumn(op)]

    @staticmethod
    def _raiseSyntaxError(lex, tok, ex=None, msg=''):
        if not ex:
            ex = predicate.SyntaxError

        cur = lex.instream.tell()
        str = lex.instream.getvalue()
        strlen = len(str)
        start = max(0, cur - 10)
        stop = min(strlen, cur + 10)
        snippet = str[start: stop]

        raise ex(cur, snippet, tok, msg=msg)
    
    def _demandBalancedParens(self):
        if self.junctionop:
            return

        startparen = endparen = 0
        for pred in self:
            startparen += pred.startparen
            endparen += pred.endparen

        if endparen != startparen:
            raise predicate.ParentheticalImbalance(startparen, endparen)

    def _parse(self, lex):
        tok = lex.get_token()
        inbetween      =  False
        isin           =  False
        inquote        =  False
        inplaceholder  =  False
        intro          =  str()
        unexpected = predicate.UnexpectedToken

        while tok != lex.eof:
            TOK = tok.upper()

            if tok == '%':
                inplaceholder = True

            elif inplaceholder:
                if tok == 's':
                    placeholder = intro + ' %s' if intro else '%s'
                    self.operands.append(placeholder)
                    intro = str()
                else:
                    msg = 'Unexpected placeholder type. ' + \
                          'Consider using %s instead'
                    self._raiseSyntaxError(lex, tok, ex=unexpected, msg=msg)
                inplaceholder = False
            
            elif tok in self.Introducers:
                if isin:
                    intro = tok
                else:
                    if len(self.operands):
                        self.rhsintroducer = tok
                    else:
                        self.lhsintroducer = tok

            elif self.iscolumn(tok):
                self.operands.append(tok)

            elif TOK == 'MATCH':
                self.operands = None
                self.operator = None
                self.match = predicate.Match(lex, self.where)

            elif self.iswordoperator(tok):
                self.operator += ' ' + tok
                if TOK == 'BETWEEN':
                    inbetween = True
                elif TOK == 'IN':
                    isin = True

            elif self._lookslikeoperator(lex, tok):
                if self.operator:
                    self._raiseSyntaxError(lex, tok, ex=unexpected)
                    
                if not len(self.operands):
                    self._raiseSyntaxError(lex, tok, ex=unexpected)

                if not self.isoperator(tok):
                    raise predicate.InvalidOperator(tok)

                self.operator = tok

            elif self.isliteral(tok):
                tok = TOK if TOK in self.Constants else tok
                if inquote:
                    if tok[0] == "'":
                        self.operands[-1] += tok
                else:
                    inquote = True # Maybe
                    self.operands.append(tok)

            elif TOK in ('AND', 'OR'):
                if not self.match and not len(self.operands):
                    self._raiseSyntaxError(lex, tok, ex=unexpected)

                if not (inbetween and TOK == 'AND'):
                    self.junction = predicate(lex, tok, wh=self.where)
                    self._demandBalancedParens()
                    return

            elif tok == '(':
                if not isin:
                    self.startparen += 1

            elif tok == ')':
                if not isin:
                    self.endparen += 1

            if inbetween and len(self.operands) == 3:
                inbetween = False

            tok = lex.get_token()

            if tok != lex.eof and tok[-1] != "'":
                inquote = False

        if not self.match:
            if self.operator in ('BETWEEN', 'NOT BETWEEN'):
                if len(self.operands) != 3:
                    msg = 'Expected 2 operands, not %s' % len(self.operands)
                    msg += '\nThere may be unquoted string literals'
                    self._raiseSyntaxError(lex, tok, ex=unexpected, msg=msg)
            else:
                if self.operator in ('IN', 'NOT IN'):
                    if len(self.operands) < 2:
                        msg = 'Expected at least 2 operands, not %s'
                        msg %= len(self.operands)
                        msg += '\nThere may be unquoted string literals'
                        self._raiseSyntaxError(lex, tok, ex=unexpected, msg=msg)
                elif len(self.operands) != 2:
                    msg = 'Expected 2 operands, not %s' % len(self.operands)
                    msg += '\nThere may be unquoted string literals'

                    self._raiseSyntaxError(lex, tok, ex=unexpected, msg=msg)

            if self.operator not in predicate.Ops:
                raise predicate.InvalidOperator(self.operator)

        self._demandBalancedParens()
                
    @property
    def operator(self):
        if self._operator is None:
            return None
        return self._operator.strip().upper()

    @operator.setter
    def operator(self, v):
        self._operator = v

    def __str__(self):
        r = str()

        r += ' %s ' % self.junctionop if self.junctionop else ''

        r += '(' * self.startparen

        if self.match:
            r += str(self.match)
        else:
            ops = self.operands

            # Append a space to the introducers if they exists
            lhsintro = self.lhsintroducer
            lhsintro = lhsintro + ' ' if lhsintro else ''
            rhsintro = self.rhsintroducer
            rhsintro = rhsintro + ' ' if rhsintro else ''

            if self.operator in ('IN', 'NOT IN'):
                r += '%s %s (%s)' % (ops[0],
                                     self.operator,
                                     ', '.join(ops[1:]))

            elif self.operator in ('BETWEEN', 'NOT BETWEEN'):
                r += '%s %s %s AND %s'
                r %= (ops[0], self.operator, *ops[1:])

            else:
                r += '%s%s %s %s%s' % (lhsintro,
                                       ops[0], 
                                       self.operator, 
                                       rhsintro,
                                       ops[1])

        r += ')' * self.endparen

        junc = self.junction
        if junc:
            r += str(junc)

        return r

    def __repr__(self):
        return "predicate('%s')" % str(self)

    @staticmethod
    def iscolumn(tok):
        TOK = tok.upper()
        return     not predicate.isoperator(tok) \
               and not predicate.isliteral(tok) \
               and tok[0].isalpha()           \
               and re.match(predicate.Isalphanum_, tok) \
               and TOK not in ('AND', 'OR', 'MATCH')

    @staticmethod
    def _lookslikeoperator(lex, tok):
        for c in tok:
            if c not in lex.punctuation_chars:
                return False
        return True

    @staticmethod
    def isoperator(tok):
        return tok.upper() in predicate.Ops + predicate.Wordops

    @staticmethod
    def iswordoperator(tok):
        return tok.upper() in predicate.Wordops

    @staticmethod
    def isliteral(tok):
        fl = ''.join((tok[0], tok[-1]))

        # If quoted
        if fl in ('""', "''"):
            return True

        # If numeric
        if tok.isnumeric():
            return True

        return tok.upper() in predicate.Constants

    @staticmethod
    def isplaceholder(tok):
        """ Returns True if `tok` is a placeholders. Examples of
        placeholders are '%s' and '_binary %s'.

        :param: str tok: The token to test.
        """
        for intro in predicate.Introducers:
            if tok == f'{intro} %s':
                return True

        return tok == '%s'

    class Match():
        re_isnatural = re.compile(
            r'^\s*in\s+natural\s+language\s+mode\s*$', \
              flags=re.IGNORECASE
        )

        re_isboolean = re.compile(
            r'^\s*in\s+boolean\s+mode\s*$',\
             flags=re.IGNORECASE
        )
        re_isquoted = re.compile(
            r"^'.*'$"
        )

        def __init__(self, lex=None, wh=None):
            self._lex            =  lex
            self.columns         =  list()
            self.searchstring    =  str()
            self._mode           =  str()
            self.junction        =  None
            self.where           =  wh
            self.searchstringisplaceholder = False
            if lex:
                self._parse(lex)

        def clone(self):
            m = type(self)()
            m.columns       =  self.columns.copy()
            m.searchstring  =  self.searchstring
            m._mode         =  self._mode

            m.searchstringisplaceholder \
                =  self.searchstringisplaceholder

            if self.junction:
                m.junction = self.junction.clone()

            return m

        def _parse(self, lex):
            tok = lex.get_token()
            incolumns  =  False
            insearch   =  False
            inagainst  =  False
            inmode     =  False

            while tok != lex.eof:
                TOK = tok.upper()
                if incolumns:
                    if predicate.iscolumn(tok):
                        self.columns.append(tok)

                elif insearch:
                    if tok == ')':
                        if not self.searchstring:
                            ex=predicate.UnexpectedToken
                            msg = 'Missing search string'
                            predicate._raiseSyntaxError(
                                lex, tok, ex=ex, msg=msg
                            )

                        isplaceholder = self.searchstring == '%s'
                        self.searchstringisplaceholder = isplaceholder
                        isquoted = bool(self.re_isquoted.match(self.searchstring))

                        if not isplaceholder and not isquoted:
                            ex=predicate.SyntaxError
                            msg = 'Search string "%s" is not quoted'
                            msg %= self.searchstring

                            predicate._raiseSyntaxError(
                                lex, tok, ex=ex, msg=msg
                            )

                        if not isplaceholder:
                            self.searchstring = self.searchstring[1:-1]
                        insearch = False
                    else:
                        self.searchstring += tok

                elif inmode:
                    if TOK in ('IN', 'NATURAL', 'BOOLEAN', 'LANGUAGE', 'MODE'):
                        self._mode += ' ' + TOK

                    elif TOK in ('AND', 'OR'):
                        self.junction = predicate(lex, tok, wh=self.where)

                    elif tok == ')':
                        lex.push_token(tok)
                        return

                    else:
                        ex=predicate.UnexpectedToken
                        msg = 'Check spelling of search modifiers '
                        predicate._raiseSyntaxError(lex, tok, ex=ex, msg=msg)

                if tok == '(':
                    if len(self.columns) and not inagainst:
                        ex=predicate.UnexpectedToken
                        msg = 'Are you missing the AGAINST keyword'
                        predicate._raiseSyntaxError(lex, tok, ex=ex, msg=msg)

                    incolumns = not len(self.columns)
                    insearch = inagainst

                elif tok == ')':
                    if incolumns and not len(self.columns):
                        ex=predicate.UnexpectedToken
                        msg = 'Missing columns list'
                        predicate._raiseSyntaxError(lex, tok, ex=ex, msg=msg)

                    incolumns = False
                    if inagainst:
                        inmode = True
                    else:
                        inagainst = False

                elif TOK == 'AGAINST':
                    inagainst = True

                tok = lex.get_token()

            try:
                self.mode
            except:
                ex=predicate.UnexpectedToken
                msg = 'Invalid search modifiers'
                predicate._raiseSyntaxError(lex, tok, ex=ex, msg=msg)
                

        @property
        def mode(self):
            mode = self._mode.strip()

            if not mode:
                return 'natural'

            if self.re_isnatural.match(mode):
                return 'natural'

            if self.re_isboolean.match(mode):
                return 'boolean'

            raise ValueError('Incorrect mode: ' + mode)

        def __repr__(self):
            return "Match('%s')" % str(self)

        def __str__(self):
            cols = self.columns.copy()
                
            r = "MATCH (%s) AGAINST ("  % ', '.join(cols)

            if self.searchstringisplaceholder:
                r += '%s'
            else:
                if self.searchstring == '%s':
                    r += '%s'
                else:
                    r += "'%s'" % self.searchstring

            if self.mode == 'natural':
                r += ' IN NATURAL LANGUAGE MODE'

            elif self.mode == 'boolean':
                r += ' IN BOOLEAN MODE'

            r += ')'

            if self.junction:
                r += str(self.junction)

            return r

    class SyntaxError(ValueError):
        def __init__(self, col=None, ctx=None, tok=None, msg=None):
            self.column = col
            self.context = ctx
            self.token = tok
            self.message = msg

        def __str__(self):
            args = (self.column, self.context)

            if self.column:
                msg = "Syntax error at column %s near '%s'" % args
            elif self.context:
                msg = "Syntax error %s near '%s'" % self.context
                
            if self.message:
                msg += '. ' + self.message

            return msg

    class ParentheticalImbalance(SyntaxError):
        def __init__(self, startparen, endparen):
            self.startparen = startparen
            self.endparen = endparen

        def __str__(self):
            msg = 'Parenthetical imbalance. '
            return msg

    class InvalidOperator(SyntaxError):
        def __init__(self, op):
            self.operator = op

        def __str__(self):
            return 'Invalid operator: ' + self.operator

    class UnexpectedToken(SyntaxError):
        def __str__(self):
            msg = ''
            if self.token:
                msg += 'Unexpected token: "%s"' % self.token

            msg = super().__str__() + '. ' + msg
            return msg

# TODO We may want to rename this to ``all``. ``all`` has the advantange
# of being a single word and, at the time of this writing, is not used.
class allstream(stream):
    """ A subtype of ``stream`` used to retrieve all rows in a
    table.
        
        # Iterate through all the artist entities
        for art in artists(orm.allstream)
            ...

    Note that it is usually preferable to use the @classproperty
    ``all`` instead::
        
        for art in artists.orm.all:
            ...
    """

    # TODO The orm.entities constructor does not test if the stream
    # object passed in is an an ``allstream``. It should probably demand
    # that no additoinal (querying) arguments be passed in if there is
    # an ``allstream`` and, that if querying arguments are passed in,
    # the stream must not be an ``allstream`` since that would be a
    # contridiction.
        
class eager:
    """ Instances of this class are passed to orm.entities.__init__ to
    specify constituents to eager-load.

    Normally, constituents are lazy-loaded::
        
        # SELECT * FROM ARTISTS WHERE NAME = {name}
        arts = artists(name=name)

        # SELECT * FROM PRESENTATIONS WHERE ARTISTID = {ARTID}
        press = arts.first.presentations

    In the above example, two SQL statements are sent to the database.
    The ``eager`` class would allow only one statement to be sent::

        # SELECT * 
        # FROM ARTISTS A
        #     INNER JOIN PRESENTATIONS P /* Eager-load */
        #         ON A.ID = P.ARTISTID
        # WHERE NAME = {name}
        arts = artists(name=name, eager('presentations'))

        # No SQL is sent to load presentations; they've been
        # eager-lodaed.
        press = arts.presentations

    Multiple constituents can be eager-loaded by passing them as
    additional arguments to the ``eager`` class::

        arts = artists(name=name, eager('presentations', 'locations'))

    Nested constituents are denoted by '.' between entity names::

        arts = artists(
            name=name, eager(
                'presentations.locations', 
                'presentations.components'
            )
        )

        # No SQL is issued for the following
        locs = arts.presentations.first.locations
        components = arts.presentations.first.components
    """

    def __init__(self, *graphs):
        """ Initialize the eager object. The *graphs containes the
        graphs to be loaded.

        :param: *graphs tuple: A collection of strings representing
        which parts of the graph to load::

                ('presentations', 'presentations.components')
        """
        self._graphs = graphs

    def join(self, to):
        """ Create a ``join`` object heirarchy from ``self`` on ``to``
        where ``to`` is an ``orm.entities`` collection (invoked from
        ``orm.entities.__init__``). Since eager-loading is accomplished
        via INNER JOINs, this method is used to establish those JOINs.

        :param: to orm.entities: The collection object to create the
        INNER JOINs on.
        """
        graphs = []

        for graph in self._graphs:
            graphs.append(graph.split('.'))

        for graph in graphs:
            parent = to
            for node in graph:

                for j in parent.orm.joins:
                    if type(j.entities).__name__ == node:
                        e = j.entities
                        break
                else:
                    e = parent.orm.mappings[node].entities()
                    parent.innerjoin(e)

                parent = e
    
    def __repr__(self):
        """ Return a representation of the ``eager`` declaration.
        """
        r = '%s(%s)'
        graphs = ', '.join(["'%s'" % x for x in self._graphs])
        r %= (type(self).__name__, graphs)
        return r

    def __str__(self):
        """ Return a representation of the ``eager`` declaration.
        """
        return ', '.join(self._graphs)

class entitiesmeta(type):
    """ An metaclass for the ``orm.entities`` class.

    This class plays a minor role for the ORM, but does permit a few
    features for the ORM user. 
    """
    def __and__(self, other):
        """ Creates a new instance of ``self`` and joins ``other`` to
        it::

            arts = artists & presentations
            assert isinstance(arts, artists)

        The SELECT for ``arts`` (arts.orm.sql) will be something like::
            
            SELECT *
            FROM artists a
                INNER JOIN presentations p
                    ON a.id = p.artistsid
        """
        self = self()
        self.join(other)

        return self

    @property
    def count(cls):
        """ Returns the number of rows in a table given a class name::

            cnt = artists.count

        This is equivalent to::
            
            SELECT COUNT(*) FROM ARTISTS;

        Note: A different mechanism is used for instances, i.e.,
        `arts.count`.
        """
        return cls.orm.all.count

    @property
    def last(cls):
        """ Return the last entity created in the database::

            # Get the last hit entity added to the database
            lasthit = ecommerce.hits.last
        """
        es = cls.orm.all.sorted('createdat')
        if es.count:
            return es.last
        return None

class entities(entitiesmod.entities, metaclass=entitiesmeta):
    re_alphanum_ = re.compile('^[a-z_][0-9a-z_]+$', flags=re.IGNORECASE)

    def __init__(self, initial=None, _p2=None, *args, **kwargs):
        """ Creates a entities collection. Passing in no arguments
        results in an empty collection. Passing in arguments results in
        the construction of a query. The query will not be executed
        here, but will rather be issued at a later time when it is
        needed - such as upon the invocation of one of the entities'
        properties or methods, or upon interation on the entities
        instance.

        Basic Queries
        -------------

        Given that you have an ``artists`` entities collection, and an
        ``artist`` entity has a first name property, you can query the
        artist entity on its firstname attribute as follows:

            arts = artists('firstname = %s', 'Jeff')

        The above is equivalent to the SQL::
            
            SELECT * FROM ARTIST WHERE FIRSTNAME = 'Jeff';

        The following constructions are equivalent to the above::

            arts = artists('firstname', 'Jeff')

            arts = artists(firstname='Jeff')

            arts = artists('firstname = %s', ('Jeff',))

        The above queries are parameterized, i.e., the SQL and the
        values are seperated to protected against SQL injection. It's
        possible to use unparameterized queries, but the following will
        result in a ValueError::

            arts = artists("firstname = 'Jeff'")

        The ORM forces you to add an empty tuple so you know you are
        using an unsafe, unparameterized query::

            arts = artists("firstname = 'Jeff'", ())

        These may be appropriate where the programmer wants to hard-code
        a value instead of using a varible whose value may have been set
        by a user.

        Full-text Queries
        -----------------
        Given that the ``artist`` entity is declared to have a full-text
        index, one can query against it using the following syntax::

            # Search for artist bio's with the word 'Cubism' in it.
            arts = artists('match(bio) against (%s)', 'Cubism')

        Eager-loading
        -------------
        Constituents are lazy-loaded by default. Passing in an object of
        type ``eager`` will cause the constituents to be eager-loaded.

            arts = artists(orm.eager('presentations'))

            # Load artists and presentations here
            cnt = arts1.count

        This causes the presentations collections to be loaded along
        with the artists collection in one call to the database.

            # No database call here
            press = arts1.first.presentations

        See more comments at the ``eager`` class.

        Streaming
        ---------
        When there are a lot of records to iterate through, you may pass
        a ``stream`` class or instance to the entities collection. This
        is useful for protecting the memory from excessive and
        unnecessary consumption. 

        Let's say there are about a million artists with the first name
        of Jeff. The following command will only pull in about a
        thousand at a time.

            arts = artists(orm.stream, firstname='Jeff')

            # Pull a chunck from the database as needed
            for art in arts:
                print(art.firstame, art.lastname)

        See more comments at the ``streaming`` class.

        Defered execution
        -----------------
        Queries are only issued when needed. The following line will
        result in no query being sent to the database::

            arts = artists(firstname='Jeff')

        As soon as we call an attribute, or iterate over the collection,
        the query is sent::

            # The query be sent when we begin to iterate
            for art in arts:
                ...

            # If we start with a property or method invocation then
            # this will be what sends the query.
            cnt = arts.count

        """
        
        # TODO _p2 should default to `undef`. Currently, a query like:
        #
        #     ents = artists('name', None)
        #
        # should mean WHERE NAME IS NULL, but is interpreted as;
        #
        #     ents = artists('name')
        #
        # which is meaningless.
        try:
            if not hasattr(type(self), 'orm'):
                raise NotImplementedError(
                    '"orm" attribute not found for "%s". '
                    'Check that the entity inherits from the '
                    'correct base class.' % type(self).__name__
                )
            try:
                self.orm = self.orm.clone()
            except builtins.AttributeError:
                msg = (
                    "Can't instantiate abstract orm.entities. "
                    "Use entities.entities for a generic entities "
                    "collection class."
                )
                raise NotImplementedError(msg)

            self.orm.instance = self

            self.orm.initing = True # change to isiniting

            self.orm.isloaded   =  False
            self.orm.isloading  =  False
            self.orm.stream     =  None
            self.orm.where      =  None
            self.orm.ischunk    =  False
            self.orm.joins      =  joins(es=self)
            self.join           =  self._join

            self.onbeforereconnect  =  entitiesmod.event()
            self.onafterreconnect   =  entitiesmod.event()
            self.onafterload        =  entitiesmod.event()

            self.onafterload       +=  self._self_onafterload

            # If a stream or eager is found in the first or second
            # argument, move it to args
            args = list(args)
            if  isinstance(initial, (stream, eager)):
                args.append(initial)
                initial = None
            elif type(initial) is type and stream in initial.mro():
                args.append(initial())
                initial = None
            elif _p2 is stream or isinstance(_p2, (stream, eager)):
                args.append(_p2)
                _p2 = None

            # Look in *args for stream class or a stream object. If
            # found, ensure the element is an instantiated stream and
            # set it to self._stream.  Delete the stream from *args.

            # TODO We should probably interate over this in reverse so
            # the `del`etions are reliable, Although, at the moment, I
            # don't think this is a problem because, for example, you
            # wouldn't pass `stream` and `chunk` at the same time.

            for i, e in enumerate(args):
                if e is stream:
                    self.orm.stream = stream()
                    self.orm.stream.entities = self
                    del args[i]
                elif isinstance(e, stream):
                    self.orm.stream = e
                    self.orm.stream.entities = self
                    del args[i]
                elif isinstance(e, eager):
                    e.join(to=self)
                    del args[i]
                elif e is stream.chunk:
                    self.orm.ischunk = True
                    del args[i]

            # The parameters express a conditional (predicate) if the
            # first is a str, or the args and kwargs are not empty.
            # Otherwise, the first parameter, `initial`, means an
            # initial set of values that the collections should be set
            # to.  The other parameters will be empty in that case.
            iscond = type(initial) is str
            iscond = iscond or (
                initial is None and (_p2 or bool(args) or bool(kwargs))
            )

            if self.orm.stream or iscond:
                super().__init__()

                # `initial` would be None when doing kwarg based
                # queries, i.e.: entities(col = 'value')
                _p1 = '' if initial is None else initial

                self._preparepredicate(_p1, _p2, *args, **kwargs)

                # Create joins to superentities and subentities where
                # necessary if not in streaming mode. (Streaming does
                # not support (and can't support) joins). Note that we
                # only want to create joins if the user has given us a
                # conditional. Unconditional entities objects imply
                # nothing needs to be loaded from the database, so don't
                # add joins.
                if not self.orm.isstreaming:
                    # Create joins between `self` and the superentity
                    # that the predicate requires be joined based on
                    # predicate columns being used. 
                    self.orm.joinsupers()

                    # Create OUTER JOINs so the SELECT statement can
                    # collect subentity data. This allows orm.populate
                    # to capture the most specialized version of the
                    # entity objects we are fetching.
                    self.orm.joinsubs()

                return

            super().__init__(initial=initial)

        finally:
            if hasattr(type(self), 'orm'):
                if hasattr(self, 'orm'):
                    self.orm.initing = False

    def clone(self, to=None):
        """ Clone the entities collection.

        If the ``to`` parameter is provided, the properties of this
        entities collection will be cloned to ``to`` and nothing will
        be returned. Note that, at the moment, to must be provide.

        :param es orm.entities: The entities collection into which this
        entites collection's properties will be "cloned".
        """
        if not to:
            raise NotImplementedError()

        to.where         =  self.where
        to.orm.stream    =  self.orm.stream
        to.orm.isloaded  =  self.orm.isloaded

    def _self_onafterload(self, src, eargs):
        """ The event handler that is invoked after the entities
        collection is loaded from the database. It records the database
        interaction of the load to the db.chronicler singleton.  The
        onafterload event is raised in orm.collect(). 
        """

        # Get a reference to the chronicler single ton
        chron = db.chronicler.getinstance()

        # Add a chonicle instance to the chronicler as a way of
        # recording, in memory, the database interaction (i.e., the SQL
        # and operation type, that occured.
        chron += db.chronicle(eargs.entity, eargs.op, eargs.sql, eargs.args)

    def innerjoin(self, *args):
        """ Creates an INNER JOIN for each entities collection in
        *args. This is a thin wrapper around orm.join. More information
        on joins can be found in that method's docstring.

        :param: *args tuple(<orm.entities>): A tuple of class references
        or object instances that inherit from orm.entities.
        """
        for es in args:
            self.join(es, join.Inner)

    def outerjoin(self, *args, **kwargs):
        """ Creates an OUTER JOIN for each entities collection in
        *args. This is a thin wrapper around orm.join. More information
        on joins can be found in that method's docstring.

        :param: *args tuple(<orm.entities>): A tuple of class references
        or object instances that inherit from orm.entities.
        """
        for es in args:
            self.join(es, join.Outer, **kwargs)

    @classmethod
    def join(cls, es, type=None):
        """ This method declares ``es`` to be joined to an instance of
        ``cls``. Later, when/if a ``SELECT`` statement is rendered, this
        declaration will be used to construct the ``JOIN`` clause.

        (
            Note that this is a @classmethod. This ``join`` method is
            replaced with the `entities._join` method on object
            construction. This is accomplished with the line::
                
                self.join = self._join

            in entities.__init__. This is done so a user can use a class
            reference or an object reference depending on the need.
            Joins using class references are convenient when no WHERE
            clause needs to be provided.
        )

        Any instance of an ``orm.entities`` collection object may have
        zero or more references to other ``orm.entities`` collection
        objects stored in its ``joins`` property. These can be chained
        together. Together, with the ``where`` property of the
        ``orm.entities`` collection objects, complex SELECT statements
        can be expessed using the ORM's API. For example::

            arts = artists('weight BETWEEN 0 AND 1', ()).join(
                        artifacts('weight BETWEEN 10 AND 11, ())
                    )

        will result in a SELECT statement similar to:

            SELECT *
            FROM artists
            INNER JOIN artist_artifacts AS aa
                ON art.id = aa.artistid
            INNER JOIN artifacts AS fact
                ON aa.artifactid = fact.id
            WHERE (art.weight BETWEEN %s AND %s)
            AND (fact.weight BETWEEN %s AND %s)

        Note that the ORM is able to infere the need for the
        ``artist_artifacts`` association table to be joined. Also note
        that the operands have been replaced with placeholder (%s)
        indicating they have been parameterized.

        :param: cls type: A reference to a class that inherits
        from ``orm.entities``. ``es`` will be joined to this object.

        :param: es type/entities: A class or object reference that
        inherits from `orm.entities`. This object will be joined to
        ``cls``.

        :param: type: The type of join (INNER/OUTER). Currently, only
        INNER JOINs are implemented. The default is INNER JOINs.
        """
        es1 = cls()
        es1._join(es, type)
        return es1
        
    def _join(self, es=None, type=None, inferassociation=True):
        # NOTE that this method is the instance method that will replace
        # the `entities.join` @classmethod when an `entities` object is
        # instantiated. Also NOTE that this method contains the logic
        # that will be called by ``entities.join`` when it is called as
        # a @classmethod. See the documentation for ``entities.join``
        # for more.
        type1, type = type, builtins.type

        # Streaming entities can't contain joins
        if self.orm.isstreaming:
            raise InvalidStream(
                'Streaming entities cannot contain joins'
            )

        if type(es) is entitiesmeta:
            es = es()
        elif type(es) is entitymeta:
            es = es.orm.entities()

        # Chain self's entitiesmappings and associationsmappings
        maps = itertools.chain(
            self.orm.mappings.entitiesmappings, 
            self.orm.mappings.associationsmappings
        )

        # Iterate over self's entitymappings and associationsmappings
        for map in maps:
            if map.entities is type(es):
                # If the joinee (es) is an entitiesmapping or
                # associationsmappings of self, then we can add es as a
                # standard join.
                break
        else:
            # When entity.orm.joinsupers() wants to join a super with
            # the subentity, we want to be able to skip the association
            # inference step. Not only is this more effecient, it will
            # also prevent bugs arising from ambiguity. 
            #
            # Consider that .joinsupers() wants to join `rapper` to
            # `singer`.  Normally, we would look for the association
            # collection `artist_artist` so we could get the
            # many-to-many relationship implied by the expression::
            #
            #     rpr.singers
            #
            # However, .joinsupers() wants a direct, one-to-one join
            # between `rapper` and `singer`. Therefore, it will set
            # inferassociation to False to prevent this.
            if inferassociation:
                # If es was not in the above `maps` collection, check if
                # it is mapped to `self` through an `assocation`. This
                # is for join operations where the `associations`
                # collection is implied, i.e.:
                #
                #     artist().join(artifacts())
                # 
                # instead of the more explicit form:
                #
                #     artist().join(artist_artifacts().join(artifacts()))

                sup = self.orm.entity
                while sup:
                    # For each of self's associations mappings and the
                    # associations mappings of it's superentities
                    for map in sup.orm.mappings.associationsmappings:

                        # If the association is reflexive, we are only
                        # interested in it if `es` is, or inherits from
                        # the objective entity of the association.
                        if map.associations.orm.isreflexive:
                            obj = map.associations.orm \
                                  .mappings['object'] \
                                  .entity

                            if not isinstance(es, obj.orm.entities):
                                continue
                        else:
                            if type(self) is type(es):
                                continue

                            # If the association is not reflexive, we
                            # don't care about the associations of the
                            # supers. Ascending the inheritance is only
                            # useful when we want to have implicit
                            # reflexive joins with subentity objects:
                            #
                            #   singers.join(singers)
                            #
                            # Without this check, joining subentity
                            # objects to their superentity results in
                            # problems. See ref: 7adeeffe.
                            if self.orm.entity is not sup:
                                continue

                        # For each entity mapping in this
                        # associationsmapping
                        maps = map.associations.orm \
                                   .mappings.entitymappings

                        for map1 in maps:

                            # If the associationsmapping's entity is the
                            # same class as the joinee (es)
                            sups = es.orm.entity.orm.superentities
                            if map1.entity.orm.entities is type(es) \
                                or map1.entity in sups:

                                # Create a new instance of the map's
                                # associations collection, add it to
                                # self's joins collection, and add es to
                                # ass's joins collection.
                                self &= map.associations & es

                                # We can return now because the implicit
                                # assocation has been joined to self,
                                # and es has been joined to the
                                # association.
                                return self
                        else:
                            msg = "%s isn't a direct constituent of %s"
                            msg %= (str(type(es)), str(type(self)))
                            raise ValueError(msg)
                    sup = sup.orm.super
            
        type = join.Inner if type1 is None else type1
        self.orm.joins += join(es=es, type=type)
        return self

    def __and__(self, other):
        """ Creates a new instance of ``self`` and joins ``other`` to
        it::

            arts = artists() & presentations

        The SELECT for ``arts`` (arts.orm.sql) will be something like::
            
            SELECT *
            FROM artists a
                INNER JOIN presentations p
                    ON a.id = p.artistsid

        ...

        Note that the above can work with a class reference instead of
        an instance::

            arts = artists & presentations
            assert isinstance(arts, artists)

        The above works by virtue of entitiesmeta.__and__, however.

        :param: other orm.entities: A references or object instances
        that inherit from orm.entities.
        """
        self.innerjoin(other)
        return self

    def __iand__(self, other):
        """ Allows the ORM user to use the &= to join entities classes::

        Instead if explicity calling .innerjoin()::

            arts.join(artifacts)

        You can use this more concise form::
            
            arts &= artifacts

        :param: other orm.entities: A references or object instances
        that inherit from orm.entities.
        """
        self.innerjoin(other)
        return self
    
    @classproperty
    def count(cls):
        # If type(cls) is type then count is being called directly off the
        # class::
        #
        #   artists.count
        #
        # In this case, we get the all stream and use its count property
        # because the request is interpreted as "give me the number of rows
        # in the artists table.
        #
        # If type(cls) is not type, it is being called of an instance::
        #   artists().count
        # 
        # cls is actually a reference to the instance (artists())
        # In this case, we just want the number of entities in the given
        # collection.
        if type(cls) is type:
            return cls.all.count
        else:
            # TODO Subscribe to executioner's on*connect events
            self = cls
            if self.orm.isstreaming:
                sql = 'SELECT COUNT(*) FROM ' + self.orm.table
                if self.orm.where:
                    sql += '\nWHERE ' + str(self.orm.where.predicate)

                ress = None
                def exec(cur):
                    nonlocal ress
                    args = self.orm.where.args if self.orm.where else ()
                        
                    cur.execute(sql, args)
                    ress = db.dbresultset(cur)

                db.executioner(exec).execute()

                return ress.first[0]
            else:
                return super().count

    def __iter__(self):
        if self.orm.isstreaming:
            for es in self.orm.stream.cursor:
                for e in es:
                    yield e
        else:
            for e in super().__iter__():
                yield e

    def __getitem__(self, key):
        if self.orm.isstreaming:
            # TODO Add indexing using a UUID. See alternative block for
            # how this is done on non-streaming entities collections.
            cur = self.orm.stream.cursor
            es = cur.advance(key)
            if isinstance(key, int):
                if es.hasone:
                    return es.first
                raise IndexError('Entities index out of range')
            return es
                
        else:
            if type(key) is UUID:
                for e in self:
                    if e.id == key:
                        return e
                else:
                    raise IndexError('Entity id not found: ' + key.hex)
            elif isinstance(key, entity):
                return self[key.id]

            elif isinstance(key, str):
                if 'name' in self.orm.mappings:
                    for e in self:
                        if e.name == key:
                            return e
                    else:
                        raise IndexError(
                            f'{self.orm.entity} '
                            f"not found with name: '{key}'"
                        )
                        
            e = super().__getitem__(key)

            # NOTE The below code original tested wheher or not
            # hasattr(e, '__init__'). However, since this invoked
            # e.__getattribute__, it was causeing unnecessary work. So
            # for performance sake, it was tweaked to not do that. `e`
            # should only be e or a list. However, this may not always
            # be the case, so a modification here will be necessary if
            # another type received.
            if isinstance(e, entity):
                return e
            elif type(e) is list:
                # TODO I don't think we ever get here any more so remove
                # this block and its conditional.
                B()
                return type(self)(initial=e)
            elif isinstance(e, entities):
                return e
            else:
                raise ValueError()
    
    def __getattribute__(self, attr):
        """ Returns the value of an attribute of this entities
        collection.

        In additon to returning the attribute's value, this is also the
        method that contains the logic for deferred loading::

            # Instatiate the entities collection, but don't load from
            # database.
            ents = myentities(name = 'my-name')

            # Calling an attribute, such as 'count', will cause the
            # SELECT query defined above to be sent to the database
            # allowing ents to load itself (via orm.collect()). The
            # SQL will look something like this::
            #
            #     SELECT * FROM myentities where name = 'my-name';
            #
            # After the data has been collected into `ents`, the 'count'
            # property will this be called and can return the number of
            # myentity objects in `ents`.
            ents.count

        As a side note, defered loading also works with iteration.
        """

        # Just return the orm instance of the entities collection if
        # attr is 'orm'.
        if attr == 'orm':
            return object.__getattribute__(self, attr)

        if attr == 'brokenrules':
            return entities.getbrokenrules(self)

        # Raise exception if we are streaming and one of these nono
        # attributes is called.
        if self.orm.isstreaming:
            nonos = (
                'getrandom',    'getrandomized',  'where',    'clear',
                'remove',       'shift',          'pop',      'reversed',
                'reverse',      'insert',         'push',     'has',
                'unshift',      'append',         '__sub__',  'getcount',
                '__setitem__',  'getindex',       'delete'
            )

            if attr in nonos:
                msg = "'%s's' attribute '%s' is not available "
                msg += 'while streaming'
                raise builtins.AttributeError(msg % (self.__class__.__name__, attr))
        else:
            # Determine if we should `load` the entities collection.
            load = True

            if self.orm.composite:
                if self.orm.composite.orm.isnew:
                    load = False

            # Don't load if joining, clearing, or attr == 'load'
            attrs = ('clear', 'outerjoin', 'innerjoin', 'join', 'load')
            load &= attr not in attrs

            # Don't load if attr = '__class__'. This is typically an
            # attempt to test the instance type using isinstance().
            load &= attr != '__class__'

            # Don't load if the entities collection is __init__'ing
            load &= not self.orm.initing

            # Don't load if the entities collection is currently being
            # loading
            load &= not self.orm.isloading

            # Don't load if self has already been loaded
            load &= not self.orm.isloaded

            # Don't load if an entity object is being removed from an
            # entities collection
            load &= not self.orm.isremoving

            # Don't load unless self has joins or self has a where
            # clause/predicate
            load &= self.orm.joins.ispopulated or bool(self.orm.where)

            if load:
                # Load the collection based on the parameters defined by
                # the invocation of the entities's __init__ method.
                self.orm.collect()


        r = object.__getattribute__(self, attr)
        if attr == 'brokenrules':
            r += self.pluck('brokenrules')

        return r

    def sort(self, key=None, reverse=None):
        """ Sort the entities collection internally by ``key``. If no
        key is given, we default to the entity object's id::

            # Create a collection
            gs = product.goods()

            # Add two entity objects to the collection
            for _ in range(2)
                gs += product.good()

            # The id's are currently not sorted
            assert gs.pluck('id') == [
                UUID('fe17eb3a-05b3-44bf-ac56-6fa46c4e7921'), 
                UUID('a068887b-ed8a-4d51-b874-864e8d1a459d'),
            ]

            # Internally sort the collection by id in ascending order
            gs.sort()

            # The entities collection is now sorted
            assert gs.pluck('id') == [
                UUID('a068887b-ed8a-4d51-b874-864e8d1a459d'),
                UUID('fe17eb3a-05b3-44bf-ac56-6fa46c4e7921'), 
            ]

        The ``reverse`` flag sorts the entities in descending order. If
        not given, the sort order will be ascending.

        Note that sorting works the same (as far as the ORM's user
        interface is concerned) whether or not we are streaming.

                # Streaming
                arts = artists(orm.stream, lastname=lastname)
                arts.sort()

                # Not streaming
                arts = artists(lastname=lastname)
                arts.sort()

        Underneath the service, an SQL ORDER BY clause will be used if
        in streaming mode, otherwise, Python's stardard sorting
        facilities will be used. This is why defered loading is
        necessary. The above lines set the parameters for the query.  It
        isn't until a regular attribute is called that the query is sent
        to the database.

            # Send SELECT statement here to load arts.
            print(arts.count)
        """

        # Default key to 'id' if not given.
        key = 'id' if key is None else key

        if self.orm.isstreaming:
            # If streaming, the key will be an ORDER BY clause. The
            # `reverse` parameter will become the SQL DESC keyword if
            # True or ASC if False.
            key = f'`{self.orm.abbreviation}.{key}`'
            key = '%s %s' % (key, 'DESC' if reverse else 'ASC')
            self.orm.stream.orderby = key
        else: 
            # If not streaming...

            # Ensure `reverse` is a bool
            reverse = False if reverse is None else reverse

            # Use the entites.entities in-memory sort algorithm.
            super().sort(key, reverse)

    def sorted(self, key=None, reverse=None):
        """ Works identically to ``entities.sort``, but instead of
        internally sorting the collection, a sorted clone of the
        collection is returned. The original collection is left
        unaltered::

            # Create a collection
            gs = product.goods()

            # Add two entity objects to the collection
            for _ in range(2)
                gs += product.good()

            # The id's are currently not sorted
            assert gs.pluck('id') == [
                UUID('fe17eb3a-05b3-44bf-ac56-6fa46c4e7921'), 
                UUID('d068887b-ed8a-4d51-b874-864e8d1a459d'),
            ]

            # Return a sorted version of the collection.
            gs1 = gs.sorted()

            # This entities collection is now sorted, but the original
            # is unaltered.
            assert gs.pluck('id') == [
                UUID('fe17eb3a-05b3-44bf-ac56-6fa46c4e7921'), 
                UUID('a068887b-ed8a-4d51-b874-864e8d1a459d'),
            ]

            assert gs1.pluck('id') == [
                UUID('a068887b-ed8a-4d51-b874-864e8d1a459d'),
                UUID('fe17eb3a-05b3-44bf-ac56-6fa46c4e7921'), 
            ]
        """
        
        key = 'id' if key is None else key
        if self.orm.isstreaming:
            key = f'`{self.orm.abbreviation}.{key}`'

            # TODO:4a7eb575 Sorting a stream does not work when the
            # `key` being sorted on is in an inherited (super) class.
            # For example, to sort files by name, we would like to do
            # this:
            #
            #    file.file.orm.all.sorted('name'):
            #
            # However, the `name` property belongs to `file`'s
            # superentity `inode`, and is in the `file_inodes` table,
            # but the ORDER BY is applied to the `file_files` table,
            # resulting in a MySQL error.
            key = '%s %s' % (key, 'DESC' if reverse else 'ASC')
            self.orm.stream.orderby = key
            return self
        else:
            reverse = False if reverse is None else reverse
            r =  super().sorted(key, reverse)
            self.clone(r)
            return r

    def save(self, *es):
        """ Persist each entity in this collection to the database in an
        atomic commit. The orm.entity and orm.entities objects in the
        *es tuple will also be persisted in the atomic transaction.  See
        the docstring at ``entity.save`` for more information on how
        entity objects are persisted.

        :param: *es tuple(<orm.entity>|<orm.entities>): A tuple of
        orm.entity and/or orm.entities objects that the users wish to
        be persisted within the atomic transaction. This is rarely
        needed but sometimes comes in handy.

            # Create an empty items collection
            itms = product.items()

            # Add 2 items to it
            for i in range(2):
                itms += product.item()

            # Both items will be created (INSERTed)
            itms.save()
        """
        exec = db.executioner(self._save)
        exec.execute(es)

    def _save(self, cur, es=None):
        """ Delegates the persistence operations to the entity objects
        themselves.
        """
        for e in self:
            e._save(cur)

        for e in self.orm.trash:
            e._save(cur)

        if es:
            for e in es:
                e._save(cur)

    def delete(self):
        """ Issue a DELETE statement to the database for each entity in
        the collection.
        """
        for e in self:
            e.delete()
        
    def give(self, es):
        """ Give the elements in `es` to this collection.
        """
        sts = self.orm.persistencestates
        super().give(es)

        # super().give(es) will mark the entities for deletion
        # (ismarkedfordeletion) since it removes entities from collections.
        # However, giving an entity to another collection is a matter of
        # updating its foreign key/composite. So restore the original
        # persistencestates of the entities then make sure they are all still
        # dirty (isdirty). This will keep them from being deleted unless that
        # had previously been explitly marked for deletion.

        es.orm.persistencestates = sts
        for e in es:
            e.orm.isdirty = True

    def append(self, obj, uniq=False, r=None):
        """ Append the `orm.entity` `obj` to this entities collection.
        This is analogous to a Python lists `append` method. Typically,
        the += operator is used to achieve the append:

            myents = myentities()
            assert myents.count == 0
            myents.append(myentitiy())

            # Note that the above is cononically written as:
            # myents += myentitiy()

            assert myents.count == 1

        :param: orm.entity obj: The entity being appended. If obj is an
        orm.entities collection, each entity in that collection will be
        appended one-at-a-time.

        :param: bool uniq: Do not append if `obj` is already in the
        collection.

        :param: orm.entities r: The collection of entities that were
        successfully appended.
        """

        # TODO Rename `obj` to `e` in this method and the base method.
        if r is None:
            r = self.orm.entities()

        if isinstance(obj, entities):
            for e in obj:
                self.append(e, r=r)
            return

        for clscomp in self.orm.composites:
            try:
                objcomp = getattr(self, clscomp.__name__)

            except Exception as ex:
                # The self collection won't always have a reference to
                # its composite.  For example: when the collection is
                # being lazy-loaded.  The lazy-loading, however, will
                # ensure the obj being appended will get this reference.
                continue
            else:
                # Assign the composite reference of this collection to
                # the obj being appended, i.e.:
                #    obj.composite = self.composite
                setattr(obj, clscomp.__name__, objcomp)

        super().append(obj, uniq, r)
        return r

    def _preparepredicate(self, _p1='', _p2=None, *args, **kwargs):
        p1, p2 = _p1, _p2

        if p2 is None and p1 != '':
            msg = '''
                Missing arguments collection.  Be sure to add arguments
                in the *args portion of the constructor.  If no args are
                needed for the query, just pass an empty tuple to
                indicate that none are needed.  Note that this is an
                opportunity to evaluate whether or not you are opening
                up an SQL injection attact vector.
            '''
            raise ValueError(textwrap.dedent(msg).lstrip())

        args = list(args)
        for k, v in kwargs.items():
            if p1: 
                p1 += ' and '
            p1 += '%s = %%s' % k
            args.append(v)

        p2isscaler = p2isiter = False

        if p2 is not None:
            if type(p2) is not str and hasattr(p2, '__iter__'):
                p2isiter = True
            else:
                p2isscaler = True

        if p2 is not None:
            if p2isscaler:
                if self.re_alphanum_.match(p1):
                    # If p1 looks like a simple column name (alphanums,
                    # underscores, no operators) assume the user is
                    # doing a simple equailty test (p1 == p2)
                    p1 += ' = %s'
                args = [p2] + args
            else: # tuple, list, etc
                args = list(p2) + args

        args = [x.bytes if type(x) is UUID else x for x in args]

        # If there is an security().proprietor and the entities collection is
        # not a chunk, then add a proprietor filter.
        #
        # There is no need to append a proprietor filter to a chunked
        # entities collection. The streamed entities collection will
        # pass in its own proprietor filter.
        if security().proprietor and not self.orm.ischunk:
            if p1:
                p1 += ' AND '

            for map in self.orm.mappings.foreignkeymappings:
                if map.fkname == 'proprietor':
                    p1 += f'{map.name} = _binary %s'
                    args.append(security().proprietor.id.bytes)
                    break

        if p1:
            self.orm.where = where(self, p1, args)
            self.orm.where.demandvalid()
            self.orm.where.args = self.orm.parameterizepredicate(args)

    def clear(self):
        """ Remove all elements from the entities collection.
        """
        try:
            # Set isremoving to True so entities.__getattribute__
            # doesn't attempt to load whenever the removing logic calls
            # an attibute on the entities collection.
            self.orm.isremoving = True
            super().clear()
        finally:
            self.orm.isremoving = False

    def remove(self, *args, **kwargs):
        """ Remove ``e`` from collection. 
        
        By default, removing ``e`` will mark e for deletion
        (ismarkedfordeletion). When the entities collection is saved (or
        when ``e`` itself is saved), the entity will be removed from the
        database. Setting the ``trash`` parameter to False will prevent
        the entity from being removed from the database, but ``e`` will
        still be removed from the collection.

        :param: e orm.entity: The entity to be removed from the
        collection.

        :param: trash bool: Determines whether or not to mark the entity
        for deletion from the database. The defalut is True.
        """
        try:
            try:
                # Do we want to mark for deletion from the database
                self.orm.dotrash = kwargs['trash']
            except KeyError:
                # The trash argument was not given, self.orm.dotrash
                # will remain True, i.e., we want to mark for deletion.
                pass
            else:
                # Clear the kwarg['trash']; super().remove isn't
                # expecting it.
                del kwargs['trash']

            # Set isremoving to True so entities.__getattribute__
            # doesn't attempt to load whenever the removing logic calls
            # an attibute on the entities collection.
            self.orm.isremoving = True
            super().remove(*args, **kwargs)
        finally:
            self.orm.isremoving = False

            # After we are done, ensure that dotrash is returned to True
            # incase it was falsified above. This ensures that by
            # default, we marke the entity for deletion when we remove()
            # it.
            self.orm.dotrash = True

    @property
    def brokenrules(self):
        """ Return the collection of brokenrules for each of the entity
        objects in this collection. If no rules have been broken, then
        an empty ``brokenrules`` collection will be returned.
        """
        # TODO This property may become obsolete because
        # __getattribute__ is currently handling the `'brokenrules' ==
        # attr` condition.
        return self.getbrokenrules()

    def getbrokenrules(self, gb=None):
        """ Return the collection of brokenrules for each of the entity
        objects in this collection. If no rules have been broken, then
        an empty ``brokenrules`` collection will be returned.

        This implementation is used internally. Most users will want to
        use the ``orm.entities.brokenrules`` property instead.
        """
        brs = entitiesmod.brokenrules()

        # This test corrects a fairly deep issue that has only come up
        # with subentity-superassociation-subentity relationships. We
        # use the below logic to return immediately when an
        # association's (self) collection has any constituents that have
        # already been visited. See the brokenrule collections being
        # tested at the bottom of
        # it_loads_and_saves_reflexive_associations_of_subentity_objects
        # for more clarifications.

        if gb is None:
            gb = list()

        if self in gb:
            return

        gb.append(self)
            
        if any(x in gb for x in self):
            return brs

        try:
            prop = type(self).__dict__['brokenrules']
        except KeyError:
            # A brokenrules property doesn't exist on self
            pass
        else:
            # A brokenrules property exists on self so call it directly
            brs += prop.fget(self)

        # TODO Replace with any() - see above.
        for e in self:
            if not isinstance(e, self.orm.entity):
                prop = type(self).__name__
                msg = "'%s' collection contains a '%s' object"
                msg %= (prop, type(e).__name__)
                brs += entitiesmod.brokenrule(msg, prop, 'valid')
                
            # TODO If an ORM users creates a brokenrules property and
            # forgets to return anything, it will lead to a strange
            # error message here. Instead, we should chek the return
            # value of e.brokenrules and, if its None, raise a more
            # informative error message.
            brs += e.getbrokenrules(gb=gb)

        return brs

    def _self_onremove(self, src, eargs):
        """ The event handler called whenever an entity is removed from
        this collection. When called, the entity object is added to the
        collection's ``trash``. When save() is called on the collection,
        the entity objects in the ``trash`` will be DELETEd from the
        database.
        """

        # By default, we want to trash (DELETE) records when they are
        # removed from the collection. In that case ``dotrash`` will be
        # True. Otherwise, the user probably only wants to remove the
        # item from the collection without DELETing it.
        if self.orm.dotrash:
            self.orm.trash += eargs.entity
            self.orm.trash.last.orm.ismarkedfordeletion = True
        super()._self_onremove(src, eargs)
                    
    def getindex(self, e):
        """ Returns the index count of the entity within the collection.
        If the entity is not in the collection, a ValueError is raised::

                    ix = es.getindex(e)
                    assert es[ix].id == e.id

        :param: e orm.entity|entity.entity: The entity object to look
        for. If ``e`` is an orm.entity, its ``id`` property will be
        compared with other orm.entity id's in this collection. If ``e``
        is an entity.entity, the logic at entities.entities.getindex is
        used instead.
        """
        if isinstance(e, entity):
            for ix, e1 in enumerate(self):
                if e.id == e1.id: return ix
            e, id = e.orm.entity.__name__, e.id
            raise ValueError("%s[%s] is not in the collection" % (e, id))

        super().getindex(e)

    def __repr__(self):
        """ Return a tabular representation of the entity objects
        contained within this entites collection.
        """
        hdr = '%s object at %s count: %s' 
        hdr %= type(self), hex(id(self)), self.count

        try:
            hdr += ' count: ' + self.count
        except:
            # self.count can raise exceptions (e.g., on object
            # initialization) so `try` to include it.
            pass

        hdr += '\n'

        tbl = table()
        r = tbl.newrow()
        r.newfield('Address')
        r.newfield('id')
        r.newfield('str')
        r.newfield('Broken Rules')

        try:
            for e in self:
                try:
                    r = tbl.newrow()
                    r.newfield(hex(id(e)))
                    r.newfield(e.id.hex[:8])
                    r.newfield(str(e))
                    b = ''
                    for br in e.brokenrules:
                        b += '%s:%s ' % (br.property, br.type)
                    r.newfield(b)
                except:
                    r = tbl.newrow()
                    msg = "There was an exception __repr__'ing '%s'"
                    msg %= id(e)
                    r.newfield(msg)
        except:
            # If we aren't able to enumerate (perhaps the self._ls hasn't been
            # set), just ignore.
            pass

        return '%s\n%s' % (hdr, tbl)

class entitymeta(type):
    """ A metaclass of the ``entity`` class. This is where the logic
    resides that takes a class's data definition and converts the
    attributes into internal mappings. For example, when the Python
    interpretor encounters the `class` statement in the following code:

        class myentity(orm.entity):
            name = str
            dob = datetime
            ismale = bool

    the entitymeta.__new__ method below will get called. This will
    convert the name, dob, and ismale attributes into interal mappings.
    Once execution of the class statement is complete, the ``myentity``
    class (as well as objects instantiated from the class) will have
    internal mappings that make the attributes behave as active record
    objects which are ready to be saved to the database::

        # The metaclass removes the original declaration that the
        # ``name`` attribute is a reference to the str type:
        assert myentity.name is not str

        # We can pier behind the scenes to see the ``name`` attribute
        # has been added to the interanl mapping collection.
        assert myentity.orm.mappings['dob'].name == 'dob'

    Because of this magic, more magic is used to make instances of
    myentity conform to the active record pattern::
        
        # Instantiate
        ent = myentity()

        # DROP and CREATE the database table corresponding to myentity
        ent.orm.recreate()

        # Set the attributes to the expected types. (The types specified
        # in the class definition (str and bool) are relevent here but
        # the details will be left out).
        ent.name = 'My Name'
        ent.ismale = False

        # Save the myentity instance to its table in the database
        ent.save()
    """

    def __new__(cls, name, bases, body):
        """ __new__ is the powerhouse of the metaclass. See the comments
        at the class-level of ``entitymeta`` for more.

        :param: cls type: A reference to the metaclass itself.

        :param: name str: The name of the entity.

        :param: bases tuple: A tuple of the base classes from which the
        class inherits

        :param: body dict: A namespace dictionary containing definitions
        for the class body
        """

        if name in ('entity', 'association'):
            return super().__new__(cls, name, bases, body)

        # Instantiate an `orm` object for this class
        ormmod = sys.modules['orm']
        orm_ = orm()

        # Instantiate a `mappings' collection for the `orm`
        orm_.mappings = mappings(orm=orm_)

        # See if we have an `entities` property, i.e., the `entities`
        # class that corresponds to this class.
        try:
            body['entities']
        except KeyError:
            # If we don't have an `entities` property, go through each
            # subclass of `orm.entities` looking for one whose name is
            # the plural of this class's name. When found, assign it to
            # this class's `entities`.
            flect = inflect.engine(); flect.classical(); 
            flect.defnoun('status', 'statuses')

            names = flect.plural(name)
            for sub in orm_.getsubclasses(of=entities):
                if sub.__name__   == names and \
                   sub.__module__ == body['__module__']:

                    body['entities'] = sub
                    break
            else:
                raise builtins.AttributeError(
                    'Entities class for "%s" couldn\'t be found. '
                    'Either specify one or define one with a '
                    'predictable name' % name
                )

        # Make sure the `orm` has a reference to the entities collection
        # class and that the entities collection class has a referenc to
        # the orm.
        orm_.entities = body['entities']
        orm_.entities.orm = orm_

        # Now that the `entities` property has been discovered/created
        # and assigned to the `orm`, lets keep it there and delete it
        # from this entity class's namespace.
        del body['entities']

        # If a class wants to define a custom table name, assign it to
        # the `orm` here and remove it from this entity class's
        # namespace. 
        try:
            orm_.table = body['table']
            del body['table']
        except KeyError:
            # Normally, classes want define a table name, so we can just
            # use the entities name (we want table names to be
            # pluralized) as the table name.
            orm_.table = orm_.entities.__name__

        # Create standard field names in the `body` list. They will
        # later be converted to mapping objects which are added to the
        # `orm`'s `mappings` collection and removed from the `body`
        # list, i.e., this entity class's namespace.
        body['id'] = primarykeyfieldmapping()

        # TODO When an ORM user assigns a value to the createdat or
        # updatedat fields, either an exception should be raised or the
        # user should be able to override the default createdat or
        # updatedat value. Currently, the user cannot override these
        # fields but is presented with no error when attempting to do
        # so.
        body['createdat'] = fieldmapping(datetime)
        body['updatedat'] = fieldmapping(datetime)

        # Use the span base class `span` to add a `begin` and `end`
        # date(time) entry to body along with an instance of the span
        # (datespan or timespan).
        span.expand(body)

        char.expand(body)

        maps = list()
        for k, v in body.items():
            # Is v a reference to a module:
            if isinstance(v, ModuleType):
                # If the datetime module was passed in, convert it to
                # the datetime.datetime class reference. This aliasing
                # is for convenience purposes.
                if v.__name__ == 'datetime':
                    v = datetime

            # Ignore the double underscore attributes
            if k.startswith('__'):
                continue
            
            if isinstance(v, mapping):
                # If the item is already a mapping, we don't need to do
                # anything; just assign it to the map variable.
                map = v

            elif v in fieldmapping.types or \
                (hasattr(v, 'mro') and alias in v.mro()):

                map = fieldmapping(v)

            elif type(v) is tuple:
                # `v` will be a tuple if multiple, comma seperated type
                # arguments are declared, i.e., `str, 0, 1,
                # orm.fulltext`
                args, kwargs = [], {}

                # Iterate over tuple
                for e in v:
                    # Is item is an index or a full index
                    isix = (
                        hasattr(e, 'mro') and index in e.mro()
                        or isinstance(e, index)
                    )
                    
                    if isix:
                        kwargs['ix'] = e
                    else:
                        args.append(e)

                # Create a new map based on the tuple's values
                map = fieldmapping(*args, **kwargs)

            elif hasattr(v, 'mro'):
                mro = v.mro()
                if ormmod.entities in mro:
                    # If `v` is a reference to an existing class that
                    # inherits from `orm.entities`, create a
                    # `entitiesmapping` object. `v` represents the
                    # "many' side of a one-to-many relationship with
                    # this class.
                    map = entitiesmapping(k, v)

                elif ormmod.entity in mro:
                    # if v is a class that inherits from orm.entities,
                    # create an entitymapping. This is for the
                    # composites of an association.
                    map = entitymapping(k, v)
                elif isinstance(v, type):
                    # If v is not an entities or entity type, but is
                    # still a type, ignore it. This condition will be
                    # True of inner classes.
                    continue
                else:
                    # TODO This can happen if we pass an incorrect type.
                    #
                    # For example
                    #    from primative import datetime
                    #    class myentity(orm.entity)
                    #       begin = datetime
                    #
                    # It would be nice to have more information
                    # presented to the ORM user as to what they did
                    # wrong.
                    #
                    # NOTE I wasn't able to reproduce the above. The
                    # elif above catches any actual type. If problem
                    # persists, please write test that actually fails.
                    raise ValueError() # Shouldn't happen
            else:
                if type(v) is ormmod.attr.wrap:
                    # `v` represents an imperitive attribute. It will
                    # contain its own mapping object so just assign
                    # reference. See the `attr` class.
                    map = v.mapping
                else:
                    # If we are here, `v` represents a staticmethod,
                    # method, property or some other attribute that is
                    # not intended for mapping.
                    continue
           
            # Name the map and append the map to the orm's mapping
            # collections.
            map._name = k
            maps.append(map)
            orm_.mappings += map

        # Iterate over the maps list. NOTE that iterating over the
        # `orm_.mappings` collection would invokes it's _populating
        # method which updates the composition of the collection. (See
        # mappings._populated.) That needlessly added about 5 seconds to
        # the start up time, so now we iterate over a simple `list` of
        # maps.
        for map in maps:
            try:
                # Now that we have all the approprite attributes from
                # this class in orm.mappings, we can delete them.
                prop = body[map.name]

                # Delete attribute if it is not an imperitive attribute.
                if type(prop) is not ormmod.attr.wrap:
                    del body[map.name]
            except KeyError:
                # The orm_.mappings.__iter__ adds new mappings which
                # won't be in body, so ignore KeyErrors
                pass

        # Ensure this class has a reference to the `orm` instantiated
        # above.
        body['orm'] = orm_

        # Recreate the class
        entity = super().__new__(cls, name, bases, body)

        orm_.entity = entity

        # Since a new entity has been created, invalidate the derived
        # cache of each entity's mappings collection's object.  They
        # must be recomputed since they are based on the existing entity
        # object available.
        for e in orm.getentitys():
            e.orm.mappings._populated = False

        # Return newly defined class
        return entity

class entity(entitiesmod.entity, metaclass=entitymeta):
    """ The base class from which all orm.entity classes inherit.
    """

    # These are the limits of the MySQL datetime type
    mindatetime=primative.datetime('1000-01-01 00:00:00.000000+00:00')
    maxdatetime=primative.datetime('9999-12-31 23:59:59.999999+00:00')

    def __init__(self, o=None, **kwargs):
        """ Constructs an entity. 

        If the ``o`` is not None, the table is queried on the primary
        key against ``o`` and the object is hydrated with the results::

            # Create the id of the entity
            id = UUID(hex='66f2ca21e3ee4dd7aa8a14f65d48c4bf')

            # Load entity by ID. The SQL sent to the database will be
            # something like the following: 
            #     SELECT * FROM MYENTITY 
            #     WHERE ID = '66f2ca21e3ee4dd7aa8a14f65d48c4bf'
            ent = myentity(id)

            assert ent.id.hex == '66f2ca21e3ee4dd7aa8a14f65d48c4bf'

        If o is None, a new entity will be created, ready to be saved to
        the database once its attributes have been correctly set:
            
            ent = myentity()
            assert ent.orm.isnew

            ent.attr1 = 'a value'
            ent.attr2 = 'another value'

            # An INSERT saves the new entity to the database
            ent.save()

            # ent knows it's not new, i.e., it's in the database.
            assert not ent.orm.isnew

        The **kwargs dict can be used to set attributes during
        construction. For example, the above ent objct could have been
        constructed like so::

            ent = myentity(
                attr1 = 'a value',
                attr2 = 'another value'
            )

        :param: o UUID: The id of the entity. If None, then a new entity
        will be created. 

        :param: kwargs dict: A dict of attribute names as keys mapped to
        the values the constructor should assign to its attributes.
        """
        
        # TODO Support eager loading:
        #
        #     art = artist(name=name, eager('presentations'))
        try:
            self.orm = self.orm.clone()
            self.orm.initing = True # TODO change to `isiniting`
            self.orm.instance = self

            # TODO These should be lazy-loaded in getters
            self.onbeforesave       =  entitiesmod.event()
            self.onaftersave        =  entitiesmod.event()
            self.onafterload        =  entitiesmod.event()
            self.onbeforereconnect  =  entitiesmod.event()
            self.onafterreconnect   =  entitiesmod.event()

            # TODO self._self_onbeforesave has no implementation. It
            # exists mearly so subentity objects can inherit from it.
            # Subentity objects should probably subscribe to this event
            # handler instead. That way, we can lazy load onbeforesave
            # above.
            self.onbeforesave      +=  self._self_onbeforesave
            self.onaftersave       +=  self._self_onaftersave
            self.onafterload       +=  self._self_onafterload
            self.onafterreconnect  +=  self._self_onafterreconnect

            super().__init__()
            if o is None:
                self.orm.isnew = True
                self.orm.isdirty = False
                self.id = uuid4()

                # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
                # Assign the proprietor (the owner of the entity) to the
                # entity's `proprietor` attribute. This ensure the
                # proprietor gets saved to the database.
                # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
                if security().proprietor:
                    self.proprietor = security().proprietor

                # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
                # If there is an owner, assign the owner to the new
                # entity so we know which user created the entity.
                # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
                if security().owner:
                    self.owner = security().owner
            else:
                if isinstance(o, str):
                    # See if we can convert str identifier to UUID. 
                    # TODO Currently this works with a hex string that
                    # has no dash. We may want to do more work to
                    # determine what we need to do if `o` has dashes,
                    # if the UUID is expressed as an int, or if the UUID
                    # has been base64 encoded.
                    o = UUID(hex=o)
                elif isinstance(o, entity):
                    o = o.id

                if type(o) is UUID:
                    res = self.orm.load(o)
                else:
                    raise TypeError(
                        'Can only load by UUID. '
                        'If you are setting attributes via the '
                        'constructor, ensure that you are including '
                        'the keys as well.'
                    )

                self.orm.populate(res)

                # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
                # Unless override is True...
                # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
                if not security().override:

                    # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
                    # Test the retrievability of the entity tto make
                    # sure the user can access the entity.
                    # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
                    vs = self.retrievability

                    # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
                    # Make sure ``retrievability`` returns a
                    # ``violations`` object since this is up to the orm
                    # user to get right.
                    # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
                    if not isinstance(vs, violations):
                        raise TypeError(
                            "'retrievability' must return a "
                            '`violations` instance.'
                        )

                    # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
                    # If there are violations...
                    # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
                    if vs.ispopulated:

                        # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
                        # Raise an AuthorizationError
                        # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
                        raise AuthorizationError(
                            msg = (
                                f'Cannot access {type(self).__name__}:'
                                f'{self.id.hex}'
                            ),
                            crud='r', vs=vs, e=self, 
                        )

            # TODO If k is not in self.orm.mappings, we should throw a
            # ValueError.
            # Set attributes via keyword arguments:
            #     per = person(first='Jesse', last='Hogan')
            for k, v in kwargs.items():
                setattr(self, k, v)

            # Post super().__init__() events
            self.onaftervaluechange += self._self_onaftervaluechange
        finally:
            self.orm.initing = False

    @property
    def retrievability(self):
        """ 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        Return a default implementation of retrievability
        💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        """
        return self._getaccessability('retrievability')

    @property
    def creatability(self):
        """ 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        Return a default implementation of creatability
        💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        """
        return self._getaccessability('creatability')

    @property
    def updatability(self):
        """ 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        Return a default implementation of updatability
        💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        """
        return self._getaccessability('updatability')

    @property
    def deletability(self):
        """ 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        Return a default implementation of deletability
        💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        """
        return self._getaccessability('deletability')

    def _getaccessability(self, type):
        """ 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        Return a default implementation of accessibility methods
        (creatability, retrievability, updatability and deletability)
        💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        """

        # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        # If override is True, return an empty violations object
        # implying that there is no accessibility issue.
        # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        if security().override:
            return violations()

        # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        # Unless override is True, the default implementation of the
        # accessibility methods is to raise an AuthorizationError.
        # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        raise AuthorizationError(
            f'{type} not implemented',
            crud=type[0], vs=None, e=self
        )

    def __getitem__(self, args):
        """ Returns the value of the attribute given, or a tuple of
        multiple value if multiple arguments are given. 

            myent = myentity()

            # These two statements are equivalent
            v = myent.attr1    # Standard notation
            v = myent['attr1'] # __getitem__ notation

            # When indexing multiple values, we get a tuple.  These two
            # statements are equivalent
            v1, v2 = myent.attr1, myent.attr2  # Standard notation
            v1, v2 = myent['attr1', 'attr2']   # __getitem__ notation

        """
        if type(args) is str:
            try:
                return getattr(self, args)
            except builtins.AttributeError as ex:
                raise IndexError(str(ex))

        vals = []

        for arg in args:
            vals.append(self[arg])

        return tuple(vals)

    def __call__(self, args):
        """ Allows for index notation to be used:

            # These two statements are equivalent
            v = myent.attr1    # Standard notation
            v = myent('attr1') # __call__ notation

            # When indexing multiple values, we get a tuple.  These two
            # statements are equivalent
            v1, v2 = myent.attr1, myent.attr2  # Standard notation
            v1, v2 = myent('attr1', 'attr2')   # __call__ notation

        See __getitem__ for full description.

        The difference between __call__ and __getitem__ is that __call__
        returns None if the attribute is not found; __getitem__ raises
        an IndexError.
        """
        try:
            return self[args]
        except IndexError:
            return None

    def _self_onafterload(self, src, eargs):
        """ A method to handle the onafterload method (invoked in
        (``orm.load``). After the entity is loaded, this handler will
        add the SQL used to load the entity and related data to the
        db.chronicler.
        """
        self._add2chronicler(eargs)

    def _self_onbeforesave(self, src, eargs):
        """ An event handler invoked the moment before the entity is
        saved. This handler does nothing, but is here so subentitty
        classes can override it.
        """
        pass

    def _self_onaftersave(self, src, eargs):
        """ A method to handle the onaftersave event (invoked in
        (``orm._save``). After the entity is loaded, this handler will
        add the SQL used to save the entity and related data to the
        db.chronicler.
        """
        self._add2chronicler(eargs)

    def _self_onafterreconnect(self, src, eargs):
        """ A method to handle the onafterreconnect event. The
        reconnection data is added to the db.chronicler.
        """
        self._add2chronicler(eargs)

    @staticmethod
    def _add2chronicler(eargs):
        """ Add SQL and related data from a database operation to the
        db.chronicler singleton.
        """
        chron = db.chronicler.getinstance()
        chron += db.chronicle(eargs.entity, eargs.op, eargs.sql, eargs.args)

    def _self_onaftervaluechange(self, src, eargs):
        """ This event handler captures the ``onaftervaluechange`` event for
        an entity. 
        
        This handler is necessary for capturing changes in atttribute
        values and flagging the entity as dirty. A dirty entity will be
        UPDATEd by the entity.save() method::

            # Load entity
            ent = myent(id)

            # Nothing has happend so we aren't dirty
            assert not ent.orm.isdirty

            # Save does nothing
            ent.save()

            # Changing an attribute will invoke this handler and dirty
            # the entity.
            ent.attr1 = 'new value'

            # Now we are dirty
            assert ent.orm.isdirty

            # .save() issues an UPDATE
            ent.save()
        """
        if not self.orm.isnew:
            self.orm.isdirty = True

    def __dir__(self):
        """ Returns a list of all property names for this entity
        including those inherited from superentities. __dir__ is called
        by the Python builtin ``dir()``. This method is also necessary
        for the autocompletion of attributes to work correctly in
        debugging tools such ad pdb.
        """
        ls = super().__dir__() + self.orm.properties

        # Remove duplicates. If an entity has an imperitive attribute, the name
        # of the attribute will come in from the call to super().__dir__()
        # while the name of its associated map will come in through
        # self.orm.properties
        return list(set(ls))

    def __setattr__(self, attr, v, cmp=True, imp=False):
        """ Set the value of `v` to the attribute (`attr`) of the
        `entity`. Attribute usually refer to the ORM mapping attributes
        (those defined in the header of a class). However, standard
        Python class attributes can also be set her..

        :param: str attr: The name of the attribute to be set

        :param: object v: The value to which the attribute will be set.

        :param: bool cmp: Determines whether `entities._setvalue` should
        compare the old value of the attribute to the new value. See the
        `cmp` variable in that method for more.

        :param: bool imp: If True, indicates that __setattr__ is being
        called by an imperitive setter. If this is the case, we want to
        avoid infinite recursion by not calling the setter. Instead, we
        allow the normal behavior of finding the ``mapping`` object
        associated with the setter and setting its ``value`` attribute
        to the ``v`` argument. By default, it is False, because this is
        only necessary for imperitive setters.
        """

        # Need to handle 'orm' first, otherwise the code below that
        # calls self.orm won't work.
        if attr == 'orm':
            return object.__setattr__(self, attr, v)

        map = self.orm.mappings(attr)

        if map is None:
            maps = self.orm.mappings.supermappings

            if attr not in maps:
                return object.__setattr__(self, attr, v)

            # If there is a setter @property (non-mapping) directly on
            # `self`, call it directly. This makes it possible to
            # override mappings with regular @property's. See how the
            # @property `person.name` updates the mapping `party.name`.
            #
            # TODO There currently isn't a use case for this, but we
            # will probably want to ascend the inheritance tree here.
            # For example, if we wanted to extend the `person` entity
            # with a new class `alien`, we would want `alien` to inherit
            # the functionality of `person.name`. Currently, that
            # probably wouldn't work.
            for name, var in vars(type(self)).items():
                if name == attr and isinstance(var, property):
                    if var.fset:
                        return object.__setattr__(self, attr, v)
                
            self.orm.super.__setattr__(attr, v, cmp)
        else:
            if isinstance(map, fieldmapping):
                if map.issetter and not imp:
                    return object.__setattr__(self, attr, v)

            # Call entity._setvalue to take advantage of its event
            # raising code. Pass in a custom setattr function for it to
            # call. Use underscores for the paramenters since we already
            # have the values it would pass in in this method's scope -
            # except for the v which, may have been processed (i.e, if
            # it is a str, it will have been strip()ed. 
            def setattr0(_, __, v):
                map.value = v

            self._setvalue(attr, v, attr, setattr0, cmp=cmp)

            if type(map) is entitymapping:
                # FIXME:6028ce62 An entitymapping attribute could be set
                # to None.  However, that would mean `v` would be None
                # here, so accesing its attributes causes an error. We
                # need to allow `v` to be None and find a different way
                # of getting the attributes it's getting
                e = v.orm.entity
                while True:
                    for map in self.orm.mappings.foreignkeymappings:

                        # A flag to determine whether or not we set this
                        # map's `value` property.
                        set = False

                        if map.isproprietor and attr == 'proprietor':
                            # If the FK map is the proprietor FK
                            # (proprietor__partyid), and the attr is
                            # 'proprietor' then we want to set this map.
                            # We sort of make an exception for
                            # proprietor setting because a proprietor's
                            # type is `party.party`, though a propietor
                            # could be a subentity of that, such as
                            # `party.company`. Normally we want an exact
                            # type match (see alternative block) for FK
                            # matching, but here we want to allow
                            # subentities.
                            set = True
                        elif map.isowner and attr == 'owner':
                            set = True
                        elif attr not in ('owner', 'proprietor'):
                            # If the value's (v) entity is the maps
                            # entity, this is the  map we are looking
                            # for.

                            # TODO We may want to remove the fkname, e1
                            # and attr tests. These were added for the
                            # proprietor's fk but that is now handled in
                            # the consequence block.
                            fkname, e1 = map.fkname, map.entity
                            set = e1 is e 
                            set = set and (not fkname or attr == fkname)

                        if set:
                            if self.orm.isreflexive:
                                if map.name.startswith(attr + '__'):
                                    self._setvalue(
                                        map.name, v.id, map.name, 
                                        setattr0, cmp=cmp
                                    )
                            else:
                                self._setvalue(
                                    map.name, v.id, map.name, 
                                    setattr0, cmp=cmp
                                )
                                break;
                    else:
                        e = e.orm.super
                        if e:
                            continue
                        else:
                            # If we have gotten here, no FK was found in
                            # self that matches the composite object
                            # passed in. This is probably because the
                            # wrong type of composite was given. The
                            # user/programmers has made a mistake.
                            # However, the brokenrules logic will detect
                            # this and alert the user to the issue.
                            pass
                    break

                # Look within the super's mapping collection for an
                # entitymapping that matches this composite. This will
                # recurse to the top of the inheritance tree. For
                # example, if we assige a rapper to a battle's rapper
                # composite:
                #
                #     btl.rapper = rpr
                # 
                # we would like that rpr to be the singer and artist of
                # the battle's super classes: concert and presentations
                # respectively:
                #
                #    conc = btl.orm.super
                #    assert conc.singer is rpr
                #
                #    pres = btl.orm.super.orm.super
                #    assert pres.artist is rpr
                sup = self.orm.super
                if sup:
                    for map in sup.orm.mappings.entitymappings:
                        if map.entity in v.orm.entity.orm.supers:
                            
                            # Take some extra precautions with
                            # proprietor mappings. Propogate a
                            # proprietor map up the inheritence tree
                            # only if the attr == 'proprietor'.
                            # Otherwise, the descision to do so would be
                            # based on type, which is too risky for the
                            # proprietor.
                            if attr != 'proprietor':
                                if map.isproprietor:
                                    continue

                            setattr(sup, map.name, v)
                            break

    def delete(self):
        """ Delete an entity's record from the database.

            # Load an existing entity
            ent = myent(id)

            # Cause a DELETE statement to be issued deleting the record
            # by its primary key.
            ent.delete()
        """

        # To delete a record, mark it for deleting. The save() method
        # will ensure the record is deleted.
        self.orm.ismarkedfordeletion = True
        self.save()

    def save(self, *es):
        """ Persist the entity to the database as well as all of its
        constituents (recursive and non-recursive), associations, and
        composites. All entity objects will be persisted in a single
        MySQL atomic transaction. The orm.entity and orm.entities
        objects in the *es tuple will also be persisted in the atomic
        transaction. ``entity`` objects maintain a persistence state
        (see orm.persistencestate) which save() uses to determine if a
        CRUD operation is needed and which CRUD operation will be used.

        :param: *es tuple(<orm.entity>|<orm.entities>): A tuple of
        orm.entity and/or orm.entities objects that the users wish to
        be persisted within the atomic transaction. This is rarely
        needed but sometimes comes in handy::
            
            # Create two new users
            usr = ecommercs.user()
            usr1 = ecommerce.user()

            # Save (INSERT) usr along with usr1 in a single atomic
            # transaction
            usr.save(usr1)

        Simple entity save
        ------------------

            # Create a goods record
            g = good()
            assert not g.orm.isnew

            # Persist (INSERT record)
            g.save()
            assert not g.orm.isnew

            # Change property
            assert not g.orm.isdirty
            g.name = 'new name'
            assert g.orm.isdirty

            # Persist (UPDATE record)
            g.save()
            assert not g.orm.isdirty

            # Delete
            g.orm.ismarkedfordeletion = True
            # Persist (DELETE record)
            g.save()

            # Alternatively, this would work:
            #     
            #     g.delete()

        Constituents
        ------------

            # Add item
            g.items += product.item()

            # Create (INSERT) a new product.item associated with the
            # good.
            g.save()

        Composite
        ---------

            # Load the product.item from the Constituents section above
            itm = product.item(g.items.first.id)

            # Change the good (composite) that the itm belongs to
            itm.good.name = 'a newer name'

            # A save of the item will cause the good to be UPDATEd
            itm.save()

        Recursive
        ---------
        Any entity objects associated with the entity being saved will
        be found and saved as well. For example, if we want to create a
        new ``artist`` and assign it a new ``presentation`` objects,
        calling save() on the artist will also save the presentation
        object::

            art = artist()
            art.presentations += presentation()

            # INSERTs for the artist and the presentation will be
            # performed.
            art.save()

        Atomicity
        ---------
        When save() is called, it creates a transaction (cursor) object.
        For each of the entity objects it save()s recursively, including
        the entity objects in *es, the transaction object will be used.
        When all the entity objects have been save()ed, the transaction
        will be committed. If an exception is raised at any point in
        this process, the transaction will be rolled back.
        """
        # Create a callable to call self._save(cur) and the _save(cur)
        # methods on earch of the objects in *es.
        def save(cur):
            self._save(cur)
            for e in es:
                e._save(cur)

        # Create an executioner object with the above save() callable
        exec = db.executioner(save)

        # Register reconnect events of then executioner so they can be
        # issued
        exec.onbeforereconnect += \
            lambda src, eargs: self.onbeforereconnect(src, eargs)
        exec.onafterreconnect  += \
            lambda src, eargs: self.onafterreconnect(src, eargs)

        # Call then executioner's exec methed which will call the exec()
        # callable above. executioner.execute will take care of dead,
        # pooled connection, and atomicity.
        exec.execute()

    def _save(self, cur=None, guestbook=None):
        """ A private method called by orm.save(). This method is where
        most of the saving logic actually resides. See the docstring at
        orm.save for an overview of the persistence operations.
        """

        # The guestbook list tracks the entity objects that have been
        # _save()ed and prevents re-save()ing the same entity. Without
        # the guestbook list, we would get infinite recursion errors
        # because to save and entity is to save it and all the entity
        # objects in its graph - some of which might be linked to each
        # other.
        if guestbook is None:
            guestbook = list()
        
        if self in guestbook:
            return

        guestbook.append(self)

        # Don't save the entity if it doesn't pass its validation rules
        # (not self.isvalid). If we are simply deleting the entity, the
        # the validation rules don't matter.
        if not self.orm.ismarkedfordeletion and not self.isvalid:
            raise db.BrokenRulesError("Can't save invalid object", self)

        # Determine if we are deleting, creating or updating the entity
        # based on its presistence state. Grab the SQL necessary for
        # the chosen operation.
        if self.orm.ismarkedfordeletion:
            crud = 'delete'
            sql, args = self.orm.mappings.getdelete()
        elif self.orm.isnew:
            crud = 'create'
            self.createdat = self.updatedat = primative.datetime.utcnow()
            sql, args = self.orm.mappings.getinsert()
        elif self.orm._isdirty:
            self.updatedat = primative.datetime.utcnow()
            crud = 'update'
            sql, args = self.orm.mappings.getupdate()
        else:
            crud = None
            sql, args = (None,) * 2

        #💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        # If we are modifying the record, the security().proprietor must
        # match the record's proprietor. This ensures one party can't
        # modify another's records.
        #💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣

        # TODO:ee897843 Don't allow a proprietor to create a record
        # belonging to a different proprietor.
        if crud in ('update', 'delete'):
            if self.proprietor__partyid != security().proprietor.id:
                raise ProprietorError(self.proprietor)

        try:
            # Take snapshot of before state
            st = self.orm.persistencestate

            # If there is no sql, then the entity isn't new, dirty or
            # marked for deletion. In that case, don't save.  However,
            # allow any constituents to be saved.
            if sql:
                # Raise event
                eargs = db.operationeventargs(
                    self, crud, sql, args, 'before'
                )

                self.onbeforesave(self, eargs)

                if not eargs.cancel:
                    # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
                    # Unless override is True, thes the creatability,
                    # updatability or deletability of the entity given
                    # the crud.
                    # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
                    if not security().override:
                        if crud == 'create':
                            vs = self.creatability
                        elif crud == 'update':
                            vs = self.updatability
                        elif crud == 'delete':
                            vs = self.deletability

                        # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
                        # If there are violations, raise an
                        # AuthorizationError
                        # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
                        if vs.ispopulated:
                            raise AuthorizationError(
                                msg=(
                                    f'Cannot {crud} '
                                    f'{type(self)}:{self.id.hex}'
                                ), crud=crud[0], vs=vs, e=self
                            )

                    # Issue the query
                    cur.execute(sql, args)

                    # Update new state
                    self.orm.isnew = self.orm.ismarkedfordeletion

                    # We must be clean if we just updated the database
                    self.orm.isdirty = False

                    # Entity must not be marked for deletion of we just
                    # updated the database
                    self.orm.ismarkedfordeletion = False

                    # Raise event
                    eargs.preposition = 'after'
                    self.onaftersave(self, eargs)

            # For each of the constituent entities classes mapped to
            # self, set the foreignkeyfieldmapping to the id of self,
            # i.e., give the child objects the value of the parent id
            # for their foreign keys
            for map in self.orm.mappings:

                if type(map) is entitymapping:
                    # TODO The below comments should probably be
                    # deleted; followentitiesmapping isn't used any more:
                    # ...
                    # Call the entity constituent's save method. Setting
                    # followentitiesmapping to false here prevents it's
                    # child/entitiesmapping constituents from being
                    # saved. This prevents infinite recursion. 
                    if map.isloaded:
                        map.value._save(
                            cur, 
                            guestbook=guestbook
                        )

                if type(map) is entitiesmapping:
                    if map.isloaded:
                        es = map.value
                        # Take snapshot of states
                        sts = es.orm.persistencestates

                        # Iterate over each entity and save them
                        # individually
                        for e in es:
                            
                            # Elements in the `es` collection may not be
                            # of the same type as the es collection.
                            # This occures when subentity objects are
                            # injected into the superentities
                            # collections. E.g.,:
                            #
                            #     sng.concerts = conc = concert()
                            #     assert conc in sng.presentations
                            #
                            # (See
                            # it_adds_subentity_to_superentiies_collection)
                            # In this case, we wouldn't want to save the
                            # reference to the concert element when
                            # iterating over the presentations
                            # collection because it causes infinine
                            # recursion. The below line will prevent
                            # this.

                            if type(es) not in e.orm.entities.mro():
                                continue

                            # Set the entity's FK to self.id value
                            for map in e.orm.mappings:
                                if type(map) is foreignkeyfieldmapping:
                                    
                                    # Under no circumstance should the
                                    # proprietor be set here. 
                                    if map.isproprietor:
                                        continue
                                    
                                    if map.entity is self.orm.entity:
                                        # Set map.value to self.id. But
                                        # rather than a direct
                                        # assignment, map.value =
                                        # self.id use setattr() to
                                        # invoke the _setvalue logic.
                                        # This ensures that the proper
                                        # events get raised, but even
                                        # more importantly, it dirties e
                                        # so e's FK will be changed in
                                        # the database.  This is mainly
                                        # for instances where the
                                        # constituent is being moved to
                                        # a different composite.
                                        setattr(e, map.name, self.id)
                                        break

                            # Call save(). If there is an Exception,
                            # restore state then re-raise
                            try:
                                # If self was deleted, delete each child
                                # constituents. Here, cascade deletes
                                # are hard-code.
                                if crud == 'delete':
                                    e.orm.ismarkedfordeletion = True

                                # TODO The below comments should
                                # probably be deleted;
                                # followentitymapping isn't used any
                                # more:
                                # If the previous operation on self was
                                # a delete, don't ascend back to self
                                # (followentitymapping == False). Doing
                                # so will recreate self in the database.
                                e._save(
                                    cur, 
                                    guestbook=guestbook
                                )
                            except Exception:
                                # Restore states
                                es.orm.persistencestates = sts
                                raise
                
                        for e in es.orm.trash:
                            trashst = e.orm.persistencestate
                            try:
                                e._save(cur, guestbook=guestbook)
                            except Exception:
                                e.orm.persistencestate = trashst
                                raise

                        # TODO If there is a rollback, shouldn't the
                        # entities be restored to the trash collection.
                        # Also, shouldn't deleting the associations
                        # trash (see below) do the same restoration.
                        es.orm.trash.clear()
                            
                if type(map) is associationsmapping:

                    if map.isloaded:
                        # For each association then each trashed
                        # association
                        for asses in map.value, map.value.orm.trash:
                            for ass in asses:
                                ass._save(cur, guestbook=guestbook)
                                for map in \
                                    ass.orm.mappings.entitymappings:
                                    if map.isloaded:
                                        if map.value is self:
                                            continue
                                        e = map.value
                                        e._save(
                                            cur, 
                                            guestbook=guestbook
                                        )

                                # The below code handles certain
                                # subentity-superassociation-subentity
                                # saves. E.g., if we have singers in the
                                # `sng.singers` pseudocollection, and
                                # the association between `sng` and
                                # `singers` is via the superassociation
                                # `artist_artist` then changes made to
                                # `singers` won't be presisted unless we
                                # descend down the inheritance tree from
                                # `artist` to `singer`. See 3cb2a6b5.

                                # Is the association reflexive and has
                                # an object.
                                if asses.orm.isreflexive and ass.object:
                                    # Get the object's class and
                                    # subentities.

                                    clss = [ass.object.orm.entities]
                                    subs = ass.object.orm.subentities
                                    clss += [
                                        x.orm.entities
                                        for x in subs
                                    ]

                                    # Descend the inheritance tree
                                    for cls in clss:
                                        name = cls.__name__

                                        # Get the association's
                                        # constituents here so we can
                                        # handle the KeyError exception.
                                        # If we get the pseudocollection
                                        # the normal way, 
                                        #
                                        #   getattr(ass, name)
                                        #
                                        # the KeyError would result in
                                        # the creation of some
                                        # non-existing subentities.
                                        const = asses.orm.constituents
                                        
                                        try:
                                            # Get pseudocollection
                                            es = const[name]
                                        except (KeyError, IndexError):
                                            # Subentity doesn't exist

                                            # NOTE:ce6ea883 Except both
                                            # KeyError and IndexError
                                            # because `const` can be a
                                            # dict or an entities
                                            # collection
                                            pass
                                        else:
                                            # Save each entity found in
                                            # the pseudocollection
                                            for e in es:
                                                e._save(cur,
                                                    guestbook=guestbook)

                        asses.orm.trash.clear()

                if type(map) is foreignkeyfieldmapping:
                    if map.value is undef:
                        map.value = None

            # If the super has not been previous set and self.orm.isnew
            # (st[0])...
            if not self.orm._super and st[0]:
                # In order for `self.orm._super` to have previously been
                # set when `self.orm.isnew` was True, an attribute of the
                # super would have to have been set in the client code
                # (this is when ._super gets its value). However,
                # sometimes the attribute won't get set thus leaving
                # ._super as None. If we are saving a new graph, we want
                # the `._super` whether or not it has been previously
                # set. Therefore, we will instantiate one here.

                # Get the superentity
                sup = self.orm.entity.orm.super

                # If there is a super entity (we may be at the top of
                # the graph)...
                if sup:
                    sup = sup()
                    sup.id = self.id
                    self.orm._super = sup

            # Get the private superentity. We don't want to use the
            # public accessor to get it because the accessor will load
            # the superentity which isn't something we want to do when
            # saving the graph.
            sup = self.orm._super
            if sup:
                if crud == 'delete':
                    sup.orm.ismarkedfordeletion = True
                sup._save(cur, guestbook=guestbook)

        except Exception:
            self.orm.persistencestate = st
            raise
        
    @property
    def brokenrules(self):
        """ Return the brokenrules collection for this entity. See
        the getbrokenrules() method for more.
        """

        # The actual logic for this is in the getbrokenrules() since it
        # can handle recursion with its optional guestbook (gb)
        # parameter.
        return self.getbrokenrules()

    def getbrokenrules(self, gb=None):
        """ Return the brokenrules collection for this entity.

        Though the `brokenrules` property can be called for convenience,
        subclasses should override this method in order to implement
        their own validation logic. This method uses the `gb`
        (guestbook) argument to prevent infinite recursion::

            class person(self):
                def getbrokenrules(self, *args, **kwargs):
                    
                    # Call up the inheritance hierarchy to get the
                    # brokenrules for all the superentity objects
                    # up to and including orm.entity.getbrokenrules.
                    brs = super().getbrokenrules(*args, **kwargs)

                    # Add our on validation: ensure emails have @ signs
                    # in them.
                    if '@' not in self.email:
                        brs += brokenrule(
                            msg = 'Invalid email address',
                            prop = 'email',
                            entity = self
                        )

                    # Return the brokenrules collection
                    return brs

        Given the above, we can expect the followiwng::
            
            per = person()

            # Broken rule
            per.email = 'jhoganATgmail.com'

            # Assert that the rule is broken
            assert per.brokenrules.count == 1
            assert per.brokenrules.first.message == 'Invalid email address'
            assert not per.isvalid

            # Fix
            per.email = 'jhogan@gmail.com'

            # Assert that there are now no broken rules
            assert not per.brokenrules.count
            assert per.isvalid
        
        Subentity classes should override this method to implement
        centralized versions of their validation logic. When they call
        up the inheritence hierarchy (see example), this method will
        eventually be called which adds the standard validation rules
        for all entity objects, vis. type checking:

            class person(self):
                age = int
                def getbrokenrules(self, *args, **kwargs):
                    brs = super().getbrokenrules(*args, **kwargs)

                    # Add our on validation: ensure emails have @ signs
                    # in them.
                    if '@' not in self.email:
                        brs += brokenrule(
                            msg = 'Invalid email address',
                            prop = 'email',
                            entity = self
                        )

                    # Return the brokenrules collection
                    return brs

            per = person()

            # Break the stardard rule and the custom rule

            # Age must be an int or coersable to an int 
            # (e.g., per.age = 123 or per.age = "123")
            per.age = 'abcdefg'  
            per.email = 'jhoganATgmail.com'

            # Now we have two broken rules
            assert per.brokenrules.count == 2
            assert per.brokenrules.first.message == 'Invalid email address'
            assert per.brokenrules.second.message == 'age is wroge type'
            assert not per.isvalid

            # Fix
            per.age = 123456
            per.email = 'jhogan@gmail.com'

            # Assert that there are now no broken rules
            assert not per.brokenrules.count
            assert per.isvalid
        """

        brs = entitiesmod.brokenrules()

        if gb is None:
            gb = list()

        if self in gb:
            return brs

        from ecommerce import user
        isroot = isinstance(self, user) and self.isroot

        gb.append(self)

        try:
            # Search for brokenrules property on self
            prop = type(self).__dict__['brokenrules']
        except KeyError:
            # A brokenrules property doesn't exist on self
            pass
        else:
            # A brokenrules property exists on self so call it directly
            brs += prop.fget(self)
            
        for map in self.orm.mappings:
            if type(map) is fieldmapping:
                t = map.type
                if t == types.str:
                    brs.demand(
                        self,         map.name,    type=str,
                        min=map.min,  max=map.max
                   )

                elif t == types.int:
                    brs.demand(
                        self,         map.name,  min=map.min,
                        max=map.max,  type=int
                    )

                elif t == types.bool:
                    brs.demand(self, map.name, type=bool)

                elif t == types.float:
                    brs.demand(self, 
                        map.name,                 type=float,
                        min=map.min,              max=map.max,
                        precision=map.precision,  scale=map.scale
                    )

                elif t == types.decimal:
                    brs.demand(
                        self,                  map.name,
                        type=decimal.Decimal,  min=map.max,
                        max=map.min,           precision=map.precision,
                        scale=map.scale
                    )

                elif t == types.bytes:
                    brs.demand(
                        self,         map.name,    type=bytes,
                        max=map.max,  min=map.min
                    )

                elif t == types.date:
                    brs.demand(
                        self, map.name, instanceof=date,
                        min=type(self).mindatetime,
                        max=type(self).maxdatetime,
                    )
                elif t == types.datetime:
                    brs.demand(self, 
                        map.name, 
                        instanceof=datetime,
                        min=type(self).mindatetime,
                        max=type(self).maxdatetime,
                    )

            elif type(map) is entitiesmapping:
                # NOTE Currently, map.value will not load the entities
                # on invocation so we get None for es. This is good
                # because we don't want to needlessly load an object to
                # see if it has broken rules.  However, if this changes,
                # we will want to make sure that we don't needlessy load
                # this. This could lead to infinite recursion (see
                # it_entity_constituents_break_entity)
                es = map.value
                if es:
                    if not isinstance(es, map.entities):
                        msg = "'%s' attribute is wrong type: %s"
                        msg %= (map.name, type(es))
                        brs += entitiesmod.brokenrule(
                            msg, map.name, 'valid'
                        )
                    brs += es.getbrokenrules(gb=gb)

            elif type(map) is entitymapping:
                if map.isloaded:
                    if not isinstance(map.value, map.entity):
                        msg = "'%s' attribute is wrong type: %s"
                        msg %= (map.name, type(map.value))
                        args = msg, map.name, 'valid'
                        brs += entitiesmod.brokenrule(*args)

                    # If the ORM user has overridden `getbrokenrules`,
                    # check if the entity has already been processed by
                    # seeing if `map.value` is in the guestbook.
                    if map.value not in gb:
                        # Get entities brokenrules
                        brs += map.value.getbrokenrules(gb=gb)

            elif isinstance(map, foreignkeyfieldmapping):
                if map.isowner and not isroot:
                    if not isinstance(map.value, UUID):
                        msg = 'Owner reference not set correctly'
                        brs += entitiesmod.brokenrule(
                            msg, map.name, 'valid', self
                        )
                    else:
                        # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
                        # Make sure the owner's id of the entiy matches
                        # that of the security singleton.
                        # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
                        if self.orm.isnew:
                            if security().owner.id != map.value:
                                msg = 'Owner id does not match orm id'
                                brs += entitiesmod.brokenrule(
                                    msg, map.name, 'valid', self
                                )

            elif type(map) is associationsmapping:
                if map.isloaded:
                    brs += map.value.getbrokenrules(gb=gb)

        return brs

    def __getattribute__(self, attr):
        """ Implements all attributes accesses for an entity.

        In addition to returning the values for standard @property's,
        methods and fields declared on the class, the __getattribute__
        method searches the entity's internal mappings collection for
        ORM attributes.
            
            class person(orm.entity):
                # A standard field
                AConstant = 1

                # An ORM attribute
                name = str

                # A standard method
                def get_upper_name(self):
                    return name.upper()

        In the above example, access to the field (AConstant), the ORM
        attribute (name) and the standard method (get_upper_name) all go
        through __getattribute__.

        Access to standard fields and methods is simple - a call is
        simply made to `object.__getattribute__(self, attr)`. The
        internal mapping collection is scanned for the ORM attribute.

        If the ORM attribute is not found in the given entity, the
        inheritance hierachy is ascended to find it::

            class party(orm.entity)
                name = str

            class person(orm.entity):
                pass

            per = person()

            # The internal mapping for party.name is used since there is
            # no person.name mapping.
            per.name = 'Jesse'

            # This can be demostrated by looking at the mapping of the
            # super (party):
            assert 'Jesse' == per.orm.super.orm.mappings['name'].value

        In addition to primative ORM mappings (``fieldmappings``),
        entitymappings, entitiesmappings and associationsmappings are
        scanned here::

            class persons(orm.entities): pass
            class users(orm.entities): pass

            class person(orm.entity):
                # A person has zero or more users, thus a `person` has
                # an entitiesmapping for the ``users`` collection that
                # will be lazy-loaded here.
                users = users

            class user(orm.entity):
                pass

            per = person()

            # Access the ``users`` collection via __getattribute__.
            usrs = per.users

        Associations and pseudocollections are also retrieved through
        this method:::
            class persons(orm.entities):          pass
            class jobs(orm.entities):             pass
            class job_persons(orm.associations):  pass

            class person(orm.entity): pass
            class job(orm.entity): pass

            # A person can have multiple jobs and a job can be done by
            # multiple persons
            class job_person(orm.association):
                person = person
                job = job

            # Get the association through __getattribute__
            per = person()
            jps = per.job_persons

            # Alternatively, get the jobs collection through
            # __getattribute__
            jbs = per.jobs
        """

        try:
            if attr == 'brokenrules':
                return entity.getbrokenrules(self)

            v = object.__getattribute__(self, attr)

            if isinstance(v, span):
                if v.isstatic:
                    v = v.clone(e=self)
                    setattr(self, attr, v)

            return v
        except sys.modules['orm'].attr.AttributeErrorWrapper as ex:
            raise ex.inner
        except AttributeError as ex:
            raise ex.inner
        except builtins.AttributeError as ex:
            pass

        self_orm = self.orm
        self_orm_entity__name__ = self_orm.entity.__name__

        # self.orm.instance is set in entity.__init__. If the user
        # overrides __init__ and doesn't call the base __init__,
        # self.orm.instance is never set. Do a quick check here to
        # inform the user if they forgot to call the base __init__
        if self_orm.isstatic:
            msg = 'orm is static. '
            msg += 'Ensure the overridden __init__ called the base __init__'
            raise ValueError(msg)

        map = self_orm.mappings(attr)

        map_type = type(map)

        # Lazy-load constituent entities map
        if map_type is entitiesmapping:
            if map.value is None:
                es = None
                map_entities = map.entities
                if not self_orm.isnew:

                    # Get the FK map of the entities constituent. 
                    maps = map_entities.orm.mappings.foreignkeymappings
                    for map1 in maps:
                        e = self_orm.entity
                        while e:
                            if map1.entity is e:
                                if not map1.fkname:
                                    break

                                if map1.fkname == e.__name__:
                                    break

                            # If not found, go up the inheritance tree
                            # and try again
                            sup = e.orm.super
                            e = sup.orm.entity if sup else None
                        else:
                            continue
                        break
                    else:
                        raise ValueError('FK map not found for entity')

                    # NOTE Though we've switch to deferred loading for
                    # entities and associations, we should still force
                    # an immediately load here for the sake of
                    # predictability.
                    es = map_entities(map1.name, self.id)
                    es.orm.collect()

                    # Assign the composite reference to the
                    # constituent's elements
                    #   i.e., art.presentations.first.artist = art
                    for e in es:
                        attr = self_orm.entity.__name__

                        def setattr1(e, attr, v):
                            sup = e
                            while sup:
                                try:
                                    map = sup.orm.mappings[attr]
                                except IndexError:
                                    sup = sup.orm.super
                                else:
                                    map.value = v
                                    break

                        # Set cmp to False and use a custom setattr.
                        # Simply calling setattr(e, attr, self) would
                        # cause e.attr to be loaded from the database
                        # for comparison when __setattr__ calls
                        # _setvalue.  However, the composite doesn't
                        # need to be loaded from the database.
                        e._setvalue(
                            attr, self, attr, 
                            cmp=False, setattr=setattr1
                        )

                        # Since we just set e's composite, e now thinks its
                        # dirty.  Correct that here.
                        e.orm.persistencestate = False, False, False

                if es is None:
                    es = map_entities()

                map.value = es

                # Assign the composite reference to the constituent
                # collection.
                #   i.e., art.presentations.artist = art

                # XXX Ascending the graph here is experimental. It
                # caused some issues in it_loads_specialized_composite.
                sup = self_orm.entity
                while sup:
                    setattr(map.value, sup.__name__, self)
                    sup = sup.orm.super

                map.value.onadd.append(self.entities_onadd)

        # Is attr in one of the supers' mappings collections? We don't
        # want to start loading super entities from the database unless
        # we know that the attr is actually in one of them.
        elif not map and attr in self_orm.mappings.supermappings:
            
            # First lets check if we are trying to get a composite that
            # comes from a super. For example, say we are trying to get
            # the `singer` composite of a battle:
            #
            #     btl.singer
            #
            # The above would normally go to the btl's super, concert,
            # and get its composite, singer. However, now that we
            # specialize composites, the singer we would be getting
            # would just be the more specialized rapper of the battle::
            #
            #     btl.rapper is btl.singer
            #
            # In order to not have to load the
            # `btl.orm.super.orm.concerts`, we can just return the
            # rapper object by scanning this classes entitymappings and
            # seeing if the attr is in one of the entitymapping's
            # entity's base classes.
            for map1 in self.orm.mappings.entitymappings:

                if map1.isowner or map1.isproprietor:
                    continue

                sups = [x.__name__ for x in map1.entity.orm.supers]
                if attr in sups:
                    return map1.value

            # If we are here, we are going to check the super to see if
            # it contains a value for attr. The check will automatically
            # propogate up the entity inheritance tree because the call
            # to getattr() will cause us to recurse back into this
            # method for the super, then its super, and so on, as
            # necessary until we finally find the entity that has the
            # attribute that we are looking for.
            sup = self_orm.super
            while sup: # :=
                sup_orm = sup.orm
                map = sup_orm.mappings(attr)
                if map:
                    map_type = type(map)
                        
                    v = getattr(sup, map.name)
                    # Assign the composite reference to the constituent
                    #   i.e., sng.presentations.singer = sng
                    if map_type is entitiesmapping:

                        # Assigne v to es to clarify it is an entities
                        # collecion.
                        es = v

                        # Iterate over each element in the entities
                        # collection including the entities entities
                        # itself:
                        #
                        #     for e in [es, es[0], es[1], ...]
                        #
                        for e in (es,) +  tuple(es):
                            # Set the composite for type(self) on the
                            # entity object or entities collection to
                            # self:
                            #
                            #     sng.presentations.singer = sng
                            #     sng.presentations[0].singer = sng
                            
                            # XXX I think we can remove this.
                            '''
                            setattr(
                                e, 
                                self_orm_entity__name__,
                                self.orm.specialist
                            )
                            '''

                            # The getattr() call above will set the
                            # composite of the entities collection to
                            # the super:
                            #
                            #     sng.presentations.artist = sng.orm.super
                            #
                            # However, so the user will get the most
                            # specialized composite, we replace that
                            # with self.orm.specialized:
                            #
                            #     sng.presentations.artist = sng
                            #
                            # And we do it by ascending the inheritance
                            # tree, this works
                            #
                            # 
                            #     assert rpr.presentations.rapper is rpr
                            #     assert rpr.presentations.singer is rpr
                            #     assert rpr.presentations.artist is rpr
                            sups1 = self_orm.entity.orm.getsupers(
                                withself=True
                            )

                            # For each super class starting with self
                            for sup1 in sups1:

                                # Get name
                                name = sup1.orm.entity.__name__

                                # Get most specialized version of self
                                spec = self.orm.specialist

                                # if e is an entity; not an entities
                                if isinstance(e, entity):

                                    # Ascend inheritence tree
                                    sup2 = e
                                    while sup2:
                                        maps1 = sup2.orm.mappings
                                        try:
                                            # Get super's map
                                            map1 = maps1[name]
                                        except IndexError:
                                            # Dosen't exist: add to dict
                                            # (bypass mapping)
                                            sup2.__dict__[name] = spec
                                        else:
                                            # If exists: add to map
                                            map1.value = spec
                                        
                                        sup2 = sup2.orm._super
                                elif isinstance(e, entities):
                                    # TODO We are already doing this in
                                    # the outer-outer block above.
                                    setattr(e, name, spec)
                                else:
                                    raise TypeError(
                                        'e must be entity or entities'
                                    )

                    if isinstance(v, associations):
                        v.orm.composite = self
                    return v

                # NOTE Each time we ascend to the next super, we are
                # loading the super. This may not be necessary.  We
                # could ascend using class names. However, this may be
                # less efficient because we would have to load the super
                # each time a request for its attribute value came in
                # where as the `super` property memoizes the super
                # object.
                sup = sup_orm.super

            raise ValueError()

        elif map_type is associationsmapping:
            map.composite = self

        elif map is None:
            # For each of self's association mappings, look for the
            # one that has entity mapping that matches `attr`. If
            # found, get the association's collection object from the
            # association mapping.  Then return that collection's
            # `attr` property.
            #
            # For example, if `self` is an `artist`, and  `attr` is
            # 'artifacts', return the association collection
            # `artifacts` collection, i.e., ::
            #
            #     art.artist_arifacts.artifacts
            #
            # This gets you the pseudocollection of the
            # artist_artifacts associations collection.

            orm = self_orm
            while orm:
                for map in orm.mappings.associationsmappings:
                    maps = map.associations.orm.mappings.entitymappings
                    for map1 in maps:
                        if map1.isproprietor:
                            continue

                        es = [map1.entity]
                        es.extend([
                            x.entity 
                            for x in map1.entity.orm.subentities
                        ])
                        for e in es:
                            if e.orm.entities.__name__ == attr:
                                # Skip if association (map) is
                                # non-reflexive and with is e is
                                # collinear with self.
                                if (
                                    self.orm.iscollinear(with_=e)
                                    and not map.entities.orm.isreflexive
                                ):
                                    continue

                                asses = getattr(self, map.name)
                                return getattr(asses, attr)

                sup = orm.super
                if not sup:
                    break

                orm = sup.orm

            return object.__getattribute__(self, attr)

        return map.value

    def entities_onadd(self, src, eargs):
        """
        An event handler invoked when an entity is added to
        an entity object's collection property::

            # Create rapper entity
            rpr = rapper()            

            # Add a new battel to the rapper's battles property
            rpr.battles += battle() 

        This handler ensures that entity objects added to these
        collections are also appended to the superentities collections
        of the entities collection they are being appended to. 

        For example, in the above code, a ``battle`` is added to the
        ``rapper``'s ``battles`` property. But since ``battle`` is a
        subentity of ``concert``, and ``concert`` is a subentity of
        ``presentation``, the ``battle`` entity will, by the logic in
        this handler,  made present in ``rpr.concerts`` as well as
        ``rpr.presentations``.

        :param: src entities: The entities collection that the
        ``eargs.entity`` is being appended to.

        :param: eargs eventargs: The event arguments. Its ``entity``
        property is the entity object that will be appended to the
        superentities.
        """

        # Get the superentities collection that the `e` was
        # appended to.
        sup = src.orm.entities.orm.super

        # If there is no superentity, there is nothing for us to do.
        if not sup:
            return

        # TODO For some reason, the above line:
        #
        #    sup = src.orm.entities.orm.super
        #
        # only gets us the entity class instead of the entities class,
        # so we need the below line to get the entities class. `super`
        # should be fixed such that we get the entities class instead.
        # Then this line can be remove.
        sup = sup.orm.entities

        # If the entities collection that was appended to has the same
        # name as the superentities collection, abort. If we didn't
        # abort, we would append to the same entities collection until
        # maximum recursion was reached. This happens when the entities
        # collection inherits from a super entity with the same name but
        # is contained within a different module. This catch was added
        # so ``effort.requirment.roles`` could be appended to. Here,
        # ``roles`` is <effort.roles> which inherits from
        # <party.roles>. See gem_effort.it_creates_roles.
        if type(src).__name__ == sup.__name__:
            return

        # Get the entity being appended
        e = eargs.entity

        # Get the superentities collection
        try:
            es = getattr(self, sup.__name__)
        except builtins.AttributeError:
            # `self` won't have the attribute `sup.__name__` if the
            # constituent class is a superentity.
            #
            # TODO We should be able to remove this if 1de11dc0 is
            # fixed.
            pass
        else:
            # Append the entity to that entities collection
            es += e


    def __repr__(self):
        """ Create a string representation of the entity.
        """
        try:
            name = self.name
        except builtins.AttributeError:
            name = ''
        else:
            if name:
                name = f", name='{self.name}'"

        r = (
            f'{type(self).__module__}.'
            f'{type(self).__name__}('
                f'id={self.id.hex}'
                f'{name}'
            ')'
        )
        return r

    def __str__(self):
        """ Return the value of the entity object's name attribute if
        there is one. Otherwise, return the entity object's id.

        This is a generic implementation. The author of entity classes
        should feel free to override this method to return the string
        that best represents the object in most situation.
        """
        if hasattr(self, 'name'):
            return '"%s"' % self.name
            
        return str(self.id)
            
class mappings(entitiesmod.entities):
    """ A collection of mappings.

    Each entity, whether as a static class or an instance, has a
    mappings collection. It can be accessed and manipulated from the
    entity, though usually this should be done by ORM code; not code
    that uses the ORM (i.e., web code)::

        class person(orm.entities):
            name = str

        # Access the person's mappings collection to assert that the
        # "name" mapping is a str.
        assert person.orm.mappings['name'].type = orm.types.str

        # Same as above but use an instance of person
        assert person().orm.mappings['name'].type = orm.types.str

    See the docstring for ``mapping`` for more information on mapping
    objects themselves.
    """
    def __init__(self, initial=None, orm=None):
        """ Initialize a mappings collection.

        :param: initial sequence: A collection of mappings to initilize
        this collection with.

        :param: orm orm: A instance of, or reference to, the ``orm``
        class that this mappings collection corresponds to. This allows
        code in the mappings collection to access the ``entity`` object
        it corresponds to::
            
            id = self.orm.entity.id
        """

        super().__init__(initial)
        self._orm = orm
        self._populated = False
        self._populating = False
        self._supermappings = None
        self._nameix = None
        self.oncountchange += self._self_oncountchange

    def _self_oncountchange(self, src, eargs):
        """ When the number of items in this collection changes, set
        self._populated to False. This ensure the self._populate()
        method gets run the next time a user tries to access an element
        (such as when the user iterates over the mappings collection).

        :param: src object: The source object that triggered the event.

        :param: eargs entities.eventargs: The ``eventargs`` is only here
        as a formality, at the moment. (NOTE It seems like this argument
        should hold the 'before1 count and perhaps the 'after' count).
        """
        self._populated = False

    def __getitem__(self, key):
        """ Given ``key``, the map is returned whose name matches the
        key.

            map = myent.orm.mappings['id']
            assert map.name == 'id'

        If the map is not found, an IndexError is raised.
        """

        # Ensure the collection has been properly "populated" before
        # access its elements.
        self._populate()

        if self._nameix is not None and isinstance(key, str):
            try:
                return self._nameix[key]
            except KeyError as ex:
                # Convert the KeyError into and IndexError. When an
                # entities.entities collection is indexed, and the index
                # is not found, we expect and IndexError. A KeyError is
                # more appropriate to dict's.
                raise IndexError(str(ex))

        # If key is not a str, use the default __getitem__
        return super().__getitem__(key)

    def __iter__(self):
        """ Before iterating over the mappings collection (or accessing
        mappings' elements in any other way), we want to ensure that
        ``self._populate`` is called. See ``self._populate`` for more.
        """
        self._populate()
        return super().__iter__()

    def __contains__(self, key):
        """ Test if ``key`` is in the mappings collection.

        For example, instead of writing the following::

            for map in maps:
                if map.name == 'somemap':
                    found = True
                    break
            else:
                found = False

        we could just write::
            
            found = 'somemap' in maps

        :param: key str: The key to look for.
        """
        if isinstance(key, str):
            return any(x.name == key for x in self)
        else:
            # NOTE entities.entities should have a __contains__ method.
            # Surprisingly, I couldn't find one.
            raise ValueError('Invalid type')

    def _populate(self):
        """ Reflect on the entities and associations to populate the
        mappings collection with up-to-date mappings values.

        Note that the method will abort if self._populated is True which
        is typically the case; otherwise it would needlessly populate
        the collection. self._populated starts out as False and is set
        to True when this method is complete. It only changes when the
        the number of maps in the collection changes (see
        mappings._self._oncountchange).
        """
        # If there is no ._orm, then we are using this class just for
        # collection purposes, so don't try to populate here.
        if self._orm is None:
            return

        if not self._populated and not self._populating:
            self._populating = True

            # Remove mapping objects for self which are derive, i.e.,
            # added by this method.
            self.clear(derived=True)

            # Create a list to store mapping objects to be appended to
            # `self` later.
            maps = list()

            # Add an entitymapping of the proprietor and owner reference.
            from party import party
            from ecommerce import user
            self += entitymapping('proprietor', party, isderived=True)
            self += entitymapping('owner', user, isderived=True)

            def add_fk_and_entity_map(e):
                # Add an entity mapping for the composite
                maps.append(
                    entitymapping(e.__name__, e, isderived=True)
                )

                # Add an FK for the constituents
                maps.append(
                    foreignkeyfieldmapping(e, isderived=True)
                )

            ''' Add FK mapings to association objects '''
            # For association objects, look for entity mappings and add
            # a foreign key mapping (e.g., For artist_artifact, add an
            # FK called artistid and artifactid).
            for map in self.entitymappings:
                maps.append(
                    foreignkeyfieldmapping(
                        map.entity, 
                        fkname = map.name, 
                        isderived=True
                    )
                )

            # Set the recursion limit to a value a higher than the
            # default (1000). This method is highly recursive because of
            # the calls to ``orm.getentitys`` and
            # ''orm.getassociations``. This recursion is necessary for
            # the algorithm. 
            #
            # Increasing the recursion limit was not necessary until
            # about halfway through creating the GEM classes when the
            # number of `orm.entity` classes got to about 200. 
            #
            # Unfortunately, I was not able to to figure out a way to
            # return the limit to its default. The normal practice of
            # doing this in a ``finally`` block does't work because it's
            # a global value and doing so would affect the other stacked
            # frames which would rely on the elevated value. So,
            # increasing it here means it's increased for the entire
            # program (unless an effort is made to find every area this
            # method is called). This is probably okay, however, since
            # it seems unlikely it will ever get so big it becomes a
            # problem.
            sys.setrecursionlimit(3000)

            ''' Add composite and constituent mappings '''
            # For each class that inherits from `orm.entity`
            for e in orm.getentitys():
                # If the entity is `self`, ignore unless this is a
                # recursive entity.
                if e is self.orm.entity and not self.orm.isrecursive:
                    continue
                     
                # Look through each of the entities mappings in the
                # giving entity (`e`).
                for map in e.orm.mappings.entitiesmappings:

                    # If `e` is a constituent of `self`
                    if map.entities is self.orm.entities:
                        add_fk_and_entity_map(e)

            ''' Add associations mappings to self '''
            # For each class that inherits form `orm.association`

            for ass in orm.getassociations():

                # For each of the `association`'s entity mappings
                for map in ass.orm.mappings.entitymappings:

                    # If the association`s entity mapping  corresponds
                    # to the self, add associations mapping.
                    if map.entity is self.orm.entity:
                        asses = ass.orm.entities
                        map = associationsmapping(
                            asses.__name__, asses, isderived=True
                        )
                        maps.append(map)
                        break

                # The need arose to ensure that orm.association objects
                # could have one-to-many relationships with orm.entities
                # object. The following block ensures that a FK to the
                # association is created along with a composite mapping
                # to the same association. This is similar to the above
                # `for e in orm.getentitys()` block.

                # TODO One-to-many relationships between association
                # objects have not received their own place in the
                # test.py script. This code was added to correct an
                # issue with the party module. Full testing for this
                # relationship type may prove necessary or desirable.
                for map in ass.orm.mappings.entitiesmappings:
                    if map.entities is self.orm.entities:
                        add_fk_and_entity_map(ass)

            # Add the list of mapping object collected above to `self`
            for map in maps:
                self += map
            
            # All mapping objects will be united through their `orm`
            # reference.
            self._nameix = dict()
            for map in self:
                map.orm = self.orm
                self._nameix[map.name] = map
                    
            # Ensure that the mapping objects are sorted in a
            # predictable way. See the mappings.sort() method for
            # details.
            self.sort()

            self._populating = False

        self._populated = True

    def clear(self, derived=False):
        """ Remove all elements from the mapping collection. If
        ``derived` is True, only remove the mapping objects whose
        ``isderived` property is True. Othewise, remove all mapping
        objects.

        :param: derived bool: If ``derived` is True, only remove the
        mapping objects whose ``isderived` property is True. Othewise,
        remove all mapping objects.  (Derived properties are those that
        are created in the _populate() method).
        """
        if derived:
            for map in [x for x in self if x.isderived]:
                self.remove(map)
        else:
            super().clear()

    def sort(self):
        """ Sort the mapping collection such that it is in a typical,
        predictable order for a collection of table columns. For
        example, the "id" column is typically the first in a list of
        table colums followed by foreign keys. For example::

            id                         # Primary Key
            createdat                  # Builtins
            updatedat
            proprietor__partyid
            owner__userid
            test__artistid             # Foreign Keys
            product__productid
            name                       # Standard fields
            number
            slug
            begin
            end

        This is done mainly for aesthetics. It might be assumed that
        INSERTs and UPDATEs rely on this ordering, but that is no longer
        the case.
        """
        # Make sure the mappings are sorted in the order they are
        # instantiated
        super().sort('_ordinal')

        # Ensure builtins attr's come right after id
        # TODO We should used orm.builtins for this
        for attr in reversed(('id', 'createdat')):
            try:
                attr = self.pop(attr)
            except ValueError:
                # attr hasn't been added to self yet
                pass
            else:
                # Unshift (insert at the begining) attr into self
                self << attr

        # Insert FK maps right after PK map
        fkmaps = list(self.foreignkeymappings)
        fkmaps.sort(key=lambda x: x.name)
        for map in fkmaps:
           self.remove(map)
           self.insertafter(0, map)

    @property
    def foreignkeymappings(self):
        """ A generator to return all the foreignkeyfieldmapping objects in the
        collection::

            for map in maps.foreignkeyfieldmappings:
                assert type(map) is foreignkeyfieldmapping
        """
        return self._generate(type=foreignkeyfieldmapping)

    @property
    def fieldmappings(self):
        """ A generator to return all the fieldmapping objects in the
        collection::

            for map in maps.fieldmappings:
                assert type(map) is fieldmapping
        """
        return self._generate(type=fieldmapping)

    @property
    def primarykeymapping(self):
        """ Return the primary key mapping from the collection::

            assert maps.primarykeymapping.name == 'id'
        """
        return list(self._generate(type=primarykeyfieldmapping))[0]

    @property
    def entitiesmappings(self):
        """ A generator to return all the entitiesmapping objects in the
        collection::

            for map in maps.entitiesmappings:
                assert type(map) is entitiesmapping
        """
        return self._generate(type=entitiesmapping)

    @property
    def entitymappings(self):
        """ A generator to return all the entitymapping objects in the
        collection::

            for map in maps.entitymappings:
                assert type(map) is entitymapping
        """
        return self._generate(type=entitymapping)

    @property
    def associationsmappings(self):
        """ A generator to return all the associationsmapping objects in
        the collection::

            for map in maps.associationsmappings:
                assert type(map) is associationsmapping
        """
        return self._generate(type=associationsmapping)

    def _generate(self, type):
        """ A generator to return all the mapping objects of a given
        type::

            for map in self._generate(type=associationsmapping):
                assert type(map) is associationsmapping

        :param: type type: The type of mapping object, e.g.,
        associationsmapping, entitymapping, entitiesmapping,
        primarykeyfieldmapping, fieldmapping, foreignkeyfieldmapping,
        etc,
        """
        for map in self:
            if builtins.type(map) is type:
                yield map

    @property
    def all(self):
        ''' Returns a generator of all mapping objects including
        supermappings.
        '''
        for map in self:
            yield map

        for map in self.supermappings:
            yield map

    @property
    def supermappings(self):
        """ Returns a ``mappings`` collection containing all the
        mappings found from the superentity objects of ``self``.
        """
        if not self._supermappings:
            e = self.orm.entity.orm.super
            self._supermappings = mappings()

            while e:
                self._supermappings += e.orm.mappings
                e = e.orm.super

        return self._supermappings
            
    @property
    def orm(self):
        """ Returns the ``orm`` instance that this mappings collection
        corresponds to. This is the bridge between the ``mappings``
        collection and the entity it's associated with::

            e = self.orm.entity
            assert e.orm.mappings is self
        """
        return self._orm

    @property
    def aggregateindexes(self):
        ixs = aggregateindexes()
        for map in self:
            if type(map) in (fieldmapping, foreignkeyfieldmapping) and map.index:
                try:
                    ix = ixs[map.index.name]
                except IndexError:
                    ix = aggregateindex()
                    ixs += ix
                ix.indexes += map.index

        return ixs

    def getinsert(self):
        """ Returns a tuple whose first element is an INSERT INTO
        statement and whose second element is the parameterized
        arguments for the INSERT INTO. The combination is used by
        ``orm.entity.save`` to create a record in the database for the
        entity if one doesn't already exist. 
        
        Calling the method does not manipulate any data in the database;
        it simply returns the INSERT INTO statement and arguments, so
        it is safe to call for debugging or other, similar purposes.
        """

        # Get the table name
        tbl = self.orm.table

        # Get a list() of fieldmapping objects for the entity
        maps = [x for x in self if isinstance(x, fieldmapping)]

        # Build the field list of the INSERT INTO string
        flds = ', '.join('`%s`' % x.name for x in maps)

        # Create a string of placeholders (%s) so we can parameterize
        # the VALUES clause.
        placeholders = ', '.join(['%s'] * len(maps))

        # Build the INSERT INTO stirng including the field names and
        # VALUES parameters.
        sql = 'INSERT INTO %s (%s) VALUES (%s);'
        sql %= (tbl, flds, placeholders)

        # Get the args. These will be values from the entity's
        # attributes.
        args = self._getargs()

        # Add MySQL introducers (e.g., _binary) where necessary.
        sql = orm.introduce(sql, args)

        return sql, args

    def getupdate(self):
        """ Returns a tuple whose first element is an UPDATE statement
        and whose second element is the parameterized arguments for the
        UPDATE. The combination is used by ``orm.entity.save`` to update
        the record in the database for the entity if it ``isdirty``.
        
        Calling the method does not manipulate any data in the database;
        it simply returns the UPDATE statement and arguments, so
        it is safe to call for debugging or other, similar purposes.
        """
        set = ''
        for map in self:
            if isinstance(map, fieldmapping):
                if isinstance(map, primarykeyfieldmapping):
                    id = map.value.bytes
                else:
                    set += '`%s` = %%s, ' % (map.name,)

        set = set[:-2]

        # TODO Use f-string and textwrap to make this nicer
        sql = """UPDATE {}
SET {}
WHERE id = %s;
        """.format(self.orm.table, set)

        # Get the args. These will be values from the entity's
        # attributes.
        args = self._getargs()

        # Move the id value from the bottom to the top
        args.append(args.pop(0))

        # Add MySQL introducers (e.g., _binary) where necessary.
        sql = orm.introduce(sql, args)

        return sql, args

    def getdelete(self):
        """ Returns a tuple whose first element is an DELETE statement
        and whose second element is the parameterized arguments for the
        DELETE. The combination is used by ``orm.entity.save`` to delete
        the record in the database for the entity if it
        ``ismarkedfordeletion``.
        
        Calling the method does not manipulate any data in the database;
        it simply returns the DELETE statement and arguments, so
        it is safe to call for debugging or other, similar purposes.
        """
        sql = 'DELETE FROM {} WHERE id = %s;'.format(self.orm.table)

        args = self['id'].value.bytes,

        # Add _binary introducer to the id's binary value in the
        # string.
        sql = orm.introduce(sql, args)

        return sql, args

    def _getargs(self):
        """ Collect attribute values for the entity into a list for
        ``getupdate()`` and ``getinsert()``.
        """
        r = []
        for map in self:
            if isinstance(map, fieldmapping):
                keymaps = primarykeyfieldmapping, foreignkeyfieldmapping
                if type(map) in keymaps and isinstance(map.value, UUID):
                    r.append(map.value.bytes)
                else:
                    v = getattr(self.orm.instance, map.name)
                    v = None if v is undef else v
                    if v is not None:
                        if map.isdatetime:
                            v = v.replace(tzinfo=None)
                        elif map.isbool:
                            v = int(v)
                    r.append(v)
        return r

    def clone(self, orm_):
        """ Create a clone of the ``mappings`` collection. 
        """
        r = mappings(orm=orm_)

        r._nameix = dict()
        for map in self:
            map = map.clone()
            r += map
            r._nameix[map.name] = map

        # NOTE Set _populated after adding to `r` because the
        # oncountchange event will set self._populated to False
        r._populated = self._populated

        for map in r:
            map.orm = orm_

        return r

class mapping(entitiesmod.entity):
    """ An abstract class to map each entity's attributes to database
    fields.

    Promenent attributes of a ``mapping`` include ``name``, which is the
    name of the attribute being mapped and ``value`` which is the value
    of the attribute being mapped. 
    
    Concrete implementations include, primarykeyfieldmapping (for the
    ``id`` attribute/field), and foreignkeyfieldmapping (for foreign key
    mappings). ``fieldmapping`` maps the scalar attributes of a class to
    the database. Other classes such as ``entitiesmapping``,
    ``entitymapping`` and ``associationsmapping`` deal with the
    relationship between the ``entity`` and other ``entity`` objects and
    ``entities`` collections.
    """
   
    # A sequential number to indicate the order the mapping was
    # instatiated.
    ordinal = 0

    def __init__(self, name, isderived=False):
        """ Create a new ``mapping`` object. This is usually done in
        ``entitymeta.__new__`` or in ``mappings._populate``.

        :param: name str: The name of the mapping. This corresponds to
        the field name in the database and the attribute name in the
        entity.

        :param: isderived bool: If True, the mapping was created in the
        ``mappings._populate`` method. This implies that the mapping
        was derived from the _populate algorithm instead of being
        explictly declared by the ORM user.
        """
        self._name = name

        # Increment and assign the ordinal
        mapping.ordinal += 1
        self._ordinal = mapping.ordinal
        self.isderived = isderived

    def isdefined(self):
        """ Returns True if the value of the ``mapping`` has been set.

        Note that the ``undef`` class is used as the default setting for
        a ``mapping`` because a value of None represents a ``null``
        value in the database - which is considered a defined value.
        """
        return self._value is not undef

    @property
    def name(self):
        """ The name of the ``mapping``

        This is usually the name of the entity's attribute, and forms
        part of the database's column name.
        """
        return self._name

    @property
    def fullname(self):
        """ The fully qualified name of the mapping.
        """
        return '%s.%s' % (self.orm.table, self.name)

    @property
    def value(self):
        """ Returns the value that the mapping object holds.

        For most mappings objects, this will simply be the scalar value
        of an entity's attribute. For other subtypes, this would be an
        ``entity`` or ``entities`` object.
        """
        msg = 'Value should be implemented by the subclass'
        raise NotImplementedError(msg)

    @value.setter
    def value(self, v):
        """ Set's the value of the mapping object.
        """
        msg = 'Value should be implemented by the subclass'
        raise NotImplementedError(msg)

    @property
    def isloaded(self):
        """ Returns True if the mappings value has already been loaded
        from the database.
        """

        return self._value not in (None, undef)

    def clone(self):
        """ Clones the ``mapping`` object.
        """
        raise NotImplementedError('Abstract')

    @property
    def _reprargs(self):
        """ Returns the arguments to represent the mapping.
        """
        args = 'fullname="%s"'
        args %= self.fullname
        return args
        
    def __repr__(self):
        """ Return the representation of the mapping.
        """
        r = '%s(%s)'
        r %= (type(self).__name__, self._reprargs)
        return r

    def __str__(self):
        """ Return the representation of the mapping.
        """
        return repr(self)
    
class associationsmapping(mapping):
    """ Represents a mapping to an entity's ``associations`` collection.
    """
    def __init__(self, name, ass, isderived=False):
        """ Set initial values.
        """

        # Store a reference to the actual association class
        self.associations  =  ass
        self._value        =  None
        self._composite    =  None
        super().__init__(name, isderived)

    def clone(self):
        """ Return a new associationsmapping with same attribute values.
        """
        return associationsmapping(
            self.name, self.associations, self.isderived
        )

    @property
    def entities(self):
        """ Returns the association's collection class.
        """
        return self.associations

    @property
    def composite(self):
        """ Returns the composite (i.e., parent) of the associations
        collections.
        """
        return self._composite

    @composite.setter
    def composite(self, v):
        """ Sets the composite (i.e., parent) of the associations
        collections.
        """
        self._composite = v
        
    @property
    def value(self):
        """ Load and memoize the associations collection object that the
        this map represents.
        """

        # If self._value isn't set, go about setting it.
        if not self._value:
            maps = mappings()

            # Get the forign keys that correspond to the composite
            for map in self.associations.orm.mappings.foreignkeymappings:
                if map.entity is type(self.composite):
                    if self.associations.orm.isreflexive:
                        # If the association is reflexive, we want the
                        # subjective foreign key which corresponds to
                        # the composite's primary key.
                        if map.issubjective:
                            maps += map
                    else:
                        maps += map

            if maps.isempty:
                raise ValueError('Foreign key not found')

            # Create the where clause by disjunctivly joining the
            # foreign keys.
            wh = ' OR '.join([x.name + ' = %s' for x in maps])
            args = [self.composite.id] * maps.count

            # Create the association's collection
            asses = self.associations(wh, args)

            # Load the association if the composite is not new. If the
            # composite is new, there would be no existing associations
            # for it to load.
            if not self.composite.orm.isnew:
                # NOTE Currently, we defer loading entities and
                # association.  However, we will want to continue
                # immediate loading this association here for the sake
                # of predictablity.
                asses.orm.collect()

            # Make sure the associations collection knows it's composite
            asses.orm.composite = self.composite

            # Memoize. Using the setter here ensures that self._setvalue
            # gets called.
            self.value = asses

        return self._value

    @value.setter
    def value(self, v):
        """ Sets the associations collection object that this mapping
        represents.
        """
        self._setvalue('_value', v, 'value')

    @property
    def _reprargs(self):
        """ Returns the interpolation arguments for this object's
        __repr__ method. See ``mapping.__repr__``.
        """
        args = super()._reprargs
        args += ', isloaded=%s' % self.isloaded
        return args

class entitiesmapping(mapping):
    """ Represents a mapping to an entity's ``entities`` collection.

    This mapping's value contains the constituents of an entity::

        # Load an artist
        art = artists(artid)

        # Get the presentations belonging to the ``art`` entity.  The
        # ``presentations`` are the constituents of ``art``, and the
        # ``presentations`` collection objects stored in the
        # ``entitiesmapping```s ``value`` property.
        press = art.presentations
    """

    def __init__(self, name, es):
        """ Set the name and the ``entities`` class reference for the
        mappings.

        :param: name str: The name of the attribute that holds the
        constituent. For example::

            class presentations(orm.entities):
                pass

            class artist(orm.entity):
                presentations = presentations

        The presentation attribute of ``artist`` would be named
        'presentations' here to reference the collection.

        :param: es type: A reference to the entities class. In the
        example given for the ``name`` parameter, ``es`` would be a
        reference to the ``presentations`` class (not a instance of
        that class).
        """
        self.entities = es
        self._value = None
        super().__init__(name)

    @property
    def value(self):
        """ Return the entities collection object that this
        entitiesmapping represents.
        """
        return self._value

    @value.setter
    def value(self, v):
        """ Set the entities collection object that this entitiesmapping
        represents.
        """
        self._setvalue('_value', v, 'value')

    @property
    def _reprargs(self):
        """ Returns the interpolation arguments for this object's
        __repr__ method. See ``mapping.__repr__``.
        """
        args = super()._reprargs
        args += ', isloaded=%s' % self.isloaded
        return args

    def clone(self):
        """ Return a new ``entitiesmapping`` with the same values as
        this one. 
        """
        return entitiesmapping(self.name, self.entities)

class entitymapping(mapping):
    """ Represents a mapping to another entity.
    """

    def __init__(self, name, e, isderived=False):
        """ Sets the initial values.

        :param: str name: The name of the map

        :param: entity e: The entity class associatied with this map

        :param: bool isderived: Indicates whether or not the map was
        created/derived by the mappings._populate() method
        """
        self.entity = e
        self._value = None
        super().__init__(name, isderived)

    @property
    def issubjective(self):
        """ Returns True if the mapping is for the subjective side of a
        reflexive association; False otherwise.
        """
        return self.orm.isreflexive \
               and self.name.startswith('subject') 

    @property
    def isobjective(self):
        """ Returns True if the mapping is for the objective side of a
        reflexive association; False otherwise.
        """
        return self.orm.isreflexive \
               and self.name.startswith('object') 

    @property
    def isproprietor(self):
        """ Returns True if the ``entity`` being referenced is the
        proprietor (``party.party``) object that each ``entity`` object
        has. Returns False otherwise.
        """
        return self.name == 'proprietor'

    @property
    def isowner(self):
        return self.name == 'owner'

    @property
    def value(self):
        """ Return the ``entity`` instance for this ``entitymapping``.
        If the ``entity`` hasn't been loaded, the foreign key for the
        entity will be used to load the entity. If the foreign key has
        no value, the entity will not be loaded and None will be return.
        Otherwise, the entity will be loaded, returned and memozied so
        subsequent calls won't result in a reload.
        """

        if not self._value:
            # Look for the foreign key for this entity. If it has a
            # value, use that value to load the entity object. If the
            # foreign key for this entity has no value, then we can't
            # load the entity so we will just return None.
            for map in self.orm.mappings.foreignkeymappings:

                # Here we are trying to make sure that the correct map
                # is selected since doing a simple type test (like the
                # one below) is insufficient because reflexive maps will
                # have two mappings with the same type.
                if (
                    self.orm.isreflexive
                    and not map.name.startswith(self.name + '__')
                ):
                    continue

                # If the given foreign key is mapped to the entity
                # corresponding to self...
                if map.entity is self.entity:

                    # The FK must be an owner map if self is an owner
                    # map.
                    if map.isowner != self.isowner:
                        continue
                    
                    # ... and if we have a foreign key value 
                    if map.value not in (undef, None):
                        
                        # ... then we can load the entity using the
                        # foreign key's value
                        self._value = self.entity(map.value)

        return self._value

    @value.setter
    def value(self, v):
        """ Set the entity.
        """
        self._setvalue('_value', v, 'value')

    def clone(self):
        """ Return a new entitymapping object with the same values as
        this one.
        """
        return entitymapping(
            self.name, self.entity, isderived=self.isderived
        )

    @property
    def _reprargs(self):
        """ Returns the interpolation arguments for this object's
        __repr__ method. See ``mapping.__repr__``.
        """
        args = super()._reprargs
        args += ', isloaded=%s' % self.isloaded
        return args

class aggregateindexes(entitiesmod.entities):
    pass

class aggregateindex(entitiesmod.entity):
    def __init__(self):
        self.indexes = indexes()

    @property
    def name(self):
        return self.indexes.first.name

    @property
    def isfulltext(self):
        return type(self.indexes.first) is fulltext

    def __str__(self):
        self.indexes.sort('ordinal')

        ixtype = 'FULLTEXT' if self.isfulltext else 'INDEX'
        r = '%s %s (' % (ixtype ,self.name)
        for i, ix in enumerate(self.indexes):
            r += (', ' if i else '') + ix.map.name

        r += ')'

        return r
            
class indexes(entitiesmod.entities):
    """ A collection of indexes. See ``index`` for more.
    """

class index(entitiesmod.entity):
    """ The ``index`` class is used by entity declarations to specify
    that a database index should be applied by the mapping::
        
        class artist(orm.entity):
            ssn = str, orm.index

        CREATE = '''
            CREATE TABLE `main_artists`(
                `id` binary(16) primary key,
                `proprietor__partyid` binary(16),
                `createdat` datetime(6),
                `updatedat` datetime(6),
                `ssn` varchar(255),
                INDEX proprietor__partyid_ix
                (proprietor__partyid),
                INDEX ssn_ix (ssn)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

        # Notice that the artist's CREATE TABLE  DDL has the line:
        #
        #     INDEX ssn_ix (ssn)
        #
        # Adding the orm.index in the entity declaration ensures we have
        # a database index for this field
        #
        # assert artist.orm.createtable ==  CREATE

    """
    def __init__(self, name=None, ordinal=None):
        """ Initialize the index.

        :param: name str: The name of the index

        :param: name ordinal: The order the index comes in.
        """
        self._name = name
        self.ordinal = ordinal
        self.map = None

    @property
    def name(self):
        """ The name of the database index.
        """
        name = self._name if self._name else self.map.name

        name = name if name.endswith('_ix') else name + '_ix'

        return name

    def __str__(self):
        """ Strung indexes are the index's name.
        """
        return self.name
    
    def __repr__(self):
        """ A string representation of the index.
        """
        return super().__repr__() + ' ' + self.name

class fulltexts(indexes):
    """ A collection of fulltext objects.
    """

class fulltext(index):
    """ Represents a MySQL FULLTEXT index.
    """
    @property
    def name(self):
        """ Returns the name of the FULLTEXT index.
        """

        name = self._name if self._name else self.map.name

        name = name if name.endswith('_ftix') else name + '_ftix'

        return name

class attr:
    """ This class makes imperitive attributes possible. 

    Most attributes for orm.entity classes are declaritive::

        class artist(orm.entity):
            firstname = str

    The value of ``artist.firstname`` can be set or retrieved. However,
    there is no getter or setter for the ``firstname`` attribute. 

    Getters
    -------

    To create a getter, we can use the ``attr`` class like so::

        class artist(orm.entity):
            @orm.attr(str):
            def firstname(self):
                return attr().capitalize()

    The above getter ensures that ``firstname`` will always return a
    capitalized value::

        art = artist()
        art.name = 'pablo'

        assert 'Pablo' == art.name

    Note the attr() function within the getter. This function returns
    the underlying value that the getter or setter is working with. In
    the above getter, the following is True::
        
        assert 'pablo' == attr()

    We can use the attr() function to set the underlying value. For
    example, the above getter could have been written like this.

        class artist(orm.entity):
            @orm.attr(str):
            def firstname(self):
                # Get the underlying value
                fname = attr()

                if not fname[0].isupper():
                    
                    # Capitalize it.
                    fname = fname.capitalize()

                    # Set the underlying value to the capitalized
                    # version. The next time this getter is called, we
                    # won't have to capitalize the attribute again.
                    attr(fname)

                # Return the capitalized version
                return fname

    The attr() Function
    -------------------

    This is much more verbose, but it illustrates some concepts. The
    attr() function retrieves the underlying value when no arguments are
    passed into it. If an argument is passed in, it will change the
    underlying value to that argument. 
    
    Using attr() to set the underlying value may be useful in cases
    where computing the value is expensive and we only want to do it once.
    Memoizing the underlying value can allow us to store the computed
    value for later retrieval. In the above case, we only would have to
    capitalize fname once. Capitalization is, of course, inexpensize,
    but if it were expensive, this technique could provide a performance
    boost.

    Database-friendly getters
    -------------------------

    Since the attribute returns the value that will be stored in the
    database, getters can be used to prepare the data for storage. For
    example, if you have a class that stored IP addresses, you could use
    the getter to return a byte representation of the IP address for
    effecient storage in the database::

        class ip(orm.entity{
            @orm.attr(bytes):
            def address(self):
                
                # Use Python's ipaddress module
                import ipaddress

                # Use the str value of the ip address to create an
                # IPv4Address object.
                ip = ipaddress.IPv4Address(attr())

                # Return the binary representation of this address
                return ip.packed

        ipv4 = ip()
        ipv4.address = '127.0.0.1'
        assert ipv4.address == b'\x7f\x00\x00\x01'

    The above illustrates that th ip.address value returns a binary
    representation of the IP address. This may be good for the database,
    but would be awful for the user who would expect a normal, str
    representation of the IP address when calling the .address
    attribute. Some more work would need to be done on the above class
    in order to satisfy the user's expectations while optimizing IP
    address persistence.

    Setters
    -------
    Creating imperitive setters is as easy as creating getters. You only
    need to specify a `v` as the first argument of the setter to
    indicate that it is such::

        class artist(orm.entity):
            @orm.attr(str):
            def firstname(self, v):
                v = v.capitalize()
                attr(v)

    Now the capitalization work is done during the setting of the
    firstname attribute instead of when getting data from the
    attribute. The code seems to work the same as the getter code above
    as far as the user is concerned.

        art = artist()
        art.name = 'pablo'

        assert 'Pablo' == art.name
                
    """
    def __init__(self, *args, **kwargs):
        """ Creates an attr decorator::

            class artist(orm.entity):
                @orm.attr(str):
                def name(self):
                    return attr()

        In the above, the ``str`` class is passed in as ``args[0]``.
        The above is equivalent to 

            class artist(orm.entity):
                name = str

        Any ORM type can be passed in just the same way they are
        notated in a class declaration. For example, the two statements
        are equivalent::

            class artist(orm.entity):
                @orm.attr(float, 5, 1)
                def width(self):
                    return attr()

        and

            class artist(orm.entity):
                width = float, 5, 1

        """
        self.args = list(args)
        self.kwargs = kwargs

    def __call__(self, meth):
        """ This method is invoked when the imperitive attribute is
        called. The ``meth`` argument passed in is the actual getter or
        setter that must be called. The ``meth`` is first wrapped by
        attr.wrap and returned to the caller. The caller then invokes
        the wrapped getter/setter.
        """
        self.args.append(meth)
        w = attr.wrap(*self.args, **self.kwargs)
        return w

    def attr(v=undef):
        """ Sets the map's value to ``v``. Returns the mapped
        value.

        This function is injected into imperitive attributes to
        provide easy access to the attributes mapping value.
        """
        if v is undef:
            try:
                return e.orm.mappings[name].value
            except IndexError:
                # If it's not in the subentity's mapping
                # collection, make a regular getattr() call on
                # e's super. 
                # TODO s/super/sup
                super = e.orm.super # :=
                if super:
                    return getattr(super, name)
        else:
            e.__setattr__(name, v, cmp=False, imp=True)
            return v

    class AttributeErrorWrapper(Exception):
        """ An AttributeError wrapper. """
        def __init__(self, ex):
            self.inner = ex

    class wrap:
        """ A decorator to make a method an imperitive attribute. 
        """
        def __init__(self, *args, **kwargs):
            args = list(args)
            self.fget = self.fset = None

            # Get the setter/getter method
            f = args.pop()

            # Get the methods paramter list
            params = f.__code__.co_varnames
            params = params[:f.__code__.co_argcount]

            # If a 'v' parameter is one of the parameters:
            if 'v' in params:
                # ... then it must be a setter. The 'v' argument
                # contains the *value* that will be assigned to the
                # attribute.
                self.fset = f
            else:
                # ... then it must be a getter.
                self.fget = f

            self.args = args
            self.kwargs = kwargs

        @property
        def mapping(self):
            """ Returns an mapping for the imperitive attribute.

            For example, in the below entity declaration, a
            ``fieldmapping`` would be returned for the `mime` property.

                class file(inode):
                    @orm.attr(str)
                    def mime(self):
                        return attr()

            """
            if entity in self.args[0].mro():
                map = entitymapping(self.fget.__name__, self.args[0])
            elif entities in self.args[0].mro():
                # NOTE Untested
                map = entitiesmapping(k, v)
            else:
                map = fieldmapping(*self.args, **self.kwargs)

            # TODO Make isexplicit a @property. It's now redundant with
            # isgetter and issetter.
            map.isexplicit = True
            map.isgetter = bool(self.fget)
            map.issetter = bool(self.fset)
            return map

        def _getset(self, instance, owner=None, value=undef):
            """ Ultimately invokes the explicity attribute setter or
            getter.
            """
            isget = value is undef
            isset = not isget
                
            if isget:
                meth = self.fget
            elif isset: 
                meth = self.fset

            # Inject global variable values into the attr() function
            attr.attr.__globals__['name']  =  meth.__name__
            attr.attr.__globals__['e']     =  instance

            # Inject attr() reference into user-level imperitive attribute
            meth.__globals__['attr'] = attr.attr

            try:
                # Invoke the imperitive attribute
                if isget:
                    return meth(instance)
                elif isset:
                    return meth(instance, value)

            except builtins.AttributeError as ex:
                # If it raises an AttributeError, wrap it. If the call
                # from e.__getattribute__ sees a regular AttributeError,
                # it will ignore it because it will assume its caller is
                # requesting the value of a mapping object.
                raise sys.modules['orm'].attr.AttributeErrorWrapper(ex)
            
        def __get__(self, instance, owner=None):
            """ Invoked when an explicit attribute is called. The
            explicit method is then invoked and its value is returned by
            this function. (See Python descriptors protocol for more.)
            """
            return self._getset(instance=instance, owner=owner)

        def __set__(self, instance, value):
            """ Invoked when an explicit attribute is set. The
            explicit method is then invoked and its value is returned by
            this function. (See Python descriptors protocol for more.)
            """
            return self._getset(instance=instance, value=value)

class fieldmapping(mapping):
    """ Represents mapping between Python types and MySQL types.

    ``fieldmappings`` represents the standard scalar types that all
    entity classes have, such as str, int, bool, date, etc. These types,
    taken with contraints such as the ``min``, ``max``, ``precision``

    fieldmappings objects are created on entity declaration and added to
    the entity's orm.mappings collection::

        class engineer(orm.entity):
            name = str
            bio = str, orm.fulltext

        name_map = engineer.orm.mappings['name']
        bio_map = engineer.orm.mappings['bio']

        assert type(name_map) is fieldmapping
        assert type(bio_map) is fieldmapping

        assert name_map.name == 'name'
        assert bio_map.name == 'bio'

    The above example would work the same if with an instance of
    ``engineer`` rather than a class reference::

        eng = engineer()
        name_map = eng.orm.mappings['name']
        bio_map = eng.orm.mappings['bio']

        assert type(name_map) is fieldmapping
        assert type(bio_map) is fieldmapping

        assert name_map.name == 'name'
        assert bio_map.name == 'bio'

    """

    # TODO Capitalize ``types``
    # Permitted types
    types = bool, str, int, float, decimal.Decimal, bytes, datetime, date

    def __init__(self, 
            type,            min=None,         max=None,
            m=None,          d=None,           name=None,
            ix=None,         isderived=False,  isexplicit=False,
            isgetter=False,  issetter=False,   span=None
    ):
        """ Creates a fieldmapping.

        :param: type int: The type of the field (str, date, bool, etc)

        :param: min int: The minimum length or size of the field

        :param: max int: The maximum length or size of the field

        :param: m int: The precision (for decimal and float types)

        :param: d int: The scale (for decimal and float types)

        :param: name str: The name of the field.

        :param: ix orm.index: The index object the class corresponds to

        :param: isderived bool: If True, the field was created in
        ``mappings._populate``. 

        :param: isexplicit bool: <To be removed>

        :param: isgetter bool: Indicates the mapping is for an
        imperitive getter.

        :param: issetter bool: Indicates the mapping is for an
        imperitive setter.

        :param: span span: A ``timespan`` or a ``datespan`` reference.
        """

        if hasattr(type, 'mro') and alias in type.mro():
            type, min, max = type()

        if type in (float, decimal.Decimal):
            if min is not None:
                m, min = min, None
            if max is not None:
                d, max = max, None
        
        # Assign arguments to fields 
        self._type       =  type
        self._value      =  undef
        self._min        =  min
        self._max        =  max
        self._precision  =  m
        self._scale      =  d
        self.isexplicit  =  isexplicit
        self.isgetter    =  isgetter
        self.issetter    =  issetter
        self._span       =  span

        # TODO Currently, a field is limited to being part of only one
        # composite or fulltext index. This code could be improved to
        # allow for multiple indexes per fieldmapping.
        if ix is not None                and \
           isinstance(ix, builtins.type) and \
           index in ix.mro():

            self._ix = ix()
        else:
            self._ix = ix

        if self.index:
            self.index.map = self

        super().__init__(name, isderived)

    @property
    def column(self):
        """ Return a database column object for the fieldmapping.

        :rtype: db.column
        """
        # NOTE This should probably be rewritten like this:
        #
        #     return db.column(self)

        col = db.column()
        col.name = self.name
        col.dbtype = self.definition
        return col

    def clone(self):
        """ Returns a new fieldmapping with the same attributes as self.
        """
        ix = self.index

        ix = type(ix)(name=ix.name, ordinal=ix.ordinal) if ix else None

        map = fieldmapping(
            self.type,       self.min,        self.max,
            self.precision,  self.scale,      self.name,
            ix,              self.isderived,  self.isexplicit,
            self.isgetter,   self.issetter,   self.span,
        )

        if ix:
            ix.map = map

        map._value = self._value

        return map

    @property
    def span(self):
        """ Returns the datespan or timespan object associated with this
        field. The self.type property would have to be a date or
        datetime respectively.
        """
        return self._span

    @property
    def _reprargs(self):
        """ Returns the interpolation arguments for this object's
        __repr__ method. See ``mapping.__repr__``.
        """
        args = super()._reprargs
        args  +=  ',  type=%s'        %  str(self.type)
        args  +=  ',  ix=%s'          %  str(self.index)
        args  +=  ',  value=%s'  %  str(self.value)
        return args

    @property
    def index(self):
        """ Return the index object associated with this fieldmapping.

        For example, in the following class declaration, the
        orm.fulltext reference would be the index:

            class engineer(orm.entity):
                bio = str, orm.fulltext

            map = engineer.orm.mappings['bio']
            assert map.index is orm.fulltext
        """
        return self._ix

    @property
    def isstr(self):
        """ Returns True if the mapping represents a str type.
        """
        return self.type == types.str

    @property
    def isdatetime(self):
        """ Returns True if the mapping represents a datetime type.
        """
        return self.type == types.datetime

    @property
    def isdate(self):
        """ Returns True if the mapping represents a date type.
        """
        return self.type == types.date

    @property
    def isbool(self):
        """ Returns True if the mapping represents a bool type.
        """
        return self.type == types.bool

    @property
    def isint(self):
        """ Returns True if the mapping represents a int type.
        """
        return self.type == types.int

    @property
    def isfloat(self):
        """ Returns True if the mapping represents a float type.
        """
        return self.type == types.float

    @property
    def isdecimal(self):
        """ Returns True if the mapping represents a decimal type.
        """
        return self.type == types.decimal

    @property
    def isbytes(self):
        """ Returns True if the mapping represents a bytes type.
        """
        return self.type == types.bytes

    @property
    def isfixed(self):
        """ Returns True if the mapping represents a fixed-sized type.

        An example of a fixed-sized type would be a CHAR type in a
        database::

            CREATE TABLE mytable(
                phone_number CHAR(10)
            );

        However, numeric types such as int's floats and decimals are
        considered fixed-size as well.
        """
        if self.isint or self.isfloat or self.isdecimal:
            return True

        if self.isbytes or self.isstr:
            return self.max == self.min
        return False

    @property
    def min(self):
        """ Return the min (minimum) value for the fieldmapping.

        The min value is the second argument given in the attribute
        declaration of an entity::

        Minimum for numeric types refers to the minimum value the
        attribute can have, while minimum values for str refer to the
        minimum length allowable.

            class artist(orm.entity):
                weight  =  int,  0,  1000
                bio     =  str,  1,  4000

        In the above, the minimum **value** for weight is 0, while the
        minimum **length** for ``bio`` is 1 character.
        """

        if self.isstr:
            # By default, a str can have 1 or more characters (and can
            # be null).
            if self._min is None:
                return 1

        elif self.isint:
            if self._min is None:
                return -2147483648

        elif self.isfloat:
            if self._min is None:
                return -self.max
            else:
                return float(self._min)

        elif self.isdecimal:
            if self._min is None:
                return -self.max
            else:
                return decimal.Decimal(self._min)

        elif self.isdatetime:
            ... # TODO?
        elif self.isbytes:
            ... # TODO?

        return self._min

    @property
    def precision(self):
        """ Return the precision value for the fieldmapping.

        The precision represents the number of significant digits that
        are stored for values. It is usually paried with a scale (see
        fieldmapping.scale) which represents the number of digits that
        can be stored following the decimal point.

        Scale applied to floats, decimal and date types.

        For datetime fieldmappings, this is 6 because in MySQL:
            > A DATETIME or TIMESTAMP value can include a trailing
            > fractional seconds part in up to microseconds (6 digits)
            > precision.

        For floats, the precision value is the second argument in an
        attribute declaration. In the example below, 8 is the precision
        of float::

            class component(orm.entity):
                weight  =  float,  8,   7
        """
        if not (self.isfloat or self.isdecimal, self.isdatetime):
            return None

        if self.isdatetime:
            return 6

        if self._precision is None:
            return 12

        return self._precision

    @property
    def scale(self):
        """ Return the scale of the fieldmapping.

        The scale represents the number of digits that can be stored
        following the decimal point. It is usually paired with the
        precision (see fieldmapping.precision) which represents the
        number of significant digits that are stored for values. 

        Scale applied to floats and decimals.
        """
        if not (self.isfloat or self.isdecimal):
            return None

        if self._scale is None:
            return 2

        return self._scale
        
    @property
    def max(self):
        """ For str types, returns the maximum number of characters the
        fieldmapping will allow. For numeric types, returns the highest
        value the fieldmapping will allow.
        """
        t = self.type
        if self.isstr:
            if self._max is None:
                return 255
            else:
                return self._max

        elif self.isint:
            if self._max is None:
                return 2147483647
            else:
                return self._max

        elif self.isfloat or self.isdecimal:
            m, d = self.precision, self.scale
            str = '9' * m
            str = '%s.%s' % (str[:m-d], str[:d])
            return float(str) if self.isfloat else decimal.Decimal(str)

        elif t is types.bytes:
            if self._max is None:
                return 255
            return self._max

    @property
    def type(self):
        """ Returns an integer representing the type (str, bool, etc)
        for the fieldmapping. The values returned correspond to the
        ``orm.types`` enum.
        """
        
        t = self._type
        if t in (str, types.str):
            return types.str
        elif t in (int, types.int):
            return types.int
        elif t in (bool, types.bool):
            return types.bool
        elif hasattr(t, '__name__') and t.__name__ == 'datetime':
            return types.datetime
        elif hasattr(t, '__name__') and t.__name__ == 'date':
            return types.date
        elif t in (float,):
            return types.float
        elif hasattr(t, '__name__') and t.__name__.lower() == 'decimal':
            return types.decimal
        elif t in (bytes,):
            return types.bytes
        return self._type

    @property
    def signed(self):
        """ Returns True if the numeric fieldmapping is allowed to be a
        negative (signed) value. If the fieldmapping is non-numeric, a
        ValueError is raised.
        """
        if self.type not in (types.int, types.float, types.decimal):
            raise ValueError()

        return self.min < 0
    
    @property
    def dbtype(self):
        """ Returns a string representing the MySQL data type
        corresponding to this field mapping e.g., 'varchar', 'datetime',
        'bit', 'tinyint', 'smallint unsigned', etc.

        This is similar to the ``definition`` property, however dbtype
        only returns the name of the database type in string form. The
        precision, scale and size are not included.
        """
        if self.isstr:
            if self.max <= 4000:
                if self.isfixed:
                    return 'char'
                else:
                    return 'varchar'
            else:
                return 'longtext'

        elif self.isint:
            if self.min < 0:
                if    self.min  >=  -128         and  self.max  <=  127:
                    return 'tinyint'
                elif  self.min  >=  -32768       and  self.max  <=  32767:
                    return 'smallint'
                elif  self.min  >=  -8388608     and  self.max  <=  8388607:
                    return 'mediumint'
                elif  self.min  >=  -2147483648  and  self.max  <=  2147483647:
                    return 'int'
                elif  self.min  >=  -2**63       and  self.max  <=  2**63-1:
                    return 'bigint'
                else:
                    raise ValueError()
            else:
                if self.max  <=  255:
                    return 'tinyint unsigned'
                elif self.max  <=  65535:
                    return 'smallint unsigned'
                elif self.max  <=  16777215:
                    return 'mediumint unsigned'
                elif self.max  <=  4294967295:
                    return 'int unsigned'
                elif self.max  <=  (2 ** 64) - 1:
                    return 'bigint unsigned'
                else:
                    raise ValueError()
        elif self.isdatetime:
            return 'datetime'
        elif self.isdate:
            return 'date'
        elif self.isbool:
            return 'bit'
        elif self.isfloat:
            return 'double'
        elif self.isdecimal:
            return 'decimal'
        elif self.isbytes:
            if self.isfixed:
                return 'binary'
            else:
                return 'varbinary'
        else:
            raise ValueError()

    @property
    def definition(self):
        """ Returns a string representing the MySQL data type
        corresponding to this field mapping e.g., varchar(255),
        datetime(6) bit, tinyint, etc. 
        """
        if self.isstr:
            # NOTE Setting the varchar max to 16,383 can cause issues
            # for larger strings such as `bio1 = str, 1, 16382`.  The
            # following may be thrown for this string on table creation:
            #
            #     _mysql_exceptions.OperationalError: (1118, 'Row size
            #     too large. The maximum row size for the used table
            #     type, not counting BLOBs, is 65535. This includes
            #     storage overhead, check the manual. You have to change
            #     some columns to TEXT or BLOBs')
            #
            # For the moment, let's set the maximum varchar to 4000
            # (which is the same as that of MS SQL Server's nvarchar). 
            #
            # In the future, we may want to calculate the row size before
            # creating the table. We can then use that value to help the
            # user understand what can be done to correct the size
            # issue.
            if self.max <= 4000:
                if self.isfixed:
                    return 'char(' + str(self.max) + ')'
                else:
                    return 'varchar(' + str(self.max) + ')'
            else:
                return 'longtext'

        elif self.isint:
            if self.min < 0:
                if    self.min  >=  -128         and  self.max  <=  127:
                    return 'tinyint'
                elif  self.min  >=  -32768       and  self.max  <=  32767:
                    return 'smallint'
                elif  self.min  >=  -8388608     and  self.max  <=  8388607:
                    return 'mediumint'
                elif  self.min  >=  -2147483648  and  self.max  <=  2147483647:
                    return 'int'
                elif  self.min  >=  -2**63       and  self.max  <=  2**63-1:
                    return 'bigint'
                else:
                    raise ValueError()
            else:
                if self.max  <=  255:
                    return 'tinyint unsigned'
                elif self.max  <=  65535:
                    return 'smallint unsigned'
                elif self.max  <=  16777215:
                    return 'mediumint unsigned'
                elif self.max  <=  4294967295:
                    return 'int unsigned'
                elif self.max  <=  (2 ** 64) - 1:
                    return 'bigint unsigned'
                else:
                    raise ValueError()
        elif self.isdatetime:
            return 'datetime(6)'
        elif self.isdate:
            return 'date'
        elif self.isbool:
            return 'bit'
        elif self.isfloat:
            return 'double(%s, %s)' % (self.precision, self.scale)
        elif self.isdecimal:
            return 'decimal(%s, %s)' % (self.precision, self.scale)
        elif self.isbytes:
            if self.isfixed:
                return 'binary(%s)' % self.max
            else:
                return 'varbinary(%s)' % self.max
        else:
            raise ValueError()

    @property
    def value(self):
        """ Return the scalar value held by the fieldmapping object.
        """

        # If _value hasn't been set, use Pythonic defaults
        if self._value is undef:
            if self.isint:
                return int()
            elif self.isbool:
                return bool()
            elif self.isfloat:
                return float()
            elif self.isdecimal:
                return decimal.Decimal()
            elif self.isstr:
                return str()
            elif self.isbytes:
                return bytes()
            else:
                return None
        
        # Ensure the value is coerced to the correct type using standard
        # Pythonic type coersion, e.g., assert '1.0' == str(1.000)
        if self._value is not None:
            if self.isstr:
                try:
                    self._value = str(self._value)
                except:
                    # If coersion fails, self._value will be a reference
                    # to the `undef` class and will be considered
                    # invalid by by brokenrules.
                    pass

            elif self.isdatetime:
                try:
                    # Favor primative.datetime over Python's default
                    # datetime since it is our customized override of
                    # Python's datetime object.
                    if type(self._value) is str:
                        self._value = primative.datetime(self._value) 
                    elif not isinstance(self._value, primative.datetime):
                        self._value = primative.datetime(self._value)
                except:
                    pass
                else:
                    utc = dateutil.tz.gettz('UTC')
                    if self._value.tzinfo and self._value.tzinfo is not utc:
                        self._value = self._value.astimezone(utc)
                    else:
                        self._value = self._value.replace(tzinfo=utc)
 
            elif self.isdate:
                try:
                    if type(self._value) is str:
                        self._value = primative.date(self._value) 
                    elif not isinstance(self._value, primative.date):
                        self._value = primative.date(self._value)
                except:
                    pass

            elif self.isbool:
                if type(self._value) is bytes:
                    # Convert the bytes string from MySQL's byytes type
                    # to a bool.
                    v = self._value
                    self._value = bool.from_bytes(v, byteorder='little')

            elif self.isint:
                try:
                    self._value = int(self._value)
                except:
                    pass
            elif self.isfloat:
                try:
                    self._value = round(float(self._value), self.scale)
                except:
                    pass

            elif self.isdecimal:
                try:
                    d = decimal.Decimal(str(self._value))
                except:
                    pass
                else:
                    self._value = round(d, self.scale)

            elif self.isbytes:
                try:
                    self._value = bytes(self._value)
                except:
                    pass

        return self._value

    @value.setter
    def value(self, v):
        """ Set the fieldmapping's value property.
        """
        self._value = v

class foreignkeyfieldmapping(fieldmapping):
    """ Represents a fieldmapping to a foreign key.
    """
    def __init__(self, e, fkname=None, isderived=False):
        """ Create a foreignkeyfieldmapping object.

        :param: e type: A reference to the composite entity class.

        :param: fkname str: The name of the entity mapping that this map
        corresponds.

        :param: isderived bool: If True, the mapping was created in the
        ``mappings._populate`` (it seems this is always the case,
        actually).
        """
        # TODO Rename fkname to name, and _fkname to _name. Note that
        # _name already exists; it's inherited from `mapping`, but I
        # don't think that's a probably for the rename.

        self.entity = e
        self._fkname = fkname
        self.value = None
        super().__init__(
            type=types.fk, 
            isderived=isderived,
            ix=index
        )

    @property
    def isowner(self):
        """ Returns True if the mapping is the foreign key referencing
        the ``owner`` (ecommerce.user) entity.
        """

        return self.name == 'owner__userid'

    @property
    def name(self):
        """ Returns the name of the foreign key column.
        """
        # TODO:055e5c02 make FK name's fully qualified. grep 055e5c02
        # for more.

        if self._fkname:
            return '%s__%s' \
                % (self._fkname, self.entity.__name__ + 'id')

        return self.entity.__name__ + 'id'

    @property
    def isproprietor(self):
        """ Return True if this foreign key mapping references the
        record's proprietor; False otherwise.
        """
        return self.name == 'proprietor__partyid'

    @property
    def fkname(self):
        """ Return the name of the entity mapping that this map
        corresponds. """
        return self._fkname

    def clone(self):
        """ Return a new foreignkeyfieldmapping with the same properties
        as this foreignkeyfieldmapping.
        """
        return foreignkeyfieldmapping(self.entity, self._fkname, self.isderived)

    @property
    def issubjective(self):
        """ Return True if this foreignkeymapping references the
        subjective side of a reflexive ``orm.association``.
        """
        return self.orm.isreflexive \
               and self.name.startswith('subject__') 

    @property
    def isobjective(self):
        """ Return True if this foreignkeymapping references the
        objective side of a reflexive ``orm.association``.
        """
        return self.orm.isreflexive \
               and self.name.startswith('object__') 

    @property
    def dbtype(self):
        """ The type of a foreign key will always be a 16 byte value
        (the binary representation of a version 4 UUID). Therefore, the
        database type will be ``binary``.
        """
        return 'binary'

    @property
    def definition(self):
        """ The type of a foreign key will always be a 16 byte value
        (the binary representation of a version 4 UUID). Therefore, the
        database type will be ``binary`` with a fixed-width of 16 bytes.
        """
        return 'binary(16)'

    @property
    def value(self):
        """ Return a version 4 UUID object representing the foreign
        key's value.
        """
        if type(self._value) is bytes:
            # Coerce the value to a UUID object for convenience.
            self._value = UUID(bytes=self._value)
            
        return self._value

    @value.setter
    def value(self, v):
        """ Set the foreign key's value.

        :param: v bytes|UUID: The value to set the foreign key to.
        """
        self._value = v

class primarykeyfieldmapping(fieldmapping):
    """ Represents a fieldmapping to a primary key (the entity's ``id``
    attribute).
    """

    def __init__(self):
        """ Instatiate.
        """

        # Ensure the type is `types.pk` (primary key).
        super().__init__(type=types.pk)

    @property
    def name(self):
        """ Return the database name of the primary key.

        This will always be 'id'.
        """
        return 'id'

    def clone(self):
        """ Return a new primarykeyfieldmapping with the same properties
        as this primarykeyfieldmapping.
        """
        return primarykeyfieldmapping()

    @property
    def dbtype(self):
        """ The type of a primary key will always be a 16 byte value
        (the binary representation of a version 4 UUID). Therefore, the
        database type will be ``binary``.
        """
        return 'binary'

    @property
    def definition(self):
        """ The type of a primary key will always be a 16 byte value
        (the binary representation of a version 4 UUID). Therefore, the
        database type will be ``binary`` with a fixed-width of 16 bytes.
        """
        return 'binary(16) primary key'

    @property
    def value(self):
        """ Return a version 4 UUID object representing the primary
        key's value.
        """

        # If a super instance exists, use that because we want a
        # subclass and its super class to share the same id. Here we use
        # ._super instead of .super because we don't want to invoke the
        # super accessor because it calls the id accessor (which calls
        # this accessor) - leading to infinite recursion. This, of
        # course, assumes that the .super accessor has previously been
        # called.

        sup = self.orm._super
        if sup:
            return sup.id

        if type(self._value) is bytes:
            # Coerce the value to a UUID object for convenience.
            self._value = UUID(bytes=self._value)

        return self._value

    @value.setter
    def value(self, v):
        """ Set the foreign key's value.

        :param: v bytes|UUID: The value to set the foreign key to.
        """
        self._value = v

        sup = self.orm._super
        if sup:
            sup.id = v

class ormclasseswrapper(entitiesmod.entities):
    """ A collection of ormclasswrapper objects.
    """
    def append(self, obj, uniq=False, r=None):
        """ Add an wrapped orm class to the collection.
        """
        if isinstance(obj, type):
            obj = ormclasswrapper(obj)
        elif isinstance(obj, ormclasswrapper):
            pass
        elif isinstance(obj, ormclasseswrapper):
            pass
        else:
            raise TypeError('obj is of the wrong type')

        super().append(obj, uniq, r)
        return r

    def __contains__(self, e):
        """ Returrns True if e is in self or is one of the wrapped
        entity in self, False otherwise.
        """
        for e1 in self:
            if e1.entity is e:
                return True
        return super().__contains__(e)

class ormclasswrapper(entitiesmod.entity):
    """ Creates a wrapper class around an entity class. The wrapped
    class is stored in the `entity` attribute. Most of the class's
    attributes are proxies for the wrapped entity class's corresponding
    attribute.
    """

    # NOTE If I remember correctly, I created this wrapper class
    # because I wanted a way to add class references to
    # entities.entities collections since the only objects that can be
    # added to entities.entities are entities.entity objects.
    def __init__(self, entity):
        """ Sets the wrapped entity.
        :param: entity orm.entity: The entity to be wrapped.
        """
        self.entity = entity
        super().__init__()

    def __str__(self):
        """ A proxy to the wrapped entity's __str__ method.
        """
        return str(self.entity)

    def __repr__(self):
        """ A proxy to the wrapped entity's __repr__ method.
        """
        return repr(self.entity)

    def __getattr__(self, attr):
        """ A proxy to any of the wrapped entity's attributes not
        implemented here.
        """
        return getattr(self.entity, attr)

    @property
    def __module__(self):
        """ A proxy to the wrapped entity's __module__ property.
        """
        return self.entity.__module__

    @property
    def orm(self):
        """ A proxy to the wrapped entity's __orm__ object.
        """
        return self.entity.orm

    @property
    def name(self):
        """ A proxy to the wrapped entity's name attribute.
        """
        return self.entity.__name__
    
    def __call__(self, *args, **kwargs):
        """ Proxies invocations to the wrapped entity.
        """
        return self.entity(*args, **kwargs)

class composites(ormclasseswrapper):
    """ A collection of wrapped composite classes.
    """

class composite(ormclasswrapper):
    """ A wrapped composite class.
    """

class constituents(ormclasseswrapper):
    """ A collection of wrapped constituent classes.
    """

class constituent(ormclasswrapper):
    """ A wrapped constituent class.
    """

@contextmanager
def sudo():
    """
    💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
    A context manager that runs any code within it as the orm's root
    user. The root user isn't restricted by standard authorization rules
    or accessibility restrictions.

        # Retrieve and update `ent` as root.
        with orm.sudo():
            ent = entity(myid)
            ent.attr = 'my-value'
            ent.save()

    💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
    """
    sec = security()
    own = sec.owner
    try:
        from ecommerce import users
        sec.owner = users.root
        yield
    finally:
        sec.owner = own

@contextmanager
def su(own):
    """
    💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
    A context manager that temporarily switches the user the ORM is
    running under.

        usr = ecommerce.users(name='luser').first
        # Retrieve entity as `usr`
        with orm.su(usr):
            ent = entity(myid)

    💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
    """
    own1 = security().owner
    try:
        from ecommerce import users
        security().owner = own
        yield
    finally:
        security().owner = own1

@contextmanager
def override():
    """ A contextmanager to ensures that security().override is True.
    When the context manager exists, orm.override is reset to whatever
    it was before the contextmanager was entered.
    """
    override = security().override
    try:
        security().override = True
        yield
    finally:
        security().override = override

class security:
    """
    💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
    A singleton that stores security related values such as the orm's
    owner, proprietor, and whether or not the accessibility override is
    set.
    💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
    """
    _instance = None
    def __new__(cls):
        if not cls._instance:
            # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
            # Implement the singleton pattern.
            # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
            cls._instance = super(security, cls).__new__(cls)

            # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
            cls._override    =  False
            cls._owner       =  None
            cls._proprietor  =  None

        return cls._instance

    @property
    def proprietor(self):
        """ Return the proprietor entity currently set.
        """
        return self._proprietor

    @proprietor.setter
    def proprietor(self, v):
        """ 
        💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        Set ``v`` to orm's proprietor. Ensure that the proprietor
        entity owns itself.

        Proprietors
        ***********

        The logic in the ORM's database interface will use the
        security().proprietor to provide multitenancy support.

        When a proprietor is set, the ORM will ensure that all records
        written to the database have their proprietor FK set to
        security().proprietor.id, meaning that the records will be the
        *property* of the security().proprietor. Only records owned by
        the security().proprietor will be read by orm query operations
        i.e.:

            ent = entity(id)  # SELECT

            (or)

            ent.save()        # INSERT OR UPDATE
            
        When updating or deleting a record, the record must be owned by
        by the security().proprietor or else a ProprietorError will be
        raised.

        :param: party.party v: The proprietor entity.
        💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        """
        self._proprietor = v

        # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        # The proprietor of the proprietor must be the proprietor:
        #    
        #    assert v.proprietor is v
        #
        # Propogate this up the inheritance hierarchy.
        # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        sup = v
        while sup:
            sup.proprietor = v
            sup = sup.orm.super

    @property
    def override(self):
        """
        💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        Return True if override is set to True or if the owner is root. 

        When override is True, accessibility methods, such as
        creatability, retrievability, updatability and deletability are
        ignored. This is useful for unit test developers who want to
        ignore the accessibility methods for the sake of convenience.
        💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        """
        if self._override:
            return True

        return self.owner and self.owner.isroot

    @override.setter
    def override(self, v):
        """
        💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        The setter for security.overide.
        💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        """
        self._override = v

    @property
    def owner(self):
        """
        💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        Returns the current owner. The owner is a ``party.user``. When
        an entity is created, the entity's ``owner`` attribute will be
        set to the orm's owner. This attribute will be saved along with
        the entity so it wil always be known who the entity's owner is.

        The owner is important for the accessibility methods because it
        helps the entity's determine who should be able to do what with
        the entity. For example, for most entity objects, the user that
        created the entity should be able to update the entity.
        💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        """
        return self._owner

    @owner.setter
    def owner(self, v):
        """
        💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        The setter for security.owner.
        💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        """
        self._owner = v

    @property
    def issudo(self):
        """
        💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        Returns True if the current owner is root.
        💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        """
        return self.owner and self.owner.isroot


class orm:
    """ The ORM class.

    The ORM class bridges the orm.entity and orm.entities classes with
    lower-level, ORM functionality. Persistence (DML) logic as well as
    data definition (DDL) logic is encapsulated here. 

    The ORM user will not use most of the attributes in the the ``orm``
    class. However, there are many, important exceptions.

    Each ``orm.entity`` and ``orm.entities`` class has an ``orm``
    attribute.  Likewise, each **instance** of these classes will also
    have an ``orm`` attribute.

    Consider the ``good`` class in the product.py module. We can use the
    ``orm`` attribute to access its collection::

        from product import good
        assert good.orm.mappings.count == 9

    At the time of this writting, the ``good`` entity has 9 ``mapping``
    objects. This works for the ``good`` class or a ``good`` object::

        assert good().orm.mappings.count == 9

    Logic in the orm.py module makes extensive use of the ``orm`` class
    and objects behind the ``orm` class (such as the ``mapping``
    classes).  Occasionally, an ORM user will need to access attributes
    behind the orm class. For example, to determine if an entity has
    been saved to the database yet, the ORM user can check the
    ``orm.isnew`` property on the entity::

        # Create a new good; don't save to database.
        g = good()
        assert g.orm.isnew

        # Save to database
        g.save()
        assert not g.orm.isnew
    
    Attributes like ``isnew` might make more sense if they were directly
    off the entity (``g.isnew``), however, we don't want to clutter up the
    entity's attribute namespace so the entity developers can name their
    attributes without worry of name collision.
    """

    # A dict to store abbreviation (see orm.getentity())
    _abbrdict    =  dict()

    # A dict to store entity names (see orm.getentity())
    _namedict    =  dict()

    _proprietor  =  None
    owner = None

    def __init__(self):
        self.mappings              =  None
        self.isnew                 =  False
        self._isdirty              =  False
        self._ismarkedfordeletion  =  False
        self.entities              =  None
        self.entity                =  None
        self._table                =  None
        self.composite             =  None   #  For association
        self._composits            =  None
        self._constituents         =  None
        self._associations         =  None
        self._trash                =  None
        self._subclasses           =  None
        self._super                =  None
        self._base                 =  undef
        self.instance              =  None
        self.stream                =  None
        self.isloaded              =  False
        self.isloading             =  False
        self.isremoving            =  False
        self.dotrash               =  True
        self.joins                 =  None
        self._abbreviation         =  str()
        self.initing               =  False
        self._sub                  =  undef

        self.recreate = self._recreate

    @property
    def issues(self):
        """ Returns a list of possible issue with an entity, such as
        issues with the way the data and relationships have been
        defined.
        
        Note that this is intended to help entity modelers debug issues
        when defining data and relationships of entity objects. It is
        not use by the ORM to raise exceptions or print warning.

        Also, this is a work-in-progress. As entity modelers discover
        issues, they can add logic here that would have better detected
        the issue in the future for the issue they are currently working
        on.
        """
        r = list()
        esup = self.entity.mro()[1]
        essup = self.entities.mro()[1]
        if esup.orm.entities is not essup:
            r.append(
                f'{self} inherits from a different entity than does '
                'its entities collection: \n'
                f'\t{self.entity.__name__}({esup})\n'
                f'\t{self.entities.__name__}({essup})'
            )


        for map in self.mappings:
            if isinstance(map, entitymapping):
                es = [
                    x
                    for x in self.mappings.entitymappings
                    if x.entity is map.entity
                ]
                if len(es) > 1:
                    r.append(
                        f'The map "{map.name}" has a type {map.entity} '
                        f'which is the duplicate of another mapping'
                    )
        return r

    def redact(self):
        """
        💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        Remove entity objects from an entities collection if the
        entity's retrievability method reports ``violations``. 

        The idea here is to ensure that objects the user is not intended
        to have read-access to are removed from the collection before
        they are sent to the user.
        💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        """

        # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        # If there is no owner, then we don't care.
        # 
        # TODO This can't be right!
        # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        if not security().owner:
            return

        # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        # If the owner is root, redact nothing.
        # 
        # TODO We could use ``security().issudo`` for this.
        # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        if security().owner.isroot:
            return

        es = self.instance

        # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        # Iterate over the collection in reverse since we may be
        # removing some elements.
        # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        for e in es.reversed():
            vs = e.retrievability
            if not isinstance(vs, violations):
                # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
                # The ORM user must have returned the wrong type from
                # their retrievability method.
                # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
                raise TypeError(
                    "'retrievability' must return a "
                    f'`violations` instance for {type(e)}'
                )

            # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
            # If the violations collection is populated, remove the
            # entity from the collection. Don't "trash" it, i.e., don't
            # delete it from the database (that would be crazy).
            # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
            if vs.ispopulated:
                es.remove(e, trash=False)

    @property
    def statement(self):
        """ Return a tabularized list of the entity's attributes and
        their corresponding values. Any exceptions that happen to occur
        will be trapped and a string representations of the exception
        will be returned."""

        try:
            tbl = table()

            es = entitiesmod.entities()
            e = self.instance
            while e:
                es += e
                e = e.orm.super

            for i, e in enumerate(es.reversed()):
                if i:
                    r = tbl.newrow()
                r = tbl.newrow()
                r.newfield('Class')
                r.newfield('%s.%s' % (e.__module__, type(e).__name__))

                for map in e.orm.mappings:
                    r = tbl.newrow()
                    try:
                        v = getattr(e, map.name)
                    except Exception as ex:
                        v = 'Exception: %s' % str(ex)
                        
                    if type(map) in (primarykeyfieldmapping, foreignkeyfieldmapping):
                        if type(map.value) is UUID:
                            v = v.hex[:8]
                        else:
                            v = str(v)
                    else:
                        try:
                            if type(map) in (entitiesmapping, associationsmapping):
                                es = v
                                if es:
                                    brs = es.getbrokenrules(
                                        guestbook=None, 
                                        followentitymapping=False
                                    )
                                    args = es.count, brs.count
                                    v = 'Count: %s; Broken Rules: %s' % args
                                else:
                                    v = str(es)
                            else:
                                v = str(v)
                        except Exception as ex:
                            v = '(%s)' % str(ex)

                    r.newfield(map.name)
                    r.newfield(v)

            tblbr = table()

            r = tblbr.newrow()
            r.newfield('Broken Rules')
            r.newfield('')
            r.newfield('')

            r = tblbr.newrow()
            r.newfield('property')
            r.newfield('type')
            r.newfield('message')

            for br in self.instance.brokenrules:
                r = tblbr.newrow()
                r.newfield(br.property)
                r.newfield(br.type)
                r.newfield(br.message)
                
            sup = self.super

            if sup:
                stmt = sup.orm.statement
                return '%s\n%s\n%s' % (stmt,
                    str(tbl), 
                    str(tblbr)
                )
        except Exception as ex:
            return 'Exception: %s ' % (str(ex),)

    @property
    def ismarkedfordeletion(self):
        """ Returns True if the entity is marked for deletion. When an
        entity is marked for deletion, the next call to orm.save will
        result in a DELETE statement sent to the database to permanently
        destroy the record.
        """
        return self._ismarkedfordeletion

    @ismarkedfordeletion.setter
    def ismarkedfordeletion(self, v):
        """ Sets the entity as marked-for-deletion. See the comments at
        the getter for more.
        """
        self._ismarkedfordeletion = v

    @classproperty
    def builtins(cls):
        """ Return a list of mapping names that are standard on all
        entities, vis. 'id', 'updatedat', 'createdat', 'owner__userid'
        and 'proprietor__partyid'.
        """
        r = ['id', 'updatedat', 'createdat']
        for map in cls.mappings.foreignkeymappings:
            if map.isproprietor or map.isowner:
                r.append(map.name)

        return r

    @staticmethod
    def exec(sql, args=None):
        # NOTE This doesn't appear to be used anywhere
        exec = db.executioner(
            lambda cur: cur.execute(sql, args)
        )

        exec()
        
    def collectivize(self):
        """ If called on an instance of ``orm.entity``, returns an
        ``orm.entities`` instance (of the corresponding type) with the
        orm.entity within it. If called on an ``orm.entities``, simply
        return a reference to the ``orm.entities``::

            per = person(name='John Doe')
            pers = per.orm.collectivize()

            assert isinstance(pers, persons)
            assert pers.count == 1
            assert per in pers

            # Not much happens if done on an orm.entities
            assert pers is pers.orm.collectivize()
        """

        if isinstance(self.instance, self.entities):
            return self.instance

        es = self.entities()
        es += self.instance
        return es

    def default(self, attr, v, dict=None):
        """ Sets an attribute to a default value. ``default`` is
        intended to be called by an entity's constructor after the
        call to ``super().__init__(*args, **kwargs)`` has been made. 

        Before setting the attribute to ``v``, however, the kwargs dict
        in the entity's constructor is inspected to determine if the
        user instantiating the entity wants to set the attribute to a
        non-default value. For example, the ``artist`` class in test.py
        defaults the ``style`` attribute to the string "classicism":

            art = artist()
            assert art.style == 'classicism'

        The ``kwargs`` argument can be used to overide this default::

            art = artist(style='cubism')
            assert art.style == 'cubism'

        The kwargs arguments will be discoverd through inspection,
        though the ``dict`` parameter  can be used instead if the kwargs
        argument isn't available for some reason.
        
        :param: attr str: The attribute/map to be set
        :param: v object: The value to set the attribute to
        :param: dict dict: A replacment dict if the calling method
        (usually __init__) doesn't have a **kwargs parameter.
        """

        # Only set defaults if the entity is new, i.e., not in the
        # database yet.
        if not self.isnew:
            return

        # Get the **kwargs dict from the calling method unless the
        # ``dict` argument was passed in.
        st = inspect.stack()
        try:
            dict = st[1].frame.f_locals['kwargs']
        except Exception as ex:
            raise ValueError(
                'Failed finding `kwargs`. '
                'Call `default` from `__init__` with **kwargs '
                'or set `dict`. ' + repr(ex)

            )

        # If the kwargs parameter from the calling method has a key for
        # attr, use it. Otherwise use the value from the ``v``.
        try:
            if dict:
                v = dict[attr]
        except KeyError:
            pass

        # Set the attribute
        setattr(self.instance, attr, v)
            
    @property
    def table(self):
        """ Returns the name of the database table name corresponding to
        the entity::

            >>> party.person.orm.table
            'party_persons'

        Note that table names consis-t of the module ('party') proceeded
        by the entities' (not the entity's) name ('persons'). Including
        the module is necessary to prevent name collisions.
        """
        mod = inspect.getmodule(self.entities)
        if mod.__name__ == '__main__':
            if hasattr(mod, '__file__'):
                mod = os.path.splitext(
                    os.path.basename(mod.__file__)
                )[0]
                if mod == 'test':
                    mod = 'main'
            else:
                mod = 'main'
        else:
            mod = mod.__name__

        return '%s_%s' % (mod, self._table)

    @table.setter
    def table(self, v):
        """ Sets the name of the database table corresponding to the
        entity.

        Note that this want include the module name. The getter prepends
        the module name automatially::

            >>> party.person.orm.table = 'somename'
            >>> party.person.orm.table
            'party_somename'
        """
        self._table = v
        
    def iscollinear(self, with_):
        """ Return True if self is colinear with ``with_``.

        Collinearity is when the ``self`` entity is an instance ``with_``,
        or an instance of a superentity of ``with_``, or an instance of
        a class that inheritance from ``with_``. It's similar to
        isinstance(), but in addition to ascending the inheritance tree,
        it also descends it. 
        
        Collinearity in this context is limited to orm.entity object.
        For example, ``artist`` is colinear with ``painter`` and
        ``singer`` and vice-versa. However none of these object are
        colinear with ``orm.entity``, ``entities.entity'' or ``object``
        and vice-versa. 
        """

        if type(with_) is not entitymeta:
            with_ = type(with_)

        if isinstance(self.instance, with_):
            return True

        for e in with_.__mro__:
            if e in (entity, associations):
                break
            if type(self.instance) in e.orm.subentities:
                return True

        return False

    @classproperty
    def all(cls):
        return cls.entities(allstream)

    def ensure(self, expects, **kwargs):
        """ Ensure that a record exists.

        Certain types of ``orm.entity`` objects are defined by a unique
        identifier, such as a ``name`` attribute. For example, a
        ``statustype`` entity may have only a ``name`` attribute
        that could have values such as 'active', 'inactive', etc . We
        would call the ``ensure`` method in it's constructor::

            class statustype(orm.entity):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    self.orm.ensure(expects=('name',), **kwargs)

                name = str

        Given the above, anytime we instantiate a new statustype, the
        ``name`` attribute is used as an identifier. The ``ensure``
        method will ensure that a new record for the ``name`` attribute
        is created if it does not already exist. If it does exists, the
        entity will be constructed as that entity::

            # Truncate the table so we are starting anew.
            statustype.orm.truncate()

            # Instatiate an 'active' status.  The constructor here
            # ensures that a record is created for the 'active'
            # statustype.
            st = statustype(name='active')

            # No need to save the statustype, it was saved by the
            # constructor
            ### st.save()

            # Since the record for the 'active' statustype was created
            # above, additional calls will return a new statustype
            # instance but to the same entity.
            st1 = statustype(name='active')

            # Same entity:
            assert st.id == st1.id
            assert 'active' == st.name
            assert 'active' == st1.name

            # Different object of course:
            assert st is not st1
        """

        # Query using the **kwargs, e.g., {'name': 'active'}
        rs = self.entities(**kwargs)

        # Get a unique set from the `expects` tuple passed in
        expects = set(expects)

        # Get a unique set of kwargs keys
        keys = set(kwargs.keys())

        if len(expects & keys) != len(expects):
            # When loading via the orm.populate() method, the expected
            # properties won't be passed in. Just return.
            return

        # If a record was found
        if rs.count:
            
            # Use the first record to populate this instance.
            self.instance.id = rs.first.id
            for k, v in kwargs.items():
                setattr(self.instance, k, getattr(rs.first, k))

            # The record isn't new or dirty so set all peristance state
            # variables to false.
            self.persistencestate = (False,) * 3

            # Repeat for all the supers that were loaded
            sup = self.instance.orm._super
            while sup:
                sup.orm.persistencestate = (False,) * 3
                sup = sup.orm._super
        else:
            # Save immediately.
            self.instance.save()
            
    # TODO This should probably be renamed to `loaded`
    def reloaded(self):
        """ Returns a new instance of an entity freshly loaded from the
        database::

            # Create an entity and save to database
            ent = entity()
            ent.save()

            # Load the entity from the database and assign it to ent1.
            # Note that nothing happens to ent.
            ent1 = ent.orm.reloaded()

            # ent1 has the same attribute values as ent, though it is
            # not the same Python object.
            assert ent.id == ent1.id
            assert ent is not ent1
        """
        return self.entity(self.instance.id)

    def exists(self, o):
        """ Returns True if ``o`` exists in the database.

        :param: o orm.entity|UUID: The entity or entity id to check the
        existence of.
        """
        return self.cast(o) is not None

    def cast(self, o):
        """ Given an entity or a UUID as `o`, a new orm.entity of the
        given type is loaded from the database and returned. If no
        such entity is in the database, None is returned.
            
            # Load human given an existing UUID
            hum = human.orm.cast(id)
            assert type(hum) is human

            # Upcast to mammal super type of human by passing in the
            # entity instead of the UUID. Note for this, we would
            # canonically just do `hum.super`.
            mam = mammal.orm.cast(hum)
            assert type(mam) is mammal

            # Downcast back to human from mammal
            hum = human.orm.cast(mam)
            assert type(hum) is human

            # Loading non-existing entities return None
            emp = employee.orm.cast(UUID())
            assert emp is None

            # You can also cast to a class
            hum = mam.orm.cast(human)
            assert type(hum) is humman

        The method is particularly useful when you have an entity but
        you want to downcast it into a particular entity.

        :param: o orm.entity/UUID: The id to be used for loading. If
        ``o`` is an orm.entity, its ``id`` attribute will be used.
        """

        try:
            e = self.entity
            if isinstance(o, entity):
                id = o.id
            elif isinstance(o, UUID):
                id = o
            elif hasattr(o, 'mro') and entity in o.mro():
                e = o
                id = self.instance.id
            else:
                raise ValueError("Can't determine id")

            return e(id)
        except db.RecordNotFoundError:
            return None

    @property
    def specialist(self):
        # TODO:a7f8f87a This is redundant with orm.leaf. I think we
        # should make the name 'leaf' but use the implementation here.
        if self.isstatic:
            # For any given entity, there can be 0 or more specialist
            # entity class references. If we wanted to get those, we 
            # should write a ``specialists`` property that returns a
            # list of those class references.
            raise ValueError(
               'specialist cannot be called on a static entity'
            )

        r = self.instance

        sub = r.orm.sub
        while sub:
            r = sub
            sub = sub.orm.sub

        return r
            
    @property
    def leaf(self):
        """ Return the lowest subentity in the inheritance tree of the
        `orm`'s `instance` property. The database is queried for each
        subclass, the database is queried. If there are no subclasess,
        `self.instance` is returned.
        """

        leaf = self.instance
        id = leaf.id

        # Itereate over subentities. `self.subentities` is assumed to
        # iterate in a way tha yields the top-most subclass first
        # progressing toward the lowest subclass.
        for cls in self.subentities:
            try:
                leaf = cls(id)
            except db.RecordNotFoundError:
                return leaf

        return leaf
                
    def clone(self):
        """ Returns a new instance of an ``orm`` object with the same
        attributes of ``self``.
        """
        r = orm()

        props = (
            'isnew',       '_isdirty',     'ismarkedfordeletion',
            'entity',      'entities',     '_table'
        )

        for prop in props: 
            setattr(r, prop, getattr(self, prop))

        r.mappings = self.mappings.clone(r)

        return r

    def __repr__(self):
        """ Returns a string representation of the ``orm`` object
        including its corresponding instance or entity class.
        """
        r = 'orm(type=<%s>, %s=True)'

        if self.isinstance:
            args = [type(self.instance).__name__]
        else:
            args = [self.entity.__name__]

        args += ['instance' if self.isinstance else 'static']

        return r % tuple(args)

    @property
    def isreflexive(self):
        """ Returns True if the association references two different
        entitymappings of the same type.

        An example if a reflexive association is ``party.party_party``::

            class party_party(orm.association):
                subject  =  party
                object   =  party
                role     =  str

        It associates a ``party`` called 'subject' with a ``party``
        called object making it a "reflexive" association.
        """
        maps = self.mappings.entitymappings
        types = [
            x.entity for x in maps
            if x.name != 'proprietor' and not x.isowner
        ]

        return bool(len(types)) and len(types) > len(set(types))
        
    @property
    def isrecursive(self):
        """ Returns True if the entity or entities class or object is
        recursive.

        A recursive entity is one that has constituents of the same type
        as the composite.

        A good example if recursive entities is the ``inode`` class in
        file.py. An inode is the superentiy of ``file`` and
        ``directory``, which compose the framework's "file system". File
        systems are recursive in that you can create directories within
        directories indefinately. (Interating over these tree structures
        is typically done with a **recursive** function, which is why we
        use the word "recursive" to describe these entity objects.)

            class inodes(orm.entities):
                pass

            class inode(orm.entity):
                inodes = inodes

        In the above example, we see that ``inode`` has a collection of
        ``inodes``, i.e., the composite inode has a constiuent of the
        same type. This is what makes a entity recursive.

            assert inode.orm.isrecursive

        Other examples of recursive entity objects include party.region,
        product.category and shipment.item. 
        """

        map = self.mappings(self.entities.__name__)
        return map is not None and map.entities is self.entities

    def joinsupers(self):
        ''' Create joins between `self` and the superentity that the
        predicate requires be joined based on predicate columns being
        used. 
        
        For example, is `muralists` is being queried, and `firstname` is
        in the predicate, then we will need to join `self` to `artist`
        since `artist` has the `firstname` property. Since `muralists`
        is a subentity of `painter`, `painter` will also be included in
        the join::

            muralists.join(
                painters.join(
                    artists
                )
            )
        '''
        
        # The top entity in the tree
        top = None

        # For each predicate
        for pred in self.where.predicate:

            # Use the MATCH (fulltext) predicate if it exists
            pred = pred.match or pred

            # Get the column name referenced by the predicate
            # FIXME If multiple columns are supported, fix below
            col = pred.columns[0]

            e = top or self.entity.orm.super

            while e: # :=

                # Find the map based on the column name
                map = e.orm.mappings(col) 

                # Is map the proprietor FK
                isfk = isinstance(map, foreignkeyfieldmapping)
                isproprietor = isfk and map.isproprietor

                # If such a map exists. Ignore the map if it is the
                # entitiy's proprietor's foreignkeymappings
                # ('proprietor__partyid') since every entity has a
                # proprietor foreignkeymappings.
                if map and not isproprietor:

                    # If we found the map, we found the entity we want
                    # to query, so assign it to `top` and break.
                    top = e.orm.entities
                    break

                e = e.orm.super

        # We never ascended so return without joining
        if not top:
            return

        # Take the current instance and create INNER JOINs on each
        # superentity until we reach the `top`. With the tables joined,
        # the query's resultset can be limited to those that have values
        # that match the columns the user is trying to query.
        es = self.instance
        while type(es) is not top:
            sup = es.orm.entities.orm.super.orm.entities()
            es = es.join(sup, inferassociation=False)
            es = sup

    def joinsubs(self):
        """ Recursively create OUTER JOIN on subentities.

        This allows the queries to pull subentity data from the database
        via the JOINs. These data are used to construct subentity
        objects that can replace its superentity. See the orm.populate
        method.
        """
        clss = orm.getsubclasses(
            of=type(self.instance), recursive=False
        )

        for cls in clss:
            self.instance.outerjoin(cls, inferassociation=False)
            j = self.instance.orm.joins.last

            j.entities.orm.joinsubs()

    def truncate(self, cur=None):
        """ Remove all date in the table that is associated with the
        entity.
        """
        # TODO Use executioner
        sql = 'TRUNCATE TABLE %s;' % self.table

        if cur:
            cur.execute(sql)
        else:
            pool = db.pool.getdefault()
            with pool.take() as conn:
                conn.query(sql)

    @staticmethod
    def recreate(*args):
        """ Drop and recreate the table for each of the entity class
        references in *args.
        """

        # NOTE that when ``orm`` is an instance (as opposed to mearly a
        # class reference), this method is replace with ``orm._recreate'
        # on initialization (see orm.__init__).

        # For each entity class references in *args
        for e in args:
            # Delegate to the instance version of ``recreate``
            e.orm.recreate()
            
    def _recreate(self, cur=None, recursive=False, guestbook=None):
        """ Drop and recreate the table for the orm ``self``. 

        :param: cur: The MySQLdb cursor used by this and all subsequent
        CREATE and DROPs

        :param: recursive: If True, the constituents and subentities of
        ``self`` will be recursively discovered and their tables
        recreated. Used internally.

        :param: guestbook: A list to keep track of which classes' tables
        have been recreated. Used internally to prevent infinite
        recursion.
        """

        # Prevent infinite recursion
        if guestbook is None:
            guestbook = list()
        else:
            if self in guestbook:
                return
        guestbook += [self]

        try: 
            conn = None
            if not cur:
                # TODO Use executioner
                pool = db.pool.getdefault()
                conn = pool.pull()
                cur = conn.createcursor()

            try:
                self.drop(cur)
            except MySQLdb.OperationalError as ex:
                try:
                    errno = ex.args[0]
                except:
                    raise

                if errno != BAD_TABLE_ERROR: # 1051
                    raise

            self.create(cur)

            if recursive:
                for map in self.mappings.entitiesmappings:
                    map.entities.orm.recreate(
                        cur, True, guestbook
                    )

                for ass in self.associations:
                    ass.entity.orm.recreate(cur, True, guestbook)

                    for map in ass.orm.mappings.entitymappings:
                        map.entity.orm.recreate(
                            cur, recursive, guestbook
                        )

                for sub in self.subentities:
                    sub.orm.recreate(cur, True, guestbook)
                            
        except Exception as ex:
            # Rollback unless conn and cur weren't successfully
            # instantiated.
            if conn and cur:
                conn.rollback()
            raise
        else:
            if conn:
                conn.commit()
        finally:
            if conn:
                pool.push(conn)
                if cur:
                    cur.close()

    def drop(self, cur=None, ignore=False):
        """ Removes the table from the database that is mapped to the
        entity.

        :param: ignore bool: If True, don't raise an error if the table
        does not exist. The default is False.

        :param: cur: The MySQLdb cursor to use for the database
        connection.
        """
        # TODO Use executioner
        # TODO UPPER CASE 'drop table'
        sql = 'drop table `%s`;' % self.table

        try:
            if cur:
                cur.execute(sql)
            else:
                pool = db.pool.getdefault()
                with pool.take() as conn:
                    conn.query(sql)
        except _mysql_exceptions.OperationalError as ex:
            if ex.args[0] == BAD_TABLE_ERROR:
                if not ignore:
                    raise
    
    def migrate(self, cur=None):
        """ Examines the entity's mapping attributes and the table that
        the entity is mapped to and issues an ALTER TABLE statement to
        the table in order to make its columns match the entity's
        attributes.

        :param: cur: The MySQLdb cursor to use for the database
        connection.
        """
        # TODO Use executioner
        sql = self.altertable

        if not sql:
            return

        if cur:
            cur.execute(sql)
        else:
            pool = db.pool.getdefault()
            with pool.take() as conn:
                conn.query(sql)

    def create(self, cur=None, ignore=False):
        """ Create a table in the database corresponding to the entity.
        """
        # TODO Use executioner
        sql = self.createtable

        try:
            if cur:
                cur.execute(sql)
            else:
                pool = db.pool.getdefault()
                with pool.take() as conn:
                    conn.query(sql)
        except _mysql_exceptions.OperationalError as ex:
            # TODO There should be an alternative block here that calls
            # `raise`
            if ex.args[0] == TABLE_EXISTS_ERROR:
                if not ignore:
                    raise
            else:
                raise
                
    @property
    def ismigrated(self):
        """ Returns True if the attributes in the entity match the
        columns in the underlying table.
        """
        return not bool(self.altertable)

    @property
    def migration(self):
        """ Returns a new ``migration`` object for the entity. See the
        ``migration`` class for more.
        """
        return migration(self.entity)

    @property
    def altertable(self):
        """ Compares the attributes of the entity with the columns of
        the entity's underlying table and returns an ALTER TABLE command
        that, if run against the database, would cause the table to
        match the entity. If there are no differences between the
        entity's attributes and the underlying table's columns, or if
        the table does not exist, None is returned.
        """
        tbl = self.dbtable

        # If there is no table in the database, there can be no ALTER
        # TABLE. We would need a CREATE TABLE, obviously, so return
        # None.
        if not tbl:
            return None

        # Create a clone of the table to track changes that would be
        # made to the real table if the altertable statement were
        # applied to it.
        altered = tbl.clone()

        maps = mappings(
            initial=(
                x for x in self.mappings 
                if isinstance(x, fieldmapping)
            )
        )

        attrs = [x.name for x in maps]
        cols = [x.name for x in tbl.columns]

        opcodes = SequenceMatcher(a=cols, b=attrs).get_opcodes()

        # listify tuples so they are mutable
        opcodes = [list(x) for x in opcodes]
        rms = list()
        for i, (tag, i1, i2, j1, j2) in enumerate(opcodes):
            if tag != 'delete':
                continue

            inserts = [x for x in opcodes if x[0] == 'insert']

            for insert in inserts:
                ix = slice(*insert[3:])
                for attr in attrs[ix]:
                    for col in cols[i1:i2]:
                        if col != attr:
                            continue

                        if opcodes[i][0] == 'delete':
                            opcodes[i][0] = 'move'
                            after = insert.copy()
                            after[0] = 'after'
                            opcodes[i].append(after)
                            after[4] = after[3]

                        after[4] += 1

                        if insert[3] + 1 == insert[4]:
                            rms.append(opcodes.index(insert))
                        else:
                            insert[3] += 1

        for rm in rms:
            del opcodes[rm]

        # If there are no differences, return None; there is nothing to
        # ALTER.
        isdiff = any([x for x in opcodes if x[0] != 'equal'])

        I = ' ' * 4
        at1 = str()
        hdr = f'ALTER TABLE `{self.table}`\n'
        if isdiff:

            for tag, i1, i2, j1, j2, *after in  opcodes:

                if tag not in ('insert', 'delete', 'move', 'replace'):
                    continue

                if tag == 'insert':
                    # ADD <column-name> <definition>
                    for i, attr in enumerate(attrs[j1:j2]):
                        map = maps[attr]
                        after = maps.getprevious(map)
                        after = altered.columns[after.name]

                        if at1: at1 += ',\n'

                        # TODO s/ADD/ADD COLUMN/ for clarity and
                        # consistancy (because we use DROP COLUMN and
                        # MODIFY COLUMN)
                        at1 += f'{I}ADD `{map.name}` {map.definition}'

                        at1 += f'\n{I*2}AFTER `{after.name}`'

                        col = db.column(map)
                        ix = altered.columns.getindex(after.name)
                        altered.columns.insertafter(ix, col)

                elif tag == 'move':
                    # CHANGE COLUMN <name> <-name> <-definition> 
                    #     AFTER <after>

                    ix = after[0][1] - 1

                    after = tbl.columns[ix]
                    for col in cols[i1:i2]:
                        map = maps[col]

                        if at1: at1 += ',\n'

                        at1 += f'{I}CHANGE COLUMN `{col}` ' + \
                             f'`{col}` {map.definition}'  + \
                             f'\n{I * 2}AFTER `{after.name}`'

                        ix = altered.columns.getindex(after.name)
                        col = altered.columns[col]
                        altered.columns.moveafter(ix, col)

                        after = map

                elif tag == 'delete':
                    for i, col in enumerate(cols[i1:i2]):
                        if at1: at1 += ',\n'

                        at1 += f'{I}DROP COLUMN `{col}`'

                        altered.columns.remove(col)

                elif tag == 'replace':
                    for col, map in zip(cols[i1:i2], maps[j1:j2]):
                        if at1: at1 += ',\n'
                        at1 += (
                            f'{I}CHANGE COLUMN `{col}` `{map.name}` '
                            f'{map.definition}'
                        )
                        altered.columns[col].name = map.name

            at1 = f'{hdr}{at1};'

        if maps.count != altered.columns.count:
            raise ConfusionError(
                'mappings:%s columns:%s' % 
                    (maps.count, altered.columns.count)
            )

        at2 = str()
        for map, col in zip(maps, altered.columns):
            if col.name != map.name:
                raise ConfusionError(
                    f'Mapping error: {map.name} != {col.name}'
                )

            if col.definition == map.definition:
                continue

            if at2: at2 += ',\n'
            at2 += f'{I}MODIFY COLUMN `{col.name}` {map.definition}';

        if at2:
            at2 = f'ALTER TABLE `{self.table}`\n{at2};'

        r = str()
        if at1:
            r = at1

        if at2:
            if r: r += '\n\n'
            r += at2

        return r or None

    @property
    def createtable(self):
        """ Returns a CREATE TABLE string which, if issued against the
        database, would create the entity's underlying table (assuming
        the table didn't already exist).
        """
        r = 'CREATE TABLE `%s`(\n' % self.table 

        for i, map in enumerate(self.mappings):
            if not isinstance(map, fieldmapping):
                continue

            if i:
                r += ',\n'

            r += '    `%s`' % map.name

            if isinstance(map, fieldmapping):
                r += ' ' + map.definition

        for ix in self.mappings.aggregateindexes:
            r += ',\n    ' + str(ix)

        r += '\n) '
        r += 'ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;'
        return r

    def reload(self, orderby=None, limit=None, offset=None):
        """ Reload the entities collection (self). A different query
        will be executed if the arguments are different, though most of
        the SELECT statement is generated by arguments passed to the
        entities collection's constructor.

        :param: str orderby: The list of columns to be passed to the
        ``ORDER BY`` clause. Used only in streaming mode.

        :param: int limit: An integer value to pass to the ``LIMIT``
        keyword.  Used only in streaming mode.

        :param: int offset:  An integer value to pass to the ``OFFSET``
        keyword.  Used only in streaming mode.
        """

        # TODO To complement orm.reloaded(), we should have an override
        # of orm.load() that reloads/refreshes an entity object. 
        try:
            # Remove all elements from collection.
            self.instance.clear()
        except:
            raise
        else:
            # Flag the entities collection as unloaded so the load()
            # method will proceed with an attempt to load.
            self.isloaded = False
            self.collect(orderby, limit, offset)

    def query(self, sql):
        # NOTE This does not appear to be in use.
        ress = None
        def exec(cur):
            nonlocal ress
            cur.execute(sql)
            ress = db.dbresultset(cur)

        exec = db.executioner(exec)

        exec.execute()

        return res

    # TODO:1d1e17dc s/dbtable/table
    @property
    def dbtable(self):
        """ Returns a ``db.table`` object representing the entity's
        underlying database table.
        """
        try:
            return db.table(self.table)
        except _mysql_exceptions.OperationalError as ex:
            if ex.args[0] == BAD_TABLE_ERROR:
                return None
            raise

    def load(self, id):
        """ Load an entity by ``id``.

        :param id uuid4: A uuid4 object representing the id of the
        entity to be loaded.
        """
        # Create the basic SELECT query.
        sql = f'SELECT * FROM {self.table} WHERE id = _binary %s'

        # Search on the `id`'s bytes.
        args = [id.bytes]

        # If the ORM's proprietor has been set, search through self's
        # foreign key mappings looking for its foreign key to its
        # proprietor. Restrict the result set to only records where the
        # proprietor's FK column matches the proprietor set at the ORM
        # level. This restricts entity records not associated with
        # security().proprietor from being loaded.
        if security().proprietor:
            for map in self.mappings.foreignkeymappings:
                if map.fkname == 'proprietor':
                    sql += f' AND {map.name} = _binary %s'
                    args.append(security().proprietor.id.bytes)
                    break

        ress = None

        # Create a callable to execute the SQL
        def exec(cur):
            nonlocal ress
            cur.execute(sql, args)
            ress = db.dbresultset(cur)

        # Create an executioner
        exec = db.executioner(exec)

        # Bubble up the executioner's events
        exec.onbeforereconnect += \
            lambda src, eargs: self.instance.onbeforereconnect(src, eargs)
        exec.onafterreconnect  += \
            lambda src, eargs: self.instance.onafterreconnect(src, eargs)

        # Run the query (this will invoke the `exec` callable above.
        exec.execute()

        # TODO We may want to reconsider raising an exception when a
        # non-existant ID is given. The expectation the user may have is
        # that the object returned from the constructor is falsey:
        #
        #     e = myentity(bad_id)
        #     if e:
        #         return e
        #     else:
        #         raise Exception('myentity not found')
        #
        # Hacking __new__ to return None may not be a good idea because
        # of all the event initialition code in __init__. However, we
        # could set a private boolean to cause the entity's __bool__
        # method to return False. Then, any call to __getattribute__()
        # could check the private boolean and raise an exception to
        # indicate that entity is as good as None because the id was
        # non-existent:
        #
        #     def __bool__(self):
        #         return not self._recordnotfound
        #
        #     def __getattribute__(self):
        #         if self._recordnotfound: raise RecordNotFoundError()
        #

        # If the `id` exists, we should only get one record back from
        # the database. If that's not the case, raise a
        # db.RecordNotFoundError.
        ress.demandhasone()

        # We are only interested in the first
        res = ress.first

        # Invoke the `onafterload` on self.instance passing in relevent
        # arguments
        eargs = db.operationeventargs(
            self.instance, 'retrieve', sql, args, 'after'
        )
        self.instance.onafterload(self.instance, eargs)

        # Give the caller the record so it can populate itself with the
        # data.
        return res
    
    def collect(self, orderby=None, limit=None, offset=None):
        """ Loads data from the database into the collection. The SQL
        used to load the data is generated mostly from arguments passed
        to the entities collection's contructor.

        Note that an ORM user typically doesn't call ``collect``
        explicitly. The call to ``collect`` is usually made by the ORM
        after the entities collection has been instantiated and during
        the invocation of one of the collection's properties or methods.
        See ``entities.__getattribute__``.

        :param: str orderby: The list of columns to be passed to the
        ``ORDER BY`` clause. Used only streaming mode.

        :param: int limit:  An integer value to pass to the ``LIMIT``
        keyword.  Used only in streaming mode.

        :param: int offset:  An integer value to pass to the ``OFFSET``
        keyword.  Used only in streaming mode.
        """

        # Don't attemt to load if already loaded.
        if self.isloaded:
            return

        try:
            # Declare that we are currently loading
            self.isloading = True
                    
            # Get SQL and SQL parameters/args
            sql, args = self.sql

            # Concatenate the orderby
            if orderby:
                sql += f'\nORDER BY {orderby}'

            # Concatenate the LIMIT and OFFSET
            if limit is not None:
                offset = 0 if offset is None else offset
                sql += f'\nLIMIT {limit} OFFSET {offset}'

            # Set up a function to be called by the database's
            # executioner to populate `ress` with the resultset
            ress = None
            def exec(cur):
                nonlocal ress
                
                # Call execute on the cursor
                cur.execute(sql, args)

                # Assign ress the resultset
                ress = db.dbresultset(cur)

            # Instantiate the executioner
            exec = db.executioner(exec)

            # Connect the executioner's *reconnect events to self's
            exec.onbeforereconnect += \
                lambda src, eargs: self.instance.onbeforereconnect(
                    src, eargs
                )

            exec.onafterreconnect  += \
                lambda src, eargs: self.instance.onafterreconnect(
                    src, eargs
                )

            # Execute the query. `ress` will be populated with the
            # results.
            exec.execute()

            # Raise self's onafterload event
            eargs = db.operationeventargs(
                self.instance, 'retrieve', sql, args, 'after'
            )

            self.instance.onafterload(self, eargs)

            # Use the resultset to populate the entities collection
            # (self) and link the entities together (linking is done in
            # `orm.link()`).
            self.populate(ress)

        finally:
            self.isloaded = True
            self.isloading = False

    @property
    def abbreviation(self):
        """ Return a unique abbreviation of the entity. This is useful
        in table aliasing to keep the size of SELECT statements small
        (table aliasing can be extremely verbose because of the way
        aliases are used to keep track of the way data is related to
        each other.)
        """
        if not self._abbreviation:
            suffix = str()

            # Get all entity classes sorted by name
            es = self.getentitys() + self.getassociations()
            es.sort(key=lambda x: x.__name__)

            def generator():
                tblelements = self.table.split('_')
                if len(tblelements) > 1:
                    # Use underscores to abbreviate, e.g.:
                    # artist_artifacts => a_a 
                    m = min(len(x) for x in tblelements)
                    for i in range(m - 1):
                        r = str()
                        for j, tblelement in func.enumerate(tblelements):
                            r += tblelement[:i + 1]
                            r += '_' if not j.last else ''
                        yield r
                                
                else:
                    # If no underscores were found, just yield each character.
                    for c in self.table:
                        yield c

            found = False
            while True:
                for c in generator():
                    self._abbreviation += c + suffix
                    for e in es:
                        if e.orm.table == self.table:
                            continue

                        abbr = e.orm.abbreviation
                        if abbr == self._abbreviation:
                            break
                    else:
                        found = True
                        break
                else:
                    # Couldn't abbreviate so increment suffix
                    self._abbreviation = str()
                    if suffix:
                        suffix = str(int(suffix) + 1)
                    else:
                        suffix = '0'

                    continue
                break

        return self._abbreviation

    @staticmethod 
    def dequote(s):
        """ Returns a string with the quotes removed.

        :param: s str: The string to remove the quotes from.
        """
        if s[0] == "'" and s[-1] == "'":
            return s[1:-1]
        return s

    # TODO s/parameterizepredicate/parameterize/
    def parameterizepredicate(self, args):
        """ In the where clause (``self.instance.orm.where``), look for
        literals, i.e.::

            WHERE COL = 'LITERAL'
        
        Replace the literal with a placeholder (%s) and add the literal
        value to args:: 
            
            WHERE COL = '%s'
            args = ['LITERAL']
        
        Return the new args.
        """

        # Then number of args should be the same number of placeholders
        # that we find when iterating over the predicates.
        placeholders = len(args)
        placeholders1 = int()
        r = list()

        for pred in self.instance.orm.where.predicate:
            if pred.match:
                if pred.match.searchstringisplaceholder:
                    r.append(args.pop(0))
                    placeholders1 += 1
                else:
                    r.append(pred.match.searchstring)
                    pred.match.searchstring = '%s';
            else:
                for i, op in enumerate(pred.operands):
                    if predicate.isliteral(op):
                        pred.operands[i] = '%s'
                        r.append(self.dequote(op))
                    elif predicate.isplaceholder(op):
                        r.append(args.pop(0))
                        placeholders1 += 1

        if placeholders != placeholders1:
            raise ValueError(
                'Mismatch between the number of placeholders and the '
                'number of arguments given'
            )

        return r
                        
    def populate(self, ress):
        """ Given a resultsets collection (from a SELECT statement with
        the specific table and field alias notation), populate the
        `entities` object.

        This method first collects all the data from the resultset and
        creates objects of the appropriate type and assigns them an
        entry in the entities dict (`edict`). The ``link`` method will
        then be called to link all the individual objects in ``edict``
        into the graph (see ``orm.link`` for more).

        :param: db.resultset(s) ress: A ``resultset`` or ``resultsets``
        instance containing the results of the SELECT for this entities
        collection. See (orm.sql) to see how the SELECT is generated.
        """

        # Create an entities dict
        edict = dict()
        skip = False

        es = self.instance

        if type(ress) is db.dbresult:
            # If we are given one resultset (simple), we are probably
            # loading an a single entity by id, i.e.::
            #
            #     ent = entity(id).
            ress = [ress]
            simple = True
            maps = self.mappings
        elif type(ress) is db.dbresultset:
            # Multiple resultsets (`not simple`) imply that we are
            # loading an entities collection, i.e::
            # 
            #     ents = entities(field = 'value')
            simple = False
        else:
            raise TypeError('Invalid type of `ress`')

        # Iterate records
        for res in ress:

            # Iterate over the record's fields
            for i, f in func.enumerate(res.fields):    # TODO s/func.//
                alias, _, col = f.name.rpartition('.')

                if not simple and (not skip or col == 'id'):
                    # If we are loading an entities colleciion we are at
                    # an id field
                    if col == 'id':
                        id = f.value
                        if not id:
                            # Continue iterating through fields until we
                            # reach an id field
                            skip = True
                            continue

                        _, _, abbr = alias.rpartition('.')

                        # Get entities class reference from abbreviation
                        eclass = orm.getentity(abbr=abbr)

                        # The key for `edict` based on the UUID and the
                        # entities class.
                        key = (id, eclass)

                        # If an entry for this id already exists in
                        # edict, skip. The object has already been taken
                        # care of and this is just a duplicate from the
                        # resultset.
                        skip = key in edict
                        if skip:
                            continue

                        # Instantiate an object from entity class.
                        e = eclass()

                        # Add to entity dict
                        edict[key]= e

                        # If e meets the criteria, append it to
                        # self.instance. First, is e an instance of
                        # self.instance's type.
                        if isinstance(e, es.orm.entity):

                            # Take the field name (i.e., alias) and
                            # split it on '.' to create a list of
                            # abbreviations.
                            abbrs = f.name.split('.')

                            # Get rid of the actual field name, i.e.,
                            # 'id'.
                            abbrs.pop()

                            # If we are at the first field in the result
                            # set we can just append because this 'id' 
                            # field will be for the root entity which is
                            # above any joins from the SELECT.
                            if i.first:
                                es += e
                                

                            else:
                                # If we are here, we must be at an 'id'
                                # field but not the first one, i.e., one
                                # from a OUTER JOINed table. The
                                # following logic looks at the
                                # inheritance hierarchy and matches it
                                # with the field name. We want to make
                                # sure `e` comes from a record that was
                                # OUTER JOINed in an effort to collect
                                # subentities (see orm.joinsubs()).

                                # Ascend inheritance tree to create a
                                # list of abbreviations.
                                abbrs1 = [
                                    x.orm.abbreviation
                                    for x in e.orm.entity.orm.getsupers(
                                        withself=True
                                    )
                                ]

                                abbrs1.reverse()

                                # Remove elements that are not in the
                                # abbreviation from the field name.
                                abbrs1 = abbrs1[-len(abbrs):]

                                # If f.name's abbreviations match `e`
                                # inheritance hierarchy abbreviations,
                                # we know that `e` came from a record
                                # that was OUTER JOINed in order to
                                # collect subentities of self.instance.
                                if abbrs == abbrs1:
                                    es += e


                        # Grab the mappings collection for the new
                        # entity while we are in the id column. The
                        # mapping values will be set later.
                        maps = e.orm.mappings

                        # During e's __init__'ing, a new instance of a
                        # super entity may be created (e.g., because an
                        # __init__ sets an attribute that is only in a
                        # super). Since we are loading here, we want to
                        # make sure this `super` set to None. 
                        #
                        # The result will be that the super will either
                        # be lazy-loaded when needed, or, if we have the
                        # super's record from the database here
                        # somewhere in `ress`, e.orm.super will be set
                        # by orm.link() to that superentity.
                        
                        e.orm.super = None

                        e.orm.persistencestate = (False,) * 3

                if skip:
                    continue

                # Assign field's value mapping objects. `maps` will be
                # the new entity's ``mappings`` or self.mappings;  see
                # above for which.
                maps[col]._value = f.value

        ''' At this point, `es` can have multiple entity objects with
        the same id but with different positions in the class hierarchy.
        For example, we could have a ``product.product`` entity and a
        ``product.good`` entity. It's very much preferable to the user
        that we have the most specialized version of this entity (which
        would, of course, be ``product.good`, since a good (or service)
        is a type of product). In this case, the following logic would
        remove the ``product.product`` from es and keep the
        ``product.good``.
        '''

        # If the resultset had multiple records
        if not simple:
            
            # Get all the id values edict's keys
            ids = set([x[0] for x in edict])

            # For each of those id...
            for id in ids:
                lowest = None

                # Iterate over edict
                for id1, eclass in edict:

                    # Find the most-specialized (lowest) subentity of
                    # eclass for the current `id`.
                    if id == id1:
                        if lowest:
                            if lowest.orm.issuperentity(of=eclass):
                                lowest = eclass
                        else:
                            lowest = eclass

                # Get the most specialized object
                e = edict[id, lowest]

                # For the current `id`, go through each entity in edict.
                # Remove the objects from `es` if it is not the most
                # specialized version of that entity.
                for (id1, eclass), e in edict.items():
                    if id == id1:
                        if eclass.orm.issuperentity(of=lowest):
                            es.remove(e, trash=False)

            #💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
            # Ensure the user has read access to the entity.
            es.orm.redact()
            #💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣

        # Link the entity objects in edict together into the graph
        orm.link(edict)

    @staticmethod
    def link(edict):
        """ For each entity or entities object in <edict>, search
        <edict> for any composites, constituents and supers then assign
        them to the entity's appropriate mapping object. 

        :param dict[tuple, entity] edict: A dict of entity or entites
                                          objects

        :returns: void

        For example, if <edict> contains an artist entity and a location
        entity, and the location entity belongs to the artist entity
        (i.e., the location entity's `artistid` foreign key has the same
        value as the artist entity's id), the location entity will be
        assigned to the artist entity's locations collection. So when
        the method is complete, the location entity can be obtained from
        the artist entity via its `locations` collection, i.e.:: 
            
            edict = dict()
            edict[(art.id, type(art)] = art
            edict[(loc.id, type(loc)] = loc

            assert loc not in art.locations

            orm.link(edict)
            
            assert loc in art.locations

        Noticed that the keys for <edict> are tuples of the entity's id
        and type.  Usually, id is enough to distinguish between two
        entities. However, a superentity will have the same id as its
        subentity. In those cases, the class is needed to distinguish
        between the subentity and the superentity. 
        """

        # For each entity in edict
        for e in edict.values():
            
            # Does `e` have a foreign key that is the id of another
            # entity in edict, i.e., is `e` a child (or constituent) of
            # another entity in edict.
            for map in e.orm.mappings.foreignkeymappings:
                if not map.value:
                    continue

                clss = [map.entity]
                clss += [x.entity for x in map.entity.orm.subentities]
                comp = None
                for cls in clss:
                    try:
                        comp = edict[map.value.bytes, cls]
                    except KeyError:
                        pass
                    else:
                        break
                else:
                    # Composite for the FK can't be found. The
                    # object for the FK isn't in edict, perhaps
                    # because the FK corresponds to a composite
                    # on one side of an associations that wasn't
                    # loaded, e.g., given
                    # `artists().join(artist_artifacts())`,
                    # artist_artifacts will have an FK for an
                    # artist and an artifact, but only artist
                    # will have been loaded.
                    continue
                    
                # If we are here, a composite was found.

                # Chain the composite's entitiesmappings and
                # associationsmappings collection into `maps`. 
                #
                # Note we need to ascend the inheritance tree to include
                # all the superentities as well. This is for loading
                # subentity objects joined to super entity association:
                #
                #   singers.join(
                #       artist_artists('role = 'sng-art_art-role-0')
                #   )
                #
                # In the above, the `comp` will be `singers`. However,
                # `singers` has no map to `artist_artists`. Its super
                # does, though, because the `super` of `singer` is
                # `artist`.

                sup = comp
                mapgens = list()
                while sup:
                    mapgens.append(sup.orm.mappings.entitiesmappings)
                    mapgens.append(sup.orm.mappings.associationsmappings)
                    sup = sup.orm.super

                # Chain the above mapping generators so we can interate
                # over each of them in the loop below.
                maps = itertools.chain(*mapgens)

                # For each of the composite mappings, if `e` is the same
                # type as the map then assign `e` to that mappings's
                # value property.  This links entity objects to their
                # constituents (e.g., artist.locations.last)
                for map1 in maps:
                    if isinstance(e, map1.entities.orm.entity):
                        if not map1.isloaded:
                            map1._value = map1.entities()
                        map1._value += e

                # For each entity mapping of `e`, if the `comp` is the
                # same type as the mapping, then assign `comp` to that
                # mapping's value property. This links entity objects
                # with their composites (e.g., loc.artist)
                for map1 in e.orm.mappings.entitymappings:
                    if e.orm.isreflexive:
                        # If the FK (map) refers to the subject side of
                        # the association, and the entitymapping (map1)
                        # is the subject of the association, then FK's
                        # value should be the composite. The same logic
                        # applies analogously to the object side.
                        if ( 
                            (map.issubjective and map1.issubjective)
                            or 
                            (map.isobjective and map1.isobjective)
                        ):
                            map1._value = comp
                    elif map1.entity is type(comp):
                        map1._value = comp

            with suppress(KeyError):
                e.orm.super = edict[e.id.bytes, e.orm.entity.orm.super]

    # TODO Rename this to `select'
    @property
    def sql(self):
        """ Return a tuple containing the SELECT statement as the first
        element and the args list as the second.
        """
        return self._getsql()

    # TODO Rename this to `getselect'
    def _getsql(self, graph=str(), whstack=None, joiner=None, join=None):
        """ The lower-level private method which bulids and returns the
        SELECT statement for the entities (self.instance) collection
        object.

        """
        # Note, since generating the SELECT statement involves
        # recursion, we need a regular method. The user would rather
        # call a property (orm.sql), however, so this is a private
        # method normally accessed through the orm.sql method.

        def raise_fk_not_found(joiner, join):
            ''' Raise a ValueError with a FK not found message. '''

            joinerpk = joiner.entity.orm.mappings.primarykeymapping.name
            msg = 'FK not found: '

            msg += '%s.%s = %s.%s'
            msg %= (joiner.table, joinerpk, join.table, '<NOT FOUND>')

            msg += "\nIs '%s' a parent to '%s'" 
            msg %= (joiner.table, join.table)
            raise ValueError(msg)

        def alias(whs):
            """ Takes a ``where`` object or collection of ``where``
            objects and replaces their predicate's column's names with a
            fully-qualified verision that contain the table alias. 
            """
            # Convert to a collection if needed
            whs = whs if hasattr(whs, '__iter__') else [whs]
            
            # Iterate over collection
            for wh in whs:
                for pred in wh.predicate:
                    if pred.match:
                        cols = pred.match.columns
                    else:
                        cols = pred.operands

                    # Prepend `graph` to each column name
                    for i, op in enumerate(cols):
                        if not pred.iscolumn(op):
                            continue
                        col = op

                        if col in self.mappings:
                            col = '`%s`.%s' % (graph, col)
                            cols[i] = col

        # Create the where stack
        whstack = list() if whstack is None else whstack

        # Update the graph. The graph is an abbreviated table alias
        # which will grow as this method recurses into itself. 
        if graph:
            parentgraph = graph
            graph += '.' + join.entities.orm.abbreviation
        else:
            graph = self.abbreviation

        # Put the SELECT in a table so it is formatted nicely
        select = table(border=None)

        ''' SELECT '''
        # Build SELECT table for the current instance of recursion
        for map in self.entity.orm.mappings:
            if not isinstance(map, fieldmapping):
                continue

            r = select.newrow()
            abbr = '%s.%s' % (graph, map.name)

            r.newfields(abbr, 'AS', abbr, ',')

        ''' JOINS '''
        joins = str() # The string that contains the JOIN SQL

        # If a `join` object was passed in
        if join:
            
            # Prepend columns in where clause with alias
            alias(whstack)

            if join.entities.orm.issuperentity(of=joiner.entities):
                # If `joins`'s entities collection is a superentity to
                # self.entities, then the `pk` will be the PK of
                # j.entities - which will virtually always be 'id'. This
                # is because the relationship between super and
                # subentities is one-to-one so joinerpk and joineepk
                # will both always be 'id'
                id = joiner.entities.orm.mappings.primarykeymapping.name
                pk = join.entities.orm.mappings.primarykeymapping.name
            elif joiner.entities.orm.issuperentity(of=join.entities):
                id = join.entities.orm.mappings.primarykeymapping.name
                pk = joiner.entities.orm.mappings.primarykeymapping.name
            else:
                if associations in joiner.entities.mro():
                    pk = join.entities.orm.mappings.primarykeymapping.name
                    fks = joiner.entities.orm.mappings.foreignkeymappings
                    for map in fks: 
                        if joiner.entities.orm.isreflexive:
                            if map.isobjective:
                                id = map.name
                                break
                        elif join.entities.orm.entity is map.entity:
                            id = map.name
                            break
                    else:
                        raise_fk_not_found(joiner, join)
                else:
                    # Get the joineepk for the joinee table.  This block
                    # represents the typical one-to-many relationship
                    # for which we will need the foreign key of the
                    # join table.
                    id = joiner.entity.orm.mappings.primarykeymapping.name
                    fks = join.entities.orm.mappings.foreignkeymappings
                    for map in fks:
                        if join.entities.orm.isreflexive:
                            if map.issubjective:
                                pk = map.name
                                break
                        elif joiner.entities.orm.entity is map.entity:
                            pk = map.name
                            break
                    else:
                        raise_fk_not_found(joiner, join)

            # Get the join keywords (e.g., 'INNER JOIN')
            joins += '%s' % join.keywords

            # Concatenate the join table name
            joins += ' ' + join.entities.orm.table

            # Concatenate the table alias
            joins += ' AS `%s`' % graph

            # Concatenate the joiner's portion of the ON clause
            joins += '\n    ON `%s`' % parentgraph

            # Concatenate the joiner's id column name
            joins += '.' + id

            joins += ' = `%s`' % graph

            joins += '.%s\n' % pk

        ''' WHERE/args '''
        args, whs, wh = list(), list(), None
        if self.where:

            # Clone the entities' `where` object then alise its column
            # names.
            wh = self.where.clone()
            alias(wh)

            # Append the cloned `where` object and args to be returned
            # later
            whs.append(wh)
            args += wh.args

        ''' Recurse into joins '''
        for j in self.joins:
            wh and whstack.append(wh)

            # Recurse into the join to collect its SQL elements
            select1, joins1, whs1, args1 = j.entities.orm._getsql(
                graph=graph,
                whstack=whstack,
                join=j,
                joiner=self
            )

            wh and whstack.pop()

            # Collect the return values form the recursion and
            # concatenate them to the variables that will be returned by
            # the current stack frame.
            select += select1         # cat select

            joins += joins1           # cat joins

            whs.extend(whs1)          # cat wheres

            args += args1             # cat args

        # Are we recursing
        recursing = graph != self.abbreviation

        # If we are at the top-level of the function, i.e., if we are
        # not recursing...
        if not recursing:

            # Put ticks around aliases in select table
            for r in select:
                graph, col = r.fields[0].value.rsplit('.', 1)
                r.fields[0].value = '`%s`.%s' % (graph, col)
                r.fields[2].value = '`%s`' % r.fields[2].value

            # Pop the trailing comma of select field
            select.rows.last.fields.pop()

            # Concatenate the select, join, and where elements
            sql = 'SELECT\n%s\nFROM %s AS `%s` \n%s' 
            sql %= (textwrap.indent(str(select), ' ' * 4), 
                    self.table, 
                    self.abbreviation, 
                    joins)

            if whs:
                sql += 'WHERE ' 
                sql +=' AND'.join('(%s)' % x.predicate for x in whs)

            # Finally, we are done. Return the sql and the args
            # seperately because the sql will have placeholders and the
            # args will be executed in a parameterized fashion (see
            # `orm.collect()`)
            return sql, args

        return select, joins, whs, args

    @staticmethod
    def introduce(sql, args):
        """ Use ``args`` to add MySQL introducers ('_binary', et. al.)
        before the unquoted placeholder tokens (%s) in ``sql``.

        :param: str  sql:  A whole or partial SQL statement.

        :param: list args: Parameters to use with query.

        :rtype: str

        :returns: Returns the ``sql`` argument with introducers added
        where appropriate.
        """

        # Where the arg is binary (bytearray or bytes), replace '%s' with
        # '_binary %s' so it's clear to MySQL where the UTF8 SQL string 
        # becomes pure binary not intended for character decoding.
        r = str()
        insingle       =  False
        indouble       =  False
        inquote        =  False
        inplaceholder  =  False
        argix          =  0

        # Iterate over sql instead of using a simple search-and-replace
        # approach so we don't add introducer to quoted instances of the
        # placeholder token.
        for s in sql:
            # Detect quotes
            if s == "'":
                insingle = not insingle

            if s == '"':
                indouble = not indouble

            inquote = indouble or insingle

            if inplaceholder:
                if s == 's':
                    if type(args[argix]) in (bytearray, bytes):
                        # Here we add the _binary introducer because the arg is
                        # binary and we are not in quoted text
                        r += '_binary %s'
                    else:
                        # A non-binary placeholder
                        r += '%s'
                    argix += 1
                else:
                    # False alarm. The previous '%' didn't indicate a
                    # placeholder token so just append '%' + s to the return
                    # string
                    r += '%' + s

                inplaceholder = False
                continue

            # Is `s` a '%' indicating the beginning of a placeholder token (%s)
            if not inquote and s == '%':
                inplaceholder = True

            if not inplaceholder:
                # Concatentate the SQL character to the return str 
                r += s

        return r

    @property
    def isstreaming(self):
        """ Return True if the entities collection is in streaming mode.
        Streaming mode implies we are accessing the results from a
        database queries in discrete chunks. See the docstrings at
        ``orm.streaming`` for more on streaming.
        """
        return self.stream is not None

    @property
    def isdirty(self):
        """ Return True if the object is not new (exists in database)
        but has changed since it was loaded in memory::

            # Load existing entity
            ent = entity(id)
            assert not ent.orm.isdirty

            # Dirty the ent by changing a property
            ent.name += 'xxx'
            assert ent.orm.isdirty

        The isdirty flag is used internally to determine if an UPDATE
        statement needs to be issued when the save method is called::

            ent.save()
        """
        if self._isdirty:
            return True

        # Ascend the inheritence tree to see if any of the loaded supers
        # are dirty. Note that this call is inherently recursive.
        if self._super:
            return self.super.orm.isdirty

        return False

    @isdirty.setter
    def isdirty(self, v):
        """ Sets the isdirty flag.  See the isdirty getter for more.

        :param: v bool: The value to set isdirty to.
        """
        self._isdirty = v

    @property
    def forentities(self):
        """ Returns True if this ``orm`` instance corresponds to an
        orm.entities object rather than an orm.entity object.
        """
        return isinstance(self.instance, entities)
        
    @property
    def forentity(self):
        """ Returns True if this ``orm`` instance corresponds to an
        orm.entity object rather than an orm.entities object.
        """
        return isinstance(self.instance, entity)

    @property
    def persistencestates(self):
        """ Returns a list of persistencestate tuples for each of the
        entity objects in the entities collection. Useful for unit tests
        and debugging. See orm.persistencestate for more.
        """
        es = self.instance
        if not self.forentities:
            msg = 'Use with entities. For entity, use persistencestate'
            raise ValueError(msg)
            
        sts = []
        for e in es:
            sts.append(e.orm.persistencestate)
        return sts

    @persistencestates.setter
    def persistencestates(self, sts):
        """ Sets the persistencestate tuple to `sts` for each of the
        entity objects within this collection. See orm.persistencestate
        for more.
        """
        es = self.instance
        if not self.forentities:
            msg = 'Use with entities. For entity, use persistencestate'
            raise ValueError(msg)

        for e, st in zip(es, sts):
            e.orm.persistencestate = st

    @property
    def persistencestate(self):
        """ Get the persistencestate tuple for an orm.entity. Useful for
        debugging and unit testing.

        The persistencestate tuple corresponds to the isnew, isdirty and
        ismarkedfordeletion flags. The following will always be true::

            # Given an entity at any point in time:
            st = ent.orm.persistencestate
            assert  ent.orm.isnew                is  st[0]
            assert  ent.orm.isdirty              is  st[1]
            assert  ent.orm.ismarkedfordeletion  is  st[2]
        """
        es = self.instance
        if not self.forentity:
            msg = 'Use with entity. For entities, use persistencestates'
            raise ValueError(msg)
        return self.isnew, self.isdirty, self.ismarkedfordeletion

    @persistencestate.setter
    def persistencestate(self, v):
        """ Set the persistencestate for an orm.entity object. See the
        persistencestate getter for more.
        """
        es = self.instance
        if not isinstance(es, entity):
            msg = 'Use with entity. For entities, use persistencestates'
            raise ValueError(msg)
        self.isnew, self.isdirty, self.ismarkedfordeletion = v

    @property
    def trash(self):
        """ Return the trash - an entities collection the same type as
        self but intended to collect entities, but whose entity objects
        are destined for DELETion.
        """
        if not self._trash:
            self._trash = self.entities()
        return self._trash

    @trash.setter
    def trash(self, v):
        self._trash = v

    @property
    def properties(self):
        """ Returns a list of all property names for this entity
        including those inherited from superentities.
        """

        # Get list of propreties for this class
        props = [x.name for x in self.mappings]

        # Look at all the associations that this entity is envolved in
        # and add the name of the associated entity to `props`. These
        # names would be for pseudocollection access (i.e.,
        # art.artifacts).
        for map in self.mappings.associationsmappings:
            for map1 in map.associations.orm.mappings.entitymappings:

                if map1.isproprietor:
                    continue

                if self.entity is not map1.entity:
                    props.append(map1.entity.orm.entities.__name__)

        # Look for properties in the super. Not that this will ascend
        # the inheritance hierarchy until we reach the root entity.
        sup = self.super
        if sup:
            props += [x for x in sup.orm.properties if x not in props]

        return props

    def issuperentity(self, of):
        """ Returns True if ``self`` is a super entity of ``of``, False
        otherwise.
        """
        return self.entity in of.orm.entity.orm.superentities

    @staticmethod
    def issub(obj1,  obj2):
        """ Returns true if obj1 is a subentity of obj2, False
        otherwise.

            :param: obj1  An entities class
            :param: obj2  An entities class
        """
        if not (isinstance(obj1, type) and isinstance(obj2, type)):
            msg = 'Only static types are currently supported'
            raise NotImplementedError(msg)

        cls1, cls2 = obj1, obj2

        # TODO s/super/sup/
        super = cls2

        while super:
            if super is cls1:
                return True
            super = super.orm.super

        return False

    @property
    def sub(self):
        """ Returns the subentity of ``self``::
            
                # Get a good
                good = product.good(goodid)

                # Get the superentity: a product instance
                prod = good.orm.super

                # prod's sub is the good
                assert prod.orm.sub is good

            In the above example, the call to ``sub`` does not result in
            a call to the database becase the prior call to ``super``
            stores a reference to the ``good`` object. However, a
            database call will be made if necessary::

                # Get a product
                prod = product.product(prodid)

                # A database call will be made here to get the
                # subentity. If the product is not a good (perhaps it's
                # a service), a db.RecordNotFoundError will be raised.
                good = prod.orm.sub
        """
        if self.isstatic:
            raise ValueError(
                'Cannot call sub on static entity'
            )

        if self._sub is undef:
            for cls in self.subentities:
                try:
                    self._sub = cls(self.instance.id)
                except db.RecordNotFoundError:
                    continue
                else:
                    break
            else:
                self._sub = None

        return self._sub

    @sub.setter
    def sub(self, v):
        """ Set the subentity. Setting the sub will typically not be
        done by the ORM user.

        :param: v orm.entity: The orm.entity being assigned as a
        subentity of self.
        """
        self._sub = v
            
    @property
    def supers(self):
        """ Return a list of superentity class references of self.
        """
        if self.isstatic:
            return [
                x for x in self.entity.__mro__[1:]
                if entity in x.__mro__[1:]
            ]
        else:
            # TODO
            # 1. Create an orm.entities instance for the most general
            #    type
            # 2. Add each super starting with self's to the collection
            # 3. Return the collection
            raise NotImplementedError(
                'orm.supers has not yet be implemented when '
                'orm.isinstance'
            )

    @property
    def super(self):
        """ For orm's that have no instance, return the super class of
        ``orm.entity``.  If orm.instance is not None, return an instance
        of that object's superentity.  A superentity means the base
        class of an entity class where the base itself is not
        ``orm.entity``, but rather a subclass of ``orm.entity``. So if
        class A inherits directly from ``orm.entity``, it will have a
        superentity of None. However if class B inherits from A. class B
        will have a superentity of A."""
        if self._super:
            return self._super

        if self._base is not undef:
            return self._base

        if self.entity:
            bases = self.entity.__bases__
            try:
                base = bases[0]
            except IndexError:
                base = None

            if base in (entity, association):
                self._base = None
                return self._base

            if self.isstatic:
                self._base = base
                return self._base

            elif self.isinstance:
                if self.isnew:
                    # Preserve subentity's id. When ._super is set,
                    # `self.instance.id` will change to the value of
                    # `self._super.id`.
                    id = self.instance.id
                    self._super = base()

                    # Set the super's id to self's id. Despite the
                    # fact that self.isnew, its existence is in some
                    # cases meaningful and should be preserved.
                    self._super.id = id
                else:
                    e = self.instance
                    if not isinstance(e, entity):
                        msg = "'super' is not an attribute of %s"
                        msg %= str(type(e))
                        raise builtins.AttributeError(msg)
                    if e.id is not undef:
                        self._super = base(e.id)

                # Ensure the super has a reference to the sub
                # (self.instance).
                self._super.orm.sub = self.instance

                return self._super
        return None

    @super.setter
    def super(self, v):
        self._super = v

    @property
    def isstatic(self):
        """ Returns True if the ``orm`` instance is being called from a
        class reference, False if the ``orm`` instance is being called
        from an instance. The antonym of ``isstatic`` is ``isinstance``.

            assert product.good.orm.isstatic
            assert not product.good().orm.isstatic
        """
        return self.instance is None

    @property
    def isinstance(self):
        """ Returns True if the ``orm`` instance is being called from a
        entity instance, False if the ``orm`` instance is being called
        from a class reference. The antonym of ``isinstance`` is
        ``isstatic``.

            assert product.good().orm.isinstance
            assert not product.good.orm.isinstance
        """

        return self.instance is not None

    def getsupers(self, withself=False):
        """ Returns a list of entity classes or entity objects
        (depending on whether or not self.isinstance) of which self is a
        subentity.

        By default this returns the same output as orm.superentities.

        :param: withself bool: If True, ``self`` will be the first
        element in the list.
        """
        r = list()

        if withself:
            if self.isinstance:
                r.append(self.instance)
            elif self.isstatic:
                r.append(self.entity)
            else:
                raise ValueError(
                    'Orm object must be instance or static'
                )

        r.extend(self.superentities)
        return r 

    @property
    def superentities(self):
        """ Returns a list of entity classes or entity objects
        (depending on whether or not self.isinstance) of which self is a
        subentity.
        """

        # TODO Rename to ``supers`` to compliment the ``super`` method.

        r = list()

        e = self.super

        while e:
            r.append(e)
            e = e.orm.super

        return r

    # TODO This should probably be renamed to `subs`
    @property
    def subentities(self):
        """ Returns a collection all the of class reference that inherit
        from this class.
        """
        if self._subclasses is None:
            clss = ormclasseswrapper()
            for sub in orm.getsubclasses(of=self.entity):
                clss += sub
            self._subclasses = clss
        return self._subclasses

    @staticmethod
    def getsubclasses(of, recursive=True):
        """ Return all subclasses of ``of`` as a list. 

        Subclasses obviously represent a tree structure, however this
        method returns a list. The subclasses of a given depth are
        ordered contigously with one another. The highest subclasses
        come first.  For example, ``orm.getsubclasses(of=artist)``
        returns::

            ['singers', 'painters', 'rappers']

        `singers` and `painters` come first because they are direct
        childern of `artist`. `rappers` comes third because it is a
        direct child of `singers`.

        :param: of type<orm.entity>: The class reference for which the
        subclasses will be returned.

        :param: recursive bool: If True, descend the inheritence tree in
        search of subentities. If False, only collect the immediate
        subentity class references.
        """
        r = []

        for sub in of.__subclasses__():
            if sub not in (associations, association):
                r.append(sub)

        if recursive:
            for sub in of.__subclasses__():
                r.extend(orm.getsubclasses(sub))

        return r

    @staticmethod
    def getassociations():
        """ Returns a list of all association classes, i.e., those
        classes that inherit from ``orm.association``.
        """
        return orm.getsubclasses(of=association)

    @staticmethod
    def getentity(name=None, abbr=None):
        """ Search for classes that inherit from ``orm.entity`` that
        match either ``name`` or ``abbr``. Returns the entity class that
        matches.

        :param: name str: The name of the entity to search for. This
        corresponds to the class's ``__name__`` attribute.

        :param: abbr str: The abbreviation of the entity to search for.
        This corresponds to the class's ``orm.abbreviation`` attribute.
        (See the ``orm.abbreviation`` getter for more).
        """

        # Cat the entity classes and the association classes into a
        # collection.
        es = orm.getentitys() + orm.getassociations()

        if name:
            # Lookup entity/association class by name.
            if not orm._namedict:
                for e in es:
                    orm._namedict[e.__name__] = e

            return orm._namedict[name]
            
        elif abbr:
            # Lookup entity/association class by abbreviation.
            if not orm._abbrdict:
                for e in es:
                    orm._abbrdict[e.orm.abbreviation] = e

            return orm._abbrdict[abbr]

    # TODO s/getentitys/getentityclasses/
    @staticmethod
    def getentitys(includeassociations=False):
        """ A static method to collect and return all the classes that
        inherit directly or indirectly from orm.entity. If
        includeassociations is True, return the classes that inherit
        from orm.association as well.

        :param: includeassociations bool: If True, include the classes
        that inherit from orm.association as well.
        """
        r = []
        for e in orm.getsubclasses(of=entity):
            if includeassociations:
                r += [e]
            else:
                if association not in e.mro():
                    if e is not association:
                        r += [e]

        # Collect duplicates
        tbls = set()
        dups = list()
        for e in r:
            if e.orm.table in tbls:
                dups.append(e)
                continue

            tbls.add(e.orm.table)

        # Remove duplicates
        for dup in dups:
            r.remove(dup)

        return r

    @staticmethod
    def getentities():
        """ Return all classes that inherit directly or indirectly from
        ``orm.entities`` as a list. Note that ``orm.associations`` are
        not included.
        """
        r = []
        for es in orm.getsubclasses(of=entities):
            if association not in es.mro():
                if es is not association:
                    r += [es]
        return r

    @property
    def associations(self):
        """ Return all association classes for which this entity has
        attributes.
        """
        if not self._associations:
            self._associations = ormclasseswrapper()
            for ass in orm.getassociations():
                for map in ass.orm.mappings.entitymappings:
                    if map.entity is self.entity:
                        self._associations += ormclasswrapper(ass)

        return self._associations
            
    @property
    def composites(self):
        if not self._composits:
            self._composits = composites()
            for sub in self.getsubclasses(of=entity):
                for map in sub.orm.mappings.entitiesmappings:
                    if map.entities.orm.entity is self.entity:
                        self._composits += composite(sub)
                        break

            for ass in self.getassociations():
                maps = list(ass.orm.mappings.entitymappings)
                for i, map in enumerate(maps):
                    if map.name == 'proprietor':
                        continue
                    if orm.issub(map.entity, self.entity):
                        if ass.orm.isreflexive:
                            if map.issubjective:
                                continue
                        e = maps[int(not bool(i))].entity
                        self._composits += composite(e)

        return self._composits

    @property
    def constituents(self):
        if self._constituents is None:
            self._constituents = constituents()
            for map in self.mappings.entitiesmappings:
                e = map.entities.orm.entity
                self._constituents += constituent(e)

            for ass in self.getassociations():
                maps = list(ass.orm.mappings.entitymappings)
                for i, map in enumerate(maps):
                    if map.entity is self.entity:
                        if ass.orm.isreflexive:
                            if map.issubjective:
                                continue
                        e = maps[int(not bool(i))].entity
                        self._constituents += constituent(e)
        return self._constituents

class associations(entities):
    """ Holds a collection of ``orm.association`` objects. 
    """

    def __init__(self, *args, **kwargs):
        """ Constructs an association collection.
        """
        super().__init__(*args, **kwargs)
        self.orm.composite = None

        # NOTE, in entities collections, the orm._constituents is of
        # type `constituents` which is an `ormclasseswrapper`.  However,
        # here we simply want it to be a dict.

        # Also:ce6ea883 NOTE that making _constituents either a dict or
        # an entities collection has already caused a problem because
        # dict.__getitem__ throws a KeyError when there is no element
        # found and an entities collection would through an IndexError
        # because it wants to conform to the interface of a list()
        # whenever possible. (See ce6ea883). We may want _constituents
        # to always be a `constituents(ormclasseswrapper)` class.
        self.orm._constituents = dict()

    def append(self, obj, uniq=False, r=None):
        """ Adds a ``orm.association`` entity to the collection.

        :param: obj orm.association: The association object to append.

        :param: uniq bool: If True, only adds the object if it does not
        already exist.

        :param: r list: An `entities` collection containing the objects
        that were added.
        """

        # If `obj` is an `association`, set it's `composite` to the
        # `self`'s `composite`, e.g.::
        #
        #     artist_artifact.artist = self.orm.composite
        # 
        # Otherwise, pass `obj` to the `super()`'s `append()` method. In
        # this case, it will likely be an a collection of `association`
        # objects.
        comp = self.orm.composite
        if isinstance(obj, association):
            # Backup obj so we can use it to ascend inheritance tree
            obj1 = obj 

            # We will continue up the inheritance tree until we find a
            # map that corresponds to the composite. We will set the
            # map's value to the composite.
            while obj:
                for map in obj.orm.mappings.entitymappings:
                    # TODO We probably should be using the association's
                    # (self) mappings collection to test the composites
                    # names. The name that matters is on the
                    # left-hand-side of the map when being defined in
                    # the association class.
                    if self.orm.isreflexive:
                        if map.issubjective:
                            # NOTE self.orm.composite can be None when the
                            # association is new. Calling 
                            #
                            #     settattr(obj, map.name, None)
                            #
                            # results in an error. The alternative block
                            # avoided this because the following will
                            # always be False. 

                            # TODO We need to only run this code:
                            #    
                            #     if self.orm.composite
                            #         self.name == type(None).__name__ 
                            #
                            # Or we could make the setattr() call accept a
                            # composite of None.
                            if comp is not None:
                                
                                # TODO map.name will always be 'subject'
                                # here. Don't we want it to be
                                #
                                #     `self.orm.composite.__class__.__name__` 
                                #
                                # Unfortately, when this is corrected,
                                # several issues result when running the
                                # tests.
                                setattr(obj, map.name, comp)
                                break
                    elif isinstance(comp, map.entity):
                        setattr(obj, map.name, comp)
                        break
                else:
                    obj = obj.orm.super  # Ascend
                    continue
                break

            # Restore `obj` to its original reference
            obj = obj1

            for map in obj.orm.mappings.entitymappings:
                if not map.isloaded:
                    continue

                # self.orm.composite will not exist when loading the
                # association.
                if not comp:
                    continue

                # When a reflexive association has an entitymap other
                # than `object` (this could be `subject` or some
                # arbitrary entity map such as `myassociationstype`), an
                # attempt to get the pseudocollection will result in an
                # AttributeError below. We want to skip this map
                # entirely. 
                
                # TODO Note that this raise the issue of what happens
                # when a non-reflexive association has an entity map
                # that isn't a part of the association:
                #
                #    class person_movie(association):
                #        person = person
                #        movie  = movie
                #        genre  = genre 
                # 
                # At the moment, it's not clear how `genre` would not
                # get included in this loop. We would expect an
                # AttributeError if we did this:
                #
                #     pms += person_movie(
                #         person=per, movie=mov, genre=gen
                #     )

                if self.orm.isreflexive and not map.isobjective:
                    continue

                compsups = [comp.orm.entity] \
                           + comp.orm.entity.orm.superentities

                if (
                    self.orm.isreflexive and map.isobjective
                    or (map.entity not in compsups)
                ):
                    try:
                        # Get pseudocollections
                        es = getattr(
                            self, 
                            map.value.orm.entities.__name__
                        )

                    except builtins.AttributeError:
                        # If the object stored in map.value is the wrong
                        # type, use the map.entity reference. This is
                        # for situations where the user appends the
                        # wrong type, but we don't want to raise an
                        # error, instead prefering that the error is
                        # discovered in the brokenrules collection. See
                        # it_doesnt_raise_exception_on_invalid_attr_values
                        # where a `location` object is being appended to
                        # an `artifact`'s pseudocollection.
                        es = getattr(
                            self, 
                            map.entity.orm.entities.__name__
                        )

                    # Remove the 'entities_onadd' event handlers when
                    # adding to the pseudocollections so they don't
                    # recursively call back into this method to add
                    # association objects. The event handlers are
                    # restored in the `finally` block.

                    # TODO Tighten up code
                    meths = [
                        x for x in es.onadd 
                        if x.__name__ == 'entities_onadd'
                    ]

                    try:
                        for meth in meths:
                            es.onadd -= meth

                        # Add map's value to pseudocollection

                        # NOTE We may want to override __contains__ such
                        # that `map.value not in es` does the same thing.
                        # Currently, identity comparisons will be done.
                        if map.value.id not in [x.id for x in es]:
                            es += map.value
                    finally:
                        # Restore entities_onadd handlers
                        for meth in meths:
                            es.onadd += meth

        super().append(obj, uniq, r)
        return r

    def _self_onremove(self, src, eargs):
        """ This event handler is called when an ``association`` is
        removed from an ``associations`` collection. When this happens, we
        want to remove the ``association``'s constituent entity (the
        non-composite entity) from its pseudocollection class - but only
        if it hasn't already been marked for deletion
        (ismarkedfordeletion). If it has been marked for deletion, that
        means the pseudocollection class is invoking this handler - so
        removing the constituent would result in infinite recursion.  
        """

        # NOTE We seemed to be cascading deletes of association entity
        # classes. I don't see why that is a good idea.
        ass = eargs.entity

        isreflexive = ass.orm.isreflexive

        for i, map in enumerate(ass.orm.mappings.entitymappings):

            # We wouldn't want to delete a proprietor or owner just
            # because we are deleting one of its association objects.
            if map.isproprietor or map.isowner:
                continue

            if isreflexive:
                cond = map.isobjective
            else:
                cond = map.entity is not type(self.orm.composite)

            if cond:
                e = map.value
                if e and not e.orm.ismarkedfordeletion:
                    # Get the pseudocollection
                    es = getattr(self, e.orm.entities.__name__)
                    es.remove(e)

                    # When removing an entity from a pseudocollection
                    # class, the class will inevitably trash the removed
                    # entity to mark it for removal from the database.
                    # However, this would mean that removing an
                    # association from the DB would cause the
                    # constituents (artifact) object to removed from the
                    # DB (cascading deletes). This is not what we want:
                    # We should be able to delete as association between
                    # two entity object without deleting the entities
                    # themselves.  pop()ing the entity off the trash
                    # collection will prevent the constituents from
                    # being deleted.

                    # Commenting out until it_removes_*_associations is
                    # fixed
                    #es.orm.trash.pop()

                    break
            
        super()._self_onremove(src, eargs)

    def entities_onadd(self, src, eargs):
        """ An event handler invoked when an entity is added to the
        association (``self``) through the association's
        pseudocollection, e.g.::

            # Create artist entity
            art = artist()            

            # Add artifact entity to the artist's pseudocollection
            art.artifact += artifact() 

        :param: src entities: The pseudocollection's entities object.

        :param: eargs eventargs: The event arguments. Its ``entity``
        property is the entity object being added to the
        pseudocollection.

        """
        ass = None

        # Create a list of the type of eargs.entity as well as its
        # superentities
        sups = eargs.entity.orm.entity.orm.superentities
        sups.append(type(eargs.entity))

        # Look through the association collection's (self's) entity
        # mappings for one that matches eargs.entity. That
        # entity mapping will refer to the association's reference to
        # the entity being added.
        for map in self.orm.mappings.entitymappings:

            # Test map.entity against sups. When a non-subentity is
            # added to the pseudocollection, we would only need to test
            # against `type(eargs.entity)`. However, when subentity
            # objects (singer) are added to super-associations
            # (artist_artists), we will need to check the superentities.
            if map.entity in sups:

                # If we are adding entity object's to reflexive
                # association collection, we add them as the 'object' of
                # the association.
                if not (self.orm.isreflexive and not map.isobjective):
                    for ass in self:
                        # For non-subentity objects, we could just do an
                        # identity comparison. However, if a subentity
                        # was added to the pseudocollection, we can and
                        # must compare the id's since the subentity's id
                        # will match its superentity's id.

                        # Get the entity object of the association. 
                        #
                        # NOTE that it will be None in cases when the
                        # association does not have the data to find the
                        # entity (such as a null value for the entity's
                        # id). In this case, ass.invalid is True so we
                        # continue to the next association.
                        e = getattr(ass, map.name)

                        if e and e.id == eargs.entity.id:
                            # eargs.entity already exists as a
                            # constituents entity in this collection of
                            # associations. There is no need to add it
                            # again.
                            return

                    # eargs.entity is not a constituent entity in this
                    # collection of associations yet so create a new
                    # association and assign eargs.entity to it.
                    ass = self.orm.entity()
                    setattr(ass, map.name, eargs.entity)

            if self.orm.isreflexive:
                if map.issubjective:
                    compmap = map
            elif map.entity is type(self.orm.composite):
                compmap = map
        
        if ass is None:
            # If ass is None, there was an issue. Likely the user
            # attempted to assign the wrong type of object to a
            # pseudocollection (e.g., art.artifacts = locations()).
            # Since we don't want to raise exceptions in cases like
            # these (preferring to allow the brokenrules property to
            # flag them as invalid), we will go ahead and create a new
            # association referencing the invalid composite
            # (eargs.entity) instead.
            ass = self.orm.entity()
            for map1 in ass.orm.mappings.entitymappings:

                # Ignore if it's the `ass`'s proprietor's or owner's
                # entitymapping
                if map1.isproprietor or map1.isowner:
                    continue

                if map1.name != compmap.name:
                    setattr(ass, map1.name, eargs.entity)

        # Assign the association collections's `composite` property to
        # the new association object's composite field; completing the
        # association
        setattr(ass, compmap.name, self.orm.composite)
        self += ass

    def entities_onremove(self, src, eargs):
        for map in self.orm.mappings.entitymappings:
            if map.entity is type(eargs.entity):
                for ass in self:
                    if getattr(ass, map.name) is eargs.entity:
                        break
                else:
                    continue
                break
        else:
            return

        self.remove(ass)

    def __getattr__(self, attr):
        """
        Return a composite object or constituent collection
        (pseudocollection) requested by the user.

        :param: str attr: The name of the attribute to return.
        :rtype: orm.entity or orm.entities
        :returns: Returns the composite or pseudocollection being
                  requested for by ``attr``
        """

        def raiseAttributeError():
            """ Raise a generic AttributeError.
            """
            msg = "'%s' object has no attribute '%s'"
            msg %= self.__class__.__name__, attr
            raise builtins.AttributeError(msg)

        # TODO Use the mappings collection to get __name__'s value.

        # If `attr` matches the association composite, return the
        # composite.  This is for the less likely case where the ORM
        # user is requesting the composite of the associations
        # collection, e.g.,:
        #
        #     art.artist_artifacts.artist
        #
        # Note that `assert art is art.artist_artifacts.artists`.
        #
        # The ascension loop as added for subentities, e.g.,
        #
        #     assert sng.orm.super is sng.artist_artists.artist 

        comp = self.orm.composite
        sups = None
        while comp:
            name = type(comp).__name__

            if attr == name:
                return comp

            if sups is None:
                sups = comp.orm.entity.orm.superentities
                sups = [x.__name__ for x in sups]

            if attr not in sups:
                break

            comp = comp.orm.super

        try:
            # Return a memoized constituent. These are created in the
            # `except KeyError` block.
            return self.orm.constituents[attr]
        except KeyError:
            for map in self.orm.mappings.entitymappings:
                # TODO Remove paranthesis
                if (self.orm.isreflexive and not map.isobjective):
                    continue

                # Get the entity for the entity map then concatenate
                # it with its subentities.
                # TODO Clean this up a little
                ess = [map.entity.orm.entities]
                ess.extend(
                    x.entity.orm.entities 
                    for x in map.entity.orm.subentities
                )

                # Iterate down the inheritance tree until we find an
                # entity/subentity with the name of the attr.
                # NOTE For most request, the entity (ess[0]) will be
                # what we want. Subentities will be needed when we
                # request a pseudocollection that is a subtype of the
                # association's objective entity:
                #    sng.<artist_artist>.singers
                for es in ess:
                    if es.__name__ == attr:
                        # Create a pseudocollection for the associations
                        # collection object (self). Append it to the self.orm's
                        # `constituents` collection.
                        es = es()
                        es.onadd    += self.entities_onadd
                        es.onremove += self.entities_onremove
                        self.orm.constituents[attr] = es
                        break
                else:
                    continue
                break
            else:
                raiseAttributeError()

            # Get all the entity objects stored in `self` then add them
            # in to the pseudocollection (es).
            for ass in self:
                e = getattr(ass, map.name) # :=
                if e:
                    # If the type of `e` does not match the `attr` str,
                    # but `attr` is a subentity of e, a
                    # subentity that matches the collection type of `es`
                    # is needed. This is required for reflexive subentity
                    # associations, e.g., consider lazy-loading the
                    # singers pseudocollection from a singer object.
                    #
                    #     assert singer is type(sng.singers.first)
                    #
                    # Without this downcasting, the following would be
                    # true:
                    #
                    #     assert artist is type(sng.singers.first)

                    #if e.orm.entities.__name__ != attr:

                    # TODO This could use a clean up, e.g.,
                    #     if attr in e.orm.subentities:
                    
                    subs = [
                        x.orm.entities.__name__ 
                        for x in e.orm.subentities
                    ]

                    if attr in subs:
                        try:
                            e = es.orm.entity(e.id)
                        except db.RecordNotFoundError:
                            continue
                    elif attr != e.orm.entities.__name__:
                        # In the line above: 
                        #
                        #     e = getattr(ass, map.name) # :=
                        #
                        # `e` will already be a subentity so the
                        # conditional `if attr in subs` will be false.
                        # However, it could be the wrong subentity
                        # bucause `attr` dosen`t match `e`.  This block
                        # prevents `e` from being appended to `es`
                        # because, if we are here, `getattr(ass,

                        # map.name)` is the wrong subtenity.
                        continue
                    es += e

            # Return pseudocollection.
            return es
        except Exception:
            raiseAttributeError()
    
class association(entity):
    pass

class migration:
    def __init__(self, e=None):
        self.entity = e

    @property
    def entities(self):
        r = entitiesmod.entities()
        es = orm.getentitys(includeassociations=True)
        tbls = db.catelog().tables

        for e in es:
            if not tbls(e.orm.table):
                # The model `e` has no corresponding table, so it should
                # probably be CREATEd
                r += ormclasswrapper(e)

        for tbl in tbls:
            for e in es:
                if e.orm.table == tbl.name:
                    break
            else:
                # `tbl` exist in database but not in model, so should
                # probably be DROPped.
                r += tbl 
                continue

            if not e.orm.ismigrated:
                # The ``e`` entity has an corresponding table, but the
                # table is not "migrated" (it differs from the model),
                # so it should probably be ALTERed.
                r += ormclasswrapper(e)

        return r

    @property
    def table(self):
        tbl = table()

        row = tbl.newrow()

        e = self.entity

        maps = mappings(
            initial=(
                x for x in e.orm.mappings 
                if isinstance(x, fieldmapping)
            )
        )

        cols = e.orm.dbtable.columns

        cnt = max(maps.count, cols.count)

        row.newfields(
            f'Model: {e.__module__}.{e.__name__}', str(), 
            f'Table: {e.orm.table}', str()
        )

        for i in range(cnt):
            map = maps(i)

            if not isinstance(map, fieldmapping):
                continue

            col = cols(i)

            if map.name == col.name:
                row = tbl.newrow()
                row.newfields(
                    map.name, map.definition, 
                    col.name, col.definition
                )

        return tbl

    @property
    def table1(self):
        tbl = table()

        row = tbl.newrow()

        e = self.entity

        maps = mappings(
            initial=(
                x for x in e.orm.mappings 
                if isinstance(x, fieldmapping)
            )
        )

        cols = e.orm.dbtable.columns

        row.newfields(
            f'Model: {e.__module__}.{e.__name__}', str(), 
            f'Table: {e.orm.table}', str()
        )

        mapdefs = [f'{x.name} {x.definition}' for x in maps]
        coldefs = [f'{x.name} {x.definition}' for x in cols]


        # TODO REMOVE ME

        mapdefs = (
            'id primary key',
            'middle varchar(255)',
            'last varchar(255)',
            'first varchar(255)',
            'email varchar(255)',
            'dob date',
        )

        coldefs = (
            'id int',
            'first varchar(255)',
            'middle varchar(255)',
            'last varchar(255)',
            'email varchar(255)',
            'dob date',
        )

        opcodes = SequenceMatcher(None, coldefs, mapdefs).get_opcodes()

        for tag, i1, i2, j1, j2 in opcodes:
            if tag == 'equal':
                gen = zip(mapdefs[j1:j2], coldefs[i1:i2])

                for mapdef, coldef in gen:
                    row = tbl.newrow()
                    row.newfields(mapdef, coldef)

            elif tag == 'delete':
                for coldef in coldefs[i1:i2]:
                    row = tbl.newrow()
                    row.newfields('', coldef)
            elif tag == 'insert':
                for mapdef in mapdefs[j1:j2]:
                    row = tbl.newrow()
                    row.newfields(mapdef, '')
            elif tag == 'replace':
                gen = zip(mapdefs[j1:j2], coldefs[i1:i2])

                for mapdef, coldef in gen:
                    row = tbl.newrow()
                    row.newfields(mapdef, coldef)
            else:
                raise ValueError()


        return tbl


    def __repr__(self):
        if self.entity.orm.ismigrated:
            return str()

        return f'{self.table}\n{self.entity.orm.altertable}'
            
# ORM Exceptions
class InvalidColumn(ValueError): pass
class InvalidStream(ValueError): pass
class ConfusionError(ValueError): pass

class ProprietorError(ValueError):
    """ An error caused by the proprietor not being set correctly for
    the given operation.
    """

    def __init__(self, actual, expected=None):
        """ Initialize the exception.

        :param: party.party actual: The proprietor that is being used.
        :param: party.party expected: The proprietor that was expected.
        """
        self.actual = actual
        self._expected = expected

    @property
    def expected(self):
        if not self._expected:
            return security().proprietor
        return self._expected

    def __str__(self):
        expected = self.expected.id.hex if self.expected else None
        return (
            f'The expected proprietor did not match the actual '
            f'proprietor; actual {self.actual.id.hex}, expected: '
            f'{expected}'
        )

    def __repr__(self):
        return str(self)

class AuthorizationError(PermissionError):
    """ An exception that indicates the currently that the current
    user is unable to create, retrieve, update or delete a record in the
    database.

    The ORM logic in orm.py will usually through this exception. The
    ORM user indicates authorization problems in the accessibility
    properties by return a ``violations`` collection.
    """
    def __init__(self, msg, crud, vs=None, e=None):
        """ Initialize the exception.

        :param: msg str: The exception's error message.

        :param: crud str: The type of access. Can be either 'c' (create)
        'r' (retrieve), 'u' (update) or 'd' (delete).

        :param: vs violations: A ``violations`` collection.

        :param: e entity: The instance of an orm.entity for which the
        authorization is denined.
        """
        crud = crud.lower()
        if crud not in 'crud':
            raise ValueError(
                'crud argument must be "c", "r", "u" or "d"'
            )


        self.message     =  msg
        self.crud        =  crud
        self.violations  =  vs if isinstance(vs, violations) else None
        self.entity      =  e

        super().__init__(msg)

class violations(entitiesmod.entities):
    """ A collection of accessibility violations. Returned by the
    accessibility properties of orm.entity to indicate that the there
    are zero or more problems with the user attempting to persist or
    retrive an entity and what those problems are.
    """
    def __init__(self, *args, **kwargs):
        """ Initialize the violations object.

        :param: entity orm.entity: The instance of an orm.entity on
        which the the violations collection is reporting. Note, this
        must be passed in as a kwargs::
            
            vs = violations(entity=self)

        """

        # Get the entity reference and delete it so we can pass it to
        # super().__init__
        try:
            e = kwargs['entity']
        except KeyError:
            e = None
        else:
            del kwargs['entity']
                
        super().__init__(*args, **kwargs)
        self.entity = e

    def __iadd__(self, o):
        """ Add `o` to the violations collection. `o` can be a str or a
        violation instance::

            @proprety
            def retrievability(self):
                vs = violations(entity=self)
                if hr not in usr.departments:
                    vs += (
                        'Only user in hr can retrive this entity'
                    )
                return vs

        :param: o str|orm.violation: A str or violation to add to the
        collection.
        """
                
        # Convert str to violaton
        if isinstance(o, str):
            o = violation(o)

        # Keep track of the collection
        o.violations = self

        # Do the actual appending
        return super().__iadd__(o)

class violation(entitiesmod.entity):
    """ Records an access violation message. Access violations are
    created in an entity's accessibility properties.
    """
    def __init__(self, msg, vs=None):
        """ Creates a violation.

        :param: msg str: The textual message that explains why access to
        a particular CRUD operation was denied.

        :param: vs orm.violations: The ``violations`` collection that
        this violation object is a member of.
        """
        self.message = msg
        self.violations = vs

    @property
    def entity(self):
        """ The instance of an orm.entity for which the authorization is
        denined.
        """
        if self.violations:
            return self.violations.entity

        return None
        

        


