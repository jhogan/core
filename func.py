# vim: set et ts=4 sw=4 fdm=marker

# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2021

from functools import reduce
import inspect
import pdb
import builtins
import sys

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

        @property
        def even(self):
            return self % 2 == 0

        @property
        def odd(self):
            return not self.even

            
    i = seqint(start, iterable=iterable)
    for e in iterable:
        yield i, e
        i += 1
        
# TODO It would be nice if getattr() could also handle indexors, i.e.,
#
#     getattr(els, "attributes['id']")
# 
# The second argument above could probably be converted to:
#
#     getattr(els, "attributes.__getitem__")('id')
#
# with a precompiled regex

def getattr(obj, attr, *args):
    # Redefine getattr() to support deep attribututes 
    # 
    # For example:
    #    Instead of this:
    #        entity.constituents.first.id
    #    we can do this:
    #        getattr(entity, 'constituents.first.id')
    def rgetattr(obj, attr):
        if obj:
            return builtins.getattr(obj, attr, *args)
        return None
    return reduce(rgetattr, [obj] + attr.split('.'))
