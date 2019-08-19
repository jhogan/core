# vim: set et ts=4 sw=4 fdm=marker

# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2019

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
        

