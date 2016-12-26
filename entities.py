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
from random import randint

class entities(object):
    def __init__(self):
        self.clear()

    def clear(self):
        self._ls=[]

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

    def where(self, fn):
        es = entities()
        for e in self:
            if fn(e): es += e
        return es

    def remove(self, e):
        if callable(e):
            rms = self.where(e)
        else:
            rms = [e]

        for i, e1 in enumerate(self):
            for e2 in rms:
                if e1 is e2:
                    del self._list[i]
                    break
                

    def reversed(self):
        r = type(self)()
        for e in reversed(self._ls):
            r += e
        return r

    @property
    def ubound(self):
        if self.isempty: return None
        return self.count - 1

    def insert(self, ix, e):
        self.insertBefore(ix, e)

    def insertBefore(self, ix, e):
        self._ls.insert(ix, e)

    def insertAfter(self, ix, e):
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

    def __lshift__(self, a):
        self.unshift(a)

    def append(self, obj, uniq=False, r=None):
        if not r: r = []
        if isinstance(obj, entity):
            t = obj
        elif isinstance(obj, entities):
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

        keyisobj = type(key) != str
            
        for e in self._list:
            if keyisobj:
                if e is key:
                    return e
            else:
                if hasattr(e, 'id'):
                    if e.id == key:   return e
                elif hasattr(e, 'name'):
                    if e.name == key: return e
    @property
    def first(self): return self[0]

    @property
    def second(self): return self[1]

    @property
    def third(self): return self[2]

    @property
    def fourth(self): return self[3]

    @property
    def fifth(self): return self[4]

    @property
    def last(self): return self[-1]

    @last.setter
    def last(self, v): self[-1] = v


    @property
    def top(self):
        """ A synonym of entities.last appropriate when the entities collection
        is being treated like a LIFO stack.  
        """
        return self.last

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
        for e in es:
            if self is e: return True
        return False

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
    
    
