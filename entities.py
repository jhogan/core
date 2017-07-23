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
from pdb import set_trace; B=set_trace
from random import randint, sample
class entities(object):
    def __init__(self, initial=None):
        self.clear()

        # Since event objects are subtypes of entities, don't add events 
        # unless self is not a type of event.
        if not isinstance(self, event):
            self.onadd    = event()
            self.onremove = event()

        if initial != None:
            self.append(initial)

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
        for t in self._list:
            yield t

    def getrandom(self, returnIndex=False):
        if self.isempty: return None
        ix = randint(0, self.ubound)
        if returnIndex:
            return self[ix], ix
        else:
            return self[ix]

    def getrandomized(self):
        """ Return a randomized version of self."""
        return type(self)(sample(self._ls, self.count))

    def where(self, qry):
        if type(qry) == type:
            cls = self.__class__
            return cls([x for x in self if type(x) == qry])

        fn = qry
        es = type(self)()
        for e in self:
            if fn(e): es += e
        return es

    def sort(self, key):
        self._ls.sort(key=key)

    def sorted(self, key):
        return type(self)(sorted(self._ls, key=key))

    def tail(self, number):
        if number > 0:
            return type(self)(self[-number:])
        return type(self)()

    def clear(self):
        # TODO Seems like we could just call: self.remove(self) but the tests
        # fail
        for e in self:
            self.onremove(self, entityremoveeventargs(e))
        self._ls=[]

    def remove(self, e):
        if isinstance(e, entities):
            rms = e
        elif callable(e):
            rms = self.where(e)
        elif type(e) == int:
            rm = self._ls[e]
            del self._ls[e]
            self.onremove(self, entityremoveeventargs(rm))
            return
        else:
            rms = [e]

        for i in range(self.ubound, -1, -1):
            for rm in rms:
                if rm is self[i]:
                    del self._list[i]
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
        r = type(self)()
        for e in reversed(self._ls):
            r += e
        return r

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
        return any(e1 is e for e1 in self)

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

        r._list.append(t)

        self._list.append(t)

        try:
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
    def _list(self):
        if not hasattr(self, '_ls'):
            self._ls = []
        return self._ls

    @property
    def count(self):
        return len(self._list)

    def __len__(self):
        return self.count

    @property
    def isempty(self):
        return self.count == 0

    @property
    def hasone(self):
        return self.count == 1

    @property
    def ispopulated(self):
        return not self.isempty

    def __repr__(self):
        r=''
        for i, t in enumerate(self):
            r += repr(t) + '\n'
        return r

    def __str__(self):
        r=''
        for i, t in enumerate(self):
            r += str(t) + '\n'
        return r

    def __setitem__(self, key, item):
        e = self[key]
        self._ls[key]=item
        self.onremove(self, entityremoveeventargs(e))
        self.onadd(self, entityaddeventargs(item))

    def __getitem__(self, key):
        if type(key) == int or type(key) == slice:
            return self._list[key]

        for e in self._list:
            if hasattr(e, 'id'):
                if e.id == key:   return e
            elif hasattr(e, 'name'):
                if e.name == key: return e

    def getindex(self, e):
        """ Return the first index of e in the collection.

        This is similar to list.index except here we use the `is` operator for
        comparison instead of the `==` operator."""

        for ix, e1 in enumerate(self):
            if e is e1: return ix
        raise ValueError("'{}' is not in the collection " + str(e))

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
        pass

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

class brokenrules(entities):
    def append(self, o, r=None):
        if isinstance(o, str):
            o = brokenrule(o)
        super().append(o, r)

class brokenrule(entity):
    def __init__(self, msg):
        self.message = msg

    def __str__(self):
        return self.message
    
class event(entities):
    def __call__(self, src, e):
        for callable in self:
            callable(src, e)

    def append(self, fn):
        if not callable(fn):
            raise ValueError('Event must be callable')
        self._list.append(fn)

class eventargs(entity):
    pass

class entityaddeventargs(eventargs):
    def __init__(self, e):
        self.entity = e

class entityremoveeventargs(eventargs):
    def __init__(self, e):
        self.entity = e

class valuechangeeventargs(eventargs):
    def __init__(self, e, oldval, newval):
        self.entity = e
        self.oldval = oldval
        self.newval = newval

    @property
    def values(self):
        return self.oldval, self.newval

class appendeventargs(eventargs):
    def __init__(self, e):
        self.entity = e

class index(entity):
    def __init__(self):
        self._ix = {}

    def append(self, val, e):
        ix     = self._ix
        try:
            vals = ix[id(val)]
        except KeyError:
            ix[id(val)] = vals = []

        vals.append(e)

    def remove(self, val, e):
        ix     = self._ix
        vals = ix[id(val)]

        for i, e1 in enumerate(vals):
            if e is e1:
                del vals[i]
                break
                
        if not len(vals):
            del ix[id(val)]

    def __call__(self, val):
        try:
            return self[val]
        except KeyError:
            return []

    def __getitem__(self, val):
        return self._ix[id(val)]



