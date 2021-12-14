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

""" This module contains a set of hightly reuseable functions.
"""

def enumerate(iterable, start=0):
    """ enumerate is a clone of Python's builtin enumerate() function.
    However, unlike builtins.enumerate(), the first element of the
    tuple returns a subclass of int with special capabilities;:

        ls = ['red', 'blue', 'green']
        for i, e in func.enumerate(ls):
            if i.first:
                assert e == 'red'
                assert i == 0
            elif i.second:
                assert e == 'blue'
                assert i == 1
            elif i.last:
                assert e == 'green'
                assert i == 2

    In the above example, even though i is an int, it has properties
    that make it easy to see where in the loop we are. This function is
    useful when the first or last element being iterated over needs
    conditional logic - which is often the case.

    :param: iterable sequence|iterator: The iterable to create enumerate
    object for.

    :param: start int: Where the counter starts.
    """

    class seqint(int):
        """ A subclass of int that helps report on where in the sequence
        of an iteration we are (see the first, second and last
        @property's.
        """
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
            """ Return True if the integer represents the first
            iteration, False otherwise.
            """
            return self == 0

        @property
        def second(self):
            """ Return True if the integer represents the second
            iteration, False otherwise.
            """
            return self == 1
            
        @property
        def last(self):
            """ Return True if the integer represents the last
            iteration, False otherwise.
            """
            return len(self.iterable) - 1 == self

        @property
        def even(self):
            """ Return True if the integer is an even number, False
            otherwise.
            """
            return self % 2 == 0

        @property
        def odd(self):
            """ Return True if the integer is an odd number, False
            otherwise.
            """
            return not self.even

    # Create a seqint using start and iterable
    i = seqint(start, iterable=iterable)

    # Iterate over `iterable` yielding the counter and the element as a
    # two element cursor.
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
