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
            epi = epiphany()
            epi.mappings = mappings()
            body['epiphany'] = epi

            for name, map in body.items():
                if not isinstance(map, mapping):
                    continue
                
                map._name = name
                epi.mappings += map


        return super().__new__(cls, name, bases, body)

class entity(entities.entity, metaclass=entitymeta):
    def __init__(self):
        self._id = uuid4()
        super().__init__()
    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, v):
        self._id = v
        return self._id

    def __dir__(self):
        return super().__dir__() + [x.name for x in self.epiphany.mappings]

    def __setattr__(self, attr, v):
        # Need to handle 'epiphany' first, otherwise the code below that
        # calls self.epiphany won't work.
        if attr == 'epiphany':
            return object.__setattr__(self, attr, v)

        map = self.epiphany.mappings[attr]

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
        brs = entities.brokenrules()
        for map in self.epiphany.mappings:

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

        if attr != 'epiphany':
            map = self.epiphany.mappings[attr]

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
