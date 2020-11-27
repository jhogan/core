# vim: set et ts=4 sw=4 fdm=marker

########################################################################
# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2020
########################################################################

"Simplicity is complexity resolved." 
    # Constantin Brancusi, Romanian Sculptor

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
    
    TODO:In the GEM, change all date and datetime attributes to past
    tense, e.g., s/acquiredat/acquired/
    
    TODO There should be a standard for association class names that makes
    them predictable. Perhaps the should be alphabetical. For example,
    given an association that associates an ``effort`` and an ``item``,
    the name should be ``effort_item`` instead of ``item_effort``, since
    the former is alphabetized. This would help to locate them faster and
    to use them in code more efficiently.

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

@unique
class types(Enum):
    """
    An ``Enum`` contanining members which represent the basic data types
    supported by the ORM such as ``str``, ``int``, ``datetime`` as well as
    ``pk`` (primary key) and ``fk`` (foreign key).  
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
    
    Many entities in the GEM require date(time) fields with names like
    ``begin`` and ``end`` to record the time an entity has been in a
    certain state. For example::

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
        begin = 'begin'
        if self.prefix:
            begin = self.prefix + begin

        if self.suffix:
            begin += self.suffix

        return begin

    @property
    def str_end(self):
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
        return getattr(self.entity, self.str_begin)

    @begin.setter
    def begin(self, v):
        setattr(self.entity, self.str_begin, v)

    @property
    def end(self):
        return getattr(self.entity, self.str_end)

    @end.setter
    def end(self, v):
        setattr(self.entity, self.str_end, v)

    def __contains__(self, dt):
        if type(self) is timespan:
            dt = primative.datetime(dt)
        elif type(self) is datespan:
            dt = primative.date(dt)
        else:
            raise TypeError('Invalid span')

        return (self.begin is None or dt >= self.begin) and \
               (self.end   is None or dt <= self.end)

    def iscurrent(self):
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
    """
    ``stream`` objects are used to configure ``entities``. Passing a ``stream``
    object to an ``entities`` ``__init__`` method instructs the `entities`
    object to function in streaming/chunking mode.
    """

    def __init__(self, chunksize=100):
        """ Sets the chunksize of the stream object.

        :param: int chunksize: The number of records to load (or chunk)
                at a time.
        """
        self.cursor = self.cursor(self)
        self.chunksize = chunksize
        self.orderby = ''

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
            if self._chunk is None:
                wh = self.entities.orm.where
                if wh: # :=
                    args1 = str(wh.predicate), wh.args 
                else:
                    args1 = tuple()
                self._chunk = type(self.entities)(*args1)
                self._chunk.orm.ischunk = True

            return self._chunk

        @property
        def entities(self):
            return self.stream.entities

        def __contains__(self, slc):
            slc = self.normalizedslice(slc)
            return self.start <= slc.start and \
                   self.stop  >= slc.stop

        def advance(self, slc):
            """
            Advance the cursor in accordance with the ``slice`` argument's
            ``start`` and ``stop`` properties. If the slice calls for data
            not currently loaded in the ``chunk`` collecion, the ``chunk``
            is cleared and loaded with new data from the database.

            :param: slice slc: The ``start`` and ``stop`` properties of the
                               slice indicate which rows in the stream to 
                               which the cursor should be advanced.
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
                    # TODO es[3:3] or es[3:2] will produce empty results like
                    # lists do. However, es[3:-1] should produces a non-empty
                    # result (also like lists). However, this case is currently
                    # unimplemented.
                    msg = 'Negative stops not implemented'
                    raise NotImplementedError(msg)
                return self.chunk[0:0]

            # Does the chunk need to be reloaded to get the data requested by
            # the slice?
            if slc not in self or not self.chunk.orm.isloaded:
                self._start = slc.start
                self._stop = slc.stop

                self.chunk.orm.reload(self.stream.orderby, self.limit, self.offset)
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
    """ A collection of ``join`` classes.
    """
    def __init__(self, initial=None, es=None):
        # NOTE In order to conform to the entitiesmod.entities.__init__'s
        # signature, we have to make es=None by default. However, we actually
        # don't want es to have a default, so we simulate the behavior here.
        if es is None:
            raise TypeError(" __init__() missing 1 required keyword argument: 'es'")

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
        """
        Returns the entities's abbreviation 

        :rtype: str
        :returns: Returns the entities's abbreviation 
        """
        return self.entities.orm.abbreviation

    @property
    def wheres(self):
        return wheres(initial=[x.where for x in self if x.where])

class join(entitiesmod.entity):
    """ Represents an SQL JOIN clause. 
    
    An entities collection class can have zero or more join objects in
    its ``joins`` collection. These are used to generate the JOIN
    portion of its SELECT statement (``entities.orm.sql``).
    """
    
    # Constants for the types of a join. Currently, noly INNER JOINS are
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
            msg = 'Entities cannot be joined to streaming entities'
            raise InvalidStream(msg)
            
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
        """ Get the SQL keyword for the join type. """
        if self.type == join.Inner:
            return 'INNER JOIN'
        elif self.type == join.Outer:
            msg = 'Left outer joins are not currently implemented'
            raise NotImplementedError(msg)
            return 'LEFT OUTER JOIN'
        else:
            raise ValueError('Invalid join type')

    def __repr__(self):
        """ Returns a representation of the ``join`` object useful for
        debugging. """
        name = type(self.entities).__name__
        typ = ['INNER', 'OUTER'][self.type == self.Outer]
        return 'join(%s, %s)' % (name, typ)

class wheres(entitiesmod.entities):
    """ A collection of ``where`` objects """
    pass

class where(entitiesmod.entity):
    """ Represents a WHERE clause of an SQL statement. """

    def __init__(self, es, pred, args):
        """ Sets the initial propreties for the ``where`` object. 
        
        :param:  entities  es: The ``entities`` collection
        associated with this ``where`` object.

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
                # NOTE If developing with a Python version that is <
                # 3.6, copy shlex.py into main directory to get the
                # punctuation_chars parameter to work.
                try:
                    lex = shlex(expr, posix=False, punctuation_chars='!=<>')
                except Exception as ex:
                    # TODO Remove all this when Python <3.6 is
                    # unsupported
                    print(ex)
                    print('Is an updated version of shlex missing. Try:')
                    print('    wget https://raw.githubusercontent.com/python/cpython/master/Lib/shlex.py')
                    raise

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

class allstream(stream):
    pass
        
class eager:
    def __init__(self, *graphs):
        self._graphs = graphs

    def join(self, to):
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
        r = '%s(%s)'
        graphs = ', '.join(["'%s'" % x for x in self._graphs])
        r %= (type(self).__name__, graphs)
        return r

    def __str__(self):
        return ', '.join(self._graphs)

class entitiesmeta(type):
    def __and__(self, other):
        self = self()
        self.join(other)
        return self

    @property
    def count(cls):
        return cls.orm.all.count

class entities(entitiesmod.entities, metaclass=entitiesmeta):
    re_alphanum_ = re.compile('^[a-z_][0-9a-z_]+$', flags=re.IGNORECASE)

    def __init__(self, initial=None, _p2=None, *args, **kwargs):
        try:
            if not hasattr(type(self), 'orm'):
                raise NotImplementedError(
                    '"orm" attribute not found for "%s". '
                    'Check that the entity inherits from the '
                    'correct base class.' % type(self).__name__
                )
            try:
                self.orm = self.orm.clone()
            except AttributeError:
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

            # If a stream or eager is found in the first or second argument,
            # move it to args
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

            # The parameters express a conditional (predicate) if the
            # first is a str, or the args and kwargs are not empty.
            # Otherwise, the first parameter, `initial`, means an
            # initial set of values that the collections should be set
            # to.  The other parameters will be empty in that case.
            iscond = type(initial) is str
            iscond = iscond or (initial is None and (_p2 or bool(args) or bool(kwargs)))

            if self.orm.stream or iscond:
                super().__init__()

                # `initial` would be None when doing kwarg based
                # queries, i.e.: entities(col = 'value')
                _p1 = '' if initial is None else initial

                self._preparepredicate(_p1, _p2, *args, **kwargs)

                # Create joins to superentities where necessary if not
                # in streaming mode. (Streaming does not support (and
                # can't support) joins.)
                if not self.orm.isstreaming:
                    self.orm.joinsupers()

                return

            super().__init__(initial=initial)

        finally:
            if hasattr(type(self), 'orm'):
                if hasattr(self, 'orm'):
                    self.orm.initing = False

    def isauthorized(self):
        "TODO"

    def clone(self, to=None):
        if not to:
            raise NotImplementedError()

        to.where         =  self.where
        to.orm.stream    =  self.orm.stream
        to.orm.isloaded  =  self.orm.isloaded

    def _self_onafterload(self, src, eargs):
        chron = db.chronicler.getinstance()
        chron += db.chronicle(eargs.entity, eargs.op, eargs.sql, eargs.args)

    def innerjoin(self, *args):
        for es in args:
            self.join(es, join.Inner)

    def outerjoin(self, *args):
        for es in args:
            self.join(es, join.Outer)

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
        can be expessed using the ORMs API. For example::

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
        type1, type = type, builtins.type
        if join.Outer == type1:
            msg = 'LEFT OUTER JOINs are not currently implemented'
            raise NotImplementedError(msg)

        # Streaming entities can't contain joins
        if self.orm.isstreaming:
            raise InvalidStream('Streaming entities cannot contain joins')

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
            # When entity.orm.superjoins() wants to join a super with
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
        self.innerjoin(other)
        return self

    def __iand__(self, other):
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
        # because the request is interpreted as "give me the the number of rows
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
        if attr == 'orm':
            return object.__getattribute__(self, attr)

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
                raise AttributeError(msg % (self.__class__.__name__, attr))
        else:
            load = True

            if self.orm.composite:
                if self.orm.composite.orm.isnew:
                    load = False

            # Don't load if joining or attr == 'load'
            load &= attr not in ('innerjoin', 'join', 'load')

            # Don't load if attr = '__class__'. This is typically an attempt
            # to test the instance type using isinstance().
            load &= attr != '__class__'

            # Don't load if the entities collection is __init__'ing
            load &= not self.orm.initing

            # Don't load if the entities collection is currently being loading
            load &= not self.orm.isloading

            # Don't load if self has already been loaded
            load &= not self.orm.isloaded

            # Don't load an entiity object is being removed from an entities
            # collection
            load &= not self.orm.isremoving

            # Don't load unless self has joins or self has a where
            # clause/predicate
            load &= self.orm.joins.ispopulated or bool(self.orm.where)

            if load:
                self.orm.collect()

        return object.__getattribute__(self, attr)

    def sort(self, key=None, reverse=None):
        key = 'id' if key is None else key
        if self.orm.isstreaming:
            key = '%s %s' % (key, 'DESC' if reverse else 'ASC')

            self.orm.stream.orderby = key
        else:
            reverse = False if reverse is None else reverse
            super().sort(key, reverse)

    def sorted(self, key=None, reverse=None):
        key = 'id' if key is None else key
        if self.orm.isstreaming:
            key = '%s %s' % (key, 'DESC' if reverse else 'ASC')
            self.orm.stream.orderby = key
            return self
        else:
            reverse = False if reverse is None else reverse
            r =  super().sorted(key, reverse)
            self.clone(r)
            return r

    def save(self, *es):
        exec = db.executioner(self._save)
        exec.execute(es)

    def _save(self, cur, es=None):
        for e in self:
            e._save(cur)

        for e in self.orm.trash:
            e._save(cur)

        if es:
            for e in es:
                e._save(cur)

    def delete(self):
        for e in self:
            e.delete()
        
    def give(self, es):
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

        :param: bool uniq: Do not append is `obj` is already in the
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
                # The self collection won't always have a reference to its
                # composite.  For example: when the collection is being
                # lazy-loaded.  The lazy-loading, however, will ensure the obj
                # being appended will get this reference.
                continue
            else:
                # Assign the composite reference of this collection to the obj
                # being appended, i.e.:
                #    obj.composite = self.composite
                setattr(obj, clscomp.__name__, objcomp)

        super().append(obj, uniq, r)
        return r

    def _preparepredicate(self, _p1='', _p2=None, *args, **kwargs):
        p1, p2 = _p1, _p2

        if p2 is None and p1 != '':
            msg = '''
                Missing arguments collection.  Be sure to add arguments in the
                *args portion of the constructor.  If no args are needed for
                the query, just pass an empty tuple to indicate that none are
                needed.  Note that this is an opportunity to evaluate whether
                or not you are opening up an SQL injection attact vector.
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
                    # underscores, no operators) assume the user is doing a
                    # simple equailty test (p1 == p2)
                    p1 += ' = %s'
                args = [p2] + args
            else: # tuple, list, etc
                args = list(p2) + args

        args = [x.bytes if type(x) is UUID else x for x in args]

        if orm.proprietor:
            if p1:
                p1 += ' AND '

            for map in self.orm.mappings.foreignkeymappings:
                if map.fkname == 'proprietor':
                    p1 += f'{map.name} = _binary %s'
                    args.append(orm.proprietor.id.bytes)
                    break

        if p1:
            self.orm.where = where(self, p1, args)
            self.orm.where.demandvalid()
            self.orm.where.args = self.orm.parameterizepredicate(args)

    def clear(self):
        """
        Remove all elements from the entities collection.
        """
        try:
            # Set isremoving to True so entities.__getattribute__ doesn't
            # attempt to load whenever the removing logic calls an attibute on
            # the entities collection.
            self.orm.isremoving = True
            super().clear()
        finally:
            self.orm.isremoving = False

    def remove(self, *args, **kwargs):
        try:
            # Set isremoving to True so entities.__getattribute__ doesn't
            # attempt to load whenever the removing logic calls an attibute on
            # the entities collection.
            self.orm.isremoving = True
            super().remove(*args, **kwargs)
        finally:
            self.orm.isremoving = False

    @property
    def brokenrules(self):
        return self.getbrokenrules()

    def getbrokenrules(self, gb=None):
        brs = entitiesmod.brokenrules()

        # This test corrects a fairly deep issue that has only come
        # up with subentity-superassociation-subentity
        # relationships. We use the below logic to return
        # immediately when an association's (self) collection has any
        # constituents that have already been visited. See the
        # brokenrule collections being tested at the bottom of
        # it_loads_and_saves_reflexive_associations_of_subentity_objects
        # for more clarifications.

        if gb is None:
            gb = list()

        if self in gb:
            return

        gb.append(self)
            
        if any(x in gb for x in self):
            return brs

        # Replace with any() - see above.
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
        self.orm.trash += eargs.entity
        self.orm.trash.last.orm.ismarkedfordeletion = True
        super()._self_onremove(src, eargs)
                    
    def getindex(self, e):
        if isinstance(e, entity):
            for ix, e1 in enumerate(self):
                if e.id == e1.id: return ix
            e, id = e.orm.entity.__name__, e.id
            raise ValueError("%s[%s] is not in the collection" % (e, id))

        super().getindex(e)

    def __repr__(self):
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
    def __new__(cls, name, bases, body):
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
                raise AttributeError(
                    'Entities class for "%s" couldn\'t be found. '
                    'Either specify one or define one with a '
                    'predictable name' % name
                )

        # Make sure the `orm` has a reference to the entities collection
        # class and that the entities collection class has a refernce to
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
                    # create an entitymapping. This is for the the
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
    # These are the limits of the MySQL datetime type
    mindatetime=primative.datetime('1000-01-01 00:00:00.000000+00:00')
    maxdatetime=primative.datetime('9999-12-31 23:59:59.999999+00:00')

    def __init__(self, o=None, **kwargs):
        try:
            self.orm = self.orm.clone()
            self.orm.initing = True # TODO change to `isiniting`
            self.orm.instance = self

            self.onbeforesave       =  entitiesmod.event()
            self.onaftersave        =  entitiesmod.event()
            self.onafterload        =  entitiesmod.event()
            self.onbeforereconnect  =  entitiesmod.event()
            self.onafterreconnect   =  entitiesmod.event()

            self.onaftersave       +=  self._self_onaftersave
            self.onafterload       +=  self._self_onafterload
            self.onafterreconnect  +=  self._self_onafterreconnect

            super().__init__()
            if o is None:
                self.orm.isnew = True
                self.orm.isdirty = False
                self.id = uuid4()
                if orm.proprietor:
                    self.proprietor = orm.proprietor
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
                    raise ValueError(
                        'Can only load by UUID. '
                        'If you are setting attributes via the '
                        'constructor, ensure that you are including'
                        'the keys as well.'
                    )

                self.orm.populate(res)

            # TODO If k is not in self.orm.mappings, we should throw a
            # ValueError.
            # Set attributes via keyword arguments:
            #     per = person(first='Jesse', last='Hogan')
            for k, v in kwargs.items():
                setattr(self, k, v)

            # Post super().__init__() events
            self.onaftervaluechange  +=  self._self_onaftervaluechange
        finally:
            self.orm.initing = False

    def __getitem__(self, args):
        if type(args) is str:
            try:
                return getattr(self, args)
            except AttributeError as ex:
                raise IndexError(str(ex))

        vals = []

        for arg in args:
            vals.append(self[arg])

        return tuple(vals)

    def __call__(self, args):
        try:
            return self[args]
        except IndexError:
            return None

    def __setitem__(self, k, v):
        map = self.orm.mappings(k)
        if map is None:
           super = self.orm.super
           if super:
               map = super.orm.mappings[k]
           else:
               raise IndexError("Map index doesn't exist: %s" % (k,))
        
        map.value = v

    def _self_onafterload(self, src, eargs):
        self._add2chronicler(eargs)

    def _self_onaftersave(self, src, eargs):
        self._add2chronicler(eargs)

    def _self_onafterreconnect(self, src, eargs):
        self._add2chronicler(eargs)

    @staticmethod
    def _add2chronicler(eargs):
        chron = db.chronicler.getinstance()
        chron += db.chronicle(eargs.entity, eargs.op, eargs.sql, eargs.args)

    def _self_onaftervaluechange(self, src, eargs):
        if not self.orm.isnew:
            self.orm.isdirty = True

    def __dir__(self):
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

        # TODO Document the `imp` parameter
        
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
                        fkname, e1 = map.fkname, map.entity
                        if e1 is e and (not fkname or attr == fkname):
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

                # If self is a subentity (i.e., concert), we will want to set
                # the superentity's (i.e, presentation) composite map to its
                # composite class (i.e., artist) value. 
                selfsuper = self.orm.super
                attrsuper = self.orm.mappings(attr).value.orm.super

                if selfsuper and attrsuper:
                    maps = selfsuper.orm.mappings
                    attr = maps(attrsuper.__class__.__name__)

                    # NOTE attr could be None for various reasons. It's
                    # unclear at the moment if this is correct logic. We
                    # will let experience using the ORM determine if we
                    # need to revisit this.
                    if attr:
                        setattr(selfsuper, attr.name, attrsuper)

    def delete(self):
        self.orm.ismarkedfordeletion = True
        self.save()

    def save(self, *es):
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

        if guestbook is None:
            guestbook = list()
        
        if self in guestbook:
            return

        guestbook.append(self)

        if not self.orm.ismarkedfordeletion and not self.isvalid:
            raise db.BrokenRulesError("Can't save invalid object", self)

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

        # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        # If we are modifying the record, the orm.proprietor matchs the
        # record's proprietory. This ensures one party can't modify
        # another's records.
        # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        if crud in ('update', 'delete'):
            if self.proprietor.id != orm.proprietor.id:
                raise ProprietorError(self.proprietor)

        try:
            # Take snapshot of before state
            st = self.orm.persistencestate

            if sql:
                # Issue the query

                # Raise event
                eargs = db.operationeventargs(self, crud, sql, args)
                self.onbeforesave(self, eargs)

                cur.execute(sql, args)

                # Update new state
                self.orm.isnew = self.orm.ismarkedfordeletion
                self.orm.isdirty, self.orm.ismarkedfordeletion \
                                                    = (False,) * 2
                # Raise event
                self.onaftersave(self, eargs)
                # If there is no sql, then the entity isn't new, dirty
                # or marked for deletion. In that case, don't save.
                # However, allow any constituents to be saved.
                pass

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
        return self.getbrokenrules()

    def getbrokenrules(self, gb=None):
        brs = entitiesmod.brokenrules()

        if gb is None:
            gb = list()

        if self in gb:
            return brs

        gb.append(self)
            
        # TODO s/super/sup/
        super = self.orm._super
        if super:
            brs += super.getbrokenrules(gb=gb)

        for map in self.orm.mappings:
            if type(map) is fieldmapping:
                t = map.type
                if t == types.str:
                    brs.demand(
                        self, 
                        map.name, 
                        type=str, 
                        min=map.min, 
                        max=map.max
                   )

                elif t == types.int:
                    brs.demand(self, map.name, min=map.min, max=map.max, 
                                     type=int)
                elif t == types.bool:
                    brs.demand(self, map.name, type=bool)

                elif t == types.float:
                    brs.demand(self, map.name, 
                                     type=float, 
                                     min=map.min, 
                                     max=map.max, 
                                     precision=map.precision,
                                     scale=map.scale)

                elif t == types.decimal:
                    brs.demand(self, map.name, 
                                     type=decimal.Decimal, 
                                     min=map.max, 
                                     max=map.min, 
                                     precision=map.precision,
                                     scale=map.scale)

                elif t == types.bytes:
                    brs.demand(self, 
                        map.name, 
                        type=bytes,
                        max=map.max, 
                        min=map.min
                    )

                elif t == types.date:
                    brs.demand(self, 
                        map.name, 
                        instanceof=date,
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

            # NOTE I added a `followentitiesmapping` flag (7d3bc6ce) which I
            # only applied to associations (see below) because association are
            # a subtype of entities. However, I could have added it to the
            # below line so that it would read:
            #
            #     `followentitiesmapping and elif type(map) is entitiesmapping:`
            #
            # However, I didn't do it because, at the moment, there is no issue
            # here with the current logic. However, that may change and we will
            # want to add (as one would expect) the `followentitiesmapping`
            # flag here as well.
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
                        brs += entitiesmod.brokenrule(msg, map.name, 'valid')
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

            elif type(map) is associationsmapping:
                if map.isloaded:
                    brs += map.value.getbrokenrules(gb=gb)

        return brs

    @staticmethod
    def _setattr(e, attr, v):
        e.orm.mappings[attr].value = v

    def __getattribute__(self, attr):
        try:
            v = object.__getattribute__(self, attr)
            if isinstance(v, span):
                if v.isstatic:
                    v = v.clone(e=self)
                    setattr(self, attr, v)
            return v
        except sys.modules['orm'].attr.AttributeErrorWrapper as ex:
            raise ex.inner
        except AttributeError as ex:
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

                    # NOTE Though we've switch to implicit loading for
                    # entities and associations, we should still
                    # explicitly load here for the sake of
                    # predictability.
                    es = map_entities(map1.name, self.id)
                    es.orm.collect()

                    # Assign the composite reference to the
                    # constituent's elements
                    #   i.e., art.presentations.first.artist = art
                    for e in es:
                        attr = self_orm.entity.__name__

                        # Set cmp to False and use a custom setattr.
                        # Simply calling setattr(e, attr, self) would
                        # cause e.attr to be loaded from the database
                        # for comparison when __setattr__ calls
                        # _setvalue.  However, the composite doesn't
                        # need to be loaded from the database.
                        e._setvalue(attr, self, attr, cmp=False, 
                                    setattr=self._setattr)

                        # Since we just set e's composite, e now thinks its
                        # dirty.  Correct that here.
                        e.orm.persistencestate = False, False, False

                if es is None:
                    es = map_entities()

                map.value = es

                # Assign the composite reference to the constituent
                #   i.e., art.presentations.artist = art
                setattr(map.value, self_orm.entity.__name__, self)

                map.value.onadd.append(self.entities_onadd)

        # Is attr in one of the supers' mappings collections. We don't
        # want to start loading super entities from the database unless
        # we know that the attr is actually in one of them.
        elif not map and attr in self_orm.mappings.supermappings:
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
                        es = v
                        for e in (es,) +  tuple(es):
                            setattr(e, self_orm_entity__name__, self)

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
        except AttributeError:
            # `self` won't have the attribute `sup.__name__` if the
            # constituent class is a superentity.
            #
            # We should be able to remove this if 1de11dc0 is fixed.
            pass
        else:
            # Append the entity to that entities collection
            es += e

    def __repr__(self):
        """ Return a tabularized list of ``self``'s properties and their
        corresponding values. Any exceptions that happen to occure will
        be trapped and a string representations of the exception will be
        returned."""

        try:
            tbl = table()

            es = entitiesmod.entities()
            e = self
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

            for br in self.brokenrules:
                r = tblbr.newrow()
                r.newfield(br.property)
                r.newfield(br.type)
                r.newfield(br.message)
                
            return '%s\n%s\n%s' % (super().__repr__(), 
                                       str(tbl), 
                                       str(tblbr))
        except Exception as ex:
            return '%s (Exception: %s) ' % (super().__repr__(), str(ex))

    def __str__(self):
        if hasattr(self, 'name'):
            return '"%s"' % self.name
            
        return str(self.id)
            
class mappings(entitiesmod.entities):
    def __init__(self, initial=None, orm=None):
        super().__init__(initial)
        self._orm = orm
        self._populated = False
        self._populating = False
        self._supermappings = None
        self._nameix = None
        self.oncountchange += self._self_oncountchange

    def _self_oncountchange(self, src, eargs):
        self._populated = False

    def __getitem__(self, key):
        self._populate()

        if self._nameix is not None and isinstance(key, str):
            try:
                return self._nameix[key]
            except KeyError as ex:
                raise IndexError(str(ex))
            
        return super().__getitem__(key)

    def __iter__(self):
        self._populate()
        return super().__iter__()

    def __contains__(self, key):
        if isinstance(key, str):
            return any(x.name == key for x in self)
        else:
            # NOTE entities.entities should have a __contains__ method.
            # Surprisingly, I couldn't find one.
            raise ValueError('Invalid type')
            return super().__contains__(key)

    def _populate(self):
        """ Reflect on the entities and associations to populate the
        mappings collection with up-to-date mappings values.
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

            # TODO:2b619f6f Remove this test
            if 'proprietor' not in self:
                from party import party

                # TODO:f9a3239c Do we need isderived=True
                self += entitymapping(
                    'proprietor', party, isderived=True
                )
            else:
                print('We need this test')
                B()

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
            # a foreign key mapping (e.g., For artist_artifact, add a
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
            sys.setrecursionlimit(2000)

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
        if derived:
            for map in [x for x in self if x.isderived]:
                self.remove(map)
        else:
            super().clear()

    def sort(self):
        # Make sure the mappings are sorted in the order they are
        # instantiated
        super().sort('_ordinal')

        # Ensure builtins attr's come right after id
        for attr in reversed(('id', 'createdat')):
            try:
                attr = self.pop(attr)
            except ValueError:
                # attr hasn't been added to self yet
                pass
            else:
                self << attr

        # Insert FK maps right after PK map
        fkmaps = list(self.foreignkeymappings)
        fkmaps.sort(key=lambda x: x.name)
        for map in fkmaps:
           self.remove(map)
           self.insertafter(0, map)

    @property
    def foreignkeymappings(self):
        return self._generate(type=foreignkeyfieldmapping)

    @property
    def fieldmappings(self):
        return self._generate(type=fieldmapping)

    @property
    def primarykeymapping(self):
        return list(self._generate(type=primarykeyfieldmapping))[0]

    @property
    def entitiesmappings(self):
        return self._generate(type=entitiesmapping)

    @property
    def entitymappings(self):
        return self._generate(type=entitymapping)

    @property
    def associationsmappings(self):
        return self._generate(type=associationsmapping)

    def _generate(self, type):
        for map in self:
            if builtins.type(map) is type:
                yield map

    @property
    def all(self):
        ''' Returns a generator of all mapping objects including
        supermappings.  '''
        for map in self:
            yield map

        for map in self.supermappings:
            yield map

    @property
    def supermappings(self):
        if not self._supermappings:
            e = self.orm.entity.orm.super
            self._supermappings = mappings()

            while e:
                self._supermappings += e.orm.mappings
                e = e.orm.super

        return self._supermappings
            
    @property
    def orm(self):
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
        tbl = self.orm.table

        maps = [x for x in self if isinstance(x, fieldmapping)]

        flds = ', '.join('`%s`' % x.name for x in maps)

        placeholders = ', '.join(['%s'] * len(maps))

        sql = 'INSERT INTO %s (%s) VALUES (%s);'
        sql %= (tbl, flds, placeholders)

        args = self._getargs()

        sql = orm.introduce(sql, args)

        return sql, args

    def getupdate(self):
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

        args = self._getargs()

        # Move the id value from the bottom to the top
        args.append(args.pop(0))

        sql = orm.introduce(sql, args)
        return sql, args

    def getdelete(self):
        sql = 'DELETE FROM {} WHERE id = %s;'.format(self.orm.table)

        args = self['id'].value.bytes,

        sql = orm.introduce(sql, args)

        return sql, args

    def _getargs(self):
        r = []
        for map in self:
            if isinstance(map, fieldmapping):
                keymaps = primarykeyfieldmapping, foreignkeyfieldmapping
                if type(map) in keymaps and isinstance(map.value, UUID):
                    r.append(map.value.bytes)
                else:
                    v = map.value if map.value is not undef else None
                    if v is not None:
                        if map.isdatetime:
                            v = v.replace(tzinfo=None)
                        elif map.isbool:
                            v = int(v)
                    r.append(v)
        return r

    def clone(self, orm_):
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
    ordinal = 0

    def __init__(self, name, isderived=False):
        self._name = name
        mapping.ordinal += 1
        self._ordinal = mapping.ordinal
        self.isderived = isderived

    @property
    def isstandard(self):
        """ Returns True if this is a standard field mapping applied by
        the entitymeta.
        """
        #  TODO Add 'proprietor'
        return self.name in ('id', 'createdat', 'updatedat')

    def isdefined(self):
        return self._value is not undef

    @property
    def name(self):
        return self._name

    @property
    def fullname(self):
        return '%s.%s' % (self.orm.table, self.name)

    @property
    def value(self):
        msg = 'Value should be implemented by the subclass'
        raise NotImplementedError(msg)

    @value.setter
    def value(self, v):
        msg = 'Value should be implemented by the subclass'
        raise NotImplementedError(msg)

    @property
    def isloaded(self):
        return self._value not in (None, undef)

    def clone(self):
        raise NotImplementedError('Abstract')

    @property
    def _reprargs(self):
        args = 'fullname="%s"'
        args %= self.fullname
        return args
        
    def __repr__(self):
        r = '%s(%s)'
        r %= (type(self).__name__, self._reprargs)
        return r

    def __str__(self):
        return repr(self)
    
class associationsmapping(mapping):
    """ Represents a mapping to an entity's associations collection.
    """
    def __init__(self, name, ass, isderived=False):
        """ Set initial values.
        """

        # Store a reference to the actual association class
        self.associations = ass
        self._value = None
        self._composite = None
        super().__init__(name, isderived)

    def clone(self):
        """ Create a new associationsmapping with same attribute values.
        """
        return associationsmapping(
            self.name, self.associations, self.isderived
        )

    @property
    def entities(self):
        """ Returns the associations collection class.
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
                # NOTE Currently, we implitly load entities and
                # association.  However, we will want to continue
                # explitly loading this association here for the sake of
                # predictablity.
                asses.orm.collect()

            # Make sure the associations collection knows it's composite
            asses.orm.composite = self.composite

            # Memoize. Using the setter here ensure that self._setvalue
            # gets called.
            self.value = asses

        return self._value

    @value.setter
    def value(self, v):
        """ Sets the associations collection object that the this map
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
    def __init__(self, name, es):
        self.entities = es
        self._value = None
        super().__init__(name)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, v):
        self._setvalue('_value', v, 'value')

    @property
    def _reprargs(self):
        args = super()._reprargs
        args += ', isloaded=%s' % self.isloaded
        return args

    def clone(self):
        return entitiesmapping(self.name, self.entities)

class entitymapping(mapping):
    """ Represents a mapping to another entity.
    """

    def __init__(self, name, e, isderived=False):
        """ Sets the initial values.

        :param: str name:       The name of the map
        :param: entity e:       The entity class associatied with this
                                map
        :param: bool isderived: Indicates whether or not the the map was
                                created/derived by the
                                mappings._populate() method
        """
        self.entity = e
        self._value = None
        super().__init__(name, isderived)

    @property
    def issubjective(self):
        return self.orm.isreflexive \
               and self.name.startswith('subject') 

    @property
    def isobjective(self):
        return self.orm.isreflexive \
               and self.name.startswith('object') 

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

                # Experimental reflexive logic. Here we are trying to
                # make sure that the correct map is selected since doing
                # a simple type test (like the one below) is
                # insufficient because reflexive maps will have two
                # mappings with the same type.
                if (
                    self.orm.isreflexive
                    and not map.name.startswith(self.name + '__')
                ):
                    continue

                # If the given foreign key is mapped to the entity
                # corresponding to self...
                if map.entity is self.entity:
                    
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
        """ Clone the entitymapping object.
        """
        return entitymapping(
            self.name, self.entity, isderived=self.isderived
        )

    @property
    def _reprargs(self):
        """ A list of arguments used by the super classes __repr__
        method.
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
    pass

class index(entitiesmod.entity):
    def __init__(self, name=None, ordinal=None):
        self._name = name
        self.ordinal = ordinal
        self.map = None

    @property
    def name(self):
        name = self._name if self._name else self.map.name

        name = name if name.endswith('_ix') else name + '_ix'

        return name

    def __str__(self):
        return self.name
    
    def __repr__(self):
        return super().__repr__() + ' ' + self.name

class fulltexts(indexes):
    pass

class fulltext(index):
    @property
    def name(self):
        name = self._name if self._name else self.map.name

        name = name if name.endswith('_ftix') else name + '_ftix'

        return name

class attr:
    def __init__(self, *args, **kwargs):
        self.args = list(args)
        self.kwargs = kwargs

    def __call__(self, meth):
        self.args.append(meth)
        w = attr.wrap(*self.args, **self.kwargs)
        return w

    def attr(v=undef):
        """ Sets the map's value to ``v``. Returns the mapped
        value.

        This function is injected into imperitive attributes to
        provide easy access to the the attributes mapping value.
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

    """ A decorator to make a method an imperitive attribute. """
    class wrap:
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

            except AttributeError as ex:
                # If it raises an AttributeError, wrap it. If the call
                # from e.__getattribute__ sees a regular AttributeError,
                # it will ignore it because it will assume its caller is
                # requesting the value of a mapping object.
                raise sys.modules['orm'].attr.AttributeErrorWrapper(ex)
            
        def __get__(self, instance, owner=None):
            return self._getset(instance=instance, owner=owner)

        def __set__(self, instance, value):
            return self._getset(instance=instance, value=value)

class fieldmapping(mapping):
    """ Represents mapping between Python types and MySQL types.
    """
    # Permitted types
    types = bool, str, int, float, decimal.Decimal, bytes, datetime, date
    def __init__(self, type,       # Type of field
                       min=None,   # Max length or size of field
                       max=None,   # Min length or size of field
                       m=None,     # Precision (in decimals and floats)
                       d=None,     # Scale (in decimals and floats)
                       name=None,  # Name of the field
                       ix=None,    # Database index
                       isderived=False,
                       isexplicit=False,
                       isgetter=False,
                       issetter=False,
                       span=None):

        if hasattr(type, 'mro') and alias in type.mro():
            type, min, max = type()

        if type in (float, decimal.Decimal):
            if min is not None:
                m, min = min, None
            if max is not None:
                d, max = max, None
        
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
        # NOTE This should probably be rewritten like this:
        #
        #     return db.column(self)

        col = db.column()
        col.name = self.name
        col.dbtype = self.definition
        return col

    def clone(self):
        ix = self.index

        ix = type(ix)(name=ix.name, ordinal=ix.ordinal) if ix else None

        map = fieldmapping(
            self.type,
            self.min,
            self.max,
            self.precision,
            self.scale,
            self.name,
            ix,
            self.isderived,
            self.isexplicit,
            self.isgetter,
            self.issetter,
            self.span,
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
        args = super()._reprargs
        args  +=  ',  type=%s'        %  str(self.type)
        args  +=  ',  ix=%s'          %  str(self.index)
        args  +=  ',  value=%s'  %  str(self.value)
        return args

    @property
    def index(self):
        return self._ix

    @property
    def isstr(self):
        return self.type == types.str

    @property
    def isdatetime(self):
        return self.type == types.datetime

    @property
    def isdate(self):
        return self.type == types.date

    @property
    def isbool(self):
        return self.type == types.bool

    @property
    def isint(self):
        return self.type == types.int

    @property
    def isfloat(self):
        return self.type == types.float

    @property
    def isdecimal(self):
        return self.type == types.decimal

    @property
    def isbytes(self):
        return self.type == types.bytes

    @property
    def isfixed(self):
        if self.isint or self.isfloat or self.isdecimal:
            return True

        if self.isbytes or self.isstr:
            return self.max == self.min
        return False

    @property
    def min(self):
        if self.isstr:
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
        if not (self.isfloat or self.isdecimal, self.isdatetime):
            return None

        if self.isdatetime:
            return 6

        if self._precision is None:
            return 12

        return self._precision

    @property
    def scale(self):
        if not (self.isfloat or self.isdecimal):
            return None

        if self._scale is None:
            return 2

        return self._scale
        
    @property
    def max(self):
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
        if self.type not in (types.int, types.float, types.decimal):
            raise ValueError()

        return self.min < 0
    
    @property
    def dbtype(self):
        """ Returns a string representing the MySQL data type
        corresponding to this field mapping e.g., 'varchar',
        'datetime', 'bit', 'tinyint', 'smallint unsigned', etc.

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
            # However, setting the varchar max to 16,383 can cause
            # issues for larger strings such as `bio1 = str, 1, 16382`.
            # The following may be thrown for this string on table
            # creation:
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
                    # Convert the bytes string fromm MySQL's bit type to a
                    # bool.
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
        self._value = v

class foreignkeyfieldmapping(fieldmapping):
    def __init__(self, e, fkname=None, isderived=False):
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
    def name(self):
        # TODO:055e5c02 make FK name's fully qualified. grep 055e5c02
        # for more.

        if self._fkname:
            return '%s__%s' \
                % (self._fkname, self.entity.__name__ + 'id')

        return self.entity.__name__ + 'id'

    @property
    def fkname(self):
        """ Return the name of the entity mapping that this map
        corresponds. """
        return self._fkname

    def clone(self):
        return foreignkeyfieldmapping(self.entity, self._fkname, self.isderived)

    @property
    def issubjective(self):
        return self.orm.isreflexive \
               and self.name.startswith('subject__') 

    @property
    def isobjective(self):
        return self.orm.isreflexive \
               and self.name.startswith('object__') 

    @property
    def dbtype(self):
        return 'binary'

    @property
    def definition(self):
        return 'binary(16)'

    @property
    def value(self):
        if type(self._value) is bytes:
            self._value = UUID(bytes=self._value)
            
        return self._value

    @value.setter
    def value(self, v):
        self._value = v

class primarykeyfieldmapping(fieldmapping):
    def __init__(self):
        super().__init__(type=types.pk)

    @property
    def name(self):
        return 'id'

    def clone(self):
        return primarykeyfieldmapping()

    @property
    def dbtype(self):
        return 'binary'

    @property
    def definition(self):
        return 'binary(16) primary key'

    @property
    def value(self):
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
            self._value = UUID(bytes=self._value)

        return self._value

    @value.setter
    def value(self, v):
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
            raise ValueError()
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
        :param: entity The entity to be wrapped.
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
        return self.entity(*args, **kwargs)

class composites(ormclasseswrapper):
    pass

class composite(ormclasswrapper):
    pass

class constituents(ormclasseswrapper):
    pass

class constituent(ormclasswrapper):
    pass

class orm:
    _abbrdict    =  dict()
    _namedict    =  dict()
    _proprietor  =  None

    @classmethod
    def setproprietor(cls, v):
        """ Set ``v`` to orm's proprietor. Ensure that the propritor
        entity owns itself.

        Proprietors
        ***********

        The logic in the ORM's database interface will use the
        orm.proprietor to provide multitenancy support.

        When a proprietor is set, the ORM will ensure that all records
        written to the database have their proprietor FK set to
        orm.proprietor.id, meaning that the records will be the
        *property* of the orm.proprietor. Only records owned by the
        orm.proprietor will be read by orm query operations i.e.:

            ent = entity(id)  # SELECT

            (or)

            ent.save()        # INSERT OR UPDATE
            
        When updating or deleting a record, the record must be owned by
        by the orm.proprietor or else a ProprietorError will be raised.

        :param: party.party v: The proprietor entity.
        """
        cls._proprietor = v

        # The proprietor of the proprietor must be the proprietor:
        #    
        #    assert v.proprietor is v
        #
        # Propogate this up the inheritance hierarchy.
        sup = v
        while sup:
            sup.proprietor = v
            sup = sup.orm.super

    @classmethod
    def getproprietor(cls):
        return cls._proprietor

    @classproperty
    def proprietor(cls):
        return cls.getproprietor()

    def __init__(self):
        self.mappings             =  None
        self.isnew                =  False
        self._isdirty             =  False
        self.ismarkedfordeletion  =  False
        self.entities             =  None
        self.entity               =  None
        self._table               =  None
        self.composite            =  None  # For association
        self._composits           =  None
        self._constituents        =  None
        self._associations        =  None
        self._trash               =  None
        self._subclasses          =  None
        self._super               =  None
        self._base                =  undef
        self.instance             =  None
        self.stream               =  None
        self.isloaded             =  False
        self.isloading            =  False
        self.isremoving           =  False
        self.joins                =  None
        self._abbreviation        =  str()
        self.initing              =  False

        self.recreate = self._recreate

    @staticmethod
    def exec(sql, args=None):
        exec = db.executioner(
            lambda cur: cur.execute(sql, args)
        )

        exec()
        
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

        The kwargs arguments is will be discoverd through inspection,
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
        self._table = v
        
    def iscollinear(self, with_):
        """ Return True if self is colinear with ``with_``.

        Collinearity is when the self entity is an instance ``with_``,
        or an instance of a superentity of ``with_``, or an instance of
        a class that inheritance from ``with_``. It's similar to
        isinstance(), but in addition to ascending the inheritance tree,
        it also descends it. 
        
        Collinearity in this context it is limited to orm.entity object.
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
        rs = self.entities(**kwargs)

        expects = set(expects)

        keys = set(kwargs.keys())

        if len(expects & keys) != len(expects):
            # When loading via the orm.populate() method, the expected
            # properties won't be passed in. Just return.
            return

        if rs.count:
            self.instance.id = rs.first.id
            for k, v in kwargs.items():
                setattr(self.instance, k, getattr(rs.first, k))

            # The record isn't new or dirty so set all peristance state
            # variables to false.
            self.persistencestate = (False,) * 3

            # Repeat for all the super that were loaded
            sup = self.instance.orm._super
            while sup:
                sup.orm.persistencestate = (False,) * 3
                sup = sup.orm._super
        else:
            # Save immediately. There is no need for the user to save
            # manually because there are only several rating objects
            # that will ever exist. We just pretend like they always
            # exist and are accessable via the construct with no fuss.
            self.instance.save()
            
    # TODO This should probably be renamed to `loaded`
    def reloaded(self):
        return self.entity(self.instance.id)

    def exists(self, o):
        """ Returns true if ``o`` exists in the database.
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
            # entity instead of the UUID. Note for this, we could also
            # just do `hum.super`.
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
        r = 'orm(type=<%s>, %s=True)'

        if self.isinstance:
            args = [type(self.instance).__name__]
        else:
            args = [self.entity.__name__]

        args += ['instance' if self.isinstance else 'static']

        return r % tuple(args)

    @property
    def isreflexive(self):
        maps = self.mappings.entitymappings
        types = [
            x.entity for x in maps
            if x.name != 'proprietor'
        ]

        return bool(len(types)) and len(types) > len(set(types))
        
    @property
    def isrecursive(self):
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
        
        top = None
        for pred in self.where.predicate:

            # FIXME If multiple columns are supported, fix below
            pred = pred.match or pred
            col = pred.columns[0]

            e = top or self.entity.orm.super

            while e: # :=
                map = e.orm.mappings(col) 
                if map:
                    top = e.orm.entities
                    break
                e = e.orm.super

        if not top:
            return

        es = self.instance
        while type(es) is not top:
            sup = es.orm.entities.orm.super.orm.entities()
            es = es.join(sup, inferassociation=False)
            es = sup

    def truncate(self, cur=None):
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
        """ Drop and recreate the table each of the entity class
        references in *args.

        Note that when ``orm`` is an instance (as opposed to mearly a
        class reference), this method is replace with ``orm._recreate'
        on initialization. 
        """

        # For each entity class reference in *args
        for e in args:
            # Delegate to the instance version of ``recreate``
            e.orm.recreate()
            
    def _recreate(self, cur=None, recursive=False, guestbook=None):
        """ Drop and recreate the table for the orm ``self``. 

        :param: cur:       The MySQLdb cursor used by this and all
                           subsequent CREATE and DROPs

        :param: recursive: If True, the constituents and subentities of
                           ``self`` will be recursively discovered and
                           their tables recreated. Used internally.

        :param: guestbook: A list to keep track of which classes' tables have
                           been recreated. Used internally to prevent
                           infinite recursion.
        """

        # Prevent infinite recursion
        if guestbook is None:
            guestbook = list()
        else:
            if self in guestbook:
                return
        guestbook += [self]

        try: 
            if cur:
                conn = None
            else:
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
        # TODO Use executioner
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
        return not bool(self.altertable)

    @property
    def migration(self):
        return migration(self.entity)

    @property
    def altertable(self):
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
        """
        Reload the entities collection (self). A different query will be
        executed if the arguments are different, though most of the
        SELECT statement is generated by arguments passed to the
        entities collection's constructor.

        :param: str orderby: The list of columns to be passed to the
                            ``ORDER BY`` clause. Used only streaming
                            mode.

        :param: int limit:   An integer value to pass to the ``LIMIT``
                             keyword.  Used only in streaming mode.

        :param: int offset:  An integer value to pass to the ``OFFSET``
                             keyword.  Used only in streaming mode.
        """

        # TODO To complement orm.reloaded(), we should have an override of
        # orm.load() that reloads/refreshed an entity object. 
        try:
            # Remove all elements from collection.
            self.instance.clear()
        except:
            raise
        else:
            # Flag the entities collection as unloaded so the load() method
            # will proceed with an attempt to load.
            self.isloaded = False
            self.collect(orderby, limit, offset)

    def query(self, sql):
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
        try:
            return db.table(self.table)
        except _mysql_exceptions.OperationalError as ex:
            if ex.args[0] == BAD_TABLE_ERROR:
                return None
            raise

    def load(self, id):
        """ Load an entity by ``id``.
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
        # orm.proprietor from being loaded.
        if orm.proprietor:
            for map in self.mappings.foreignkeymappings:
                if map.fkname == 'proprietor':
                    sql += f' AND {map.name} = _binary %s'
                    args.append(orm.proprietor.id.bytes)
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
        # of all the event initialition code is in __init__. However, we
        # could set a private boolean to cause the entity's __bool__
        # method to return False. Then any call to __getattribute__()
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
        # db.RecordNotFoundError
        ress.demandhasone()

        # We are only interested in the first
        res = ress.first

        # Invoke the `onafterload` on self.instance passing in relevent
        # arguments
        eargs = db.operationeventargs(self.instance, 'retrieve', sql, args)
        self.instance.onafterload(self.instance, eargs)

        # Give the caller the record so it can populate itself with the
        # data.
        return res
    
    def collect(self, orderby=None, limit=None, offset=None):
        """
        Loads data from the database into the collection. The SQL used 
        to load the data is generated mostly from arguments passed to
        the entities collection's contructor.

        Note that an ORM user typically doesn't call ``load`` explicitly. The
        call to ``load`` is usually made by the ORM after the entities
        collection has been instantiated and during the invocation of one of
        the collection's properties or methods. See
        ``entities.__getattribute__``.

        :param: str orderby: The list of columns to be passed to the ``ORDER
                             BY`` clause. Used only streaming mode.

        :param: int limit:   An integer value to pass to the ``LIMIT`` keyword.
                             Used only in streaming mode.

        :param: int offset:  An integer value to pass to the ``OFFSET``
                             keyword.  Used only in streaming mode.
        """

        # Don't attemt to load if already loaded.
        if self.isloaded:
            return

        try:
            self.isloading = True

            # Get SQL and SQL parameters/args
            sql, args = self.sql

            # Concatenate the orderby
            if orderby:
                sql += ' ORDER BY ' + orderby

            # Concatenate the LIMIT and OFFSET
            if limit is not None:
                offset = 0 if offset is None else offset
                sql += ' LIMIT %s OFFSET %s' % (limit, offset)

            # Set up a function to be called by the database's executioner to
            # populate `ress` with the resultset
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
                lambda src, eargs: self.instance.onbeforereconnect(src, eargs)
            exec.onafterreconnect  += \
                lambda src, eargs: self.instance.onafterreconnect(src, eargs)

            # Execute the query. `ress` will be populated with the results.
            exec.execute()

            # Raise self's onafterload event
            eargs = db.operationeventargs(self.instance, 'retrieve', sql, args)
            self.instance.onafterload(self, eargs)

            # Use the resultset to populate the entities collection (self) and
            # link the entities together (linking is done in `orm.link()`).
            self.populate(ress)

        finally:
            self.isloaded = True
            self.isloading = False

    @property
    def abbreviation(self):
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
        if s[0] == "'" and s[-1] == "'":
            return s[1:-1]
        return s

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
        edict = dict()
        skip = False

        es = self.instance
        if type(ress) is db.dbresult:
            ress = [ress]
            simple = True
            maps = self.mappings
        elif type(ress) is db.dbresultset:
            simple = False
        else:
            raise ValueError('Invalid type of `ress`')

        for res in ress:
            for i, f in func.enumerate(res.fields):
                alias, _, col = f.name.rpartition('.')

                if not simple and (not skip or col == 'id'):
                    if col == 'id':
                        id = f.value

                        _, _, abbr = alias.rpartition('.')
                        eclass = orm.getentity(abbr=abbr)

                        key = (id, eclass)
                        skip = key in edict
                        if skip:
                            continue

                        e = eclass()

                        edict[key]= e

                        if i.first:
                            es += e

                        maps = e.orm.mappings

                        # During e's __init__'ing, a new instance of a super
                        # entity may be created (e.g., because an __init__ sets
                        # an attribute that is only in a super). Since we are
                        # loading here, we want to make sure this super set to
                        # None. 
                        #
                        # The result will be that the super will either
                        # be lazy-loaded when needed, or, if we have the supers
                        # record from the database here somewhere in `ress`,
                        # e.orm.super will be set by orm.link() to that
                        # super entity.
                        
                        e.orm.super = None

                        e.orm.persistencestate = (False,) * 3

                if skip:
                    continue

                maps[col]._value = f.value

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
        between the subentity and the super entity. 
        """

        # For each entity in edict
        for e in edict.values():
            
            # Does `e` have a foreign key that is the id of another entity in
            # edict, i.e., is `e` a child (or constituent) of other entity in
            # edict.
            for map in e.orm.mappings.foreignkeymappings:
                if not map.value:
                    continue

                # map.entity.orm.subentities.first.entity.__class__]
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
                    
                # If we are here, a composite was found

                # Chain the composite's entitiesmappings and
                # associationsmappings collection into `maps`. 
                #
                # Note we need to ascend the inheritance tree to include
                # all the superentities as well. This for loading
                # subentity objects join to super entity association:
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

    @property
    def sql(self):
        """ Return a tuple containing the SELECT statement as the first
        element and the args list as the second.
        """
        return self._getsql()

    def _getsql(self, graph=str(), whstack=None, joiner=None, join=None):
        """ The lower-level private method which bulids and returns the
        SELECT statement for the entities (self.instance) collection
        object.
        """

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
        """
        Use ``args`` to add introducers ('_binary', et. al.) before the
        unquoted placeholder tokens (%s) in ``sql``.

        :param: str  sql:  A whole are partial SQL statement.
        :param: list args: Parameters to use with query.
        :rtype: str
        :returns: Returns the ``sql`` argument with introducers added where
                  appropriate
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
        # placeholder token
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
        return self.stream is not None

    @property
    def isdirty(self):
        if self._isdirty:
            return True

        if self._super:
            return self.super.orm.isdirty

        return False

    @isdirty.setter
    def isdirty(self, v):
        self._isdirty = v

    @property
    def forentities(self):
        return isinstance(self.instance, entities)
        
    @property
    def forentity(self):
        return isinstance(self.instance, entity)

    @property
    def persistencestates(self):
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
        es = self.instance
        if not self.forentities:
            msg = 'Use with entities. For entity, use persistencestate'
            raise ValueError(msg)

        for e, st in zip(es, sts):
            e.orm.persistencestate = st

    @property
    def persistencestate(self):
        es = self.instance
        if not self.forentity:
            msg = 'Use with entity. For entities, use persistencestates'
            raise ValueError(msg)
        return self.isnew, self.isdirty, self.ismarkedfordeletion

    @persistencestate.setter
    def persistencestate(self, v):
        es = self.instance
        if not isinstance(es, entity):
            msg = 'Use with entity. For entities, use persistencestates'
            raise ValueError(msg)
        self.isnew, self.isdirty, self.ismarkedfordeletion = v

    @property
    def trash(self):
        if not self._trash:
            self._trash = self.entities()
        return self._trash

    @trash.setter
    def trash(self, v):
        self._trash = v

    @property
    def properties(self):
        """ Returns a list of all property names for this entity
        including those inherited from super entities.

        :returns: list A list of all the property names for this entity.
        """
        props = [x.name for x in self.mappings]

        for map in self.mappings.associationsmappings:
            for map1 in map.associations.orm.mappings.entitymappings:
                if self.entity is not map1.entity:
                    props.append(map1.entity.orm.entities.__name__)

        # TODO s/super/sup/
        super = self.super
        if super:
            props += [x for x in super.orm.properties if x not in props]

        return props

    def issuperentity(self, of):
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

        super = cls2

        while super:
            if super is cls1:
                return True
            super = super.orm.super

        return False

    @property
    def super(self):
        """ For orms that have no instance, return the super class of
        `orm.entity`.  If orm.instance is not None, return an instance of that
        object's super class.  A super class here means the base class of an
        entity class where the base itself is not `entity`, but rather a
        subclass of `entity`. So if class A inherits directly from entity, it
        will have a super of None. However if class B inherits from A. class B
        will have a super of A."""
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
                    # fact that self.isnew, its existing is in some
                    # cases meaningful and should be preserved.
                    self._super.id = id
                else:
                    e = self.instance
                    if not isinstance(e, entity):
                        msg = "'super' is not an attribute of %s"
                        msg %= str(type(e))
                        raise AttributeError(msg)
                    if e.id is not undef:
                        self._super = base(e.id)

                return self._super
        return None

    @super.setter
    def super(self, v):
        self._super = v

    @property
    def isstatic(self):
        return self.instance is None

    @property
    def isinstance(self):
        return self.instance is not None

    @property
    def superentities(self):
        ''' Returns a list of entity classes or entity objects (depending on
        whether or not self.isinstance) of which self is a subentity. '''

        r = list()
        e = self.super

        while e:
            r.append(e)
            e = e.orm.super

        return r

    # TODO This should probably be renamed to `subentities`
    @property
    def subentities(self):
        if self._subclasses is None:
            clss = ormclasseswrapper()
            for sub in orm.getsubclasses(of=self.entity):
                clss += sub
            self._subclasses = clss
        return self._subclasses

    @staticmethod
    def getsubclasses(of):
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

        :param: entity of The entity for which the subclasses will be
        returned.
        """
        r = []

        for sub in of.__subclasses__():
            if sub not in (associations, association):
                r.append(sub)

        for sub in of.__subclasses__():
            r.extend(orm.getsubclasses(sub))

        return r

    @staticmethod
    def getassociations():
        return orm.getsubclasses(of=association)

    @staticmethod
    def getentity(name=None, abbr=None):
        es = orm.getentitys() + orm.getassociations()

        if name:
            # Lookup entity/association class by abbreviation.
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
        # NOTE We may want to cache this
        r = []
        for es in orm.getsubclasses(of=entities):
            if association not in es.mro():
                if es is not association:
                    r += [es]
        return r

    @property
    def associations(self):
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

class saveeventargs(entitiesmod.eventargs):
    def __init__(self, e):
        self.entity = e

class associations(entities):
    """ Holds a collection of :class:`.association` objects. """

    def __init__(self, *args, **kwargs):
        """ Constructs an association collection. """
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
        """ Adds a :class:`.association` entity to the collection.

            :param: obj   The association object to append.
            :param: uniq  If True, only adds the object if it does not
                          already exist.
            :param: r     An `entities` collection containing the
                          objects that were added.
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
                    # names. The name that matters is on the LHS of the map
                    # when being defined in the association class.
                    if self.orm.isreflexive:
                        if map.issubjective:
                            # NOTE self.orm.composite can be None when the
                            # association is new. Calling 
                            #
                            #     settattr(obj, map.name, None)
                            #
                            # results in an error. The alternative block
                            # avoided this because the following will
                            # always be False. TODO We need to only run this
                            # code `if self.orm.composite`
                            #     self.name == type(None).__name__ 
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
                # arbitrary entity map such as `myassociationstype`, an
                # attempt to get the pseudocollection will result in an
                # AttributeError below. We want to skip this map
                # entirely. TODO Note that this raise the
                # issue of what happens when a non-reflexive association
                # has an entity map that isn't a part of the
                # association:
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

                    except AttributeError:
                        # If the object stored in map.value is the wrong
                        # type, use the map.entity reference. This is
                        # for situations where the user appends the
                        # wrong type, but we don't want to raise an
                        # error, instead prefering that the error is
                        # discovered in the broken rules collection. See
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
                        # that `map.value no in es` does the same thing.
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
        """ This event handler occures when an association is removed
        from an assoctions collection. When this happens, we want to
        remove the association's constituent entity (the non-composite
        entity) from its pseudocollection class - but only if it hasn't
        already been marked for deletion (ismarkedfordeletion). If it
        has been marked for deletion, that means the pseudocollection
        class is invoking this handler - so removing the constituent
        would result in infinite recursion.  
        """
        ass = eargs.entity

        isreflexive = ass.orm.isreflexive

        for i, map in enumerate(ass.orm.mappings.entitymappings):
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
                    # association from the db would cause the
                    # constitutent (artifact) object to removed from the
                    # db (cascading deletes). This is not what we want:
                    # We should be able to delete as association between
                    # two entity object without deleting the entities
                    # themselves.  pop()ing the entity off the trash
                    # collection will prevent the constitutent from
                    # being deleted.

                    # Commenting out until it_removes_*_associations is
                    # fixed
                    #es.orm.trash.pop()

                    break
            
        super()._self_onremove(src, eargs)

    def entities_onadd(self, src, eargs):
        """
        An event handler invoked when an entity is added to the
        association (``self``) through the associations
        pseudocollection, e.g.::

            # Create artist entity
            art = artist()            

            # Add artifact entity to the artist's pseudocollection
            art.artifact += artifact() 

        :param: src entities:    The pseudocollection's entities object.
        :param: eargs eventargs: The event arguments. Its ``entity``
                                 property is the entity object being
                                 added to the pseudocollection.
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
                        # id). In this case, ass.invalid == True so we
                        # continue to the next association.
                        e = getattr(ass, map.name)

                        if e and e.id == eargs.entity.id:
                            # eargs.entity already exists as a
                            # constitutent entity in this collection of
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
            raise AttributeError(msg)

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

        :param: paryt.party actual: The proprietor that is being used.
        :param: paryt.party expected: The proprietor that was expected.
        """
        self.actual = actual
        self._expected = expected

    @property
    def expected(self):
        if not self._expected:
            return orm.proprietor
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
        

