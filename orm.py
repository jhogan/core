# vim: set et ts=4 sw=4 fdm=marker
"""
MIT License

Copyright (c) 2018 Jesse Hogan

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
from pdb import set_trace; B=set_trace
from pprint import pprint
from table import table
import builtins
import textwrap
from uuid import uuid4, UUID
import entities as entitiesmod
import sys
import db
from MySQLdb.constants.ER import BAD_TABLE_ERROR
import MySQLdb
from enum import Enum, unique

@unique
class types(Enum):
    str = 0
    int = 1
    pk  = 2

class undef:
    pass

class entities(entitiesmod.entities):
    pass

class entitymeta(type):
    def __new__(cls, name, bases, body):
        # If name == 'entity', the `class entity` statement is being executed.
        if name != 'entity':
            orm_ = orm()
            orm_.mappings = mappings(orm_)

            try:
                body['entities']
            except KeyError:
                for sub in orm_.getentitiessubclasses():

                    if sub.__name__   == name + 's' and \
                       sub.__module__ == body['__module__']:

                        body['entities'] = sub
                        break
                else:
                    msg = "Entities class coudn't be found. "
                    msg += "Either specify one or define one with a predictable name"
                    raise AttributeError(msg)

            orm_.entities = body['entities']
            del body['entities']

            try:
                orm_.table = body['table']
                del body['table']
            except KeyError:
                orm_.table = orm_.entities.__name__

            body['id'] = mapping(name='id', type=types.pk)
            for name1, map in body.items():
                if not isinstance(map, mapping):
                    continue
                
                map._name = name1
                orm_.mappings += map

            for map in orm_.mappings:
                del body[map.name]

            # Make sure the mappings are sorted in the order they are
            # instantiated
            orm_.mappings.sort('_ordinal')

            # The id will be the last elment, so pop it off and unshift so it's
            # always the first element
            orm_.mappings << orm_.mappings.pop()

            body['orm'] = orm_

        return super().__new__(cls, name, bases, body)

class entity(entitiesmod.entity, metaclass=entitymeta):
    def __init__(self, id=None):
        self.orm = self.orm.clone()
        self.orm.mappings.entity = self

        if id is None:
            self.orm.isnew = True
            self.orm.isdirty = False
            self.id = uuid4()
        else:
            sql = 'select * from {} where id = %s'
            sql = sql.format(self.orm.table)

            args = id.bytes,

            # TODO Make db.pool varient
            pool = db.pool.getdefault()

            with pool.take() as conn:
                cur = conn.createcursor()
                cur.execute(sql, args)

            ress = db.dbresultset(cur)
            ress.demandhasone()
            res = ress.first
            for map in self.orm.mappings:
                map.value = res[map.name]

            self.orm.isnew = False
            self.orm.isdirty = False

        super().__init__()

        # Events
        self.onaftervaluechange  +=  self._self_onaftervaluechange

    def _self_onaftervaluechange(self, src, eargs):
        if not self.orm.isnew:
            self.orm.isdirty = True

    def __dir__(self):
        return super().__dir__() + [x.name for x in self.orm.mappings]

    def __setattr__(self, attr, v):
        # Need to handle 'orm' first, otherwise the code below that
        # calls self.orm won't work.
        if attr == 'orm':
            return object.__setattr__(self, attr, v)

        map = self.orm.mappings[attr]

        if map is None:
            return object.__setattr__(self, attr, v)
        else:
            # Call entity._setvalue to take advantage of its event raising
            # code. Pass in a custom setattr function for it to call. Use
            # underscores for the paramenters since we already have the values
            # it would pass in in this method's scope - execpt for the v
            # which, may have been processed (i.e, if it is a str, it will
            # have been strip()ed. 
            def setattr(_, __, v):
                map.value = v

            self._setvalue(attr, v, attr, setattr)

    @property
    def brokenrules(self):
        brs = entitiesmod.brokenrules()
        for map in self.orm.mappings:

            if map.type == str:
                if map.max is undef:
                    if map.value is not None:
                        brs.demand(self, map.name, max=255)
                else:
                    brs.demand(self, map.name, max=map.max)

                if map.full:
                    brs.demand(self, map.name, full=True)
                        
        return brs

    def __getattribute__(self, attr):
        map = None

        if attr != 'orm' and self.orm.mappings:
            map = self.orm.mappings[attr]

        if map is None:
            return object.__getattribute__(self, attr)

        return map.value

class mappings(entities.entities):
    pass

class mapping(entities.entity):
    def __init__(self, type, default=undef, max=undef, full=False):
        self._type = type
        self._value = undef
        self._default = default
        self._max = max
        self._full = full
        self._name = None

    @property
    def full(self):
        return self._full

    @property
    def default(self):
        return self._default

    @property
    def max(self):
        return self._max

    @property
    def type(self):
        return self._type

    @property
    def name(self):
        return self._name

    @property
    def value(self):
        if self._value is undef:
            if self.default is undef:
                if self.type == types.str:
                    return ''
            else:
                return self.default
        else:
            if self.ispk and type(self._value) is bytes:
                self._value = UUID(bytes=self._value)
                
            return self._value

    @value.setter
    def value(self, v):
        self._value = v

class orm:
    def __init__(self):
        self.mappings = None
        self.isnew = False
        self.isdirty = False
        self.ismarkedfordeletion = False
        self.entities = None
        self.table = None

    def clone(self):
        r = orm()

        for p in 'isnew', 'isdirty', 'ismarkedfordeletion', 'entities', 'table':
            setattr(r, p, getattr(self, p))

        r.mappings = self.mappings.clone(r)

        return r

    @property
    def properties(self):
        return [x.name for x in self.mappings]

    @staticmethod
    def getentitiessubclasses(cls=entities):
        r = []

        for subclass in cls.__subclasses__():
            r.append(subclass)
            r.extend(orm.getentitiessubclasses(subclass))

        return r
