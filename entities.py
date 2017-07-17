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
        if initial != None:
            self.append(initial)

    def clear(self):
        self._ls=[]

    def __call__(self, ix):
        """
        Allow collections to be called providing similar functionality to the
        way they can be indexed. The difference is that None is returned if ix
        is not a valid index. Only positve indexes are considered valid.
        """
        try: 
            if ix < 0:
                raise IndexError
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
        es = type(self)()
        ls = sorted(self._ls, key=key)
        for e in ls:
            es += e
        return es

    def tail(self, number):
        es = type(self)()
        if number > 0:
            for e in self[-number:]:
                es += e
        return es

    def remove(self, e):
        if isinstance(e, entities):
            rms = e
        elif callable(e):
            rms = self.where(e)
        elif type(e) == int:
            del self._ls[e]
            return
        else:
            rms = [e]

        for i in range(self.ubound, -1, -1):
            for rm in rms:
                if rm is self[i]:
                    del self._list[i]
                    break

    def __isub__(self, e):
        self.remove(e)
        return self

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

    def insertafter(self, ix, e):
        self._ls.insert(ix + 1, e)

    def move(self, srcix, dstix):
        # TODO: This is untested
        if srcix == dstix:
            raise Exception('Source and destination are the same: {}'.format((srcix, dstix)))

        e = self.pop(srcix)
        self.insert(dstix, e)

    def shift(self):
        return self._ls.pop(0)

    def unshift(self, t):
        # TODO: Return entities object to indicate what was unshifted
        return self._ls.insert(0, t)

    def pop(self, ix=None):
        if ix == None: return self._ls.pop()
        return self._ls.pop(ix)

    def push(self, e):
        self += e

    def has(self, e):
        return any(e1 is e for e1 in self)

    def hasnt(self, e):
        return not self.has(e)

    def __lshift__(self, a):
        self.unshift(a)
    
    def append(self, obj, uniq=False, r=None):
        if not r: r = []
        if isinstance(obj, entity):
            t = obj
        elif isinstance(obj, entities) or hasattr(obj, '__iter__'):
            for t in obj:
                if uniq:
                    for t1 in self:
                        if t is t1: break
                    else:
                        self.append(t, r=r)
                        continue
                    break
                else:
                    self.append(t, r=r)
            return r
        else: 
            raise ValueError('Unsupported object appended')

        if uniq:
            for t1 in self:
                if t is t1: return r

        r.append(t)
        for t in r:
            self._list.append(t)

        return r

    def __iadd__(self, t):
        self.append(t)
        return self

    def __iand__(self, t):
        self.append(t, uniq=True)
        return self

    def add(self, ts):
        self += ts
        return self

    def __add__(self, t):
        return self.add(t)

    def __sub__(self, es):
        r = type(self)()
        for e in self:
            if not e.isin(es):
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

    def __str__(self):
        if not self.isempty:
            r=''
            for i, t in enumerate(self):
                if i > 0: r += "\n"
                r += str(t)
            return r
        return ''

    def __setitem__(self, key, item):
        self._ls[key]=item

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
        comarison instead of the `==` operator."""

        for ix, e1 in enumerate(self):
            if e is e1: return ix
        raise ValueError("'{}' is not in the collection " + e)

    def _getbyindex(self, ix):
        # TODO This can be replace with a call to enttities.__call__
        try: return self[ix]
        except IndexError: return None

    @property
    def first(self): return self._getbyindex(0)

    @property
    def second(self): return self._getbyindex(1)

    @second.setter
    def second(self, v): self[1] = v

    @property
    def third(self): return self._getbyindex(2)

    @property
    def fourth(self): return self._getbyindex(3)

    @property
    def fifth(self): return self._getbyindex(4)

    @property
    def sixth(self): return self._getbyindex(5)

    @property
    def last(self): return self._getbyindex(-1)

    @last.setter
    def last(self, v): self[-1] = v

    @property
    def brokenrules(self):
        r = brokenrules()
        for ent in self:
            r += ent.brokenrules
        return r

    @property
    def isvalid(self):
        return self.brokenrules.isempty

class entity():
    def __init__(self):
        pass

    def add(self, t):
        th = entities()
        th += self
        th += t
        return th

    def isin(self, es):
        """Test if self is in entities object `es`. This is like the the `in`
        operator (__contains__()) except it tests for object identity (with `is`) 
        instead of object equality (`==` or __eq__()).
        """
        return any(self is e for e in es)

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
            d = ix[id(val)]
        except KeyError:
            ix[id(val)] = d = {}

        d[id(e)] = e

    def remove(self, val, e):
        ix     = self._ix
        del ix[id(val)][id(e)]
        if not len(ix[id(val)]):
            del ix[id(val)]

    def __getitem__(self, val):
        return self._ix[id(val)]

    def __call__(self, val):
        try:
            return self[val].values()
        except KeyError:
            return []
