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
from datetime import datetime
from pdb import set_trace; B=set_trace
from random import randint, sample
import re
import sys
import builtins
from pprint import pprint
from functools import total_ordering

class entities(object):
    def __init__(self, initial=None):
        self._ls = []

        # The event and indexes classes are subtypes of entites. Don't add
        # events and indexes to these types in order to avoid infinite
        # recursion.
        if not isinstance(self, event) and not isinstance(self, indexes):

            # Instantiate events
            self.onadd                =  event()
            self.onremove             =  event()

            # TODO Write tests for these two events
            self.onbeforevaluechange  =  event()
            self.onaftervaluechange   =  event()

            # Local subscriptions to events
            self.onadd                +=  self._self_onadd
            self.onremove             +=  self._self_onremove

            # Instatiate indexes
            ix = index(name='identity', keyfn=lambda e: e)
            ix.indexes = self.indexes
            self.indexes._ls.append(ix)

        # Append initial collection
        if initial != None:
            self.append(initial)

    def __bool__(self):
        # An entities collection will always pass a truth test
        return True

    def _self_onadd(self, src, eargs):
        for ix in self.indexes:
            ix += eargs.entity

        if hasattr(eargs.entity, 'onbeforevaluechange'):
            eargs.entity.onbeforevaluechange += \
                self._entity_onbeforevaluechange 

        if hasattr(eargs.entity, 'onaftervaluechange'):
            eargs.entity.onaftervaluechange += \
                self._entity_onaftervaluechange 
            
    def _self_onremove(self, src, eargs):
        for ix in self.indexes:
            ix -= eargs.entity

        if hasattr(eargs.entity, 'onbeforevaluechange'):
            eargs.entity.onbeforevaluechange -= \
                self._entity_onbeforevaluechange 

        if hasattr(eargs.entity, 'onaftervaluechange'):
            eargs.entity.onaftervaluechange -= \
                self._entity_onaftervaluechange 

    def _entity_onbeforevaluechange(self, src, eargs):
        # Invoked before a change is made to a value on one of the collected
        # entities

        # Raise an analogous event for the collection itself
        self.onbeforevaluechange(src, eargs)
        for ix in self.indexes:
            if ix.property == eargs.property:
                ix.remove(eargs.entity)

    def _entity_onaftervaluechange(self, src, eargs):
        # Invoked after a change is made to a value on one of the collected
        # entities

        # Raise an analogous event for the collection itself
        self.onaftervaluechange(src, eargs)
        for ix in self.indexes:
            if ix.property == eargs.property:
                ix += eargs.entity

    @property
    def indexes(self):
        if not hasattr(self, '_indexes'):
            self._indexes = indexes(type(self))
        return self._indexes

    @indexes.setter
    def indexes(self, v):
        """ This setter is intended to permit the += operator to be used to 
        add indexes to the entities.indexes collection. Normally, you wouldn't
        want to set the indexes collection this way. """
        self._indexes = v

    def __call__(self, ix):
        """
        Allow collections to be called providing similar functionality to the
        way they can be indexed. 
        """
        # Should negative numbers be allowed. If not, why?
        try: 
            return self[ix]
        except IndexError: 
            return None

    def __iter__(self):
        for t in self._ls:
            yield t

    def pluck(self, prop):
        # TODO: Write test

        ls = []
        for e in self:
            ls.append(getattr(e, prop))

        return ls

    def getrandom(self, returnIndex=False):
        if self.isempty: return None
        ix = randint(0, self.ubound)
        if returnIndex:
            return self[ix], ix
        else:
            return self[ix]

    def getrandomized(self):
        """ Return a randomized version of self."""
        return type(self)(initial=sample(self._ls, self.count))

    def where(self, qry):
        if type(qry) == type:
            cls = self.__class__
            return cls([x for x in self if type(x) == qry])

        fn = qry
        es = type(self)()
        for e in self:
            if fn(e): es += e
        return es


    @total_ordering
    class mintype(object):
        def __le__(self, e): return True
        def __eq__(self, e): return (self is e)

    # TODO Test reverse parameter
    def sort(self, key, reverse=False):

        if type(key) == str:
            min = entities.mintype()
            def key1(x):
                v = getattr(x, key)
                # None's don't sort so do this
                return min if v is None else v
        elif callable(str):
            key1 = key

        self._ls.sort(key=key1, reverse=reverse)

    def sorted(self, key, reverse=False):
        if type(key) == str:
            min = entities.mintype()
            def key1(x):
                v = getattr(x, key)
                # None's don't sort so do this
                return min if v is None else v
        elif callable(str):
            key1 = key

        return type(self)(sorted(self._ls, key=key1, reverse=reverse))

    def tail(self, number):
        if number > 0:
            return type(self)(self[-number:])
        return type(self)()

    def clear(self):
        self.remove(self)

    def remove(self, e):
        if isinstance(e, entities):
            rms = e
        elif callable(e) and not isinstance(self, event):
            rms = self.where(e)
        elif type(e) == int:
            rm = self._ls[e]
            del self._ls[e]
            self.onremove(self, entityremoveeventargs(rm))
            return
        else:
            rms = [e]

        for i in range(self.count - 1, -1, -1):
            for rm in rms:
                if rm is self[i]:
                    del self._ls[i]
                    self.onremove(self, entityremoveeventargs(rm))
                    break

    def __isub__(self, e):
        self.remove(e)
        return self

    def shift(self):
        return self.pop(0)

    def pop(self, ix=None):
        if self.count == 0:
            return None

        if ix == None: 
            e = self.last
            self._ls.pop()
        else:
            e = self[ix]
            self._ls.pop(ix)
        self.onremove(self, entityremoveeventargs(e))
        return e

    def reversed(self):
        for e in reversed(self._ls):
            yield e

    def reverse(self):
        self._ls.reverse()

    @property
    def ubound(self):
        if self.isempty: return None
        return self.count - 1

    def insert(self, ix, e):
        self.insertbefore(ix, e)

    def insertbefore(self, ix, e):
        self._ls.insert(ix, e)
        try:
            self.onadd(self, entityaddeventargs(e))
        except AttributeError as ex:
            msg = str(ex)
            msg += '\n' + 'Ensure the superclass\'s __init__ is called.'
            raise AttributeError(msg)

    def insertafter(self, ix, e):
        self.insertbefore(ix + 1, e)

    def unshift(self, e):
        # TODO: Return entities object to indicate what was unshifted
        self.insertbefore(0, e)

    def push(self, e):
        self += e

    def move(self, srcix, dstix):
        raise NotImplementedError('move has not been implemented yet')
        # TODO: This is untested
        # NOTE When implemented, ensure that onadd does not get needlessly 
        # called
        if srcix == dstix:
            raise Exception('Source and destination are the same: {}'.format((srcix, dstix)))

        e = self.pop(srcix)
        self.insert(dstix, e)

    def has(self, e):
        return self.indexes['identity'](e).ispopulated

    def hasnt(self, e):
        return not self.has(e)

    def __lshift__(self, a):
        self.unshift(a)
    
    def append(self, obj, uniq=False, r=None):
        # Create the return object if it hasn't been passed in
        if r == None:
            # We use a generic entities class here because to use the subclass
            # (type(self)()) would cause errors in subclasses that demanded
            # positional arguments be supplied.
            r = entities()

        if isinstance(obj, entity):
            t = obj

        elif hasattr(obj, '__iter__'):
            for t in obj:
                if uniq:
                    if self.hasnt(t):
                        self.append(t, r=r)
                else:
                    self.append(t, r=r)
            return r
        else: 
            raise ValueError('Unsupported object appended: ' + str(type(obj)))

        if uniq and self.has(t):
            return r

        r._ls.append(t)

        self._ls.append(t)

        try:
            if not isinstance(self, event) and not isinstance(self, indexes):
                self.onadd(self, entityaddeventargs(t))
        except AttributeError as ex:
            msg = str(ex)
            msg += '\n' + 'Ensure the superclass\'s __init__ is called.'
            raise AttributeError(msg)

        return r

    def __iadd__(self, t):
        self.append(t)
        return self

    def __iand__(self, t):
        self.append(t, uniq=True)
        return self

    def __add__(self, es):
        r = type(self)()
        r += self
        r += es
        return r

    def __sub__(self, es):
        r = type(self)()

        # If es is not an iterable, such as an entitities collection, assume 
        # it is an entity object and convert it into a collection of one.
        if not hasattr(es, '__iter__'):
            es = entities([es])

        for e in self:
            if es.hasnt(e):
                r += e
        return r

    @property
    def count(self):
        return len(self._ls)

    def getcount(self, qry):
        # TODO Test
        return self.where(qry).count

    def __len__(self):
        return self.count

    @property
    def isempty(self):
        return self.count == 0

    @property
    def hasone(self):
        return self.count == 1

    @property
    def hasplurality(self):
        return self.count > 1

    @property
    def ispopulated(self):
        return not self.isempty

    def __repr__(self):
        return self._tostr(repr)

    def __str__(self):
        return self._tostr(str)

    def _tostr(self, fn=str, includeHeader=True):
        if includeHeader:
            r = '{} object at {} count: {}\n' \
                .format(type(self), hex(id(self)), self.count)
            indent = ' ' * 4 
        else:
            r = ''
            indent = ''

        for i, t in enumerate(self):
            r += indent + fn(t) + '\n'
        return r

    def __setitem__(self, key, item):
        e = self[key]
        self._ls[key]=item

        # If key is a slice. then what was removed and what was added could
        # have been an iterable. Therefore, we need to convert them to
        # iterable then raise the onadd and onremove events for each entity
        # that had been removed and added.
        items  =  item  if  hasattr(item,  '__iter__')  else  [item]
        es     =  e     if  hasattr(e,     '__iter__')  else  [e]
            
        for item in items:
            self.onadd(self, entityaddeventargs(item))

        for e in es:
            self.onremove(self, entityremoveeventargs(e))

    def __getitem__(self, key):
        if type(key) == int or type(key) == slice:
            return self._ls[key]

        for e in self._ls:
            if hasattr(e, 'id'):
                if e.id == key:   return e
            elif hasattr(e, 'name'):
                if e.name == key: return e

    def getindex(self, e):
        """ Return the first index of e in the collection.

        This is similar to list.index except here we use the `is` operator for
        comparison instead of the `==` operator."""

        # TODO:OPT We may be able to cache this and invalidate the cache using
        # the standard events

        for ix, e1 in enumerate(self):
            if e is e1: return ix
        raise ValueError("'{}' is not in the collection " + repr(e))

    @property
    def first(self): 
        return self(0)

    @first.setter
    def first(self, v): 
        self[0] = v

    @property
    def second(self): 
        return self(1)

    @second.setter
    def second(self, v): 
        self[1] = v

    @property
    def third(self): 
        return self(2)

    @third.setter
    def third(self, v): 
        self[2] = v
    @property
    def fourth(self): 
        return self(3)

    @fourth.setter
    def fourth(self, v): 
        self[3] = v

    @property
    def fifth(self): 
        return self(4)

    @fifth.setter
    def fifth(self, v): 
        self[4] = v

    @property
    def sixth(self): 
        return self(5)

    @sixth.setter
    def sixth(self, v): 
        self[5] = v

    @property
    def last(self): 
        return self(-1)

    # TODO Add tests
    @last.setter
    def last(self, v): 
        self[-1] = v

    @property
    def ultimate(self): 
        return self.last

    @ultimate.setter
    def ultimate(self, v): 
        self.last = v

    @property
    def penultimate(self): 
        return self(-2)

    @penultimate.setter
    def penultimate(self, v): 
        self[-2] = v

    @property
    def antepenultimate(self): 
        return self(-3)

    @antepenultimate.setter
    def antepenultimate(self, v): 
        self[-3] = v

    @property
    def preantepenultimate(self): 
        return self(-4)

    @preantepenultimate.setter
    def preantepenultimate(self, v): 
        self[-4] = v

    @property
    def brokenrules(self):
        r = brokenrules()
        for e in self:
            brs = e.brokenrules
            if not isinstance(brs, brokenrules):
                msg = 'Broken rule is an invalid type. '
                msg += 'Ensure you are using the @property decorator '
                msg += 'and the property is returning a brokenrules '
                msg += 'collection.'
                raise ValueError(msg)
            r += brs
        return r

    @property
    def isvalid(self):
        return self.brokenrules.isempty

class entity():
    def __init__(self):
        self.onbeforevaluechange = event()
        self.onaftervaluechange = event()

    @property
    def log(self):
        # Defer import to avoid circular dependency
        from configfile import configfile
        return configfile.getinstance().logs.default

    def _setvalue(self, field, new, prop, setattr=setattr):
        # TODO: It's nice to strip any string because that's vitually
        # always the desired behaviour.  However, at some point, we will
        # want to preserve the whitespace on either side.  Therefore, we
        # should add a parameter (or something) to make it possible to
        # persiste an unstripped string.
        if type(new) == str:
            new = new.strip()

        old = getattr(self, field)

        if old != new:
            if hasattr(self, 'onbeforevaluechange'):
                eargs = entityvaluechangeeventargs(self, prop)
                self.onbeforevaluechange(self, eargs)

            setattr(self, field, new)

            if hasattr(self, 'onaftervaluechange'):
                eargs = entityvaluechangeeventargs(self, prop)
                self.onaftervaluechange(self, eargs)

            # TODO: Return value is new. Add a unit tests for it.
            return new

    def add(self, e):
        es = entities()
        es += self
        es += e
        return es

    def __add__(self, t):
        return self.add(t)

    @property
    def brokenrules(self):
        return brokenrules()

    @property
    def isvalid(self):
        return self.brokenrules.isempty

class brokenruleserror(Exception):
    def __init__(self, msg, obj):
        self.message = msg
        self.object = obj

class brokenrules(entities):
    def append(self, o, r=None):
        if isinstance(o, str):
            o = brokenrule(o)
        super().append(o, r)

    def demand(self, cls, prop, 
                     full=False, 
                     isemail=False, 
                     isdate=False,
                     max=None,
                     type=None):
        v = getattr(cls, prop)

        if type is not None and v is not None:
            if builtins.type(v) is not type:
                self += brokenrule(prop + ' is wrong type', prop, 'valid')

        if full:
            if (builtins.type(v) == str and v.strip() == '') or v is None:
                self += brokenrule(prop + ' is empty', prop, 'full')

        if isemail:
            pattern = r'[^@]+@[^@]+\.[^@]+'
            if v == None or not re.match(pattern, v):
                self += brokenrule(prop + ' is invalid', prop, 'valid')

        if max != None:
            if v != None and len(v) > max:
                # property can only break the 'fits' rule if it hasn't broken
                # the 'full' rule. E.g., a property can be a string of
                # whitespaces which may break the 'full' rule. In that case,
                # a broken 'fits' rule would't make sense.
                if not self.contains(prop, 'full'):
                    self += brokenrule(prop + ' is too lengthy', prop, 'fits')

        if isdate:
            if builtins.type(v) != datetime:
                self += brokenrule(prop + " isn't a date", prop, 'valid')

    def contains(self, prop=None, type=None):
        for br in self:
            if (prop == None or br.property == prop) and \
               (type == None or br.type     == type):
                return True
        return False
                

class brokenrule(entity):
    def __init__(self, msg, prop=None, type=None):
        self.message = msg
        self.property = prop

        if type != None:
            if type not in ['full', 'valid', 'fits', 'empty', 'unique']:
                raise Exception('Invalid brokenrules type')
        self.type = type

    def __str__(self):
        return self.message
    
class event(entities):
    def __call__(self, src, e):
        for callable in self:
            callable(src, e)

    def append(self, fn):
        if not callable(fn):
            raise ValueError('Event must be callable')
        if isinstance(fn, event):
            raise ValueError('Attempted to append event to event collection.')
            
        self._ls.append(fn)

    def remove(self, fn):
        # This is experimental as of 20180506. Previously, events were removed
        # by the base method entities.remove(). But it was noticed that the
        # identity test wasn't matching the bound method being removed:
        #
        #    if rm is self[i]:
        #
        # Bound method id's (id(obj.method)) seem to change over time. 
        # However, an equality test does match bound method which is why
        # the code below reads:
        #
        #    if fn == self[i]
        #
        # This may also explain why it has been noticed that there have
        # been a build up of events in event collections which it would
        # seem shouldn't be there.
        if not callable(fn):
            raise ValueError('Event must be callable')

        for i in range(self.count - 1, -1, -1):
            if fn == self[i]:
                del self._ls[i]
                break

class eventargs(entity):
    pass

class entityaddeventargs(eventargs):
    def __init__(self, e):
        self.entity = e

class entityremoveeventargs(eventargs):
    def __init__(self, e):
        self.entity = e

class entityvaluechangeeventargs(eventargs):
    def __init__(self, e, prop):
        self.property = prop
        self.entity = e

class appendeventargs(eventargs):
    def __init__(self, e):
        self.entity = e

class indexes(entities):
    def __init__(self, cls):
        super().__init__()
        self.class_ = cls
        
    def __getitem__(self, name):
        if type(name) == int:
            return super().__getitem__(name)

        for ix in self:
            if ix.name == name:
                return ix
        return None

    def append(self, ix, uniq=None, r=None):
        ix.indexes = self
        return super().append(ix, uniq, r)
        
class index(entity):
    def __init__(self, name=None, keyfn=None, prop=None):
        self._ix = {}
        self.name = name
        self.keyfunction = keyfn
        self.property = prop

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        if type(name) == int:
            raise ValueError('"name" cannot be an int')
        self._name = name

    def append(self, e):
        ix     = self._ix

        val = self.keyfunction(e)
        key = index._getkey(val)

        try:
            vals = ix[key]
        except KeyError:
            ix[key] = vals = []

        vals.append(e)

    @staticmethod
    def _getkey(val):
        # TODO: Since lists aren't hashable, we convert the list to a string.
        # This isn't ideal since using (0, 1) as the index value on retrieval
        # is the same as using [0, 1].


        # Try to return a hashable version of the value
        if val.__hash__:
            return val
        elif type(val) == list:
            return tuple(val)
        else:
            return id(val)

    def __iadd__(self, e):
        self.append(e)
        return self

    def remove(self, e):
        ix     = self._ix

        val = self.keyfunction(e)
        key = index._getkey(val)

        vals = ix[key]

        for i, e1 in enumerate(vals):
            if e is e1:
                del vals[i]
                break
                
        if not len(vals):
            del ix[key]

    def __isub__(self, e):
        self.remove(e=e)
        return self

    def __call__(self, val, limit=None):
        try:
            return self[val, limit]
        except KeyError:
            return self.indexes.class_()

    def getlist(self, val, limit=None):
        key = index._getkey(val)

        ls = self._ix[key]
        return ls[:limit]

    def __getitem__(self, args):
        if type(args) == tuple:
            val, limit = args
        else:
            val, limit = args, None

        cls = self.indexes.class_
        es = cls()

        # Don't use the constructor's initial parameter. It relies on a 
        # correct implementation of __init__ in the subclass. 
        for e in self.getlist(val, limit):
            es += e
        return es

    def __len__(self):
        return len(self._ix)

def demand(sub, type=None):
    if type is not None:
        if builtins.type(sub) != type:
            msg = 'Value is of type {} instead of {}'
            msg = msg.format(str(builtins.type(sub)), str(type))
            raise TypeError(msg)
