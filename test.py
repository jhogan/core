# vim: set et ts=4 sw=4 fdm=marker

########################################################################
# Copyright (C) Jesse Hogan - All Rights Reserved                      #
# Unauthorized copying of this file, via any medium is strictly        #
# prohibited                                                           #
# Proprietary and confidential                                         #
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2019                 #
########################################################################

from articles import *
from auth import jwt
from configfile import configfile
from contextlib import contextmanager
from datetime import timezone, datetime
from entities import BrokenRulesError, rgetattr
from func import enumerate
from MySQLdb.constants.ER import BAD_TABLE_ERROR, DUP_ENTRY
from parties import *
from pdb import Pdb
from random import randint, uniform
from table import *
from tester import *
from uuid import uuid4
import dateutil
import db
import decimal; dec=decimal.Decimal
import functools
import io
import jwt as pyjwt
import math
import MySQLdb
import _mysql_exceptions
import orm
import pathlib
import primative
import re
import textwrap
import dom
import gem

# Set conditional break points
def B(x=True):
    if x: 
        #Pdb().set_trace(sys._getframe().f_back)
        from IPython.core.debugger import Tracer; 
        Tracer().debugger.set_trace(sys._getframe().f_back)

# We will use basic and supplementary multilingual plane UTF-8
# characters when testing str attributes to ensure unicode is being
# supported.

# A two byte character from the Basic Multilingual Plane

Δ = bytes("\N{GREEK CAPITAL LETTER DELTA}", 'utf-8').decode()

# A three byte character
V = bytes("\N{ROMAN NUMERAL FIVE}", 'utf-8').decode()

# A four byte character from the Supplementary Multilingual Plane
Cunei_a = bytes("\N{CUNEIFORM SIGN A}", 'utf-8').decode()

def getattr(obj, attr, *args):
    # Redefine getattr() to support deep attributes 
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
    return functools.reduce(rgetattr, [obj] + attr.split('.'))

def la2gr(chars):
    map = {
        'a': b'\u03b1', 'b': b'\u03b2', 'c': b'\u03ba', 'd': b'\u03b4', 'e': b'\u03b5',
        'f': b'\u03c6', 'g': b'\u03b3', 'h': b'\u03b7', 'i': b'\u03b9', 'j': b'\u03c3',
        'k': b'\u03ba', 'l': b'\u03bb', 'm': b'\u03b1', 'n': b'\u03bc', 'o': b'\u03c0',
        'p': b'\u03b1', 'q': b'\u03b8', 'r': b'\u03c1', 's': b'\u03c3', 't': b'\u03c4',
        'u': b'\u03c5', 'v': b'\u03b2', 'w': b'\u03c9', 'x': b'\u03be', 'y': b'\u03c5',
        'z': b'\u03b6',
    }

    r = ''
    for c in chars.lower():
        try:
            r += map[c].decode('unicode_escape')
        except:
            r += ' '
    return r
        
class knights(entities):
    def __init__(self, initial=None):
        self.indexes += index(name='name', 
                        keyfn=lambda k: k.name, 
                        prop='name')

        self.indexes += index(name='traittype', 
                              keyfn=lambda f: type(f.trait),
                              prop='trait')

        super().__init__(initial);

    @staticmethod
    def createthe4():
        ks = knights()
        ks += knight('Lancelot')
        ks += knight('Authur')
        ks += knight('Galahad')
        ks += knight('Bedevere')
        return ks

class sillyknights(knights):
    def __init__(self, initial=None):
        super().__init__(initial);

        # NOTE This is the proper way to override append: the obj, uniq
        # and r parameters must be given and uniq and r must be defaulted
        # to None. The results of the call to the super classe's append
        # methed must be returned to the caller. It's possible to skip
        # some of these step, however neglating to properly override
        # append will result in strange and difficult-to-diagnose bugs
        # when certain, seemingly innocous forms of appending are tried.
        def append(self, obj, uniq=None, r=None):
            # Do something silly
            # Now have the super class do the appending
            return super().append(obj, uniq=uniq,  r=r)

    @staticmethod
    def createthe4():
        ks = sillyknights()
        ks += sillyknight('knight who says ni 1')
        ks += sillyknight('knight who says ni 2')
        ks += sillyknight('french knight')
        ks += sillyknight('black knight')
        return ks

class knight(entity):
    def __init__(self, name):
        self.name = name
        self._trait = None
        super().__init__()

    @property
    def trait(self):
        return self._trait

    @trait.setter
    def trait(self, v):
        self._setvalue('_trait', v, 'trait')

    @property
    def brokenrules(self):
        brs = brokenrules()
        if type(self.name) != str:
            brs += brokenrule("Names must be strings")
        return brs

    def __repr__(self):
        return super().__repr__() + ' ' + self.name

    def __str__(self):
        return str(self.name)

class sillyknight(knight):
    pass

class philosophers(entities):
    pass

class philosopher(entity):
    def __init__(self, name):
        self.name = name

class singer(entity):
    def __init__(self, name):
        self.name = name

class constants(entities):
    pass

class constant(entity):
    def __init__(self, v):
        self.value = v

def createtable(x, y):
    tbl = table()
    for i in range(y):
        r = tbl.newrow()
        for j in range(x):
            r.newfield([i, j])
    return tbl

class test_entities(tester):
    def it_instantiates(self):

        # Plain ol' instantiate
        try:
            es = entities()
        except:
            self.assertFail('Failed instantiating entities')

        # Instantiate with an array of entities
        e1, e2 = entity(), entity()

        es = entities([e1, e2])

        self.assertIs(e1, es[0])
        self.assertIs(e2, es[1])

    def it_is_not_falsy(self):
        es = entities()
        self.assertTruthy(es)

    def it_clears(self):
        """ Test to ensure the clear() method removes entities. """
        es = entities([entity(), entity()])
        es.clear()
        self.assertTrue(es.isempty)
        
    def it_calls__call__(self):
        """ Test that the indexer (__call__()) returns the the correct entity
        or None if the index is invalid. """
        e1, e2 = entity(), entity()

        es = entities([e1, e2])

        self.assertIs(e1, es(0))
        self.assertIs(e2, es(1))

        try:
            e = es(2)
        except:
            self.assertFail('__call__ should return None if index is invalid.')

        self.assertNone(es(2))

    def it_iterates(self):
        """ Ensure the iterator (__iter__()) works. """
        e1, e2 = entity(), entity()

        es = entities([e1, e2])

        for i, e in enumerate(es):
            if i == 0:
                self.assertIs(e1, e)
            elif i == 1:
                self.assertIs(e2, e)
            else:
                self.assertFail('We should have only interated twice.')

    def it_gets_random(self):
        """ Ensure es.getrandom() eventually returns a random entity. """
        e1, e2 = entity(), entity()
        es = entities([e1, e2])

        got1 = got2 = False
        for _ in range(100):
            e = es.getrandom()
            if e is e1:
                got1 = True
            elif e is e2:
                got2 = True

            if got1 and got2:
                break

        if not (got1 and got2):
            self.assertFail('Failed getting random entities')

    def it_gets_randomized(self):
        """ Ensure es.getrandomized() returns a randomized version of itself.
        """

        # Subclass entities to ensure that getrandomized returns a instance of
        # the subclass.
        class pantheon(entities):
            pass

        e1, e2 = entity(), entity()
        gods = pantheon([e1, e2])

        initord = randord = False
        for _ in range(100):
            rgods = gods.getrandomized()

            self.assertEq(pantheon, type(rgods))
            self.assertEq(gods.count, rgods.count)

            if gods.first == rgods.first and gods.second == rgods.second:
                initord = True
            elif gods.first == rgods.second and gods.second == rgods.first:
                randord = True

            if initord and randord:
                break

        if not (initord and randord):
            self.assertFail('Failed getting random entities')

    def it_calls_where(self):
        """ Where queries the entities collection."""

        n = philosopher('neitzsche')
        s = philosopher('schopenhaurer')
        sj = singer('salena jones')
        bb = singer('burt bacharach')

        ps1 = philosophers([n, s, sj, bb])

        # Results of query should return the one entry in 'ps1' where
        # the type is 'singer' (not 'philosopher')
        ps2 = ps1.where(singer)
        self.assertEq(2, ps2.count)
        self.assertEq(philosophers, type(ps2))
        self.assertIs(sj, ps2.first)
        self.assertIs(bb, ps2.second)

        # Test where() using a callable.  Get all the "philosophers" who have
        # 's' in their names. 
        for i in range(2):
            if i == 0:
                # On the first go, use a lambda
                fn = lambda e: 's' in e.name
            else:
                # On the second go, use a function. We just want to make sure 
                # where() doesn't discriminate based on callabel type
                def fn(e):
                    return 's' in e.name
            ps2 = ps1.where(fn)
            self.assertEq(3, ps2.count)
            self.assertEq(philosophers, type(ps2))
            self.assertEq(philosopher, type(ps2.first))
            self.assertEq(philosopher, type(ps2.second))
            self.assertEq(philosopher, type(ps2.second))
            self.assertIs(n, ps2.first)
            self.assertIs(s, ps2.second)
            self.assertIs(sj, ps2.third)

    def it_calls_sort_with_incomparable_types(self):
        # The entities.mintype class was added to sort things that are
        # incomparable, such as uuid's and None values

        # Create a collection of knights
        ks = knights()
        id = uuid4()
        ks += knight(id)
        ks += knight(None)

        ks.sort('name')

        self.assertIs(None, ks.first.name)
        self.assertIs(id, ks.second.name)

        ks.sort('name', True)

        self.assertIs(id, ks.first.name)
        self.assertIs(None, ks.second.name)

    def it_calls_sorted_with_incomparable_types(self):
        # Create a collection of knights
        ks = knights()
        id = uuid4()
        ks += knight(id)
        ks += knight(None)

        ks = ks.sorted('name')

        self.assertIs(None, ks.first.name)
        self.assertIs(id, ks.second.name)

        ks = ks.sorted('name', True)

        self.assertIs(id, ks.first.name)
        self.assertIs(None, ks.second.name)

    def it_calls_sort_with_str(self):
        """ The entities.sort() method sorts the collection in-place -
        much like the standard Python list.sort() does."""

        # Create a collection of knights
        ks = knights()
        ks += knight('Lancelot')
        ks += knight('Authur')
        ks += knight('Galahad')
        ks += knight('Bedevere')
        cnt = ks.count

        # Sort them by name
        ks.sort(key=lambda k: k.name)

        # Test the sort

        # Ensure count hasn't changed
        self.assertEq(cnt, ks.count)

        # Ensure sort is alphabetic
        self.assertEq('Authur',    ks.first.name)
        self.assertEq('Bedevere',  ks.second.name)
        self.assertEq('Galahad',   ks.third.name)
        self.assertEq('Lancelot',  ks.fourth.name)

        Light = 12000000 # miles per minute
        cs = constants()
        cs += constant(Light)
        cs += constant(math.pi)
        cs += constant(math.e)

        cs.sort(key=lambda c: c.value)
        self.assertEq(math.e,    cs.first.value)
        self.assertEq(math.pi,  cs.second.value)
        self.assertEq(Light,    cs.third.value)

    def it_calls_sort_by_lambda(self):
        """ The entities.sort() method sorts the collection in-place -
        much like the standard Python list.sort() does."""

        # Create a collection of knights
        ks = knights()
        ks += knight('Lancelot')
        ks += knight('Authur')
        ks += knight('Galahad')
        ks += knight('Bedevere')
        cnt = ks.count

        # Sort them by name
        ks.sort(key=lambda k: k.name)

        # Test the sort

        # Ensure count hasn't changed
        self.assertEq(cnt, ks.count)

        # Ensure sort is alphabetic
        self.assertEq('Authur',    ks.first.name)
        self.assertEq('Bedevere',  ks.second.name)
        self.assertEq('Galahad',   ks.third.name)
        self.assertEq('Lancelot',  ks.fourth.name)

        # Sort them by name in reverse
        ks.sort(key=lambda k: k.name, reverse=True)

        # Test the sort

        # Ensure count hasn't changed
        self.assertEq(cnt, ks.count)

        # Ensure sort is alphabetic
        self.assertEq('Lancelot',  ks.first.name)
        self.assertEq('Galahad',   ks.second.name)
        self.assertEq('Bedevere',  ks.third.name)
        self.assertEq('Authur',    ks.fourth.name)

        Light = 12000000 # miles per minute
        cs = constants()
        cs += constant(Light)
        cs += constant(math.pi)
        cs += constant(math.e)

        cs.sort(key=lambda c: c.value)
        self.assertEq(math.e,   cs.first.value)
        self.assertEq(math.pi,  cs.second.value)
        self.assertEq(Light,    cs.third.value)

        cs.sort(key=lambda c: c.value, reverse=True)
        self.assertEq(Light,    cs.first.value)
        self.assertEq(math.pi,  cs.second.value)
        self.assertEq(math.e,   cs.third.value)

    def it_calls_sorted_with_str(self):
        """ The entities.sorted() method is like entities.sort() except
        it returns a new sorted entities collection and leaves the existing
        one untouched. """

        Light = 12000000 # miles per minute

        # Create a collection of knights
        ks = knights()
        ks += knight('Lancelot')
        ks += knight('Authur')
        ks += knight('Galahad')
        ks += knight('Bedevere')

        # Create a sorted version
        ks1 = ks.sorted('name')

        # Test the sort

        # Ensure count hasn't changed
        self.assertEq(ks.count, ks1.count)
        self.assertIs(knights, type(ks1))

        # Ensure original was not sorted.
        self.assertEq('Lancelot',  ks.first.name)
        self.assertEq('Authur',    ks.second.name)
        self.assertEq('Galahad',   ks.third.name)
        self.assertEq('Bedevere',  ks.fourth.name)

        # Ensure sort is alphabetic
        self.assertEq('Authur',    ks1.first.name)
        self.assertEq('Bedevere',  ks1.second.name)
        self.assertEq('Galahad',   ks1.third.name)
        self.assertEq('Lancelot',  ks1.fourth.name)

        # Numeric sort 

        # Create numeric constant collection
        cs = constants()
        cs += constant(Light)
        cs += constant(math.pi)
        cs += constant(math.e)

        cs1 = cs.sorted('value')

        # Ensure original was not sorted
        self.assertEq(Light,    cs.first.value)
        self.assertEq(math.pi,  cs.second.value)
        self.assertEq(math.e,   cs.third.value)

        # Ensure cs1 is sorted numerically
        self.assertEq(math.e,   cs1.first.value)
        self.assertEq(math.pi,  cs1.second.value)
        self.assertEq(Light,    cs1.third.value)

    def it_calls_sorted_with_lambda(self):
        """ The entities.sorted() method is like entities.sort() except
        it returns a new sorted entities collection and leaves the existing
        one untouched. """

        Light = 12000000 # miles per minute

        # Create a collection of knights
        ks = knights()
        ks += knight('Lancelot')
        ks += knight('Authur')
        ks += knight('Galahad')
        ks += knight('Bedevere')

        # Create a sorted version
        ks1 = ks.sorted(key=lambda k: k.name)

        # Test the sort

        # Ensure count hasn't changed
        self.assertEq(ks.count, ks1.count)
        self.assertIs(knights, type(ks1))

        # Ensure original was not sorted.
        self.assertEq('Lancelot',  ks.first.name)
        self.assertEq('Authur',    ks.second.name)
        self.assertEq('Galahad',   ks.third.name)
        self.assertEq('Bedevere',  ks.fourth.name)

        # Ensure sort is alphabetic
        self.assertEq('Authur',    ks1.first.name)
        self.assertEq('Bedevere',  ks1.second.name)
        self.assertEq('Galahad',   ks1.third.name)
        self.assertEq('Lancelot',  ks1.fourth.name)

        # Sort in descending
        ks1 = ks.sorted(key=lambda k: k.name, reverse=True)

        # Ensure sort is reverse alphabetic
        self.assertEq('Lancelot',  ks1.first.name)
        self.assertEq('Galahad',   ks1.second.name)
        self.assertEq('Bedevere',  ks1.third.name)
        self.assertEq('Authur',    ks1.fourth.name)

        # Numeric sort 

        # Create numeric constant collection
        cs = constants()
        cs += constant(Light)
        cs += constant(math.pi)
        cs += constant(math.e)

        cs1 = cs.sorted(key=lambda c: c.value)

        # Ensure original was not sorted
        self.assertEq(Light,    cs.first.value)
        self.assertEq(math.pi,  cs.second.value)
        self.assertEq(math.e,   cs.third.value)

        # Ensure cs1 is sorted numerically
        self.assertEq(math.e,   cs1.first.value)
        self.assertEq(math.pi,  cs1.second.value)
        self.assertEq(Light,    cs1.third.value)

        # Test revers sort
        cs1 = cs.sorted(lambda c: c.value, True)
        self.assertEq(Light,    cs1.first.value)
        self.assertEq(math.pi,  cs1.second.value)
        self.assertEq(math.e,   cs1.third.value)

    def it_calls_head(self):
        """ Head returns an entities collection containing the first 'number' of
        entities in the collection."""

        # Create some knights
        ks = knights()
        ks += knight('Lancelot')
        ks += knight('Authur')
        ks += knight('Galahad')
        ks += knight('Bedevere')

        # Call head() with a number for 0 to 4
        for i in range(ks.count + 1):
            head = ks.head(i)
            self.assertEq(i, head.count)
            self.assertEq(knights, type(head))

            # Ensure the elements of the head are as expected
            for j in range(0, i):
                self.assertEq(ks[j], head[j])

    def it_calls_tail(self):
        """ Tail returns an entities collection containing the last 'number'
        of entities in the collection."""

        # Create some knights
        ks = knights()
        ks += knight('Lancelot')
        ks += knight('Authur')
        ks += knight('Galahad')
        ks += knight('Bedevere')

        # Call tail() with a number for 0 to 4
        for i in range(ks.count + 1):
            t = ks.tail(i)
            self.assertEq(i, t.count)
            self.assertEq(knights, type(t))

            # Ensure the elements of the tail are as expected
            for j in range(1, i + 1):
                self.assertEq(ks[-j], t[-j])

    def it_calls_remove(self):
        """ The entities.remove method removesd entity objects from itself.
        Different types of arguments can be given to indicate what entity
        objects need to be removed."""
        
        # Create some knights
        ks = knights.createthe4()

        ## Remove Galahad by index ##
        ks.remove(2) 
        self.assertCount(3, ks)
        self.assertCount(0, ks.where(lambda k: k.name == 'Galahad'))

        # Recreate the four knights
        ks = knights.createthe4()

        ## Remove the second one by object identity ##
        nd = ks.second
        ks.remove(nd)
        self.assertCount(3, ks)
        self.assertFalse(ks.has(nd)) # Ensure second knight is not in ks

        ## Remove by entities collection ##

        # Get a knights collection containing first 2 knights from ks
        ks = knights.createthe4()
        ks1 = knights(ks[:2])

        # Pass knights collectios in to remove() to remove them from ks
        ks.remove(ks1)

        # Ensure the first 2 where removed
        self.assertCount(2, ks)
        self.assertFalse(ks.has(ks1.first))
        self.assertFalse(ks.has(ks1.second))

        ## Remove using a callable##
        ks = knights.createthe4()

        # Get a reference to Bedevere
        k = ks.last

        # Remove Bedevere
        ks.remove(lambda k: k.name == 'Bedevere')

        self.assertCount(3, ks)
        self.assertFalse(ks.has(k))

        ## Remove a duplicate
        ni = knight('knight who says ni')

        # Add ni twice
        ks += ni
        ks += ni

        # Now the count is 5
        self.assertCount(5, ks)

        # If we remove ni once, we end up removing both instance of ni. This
        # is counter-intuitive, and may not be Right, but it seems the most 
        # logical at the moment.
        ks -= ni
        self.assertCount(3, ks)
        self.assertFalse(ks.has(ni))

    def it_calls__isub__(self):
        """ entities.__isub__() is essentially a wrapper around
        entities.removes. The test here will be similar to it_calls_remove.
        """

        ## Remove Galahad by index ##
        
        # API NOTE This works simply because __isub__ is a wrapper for
        # remove(). However, it seems so semantically insensable that a
        # ValueError probably should be thrown here.

        # Create some knights 
        ks = knights.createthe4()
        ks -= 2
        self.assertCount(3, ks)
        self.assertCount(0, ks.where(lambda k: k.name == 'Galahad'))

        # Create some knights
        ks = knights.createthe4()

        ## Remove Galahad by index ##
        galahad = ks.where(lambda k: k.name == 'Galahad').first

        ks -= galahad

        self.assertCount(3, ks)
        self.assertCount(0, ks.where(lambda k: k.name == 'Galahad'))

        ## Remove by entities collection ##

        # Get a knights collection containing first 2 knights from ks
        ks = knights.createthe4()
        ks1 = knights(ks[:2])

        # Pass knights collectios in to remove() to remove them from ks
        ks -= ks1

        # Ensure the first 2 where removed
        self.assertCount(2, ks)
        self.assertFalse(ks.has(ks1.first))
        self.assertFalse(ks.has(ks1.second))

        ## Remove using a callable ##
        ks = knights.createthe4()

        # Get a reference to Bedevere
        k = ks.last

        # Remove Bedevere

        # API NOTE This should probably raise a ValueError as well
        ks -= lambda k: k.name == 'Bedevere'

        self.assertCount(3, ks)
        self.assertFalse(ks.has(k))

    def it_calls_reversed(self):
        """ The entities.reversed() method allows you to iterate
        in reverse order over the entities collection. It is modeled
        on https://docs.python.org/3/library/functions.html#reversed """

        ks = knights.createthe4()
        for i, k in enumerate(ks.reversed()):
            j = ks.ubound - i
            self.assertIs(ks[j], k)

    def it_calls_reverse(self):
        """ The entities.reverse() method reverses the order of the entity 
        objects within the entities collection. """

        ks = knights.createthe4()
        rst, nd, rd, th = ks[:]

        ks.reverse()

        self.assertCount(4, ks)

        self.assertIs(rst,  ks.last)
        self.assertIs(nd,   ks.third)
        self.assertIs(rd,   ks.second)
        self.assertIs(th,   ks.first)

    def it_gets_ubound(self):
        """ The upper bound is the highest number that can be given to the
        indexer."""
        
        ks = knights.createthe4()

        # Ensure that ubound is the number of elements minus one.
        self.assertEq(3, ks.ubound)

        # If the collection is empty, a ubound can't exist so set it should be
        # None.
        self.assertNone(entities().ubound)

    def it_calls_insert(self):
        """ Normally we append to the end of collections. The insert() method
        allows us to insert entity objects into arbitrary areas of the 
        collection. """

        ks = knights.createthe4()
        ni = knight('knight who says ni')

        ks.insert(2, ni)

        self.assertEq(5, ks.count)
        self.assertIs(ks.third, ni)

    def it_calls_insertbefore(self):
        """ Inserts an entity before an index position. """

        ks = knights.createthe4()
        ni = knight('knight who says ni')

        ks.insertbefore(2, ni)

        self.assertEq(5, ks.count)
        self.assertIs(ks.third, ni)

    def it_calls_insertafter(self):
        """ Inserts an entity after an index position. """

        ks = knights.createthe4()
        ni = knight('knight who says ni')

        ks.insertafter(2, ni)

        self.assertEq(5, ks.count)
        self.assertIs(ks.fourth, ni)

    def it_calls_shift(self):
        """ Calling shift removes the first entity object from the collection
        and returns it to the caller."""

        ks = knights.createthe4()
        rst = ks.shift()

        self.assertEq(3, ks.count)
        self.assertFalse(ks.has(rst))

        # Ensure empty collection shift None
        self.assertNone(entities().shift())

    def it_calls_unshift(self):
        """ Calling unshift() inserts an elment into the collection making it
        the first element."""

        ks = knights.createthe4()
        ni = knight('knight who says ni')

        ks.unshift(ni)

        self.assertEq(5, ks.count)
        self.assertIs(ks.first, ni)

    def it_calls_pop(self):
        """ Calling pop() removes and returns the last element in the 
        collection."""

        ks = knights.createthe4()
        last = ks.pop()

        self.assertEq(3, ks.count)
        self.assertFalse(ks.has(last))

        # Ensure empty collection pops None
        self.assertNone(entities().pop())

    def it_calls_push(self):
        """ Calling push() causes the argument to be added to the end of
        the collection. """
        ks = knights.createthe4()
        ni = knight('knight who says ni')

        ks.push(ni)

        self.assertEq(5, ks.count)
        self.assertIs(ni, ks.last)

    def it_calls_has(self):
        """ The has() method determines if the argument is in the collection
        using object identity (is) as opposed to object equality (==). """

        ks = knights.createthe4()
        for k in ks:
            self.assertTrue(ks.has(k))

        ni = knight('knight who says ni')
        self.assertFalse(ks.has(ni))
        self.assertTrue(ks.hasnt(ni))

    def it_calls__lshift__(self):
        """ The lshift operator (<<) is a wrapper around unshift. """

        ks = knights.createthe4()
        ni = knight('knight who says ni')
        ks << ni

        self.assertEq(5, ks.count)
        self.assertIs(ks.first, ni)

    def it_calls_append(self):
        """ The append() method adds entity objects to the end of the
        collection. It can also append collections. If the uniq flag is True,
        only objects not already in the collection will be appended. This
        method returns a generic entities collection of all the objects that
        were added."""

        ## Test appending one entity ##
        ks = knights.createthe4()
        ni = knight('knight who says ni')
        ks1 = ks.append(ni)

        self.assertEq(5, ks.count)
        self.assertEq(1, ks1.count)
        self.assertIs(ks.last, ni)
        self.assertIs(ks1.first, ni)
        self.assertEq(entities, type(ks1))

        ## Test appending one unique entity with the uniq flag set. We
        ## should get a successful appending like above since the entity
        ## is unique.

        ks = knights.createthe4()
        ni = knight('knight who says ni')
        ks1 = ks.append(ni, uniq=True)

        self.assertEq(5, ks.count)
        self.assertEq(1, ks1.count)
        self.assertIs(ks.last, ni)
        self.assertIs(ks1.first, ni)
        self.assertEq(entities, type(ks1))

        ## Test appending one non-unique entity with the uniq flag set. We
        ## should get a successful appending like above since the entity
        ## is unique.

        ks = knights.createthe4()
        ks1 = ks.append(ks.first, uniq=True)

        self.assertEq(4, ks.count)
        self.assertTrue(ks1.isempty)
        self.assertEq(entities, type(ks1))

        ## Test appending an entities collection to an entities collection.
        ks = knights.createthe4()
        nis = knights()
        nis += knight('knight who says ni 1')
        nis += knight('knight who says ni 2')

        ks1 = ks.append(nis)

        self.assertEq(6,           ks.count)
        self.assertEq(2,           ks1.count)
        self.assertIs(nis.first,   ks.penultimate)
        self.assertIs(nis.second,  ks.last)
        self.assertIs(nis.first,   ks1.first)
        self.assertIs(nis.second,  ks1.second)
        self.assertEq(entities,    type(ks1))

        # Test appending an entities collection to an entities collection
        # where one of the entities being appended is not unique, though 
        # the uniq flag is is not changed from its default value of False.

        ks = knights.createthe4()
        nis = knights()
        nis += knight('knight who says ni 1')
        nis += ks.first # The non-unique entity

        ks1 = ks.append(nis)

        self.assertEq(6,           ks.count)
        self.assertEq(2,           ks1.count)
        self.assertIs(nis.first,   ks.penultimate)
        self.assertIs(nis.second,  ks.last)
        self.assertIs(nis.first,   ks1.first)
        self.assertIs(nis.second,  ks1.second)
        self.assertEq(entities,    type(ks1))

        # Test appending an entities collection to an entities collection
        # where one of the entities being appended is not unique.

        ks = knights.createthe4()
        nis = knights()
        nis += knight('knight who says ni 1')
        nis += ks.first # The non-unique entity

        ks1 = ks.append(nis, uniq=True)

        self.assertEq(5,           ks.count)
        self.assertEq(1,           ks1.count)
        self.assertIs(nis.first,   ks.last)
        self.assertIs(nis.first,   ks1.first)
        self.assertEq(entities,    type(ks1))
        self.assertFalse(ks1.has(nis.second))

        # Test appending an entities collection to an entities collection
        # where both of the entities being appended are not unique.

        ks = knights.createthe4()
        nis = knights()
        nis += ks.first
        nis += ks.second # The non-unique entity

        ks1 = ks.append(nis, uniq=True)

        self.assertEq(4,           ks.count)
        self.assertEq(0,           ks1.count)
        self.assertEq(entities,    type(ks1))
        self.assertFalse(ks1.has(nis.first))
        self.assertFalse(ks1.has(nis.second))

        ## Ensure we get a ValueError if we append something that isn't
        ## an entity or entities type

        ks = knights.createthe4()
        try:
            ks.append(1)
            self.assertFail('Append accepted invalid type')
        except Exception as ex:
            self.assertEq(ValueError, type(ex))

    def it_subclasses_append(self):

        # Append one knight
        sks = sillyknights()
        fk = knight('french knight')
        sks += fk

        self.assertTrue(sks.hasone)
        self.assertIs(sks.first, fk)

        # Append a collection of knightns
        # Note: The overridden append() must accept the 'r' parameter and 
        # default it to None for this to work.
        bk = knight('black knight')
        ks = bk + fk

        sks += ks

        self.assertEq(3, sks.count)
        for i, k in enumerate([fk, bk, fk]):
            self.assertIs(sks[i], k)

        # Append a unique knight insisting it be unique
        ni = knight('knight who says ni')
        sks |= ni
        self.assertEq(4, sks.count)
        for i, k in enumerate([fk, bk, fk, ni]):
            self.assertIs(sks[i], k)

        # Append a non-unique knight insisting in be unique
        sks |= ni
        self.assertEq(4, sks.count)
        for i, k in enumerate([fk, bk, fk, ni]):
            self.assertIs(sks[i], k)

        # Append a non-unique knight insisting in be unique using the append
        # method rather than the |= operator in order to obtain the results
        res = sks.append(ni, uniq=True)
        self.assertTrue(res.isempty)
        self.assertEq(4, sks.count)
        for i, k in enumerate([fk, bk, fk, ni]):
            self.assertIs(sks[i], k)

        # Append a non-unique collection of knights insisting they be unique
        # using the append method rather than the |= operator in order to
        # obtain the results
        ks = ni + knight('knight who says ni2')
        res = sks.append(ks, uniq=True)
        self.assertTrue(res.hasone)
        self.assertEq(5, sks.count)
        for i, k in enumerate([fk, bk, fk, ni, ks.second]):
            self.assertIs(sks[i], k)

        # Create a new collection based on the old one by instantiating with
        # the old collection as an argument. 
        sks1 = knights(sks)
        self.assertEq(sks1.count, sks.count)
        for i, k in enumerate(sks1):
            self.assertIs(k, sks1[i])

        # Create a new collection based on the old one by instantiating with
        # a list of entity objects from the old collection.
        sks1 = knights(list(sks))
        self.assertEq(sks1.count, sks.count)
        for i, k in enumerate(sks1):
            self.assertIs(k, sks1[i])
            
    def it_calls__iadd__(self):
        """ The += operator (__iadd__) wraps the append method. It can 
        everything append() can do except reject non-unique enity objects.
        Also, there is no way to determine what has been added. """

        ## Test appending one entity ##
        ks = knights.createthe4()
        ni = knight('knight who says ni')
        ks += ni

        self.assertEq(5, ks.count)
        self.assertIs(ks.last, ni)

        ## Test appending an entities collection to an entities collection.
        ks = knights.createthe4()

        nis = knight('knight 1') + knight('knight 2')
        ks += nis

        self.assertEq(6,           ks.count)
        self.assertIs(nis.first,   ks.penultimate)
        self.assertIs(nis.second,  ks.last)

        ## Ensure we get a ValueError if we append something that isn't
        ## an entity, entities type.
        ks = knights.createthe4()
        try:
            ks += 1
            self.assertFail('Append accepted invalid type')
        except Exception as ex:
            self.assertEq(ValueError, type(ex))

    def it_calls__iand__(self):
        """ The |= opreator (__iand__) wraps the append() methed setting
        the unique flag to True. So |= is like a regular append accept 
        objecs won't be appended if already exist in the collection."""

        ## Test appending one unique entity ##
        ks = knights.createthe4()
        ni = knight('knight who says ni')
        ks |= ni

        self.assertEq(5, ks.count)
        self.assertIs(ks.last, ni)

        # Test appending one non-unique entity. Nothing should sucessfully
        # be appended.

        ks = knights.createthe4()
        ks |= ks.first

        self.assertEq(4, ks.count)

        # Test appending an entities collection to an entities collection
        # where one of the entities being appended is not unique.

        ks = knights.createthe4()
        nis = knights()
        nis += knight('knight who says ni 1')
        nis += ks.first # The non-unique entity

        ks |= nis

        self.assertEq(5, ks.count)
        self.assertIs(nis.first,   ks.last)

        # Test appending an entities collection to an entities collection
        # where both of the entities being appended are not unique.
        # Nothing will be sucessfully appended
        ks = knights.createthe4()
        nis = knights()
        nis += ks.first
        nis += ks.second # The non-unique entity

        ks |= nis

        self.assertEq(4, ks.count)

        ## Ensure we get a ValueError if we append something that isn't
        ## an entity or entities type
        ks = knights.createthe4()
        try:
            ks |= 1
            self.assertFail('Append accepted invalid type')
        except Exception as ex:
            self.assertEq(ValueError, type(ex))

    def it_calls__add__(self):
        """ The + operator adds an entity object, or a collection of 
        entity objects, to the existing entities collection producing
        a new entities collection of the same type. """

        # Add a single entity to the collection
        ks = knights.createthe4()
        ni = knight('knight who says ni 1')
        ks1 = ks + ni

        self.assertEq(4, ks.count)
        self.assertEq(5, ks1.count)
        self.assertEq(knights, type(ks1))
        self.assertIs(ks1.last, ni)

        # Add an entities collection to ks

        ks = knights.createthe4()
        nis = knights()
        nis += knight('knight who says ni 1')
        nis += knight('knight who says ni 2')

        ks1 = ks + nis

        self.assertEq(4,                ks.count)
        self.assertEq(6,                ks1.count)
        self.assertEq(knights,          type(ks1))
        self.assertIs(ks1.penultimate,  nis.first)
        self.assertIs(ks1.last,         nis.last)

    def it_calls__sub__(self):
        """ The - operator removes an entity object, or a collection of 
        entity objects, from the existing entities collection producing
        a new entities collection of the same type. """

        # Remove a single entity from the collection
        ks = knights.createthe4()
        rst = ks.first
        ks1 = ks - rst

        self.assertEq(4, ks.count)
        self.assertEq(3, ks1.count)
        self.assertEq(knights, type(ks1))
        self.assertFalse(ks1.has(rst))
        self.assertTrue(ks.has(rst))

        # Remove an entities collection from ks

        ks = knights.createthe4()
        es = knights(ks[:2])

        ks1 = ks - es

        self.assertEq(4,           ks.count)
        self.assertEq(2,           ks1.count)
        self.assertEq(knights,     type(ks1))
        self.assertIs(ks1.first,   ks.third)
        self.assertIs(ks1.second,  ks.fourth)

    def it_gets__ls(self):
        """ The _list property is a 'private' property representing
        the underlying Python list object used to store the entities."""
        ks = knights.createthe4()

        for i, k in enumerate(ks):
            self.assertIs(ks._ls[i], k)

    def it_gets_count(self):
        """ The count property is the number of entities in the collection.
        The __len__, isempty, hasone, and ispopulated methods are based on the
        count property so they will tested here.  """
        ks = knights.createthe4()

        self.assertEq(4, ks.count)
        self.assertEq(4, len(ks))
        self.assertFalse(ks.isempty)
        self.assertFalse(ks.hasone)
        self.assertTrue(ks.ispopulated)

        # Create a collection of one
        ks = knights(ks.first) 
        self.assertEq(1, ks.count)
        self.assertEq(1, len(ks))
        self.assertFalse(ks.isempty)
        self.assertTrue(ks.hasone)
        self.assertTrue(ks.ispopulated)

        # Clear the collection so it will have no entities
        ks.clear()

        self.assertEq(0, ks.count)
        self.assertEq(0, len(ks))
        self.assertTrue(ks.isempty)
        self.assertFalse(ks.hasone)
        self.assertFalse(ks.ispopulated)

    def it_calls__str__(self):
        """ The __str__ method will return a concatenation of the results
        of each entities __str__ invocation followed by a line ending."""

        ks = knights.createthe4()
        hdr = '{} object at {} count: {}\n' \
            .format(str(type(ks)), str(hex(id(ks))), ks.count)
        s = hdr + """    Lancelot
    Authur
    Galahad
    Bedevere
"""
        self.assertEq(s, str(ks))

        ks.clear()

        hdr = '{} object at {} count: {}\n' \
            .format(str(type(ks)), str(hex(id(ks))), ks.count)

        self.assertEq(hdr, str(ks))

    def it_calls__repr__(self):
        """ The __repr__ method will return a concatenation of the results
        of each entities __repr__ invocation followed by a line ending."""

        ks = knights.createthe4()

        for i, l in enumerate(repr(ks).splitlines()):
            if i == 0:
                continue
            l = l.strip()
            self.assertEq(l, repr(ks[i-1]))

        ks.clear()

        r = '{} object at {} count: {}\n' \
            .format(str(type(ks)), str(hex(id(ks))), ks.count)

        self.assertEq(r, repr(ks))

    def it_calls__setitem__(self):
        """ The __setitem__ method is used to set an item in the 
        collection by an index."""

        ks = knights.createthe4()
        ni = knight('knight who says ni 1')

        # Set the second element to ni
        ks[1] = ni

        self.assertEq(4, ks.count)
        self.assertIs(ni, ks.second)

        ks = knights.createthe4()

        nis = knights()
        nis += knight('knight who says ni 1')
        nis += knight('knight who says ni 1')

        # Set the third and forth elements to nis[0] and nis[1] 
        ks[2:4] = nis
        
        self.assertEq(4, ks.count)
        self.assertIs(nis.first, ks.third)
        self.assertIs(nis.second, ks.fourth)

        # Assighn nis[0] and nis[1] to ks[0] and ks[2]
        ks = knights.createthe4()
        ks[::2] = nis
        self.assertEq(4, ks.count)
        self.assertIs(nis.first, ks.first)
        self.assertIs(nis.second, ks.third)

        # Ensure that setting an entity to an index that doesn't exist causes
        # an error.
        try:
            ks[5] = ni
            self.assertFail("This should raise an IndexError.")
        except IndexError:
            pass
        except Exception:
            self.assertFail("This should not raise a generic Exception.")

    def it_calls__getitems__(self):
        """ The __getitem__ method is used to get an item in the 
        collection by an index."""
        ks = knights()
        ni = knight('knight who says ni 1')
        ks += ni

        # Test getting a single element
        self.assertIs(ks[0], ni)

        ni1 = knight('knight who says ni 2')
        ks += ni1

        # Test getting two elements
        self.assertIs(ks[0], ni)
        self.assertIs(ks[1], ni1)

        # Test getting by a slice
        ni, ni1 = ks[:2]
        self.assertIs(ks[0], ni)
        self.assertIs(ks[1], ni1)

        # Test getting using a stride
        ks = knights().createthe4()
        k, k3 = ks[::2]
        self.assertIs(k, ks.first)
        self.assertIs(k3, ks.third)
    
    def it_calls_getindex(self):
        """ The getindex method returns the 0-based index/position of
        the given element within the collection. """

        ks = knights().createthe4()
        for i, k in enumerate(ks):
            self.assertEq(i, ks.getindex(k))

        try:
            ks.getindex(knight(''))
            self.assertFail('getindex should have raised a ValueError.')
        except ValueError:
            pass
        except Exception as ex:
            self.assertFail('getindex should have raised a ValueError.')

    def it_gets_the_ordinals(self):
        """ The "ordinals" are propreties like "first", "second", and
        "last"."""

        ks = knights().createthe4()
        self.assertIs(ks[0], ks.first)
        self.assertIs(ks[1], ks.second)
        self.assertIs(ks[2], ks.third)
        self.assertIs(ks[3], ks.fourth)
        self.assertIs(ks[3], ks.last)
        self.assertIs(ks[3], ks.ultimate)
        self.assertIs(ks[2], ks.penultimate)
        self.assertIs(ks[1], ks.antepenultimate)
        self.assertIs(ks[0], ks.preantepenultimate)

        # Ordinals should return None if the the value doesn't exist
        self.assertNone(ks.fifth)
        self.assertNone(ks.sixth)

        # All ordinals should return None if the collection is empty
        ks.clear()
        self.assertNone(ks.first)
        self.assertNone(ks.second)
        self.assertNone(ks.third)
        self.assertNone(ks.fourth)
        self.assertNone(ks.last)
        self.assertNone(ks.ultimate)
        self.assertNone(ks.penultimate)
        self.assertNone(ks.antepenultimate)
        self.assertNone(ks.preantepenultimate)

        # Ensure ordinals return sensible results with a collection of 1
        ni = knight('knight who says ni 1')
        ks += ni
        self.assertIs(ni, ks.first)
        self.assertIs(ni, ks.last)
        self.assertIs(ni, ks.ultimate)
        self.assertNone(ks.second)
        self.assertNone(ks.third)
        self.assertNone(ks.fourth)
        self.assertNone(ks.penultimate)
        self.assertNone(ks.antepenultimate)
        self.assertNone(ks.preantepenultimate)

        # Ensure ordinals return sensible results with a collection of 2
        ni1 = knight('knight who says ni 2')
        ks += ni1
        self.assertIs(ni, ks.first)
        self.assertIs(ni1, ks.second)
        self.assertIs(ni1, ks.last)
        self.assertIs(ni1, ks.ultimate)
        self.assertIs(ni, ks.penultimate)
        self.assertNone(ks.third)
        self.assertNone(ks.fourth)
        self.assertNone(ks.antepenultimate)
        self.assertNone(ks.preantepenultimate)

        # Ensure ordinals return sensible results with a collection of 3
        ni2= knight('knight who says ni 2')
        ks += ni2
        self.assertIs(ni, ks.first)
        self.assertIs(ni1, ks.second)
        self.assertIs(ni2, ks.third)
        self.assertIs(ni2, ks.last)
        self.assertIs(ni2, ks.ultimate)
        self.assertIs(ni1, ks.penultimate)
        self.assertIs(ni, ks.antepenultimate)
        self.assertNone(ks.fourth)

        # Test that fifth and sixth return
        ks = knights.createthe4()
        ni5= knight('knight who says ni 5')
        ni6= knight('knight who says ni 6')
        ks += ni5 + ni6
        self.assertIs(ni5, ks.fifth)
        self.assertIs(ni6, ks.sixth)

    def it_gets_brokenrules(self):
        """ A broken rule is an entity that represents a problem with the
        state of an entitiy. Each entities collection by default returns a
        broken rules collection which is an aggregates of the broken rules
        collections of the entities it contains."""

        # Ensure that the default knights collection is valid, i.e., its 
        # brokenrules collectios is empty
        ks = knights.createthe4()
        self.assertTrue(ks.isvalid)
        self.assertValid(ks)
        self.assertTrue(ks.brokenrules.isempty)

        # Break one of the knights broken rules
        ks.first.name = 123
        self.assertFalse(ks.isvalid)
        self.assertInValid(ks)
        self.assertTrue(ks.brokenrules.hasone)
        self.assertEq(ks.brokenrules.first.message, 'Names must be strings')
        self.assertEq(str(ks.brokenrules.first), 'Names must be strings')

        # Break all of the knights broken rules and test each entity's 
        # broken rules collection individually
        for k in ks:
            k.name = 123
            self.assertFalse(k.isvalid)
            self.assertInValid(k)
            self.assertTrue(k.brokenrules.hasone)
            self.assertEq(k.brokenrules.first.message, 'Names must be strings')
            self.assertEq(str(k.brokenrules.first), 'Names must be strings')

        # Now test the knigts collection's broken rules.
        self.assertFalse(ks.isvalid)
        self.assertInValid(ks)
        self.assertCount(4, ks.brokenrules)

        for br in ks.brokenrules:
            self.assertEq(br.message, 'Names must be strings')
            self.assertEq(str(br), 'Names must be strings')

    def it_raises_onadd(self):
        """ The onappended event is called whenever an entity is added to the
        the collection. """
        ks = knights()
        the4 = knights.createthe4()

        # snare will be a collection to capture the knights caught in the 
        # event handler
        snare = knights()

        # The onadd event handler
        def local_onadd(src, eargs):
            nonlocal snare
            snare += eargs.entity

        # Subscribe to event handler
        ks.onadd += local_onadd

        # Append a single entity to ks
        ks += the4.first

        self.assertIs(the4.first, snare.first)
        self.assertTrue(snare.hasone)

        # Append an entities collection to ks
        ks += entities([the4.second, the4.third])
        self.assertIs(the4.first, snare.first)
        self.assertIs(the4.second, snare.second)
        self.assertIs(the4.third, snare.third)
        self.assertEq(3, snare.count)

        # Append a duplicate entity
        ks += the4.first
        self.assertIs(the4.first, snare.first)
        self.assertIs(the4.second, snare.second)
        self.assertIs(the4.third, snare.third)
        self.assertEq(4, snare.count)

        # Appned a duplicate entity again but with the |= operator to ensure
        # it won't be appended
        ks |= the4.first
        self.assertIs(the4.first, snare.first)
        self.assertIs(the4.second, snare.second)
        self.assertIs(the4.third, snare.third)
        self.assertEq(4, snare.count)

        # Appned a collection of duplicate entity again but with the |=
        # operator to ensure they won't be appended
        ks |= entities([the4.second, the4.third])
        self.assertIs(the4.first, snare.first)
        self.assertIs(the4.second, snare.second)
        self.assertIs(the4.third, snare.third)
        self.assertEq(4, snare.count)

        # Clear the collections to start insert tests
        snare.clear()
        ks.clear()

        # Unshift the first knight into ks
        ks << the4.first
        self.assertIs(the4.first, snare.first)
        self.assertTrue(snare.hasone)
        self.assertCount(1, snare)

        # insert
        ks.insert(0, the4.second)
        self.assertIs(the4.first, snare.first)
        self.assertIs(the4.second, snare.second)
        self.assertCount(2, snare)

        # insertbefore
        ks.insertbefore(0, the4.third)
        self.assertIs(the4.first, snare.first)
        self.assertIs(the4.second, snare.second)
        self.assertIs(the4.third, snare.third)
        self.assertCount(3, snare)

        # insertafter
        ks.insertafter(0, the4.fourth)
        self.assertIs(the4.first, snare.first)
        self.assertIs(the4.second, snare.second)
        self.assertIs(the4.third, snare.third)
        self.assertIs(the4.fourth, snare.fourth)
        self.assertCount(4, snare)

        # Clear the collections to continue different tests
        snare.clear()
        ks.clear()

        # push
        ks.push(the4.first)
        self.assertIs(the4.first, snare.first)
        self.assertTrue(snare.hasone)
        self.assertCount(1, snare)

        # Instantiate with collection
        ks = entities([the4.first, the4.second])
        # TODO We need to test that instatiating with a list of entities
        # invokes the onadd event. Obviously, we can't subscribe to the
        # event until the object is instantiated. There needs to be a
        # workaround that doesn't involve altering the entities classes.

    def it_raises_onremove(self):
        """ The onremove event is called whenever an entity is removed from
        the the collection. """
        snare = knights()

        # The onremove event handler
        def local_onaremove(src, eargs):
            nonlocal snare
            snare += eargs.entity

        # Create the four
        ks = knights.createthe4()

        # Make local_onaremove the event handler
        ks.onremove += local_onaremove

        # Remove the first element
        rst = ks.first
        ks -= rst
        self.assertTrue(snare.hasone)
        self.assertIs(rst, snare.first)

        # Remove two elements as an entities collection
        ks1 = entities([ks.first, ks.second])
        ks -= ks1
        self.assertCount(3, snare)
        self.assertIs(rst, snare.first)
        self.assertIs(ks1.second, snare.second)
        self.assertIs(ks1.first, snare.third)

        # Remove by index
        last = ks.last
        ks.remove(0)
        self.assertCount(4, snare)
        self.assertIs(rst, snare.first)
        self.assertIs(ks1.second, snare.second)
        self.assertIs(ks1.first, snare.third)
        self.assertIs(last, snare.fourth)

        # Get the knights again and clear the snare for more tests
        ks = knights.createthe4()
        ks.onremove += local_onaremove
        snare.clear()

        # shift
        rst = ks.shift()
        self.assertCount(1, snare)
        self.assertIs(rst, snare.first)

        # pop
        nd = ks.pop()
        self.assertCount(2, snare)
        self.assertIs(rst, snare.first)
        self.assertIs(nd, snare.second)

        # pop with index
        rd = ks.pop(1)
        self.assertCount(3, snare)
        self.assertIs(rst, snare.first)
        self.assertIs(nd, snare.second)
        self.assertIs(rd, snare.third)

        # clear
        snare.clear()
        ks = knights.createthe4()
        rst, nd, rd, rth = ks[:4]
        ks.onremove += local_onaremove
        ks.clear()

        # Removed knights will be snared in reverse order since the clear
        # algorithm removes the knights in reverse order
        self.assertCount(4, snare)
        self.assertIs(rst, snare.fourth)
        self.assertIs(nd, snare.third)
        self.assertIs(rd, snare.second)
        self.assertIs(rth, snare.first)

    def it_raises_onremove_and_onadd_when_calling__setitem__(self):
        
        """ Setting an entity to a position in a collection will cause the
        onremove event to be raised, indicating the removal of the original
        entity, and the onadd event to be raised, indicating the addition of
        the new entity. """

        addsnare = knights()
        rmsnare = knights()
        # The onadd event handler
        def local_onadd(src, eargs):
            nonlocal addsnare
            addsnare += eargs.entity

        # The onremove event handler
        def local_onaremove(src, eargs):
            nonlocal rmsnare
            rmsnare += eargs.entity

        # Get the4 and subscribe to the event handlers
        the4 = knights.createthe4()

        the4.onadd    += local_onadd
        the4.onremove += local_onaremove
        
        # Make the first entity ni and ensure the event handlers caught the 
        # added and removed knights
        ni = knight('knight who says ni')
        ni1 = knight('knight who says ni1')
        rst = the4.first

        the4[0] = ni
        self.assertCount(1, addsnare)
        self.assertEq(rmsnare.count, addsnare.count)
        self.assertIs(rst, rmsnare.first)
        self.assertIs(ni, addsnare.first)

        # first ordinal 
        the4.first = ni1
        self.assertCount(2, addsnare)
        self.assertEq(rmsnare.count, addsnare.count)
        self.assertIs(rst, rmsnare.first)
        self.assertIs(ni, rmsnare.second)
        self.assertIs(ni, addsnare.first)
        self.assertIs(ni1, addsnare.second)

        # second ordinal
        nd = the4.second
        the4.second = ni
        self.assertCount(3, addsnare)
        self.assertEq(rmsnare.count, addsnare.count)
        self.assertIs(rst, rmsnare.first)
        self.assertIs(ni, rmsnare.second)
        self.assertIs(nd, rmsnare.third)

        self.assertIs(ni, addsnare.first)
        self.assertIs(ni1, addsnare.second)
        self.assertIs(ni, addsnare.third)

        # third ordinal
        rd = the4.third
        the4.third = ni
        self.assertCount(4, addsnare)
        self.assertEq(rmsnare.count, addsnare.count)
        self.assertIs(rst, rmsnare.first)
        self.assertIs(ni, rmsnare.second)
        self.assertIs(nd, rmsnare.third)
        self.assertIs(rd, rmsnare.fourth)

        self.assertIs(ni, addsnare.first)
        self.assertIs(ni1, addsnare.second)
        self.assertIs(ni, addsnare.third)
        self.assertIs(ni, addsnare.fourth)

        # fourth ordinal
        rth = the4.fourth
        the4.fourth = ni
        self.assertCount(5, addsnare)
        self.assertEq(rmsnare.count, addsnare.count)
        self.assertIs(rst, rmsnare.first)
        self.assertIs(ni, rmsnare.second)
        self.assertIs(nd, rmsnare.third)
        self.assertIs(rd, rmsnare.fourth)
        self.assertIs(rth, rmsnare.fifth)

        self.assertIs(ni, addsnare.first)
        self.assertIs(ni1, addsnare.second)
        self.assertIs(ni, addsnare.third)
        self.assertIs(ni, addsnare.fourth)

        # Add two more to the4 
        fifth, sixth = knights.createthe4()[:2]
        the4 += fifth + sixth

        self.assertCount(7, addsnare)
        self.assertEq(rmsnare.count + 2, addsnare.count)
        self.assertIs(rst, rmsnare.first)
        self.assertIs(ni, rmsnare.second)
        self.assertIs(nd, rmsnare.third)
        self.assertIs(rd, rmsnare.fourth)
        self.assertIs(rth, rmsnare.fifth)

        self.assertIs(ni, addsnare.first)
        self.assertIs(ni1, addsnare.second)
        self.assertIs(ni, addsnare.third)
        self.assertIs(ni, addsnare.fourth)
        self.assertIs(fifth, addsnare.sixth)
        self.assertIs(sixth, addsnare[6])

        # fifth ordinal
        fifth = the4.fifth
        the4.fifth = ni

        self.assertCount(8, addsnare)
        self.assertEq(rmsnare.count + 2, addsnare.count)
        self.assertIs(rst, rmsnare.first)
        self.assertIs(ni, rmsnare.second)
        self.assertIs(nd, rmsnare.third)
        self.assertIs(rd, rmsnare.fourth)
        self.assertIs(rth, rmsnare.fifth)
        self.assertIs(fifth, rmsnare.sixth)

        self.assertIs(ni, addsnare.first)
        self.assertIs(ni1, addsnare.second)
        self.assertIs(ni, addsnare.third)
        self.assertIs(ni, addsnare.fourth)
        self.assertIs(fifth, addsnare.sixth)
        self.assertIs(sixth, addsnare[6])
        self.assertIs(ni, addsnare[7])

        # sixth ordinal
        sixth = the4.sixth
        the4.sixth = ni

        self.assertCount(9, addsnare)
        self.assertEq(rmsnare.count + 2, addsnare.count)
        self.assertIs(rst, rmsnare.first)
        self.assertIs(ni, rmsnare.second)
        self.assertIs(nd, rmsnare.third)
        self.assertIs(rd, rmsnare.fourth)
        self.assertIs(rth, rmsnare.fifth)
        self.assertIs(fifth, rmsnare.sixth)
        self.assertIs(sixth, rmsnare[6])

        self.assertIs(ni, addsnare.first)
        self.assertIs(ni1, addsnare.second)
        self.assertIs(ni, addsnare.third)
        self.assertIs(ni, addsnare.fourth)
        self.assertIs(fifth, addsnare.sixth)
        self.assertIs(sixth, addsnare[6])
        self.assertIs(ni, addsnare[7])
        self.assertIs(ni, addsnare[8])

        # last
        the4.clear()
        rmsnare.clear()
        the4 += knights.createthe4()
        addsnare.clear()

        last = the4.last
        the4.last = the4.first
        self.assertCount(1, addsnare)
        self.assertEq(rmsnare.count, addsnare.count)
        self.assertIs(last, rmsnare.first)
        self.assertIs(the4.last, addsnare.first)

        # last
        the4.clear()
        rmsnare.clear()
        the4 += knights.createthe4()
        addsnare.clear()

        # ultimate
        ultimate = the4.ultimate
        the4.ultimate = the4.first
        self.assertCount(1, addsnare)
        self.assertEq(rmsnare.count, addsnare.count)
        self.assertIs(ultimate, rmsnare.first)
        self.assertIs(the4.ultimate, addsnare.first)

        # penultimate
        the4.clear()
        rmsnare.clear()
        the4 += knights.createthe4()
        addsnare.clear()

        penultimate = the4.penultimate
        the4.penultimate = the4.first
        self.assertCount(1, addsnare)
        self.assertEq(rmsnare.count, addsnare.count)
        self.assertIs(penultimate, rmsnare.first)
        self.assertIs(the4.penultimate, addsnare.first)

        # antepenultimate
        the4.clear()
        rmsnare.clear()
        the4 += knights.createthe4()
        addsnare.clear()

        antepenultimate = the4.antepenultimate
        the4.antepenultimate = the4.first
        self.assertCount(1, addsnare)
        self.assertEq(rmsnare.count, addsnare.count)
        self.assertIs(antepenultimate, rmsnare.first)
        self.assertIs(the4.antepenultimate, addsnare.first)

        # preantepenultimate
        the4.clear()
        rmsnare.clear()
        the4 += knights.createthe4()
        addsnare.clear()

        preantepenultimate = the4.preantepenultimate
        the4.preantepenultimate = the4.first
        self.assertCount(1, addsnare)
        self.assertEq(rmsnare.count, addsnare.count)
        self.assertIs(preantepenultimate, rmsnare.first)
        self.assertIs(the4.preantepenultimate, addsnare.first)

    def it_uses_identityindex(self):
        ks = knights.createthe4()
        ix = ks.indexes['identity']

        # Test default id indexing for the four
        self.assertEq(4, len(ix))
        for i, k in enumerate(ks):
            self.assertIs(knights, type(ix[ks[i]]))
            self.assertIs(k, ix[ks[i]].first)
            self.assertEq(1, ix[ks[i]].count)

        # Append a knight and retest
        ni = knight('knight who says ni')
        ks += ni
        self.assertEq(5, len(ix))
        for i, k in enumerate(ks):
            self.assertIs(knights, type(ix[ks[i]]))
            self.assertIs(k, ix[ks[i]].first)
            self.assertEq(1, ix[ks[i]].count)

        # Append a non-unique entity
        ks += ni
        self.assertEq(5, len(ix))
        for i, k in enumerate(ks):
            self.assertIs(k, ix[ks[i]].first)
            if k == ni:
                # Ensure that ni's index entry returns 2 entities
                self.assertEq(2, ix[ks[i]].count)
            else:
                self.assertEq(1, ix[ks[i]].count)

        # Remove a non-unique entity

        # NOTE It may seem like we are removing one entity here. But since ni
        # was added twice, removing ni will remove both entries in the
        # collection, and consequently, the index entry for ni will be remove
        # as well. Note that this behavior may be considerd Wrong and,
        # consequently changed.
        ks -= ni
        self.assertEq(4, len(ix))
        for i, k in enumerate(ks):
            self.assertIs(k, ix[ks[i]].first)
            self.assertEq(1, ix[ks[i]].count)

    def it_creates_and_uses_index(self):

        the4 = knights.createthe4()
        sks = sillyknights()

        sks += the4.first

        ks = sks.indexes['name']['Lancelot']

        self.assertTrue(ks.hasone)
        self.assertIs(ks.first, sks.first)
        self.assertEq(sillyknights, type(ks))

        for i in range(5):
            for j in range(5):
                sks += sillyknight([i, j])
                sks += sillyknight((i, j))

        for i in range(5):
            for j in range(5):
                ks = sks.indexes['name']([i, j])
                self.assertEq(2, ks.count)
                for k in ks:
                    if type(k.name) == tuple:
                        self.assertEq(k.name, (i, j))
                    elif type(k.name) == list:
                        self.assertEq(k.name, [i, j])

    def it_calls_pluck(self):
        ks = knights()
        ks += knight(' Sir Lancelot ')
        ks.last.trait = 'UPPER UPPER'

        ks += knight(' sir authur ')
        ks.last.trait = 'lower UPPER'

        ks += knight(' Sir galahad ')
        ks.last.trait = 'lower lower'

        ks += knight(' sir Bedevere ')
        ks.last.trait = 'Cap Cap'

        self.eq([k.name for k in ks], ks.pluck('name'))

        ls = list()
        for k in ks:
            ls.append( [k.name, k.trait] )

        # Test multi *args
        self.eq(
            [[x.name, x.trait] for x in ks], 
            ks.pluck('name', 'trait')
        )
            
        # Test standandard replacement field
        self.eq(
            [x.name for x in ks], 
            ks.pluck('{name}')
        )

        # Test multiple replacement fields
        self.eq(
            [x.name + '-'  + x.trait for x in ks], 
            ks.pluck('{name}-{trait}')
        )

        # Test custom conversion flags 
        # Uppercase and lowercase
        self.eq(
            [x.name.upper() + '-'  + x.trait.lower() for x in ks], 
            ks.pluck('{name!u}-{trait!l}')
        )

        # Test custom conversion flags 
        # Capitalize and title case
        self.eq(
            [x.name.capitalize() + '-'  + x.trait.title() for x in ks], 
            ks.pluck('{name!c}-{trait!t}')
        )

        # Test custom conversion flags 
        # Strip and reverse
        self.eq(
            [x.name.strip() + '-'  + x.trait[::-1] for x in ks], 
            ks.pluck('{name!s}-{trait!r}')
        )

        # Test custom conversion flag: first n-characters of
        for i in range(10):
            self.eq(
                [x.name[:i] + '-'  + x.trait for x in ks], 
                ks.pluck('{name!' + str(i) + '}-{trait}')
            )

class test_entity(tester):
    def it_calls__add__(self):
        """ The + operator concatenates an entity with another
        entity or enities collection and returns an enities
        collection containing the concatenation."""

        # Concatenate 2 knights into an entities collection of knights.
        ni = knight('knight who says ni 1')
        ni1 = knight('knight who says ni 2')

        ks = ni + ni1

        self.assertEq(entities, type(ks))
        self.assertEq(2, ks.count)
        self.assertIs(ks.first, ni)
        self.assertIs(ks.second, ni1)

        # Now contatenate an entities collection to an entity
        
        the4 = knights.createthe4()
        ks = ni + the4
        self.assertEq(entities,   type(ks))
        self.assertEq(5,          ks.count)
        self.assertIs(ks.first,   ni)
        self.assertIs(ks.second,  the4.first)
        self.assertIs(ks.third,   the4.second)
        self.assertIs(ks.fourth,  the4.third)
        self.assertIs(ks.fifth,   the4.fourth)

    def it_gets_brokenrules(self):
        """ This functionality is tested in
        test_entities.it_gets_brokenrules."""
        pass

class test_table(tester):
    def it_calls__init__(self):
        # Ensure we can instantiate without arguments
        try:
            tbl = table()
        except:
            self.assertFail('Table should instatiate without arguments')

        # Instatiate a table with 10 rows and 20 columns. All the fields'
        # values should be None
        tbl = table(x=10, y=20)

        self.assertEq(20, tbl.rows.count)
        self.assertEq(10, tbl.columns.count)
        self.assertEq(10, tbl.rows.first.fields.count)
        for r in tbl:
            for f in r:
                self.assertNone(f.value)
        

        # Instatiate a table with 10 rows and 20 columns. All the fields'
        # values should be the knight set by the initval argument.
        k = knights.createthe4().first
        tbl = table(x=10, y=20, initval=k)

        self.assertEq(20, tbl.rows.count)
        self.assertEq(10, tbl.columns.count)
        self.assertEq(10, tbl.rows.first.fields.count)
        for r in tbl:
            for f in r:
                self.assertIs(k, f.value)

    def it_calls__iter__(self):
        tbl = createtable(5, 5)
        for r in tbl:
            self.assertEq(row, type(r))
            self.assertEq(5, r.fields.count)

    def it_calls__getitem__(self):
        tbl = createtable(5, 5)
        for i in range(5):
            self.assertEq(row, type(tbl[i]))

    def it_calls__call__(self):
        tbl = createtable(5, 5)
        for i in range(5):
            for j in range(5):
                self.assertEq([i, j], tbl(i, j).value)

    def it_calls_newrow(self):
        # Ensure newrow creates a row in the table and returns it
        tbl = table()
        r = tbl.newrow()
        self.assertEq(1, tbl.rows.count)
        self.assertIs(tbl.rows.first, r)

    def it_gets_columns(self):
        tbl = createtable(5, 5)
        cs = tbl.columns
        self.assertEq(columns, type(cs))

        for i, c in enumerate(cs):
            for j, f in enumerate(c.fields):
                self.assertEq([j, i], f.value)

    def it_gets_fields(self):
        """ The table.fields property contains all the fields in the table.

        The normal hierarchy of a table structure is:

            table: 
                rows:
                    row:
                        fields:
                            field

        That's to say: A table object has a rows collection which gives you
        access to ewerything underneath. However, client code will often want
        access to the fields themselves at the table level. This fields
        collections is built and maintained by onadd and onremove events
        happening in the subordinate objects of the table object.  So, for
        testing, these means we need to ensure that, no matter how a field is
        added or removed from a table, these addition or removal needs to be
        reflected in the table.fields property. Note, however, that the
        table.fields property itself is meant to be read-only (for the most
        part) so additions or removals to table.fields itself should not make
        any changes to the table object (because 'fields' is a vector and
        table is a matrix so it's impossible to add or remove from 'fields' in
        a way that addresses the hiearchy of the matrix.) """

        tbl = createtable(5, 5)
        fs = tbl.fields

        # Ensure the correct type then count
        self.assertEq(fields, type(fs))
        self.assertEq(5 * 5, fs.count)

        # Ensure the fields collection is built in type-writer order
        for i, f in enumerate(fs):
            x, y = i % 5, int(i / 5)
            self.assertEq([y, x], f.value)

        # Create a new row to test adding to it
        r = tbl.newrow()

        # Ensure count hasn't changes
        self.assertEq(5 * 5, fs.count)

        the4 = knights.createthe4()
        rst = r.newfield(the4.first)

        # Ensure count has been incremented
        self.assertEq((5 * 5) + 1, fs.count)
        
        # Ensure last object added is the last in the fields collection.
        self.assertIs(rst, fs.last)

        # Remove the field and ensure the fields collection contains a 
        # decremented count.
        r.fields.pop()
        self.assertEq(5 * 5, fs.count)

        # Add 4 and ensure the count is correct
        for k in the4:
            r.newfield(k)

        self.assertEq((5 * 5) + 4, fs.count)

        # Remove the row and ensure the field count reflects that all the
        # fields in that row have been removed

        tbl.rows -= r
        self.assertEq(5 * 5, fs.count)

        # Test fields property after setting them in the table object.

        # TODO  When setting fields, the old field(s) is removed from the
        # table.fields collection, but the new field(s) ends up at the end of
        # the table.fields collection instead of in place of the removed
        # field(s). This is because the fields.__setitem__ simply calls the
        # onadd the onremove event, which causes an append to the collection.
        # Ideally, the new field wouldn't be appended, but would rather be set
        # in the correct location of the table.fields property. However,
        # currently there is no use case for this. However, since this should
        # change, use of table.fields shouldn't make assuptions about where
        # newly set fields will appear until this behavior is corrected.

        tbl[0][0] = rst = field(the4.first)
        tbl[0].fields.second = nd = field(the4.second)
        tbl[0].fields[2:4] = rd, rth = fields(initial=the4[2:4])

        self.assertEq(tbl.fields.first.value, [0, 4])
        self.assertIs(tbl.fields.preantepenultimate, rst)
        self.assertIs(tbl.fields.antepenultimate, nd)
        self.assertIs(tbl.fields.penultimate, rd)
        self.assertIs(tbl.fields.ultimate, rth)

    def it_calls_count(self):
        k = knights.createthe4().first
        tbl = table(x=10, y=20, initval=k)

        # TODO Wait for indexs to be reimplemented
        # self.assertEq(20 * 10, tbl.count(k))

    def it_call_where(self):
        class sillyknight(knight):
            pass
        
        the4 = knights.createthe4()
        tbl = table(x=10, y=20)
        r = tbl.newrow()
        r.newfield(the4.first)
        r.newfield(the4.second)

        ni1 = sillyknight('knight who says ni 1')
        ni2 = sillyknight('knight who says ni 2')
        fr = sillyknight('french knight')
        r = tbl.newrow()
        r.newfields(ni1, ni2, fr)

        # Test getting fields by the type of value in the fields
        fs = tbl.where(sillyknight)
        self.assertEq(3, fs.count)
        for f in fs:
            self.assertEq(tbl, f.table)

        # Same as above but with a limit
        for limit in range(2, -1, -1):
            fs = tbl.where(sillyknight, limit=limit)
            self.assertEq(limit, fs.count)
            for f in fs:
                self.assertEq(tbl, f.table)

        fs = tbl.where(knight)
        self.assertEq(2, fs.count)
        for f in fs:
            self.assertEq(tbl, f.table)

        # Same as above but with a limit
        for limit in range(2, -1, -1):
            fs = tbl.where(knight, limit=limit)
            self.assertEq(limit, fs.count)
            for f in fs:
                self.assertEq(tbl, f.table)

        # Query with a callable
        fs = tbl.where(lambda v: type(v) == knight)
        self.assertEq(2, fs.count)
        self.assertEq(fields, type(fs))
        for i, f in enumerate(fs):
            self.assertIs(the4[i], fs[i].value)
            self.assertEq(tbl, f.table)

        # Query with a callable and a limit
        for limit in range(2, -1, -1):
            fs = tbl.where(lambda v: type(v) == knight, limit)
            self.assertEq(limit, fs.count)
            self.assertEq(fields, type(fs))
            for i, f in enumerate(fs):
                self.assertIs(the4[i], fs[i].value)
                self.assertEq(tbl, f.table)

        # Query table's field by the value of the fields
        r.newfield(ni1) # Add a second ni1

        fs = tbl.where(ni1)
        self.assertEq(2, fs.count)
        for i, f in enumerate(fs):
            self.assertIs(ni1, f.value)
            self.assertEq(tbl, f.table)

        for limit in range(2, -1, -1):
            fs = tbl.where(ni1, limit=limit)
            self.assertEq(limit, fs.count)
            for i, f in enumerate(fs):
                self.assertIs(ni1, f.value)
                self.assertEq(tbl, f.table)

        # When a fields value is update, the 'value' index that tbl.where
        # depends upon must be update in order for these by-value seeks to
        # work. To test this, we simply set the 'value' property of the 'field'
        # object to an arbitray value and ensure that searching for that
        # arbitray value using where() still works.
        r.fields.first.value = 'ni ni ni'

        fs = tbl.where('ni ni ni')
        self.assertEq(1, fs.count)
        for i, f in enumerate(fs):
            self.assertIs('ni ni ni', f.value)
            self.assertEq(tbl, f.table)

        # Now lets set two fields' value property to a new value
        ekke = 'Ekke Ekke Ekke Ekke Ptang Zoo Boing!'
        r.fields.first.value = ekke
        r.fields.second.value = ekke

        fs = tbl.where(ekke)
        self.assertEq(2, fs.count)
        for i, f in enumerate(fs):
            self.assertIs(ekke, f.value)
            self.assertEq(tbl, f.table)

    def it_calls_remove(self):
        the4 = knights.createthe4()
        tbl = table(x=10, y=20)
        r = tbl.newrow()
        r.newfield(the4.first)
        r.newfield(the4.second)
        
        tbl.remove(entities(the4.first))
        fs = tbl.where(lambda v: type(v) == knight)
        self.assertEq(1, fs.count)
        self.assertEq(fields, type(fs))
        self.assertIs(the4.second, fs.first.value)

    def it_calls_slice(self):
        tbl = table(x=10, y=20)
        
        # Ensure that a TypeError will occure if radius isn't an int
        f = tbl[0][0]
        try:
            tbl.slice(center=f, radius="123")
            self.assertFail('The radius should be an int')
        except TypeError:
            self.assertTrue(True)
        except Exception as ex:
            self.assertFail('Incorrect exception raised: ' + str(type(ex)))
        
        # Ensure that a TypeError will occure if center isn't a field
        try:
            tbl.slice(center=entity(), radius=123)
            self.assertFail('Center should be a field')
        except TypeError:
            self.assertTrue(True)
        except Exception as ex:
            self.assertFail('Incorrect exception raised: ' + str(type(ex)))

        # Assign the value property of each field in the table a unique,
        # index-based value.
        for i, r in enumerate(tbl.rows):
            for j, f in enumerate(r.fields):
                f.value = str([i, j])

        # Get a slice where the middle field is the top-most, left-most field
        # of the table
        f = tbl[0][0]
        s = tbl.slice(f, 1)
        self.assertIs(table, type(s))
        self.assertIs(tbl(0, 0).value,   s(0, 0).value)
        self.assertIs(tbl(0, 1).value, s(0, 1).value)
        self.assertIs(tbl(1, 0).value,  s(1, 0).value)
        self.assertIs(tbl(1, 1).value, s(1, 1).value)
        self.assertEq(4, s.fields.count)

        # Get a slice where the middle field is the bottom-most, left-most
        # field of the table
        s = tbl.slice(tbl.rows.last.fields.first, 1)
        self.assertIs(table, type(s))
        self.assertIs(tbl.rows.penultimate.fields.first.value, s(0, 0).value)
        self.assertIs(tbl.rows.penultimate.fields.second.value, s(0, 1).value)
        self.assertIs(tbl.rows.last.fields.first.value, s(1, 0).value)
        self.assertIs(tbl.rows.last.fields.second.value, s(1, 1).value)
        self.assertEq(4, s.fields.count)

        # Get a slice where the middle field is the bottom-most, right-most
        # field of the table
        s = tbl.slice(tbl.rows.last.fields.last, 1)
        self.assertIs(table, type(s))
        self.assertIs(tbl.rows.penultimate.fields.penultimate.value, s(0, 0).value)
        self.assertIs(tbl.rows.penultimate.fields.last.value, s(0, 1).value)
        self.assertIs(tbl.rows.last.fields.penultimate.value, s(1, 0).value)
        self.assertIs(tbl.rows.last.fields.last.value, s(1, 1).value)
        self.assertEq(4, s.fields.count)

        # Get a slice where the middle field is the top-most, right-most
        # field of the table
        s = tbl.slice(tbl.rows.first.fields.last, 1)
        self.assertIs(table, type(s))
        self.assertIs(tbl.rows.first.fields.penultimate.value, s(0, 0).value)
        self.assertIs(tbl.rows.first.fields.last.value, s(0, 1).value)
        self.assertIs(tbl.rows.second.fields.penultimate.value, s(1, 0).value)
        self.assertIs(tbl.rows.second.fields.last.value, s(1, 1).value)
        self.assertEq(4, s.fields.count)

        # Get a slice where the middle field somewhere in the center of the
        # table so we get a slice with nine field objects.
        s = tbl.slice(tbl.rows.fifth.fields.fifth, 1)
        self.assertIs(table, type(s))
        self.assertIs(tbl(3,3).value, s(0, 0).value)
        self.assertIs(tbl(3,4).value, s(0, 1).value)
        self.assertIs(tbl(3,5).value, s(0, 2).value)

        self.assertIs(tbl(4,3).value, s(1, 0).value)
        self.assertIs(tbl(4,4).value, s(1, 1).value)
        self.assertIs(tbl(4,5).value, s(1, 2).value)

        self.assertIs(tbl(5,3).value, s(2, 0).value)
        self.assertIs(tbl(5,4).value, s(2, 1).value)
        self.assertIs(tbl(5,5).value, s(2, 2).value)

    def it_calls__str__(self):
        the4 = knights.createthe4()
        tbl = table()
        r = tbl.newrow()
        r.newfield(the4.first)
        r.newfield(the4.second)
        r = tbl.newrow()
        r.newfield(the4.third)
        r.newfield(the4.fourth)

        s =  '+---------------------+\n'
        s += '| Lancelot | Authur   |\n'
        s += '|---------------------|\n'
        s += '| Galahad  | Bedevere |\n'
        s += '+---------------------+\n'

        self.assertEq(s, str(tbl))

class test_columns(tester):
    def it_gets_widths(self):
        tbl = table()
        for i in range(5):
            r = tbl.newrow()
            for j in range(5):
                r.newfield([i, j])

        cs = tbl.columns
        self.assertEq(5, cs.count)
        self.assertEq([6] * 5, cs.widths)

class test_column(tester):
    def it_calls__init(self):
        tbl = createtable(5, 5)

        cs = tbl.columns
        self.assertEq(5, cs.count)
        self.assertEq(columns, type(cs))
        for i, c in enumerate(cs):
            self.assertEq(column, type(c))
            fs = c.fields
            self.assertEq(5, fs.count)
            for j, f in enumerate(fs):
                self.assertEq(field, type(f))
                y, x = j, i
                self.assertEq([y, x], f.value)

    def it_calls_width(self):
        """ The width property of a column is the maximun number of characters
        contained in the value property of all the fields in the column. """

        # Populate the field's with strings of 'x' where the last column
        # contains 4 'x''s, which will be the largest. 
        tbl = createtable(5, 5)
        for i, r in enumerate(tbl):
            for f in r:
                f.value = 'x' * i

        # Test that the maximum column length is 4
        for c in tbl.columns:
            self.assertEq(4, c.width)

class test_row(tester):
    def it_calls__getitems__(self):
        """ The __getitem__ method returns the field at the given index
        number.  """
        tbl = createtable(5, 5)
        for r in tbl:
            for i, f in enumerate(r.fields):
                self.assertIs(f, r[i])

    def it_calls__setitems__(self):
        """ The __setitem__ method sets field at the given index
        number.  """
        tbl = createtable(5, 5)
        for i, r in enumerate(tbl):
            for j, f in enumerate(r.fields):
                r[j] = f1 = field([i, j])
                self.assertIs(f1, r[j])

    def it_gets_index(self):
        """ A row's index property contains the 0-based ordinal, i.e.,
        the first row in a table has an index of 0, the second has an
        index of 1, and so on. """

        # Create a table with 5 rows and ensure their index property is equal
        # to the position of the row in the table.
        tbl = createtable(5, 5)
        for i, r in enumerate(tbl):
            self.assertEq(i, r.index)

    def it_gets_table(self):
        """ Every row will have a reference to the table it's in. """
        tbl = createtable(5, 5)
        for r in tbl:
            self.assertIs(tbl, r.table)

    def it_gets_above(self):
        """ The above property of a row is the row object above the given row.
        """

        tbl = createtable(5, 5)
        prev = None
        for r in tbl:
            self.assertIs(prev, r.above)
            prev = r

    def it_gets_below(self):
        """ The below property of a row is the row object below the given row.
        """

        tbl = createtable(5, 5)
        rs = tbl.rows
        for i, r in enumerate(rs):
            self.assertIs(rs(i + 1), r.below)

    def it_calls_newfield(self):
        """ The newfield method creates a new field object and appends it to
        the row's fields collection. """
        tbl = table()
        r = tbl.newrow()
        f = r.newfield(123)

        self.assertEq(field, type(f))
        self.assertEq(1, r.fields.count)
        self.assertIs(f, r.fields.first)
        self.assertIs(f, tbl.rows.first.fields.first)
        self.assertEq(123, f.value)

    def it_calls__repr__(self):
        tbl = createtable(2, 2)

        expect = '''
        +-----------------+
        | [1, 0] | [1, 1] |
        +-----------------+
        '''
        expect = textwrap.dedent(expect).lstrip()

        self.eq(expect, repr(tbl.rows.second))

class test_fields(tester):
    def it_get_row(self):
        " A fields collection will have a reference to the row it's in. """
        tbl = table()
        r = tbl.newrow()
        f = r.newfield(123)
        self.assertIs(r, f.row)

    def it_get_table(self):
        " A fields collection will have a reference to the table it's in. """
        tbl = table()
        r = tbl.newrow()
        f = r.newfield(123)
        self.assertIs(tbl, f.table)

    def it_get_values(self):
        """ A fields collection value property will be a list of all the values
        in each of its field objects. """
        tbl = createtable(5, 5)
        for i, r in enumerate(tbl):
            for j, f in enumerate(r):
                f.value = [i, j]

        for i, r in enumerate(tbl):
            self.assertEq([[i, x] for x in range(5)], r.fields.values)

class test_field(tester):
    def it_gets_values(self):
        """ The constructor of field will set the value property. """
        f = field(123)
        self.assertEq(123, f.value)

    def it_sets_value(self):
        """ The value property is a read/write property so ensure it can be
        read and written to. """
        f = field(123)
        f.value = 'abc'
        self.assertEq('abc', f.value)

    def it_calls_clone(self):
        """ Calling clone on a field object will create a new field with the
        same value."""
        f = field(123)
        clone = f.clone()

        self.assertEq(f.value, clone.value)

    def it_gets_index(self):
        """ The index property of a field objects gives the ordinal position
        the field occupies in the row. """
        tbl = table(5, 5)
        for r in tbl:
            for i, f in enumerate(r):
                self.assertEq(i, f.index)

    def it_gets_table(self):
        """ Each field object will contain a reference to its table object. 
        """
        tbl = table(5, 5)
        for r in tbl:
            for f in r:
                self.assertIs(tbl, f.table)
    
    def it_gets_row(self):
        """ Each field object will contain a reference to its row object. 
        """
        tbl = table(5, 5)
        for r in tbl:
            for f in r:
                self.assertIs(r, f.row)

    def it_gets_above(self):
        tbl = table(5, 5)
        rs = tbl.rows
        for i, r in enumerate(rs):
            fs = r.fields
            for j, f in enumerate(fs):
                if i == 0:
                    self.assertNone(f.above)
                else:
                    self.assertIs(rs[i - 1].fields(j), f.above)

    def it_gets_below(self):
        tbl = table(5, 5)
        rs = tbl.rows
        for i, r in enumerate(rs):
            fs = r.fields
            for j, f in enumerate(fs):
                if i == rs.ubound:
                    self.assertNone(f.below)
                else:
                    self.assertIs(rs[i + 1].fields(j), f.below)

    def it_gets_left(self):
        tbl = table(5, 5)
        for r in tbl:
            fs = r.fields
            for i, f in enumerate(fs):
                if i == 0:
                    self.assertNone(f.left)
                else:
                    self.assertIs(fs[i - 1], f.left)

    def it_gets_right(self):
        tbl = table(5, 5)
        for r in tbl:
            fs = r.fields
            for i, f in enumerate(fs):
                if i == fs.ubound:
                    self.assertNone(f.right)
                else:
                    self.assertIs(fs[i + 1], f.right)

    def it_gets_aboveleft(self):
        tbl = table(5, 5)
        rs = tbl.rows
        for i, r in enumerate(rs):
            fs = r.fields
            for j, f in enumerate(fs):
                if i == 0 or j == 0:
                    self.assertNone(f.aboveleft)
                else:
                    self.assertIs(r.above.fields[j - 1], f.aboveleft)

    def it_gets_belowleft(self):
        tbl = table(5, 5)
        rs = tbl.rows
        for i, r in enumerate(rs):
            fs = r.fields
            for j, f in enumerate(fs):
                if i == rs.ubound or j == 0:
                    self.assertNone(f.belowleft)
                else:
                    self.assertIs(r.below.fields[j - 1], f.belowleft)

    def it_gets_aboveright(self):
        tbl = table(5, 5)
        rs = tbl.rows
        for i, r in enumerate(rs):
            fs = r.fields
            for j, f in enumerate(fs):
                if i == 0 or j == fs.ubound:
                    self.assertNone(f.aboveright)
                else:
                    self.assertIs(r.above.fields[j + 1], f.aboveright)

    def it_gets_belowright(self):
        tbl = table(5, 5)
        rs = tbl.rows
        for i, r in enumerate(rs):
            fs = r.fields
            for j, f in enumerate(fs):
                if i == rs.ubound or j == fs.ubound:
                    self.assertNone(f.belowright)
                else:
                    self.assertIs(r.below.fields[j + 1], f.belowright)

    def it_calls__str__(self):
        Reverse='\033[07m'
        Endc = '\033[0m'

        tbl = table(1, 1, 123)
        self.assertEq('123', str(tbl[0][0]))

        tbl.rows.first.newfield('abc')
        s  = '+-----------+\n'
        s += '| 123 | ' + Reverse + 'abc' + Endc + ' |\n'
        s += '+-----------+\n'
        self.assertEq(s, tbl[0][1].__str__(table=True))

    def _it_calls_get_direction(self, fn, bt, cab, c):
        """ This is the generic method for all the self.it_calls_get*()
        methods.  It tests the field.get<direction> methods like
        field.getabove().

        :param str fn: The name of the method we are testing, e.g., 'getabove'

        :param bt calable: Boundry test. If this returns True, the reach has
        exceeded the boundry of the table.

        :param cab callable: Closests at Boundry. Returns the field object
        without exceeding the reach of the boundry, in which case it would
        have to return None.

        :param c callable: Returns the field without a concern for exceeding
        the boundry. 

        """

        tbl = table(5, 5)
        rs = tbl.rows

        for i, r in enumerate(rs):
            fs = r.fields
            for j, f in enumerate(fs):
                for closest in [True, False]:
                    for number in range(rs.count * 2):
                        if bt(rs, i, j, number):
                            if closest:
                                expect = cab(rs, i, j, number)
                            else:
                                expect = None
                        else:
                            expect = c(rs, i, j, number)

                        actual = getattr(f, fn)(number=number, closest=closest)
                        if expect is not actual:
                            expect = cab(rs, i, j, number)
                        self.assertIs(expect, actual)

    def it_calls_getabove(self):
        bt  = lambda rs, i, j, number: i - number < 0
        cab = lambda rs, i, j, number: rs[0][j]
        c   = lambda rs, i, j, number: rs[i - number][j]

        self._it_calls_get_direction('getabove', bt, cab, c)

    def it_calls_getbelow(self):
        bt  = lambda rs, i, j, number: i + number > rs.ubound
        cab = lambda rs, i, j, number: rs[rs.ubound][j]
        c   = lambda rs, i, j, number: rs[i + number][j]

        self._it_calls_get_direction('getbelow', bt, cab, c)

    def it_calls_getleft(self):
        bt  = lambda rs, i, j, number: j - number < 0
        cab = lambda rs, i, j, number: rs[i][0]
        c   = lambda rs, i, j, number: rs[i][j - number]

        self._it_calls_get_direction('getleft', bt, cab, c)

    def it_calls_getright(self):
        bt  = lambda rs, i, j, number: j + number > rs[i].fields.ubound
        cab = lambda rs, i, j, number: rs[i][rs[i].fields.ubound]
        c   = lambda rs, i, j, number: rs[i][j + number]

        self._it_calls_get_direction('getright', bt, cab, c)

    def it_calls_getaboveleft(self):
        bt = lambda rs, i, j, number: i - number < 0 or j - number < 0
        
        def cab(rs, i, j, number):
            f = rs[i][j]

            for _ in range(number):
                neighbor = f.aboveleft
                if not neighbor:
                    return f
                f = neighbor

        c  = lambda rs, i, j, number: rs[i - number][j - number]

        self._it_calls_get_direction('getaboveleft', bt, cab, c)

    def it_calls_getbelowleft(self):
        bt = lambda rs, i, j, number: i + number > rs.ubound \
                                      or j - number < 0
        
        def cab(rs, i, j, number):
            f = rs[i][j]

            for _ in range(number):
                neighbor = f.belowleft
                if not neighbor:
                    return f
                f = neighbor
            return f

        c  = lambda rs, i, j, number: rs[i + number][j - number]

        self._it_calls_get_direction('getbelowleft', bt, cab, c)

    def it_calls_getaboveright(self):
        bt = lambda rs, i, j, number: i - number < 0 \
                                      or j + number > rs.table.columns.ubound
        
        def cab(rs, i, j, number):
            f = rs[i][j]

            for _ in range(number):
                neighbor = f.aboveright
                if not neighbor:
                    return f
                f = neighbor
            return f

        c  = lambda rs, i, j, number: rs[i - number][j + number]

        self._it_calls_get_direction('getaboveright', bt, cab, c)

    def it_calls_getbelowright(self):
        bt = lambda rs, i, j, number: i + number > rs.ubound \
                                      or j + number > rs.table.columns.ubound
        
        def cab(rs, i, j, number):
            f = rs[i][j]

            for _ in range(number):
                neighbor = f.belowright
                if not neighbor:
                    return f
                f = neighbor
            return f

        c  = lambda rs, i, j, number: rs[i + number][j + number]

        self._it_calls_get_direction('getbelowright', bt, cab, c)
    
    def it_gets__str__(self):
        tbl = table(5, 5, initval='123')
        for f in tbl.fields:
            self.assertEq('123', str(f))

        s = """+-----------------------------+
| \x1b[07m123\x1b[0m | 123 | 123 | 123 | 123 |
|-----------------------------|
| 123 | 123 | 123 | 123 | 123 |
|-----------------------------|
| 123 | 123 | 123 | 123 | 123 |
|-----------------------------|
| 123 | 123 | 123 | 123 | 123 |
|-----------------------------|
| 123 | 123 | 123 | 123 | 123 |
+-----------------------------+
"""
        f = tbl[0][0]
        self.assertEq(s, f.__str__(table=True))

class test_index(tester):
    # TODO Complete this class
    def it_calls_getindex(self):
        sks = sillyknights.createthe4()
        french_knight = 'french knight'

        ls = sks.indexes['name'].getlist(french_knight)

        self.assertIs(list, type(ls))
        self.assertEq(1, len(ls))

        sks += sillyknight(french_knight)

        ls = sks.indexes['name'].getlist(french_knight)
        self.assertIs(list, type(ls))
        self.assertEq(2, len(ls))

    def it_calls_append(self):
        # TODO
        pass

    def it_calls_remove(self):
        ks = knights.createthe4()

        ix = ks.indexes['traittype'];

        # Remove the first knight from the index. Since the trait property was
        # None, the value of the index will be NoneType. So check that the
        # index with the value of type(None) has 3 entities.
        ix.remove(ks.first)
        self.assertEq(3, ix(type(None)).count)

        # Add a knight with a trait whose type is str. 
        k = knight('sir robins')
        k.trait = 'not-quite-so bravery'
        ks += k

        # Ensure that the trait index has an entry for an str trait
        self.assertEq(1, ix(str).count)

        # Now remove it from the index
        ix.remove(k)

        # Ensure that it has been removed.
        self.assertTrue(ix(str).isempty)

        # TODO
        # Test the return value from the remove() method

    def it_calls_move(self):
        ks = knights.createthe4()
        ix = ks.indexes['traittype']

        # First, all the trait types will be NoneType
        self.assertEq(4, ix(type(None)).count)

        # Set the trait. When the trait property is set, the onvaluechange 
        # event will be raised which will cause the knight to be 
        # removed from the index at key NoneType to the key 'str'
        ks['Lancelot'].trait = 'bravery'

        # Now, 3 trait types will be NoneTypes and 1 will be a str ('bravery')
        self.assertEq(3, ix(type(None)).count)
        self.assertEq(1, ix(str).count)

class test_logs(tester):
    
    def it_writes_to_log(self):
        # Since this goes to syslogd, a user will need to verify that
        # these messages were successfully logged.
        logs = []
        def onlog(src, eargs):
            logs.append(eargs.record.message)

        cfg = configfile.getinstance()
        if not cfg.isloaded:
            # TODO We should raise something like CantTestError
            return

        l = cfg.logs.default
        l.onlog += onlog

        l.debug('xdebug');
        self.assertTrue('xdebug' in logs)
        self.assertCount(1, logs)

        l.info('xinfo');
        self.assertTrue('xinfo' in logs)
        self.assertCount(2, logs)

        l.warning('xwarning');
        self.assertTrue('xwarning' in logs)
        self.assertCount(3, logs)

        l.error('xerror');
        self.assertTrue('xerror' in logs)
        self.assertCount(4, logs)

        l.critical('xcritical');
        self.assertCount(5, logs)

        self.assertTrue('xcritical' in logs)
        try:
            raise Exception('derp')
        except:
            l.exception('xexception')
            self.assertTrue('xexception' in logs)
            self.assertCount(6, logs)

class test_jwt(tester):
    def __init__(self):
        super().__init__()
    
    def it_calls_exp(self):
        t = jwt()

        # Exp defaults to 24 hours in the future
        hours = math.ceil((t.exp - datetime.datetime.now()).seconds / 3600)
        self.assertEq(24, hours)

        # Specify 48 hours to expire
        t = jwt(ttl=48)
        hours = math.ceil((t.exp - datetime.datetime.now()).seconds / 3600)
        self.assertEq(24, hours)

    def it_calls_token(self):
        t = jwt()
        token = t.token
        secret = configfile.getinstance()['jwt-secret']

        d = pyjwt.decode(token, secret)

        exp = datetime.datetime.fromtimestamp(d['exp'])

        # Ensure exp is about 24 hours into the future
        hours = math.ceil((exp - datetime.datetime.now()).seconds / 3600)
        self.assertEq(24, hours)

    def it_sets_iss(self):
        iss = str(uuid4())
        t = jwt()
        t.iss = iss
        token = t.token

        self.assertEq(iss, t.iss)

        t1 = jwt(token)
        self.assertEq(iss, t1.iss)

        token = t1.token
        t1.iss = str(uuid4())
        self.assertNe(token, t1.token)

    def it_fails_decoding_with_wrong_secret(self):
        t = jwt()

        try:
            d = pyjwt.decode(t.token, 'wrong-secret')
        except pyjwt.exceptions.DecodeError:
            pass # This is the expected path
        except Exception as ex:
            self.assertFail('Wrong exception type')
        else:
            self.assertFail('Exception not thrown')
            print(ex)

    def it_makes_tokes_eq_to__str__(self):
        t = jwt()
        self.assertEq(t.token, str(t))

    def it_validates(self):
        # Valid
        t = jwt()
        t1 = jwt(t.token)

        # Invalid
        t = jwt('an invalid token')
        self.assertFalse(t.isvalid)

class test_datetime(tester):
    def it_calls__init__(self):
        utc = datetime.timezone.utc
        
        # Test datetime with standard args
        args = (2003, 10, 11, 17, 13, 46)
        expect = datetime.datetime(*args, tzinfo=utc)
        actual = primative.datetime(*args, tzinfo=utc)
        self.eq(expect, actual)

        # Test datetime with standard a string arg intended for datautil.parser
        actual = primative.datetime('Sat Oct 11 17:13:46 UTC 2003')
        self.eq(expect, actual)

    def it_calls_astimezone(self):
        utc = datetime.timezone.utc

        args = (2003, 10, 11, 17, 13, 46)
        dt = primative.datetime(*args, tzinfo=utc)
        
        aztz = dateutil.tz.gettz('US/Arizona')
        actual = datetime.datetime(2003, 10, 11, 10, 13, 46, tzinfo=aztz)

        expect = dt.astimezone(aztz)
        self.eq(expect, actual)

        # FIXME
        # If datetime.astimezone is given an invalid argument for the timezone
        # (i.e., dt.astimezone('XXX')), it will give the following warning but
        # will not throw an exception. This needs to be investigated and
        # probably remedied.
        #
        #     /usr/lib/python3/dist-packages/dateutil/zoneinfo/__init__.py:36:
        #     UserWarning: I/O error(2): No such file or directory
        #     warnings.warn("I/O error({0}): {1}".format(e.errno, e.strerror))

        expect = dt.astimezone('US/Arizona')
        self.eq(expect, actual)

class mycli(cli):
    def registertraceevents(self):
        ts = self.testers
        ts.oninvoketest += lambda src, eargs: print('.', end='', flush=True)
       

##################################################################################
''' ORM Tests '''
##################################################################################

class comments(orm.entities):
    pass

class comment(orm.entity):
    title = str
    body = str
    comments = comments

    @staticmethod
    def getvalid():
        com = comment()
        com.title = uuid4().hex
        com.body = '%s\n%s' % (uuid4().hex, uuid4().hex)
        return com

class locations(orm.entities):
    pass

class presentations(orm.entities):
    pass

class concerts(presentations):
    pass

class battles(concerts):
    pass

class components(orm.entities):
    pass

class artifacts(orm.entities):
    pass

class artists(orm.entities):
    pass

class location(orm.entity):
    address     = str
    description = str

    @staticmethod
    def getvalid():
        loc = location()
        loc.description = uuid4().hex
        loc.address     = uuid4().hex
        return loc

class presentation(orm.entity):
    date         =  datetime
    name         =  orm.fieldmapping(str)
    description  =  str
    locations    =  locations
    components   =  components
    title        =  str,        orm.fulltext('title_desc',0)
    description1 =  str,        orm.fulltext('title_desc',1)

    @staticmethod
    def getvalid():
        pres = presentation()
        pres.name          =  uuid4().hex
        pres.description   =  uuid4().hex
        pres.description1  =  uuid4().hex
        pres.title         =  uuid4().hex
        return pres

class concert(presentation):
    @staticmethod
    def getvalid():
        pres = presentation.getvalid()
        conc = concert()
        conc.record = uuid4().hex
        conc.name = uuid4().hex
        conc.title = pres.title
        conc.description = pres.description
        conc.description1 = pres.description1
        return conc
    
    record = orm.fieldmapping(str)

    # tinyint
    ticketprice  =  orm.fieldmapping(int,  min=-128,      max=127)

    # mediumint
    attendees    =  orm.fieldmapping(int,  min=-8388608,  max=8388607)

    # tinyint unsigned
    duration     =  orm.fieldmapping(int,  min=0,         max=255)

    # mediumint unsigned
    capacity     =  orm.fieldmapping(int,  min=0,         max=16777215)

    # int unsigned
    externalid   =  orm.fieldmapping(int,  min=0,         max=4294967295)

    # bigint unsigned
    externalid1  =  orm.fieldmapping(int,  min=0,         max=(2**64)-1)

class battle(concert):
    views = int

    @staticmethod
    def getvalid():
        conc = concert.getvalid()
        btl = battle()

        for map in conc.orm.mappings.all:
            if type(map) is not orm.fieldmapping:
                continue
            setattr(btl, map.name, getattr(conc, map.name))

        return btl

class component(orm.entity):
    @staticmethod
    def getvalid():
        comp = component()
        comp.name = uuid4().hex
        comp.digest = bytes([randint(0, 255) for _ in range(32)])
        return comp

    name    =  str
    weight  =  float,  8,   7
    height  =  float
    digest  =  bytes,  16,  255

    @orm.attr(float, 5, 1)
    def width(self):
        return attr(abs(attr()))

class artifact(orm.entity):
    def getvalid():
        fact = artifact()
        fact.title = uuid4().hex
        fact.description = uuid4().hex
        return fact

    title        =  str,        orm.fulltext('title_desc',0)
    description  =  str,        orm.fulltext('title_desc',1)
    weight       =  int,        -2**63,                       2**63-1
    abstract     =  bool
    price        =  dec
    components   =  components

class artist(orm.entity):
    firstname      =  str, orm.index('fullname', 1)
    lastname       =  str, orm.index('fullname', 0)
    lifeform       =  str
    weight         =  int, 0, 1000
    networth       =  int
    style          =  str, 1, 50
    dob            =  datetime
    password       =  bytes, 32, 32
    ssn            =  str, 11, 11, orm.index #  char
    locations      =  locations
    presentations  =  presentations

    # title here to be ambigous with artifact.title. It's purpose is to ensure
    # against ambiguity problems that may arise
    title          =  str, 0, 1
    phone2         =  str, 0, 1
    email_1        =  str, 0, 1

    # Bio's will be longtext. Any str where max > 65,535 can no longer be a
    # varchar, so we make it a longtext.
    bio = str, 1, 65535 + 1, orm.fulltext

    comments = comments

    @staticmethod
    def getvalid():
        art = artist()
        art.firstname = 'Gary'
        art.lastname  = 'Yourofsky'
        art.lifeform  = uuid4().hex
        art.password  = bytes([randint(0, 255) for _ in range(32)])
        art.ssn       = '1' * 11
        art.phone     = '1' * 7
        art.email     = 'username@domain.tld'
        return art

    @orm.attr(int, 1000000, 9999999)
    def phone(self):
        phone = attr()
        if phone is None:
            return None
        # Strip non-numerics ( "(555)-555-555" -> "555555555" )

        if type(phone) is str and not phone.isnumeric():
            phone = re.sub('\D*', '', phone)

            # Cache in map so we don't have to do this every time the
            # phone attribute is read. (Normally, caching in the map
            # would be needed if the operation actually took a really
            # long time.  The output for the re.sub wouldn't typically
            # need to be cached. This is simply to test the attr()
            # function's ability to set map values.)
            attr(phone)

        return attr()

    @orm.attr(str, 3, 254)
    def email(self):
        return attr().lower()

    # Though it seems logical that there would be mutator analog to the
    # accessor logic (used above for the 'phone' attr), there doesn't
    # seem to be a need for this. Conversions should be done in the
    # accessor (as in the 'phone' accessor above).  If functionality
    # needs to run when a mutator is called, this can be handled in an
    # onaftervaluechange handler (though this seems rare).  Since at the
    # moment, no use-case can be imagined for mutator @attr's, we should
    # leave this unimplemented. If a use-case presents itself, the
    # below, commented-out code approximates how it should look.  The
    # 'setter' method in the 'Property' class here
    # https://docs.python.org/3/howto/descriptor.html#properties hints
    # at how this may be implemented in orm.attr.
    """
    @phone.setter(str)
    def phone(self,)
        self.orm.mappings('phone').value = v
    """

    def __init__(self, o=None):
        super().__init__(o)

        if self.orm.isnew:
            self.lifeform = 'organic'
            self.bio = None
            self.style = 'classicism'
            self._processing = False

    def clear(self):
        self.locations.clear()
        self.presentations.clear()

    @property
    def processing(self):
        return self._processing

    @processing.setter
    def processing(self, v):
        self._processing = v

    @property
    def fullname(self):
        return self.firstname + ' ' + self.lastname

    def __str__(self):
        return self.fullname
        
class artist_artifacts(orm.associations):
    pass

class artist_artifact(orm.association):
    artist    =  artist
    artifact  =  artifact
    role      =  str
    planet    =  str

    def __init__(self, o=None):
        self['planet'] = 'Earth'
        self._processing = False
        super().__init__(o)

    @staticmethod
    def getvalid():
        # TODO Is an aa without an artifact object valid, i.e., should
        # it not have a brokenrule for the missing artifact?
        aa = artist_artifact()
        aa.role = uuid4().hex
        aa.timespan = uuid4().hex
        return aa

    # The duration an artist worked on an artifact
    @orm.attr(str)
    def timespan(self):
        return attr().replace(' ', '-')

    @property
    def processing(self):
        return self._processing

    @processing.setter
    def processing(self, v):
        self._processing = v

class singers(artists):
    pass

class singer(artist):
    voice    = str
    concerts = concerts

    @staticmethod
    def getvalid():
        super = singer.orm.super.getvalid()

        sng = singer()
        keymaps = (orm.primarykeyfieldmapping, orm.foreignkeyfieldmapping)
        for map in super.orm.mappings:
            if isinstance(map, orm.fieldmapping) and type(map) not in keymaps:
                setattr(sng, map.name, getattr(super, map.name))

        sng.voice     = uuid4().hex
        sng.register  = 'laryngealization'
        return sng

    @orm.attr(str)
    def register(self):
        #v = self.orm.mappings['register'].value.lower()
        v = attr().lower()

        if v in ('laryngealization', 'pulse phonation', 'creak'):
            return 'vocal fry'
        if v in ('flute', 'whistle tone'):
            return 'whistle'
        return v

    def __init__(self, o=None):
        self._transmitting = False
        super().__init__(o)

    def clear(self):
        super().clear()
        self.concerts.clear()

    @property
    def transmitting(self):
        return self._transmitting

    @transmitting.setter
    def transmitting(self, v):
        self._transmitting = v

class rappers(singers):
    pass

class rapper(singer):
    nice = int
    stagename = str
    battles = battles

    def __init__(self, o=None):
        super().__init__(o)
        if self.orm.isnew:
            self.nice = 10
            self._elevating = False

    @staticmethod
    def getvalid():
        keymaps = (orm.primarykeyfieldmapping, orm.foreignkeyfieldmapping)

        rpr = rapper()
        sup = type(rpr.orm.super).getvalid()
        while sup: # :=
            for map in sup.orm.mappings:
                if isinstance(map, orm.fieldmapping) and type(map) not in keymaps:
                    setattr(rpr, map.name, getattr(sup, map.name))

            sup = type(sup.orm.super).getvalid() if sup.orm.super else None

        rpr.nice = randint(1, 255)
        rpr.stagename = '1337 h4x0r'
        return rpr

    @property
    def elevating(self):
        return self._elevating

    @elevating.setter
    def elevating(self, v):
        self._elevating = v

    @orm.attr(str)
    def abilities(self):
        def bs():
            r = list()
            r.append('endless rhymes')
            r.append('delivery')
            r.append('money')
            return r

        return str(attr()) if attr() else attr(str(bs()))

class issues(orm.entities):
    pass

class issue(orm.entity):
    @orm.attr(str)
    def raiseAttributeError(self):
        raise AttributeError()

class test_orm(tester):
    def __init__(self):
        super().__init__()
        self.chronicles = db.chronicles()
        db.chronicler.getinstance().chronicles.onadd += self._chronicler_onadd

        artist.orm.recreate(recursive=True)
        comment.orm.recreate()
    
    def _chrons(self, e, op):
        chrons = self.chronicles.where('entity',  e)
        if not (chrons.hasone and chrons.first.op == op):
            self._failures += failure()

    def _chronicler_onadd(self, src, eargs):
        self.chronicles += eargs.entity
        #print(eargs.entity)

    @contextmanager
    def _chrontest(self):
        test_orm = self
        class tester:
            def __init__(self):
                self.count = 0

            def run(self, callable):
                test_orm.chronicles.clear()
                r = callable()
                self.chronicles = test_orm.chronicles.clone()
                return r

            def created(self, e):
                if not self._test(e, 'create'):
                    test_orm._failures += failure()

            def retrieved(self, e):
                if not self._test(e, 'retrieve'):
                    test_orm._failures += failure()

            def updated(self, e):
                if not self._test(e, 'update'):
                    test_orm._failures += failure()

            def deleted(self, e):
                if not self._test(e, 'delete'):
                    test_orm._failures += failure()

            def _test(self, e, op):
                chron = self.chronicles.where('entity',  e)
                if chron.hasone and chron.first.op == op:
                    self.count += 1
                    return True
                return False

            def __str__(self):
                r = 'Test count: %s\n\n' % self.count
                r += str(self.chronicles)
                return r

        t = tester() # :=
        yield t

        # HACK The below gets around the fact that tester.py can't deal
        # with stack offsets at the moment.
        # TODO Correct the above HACK.
        msg = "test in %s at %s: Incorrect chronicles count." 
        msg %= inspect.stack()[2][2:4]

        cnt = 0
        for chron in t.chronicles:
            cnt += int(chron.op not in ('reconnect',))
            
        self.eq(cnt, t.count, msg)

    def it_creates_indexes_on_foreign_keys(self):
        # Standard entity
        self.notnone(presentation.orm.mappings['artistid'].index)

        # Recursive entity
        self.notnone(comment.orm.mappings['commentid'].index)

        # Associations
        self.notnone(artist_artifact.orm.mappings['artistid'].index)
        self.notnone(artist_artifact.orm.mappings['artifactid'].index)
        
    def it_calls_isrecursive_property(self):
        self.false(artist.orm.isrecursive)
        self.false(artist().orm.isrecursive)
        self.false(artists.orm.isrecursive)
        self.false(artists().orm.isrecursive)

        self.false(artist_artifact.orm.isrecursive)
        self.false(artist_artifact().orm.isrecursive)
        self.false(artist_artifacts.orm.isrecursive)
        self.false(artist_artifacts().orm.isrecursive)

        self.true(comment.orm.isrecursive)
        self.true(comment().orm.isrecursive)
        self.true(comments.orm.isrecursive)
        self.true(comments().orm.isrecursive)

    def it_computes_abbreviation(self):
        es = orm.orm.getentitys() + orm.orm.getassociations()

        abbrs = [e.orm.abbreviation for e in es]
        abbrs1 = [e().orm.abbreviation for e in es]
        self.unique(abbrs)
        self.eq(abbrs, abbrs1)

        for i in range(10):
            self.eq(abbrs, [e.orm.abbreviation for e in es])
            self.eq(abbrs, [e().orm.abbreviation for e in es])

    def it_calls_count_on_class(self):
        cnt = 10
        for i in range(cnt):
            artist.getvalid().save()

        self.ge(artists.count, cnt)

        arts = artists()
        arts += artist.getvalid()
        arts.count

    def it_calls__str__on_entities(self):
        arts = artists()
        arts += artist.getvalid()
        arts += artist.getvalid()

        r = '%s object at %s count: %s\n' % (type(arts), 
                                             hex(id(arts)), 
                                             arts.count)
        for art in arts:
            r += '    ' + str(art) + '\n'
            
        self.eq(r, str(arts))

    def it_has_index(self):
        # TODO When DDL reading facilities are made available through
        # the DDL migration code, use them to ensure that artists.ssn
        # and other indexed columns are sucessfully being index in
        # MySQL.
        ...

    def it_has_composite_index(self):
        # TODO When DDL reading facilities are made available through
        # the DDL migration code, use them to ensure that
        # artist.firstname and artist.lastname share a composite index.
        ...

    def it_calls_createdat(self):
        art = artist.getvalid()
        self.none(art.createdat)
        
        # Ensure the createdat gets the current datetime

        # Strip seconds and microsecond for comparison
        expect = primative.datetime.utcnow().replace(microsecond=0, second=0)
        art.save()
        actual = art.createdat.replace(microsecond=0, second=0)

        art = artist(art.id)
        self.eq(expect, actual)

        # Ensure the createdat isn't change on subsequest saves
        art.firstname == uuid4().hex
        art.save()
        art1 = artist(art.id)
        self.eq(art.createdat, art1.createdat)

    def it_calls_updatedate(self):
        art = artist.getvalid()
        self.none(art.updatedat)
        
        # Ensure the updatedat gets the current datetime on creation

        # Strip seconds and microsecond for comparison
        expect = primative.datetime.utcnow().replace(microsecond=0, second=0)
        art.save()
        actual = art.updatedat.replace(microsecond=0, second=0)

        art = artist(art.id)
        self.eq(expect, actual)

        # Ensure the updatedat is change on subsequest saves
        art.firstname = uuid4().hex
        expected = art.updatedat
        art.save()
        art1 = artist(art.id)
        self.gt(art.updatedat, expected)

    def it_cant_instantiate_entities(self):
        ''' Since orm.entities() wouldn't have an orm property (since a
        subclass hasn't invoked the metaclass code that would assign it the orm
        property), generic entities collections shouldn't be allowed. They
        should basically be considered abstract. '''
        self.expect(NotImplementedError, lambda: orm.entities())

    def it_calls__str__on_entity(self):
        art = artist.getvalid()
        self.eq(art.fullname, str(art))
        
    def it_has_static_composites_reference(self):
        comps = location.orm.composites
        es = [x.entity for x in comps]
        self.two(comps)
        self.true(presentation in es)
        self.true(artist in es)

        comps = presentation.orm.composites
        self.one(comps)
        self.is_(comps.first.entity, artist)

        comps = artifact.orm.composites
        self.one(comps)
        self.is_(comps.first.entity, artist)

        comps = artist.orm.composites
        self.one(comps)
        self.is_(comps.first.entity, artifact)

        comps = singer.orm.composites
        self.one(comps)
        self.is_(comps.first.entity, artifact)

        comps = concert.orm.composites
        self.one(comps)
        self.is_(comps.first.entity, singer)

    def it_has_static_constituents_reference(self):
        consts = [x.entity for x in artist.orm.constituents]
        self.four(consts)
        self.true(presentation in consts)
        self.true(artifact     in consts)
        self.true(location     in consts)
        self.true(comment     in consts)

        consts = artist.orm.constituents['presentation'].orm.constituents
        self.two(consts)
        consts.sort('name')
        self.is_(consts.first.entity, component)
        self.is_(consts.second.entity, location)

        consts = artifact.orm.constituents
        self.two(consts)

        consts.sort('name')
        self.is_(consts.first.entity, artist)
        self.is_(consts.second.entity, component)

        consts = [x.entity for x in comments.orm.constituents]
        self.one(consts)
        self.true(comment in consts)

    def it_has_static_super_references(self):
        self.is_(artist, singer.orm.super)

    def it_loads_and_saves_multicomposite_entity(self):
        chrons = self.chronicles

        # Create artist with presentation with empty locations and
        # presentations, reload and test
        art = artist.getvalid()
        pres = presentation.getvalid()

        self.zero(art.locations)
        self.zero(pres.locations)
        self.isnot(art.locations, pres.locations)

        art.presentations += pres

        chrons.clear()
        art.save()
        self.two(chrons)
        self._chrons(art, 'create')
        self._chrons(pres, 'create')

        art = artist(art.id)
        
        self.zero(art.presentations.first.locations)
        self.zero(art.locations)

        # Add locations, save, test, reload, test
        art.locations += location.getvalid()
        art.presentations.first.locations += location.getvalid()

        chrons.clear()
        art.save()
        self.two(chrons)
        self._chrons(art.locations.first,                     'create')
        self._chrons(art.presentations.first.locations.first, 'create')

        art1 = artist(art.id)

        chrons.clear()
        self.eq(art.locations.first.id, art1.locations.first.id)
        self.eq(art.presentations.first.locations.first.id, 
                art1.presentations.first.locations.first.id)

        self.three(chrons)
        self._chrons(art1.presentations,                  'retrieve')
        self._chrons(art1.presentations.first.locations,  'retrieve')
        self._chrons(art1.locations,                      'retrieve')

    def it_loads_and_saves_multicomposite_subentity(self):
        chrons = self.chronicles

        # Create singer with concert with empty locations and
        # concerts, reload and test
        sng = singer.getvalid()
        conc = concert.getvalid()

        self.zero(sng.locations)
        self.zero(conc.locations)
        self.isnot(sng.locations, conc.locations)

        sng.concerts += conc

        chrons.clear()
        sng.save()




        B(chrons.count != 4)
        # NOTE The below line produced a failure today, but it went
        # away.  (Jul 6)
        self.four(chrons)





        self._chrons(sng, 'create')
        self._chrons(conc, 'create')
        self._chrons(sng.orm.super, 'create')
        self._chrons(conc.orm.super, 'create')

        sng = singer(sng.id)
        
        self.zero(sng.concerts.first.locations)
        self.zero(sng.locations)

        # Add locations, save, test, reload, test
        sng.locations += location.getvalid()
        sng.concerts.first.locations += location.getvalid()

        chrons.clear()
        sng.save()
        self.two(chrons)
        self._chrons(sng.locations.first, 'create')
        self._chrons(sng.concerts.first.locations.first, 'create')

        sng1 = singer(sng.id)

        chrons.clear()

        self.eq(sng.locations.first.id, sng1.locations.first.id)
        self.eq(sng.concerts.first.locations.first.id, 
                sng1.concerts.first.locations.first.id)

        self.five(chrons)
        self._chrons(sng1.concerts,                  'retrieve')
        self._chrons(sng1.concerts.first.orm.super,  'retrieve')
        self._chrons(sng1.concerts.first.locations,  'retrieve')
        self._chrons(sng1.locations,                 'retrieve')

        # NOTE Loading locations requires that we load singer's
        # superentity (artist) first because `locations` is a
        # constituent of `artist`.  Though this may seem ineffecient,
        # since the orm has what it needs to load `locations` without
        # loading `artist`, we would want the following to work for the
        # sake of predictability:
        #
        #     assert sng1.locations.artists is sng1.orm.super
        #
        self._chrons(sng1.locations.artist,          'retrieve')

        chrons.clear()
        self.is_(sng1.locations.artist, sng1.orm.super)
        self.zero(chrons)

    def it_loads_and_saves_multicomposite_subsubentity(self):
        # Create rapper with battle with empty locations and
        # battles, reload and test
        rpr = rapper.getvalid()
        btl = battle.getvalid()

        self.zero(rpr.locations)
        self.zero(btl.locations)
        self.isnot(rpr.locations, btl.locations)

        rpr.battles += btl

        with self._chrontest() as t:
            t.run(rpr.save)
            t.created(rpr)
            t.created(rpr.orm.super)
            t.created(rpr.orm.super.orm.super)
            t.created(btl)
            t.created(btl.orm.super)
            t.created(btl.orm.super.orm.super)

        rpr = rapper(rpr.id)
        
        self.zero(rpr.battles.first.locations)
        self.zero(rpr.locations)

        # Add locations, save, test, reload, test
        rpr.locations += location.getvalid()
        rpr.battles.first.locations += location.getvalid()

        with self._chrontest() as t:
            t.run(rpr.save)
            t.created(rpr.locations.first)
            t.created(rpr.battles.first.locations.first)
            
        rpr1 = rapper(rpr.id)

        def f():
            self.eq(rpr.locations.first.id, rpr1.locations.first.id)
            self.eq(rpr.battles.first.locations.first.id, 
                    rpr1.battles.first.locations.first.id)

        with self._chrontest() as t:
            t.run(f)
            t.retrieved(rpr1.orm.super)
            t.retrieved(rpr1.orm.super.orm.super)
            t.retrieved(rpr1.battles)
            t.retrieved(rpr1.battles.first.orm.super)
            t.retrieved(rpr1.battles.first.orm.super.orm.super)
            t.retrieved(rpr1.battles.first.locations)
            t.retrieved(rpr1.locations)

        # NOTE Loading locations requires that we load rapper's
        # superentity (artist) first because `locations` is a
        # constituent of `artist`.  Though this may seem ineffecient,
        # since the orm has what it needs to load `locations` without
        # loading `artist`, we would want the following to work for the
        # sake of predictability:
        #
        #     assert rpr1.locations.artists is rpr1.orm.super
        #
        def f():
            self.is_(rpr1.locations.artist, rpr1.orm.super.orm.super)

            # This doesn't work
            #self.is_(rpr1.locations.singer, rpr1.orm.super)

            self.is_(rpr1.locations.rapper, rpr1)

        with self._chrontest() as t:
            t.run(f)

    def it_receives_AttributeError_from_explicit_attributes(self):
        # An issue was discovered in the former entities.__getattr__.
        # When an explicit attribute raised an AttributeError, the
        # __getttr__ was invoked (this is the reason it gets invoke in
        # the first place) and returned the map.value of the attribute.
        # The effect was that the explict attribute never had a chance
        # to run, so we got whatever was in map.value.
        #
        # To correct this, the __getattr__ was converted to a
        # __getattribute__, and some adjustments were made
        # (map.isexplicit was added). Now, an explicit attribute can
        # raise an AttributeError and it bubble up correctly (as
        # confirmed by this test). The problem isn't likely to
        # resurface. However, this test was written just as a way to
        # ensure the issue never comes up again. The `issue` entity
        # class was created for this test because adding the
        # `raiseAttributeError` explicit attribute to other classes
        # cause an AttributeError to be raise when the the brokenrules
        # logic was invoked, which broke a lot of tests.
        #
        # Update 20090814: This issue did arise again when optimizing
        # the entity__getattribute__ method. To solve the issue, the
        # AttributeError from the explicit attritute is wrappped in
        # orm.attr.AttributeErrorWrapper then converted to a regular
        # AttributeError.

        iss = issue()
        self.expect(AttributeError, lambda: iss.raiseAttributeError)

    def it_loads_and_saves_associations(self):
        # TODO Test loading and saving deeply nested associations
        chrons = self.chronicles
        
        chrons.clear()
        art = artist.getvalid()

        self.zero(chrons)

        aa = art.artist_artifacts
        self.zero(aa)

        # Ensure property caches
        self.is_(aa, art.artist_artifacts)

        # Test loading associated collection
        facts = art.artifacts
        self.zero(facts)

        # Ensure property caches
        self.is_(facts, art.artifacts)

        # Ensure the association's associated collections is the same as the
        # associated collection of the entity.
        self.is_(art.artifacts, art.artist_artifacts.artifacts)

        self.is_(art, art.artist_artifacts.artist)

        # Save and load an association
        art                   =   artist.getvalid()
        fact                  =   artifact.getvalid()
        aa                    =   artist_artifact.getvalid()
        aa.role               =   uuid4().hex
        aa.artifact           =   fact
        art.artist_artifacts  +=  aa

        self.is_(fact,    art.artist_artifacts.first.artifact)
        self.is_(art,     art.artist_artifacts.first.artist)
        self.eq(aa.role,  art.artist_artifacts.first.role)
        self.one(art.artist_artifacts)
        self.one(art.artifacts)

        chrons.clear()
        art.save()

        self.three(chrons)
        self.three(chrons.where('create'))
        self.one(chrons.where('entity', art))
        self.one(chrons.where('entity', aa))
        self.one(chrons.where('entity', fact))

        chrons.clear()
        art1 = artist(art.id)

        self.one(chrons)
        self.one(chrons.where('retrieve'))
        self.one(chrons.where('entity', art1))

        self.one(art1.artist_artifacts)
        self.one(art1.artifacts)

        aa1 = art1.artist_artifacts.first

        self.eq(art.id,          art1.id)
        self.eq(aa.id,           aa1.id)
        self.eq(aa.role,         aa1.role)

        self.eq(aa.artist.id,    aa1.artist.id)
        self.eq(aa.artistid,     aa1.artistid)

        self.eq(aa.artifact.id,  aa1.artifact.id)
        self.eq(aa.artifactid,   aa1.artifactid)

        # Add as second artist_artifact, save, reload and test
        aa2 = artist_artifact.getvalid()
        aa2.artifact = artifact.getvalid()

        art1.artist_artifacts += aa2

        chrons.clear()
        art1.save()

        self.two(chrons)
        self.two(chrons.where('create'))
        self.one(chrons.where('entity', aa2))
        self.one(chrons.where('entity', aa2.artifact))

        art2 = artist(art1.id)
        self.eq(art1.id,         art2.id)

        aas1=art1.artist_artifacts.sorted('role')
        aas2=art2.artist_artifacts.sorted('role')

        for aa1, aa2 in zip(aas1, aas2):

            self.eq(aa1.id,           aa2.id)
            self.eq(aa1.role,         aa2.role)

            self.eq(aa1.artist.id,    aa2.artist.id)
            self.eq(aa1.artistid,     aa2.artistid)

            self.eq(aa1.artifact.id,  aa2.artifact.id)
            self.eq(aa1.artifactid,   aa2.artifactid)

        # Add a third artifact to artist's pseudo-collection.
        # Save, reload and test.
        art2.artifacts += artifact.getvalid()
        art2.artist_artifacts.last.role = uuid4().hex
        art2.artist_artifacts.last.planet = uuid4().hex
        art2.artist_artifacts.last.timespan = uuid4().hex
        self.three(art2.artifacts)
        self.three(art2.artist_artifacts)

        chrons.clear()
        art2.save()
        self.two(chrons)
        self.two(chrons.where('create'))
        self.one(chrons.where('entity', art2.artist_artifacts.third))
        self.one(chrons.where('entity', art2.artist_artifacts.third.artifact))

        art3 = artist(art2.id)

        self.three(art3.artifacts)
        self.three(art3.artist_artifacts)

        aas2 = art2.artist_artifacts.sorted('role')
        aas3 = art3.artist_artifacts.sorted('role')

        for aa2, aa3 in zip(aas2, aas3):
            self.eq(aa2.id,           aa3.id)
            self.eq(aa2.role,         aa3.role)

            self.eq(aa2.artist.id,    aa3.artist.id)
            self.eq(aa2.artistid,     aa3.artistid)

            self.eq(aa2.artifact.id,  aa3.artifact.id)
            self.eq(aa2.artifactid,   aa3.artifactid)

        # Add two components to the artifact's components collection
        comps3 = components()
        for _ in range(2):
            comps3 += component.getvalid()

        comps3.sort()
        art3.artist_artifacts.first.artifact.components += comps3.first
        art3.artifacts.first.components += comps3.second

        self.two(art3.artist_artifacts.first.artifact.components)
        self.two(art3.artifacts.first.components)

        self.is_(comps3[0], art3.artist_artifacts.first.artifact.components[0])
        self.is_(comps3[1], art3.artist_artifacts.first.artifact.components[1])
        self.is_(comps3[0], art3.artifacts.first.components[0])
        self.is_(comps3[1], art3.artifacts.first.components[1])

        chrons.clear()
        art3.save()

        self.two(chrons)
        self.two(chrons.where('create'))
        self.one(chrons.where('entity', comps3.first))
        self.one(chrons.where('entity', comps3.second))

        art4 = artist(art3.id)
        comps4 = art4.artist_artifacts.first.artifact.components.sorted()

        self.two(comps4)
        self.eq(comps4.first.id, comps3.first.id)
        self.eq(comps4.second.id, comps3.second.id)

        # This fixes an issue that came up in development: When you add valid
        # aa to art, then add a fact to art (thus adding an invalid aa to art),
        # strange things where happening with the brokenrules. 
        art = artist.getvalid()
        art.artist_artifacts += artist_artifact.getvalid()
        art.artifacts += artifact.getvalid()

        self.zero(art.artist_artifacts.first.brokenrules)
        self.two(art.artist_artifacts.second.brokenrules)
        self.two(art.brokenrules)

        # Fix broken aa
        art.artist_artifacts.second.role = uuid4().hex
        art.artist_artifacts.second.timespan = uuid4().hex

        self.zero(art.artist_artifacts.second.brokenrules)
        self.zero(art.brokenrules)

    def it_updates_associations_constituent_entity(self):
        art = artist.getvalid()
        chrons = self.chronicles

        for i in range(2):
            aa = artist_artifact.getvalid()
            aa.artifact = artifact.getvalid()
            art.artist_artifacts += aa

        art.save()

        art1 = artist(art.id)

        for fact in art1.artifacts:
            fact.title = uuid4().hex

        # Save and reload
        self.chronicles.clear()
        art1.save()

        # Ensure the four entities where updated
        self.two(chrons)
        self.two(chrons.where('update'))
        self.one(chrons.where('entity', art1.artifacts.first))
        self.one(chrons.where('entity', art1.artifacts.second))
        
        art2 = artist(art1.id)

        self.two(art1.artifacts)
        self.two(art2.artifacts)

        facts  = art. artifacts.sorted('title')
        facts1 = art1.artifacts.sorted('title')
        facts2 = art2.artifacts.sorted('title')

        for f, f2 in zip(facts, facts2):
            self.ne(f.title, f2.title)

        for f1, f2 in zip(facts1, facts2):
            self.eq(f1.title, f2.title)

        attrs = 'artifacts.first.components', \
               'artist_artifacts.first.artifact.components'

        for attr in attrs:
            comps = getattr(art2, attr)
            comps += component.getvalid()

        art2.save()

        art3 = artist(art2.id)

        for attr in attrs:
            comps = getattr(art3, attr)
            for comp in comps:
                comp.name = uuid4().hex

        chrons.clear()
        art3.save()

        self.two(chrons)
        self.two(chrons.where('update'))
        self.one(chrons.where('entity', art3.artifacts.first.components.first))
        self.one(chrons.where('entity', art3.artifacts.first.components.second))

        art4 = artist(art3.id)

        for attr in attrs:
            comps2 = getattr(art2, attr)
            comps3 = getattr(art3, attr)
            comps4 = getattr(art4, attr)

            self.two(comps2)
            self.two(comps3)
            self.two(comps4)

            for comp4 in comps4:
                for comp2 in comps2:
                    self.ne(comp2.name, comp4.name)

            for comp4 in comps4:
                for comp3 in comps3:
                    if comp4.name == comp3.name:
                        break
                else:
                    self.fail('No match within comps4 and comps3')

        # TODO Test deeply nested associations

    def it_updates_association(self):
        chrons = self.chronicles

        art = artist.getvalid()

        for i in range(2):
            aa = artist_artifact.getvalid()
            aa.artifact = artifact.getvalid()
            art.artist_artifacts += aa

        art.save()

        art1 = artist(art.id)

        for aa in art1.artist_artifacts:
            aa.role = uuid4().hex

        # Save and reload
        chrons.clear()
        art1.save()

        self.two(chrons)
        self.two(chrons.where('update'))
        self.one(chrons.where('entity', art1.artist_artifacts.first))
        self.one(chrons.where('entity', art1.artist_artifacts.first))

        art2 = artist(art1.id)

        aas  = art. artist_artifacts.sorted('role')
        aas1 = art1.artist_artifacts.sorted('role')
        aas2 = art2.artist_artifacts.sorted('role')

        for aa, aa2 in zip(aas, aas2):
            self.ne(aa.role, aa2.role)

        for aa1, aa2 in zip(aas1, aas2):
            self.eq(aa1.role, aa2.role)

        # TODO Test deeply nested associations

    def it_removes_associations(self):
        chrons = self.chronicles

        for removeby in 'pseudo-collection', 'association':
            art = artist.getvalid()

            for i in range(2):
                aa = artist_artifact.getvalid()
                aa.artifact = artifact.getvalid()
                aa.artifact.components += component.getvalid()
                art.artist_artifacts += aa
                art.artist_artifacts.last.artifact.components += component.getvalid()

            art.save()

            art = artist(art.id)
            
            self.two(art.artist_artifacts)
            self.zero(art.artist_artifacts.orm.trash)
            self.two(art.artifacts)
            self.zero(art.artifacts.orm.trash)

            if removeby == 'pseudo-collection':
                rmfact = art.artifacts.shift()
            elif removeby == 'association':
                rmfact = art.artist_artifacts.shift().artifact

            rmcomps = rmfact.components

            rmaa = art.artist_artifacts.orm.trash.first

            self.one(art.artist_artifacts)
            self.one(art.artist_artifacts.orm.trash)
            self.one(art.artifacts)
            self.one(art.artifacts.orm.trash)

            for f1, f2 in zip(art.artifacts, art.artist_artifacts.artifacts):
                self.isnot(f1, rmfact)
                self.isnot(f2, rmfact)

            chrons.clear()
            art.save()

            self.four(chrons)
            self.four(chrons.where('delete'))
            self.one(chrons.where('entity', rmcomps.first))
            self.one(chrons.where('entity', rmcomps.second))
            self.one(chrons.where('entity', rmfact))
            self.one(chrons.where('entity', art.artist_artifacts.orm.trash.first))

            art1 = artist(art.id)

            self.one(art1.artist_artifacts)
            self.zero(art1.artist_artifacts.orm.trash)
            self.one(art1.artifacts)
            self.zero(art1.artifacts.orm.trash)
                
            aas = art.artist_artifacts.sorted('role')
            aas1 = art1.artist_artifacts.sorted('role')

            for aa, aa1 in zip(aas, aas1):
                self.eq(aa.id,           aa1.id)
                self.eq(aa.role,         aa1.role)

                self.eq(aa.artist.id,    aa1.artist.id)
                self.eq(aa.artistid,     aa1.artistid)

                self.eq(aa.artifact.id,  aa1.artifact.id)
                self.eq(aa.artifactid,   aa1.artifactid)

            for fact in art1.artifacts:
                self.ne(rmfact.id, fact.id)

            self.expect(db.RecordNotFoundError, lambda: artist_artifact(rmaa.id))
            self.expect(db.RecordNotFoundError, lambda: artifact(rmfact.id))

            for comp in rmcomps:
                self.expect(db.RecordNotFoundError, lambda: component(comp.id))

        # TODO Test deeply nested associations

    def it_rollsback_save_with_broken_trash(self):
        art = artist.getvalid()
        art.presentations += presentation.getvalid()
        art.save()

        art = artist(art.id)
        art.presentations.pop()

        self.zero(art.presentations)
        self.one(art.presentations.orm.trash)

        artst     =  art.orm.persistencestate
        presssts  =  art.presentations.orm.trash.orm.persistencestates

        # Break save method
        pres = art.presentations.orm.trash.first
        save, pres._save = pres._save, lambda cur: 0/0

        self.expect(ZeroDivisionError, lambda: art.save())

        self.eq(artst,     art.orm.persistencestate)
        self.eq(presssts,  art.presentations.orm.trash.orm.persistencestates)

        # Restore unbroken save method
        pres._save = save
        trashid = art.presentations.orm.trash.first.id

        art.save()

        self.zero(artist(art.id).presentations)

        self.expect(db.RecordNotFoundError, lambda: presentation(trashid))

        # Test associations
        art = artist.getvalid()
        art.artifacts += artifact.getvalid()
        factid = art.artifacts.first.id
        aa = art.artist_artifacts.first
        aaid = aa.id
        aa.role = uuid4().hex
        aa.timespan = uuid4().hex

        art.save()

        art = artist(art.id)
        art.artifacts.pop()

        aatrash = art.artist_artifacts.orm.trash
        artst    =  art.orm.persistencestate
        aasts    =  aatrash.orm.persistencestates
        aassts   =  aatrash.first.orm.trash.orm.persistencestates
        factssts =  art.artifacts.orm.trash.orm.persistencestates

        self.zero(art.artifacts)
        self.one(art.artist_artifacts.orm.trash)
        self.one(art.artifacts.orm.trash)

        # Break save method
        fn = lambda cur, follow: 0/0
        save = art.artist_artifacts.orm.trash.first._save
        art.artist_artifacts.orm.trash.first._save = fn

        self.expect(ZeroDivisionError, lambda: art.save())

        aatrash = art.artist_artifacts.orm.trash

        self.eq(artst,     art.orm.persistencestate)
        self.eq(aasts,     aatrash.orm.persistencestates)
        self.eq(aassts,    aatrash.first.orm.trash.orm.persistencestates)
        self.eq(factssts,  art.artifacts.orm.trash.orm.persistencestates)

        self.zero(art.artifacts)
        self.one(art.artist_artifacts.orm.trash)
        self.one(art.artifacts.orm.trash)
        self.one(artist(art.id).artifacts)
        self.one(artist(art.id).artist_artifacts)

        # Restore unbroken save method
        art.artist_artifacts.orm.trash.first._save = save

        art.save()
        self.zero(artist(art.id).artifacts)
        self.zero(artist(art.id).artist_artifacts)

        self.expect(db.RecordNotFoundError, lambda: artist_artifact(aa.id))
        self.expect(db.RecordNotFoundError, lambda: artifact(factid))

    def it_raises_error_on_invalid_attributes_of_associations(self):
        art = artist()
        self.expect(AttributeError, lambda: art.artist_artifacts.artifactsX)

    def it_has_broken_rules_of_constituents(self):
        art                =   artist.getvalid()
        pres               =   presentation.getvalid()
        loc                =   location.getvalid()
        pres.locations     +=  loc
        art.presentations  +=  pres

        # Break the max-size rule on presentation.name
        pres.name = 'x' * (presentation.orm.mappings['name'].max + 1)

        self.one(art.brokenrules)
        self.broken(art, 'name', 'fits')

        # Break deeply (>2) nested constituent
        # Break the max-size rule on location.description

        loc.description = 'x' * (location.orm.mappings['description'].max + 1)
        self.two(art.brokenrules)
        self.broken(art, 'description', 'fits')

        # unbreak
        loc.description = 'x' * location.orm.mappings['description'].min
        pres.name =       'x' * presentation.orm.mappings['name'].min
        self.zero(art.brokenrules)

        # The artist_artifact created when assigning a valid artifact will
        # itself have two broken rules by default. Make sure they bubble up to
        # art.
        art.artifacts += artifact.getvalid()
        self.two(art.brokenrules)
        self.broken(art, 'timespan', 'fits')
        self.broken(art, 'role',     'fits')

        # Fix the artist_artifact
        art.artist_artifacts.first.role     = uuid4().hex
        art.artist_artifacts.first.timespan = uuid4().hex
        self.true(art.isvalid) # Ensure fixed

        # Break an artifact and ensure the brokenrule bubbles up to art
        art.artifacts.first.weight = uuid4().hex # break
        self.one(art.brokenrules)
        self.broken(art, 'weight', 'valid')

    def it_moves_constituent_to_a_different_composite(self):
        chrons = self.chronicles

        # Persist an art with a pres
        art = artist.getvalid()
        art.presentations += presentation.getvalid()
        art.presentations.last.name = uuid4().hex
        art.save()

        # Give the pres to a new artist (art1)
        art1 = artist.getvalid()
        art.presentations.give(art1.presentations)

        # Ensure the move was made in memory
        self.zero(art.presentations)
        self.one(art1.presentations)
        
        # Save art1 and ensure the pres's artistid is art1.id
        chrons.clear()
        art1.save()

        self.two(chrons)
        self.one(chrons.where('entity', art1))
        self.one(chrons.where('entity', art1.presentations.first))

        self.zero(artist(art.id).presentations)
        self.one(artist(art1.id).presentations)

        # Move deeply nested entity

        # Create and save a new location
        art1.presentations.first.locations += location.getvalid()

        art1.save()

        # Create a new presentation and give the location in art1 to the
        # locations collection of art.
        art.presentations += presentation.getvalid()
        art1.presentations.first.locations.give(art.presentations.last.locations)

        chrons.clear()
        art.save()

        self.two(chrons)

        loc = art.presentations.last.locations.last
        pres = art.presentations.last

        self.eq(chrons.where('entity', pres).first.op, 'create')
        self.eq(chrons.where('entity', loc).first.op, 'update')

        self.zero(artist(art1.id).presentations.first.locations)
        self.one(artist(art.id).presentations.first.locations)

    def it_calls_count_on_streamed_entities_after_calling_sql(self):
        # An issue occured which cause counts on streamed entities to
        # fail if the ``sql`` property was called first. This was
        # because the ``sql`` property did not clone it entities
        # collection's ``where`` object which meant the where object
        # would be permenately mutated; meeting the needs of the `sql`
        # property, but not the needs of other clients.
        #
        # The solution has been fixed, but this test will remain to
        # ensure the problem dosen't arise again.

        arts = artists(orm.stream, firstname=uuid4().hex)

        # Call `sql` to mutate `arts`'s ``where` object
        arts.orm.sql

        # We exect no exception when calling `count`
        self.expect(None, lambda: arts.count)

    def it_calls_count_on_streamed_entities(self):
        arts1 = artists()
        firstname = uuid4().hex
        for i in range(2):
            art = artist.getvalid()
            art.firstname = firstname
            arts1 += art
            art.save()

        arts = artists(orm.stream, firstname=firstname)
        self.true(arts.orm.isstreaming)
        self.eq(2, arts.count)

        # Ensure count works in nonstreaming mode
        self.false(arts1.orm.isstreaming)
        self.eq(2, arts1.count)

    def it_raises_exception_when_innerjoin_stream_entities(self):
        ''' Streaming and joins don't mix. An error should be thrown
        if an attempt to stream joins is detected. The proper way 
        to stream constituents would probably be with a getter, e.g.:

            for fact in art.get_artifacts(orm.stream):
                ...

        '''

        fns = (
            lambda:  artists(orm.stream).join(locations()),
            lambda:  artists()            &  locations(orm.stream),

            lambda:  artists(orm.stream)  &  artist_artifacts(),
            lambda:  artists()            &  artist_artifacts(orm.stream),

            lambda:  artists(orm.stream)  &  artifacts(),
            lambda:  artists()            &  artifacts(orm.stream),

            lambda:  artists() & artist_artifacts() & artifacts(orm.stream)

        )

        for fn in fns:
            self.expect(orm.invalidstream, fn)

    def it_calls__iter__on_streamed_entities(self):
        # Create a variant number of artists to test. This will help
        # discover one-off errors in the __iter__
        for i in range(4):
            # Create some artists in db with the same lastname 
            lastname = uuid4().hex
            arts = artists()
            for _ in range(i):
                arts += artist.getvalid()
                arts.last.lastname = lastname
                arts.last.save()

            # Create a streamed artists collection where lastname is the same as
            # the artists created above. Set chunksize to a very low value of 2 so
            # the test isn't too slow. Order by id so the iteration test
            # below can be preformed correctly.
            stm = orm.stream(chunksize=2)
            arts1 = artists(stm, lastname=lastname).sorted()

            # Ensure streamed collection count matches non-streamed count
            self.eq(arts1.count, arts.count)

            # Iterate over the streamed collection and compare it two the
            # non-streameed artists collections above. Do this twice so we know
            # __iter__ resets itself correctly.
            arts.sort()
            for _ in range(2):
                j = -1
                for j, art in enumerate(arts1):
                    self.eq(arts[j].id, art.id)
                    self.eq(lastname, art.lastname)

                self.eq(i, j + 1)

        # Ensure that interation works after fetching an element from a chunk
        # that comes after the first chunk.
        arts1[i - 1] # Don't remove
        self.eq(arts1.count, len(list(arts1)))

    def it_calls__getitem__on_entities(self):
        arts = artists()
        for _ in range(4):
            art = artist.getvalid()
            arts += art

        self.is_(art, arts[art.id])
        self.is_(art, arts[art])
        self.expect(IndexError, lambda: arts[uuid4()])

        arts.sort()
        arts1 = arts[:2].sorted()

        for art, art1 in zip(arts, arts1):
            self.eq(art.id, art1.id)

        art1 = arts[0]

        self.eq(arts.first.id, art1.id)

    def it_calls__getitem__on_streamed_entities(self):
        lastname = uuid4().hex
        arts = artists()
        cnt = 10
        for _ in range(cnt):
            arts += artist.getvalid()
            arts.last.lastname = lastname
            arts.last.save()

        # Test every chunk size
        for chunksize in range(1, 12):
            stm = orm.stream(chunksize=chunksize)
            arts1 = artists(stm, lastname=lastname).sorted()

            arts.sort()
            
            # Test indexing in asceding order
            for i in range(10):
                self.eq(arts[i].id, arts1[i].id)
                self.eq(arts[i].id, arts1(i).id)

            # Test indexing in descending order
            for i in range(9, 0, -1):
                self.eq(arts[i].id, arts1[i].id)

            # Test negative indexing in descending order
            for i in range(0, -10, -1):
                self.eq(arts[i].id, arts1[i].id)
                self.eq(arts[i].id, arts1(i).id)

            # Test getting chunks from different ends of the ultimate
            # result-set in an alternating fashion
            for i in range(0, -10, -1):
                self.eq(arts[i].id, arts1[i].id)
                self.eq(arts[abs(i)].id, arts1[abs(i)].id)

            # Test slices
            for i in range(10):
                for j in range(10):
                    self.eq(arts[i:j].pluck('id'), arts1[i:j].pluck('id'))

            # Negative slices (i.e., arts1[4:3]) should produce empty results
            for i in range(10):
                for j in range(i -1, 0, -1):
                    self.zero(arts1[i:j])
                for j in range(0, -10 -1):
                    # TODO Negative stops (arts1[4:-4]) are currently
                    # not implemented.
                    self.expect(NotImplementedError, lambda: arts1[i:j])

            # Ensure that __getitem__ raises IndexError if the index is out of
            # range
            self.expect(IndexError, lambda: arts1[cnt + 1])

            # Ensure that __call__ returns None if the index is out of range
            self.none(arts1(cnt + 1))

            # NOTE that UUID indexing on streams has not been
            # implemented yet.
            # TODO Test indexing by UUID, i.e.,
            # arts[id]

    def it_calls_unavailable_attr_on_streamed_entities(self):
        arts = artists(orm.stream)
        nonos = (
            'getrandom',    'getrandomized',  'where',    'clear',
            'remove',       'shift',          'pop',      'reversed',
            'reverse',      'insert',         'push',     'has',
            'unshift',      'append',         '__sub__',  'getcount',
            '__setitem__',  'getindex',       'delete'
        )

        for nono in nonos:
            self.expect(AttributeError, lambda: getattr(arts, nono))
        
    def it_calls_head_and_tail_on_streamed_entities(self):
        lastname = uuid4().hex
        arts = artists()
        for i in range(10):
            art = artist.getvalid()
            art.lastname = lastname
            arts += art
            art.save()

        arts1 = artists(orm.stream, lastname=lastname).sorted()
        arts.sort()

        self.eq(arts.head(2).pluck('id'), arts1.head(2).pluck('id'))

        arts1.tail(2)
        self.eq(arts.tail(2).pluck('id'), arts1.tail(2).pluck('id'))

    def it_calls_ordinals_on_streamed_entities(self):
        ords = ('first',            'second',             'third',
                'fourth',           'fifth',              'sixth',
                'last',             'ultimate',           'penultimate',
                'antepenultimate',  'preantepenultimate')

        lastname = uuid4().hex
        arts = artists()
        for _ in range(6):
            arts += artist.getvalid()
            arts.last.lastname = lastname
            arts.last.save()

        arts1 = artists(orm.stream, lastname=lastname).sorted()
        arts.sort()
        for ord in ords:
            self.eq(getattr(arts, ord).id, getattr(arts1, ord).id)

    def it_adds_subentity_to_superentities_collection(self):
        """ Ensure that entity objects (concert) added to collection
        propreties (concerts) are availibale in the superentities
        collection properties (presentations) before and after save.
        """

        # Add concert to concerts property and ensure it exists in
        # presentations propreties
        sng = singer.getvalid()
        sng.concerts += concert.getvalid()

        self.one(sng.concerts)
        self.one(sng.presentations)
        self.is_(sng.concerts.first, sng.presentations.first)

        # Ensure that, afer reloading, the presentations and concerts
        # properties have the same concert object.
        sng.save()

        sng1 = singer(sng.id)

        self.one(sng1.presentations)
        self.eq(sng.presentations.first.id, sng1.presentations.first.id)

        self.one(sng1.concerts)
        self.eq(sng.concerts.first.id, sng1.concerts.first.id)

        self.eq(sng.concerts.first.id, sng1.presentations.first.id)

        # Add another concert, save and reload to ensure the the above
        # logic works when using a non-new singer
        sng = sng1

        sng.concerts += concert.getvalid()

        self.two(sng.concerts)
        self.two(sng.presentations)

        for conc, pres in zip(sng.concerts, sng.presentations):
            self.eq(conc.id, pres.id)

        # Ensure that, afer reloading, the presentations and concerts
        # properties have the same concert objects
        sng.save()

        sng1 = singer(sng.id)

        self.two(sng1.presentations)
        self.two(sng1.concerts)

        sng.concerts.sort()
        sng1.concerts.sort()
        sng1.presentations.sort()

        for conc, conc1 in zip(sng.concerts, sng1.concerts):
            self.eq(conc.id, conc1.id)

        for conc, pres in zip(sng1.concerts, sng1.presentations):
            self.eq(conc.id, pres.id)

    def it_adds_subsubentity_to_superentities_collection(self):
        # Add concert to concerts property and ensure it exists in
        # presentations propreties
        rpr = rapper.getvalid()

        btl = battle.getvalid()
        rpr.battles  += btl

        conc = concert.getvalid()
        rpr.concerts += conc

        self.one(rpr.battles)
        self.two(rpr.concerts)
        self.two(rpr.presentations)
        self.type(battle,             rpr.battles.first)
        self.type(battle,             rpr.concerts.first)
        self.type(concert,            rpr.concerts.second)
        self.type(battle,             rpr.presentations.first)
        self.type(concert,            rpr.presentations.second)
        self.is_(rpr.battles.first,   rpr.concerts.first)
        self.is_(rpr.concerts.first,  rpr.presentations.first)

        # Ensure that, after reloading, the presentations and concerts
        # properties have the same concert object.
        rpr.save()

        rpr1 = rapper(rpr.id)

        self.two(rpr1.presentations)
        self.true(btl.id   in  rpr1.presentations.pluck('id'))
        self.true(conc.id  in  rpr1.presentations.pluck('id'))

        self.two(rpr1.concerts)
        self.true(btl.id   in  rpr1.concerts.pluck('id'))
        self.true(conc.id  in  rpr1.concerts.pluck('id'))

        self.one(rpr1.battles)
        self.eq(btl.id, rpr1.battles.first.id)

        # Add another battle, save and reload to ensure the the above
        # logic works when using a non-new rapper
        rpr = rpr1

        btl = battle.getvalid()
        rpr.battles += btl

        self.two(rpr.battles)
        self.three(rpr.concerts)
        self.three(rpr.presentations)

        self.true(btl  in  rpr1.battles)
        self.true(btl  in  rpr1.concerts)
        self.true(btl  in  rpr1.presentations)

        # Ensure that, afer reloading, the presentations and concerts
        # properties have the same concert objects
        rpr.save()

        rpr1 = rapper(rpr.id)

        self.two(rpr1.battles)
        self.three(rpr1.concerts)
        self.three(rpr1.presentations)

        for btl in rpr.battles:
            self.true(btl.id in rpr1.concerts.pluck('id'))
            self.true(btl.id in rpr1.presentations.pluck('id'))

        for conc in rpr.concerts:
            self.true(conc.id in rpr1.presentations.pluck('id'))

    def it_calls_sort_and_sorted_on_streamed_entities(self):
        lastname = uuid4().hex
        arts = artists()
        for _ in range(10):
            arts += artist.getvalid()
            arts.last.firstname = uuid4().hex
            arts.last.lastname = lastname
            arts.last.save()

        # Test sorting on None - which means: 'sort on id', since id is the
        # default.  Then sort on firstname
        for sort in None, 'firstname':
            for reverse in None, False, True:
                arts.sort(sort, reverse)
                arts1 = artists(orm.stream, lastname=lastname)
                arts1.sort(sort, reverse)

                # Test sort()
                for i, art1 in enumerate(arts1):
                    self.eq(arts[i].id, art1.id)

                # Test sorted()
                for i, art1 in enumerate(arts1.sorted(sort, reverse)):
                    self.eq(arts[i].id, art1.id)

    def it_calls_all(self):
        arts = artists()
        cnt = 10
        firstname = uuid4().hex
        for _ in range(cnt):
            arts += artist.getvalid()
            arts.last.firstname = firstname
            arts.last.save()

        arts1 = artists.all
        self.true(arts1.orm.isstreaming)
        self.ge(arts1.count, cnt)

        arts = [x for x in arts1 if x.firstname == firstname]
        self.count(cnt, arts)

    def it_saves_entities(self):
        chrons = self.chronicles

        arts = artists()

        for _ in range(2):
            arts += artist.getvalid()
            arts.last.firstname = uuid4().hex
            arts.last.lastname = uuid4().hex

        chrons.clear()
        arts.save()

        self.two(chrons)
        self.eq(chrons.where('entity', arts.first).first.op, 'create')
        self.eq(chrons.where('entity', arts.second).first.op, 'create')

        for art in arts:
            art1 = artist(art.id)

            for map in art.orm.mappings:
                if not isinstance(map, orm.fieldmapping):
                    continue

                self.eq(getattr(art, map.name), getattr(art1, map.name))

    def it_searches_entities(self):
        artists.orm.truncate()
        arts = artists()
        uuid = uuid4().hex
        for i in range(4):
            art = artist.getvalid()
            arts += art
            art.firstname = uuid4().hex

            if i >= 2:
                art.lastname = uuid
            else:
                art.lastname = uuid4().hex

        arts.save()

        # For clarity, this is a recipe for doing `where x in ([...])`
        # queries.  The where string has to be created manually.
        ids = sorted(arts[0:2].pluck('id'))
        where = 'id in (' + ','.join(['%s'] * len(ids)) + ')'

        self.chronicles.clear()

        arts1 = artists(where, ids)
        self.zero(self.chronicles) # defered

        with self._chrontest() as t:
            t.run(lambda: self.two(arts1))
            t.retrieved(arts1)

        arts1.sort() 
        self.eq(ids[0], arts1.first.id)
        self.eq(ids[1], arts1.second.id)
        # Test a plain where string with no args
        def fn():
            artists("firstname = '%s'" % arts.first.firstname)

        # This should throw an error because we want the user to specify an
        # empty tuple if they don't want to pass in args. This serves as a
        # reminder that they are not taking advantage of the
        # prepared/parameterized statements and may therefore be exposing
        # themselves to SQL injection attacks.
        self.expect(ValueError, fn)

        self.chronicles.clear()

        arts1 = artists("firstname = '%s'" % arts.first.firstname, ())
        self.zero(self.chronicles) # defered

        with self._chrontest() as t:
            t.run(lambda: len(arts1)) # load
            t.retrieved(arts1)

        self.one(arts1)

        self.eq(arts.first.id, arts1.first.id)

        # Test a simple 2 arg equality test
        arts1 = artists("firstname", arts.first.firstname)
        self.one(arts1)
        self.eq(arts.first.id, arts1.first.id)

        fname, lname = arts.first['firstname', 'lastname']

        # Test where literal has a UUID so introducers (_binary) are
        # tested.
        arts1 = artists("id", arts.first.id)
        self.one(arts1)
        self.eq(arts.first.id, arts1.first.id)

        # Test a where string with an args tuple
        arts1 = artists('firstname = %s', (arts.first.firstname,))
        self.one(arts1)
        self.eq(arts.first.id, arts1.first.id)

        # Test a where string with an args tuple and an args param
        where = 'firstname = %s and lastname = %s'
        arts1 = artists(where, (fname,), lname)
        self.one(arts1)
        self.eq(arts.first.id, arts1.first.id)

        # Test a where string with an args tuple and a *args element
        arts1 = artists('firstname = %s and lastname = %s', fname, lname)
        self.one(arts1)
        self.eq(arts.first.id, arts1.first.id)

        # Test a where string with one *args param
        arts1 = artists('firstname = %s', arts.first.firstname)
        self.one(arts1)
        self.eq(arts.first.id, arts1.first.id)

        # Test a where string with a multi-args tuple
        args = arts.first['firstname', 'lastname']
        arts1 = artists('firstname = %s and lastname = %s', args)
        self.one(arts1)
        self.eq(arts.first.id, arts1.first.id)

        # Test a where string with a multi-args tuple and an *arg
        # element
        args = arts.first['firstname', 'lastname']
        where = 'firstname = %s and lastname = %s and id = %s'
        arts1 = artists(where, args, arts.first.id)
        self.one(arts1)
        self.eq(arts.first.id, arts1.first.id)

        # Test a search that gets us two results
        arts1 = artists('lastname = %s', (uuid,))
        arts1 = arts1.sorted()
        self.two(arts1)
        arts2 = (arts.third + arts.fourth).sorted('id')
        self.eq(arts2.first.id, arts1.first.id)
        self.eq(arts2.second.id, arts1.second.id)

        arts1 = artists(firstname = arts.first.firstname)
        self.one(arts1)
        self.eq(arts1.first.id, arts.first.id)

        arts1 = artists(firstname = fname, lastname = lname)
        self.one(arts1)
        self.eq(arts1.first.id, arts.first.id)

        id = arts.first.id

        def fn():
            artists('id = id', firstname = fname, lastname = lname)

        # Force user to supply an empty args list
        self.expect(ValueError, fn)
        arts = artists('id = id', (), firstname = fname, lastname = lname)
        self.one(arts1)
        arts.first
        self.eq(arts1.first.id, arts.first.id)

        arts = artists('id = %s', (id,), firstname = fname, lastname = lname)
        self.one(arts1)
        self.eq(arts1.first.id, arts.first.id)

        arts = artists('id = %s', (id,), firstname = fname, lastname = lname)
        self.one(arts1)
        self.eq(arts1.first.id, arts.first.id)

    def it_searches_subentities(self):
        artists.orm.truncate()
        singers.orm.truncate()
        sngs = singers()
        uuid = uuid4().hex
        for i in range(4):
            sng = singer.getvalid()
            sngs += sng
            sng.voice = uuid4().hex
            sng.firstname = uuid4().hex

            if i >= 2:
                sng.register = uuid
            else:
                sng.register = uuid4().hex

            sng.save()

        # Test a plain where string with no args
        def fn():
            singers("firstname = '%s'" % sngs.first.firstname)

        # This should throw an error because we want the user to specify an
        # empty tuple if they don't want to pass in args. This serves as a
        # reminder that they are not taking advantage of the
        # prepared/parameterized statements and may therefore be exposing
        # themselves to SQL injection attacks.
        self.expect(ValueError, fn)

        '''
        Test searching on subentity's properties
        '''
        self.chronicles.clear()
        sngs1 = singers("voice = '%s'" % sngs.first.voice, ())
        self.zero(self.chronicles) # defered

        self.one(sngs1)

        self.eq(sngs.first.id, sngs1.first.id)

        # Only one query will have been executed
        self.one(self.chronicles)
        self._chrons(sngs1, 'retrieve')

        '''
        Test searching on a property of singer's superentity
        '''
        # Each firstname will be unique so we should should only get one result
        # from this query and it should be entity-equivalent sngs.first
        self.chronicles.clear()
        sngs1 = singers("firstname = '%s'" % sngs.first.firstname, ())
        self.zero(self.chronicles) # defered

        self.one(sngs1)
        self.one(self.chronicles) # defered
        self._chrons(sngs1, 'retrieve')

        # Calling isvalid will result in zero additional queries
        self.true(sngs1.isvalid)
        self.one(self.chronicles)

        self.eq(sngs.first.id, sngs1.first.id)

        '''
        Test searching on a property of singer and a property of singer's
        superentity (artist)
        '''
        sngs.sort()
        self.chronicles.clear()
        where = "voice = '%s' or firstname = '%s'" 
        where %= sngs.first.voice, sngs.second.firstname
        sngs1 = singers(where, ())
        self.zero(self.chronicles) # defered

        sngs1.sort()

        # Sorting will cause a load
        self.one(self.chronicles)
        self._chrons(sngs1, 'retrieve')

        # Make sure valid
        self.true(sngs1.isvalid)

        # isvalid should not cause any additional queries to be chronicled (if
        # we had not included the firstname in the above query, isvalid would
        # need to load singer's super
        self.one(self.chronicles)

        self.two(sngs1)
        self.eq(sngs.first.id, sngs1.first.id)
        self.eq(sngs.second.id, sngs1.second.id)

        # Still nothing new chronicled
        self.one(self.chronicles)

    def it_searches_subsubentities(self):
        artists.orm.truncate()
        singers.orm.truncate()
        rappers.orm.truncate()

        rprs = rappers()
        uuid = uuid4().hex
        for i in range(4):
            rpr = rapper.getvalid()
            rprs += rpr
            rpr.stagename = uuid4().hex
            rpr.voice = uuid4().hex
            rpr.firstname = uuid4().hex

            if i >= 2:
                rpr.register = uuid
            else:
                rpr.register = uuid4().hex

            rpr.save()

        # Test a plain where string with no args
        def fn():
            rappers("firstname = '%s'" % rprs.first.firstname)

        # This should throw an error because we want the user to specify
        # an empty tuple if they don't want to pass in args. This serves
        # as a reminder that they are not taking advantage of the
        # prepared/parameterized statements and may therefore be
        # exposing themselves to SQL injection attacks.
        self.expect(ValueError, fn)

        '''
        Test searching on subentity's properties
        '''

        self.chronicles.clear()
        rprs1 = rappers("voice = '%s'" % rprs.first.voice, ())
        self.zero(self.chronicles) # defered

        self.one(rprs1)

        self.eq(rprs.first.id, rprs1.first.id)

        ''' Test searching on a property of rapper's immediate
        superentity (singer)'''
        self.chronicles.clear()
        rprs1 = rappers("voice = '%s'" % rprs.first.voice, ())
        self.zero(self.chronicles) # defered

        with self._chrontest() as t:
            t.run(lambda: self.one(rprs1))
            t.retrieved(rprs1)

        self.eq(rprs.first.id, rprs1.first.id)

        self.true(rprs1.isvalid)

        '''
        Test searching on a property of rapper's superentity's
        superentity (artist)
        '''
        # Each firstname will be unique so we should should only get one
        # result from this query and it should be entity-equivalent
        # rprs.first
        self.chronicles.clear()
        rprs1 = rappers("firstname = '%s'" % rprs.first.firstname, ())
        self.zero(self.chronicles) # defered

        with self._chrontest() as t:
            # This will result in a query
            t.run(lambda: self.one(rprs1))

            # Calling isvalid will result in zero additional queries
            self.true(rprs1.isvalid)
            t.retrieved(rprs1)

        self.eq(rprs.first.id, rprs1.first.id)

        '''
        Test searching on a property of singer and a property of
        rapper's superentity (artist)
        '''
        rprs.sort()

        wh = "voice = '%s' or firstname = '%s'" 
        wh %= rprs.first.voice, rprs.second.firstname
        rprs1 = rappers(wh, ())
        with self._chrontest() as t:
            t.run(lambda: self.two(rprs1))

            t.retrieved(rprs1)

        # Make sure valid

        with self._chrontest() as t:
            t.run(lambda: self.true(rprs1.isvalid))
            # isvalid should not cause any additional queries to be
            # chronicled (if we had not included the firstname in the
            # above query, isvalid would need to load rapper's super

            self.two(rprs1)
            self.eq(rprs.first.id, rprs1.first.id)
            self.eq(rprs.second.id, rprs1.second.id)

            # Still nothing new chronicled

        wh = "voice = '%s'" 
        wh %= rprs.first.voice
        rprs1 = rappers(wh, ())

        with self._chrontest() as t:
            t.run(lambda: self.one(rprs1))
            t.retrieved(rprs1)

        self.true(rprs1.isvalid)
        self.eq(rprs.first.id, rprs1.first.id)

        wh = "nice = '%s' or voice = '%s'" 
        wh %= rprs.first.nice, rprs.second.voice
        rprs1 = rappers(wh, ())

        with self._chrontest() as t:
            t.run(lambda: self.two(rprs1))
            t.retrieved(rprs1)

        self.true(rprs1.isvalid)

        rprs1.sort()
        self.eq(rprs.first.id, rprs1.first.id)
        self.eq(rprs.second.id, rprs1.second.id)

        wh = "nice = '%s'" 
        wh %= rprs.first.nice
        rprs1 = rappers(wh, ())

        with self._chrontest() as t:
            t.run(lambda: self.one(rprs1))
            t.retrieved(rprs1)

        self.true(rprs1.isvalid)

        self.eq(rprs.first.id, rprs1.first.id)

    def it_searches_entities_using_fulltext_index(self):
        for e in artists, artifacts, concerts:
            e.orm.truncate()

        arts, facts = artists(), artifacts()
        for i in range(2):
            art = artist.getvalid()
            fact = artifact.getvalid()
            if i:
                art.bio = fact.title = 'one two three %s four five six'
                fact.description = 'seven eight %s nine ten'
            else:
                art.bio = la2gr('one two three four five six')
                fact.title = art.bio
                fact.description = la2gr('seven eight nine ten')

            arts += art; facts += fact

        arts.save(facts)

        # Search string of 'zero' should produce zero results
        arts1 = artists('match(bio) against (%s)', 'zero')
        self.zero(arts1)

        # Search for the word "three"
        arts1 = artists('match(bio) against (%s)', 'three')
        self.one(arts1)
        self.eq(arts.second.id, arts1.first.id)

        # Search for the Greek transliteration of "three". We want to ensure
        # there is no issue with Unicode characters.
        arts1 = artists('match(bio) against (%s)', la2gr('three'))
        self.one(arts1)
        self.eq(arts.first.id, arts1.first.id)

        # Test "composite" full-text search

        # Search string of 'zero' should produce zero results
        arts1 = artifacts('match(title, description) against(%s)', 'zero')
        self.zero(arts1)

        # Search for the word "three". "three" is in 'title'.
        arts1 = artifacts('match(title, description) against(%s)', 'three')
        self.one(arts1)
        self.eq(facts.second.id, arts1.first.id)

        # Search for eight. "eight" is in 'description'.
        arts1 = artifacts('match(title, description) against(%s)', 'eight')
        self.one(arts1)
        self.eq(facts.second.id, arts1.first.id)

        # Search for the Greek transliteration of "three". It is in 'title';
        arts1 = artifacts('match(title, description) against(%s)', la2gr('three'))
        self.one(arts1)
        self.eq(facts.first.id, arts1.first.id)

        # Search for the Greek transliteration of "eight". It is in 'description'.
        arts1 = artifacts('match(title, description) against(%s)', la2gr('eight'))
        self.one(arts1)
        self.eq(facts.first.id, arts1.first.id)

        # Search for literal placeholders string (i.e., '%s')
        arts1 = artists("match(bio) against (%s)", 'three %s')
        self.one(arts1)
        self.eq(arts.second.id, arts1.first.id)

        # NOTE MySQL doesn't return a match here, even though there is a
        # literal '%s' in the artist.bio field
        arts1 = artists("match(bio) against ('%s')", ())
        self.zero(arts1)

        arts1 = artists("match(bio) against ('three %s')", ())
        self.one(arts1)
        self.eq(arts.second.id, arts1.first.id)

        arts1 = artists("match(bio) against ('%x')", ())
        self.zero(arts1)

    def it_searches_subentities_using_fulltext_index(self):
        artists.orm.truncate()
        singers.orm.truncate()
        rappers.orm.truncate()
        concerts.orm.truncate()

        sngs, concs = artists(), concerts()
        for i in range(2):
            sng = singer.getvalid()
            conc = concert.getvalid()
            if i:
                sng.bio = conc.title = 'one two three four five six'
                conc.description1 = 'seven eight nine ten'
            else:
                sng.bio = conc.title = la2gr('one two three four five six')
                conc.description1 = la2gr('seven eight nine ten')

            sngs += sng; concs += conc

        sngs.save(concs)

        # Search string of 'zero' should produce zero results
        sngs1 = singers("match(bio) against (%s)", 'zero')
        self.zero(sngs1)

        # Search string of 'zero' should produce zero results
        sngs1 = singers("match(bio) against ('zero')", ())
        self.zero(sngs1)

        # Search for the word "three"
        sngs1 = singers("match(bio) against (%s)", 'three')
        self.one(sngs1)
        self.eq(sngs.second.id, sngs1.first.id)

        # Search for the word "three"
        sngs1 = singers("match(bio) against ('three')", ())
        self.one(sngs1)
        self.eq(sngs.second.id, sngs1.first.id)

        # Search for the Greek transliteration of "three". We want to ensure
        # there is no issue with Unicode characters.
        sngs1 = singers("match(bio) against (%s)", la2gr('three'))
        self.one(sngs1)
        self.eq(sngs.first.id, sngs1.first.id)

        l = lambda: concerts("match(title, xxx) against(%s)", 'zero')
        self.expect(orm.invalidcolumn, l)

        # Test "composite" full-text search

        # Search string of 'zero' should produce zero results
        concs1 = concerts("match(title, description1) against(%s)", 'zero')
        self.zero(concs1)
        
        concs1 = concerts("match(title, description1) against('zero')", ())
        self.zero(concs1)

        # Search for the word "three". "three" is in 'title'.
        concs1 = concerts("match(title, description1) against(%s)", 'three')
        self.one(concs1)
        self.eq(concs.second.id, concs1.first.id)

        # Search for the word "three". "three" is in 'title'.
        concs1 = concerts("match(title, description1) against('three')", ())
        self.one(concs1)
        self.eq(concs.second.id, concs1.first.id)

        # Search for eight. "eight" is in 'description1'.
        concs1 = concerts("match(title, description1) against(%s)", 'eight')
        self.one(concs1)
        self.eq(concs.second.id, concs1.first.id)

        # Search for eight. "eight" is in 'description1'.
        concs1 = concerts("match(title, description1) against('eight')", ())
        self.one(concs1)
        self.eq(concs.second.id, concs1.first.id)

        # Search for the Greek transliteration of "three". It is in 'title';
        wh = "match(title, description1) against('%s')" % la2gr('three')
        concs1 = concerts(wh, ())
        self.one(concs1)
        self.eq(concs.first.id, concs1.first.id)

        # Search for the Greek transliteration of "eight". It is in 'description1'
        concs1 = concerts("match(title, description1) against(%s)", la2gr('eight'))
        self.one(concs1)
        self.eq(concs.first.id, concs1.first.id)

        # Search for the Greek transliteration of "eight". It is in 'description1'
        wh = "match(title, description1) against('%s')" % la2gr('eight')
        concs1 = concerts(wh, ())
        self.one(concs1)
        self.eq(concs.first.id, concs1.first.id)

    def it_searches_subsubentities_using_fulltext_index(self):
        artists.orm.truncate()
        singers.orm.truncate()
        rappers.orm.truncate()

        rprs, btls = rappers(), battles()
        for i in range(2):
            rpr = rapper.getvalid()
            btl = battle.getvalid()
            if i:
                rpr.bio = btl.title = 'one two three four five six'
                btl.description1 = 'seven eight nine ten'
            else:
                rpr.bio = btl.title = la2gr('one two three four five six')
                btl.description1 = la2gr('seven eight nine ten')

            rprs += rpr; btls += btl

        rprs.save(btls)

        # Search string of 'zero' should produce zero results
        rprs1 = rappers("match(bio) against (%s)", 'zero')
        self.zero(rprs1)

        # Search string of 'zero' should produce zero results
        rprs1 = rappers("match(bio) against ('zero')", ())
        self.zero(rprs1)

        # Search for the word "three"
        rprs1 = rappers("match(bio) against (%s)", 'three')
        self.one(rprs1)

        # Search for the word "three"
        rprs1 = rappers("match(bio) against ('three')", ())
        self.one(rprs1)
        self.eq(rprs.second.id, rprs1.first.id)

        # Search for the Greek transliteration of "three". We want to
        # ensure there is no issue with Unicode characters.
        rprs1 = rappers("match(bio) against (%s)", la2gr('three'))
        self.one(rprs1)
        self.eq(rprs.first.id, rprs1.first.id)

        l = lambda: battles("match(title, xxx) against(%s)", 'zero')
        self.expect(orm.invalidcolumn, l)

        # Test "composite" full-text search

        # Search string of 'zero' should produce zero results
        btls1 = battles("match(title, description1) against(%s)", 'zero')
        self.zero(btls1)
        
        btls1 = battles("match(title, description1) against('zero')", ())
        self.zero(btls1)

        # Search for the word "three". "three" is in 'title'.
        btls1 = battles("match(title, description1) against(%s)", 'three')
        self.one(btls1)
        self.eq(btls.second.id, btls1.first.id)

        # Search for the word "three". "three" is in 'title'.
        btls1 = battles("match(title, description1) against('three')", ())
        self.one(btls1)
        self.eq(btls.second.id, btls1.first.id)

        # Search for eight. "eight" is in 'description1'.
        btls1 = battles("match(title, description1) against(%s)", 'eight')
        self.one(btls1)
        self.eq(btls.second.id, btls1.first.id)

        # Search for eight. "eight" is in 'description1'.
        btls1 = battles("match(title, description1) against('eight')", ())
        self.one(btls1)
        self.eq(btls.second.id, btls1.first.id)

        # Search for the Greek transliteration of "three". It is in 'title';
        wh = "match(title, description1) against('%s')" % la2gr('three')
        btls1 = battles(wh, ())
        self.one(btls1)
        self.eq(btls.first.id, btls1.first.id)

        # Search for the Greek transliteration of "eight". It is in 'description1'
        btls1 = battles("match(title, description1) against(%s)", la2gr('eight'))
        self.one(btls1)
        self.eq(btls.first.id, btls1.first.id)

        # Search for the Greek transliteration of "eight". It is in 'description1'
        wh = "match(title, description1) against('%s')" % la2gr('eight')
        btls1 = battles(wh, ())
        self.one(btls1)
        self.eq(btls.first.id, btls1.first.id)
        
    def it_rollsback_save_of_entities(self):
        # Create two artists
        arts = artists()

        for _ in range(2):
            arts += artist.getvalid()
            arts.last.firstname = uuid4().hex
            arts.last.lastname = uuid4().hex

        arts.save()

        # First, break the save method so a rollback occurs, and test
        # the rollback. Second, fix the save method and ensure success.
        for i in range(2):
            if i:
                # Restore original save method
                arts.second._save = save

                # Update property 
                arts.first.firstname = new = uuid4().hex
                arts.save()
                self.eq(new, artist(arts.first.id).firstname)
            else:
                # Update property
                old, arts.first.firstname \
                    = arts.first.firstname, uuid4().hex

                # Break save method
                save, arts.second._save = arts.second._save, lambda x: 0/0

                self.expect(ZeroDivisionError, lambda: arts.save())
                self.eq(old, artist(arts.first.id).firstname)

    def it_deletes_entities(self):
        # Create two artists
        arts = artists()

        for _ in range(2):
            arts += artist.getvalid()
        
        arts.save()

        art = arts.shift()
        self.one(arts)
        self.one(arts.orm.trash)

        self.chronicles.clear()
        arts.save()
        self.one(self.chronicles)
        self._chrons(art, 'delete')

        self.expect(db.RecordNotFoundError, lambda: artist(art.id))
        
        # Ensure the remaining artist still exists in database
        self.expect(None, lambda: artist(arts.first.id))

    def it_doesnt_needlessly_save_entitity(self):
        chrons = self.chronicles

        art = artist()

        art.firstname = uuid4().hex
        art.lastname = uuid4().hex
        art.ssn = '1' * 11
        art.phone = '1' * 7
        art.password  = bytes([randint(0, 255) for _ in range(32)])
        art.email = 'username@domain.tld'

        for i in range(2):
            chrons.clear()
            
            with self._chrontest() as t:
                t.run(art.save)
                if i == 0:
                    t.created(art)
                elif i == 1:
                    # Nothing created second time
                    pass

        # Dirty art and save. Ensure the object was actually saved if needed
        art.firstname = uuid4().hex
        for i in range(2):
            chrons.clear()
            art.save()

            if i == 0:
                self.one(chrons)
                self.eq(chrons.where('entity', art).first.op, 'update')
            elif i == 1:
                self.zero(chrons)

        # Test constituents
        art.presentations += presentation.getvalid()
        
        for i in range(2):
            chrons.clear()
            art.save()

            if i == 0:
                self.one(chrons)
                pres = art.presentations.last
                self.eq(chrons.where('entity', pres).first.op, 'create')
            elif i == 1:
                self.zero(chrons)

        # Test deeply-nested (>2) constituents
        art.presentations.last.locations += location.getvalid()

        for i in range(2):

            chrons.clear()
            art.save()

            if i == 0:
                self.one(chrons)
                loc = art.presentations.last.locations.last
                self.eq(chrons.where('entity', loc).first.op, 'create')
            elif i == 1:
                self.zero(chrons)

    def entity_contains_reference_to_composite(self):
        chrons = self.chronicles

        art = artist.getvalid()

        for _ in range(2):
            art.presentations += presentation.getvalid()

            for _ in range(2):
                art.presentations.last.locations += location.getvalid()

        art.save()

        for i, art in enumerate((art, artist(art.id))):
            for pres in art.presentations:
                chrons.clear()
                    
                self.is_(art, pres.artist)
                self.zero(chrons)

                for loc in pres.locations:
                    chrons.clear()
                    self.is_(pres, loc.presentation)
                    self.zero(chrons)

    def it_loads_and_saves_entities_constituents(self):
        chrons = self.chronicles

        # Ensure that a new composite has a constituent object with zero
        # elements
        art = artist.getvalid()
        self.zero(art.presentations)

        # Ensure a saved composite object with zero elements in a
        # constituent
        # collection loads with zero the constituent collection containing zero
        # elements.
        art.firstname = uuid4().hex
        art.lastname = uuid4().hex

        self.is_(art.presentations.artist, art)
        self.zero(art.presentations)

        art.save()

        self.is_(art.presentations.artist, art)
        self.zero(art.presentations)

        art = artist(art.id)
        self.zero(art.presentations)
        self.is_(art.presentations.artist, art)

        # Create some presentations within artist, save artist, reload and test
        art = artist.getvalid()
        art.presentations += presentation.getvalid()
        art.presentations += presentation.getvalid()

        for pres in art.presentations:
            pres.name = uuid4().hex

        chrons.clear()
        art.save()

        self.three(chrons)
        press = art.presentations
        self.eq(chrons.where('entity', art).first.op, 'create')
        self.eq(chrons.where('entity', press.first).first.op, 'create')
        self.eq(chrons.where('entity', press.second).first.op, 'create')

        art1 = artist(art.id)

        chrons.clear()

        press = art1.presentations
        art.presentations.sort()

        self.one(chrons)

        self.eq(chrons.where('entity', press).first.op, 'retrieve')
        art1.presentations.sort()
        for pres, pres1 in zip(art.presentations, art1.presentations):
            self.eq((False, False, False), pres.orm.persistencestate)
            self.eq((False, False, False), pres1.orm.persistencestate)
            for map in pres.orm.mappings:
                if isinstance(map, orm.fieldmapping):
                    self.eq(getattr(pres, map.name), getattr(pres1, map.name))
            
            self.is_(art1, pres1.artist)

        # Create some locations with the presentations, save artist, reload and
        # test
        for pres in art.presentations:
            for _ in range(2):
                pres.locations += location.getvalid()

        chrons.clear()
        art.save()

        self.four(chrons)

        locs = art.presentations.first.locations
        self.eq(chrons.where('entity', locs.first).first.op, 'create')
        self.eq(chrons.where('entity', locs.second).first.op, 'create')

        locs = art.presentations.second.locations
        self.eq(chrons.where('entity', locs.first).first.op, 'create')
        self.eq(chrons.where('entity', locs.second).first.op, 'create')

        art1 = artist(art.id)
        self.two(art1.presentations)

        art.presentations.sort()
        art1.presentations.sort()
        for pres, pres1 in zip(art.presentations, art1.presentations):

            pres.locations.sort()

            chrons.clear()
            pres1.locations.sort()

            self.one(chrons)
            locs = pres1.locations

            self.eq(chrons.where('entity', locs).first.op, 'retrieve')

            for loc, loc1 in zip(pres.locations, pres1.locations):
                for map in loc.orm.mappings:
                    if isinstance(map, orm.fieldmapping):
                        v, v1 = getattr(loc, map.name), getattr(loc1, map.name)
                        self.eq(v, v1)
            
                self.is_(pres1, loc1.presentation)

        # Test appending a collection of constituents to a constituents
        # collection. Save, reload and test.
        art = artist.getvalid()
        press = presentations()

        for _ in range(2):
            press += presentation.getvalid()

        art.presentations += press

        for i in range(2):
            if i:
                art.save()
                art = artist(art.id)

            self.eq(press.count, art.presentations.count)

            for pres in art.presentations:
                self.is_(art, pres.artist)

    def it_updates_entity_constituents_properties(self):
        chrons = self.chronicles
        art = artist.getvalid()

        for _ in range(2):
            art.presentations += presentation.getvalid()
            art.presentations.last.name = uuid4().hex

            for _ in range(2):
                art.presentations.last.locations += location.getvalid()
                art.presentations.last.locations.last.description = uuid4().hex

        art.save()

        art1 = artist(art.id)
        for pres in art1.presentations:
            pres.name = uuid4().hex
            
            for loc in pres.locations:
                loc.description = uuid4().hex

        chrons.clear()
        art1.save()
        self.six(chrons)
        for pres in art1.presentations:
            self.eq(chrons.where('entity', pres).first.op, 'update')
            for loc in pres.locations:
                self.eq(chrons.where('entity', loc).first.op, 'update')
            

        art2 = artist(art.id)
        press = (art.presentations, art1.presentations, art2.presentations)
        for pres, pres1, pres2 in zip(*press):
            # Make sure the properties were changed
            self.ne(getattr(pres2, 'name'), getattr(pres,  'name'))

            # Make user art1.presentations props match those of art2
            self.eq(getattr(pres2, 'name'), getattr(pres1, 'name'))

            locs = pres.locations, pres1.locations, pres2.locations
            for loc, loc1, loc2 in zip(*locs):
                # Make sure the properties were changed
                self.ne(getattr(loc2, 'description'), getattr(loc,  'description'))

                # Make user art1 locations props match those of art2
                self.eq(getattr(loc2, 'description'), getattr(loc1, 'description'))

    def it_saves_and_loads_entity_constituent(self):
        chrons = self.chronicles

        # Make sure the constituent is None for new composites
        pres = presentation.getvalid()

        chrons.clear()
        self.none(pres.artist)
        self.zero(chrons)

        self.zero(pres.brokenrules)
        
        # Test setting an entity constituent then test saving and loading
        art = artist.getvalid()
        pres.artist = art
        self.is_(art, pres.artist)

        with self._chrontest() as t:
            t.run(pres.save)
            t.created(art)
            t.created(pres)

        # Load by artist then lazy-load presentations to test
        art1 = artist(pres.artist.id)
        self.one(art1.presentations)
        self.eq(art1.presentations.first.id, pres.id)

        # Load by presentation and lazy-load artist to test
        pres1 = presentation(pres.id)

        chrons.clear()
        self.eq(pres1.artist.id, pres.artist.id)
        self.one(chrons)
        self.eq(chrons.where('entity', pres1.artist).first.op,  'retrieve')

        art1 = artist.getvalid()
        pres1.artist = art1

        chrons.clear()
        pres1.save()

        self.two(chrons)
        self.eq(chrons.where('entity', art1).first.op,  'create')
        self.eq(chrons.where('entity', pres1).first.op, 'update')

        pres2 = presentation(pres1.id)
        self.eq(art1.id, pres2.artist.id)
        self.ne(art1.id, art.id)

        # Test deeply-nested (>2)
        # Set entity constuents, save, load, test
       
        loc = location.getvalid()
        self.none(loc.presentation)

        loc.presentation = pres = presentation.getvalid()
        self.is_(pres, loc.presentation)

        chrons.clear()
        self.none(loc.presentation.artist)
        self.zero(chrons)

        loc.presentation.artist = art = artist.getvalid()
        self.is_(art, loc.presentation.artist)

        loc.save()

        self.three(chrons)
        self.eq(chrons.where('entity',  loc).first.op,               'create')
        self.eq(chrons.where('entity',  loc.presentation).first.op,  'create')
        self.eq(chrons.where('entity',  art).first.op,               'create')

        chrons.clear()
        loc1 = location(loc.id)
        pres1 = loc1.presentation

        self.eq(loc.id, loc1.id)
        self.eq(loc.presentation.id, loc1.presentation.id)
        self.eq(loc.presentation.artist.id, loc1.presentation.artist.id)

        self.three(chrons)
        self.eq(chrons.where('entity',  loc1).first.op,          'retrieve')
        self.eq(chrons.where('entity',  pres1).first.op,         'retrieve')
        self.eq(chrons.where('entity',  pres1.artist).first.op,  'retrieve')

        # Change the artist
        loc1.presentation.artist = art1 = artist.getvalid()

        chrons.clear()
        loc1.save()

        self.two(chrons)
        pres1 = loc1.presentation

        self.eq(chrons.where('entity',  pres1).first.op,  'update')
        self.eq(chrons.where('entity',  art1).first.op,   'create')

        loc2 = location(loc1.id)
        self.eq(loc1.presentation.artist.id, loc2.presentation.artist.id)
        self.ne(art.id, loc2.presentation.artist.id)

        # NOTE Going up the graph, mutating attributes and persisting
        # lower in the graph won't work because of the problem of
        # infinite recursion.  The below tests demonstrate this.

        # Assign a new name
        name = uuid4().hex
        loc2.presentation.artist.presentations.first.name = name

        # The presentation objects here aren't the same reference so they will
        # have different states.
        self.ne(loc2.presentation.name, name)

        chrons.clear()
        loc2.save()

        self.zero(chrons)

        loc2 = location(loc2.id)

        self.one(chrons)
        self.eq(chrons.where('entity',  loc2).first.op,   'retrieve')

        # The above save() didn't save the new artist's presentation collection
        # so the new name will not be present in the reloaded presentation
        # object.
        self.ne(loc2.presentation.name, name)
        self.ne(loc2.presentation.artist.presentations.first.name, name)

    def entity_constituents_break_entity(self):
        pres = presentation.getvalid()
        pres.artist = artist.getvalid()

        # Break rule that art.networth should be an int
        pres.artist.networth = str() # Break

        self.one(pres.brokenrules)
        self.broken(pres, 'networth', 'valid')

        pres.artist.networth = int() # Unbreak
        self.zero(pres.brokenrules)

        loc = location.getvalid()
        loc.description = 'x' * 256 # break
        loc.presentation = presentation.getvalid()
        loc.presentation.name = 'x' * 256 # break
        loc.presentation.artist = artist.getvalid()
        loc.presentation.artist.firstname = 'x' * 256 # break

        self.three(loc.brokenrules)
        for prop in 'description', 'name', 'firstname':
            self.broken(loc, prop, 'fits')

    def it_rollsback_save_of_entity_with_broken_constituents(self):
        art = artist.getvalid()

        art.presentations += presentation.getvalid()
        art.presentations.last.name = uuid4().hex

        art.presentations += presentation.getvalid()
        art.presentations.last.name = uuid4().hex

        # Cause the last presentation's invocation of save() to raise an
        # Exception to cause a rollback
        art.presentations.last._save = lambda cur, followentitymapping: 1/0

        # Save expecting the ZeroDivisionError
        self.expect(ZeroDivisionError, lambda: art.save())

        # Ensure state of art was restored to original
        self.true(art.orm.isnew)
        self.false(art.orm.isdirty)
        self.false(art.orm.ismarkedfordeletion)

        # Ensure artist wasn't saved
        self.expect(db.RecordNotFoundError, lambda: artist(art.id))

        # For each presentations, ensure state was not modified and no presentation 
        # object was saved.
        for pres in art.presentations:
            self.true(pres.orm.isnew)
            self.false(pres.orm.isdirty)
            self.false(pres.orm.ismarkedfordeletion)
            self.expect(db.RecordNotFoundError, lambda: presentation(pres.id))

    def it_calls_entities(self):
        
        # Creating a single orm.entity with no collection should produce an
        # AttributeError
        def fn():
            class single(orm.entity):
                firstname = orm.fieldmapping(str)

        self.expect(AttributeError, fn)

        # Test explicit detection of orm.entities 
        class bacteria(orm.entities):
            pass

        class bacterium(orm.entity):
            entities = bacteria
            name = orm.fieldmapping(str)

        b = bacterium()
        self.is_(b.orm.entities, bacteria)
        self.eq(b.orm.table, 'bacteria')

        # Test implicit entities detection based on naive pluralisation
        art = artist()
        self.is_(art.orm.entities, artists)
        self.eq(art.orm.table, 'artists')

        # Test implicit entities detection of entities subclass based on naive
        # pluralisation
        s = singer()
        self.is_(s.orm.entities, singers)
        self.eq(s.orm.table, 'singers')

    def it_calls_id_on_entity(self):
        art = artist.getvalid()

        self.true(hasattr(art, 'id'))
        self.type(uuid.UUID, art.id)
        self.zero(art.brokenrules)

    def it_calls_custom_methods_on_entity(self):
        art = artist()

        # Ensure artist.__init__ got called. It will default "lifeform" to
        # 'organic'
        self.eq('organic', art.lifeform)

        art.presentations += presentation()
        art.locations += location()

        self.one(art.presentations)
        self.one(art.locations)

        # Ensure the custom method clear() is called and successfully clears
        # the presentations and locations collections.
        art.clear()

        self.zero(art.presentations)
        self.zero(art.locations)

        # Test a custom @property
        self.false(art.processing)
        art.processing = True
        self.true(art.processing)

        # Test it calls fields
        uuid = uuid4().hex
        art.test = uuid
        self.eq(uuid, art.test)

    def it_calls_custom_methods_on_subentity(self):
        sng = singer()

        # Ensure artist.__init__ got called. It will default "lifeform"
        # to 'organic'
        self.eq('organic', sng.lifeform)

        sng.concerts += concert()
        sng.locations += location()

        self.one(sng.concerts)
        self.one(sng.locations)

        # Ensure the custom method clear() is called and successfully clears
        # the presentations and locations collections.
        sng.clear()

        self.zero(sng.concerts)
        self.zero(sng.locations)

        # Test a custom @property
        self.false(sng.transmitting)
        sng.transmitting = True
        self.true(sng.transmitting)

        # Test a custom @property in super class 
        self.false(sng.processing)
        sng.processing = True
        self.true(sng.processing)

        # Test it calls fields
        uuid = uuid4().hex
        sng.test = uuid
        self.eq(uuid, sng.test)

    def it_calls_custom_methods_on_subsubentity(self):
        # TODO Currently, concerts and locations entities collections
        # are being added to rpr. Once we have a subentity of concerts
        # that belongs to rapper, we should append one of those here as
        # well. Then we should add a clear() override (i.e., an actual
        # custom method to test) to rapper that will clear the new
        # subentity of concerts as well as calling the super()'s clear()
        # method which will clear the concerts and locations.
        rpr = rapper()

        # Ensure artist.__init__ got called. It will default "lifeform"
        # to 'organic'
        self.eq('organic', rpr.lifeform)

        # Ensure rapper.__init__ got called. It will default "nice"
        # to 10
        self.eq(10, rpr.nice)

        rpr.concerts += concert()
        rpr.locations += location()

        self.one(rpr.concerts)
        self.one(rpr.locations)

        # Ensure the custom method clear() is called and successfully
        # clears the presentations and locations collections.
        rpr.clear()

        self.zero(rpr.concerts)
        self.zero(rpr.locations)

        # Test a custom @property
        self.false(rpr.elevating)
        rpr.elevating = True
        self.true(rpr.elevating)

        # Test a custom @property on super entity (singer)
        self.false(rpr.transmitting)
        rpr.transmitting = True
        self.true(rpr.transmitting)

        # Test a custom @property in super's super entity (artist)
        self.false(rpr.processing)
        rpr.processing = True
        self.true(rpr.processing)

        # Test it calls fields
        uuid = uuid4().hex
        rpr.test = uuid
        self.eq(uuid, rpr.test)

    def it_calls__getitem__on_entity(self):
        art = artist()
        art.firstname = uuid4().hex
        art.lastname = uuid4().hex
        art.phone = '1' * 7

        self.eq(art['firstname'], art.firstname)

        expected = art.firstname, art.lastname
        actual = art['firstname', 'lastname']

        self.eq(expected, actual)
        self.expect(IndexError, lambda: art['idontexist'])

        actual = art['presentations', 'locations']
        expected = art.presentations, art.locations

        actual = art['phone']
        expected = art.phone

        self.eq(actual, expected)

    def it_calls__getitem__on_subentity(self):
        sng = singer()
        sng.firstname = uuid4().hex
        sng.lastname = uuid4().hex
        sng.voice = uuid4().hex
        sng.register = 'laryngealization'

        self.eq(sng['firstname'], sng.firstname)

        names = sng.firstname, sng.lastname
        self.eq(names, sng['firstname', 'lastname'])
        self.expect(IndexError, lambda: sng['idontexist'])

        actual = sng['presentations', 'locations']
        expected = sng.presentations, sng.locations

        self.eq(actual, expected)

        actual = sng['voice', 'concerts']
        expected = sng.voice, sng.concerts

        self.eq(actual, expected)

        actual = sng['phone']
        expected = sng.phone

        self.eq(actual, expected)

    def it_calls__getitem__on_subsubentity(self):
        rpr = rapper()
        rpr.firstname = uuid4().hex
        rpr.lastname = uuid4().hex
        rpr.voice = uuid4().hex
        rpr.register = 'laryngealization'

        self.eq(rpr['firstname'], rpr.firstname)

        names = rpr.firstname, rpr.lastname
        self.eq(names, rpr['firstname', 'lastname'])
        self.expect(IndexError, lambda: rpr['idontexist'])

        actual = rpr['presentations', 'locations']
        expected = rpr.presentations, rpr.locations

        self.eq(actual, expected)

        actual = rpr['voice', 'concerts']
        expected = rpr.voice, rpr.concerts

        self.eq(actual, expected)

        actual = rpr['phone']
        expected = rpr.phone

        self.eq(actual, expected)

        actual = rpr['nice', 'stagename']
        expected = rpr.nice, rpr.stagename

        self.eq(actual, expected)

        actual = rpr['nice']
        expected = rpr.nice

        self.eq(actual, expected)

    def it_calls__getitem__on_association(self):
        art = artist()
        art.artist_artifacts += artist_artifact()
        aa = art.artist_artifacts.first

        self.eq(aa['role'], aa.role)

        expected = aa.role, aa.planet
        actual = aa['role', 'planet']

        self.eq(expected, actual)
        self.expect(IndexError, lambda: aa['idontexist'])

        actual = aa['artist', 'artifact']
        expected = aa.artist, aa.artifact

        self.eq(actual, expected)

        aa.timespan = '1/1/2001 3/3/2001'
        actual = aa['timespan', 'processing']
        expected = aa.timespan, aa.processing

        self.eq(actual, expected)

    def it_doesnt_raise_exception_on_invalid_attr_values(self):
        # For each type of attribute, ensure that any invalid value can be
        # given. The invalid value should cause a brokenrule but should never
        # result in a type coercion exception on assignment or retrieval

        # datetime
        art = artist.getvalid()
        art.dob = uuid4().hex       
        self.expect(None, lambda: art.dob) 
        self.one(art.brokenrules)
        self.broken(art, 'dob', 'valid')

        # int
        art = artist.getvalid()
        art.weight = uuid4().hex       
        self.expect(None, lambda: art.weight) 
        self.one(art.brokenrules)
        self.broken(art, 'weight', 'valid')

        # float
        comp = component.getvalid()
        comp.height = uuid4().bytes       
        self.expect(None, lambda: comp.height) 
        self.one(comp.brokenrules)
        self.broken(comp, 'height', 'valid')

        # decimal
        fact = artifact.getvalid()
        fact.price = uuid4().bytes       
        self.expect(None, lambda: fact.price) 
        self.one(fact.brokenrules)
        self.broken(fact, 'price', 'valid')

        # bytes
        comp = component.getvalid()
        comp.digest = uuid4().hex       
        self.expect(None, lambda: comp.digest) 
        self.one(comp.brokenrules)
        self.broken(comp, 'digest', 'valid')

        # constituent entity
        art = artist.getvalid()
        art.presentations += location.getvalid() # break
        self.expect(None, lambda: art.presentations) 
        self.one(art.brokenrules)
        self.broken(art, 'presentations', 'valid')

        # constituent
        art = artist.getvalid()
        art.presentations = locations() # break
        self.expect(None, lambda: art.presentations) 
        self.one(art.brokenrules)
        self.broken(art, 'presentations', 'valid')

        # composite
        pres = presentation.getvalid()
        pres.artist = location.getvalid()

        self.one(pres.brokenrules)
        self.broken(pres, 'artist', 'valid')

        loc = location.getvalid()
        loc.presentation = pres

        self.broken(loc, 'artist', 'valid')

        # associations

        # Add wrong type to association
        art = artist.getvalid()
        art.artist_artifacts += location()
        self.three(art.brokenrules)
        self.broken(art, 'artist_artifacts', 'valid')

        # Add wrong type to the pseudo-collection
        art = artist.getvalid()
        facts = art.artifacts 
        loc = location.getvalid()
        facts += loc

        self.three(art.brokenrules)
        self.broken(art, 'artifact', 'valid')
        
    def it_calls_explicit_attr_on_subentity(self):
        # Test inherited attr (phone)
        sng = singer()
        sng.firstname = uuid4().hex
        sng.lastname  = uuid4().hex
        sng.voice     = uuid4().hex
        sng.lifeform  = uuid4().hex
        sng.password  = bytes([randint(0, 255) for _ in range(32)])
        sng.ssn       = '1' * 11
        sng.register  = 'laryngealization'
        sng.email     = 'username@domain.tld'
        self.eq(int(), sng.phone)

        sng.phone = '1' * 7
        self.type(int, sng.phone)

        sng.save()

        art1 = singer(sng.id)
        self.eq(sng.phone, art1.phone)

        art1.phone = '1' * 7
        self.type(int, art1.phone)

        art1.save()

        art2 = singer(art1.id)
        self.eq(art1.phone, art2.phone)

        # Test non-inherited attr (register)
        sng = singer()
        sng.firstname = uuid4().hex
        sng.lastname  = uuid4().hex
        sng.voice     = uuid4().hex
        sng.lifeform  = uuid4().hex
        sng.password  = bytes([randint(0, 255) for _ in range(32)])
        sng.ssn       = '1' * 11
        sng.phone     = '1' * 7
        sng.email     = 'username@domain.tld'
        self.is_(str(), sng.register)

        sng.register = 'Vocal Fry'
        self.eq('vocal fry', sng.register)

        sng.save()

        art1 = singer(sng.id)
        self.eq(sng.register, art1.register)

        art1.register = 'flute'
        self.eq('whistle', art1.register)

        art1.save()

        art2 = singer(art1.id)
        self.eq(art1.register, art2.register)

    def it_calls_explicit_attr_on_subsubentity(self):
        # Test inherited attr (artist.phone)
        rpr = rapper()
        rpr.firstname = uuid4().hex
        rpr.lastname  = uuid4().hex
        rpr.voice     = uuid4().hex
        rpr.lifeform  = uuid4().hex
        rpr.stagename  = uuid4().hex
        rpr.password  = bytes([randint(0, 255) for _ in range(32)])
        rpr.ssn       = '1' * 11
        rpr.register  = 'laryngealization'
        rpr.email     = 'username@domain.tld'
        self.eq(int(), rpr.phone)

        rpr.phone = '1' * 7
        self.type(int, rpr.phone)

        rpr.save()

        rpr1 = rapper(rpr.id)
        self.eq(rpr.phone, rpr1.phone)

        rpr1.phone = '1' * 7
        self.type(int, rpr1.phone)

        rpr1.save()

        self.eq(rpr1.phone, rapper(rpr1.id).phone)

        # Test inherited attr from super (singer.register)
        rpr = rapper()
        rpr.firstname = uuid4().hex
        rpr.lastname  = uuid4().hex
        rpr.voice     = uuid4().hex
        rpr.lifeform  = uuid4().hex
        rpr.stagename  = uuid4().hex
        rpr.password  = bytes([randint(0, 255) for _ in range(32)])
        rpr.ssn       = '1' * 11
        rpr.phone     = '1' * 7
        rpr.email     = 'username@domain.tld'
        self.is_(str(), rpr.register)

        rpr.register = 'Vocal Fry'
        self.eq('vocal fry', rpr.register)

        rpr.save()

        rpr1 = rapper(rpr.id)
        self.eq(rpr.register, rpr1.register)

        rpr1.register = 'flute'
        self.eq('whistle', rpr1.register)

        rpr1.save()

        rpr2 = rapper(rpr1.id)
        self.eq(rpr1.register, rpr2.register)

        # Test non-inherited attr from rapper
        rpr = rapper()
        rpr.firstname = uuid4().hex
        rpr.lastname  = uuid4().hex
        rpr.voice     = uuid4().hex
        rpr.lifeform  = uuid4().hex
        rpr.stagename  = uuid4().hex
        rpr.password  = bytes([randint(0, 255) for _ in range(32)])
        rpr.ssn       = '1' * 11
        rpr.phone     = '1' * 7
        rpr.email     = 'username@domain.tld'
        rpr.register  = 'laryngealization'
        abilities     = "['endless rhymes', 'delivery', 'money']"
        self.eq(abilities, rpr.abilities)

        rpr.abilities = abilities = ['being wack']

        self.eq(str(abilities), rpr.abilities)

        rpr.save()

        self.eq(rpr.abilities, rapper(rpr.id).abilities)

    def it_calls_explicit_attr_on_association(self):
        art = artist.getvalid()

        art.artist_artifacts += artist_artifact.getvalid()
        aa = art.artist_artifacts.first

        # Ensure the overridden __init__ was called. It defaults planet to
        # "Earth".
        self.eq('Earth', aa.planet)

        # Test the explicit attribute timespan. It removes spaces from the
        # value and replaces them with dashes.
        art.artist_artifacts.first.timespan = '1/10/2018 2/10/2018'
        self.eq('1/10/2018-2/10/2018', aa.timespan)

        art.save()
        art1 = artist(art.id)
        self.eq('1/10/2018-2/10/2018', aa.timespan)

        # Test non-mapped property
        self.false(aa.processing)
        aa.processing = True
        self.true(aa.processing)

        # Test field
        uuid = str(uuid4())
        self.test = uuid
        self.eq(uuid, self.test)

    def it_calls_bytes_attr_on_entity(self):
        def saveok(e, attr):
            getattr(e, 'save')()
            e1 = type(e)(e.id)

            return getattr(e, attr) == getattr(e1, attr)

        def rand(size):
            return bytes([randint(0, 255) for _ in range(size)])

        # Test bytes attribute as a varbinary (min != max)
        comp = component()
        comp.name = uuid4().hex
        map = comp.orm.mappings['digest']

        # Make sure the password field hasn't been tampered with
        self.ne(map.min, map.max) 
        self.eq('varbinary(%s)' % map.max, map.dbtype)
        self.true(hasattr(comp, 'digest'))
        self.type(bytes, comp.digest)
        self.one(comp.brokenrules)
        self.broken(comp, 'digest', 'fits')

        # Test max
        self.ne(map.min, map.max) 
        comp.digest = rand(map.max)
        self.true(saveok(comp, 'digest'))

        comp.digest = rand(map.max + 1)
        self.broken(comp, 'digest', 'fits')

        # Test min
        comp.digest = rand(map.max)
        self.true(saveok(comp, 'digest'))
        
        comp.digest = rand(map.min - 1)
        self.broken(comp, 'digest', 'fits')

        # Ensure non-Bytes are coerced in accordance with bytes()'s rules.
        arrint = [randint(0, 255) for _ in range(32)]
        for v in arrint, bytearray(arrint):
            comp.digest = v
            self.eq(bytes(arrint), comp.digest)
            self.type(bytes, comp.digest)
            self.true(saveok(comp, 'digest'))

        # Test bytes attribute as a binary (min != max)
        art = artist()
        art.firstname = uuid4().hex
        art.lastname = uuid4().hex
        art.ssn = '1' * 11
        art.phone = '1' * 7
        art.email = 'username@domain.tld'
        map = art.orm.mappings['password']

        # Make sure the password field hasn't been tampered with
        self.eq(map.min, map.max) 
        self.eq('binary(%s)' % map.max, map.dbtype)
        self.true(hasattr(art, 'password'))
        self.type(bytes, art.password)
        self.one(art.brokenrules)
        self.broken(art, 'password', 'fits')

        # Test default
        self.eq(b'', art.password)

        # Test max
        art.password = rand(map.max)
        self.true(saveok(art, 'password'))

        art.password = rand(map.max + 1)
        self.broken(art, 'password', 'fits')

        # Test min
        art.password = rand(map.max)
        self.true(saveok(art, 'password'))
        
        art.password = rand(map.min - 1)
        self.broken(art, 'password', 'fits')

        # Ensure non-Bytes are coerced in accordance with bytes()'s rules.
        arrint = [randint(0, 255) for _ in range(32)]
        for v in arrint, bytearray(arrint):
            art.password = v
            self.eq(bytes(arrint), art.password)
            self.type(bytes, art.password)
            self.true(saveok(art, 'password'))

    def it_calls_bool_attr_on_entity(self):
        def saveok(e, attr):
            getattr(e, 'save')()
            e1 = type(e)(e.id)
            return getattr(e, attr) == getattr(e1, attr)

        fact = artifact.getvalid()
        self.eq('bit', fact.orm.mappings['abstract'].dbtype)
        self.type(bool, fact.abstract)
        self.true(hasattr(fact, 'abstract'))
        self.zero(fact.brokenrules)

        # Test default
        self.false(fact.abstract)
        self.true(saveok(fact, 'abstract'))

        # Test save
        for b in True, False:
            fact.abstract = b
            self.type(bool, fact.abstract)
            self.eq(b, fact.abstract)
            self.true(saveok(fact, 'abstract'))

        # Falsys and Truthys not allowed
        for v in int(), float(), str():
            fact.abstract = v
            self.one(fact.brokenrules)
            self.broken(fact, 'abstract', 'valid')

        # None, of course, is allowed despite being Falsy
        fact.abstract = None
        self.zero(fact.brokenrules)

    def it_calls_explicit_str_attr_on_entity(self):
        def saveok(e, attr):
            getattr(e, 'save')()
            e1 = type(e)(e.id)
            return getattr(e, attr) == getattr(e1, attr)

        # Ensure that a non-str gets converted to a str
        for o in int(1), float(3.14), dec(1.99), datetime.now(), True:
            art = artist()
            art.email = o
            self.type(str, art.email)
            self.eq(str(o).lower(), art.email)

        Δ = la2gr('d')

        for art in (artist(), singer()):
            map = art.orm.mappings('email')
            if not map:
                map = art.orm.super.orm.mappings['email']
            self.true(hasattr(art, 'email'))
            self.eq(str(), art.email)
            self.eq((3, 254), (map.min, map.max))

            art.email = email = 'USERNAME@DOMAIN.TDL'
            self.eq(email.lower(), art.email)

            art.email = '\n\t ' + email + '\n\t '
            self.eq(email.lower(), art.email)

            art = artist.getvalid()
            min, max = map.min, map.max

            art.email = Δ * map.max
            self.true(saveok(art, 'email'))

            art.email += Δ
            self.one(art.brokenrules)
            self.broken(art, 'email', 'fits')

            art.email = Δ * min
            self.true(saveok(art, 'email'))

            art.email = (Δ * (min - 1))
            self.one(art.brokenrules)
            self.broken(art, 'email', 'fits')

    def it_calls_str_attr_on_entity(self):
        def saveok(e, attr):
            getattr(e, 'save')()
            e1 = type(e)(e.id)
            return getattr(e, attr) == getattr(e1, attr)

        # Ensure that a non-str gets converted to a str
        for o in int(1), float(3.14), dec(1.99), datetime.now(), True:
            art = artist()
            art.firstname = o
            self.type(str, art.firstname)
            self.eq(str(o), art.firstname)

        for art in (artist(), singer()):
            art.lastname  = uuid4().hex
            art.lifeform  = uuid4().hex
            art.password  = bytes([randint(0, 255) for _ in range(32)])
            art.ssn       = '1' * 11
            art.phone     = '1' * 7
            art.email     = 'username@domain.tld'
            if type(art) is singer:
                art.voice     = uuid4().hex
                art.register  = 'laryngealization'
            
            map = art.orm.mappings('firstname')
            if not map:
                map = art.orm.super.orm.mappings['firstname']

            self.false(map.isfixed)
            self.eq('varchar(%s)' % (str(map.max),), map.dbtype)

            min, max = map.min, map.max

            art.firstname = firstname = '\n\t ' + (Δ * 10) + '\n\t '
            self.eq(firstname.strip(), art.firstname)

            art.firstname = Δ * max
            self.true(saveok(art, 'firstname'))

            art.firstname += Δ
            self.one(art.brokenrules)
            self.broken(art, 'firstname', 'fits')

            art.firstname = Δ * min
            self.true(saveok(art, 'firstname'))

            art.firstname = (Δ * (min - 1))
            self.one(art.brokenrules)
            self.broken(art, 'firstname', 'fits')

            art.firstname = Cunei_a * 255
            self.true(saveok(art, 'firstname'))

            art.firstname += Cunei_a
            self.one(art.brokenrules)
            self.broken(art, 'firstname', 'fits')

            art.firstname = Cunei_a * 255 # Unbreak

            art.firstname = None
            self.true(saveok(art, 'firstname'))

            # Test fixed-length ssn property
            art = artist()
            art.firstname = uuid4().hex
            art.lastname  = uuid4().hex
            art.lifeform  = uuid4().hex
            art.password  = bytes([randint(0, 255) for _ in range(32)])
            art.phone     = '1' * 7
            art.email     = 'username@domain.tld'
            if type(art) is singer:
                art.voice     = uuid4().hex
                art.register  = 'laryngealization'

            map = art.orm.mappings['ssn']
            self.true(map.isfixed)
            self.eq('char(%s)' % (map.max,), map.dbtype)
            self.empty(art.ssn)

            # We are treating ssn as a fixed-length string that can hold any
            # unicode character - not just numeric characters. So lets user a roman
            # numeral V.
            art.ssn = V * map.max
            self.true(saveok(art, 'ssn'))

            art.ssn = V * (map.max + 1)
            self.one(art.brokenrules)
            self.broken(art, 'ssn', 'fits')

            art.ssn = V * (map.min - 1)
            self.one(art.brokenrules)
            self.broken(art, 'ssn', 'fits')

            art.ssn = None
            self.true(saveok(art, 'ssn'))

            # Test longtext
            art = artist()
            art.firstname = uuid4().hex
            art.lastname  = uuid4().hex
            art.lifeform  = uuid4().hex
            art.password  = bytes([randint(0, 255) for _ in range(32)])
            art.phone     = '1' * 7
            art.email     = 'username@domain.tld'
            art.ssn       = V * 11
            if type(art) is singer:
                art.voice     = uuid4().hex
                art.register  = 'laryngealization'

            map = art.orm.mappings['bio']
            self.false(map.isfixed)
            self.eq('longtext', map.dbtype)
            self.none(art.bio)

            art.bio = V * map.max
            self.true(saveok(art, 'bio'))

            art.bio = V * (map.max + 1)
            self.one(art.brokenrules)
            self.broken(art, 'bio', 'fits')

            art.bio = V * (map.min - 1)
            self.one(art.brokenrules)
            self.broken(art, 'bio', 'fits')

            art.bio = None
            self.true(saveok(art, 'bio'))

    def it_calls_explicit_float_attr_on_entity(self):
        def saveok(e, attr):
            getattr(e, 'save')()
            e1 = builtins.type(e)(e.id)
            return getattr(e, attr) == getattr(e1, attr)

        comp = component.getvalid()

        map = comp.orm.mappings['width']
        self.type(float, comp.width)
        self.eq(-9999.9, map.min)
        self.eq(9999.9, map.max)

        comp.width = -100
        self.eq(100, comp.width)

        saveok(comp, 'width')

    def it_calls_explicit_int_attr_on_entity(self):
        def saveok(e, attr):
            getattr(e, 'save')()
            e1 = builtins.type(e)(e.id)
            return getattr(e, attr) == getattr(e1, attr)

        art = artist.getvalid()

        map = art.orm.mappings['phone']
        self.type(int, art.phone)
        self.eq(1000000, map.min)
        self.eq(9999999, map.max)

        art.phone = '555-5555'
        self.eq(5555555, art.phone)

        saveok(art, 'phone')

    def it_calls_num_attr_on_entity(self):
        def saveok(e, attr):
            getattr(e, 'save')()
            e1 = builtins.type(e)(e.id)
            return getattr(e, attr) == getattr(e1, attr)

        constraints = (
            {
                'cls': artifact,
                'attr': 'price',
                'type': 'decimal(12, 2)',
                'signed': True,
            },
            {
                'cls': component,
                'attr': 'height',
                'type': 'double(12, 2)',
                'signed': True,
            },
            {
                'cls': component,
                'attr': 'weight',
                'type': 'double(8, 7)',
                'signed': True,
            },
            {
                'cls': concert,
                'attr': 'ticketprice',
                'type': 'tinyint',
                'signed': True,
            },
            {
                'cls': concert,
                'type': 'tinyint unsigned',
                'attr': 'duration',
                'signed': False,
            },
            {
                'cls': concert,
                'type': 'mediumint',
                'attr': 'attendees',
                'signed': True,
            },
            {
                'cls': concert,
                'type': 'mediumint unsigned',
                'attr': 'capacity',
                'signed': False,
            },
            {
                'cls': artist,
                'type': 'smallint unsigned',
                'attr': 'weight',
                'signed': False,
            },
            {
                'cls': artist,
                'type': 'int',
                'attr': 'networth',
                'signed': True,
            },
            {
                'cls': concert,
                'type': 'int unsigned',
                'attr': 'externalid',
                'signed': False,
            },
            {
                'cls': artifact,
                'type': 'bigint',
                'attr': 'weight',
                'signed': True,
            },
            {
                'cls': concert,
                'type': 'bigint unsigned',
                'attr': 'externalid1',
                'signed': False,
            },
        )
        for const in constraints:
            type    =  const['type']
            attr    =  const['attr']
            cls     =  const['cls']
            signed  =  const['signed']

            if 'double' in type:
                pytype =  float
            elif 'decimal' in type:
                pytype = dec
            elif 'int' in type:
                pytype = int

            dectype = pytype in (float, dec)

            obj = cls.getvalid()
            map = obj.orm.mappings[attr]

            min, max = map.min, map.max

            self.eq(type, map.dbtype, str(const))
            self.eq(signed, map.signed, str(const))
            self.true(hasattr(obj, attr))
            self.zero(obj.brokenrules)
            self.type(pytype, getattr(obj, attr))

            # Test default
            self.eq(pytype(), getattr(obj, attr))
            self.true(saveok(obj, attr))

            # Test min
            setattr(obj, attr, min)
            self.zero(obj.brokenrules)
            self.true(saveok(obj, attr))

            setattr(obj, attr, getattr(obj, attr) - 1)
            self.one(obj.brokenrules)
            self.broken(obj, attr, 'fits')

            # Test max
            setattr(obj, attr, max)
            self.zero(obj.brokenrules)
            self.true(saveok(obj, attr))

            setattr(obj, attr, getattr(obj, attr) + 1)
            self.one(obj.brokenrules)
            self.broken(obj, attr, 'fits')

            # Test given an int as a str
            v = randint(int(min), int(max))
            setattr(obj, attr, str(v))
            self.eq(pytype(v), getattr(obj, attr))

            # Test given a float/decimal as a str. This also ensures that floats and
            # Decimals round to their scales.
            if pytype is not int:
                v = round(uniform(float(min), float(max)), map.scale)
                setattr(obj, attr, str(v))

                self.eq(round(pytype(v), map.scale), 
                        getattr(obj, attr), str(const))

                self.type(pytype, getattr(obj, attr))
                self.true(saveok(obj, attr))

            # Nullable
            setattr(obj, attr, None)
            self.zero(obj.brokenrules)
            self.true(saveok(obj, attr))

    def it_calls_datetime_attr_on_entity(self):
        utc = timezone.utc

        # It converts naive datetime to UTC
        art = artist.getvalid()
        self.none(art.dob)
        art.dob = '2004-01-10'
        self.type(primative.datetime, art.dob)
        self.type(primative.datetime, art.dob)
        expect = datetime(2004, 1, 10, tzinfo=utc)
        self.eq(expect, art.dob)
       
        # Save, reload, test
        art.save()
        self.eq(expect, artist(art.id).dob)
        self.type(primative.datetime, artist(art.id).dob)

        # It converts aware datetime to UTC
        aztz = dateutil.tz.gettz('US/Arizona')
        azdt = datetime(2003, 10, 11, 10, 13, 46, tzinfo=aztz)
        art.dob = azdt
        expect = azdt.astimezone(utc)

        self.eq(expect, art.dob)

        # Save, reload, test
        art.save()
        self.eq(expect, artist(art.id).dob)
        self.type(primative.datetime, artist(art.id).dob)

        # It converts backt to AZ time using string tz
        self.eq(azdt, art.dob.astimezone('US/Arizona'))

        # Test invalid date times
        art = art.getvalid()
        
        # Python can do a 1 CE, but MySQL can't so this should break validation.
        art.dob = datetime(1, 1, 1)
        self.one(art.brokenrules)
        self.broken(art, 'dob', 'fits')

        # Ensure microseconds are persisted
        ms = randint(100000, 999999)
        art.dob = primative.datetime('9999-12-31 23:59:59.%s' % ms)
        art.save()
        self.eq(ms, artist(art.id).dob.microsecond)

        # The max is 9999-12-31 23:59:59.999999
        art.dob = primative.datetime('9999-12-31 23:59:59.999999')
        art.save()
        self.eq(art.dob, artist(art.id).dob)
        
    def it_calls_str_propertys_setter_on_entity(self):
        class persons(orm.entities):
            pass

        class person(orm.entity):
            firstname = orm.fieldmapping(str)

        p = person()

        uuid = uuid4().hex
        p.firstname = uuid

        self.eq(uuid, p.firstname)
        self.zero(p.brokenrules)

        # Ensure whitespace in strip()ed from str values.
        p.firstname = ' \n\t' + uuid + ' \n\t'
        self.eq(uuid, p.firstname)
        self.zero(p.brokenrules)

    def it_calls_save_on_entity(self):
        art = artist.getvalid()

        # Test creating and retrieving an entity
        art.firstname = uuid4().hex
        art.lastname  = uuid4().hex
        art.lifeform  = uuid4().hex

        self.true(art.orm.isnew)
        self.false(art.orm.isdirty)

        with self._chrontest() as t:
            t.run(art.save)
            t.created(art)

        self.false(art.orm.isnew)
        self.false(art.orm.isdirty)

        art1 = artist(art.id)

        self.false(art1.orm.isnew)
        self.false(art1.orm.isdirty)

        for map in art1.orm.mappings:
            if isinstance(map, orm.fieldmapping):
                expect = getattr(art, map.name)
                actual = getattr(art1, map.name)
                self.eq(expect, actual, map.name)

        # Test changing, saving and retrieving an entity
        art1.firstname  =  uuid4().hex
        art1.lastname   =  uuid4().hex
        art1.phone      =  '2' * 7
        art1.lifeform   =  uuid4().hex
        art1.style      =  uuid4().hex
        art1.weight     += 1
        art1.networth   =  1
        art1.dob        =  primative.datetime.now().replace(tzinfo=timezone.utc)
        art1.password   = bytes([randint(0, 255) for _ in range(32)])
        art1.ssn        = '2' * 11
        art1.bio        = uuid4().hex
        art1.email      = 'username1@domain.tld'
        art1.title      = uuid4().hex[0]
        art1.phone2     = uuid4().hex[0]
        art1.email_1    = uuid4().hex[0]

        self.false(art1.orm.isnew)
        self.true(art1.orm.isdirty)

        # Ensure that changing art1's properties don't change art's. This
        # problem is likely to not reoccure, but did come up in early
        # development.
        for prop in art.orm.properties:
            if prop == 'id':
                self.eq(getattr(art1, prop), getattr(art, prop), prop)
            else:
                if prop in ('createdat', 'updatedat'):
                    continue
                self.ne(getattr(art1, prop), getattr(art, prop), prop)

        self.chronicles.clear()
        art1.save()
        self._chrons(art1, 'update')

        self.false(art1.orm.isnew)
        self.false(art1.orm.isdirty)

        art2 = artist(art.id)

        for map in art2.orm.mappings:
            if isinstance(map, orm.fieldmapping):
                if map.isdatetime:
                    name = map.name
                    dt1 = getattr(art1, name)
                    dt2 = getattr(art2, name)
                    setattr(art1, name, dt1.replace(second=0, microsecond=0))
                    setattr(art2, name, dt2.replace(second=0, microsecond=0))
                self.eq(getattr(art1, map.name), getattr(art2, map.name))

    def it_fails_to_save_broken_entity(self):
        art = artist()

        art.firstname = 'x' * 256
        self.broken(art, 'firstname', 'fits')

        # TODO Today (20190815) we got a 
        #     MySQLdb.OperationalError(2006, 'MySQL server has gone away')
        # error instead of a BrokenRulesError. Why would we get this
        # from as simple save.
        # UPDATE Happened again 20190819
        try:
            art.save()
        except Exception as ex:
            self.type(BrokenRulesError, ex)
        else:
            self.fail('Exception not thrown')

    def it_hard_deletes_entity(self):
        for i in range(2):
            art = artist.getvalid()

            art.save()

            self.expect(None, lambda: artist(art.id))

            if i:
                art.lastname  = uuid4().hex
                self.zero(art.brokenrules)
            else:
                art.lastname  = 'X' * 265 # break rule
                self.one(art.brokenrules)

            self.chronicles.clear()
            art.delete()
            self.one(self.chronicles)
            self._chrons(art, 'delete')

            self.eq((True, False, False), art.orm.persistencestate)

            self.expect(db.RecordNotFoundError, lambda: artist(art.id))

    def it_deletes_from_entitys_collections(self):
        # Create artist with a presentation and save
        art = artist.getvalid()
        pres = presentation.getvalid()
        art.presentations += pres
        loc = location.getvalid()
        art.presentations.last.locations += loc
        art.save()

        # Reload
        art = artist(art.id)

        # Test presentations and its trash collection
        self.one(art.presentations)
        self.zero(art.presentations.orm.trash)

        self.one(art.presentations.first.locations)
        self.zero(art.presentations.first.locations.orm.trash)

        # Remove the presentation
        pres = art.presentations.pop()

        # Test presentations and its trash collection
        self.zero(art.presentations)
        self.one(art.presentations.orm.trash)

        self.one(art.presentations.orm.trash.first.locations)
        self.zero(art.presentations.orm.trash.first.locations.orm.trash)

        self.chronicles.clear()
        art.save()
        self.two(self.chronicles)
        self._chrons(pres, 'delete')
        self._chrons(pres.locations.first, 'delete')

        art = artist(art.id)
        self.zero(art.presentations)
        self.zero(art.presentations.orm.trash)

        self.expect(db.RecordNotFoundError, lambda: presentation(pres.id))
        self.expect(db.RecordNotFoundError, lambda: location(loc.id))

    def it_raises_exception_on_unknown_id(self):
        for cls in singer, artist:
            try:
                cls(uuid4())
            except Exception as ex:
                self.type(db.RecordNotFoundError, ex)
            else:
                self.fail('Exception not thrown')

    def it_calls_dir_on_entity(self):
        # Make sure mapped properties are returned when dir() is called.
        # Also ensure there is only one of each property in the directory. If
        # there are more, entitymeta may not be deleting the original property
        # from the class body.
        art = artist()
        dir = builtins.dir(art)
        for p in art.orm.properties:
            self.eq(1, dir.count(p))

    def it_calls_dir_on_subentity(self):
        # Make sure mapped properties are returned when dir() is called.
        # Also ensure there is only one of each property in the
        # directory. If there are more, entitymeta may not be deleting
        # the original property from the class body.

        art = artist()
        sng = singer()
        dir = builtins.dir(sng)

        # Inherited
        for p in art.orm.properties:
            self.eq(1, dir.count(p))

        # Non-inherited
        for p in sng.orm.properties:
            self.eq(1, dir.count(p))

    def it_calls_dir_on_subsubentity(self):
        # Make sure mapped properties are returned when dir() is called.
        # Also ensure there is only one of each property in the
        # directory. If there are more, entitymeta may not be deleting
        # the original property from the class body.

        art = artist()
        sng = singer()
        rpr = rapper()
        dir = builtins.dir(rpr)

        # Indirectly inherited
        for p in art.orm.properties:
            self.eq(1, dir.count(p), p)

        # Directly inherited
        for p in sng.orm.properties:
            self.eq(1, dir.count(p), p)

        # Not inherited
        for p in rpr.orm.properties:
            self.eq(1, dir.count(p), p)

    def it_calls_dir_on_association(self):
        art = artist()
        art.artifacts += artifact()
        aa = art.artist_artifacts.first

        d = dir(aa)

        for prop in aa.orm.properties:
            self.eq(1, d.count(prop))

    def it_reconnects_closed_database_connections(self):
        def art_onafterreconnect(src, eargs):
            drown()

        def drown():
            pool = db.pool.getdefault()
            for conn in pool._in + pool._out:
                conn.kill()

        # Kill all connections in and out of the pool
        drown()

        art = artist.getvalid()

        # Subscribe to the onafterreconnect event so the connections can
        # be re-drowned. This will ensure that the connections never get
        # sucessfully reconnected which will cause an OperationalError.
        art.onafterreconnect += art_onafterreconnect

        self.expect(MySQLdb.OperationalError, lambda: art.save())

        # Make sure the connections have been killed.
        drown()

        # Unsubscribe so .save() is allowed to reconnect. This will cause
        # save() to be successful.
        art.onafterreconnect -= art_onafterreconnect

        self.expect(None, lambda: art.save())

        # Ensure e._load recovers correctly from a disconnect like we did with
        # e.save() above.  (Normally, __init__(id) for an entity calls
        # self._load(id) internally.  Here we call art._load directly so we
        # have time to subscribe to art's onafterreconnect event.)
        drown()
        id, art = art.id, artist.getvalid()
        art.onafterreconnect += art_onafterreconnect

        self.expect(MySQLdb.OperationalError, lambda: art._load(id))

        art.onafterreconnect -= art_onafterreconnect

        self.expect(None, lambda: art._load(id))

        # Ensure that es.orm.load() recovers correctly from a reconnect
        arts = artists(id=id)

        # Subscribe to event to ensure loads fail. This will load arts first
        # then subscribe so we have to clear arts next.
        arts.onafterreconnect += art_onafterreconnect

        # Subscribing to the event above loads arts so call the clear() method.
        arts.clear()

        # In addition to clear()ing the collection, flag the collection as
        # unloaded to ensure an attempt is made to reload the collection when
        # `arts.count` is called below.
        arts.orm.isloaded = False

        # Make sure connections are drowned.
        drown()

        # Calling count (or any attr) forces a load. Enuser the load causing an
        # exception due to the previous drown()ing of connections.
        self.expect(MySQLdb.OperationalError, lambda: arts.count)

        # Remove the drowning event. 
        arts.onafterreconnect -= art_onafterreconnect

        # Drown again. We want to ensure that the next load will cause a
        # recovery form the dead connection.
        drown()

        # Clear to force a reload
        arts.clear()

        # Calling the count property (like any attr) will load arts. No
        # exception will be thrown because the drowning event handler was
        # unsubscribed from.
        self.expect(None, lambda: arts.count)

    def it_mysql_warnings_are_exceptions(self):
        def warn(cur):
            cur.execute('select 0/0')

        exec = db.executioner(warn)

        self.expect(_mysql_exceptions.Warning, lambda: exec.execute())

    def it_saves_multiple_graphs(self):
        art1 = artist.getvalid()
        art2 = artist.getvalid()
        sng = singer.getvalid()

        pres     =  presentation.getvalid()
        sngpres  =  presentation.getvalid()
        loc      =  location.getvalid()

        art1.presentations += pres
        sng.presentations += sngpres
        art1.presentations.first.locations += loc

        arts = artists()
        for _ in range(2):
            arts += artist.getvalid()

        art1.save(art2, arts, sng)

        for e in art1 + art2 + arts + sng:
            self.expect(None, lambda: artist(e.id))

        self.expect(None, lambda: presentation(pres.id))
        self.expect(None, lambda: presentation(sngpres.id))
        self.expect(None, lambda: location(loc.id))
        self.expect(None, lambda: singer(sng.id))

        art1.presentations.pop()

        art2.save(art1, arts)

        for e in art1 + art2 + arts + sng:
            self.expect(None, lambda: artist(e.id))

        self.expect(None, lambda: singer(sng.id))

        self.expect(db.RecordNotFoundError, lambda: presentation(pres.id))
        self.expect(db.RecordNotFoundError, lambda: location(loc.id))

        for e in art1 + art2 + arts + sng:
            e.delete()
            self.expect(db.RecordNotFoundError, lambda: artist(pres.id))

        arts.save(art1, art2, sng)

        for e in art1 + art2 + arts + sng:
            self.expect(None, lambda: artist(e.id))

    def it_rollsback_save_of_entities_constituent(self):
        # Create two artists
        pres = presentation.getvalid()
        art = artist.getvalid()
        art.presentations += pres

        arts = artists()

        for _ in range(2):
            arts += artist.getvalid()
            arts.last.firstname = uuid4().hex

        def saveall():
            pres.save(arts.first, arts.second)

        saveall()

        # First, break the save method so a rollback occurs, and test
        # the rollback. Second, fix the save method and ensure success.
        for i in range(2):
            if i:
                # Restore original save method
                arts.second._save = save

                # Update property 
                arts.first.firstname = new = uuid4().hex
                saveall()
                self.eq(new, artist(arts.first.id).firstname)
            else:
                # Update property
                old, arts.first.firstname \
                    = arts.first.firstname, uuid4().hex

                # Break save method
                save, arts.second._save \
                    = arts.second._save, lambda x: 0/0

                self.expect(ZeroDivisionError, saveall)

                self.eq(old, artist(arts.first.id).firstname)

    def it_calls_inherited_property(self):
        s = singer()
        uuid = uuid4().hex
        s.firstname = uuid 
        self.eq(uuid, s.firstname)

    def it_inherited_class_has_same_id_as_super(self):
        s = singer()
        self.eq(s.orm.super.id, s.id)

    def it_saves_and_loads_inherited_entity(self):
        sng = singer.getvalid()
        sng.firstname  =  fname  =  uuid4().hex
        sng.voice      =  voc    =  uuid4().hex
        sng.save()

        art = sng1 = None
        def load():
            nonlocal art, sng1
            art   = artist(sng.id)
            sng1 = singer(sng.id)

        self.expect(None, load)

        self.eq(fname,  art.firstname)
        self.eq(fname,  sng1.firstname)
        self.eq(voc,    sng1.voice)

    def it_saves_subentities(self):
        chrons = self.chronicles

        sngs = singers()

        for _ in range(2):
            sngs += singer.getvalid()
            sngs.last.firstname = uuid4().hex
            sngs.last.lastname = uuid4().hex

        with self._chrontest() as t:
            t.run(lambda: sngs.save())
            t.created(sngs.first)
            t.created(sngs.second)
            t.created(sngs.first.orm.super)
            t.created(sngs.second.orm.super)

        for sng in sngs:
            sng1 = singer(sng.id)
            for map in sng.orm.mappings.all:
                if not isinstance(map, orm.fieldmapping):
                    continue

                self.eq(getattr(sng, map.name), getattr(sng1, map.name))

    def it_saves_subsubentities(self):
        rprs = rappers()

        for _ in range(2):
            rprs += rapper.getvalid()
            rprs.last.firstname = uuid4().hex
            rprs.last.lastname = uuid4().hex

        with self._chrontest() as t:
            t.run(lambda: rprs.save())
            t.created(rprs.first)
            t.created(rprs.second)
            t.created(rprs.first.orm.super)
            t.created(rprs.second.orm.super)
            t.created(rprs.first.orm.super.orm.super)
            t.created(rprs.second.orm.super.orm.super)

        for rpr in rprs:
            rpr1 = rapper(rpr.id)

            for map in rpr.orm.mappings.all:
                if not isinstance(map, orm.fieldmapping):
                    continue

                self.eq(getattr(rpr, map.name), getattr(rpr1, map.name))

    def it_rollsback_save_of_subentities(self):
        # Create two singers
        sngs = singers()

        for _ in range(2):
            sngs += singer.getvalid()
            sngs.last.firstname = uuid4().hex
            sngs.last.lastname = uuid4().hex

        sngs.save()

        # First, break the save method so a rollback occurs, and test the
        # rollback. Second, fix the save method and ensure success.
        for i in range(2):
            if i:
                # Restore original save method
                sngs.second._save = save

                # Update property 
                sngs.first.firstname = new = uuid4().hex
                sngs.save()
                self.eq(new, singer(sngs.first.id).firstname)
            else:
                # Update property
                old, sngs.first.firstname = sngs.first.firstname, uuid4().hex

                # Break save method
                save, sngs.second._save = sngs.second._save, lambda x: 0/0

                self.expect(ZeroDivisionError, lambda: sngs.save())
                self.eq(old, singer(sngs.first.id).firstname)

    def it_rollsback_save_of_subsubentities(self):
        # Create two rappers
        rprs = rappers()

        for _ in range(2):
            rprs += rapper.getvalid()
            rprs.last.firstname = uuid4().hex
            rprs.last.lastname = uuid4().hex

        rprs.save()

        # First, break the save method so a rollback occurs, and test
        # the rollback. Second, fix the save method and ensure success.
        for i in range(2):
            if i:
                # Restore original save method
                rprs.second._save = save

                # Update property 
                rprs.first.firstname = new = uuid4().hex
                rprs.save()
                self.eq(new, rapper(rprs.first.id).firstname)
            else:
                # Update property
                old, rprs[0].firstname = rprs[0].firstname, uuid4().hex

                # Break save method
                save, rprs[1]._save = rprs[1]._save, lambda x: 0/0

                self.expect(ZeroDivisionError, lambda: rprs.save())
                self.eq(old, rapper(rprs.first.id).firstname)

    def it_sets_reference_to_composite_on_subentity(self):
        chrons = self.chronicles

        sng = singer.getvalid()
        for _ in range(2):
            pres = presentation.getvalid()
            sng.presentations += pres

            pres.locations += location.getvalid()

        sng.save()

        for i, sng1 in enumerate((sng, singer(sng.id))):
            for pres in sng1.presentations:
                self.is_(sng1,            pres.singer)
                self.is_(sng1.orm.super,  pres.artist)
                self.eq(pres.singer.id,   pres.artist.id)
                self.type(artist,         sng1.orm.super)
                self.type(artist,         pres.singer.orm.super)

                chrons.clear()
                locs = sng.presentations[pres].locations.sorted()
                locs1 = pres.locations.sorted()

                loc, loc1 = locs.first, locs1.first

                if i:
                    self.one(chrons)
                    self.eq(chrons.where('entity', pres.locations).first.op, 'retrieve')
                else:
                    self.zero(chrons)

                self.one(locs)
                self.one(locs1)
                self.eq(loc.id, loc1.id)

        sng = singer.getvalid()

        for _ in range(2):
            sng.concerts += concert.getvalid()
            sng.concerts.last.locations += location.getvalid()

        sng.save()

        for i, sng in enumerate((sng, singer(sng.id))):
            for j, conc in sng.concerts.enumerate():
                chrons.clear()
                self.is_(sng,            conc.singer)
                self.is_(sng.orm.super,  conc.singer.orm.super)
                self.type(artist,        sng.orm.super)
                self.type(artist,        conc.singer.orm.super)

                if i and not j:
                    self.one(chrons)
                else:
                    self.zero(chrons)

                chrons.clear()
                locs = sng.concerts[conc].locations.sorted()
                locs1 = conc.locations.sorted()

                loc, loc1 = locs.first, locs1.first

                if i:
                    self.eq(chrons.where('entity', conc.locations).first.op, 'retrieve')
                    self.eq(chrons.where('entity', conc.orm.super).first.op, 'retrieve')
                    self.two(chrons)
                else:
                    self.zero(chrons)

                self.one(locs)
                self.one(locs1)
                self.eq(loc.id, loc1.id)

    def it_sets_reference_to_composite_on_subsubentity(self):
        rpr = rapper.getvalid()
        for _ in range(2):
            pres = presentation.getvalid()
            rpr.presentations += pres
            pres.locations += location.getvalid()

        rpr.save()

        for i, rpr1 in enumerate((rpr, rapper(rpr.id))):
            for pres in rpr1.presentations:

                # TODO Calling pres.singer raise exception
                #self.is_(rpr1.orm.super,  pres.singer)
                #self.eq(pres.singer.id,   pres.artist.id)
                #self.type(artist,         pres.singer.orm.super)
                self.is_(rpr1,                      pres.rapper)
                self.is_(rpr1.orm.super.orm.super,  pres.artist)
                self.type(rapper,                   pres.rapper)
                self.type(artist,         rpr1.orm.super.orm.super)

                locs = rpr.presentations[pres].locations.sorted()

                with self._chrontest() as t:
                    locs1 = t.run(pres.locations.sorted)

                self.one(locs)
                self.one(locs1)
                self.eq(locs.first.id, locs1.first.id)

        rpr = rapper.getvalid()

        for _ in range(2):
            rpr.concerts += concert.getvalid()
            rpr.concerts.last.locations += location.getvalid()

        rpr.save()

        for i, rpr in enumerate((rpr, rapper(rpr.id))):
            for j, conc in rpr.concerts.enumerate():
                
                def f():
                    self.is_(rpr,            conc.rapper)
                    self.is_(rpr.orm.super,  conc.singer)

                    # TODO Calling cons.artists failes
                    # self.is_(rpr.orm.super.orm.super,  conc.artist)
                    self.type(singer,        rpr.orm.super)
                    self.type(artist,        conc.singer.orm.super)

                with self._chrontest() as t:
                    t.run(f)
                    if i and not j:
                        t.retrieved(conc.singer.orm.super)

                def f():
                    locs = rpr.concerts[conc].locations.sorted()
                    locs1 = conc.locations.sorted()
                    return locs, locs1

                with self._chrontest() as t:
                    locs, locs1 = t.run(f)

                    if i:
                        t.retrieved(conc.locations)
                        t.retrieved(conc.orm.super)

                    loc, loc1 = locs.first, locs1.first
                    self.one(locs)
                    self.one(locs1)
                    self.eq(loc.id, loc1.id)

        for _ in range(2):
            rpr.battles += battle.getvalid()
            rpr.battles.last.locations += location.getvalid()

        rpr.save()

        for i, rpr in enumerate((rpr, rapper(rpr.id))):
            for j, btl in rpr.battles.enumerate():
                def f():
                    self.is_(rpr,                      btl.rapper)

                    # TODO Accessing btl.singer and btl.artist 
                    #self.is_(rpr.orm.super,            btl.singer)
                    #self.is_(rpr.orm.super.orm.super,  btl.artist)

                    self.type(rapper,                  btl.rapper)
                    #self.type(singer,                  btl.singer)
                    #self.type(artist,                  btl.artist)

                with self._chrontest() as t:
                    t.run(f)

    def it_loads_and_saves_subentitys_constituents(self):
        chrons = self.chronicles

        # Ensure that a new composite has a constituent object with zero
        # elements
        sng = singer.getvalid()
        self.zero(sng.presentations)

        # Ensure a saved composite object with zero elements in a
        # constituent collection loads with zero the constituent
        # collection containing zero elements.
        sng.firstname = uuid4().hex
        sng.lastname  = uuid4().hex
        sng.voice     = uuid4().hex

        self.zero(sng.presentations)

        sng.save()

        self.zero(sng.presentations)

        sng = singer(sng.id)
        self.zero(sng.presentations)
        self.is_(sng,            sng.presentations.singer)
        self.is_(sng.orm.super,  sng.presentations.artist)

        sng = singer.getvalid()

        sng.presentations += presentation.getvalid()
        sng.presentations += presentation.getvalid()

        for pres in sng.presentations:
            pres.name = uuid4().hex

        chrons.clear()
        sng.save()

        self.four(chrons)
        press = sng.presentations
        self.eq(chrons.where('entity', sng.orm.super).first.op, 'create')
        self.eq(chrons.where('entity', sng).first.op, 'create')
        self.eq(chrons.where('entity', press.first).first.op, 'create')
        self.eq(chrons.where('entity', press.second).first.op, 'create')

        sng1 = singer(sng.id)

        chrons.clear()
        press = sng1.presentations

        self.two(chrons)

        self.eq(chrons.where('entity', press).first.op, 'retrieve')

        sng.presentations.sort()
        sng1.presentations.sort()
        for pres, pres1 in zip(sng.presentations, sng1.presentations):
            for map in pres.orm.mappings:
                if isinstance(map, orm.fieldmapping):
                    self.eq(getattr(pres, map.name), getattr(pres1, map.name))
            
            self.is_(pres1.singer, sng1)
            self.is_(pres1.artist, sng1.orm.super)

        # Create some locations with the presentations, save singer,
        # reload and test
        for pres in sng.presentations:
            for _ in range(2):
                pres.locations += location.getvalid()

        chrons.clear()
        sng.save()

        self.four(chrons)

        locs = sng.presentations.first.locations
        self.eq(chrons.where('entity', locs.first).first.op, 'create')
        self.eq(chrons.where('entity', locs.second).first.op, 'create')

        locs = sng.presentations.second.locations
        self.eq(chrons.where('entity', locs.first).first.op, 'create')
        self.eq(chrons.where('entity', locs.second).first.op, 'create')

        sng1 = singer(sng.id)
        self.two(sng1.presentations)

        sng.presentations.sort()
        sng1.presentations.sort()
        for pres, pres1 in zip(sng.presentations, sng1.presentations):

            pres.locations.sort()

            chrons.clear()
            pres1.locations.sort()

            self.one(chrons)
            locs = pres1.locations
            self.eq(chrons.where('entity', locs).first.op, 'retrieve')

            for loc, loc1 in zip(pres.locations, pres1.locations):
                for map in loc.orm.mappings:
                    if isinstance(map, orm.fieldmapping):
                        self.eq(getattr(loc, map.name), getattr(loc1, map.name))
            
                self.is_(pres1, loc1.presentation)

        # Test appending a collection of constituents to a constituents
        # collection. Save, reload and test.
        sng = singer.getvalid()
        press = presentations()

        for _ in range(2):
            press += presentation.getvalid()

        sng.presentations += press

        for i in range(2):
            if i:
                sng.save()
                sng = singer(sng.id)

            self.eq(press.count, sng.presentations.count)

            for pres in sng.presentations:
                self.is_(sng, pres.singer)
                self.is_(sng.orm.super, pres.artist)

    def it_loads_and_saves_subsubentitys_constituents(self):
        rpr = rapper.getvalid()
        self.zero(rpr.presentations)
        self.zero(rpr.concerts)

        # Ensure a saved composite object with zero elements in a
        # constituent collection loads with zero the constituent
        # collection containing zero elements.
        rpr.firstname = uuid4().hex
        rpr.lastname  = uuid4().hex
        rpr.voice     = uuid4().hex

        self.zero(rpr.presentations)
        self.zero(rpr.concerts)

        rpr.save()

        self.zero(rpr.presentations)
        self.zero(rpr.concerts)

        rpr = rapper(rpr.id)

        self.zero(rpr.presentations)
        self.zero(rpr.concerts)
        self.is_(rpr,                      rpr.presentations.rapper)

        # TODO rpr.presentations.singer isn't available here, though it
        # id: e217aa8b6db242eebfd88f11a55d1fde feels like it should be.
        # The reason `rapper` is available is because
        # rpr.__getattribute__ sets it. The reason `artist` is available
        # is because `presentations` is a constituent of artist.
        #
        # `singer` could be made available, but its implementation would
        # be tricky. Code in entities.__getattribute__ could look for
        # artist or rapper and try to work out the id for singer, then
        # load singer from the db. I'd like this to be presented as a
        # realistic use case before proceeding with an implementation.
        #self.is_(rpr.orm.super,            rpr.presentations.singer)
        self.is_(rpr.orm.super.orm.super,  rpr.presentations.artist)

        rpr = rapper.getvalid()

        for _ in range(2):
            rpr.concerts                 +=  concert.getvalid()
            rpr.presentations            +=  presentation.getvalid()
            rpr.presentations.last.name  =   uuid4().hex
            rpr.concerts.last.name       =   uuid4().hex

        with self._chrontest() as t:
            t.run(rpr.save)

            t.created(rpr)
            t.created(rpr.orm.super)
            t.created(rpr.orm.super.orm.super)
            t.created(rpr.concerts.first)
            t.created(rpr.concerts.second)
            t.created(rpr.concerts.first.orm.super)
            t.created(rpr.concerts.second.orm.super)
            t.created(rpr.presentations.first)
            t.created(rpr.presentations.second)

        rpr1 = rapper(rpr.id)

        with self._chrontest() as t:
            press = t.run(lambda: rpr1.presentations)
            t.retrieved(press)
            t.retrieved(rpr1.orm.super)
            t.retrieved(rpr1.orm.super.orm.super)

        rpr.presentations.sort()
        rpr1.presentations.sort()

        for pres, pres1 in zip(rpr.presentations, rpr1.presentations):
            if presentation in [x.__class__ for x in (pres, pres1)]:
                maps = presentations.orm.mappings
            else:
                maps = concerts.orm.mappings

            for map in maps:
                if map.name in ('createdat', 'updatedat'):
                    continue

                if isinstance(map, orm.fieldmapping):
                    self.eq(getattr(pres, map.name), 
                            getattr(pres1, map.name), map.name)
            
            self.is_(pres1.rapper, rpr1)
            # TODO The below dosen't work because pres has an artist
            # but doesn't know how to downcast that artist to
            # singer.
            # See e217aa8b6db242eebfd88f11a55d1fde
            # self.is_(pres1.singer, rpr1.orm.super)
            self.is_(pres1.artist, rpr1.orm.super.orm.super)

        # Create some locations with the presentations, save rapper,
        # reload and test
        for pres in rpr.presentations:
            for _ in range(2):
                pres.locations += location.getvalid()

        with self._chrontest() as t:
            t.run(rpr.save)
            for pres in rpr.presentations:
                for i in range(2):
                    t.created(pres.locations[i])

        rpr1 = rapper(rpr.id)
        self.four(rpr1.presentations)

        rpr.presentations.sort()
        rpr1.presentations.sort()

        for pres, pres1 in zip(rpr.presentations, rpr1.presentations):
            pres.locations.sort()

            with self._chrontest() as t:
                t.run(lambda: pres1.locations.sort())
                t.retrieved(pres1.locations)

            for loc, loc1 in zip(pres.locations, pres1.locations):
                for map in loc.orm.mappings:
                    if isinstance(map, orm.fieldmapping):
                        self.eq(
                            getattr(loc, map.name), 
                            getattr(loc1, map.name)
                        )
            
                self.is_(pres1, loc1.presentation)

        # Test appending a collection of constituents to a constituents
        # collection. Save, reload and test.
        rpr = rapper.getvalid()
        press = presentations()

        for _ in range(2):
            press += presentation.getvalid()

        rpr.presentations += press

        for i in range(2):
            if i:
                rpr.save()
                rpr = rapper(rpr.id)

            self.eq(press.count, rpr.presentations.count)

            for pres in rpr.presentations:
                self.is_(rpr, pres.rapper)

                # TODO The below dosen't work because pres has an artist
                # but doesn't know how to downcast that artist to
                # singer.
                # See e217aa8b6db242eebfd88f11a55d1fde
                #self.is_(rpr.orm.super.id, pres.singer.id)

                self.is_(rpr.orm.super.orm.super.id, pres.artist.id)

    def it_loads_and_saves_subentitys_subentity_constituents(self):
        chrons = self.chronicles

        # Ensure that a new composite has a constituent subentities with
        # zero elements
        sng = singer.getvalid()
        self.zero(sng.concerts)

        # Ensure a saved composite object with zero elements in a
        # subentities constituent collection loads with zero the
        # constituent collection containing zero elements.
        sng.firstname = uuid4().hex
        sng.lastname  = uuid4().hex
        sng.voice     = uuid4().hex

        self.zero(sng.concerts)

        sng.save()

        self.zero(sng.concerts)

        sng = singer(sng.id)

        self.zero(sng.concerts)

        self.is_(sng,            sng.concerts.singer)

        # TODO Entities collections can't load super composites:
        # `sng.concerts.singer` above works because when `concerts` is
        # loaded by sng's __getattribute__, self is assigned to the
        # `singer` reference. However, the super's of singer don't get
        # assigned. When sng.concerts.artist is called below, the artist
        # should be lazy-loaded.
        # self.is_(sng.orm.super,  sng.concerts.artist)

        sng = singer.getvalid()

        sng.concerts += concert.getvalid()
        sng.concerts += concert.getvalid()

        for conc in sng.concerts:
            conc.name = uuid4().hex

        chrons.clear()
        sng.save()

        self.six(chrons)
        concs = sng.concerts
        self.eq(chrons.where('entity',  sng.orm.super).first.op,    'create')
        self.eq(chrons.where('entity',  sng).first.op,              'create')
        self.eq(chrons.where('entity',  concs.first).first.op,      'create')
        self.eq(chrons.where('entity',  concs.second).first.op,     'create')
        self.eq(chrons.where('entity',  concs[0].orm.super)[0].op,  'create')
        self.eq(chrons.where('entity',  concs[1].orm.super)[0].op,  'create')

        sng1 = singer(sng.id)

        chrons.clear()
        concs = sng1.concerts

        self.one(chrons)
        self.eq(chrons.where('entity', concs).first.op, 'retrieve')

        sng.concerts.sort()
        sng1.concerts.sort()
        for conc, conc1 in zip(sng.concerts, sng1.concerts):
            for map in conc.orm.mappings:
                if isinstance(map, orm.fieldmapping):
                    self.eq(getattr(conc, map.name), getattr(conc1, map.name))
            
            self.is_(conc1.singer, sng1)

        # Create some locations with the concerts, save singer, reload and
        # test
        for conc in sng.concerts:
            for _ in range(2):
                conc.locations += location.getvalid()

        chrons.clear()
        sng.save()

        self.four(chrons)

        locs = sng.concerts.first.locations
        self.eq(chrons.where('entity', locs.first).first.op, 'create')
        self.eq(chrons.where('entity', locs.second).first.op, 'create')

        locs = sng.concerts.second.locations
        self.eq(chrons.where('entity', locs.first).first.op, 'create')
        self.eq(chrons.where('entity', locs.second).first.op, 'create')

        sng1 = singer(sng.id)
        self.two(sng1.concerts)

        sng.concerts.sort()
        sng1.concerts.sort()
        for conc, conc1 in zip(sng.concerts, sng1.concerts):

            conc.locations.sort()

            chrons.clear()
            conc1.locations.sort()

            locs = conc1.locations

            self.eq(chrons.where('entity', locs).first.op, 'retrieve')
            self.eq(chrons.where('entity', conc1.orm.super).first.op, 'retrieve')
            self.two(chrons)

            for loc, loc1 in zip(conc.locations, conc1.locations):
                for map in loc.orm.mappings:
                    if isinstance(map, orm.fieldmapping):
                        self.eq(getattr(loc, map.name), getattr(loc1, map.name))
            
                self.is_(conc1, loc1.concert)

        # Test appending a collection of constituents to a constituents
        # collection. Save, reload and test.
        sng = singer.getvalid()
        concs = concerts()

        for _ in range(2):
            concs += concert.getvalid()

        sng.concerts += concs

        for i in range(2):
            if i:
                sng.save()
                sng = singer(sng.id)

            self.eq(concs.count, sng.concerts.count)

            for conc in sng.concerts:
                self.is_(sng, conc.singer)
                self.type(artist, sng.orm.super)

    def it_loads_and_saves_subsubentitys_subsubentity_constituents(
        self):

        # Ensure that a new composite has a constituent subentities with
        # zero elements
        rpr = rapper.getvalid()
        self.zero(rpr.battles)

        # Ensure a saved composite object with zero elements in a
        # subentities constituent collection loads with zero the
        # constituent collection containing zero elements.
        rpr.firstname  =  uuid4().hex
        rpr.lastname   =  uuid4().hex
        rpr.voice      =  uuid4().hex
        rpr.stagename  =  uuid4().hex

        self.zero(rpr.battles)

        rpr.save()

        self.zero(rpr.battles)

        rpr = rapper(rpr.id)

        self.zero(rpr.battles)

        self.is_(rpr,            rpr.battles.rapper)

        # TODO Entities collections can't load super composites:
        # `rpr.battles.rapper` above works because when `battles` is
        # loaded by rpr's __getattribute__, self is assigned to the
        # `rapper` reference. However, the super's of rapper don't get
        # assigned. When rpr.battles.artist is called below, the artist
        # should be lazy-loaded.
        # self.is_(rpr.orm.super,  rpr.battles.artist)

        rpr = rapper.getvalid()

        rpr.battles += battle.getvalid()
        rpr.battles += battle.getvalid()

        for btl in rpr.battles:
            btl.name = uuid4().hex

        with self._chrontest() as t:
            t.run(rpr.save)
            t.created(rpr)
            t.created(rpr.orm.super)
            t.created(rpr.orm.super.orm.super)
            t.created(rpr.battles.first)
            t.created(rpr.battles.first.orm.super)
            t.created(rpr.battles.first.orm.super.orm.super)
            t.created(rpr.battles.second)
            t.created(rpr.battles.second.orm.super)
            t.created(rpr.battles.second.orm.super.orm.super)
        
        rpr1 = rapper(rpr.id)

        with self._chrontest() as t:
            btls = t.run(lambda: rpr1.battles)
            t.retrieved(btls)

        rpr.battles.sort()
        rpr1.battles.sort()
        for btl, btl1 in zip(rpr.battles, rpr1.battles):
            for map in btl.orm.mappings:
                if isinstance(map, orm.fieldmapping):
                    self.eq(
                        getattr(btl, map.name), 
                        getattr(btl1, map.name)
                    )
            
            self.is_(btl1.rapper, rpr1)

        # Create some locations with the battles, save rapper, reload
        # and test
        for btl in rpr.battles:
            for _ in range(2):
                btl.locations += location.getvalid()

        with self._chrontest() as t:
            t.run(rpr.save)
            t.created(rpr.battles.first.locations.first)
            t.created(rpr.battles.first.locations.second)
            t.created(rpr.battles.second.locations.first)
            t.created(rpr.battles.second.locations.second)

        rpr1 = rapper(rpr.id)
        self.two(rpr1.battles)

        rpr.battles.sort()
        rpr1.battles.sort()
        for btl, btl1 in zip(rpr.battles, rpr1.battles):
            btl.locations.sort()

            with self._chrontest() as t:
                t.run(lambda: btl1.locations.sort)
                t.retrieved(btl1.locations)
                t.retrieved(btl1.orm.super)
                t.retrieved(btl1.orm.super.orm.super)

            for loc, loc1 in zip(btl.locations, btl1.locations):
                for map in loc.orm.mappings:
                    if isinstance(map, orm.fieldmapping):
                        self.eq(getattr(loc, map.name), getattr(loc1, map.name))
            
                self.is_(btl1, loc1.battle)

        # Test appending a collection of constituents to a constituents
        # collection. Save, reload and test.
        rpr = rapper.getvalid()
        btls = battles()

        for _ in range(2):
            btls += battle.getvalid()

        rpr.battles += btls

        for i in range(2):
            if i:
                rpr.save()
                rpr = rapper(rpr.id)

            self.eq(btls.count, rpr.battles.count)

            for btl in rpr.battles:
                self.is_(rpr, btl.rapper)
                self.type(singer, rpr.orm.super)

    def it_updates_subentities_constituents_properties(self):
        chrons = self.chronicles
        sng = singer.getvalid()

        for _ in range(2):
            sng.presentations += presentation.getvalid()
            sng.presentations.last.name = uuid4().hex

            for _ in range(2):
                sng.presentations.last.locations += location.getvalid()
                sng.presentations.last.locations.last.description = uuid4().hex

        sng.save()

        sng1 = singer(sng.id)
        for pres in sng1.presentations:
            pres.name = uuid4().hex
            
            for loc in pres.locations:
                loc.description = uuid4().hex

        chrons.clear()
        sng1.save()
        self.six(chrons)
        for pres in sng1.presentations:
            self.eq(chrons.where('entity', pres).first.op, 'update')
            for loc in pres.locations:
                self.eq(chrons.where('entity', loc).first.op, 'update')
            

        sng2 = singer(sng.id)
        press = sng.presentations, sng1.presentations, sng2.presentations
        for pres, pres1, pres2 in zip(*press):

            # Make sure the properties were changed
            self.ne(getattr(pres2, 'name'), getattr(pres,  'name'))

            # Make user sng1.presentations props match those of sng2
            self.eq(getattr(pres2, 'name'), getattr(pres1, 'name'))

            locs = pres.locations, pres1.locations, pres2.locations
            for loc, loc1, loc2 in zip(*locs):
                # Make sure the properties were changed
                self.ne(getattr(loc2, 'description'), getattr(loc,  'description'))

                # Make user sng1 locations props match those of sng2
                self.eq(getattr(loc2, 'description'), getattr(loc1, 'description'))

    def it_updates_subsubentities_constituents_properties(self):
        rpr = rapper.getvalid()

        for _ in range(2):
            rpr.presentations += presentation.getvalid()
            rpr.presentations.last.name = uuid4().hex

            for _ in range(2):
                rpr.presentations.last.locations \
                    += location.getvalid()
                rpr.presentations.last.locations.last.description \
                    = uuid4().hex

        rpr.save()

        rpr1 = rapper(rpr.id)
        for pres in rpr1.presentations:
            pres.name = uuid4().hex
            
            for loc in pres.locations:
                loc.description = uuid4().hex

        with self._chrontest() as t:
            t.run(rpr1.save)
            for pres in rpr1.presentations:
                t.updated(pres)
                for loc in pres.locations:
                    t.updated(loc)
            
        rpr2 = rapper(rpr.id)

        press = (
            rpr.presentations, 
            rpr1.presentations, 
            rpr2.presentations
        )

        for pres, pres1, pres2 in zip(*press):

            # Make sure the properties were changed
            self.ne(getattr(pres2, 'name'), getattr(pres,  'name'))

            # Make user rpr1.presentations props match those of rpr2
            self.eq(getattr(pres2, 'name'), getattr(pres1, 'name'))

            locs = pres.locations, pres1.locations, pres2.locations
            for loc, loc1, loc2 in zip(*locs):
                # Make sure the properties were changed
                self.ne(
                    getattr(loc2, 'description'),
                    getattr(loc,  'description')
                )

                # Make user rpr1 locations props match those of rpr2
                self.eq(
                    getattr(loc2, 'description'), 
                    getattr(loc1, 'description')
                )

    def it_updates_subentitys_subentities_constituents_properties(self):
        chrons = self.chronicles
        sng = singer.getvalid()

        for _ in range(2):
            sng.concerts += concert.getvalid()
            sng.concerts.last.record = uuid4().hex

            for _ in range(2):
                sng.concerts.last.locations += location.getvalid()
                sng.concerts.last.locations.last.description = uuid4().hex

        sng.save()

        sng1 = singer(sng.id)
        for conc in sng1.concerts:
            conc.record = uuid4().hex
            conc.name   = uuid4().hex
            
            for loc in conc.locations:
                loc.description = uuid4().hex

        chrons.clear()
        sng1.save()

        self.eight(chrons)
        for conc in sng1.concerts:
            self.eq(chrons.where('entity', conc).first.op, 'update')
            self.eq(chrons.where('entity', conc.orm.super).first.op, 'update')
            for loc in conc.locations:
                self.eq(chrons.where('entity', loc).first.op, 'update')
            

        sng2 = singer(sng.id)
        concs = (sng.concerts, sng1.concerts, sng2.concerts)
        for conc, conc1, conc2 in zip(*concs):
            # Make sure the properties were changed
            self.ne(getattr(conc2, 'record'), getattr(conc,  'record'))
            self.ne(getattr(conc2, 'name'),   getattr(conc,  'name'))

            # Make user sng1.concerts props match those of sng2
            self.eq(getattr(conc2, 'record'), getattr(conc1, 'record'))
            self.eq(getattr(conc2, 'name'),   getattr(conc1, 'name'))

            locs = conc.locations, conc1.locations, conc2.locations
            for loc, loc1, loc2 in zip(*locs):
                # Make sure the properties were changed
                self.ne(getattr(loc2, 'description'), getattr(loc,  'description'))

                # Make user sng1 locations props match those of sng2
                self.eq(getattr(loc2, 'description'), getattr(loc1, 'description'))

    def it_updates_subsubentitys_subsubentities_constituents_properties(
        self):

        rpr = rapper.getvalid()

        for _ in range(2):
            rpr.concerts += concert.getvalid()
            rpr.concerts.last.record = uuid4().hex

            for _ in range(2):
                rpr.concerts.last.locations \
                    += location.getvalid()

                rpr.concerts.last.locations.last.description \
                    = uuid4().hex

        rpr.save()

        rpr1 = rapper(rpr.id)
        for conc in rpr1.concerts:
            conc.record = uuid4().hex
            conc.name   = uuid4().hex
            
            for loc in conc.locations:
                loc.description = uuid4().hex

        with self._chrontest() as t:
            t.run(rpr1.save)
            for conc in rpr1.concerts:
                t.updated(conc)
                t.updated(conc.orm.super)
                for loc in conc.locations:
                    t.updated(loc)

        rpr2 = rapper(rpr.id)
        concs = (rpr.concerts, rpr1.concerts, rpr2.concerts)
        for conc, conc1, conc2 in zip(*concs):
            # Make sure the properties were changed
            self.ne(getattr(conc2, 'record'), getattr(conc,  'record'))
            self.ne(getattr(conc2, 'name'),   getattr(conc,  'name'))

            # Make user rpr1.concerts props match those of rpr2
            self.eq(getattr(conc2, 'record'), getattr(conc1, 'record'))
            self.eq(getattr(conc2, 'name'),   getattr(conc1, 'name'))

            locs = conc.locations, conc1.locations, conc2.locations
            for loc, loc1, loc2 in zip(*locs):
                # Make sure the properties were changed
                self.ne(
                    getattr(loc2, 'description'), 
                    getattr(loc,  'description')
                )

                # Make user rpr1 locations props match those of rpr2
                self.eq(
                    getattr(loc2, 'description'), 
                    getattr(loc1, 'description')
                )

        # Battles
        rpr1 = rapper(rpr.id)
        for btl in rpr1.battles:
            btl.record = uuid4().hex
            btl.name   = uuid4().hex
            btl.views  = rand(1, 255)
            
            for loc in btl.locations:
                loc.description = uuid4().hex

        with self._chrontest() as t:
            t.run(rpr1.save)
            for btl in rpr1.battles:
                t.updated(btl)
                t.updated(btl.orm.super)
                for loc in btl.locations:
                    t.updated(loc)

        rpr2 = rapper(rpr.id)
        btls = (rpr.battles, rpr1.battles, rpr2.battles)
        for btl, btl1, btl2 in zip(*btls):
            # Make sure the properties were changed
            self.ne(getattr(btl2,  'record'),  getattr(btl,  'record'))
            self.ne(getattr(btl2,  'name'),    getattr(btl,  'name'))
            self.ne(getattr(btl2,  'views'),   getattr(btl,  'views'))

            # Make user rpr1.battles props match those of rpr2
            self.eq(getattr(btl2,  'record'),  getattr(btl1,  'record'))
            self.eq(getattr(btl2,  'views'),   getattr(btl1,  'views'))
            self.ne(getattr(btl2,  'name'),    getattr(btl,   'name'))

            locs = btl.locations, btl1.locations, btl2.locations
            for loc, loc1, loc2 in zip(*locs):
                # Make sure the properties were changed
                self.ne(
                    getattr(loc2, 'description'), 
                    getattr(loc,  'description')
                )

                # Make user rpr1 locations props match those of rpr2
                self.eq(
                    getattr(loc2, 'description'), 
                    getattr(loc1, 'description')
                )

    def it_saves_and_loads_subentity_constituent(self):
        chrons = self.chronicles

        # Make sure the constituent is None for new composites
        pres = presentation.getvalid()

        chrons.clear()
        self.none(pres.artist)
        self.zero(chrons)

        self.zero(pres.brokenrules)

        # Test setting an entity constituent then test saving and loading
        sng = singer.getvalid()
        pres.artist = sng
        self.is_(sng, pres.artist)

        chrons.clear()
        pres.save()
        self.three(chrons)
        self.eq(chrons.where('entity',  sng).first.op,            'create')
        self.eq(chrons.where('entity',  sng.orm.super).first.op,  'create')
        self.eq(chrons.where('entity',  pres).first.op,           'create')

        # Load by artist then lazy-load presentations to test
        art1 = artist(pres.artist.id)
        self.one(art1.presentations)
        self.eq(art1.presentations.first.id, pres.id)

        # Load by presentation and lazy-load artist to test
        pres1 = presentation(pres.id)

        chrons.clear()
        self.eq(pres1.artist.id, pres.artist.id)
        self.one(chrons)
        self.eq(chrons.where('entity', pres1.artist).first.op,  'retrieve')

        sng1 = singer.getvalid()
        pres1.artist = sng1

        chrons.clear()
        pres1.save()

        self.three(chrons)
        self.eq(chrons.where('entity', sng1).first.op,  'create')
        self.eq(chrons.where('entity', sng1.orm.super).first.op, 'create')
        self.eq(chrons.where('entity', pres1).first.op, 'update')

        pres2 = presentation(pres1.id)
        self.eq(sng1.id, pres2.artist.id)
        self.ne(sng1.id, sng.id)

        # Test deeply-nested (>2)
        # Set entity constuents, save, load, test
       
        loc = location.getvalid()
        self.none(loc.presentation)

        loc.presentation = pres = presentation.getvalid()
        self.is_(pres, loc.presentation)

        chrons.clear()
        self.none(loc.presentation.artist)
        self.zero(chrons)

        loc.presentation.artist = sng = singer.getvalid()
        self.is_(sng, loc.presentation.artist)

        loc.save()

        self.four(chrons)
        self.eq(chrons.where('entity',  loc).first.op,               'create')
        self.eq(chrons.where('entity',  loc.presentation).first.op,  'create')
        self.eq(chrons.where('entity',  sng).first.op,               'create')
        self.eq(chrons.where('entity',  sng.orm.super).first.op,     'create')

        chrons.clear()
        loc1 = location(loc.id)
        pres1 = loc1.presentation

        self.eq(loc.id, loc1.id)
        self.eq(loc.presentation.id, loc1.presentation.id)
        self.eq(loc.presentation.artist.id, loc1.presentation.artist.id)

        self.three(chrons)
        self.eq(chrons.where('entity',  loc1).first.op,          'retrieve')
        self.eq(chrons.where('entity',  pres1).first.op,         'retrieve')
        self.eq(chrons.where('entity',  pres1.artist).first.op,  'retrieve')

        # Change the artist
        loc1.presentation.artist = sng1 = singer.getvalid()

        chrons.clear()
        loc1.save()

        self.three(chrons)
        pres1 = loc1.presentation

        self.eq(chrons.where('entity',  pres1).first.op,           'update')
        self.eq(chrons.where('entity',  sng1).first.op,            'create')
        self.eq(chrons.where('entity',  sng1.orm.super).first.op,  'create')

        loc2 = location(loc1.id)
        self.eq(loc1.presentation.artist.id, loc2.presentation.artist.id)
        self.ne(sng.id, loc2.presentation.artist.id)

        # NOTE Going up the graph, mutating attributes and persisting
        # lower in the graph won't work because of the problem of
        # infinite recursion.  The below tests demonstrate this.

        # Assign a new name
        name = uuid4().hex
        loc2.presentation.artist.presentations.first.name = name

        # The presentation objects here aren't the same reference so they will
        # have different states.
        self.ne(loc2.presentation.name, name)

        chrons.clear()
        loc2.save()

        self.zero(chrons)

        loc2 = location(loc2.id)

        self.one(chrons)
        self.eq(chrons.where('entity',  loc2).first.op,   'retrieve')

        # The above save() didn't save the new artist's presentation collection
        # so the new name will not be present in the reloaded presentation
        # object.
        self.ne(loc2.presentation.name, name)
        self.ne(loc2.presentation.artist.presentations.first.name, name)

    def it_saves_and_loads_subsubentity_constituent(self):
        # Make sure the constituent is None for new composites
        pres = presentation.getvalid()

        with self._chrontest() as t:
            t.run(lambda: pres.artist)

        self.none(pres.artist)

        self.zero(pres.brokenrules)

        # Test setting an entity constituent then test saving and
        # loading
        rpr = rapper.getvalid()
        pres.artist = rpr
        self.is_(rpr, pres.artist)

        with self._chrontest() as t:
            t.run(pres.save)
            t.created(rpr)
            t.created(rpr.orm.super)
            t.created(rpr.orm.super.orm.super)
            t.created(pres)

        # Load by artist then lazy-load presentations to test
        art1 = artist(pres.artist.id)
        self.one(art1.presentations)
        self.eq(art1.presentations.first.id, pres.id)

        # Load by presentation and lazy-load artist to test
        pres1 = presentation(pres.id)

        with self._chrontest() as t:
            t.run(lambda: pres1.artist)
            t.retrieved(pres1.artist)
           
        self.eq(pres1.artist.id, pres.artist.id)

        rpr1 = rapper.getvalid()
        pres1.artist = rpr1

        with self._chrontest() as t:
            t.run(pres1.save)
            t.created(rpr1)
            t.created(rpr1.orm.super)
            t.created(rpr1.orm.super.orm.super)
            t.updated(pres1)

        pres2 = presentation(pres1.id)
        self.eq(rpr1.id, pres2.artist.id)
        self.ne(rpr1.id, rpr.id)

        # Test deeply-nested (>2)
        # Set entity constuents, save, load, test
       
        loc = location.getvalid()
        self.none(loc.presentation)

        loc.presentation = pres = presentation.getvalid()
        self.is_(pres, loc.presentation)

        with self._chrontest() as t:
            t.run(lambda: loc.presentation.artist)

        self.none(loc.presentation.artist)

        loc.presentation.artist = rpr = rapper.getvalid()
        self.is_(rpr, loc.presentation.artist)

        with self._chrontest() as t:
            t.run(loc.save)
            t.created(loc)
            t.created(loc.presentation)
            t.created(rpr)
            t.created(rpr.orm.super)
            t.created(rpr.orm.super.orm.super)

        with self._chrontest() as t:
            def f():
                loc1 = location(loc.id)
                pres1 = loc1.presentation
                pres1.artist
                return loc1, pres1
            loc1, pres1 = t.run(f)

            t.retrieved(loc1)
            t.retrieved(pres1)
            t.retrieved(pres1.artist)

        self.eq(loc.id, loc1.id)
        self.eq(loc.presentation.id, loc1.presentation.id)
        self.eq(loc.presentation.artist.id, loc1.presentation.artist.id)

        # Change the artist
        loc1.presentation.artist = rpr1 = rapper.getvalid()

        with self._chrontest() as t:
            t.run(loc1.save)
            t.updated(loc1.presentation)
            t.created(rpr1)
            t.created(rpr1.orm.super)
            t.created(rpr1.orm.super.orm.super)

        loc2 = location(loc1.id)

        self.eq(
            loc1.presentation.artist.id, 
            loc2.presentation.artist.id
        )

        self.ne(rpr.id, loc2.presentation.artist.id)

        # NOTE: Going up the graph, mutating attributes and persisting
        # lower in the graph won't work because of the problem of
        # infinite recursion.  The below tests demonstrate this.  Assign
        # a new name
        name = uuid4().hex
        loc2.presentation.artist.presentations.first.name = name

        # The presentation objects here aren't the same reference so
        # they will have different states.
        self.ne(loc2.presentation.name, name)

        with self._chrontest() as t:
            t.run(loc2.save)

        with self._chrontest() as t:
            loc2 = t.run(lambda: location(loc2.id))
            t.retrieved(loc2)

        # The above save() didn't save the new artist's presentation
        # collection so the new name will not be present in the reloaded
        # presentation object.
        self.ne(loc2.presentation.name, name)
        self.ne(loc2.presentation.artist.presentations.first.name, name)

    def it_saves_and_loads_subentities_subentity_constituent(self):
        chrons = self.chronicles

        # Make sure the constituent is None for new composites
        conc = concert.getvalid()

        chrons.clear()
        self.none(conc.singer)
        self.expect(AttributeError, lambda: conc.artist)
        self.zero(chrons)

        self.zero(conc.brokenrules)

        # Test setting an entity constituent then test saving and loading
        sng = singer.getvalid()
        conc.singer = sng
        self.is_(sng, conc.singer)

        with self._chrontest() as t:
            t.run(conc.save)
            t.created(sng)
            t.created(sng.orm.super)
            t.created(conc)
            t.created(conc.orm.super)

        # Load by singer then lazy-load concerts to test
        sng1 = singer(conc.singer.id)
        self.one(sng1.concerts)
        self.eq(sng1.concerts.first.id, conc.id)

        # Load by concert and lazy-load singer to test
        conc1 = concert(conc.id)

        chrons.clear()
        self.eq(conc1.singer.id, conc.singer.id)

        self._chrons(conc1.singer,            'retrieve')
        self.one(chrons)

        sng1 = singer.getvalid()
        conc1.singer = sng1

        chrons.clear()
        conc1.save()

        self.four(chrons)
        self._chrons(sng1,             'create')
        self._chrons(sng1.orm.super,   'create')
        self._chrons(conc1,            'update')
        self._chrons(conc1.orm.super,  'update')

        conc2 = concert(conc1.id)
        self.eq(sng1.id, conc2.singer.id)
        self.ne(sng1.id, sng.id)

        # TODO Test deeply-nested (>2)
        # Set entity constuents, save, load, test

        # TODO We need to answer the question should loc.concert exist.
        # concert().locations exists, so it would seem that the answer
        # would be "yes". However, the logic for this would be strange
        # since we would need to query the mappings collection of each
        # subentities of the presentation collection to find a match.
        # Plus, this seems like a very unlikely way for someone to want
        # to use the ORM. I would like to wait to see if this comes up
        # in a real life situation before writing the logic and tests
        # for this. 
        """
        self.expect(AttributeError, lambda: loc.concert)
       
        loc = location.getvalid()
        self.none(loc.concert)

        loc.concert = conc = concert.getvalid()
        self.is_(conc, loc.concert)

        chrons.clear()
        self.none(loc.concert.singer)
        self.zero(chrons)

        loc.concert.singer = sng = singer.getvalid()
        self.is_(sng, loc.concert.singer)

        loc.save()

        self.four(chrons)
        self.eq(chrons.where('entity',  loc).first.op,               'create')
        self.eq(chrons.where('entity',  loc.concert).first.op,  'create')
        self.eq(chrons.where('entity',  sng).first.op,               'create')
        self.eq(chrons.where('entity',  sng.orm.super).first.op,     'create')

        chrons.clear()
        loc1 = location(loc.id)
        conc1 = loc1.concert

        self.eq(loc.id, loc1.id)
        self.eq(loc.concert.id, loc1.concert.id)
        self.eq(loc.concert.singer.id, loc1.concert.singer.id)

        self.three(chrons)
        self.eq(chrons.where('entity',  loc1).first.op,          'retrieve')
        self.eq(chrons.where('entity',  conc1).first.op,         'retrieve')
        self.eq(chrons.where('entity',  conc1.singer).first.op,  'retrieve')

        # Change the singer
        loc1.concert.singer = sng1 = singer.getvalid()

        chrons.clear()
        loc1.save()

        self.three(chrons)
        conc1 = loc1.concert

        self.eq(chrons.where('entity',  conc1).first.op,           'update')
        self.eq(chrons.where('entity',  sng1).first.op,            'create')
        self.eq(chrons.where('entity',  sng1.orm.super).first.op,  'create')

        loc2 = location(loc1.id)
        self.eq(loc1.concert.singer.id, loc2.concert.singer.id)
        self.ne(sng.id, loc2.concert.singer.id)

        # Note: Going up the graph, mutating attributes and persisting lower in
        # the graph won't work because of the problem of infinite recursion.
        # The below tests demonstrate this.

        # Assign a new name
        name = uuid4().hex
        loc2.concert.singer.concerts.first.name = name

        # The concert objects here aren't the same reference so they will
        # have different states.
        self.ne(loc2.concert.name, name)

        chrons.clear()
        loc2.save()

        self.zero(chrons)

        loc2 = location(loc2.id)

        self.one(chrons)
        self.eq(chrons.where('entity',  loc2).first.op,   'retrieve')

        # The above save() didn't save the new singer's concert collection
        # so the new name will not be present in the reloaded concert
        # object.
        self.ne(loc2.concert.name, name)
        self.ne(loc2.concert.singer.concerts.first.name, name)
        """

    def it_saves_and_loads_subsubentities_subsubentity_constituent(
        self):

        # Make sure the constituent is None for new composites
        btl = battle.getvalid()

        with self._chrontest() as t:
            def f():
                self.none(btl.rapper)
                self.expect(AttributeError, lambda: btl.singer)
                self.expect(AttributeError, lambda: btl.artist)
            t.run(f)

        self.zero(btl.brokenrules)

        # Test setting an entity constituent then test saving and
        # loading
        rpr = rapper.getvalid()
        btl.rapper = rpr
        self.is_(rpr, btl.rapper)

        with self._chrontest() as t:
            t.run(btl.save)
            t.created(rpr)
            t.created(rpr.orm.super)
            t.created(rpr.orm.super.orm.super)
            t.created(btl)
            t.created(btl.orm.super)
            t.created(btl.orm.super.orm.super)

        # Load by rapper then lazy-load battles to test
        rpr1 = rapper(btl.rapper.id)
        self.one(rpr1.battles)
        self.eq(rpr1.battles.first.id, btl.id)

        # Load by battle and lazy-load rapper to test
        btl1 = battle(btl.id)

        with self._chrontest() as t:
            t.run(lambda: self.eq(btl1.rapper.id, btl.rapper.id))
            t.retrieved(btl1.rapper)

        rpr1 = rapper.getvalid()
        btl1.rapper = rpr1

        with self._chrontest() as t:
            t.run(btl1.save)
            t.created(rpr1)
            t.created(rpr1.orm.super)
            t.created(rpr1.orm.super.orm.super)
            t.updated(btl1)
            t.updated(btl1.orm.super)
            t.updated(btl1.orm.super.orm.super)

        btl2 = battle(btl1.id)
        self.eq(rpr1.id, btl2.rapper.id)
        self.ne(rpr1.id, rpr.id)

    def subentity_constituents_break_entity(self):
        pres = presentation.getvalid()
        pres.artist = singer.getvalid()

        # Get max lengths for various properties
        presmax  =  presentation.  orm.  mappings['name'].         max
        locmax   =  location.      orm.  mappings['description'].  max
        artmax   =  artist.        orm.  mappings['firstname'].    max
        x = 'x'

        pres.artist.firstname = x * (artmax + 1)
        self.one(pres.brokenrules)
        self.broken(pres, 'firstname', 'fits')

        pres.artist.firstname = uuid4().hex # Unbreak
        self.zero(pres.brokenrules)

        loc = location.getvalid()
        loc.description = x * (locmax + 1) # break

        loc.presentation = presentation.getvalid()
        loc.presentation.name = x * (presmax + 1) # break

        loc.presentation.artist = singer.getvalid()
        loc.presentation.artist.firstname = x * (artmax + 1) # break

        self.three(loc.brokenrules)
        for prop in 'description', 'name', 'firstname':
            self.broken(loc, prop, 'fits')

    def subsubentity_constituents_break_entity(self):
        pres = presentation.getvalid()
        pres.artist = rapper.getvalid()

        # Get max lengths for various properties
        presmax  =  presentation.  orm.  mappings['name'].         max
        locmax   =  location.      orm.  mappings['description'].  max
        artmax   =  artist.        orm.  mappings['firstname'].    max
        x = 'x'

        pres.artist.firstname = x * (artmax + 1)
        self.one(pres.brokenrules)
        self.broken(pres, 'firstname', 'fits')

        pres.artist.firstname = uuid4().hex # Unbreak
        self.zero(pres.brokenrules)

        loc = location.getvalid()
        loc.description = x * (locmax + 1) # break

        loc.presentation = presentation.getvalid()
        loc.presentation.name = x * (presmax + 1) # break

        loc.presentation.artist = rapper.getvalid()
        loc.presentation.artist.firstname = x * (artmax + 1) # break

        self.three(loc.brokenrules)
        for prop in 'description', 'name', 'firstname':
            self.broken(loc, prop, 'fits')

    def subentity_constituents_break_subentity(self):
        conc = concert.getvalid()
        conc.singer = singer.getvalid()

        # Break rule that art.firstname should be a str
        conc.singer.firstname = 'x' * 256 # Break

        self.one(conc.brokenrules)
        self.broken(conc, 'firstname', 'fits')

        conc.singer.firstname = uuid4().hex # Unbreak
        self.zero(conc.brokenrules)

    def subsubentity_constituents_break_subsubentity(self):
        btl = battle.getvalid()
        btl.rapper = rapper.getvalid()

        # Break rule that art.firstname should be a str
        btl.rapper.firstname = 'x' * 256 # Break

        self.one(btl.brokenrules)
        self.broken(btl, 'firstname', 'fits')

        btl.rapper.firstname = uuid4().hex # Unbreak
        self.zero(btl.brokenrules)

    def it_rollsback_save_of_subentity_with_broken_constituents(self):
        sng = singer.getvalid()

        sng.presentations += presentation.getvalid()
        sng.presentations.last.name = uuid4().hex

        sng.presentations += presentation.getvalid()
        sng.presentations.last.name = uuid4().hex

        sng.concerts += concert.getvalid()
        sng.concerts.last.name = uuid4().hex

        # Cause the last presentation's invocation of save() to raise an
        # Exception to cause a rollback
        sng.presentations.last._save = lambda cur, followentitymapping: 1/0

        # Save expecting the ZeroDivisionError
        self.expect(ZeroDivisionError, lambda: sng.save())

        # Ensure state of sng was restored to original
        self.eq((True, False, False), sng.orm.persistencestate)

        # Ensure singer wasn't saved
        self.expect(db.RecordNotFoundError, lambda: singer(sng.id))

        # For each presentations and concerts, ensure state was not modified
        # and no presentation object was saved.
        for pres in sng.presentations:
            self.eq((True, False, False), pres.orm.persistencestate)
            self.expect(db.RecordNotFoundError, lambda: presentation(pres.id))

        for conc in sng.concerts:
            self.eq((True, False, False), conc.orm.persistencestate)
            self.expect(db.RecordNotFoundError, lambda: concert(conc.id))

    def it_rollsback_save_of_subsubentity_with_broken_constituents(
        self):
        rpr = rapper.getvalid()

        rpr.presentations += presentation.getvalid()
        rpr.presentations.last.name = uuid4().hex

        rpr.presentations += presentation.getvalid()
        rpr.presentations.last.name = uuid4().hex

        rpr.concerts += concert.getvalid()
        rpr.concerts.last.name = uuid4().hex

        # Cause the last presentation's invocation of save() to raise an
        # Exception to cause a rollback
        rpr.presentations.last._save = lambda cur, followentitymapping: 1/0

        # Save expecting the ZeroDivisionError
        self.expect(ZeroDivisionError, lambda: rpr.save())

        # Ensure state of rpr was restored to original
        self.eq((True, False, False), rpr.orm.persistencestate)

        # Ensure rapper wasn't saved
        self.expect(db.RecordNotFoundError, lambda: rapper(rpr.id))

        # For each presentations and concerts, ensure state was not
        # modified and no presentation object was saved.
        for pres in rpr.presentations:
            self.eq((True, False, False), pres.orm.persistencestate)
            self.expect(
                db.RecordNotFoundError, 
                lambda: presentation(pres.id)
            )

        for conc in rpr.concerts:
            self.eq((True, False, False), conc.orm.persistencestate)
            self.expect(
                db.RecordNotFoundError,
                lambda: concert(conc.id)
            )

    def it_deletes_subentities(self):
        # Create two singers
        sngs = singers()

        for _ in range(2):
            sngs += singer.getvalid()
            sngs.last.firstname = uuid4().hex
            sngs.last.lastname = uuid4().hex
        
        self.chronicles.clear()
        sngs.save()
        self.four(self.chronicles)

        sng = sngs.shift()
        self.one(sngs)
        self.one(sngs.orm.trash)

        self.chronicles.clear()
        sngs.save()
        self.two(self.chronicles)
        self._chrons(sng, 'delete')
        self._chrons(sng.orm.super, 'delete')

        for sng in sng, sng.orm.super:
            self.expect(db.RecordNotFoundError, lambda: singer(sng.id))
            
        # Ensure the remaining singer and artist still exists in database
        for sng in sngs.first, sngs.first.orm.super:
            self.expect(None, lambda: singer(sng.id))

    def it_deletes_subsubentities(self):
        # Create two rappers
        rprs = rappers()

        for _ in range(2):
            rprs += rapper.getvalid()
            rprs.last.firstname = uuid4().hex
            rprs.last.lastname = uuid4().hex
        
        with self._chrontest() as t:
            t.run(lambda: rprs.save())
            t.created(rprs.first)
            t.created(rprs.second)
            t.created(rprs.first.orm.super)
            t.created(rprs.second.orm.super)
            t.created(rprs.first.orm.super.orm.super)
            t.created(rprs.second.orm.super.orm.super)

        rpr = rprs.shift()
        self.one(rprs)
        self.one(rprs.orm.trash)

        with self._chrontest() as t:
            t.run(lambda: rprs.save())
            t.deleted(rpr)
            t.deleted(rpr.orm.super)
            t.deleted(rpr.orm.super.orm.super)

        while rpr:
            self.expect(db.RecordNotFoundError, lambda: rapper(rpr.id))
            rpr = rpr.orm.super
            
        # Ensure the remaining rapper and artist still exists in database
        rpr = rprs.first
        while rpr:
            self.expect(None, lambda: rapper(rpr.id))
            rpr = rpr.orm.super

    def it_doesnt_needlessly_save_subentity(self):
        chrons = self.chronicles

        sng = singer.getvalid()
        sng.firstname  =  uuid4().hex
        sng.lastname   =  uuid4().hex
        sng.voice      =  uuid4().hex

        for i in range(2):
            chrons.clear()
            sng.save()
            
            if i == 0:
                self.two(chrons)
                self.eq(chrons.where('entity', sng).first.op,           'create')
                self.eq(chrons.where('entity', sng.orm.super).first.op, 'create')
            elif i == 1:
                self.zero(chrons)

        # Dirty sng and save. Ensure the object was actually saved
        sng.firstname = uuid4().hex
        sng.voice     = uuid4().hex

        for i in range(2):
            chrons.clear()
            sng.save()
            if i == 0:
                self.two(chrons)
                self.eq(chrons.where('entity', sng).first.op,           'update')
                self.eq(chrons.where('entity', sng.orm.super).first.op, 'update')
            elif i == 1:
                self.zero(chrons)

        # Test constituents
        sng.presentations += presentation.getvalid()
        sng.concerts      += concert.getvalid()
        
        for i in range(2):
            chrons.clear()
            sng.save()

            if i == 0:
                self.three(chrons)
                self._chrons(sng.presentations.last,       'create')
                self._chrons(sng.concerts.last,            'create')
                self._chrons(sng.concerts.last.orm.super,  'create')
            elif i == 1:
                self.zero(chrons)

        # Test deeply-nested (>2) constituents
        sng.presentations.last.locations += location.getvalid()
        sng.concerts.last.locations      += location.getvalid()

        for i in range(2):
            chrons.clear()
            sng.save()

            if i == 0:
                self.two(chrons)
                self._chrons(sng.presentations.last.locations.last, 'create')
                self._chrons(sng.concerts.last.locations.last,      'create')
            elif i == 1:
                self.zero(chrons)

    def it_doesnt_needlessly_save_subsubentity(self):
        rpr = rapper.getvalid()
        rpr.firstname  =  uuid4().hex
        rpr.lastname   =  uuid4().hex
        rpr.voice      =  uuid4().hex
        rpr.stagename  =  uuid4().hex

        for i in range(2):
            with self._chrontest() as t:
                t.run(rpr.save)
                if i == 0:
                    t.created(rpr)
                    t.created(rpr.orm.super)
                    t.created(rpr.orm.super.orm.super)

                if t.chronicles.count > 3:
                    print(t.chronicles)
                    print(
                        '''
                        # SPORADIC The following came up in one test
                        # run: Aug 6 2019
                        eq in _chrontest at 523
                        expect: 4
                        actual: 3
                        message: test in 6446 at
                        it_doesnt_needlessly_save_subsubentity: Incorrect
                        chronicles count.
                        '''
                    )
                    B()


        # Dirty rpr and save. Ensure the object was actually saved
        rpr.firstname  =  uuid4().hex
        rpr.voice      =  uuid4().hex
        rpr.stagename  =  uuid4().hex

        for i in range(2):
            with self._chrontest() as t:
                t.run(rpr.save)
                if i == 0:
                    t.updated(rpr)
                    t.updated(rpr.orm.super)
                    t.updated(rpr.orm.super.orm.super)

        # Test constituents
        rpr.presentations += presentation.getvalid()
        rpr.concerts      += concert.getvalid()
        rpr.battles       += battle.getvalid()
        
        for i in range(2):
            with self._chrontest() as t:
                t.run(rpr.save)
                if i == 0:
                    t.created(rpr.presentations.last)
                    t.created(rpr.concerts.last)
                    t.created(rpr.concerts.last.orm.super)
                    t.created(rpr.battles.last)
                    t.created(rpr.battles.last.orm.super)
                    t.created(rpr.battles.last.orm.super.orm.super)

        # Test deeply-nested (>2) constituents
        rpr.presentations.last.locations += location.getvalid()
        rpr.concerts.last.locations      += location.getvalid()

        for i in range(2):
            with self._chrontest() as t:
                t.run(rpr.save)
                if i == 0:
                    t.created(rpr.presentations.last.locations.last)
                    t.created(rpr.concerts.last.locations.last)

    def it_calls_id_on_subentity(self):
        sng = singer.getvalid()

        self.true(hasattr(sng, 'id'))
        self.type(uuid.UUID, sng.id)
        self.zero(sng.brokenrules)

    def it_calls_id_on_subsubentity(self):
        rpr = rapper.getvalid()

        self.true(hasattr(rpr, 'id'))
        self.type(uuid.UUID, rpr.id)
        self.zero(rpr.brokenrules)

    def it_calls_save_on_subentity(self):
        chrons = self.chronicles
        sng = singer.getvalid()

        # Test creating and retrieving an entity
        self.eq((True, False, False), sng.orm.persistencestate)

        chrons.clear()
        sng.save()
        self.eq(chrons.where('entity', sng).first.op,           'create')
        self.eq(chrons.where('entity', sng.orm.super).first.op, 'create')

        self.eq((False, False, False), sng.orm.persistencestate)

        sng1 = singer(sng.id)

        self.eq((False, False, False), sng1.orm.persistencestate)

        for map in sng1.orm.mappings.all:
            if isinstance(map, orm.fieldmapping):
                self.eq(getattr(sng, map.name), getattr(sng1, map.name))

        # Test changing, saving and retrieving an entity
        sng1.firstname = uuid4().hex
        sng1.lastname  = uuid4().hex
        sng1.voice     = uuid4().hex
        sng1.lifeform  = uuid4().hex
        sng1.phone     = '2' * 7
        sng1.register  = uuid4().hex
        sng1.style     = uuid4().hex
        sng1.weight    = 1
        sng1.networth  =- 1
        sng1.dob       = datetime.now()
        sng1.password  = bytes([randint(0, 255) for _ in range(32)])
        sng1.ssn       = '2' * 11
        sng1.bio       = uuid4().hex
        sng1.email     = 'username1@domain.tld'
        sng1.title     = uuid4().hex[0]
        sng1.phone2    = uuid4().hex[0]
        sng1.email_1   = uuid4().hex[0]

        self.eq((False, True, False), sng1.orm.persistencestate)

        # Ensure that changing sng1's properties don't change sng's.
        # This problem is likely to not reoccur, but did come up in
        # early development.

        for prop in sng.orm.properties:
            if prop == 'artifacts':
                # The subentity-to-associations relationship has not
                # been implemented, so skip the call to sng.artifacts
                # TODO Implement the subentity-to-associations
                # relationships
                continue

            if prop == 'id':
                self.eq(getattr(sng1, prop), getattr(sng, prop), prop)
            else:
                if prop in ('createdat', 'updatedat'):
                    continue
                self.ne(getattr(sng1, prop), getattr(sng, prop), prop)

        sng1.save()

        self.eq((False, False, False), sng1.orm.persistencestate)

        sng2 = singer(sng.id)

        for map in sng2.orm.mappings.all:
            if isinstance(map, orm.fieldmapping):
                self.eq(getattr(sng1, map.name), getattr(sng2, map.name))

        # Ensure that the entity is persisted correctly when inherited and
        # non-inherited properties change.
        for prop in 'firstname', 'voice':
            sng = singer(sng.id)
            
            self.eq((False, False, False), sng.orm.persistencestate, prop)

            setattr(sng, prop, uuid4().hex)

            self.eq((False, True, False), sng.orm.persistencestate, prop)

            chrons.clear()
            sng.save()

            self.one(chrons)
            e = sng.orm.super if prop == 'firstname' else sng
            self.eq(chrons.where('entity', e).first.op, 'update')

            self.eq((False, False, False), sng.orm.persistencestate, prop)

    def it_calls_save_on_subsubentity(self):
        rpr = rapper.getvalid()

        # Test creating and retrieving an entity
        self.eq((True, False, False), rpr.orm.persistencestate)

        with self._chrontest() as t:
            t.run(lambda: rpr.save())
            t.created(rpr)
            t.created(rpr.orm.super)
            t.created(rpr.orm.super.orm.super)

        self.eq((False, False, False), rpr.orm.persistencestate)

        rpr1 = rapper(rpr.id)

        self.eq((False, False, False), rpr1.orm.persistencestate)

        for map in rpr1.orm.mappings.all:
            if isinstance(map, orm.fieldmapping):
                self.eq(getattr(rpr, map.name), getattr(rpr1, map.name))

        # Test changing, saving and retrieving an entity
        rpr1.firstname = uuid4().hex
        rpr1.lastname  = uuid4().hex
        rpr1.voice     = uuid4().hex
        rpr1.lifeform  = uuid4().hex
        rpr1.phone     = '2' * 7
        rpr1.register  = uuid4().hex
        rpr1.style     = uuid4().hex
        rpr1.weight    = 1
        rpr1.networth  =- 1
        rpr1.dob       = datetime.now()
        rpr1.password  = bytes([randint(0, 255) for _ in range(32)])
        rpr1.ssn       = '2' * 11
        rpr1.bio       = uuid4().hex
        rpr1.email     = 'username1@domain.tld'
        rpr1.title     = uuid4().hex[0]
        rpr1.phone2    = uuid4().hex[0]
        rpr1.email_1   = uuid4().hex[0]
        rpr1.nice      = randint(0, 255)
        rpr1.stagename = uuid4().hex
        rpr1.abilities = list('wackness')

        self.eq((False, True, False), rpr1.orm.persistencestate)

        # Ensure that changing rpr1's properties don't change rpr's.
        # This problem is likely to not reoccur, but did come up in
        # early development.
        for prop in rpr.orm.properties:
            if prop == 'artifacts':
                # The subentity-to-associations relationship has not
                # been implemented, so skip the call to rpr.artifacts
                # TODO Implement the subentity-to-associations
                # relationships
                continue

            if prop == 'id':
                self.eq(getattr(rpr1, prop), getattr(rpr, prop), prop)
            else:
                if prop in ('createdat', 'updatedat'):
                    continue
                self.ne(getattr(rpr1, prop), getattr(rpr, prop), prop)
    
        rpr1.save()

        self.eq((False, False, False), rpr1.orm.persistencestate)

        rpr2 = rapper(rpr.id)

        for map in rpr2.orm.mappings.all:
            if isinstance(map, orm.fieldmapping):
                self.eq(getattr(rpr1, map.name), getattr(rpr2, map.name))

        # Ensure that the entity is persisted correctly when inherited
        # and non-inherited properties change.
        for prop in 'firstname', 'voice', 'stagename':
            rpr = rapper(rpr.id)
            
            self.eq((False, False, False), rpr.orm.persistencestate)

            setattr(rpr, prop, uuid4().hex)

            self.eq((False, True, False), rpr.orm.persistencestate)

            with self._chrontest() as t:
                t.run(lambda: rpr.save())
                if prop == 'firstname':
                    e = rpr.orm.super.orm.super
                elif prop == 'voice':
                    e = rpr.orm.super
                elif prop == 'stagename':
                    e = rpr
                else:
                    raise ValueError()
                t.updated(e)

            self.eq((False, False, False), rpr.orm.persistencestate)

    def it_fails_to_save_broken_subentity(self):
        sng = singer()

        for prop in 'firstname', 'voice':
            setattr(sng, prop, 'x' * 256)

            self.broken(sng, prop, 'fits')

            try:
                sng.save()
            except Exception as ex:
                self.type(BrokenRulesError, ex)
            else:
                self.fail('Exception not thrown')

    def it_hard_deletes_subentity(self):
        chrons = self.chronicles
        sng = singer.getvalid()

        sng.save()

        chrons.clear()
        sng.delete()
        self.two(chrons)
        self.eq(chrons.where('entity', sng).first.op,           'delete')
        self.eq(chrons.where('entity', sng.orm.super).first.op, 'delete')

        self.eq((True, False, False), sng.orm.persistencestate)

        self.expect(db.RecordNotFoundError, lambda: artist(sng.id))
        self.expect(db.RecordNotFoundError, lambda: singer(sng.id))

        # Ensure that an invalid sng can be deleted
        sng = singer.getvalid()

        sng.firstname = uuid4().hex
        sng.lastname  = uuid4().hex
        sng.save()

        sng.lastname  = 'X' * 256 # Invalidate

        sng.delete()
        self.expect(db.RecordNotFoundError, lambda: artist(sng.id))
        self.expect(db.RecordNotFoundError, lambda: singer(sng.id))

    def it_hard_deletes_subsubentity(self):
        rpr = rapper.getvalid()

        rpr.save()

        with self._chrontest() as t:
            t.run(rpr.delete)
            t.deleted(rpr)
            t.deleted(rpr.orm.super)
            t.deleted(rpr.orm.super.orm.super)

        self.eq((True, False, False), rpr.orm.persistencestate)

        es = [rpr.orm.entity] + rpr.orm.entity.orm.superclasess
        for e in es:
            self.expect(db.RecordNotFoundError, lambda: e(rpr.id))

        # Ensure that an invalid rpr can be deleted
        rpr = rapper.getvalid()

        rpr.firstname = uuid4().hex
        rpr.lastname  = uuid4().hex
        rpr.save()

        rpr.lastname  = 'X' * 256 # Invalidate

        self.false(rpr.isvalid)

        rpr.delete()
        for e in es:
            self.expect(db.RecordNotFoundError, lambda: e(rpr.id))

    def it_deletes_from_subentitys_entities_collections(self):
        chrons = self.chronicles

        # Create singer with a presentation and save
        sng = singer.getvalid()
        pres = presentation.getvalid()
        sng.presentations += pres
        loc = location.getvalid()
        locs = sng.presentations.last.locations 
        locs += loc
        sng.save()

        # Reload
        sng = singer(sng.id)

        # Test presentations and its trash collection
        self.one(sng.presentations)
        self.zero(sng.presentations.orm.trash)
        
        self.one(sng.presentations.first.locations)
        self.zero(sng.presentations.first.locations.orm.trash)

        # Remove the presentation
        rmsng = sng.presentations.pop()

        # Test presentations and its trash collection
        self.zero(sng.presentations)
        self.one(sng.presentations.orm.trash)

        self.one(sng.presentations.orm.trash.first.locations)
        self.zero(sng.presentations.orm.trash.first.locations.orm.trash)

        chrons.clear()
        sng.save()
        self.two(chrons)
        self._chrons(rmsng, 'delete')
        self._chrons(rmsng.locations.first, 'delete')
        
        sng = singer(sng.id)
        self.zero(sng.presentations)
        self.zero(sng.presentations.orm.trash)

        self.expect(db.RecordNotFoundError, lambda: presentation(pres.id))
        self.expect(db.RecordNotFoundError, lambda: location(loc.id))

    def it_deletes_from_subsubentitys_entities_collections(self):
        # Create rapper with a presentation and save
        rpr = rapper.getvalid()
        pres = presentation.getvalid()
        rpr.presentations += pres
        loc = location.getvalid()
        locs = rpr.presentations.last.locations 
        locs += loc
        rpr.save()

        # Reload
        rpr = rapper(rpr.id)

        # Test presentations and its trash collection
        self.one(rpr.presentations)
        self.zero(rpr.presentations.orm.trash)
        
        self.one(rpr.presentations.first.locations)
        self.zero(rpr.presentations.first.locations.orm.trash)

        # Remove the presentation
        rmrpr = rpr.presentations.pop()

        # Test presentations and its trash collection
        self.zero(rpr.presentations)
        self.one(rpr.presentations.orm.trash)

        self.one(
            rpr.presentations.orm.trash.first.locations)

        self.zero(
            rpr.presentations.orm.trash.first.locations.orm.trash)

        with self._chrontest() as t:
            t.run(rpr.save)
            t.deleted(rmrpr)
            t.deleted(rmrpr.locations.first)

        rpr = rapper(rpr.id)
        self.zero(rpr.presentations)
        self.zero(rpr.presentations.orm.trash)

        self.expect(
            db.RecordNotFoundError, 
            lambda: presentation(pres.id)
        )

        self.expect(
            db.RecordNotFoundError, 
            lambda: location(loc.id)
        )

    def it_deletes_from_subentitys_subentities_collections(self):
        chrons = self.chronicles

        # Create singer with a concert and save
        sng = singer.getvalid()
        conc = concert.getvalid()
        sng.concerts += conc
        loc = location.getvalid()
        sng.concerts.last.locations += loc
        sng.save()

        # Reload
        sng = singer(sng.id)

        # Test concerts and its trash collection
        self.one(sng.concerts)
        self.zero(sng.concerts.orm.trash)

        self.one(sng.concerts.first.locations)
        self.zero(sng.concerts.first.locations.orm.trash)

        # Remove the concert
        rmconc = sng.concerts.pop()

        # Test concerts and its trash collection
        self.zero(sng.concerts)
        self.one(sng.concerts.orm.trash)

        self.one(sng.concerts.orm.trash.first.locations)
        self.zero(sng.concerts.orm.trash.first.locations.orm.trash)

        chrons.clear()
        sng.save()

        self.three(chrons)
        self._chrons(rmconc, 'delete')
        self._chrons(rmconc.orm.super, 'delete')
        self._chrons(rmconc.locations.first, 'delete')

        sng = singer(sng.id)
        self.zero(sng.concerts)
        self.zero(sng.concerts.orm.trash)

        self.expect(db.RecordNotFoundError, lambda: concert(conc.id))
        self.expect(db.RecordNotFoundError, lambda: location(loc.id))

    def it_deletes_from_subsubentitys_subsubentities_collections(self):
        # Create rapper with a battle and save
        rpr = rapper.getvalid()
        btl = battle.getvalid()
        rpr.battles += btl
        loc = location.getvalid()
        rpr.battles.last.locations += loc
        rpr.save()

        # Reload
        rpr = rapper(rpr.id)

        # Test battles and its trash collection
        self.one(rpr.battles)
        self.zero(rpr.battles.orm.trash)

        self.one(rpr.battles.first.locations)
        self.zero(rpr.battles.first.locations.orm.trash)

        # Remove the battle
        rmbtl = rpr.battles.pop()

        # Test battles and its trash collection
        self.zero(rpr.battles)
        self.one(rpr.battles.orm.trash)

        self.one(rpr.battles.orm.trash.first.locations)
        self.zero(rpr.battles.orm.trash.first.locations.orm.trash)

        with self._chrontest() as t:
            t.run(rpr.save)
            t.deleted(rmbtl)
            t.deleted(rmbtl.orm.super)
            t.deleted(rmbtl.orm.super.orm.super)
            t.deleted(rmbtl.locations.first,)

        rpr = rapper(rpr.id)
        self.zero(rpr.battles)
        self.zero(rpr.battles.orm.trash)

        self.expect(db.RecordNotFoundError, lambda: battle(btl.id))
        self.expect(db.RecordNotFoundError, lambda: location(loc.id))

    def _create_join_test_data(self):
        ''' Create test data to be used by the outer/inner join tests. '''

        for c in (artist, presentation, location, artist_artifact, artifact):
            c.orm.truncate()

        # The artist entities and constituents will have sequential indexes to
        # query against.
        arts = artists()
        for i in range(4):
            art = artist.getvalid()
            art.firstname = 'fn-' + str(i)
            art.lastname = 'ln-'  + str(i + 1)
            arts += art

            for j in range(4):
                art.locations += location.getvalid()
                art.locations.last.address = 'art-loc-addr-' + str(j)
                art.locations.last.description = 'art-loc-desc-' + str(j + 1)
                
            for k in range(4):
                art.presentations += presentation.getvalid()
                pres = art.presentations.last
                pres.name = 'pres-name-' + str(k)
                pres.description = 'pres-desc-' + str(k + 1) + '-' + str(i)

                for l in range(4):
                    pres.locations += location.getvalid()
                    pres.locations.last.address = 'pres-loc-addr-' + str(l)
                    pres.locations.last.description ='pres-loc-desc-' +  str(l + 1)

            for k in range(4):
                aa = artist_artifact.getvalid()
                aa.role = 'art-art_fact-role-' + str(k)
                aa.planet = 'art-art_fact-planet-' + str(k + 1)
                fact = artifact.getvalid()

                aa.artifact = fact
                fact.title = 'art-art_fact-fact-title-' + str(k)
                fact.description = 'art-art_fact-fact-desc-' + str(k + 1)

                # TODO:OPT Even though art.orm.isnew, artist_artifacts
                # is still loaded from the database. There should be a
                # check that ensures this doesn't happen. This could
                # lead to a large performance boast.
                art.artist_artifacts += aa

                for l in range(4):
                    comp = component.getvalid()
                    comp.name = 'art-art_fact-role-fact-comp-name' + str(l)
                    fact.components += comp

        arts.save()

        return arts

    def it_calls_innerjoin_on_entities_with_BETWEEN_clauses(self):
        arts = artists()
        for i in range(8):
            art = artist.getvalid()
            art.weight = i

            aa = artist_artifact.getvalid()
            art.artist_artifacts += aa
            aa.artifact = artifact.getvalid()
            aa.artifact.weight = i + 10

            arts += art

        arts.save()

        for op in '', 'NOT':
            # Load an innerjoin where both tables have [NOT] IN where
            # clause
            # 	SELECT *
            # 	FROM artists
            # 	INNER JOIN artist_artifacts AS `artists.artist_artifacts`
            # 		ON `artists`.id = `artists.artist_artifacts`.artistid
            # 	INNER JOIN artifacts AS `artists.artist_artifacts.artifacts`
            # 		ON `artists.artist_artifacts`.artifactid = `artists.artist_artifacts.artifacts`.id
            # 	WHERE (`artists`.firstname [NOT] IN (%s, %s))
            # 	AND (`artists.artist_artifacts.artifacts`.title[NOT]  IN (%s, %s))

            arts1 = artists('weight %s BETWEEN 0 AND 1' % op, ()).join(
                        artifacts('weight %s BETWEEN 10 AND 11' %op, ())
                    )

            if op == 'NOT':
                self.six(arts1)
            else:
                self.two(arts1)

            for art1 in arts1:
                if op == 'NOT':
                    self.gt(art1.weight, 1)
                else:
                    self.le(art1.weight, 1)

                self.one(art1.artifacts)

                fact1 = art1.artifacts.first
                
                if op == 'NOT':
                    self.gt(fact1.weight, 11)
                else:
                    self.le(fact1.weight, 11)

        artwhere = 'weight BETWEEN 0 AND 1 OR weight BETWEEN 3 AND 4'
        factwhere = 'weight BETWEEN 10 AND 11 OR weight BETWEEN 13 AND 14'
        arts1 = artists(artwhere, ()).join(
                    artifacts(factwhere, ())
                )

        self.four(arts1)

        for art1 in arts1:
            self.true(art1.weight in (0, 1, 3, 4))

            self.one(art1.artifacts)

            fact1 = art1.artifacts.first
            
            self.true(fact1.weight in (10, 11, 13, 14))

    def it_calls_innerjoin_on_entities_with_IN_clauses(self):
        for e in artists, artifacts:
            e.orm.truncate()
        arts = artists()
        for i in range(8):
            art = artist.getvalid()
            art.firstname = uuid4().hex

            aa = artist_artifact.getvalid()
            art.artist_artifacts += aa
            aa.artifact = artifact.getvalid()
            aa.artifact.title = uuid4().hex

            arts += art

        arts.save()

        for op in '', 'NOT':
            # Load an innerjoin where both tables have [NOT] IN where clause
            # 	SELECT *
            # 	FROM artists
            # 	INNER JOIN artist_artifacts AS `artists.artist_artifacts`
            # 		ON `artists`.id = `artists.artist_artifacts`.artistid
            # 	INNER JOIN artifacts AS `artists.artist_artifacts.artifacts`
            # 		ON `artists.artist_artifacts`.artifactid = `artists.artist_artifacts.artifacts`.id
            # 	WHERE (`artists`.firstname [NOT] IN (%s, %s))
            # 	AND (`artists.artist_artifacts.artifacts`.title[NOT]  IN (%s, %s))

            firstnames = ['\'%s\'' % x for x in arts.pluck('firstname')]
            artwhere = 'firstname %s IN (%s)' % (op, ', '.join(firstnames[:4]))

            titles = ['\'%s\'' % x.first.title for x in arts.pluck('artifacts')]
            factwhere = 'title %s IN (%s)' % (op, ', '.join(titles[:4]))

            arts1 = artists(artwhere, ()) & artifacts(factwhere, ())

            self.four(arts1)
            titles = [x[1:-1] for x in titles]

            for art1 in arts1:
                if op == 'NOT':
                    self.true(art1.firstname not in arts.pluck('firstname')[:4])
                else:
                    self.true(art1.firstname in arts.pluck('firstname')[:4])

                self.one(art1.artifacts)

                fact1 = art1.artifacts.first
                
                if op == 'NOT':
                    self.true(fact1.title not in titles[:4])
                else:
                    self.true(fact1.title in titles[:4])

        # Test using conjoined IN clauses in artists and artifacts.
        # artwhere
        artwhere1 = 'firstname IN (%s)' % (', '.join(firstnames[:2]))
        artwhere2 = 'firstname IN (%s)' % (', '.join(firstnames[2:4]))

        artwhere = '%s OR %s' % (artwhere1, artwhere2)

        # factwhere
        titles = ['\'%s\'' % x.first.title for x in arts.pluck('artifacts')]
        factwhere1 = 'title IN (%s)' % (', '.join(titles[:2]))
        factwhere2 = 'title IN (%s)' % (', '.join(titles[2:4]))

        factwhere = '%s OR %s' % (factwhere1, factwhere2)

        arts1 = artists(artwhere, ()).join(
            artifacts(factwhere, ())
        )

        self.four(arts1)

        titles = [x[1:-1] for x in titles]

        for art1 in arts1:
            self.true(art1.firstname in arts.pluck('firstname')[:4])
            self.one(art1.artifacts)
            fact1 = art1.artifacts.first
            self.true(fact1.title in titles[:4])

    def it_calls_innerjoin_on_entities_with_MATCH_clauses(self):
        artkeywords, factkeywords = [], []

        arts = artists()
        for i in range(2):
            art = artist.getvalid()
            artkeyword, factkeyword = uuid4().hex, uuid4().hex
            artkeywords.append(artkeyword)
            factkeywords.append(factkeyword)
            art.bio = 'one two three %s five six' % artkeyword
            aa = artist_artifact.getvalid()

            art.artist_artifacts += aa

            aa.artifact = artifact.getvalid()

            aa.artifact.title = 'one two three %s five six' % factkeyword

            arts += art

        arts.save()

        # Query where composite and constituent have one MATCH clase each
        arts1 = artists("match(bio) against ('%s')" % artkeywords[0], ()).join(
            artifacts(
                "match(title, description) against ('%s')" %  factkeywords[0], ()
            )
        )

        # Query where composite and constituent have two MATCH clase each
        artmatch = (
            "MATCH(bio) AGAINST ('%s') OR "
            "MATCH(bio) AGAINST ('%s')"
        )

        factmatch = (
            "MATCH(title, description) AGAINST ('%s') OR "
            "MATCH(title, description) AGAINST ('%s')"
        )

        artmatch  %= tuple(artkeywords)
        factmatch %= tuple(factkeywords)

        arts1 = artists(artmatch, ()) & artifacts(factmatch, ())

        self.two(arts1)

        arts.sort()
        arts1.sort()

        for art, art1 in zip(arts, arts1):
            self.eq(art.id, art1.id)
            self.eq(art.artifacts.first.id, art1.artifacts.first.id)

    def it_calls_innerjoin_on_associations(self):
        arts = self._create_join_test_data()

        arts.sort()

        fff = False, False, False

        # Test artists joined with artist_artifacts with no condititons
        arts1 = artists()
        arts1 &= artist_artifacts()

        self.one(arts1.orm.joins)

        self.four(arts1)

        arts1.sort()
        
        self.chronicles.clear()

        for art, art1 in zip(arts, arts1):
            self.eq(art.id, art1.id)

            self.eq(fff, art1.orm.persistencestate)

            self.four(art1.artist_artifacts)

            art.artist_artifacts.sort()
            art1.artist_artifacts.sort()

            for aa, aa1 in zip(art.artist_artifacts, art1.artist_artifacts):
                self.eq(aa.id, aa.id)

                self.eq(fff, aa1.orm.persistencestate)

                aa1.artifact

                self.eq(aa.artifact.id, aa1.artifact.id)
                
                self.is_(aa1.artifact, self.chronicles.last.entity)
                self.eq('retrieve', self.chronicles.last.op)

                self.eq(aa1.artist.id, art1.id)

        # NOTE The above will lazy-load aa1.artifact 16 times
        self.count(16, self.chronicles)

        # Test artists joined with artist_artifacts where the association has a
        # conditional
        arts1 = artists.join(
            artist_artifacts('role = %s', ('art-art_fact-role-0',))
        )

        self.one(arts1.orm.joins)

        self.four(arts1)

        self.chronicles.clear()

        arts1.sort()
        for art, art1 in zip(arts, arts1):
            self.eq(art.id, art1.id)

            self.eq(fff, art1.orm.persistencestate)

            self.one(art1.artist_artifacts)

            aa1 = art1.artist_artifacts.first
            self.eq(aa1.role, 'art-art_fact-role-0')
            self.eq(aa1.artifactid, aa1.artifact.id)

            self.eq(fff, aa1.orm.persistencestate)

            # The call to aa1.artifact wil lazy-load artifact which will add to
            # self.chronicles
            self.eq('retrieve', self.chronicles.last.op)

            self.is_(aa1.artifact, self.chronicles.last.entity)

            self.eq(fff, aa1.artifact.orm.persistencestate)

        # NOTE This wil lazy-load aa1.artifact 4 times
        self.four(self.chronicles)

        # Test unconditionally joining the associated entities collecties
        # (artist_artifacts) with its composite (artifacts)
        for b in False, True:
            if b:
                # Implicitly join artist_artifact
                arts1 = artists.join(artifacts)
            else:
                # Explicitly join artist_artifact
                arts1 = artists() 
                arts1 &= artist_artifacts & artifacts

            self.one(arts1.orm.joins)
            self.type(artist_artifacts, arts1.orm.joins.first.entities)
            self.one(arts1.orm.joins.first.entities.orm.joins)
            facts = arts1.orm.joins.first.entities.orm.joins.first.entities
            self.type(artifacts, facts)

            arts1.sort()

            self.chronicles.clear()

            self.four(arts1)

            for art, art1 in zip(arts, arts1):
                self.eq(art.id, art1.id)

                self.eq(fff, art1.orm.persistencestate)

                self.four(art1.artist_artifacts)

                art.artist_artifacts.sort()
                art1.artist_artifacts.sort()

                for aa, aa1 in zip(art.artist_artifacts, art1.artist_artifacts):
                    self.eq(fff, aa1.orm.persistencestate)
                    self.eq(aa.id, aa.id)
                    self.eq(aa.artifact.id, aa1.artifact.id)

            self.zero(self.chronicles)

        # Test joining the associated entities collecties (artist_artifacts)
        # with its composite (artifacts) where the composite's join is
        # conditional.
        for b in True, False:
            if b:
                # Explicitly join artist_artifacts
                arts1 = artists() 
                arts1 &= artist_artifacts & artifacts('description = %s', ('art-art_fact-fact-desc-1',))
            else:
                # Implicitly join artist_artifacts
                arts1 = artists() & artifacts('description = %s', ('art-art_fact-fact-desc-1',))

            self.one(arts1.orm.joins)
            self.type(artist_artifacts, arts1.orm.joins.first.entities)
            self.one(arts1.orm.joins.first.entities.orm.joins)
            facts = arts1.orm.joins.first.entities.orm.joins.first.entities
            self.type(artifacts, facts)

            arts1.sort()

            self.four(arts1)

            self.chronicles.clear()
            for art, art1 in zip(arts, arts1):
                self.eq(fff, art1.orm.persistencestate)
                self.eq(art.id, art1.id)

                aas = art1.artist_artifacts
                self.one(aas)
                self.eq('art-art_fact-fact-desc-1', aas.first.artifact.description)
                self.eq(fff, aas.first.orm.persistencestate)

            self.zero(self.chronicles)

        # Test joining the associated entities collecties (artist_artifacts)
        # with its composite (artifacts) where the composite's join is
        # conditional along with the other two.
        arts1 =  artists('firstname = %s', ('fn-1')) 
        arts1 &= artist_artifacts('role = %s', ('art-art_fact-role-0',)) & \
                 artifacts('description = %s', ('art-art_fact-fact-desc-1',))

        self.one(arts1)

        self.chronicles.clear()
        self.eq('fn-1', arts1.first.firstname)

        aas1 = arts1.first.artist_artifacts
        self.one(aas1)
        self.eq(fff, aas1.first.orm.persistencestate)
        self.eq('art-art_fact-role-0', aas1.first.role)
        self.eq('art-art_fact-fact-desc-1', aas1.first.artifact.description)

        self.zero(self.chronicles)

        # Test joining a constituent (component) of the composite (artifacts)
        # of the association (artist_artifacts) without conditions.
        for b in True, False:
            if b:
                # Explicitly join the associations (artist_artifacts())
                arts1 = artists.join(
                            artist_artifacts.join(
                                artifacts & components
                            )
                        )
            else:
                # Implicitly join the associations (artist_artifacts())
                arts1 =  artists.join(
                            artifacts & components
                         )

            self.four(arts1)

            arts1.sort()

            self.chronicles.clear()

            for art, art1 in zip(arts, arts1):
                self.eq(fff, art1.orm.persistencestate)
                self.eq(art.id, art1.id)
                aas = art.artist_artifacts.sorted()
                aas1 = art1.artist_artifacts.sorted()
                self.four(aas1)

                for aa, aa1 in zip(aas, aas1):
                    self.eq(fff, aa1.orm.persistencestate)
                    self.eq(aa.id, aa1.id)
                    fact = aa.artifact
                    fact1 = aa1.artifact
                    self.eq(fff, fact1.orm.persistencestate)

                    self.eq(fact.id, fact1.id)

                    comps = fact.components.sorted()
                    comps1 = fact1.components.sorted()

                    self.four(comps1)

                    for comp, comp1 in zip(comps, comps1):
                        self.eq(fff, comp1.orm.persistencestate)
                        self.eq(comp.id, comp1.id)

            self.zero(self.chronicles)

        # Test joining a constituent (component) of the composite (artifacts)
        # of the association (artist_artifacts) with conditions.
        aarole = 'art-art_fact-role-1'
        facttitle = 'art-art_fact-fact-title-1'
        compname = 'art-art_fact-role-fact-comp-name1'
        arts1 =  artists() & (
                    artist_artifacts(role = aarole) & (
                        artifacts(title = facttitle) & components(name = compname)
                    )
                 )

        self.four(arts1)

        arts1.sort()

        self.chronicles.clear()

        for art, art1 in zip(arts, arts1):
            self.eq(fff, art1.orm.persistencestate)

            self.eq(art.id, art1.id)
            aas1 = art1.artist_artifacts
            self.one(aas1)

            self.eq(aarole, aas1.first.role)
            self.eq(fff, aas1.first.orm.persistencestate)

            self.eq(facttitle, aas1.first.artifact.title)
            self.eq(fff, aas1.first.artifact.orm.persistencestate)

            self.one(aas1.first.artifact.components)

            self.eq(compname, aas1.first.artifact.components.first.name)
            self.eq(fff, aas1.first.artifact.components.first.orm.persistencestate)

        self.zero(self.chronicles)

    def it_calls_outerjoin(self):
        # Outer join artists with presentations; no predicates
        arts1 = artists()
        press1 = presentations()

        # I don't currently see the point in OUTER LEFT JOINs in ORMs, so,
        # until a use case is presented, we will raise a NotImplementedError
        self.expect(NotImplementedError, lambda: arts1.outerjoin(press1))
        
    def it_ensures_that_the_match_columns_have_full_text_indexes(self):
        exprs = (
            "match (firstname) against ('keyword') and firstname = 1",
            "firstname = 1 and match (lastname) against ('keyword')",
        )

        for expr in exprs:
            self.expect(orm.invalidcolumn, lambda: artists(expr, ()))

        exprs = (
            "match (bio) against ('keyword') and firstname = 1",
            "firstname = 1 and match (bio) against ('keyword')",
        )

        for expr in exprs:
            self.expect(None, lambda: artists(expr, ()))

    def it_demand_that_the_column_exists(self):
        exprs = (
            "notacolumn = 'value'",
            "firstname = 'value' or notacolumn = 'value'",
            "notacolumn between 'value' and 'othervalue'",
            "match (notacolumn) against ('keyword') and firstname = 1",
            "firstname = 1 and match (notacolumn) against ('keyword')",
            "match (bio) against ('keyword') and notacolumn = 1",
            "notacolumn = 1 and match (bio) against ('keyword')",
        )

        for expr in exprs:
            self.expect(orm.invalidcolumn, lambda: artists(expr, ()))

    def it_parameterizes_predicate(self):
        ''' Ensure that the literals in predicates get replaced with
        placeholders and that the literals are moved to the correct 
        positions in the where.args list. '''

        # TODO With the addition of this feature, we can remove the
        # requirement that an empty tuple be given as the second
        # argument here. It also seems possible that we remove the args
        # tuple altogether since it no longer seems necessary. NOTE, on
        # the other hand, we may want to keep the argument parameter for
        # binary queries, e.g.,:
        #
        #     artist('id = %s', (uuid.bytes,))
        #
        # Writing the above using string concatenation is difficult.
        #
        # HOWEVER: Given that the predicate parser
        # (`predicate._parse()`) has not been thoroughly review by
        # security specialists, it is considered unsafe to rely on it to
        # correctly identify literals and columns in WHERE predicates.
        # Because of this, until we have a proof that the predicate
        # parser is invincible to malicious attacts, we should continue
        # to insist that the user use the `args` tuple to pass in
        # varient values when querying entities collections so the
        # underlying MySQL library can safely deal with these arguments
        # seperately.

        arts = artists("firstname = '1234'", ())
        self.eq("1234", arts.orm.where.args[0])
        self.eq("%s", arts.orm.where.predicate.operands[1])

        arts = artists("firstname = '1234' or lastname = '5678'", ())
        self.eq("1234", arts.orm.where.args[0])
        self.eq("5678", arts.orm.where.args[1])
        for i, pred in enumerate(arts.orm.where.predicate):
            self.eq("%s", pred.operands[1])
            self.lt(i, 2)

        expr = (
            "firstname between '1234' and '5678' or "
            "lastname  between '2345' and '6789'"
        )

        arts = artists(expr, ())
        self.eq("1234", arts.orm.where.args[0])
        self.eq("5678", arts.orm.where.args[1])
        self.eq("2345", arts.orm.where.args[2])
        self.eq("6789", arts.orm.where.args[3])
        for i, pred in enumerate(arts.orm.where.predicate):
            self.eq("%s", pred.operands[1])
            self.lt(i, 2)

    def it_raises_exception_when_a_non_existing_column_is_referenced(self):
        self.expect(orm.invalidcolumn, lambda: artists(notacolumn = 1234))

    def it_raises_exception_when_bytes_type_is_compared_to_nonbinary(
        self):

        # TODO This should raise an exception
        arts1 = artists('id = 123', ())
        return
        arts1 &= artifacts()

        arts1.orm.load()

    def it_calls_innerjoin_on_entities_and_writes_new_records(self):
        arts = self._create_join_test_data()
        arts.sort()

        arts1 = artists() & (artifacts() & components())

        # Explicitly load artists->artifacts->components. Add an entry to
        # `arts1` and make sure that the new record persists.
        arts1.orm.load()

        art1 = artist.getvalid()
        arts1 += art1
        aas1 = art1.artist_artifacts
        aas1 += artist_artifact.getvalid()
        aas1.last.artifact = artifact.getvalid()
        aas1.last.artifact.components += component.getvalid()
        arts1.save()

        art2 = None
        def instantiate():
            nonlocal art2
            art2 = artist(art1.id)

        self.expect(None, instantiate)

        self.eq(art1.id, art2.id)

        aas2 = art2.artist_artifacts
        facts2 = art2.artifacts
        self.one(aas2)
        self.one(facts2)

        self.eq(art1.artist_artifacts.last.id, aas2.last.id)
        self.eq(art1.artifacts.last.id, facts2.last.id)

        comps2 = facts2.first.components
        self.one(comps2)
        
        self.eq(art1.artifacts.last.components.last.id,
                comps2.last.id)

        # Reload using the explicit loading, join method and update the record
        # added above. Ensure that the new data presists.
        arts3 = artists() & (artifacts() & components())
        arts3.orm.load()
        art3 = arts3[art2.id]
        newval = uuid4().hex

        art3.firstname = newval
        art3.artist_artifacts.first.role = newval
        art3.artifacts.first.title = newval
        art3.artifacts.first.components.first.name = newval

        arts3.save()

        art4 = artist(art3.id)

        self.eq(newval, art4.firstname)
        self.eq(newval, art4.artist_artifacts.first.role)
        self.eq(newval, art4.artifacts.first.title)
        self.eq(newval, art4.artifacts.first.components.first.name)

    def it_calls_innerjoin_on_entities(self):
        fff = False, False, False

        def join(joiner, joinee, type):
            if type in ('innerjoin', 'join'):
                getattr(joiner, type)(joinee)
            elif type  == 'standard':
                joiner = joiner & joinee
            elif type  == 'inplace':
                joiner &= joinee

            # Incorrect implementation of & and &= can nullify `joiner`, even
            # though the actual join was successful, so ensure `joiner` is
            # notnone
            self.notnone(joiner)

        arts = self._create_join_test_data()

        jointypes = 'innerjoin', 'join', 'standard', 'inplace', 'class'

        # Inner join where only artist has a where clause
        for t in jointypes:
            arts1 = artists(firstname = 'fn-0')

            if t == 'class':
                join(arts1, presentations, 'innerjoin')
                press = arts1.orm.joins.last.entities
                join(press, locations, 'innerjoin')
                locs = press.orm.joins.last.entities
                join(arts1, locations, 'innerjoin')
                artlocs = arts1.orm.joins.last.entities
            else:
                press = presentations()
                locs = locations()
                artlocs = locations()
                join(arts1, press, t)
                join(press, locs, t)
                join(arts1, artlocs, t)

            self.two(arts1.orm.joins)
            self.one(press.orm.joins)
            self.zero(locs.orm.joins)

            # Test
            self.one(arts1)

            self.chronicles.clear()

            art1 = arts1.first
            self.eq(arts.first.id, art1.id)

            self.eq(fff, art1.orm.persistencestate)

            press = arts.first.presentations.sorted()
            press1 = art1.presentations.sorted()

            self.four(press1)

            locs = arts.first.locations.sorted()
            locs1 = art1.locations.sorted() 
            self.four(locs1)

            for loc, loc1 in zip(locs, locs1):
                self.eq(fff, loc.orm.persistencestate)
                self.eq(loc.id, loc1.id)

            for pres, pres1 in zip(press, press1):
                self.eq(fff, pres.orm.persistencestate)
                self.eq(pres.id, pres1.id)

                locs = pres.locations.sorted()
                locs1 = pres1.locations.sorted() 
                self.four(pres1.locations)

                for loc, loc1 in zip(locs, locs1):
                    self.eq(fff, loc.orm.persistencestate)
                    self.eq(loc.id, loc1.id)

            self.zero(self.chronicles)

        # Inner join query: All four have where clauses with simple predicate,
        # i.e., (x=1)
        for t in jointypes:
            if t == 'class':
                continue

            arts1    =  artists        (firstname    =  'fn-0')
            press    =  presentations  (name         =  'pres-name-0')
            locs     =  locations      (description  =  'pres-loc-desc-1')
            artlocs  =  locations      (address      =  'art-loc-addr-0')

            join(press,  locs,     t)
            join(arts1,  press,    t)
            join(arts1,  artlocs,  t)

            self.two(arts1.orm.joins)
            self.one(press.orm.joins)
            self.zero(locs.orm.joins)

            self.one(arts1)

            self.chronicles.clear()

            art1 = arts1.first
            self.eq(fff, art1.orm.persistencestate)
            self.eq('fn-0', art1.firstname)

            locs1 = art1.locations
            self.one(locs1)
            loc1 = locs1.first
            self.eq(fff, loc1.orm.persistencestate)
            self.eq('art-loc-addr-0', loc1.address)

            press1 = art1.presentations
            self.one(press1)
            pres = press1.first
            self.eq(fff, pres.orm.persistencestate)
            self.eq('pres-name-0', pres.name)

            locs1 = pres.locations
            self.one(locs1)
            loc = locs1.first
            self.eq(fff, loc.orm.persistencestate)
            self.eq('pres-loc-desc-1', loc.description)

            self.zero(self.chronicles)

        # Inner join query: Artist has a conjoined predicate
        # i.e, (x=1 and y=1)
        # firstname=firstname will match the last artist while lifeform=organic
        # will match the first artist.
        for t in jointypes:
            if t == 'class':
                continue

            arts1    =  artists('firstname = %s or '
                                'lastname = %s' , ('fn-0', 'ln-2'))

            if t == 'class':
                join(arts1, presentations, 'innerjoin')
                press = arts1.orm.joins.last.entities
                join(press, locations, 'innerjoin')
                locs = press.orm.joins.last.entities
                join(arts1, locations, 'innerjoin')
                artlocs = arts1.orm.joins.last.entities
            else:
                press = presentations()
                locs = locations()
                artlocs = locations()
                join(arts1, press, t)
                join(press, locs, t)
                join(arts1, artlocs, t)
                

            self.two(arts1.orm.joins)
            self.one(press.orm.joins)
            self.zero(locs.orm.joins)
            
            self.two(arts1)

            self.chronicles.clear()

            # Test that the correct graph was loaded
            for art1 in arts1:
                self.eq(fff, art1.orm.persistencestate)
                self.true(art1.firstname == 'fn-0' or
                          art1.lastname  == 'ln-2')

                arts.first.presentations.sort('name')
                press1 = art1.presentations.sorted('name')
                self.four(press1)

                for i, pres1 in press1.enumerate():
                    self.eq(fff, pres1.orm.persistencestate)
                    pres = arts.first.presentations[i]
                    self.eq(pres.name, pres1.name)

                    locs  = pres.locations.sorted('description')
                    locs1 = pres1.locations.sorted('description')
                    self.four(locs1)

                    for i, loc1 in locs1.enumerate():
                        self.eq(fff, loc1.orm.persistencestate)
                        self.eq(locs[i].address, loc1.address)
                        self.eq(locs[i].description, loc1.description)
            
            self.zero(self.chronicles)

        for t in jointypes:
            arts1 = artists('firstname = %s and lastname = %s', 
                            ('fn-0', 'ln-1'))
            locs  = locations('address = %s or description = %s', 
                             ('pres-loc-addr-0', 'pres-loc-desc-2'))

            artlocs  =  locations('address = %s or description = %s', 
                                 ('art-loc-addr-0', 'art-loc-desc-2'))

            if t == 'class':
                join(arts1, presentations, 'innerjoin')
                press = arts1.orm.joins.last.entities
                join(arts1,  artlocs,  'innerjoin')
                join(press,  locs,     'innerjoin')
            else:
                press = presentations()
                join(arts1,  press,    t)
                join(arts1,  artlocs,  t)
                join(press,  locs,     t)

            # Test join counts
            self.two(arts1.orm.joins)
            self.one(press.orm.joins)
            self.zero(locs.orm.joins)

            # Only one artist will have been retrieved by the query
            self.one(arts1)

            self.chronicles.clear()

            self.eq(fff, arts1.first.orm.persistencestate)

            # Test artist's locations
            locs = arts1.first.locations
            self.two(locs)
            for loc in locs:
                self.eq(fff, loc.orm.persistencestate)
                self.true(loc.address     == 'art-loc-addr-0' or 
                          loc.description == 'art-loc-desc-2')

            # Test arts1.first.presentations' locations
            press = arts1.first.presentations

            # All four presentations were match by the location predicate
            self.four(press) 
            for pres in press:
                self.eq(fff, pres.orm.persistencestate)
                self.two(pres.locations)
                for loc in pres.locations:
                    self.eq(fff, loc.orm.persistencestate)
                    self.true(loc.address     == 'pres-loc-addr-0' or 
                              loc.description == 'pres-loc-desc-2')

            self.zero(self.chronicles)

        for t in jointypes:
            # Query where the only filter is down the graph three levels
            # artist->presentation->locations. The algorithm that generates the
            # where predicate has unusual recursion logic that is sensitive to
            # top-level joins not having `where` objects so we need to make
            # sure this doesn't get broken.
            locs  = locations('address = %s or description = %s', 
                             ('pres-loc-addr-0', 'pres-loc-desc-2'))

            if t == 'class':
                arts1 = artists.join(presentations)
                press = arts1.orm.joins.last.entities
                join(press, locs, 'innerjoin')
            else:
                press = presentations()
                arts1 = artists()
                join(arts1, press, t)
                join(press, locs, t)

            # Test join counts
            self.one(arts1.orm.joins)
            self.one(press.orm.joins)
            self.zero(locs.orm.joins)

            self.four(arts1)

            self.chronicles.clear()

            for art in arts1:
                self.eq(fff, art.orm.persistencestate)
                self.four(art.presentations)
                for pres in art.presentations:
                    self.eq(fff, pres.orm.persistencestate)
                    self.two(pres.locations)
                    for loc in pres.locations:
                        self.eq(fff, loc.orm.persistencestate)
                        self.true(loc.address     == 'pres-loc-addr-0' or
                                  loc.description == 'pres-loc-desc-2')

            self.zero(self.chronicles)
            
        # Test joining using the three our more & operators.

        # NOTE Sadely, parenthesis must be used to correct precedence. This
        # will likely lead to confusion if the & techinique is promoted. I'm
        # thinking &= should be recommended instead.
        for t in ('class', 'instance'):
            if t == 'class':
                arts1 = artists & (presentations & locations)
            else:
                arts1 = artists() & (presentations() & locations())

            self.four(arts1)

            self.chronicles.clear()

            for art in arts1:
                self.eq(fff, art.orm.persistencestate)
                self.four(art.presentations)
                for pres in art.presentations:
                    self.eq(fff, pres.orm.persistencestate)
                    self.four(pres.locations)

            self.zero(self.chronicles)
                    
    def it_eager_loads_constituents(self):
        arts = artists()
        for _ in range(4):
            arts += artist.getvalid()

            arts.last.artist_artifacts \
                += artist_artifact.getvalid()

            arts.last.artist_artifacts.last.artifact \
                = artifact.getvalid()

            arts.last.locations += location.getvalid()

            arts.last.presentations += presentation.getvalid()

            arts.last.presentations.last.locations  \
                += location.getvalid()

            arts.last.presentations.last.components \
                += component.getvalid()
        arts.save()

        # Eager-load one constituent
        arts1 = artists(orm.eager('presentations'))
        self.one(arts1.orm.joins)
        self.type(presentations, arts1.orm.joins.first.entities)

        self.le(arts.count, arts1.count)

        for art in arts:
            art1 = arts1(art.id)
            self.notnone(art1)

            for pres in art.presentations:
                pres1 = art1.presentations(pres.id)
                self.notnone(pres1)

        # Eager-load two constituents
        arts1 = artists(orm.eager('presentations', 'locations'))
        self.two(arts1.orm.joins)
        self.type(presentations, arts1.orm.joins.first.entities)
        self.type(locations, arts1.orm.joins.second.entities)

        self.le(arts.count, arts1.count)

        for art in arts:
            art1 = arts1(art.id)
            self.notnone(art1)

            for pres in art.presentations:
                pres1 = art1.presentations(pres.id)
                self.notnone(pres1)

            for loc in art.locations:
                loc1 = art1.locations(loc.id)
                self.notnone(loc1)

        # Eager-load two constituents
        arts1 = artists(orm.eager('presentations', 'locations'))
        self.two(arts1.orm.joins)
        self.type(presentations, arts1.orm.joins.first.entities)
        self.type(locations, arts1.orm.joins.second.entities)

        self.le(arts.count, arts1.count)

        for art in arts:
            art1 = arts1(art.id)
            self.notnone(art1)

            for pres in art.presentations:
                pres1 = art1.presentations(pres.id)
                self.notnone(pres1)

            for loc in art.locations:
                loc1 = art1.locations(loc.id)
                self.notnone(loc1)
            
        # Eager-load two constituents
        arts1 = artists(orm.eager('presentations.locations', 'presentations.components'))
        self.one(arts1.orm.joins)
        self.two(arts1.orm.joins.first.entities.orm.joins)
        presjoins = arts1.orm.joins.first.entities.orm.joins
        self.type(locations, presjoins.first.entities)
        self.type(components, presjoins.second.entities)

        self.le(arts.count, arts1.count)

        for art in arts:
            art1 = arts1(art.id)
            self.notnone(art1)

            for pres in art.presentations:
                pres1 = art1.presentations(pres.id)
                self.notnone(pres1)

                for loc in pres.locations:
                    loc1 = pres1.locations(loc.id)
                    self.notnone(loc1)

                for comp in pres.components:
                    comp1 = pres1.components(comp.id)
                    self.notnone(comp1)

    def it_creates_iter_from_predicate(self):
        ''' Test the predicates __iter__() '''

        # Iterate over one predicate
        pred = orm.predicate('col = 1')
        pred1 = None
        for i, pred1 in enumerate(pred):
            self.eq(str(pred1), str(pred))

        self.notnone(pred1)
        self.eq(0, i)

        # Iterate over two predicates
        pred = orm.predicate('col = 1 and col1 = 2')

        pred1 = None
        for i, pred1 in enumerate(pred):
            if i == 0:
                self.eq('col = 1 AND col1 = 2', str(pred1))
            elif i == 1:
                self.eq(' AND col1 = 2', str(pred1))
            else:
                self.fail('Predicate count exceeds 2')

        # Iterate over match predicate and standard
        pred = orm.predicate("match(col) against ('keyword') and col = 1")

        pred1 = None
        for i, pred1 in enumerate(pred):
            if i == 0:
                expr = (
                    "MATCH (col) AGAINST "
                   "('keyword' IN NATURAL LANGUAGE MODE) "
                   "AND col = 1"
                )
                self.eq(expr, str(pred1))
            elif i == 1:
                self.eq(' AND col = 1', str(pred1))
            else:
                self.fail('Predicate count exceeds 2')

        # Iterate over match predicate and standard or standard
        pred = orm.predicate("match(col) against ('keyword') and col = 1 or col1 = 2")

        pred1 = None
        for i, pred1 in enumerate(pred):
            if i == 0:
                expr = (
                    "MATCH (col) AGAINST ('keyword' "
                    "IN NATURAL LANGUAGE MODE) AND col = 1 OR col1 = 2"
                )
                self.eq(expr, str(pred1))
            elif i == 1:
                self.eq(' AND col = 1 OR col1 = 2', str(pred1))
            elif i == 2:
                self.eq(' OR col1 = 2', str(pred1))
            else:
                self.fail('Predicate count exceeds 2')
        
    def it_failes_parsing_malformed_predicates(self):
        p = orm.predicate("match ((col) against ('search str')")
        parens = '''
            (col = 1
            (col = 1) or (( col = 2)
            (col = 1) and ( col = 2 or (col = 3)
            (col = 1) and col = 2 or (col = 3))
            (col = 1 and col = 2 or (col = 3)
            (col = 1))
            ((col = 1)
            x = 1 and (x = 1 and x = 1
            match (col) against ('search str') and col = 1)
            (match (col) against ('search str') and col = 1
            match (col) against ('search str') and (col = 1
            match (col) against ('search str')) and col = 1
            match (col) against ('search str') and )col = 1
        '''

        syntax = '''
            match (col) against (unquoted)
        '''

        unexpected = '''
            col = 1 and
            col = 1 =
            = col = 1
            = 1
            1 =
            or col = 1
            match against ('search str')
            match (col) ('search str')
            match () against ('search str')
            match () ('search str')
            match (col) ('search str')
            match (col) against ()
            match (col) against ('search str') in UNnatural language mode
            match (col) against ('search str') mode language natural in
            match (col,) against ('search str') mode language natural in
            col = %S
            col in ()
            col in (1) or col in ()
            col in (
            col in (1) or col in (
        '''

        invalidop = '''
            col != 1
            col === 1
            col <<< 1
            () against ('search str')
        '''

        pairs = (
            (orm.predicate.ParentheticalImbalance,  parens),
            (orm.predicate.SyntaxError,             syntax),
            (orm.predicate.UnexpectedToken,         unexpected),
            (orm.predicate.InvalidOperator,         invalidop),
        )

        for ex, exprs in pairs:
            for expr in exprs.splitlines():
                expr = expr.strip()
                if not expr:
                    continue
 
                try:
                    pred = orm.predicate(expr)
                except Exception as ex1:
                    if type(ex1) is not ex:
                        msg = (
                            'Incorrect exception type; '
                            'expected: %s; actual: %s'
                        ) % (ex, type(ex1))

                        self.fail(msg)
                else:
                    self.fail('No exception parsing: ' + expr)

    def it_parses_where_predicate(self):
        def test(expr, pred, first, op, second, third=''):
            msg = expr
            self.eq(first,   pred.operands[0],  msg)
            self.eq(op,      pred.operator,     msg)
            if second:
                self.eq(second,  pred.operands[1],  msg)

            if third:
                self.eq(third,  pred.operands[2],  msg)
                
            self.eq(expr,    str(pred),         msg)

        # Simple col = literal
        for expr in 'col = 11', 'col=11':
            pred = orm.predicate(expr)
            test('col = 11', pred, 'col', '=', '11')

        # Joined simple col > literal (or|and) col < literal
        for op in 'and', 'or':
            for expr in 'col > 0 %s col < 11' % op, 'col>0 %s col<11' % op:
                pred = orm.predicate(expr)
                test('col > 0 %s col < 11' % op.upper(), pred, 'col', '>', '0')

        # Simple literal = column
        for expr in '11 = col', '11=col':
            pred = orm.predicate(expr)
            test('11 = col', pred, '11', '=', 'col')

        # Joined simple literal > col (or|and) literal < col
        for op in 'and', 'or':
            for expr in '0 > col %s 11 < col' % op, '0>col %s 11<col' % op:
                pred = orm.predicate(expr)
                test('0 > col %s 11 < col' % op.upper(), pred, '0', '>', 'col')
                test(' %s 11 < col' % op.upper(), pred.junction, '11', '<', 'col')

        # Simple c = l
        for expr in 'c = 1', 'c=1':
            pred = orm.predicate(expr)
            test('c = 1', pred, 'c', '=', '1')

        # Joined simple c > 1 (or|and) 1 < c
        for op in 'and', 'or':
            for expr in '0 > c %s 1 < c' % op, '0>c %s 1<c' % op:
                pred = orm.predicate(expr)
                test('0 > c %s 1 < c' % op.upper(), pred, '0', '>', 'c')
                test(' %s 1 < c' % op.upper(), pred.junction, '1', '<', 'c')

        # Simple l = c
        for expr in '1 = c', '1=c':
            pred = orm.predicate(expr)
            test('1 = c', pred, '1', '=', 'c')

        # Simple col = 'literal'
        for expr in "col = '11'", "col='11'":
            pred = orm.predicate(expr)
            test("col = '11'", pred, 'col', '=', "'11'")

        # Joined simple col > 'literal' (or|and) col = 'literal'
        for op in 'and', 'or':
            exprs = (
                "col = '11' %s col1 = '111'" % op, 
                "col='11' %s col1='111'" % op.upper()
            )
            for expr in exprs:
                pred = orm.predicate(expr)
                test( "col = '11' %s col1 = '111'" % op.upper(), pred, 'col', '=', "'11'")
                test( " %s col1 = '111'" % op.upper(), pred.junction, 'col1', '=', "'111'")

        # Simple 'literal' = column
        for expr in "'11' = col", "'11'=col":
            pred = orm.predicate(expr)

            test("'11' = col", pred, "'11'", '=', 'col')

        # Simple col = "literal"
        for expr in 'col = "11"', 'col="11"':
            pred = orm.predicate(expr)
            test('col = "11"', pred, 'col', '=', '"11"')

        # Simple "literal" <= column ; Test multicharacter special ops)
        for expr in 'col <= 11', 'col<=11':
            pred = orm.predicate(expr)
            test('col <= 11', pred, 'col', '<=', '11')

        # Simple column = 'lit=eral' (literal has operator in it)
        for expr in  "col = '1 = 1'", "col='1 = 1'":
            test("col = '1 = 1'", orm.predicate(expr), 'col', '=', "'1 = 1'")

        # Simple 'lit=eral' = column (literal has operator in it)
        for expr in "'1 = 1' = col", "'1 = 1'=col":
            test("'1 = 1' = col", orm.predicate(expr), "'1 = 1'", '=', 'col')

        # column is literal
        for expr in 'col is null', 'col  IS  NULL':
            test('col IS NULL', orm.predicate(expr), 'col', 'IS', 'NULL')

        # literal is column
        for expr in 'null is col', 'NULL  IS  col':
            test('NULL IS col', orm.predicate(expr), 'NULL', 'IS', 'col')

        # column is not literal
        for expr in 'col is not null', 'col  IS  NOT   NULL':
            pred = orm.predicate(expr)
            test('col IS NOT NULL', pred, 'col', 'IS NOT', 'NULL')

        # literal is not column
        for expr in 'null is not col', 'NULL  IS   NOT col':
            pred = orm.predicate(expr)
            test('NULL IS NOT col', pred, 'NULL', 'IS NOT', 'col')

        # column like literal
        for expr in "col like '%lit%'", "col   LIKE '%lit%'":
            pred = orm.predicate(expr)
            test("col LIKE '%lit%'", pred, 'col', 'LIKE', "'%lit%'")

        # column not like literal
        for expr in "col not like '%lit%'", "col   NOT  LIKE '%lit%'":
            pred = orm.predicate(expr)
            test("col NOT LIKE '%lit%'", pred, 'col', 'NOT LIKE', "'%lit%'")

        # column is literal
        for expr in "col is true", "col   IS   TRUE":
            pred = orm.predicate(expr)
            test('col IS TRUE', pred, 'col', 'IS', "TRUE")

        # column is not literal
        for expr in "col is not true", "col   IS   NOT TRUE":
            pred = orm.predicate(expr)
            test('col IS NOT TRUE', pred, 'col', 'IS NOT', "TRUE")

        # column is literal
        for expr in "col is false", "col   IS   FALSE":
            pred = orm.predicate(expr)
            test('col IS FALSE', pred, 'col', 'IS', "FALSE")

        # column is not literal
        for expr in "col is not false", "col   IS   NOT FALSE":
            pred = orm.predicate(expr)
            test('col IS NOT FALSE', pred, 'col', 'IS NOT', "FALSE")

        # column between 1 and 10
        for expr in 'col between 1 and 10', 'col   BETWEEN  1  AND  10':
            pred = orm.predicate(expr)
            test('col BETWEEN 1 AND 10', pred, 'col', 'BETWEEN', '1', '10')

        for op in 'and', 'or':
            OP = op.upper()
            exprs = (
                'col between 1 and 10 %s col1 = 1'% op, 
                'col   BETWEEN  1  AND  10  %s  col1  =  1' % OP
            )
            for expr in exprs:
                pred = orm.predicate(expr)
                test(
                    'col BETWEEN 1 AND 10 %s col1 = 1' % OP, pred,
                    'col', 'BETWEEN', '1', '10' 
                )
                test(
                    ' %s col1 = 1' % OP, pred.junction, 
                    'col1', '=', '1'
                )

        # column not between 1 and 10
        for expr in 'col not between 1 and 10', 'col   NOT BETWEEN  1  AND  10':
            pred = orm.predicate(expr)
            test('col NOT BETWEEN 1 AND 10', pred, 'col', 'NOT BETWEEN', '1', '10')

        def testmatch(pred, cols, expr, mode='natural'):
            self.none(pred.operands)
            self.notnone(pred.match)
            self.eq(cols, pred.match.columns)
            self.eq(expr, str(pred.match))

            if pred.junctionop:
                self.eq(' %s %s' % (pred.junctionop, expr), str(pred))

            self.eq(mode, pred.match.mode)

        # match(col) against ('keyword')
        exprs =  "match(col) against ('keyword')",  "MATCH ( col )  AGAINST  ( 'keyword' )"
        for expr in exprs:
            pred = orm.predicate(expr)
            expr = (
                "MATCH (col) AGAINST ('keyword' "
                "IN NATURAL LANGUAGE MODE)"
            )
            testmatch(pred, ['col'], expr)

        # match (col) against ('''keyword has ''single-quoted'' strings''')
        expr =  "MATCH (col) AGAINST ('''keyword has ''single-quoted'' strings''')"
        pred = orm.predicate(expr)
        self.eq("''keyword has ''single-quoted'' strings''", pred.match.searchstring)
        expr =  (
            "MATCH (col) AGAINST ('''keyword has ''single-quoted'' strings''' "
            "IN NATURAL LANGUAGE MODE)"
        )
        testmatch(pred, ['col'], expr)

        # match (col) against ('"keyword has "double-quoted"' strings"')
        expr =  "MATCH (col) AGAINST ('\"keyword has \"double-quoted\" strings\"')"
        pred = orm.predicate(expr)
        self.eq("\"keyword has \"double-quoted\" strings\"", pred.match.searchstring)

        expr = (
            "MATCH (col) AGAINST ('\"keyword has \"double-quoted\" strings\"' "
            "IN NATURAL LANGUAGE MODE)"
        )

        testmatch(pred, ['col'], expr)

        # match(col) against ('keyword') and col = 1
        for op in 'and', 'or':
            OP = op.upper()
            exprs = (
                "match(col) against ('keyword') %s col = 1" % op, 
                "match(col)  against  ('keyword')  %s col=1" % OP
            )
            for expr in exprs:
                pred = orm.predicate(expr)
                expr = (
                    "MATCH (col) AGAINST ('keyword' "
                    "IN NATURAL LANGUAGE MODE) %s col = 1" % OP
                )

                testmatch(pred, ['col'], expr)

                expr = (
                    "MATCH (col) AGAINST ('keyword' "
                    "IN NATURAL LANGUAGE MODE) %s col = 1" % OP
                )

                self.eq(expr, str(pred))

                test(
                    ' %s col = 1' % OP, pred.match.junction, 
                    'col', '=', '1'
                )

        # (match(col) against ('keyword')) and (col = 1)
        for op in 'and', 'or':
            OP = op.upper()
            exprs = (
                "(match(col) against ('keyword')) %s (col = 1)" % op, 
                "(match(col)  against  ('keyword'))  %s (col=1)" % OP
            )
            for expr in exprs:
                pred = orm.predicate(expr)
                expr = (
                    "MATCH (col) AGAINST ('keyword' "
                    "IN NATURAL LANGUAGE MODE)"
                )

                testmatch(pred, ['col'], expr)

                expr = (
                    "(MATCH (col) AGAINST ('keyword' "
                    "IN NATURAL LANGUAGE MODE)) %s (col = 1)" % OP
                )

                self.eq(expr, str(pred))

                test(
                    ' %s (col = 1)' % OP, pred.junction, 
                    'col', '=', '1'
                )

        # (match(col) against ('keyword') and col = 1) and (col1 = 2)
        for op in 'and', 'or':
            OP = op.upper()
            exprs = (
                "(match(col) against ('keyword') and col = 1) %s (col1 = 2)" % op, 
                "(match(col)  against  ( 'keyword' ) and col=1)  %s (col1=2)" % OP
            )
            for expr in exprs:
                pred = orm.predicate(expr)
                expr = (
                    "(MATCH (col) AGAINST ('keyword' "
                    "IN NATURAL LANGUAGE MODE) "
                    "AND col = 1) %s (col1 = 2)" % OP
                )

                self.eq(expr, str(pred))

        # col = 1 and match(col) against ('keyword')
        for op in 'and', 'or':
            OP = op.upper()
            exprs = (
                "col = 1 %s match(col) against ('keyword')" % op, 
                "col  =  1  %s  match(col)  against  ('keyword')" % OP
            )
            for expr in exprs:
                pred = orm.predicate(expr)
                expr = (
                    "col = 1 " + OP + " MATCH (col) AGAINST ('keyword' "
                    "IN NATURAL LANGUAGE MODE)"
                )
                test(expr, pred, 'col', '=', '1')
                expr = (
                    "MATCH (col) AGAINST ('keyword' "
                    "IN NATURAL LANGUAGE MODE)"
                )
                testmatch(pred.junction, ['col'], expr)

        # match(col1, col2) against ('keyword')
        exprs =  "match(col1, col2) against ('keyword')", \
                 "MATCH ( col1, col2 )  AGAINST  ( 'keyword' )"
        for expr in exprs:
            pred = orm.predicate(expr)
            expr = (
                "MATCH (col1, col2) AGAINST ('keyword' "
                "IN NATURAL LANGUAGE MODE)"
            )
            testmatch(pred, ['col1', 'col2'], expr)

        # FIXME This is incorrect syntax 
        # (8e385bb9-41cd-4943-bba8-d72cb9f5b938)
        # match(col1, col2) against ('keyword') in natural language mode
        exprs =  "match(col1, col2) against ('keyword') in natural language mode", \
                 "MATCH ( col1, col2 )  AGAINST  ( 'keyword' )  IN  NATURAL     LANGUAGE    MODE"
        for expr in exprs:
            pred = orm.predicate(expr)
            expr = (
                "MATCH (col1, col2) AGAINST ('keyword' "
                "IN NATURAL LANGUAGE MODE)"
            )
            testmatch(pred, ['col1', 'col2'], expr)

        # FIXME This is incorrect syntax
        # match(col1, col2) against ('keyword') in boolean mode
        exprs =  "match(col1, col2) against ('keyword') in boolean mode", \
                 "MATCH ( col1, col2 )  AGAINST  ( 'keyword' )  IN      BOOLEAN    MODE"
        for expr in exprs:
            pred = orm.predicate(expr)
            expr = (
                "MATCH (col1, col2) AGAINST ('keyword' "
                "IN BOOLEAN MODE)"
            )
            testmatch(pred, ['col1', 'col2'], expr, 'boolean')

        # (col = 1)
        for expr in '(col = 1)', '( col=1 )':
            pred = orm.predicate(expr)
            expr = '(col = 1)'
            test(expr, pred, 'col', '=', '1')

        # (col = 1) and (col1 = 2)
        for expr in '(col = 1) and (col1 = 2)', '(col=1)AND(col1=2)':
            pred = orm.predicate(expr)
            expr = '(col = 1) AND (col1 = 2)'
            test(expr, pred, 'col', '=', '1')

            expr = ' AND (col1 = 2)'
            test(expr, pred.junction, 'col1', '=', '2')

        # (col = 1 and col1 = 2)
        for expr in '(col = 1 and col1 = 2)', '(col=1 AND col1=2)':
            pred = orm.predicate(expr)
            expr = '(col = 1 AND col1 = 2)'
            test(expr, pred, 'col', '=', '1')

            expr = ' AND col1 = 2)'
            test(expr, pred.junction, 'col1', '=', '2')

        # (col = 1 and (col1 = 2 and col2 = 3))
        exprs = (
           '(col = 1 and (col1 = 2 and col2 = 3))',
           '(col  =  1  AND ( col1=2 AND col2 = 3 ) )',
        )
        for expr in exprs:
            pred = orm.predicate(expr)
            expr = '(col = 1 AND (col1 = 2 AND col2 = 3))'
            test(expr, pred, 'col', '=', '1')

            expr = ' AND (col1 = 2 AND col2 = 3))'
            test(expr, pred.junction, 'col1', '=', '2')

        # ((col = 1 and col1 = 2) and col2 = 3)
        exprs = (
           '((col = 1 and col1 = 2) and col2 = 3)',
           '((col=1 AND col1=2) AND col2=3)',
        )
        for expr in exprs:
            pred = orm.predicate(expr)
            expr = '((col = 1 AND col1 = 2) AND col2 = 3)'
            test(expr, pred, 'col', '=', '1')

        # col = 'can''t won''t shan''t'
        expr = "col = 'can''t won''t shan''t'"
        pred = orm.predicate(expr)
        expr = "col = 'can''t won''t shan''t'"
        test(expr, pred, 'col', '=', "'can''t won''t shan''t'")

        for op in orm.predicate.Specialops:
            expr = 'col %s 123' % op
            pred = orm.predicate(expr)
            test(expr, pred, 'col', op, '123')

        # col_1 = 1 and col_2 = 2
        expr = "col_0 = 0 AND col_1 = 1"
        for i, pred in enumerate(orm.predicate(expr)):
            col = 'col_' + str(i)
            if i.first:
                expr = 'col_0 = 0 AND col_1 = 1' 
            elif i.second:
                expr = ' AND col_1 = 1'
            test(expr, pred, col, '=', str(i))
        
        ## Placeholders ##
        expr = 'col = %s'
        pred = orm.predicate(expr)
        test(expr, pred, 'col', '=', '%s')

        ## Parse introducers#
        expr = 'id = _binary %s'
        pred = orm.predicate(expr)
        self.eq('id = _binary %s', str(pred))

        # _binary id = %s
        expr = '_binary id = %s'
        pred = orm.predicate(expr)
        self.eq('_binary id = %s', str(pred))

        # _binary id = _binary %s
        expr = '_binary id = _binary %s'
        pred = orm.predicate(expr)
        self.eq('_binary id = _binary %s', str(pred))

        # col in (123) 
        exprs = (
            'col in (123)',
            'col IN(123)',
        )

        for expr in exprs:
            pred = orm.predicate(expr)
            self.eq('col IN (123)', str(pred))

        # col in (123, 'test') 
        exprs = (
            "col in (123, 'test')",
            "col IN(123, 'test')",
        )

        for expr in exprs:
            pred = orm.predicate(expr)
            self.eq("col IN (123, 'test')", str(pred))

        # col in (123, '''test ''single-quoted'' strings''')
        exprs = (
            "col in (123, '''test ''single-quoted'' strings''')",
            "col IN(123,'''test ''single-quoted'' strings''')",
        )

        for expr in exprs:
            pred = orm.predicate(expr)
            self.eq("col IN (123, '''test ''single-quoted'' strings''')", str(pred))

        # col in (1 2 3 'test', 'test1')
        exprs = (
            "col in (1, 2, 3, 'test', 'test1')",
            "col IN(1, 2, 3, 'test', 'test1')",
        )

        for expr in exprs:
            pred = orm.predicate(expr)
            self.eq("col IN (1, 2, 3, 'test', 'test1')", str(pred))

        # col not in (1 2 3 'test', 'test1')
        exprs = (
            "col not in (1, 2, 3, 'test', 'test1')",
            "col NOT IN(1, 2, 3, 'test', 'test1')",
        )

        for expr in exprs:
            pred = orm.predicate(expr)
            self.eq("col NOT IN (1, 2, 3, 'test', 'test1')", str(pred))

        exprs = (
            'col in (_binary %s)',
            'col IN(_binary %s)',
        )

        for expr in exprs:
            pred = orm.predicate(expr)
            self.eq("col IN (_binary %s)", str(pred))

        exprs = (
            'col in (_binary %s, _binary %s)',
            'col IN(_binary %s,_binary %s)',
        )

        for expr in exprs:
            pred = orm.predicate(expr)
            self.eq("col IN (_binary %s, _binary %s)", str(pred))

    def it_saves_recursive_entity(self):

        def recurse(com1, com2, expecteddepth, curdepth=0):
            with self._chrontest() as t:
                t.run(lambda: com2.comments)
                t.retrieved(com2.comments)

            self.is_(com2, com2.comments.comment)

            self.eq(com1.comments.count, com2.comments.count)

            self.eq(com1.id, com2.id)
            for prop in ('id', 'title', 'body'):
                self.eq(getattr(com1, prop), getattr(com2, prop))

            maxdepth = curdepth

            [com.comments.sort() for com in (com1, com2)]

            for com1, com2 in zip(com1.comments, com2.comments):
                maxdepth = recurse(
                    com1, 
                    com2, 
                    expecteddepth=expecteddepth, 
                    curdepth = curdepth + 1
                )
                maxdepth = max(maxdepth, curdepth)

            if curdepth == 0:
                self.eq(expecteddepth, maxdepth)

            return maxdepth

        ' Test non-recursive (no constituent comments) '
        com = comment.getvalid()
        com.save()

        recurse(com, comment(com.id), expecteddepth=0)

        ' Test recursive shallow recursion (1 level) '
        com = comment.getvalid()
        self.zero(com.comments)

        for _ in range(2):
            com.comments += comment.getvalid()
            com.comments.last.title = uuid4().hex
            com.comments.last.body = uuid4().hex

        with self._chrontest() as t:
            t.run(com.save)
            t.created(com)
            t.created(com.comments.first)
            t.created(com.comments.second)

        recurse(com, comment(com.id), expecteddepth=1)

        ''' Test deep recursion '''
        com = comment.getvalid()

        # Create
        for _ in range(2):
            com.comments += comment.getvalid()
            com1 = com.comments.last
            com1.title = uuid4().hex
            com1.body = uuid4().hex
            for _ in range(2):
                com1.comments += comment.getvalid()
                com2 = com1.comments.last
                com2.title = uuid4().hex
                com2.body = uuid4().hex

        with self._chrontest() as t:
            t.run(com.save)
            t.created(com)
            t.created(com.comments.first)
            t.created(com.comments.first.comments.first)
            t.created(com.comments.first.comments.second)
            t.created(com.comments.second)
            t.created(com.comments.second.comments.first)
            t.created(com.comments.second.comments.second)

        recurse(com, comment(com.id), expecteddepth=2)

    def it_updates_recursive_entity(self):
        def recurse(com1, com2):
            for prop in ('id', 'title', 'body'):
                self.eq(getattr(com1, prop), getattr(com2, prop))

            self.eq(com1.comments.count, com2.comments.count)

            for com11, com22 in zip(com1.comments, com2.comments):
                recurse(com11, com22)

        ' Test non-recursive (no constituent comments) '
        com = comment.getvalid()
        com.save()
        
        com = comment(com.id)
        com.title = uuid4().hex
        com.body = uuid4().hex

        with self._chrontest() as t:
            t.run(com.save)
            t.updated(com)

        com1 = comment(com.id)
        
        recurse(com1, com)

        ' Test recursive shallow recursion (1 level) '
        for _ in range(2):
            com1.comments += comment.getvalid()
            com1.comments.last.title = uuid4().hex
            com1.comments.last.body = uuid4().hex

        com1.save()

        com1 = comment(com1.id)

        com1.title = uuid4().hex
        com1.body = uuid4().hex

        for com in com1.comments:
            com.title = uuid4().hex
            com.body = uuid4().hex

        with self._chrontest() as t:
            t.run(com1.save)
            t.updated(com1)
            t.updated(com1.comments.first)
            t.updated(com1.comments.second)

        com2 = comment(com1.id)

        recurse(com1, com2)

        ''' Test deep recursion '''
        com2.title = uuid4().hex
        com2.body = uuid4().hex

        for com in com2.comments:
            for _ in range(2):
                com.comments += comment.getvalid()

        com2.save()
        com2 = comment(com2.id)

        com2.title = uuid4().hex
        com2.body = uuid4().hex

        for com in com2.comments:
            com.title = uuid4().hex
            com.body = uuid4().hex
            for com in com.comments:
                com.title = uuid4().hex
                com.body = uuid4().hex
                
        with self._chrontest() as t:
            t.run(com2.save)
            t.updated(com2)
            for com in com2.comments:
                t.updated(com)
                for com in com.comments:
                    t.updated(com)

        recurse(com2, comment(com2.id))

    def it_loads_and_saves_entitys_recursive_entities(self):
        art = artist.getvalid()

        for _ in range(2):
            art.comments += comment.getvalid()

        for com in art.comments:
            for _ in range(2):
                com.comments += comment.getvalid()

        with self._chrontest() as t:
            t.run(art.save)
            t.created(art)
            for com in art.comments:
                t.created(com)
                for com in com.comments:
                    t.created(com)

        art1 = artist(art.id)

        self.eq(art.id, art1.id)

        coms, coms1 = art.comments, art1.comments

        self.two(coms1)

        for com, com1 in zip(coms.sorted(), coms1.sorted()):
            self.eq(com.id, com1.id)
            coms, coms1 = com.comments, com.comments

            self.two(coms1)

            for com, com1 in zip(coms.sorted(), coms1.sorted()):
                self.eq(com.id, com1.id)

########################################################################
# Test dom                                                             #
########################################################################

class test_site(tester):
    def it_calls__init__(self):
        name = uuid4().hex
        ws = dom.site(name)
        self.eq(ws.name, name)
        self.zero(ws.pages)

class test_page(tester):
    def it_calls__init__(self):
        name = uuid4().hex
        pg = dom.page(name)
        self.eq(pg.name, name)
        self.zero(pg.pages)

class test_element(tester):
    def it_calls_parent(self):
        p = dom.paragraph()
        self.none(p.parent)

        txt = dom.text('some text')
        p += txt
        self.none(p.parent)
        self.is_(p, txt.parent)

        b = dom.strong('strong text')
        txt += b
        self.none(p.parent)
        self.is_(p, txt.parent)
        self.is_(txt, b.parent)
        self.is_(txt, b.getparent())
        self.is_(txt, b.getparent(0))
        self.is_(p, b.parent.parent)
        self.is_(p, b.grandparent)
        self.is_(p, b.getparent(1))
        self.is_(b, b.elements.first.parent)
        self.is_(txt, b.elements.first.grandparent)
        self.is_(p, b.elements.first.greatgrandparent)
        self.is_(p, b.elements.first.getparent(2))

    def it_calls_siblings(self):
        p = dom.paragraph()

        txt = dom.text('some text')
        p += txt
        self.zero(txt.siblings)

        b = dom.strong('some strong text')
        p += b
        self.one(txt.siblings)
        self.is_(b, txt.siblings.first)
        self.one(b.siblings)
        self.is_(txt, b.siblings.first)

        i = dom.emphasis('some emphasized text')
        p += i
        self.two(txt.siblings)
        self.is_(b, txt.siblings.first)
        self.is_(i, txt.siblings.second)

        self.two(b.siblings)
        self.is_(txt, b.siblings.first)
        self.is_(i, b.siblings.second)

        self.two(i.siblings)
        self.is_(txt, i.siblings.first)
        self.is_(b, i.siblings.second)

    def it_raises_when_moving_elements(self):
        p = dom.paragraph()
        txt = dom.text('some text')
        p += txt

        p1 = dom.paragraph()
        self.expect(dom.DomMoveError, lambda: p1.__iadd__(txt))

    def it_calls_noend(self):
        self.false(dom.paragraph.noend)
        self.false(dom.paragraph().noend)

        self.true(dom.base.noend)
        self.true(dom.base().noend)

    def it_calls_id(self):
        p = dom.paragraph()
        uuid = uuid4().hex
        p.id = uuid
        self.one(p.attributes)
        self.eq(uuid, p.id)

    def it_calls_anchor_attributes(self):
        """ Since there are so many HTML classes that were originally 
        autogenerated, we will select one, `anchor` to run some basic
        tests to make sure that it is working correctely.
        """
        a = dom.anchor()
        as_ = dom.anchors()

        self.isinstance(as_, dom.elements)
        self.isinstance(a, dom.element)

        attrs = (
            'referrerpolicy',  'target',  'hreflang',
            'ping',            'media',   'href',
            'download',        'rel',     'shape',
        )

        for i, attr in enumerate(attrs):
            uuid = uuid4().hex
            setattr(a, attr, uuid)
            self.eq(uuid, getattr(a, attr))
            self.count(i + 1, a.attributes)
        
class test_comment(tester):
    def it_calls_html(self):
        txt = 'Who wrote this crap'
        com = dom.comment(txt)

        expect = '<!--%s-->' % txt
        self.eq(expect, com.html)

class test_paragraph(tester):
    def it_calls__init___with_str_and_args(self):
        ''' With str arg '''
        hex1, hex2 = [x.hex for x in (uuid4(), uuid4())]
        p = dom.paragraph('''
        hex1: %s
        hex2: %s
        ''', hex1, hex2)
        
        expect = self.dedent('''
        <p>
          hex1: %s
          hex2: %s
        </p>
        ''', hex1, hex2)

        self.eq(expect, p.html)

        ''' With element arg '''
        txt = dom.text('Plain white sauce!')

        strong = dom.strong('''
            Plain white sauce will make your teeth
        ''')

        # Nest <span> into <strong>
        strong += dom.span('go grey.');
        txt += strong

        # NOTE The spacing is botched. This should be corrected when we
        # write tests for dom.text.
        expect = self.dedent('''
        <p>
          Plain white sauce!
          <strong>
            Plain white sauce will make your teeth
            <span>
              go grey.
            </span>
          </strong>
        </p>
        ''')

        p = dom.paragraph(txt)
        self.eq(expect, p.html)

        # Expect a ValueError if *args are given for a non-str first
        # argument
        self.expect(
          ValueError, 
          lambda: dom.paragraph(txt, 'arg1', 'arg2')
        )

    def it_calls_html(self):
        p = dom.paragraph()

        p += '''
            Plain white sauce!
        '''

        strong = dom.strong('''
            Plain white sauce will make your teeth
        ''')

        # Nest <span> into <strong>
        strong += dom.span('go grey.');

        p += strong

        p += '''
            Doesn't matter, just throw it away!
        '''
        expect = self.dedent('''
        <p>
          Plain white sauce!
          <strong>
            Plain white sauce will make your teeth
            <span>
              go grey.
            </span>
          </strong>
          Doesn&#x27;t matter, just throw it away!
        </p>
        ''')

        self.eq(expect, p.html)

class test_text(tester):
    def it_calls_html(self):
        txt = self.dedent('''
        <p>
          Plain white sauce!
          <strong>
            Plain white sauce will make your teeth
            <span>
              go grey.
            </span>
          </strong>
          Doesn't matter, just throw it away!
        </p>
        ''')

        expect = self.dedent('''
        &lt;p&gt;
          Plain white sauce!
          &lt;strong&gt;
            Plain white sauce will make your teeth
            &lt;span&gt;
              go grey.
            &lt;/span&gt;
          &lt;/strong&gt;
          Doesn&#x27;t matter, just throw it away!
        &lt;/p&gt;
        ''')

        txt = dom.text(txt)
        self.eq(expect, txt.html)

    def it_calls__str__(self):
        txt = self.dedent('''
        <p>
          Plain white sauce!
          <strong>
            Plain white sauce will make your teeth
            <span>
              go grey.
            </span>
          </strong>
          Doesn't matter, just throw it away!
        </p>
        ''')

        expect = self.dedent('''
        <p>
          Plain white sauce!
          <strong>
            Plain white sauce will make your teeth
            <span>
              go grey.
            </span>
          </strong>
          Doesn't matter, just throw it away!
        </p>
        ''')

        txt = dom.text(txt)
        self.eq(expect, str(txt))

class test_attribute(tester):
    def it_deals_with_undef_attr(self):
        p = dom.paragraph()
        uuid = uuid4().hex
        attr = p.attributes[uuid]
        self.is_(p.attributes[uuid], attr)
        self.zero(p.classes)
        self.zero(p.attributes)
        
        for p in p.attributes:
            self.fail()

        attr.value = uuid4().hex
        self.zero(p.classes)
        self.one(p.attributes)
        self.eq(p.attributes.first.value, attr.value)
        
    def it_sets_None_attr(self):
        expect = self.dedent('''
        <input disabled>
        </input>
        ''')

        inp = dom.input()
        inp.attributes['disabled'] = None
        self.one(inp.attributes)
        self.eq(expect, inp.html)

        inp = dom.input()
        inp.attributes.append('disabled')
        self.one(inp.attributes)
        self.eq(expect, inp.html)

        inp = dom.input()
        inp.attributes += 'disabled'
        self.one(inp.attributes)
        self.eq(expect, inp.html)
        
        inp = dom.input()
        inp.attributes += 'disabled', None
        self.one(inp.attributes)
        self.eq(expect, inp.html)

    def it_appends_attribute(self):
        # Append attribute object
        p = dom.paragraph()
        self.zero(p.attributes)
        id = uuid4().hex
        p.attributes += dom.attribute('id', id)
        self.one(p.attributes)
        self.eq('id', p.attributes.first.name)
        self.eq(id, p.attributes.first.value)

        # Append a tuple
        name = uuid4().hex
        p.attributes += 'name', name
        self.two(p.attributes)
        self.eq('name', p.attributes.second.name)
        self.eq(name, p.attributes.second.value)

        # Append a list
        style = 'color: 8ec298'
        p.attributes += ['style', style]
        self.three(p.attributes)
        self.eq('style', p.attributes.third.name)
        self.eq(style, p.attributes.third.value)

        # It appends using kvp as argument
        title = uuid4().hex
        p.attributes.append('title', title)
        self.four(p.attributes)
        self.eq('title', p.attributes.fourth.name)
        self.eq(title, p.attributes.fourth.value)

        # It appends using indexer
        cls = uuid4().hex
        p.attributes['class'] = cls
        self.five(p.attributes)
        self.eq('class', p.attributes.fifth.name)
        self.eq(cls, p.attributes.fifth.value)

    def it_makes_class_attribute_a_cssclass(self):
        p = dom.paragraph()
        p.attributes['class'] = 'form-group'
        cls = p.attributes['class']
        self.type(dom.cssclass, cls)

    def it_removes_attribute(self):
        # Add three attributes
        p = dom.paragraph()
        id, name, cls = [uuid4().hex for _ in range(3)]
        style = dom.attribute('style', 'color: 8ec298')
        p.attributes += 'id', id
        p.attributes += 'name', name
        p.attributes += style
        p.attributes += 'class', cls
        self.four(p.attributes)

        self.true('id'    in  p.attributes)
        self.true('name'  in  p.attributes)
        self.true(style   in  p.attributes)
        self.true('class' in  p.attributes)

        # Remove by str usinge method
        p.attributes.remove('id')
        self.three(p.attributes)
        self.false('id' in p.attributes)

        # Remove by str using operator
        p.attributes -= 'name'
        self.two(p.attributes)
        self.false('name' in p.attributes)

        # Remove by object using operator
        p.attributes -= style
        self.one(p.attributes)
        self.false(style in p.attributes)

        del p.attributes['class']
        self.zero(p.attributes)
        self.false('class' in p.attributes)

    def it_updates_attribute(self):
        # Add three attributes
        p = dom.paragraph()
        id, name = uuid4().hex, uuid4().hex, 
        style = dom.attribute('style', 'color: 8ec298')
        cls = uuid4().hex
        p.attributes += 'id', id
        p.attributes += 'name', name
        p.attributes += style
        p.attributes += 'class', cls
        self.true('id'    in  p.attributes)
        self.true('name'  in  p.attributes)
        self.true(style   in  p.attributes)
        self.true('class' in  p.attributes)

        id, name = uuid4().hex, uuid4().hex, 
        style = dom.attribute('style', 'color: 8ec298')

        p.attributes['id'].value = id
        self.eq(id, p.attributes.first.value)

        cls = uuid4().hex
        p.attributes['class'] = cls
        self.eq(cls, p.attributes.fourth.value)

    def it_doesnt_append_nonunique(self):
        # Add three attributes
        p = dom.paragraph()
        id, name = uuid4().hex, uuid4().hex, 
        style = dom.attribute('style', 'color: 8ec298')
        p.attributes += 'id', id
        p.attributes += 'name', name
        p.attributes += style

        attrs = p.attributes
        ex = dom.AttributeExistsError
        self.expect(ex, lambda: attrs.append('id', id))
        self.expect(ex, lambda: attrs.append('name', name))
        self.expect(ex, lambda: attrs.append('style', style))

class test_cssclass(tester):
    def it_deals_with_undef_attr(self):
        p = dom.paragraph()
        attr = p.attributes['class']
        self.is_(p.attributes['class'], attr)
        self.zero(p.classes)
        self.zero(p.attributes)
        
        for p in p.attributes:
            self.fail()

        attr.value = uuid4().hex
        self.one(p.classes)
        self.one(p.attributes)
        self.eq(p.attributes.first.value, attr.value)

    def it_calls_class_twice(self):
        # Calling p.classes raised an error in development. This is a
        # test to ensure the problem doesn't somehow resurface.
        p = dom.paragraph()
        self.expect(None, lambda: p.classes)
        self.expect(None, lambda: p.classes)

    def it_appends_classes(self):
        ''' Add by various methods '''
        p = dom.paragraph()
        self.eq(p.classes.html, p.attributes['class'].html)
        cls = dom.cssclass('my-class-1')
        p.attributes['class'].append(cls)
        self.is_(p.classes, p.attributes['class'])
        self.one(p.classes)
        self.true('my-class-1' in p.attributes['class'])

        expect = self.dedent('''
        <p class="%s">
        </p>
        ''', 'my-class-1')
        self.eq(expect, p.html)

        p.classes.append('my-class-2')
        self.two(p.classes)
        self.true('my-class-2' in p.classes)

        expect = self.dedent('''
        <p class="%s">
        </p>
        ''', 'my-class-1 my-class-2')
        self.eq(expect, p.html)

        p.classes += 'my-class-3'
        self.three(p.classes)
        self.eq(p.classes[2], 'my-class-3')

        expect = self.dedent('''
        <p class="%s">
        </p>
        ''', 'my-class-1 my-class-2 my-class-3')
        self.eq(expect, p.html)

        ''' Re-add the same class and expect an exception '''
        for i in range(1, 4):
            cls = 'my-class-%s' % str(i)
            self.expect(
                dom.ClassExistsError, 
                lambda: p.classes.append(dom.cssclass(cls))
            )

            self.expect(
                dom.ClassExistsError, 
                lambda: p.classes.append(cls)
            )

            def f():
                p.classes += cls

            self.expect(
                dom.ClassExistsError, 
                f
            )

    def it_adds_multiple_classes_at_a_time(self):
        ''' Add by various methods '''
        p = dom.paragraph()
        self.eq(p.classes.html, p.attributes['class'].html)

        expect = self.dedent('''
        <p>
        </p>
        ''')
        self.eq(expect, p.html)

        p.classes += dom.cssclass('my-class-1 my-class-a')
        self.eq(p.classes.html, p.attributes['class'].html)
        self.two(p.classes)
        self.two(p.attributes['class'])

        expect = self.dedent('''
        <p class="%s">
        </p>
        ''', 'my-class-1 my-class-a')

        p.classes.append('my-class-2 my-class-b')
        self.four(p.classes)
        self.eq(p.classes.html, p.attributes['class'].html)
        self.eq(
            'class="my-class-1 my-class-a my-class-2 my-class-b"',
            p.classes.html
        )
        return

        expect = self.dedent('''
        <p class="%s">
        </p>
        ''', 'my-class-1 my-class-b')

        self.eq(expect, p.html)

        p.classes.append('my-class-2', 'my-class-c')
        self.four(p.classes)
        self.eq(
            'class="my-class-1 my-class-b my-class-2 my-class-c"',
            p.classes.html
        )

        expect = self.dedent('''
        <p class="%s">
        </p>
        ''', 'my-class-1 my-class-b my-class-2 my-class-c')

        self.eq(expect, p.html)

        p.classes += 'my-class-3', 'my-class-d'
        self.six(p.classes)

        expect = (
            'class="my-class-1 my-class-b '
            'my-class-2 my-class-c '
            'my-class-3 my-class-d"'
        )

        self.eq(expect, p.classes.html)

        p.classes += 'my-class-4 my-class-e'
        self.eight(p.classes)

        expect = (
            'class="my-class-1 my-class-b '
            'my-class-2 my-class-c '
            'my-class-3 my-class-d '
            'my-class-4 my-class-e"'
        )

        self.eq(expect, p.classes.html)

    def it_removes_classes(self):
        p = dom.paragraph()
        p.classes += 'c1 c2 c3 c4 c5 c6 c7 c8'
        self.eight(p.classes)

        p.classes.remove('c4')
        self.seven(p.classes)
        self.eq('class="c1 c2 c3 c5 c6 c7 c8"', p.classes.html)

        p.classes -= 'c3'
        self.six(p.classes)
        self.eq('class="c1 c2 c5 c6 c7 c8"', p.classes.html)

        del p.classes['c2']
        self.five(p.classes)
        self.eq('class="c1 c5 c6 c7 c8"', p.classes.html)

    def it_removes_multiple_classes(self):
        p = dom.paragraph()
        p.classes += 'c1 c2 c3 c4 c5 c6 c7 c8'
        self.eight(p.classes)

        p.classes.remove('c1 c8')
        self.six(p.classes)
        self.eq('class="c2 c3 c4 c5 c6 c7"', p.classes.html)

        p.classes -= 'c2', 'c7'
        self.four(p.classes)
        self.eq('class="c3 c4 c5 c6"', p.classes.html)

        rm = '%s %s' % (uuid4().hex, uuid4().hex)
        self.expect(IndexError, lambda: p.classes.remove(rm))

class test_header(tester):
    pass

class test_html(tester):
    def it_morphs(self):
        # When dom.html is given a string, it morphs into a subtype of
        # `elements`. When single str argument is given, it remains a
        # dom.html.
        self.type(dom.html, dom.html())
        self.type(dom.elements, dom.html('<p></p>'))
    
    def it_raises_on_unclosed_tags(self):
        html = self.dedent('''
        <body>
          <p>
        </body>
        ''')

        ex = self.expect(dom.HtmlParseError, lambda: dom.html(html))

        if type(ex) is dom.HtmlParseError:
            self.eq((2, 2), (ex.line, ex.column))

    def it_doesnt_raise_on_unnested_comment(self):
        html = self.dedent('''
          <!-- A comment -->
          <p>
            A paragraph.
          </p>
        ''')

        self.expect(None, lambda: dom.html(html))

    def it_raises_on_unexpected_text(self):
        html = self.dedent('''
          Some unexpected text
          </p>
        </body>
        ''')

        ex = self.expect(dom.HtmlParseError, lambda: dom.html(html))

        if type(ex) is dom.HtmlParseError:
            self.eq((1, 0), (ex.line, ex.column))
        
    def it_parses(self):
        els = dom.html(testhtml)
        self.eq(testhtml, els.html)

    def it_doesnt_parse_decls(self):
        html = '''
        <!DOCTYPE html>
        <html>
        </html>
        '''
        self.expect(NotImplementedError, lambda: dom.html(html))

    def it_doesnt_parse_unknown_decls(self):
        # TODO The below dosen't work. The fake uknown declaration is
        # interpreted as a comment. The parses `unknown_decl` method is
        # never called. I'm not sure how to create an unknown
        # declaration. I also don't know why <!DERPTYPE herp> is
        # interpreted as a comment.
        return
        html = '''
        <html>
        <!DERPTYPE herp>
        </html>
        '''
        dom.html(html)
        self.expect(NotImplementedError, lambda: dom.html(html))

    def it_doesnt_parse_processing_instructions(self):
        html = '''
        <?xml version="1.0" encoding="UTF-8" ?>
        <html>
        </html>
        '''
        self.expect(NotImplementedError, lambda: dom.html(html))

class test_markdown(tester):
    def it_parses_code(self):
        md = dom.markdown('''
        Use the `printf()` function.
        ''')
        self.type(dom.code, md.first.elements.second)
        self.eq(
            'printf()', 
            md.first.elements.second.elements.first.html
        )

        md = dom.markdown('''
        ``There is a literal backtick (`) here.``
        ''')
        self.type(dom.code, md.first.elements.first)
        self.eq(
            'There is a literal backtick (`) here.', 
            md.first.elements.first.elements.first.html
        )

        md = dom.markdown('''
        A single backtick in a code span: `` ` ``

        A backtick-delimited string in a code span: `` `foo` ``
        ''')
        self.type(dom.code, md.first.elements.second)
        self.eq('`', md.first.elements.second.elements.first.html)
        self.type(dom.code, md.second.elements.second)
        self.eq('`foo`', md.second.elements.second.elements.first.html)

        md = dom.markdown('''
        Please don't use any `<blink>` tags.
        ''')
        self.type(dom.code, md.first.elements.second)

        self.eq(
            '&lt;blink&gt;', 
            md.first.elements.second.elements.first.html
        )

        md = dom.markdown('''
        `&#8212;` is the decimal-encoded equivalent of `&mdash;`.
        ''')

        self.type(dom.code, md.first.elements.first)
        self.eq(
            '&amp;#8212;', 
            md.first.elements.first.elements.first.html
        )
        self.eq(
            '&amp;mdash;', 
            md.first.elements.third.elements.first.html
        )

    def it_parses_images(self):
        md = dom.markdown('''
        ![Alt text](/path/to/img.jpg)

        ![Alt text](/path/to/img.jpg "Optional title")
        ''')
        img = md.first.elements.first
        self.type(dom.img, img)
        self.eq('Alt text', img.alt)
        self.eq('/path/to/img.jpg', img.src)

        img = md.second.elements.first
        self.type(dom.img, img)
        self.eq('Alt text', img.alt)
        self.eq('/path/to/img.jpg', img.src)
        self.eq('Optional title', img.title)

        md = dom.markdown('''
        ![Alt text][id]

        [id]: url/to/image  "Optional title attribute"
        ''')

        img = md.first.elements.first
        self.type(dom.img, img)
        self.eq('url/to/image', img.src)
        self.eq('Optional title attribute', img.title)
        
    def it_parses_code_blocks(self):
        md = dom.markdown('''
        This is a normal paragraph:

            # This is a code block.
            print('Hello, World')
            sys.exit(0)


        This is another paragraph.
        ''')

        self.type(dom.paragraph, md.first)

        self.eq(
            'This is a normal paragraph:', 
            md.first.elements.first.html
        )

        self.type(dom.pre, md.second)
        self.type(dom.code, md.second.elements.first)

        self.type(dom.paragraph, md.third)
        self.eq(
            'This is another paragraph.', 
            md.third.elements.first.html
        )

        expect = self.dedent('''
        <p>
          This is a normal paragraph:
        </p>
        <pre>
          <code>
            # This is a code block.
            print(&#x27;Hello, World&#x27;)
            sys.exit(0)
          </code>
        </pre>
        <p>
          This is another paragraph.
        </p>
        ''')

        self.eq(expect, md.html)

    def it_parses_horizontal_rules(self):
        md = dom.markdown('''
        * * *

        ***

        *****

        - - -

        ---------------------------------------
        ''')
        self.five(md)
        for hr in md:
            self.type(dom.hr, hr)

    def it_parses_inline_links(self):
        md = dom.markdown('''
        This is [an example](http://example.com/ "Title") inline link.

        [This link](http://example.net/) has no title attribute.
        ''')

        self.two(md)
        self.three(md.first.elements)
        self.type(dom.a, md.first.elements.second)
        self.two(md.first.elements.second.attributes)
        self.eq('Title', md.first.elements.second.title)
        self.eq('http://example.com/', md.first.elements.second.href)
        self.two(md.second.elements)
        self.type(dom.a, md.second.elements.first)
        self.one(md.second.elements.first.attributes)
        self.is_(dom.undef, md.second.elements.first.title)
        self.eq('http://example.net/', md.second.elements.first.href)


        md = dom.markdown('See my [About](/about/) page for details.')
        self.one(md)
        self.type(dom.p, md.first)
        self.type(dom.a, md.first.elements.second)
        self.eq('/about/', md.first.elements.second.href)

        defs = [
          '[id]: http://example.com/  "Optional Title Here"',

          # NOTE Single quotes don't work here which is strangly
          # consistent with a bug noted on the official Markdown page:
          # "NOTE: There is a known bug in Markdown.pl 1.0.1 which
          # prevents single quotes from being used to delimit link
          # titles."
          # (https://daringfireball.net/projects/markdown/syntax#list)
          # "[id]: http://example.com/  'Optional Title Here'",

          '[id]: http://example.com/  (Optional Title Here)',
          '[ID]: <http://example.com/>  (Optional Title Here)',

          # NOTE This should probably work, but it dosen't in mistune,
          # "You can put the title attribute on the next line and use
          # extra spaces or tabs for padding, which tends to look better
          # with longer URLs:"
          #     [id]: http://example.com/longish/path/to/resource/here
          #         "Optional Title Here"
          # '[id]: http://example.com\n             "Optional Title Here"'
        ]

        for def_ in defs:
          md = dom.markdown('''
          This is [an example][id] reference-style link.
          %s
          ''' % def_)
          self.eq('http://example.com/', md[0].elements[1].href)
          self.eq('Optional Title Here', md[0].elements[1].title)


        md = dom.markdown('''
        [Google][]
        [Google]: http://google.com/
        ''')

        self.type(dom.a, md.first.elements.first)
        self.eq('Google', md.first.elements.first.elements.first.html)

        md = dom.markdown('''
        Visit [Daring Fireball][] for more information.
        [Daring Fireball]: http://daringfireball.net/
        ''')

        self.type(dom.a, md.first.elements.second)
        self.eq('Daring Fireball', md[0].elements[1].elements[0].html)

    def it_parses_emphasis(self):
        # NOTE "emphasis" here includes both <em> and <strong>

        md = dom.markdown('''
        *single asterisks*

        _single underscores_

        **double asterisks**

        __double underscores__
        ''')
        self.type(dom.em, md.first.elements.first)
        self.type(dom.em, md.second.elements.first)
        self.type(dom.strong, md.third.elements.first)
        self.type(dom.strong, md.fourth.elements.first)

        # NOTE The second one, un_frigging_believable, correctly does
        # not result in emphasization.
        md = dom.markdown('''
        un*frigging*believable

        un_frigging_believable

        un**frigging**believable

        un__frigging__believable
        ''')
        self.type(dom.em, md.first.elements.second)
        # The second one doesn't cause emphasization so comment this
        # out.
        # self.type(dom.em, md.second.elements.second)
        self.type(dom.strong, md.third.elements.second)
        self.type(dom.strong, md.fourth.elements.second)

        md = dom.markdown('''
        \*this text is surrounded by literal asterisks\*
        ''')

        self.eq(
            '*this text is surrounded by literal asterisks*',
            md.first.elements.first.html
        )

    def it_parses_inline_html(self):
        md = dom.markdown('''
          This is a regular paragraph.

          <table>
            <tr>
              <td>Foo</td>
            </tr>
          </table>

          This is another regular paragraph.
        ''')

        self.three(md)
        self.type(dom.paragraph, md.first)
        self.type(dom.table, md.second)
        self.one(md.second.elements)
        self.type(dom.tablerow, md.second.elements.first)
        self.one(md.second.elements.first.elements)
        self.type(
            dom.tabledata, 
            md.second.elements.first.elements.first
        )
        self.one(md.second.elements.first.elements.first.elements)
        self.type(
            dom.text, 
            md.second.elements.first.elements.first.elements.first
        )

        self.eq(
            'Foo',
            md.second.elements.first.elements.first.elements.first.html
        )
        self.type(dom.paragraph, md.third)

        md = dom.markdown('<http://example.com/>')
        a = md.first.elements.first
        self.type(dom.a, a)
        self.eq('http://example.com/', a.href)
        self.eq('http://example.com/', a.elements.first.html)

        # NOTE The Markdown spec says the below should obscure the email
        # address by using "randomized decimal and hex entity-encoding"
        # to conceal the address from naive spambots. However, mistune
        # does not do this and instead creates a typical mailto: link.
        # See
        # https://daringfireball.net/projects/markdown/syntax#autolink
        # for more information.
        md = dom.markdown('<address@example.com>')
        a = md.first.elements.first
        self.type(dom.a, a)
        self.eq('mailto:address@example.com', a.href)
        self.eq('address@example.com', a.elements.first.html)

    def it_parses_html_entities(self):
        md = dom.markdown('&copy;')
        expect = self.dedent('''
        <p>
          &copy;
        </p>
        ''')

        # FIXME
        # self.eq(expect, md.html)

        md = dom.markdown('AT&T')
        expect = self.dedent('''
        <p>
          AT&amp;T
        </p>
        ''')

        self.eq(expect, md.html)


        md = dom.markdown('4 < 5')

        expect = self.dedent('''
        <p>
          4 &lt; 5
        </p>
        ''')
        self.eq(expect, md.html)

    def it_adds_linebreaks_to_paragraphs(self):
        # "When you do want to insert a <br /> break tag using Markdown,
        # you end a line with two or more spaces, then type return."
        # https://daringfireball.net/projects/markdown/syntax#block
        md = self.dedent('''
        This is a paragraph with a  
        hard line break.
        ''')

        expect = self.dedent('''
        <p>
          This is a paragraph with a
          <br>
          hard line break.
        </p>
        ''')
        
        md = dom.markdown(md)
        self.eq(expect, md.html)

    def it_raises_with_nonstandard_inline_html_tags(self):
        # TODO  
        pass

    def it_parses_headers(self):
        # Setext-style headers 
        md = dom.markdown('''
        This is an H1
        =============

        This is an H2
        -------------
        ''')

        self.two(md)
        self.type(dom.h1, md.first)
        self.eq('This is an H1', md.first.elements.first.html)
        self.type(dom.h2, md.second)
        self.eq('This is an H2', md.second.elements.first.html)

        # Atx-style headers
        md = dom.markdown('''
        # This is an H1

        ## This is an H2

        ###### This is an H6
        ''')
        self.three(md)
        self.type(dom.h1, md.first)
        self.eq('This is an H1', md.first.elements.first.html)
        self.type(dom.h2, md.second)
        self.eq('This is an H2', md.second.elements.first.html)
        self.type(dom.h6, md.third)
        self.eq('This is an H6', md.third.elements.first.html)
    
    def it_parses_blockquotes(self):
        md = dom.markdown('''
        > This is a blockquote with two paragraphs. Lorem ipsum dolor
        > sit amet,
        > consectetuer adipiscing elit. Aliquam hendrerit mi posuere
        > lectus.
        > Vestibulum enim wisi, viverra nec, fringilla in, laoreet
        > vitae, risus.
        > 
        > Donec sit amet nisl. Aliquam semper ipsum sit amet velit.
        > Suspendisse
        > id sem consectetuer libero luctus adipiscing.
        ''')

        self.one(md)
        self.type(dom.blockquote, md.first)

        self.two(md.first.elements)
        self.type(dom.paragraph, md.first.elements.first)
        self.type(dom.paragraph, md.first.elements.second)

        md = dom.markdown('''
        > This is a blockquote with two paragraphs. Lorem ipsum dolor sit amet,
        consectetuer adipiscing elit. Aliquam hendrerit mi posuere lectus.
        Vestibulum enim wisi, viverra nec, fringilla in, laoreet vitae, risus.

        > Donec sit amet nisl. Aliquam semper ipsum sit amet velit. Suspendisse
        id sem consectetuer libero luctus adipiscing.
        ''')

        self.one(md)
        self.type(dom.blockquote, md.first)

        self.two(md.first.elements)
        self.type(dom.paragraph, md.first.elements.first)
        self.type(dom.paragraph, md.first.elements.second)

        # Nested

        md = dom.markdown('''
        > This is the first level of quoting.
        >
        > > This is nested blockquote.
        >
        > Back to the first level.
        ''')
        self.one(md)
        self.type(dom.blockquote, md.first)

        self.three(md.first.elements)
        self.type(dom.paragraph, md.first.elements.first)
        self.type(dom.blockquote, md.first.elements.second)
        self.type(dom.paragraph, md.first.elements[1].elements.first)
        self.type(dom.paragraph, md.first.elements.third)

        md = dom.markdown('''
        > ## This is a header.
        > 
        > 1.   This is the first list item.
        > 2.   This is the second list item.
        > 
        > Here's some example code:
        > 
        >     return shell_exec("echo $input | $markdown_script");

        ''')

        self.one(md)
        self.type(dom.blockquote, md.first)
        self.type(dom.h2, md.first.elements.first)
        self.type(dom.ol, md.first.elements.second)
        self.type(dom.li, md.first.elements.second.elements.first)
        self.type(dom.li, md.first.elements.second.elements.second)
        self.type(dom.p, md.first.elements.third)
        self.type(dom.pre, md.first.elements.fourth)
        self.type(dom.code, md.first.elements.fourth.elements.first)

    def it_parses_lists(self):
        for bullet in '*', '+', '-':
          md = self.dedent('''
          ?   Red
          ?   Green
          ?   Blue
          ''')

          md = md.replace('?', bullet)

          md = dom.markdown(md)

          self.one(md)
          self.type(dom.ul, md.first)
          self.three(md.first.elements)
          self.type(dom.li, md.first.elements.first)
          self.type(dom.li, md.first.elements.second)
          self.type(dom.li, md.first.elements.third)

        # NOTE Ordered list are created by starting the lines with
        # orditals (1., 2., etc). However, "he actual numbers you use to
        # mark the list have no effect on the HTML output Markdown
        # produces.".
        # (https://daringfireball.net/projects/markdown/syntax#list). So
        # the below test is writtes 1, 3, 2.
        md = dom.markdown('''
        1.  Bird
        3.  Parish
        2.  McHale
        ''')

        self.one(md)
        self.type(dom.ol, md.first)
        self.three(md.first.elements)
        self.type(dom.li, md.first.elements.first)
        self.type(dom.li, md.first.elements.second)
        self.type(dom.li, md.first.elements.third)

        for lazy in True, False:
            if lazy:
                md = dom.markdown('''
                *   Lorem ipsum dolor sit amet, consectetuer adipiscing elit.
                Aliquam hendrerit mi posuere lectus. Vestibulum enim
                wisi, viverra nec, fringilla in, laoreet vitae, risus.
                *   Donec sit amet nisl. Aliquam semper ipsum sit amet
                velit.  Suspendisse id sem consectetuer libero luctus
                adipiscing.
                ''')
            else:
                md = dom.markdown('''
                *   Lorem ipsum dolor sit amet, consectetuer adipiscing
                    elit.  Aliquam hendrerit mi posuere lectus.
                    Vestibulum enim wisi, viverra nec, fringilla in,
                    laoreet vitae, risus.
                *   Donec sit amet nisl. Aliquam semper ipsum sit amet
                    velit.  Suspendisse id sem consectetuer libero
                    luctus adipiscing.
                ''')
            self.one(md)
            self.type(dom.ul, md.first)
            self.two(md.first.elements)
            self.type(dom.li, md.first.elements.first)
            self.type(dom.li, md.first.elements.second)

        md = dom.markdown('''
        *   Bird

        *   Magic
        ''')

        self.one(md)
        self.type(dom.ul, md.first)
        self.two(md.first.elements)
        self.one(md.first.elements.first.elements)
        self.type(dom.p, md.first.elements.first.elements.first)
        self.type(dom.p, md.first.elements.second.elements.first)

        for lazy in True, False:
            if lazy:
              md = dom.markdown('''
              *   This is a list item with two paragraphs.

                  This is the second paragraph in the list item. You're
              only required to indent the first line. Lorem ipsum dolor
              sit amet, consectetuer adipiscing elit.

              *   Another item in the same list.
              ''')
            else:
                md = dom.markdown('''
                1.  This is a list item with two paragraphs. Lorem ipsum
                    dolor sit amet, consectetuer adipiscing elit.
                    Aliquam hendrerit mi posuere lectus.

                    Vestibulum enim wisi, viverra nec, fringilla in,
                    laoreet vitae, risus. Donec sit amet nisl. Aliquam
                    semper ipsum sit amet velit.

                2.  Suspendisse id sem consectetuer libero luctus
                    adipiscing.

              ''')
            self.one(md)
            self.type(dom.ul if lazy else dom.ol, md.first)
            self.two(md.first.elements)
            self.two(md.first.elements.first.elements)
            self.type(dom.p, md.first.elements.first.elements.first)
            self.type(dom.p, md.first.elements.second.elements.first)

        md = dom.markdown('''
        *   A list item with a blockquote:

            > This is a blockquote
            > inside a list item.
        ''')

        self.one(md)
        self.type(dom.ul, md.first)
        self.type(dom.li, md.first.elements.first)
        self.two(md.first.elements.first.elements)
        self.type(dom.p, md.first.elements.first.elements.first)
        self.type(dom.blockquote, md[0].elements[0].elements[1])

        md = dom.markdown('''
        *   A list item with a code block:

                <code goes here>
        ''')
        self.one(md)
        self.type(dom.ul, md.first)
        self.one(md.first.elements)
        self.two(md.first.elements.first.elements)
        self.type(dom.p, md.first.elements.first.elements.first)
        self.type(dom.pre, md.first.elements.first.elements.second)
        self.one(md.first.elements.first.elements.second.elements)
        self.type(
            dom.code,
            md.first.elements.first.elements.second.elements.first
        )

        md = dom.markdown('''
        1986\. What a great season.
        ''')
        self.one(md)
        self.type(dom.p, md.first)



    def it_parses_paragraph(self):
        ''' Parse a simple, one-line paragraph '''
        md = dom.markdown('''
        This is a paragraph.
        ''')

        self.one(md)
        self.type(dom.paragraph, md.first)

        expect = self.dedent('''
        <p>
          This is a paragraph.
        </p>
        ''')

        self.eq(expect, md.first.html)

        ''' Parse two paragraphs '''
        md = dom.markdown('''
        Parcite, mortales, dapibus temerare nefandis
        corpora! Sunt fruges, sunt deducentia ramos
        pondere poma suo tumidaeque in vitibus uvae,
        sunt herbae dulces, sunt quae mitescere flamma
        mollirique queant; nec vobis lacteus umor
        eripitur, nec mella thymi redolentia flore:
        prodiga divitias alimentaque mitia tellus
        suggerit atque epulas sine caede et sanguine praebet.

        Carne ferae sedant ieiunia, nec tamen omnes:
        quippe equus et pecudes armentaque gramine vivunt.
        At quibus ingenium est inmansuetumque ferumque,
        Armeniae tigres iracundique leones
        cumque lupis ursi, dapibus cum sanguine gaudent.
        Heu quantum scelus est in viscera viscera condi
        congestoque avidum pinguescere corpore corpus
        alteriusque animantem animantis vivere leto!
        Scilicet in tantis opibus, quas optima matrum
        terra parit, nil te nisi tristia mandere saevo
        vulnera dente iuvat ritusque referre Cyclopum,
        nec, nisi perdideris alium, placare voracis
        et male morati poteris ieiunia ventris?
        ''')

        self.two(md)
        self.type(dom.paragraph, md.first)
        self.type(dom.paragraph, md.second)

        expect = self.dedent('''
        <p>
          Parcite, mortales, dapibus temerare nefandis
          corpora! Sunt fruges, sunt deducentia ramos
          pondere poma suo tumidaeque in vitibus uvae,
          sunt herbae dulces, sunt quae mitescere flamma
          mollirique queant; nec vobis lacteus umor
          eripitur, nec mella thymi redolentia flore:
          prodiga divitias alimentaque mitia tellus
          suggerit atque epulas sine caede et sanguine praebet.
        </p>
        <p>
          Carne ferae sedant ieiunia, nec tamen omnes:
          quippe equus et pecudes armentaque gramine vivunt.
          At quibus ingenium est inmansuetumque ferumque,
          Armeniae tigres iracundique leones
          cumque lupis ursi, dapibus cum sanguine gaudent.
          Heu quantum scelus est in viscera viscera condi
          congestoque avidum pinguescere corpore corpus
          alteriusque animantem animantis vivere leto!
          Scilicet in tantis opibus, quas optima matrum
          terra parit, nil te nisi tristia mandere saevo
          vulnera dente iuvat ritusque referre Cyclopum,
          nec, nisi perdideris alium, placare voracis
          et male morati poteris ieiunia ventris?
        </p>
        ''')

        self.eq(expect, md.html)

class test_site(tester):
    def it_calls_name(self):
        name = uuid4().hex
        s = dom.site(name)
        self.eq(name, s.name)

class test_selectors(tester):
    def it_parses_chain_of_elements(self):
        ''' One '''
        sels = dom.selectors('E')
        self.one(sels)
        els = sels.first.elements
        self.one(els)
        self.eq(['E'], els.pluck('element'))

        desc = dom.selector.Descendant
        self.none(els.first.combinator)
        self.eq('E', repr(sels))
        self.eq('E', str(sels))

        ''' Two '''
        sels = dom.selectors('E F')
        self.one(sels)
        els = sels.first.elements
        self.two(els)
        self.eq(['E', 'F'], els.pluck('element'))

        desc = dom.selector.Descendant
        self.none(els.first.combinator)
        self.eq(desc, els.second.combinator)
        self.eq('E F', repr(sels))
        self.eq('E F', str(sels))

        ''' Three '''
        sels = dom.selectors('E F G')
        self.one(sels)
        els = sels.first.elements
        self.three(els)
        self.eq(['E', 'F', 'G'], els.pluck('element'))

        desc = dom.selector.Descendant
        self.none(els.first.combinator)
        self.eq(desc, els.second.combinator)
        self.eq(desc, els.third.combinator)
        self.eq('E F G', repr(sels))
        self.eq('E F G', str(sels))

    def it_selects_with_chain_of_elements(self):
        html = dom.html(Shakespeare)

        sels = [
          'h2',
          'div h2', 
          'div div h2',
          'body h2',
          'html h2',
          'html body h2',
          'html div h2',
        ]

        for sel in sels:
          h2s = html[sel]
          self.one(h2s)
          self.type(dom.h2, h2s.first)

        sels = [
          'h2 div',
          'div body h2', 
          'div body h2',
          'body body h2',
          'div html h2',
          'body wbr h2', 
          'body nonstandardtag h2', 
          'h3 h2', 
          'wbr', 
          'nonstandardtag'
        ]

        for sel in sels:
          self.zero(html[sel], sel)

    def it_parses_attribute_elements(self):
        sels = 'E[foo=bar] F[qux="quux"] G[garply=waldo]'
        sels = dom.selectors(sels)
        self.one(sels)
        sel = sels.first

        el = sel.elements.first
        self.eq('E', el.element)
        self.one(el.attributes)
        attr = el.attributes.first
        self.eq('foo', attr.key)
        self.eq('=', attr.operator)
        self.eq('bar', attr.value)

        el = sel.elements.second
        self.eq('F', el.element)
        self.one(el.attributes)
        attr = el.attributes.first
        self.eq('qux', attr.key)
        self.eq('=', attr.operator)
        self.eq('quux', attr.value)

        el = sel.elements.third
        self.eq('G', el.element)
        self.one(el.attributes)
        attr = el.attributes.first
        self.eq('garply', attr.key)
        self.eq('=', attr.operator)
        self.eq('waldo', attr.value)

        sels = 'E[foo~=bar] F[qux^="quux"] G[garply$=waldo]'
        sels = dom.selectors(sels)
        self.one(sels)
        sel = sels.first

        el = sel.elements.first
        self.eq('E', el.element)
        self.one(el.attributes)
        attr = el.attributes.first
        self.eq('foo', attr.key)
        self.eq('~=', attr.operator)
        self.eq('bar', attr.value)

        el = sel.elements.second
        self.eq('F', el.element)
        self.one(el.attributes)
        attr = el.attributes.first
        self.eq('qux', attr.key)
        self.eq('^=', attr.operator)
        self.eq('quux', attr.value)

        el = sel.elements.third
        self.eq('G', el.element)
        self.one(el.attributes)
        attr = el.attributes.first
        self.eq('garply', attr.key)
        self.eq('$=', attr.operator)
        self.eq('waldo', attr.value)

        # multiple attribute selectors
        sels = 'E[foo=bar][qux="quux"] F[garply=waldo][foo=bar]'
        sels = dom.selectors(sels)
        self.one(sels)
        sel = sels.first

        el = sel.elements.first
        self.eq('E', el.element)
        self.two(el.attributes)
        attr = el.attributes.first
        self.eq('foo', attr.key)
        self.eq('=', attr.operator)
        self.eq('bar', attr.value)
        attr = el.attributes.second
        self.eq('qux', attr.key)
        self.eq('=', attr.operator)
        self.eq('quux', attr.value)

        el = sel.elements.second
        self.eq('F', el.element)
        self.two(el.attributes)
        attr = el.attributes.first
        self.eq('garply', attr.key)
        self.eq('=', attr.operator)
        self.eq('waldo', attr.value)
        attr = el.attributes.second
        self.eq('foo', attr.key)
        self.eq('=', attr.operator)
        self.eq('bar', attr.value)

    def it_parses_class_elements(self):
        sels = 'E.warning'
        sels = dom.selectors(sels)
        B()
        self.one(sels)
      

########################################################################
# Test parties                                                         #
########################################################################
class test_gem(tester):
    def __init__(self):
        super().__init__()
        gem.party.orm.recreate(recursive=True)

    def it_loads_and_saves_organization(self):
        org = gem.organization()
        org.name = uuid4().hex
        org.save()

        self.eq(org.id, gem.organization(org.id).id)


testhtml = tester.dedent('''
<html id="myhtml" arbit="trary">
  <!-- This is an HTML document -->
  <head>
    <!-- This is the head of the HTML document -->
    <base href="www.example.com">
  </head>
  <body>
    <p>
      Lorum &amp; Ipsum Δ
    </p>
    <p>
      This is some
      <strong>
        strong text.
      </strong>
    </p>
    <p>
      This too is some
      <strong>
        strong text.
      </strong>
    </p>
  </body>
</html>
''')


Shakespeare = '''
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en" debug="true">
  <head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
  </head>
  <body>
    <div id="test">
      <div class="dialog">
        <h2>
          As You Like It
        </h2>
        <div id="playwright">
          by William Shakespeare
        </div>
        <div class="dialog scene thirdClass" id="scene1">
          <h3>
            ACT I, SCENE III. A room in the palace.
          </h3>
          <div class="dialog">
            <div class="direction">
              Enter CELIA and ROSALIND
            </div>
          </div>
          <div id="speech1" class="character">
            CELIA
          </div>
          <div class="dialog">
            <div id="scene1.3.1">
              Why, cousin! why, Rosalind! Cupid have mercy! not a word?
            </div>
          </div>
          <div id="speech2" class="character">
            ROSALIND
          </div>
          <div class="dialog">
            <div id="scene1.3.2">
              Not one to throw at a dog.
            </div>
          </div>
          <div id="speech3" class="character">
            CELIA
          </div>
          <div class="dialog">
            <div id="scene1.3.3">
              No, thy words are too precious to be cast away upon
            </div>
            <div id="scene1.3.4">
              curs; throw some of them at me; come, lame me with reasons.
            </div>
          </div>
          <div id="speech4" class="character">
            ROSALIND
          </div>
          <div id="speech5" class="character">
            CELIA
          </div>
          <div class="dialog">
            <div id="scene1.3.8">
              But is all this for your father?
            </div>
          </div>
          <div class="dialog">
            <div id="scene1.3.5">
              Then there were two cousins laid up; when the one
            </div>
            <div id="scene1.3.6">
              should be lamed with reasons and the other mad
            </div>
            <div id="scene1.3.7">
              without any.
            </div>
          </div>
          <div id="speech6" class="character">
            ROSALIND
          </div>
          <div class="dialog">
            <div id="scene1.3.9">
              No, some of it is for my child&#x27;s father. O, how
            </div>
            <div id="scene1.3.10">
              full of briers is this working-day world!
            </div>
          </div>
          <div id="speech7" class="character">
            CELIA
          </div>
          <div class="dialog">
            <div id="scene1.3.11">
              They are but burs, cousin, thrown upon thee in
            </div>
            <div id="scene1.3.12">
              holiday foolery: if we walk not in the trodden
            </div>
            <div id="scene1.3.13">
              paths our very petticoats will catch them.
            </div>
          </div>
          <div id="speech8" class="character">
            ROSALIND
          </div>
          <div class="dialog">
            <div id="scene1.3.14">
              I could shake them off my coat: these burs are in my heart.
            </div>
          </div>
          <div id="speech9" class="character">
            CELIA
          </div>
          <div class="dialog">
            <div id="scene1.3.15">
              Hem them away.
            </div>
          </div>
          <div id="speech10" class="character">
            ROSALIND
          </div>
          <div class="dialog">
            <div id="scene1.3.16">
              I would try, if I could cry &#x27;hem&#x27; and have him.
            </div>
          </div>
          <div id="speech11" class="character">
            CELIA
          </div>
          <div class="dialog">
            <div id="scene1.3.17">
              Come, come, wrestle with thy affections.
            </div>
          </div>
          <div id="speech12" class="character">
            ROSALIND
          </div>
          <div class="dialog">
            <div id="scene1.3.18">
              O, they take the part of a better wrestler than myself!
            </div>
          </div>
          <div id="speech13" class="character">
            CELIA
          </div>
          <div class="dialog">
            <div id="scene1.3.19">
              O, a good wish upon you! you will try in time, in
            </div>
            <div id="scene1.3.20">
              despite of a fall. But, turning these jests out of
            </div>
            <div id="scene1.3.21">
              service, let us talk in good earnest: is it
            </div>
            <div id="scene1.3.22">
              possible, on such a sudden, you should fall into so
            </div>
            <div id="scene1.3.23">
              strong a liking with old Sir Rowland&#x27;s youngest son?
            </div>
          </div>
          <div id="speech14" class="character">
            ROSALIND
          </div>
          <div class="dialog">
            <div id="scene1.3.24">
              The duke my father loved his father dearly.
            </div>
          </div>
          <div id="speech15" class="character">
            CELIA
          </div>
          <div class="dialog">
            <div id="scene1.3.25">
              Doth it therefore ensue that you should love his son
            </div>
            <div id="scene1.3.26">
              dearly? By this kind of chase, I should hate him,
            </div>
            <div id="scene1.3.27">
              for my father hated his father dearly; yet I hate
            </div>
            <div id="scene1.3.28">
              not Orlando.
            </div>
          </div>
          <div id="speech16" class="character">
            ROSALIND
          </div>
          <div title="wtf" class="dialog">
            <div id="scene1.3.29">
              No, faith, hate him not, for my sake.
            </div>
          </div>
          <div id="speech17" class="character">
            CELIA
          </div>
          <div class="dialog">
            <div id="scene1.3.30">
              Why should I not? doth he not deserve well?
            </div>
          </div>
          <div id="speech18" class="character">
            ROSALIND
          </div>
          <div class="dialog">
            <div id="scene1.3.31">
              Let me love him for that, and do you love him
            </div>
            <div id="scene1.3.32">
              because I do. Look, here comes the duke.
            </div>
          </div>
          <div id="speech19" class="character">
            CELIA
          </div>
          <div class="dialog">
            <div id="scene1.3.33">
              With his eyes full of anger.
            </div>
            <div class="direction">
              Enter DUKE FREDERICK, with Lords
            </div>
          </div>
          <div id="speech20" class="character">
            DUKE FREDERICK
          </div>
          <div class="dialog">
            <div id="scene1.3.34">
              Mistress, dispatch you with your safest haste
            </div>
            <div id="scene1.3.35">
              And get you from our court.
            </div>
          </div>
          <div id="speech21" class="character">
            ROSALIND
          </div>
          <div class="dialog">
            <div id="scene1.3.36">
              Me, uncle?
            </div>
          </div>
          <div id="speech22" class="character">
            DUKE FREDERICK
          </div>
          <div class="dialog">
            <div id="scene1.3.37">
              You, cousin
            </div>
            <div id="scene1.3.38">
              Within these ten days if that thou be&#x27;st found
            </div>
            <div id="scene1.3.39">
              So near our public court as twenty miles,
            </div>
            <div id="scene1.3.40">
              Thou diest for it.
            </div>
          </div>
          <div id="speech23" class="character">
            ROSALIND
          </div>
          <div class="dialog">
            <div id="scene1.3.41">
              I do beseech your grace,
            </div>
            <div id="scene1.3.42">
              Let me the knowledge of my fault bear with me:
            </div>
            <div id="scene1.3.43">
              If with myself I hold intelligence
            </div>
            <div id="scene1.3.44">
              Or have acquaintance with mine own desires,
            </div>
            <div id="scene1.3.45">
              If that I do not dream or be not frantic,--
            </div>
            <div id="scene1.3.46">
              As I do trust I am not--then, dear uncle,
            </div>
            <div id="scene1.3.47">
              Never so much as in a thought unborn
            </div>
            <div id="scene1.3.48">
              Did I offend your highness.
            </div>
          </div>
          <div id="speech24" class="character">
            DUKE FREDERICK
          </div>
          <div class="dialog">
            <div id="scene1.3.49">
              Thus do all traitors:
            </div>
            <div id="scene1.3.50">
              If their purgation did consist in words,
            </div>
            <div id="scene1.3.51">
              They are as innocent as grace itself:
            </div>
            <div id="scene1.3.52">
              Let it suffice thee that I trust thee not.
            </div>
          </div>
          <div id="speech25" class="character">
            ROSALIND
          </div>
          <div class="dialog">
            <div id="scene1.3.53">
              Yet your mistrust cannot make me a traitor:
            </div>
            <div id="scene1.3.54">
              Tell me whereon the likelihood depends.
            </div>
          </div>
          <div id="speech26" class="character">
            DUKE FREDERICK
          </div>
          <div class="dialog">
            <div id="scene1.3.55">
              Thou art thy father&#x27;s daughter; there&#x27;s enough.
            </div>
          </div>
          <div id="speech27" class="character">
            ROSALIND
          </div>
          <div class="dialog">
            <div id="scene1.3.56">
              So was I when your highness took his dukedom;
            </div>
            <div id="scene1.3.57">
              So was I when your highness banish&#x27;d him:
            </div>
            <div id="scene1.3.58">
              Treason is not inherited, my lord;
            </div>
            <div id="scene1.3.59">
              Or, if we did derive it from our friends,
            </div>
            <div id="scene1.3.60">
              What&#x27;s that to me? my father was no traitor:
            </div>
            <div id="scene1.3.61">
              Then, good my liege, mistake me not so much
            </div>
            <div id="scene1.3.62">
              To think my poverty is treacherous.
            </div>
          </div>
          <div id="speech28" class="character">
            CELIA
          </div>
          <div class="dialog">
            <div id="scene1.3.63">
              Dear sovereign, hear me speak.
            </div>
          </div>
          <div id="speech29" class="character">
            DUKE FREDERICK
          </div>
          <div class="dialog">
            <div id="scene1.3.64">
              Ay, Celia; we stay&#x27;d her for your sake,
            </div>
            <div id="scene1.3.65">
              Else had she with her father ranged along.
            </div>
          </div>
          <div id="speech30" class="character">
            CELIA
          </div>
          <div class="dialog">
            <div id="scene1.3.66">
              I did not then entreat to have her stay;
            </div>
            <div id="scene1.3.67">
              It was your pleasure and your own remorse:
            </div>
            <div id="scene1.3.68">
              I was too young that time to value her;
            </div>
            <div id="scene1.3.69">
              But now I know her: if she be a traitor,
            </div>
            <div id="scene1.3.70">
              Why so am I; we still have slept together,
            </div>
            <div id="scene1.3.71">
              Rose at an instant, learn&#x27;d, play&#x27;d, eat together,
            </div>
            <div id="scene1.3.72">
              And wheresoever we went, like Juno&#x27;s swans,
            </div>
            <div id="scene1.3.73">
              Still we went coupled and inseparable.
            </div>
          </div>
          <div id="speech31" class="character">
            DUKE FREDERICK
          </div>
          <div class="dialog">
            <div id="scene1.3.74">
              She is too subtle for thee; and her smoothness,
            </div>
            <div id="scene1.3.75">
              Her very silence and her patience
            </div>
            <div id="scene1.3.76">
              Speak to the people, and they pity her.
            </div>
            <div id="scene1.3.77">
              Thou art a fool: she robs thee of thy name;
            </div>
            <div id="scene1.3.78">
              And thou wilt show more bright and seem more virtuous
            </div>
            <div id="scene1.3.79">
              When she is gone. Then open not thy lips:
            </div>
            <div id="scene1.3.80">
              Firm and irrevocable is my doom
            </div>
            <div id="scene1.3.81">
              Which I have pass&#x27;d upon her; she is banish&#x27;d.
            </div>
          </div>
          <div id="speech32" class="character">
            CELIA
          </div>
          <div class="dialog">
            <div id="scene1.3.82">
              Pronounce that sentence then on me, my liege:
            </div>
            <div id="scene1.3.83">
              I cannot live out of her company.
            </div>
          </div>
          <div id="speech33" class="character">
            DUKE FREDERICK
          </div>
          <div class="dialog">
            <div id="scene1.3.84">
              You are a fool. You, niece, provide yourself:
            </div>
            <div id="scene1.3.85">
              If you outstay the time, upon mine honour,
            </div>
            <div id="scene1.3.86">
              And in the greatness of my word, you die.
            </div>
            <div class="direction">
              Exeunt DUKE FREDERICK and Lords
            </div>
          </div>
          <div id="speech34" class="character">
            CELIA
          </div>
          <div class="dialog">
            <div id="scene1.3.87">
              O my poor Rosalind, whither wilt thou go?
            </div>
            <div id="scene1.3.88">
              Wilt thou change fathers? I will give thee mine.
            </div>
            <div id="scene1.3.89">
              I charge thee, be not thou more grieved than I am.
            </div>
          </div>
          <div id="speech35" class="character">
            ROSALIND
          </div>
          <div class="dialog">
            <div id="scene1.3.90">
              I have more cause.
            </div>
          </div>
          <div id="speech36" class="character">
            CELIA
          </div>
          <div class="dialog">
            <div id="scene1.3.91">
              Thou hast not, cousin;
            </div>
            <div id="scene1.3.92">
              Prithee be cheerful: know&#x27;st thou not, the duke
            </div>
            <div id="scene1.3.93">
              Hath banish&#x27;d me, his daughter?
            </div>
          </div>
          <div id="speech37" class="character">
            ROSALIND
          </div>
          <div class="dialog">
            <div id="scene1.3.94">
              That he hath not.
            </div>
          </div>
          <div id="speech38" class="character">
            CELIA
          </div>
          <div class="dialog">
            <div id="scene1.3.95">
              No, hath not? Rosalind lacks then the love
            </div>
            <div id="scene1.3.96">
              Which teacheth thee that thou and I am one:
            </div>
            <div id="scene1.3.97">
              Shall we be sunder&#x27;d? shall we part, sweet girl?
            </div>
            <div id="scene1.3.98">
              No: let my father seek another heir.
            </div>
            <div id="scene1.3.99">
              Therefore devise with me how we may fly,
            </div>
            <div id="scene1.3.100">
              Whither to go and what to bear with us;
            </div>
            <div id="scene1.3.101">
              And do not seek to take your change upon you,
            </div>
            <div id="scene1.3.102">
              To bear your griefs yourself and leave me out;
            </div>
            <div id="scene1.3.103">
              For, by this heaven, now at our sorrows pale,
            </div>
            <div id="scene1.3.104">
              Say what thou canst, I&#x27;ll go along with thee.
            </div>
          </div>
          <div id="speech39" class="character">
            ROSALIND
          </div>
          <div class="dialog">
            <div id="scene1.3.105">
              Why, whither shall we go?
            </div>
          </div>
          <div id="speech40" class="character">
            CELIA
          </div>
          <div class="dialog">
            <div id="scene1.3.106">
              To seek my uncle in the forest of Arden.
            </div>
          </div>
          <div id="speech41" class="character">
            ROSALIND
          </div>
          <div class="dialog">
            <div id="scene1.3.107">
              Alas, what danger will it be to us,
            </div>
            <div id="scene1.3.108">
              Maids as we are, to travel forth so far!
            </div>
            <div id="scene1.3.109">
              Beauty provoketh thieves sooner than gold.
            </div>
          </div>
          <div id="speech42" class="character">
            CELIA
          </div>
          <div class="dialog">
            <div id="scene1.3.110">
              I&#x27;ll put myself in poor and mean attire
            </div>
            <div id="scene1.3.111">
              And with a kind of umber smirch my face;
            </div>
            <div id="scene1.3.112">
              The like do you: so shall we pass along
            </div>
            <div id="scene1.3.113">
              And never stir assailants.
            </div>
          </div>
          <div id="speech43" class="character">
            ROSALIND
          </div>
          <div class="dialog">
            <div id="scene1.3.114">
              Were it not better,
            </div>
            <div id="scene1.3.115">
              Because that I am more than common tall,
            </div>
            <div id="scene1.3.116">
              That I did suit me all points like a man?
            </div>
            <div id="scene1.3.117">
              A gallant curtle-axe upon my thigh,
            </div>
            <div id="scene1.3.118">
              A boar-spear in my hand; and--in my heart
            </div>
            <div id="scene1.3.119">
              Lie there what hidden woman&#x27;s fear there will--
            </div>
            <div id="scene1.3.120">
              We&#x27;ll have a swashing and a martial outside,
            </div>
            <div id="scene1.3.121">
              As many other mannish cowards have
            </div>
            <div id="scene1.3.122">
              That do outface it with their semblances.
            </div>
          </div>
          <div id="speech44" class="character">
            CELIA
          </div>
          <div class="dialog">
            <div id="scene1.3.123">
              What shall I call thee when thou art a man?
            </div>
          </div>
          <div id="speech45" class="character">
            ROSALIND
          </div>
          <div class="dialog">
            <div id="scene1.3.124">
              I&#x27;ll have no worse a name than Jove&#x27;s own page;
            </div>
            <div id="scene1.3.125">
              And therefore look you call me Ganymede.
            </div>
            <div id="scene1.3.126">
              But what will you be call&#x27;d?
            </div>
          </div>
          <div id="speech46" class="character">
            CELIA
          </div>
          <div class="dialog">
            <div id="scene1.3.127">
              Something that hath a reference to my state
            </div>
            <div id="scene1.3.128">
              No longer Celia, but Aliena.
            </div>
          </div>
          <div id="speech47" class="character">
            ROSALIND
          </div>
          <div class="dialog">
            <div id="scene1.3.129">
              But, cousin, what if we assay&#x27;d to steal
            </div>
            <div id="scene1.3.130">
              The clownish fool out of your father&#x27;s court?
            </div>
            <div id="scene1.3.131">
              Would he not be a comfort to our travel?
            </div>
          </div>
          <div id="speech48" class="character">
            CELIA
          </div>
          <div class="dialog">
            <div id="scene1.3.132">
              He&#x27;ll go along o&#x27;er the wide world with me;
            </div>
            <div id="scene1.3.133">
              Leave me alone to woo him. Let&#x27;s away,
            </div>
            <div id="scene1.3.134">
              And get our jewels and our wealth together,
            </div>
            <div id="scene1.3.135">
              Devise the fittest time and safest way
            </div>
            <div id="scene1.3.136">
              To hide us from pursuit that will be made
            </div>
            <div id="scene1.3.137">
              After my flight. Now go we in content
            </div>
            <div id="scene1.3.138">
              To liberty and not to banishment.
            </div>
            <div class="direction">
              Exeunt
            </div>
          </div>
        </div>
      </div>
    </div>
  </body>
</html>

'''
cli().run()
