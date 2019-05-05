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

def enumerate(iterable, start=0):

    class seqint(int):
        def __new__(cls, *args, **kwargs):
            try:
                iterable = kwargs['iterable']
            except IndexError:
                raise IndexError('Missing iterable')
            else:
                del kwargs['iterable']
            
            r = super(seqint, cls).__new__(cls, *args, **kwargs)
            r.iterable = iterable
            return r

		# TODO Finish off the subtype-specific operators
		# See https://stackoverflow.com/questions/3238350/subclassing-int-in-python
        def __add__(self, other):
            r = super(seqint, self).__add__(other)
            return self.__class__(r, iterable=self.iterable)

        def __sub__(self, other):
            r = super(seqint, self).__sub__(other)
            return self.__class__(r, iterable=self.iterable)

        def __mul__(self, other):
            r = super(seqint, self).__mul__(other)
            return self.__class__(r, iterable=self.iterable)

        def __div__(self, other):
            r = super(seqint, self).__div__(other)
            return self.__class__(r, iterable=self.iterable)

        def __str__(self):
            return ("%d" % int(self))

        @property
        def first(self):
            return self == 0

        @property
        def second(self):
            return self == 1
            
        @property
        def last(self):
            return len(self.iterable) - 1 == self
            
    i = seqint(start, iterable=iterable)
    for e in iterable:
        yield i, e
        i += 1
        

