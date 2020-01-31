# vim: set et ts=4 sw=4 fdm=marker

########################################################################
# Copyright (C) Jesse Hogan - All Rights Reserved                      #
# Unauthorized copying of this file, via any medium is strictly        #
# prohibited                                                           #
# Proprietary and confidential                                         #
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2020                 #
########################################################################

from auth import jwt
from configfile import configfile
from contextlib import contextmanager
from datetime import timezone, datetime
from entities import BrokenRulesError
from func import enumerate, getattr, B
from MySQLdb.constants.ER import BAD_TABLE_ERROR, DUP_ENTRY
from random import randint, uniform
from table import *
from tester import *
from uuid import uuid4
import dateutil
import db
import decimal; dec=decimal.Decimal
import dom
import functools
import gem
import io
import jwt as pyjwt
import math
import MySQLdb
import _mysql_exceptions
import orm
import pathlib
import pom
import primative
import re
import textwrap
import gem
from pprint import pprint

# TODO Update copyright years

# We will use basic and supplementary multilingual plane UTF-8
# characters when testing str attributes to ensure unicode is being
# supported.

# A two byte character from the Basic Multilingual Plane

Δ = bytes("\N{GREEK CAPITAL LETTER DELTA}", 'utf-8').decode()

# A three byte character
V = bytes("\N{ROMAN NUMERAL FIVE}", 'utf-8').decode()

# A four byte character from the Supplementary Multilingual Plane
Cunei_a = bytes("\N{CUNEIFORM SIGN A}", 'utf-8').decode()

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

class performer(entity):
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
        sj = performer('salena jones')
        bb = performer('burt bacharach')

        ps1 = philosophers([n, s, sj, bb])

        # Results of query should return the one entry in 'ps1' where
        # the type is 'performer' (not 'philosopher')
        ps2 = ps1.where(performer)
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
        """ The |= operator (__iand__) wraps the append() methed setting
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

        # TODO  When setting fields, the old field(s) is removed from
        # the table.fields collection, but the new field(s) ends up at
        # the end of the table.fields collection instead of in place of
        # the removed field(s). This is because the fields.__setitem__
        # simply calls the onadd the onremove event, which causes an
        # append to the collection.  Ideally, the new field wouldn't be
        # appended, but would rather be set in the correct location of
        # the table.fields property. However, currently there is no use
        # case for this. However, since this should change, use of
        # table.fields shouldn't make assuptions about where newly set
        # fields will appear until this behavior is corrected.

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
        hours = math.ceil((t.exp - datetime.now()).seconds / 3600)
        self.assertEq(24, hours)

        # Specify 48 hours to expire
        t = jwt(ttl=48)
        hours = math.ceil((t.exp - datetime.now()).seconds / 3600)
        self.assertEq(24, hours)

    def it_calls_token(self):
        t = jwt()
        token = t.token
        secret = configfile.getinstance()['jwt-secret']

        d = pyjwt.decode(token, secret)

        exp = datetime.fromtimestamp(d['exp'])

        # Ensure exp is about 24 hours into the future
        hours = math.ceil((exp - datetime.now()).seconds / 3600)
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
        utc = timezone.utc
        
        # Test datetime with standard args
        args = (2003, 10, 11, 17, 13, 46)
        expect = datetime(*args, tzinfo=utc)
        actual = primative.datetime(*args, tzinfo=utc)
        self.eq(expect, actual)

        # Test datetime with standard a string arg intended for datautil.parser
        actual = primative.datetime('Sat Oct 11 17:13:46 UTC 2003')
        self.eq(expect, actual)

    def it_calls_astimezone(self):
        utc = timezone.utc

        args = (2003, 10, 11, 17, 13, 46)
        dt = primative.datetime(*args, tzinfo=utc)
        
        aztz = dateutil.tz.gettz('US/Arizona')
        actual = datetime(2003, 10, 11, 10, 13, 46, tzinfo=aztz)

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

class exhibitions(presentations):
    pass

class unveilings(exhibitions):
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

class exhibition(presentation):
    @staticmethod
    def getvalid():
        pres = presentation.getvalid()
        exh = exhibition()
        exh.record = uuid4().hex
        exh.name = uuid4().hex
        exh.title = pres.title
        exh.description = pres.description
        exh.description1 = pres.description1
        return exh

class unveiling(exhibition):
    @staticmethod
    def getvalid():
        exh = exhibition.getvalid()
        unv = unveiling()
        unv.record        =  exh.record
        unv.name          =  exh.name
        unv.title         =  exh.title
        unv.description   =  exh.description
        unv.description1  =  exh.description1
        return unv

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

    # Support datetime module as well as datetime.datetime class
    dob1           =  sys.modules['datetime']
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

    bio1 = str, 1, 4001
    bio2 = str, 1, 4000

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
        art.bio1      = '11'
        art.bio2      = '2'

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

class painters(artists):
    pass

class painter(artist):
    style = str
    exhibitions = exhibitions
    
    @staticmethod
    def getvalid():
        sup = painter.orm.super.getvalid()

        pnt = painter()
        keymaps = (orm.primarykeyfieldmapping, orm.foreignkeyfieldmapping)
        for map in sup.orm.mappings:
            if isinstance(map, orm.fieldmapping) and type(map) not in keymaps:
                setattr(pnt, map.name, getattr(sup, map.name))

        pnt.style = 'impressionism'

        return pnt

class muralists(painters):
    pass

class muralist(painter):
    street = bool
    unveilings = unveilings
    @staticmethod
    def getvalid():
        sup = muralist.orm.super.getvalid()

        mur = muralist()
        keymaps = (orm.primarykeyfieldmapping, orm.foreignkeyfieldmapping)
        for map in artist.orm.mappings:
            if isinstance(map, orm.fieldmapping) and type(map) not in keymaps:
                setattr(mur, map.name, getattr(sup, map.name))

        mur.style = 'classical'
        mur.street = False

        return mur

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

class artist_artists(orm.associations):
    pass

class artist_artist(orm.association):
    subject   =  artist
    object    =  artist
    role      =  str
    slug      =  str

    def __init__(self, o=None):
        self._processing = True
        super().__init__(o)

    @staticmethod
    def getvalid():
        aa = artist_artist()
        aa.role = uuid4().hex
        aa.slug = uuid4().hex
        aa.timespan = uuid4().hex
        return aa

    # The duration an artist worked with another artist
    @orm.attr(str)
    def timespan(self):
        return attr().replace(' ', '-')

    @property
    def processing(self):
        return self._processing

    @processing.setter
    def processing(self, v):
        self._processing = v

class test_orm(tester):
    def __init__(self):
        super().__init__()
        self.chronicles = db.chronicles()
        db.chronicler.getinstance().chronicles.onadd += self._chronicler_onadd

        artist.orm.recreate(recursive=True)
        comment.orm.recreate()

        # Inject a reference to the self._chrontest context manager into
        # each test method as 'ct'. This will make testing chronicles
        # easier to type.

        # TODO Replace all `with self._chrontest()` with `with ct()`
        for meth in type(self).__dict__.items():
            if type(meth[1]) != FunctionType: 
                continue
            if meth[0][0] == '_': 
                continue
            meth[1].__globals__['ct'] = self._chrontest
    
    def _chrons(self, e, op):
        chrons = self.chronicles.where('entity',  e)
        if not (chrons.hasone and chrons.first.op == op):
            self._failures += failure()

    def _chronicler_onadd(self, src, eargs):
        self.chronicles += eargs.entity
        #print(eargs.entity.entity.__class__)
        #B( eargs.entity.entity.__class__ is artist_artifacts)

    @contextmanager
    def _chrontest(self):
        test_orm = self
        class tester:
            def __init__(self):
                self.count = int()
                self.tested = list()

            def run(self, callable=None):
                return self(callable)

            def __call__(self, callable=None):
                # TODO If `callable` is not a callable, throw an
                # exception.
                test_orm.chronicles.clear()

                r = None

                if callable:
                    r = callable()

                self.chronicles = test_orm.chronicles.clone()
                return r

            def created(self, *es):
                for e in es:
                    if not self._test(e, 'create'):
                        test_orm._failures += failure()

            def retrieved(self, e):
                if not self._test(e, 'retrieve'):
                    test_orm._failures += failure()

            def updated(self, *es):
                for e in es:
                    if not self._test(e, 'update'):
                        test_orm._failures += failure()

            def deleted(self, e):
                if not self._test(e, 'delete'):
                    test_orm._failures += failure()

            def _test(self, e, op):
                def raise_already_tested():
                    raise ValueError(
                        '<%s>.%s has already been tested' 
                        % (type(e).__name__, e.id)
                    )

                if not(
                        isinstance(e, orm.entity) \
                        or isinstance(e, orm.entities)
                    ):
                    raise ValueError('e must be an orm.entity')

                if e in self.tested:
                    raise_already_tested()

                self.tested.append(e)

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
            
        self.eq(t.count, cnt, msg)

    def it_creates_indexes_on_foreign_keys(self):
        # Standard entity
        self.notnone(presentation.orm.mappings['artistid'].index)

        # Recursive entity
        self.notnone(comment.orm.mappings['commentid'].index)

        # Associations
        self.notnone(artist_artifact.orm.mappings['artist__artistid'].index)
        self.notnone(artist_artifact.orm.mappings['artifact__artifactid'].index)
        
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

        # FIXME This failed today:
        # Jan 21, 2020

        self.unique(abbrs)
        self.eq(abbrs, abbrs1)

        # FIXME It was discovered that one of the entities, presumably
        # battle, was at one point abbreviated as 'ba' then subsequently
        # abbreviated as 'b'.
        # - Oct 25 2019

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
        subclass hasn't invoked the metaclass code that would assign it
        the orm property), generic entities collections shouldn't be
        allowed. They should basically be considered abstract. '''
        self.expect(NotImplementedError, lambda: orm.entities())

    def it_calls__str__on_entity(self):
        art = artist.getvalid()
        self.eq(art.fullname, str(art))
        
    def it_calls_isreflexive(self):
        self.false(artists.orm.isreflexive)
        self.false(artist.orm.isreflexive)
        self.false(artist().orm.isreflexive)
        self.false(artists().orm.isreflexive)

        self.false(artist_artifact.orm.isreflexive)
        self.false(artist_artifact().orm.isreflexive)
        self.false(artist_artifacts.orm.isreflexive)
        self.false(artist_artifacts().orm.isreflexive)

        self.true(artist_artist.orm.isreflexive)
        self.true(artist_artist().orm.isreflexive)
        self.true(artist_artists.orm.isreflexive)
        self.true(artist_artists().orm.isreflexive)

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
        self.two(comps)
        self.true(artifact in comps)
        self.true(artist in comps)

        comps = singer.orm.composites
        self.two(comps)
        self.true(artifact in comps)
        self.true(artist in comps)

        comps = concert.orm.composites
        self.one(comps)
        self.is_(comps.first.entity, singer)

    def it_has_static_constituents_reference(self):
        consts = artist.orm.constituents
        self.five(artist.orm.constituents)
        self.true(presentation  in  consts)
        self.true(artifact      in  consts)
        self.true(location      in  consts)
        self.true(comment       in  consts)
        self.true(artist        in  consts)

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

        # FIXME `chrons`'s count did not equal two during a standard
        # test 2020-01-15
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
        # FIXME The below line produced a failure today, but it went
        # away.  Jul 6, 2019
        # AGAIN Dec 15, 2019
        # AGAIN Jan 21, 2020
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

        self.is_(art, art.artist_artifacts.artist)

        # Save and load an association
        art                   =   artist.getvalid()
        fact1                 =   artifact.getvalid()
        aa                    =   artist_artifact.getvalid()
        aa.role               =   uuid4().hex
        aa.artifact           =   fact1
        art.artist_artifacts  +=  aa 

        self.is_(fact1,    art.artist_artifacts.first.artifact)
        self.is_(art,      art.artist_artifacts.first.artist)
        self.eq(aa .role,  art.artist_artifacts.first.role)
        self.one(art.artist_artifacts)
        self.one(art.artifacts)

        # Add a second association and test
        fact2                  =   artifact.getvalid()
        aa1                    =   artist_artifact.getvalid()
        aa1.role               =   uuid4().hex
        aa1.artifact           =   fact2
        art.artist_artifacts   +=  aa1

        self.is_(fact2,    art.artist_artifacts.last.artifact)
        self.is_(art,      art.artist_artifacts.last.artist)
        self.eq(aa1.role,  art.artist_artifacts.last.role)
        self.two(art.artist_artifacts)
        self.two(art.artifacts)

        with self._chrontest() as t:
            t.run(art.save)
            t.created(art)
            t.created(aa )
            t.created(aa1)
            t.created(fact1)
            t.created(fact2)

            # FIXME The save is reloading art.artist_arifacts for some
            # reason. See related at d7a42a95
            t.retrieved(art.artist_artifacts)


        with self._chrontest() as t:
            art1 = t.run(lambda: artist(art.id))
            t.retrieved(art1)

        self.two(art1.artist_artifacts)
        self.two(art1.artifacts)

        aa1 = art1.artist_artifacts[aa.id]

        self.eq(art.id,               art1.id)
        self.eq(aa.id,                aa1.id)
        self.eq(aa.role,              aa1.role)
        self.eq(aa.artist.id,         aa1.artist.id)
        self.eq(aa.artist__artistid,  aa1.artist__artistid)

        self.eq(aa.artifact.id,  aa1.artifact.id)
        self.eq(
            aa.artifact__artifactid,
            aa1.artifact__artifactid
        )

        # Add as second artist_artifact, save, reload and test
        aa2 = artist_artifact.getvalid()
        aa2.artifact = artifact.getvalid()

        art1.artist_artifacts += aa2

        self.three(art1.artist_artifacts)
        self.three(art1.artifacts)

        with self._chrontest() as t:
            t.run(art1.save)
            t.created(aa2)
            t.created(aa2.artifact)

        art2 = artist(art1.id)
        self.eq(art1.id,         art2.id)

        aas1=art1.artist_artifacts.sorted('role')
        aas2=art2.artist_artifacts.sorted('role')

        for aa1, aa2 in zip(aas1, aas2):

            self.eq(aa1.id,           aa2.id)
            self.eq(aa1.role,         aa2.role)

            self.eq(aa1.artist.id,    aa2.artist.id)
            self.eq(
                aa1.artist__artistid,     
                aa2.artist__artistid
            )

            self.eq(aa1.artifact.id,  aa2.artifact.id)
            self.eq(
                aa1.artifact__artifactid,
                aa2.artifact__artifactid
            )

        # Add a third artifact to artist's pseudo-collection.
        # Save, reload and test.
        art2.artifacts += artifact.getvalid()
        art2.artist_artifacts.last.role = uuid4().hex
        art2.artist_artifacts.last.planet = uuid4().hex
        art2.artist_artifacts.last.timespan = uuid4().hex
        
        self.four(art2.artifacts)
        self.four(art2.artist_artifacts)

        with self._chrontest() as t:
            t.run(art2.save)
            t.created(art2.artist_artifacts.fourth)
            t.created(art2.artist_artifacts.fourth.artifact)

        art3 = artist(art2.id)

        self.four(art3.artifacts)
        self.four(art3.artist_artifacts)

        aas2 = art2.artist_artifacts.sorted('role')
        aas3 = art3.artist_artifacts.sorted('role')

        for aa2, aa3 in zip(aas2, aas3):
            self.eq(aa2.id,                    aa3.id)
            self.eq(aa2.role,                  aa3.role)
            self.eq(aa2.artist.id,             aa3.artist.id)
            self.eq(aa2.artist__artistid,      aa3.artist__artistid)
            self.eq(aa2.artifact.id,           aa3.artifact.id)
            self.eq(aa2.artifact__artifactid,  aa3.artifact__artifactid)

        # Add two components to the artifact's components collection
        comps3 = components()
        for _ in range(2):
            comps3 += component.getvalid()

        comps3.sort()
        art3.artist_artifacts.first.artifact.components += comps3.first
        art3.artifacts.first.components += comps3.second

        self.two(art3.artist_artifacts.first.artifact.components)
        self.two(art3.artifacts.first.components)

        self.is_(
            comps3[0], 
            art3.artist_artifacts[0].artifact.components[0]
        )
        self.is_(
            comps3[1], 
            art3.artist_artifacts[0].artifact.components[1]
        )
        self.is_(
            comps3[0], 
            art3.artifacts[0].components[0]
        )
        self.is_(
            comps3[1], 
            art3.artifacts[0].components[1]
        )

        with self._chrontest() as t:
            t.run(art3.save)
            t.created(comps3.first)
            t.created(comps3.second)

        art4 = artist(art3.id)
        comps4 = art4.artist_artifacts[0].artifact.components.sorted()

        self.two(comps4)
        self.eq(comps4.first.id, comps3.first.id)
        self.eq(comps4.second.id, comps3.second.id)

        # This fixes an issue that came up in development: When you add
        # valid aa to art, then add a fact to art (thus adding an
        # invalid aa to art), strange things were happening with the
        # brokenrules. 
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

        with self._chrontest() as t:
            t.run(art1.save)
            t.updated(*art1.artist_artifacts)

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
        # FIXME Removing associations is broken at the moment because it
        # cascades any deletion of an association. 
        #
        # The following code
        #     
        #     art.artifacts.shift()
        #
        # should delete the artist_artists association and the artifact.
        # However, the (presumed synonymous): code:
        #
        #     art.artist_artifacts.shift()
        #
        # should remove the association but not the artifact.
        #
        # In associations._self._onremove, a line was added which is
        # currently commented out:
        # 
        #   es.orm.trash.pop()
        #
        # It corrects the problem with adding the artifact to the trash
        # collection. However, the entity._save method still causes the
        # artifact to be deleted. Some investigation into that should be
        # undertaken to correct the issue.
        #
        # Note that the it_removes_reflexive_associations test will also
        # need to be updated when this bug has been corrected.

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
                self.eq(
                    aa.artist__artistid,
                    aa1.artist__artistid
                )

                self.eq(aa.artifact.id,  aa1.artifact.id)
                self.eq(
                    aa.artifact__artifactid,
                    aa1.artifact__artifactid
                )

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
        save, pres._save = pres._save, lambda cur, guestbook: 0/0

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
        fn = lambda cur, guestbook: 0/0
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
        self.expect(AttributeError, lambda: art.artist_artists.objectX)

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
        # presentations properties
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

        # ref: 7adeeffe
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

        art = artist.getvalid()

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

        # The presentation objects here aren't the same reference so
        # they will have different states.
        self.ne(loc2.presentation.name, name)
        self.eq(loc2.presentation.artist.presentations.first.name, name)

        # However, saving does update the presentation object
        with self._chrontest() as t:
            t.run(loc2.save)
            t.updated(loc2.presentation.artist.presentations.first)

        loc2 = location(loc2.id)

        # The above save() saved the new artist's presentation
        # collection so the new name will be present in the reloaded
        # presentation object.
        self.eq(loc2.presentation.name, name)
        self.eq(loc2.presentation.artist.presentations.first.name, name)

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
        art.presentations.last._save = lambda cur, guestbook: 1/0

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
        art.artist_artifacts += artist_artifact.getvalid()
        aa = art.artist_artifacts.first
        aa.artifact = artifact.getvalid()

        self.eq(aa['role'], aa.role)

        expected = aa.role, aa.planet
        actual = aa['role', 'planet']
    
        self.eq(expected, actual)
        self.expect(IndexError, lambda: aa['idontexist'])

        actual = aa['artist', 'artifact']
        expected = aa.artist, aa.artifact

        self.two([x for x in actual if x is not None])
        self.two([x for x in expected if x is not None])

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
        sng.bio1      = uuid4().hex
        sng.bio2      = uuid4().hex
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
        sng.bio1      = uuid4().hex
        sng.bio2      = uuid4().hex
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
        rpr.bio1      = uuid4().hex
        rpr.bio2      = uuid4().hex
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
        rpr.bio1      = uuid4().hex
        rpr.bio2      = uuid4().hex
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
        rpr.bio1      = uuid4().hex
        rpr.bio2      = uuid4().hex
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
        art.bio1  = uuid4().hex
        art.bio2  = uuid4().hex
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
            art.bio1      = 'herp'
            art.bio2      = 'derp'
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
            art.bio1      = 'herp'
            art.bio2      = 'derp'
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

            # Test Varchar
            art = artist()

            map = art.orm.mappings['bio1']
            self.false(map.isfixed)
            self.eq('longtext', map.dbtype)
            self.eq(4001, map.max)
            self.eq(1, map.min)

            map = art.orm.mappings['bio2']
            self.false(map.isfixed)
            self.eq('varchar(4000)', map.dbtype)
            self.eq(4000, map.max)
            self.eq(1, map.min)

            # Test longtext
            art = artist()
            art.firstname = uuid4().hex
            art.lastname  = uuid4().hex
            art.lifeform  = uuid4().hex
            art.password  = bytes([randint(0, 255) for _ in range(32)])
            art.phone     = '1' * 7
            art.email     = 'username@domain.tld'
            art.ssn       = V * 11
            art.bio1      = 'herp'
            art.bio2      = 'derp'
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
        art.dob1 = '2005-01-10'
        self.type(primative.datetime, art.dob)
        self.type(primative.datetime, art.dob1)

        expect = datetime(2004, 1, 10, tzinfo=utc)
        self.eq(expect, art.dob)

        expect = datetime(2005, 1, 10, tzinfo=utc)
        self.eq(expect, art.dob1)
       
        # Save, reload, test
        art.save()
        expect = datetime(2004, 1, 10, tzinfo=utc)
        self.eq(expect, artist(art.id).dob)
        self.type(primative.datetime, artist(art.id).dob)

        # Ensure dob1 saves and loads like dob
        expect = datetime(2005, 1, 10, tzinfo=utc)
        self.eq(expect, artist(art.id).dob1)
        self.type(primative.datetime, artist(art.id).dob1)

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
        art1.dob1       =  primative.datetime.now().replace(tzinfo=timezone.utc)
        art1.password   = bytes([randint(0, 255) for _ in range(32)])
        art1.ssn        = '2' * 11
        art1.bio        = uuid4().hex
        art1.bio1       = uuid4().hex
        art1.bio2       = uuid4().hex
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

        try:
            art.save()
        except MySQLdb.OperationalError as ex:
            # TODO Today, 20190815, we got a 
            #     MySQLdb.OperationalError(2006, 'MySQL server has gone away')
            # error instead of a BrokenRulesError. Why would we get this
            # from a simple save.
            # UPDATE Happened again 20190819
            # UPDATE Happened again 20191124
            print(
                'An MySQLdb.OperationalError occured. '
                'See comment above in source code.'
            )
            B()
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

        # Reflexive
        art.artists += artist.getvalid()
        aa = art.artist_artists.first

        d = dir(aa)

        for prop in aa.orm.properties:
            self.eq(1, d.count(prop))

    def it_calls_dir_on_entity_pseudocollection(self):
        # TODO Pseudocollection on reflexive association don't currently
        # work. See commented-out assertions.
        art = artist.getvalid()
        d = dir(art)
        self.true('artifacts' in d)
        #self.true('artists' in d)

        sng = singer.getvalid()
        d = dir(sng)
        self.true('artifacts' in d)
        #self.true('singers' in d)
        #self.true('artists' in d)
        
        rpr = rapper.getvalid()
        d = dir(rpr)
        self.true('artifacts' in d)
        #self.true('singers' in d)
        #self.true('artists' in d)
        
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

                    # TODO Calling cons.artists fails
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

        # FIXME The chrontests fail now that the chron tester checks for
        # duplicates.
        rpr.save()

        '''
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
        '''

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

        # The presentation objects here aren't the same reference so
        # they will have different states.
        self.ne(loc2.presentation.name, name)
        self.eq(loc2.presentation.artist.presentations.first.name, name)

        # However, saving does update the presentation object
        with self._chrontest() as t:
            t.run(loc2.save)
            t.updated(loc2.presentation.artist.presentations.first)

        loc2 = location(loc2.id)

        # The above save() saved the new artist's presentation
        # collection so the new name will be present in the reloaded
        # presentation object.
        self.eq(loc2.presentation.name, name)
        self.eq(loc2.presentation.artist.presentations.first.name, name)


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

        # NOTE Going up the graph, mutating attributes and persisting
        # lower in the graph won't work because of the problem of
        # infinite recursion.  The below tests demonstrate this.

        # Assign a new name
        name = uuid4().hex
        loc2.presentation.artist.presentations.first.name = name

        # The presentation objects here aren't the same reference so
        # they will have different states.
        self.ne(loc2.presentation.name, name)
        self.eq(loc2.presentation.artist.presentations.first.name, name)

        # However, saving does update the presentation object
        with self._chrontest() as t:
            t.run(loc2.save)
            t.updated(loc2.presentation.artist.presentations.first)

        loc2 = location(loc2.id)

        # The above save() saved the new artist's presentation
        # collection so the new name will be present in the reloaded
        # presentation object.
        self.eq(loc2.presentation.name, name)
        self.eq(loc2.presentation.artist.presentations.first.name, name)

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
        sng.presentations.last._save = lambda cur, guestbook: 1/0

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
        rpr.presentations.last._save = lambda cur, guestbook: 1/0

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
        
        # FIXME The following chron tests fail now that the chron tester
        # no longer permits duplicate objects form being tested
        '''
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
        '''

        # Test deeply-nested (>2) constituents
        rpr.presentations.last.locations += location.getvalid()
        rpr.concerts.last.locations      += location.getvalid()

        # FIXME The following chron tests fail now that the chron tester
        # no longer permits duplicate objects form being tested
        '''
        for i in range(2):
            with self._chrontest() as t:
                t.run(rpr.save)
                if i == 0:
                    t.created(rpr.presentations.last.locations.last)
                    t.created(rpr.concerts.last.locations.last)
        '''

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
        sng1.dob1      = datetime.now()
        sng1.dob2      = datetime.now()
        sng1.password  = bytes([randint(0, 255) for _ in range(32)])
        sng1.ssn       = '2' * 11
        sng1.bio       = uuid4().hex
        sng1.bio1      = uuid4().hex
        sng1.bio2      = uuid4().hex
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
        rpr1.dob1      = datetime.now()
        rpr1.dob2      = datetime.now()
        rpr1.password  = bytes([randint(0, 255) for _ in range(32)])
        rpr1.ssn       = '2' * 11
        rpr1.bio       = uuid4().hex
        rpr1.bio1      = uuid4().hex
        rpr1.bio2      = uuid4().hex
        rpr1.email     = 'username1@domain.tld'
        rpr1.title     = uuid4().hex[0]
        rpr1.phone2    = uuid4().hex[0]
        rpr1.email_1   = uuid4().hex[0]
        rpr1.nice      = rpr.nice + 1
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
            except MySQLdb.OperationalError as ex:
                # This happened today (Oct 30 2019)
                #    OperationalError(2006, 'MySQL server has gone away') 
                # AGAIN Jan 23, 2020

                print(ex)
                B()
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

        es = [rpr.orm.entity] + rpr.orm.entity.orm.superclasses
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

    def _create_join_test_reflexive_data(self):
        """ Create test data to test inner/outer joins against reflexive
        associations.
        """

        for c in (artist, presentation, artist_artist):
            c.orm.truncate()

        # The artist entities and constituents will have sequential
        # indexes to query against.
        arts = artists()
        for i in range(4):
            art = artist.getvalid()
            art.firstname = 'fn-' + str(i)
            art.lastname = 'ln-'  + str(i + 1)
            art.lifeform = 'subject'
            arts += art

            for k in range(4):
                aa = artist_artist.getvalid()
                aa.role = 'art-art_art-role-' + str(k)
                aa.slug = 'art-art_art-slug-' + str(k + 1)
                artobj = artist.getvalid()

                aa.object = artobj
                artobj.firstname = 'art-art_art-art-fn-' + str(k)
                artobj.lastname = 'art-art_art-art-ln' + str(k + 1)
                artobj.lifeform = 'object'

                art.artist_artists += aa

                for l in range(4):
                    pres = presentation.getvalid()
                    name = 'art-art_art-art-presentation-name-' + str(l)
                    pres.name =  name
                    artobj.presentations += pres

        arts.save()
        return arts

    def _create_join_test_subentity_reflexive_data(self):
        """ Create test data to test inner/outer joins against the
        subenties joined by reflexive associations.
        """

        for c in (singers, artist, presentation, artist_artist):
            c.orm.truncate()

        # The singer entities and constituents will have sequential
        # indexes to query against.
        sngs = singers()
        for i in range(4):
            sng = singer.getvalid()
            sng.firstname = 'fn-' + str(i)
            sng.lastname = 'ln-'  + str(i + 1)
            sng.lifeform = 'subject'
            sng.register = 'reg-' + str(i)
            sngs += sng

            ''' Create singers '''
            for k in range(4):
                aa = artist_artist.getvalid()
                aa.role = 'sng-art_art-role-' + str(k)
                aa.slug = 'sng-art_art-slug-' + str(k + 1)
                sngobj = singer.getvalid()

                aa.object = sngobj
                sngobj.firstname = 'sng-art_art-sng-fn-' + str(k)
                sngobj.lastname = 'sng-art_art-sng-ln' + str(k + 1)
                sngobj.register = 'sng-art_art-sng-reg-'+ str(k)
                sngobj.lifeform = 'object'

                sng.artist_artists += aa

                for l in range(4):
                    conc = concert.getvalid()
                    name = 'sng-art_art-sng-conc-name-' + str(l)
                    conc.name =  name
                    sngobj.concerts += conc

            ''' Create painters '''
            for k in range(4, 8):
                aa = artist_artist.getvalid()
                aa.role = 'sng-art_art-role-' + str(k)
                aa.slug = 'sng-art_art-slug-' + str(k + 1)
                pntobj = painter.getvalid()

                aa.object = pntobj
                pntobj.firstname = 'sng-art_art-pnt-fn-' + str(k)
                pntobj.lastname = 'sng-art_art-pnt-ln' + str(k + 1)
                pntobj.style = 'sng-art_art-pnt-sty-'+ str(k)

                sng.artist_artists += aa

                for l in range(4):
                    exh = exhibition.getvalid()
                    name = 'sng-art_art-pnt-exh-name-' + str(l)
                    exh.name =  name
                    pntobj.exhibitions += exh

            ''' Create muralists '''
            for k in range(8, 12):
                aa = artist_artist.getvalid()
                aa.role = 'sng-art_art-role-' + str(k)
                aa.slug = 'sng-art_art-slug-' + str(k + 1)
                murobj = muralist.getvalid()

                aa.object = murobj
                murobj.firstname = 'sng-art_art-mur-fn-' + str(k)
                murobj.lastname = 'sng-art_art-mur-ln' + str(k + 1)
                murobj.style = 'sng-art_art-mur-sty-'+ str(k)
                murobj.street = True

                sng.artist_artists += aa

                for l in range(4):
                    unv = unveiling.getvalid()
                    name = 'sng-art_art-mur-unv-name-' + str(l)
                    unv.name =  name
                    murobj.unveilings += unv

        sngs.save()
        return sngs

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
            # Load an innerjoin where both tables have [NOT] IN where clause
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

            self.eq(aa1.artifact__artifactid, aa1.artifact.id)

            self.eq(fff, aa1.orm.persistencestate)

            # The call to aa1.artifact wil lazy-load artifact which will add to
            # self.chronicles
            self.eq('retrieve', self.chronicles.last.op)

            self.is_(aa1.artifact, self.chronicles.last.entity)

            self.eq(fff, aa1.artifact.orm.persistencestate)

        # NOTE This wil lazy-load aa1.artifact 4 times
        self.four(self.chronicles)

        # Test unconditionally joining the associated entities
        # collections (artist_artifacts) with its composite (artifacts)
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

        # Test joining the associated entities collections
        # (artist_artifacts) with its composite (artifacts) where the
        # composite's join is conditional.
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

        # Test joining the associated entities collections
        # (artist_artifacts) with its composite (artifacts) where the
        # composite's join is conditional along with the other two.
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
        
    def it_fails_parsing_malformed_predicates(self):
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

    def it_loads_and_saves_reflexive_associations(self):
        art = artist.getvalid()
        aa = art.artist_artists
        self.zero(aa)

        # Ensure property caches
        self.is_(aa, art.artist_artists)

        # Test loading associated collection
        artsb = art.artists
        self.zero(artsb)

        # Ensure property caches
        self.is_(artsb, art.artists)

        # Ensure the association's associated collections is the same as
        # the associated collection of the entity.

        self.is_(art.artists, art.artist_artists.artists)
        self.is_(art, art.artist_artists.artist)

        # Save and load an association
        aa                    =   artist_artist.getvalid()
        aa.role               =   uuid4().hex
        objart                =   artist.getvalid()
        aa.object             =   objart
        art.artist_artists    +=  aa

        self.is_(art,     art.artist_artists.first.subject)
        self.is_(objart,  art.artist_artists.first.object)
        self.isnot(art,   art.artist_artists.first.object)
        self.eq(aa.role,  art.artist_artists.first.role)

        self.one(art.artist_artists)
        self.one(art.artists)

        with self._chrontest() as t:
            t.run(art.save)
            t.created(art, aa, objart)

            # FIXME The save is reloading art.artist_arifacts for some
            # reason. See related at d7a42a95
            t.retrieved(art.artist_artists)

        with self._chrontest() as t:
            art1 = t.run(lambda: artist(art.id))
            t.retrieved(art1)
        
        self.one(art1.artist_artists)
        self.one(art1.artists)

        aa1 = art1.artist_artists.first

        self.eq(art.id,          art1.id)
        self.eq(aa.id,           aa1.id)
        self.eq(aa.role,         aa1.role)

        self.eq(aa.subject.id,         aa1.subject.id)
        self.eq(aa.subject__artistid,  aa1.subject__artistid)
        self.eq(aa.object.id,          aa1.object.id)
        self.eq(aa.object__artistid,   aa1.object__artistid)

        # Add as second artist_artist, save, reload and test
        aa2           =  artist_artist.getvalid()
        aa2.object    =  artist.getvalid()

        art1.artist_artists += aa2

        self.is_(art1,    aa2.subject)
        self.isnot(art1,  aa2.object)

        with self._chrontest() as t:
            t.run(art1.save)
            t.created(aa2, aa2.object)

        art2 = artist(art1.id)
        self.eq(art1.id,         art2.id)

        aas1=art1.artist_artists.sorted('role')
        aas2=art2.artist_artists.sorted('role')

        for aa1, aa2 in zip(aas1, aas2):
            self.eq(aa1.id,           aa2.id)
            self.eq(aa1.role,         aa2.role)

            self.eq(aa1.subject.id,         aa2.subject.id)
            self.eq(aa1.subject__artistid,  aa2.subject__artistid)
            self.eq(aa1.object.id,          aa2.object.id)
            self.eq(aa1.object__artistid,   aa2.object__artistid)

        # Add a third artist to artist's pseudo-collection.
        # Save, reload and test.
        objart = artist.getvalid()
        art2.artists += objart

        self.is_(art2,            art2.artist_artists.last.subject)
        self.is_(objart,          art2.artist_artists.last.object)
        art2.artist_artists.last.role = uuid4().hex
        art2.artist_artists.last.slug = uuid4().hex
        art2.artist_artists.last.timespan = uuid4().hex
        aa2 = art2.artist_artists.last

        self.three(art2.artists)
        self.three(art2.artist_artists)
        self.isnot(aa2.subject,  aa2.object)

        with self._chrontest() as t:
            t.run(art2.save)
            t.created(art2.artist_artists.third)
            t.created(art2.artist_artists.third.object)

        art3 = artist(art2.id)

        self.three(art3.artists)
        self.three(art3.artist_artists)

        aas2 = art2.artist_artists.sorted('role')
        aas3 = art3.artist_artists.sorted('role')

        for aa2, aa3 in zip(aas2, aas3):
            self.eq(aa2.id,                 aa3.id)
            self.eq(aa2.role,               aa3.role)
            self.eq(aa2.subject.id,         aa3.subject.id)
            self.eq(aa2.object.id,          aa3.object.id)
            self.eq(aa2.subject__artistid,  aa3.subject__artistid)
            self.eq(aa2.object__artistid,   aa3.object__artistid)

        # Add two presentations to the artist's presentations collection
        press3 = presentations()
        for _ in range(2):
            press3 += presentation.getvalid()

        press3.sort()
        art3.artist_artists.first.object.presentations += press3.first
        art3.artists.first.presentations += press3.second

        self.two(art3.artist_artists.first.object.presentations)
        self.two(art3.artists.first.presentations)

        self.is_(press3[0], art3.artist_artists[0].object.presentations[0])
        self.is_(press3[1], art3.artist_artists[0].object.presentations[1])
        self.is_(press3[0], art3.artists[0].presentations[0])
        self.is_(press3[1], art3.artists[0].presentations[1])

        with self._chrontest() as t:
            t.run(art3.save)
            t.created(press3.first)
            t.created(press3.second)

        art4 = artist(art3.id)
        press4 = art4.artist_artists.first.object.presentations.sorted()

        self.two(press4)
        self.eq(press4.first.id, press3.first.id)
        self.eq(press4.second.id, press3.second.id)

        # NOTE The below comment and tests were carried over from
        # it_loads_and_saves_associations:
        # This fixes an issue that came up in development: When you add valid
        # aa to art, then add a fact to art (thus adding an invalid aa to art),
        # strange things were happening with the brokenrules. 
        art = artist.getvalid()
        art.artist_artists += artist_artist.getvalid()
        art.artists += artist.getvalid()

        self.zero(art.artist_artists.first.brokenrules)
        self.zero(art.artist_artists.first.brokenrules)
        self.three(art.artist_artists.second.brokenrules)
        self.three(art.brokenrules)

        # Fix broken aa
        art.artist_artists.second.role = uuid4().hex
        art.artist_artists.second.slug = uuid4().hex
        art.artist_artists.second.timespan = uuid4().hex

        self.zero(art.artist_artists.second.brokenrules)
        self.zero(art.brokenrules)

    def it_updates_reflexive_association(self):
        # TODO We should test updateing aa.subject and aa.object
        art = artist.getvalid()

        for i in range(2):
            aa = artist_artist.getvalid()
            art.artist_artists += aa

        # TODO This should not be possible because no object was
        # assigned to aa (assert aa.object is None). There should be a
        # broken rule preventing this. 
        #
        # I think this test has a bug in it, though. We should be
        # assigning 
        #
        #   aa.object = artist.getvalid()
        # 
        # above.
        art.save()

        art1 = artist(art.id)

        for aa in art1.artist_artists:
            aa.role = uuid4().hex

        # Save and reload
        with self._chrontest() as t:
            t.run(art1.save)
            t.updated(*art1.artist_artists)

        art2 = artist(art1.id)

        aas  = art. artist_artists.sorted('role')
        aas1 = art1.artist_artists.sorted('role')
        aas2 = art2.artist_artists.sorted('role')

        for aa, aa2 in zip(aas, aas2):
            self.ne(aa.role, aa2.role)

        for aa1, aa2 in zip(aas1, aas2):
            self.eq(aa1.role, aa2.role)

        # TODO Test deeply nested associations

    def it_updates_reflexive_associations_constituent_entity(self):
        art = artist.getvalid()

        for i in range(2):
            aa = artist_artist.getvalid()
            aa.object = artist.getvalid()
            art.artist_artists += aa

        self.two(art.artist_artists)
        self.two(art.artists)

        art.save()

        art1 = artist(art.id)

        for art2 in art1.artists:
            art2.firstname = uuid4().hex

        with self._chrontest() as t:
            t.run(art1.save)
            t.updated(*art1.artists)

        art2 = artist(art1.id)

        self.two(art1.artists)
        self.two(art2.artists)

        artobjs  = art. artists.sorted('firstname')
        artobjs1 = art1.artists.sorted('firstname')
        artobjs2 = art2.artists.sorted('firstname')

        for artb, artb2 in zip(artobjs, artobjs2):
            self.ne(artb.firstname, artb2.firstname)

        for artb1, artb2 in zip(artobjs1, artobjs2):
            self.eq(artb1.firstname, artb2.firstname)

        attrs = (
            'artists.first.presentations',
            'artist_artists.first.object.presentations'
        )

        for attr in attrs:
            press = getattr(art2, attr)
            press += presentation.getvalid()

        self.two(press)

        art2.save()

        art3 = artist(art2.id)

        for attr in attrs:
            press = getattr(art3, attr)
            for pres in press:
                pres.name = uuid4().hex

        with self._chrontest() as t:
            t.run(art3.save)
            t.updated(art3.artists.first.presentations.first)
            t.updated(art3.artists.first.presentations.second)

        art4 = artist(art3.id)

        for attr in attrs:
            press2 = getattr(art2, attr)
            press3 = getattr(art3, attr)
            press4= getattr(art4, attr)

            self.two(press2)
            self.two(press3)
            self.two(press4)

            for pres4 in press4:
                for pres2 in press2:
                    self.ne(pres2.name, pres4.name)

            for pres4 in press4:
                for pres3 in press3:
                    if pres4.name == pres3.name:
                        break
                else:
                    self.fail('No match within press4 and press3')

        # TODO Test deeply nested associations

    def it_calls__getitem__on_reflexive_association(self):
        art = artist()
        art.artist_artists += artist_artist.getvalid()
        aa = art.artist_artists.first
        aa.object = artist.getvalid()

        self.eq(aa['role'], aa.role)

        expected = aa.role, aa.slug
        actual = aa['role', 'slug']

        self.eq(expected, actual)
        self.expect(IndexError, lambda: aa['idontexist'])

        actual = aa['object', 'subject']
        expected = aa.object, aa.subject

        self.two([x for x in actual if x is not None])
        self.two([x for x in expected if x is not None])

        self.eq(actual, expected)

        # Custom attributes and fields
        aa.timespan = '1/1/2001 3/3/2001'
        actual = aa['timespan', 'processing']
        expected = aa.timespan, aa.processing
        self.eq(actual, expected)

    def it_calls_innerjoin_on_reflexive_associations(self):
        arts = self._create_join_test_reflexive_data()

        fff = False, False, False

        # Test artists joined with artist_artists with no condititons
        arts1 = artists & artist_artists

        self.one(arts1.orm.joins)

        self.four(arts1)

        arts.sort()
        arts1.sort()
        
        self.chronicles.clear()

        for art, art1 in zip(arts, arts1):
            self.eq(art.id, art1.id)

            self.eq(fff, art1.orm.persistencestate)

            self.four(art1.artist_artists)

            art.artist_artists.sort()
            art1.artist_artists.sort()

            for aa, aa1 in zip(art.artist_artists, art1.artist_artists):
                self.eq(aa.id, aa.id)

                self.eq(fff, aa1.orm.persistencestate)

                self.eq(aa.subject.id, aa1.subject.id)
                aa1.object

                self.eq(aa.object.id, aa1.object.id)

                self.is_(aa1.subject, art1)

        # NOTE The above will lazy-load aa1.object 16 times
        self.count(16, self.chronicles)

        # Test artists joined with artist_artists where the association has a
        # conditional
        arts1 = artists.join(
            artist_artists('role = %s', ('art-art_art-role-0',))
        )

        self.one(arts1.orm.joins)

        self.four(arts1)

        self.chronicles.clear()

        arts1.sort()
        for art, art1 in zip(arts, arts1):
            self.eq(art.id, art1.id)

            self.eq(fff, art1.orm.persistencestate)

            self.one(art1.artist_artists)

            aa1 = art1.artist_artists.first
            self.eq(aa1.role, 'art-art_art-role-0')

            self.is_(art1, aa1.subject)
            self.eq(aa1.subject__artistid, aa1.subject.id)
            self.eq(aa1.object__artistid, aa1.object.id)

            self.eq(fff, aa1.orm.persistencestate)

            self.eq(fff, aa1.subject.orm.persistencestate)
            self.eq(fff, aa1.object.orm.persistencestate)

        # Test unconditionally joining the associated entities
        # collections (artist_artists) with its composite (artists)
        for b in False, True:
            if b:
                # Implicitly join artist_artists
                arts1 = artists & artists
            else:
                # Explicitly join artist_artists
                arts1 = artists
                arts1 &= artist_artists & artists

            self.one(arts1.orm.joins)

            self.type(artist_artists, arts1.orm.joins.first.entities)
            self.one(arts1.orm.joins.first.entities.orm.joins)
            objarts = arts1.orm.joins.first.entities.orm.joins.first.entities
            self.type(artists, objarts)

            arts1.sort()

            self.chronicles.clear()

            self.four(arts1)

            for art, art1 in zip(arts, arts1):
                self.eq(art.id, art1.id)

                self.eq(fff, art1.orm.persistencestate)

                self.four(art1.artist_artists)

                art.artist_artists.sort()
                art1.artist_artists.sort()

                aass = zip(art.artist_artists, art1.artist_artists)
                for aa, aa1 in aass:
                    self.eq(fff, aa1.orm.persistencestate)
                    self.eq(aa.id, aa.id)
                    self.eq(
                        aa.subject__artistid, 
                        aa1.subject__artistid
                    )
                    self.eq(
                        aa.object__artistid, 
                        aa1.object__artistid
                    )
                    self.eq(aa.subject.id, aa1.subject.id)
                    self.eq(aa.object.id, aa1.object.id)

            self.zero(self.chronicles)

        # Test joining the associated entities collections
        # (artist_artists) with its composite (artists) where the
        # composite's join is conditional.
        for b in True, False:
            if b:
                # Explicitly join artist_artists
                arts1 = artists() 
                arts1 &= artist_artists.join(
                            artists(
                                'firstname = %s', 
                                ('art-art_art-art-fn-1',)
                            )
                        )
            else:
                # Implicitly join artist_artists
                arts1 = artists().join(
                            artists(
                                'firstname = %s', 
                                ('art-art_art-art-fn-1',)
                            )
                        )
            self.one(arts1.orm.joins)
            self.type(artist_artists, arts1.orm.joins.first.entities)
            self.one(arts1.orm.joins.first.entities.orm.joins)
            objarts = arts1.orm.joins.first.entities.orm.joins.first.entities
            self.type(artists, objarts)

            arts1.sort()

            self.four(arts1)

            self.chronicles.clear()
            for art, art1 in zip(arts, arts1):
                self.eq(fff, art1.orm.persistencestate)
                self.eq(art.id, art1.id)

                aas = art1.artist_artists
                self.one(aas)
                self.eq(
                    'art-art_art-art-fn-1', 
                    aas.first.object.firstname
                )
                self.eq(fff, aas.first.orm.persistencestate)

            self.zero(self.chronicles)

        # Test joining the associated entities collections
        # (artist_artists) with its composite (artists) where the
        # composite's join is conditional along with the other two.
        arts1 =  artists('firstname = %s', ('fn-1')).join(
                    artist_artists(
                        'role = %s', 
                        ('art-art_art-role-0',)
                     ).join(
                         artists(
                             'firstname = %s', 
                             ('art-art_art-art-fn-0',)
                         )
                    )
                 )

        self.one(arts1)

        self.chronicles.clear()
        self.eq('fn-1', arts1.first.firstname)

        aas1 = arts1.first.artist_artists
        self.one(aas1)
        self.eq(fff, aas1.first.orm.persistencestate)
        self.eq('art-art_art-role-0', aas1.first.role)
        self.eq('art-art_art-art-fn-0', aas1.first.object.firstname)
        self.eq(arts1.first.id, aas1.first.subject.id)
        self.eq(arts1.first.id, aas1.first.subject__artistid)
        self.ne(
            aas1.first.subject__artistid,
            aas1.first.object__artistid
        )
        self.eq(
            aas1.first.object.id,
            aas1.first.object__artistid
        )
        self.zero(self.chronicles)

        # Test joining a constituent (presentations) of the composite
        # (artists) of the association (artist_artists) without
        # conditions.
        for b in True, False:
            if b:
                # Explicitly join the associations (artist_artists())
                arts1 = artists.join(
                            artist_artists.join(
                                artists & presentations
                            )
                        )
            else:
                # Implicitly join the associations (artist_artists())
                arts1 =  artists.join(
                            artists & presentations
                         )

            self.four(arts1)

            arts1.sort()

            self.chronicles.clear()

            for art, art1 in zip(arts, arts1):
                self.eq(fff, art1.orm.persistencestate)
                self.eq(art.id, art1.id)
                aas = art.artist_artists.sorted()
                aas1 = art1.artist_artists.sorted()
                self.four(aas1)

                for aa, aa1 in zip(aas, aas1):
                    self.eq(fff, aa1.orm.persistencestate)
                    self.eq(aa.id, aa1.id)
                    artobj = aa.object
                    artobj1 = aa1.object
                    self.eq(fff, artobj1.orm.persistencestate)

                    self.eq(artobj.id, artobj1.id)

                    press = artobj.presentations.sorted()
                    press1 = artobj1.presentations.sorted()

                    self.four(press1)

                    for pres, pres1 in zip(press, press1):
                        self.eq(fff, pres1.orm.persistencestate)
                        self.eq(pres.id, pres1.id)

            self.zero(self.chronicles)

        # Test joining a constituent (presentation) of the composite
        # (artists) of the association (artist_artists) with conditions.
        aarole = 'art-art_art-role-1'
        fn = 'art-art_art-art-fn-1'
        presname = 'art-art_art-art-presentation-name-1'
        arts1 =  artists().join(
                    artist_artists(role = aarole).join(
                        artists(firstname = fn).join(
                            presentations(name = presname)
                        )
                    )
                 )


        arts1.sort()

        self.chronicles.clear()

        for art, art1 in zip(arts, arts1):
            self.eq(fff, art1.orm.persistencestate)

            self.eq(art.id, art1.id)
            aas1 = art1.artist_artists
            self.one(aas1)

            self.eq(aarole, aas1.first.role)
            self.eq(fff, aas1.first.orm.persistencestate)

            self.eq(fn, aas1.first.object.firstname)
            self.eq(fff, aas1.first.object.orm.persistencestate)

            self.one(aas1.first.object.presentations)

            self.eq(
                presname, 
                aas1.first.object.presentations.first.name
            )


        self.zero(self.chronicles)

    def it_removes_reflexive_associations(self):
        for removeby in 'pseudo-collection', 'association':
            art = artist.getvalid()
            for _ in range(2):
                art.presentations += presentation.getvalid()

            for i in range(2):
                aa = artist_artist.getvalid()
                aa.object = artist.getvalid()
                for _ in range(2):
                    aa.object.presentations += presentation.getvalid()
                art.artist_artists += aa
                
            art.save()

            art = artist(art.id)
            
            self.two(art.artist_artists)
            self.zero(art.artist_artists.orm.trash)
            self.two(art.artists)
            self.zero(art.artists.orm.trash)

            if removeby == 'pseudo-collection':
                rmart = art.artists.shift()
            elif removeby == 'association':
                rmart = art.artist_artists.shift().object

            rmpress = rmart.presentations

            rmaa = art.artist_artists.orm.trash.first

            self.one(art.artist_artists)
            self.one(art.artist_artists.orm.trash)
            self.one(art.artists)
            self.one(art.artists.orm.trash)

            for a1, a2 in zip(art.artists, art.artist_artists.artists):
                self.isnot(a1, rmart)
                self.isnot(a2, rmart)

            with self._chrontest() as t:
                t.run(art.save)
                t.deleted(rmpress.first)
                t.deleted(rmpress.second)
                t.deleted(rmart)
                t.deleted(art.artist_artists.orm.trash.first)

            art1 = artist(art.id)

            self.one(art1.artist_artists)
            self.zero(art1.artist_artists.orm.trash)
            self.one(art1.artists)
            self.zero(art1.artists.orm.trash)
                
            aas = art.artist_artists.sorted('role')
            aas1 = art1.artist_artists.sorted('role')

            for aa, aa1 in zip(aas, aas1):
                self.eq(aa.id,           aa1.id)
                self.eq(aa.role,         aa1.role)

                self.eq(
                    aa.subject__artistid,
                    aa1.subject__artistid
                )

                self.eq(
                    aa.object__artistid,
                    aa1.object__artistid
                )

                self.eq(aa.subject.id,  aa1.subject.id)
                self.eq(aa.object.id,   aa1.object.id)

            for art in art1.artists:
                self.ne(rmart.id, art.id)

            self.expect(
                db.RecordNotFoundError, 
                lambda: artist_artist(rmaa.id)
            )

            self.expect(
                db.RecordNotFoundError,
                lambda: artist(rmart.id)
            )

            for pres in rmpress:
                self.expect(
                    db.RecordNotFoundError, 
                    lambda: presentation(pres.id)
                )

        # TODO Test deeply nested associations

    def it_loads_and_saves_subentity_reflexive_associations(self):
        sng = singer.getvalid()

        with ct() as t:
            aa = t.run(lambda: sng.artist_artists)

        self.is_(sng, sng.artist_artists.orm.composite)

        self.zero(aa)

        # Ensure property memoizes
        self.is_(aa, sng.artist_artists)

        # Test loading associated collection
        with ct() as t:
            artsb = t.run(lambda: sng.artists)

        self.zero(artsb)
        self.type(artists, artsb)

        # Test loading associated subentity collection
        with ct() as t:
            sngsb = t(lambda: sng.singers)
            pntsb = t(lambda: sng.painters)
            mursb = t(lambda: sng.muralists)

        self.type(singers, sngsb)
        self.type(painters, pntsb)
        self.type(muralists, mursb)
        self.zero(sngsb)
        self.zero(pntsb)
        self.zero(mursb)

        # Ensure association is same after accessing `singers`
        # pseudocollection.
        self.is_(aa, sng.artist_artists)

        # Ensure property memoizes
        self.is_(artsb, sng.artists)
        self.is_(sngsb, sng.singers)
        self.is_(pntsb, sng.painters)
        self.is_(mursb, sng.muralists)

        # Ensure the association's associated collections is the same as
        # the associated collection of the entity.
        self.is_(sng.artists,    sng.artist_artists.artists)
        self.is_(sng.singers,    sng.artist_artists.singers)
        self.is_(sng.painters,   sng.artist_artists.painters)
        self.is_(sng.muralists,  sng.artist_artists.muralists)

        self.is_(sng,            sng.artist_artists.singer)
        self.is_(sng.orm.super,  sng.artist_artists.artist)

        ''' Save and load an association '''

        # Singer
        aa                    =   artist_artist.getvalid()
        aa.role               =   uuid4().hex
        objsng                =   singer.getvalid()
        aa.object             =   objsng
        sng.artist_artists    +=  aa

        self.is_    (sng,      sng.artist_artists.first.subject)
        self.is_    (objsng,   sng.artist_artists.first.object)
        self.isnot  (sng,      sng.artist_artists.first.object)
        self.eq     (aa.role,  sng.artist_artists.first.role)

        # Painter
        aa                    =   artist_artist.getvalid()
        aa.role               =   uuid4().hex
        objpnt                =   painter.getvalid()
        aa.object             =   objpnt
        sng.artist_artists    +=  aa

        # Muralist
        aa                    =   artist_artist.getvalid()
        aa.role               =   uuid4().hex
        objmur                =   muralist.getvalid()
        aa.object             =   objmur

        sng.artist_artists    +=  aa


        self.three(sng.artist_artists)

        # TODO Should adding singer to sng.artist_artists result in an
        # addition to sng.artists
        # self.one(sng.artists)
        self.zero(sng.artists)

        self.one(sng.painters)
        self.one(sng.singers)
        self.one(sng.muralists)

        self.is_(objsng, sng.singers.first)
        self.is_(objpnt, sng.painters.first)
        self.is_(objmur, sng.muralists.first)

        with ct() as t:
            t.run(sng.save)
            t.created(sng, sng.orm.super)
            t.created(*sng.artist_artists)


            t.created(objsng, objsng.orm.super)
            t.created(objpnt, objpnt.orm.super)
            t.created(
                objmur, 
                objmur.orm.super,
                objmur.orm.super.orm.super
            )

            # FIXME The save is reloading sng.artist_arifacts for some
            # reason. See related at d7a42a95
            t.retrieved(sng.artist_artists)
                
        with ct() as t:
            sng1 = t.run(lambda: singer(sng.id))
            t.retrieved(sng1)

        with ct() as t:
            aas1 = t(lambda: sng1.artist_artists)
            t.retrieved(sng1.artist_artists)
            # FIXME We should not be retrieving artist here
            t.retrieved(sng1.artist_artists.artist)

        self.three(aas1)

        self.is_(sng1.orm.super, sng1.artist_artists.artist)
        self.is_(sng1, sng1.artist_artists.singer)

        with ct() as t:
            t(lambda: sng1.painters)

            # The associations.__getattr__ method will load each of the
            # thre `artist` entities from the association individually.
            t.retrieved(sng1.artist_artists.first.object)
            t.retrieved(sng1.artist_artists.second.object)
            t.retrieved(sng1.artist_artists.third.object)

            # The `associations.__getattr__` method will then load the
            # `painter` entity. Since the `muralist` entity is a type of
            # `painter` entity, it will be loaded in the `painters`
            # pseudocollection as wel.
            t.retrieved(sng1.painters.first)
            t.retrieved(sng1.painters.second)

        with ct() as t:
            t(lambda: sng1.singers)
            t.retrieved(sng1.singers.first)

        with ct() as t:
            t(lambda: sng1.muralists)
            t.retrieved(sng1.muralists.first)


        # Ensure pseudocollections are being memoized and have the
        # right count
        with ct() as t:
            self.three(t(lambda: sng1.artists))
            self.two(t(lambda: sng1.painters))
            self.one(t(lambda: sng1.singers))


        self.type(singer,    sng1)
        self.type(singer,    sng1.singers.first)
        self.type(muralist,  sng1.muralists.first)
        self.type(painter,   sng1.painters.first)
        self.type(painter,   sng1.painters.second)
        self.type(artist,    sng1.artists.first)
        self.type(artist,    sng1.artists.second)
        self.type(artist,    sng1.artists.third)

        self.eq(sng.id,         sng1.id)

        aa1 = sng1.artist_artists[sng.artist_artists.first.id]
        aa = sng.artist_artists.first
        self.eq(aa.id,                 aa1.id)
        self.eq(aa.role,               aa1.role)
        self.eq(aa.subject.id,         aa1.subject.id)
        self.eq(aa.subject__artistid,  aa1.subject__artistid)
        self.eq(aa.object.id,          aa1.object.id)
        self.eq(aa.object__artistid,   aa1.object__artistid)
        self.type(singer,              aa.object)
        self.type(artist,              aa1.object)

        aa = sng.artist_artists.second
        aa1 = sng1.artist_artists[aa.id]
        self.eq(aa.id,                 aa1.id)
        self.eq(aa.role,               aa1.role)
        self.eq(aa.subject.id,         aa1.subject.id)
        self.eq(aa.subject__artistid,  aa1.subject__artistid)
        self.eq(aa.object.id,          aa1.object.id)
        self.eq(aa.object__artistid,   aa1.object__artistid)
        self.type(painter,             aa.object)
        self.type(artist,              aa1.object)

        aa = sng.artist_artists.third
        aa1 = sng1.artist_artists[aa.id]
        self.eq(aa.id,                 aa1.id)
        self.eq(aa.role,               aa1.role)
        self.eq(aa.subject.id,         aa1.subject.id)
        self.eq(aa.subject__artistid,  aa1.subject__artistid)
        self.eq(aa.object.id,          aa1.object.id)
        self.eq(aa.object__artistid,   aa1.object__artistid)
        self.type(muralist,            aa.object)
        self.type(artist,              aa1.object)


        # NOTE
        # Q Should aa1.subject be artist or downcasted to singer?  
        # A No, since aa1 is an artist_artist type, it's `subject`
        # attribute must reflect that. If we wanted `subject` to be of
        # type `singer`, we should subclass artist_artist to create a
        # new association called `singer_singer`. However, we may want
        # to have an automatic downcasting property call
        # `as_<subentity>` that will return and downcasted version of
        # `subject` and that the graph will understand so it can be used
        # for persistence, e.g., 
        #
        #   aa1.subject.as_singer.register = 'laryngealization'
        #   aa1.save()
        #
        # UPDATE After thinking about this more, I don't see an issue
        # with artist_artist.subject and artist_artist.object
        # downcasting themselves to their most specialized types. This
        # would require additional, and prehaps needless database hits,
        # however, the convenience may be worth it.

        ''' Add three more (singer, painter and muralist) to
        artist_artist, save, reload and test '''

        # Add singer
        aa2           =  artist_artist.getvalid()
        objsng        =  singer.getvalid()
        aa2.object    =  objsng
        sng1.artist_artists += aa2

        self.is_(sng1,    aa2.subject)
        self.is_(objsng,  aa2.object)
        self.four(sng1.artist_artists)
        self.two(sng1.singers)

        # Add painter
        aa2           =  artist_artist.getvalid()
        objpnt        =  painter.getvalid()
        aa2.object    =  objpnt
        sng1.artist_artists += aa2

        self.is_(sng1,    aa2.subject)
        self.is_(objpnt,  aa2.object)
        self.five(sng1.artist_artists)
        self.two(sng1.singers)
        self.three(sng1.painters)

        # Add muralist
        aa2           =  artist_artist.getvalid()
        objmur        =  muralist.getvalid()
        aa2.object    =  objmur
        sng1.artist_artists += aa2

        self.is_(sng1,    aa2.subject)
        self.is_(objmur,  aa2.object)
        self.six(sng1.artist_artists)
        self.two(sng1.singers)
        self.three(sng1.painters)
        self.two(sng1.muralists)

        # TODO The artists collection will still have three `artist`s
        # entity objects. They are equal but not identical to the 
        # singer, muralist and painter that were loaded:
        # 
        #    assert sng1.singers.first.id == sng1.artists.first.id
        #    assert sng1.painters.first.id == sng1.artists.second.id
        #    assert sng1.muralists.first.id == sng1.artists.third.id
        #
        # However, we would expect the newly added singer and painter to
        # be in the `artists` collection as well. Some work needs to be
        # done to ensure that entity objects in these collections are
        # downcasted/upcasted correctely and propogated to the correct
        # entities collection object on load and on append.
        self.three(sng1.artists)

        with ct() as t:
            t(sng1.save)
            t.created(objsng,  objsng.orm.super)
            t.created(objpnt,  objpnt.orm.super)
            t.created(
                objmur,  
                objmur.orm.super, 
                objmur.orm.super.orm.super
            )
            t.created(*sng1.artist_artists.tail(3))

        sng2 = singer(sng1.id)
        self.eq(sng1.id, sng2.id)

        aas1=sng1.artist_artists.sorted('role')
        aas2=sng2.artist_artists.sorted('role')

        self.six(aas1); self.six(aas2)
        for aa1, aa2 in zip(aas1, aas2):
            self.eq(aa1.id,                 aa2.id)
            self.eq(aa1.role,               aa2.role)

            self.eq(aa1.subject.id,         aa2.subject.id)
            self.eq(aa1.subject__artistid,  aa2.subject__artistid)
            self.eq(aa1.object.id,          aa2.object.id)
            self.eq(aa1.object__artistid,   aa2.object__artistid)

        # Add a third singer and painter to their pseudo-collections.
        # Save, reload and test.
        objsng = singer.getvalid()
        sng2.singers += objsng

        objpnt = painter.getvalid()
        sng2.painters += objpnt

        objmur = muralist.getvalid()
        sng2.muralists += objmur


        self.is_(sng2,    sng2.artist_artists.antepenultimate.subject)
        self.is_(objsng,  sng2.artist_artists.antepenultimate.object)

        self.is_(sng2,    sng2.artist_artists.penultimate.subject)
        self.is_(objpnt,  sng2.artist_artists.penultimate.object)

        self.is_(sng2,    sng2.artist_artists.ultimate.subject)
        self.is_(objmur,  sng2.artist_artists.ultimate.object)


        for aa2 in sng2.artist_artists.tail(3):
            aa2.role      =  uuid4().hex
            aa2.slug      =  uuid4().hex
            aa2.timespan  =  uuid4().hex
            self.isnot(aa2.subject,  aa2.object)


        self.three(sng2.singers)
        self.five(sng2.painters)
        self.three(sng2.muralists)
        self.nine(sng2.artist_artists)

        with ct() as t:
            t(sng2.save)
            t.created(
                *sng2.artist_artists.tail(3),
                *sng2.artist_artists.tail(3).pluck('object'),
                sng2.artist_artists.antepenultimate.object.orm.super,
                sng2.artist_artists.penultimate.object.orm.super,
                sng2.artist_artists.last.object.orm.super,
                sng2.artist_artists.last.object.orm.super.orm.super
            )

        sng3 = singer(sng2.id)

        self.three(sng3.singers)
        self.six(sng3.painters)
        self.three(sng3.muralists)
        self.nine(sng3.artist_artists)


        aas2 = sng2.artist_artists.sorted('role')
        aas3 = sng3.artist_artists.sorted('role')

        self.nine(aas2); self.nine(aas3)
        for aa2, aa3 in zip(aas2, aas3):
            self.eq(aa2.id,                 aa3.id)
            self.eq(aa2.role,               aa3.role)
            self.eq(aa2.subject.id,         aa3.subject.id)
            self.eq(aa2.object.id,          aa3.object.id)
            self.eq(aa2.subject__artistid,  aa3.subject__artistid)
            self.eq(aa2.object__artistid,   aa3.object__artistid)

        # Add two presentations to the singers's, muralist's and
        # painter's presentations collection
        press3 = presentations()
        for _ in range(3):
            press3 += presentation.getvalid()

        press3.sort()
        sng3.singers.first.presentations    +=  press3.first

        # Make sure the first painter is a painter and not a muralist
        self.type(painter, sng3.painters.first)

        for pnt3 in sng3.painters:
            try:
                muralist(pnt3.id)
            except db.RecordNotFoundError:
                pnt3.presentations   +=  press3.second
                break
        else:
            self.fail("Couldn't find painter type")


        sng3.muralists.first.presentations  +=  press3.third

        # Remove for the moment because we don't know if
        # sng3.artist_artists.first is a painter or a singer
        # sng3.artist_artists.first.object.presentations \
        #     += press3.third

        # NOTE (3cb2a6b5) In the non-subentity version of this test
        # (it_loads_and_saves_reflexive_associations), the following is
        # True:
        # 
        #     art3.artist_artists.first.object is art3.artists
        #
        # However, that can't be the case here because
        #
        #     type(sng3.artist_artists.first.object) is artist
        #
        # That means that the above appends go to two different
        # presentations collections. The commented out assertions below
        # would fail but are left here to illustrates the consequences of
        # this issue.

        #self.one(sng3.artist_artists.first.object.presentations)

        self.one(sng3.singers.first.presentations)
        self.one(pnt3.presentations)
        self.one(sng3.muralists.first.presentations)

        aas3 = sng3.artist_artists
        self.is_(
            press3.first, 
            sng3.singers.first.presentations.first
        )

        self.is_(
            press3.second, 
            pnt3.presentations.first
        )

        self.is_(
            press3.third, 
            sng3.muralists.first.presentations.first
        )

        with ct() as t:
            t(sng3.save)
            t.created(*press3)

        sng4 = singer(sng3.id)

        press4 = sng4.singers[sng3.singers.first.id].presentations
        self.eq(
            sng3.singers.first.presentations.sorted().pluck('id'),
            press4.sorted().pluck('id')
        )

        press4 = sng4.painters[pnt3.id].presentations
        self.eq(
            pnt3.presentations.sorted().pluck('id'),
            press4.sorted().pluck('id')
        )

        # NOTE The below comment and tests were carried over from
        # it_loads_and_saves_associations:
        # This fixes an issue that came up in development: When you add valid
        # aa to art, then add a fact to art (thus adding an invalid aa to art),
        # strange things were happening with the brokenrules. 
        sng = singer.getvalid()
        sng.artist_artists += artist_artist.getvalid()
        sng.singers += singer.getvalid()
        sng.painters += painter.getvalid()
        sng.muralists += muralist.getvalid()

        self.zero(sng.artist_artists.first.brokenrules)
        self.three(sng.artist_artists.second.brokenrules)
        self.nine(sng.brokenrules)

        # Fix broken aa
        sng.artist_artists.second.role = uuid4().hex
        sng.artist_artists.second.slug = uuid4().hex
        sng.artist_artists.second.timespan = uuid4().hex

        sng.artist_artists.third.role = uuid4().hex
        sng.artist_artists.third.slug = uuid4().hex
        sng.artist_artists.third.timespan = uuid4().hex

        sng.artist_artists.fourth.role = uuid4().hex
        sng.artist_artists.fourth.slug = uuid4().hex
        sng.artist_artists.fourth.timespan = uuid4().hex

        self.zero(sng.artist_artists.second.brokenrules)
        self.zero(sng.artist_artists.third.brokenrules)
        self.zero(sng.brokenrules)

    def it_updates_subentity_reflexive_associations_constituent_entity(self):
        sng = singer.getvalid()

        for i in range(6):
            aa = artist_artist.getvalid()
            if i in (0, 1):
                aa.object = singer.getvalid()
            elif i in (2, 3):
                aa.object = painter.getvalid()
            elif i in (4, 5):
                aa.object = muralist.getvalid()
            sng.artist_artists += aa

        self.six(sng.artist_artists)
        self.two(sng.singers)
        self.two(sng.painters)
        self.two(sng.muralists)
        self.zero(sng.artists)

        sng.save()

        sng1 = singer(sng.id)

        # Update properties of singer, painter and muralists
        for sng2 in sng1.singers:
            sng2.register = uuid4().hex

        for pnt2 in sng1.painters:
            pnt2.style = uuid4().hex

        for mur2 in sng1.muralists:
            mur2.street = True

        with ct() as t:
            t.run(sng1.save)
            t.updated(*sng1.singers)
            t.updated(*sng1.painters)
            t.updated(*sng1.muralists)

        # Update properties of super (artist)
        for sng2 in sng1.singers:
            sng2.firstname = uuid4().hex

        for pnt2 in sng1.painters:
            pnt2.lastname = uuid4().hex

        for mur2 in sng1.muralists:
            mur2.lastname = uuid4().hex # artist.lastname
            mur2.style    = uuid4().hex # painter.style

        with ct() as t:
            t.run(sng1.save)
            t.updated(*sng1.singers.pluck('orm.super'))
            t.updated(*sng1.painters.pluck('orm.super'))
            t.updated(*sng1.muralists.pluck('orm.super'))
            t.updated(*sng1.muralists.pluck('orm.super.orm.super'))

        sng2 = singer(sng1.id)

        self.two(sng2.singers)
        self.four(sng2.painters)
        self.two(sng2.muralists)
        self.six(sng2.artists)

        ''' Test that singer entitiy objects were updateded '''
        sngobjs  = sng. singers.sorted()
        sngobjs1 = sng1.singers.sorted()
        sngobjs2 = sng2.singers.sorted()

        for sngb, sngb2 in zip(sngobjs, sngobjs2):
            self.ne(sngb.firstname, sngb2.firstname)
            self.ne(sngb.register,  sngb2.register)

        for sngb1, sngb2 in zip(sngobjs1, sngobjs2):
            self.eq(sngb1.firstname, sngb2.firstname)
            self.eq(sngb1.register, sngb2.register)

        ''' Test that painter entitiy objects were updateded '''
        def wh(mur):
            return not muralist.orm.exists(mur.id)

        pntobjs  = sng. painters.where(wh).sorted()
        pntobjs1 = sng1.painters.where(wh).sorted()
        pntobjs2 = sng2.painters.where(wh).sorted()

        for pntb, pntb2 in zip(pntobjs, pntobjs2):
            self.ne(pntb.lastname, pntb2.lastname)
            self.ne(pntb.style,  pntb2.style)

        for pntb1, pntb2 in zip(pntobjs1, pntobjs2):
            self.eq(pntb1.lastname, pntb2.lastname)
            self.eq(pntb1.style, pntb2.style)

        ''' Test that muralist entitiy objects were updated '''
        murobjs  = sng. muralists.sorted()
        murobjs1 = sng1.muralists.sorted()
        murobjs2 = sng2.muralists.sorted()

        for murb, murb2 in zip(murobjs, murobjs2):
            self.ne(murb.lastname,   murb2.lastname)
            self.ne(murb.style,      murb2.style)
            self.ne(murb.street,     murb2.street)

        for murb1, murb2 in zip(murobjs1, murobjs2):
            self.eq(murb1.lastname,  murb2.lastname)
            self.eq(murb1.style,     murb2.style)
            self.eq(murb1.street,    murb2.street)

        ''' Add presentation to singer objects '''
        sng2.singers.first.presentations += presentation.getvalid()
        self.one(sng2.singers.first.presentations)

        # Get the `artist_artist` object for `sng2.singers.first` 
        aa1 = [ 
            x 
            for x in sng2.artist_artists
            if x.object.id == sng2.singers.first.id
        ][0]

        aa1.object.presentations += presentation.getvalid()
        self.one(sng2.singers.first.presentations)
        self.one(aa1.object.presentations)

        # NOTE (3cb2a6b5) In the non-subentity version of this test
        # (it_loads_and_saves_reflexive_associations), the following
        # is True:
        #
        #   sng2.singers.first.presentations is \
        #   sng2.artist_artists.first.object.presentations

        # However, that can't be the case here because
        #
        #     type(sng2.artist_artists.first.object) is artist
        #
        # That means that the above appends go to two different
        # presentations collections. 

        self.isnot(
            sng2.singers.first.presentations,
            aa1.object.presentations
        )

        self.isnot(
            sng2.singers.first.presentations.first,
            aa1.object.presentations.first
        )

        ''' Add presentation to painter object '''
        for objpnt2 in sng2.painters:
            if not muralist.orm.exists(objpnt2.id):
                break
        else:
            raise TypeError("Can't find a non-muralist painter")


        objpnt2.presentations += presentation.getvalid()
        self.one(objpnt2.presentations)

        # Get the `artist_artist` object for `objpnt2`. 
        aa2 = [ 
            x 
            for x in sng2.artist_artists
            if x.object.id == objpnt2.id
        ][0]

        aa2.object.presentations += presentation.getvalid()
        self.one(objpnt2.presentations)
        self.one(aa2.object.presentations)

        self.isnot(
            objpnt2.presentations,
            aa2.object.presentations
        )

        self.isnot(
            objpnt2.presentations.first,
            aa2.object.presentations.first
        )

        self.one(sng2.singers.first.presentations)
        self.one(aa1.object.presentations)
        self.one(objpnt2.presentations)
        self.one(aa2.object.presentations)

        ''' Add presentation to muralist object '''
        objmur2 = sng2.muralists.first

        objmur2.presentations += presentation.getvalid()
        self.one(objmur2.presentations)

        # Get the `artist_artist` object for `objmur2`. 
        aa3 = [ 
            x 
            for x in sng2.artist_artists
            if x.object.id == objmur2.id
        ][0]

        aa3.object.presentations += presentation.getvalid()
        self.one(objmur2.presentations)
        self.one(aa3.object.presentations)

        self.isnot(
            objmur2.presentations,
            aa3.object.presentations
        )

        self.isnot(
            objmur2.presentations.first,
            aa3.object.presentations.first
        )

        self.one(sng2.singers.first.presentations)
        self.one(aa1.object.presentations)
        self.one(objpnt2.presentations)
        self.one(objmur2.presentations)
        self.one(aa3.object.presentations)

        with ct() as t:
            t(sng2.save)
            t.created(
                sng2.singers.first.presentations.first,
                aa1.object.presentations.first,
                objpnt2.presentations.first,
                aa2.object.presentations.first,
                objmur2.presentations.first,
                aa3.object.presentations.first,
            )

        sng3 = singer(sng2.id)

        sng3obj = sng3.singers[sng2.singers.first.id]
        sng3obj.presentations.first.name = uuid4().hex

        pnt3obj = sng3.painters[objpnt2.id]
        pnt3obj.presentations.first.name = uuid4().hex

        mur3obj = sng3.muralists[objmur2.id]
        mur3obj.presentations.first.name = uuid4().hex

        with self._chrontest() as t:
            t.run(sng3.save)
            t.updated(
                sng3obj.presentations.first,
                pnt3obj.presentations.first,
                mur3obj.presentations.first
            )

        sng4 = singer(sng3.id)

        sngid = sng3obj.id
        presid =sng3obj.presentations.first.id
        self.eq(
            sng3obj.presentations.first.name,
            sng4.singers[sngid].presentations[presid].name
        )

        pntid = pnt3obj.id
        presid =pnt3obj.presentations.first.id
        self.eq(
            pnt3obj.presentations.first.name,
            sng4.painters[pntid].presentations[presid].name
        )

        murid = mur3obj.id
        presid =mur3obj.presentations.first.id
        self.eq(
            mur3obj.presentations.first.name,
            sng4.painters[murid].presentations[presid].name
        )

        # TODO Test deeply nested associations

    def it_calls_innerjoin_on_subentity_reflexive_associations(self):
        sngs = self._create_join_test_subentity_reflexive_data()

        fff = False, False, False

        # Test artists joined with artist_artists with no condititons
        sngs1 = singers & artist_artists

        self.one(sngs1.orm.joins)

        self.four(sngs1)

        sngs.sort()
        sngs1.sort()
        
        self.chronicles.clear()

        for sng, sng1 in zip(sngs, sngs1):
            self.eq(sng.id, sng1.id)

            self.eq(fff, sng1.orm.persistencestate)

            self.twelve(sng1.artist_artists)

            sng.artist_artists.sort()
            sng1.artist_artists.sort()

            for aa, aa1 in zip(sng.artist_artists, sng1.artist_artists):
                self.eq(aa.id, aa.id)

                self.eq(fff, aa1.orm.persistencestate)

                self.eq(aa.subject.id, aa1.subject.id)

                self.eq(aa.object.id, aa1.object.id)

                # NOTE aa1.subject can't be identical to sng1 because
                # aa1.subject must be of type `artist`. However, their
                # id's should match
                #self.is_(aa1.subject, sng1)
                self.eq(aa1.subject.id, sng1.id)

        # NOTE The above will lazy-load aa1.object 48 times
        self.count(48, self.chronicles)

        # Test singers joined with artist_artists where the association
        # has a conditional
        sngs1 = singers.join(
            artist_artists('role = %s', ('sng-art_art-role-0',))
        )

        self.one(sngs1.orm.joins)

        with ct() as t:
            t(lambda: self.four(sngs1))
            t.retrieved(sngs1)
            for sng1 in sngs1:
                t.retrieved(sng1.orm.super)

        self.chronicles.clear()

        sngs1.sort()
        for sng, sng1 in zip(sngs, sngs1):
            self.eq(sng.id, sng1.id)

            self.eq(fff, sng1.orm.persistencestate)

            self.one(sng1.artist_artists)

            aa1 = sng1.artist_artists.first
            self.eq(aa1.role, 'sng-art_art-role-0')

            self.is_(sng1, aa1.subject)
            self.type(singer, aa1.subject)
            self.eq(aa1.subject__artistid, aa1.subject.id)
            self.eq(aa1.object__artistid, aa1.object.id)

            self.eq(fff, aa1.orm.persistencestate)

            self.eq(fff, aa1.subject.orm.persistencestate)
            self.eq(fff, aa1.object.orm.persistencestate)

        # Test unconditionally joining the associated entities
        # collections (artist_artists) with its composites (singer and
        # painter)
        for b in False, True:
            for es in (singers, painters, muralists):
                if b:
                    # Implicitly join artist_artists
                    sngs1 = singers & es
                else:
                    # Explicitly join artist_artists
                    sngs1 = singers
                    sngs1 &= artist_artists & es

                self.one(sngs1.orm.joins)

                self.type(
                    artist_artists, 
                    sngs1.orm.joins.first.entities
                )
                self.one(sngs1.orm.joins.first.entities.orm.joins)

                obj = sngs1.orm.joins.first.entities \
                      .orm.joins.first.entities

                self.type(es, obj)

                sngs1.sort()

                self.chronicles.clear()

                self.four(sngs1)

                for sng, sng1 in zip(sngs, sngs1):
                    self.eq(sng.id, sng1.id)

                    self.eq(fff, sng1.orm.persistencestate)

                    if es is singers:
                        self.four(sng1.artist_artists)
                    elif es is painters:
                        self.eight(sng1.artist_artists)

                    aas1 = sng1.artist_artists

                    # Create an aa collection where the non-singers
                    # (painters) from sng.artist_artists have been
                    # removed
                    aas = sng.artist_artists.where(
                                lambda x: x.id in aas1.pluck('id')
                          )

                    aas.sort(); aas1.sort()
                    if es in (singers, muralists):
                        self.four(aas)
                        self.four(aas1)
                    elif es is painters:
                        self.eight(aas)
                        self.eight(aas1)

                    for aa, aa1 in zip(aas, aas1):
                        self.expect(
                            None, 
                            lambda: es.orm.entity(aa.object.id)
                        )
                        self.eq(fff, aa1.orm.persistencestate)
                        self.eq(aa.id, aa.id)
                        self.eq(
                            aa.subject__artistid, 
                            aa1.subject__artistid
                        )
                        self.eq(
                            aa.object__artistid, 
                            aa1.object__artistid
                        )
                        self.eq(aa.subject.id, aa1.subject.id)
                        self.eq(aa.object.id, aa1.object.id)

                # The test to determine what subentity aa.object is:
                #
                #     self.expect(None, lambda: es.orm.entity(aa.object.id))
                #
                # will result in 16 chronicled objects for singer and 32
                # chronicled objects for painters.
                if es in (singers, muralists):
                    self.count(16, self.chronicles)
                elif es is painters:
                    self.count(32, self.chronicles)

        # Test joining the associated entities collections
        # (artist_artists) with its composite (singer/painter) where the
        # composite's join is conditional.
        for b in True, False:
            for es in (singers, painters, muralists):
                if es is singers:
                    wh = 'firstname = %s and register = %s'
                    args = (
                        'sng-art_art-sng-fn-1',
                        'sng-art_art-sng-reg-1',
                    )
                elif es is painters:
                    wh = 'firstname = %s and style = %s'
                    args = (
                        'sng-art_art-pnt-fn-4',
                        'sng-art_art-pnt-sty-4',
                    )
                elif es is muralists:
                    wh = 'firstname = %s and style = %s and street = %s'
                    args = (
                        'sng-art_art-mur-fn-8',
                        'sng-art_art-mur-sty-8',
                        True,
                    )

                if b:
                    # Explicitly join artist_artists
                    sngs1 = singers() 
                    sngs1 &= artist_artists.join(
                                es(wh, args)
                            )
                else:
                    # Implicitly join artist_artists
                    sngs1 = singers().join(
                                    es(wh, args)
                            )

                self.one(sngs1.orm.joins)
                self.type(
                    artist_artists, 
                    sngs1.orm.joins.first.entities
                )
                self.one(sngs1.orm.joins.first.entities.orm.joins)

                self.type(
                    es, 
                    sngs1.orm.joins.first.entities.orm.joins.first.entities
                )

                sngs1.sort()

                self.four(sngs1)

                self.chronicles.clear()
                for sng, sng1 in zip(sngs, sngs1):
                    self.eq(fff, sng1.orm.persistencestate)
                    self.eq(sng.id, sng1.id)

                    aas = sng1.artist_artists
                    self.one(aas)
                    self.eq(
                        args[0],
                        aas.first.object.firstname
                    )

                    # Downcast 46e3dc32
                    obj = es.orm.entity(aas.first.object.id)

                    if es is singers:
                        attr, v = 'register', args[1]
                    elif es is painters:
                        attr, v = 'style', args[1]
                    elif es is muralists:
                        attr, v = 'street', args[2]

                    # This will cause painter to be loaded if attr ==
                    # style
                    self.eq(v, getattr(obj, attr))
                    self.eq(fff, aas.first.orm.persistencestate)

                # The downcast above 46e3dc32 will result in four loads of
                # singer/painter
                self.four(self.chronicles)

        ''' Test joining the associated entities collections
        (artist_artists) with its composite (singers) where the
        composite's join is conditional along with the other two.'''
        sngs1 =  singers('firstname = %s and register = %s', 
                        ('fn-1', 'reg-1')).join(
                    artist_artists('role = %s',
                        ('sng-art_art-role-0',)
                    ).join(
                         singers('firstname = %s and register = %s', (
                                'sng-art_art-sng-fn-0',
                                'sng-art_art-sng-reg-0',
                            )
                         )
                    )
                 )

        self.one(sngs1)

        self.chronicles.clear()
        self.eq('fn-1', sngs1.first.firstname)
        self.eq('reg-1', sngs1.first.register)

        aas1 = sngs1.first.artist_artists
        self.one(aas1)
        self.eq(fff, aas1.first.orm.persistencestate)
        self.eq('sng-art_art-role-0', aas1.first.role)
        self.eq('sng-art_art-sng-fn-0', aas1.first.object.firstname)
        self.eq(
            'sng-art_art-sng-reg-0', 
            singer(aas1.first.object.id).register # downcast c8200aa7
        )
        self.eq(sngs1.first.id, aas1.first.subject.id)
        self.eq(sngs1.first.id, aas1.first.subject__artistid)
        self.ne(
            aas1.first.subject__artistid,
            aas1.first.object__artistid
        )
        self.eq(
            aas1.first.object.id,
            aas1.first.object__artistid
        )

        # We will have one chronicles from the downcast c8200aa7
        self.one(self.chronicles)

        ''' Test joining the associated entities collections
        (artist_artists) with its subentity composite (painters) where
        the composite's join is conditional along with the other two.
        '''
        sngs1 =  singers('firstname = %s and register = %s', 
                        ('fn-1', 'reg-1')).join(
                    artist_artists('role = %s',
                        ('sng-art_art-role-4',)
                    ).join(
                         painters('firstname = %s and style = %s', (
                                'sng-art_art-pnt-fn-4',
                                'sng-art_art-pnt-sty-4',
                            )
                         )
                    )
                 )

        self.one(sngs1)

        self.chronicles.clear()
        self.eq('fn-1', sngs1.first.firstname)
        self.eq('reg-1', sngs1.first.register)

        aas1 = sngs1.first.artist_artists
        self.one(aas1)
        self.eq(fff, aas1.first.orm.persistencestate)
        self.eq('sng-art_art-role-4', aas1.first.role)
        self.eq('sng-art_art-pnt-fn-4', aas1.first.object.firstname)
        self.eq(
            'sng-art_art-pnt-sty-4', 
            painter(aas1.first.object.id).style # downcast c8200aa7
        )
        self.eq(sngs1.first.id, aas1.first.subject.id)
        self.eq(sngs1.first.id, aas1.first.subject__artistid)
        self.ne(
            aas1.first.subject__artistid,
            aas1.first.object__artistid
        )
        self.eq(
            aas1.first.object.id,
            aas1.first.object__artistid
        )

        ''' Test joining the associated entities collections
        (artist_artists) with its subsubentity composite (muralists)
        where the composite's join is conditional along with the other
        two. '''
        sngs1 =  singers('firstname = %s and register = %s', 
                        ('fn-1', 'reg-1')).join(
                    artist_artists('role = %s',
                        ('sng-art_art-role-8',)
                    ).join(
                         muralists(
                             'firstname = %s and '
                             'style = %s and '
                             'street = %s', (
                                'sng-art_art-mur-fn-8',
                                'sng-art_art-mur-sty-8',
                                True
                            )
                         )
                    )
                 )

        self.one(sngs1)

        self.chronicles.clear()
        self.eq('fn-1', sngs1.first.firstname)
        self.eq('reg-1', sngs1.first.register)

        aas1 = sngs1.first.artist_artists
        self.one(aas1)
        self.eq(fff, aas1.first.orm.persistencestate)
        self.eq('sng-art_art-role-8', aas1.first.role)
        self.eq('sng-art_art-mur-fn-8', aas1.first.object.firstname)
        self.eq(
            'sng-art_art-mur-sty-8', 
            painter(aas1.first.object.id).style # downcast c8200aa7
        )
        self.eq(sngs1.first.id, aas1.first.subject.id)
        self.eq(sngs1.first.id, aas1.first.subject__artistid)
        self.ne(
            aas1.first.subject__artistid,
            aas1.first.object__artistid
        )
        self.eq(
            aas1.first.object.id,
            aas1.first.object__artistid
        )

        # We will have one chronicles from the downcast c8200aa7
        self.one(self.chronicles)

        ''' Test joining a constituent (concerts) of the composite
        (singers) of the association (artist_artists) without
        conditions.
        '''
        for es in (singers, painters, muralists):
            if es is singers:
                const = concerts
            elif es is painters:
                const = exhibitions
            elif es is muralists:
                const = unveilings

            for b in True, False:
                if b:
                    # Explicitly join the associations (artist_artists())
                    sngs1 = singers.join(
                                artist_artists.join(
                                    es & const
                                )
                            )
                else:
                    # Implicitly join the associations (artist_artists())
                    sngs1 =  singers.join(
                                es & const
                             )

                sngs1.sort()

                self.chronicles.clear()

                for sng, sng1 in zip(sngs, sngs1):
                    self.eq(fff, sng1.orm.persistencestate)
                    self.eq(sng.id, sng1.id)

                    aas1 = sng1.artist_artists.sorted()
                    aas = sng \
                            .artist_artists \
                            .where(
                                lambda x: x.id in aas1.pluck('id')
                            ) \
                            .sorted()

                    self.zero(self.chronicles)

                    if es is painters:
                        # If es is painters, then we will have 4
                        # painters and 4 muralists as the `object`
                        # property of each aa object in aas1. Use the
                        # orm.leaf property to determine the type. 
                        #
                        # If es in (muralists, singers), we will only
                        # have 4 in the aas1 collection.
                        for e in (painter, muralist):
                            self.eq(
                                [e] * 4,
                                [
                                    type(x) 
                                    for x in aas1.pluck('object.orm.leaf')
                                    if type(x) is e
                                ]
                            )
                        self.eight(aas); self.eight(aas1)
                    elif es is muralists:
                        self.eq(
                            [muralist] * 4,
                            [
                                type(x) 
                                for x in aas1.pluck('object.orm.leaf')
                            ]
                        )
                        self.four(aas); self.four(aas1)
                    elif es is singers:
                        self.eq(
                            [singer] * 4,
                            [
                                type(x) 
                                for x in aas1.pluck('object.orm.leaf')
                            ]
                        )
                        self.four(aas); self.four(aas1)
                    else:
                        raise ValueError()

                    # Plucking leafs will result in db hits, so clear
                    # self.chronicles again.
                    self.chronicles.clear()

                    for aa, aa1 in zip(aas, aas1):
                        self.eq(fff, aa1.orm.persistencestate)
                        self.eq(aa.id, aa1.id)
                        sngobj = aa.object
                        sngobj1 = aa1.object
                        self.eq(fff, sngobj1.orm.persistencestate)

                        self.eq(sngobj.id, sngobj1.id)

                        attr = const.__name__
                        consts = getattr(sngobj, attr).sorted()
                        consts1 = getattr(sngobj1, attr).sorted()

                        self.four(consts); self.four(consts1)

                        for conc, conc1 in zip(consts, consts1):
                            self.eq(fff, conc1.orm.persistencestate)
                            self.eq(conc.id, conc1.id)

                self.zero(self.chronicles)

        ''' Test joining a constituent (concerts) of the composite
        (singers) of the association (artist_artists) with conditions.
        '''
        aarole = 'sng-art_art-role-1'
        fn = 'sng-art_art-sng-fn-1'
        regname = 'sng-art_art-sng-reg-0'
        consname = 'sng-art_art-sng-conc-name-1'
        sngs1 =  singers().join(
                    artist_artists(role = aarole).join(
                        singers(firstname = fn).join(
                            concerts(name =consname)
                        )
                    )
                 )

        sngs1.sort()

        self.four(sngs)
        self.four(sngs1)
        self.chronicles.clear()

        for sng, sng1 in zip(sngs, sngs1):
            self.eq(fff, sng1.orm.persistencestate)

            self.eq(sng.id, sng1.id)
            aas1 = sng1.artist_artists
            self.one(aas1)

            self.eq(aarole, aas1.first.role)
            self.eq(fff, aas1.first.orm.persistencestate)

            self.eq(fn, aas1.first.object.firstname)
            self.eq(fff, aas1.first.object.orm.persistencestate)

            # FIXME:9cad10a9 The below tests can't work
            #self.one(aas1.first.object.concerts)

            # self.eq(
            #     consname, 
            #     aas1.first.object.concerts.first.name
            # )

        self.zero(self.chronicles)

        ''' Test joining a constituent (exhibitions) of the composite
        (painters) of the association (artist_artists) with conditions.
        '''
        aarole = 'sng-art_art-role-4'
        fn = 'sng-art_art-pnt-fn-4'
        exhname = 'sng-art_art-pnt-exh-name-0'
        sngs1 =  singers().join(
                    artist_artists(role = aarole).join(
                        painters(firstname = fn).join(
                            exhibitions(name = exhname)
                        )
                    )
                 )

        sngs1.sort()

        self.four(sngs); self.four(sngs1)
        self.chronicles.clear()

        for sng, sng1 in zip(sngs, sngs1):
            self.eq(fff, sng1.orm.persistencestate)

            self.eq(sng.id, sng1.id)
            aas1 = sng1.artist_artists
            self.one(aas1)

            self.eq(aarole, aas1.first.role)
            self.eq(fff, aas1.first.orm.persistencestate)

            self.eq(fn, aas1.first.object.firstname)
            self.eq(fff, aas1.first.object.orm.persistencestate)

            # FIXME:9cad10a9 This test can't work because
            # `aas1.first.object` is an <artist> and <artist>s don't
            # have exhibitions; <painter>s do. We could downcast to
            # <painter> but that doesn't allow for the INNER JOIN of
            # exhibitions to be tested. Perhaps the solution is to
            # downcast `aas1.first.object` in orm.link() and link the
            # <exhibition> objects there.
            #self.one(aas1.first.object.exhibitions)

            #self.eq(
            #    consname, 
            #    aas1.first.object.exhibitions.first.name
            #)


        # The downcast to painter wil load for objects
        self.zero(self.chronicles)

        ''' Test joining a constituent (unveilings) of the composite
        (muralists) of the association (artist_artists) with conditions.
        '''
        aarole = 'sng-art_art-role-8'
        fn = 'sng-art_art-mur-fn-8'
        unvname = 'sng-art_art-mur-unv-name-0'
        sngs1 =  singers().join(
                    artist_artists(role = aarole).join(
                        muralists(firstname = fn).join(
                            unveilings(name = unvname)
                        )
                    )
                 )

        sngs1.sort()

        self.four(sngs); self.four(sngs1)
        self.chronicles.clear()

        for sng, sng1 in zip(sngs, sngs1):
            self.eq(fff, sng1.orm.persistencestate)

            self.eq(sng.id, sng1.id)
            aas1 = sng1.artist_artists
            self.one(aas1)

            self.eq(aarole, aas1.first.role)
            self.eq(fff, aas1.first.orm.persistencestate)

            self.eq(fn, aas1.first.object.firstname)
            self.eq(fff, aas1.first.object.orm.persistencestate)

            # FIXME:9cad10a9 This test can't work because
            # `aas1.first.object` is an <artist> and <artist>s don't
            # have exhibitions; <painter>s do. We could downcast to
            # <painter> but that doesn't allow for the INNER JOIN of
            # exhibitions to be tested. Perhaps the solution is to
            # downcast `aas1.first.object` in orm.link() and link the
            # <exhibition> objects there.
            #self.one(aas1.first.object.exhibitions)

            #self.eq(
            #    consname, 
            #    aas1.first.object.exhibitions.first.name
            #)


        # The downcast to painter wil load for objects
        self.zero(self.chronicles)

########################################################################
# Test dom                                                             #
########################################################################

class foonet(pom.site):
    def __init__(self):
        super().__init__()

        # TODO This init logic probably should mostly put in overridden
        # properties:
        #
        #   foonet.pages
        #   foonet.lang
        #   foonet.charset
        #   foonet.stylesheets
        #   foonet.header
        #   foonet.footer

        ''' Pages '''
        self.pages += home()
        self.pages += about()
        self.pages += contact_us()
        self.pages += blogs()
        self.pages += admin()

        ''' Metadata '''
        self.lang = 'es'
        self.charset = 'iso-8859-1'
        self.stylesheets.append(
            'https://maxcdn.bootstrapcdn.com/'
                'bootstrap/4.0.0/css/bootstrap.min.css'
        )

        ''' Header '''
        self.header.logo = pom.logo('FooNet')

        ''' Header Menus '''
        mnus = self.header.menus
        mnu = self._adminmenu
        mnus += mnu

        ''' Sidebar and sidebar menu '''
        mnus = pom.menus()
        mnu = pom.menu('left-sidebar-nav')
        mnus += mnu

        mnu.items += pom.menu.item('Main page', '/')

        sb = pom.sidebar('left')
        self.sidebars += sb
        sb += mnus

        ''' Footer  '''

    @property
    def _adminmenu(self):
        mnu = pom.menu('admin')
        mnu.items += pom.menu.item('Users')

        mnu.items.last.items \
            += pom.menu.item(self['/en/admin/users/statistics'])

        mnu.items += pom.menu.item('Reports')

        rpt = mnu.items.last

        pg = self['/en/admin/reports/netsales']

        rpt.items += pom.menu.item(pg)

        rpt.seperate()

        pg = self['/en/admin/reports/accountsummary']
        rpt.items += pom.menu.item(pg)

        return mnu

class admin(pom.page):
    def __init__(self):
        super().__init__()
        self.pages += users()
        self.pages += reports()

class users(pom.page):
    def __init__(self):
        super().__init__()
        self.pages += statistics()

class statistics(pom.page):
    def __init__(self):
        super().__init__()

class reports(pom.page):
    def __init__(self):
        super().__init__()
        self.pages += netsales()
        self.pages += accountsummary()

class netsales(pom.page):
    def __init__(self):
        super().__init__()

class accountsummary(pom.page):
    pass

class home(pom.page):
    def __init__(self):
        super().__init__()

    @property
    def name(self):
        return 'index'

class blogs(pom.page):
    def __init__(self):
        super().__init__()
        self.pages += blog_categories('categories')
        self.pages += blog_posts('posts')
        self.pages += blog_comments('comments')

class blog_categories(pom.page):
    pass

class blog_posts(pom.page):
    pass

class blog_comments(pom.page):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pages += blog_approved_comments('approved')
        self.pages += blog_rejected_comments('rejected')

class blog_approved_comments(pom.page):
    pass

class blog_rejected_comments(pom.page):
    pass

class about(pom.page):
    def __init__(self):
        super().__init__()
        self.pages += about_team()

class about_team(pom.page):
    @property
    def name(self):
        return 'team'

class contact_us(pom.page):
    pass
    
class pom_site(tester):
    def it_calls__init__(self):
        ws = foonet()
        self.five(ws.pages)

    def it_calls__repr__(self):
        self.eq('site()', repr(pom.site()))
        self.eq('site()', str(pom.site()))

        self.eq('foonet()', repr(foonet()))
        self.eq('foonet()', str(foonet()))
        
    def it_calls__getitem__(self):
        ws = foonet()
        for path in ('/', '', '/en/index'):
            self.type(home, ws[path])

        self.type(about, ws['/en/about'])
        self.type(about_team, ws['/en/about/team'])

    def it_raise_on_invalid_path(self):
        ws = foonet()
        self.expect(IndexError, lambda: ws['/en/index/about/teamxxx'])
        self.expect(IndexError, lambda: ws['/en/xxx'])
        self.expect(IndexError, lambda: ws['/en/derp'])

        self.expect(IndexError, lambda: ws[dom.p()])

    def it_calls_html(self):
        ws = pom.site()
        self.type(dom.html, ws.html)
        self.eq('en', ws.html.lang)

        ws = foonet()
        self.type(dom.html, ws.html)
        self.eq('es', ws.html.lang)

    def it_calls_head(self):
        ''' Foonet's head '''
        vp = 'width=device-width, initial-scale=1, shrink-to-fit=no'

        ws = foonet()
        hd = ws.head
        self.one(hd.children['meta[charset=iso-8859-1]'])
        self.one(hd.children['meta[name=viewport][content="%s"]' % vp])

        titles = hd.children['title']
        self.one(titles)
        self.eq('foonet', titles.first.text)

        # Mutate ws properties to ensure they show up in .head 
        charset = uuid4().hex
        vp = uuid4().hex
        title = uuid4().hex

        ws.charset = charset
        ws.viewport = vp
        ws.title = title

        hd = ws.head
        self.one(hd.children['meta[charset="%s"]' % charset])
        self.one(hd.children['meta[name=viewport][content="%s"]' % vp])

        titles = hd.children['title']
        self.one(titles)
        self.eq(title, titles.first.text)

        ws = pom.site()
        hd = ws.head
        self.one(hd.children['meta[charset=utf-8]'])

        titles = hd.children['title']
        self.one(titles)
        self.eq('site', titles.first.text)

    def it_calls_header(self):
        ws = foonet()
        hdr = ws.header
        self.type(pom.header, hdr)

    def it_calls_admin_menu(self):
        ws = foonet()

        mnus = ws.header.menus
        mnu = mnus['admin']
        self.two(mnu.items)

        rpt = mnu.items.second
        self.type(pom.menu.item, rpt.items.first)
        self.type(pom.menu.separator, rpt.items.second)
        self.type(pom.menu.item, rpt.items.third)

    def it_menu_has_aria_attributes(self):
        ws = foonet()

        navs = ws.header['nav']
        self.two(navs)

        self.one(navs['[aria-label=Admin]'])
        self.one(navs['[aria-label=Main]'])

    def it_calls_main_menu(self):
        ws = pom.site()
        mnu = ws.header.menu
        self.zero(mnu.items)

        ws = foonet()
        mnu = ws.header.menu
        self.five(mnu.items)

        self.eq(
            ['/index', '/about', '/contact-us', '/blogs', '/admin'],
            mnu.items.pluck('page.path')
        )

        self.eq(
            [home, about, contact_us, blogs, admin],
            [type(x) for x in  mnu.items.pluck('page')]
        )

        blg = mnu.items.penultimate
        self.eq(
            ['/blogs/categories', '/blogs/posts', '/blogs/comments'],
            blg.items.pluck('page.path')
        )

        self.eq(
            [blog_categories, blog_posts, blog_comments],
            [
                type(x) 
                for x in blg.items.pluck('page')
            ]
        )

        self.eq(
            ['/blogs/comments/approved', '/blogs/comments/rejected'],
            blg.items.last.items.pluck('page.path')
        )

        self.eq(
            [blog_approved_comments, blog_rejected_comments],
            [type(x) for x in blg.items.last.items.pluck('page')]
        )

        for _ in range(2): # Ensure indempotence
            # The header's html will contain two <nav>s: one for the
            # main and one for the admin
            self.two(dom.html(ws.header.html)['nav'])
            self.two(ws.header['nav'])

            # ... and one <ul>'s under the <nav>
            self.two(dom.html(ws.header.html)['nav>ul'])
            self.two(ws.header['nav>ul'])

        # Removing a menu removes a <nav> from the header's html.
        ws.header.menus.pop()
        self.one(dom.html(ws.header.html)['nav'])
        self.one(ws.header['nav'])

    def it_mutates_main_menu(self):
        ws = foonet()
        mnu = ws.header.menu
        self.five(mnu.items)

        # blogs item
        itm = mnu.items.fourth

        ''' It updates a menu item '''
        sels = dom.selectors('li > a[href="%s"]' % '/blogs/categories')
        self.one(ws.header[sels])
        self.one(mnu[sels])

        # Get /blogs/categories
        blgcat = itm.items.first

        class tags(pom.page):
            pass

        blgcat.page = tags()

        sels = dom.selectors('li > a[href="%s"]' % blgcat.page.path)
        self.one(ws.header[sels])
        self.one(mnu[sels])

        sels = dom.selectors('li > a[href="%s"]' % '/blogs/categories')
        self.zero(ws.header[sels])
        self.zero(mnu[sels])

        ''' It adds a menu item '''
        mnu.items += pom.menu.item('My Profile')
        self.six(mnu.items)

        sels = dom.selectors('li')
        self.true('My Profile' in (x.text for x in mnu[sels]))
        self.true('My Profile' in (x.text for x in ws.header[sels]))

        ''' Delete the blogs munu '''
        sels = dom.selectors('li > a[href="%s"]' % itm.page.path)
        self.one(ws.header[sels])
        self.one(mnu[sels])

        # Remove the blog menu
        itms = mnu.items.remove(mnu.items.fourth)
        self.one(itms)
        self.type(pom.menu.item, itms.first)
        self.eq('blogs', itms.first.text)

        sels = dom.selectors('li > a[href="%s"]' % itm.page.path)
        self.zero(ws.header[sels])
        self.zero(mnu[sels])

class pom_page(tester):
    def it_calls__init__(self):
        name = uuid4().hex
        pg = pom.page()
        self.zero(pg.pages)

    def it_implements_main(self):
        class stats(pom.page):
            def main(self):
                m = self.main
                m += dom.h2('Statistics')
                m += dom.p('''
                    These are the company's sales statistics:
                ''')
                self._main_snapshot = dom.html(m.html)
                self._html_snapshot = dom.html(self.html)

        pg = stats()

        self.eq('Stats', pg.title)
        self.eq('Stats', pg['html>head>title'].text)

        # Upon instantiation, the page's `main` attribute will be
        # replace with a dom.main object. A reference to the  `main`
        # method with be held in a private variable.
        self.type(dom.main, pg.main)

        # Invoking `elements` forces main to be called
        pg.elements

        # Snapshop of main tag should only include a few elements
        self.five(pg._main_snapshot.all)

        # The snapshop of the page's html will be a full document (i.e.,
        # it starts with <html>). However, since the page object hasn't
        # been attached to a site object (it will be below), the site
        # specific HTML (the <head> tag and the page <header> can not be
        # included.
        self.one(pg._html_snapshot['head'])
        self.one(pg._html_snapshot['header'])
        self.one(pg._html_snapshot['html'])
        self.one(pg._html_snapshot['html>body'])
        self.one(pg._html_snapshot['html>body>main'])
        self.one(pg._html_snapshot['html>body>main>h2'])
        self.one(pg._html_snapshot['html>body>main>p'])
        
        ''' Test page after being associated to a site object '''
        pg = stats()
        ws = foonet()
        ws.pages += pg

        # Invoking `elements` forces main to be called
        pg.elements

        # Now the _html_snapshot will have a <head> and a <header>
        # derived from the site object it was associated with.
        self.five(pg._main_snapshot.all)
        self.one(pg._html_snapshot['head'])
        self.one(pg._html_snapshot['header'])
        self.one(pg._html_snapshot['html'])
        self.one(pg._html_snapshot['html>body'])
        self.one(pg._html_snapshot['html>body>main'])
        self.one(pg._html_snapshot['html>body>main>h2'])
        self.one(pg._html_snapshot['html>body>main>p'])

        # pg will have a header and a head that is cloned from ws's
        # header and head. Ensure that they are not identical.
        self.isnot(ws.header, pg.header)
        self.isnot(ws.head, pg.head)
        self.isnot(ws.header.menus, pg.header.menus)
        self.isnot(ws.header.menu, pg.header.menu)

    def it_changes_lang_from_main(self):
        lang = uuid4().hex
        class stats(pom.page):
            def main(self):
                m = self.main
                m += dom.h2('Statistics')
                m += dom.p('''
                    These are the company's sales statistics:
                ''')

                self.lang = lang

        pg = stats()

        # Invoking elements invokes stats.main()
        pg.elements

        self.eq(lang, pg.lang)
        self.eq(lang, pg.attributes['lang'].value)

        ''' Test page after being associated to a site object '''
        pg = stats()
        ws = foonet()
        ws.pages += pg

        # Invoking `elements` forces main to be called
        pg.elements

        self.eq(lang, pg.lang)
        self.eq(lang, pg.attributes['lang'].value)

    def it_changes_main_menu_from_main(self):
        class stats(pom.page):
            def main(self):
                m = self.main
                m += dom.h2('Statistics')
                m += dom.p('''
                    These are the company's sales statistics:
                ''')

                self.header.menu.items += pom.menu.item(
                    'Statistics',
                    href='http://www.statistics.com'
                )

        pg = stats()
        ws = foonet()
        ws.pages += pg

        # Invoking elements invokes stats.main()
        pg.elements

        self.eq('Statistics', pg.header.menu.items.last.text)
        self.ne('Statistics', ws.header.menu.items.last.text)

        self.eq(
            'http://www.statistics.com',
            pg.header.menu.items.last.href
        )

        sels = dom.selectors(
            'nav[aria-label=Main]>ul>li>a[href="http://www.statistics.com"]'
        )

        self.one(pg[sels])

        self.eq(
            'http://www.statistics.com',
            pg.header.menu.items.last.href
        )

    def it_changes_title_from_main(self):
        id = uuid4().hex
        class stats(pom.page):
            def main(self):
                m = self.main
                nonlocal id
                m += dom.h2('Statistics')
                m += dom.p('''
                    These are the company's sales statistics:
                ''')

                self.title = id

        pg = stats()

        # Invoking elements invokes stats.main()
        pg.elements

        self.eq(id, pg.title)
        self.eq(id, pg['head>title'].text)

        ''' Test page after being associated to a site object '''
        pg = stats()
        ws = foonet()
        ws_title = ws.title
        ws.pages += pg

        # Invoking `elements` forces main to be called
        pg.elements

        self.eq(id, pg.title)
        self.eq(id, pg['html>head>title'].text)
        self.eq(ws_title, ws.title)

    def it_clones_site_objects(self):
        ws = foonet()
        pg = ws['/en/blogs']
        self.notnone(pg.site)

        self.isnot(pg.header,        ws.header)
        self.isnot(pg.header.menu,   ws.header.menu)
        self.isnot(pg.header.menus,  ws.header.menus)
        self.isnot(pg.head,          ws.head)

    def it_calls_site(self):
        ws = foonet()
        self.is_(ws, ws['/en/blogs'].site)
        self.is_(ws, ws['/en/blogs/comments'].site)
        self.is_(ws, ws['/en/blogs/comments/rejected'].site)

    def it_changes_sidebars_from_main(self):

        class stats(pom.page):
            def main(self):
                m = self.main
                m += dom.h2('Statistics')
                m += dom.p('''
                    These are the company's sales statistics:
                ''')

                sb = self.sidebars['left']
                mnu = sb['nav'].first
                mnu.items += pom.menu.item('About stats')

        ws = foonet()

        pg = stats()
        ws.pages += pg

        # Invoke stats.main
        pg.elements

        wsmnu = ws.sidebars['left']['nav'].first
        pgmnu = pg.sidebars['left']['nav'].first


        # Make sure the site's menu was not changed
        self.eq(wsmnu.items.count + 1, pgmnu.items.count)

        self.eq('Main page', pgmnu.items.first.text)
        self.eq('About stats', pgmnu.items.second.text)
        
class dom_elements(tester):
    def it_gets_text(self):
        # FIXME:fa4e6674 This is a non-trivial problem
        return
        html = dom.html('''
        <div>
            <p>
                This is a paragraph with 
                <em>
                    emphasized text
                </em>.
            </p>
            <p>
                This is a paragraph with 
                <strong>
                    strong text
                </strong>.
            </p>
        </div>
        ''')

        expect = self.dedent('''
        This is a paragraph with emphasized text.
        This is a paragraph with strong text.
        ''')

        self.eq(expect, html.text)

        html = dom.html('''
        <p>This is a paragraph with <em>emphasized text</em>.</p>
        <p>This is a paragraph with <strong>strong text</strong>.</p>
        ''')

        self.eq(expect, html.text)

        html = dom.html(Shakespeare)
        expect = self.dedent('''
        No, thy words are too precious to be cast away upon
        curs; throw some of them at me; come, lame me with reasons.
        ''')

        actual = html['#speech3+div'].text

        self.eq(expect, actual)

        html = dom.html('<p>%s</p>' % actual)
        self.eq(expect, html.text)

    def it_calls_html(self):
        html = dom.html(TestHtml)
        self.eq(TestHtmlMin, html.html)

        htmlmin = dom.html(TestHtmlMin)
        self.eq(html.html, htmlmin.html)

    def it_calls_pretty(self):
        htmlmin = dom.html(TestHtmlMin)
        self.eq(TestHtml, htmlmin.pretty)

        html = dom.html(TestHtml)
        self.eq(TestHtmlMin, html.html)

    def it_removes_elements(self):
        html = dom.html(TestHtml)

        bs = html['strong']
        self.two(bs)

        bs = bs.remove()
        self.two(bs)

        self.eq([None, None], bs.pluck('parent'))

        bs = html['strong']
        self.zero(bs)

class dom_element(tester):
    def it_gets_text(self):
        # FIXME:fa4e6674 This is a non-trivial problem
        return

        html = dom.html('''
        <div>
          <p>
            This is a paragraph with <em>emphasized</em> text.
          </p>
        </div>
        ''')
        p = html['p'].first

        expect = 'This is a paragraph with emphasized text.'
        self.eq(expect, p.text)
        print(p.pretty)

    def it_sets_text(self):
        html = dom.html('''
        <div>
            <p>
                This is a paragraph with 
                <em>
                    emphasized text
                </em>.
            </p>
            <p>
                This is a paragraph with 
                <strong>
                    strong text
                </strong>.
            </p>
        </div>
        ''')

        self.two(html['div'].first.children)

        html['div'].text = 'Some text'

        self.zero(html['div'].first.children)

        self.eq('Some text', html['div'].first.elements.first.value)

        expect = self.dedent('''
        <div>
          Some text
        </div>''')

        self.eq(expect, html.pretty)

    def it_class_language(self):
        html = dom.html('''
        <html lang="en">
            <head></head>
            <body>
                <div>
                    <p>
                        My language is 'en' because it was specified in
                        the root html tag.
                    </p>
                </div>
                <section lang="fr">
                    <p>Comment dites-vous "Bonjour" en Espanol?</p>

                    <div>
                        <blockquote lang="es">
                            <p>
                                My language will be Spainish.
                            </p>
                        </blockquote>
                    </div>
                </section>
            </body>
        </html>
        ''')

        p = html[0].children[1].children[0].children[0]
        self.type(dom.p, p)
        self.eq('en', p.language)

        self.type(dom.div, p.parent)
        self.eq('en', p.parent.language)

        p = html[0].children[1].children[1].children[0]
        self.type(dom.p, p)
        self.eq('fr', p.language)

        self.type(dom.section, p.parent)
        self.eq('fr', p.parent.language)

        p = html[0] \
                .children[1] \
                .children[1] \
                .children[1] \
                .children[0] \
                .children[0] 
        self.type(dom.p, p)
        self.eq('es', p.language)

        self.type(dom.blockquote, p.parent)
        self.eq('es', p.parent.language)

        html = dom.html('''
        <html>
            <head></head>
            <body>
                <div>
                    <p>
                        This document contains no 'lang' attribute so
                        all of the elements' `language` @property's
                        should be None.
                    </p>
                </div>
            </body>
        </html>
        ''')

        self.all(x.lang is None for x in html.all)

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
        self.zero(b.siblings)

        i = dom.emphasis('some emphasized text')
        p += i
        self.two(txt.siblings)
        self.is_(b, txt.siblings.first)
        self.is_(i, txt.siblings.second)

        self.one(b.siblings)
        self.is_(i, b.siblings.first)

        self.one(i.siblings)
        self.is_(b, i.siblings.first)

    def it_raises_when_moving_elements(self):
        p = dom.paragraph()
        txt = dom.text('some text')
        p += txt

        p1 = dom.paragraph()
        self.expect(dom.MoveError, lambda: p1.__iadd__(txt))

    def it_calls_isvoid(self):
        self.false(dom.paragraph.isvoid)
        self.false(dom.paragraph().isvoid)

        self.true(dom.base.isvoid)
        self.true(dom.base().isvoid)

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

class dom_paragraph(tester):
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

        self.eq(expect, p.pretty)

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
        self.eq(expect, p.pretty)

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

        self.eq(expect, p.pretty)

class dom_text(tester):
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

class dom_attribute(tester):
    def it_raises_on_invalid_attributes(self):
        # Test for valid characters in attribute names. Based on
        # https://html.spec.whatwg.org/multipage/syntax.html#attributes-2
        p = dom.paragraph()

        def ass(name):
            p.attributes[name] = name

        # These punctuation marks are not allowed.
        invalids = ' "\'/='
        for invalid in invalids:
            for i in range(3):
                name = list('abc')
                name[i] = invalid
                self.expect(ValueError, lambda: ass(''.join(name)))

        # Non-characters are not allowed
        nonchars = range(0xfdd0, 0xfdef)
        for nonchar in nonchars:
            for i in range(3):
                name = list('abc')
                name[i] = chr(nonchar)
                self.expect(ValueError, lambda: ass(''.join(name)))

        # Control charcters are not allowed
        ctrls = range(0x007f, 0x009f)
        for ctrl in ctrls:
            for i in range(3):
                name = list('abc')
                name[i] = chr(ctrl)
                self.expect(ValueError, lambda: ass(''.join(name)))
        
    def it_deals_with_undef_attr(self):
        p = dom.paragraph()
        uuid = uuid4().hex
        attr = p.attributes[uuid]
        self.is_(p.attributes[uuid], attr)

        self.true(p.classes.count     ==  0)
        self.true(p.attributes.count  ==  0)
        self.true(len(p.classes)      ==  0)
        self.true(len(p.attributes)   ==  0)
        self.zero(p.attributes.sorted('name'))

        self.zero(list(p.attributes.reversed()))
        self.none(p.attributes.first)
        self.none(p.attributes(0))
        self.expect(IndexError, lambda: p.attributes[0])
        self.zero(p.attributes[0:1])
        
        for p in p.attributes:
            self.fail()

        attr.value = uuid4().hex
        self.zero(p.classes)
        self.one(p.attributes)
        self.eq(p.attributes.first, attr)
        self.eq(p.attributes[0], attr)
        self.eq(p.attributes(0), attr)
        self.true(p.classes.count     ==  0)
        self.true(p.attributes.count  ==  1)
        self.true(len(p.classes)      ==  0)
        self.true(len(p.attributes)   ==  1)
        self.one(p.attributes.sorted('name'))
        self.one(list(p.attributes.reversed()))
        self.one(p.attributes[0:1])
        self.is_(p.attributes.first, p.attributes[0:1].first)

        for i, _ in enumerate(p.attributes):
            i += 1

        self.eq(1, i)

        uuid = uuid4().hex
        attr = p.attributes[uuid]
        self.is_(p.attributes[uuid], attr)

        self.true(p.classes.count     ==  0)
        self.true(p.attributes.count  ==  1)
        self.true(len(p.classes)      ==  0)
        self.true(len(p.attributes)   ==  1)
        self.one(p.attributes.sorted('name'))
        self.one(list(p.attributes.reversed()))
        self.notnone(p.attributes.first)
        self.none(p.attributes.second)
        self.notnone(p.attributes(0))
        self.notnone(p.attributes(0))
        self.none(p.attributes(1))
        self.none(p.attributes(1))
        self.expect(None, lambda: p.attributes[0])
        self.expect(IndexError, lambda: p.attributes[1])
        self.one(p.attributes[0:1])
        self.is_(p.attributes.first, p.attributes[0:1].first)
        
        attr.value = uuid4().hex
        self.zero(p.classes)
        self.two(p.attributes)
        self.eq(p.attributes.second, attr)
        self.eq(p.attributes[1], attr)
        self.eq(p.attributes(1), attr)
        self.true(p.classes.count     ==  0)
        self.true(p.attributes.count  ==  2)
        self.true(len(p.classes)      ==  0)
        self.true(len(p.attributes)   ==  2)
        self.two(p.attributes.sorted('name'))
        self.two(list(p.attributes.reversed()))
        self.two(p.attributes[0:2])
        self.is_(p.attributes.first, p.attributes[0:2].first)
        self.is_(p.attributes.second, p.attributes[0:2].second)

        i = 0
        for i, _ in enumerate(p.attributes):
            i += 1

        self.eq(2, i)

    def it_sets_None_attr(self):
        expect = self.dedent('''
        <input disabled>
        </input>
        ''')

        inp = dom.input()
        inp.attributes['disabled'] = None
        self.one(inp.attributes)
        self.eq(expect, inp.pretty)

        inp = dom.input()
        inp.attributes.append('disabled')
        self.one(inp.attributes)
        self.eq(expect, inp.pretty)

        inp = dom.input()
        inp.attributes += 'disabled'
        self.one(inp.attributes)
        self.eq(expect, inp.pretty)
        
        inp = dom.input()
        inp.attributes += 'disabled', None
        self.one(inp.attributes)
        self.eq(expect, inp.pretty)

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

        # Append a collection of attributes:
        attrs = dom.attributes()
        attrs += 'foo', 'bar'
        attrs += 'baz', 'quux'
        p.attributes += attrs

        # it appends using a dict()
        cls = uuid4().hex
        p.attributes += {
            'lang': 'en',
            'dir': 'ltr'
        }

        self.nine(p.attributes)
        self.eq('en', p.lang)
        self.eq('ltr', p.dir)

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

        # Append using `append` method
        self.expect(ex, lambda: attrs.append('id', id))
        self.expect(ex, lambda: attrs.append('name', name))
        self.expect(ex, lambda: attrs.append('style', style))

        attrs = {
            'id': id,
            'name': name,
        }

        for k, v in attrs.items():
            # Append using list
            def f():
                p.attributes += [k, v]
            self.expect(ex, f)

            # Append using attribute object
            def f():
                p.attributes += dom.attribute(k, v)
            self.expect(ex, f)

            # Append using tuple
            def f():
                p.attributes += k, v
            self.expect(ex, f)

            # Append using attributes collection
            def f():
                attrs = dom.attributes()
                attrs += k, v
                p.attributes += attrs
            self.expect(ex, f)

            # Append using dict
            def f():
                p.attributes += {
                    k: v
                }
            self.expect(ex, f)

class dom_cssclass(tester):
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

        expect = '<p class="my-class-1"></p>'
        self.eq(expect, p.html)

        p.classes.append('my-class-2')
        self.two(p.classes)
        self.true('my-class-2' in p.classes)

        expect = self.dedent('''
        <p class="%s">
        </p>
        ''', 'my-class-1 my-class-2')
        self.eq(expect, p.pretty)

        p.classes += 'my-class-3'
        self.three(p.classes)
        self.eq(p.classes[2], 'my-class-3')

        expect = self.dedent('''
        <p class="%s">
        </p>
        ''', 'my-class-1 my-class-2 my-class-3')
        self.eq(expect, p.pretty)

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

        expect = '<p></p>'
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

class dom_html(tester):
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
        els = dom.html(TestHtml)
        self.eq(TestHtmlMin, els.html)

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

class dom_markdown(tester):
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

        self.eq(expect, md.pretty)

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

        self.is_(None, md.second.elements.first.title)
        self.false(md.second.elements.first.attributes['title'].isdef)
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
        self.one(md.second.children)
        self.type(dom.tablerow, md.second.children.first)
        self.one(md.second.children.first.children)
        self.type(
            dom.tabledata, 
            md.second.children.first.children.first
        )
        self.one(md.second.children.first.children.first.elements)
        self.type(
            dom.text, 
            md.second.children.first.children.first.elements.first
        )

        self.eq(
            'Foo',
            md.second.children.first.children.first.elements.first.html
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
        a = md.first.children.first
        self.type(dom.a, a)
        self.eq('mailto:address@example.com', a.href)
        self.eq('address@example.com', a.elements.first.html)

    def it_parses_html_entities(self):
        md = dom.markdown('AT&T')
        expect = self.dedent('''
        <p>
          AT&amp;T
        </p>
        ''')

        self.eq(expect, md.pretty)
        return 

        md = dom.markdown('&copy;')
        expect = self.dedent('''
        <p>
          &copy;
        </p>
        ''')

        self.eq(expect, md.pretty)


        md = dom.markdown('4 < 5')

        expect = self.dedent('''
        <p>
          4 &lt; 5
        </p>
        ''')
        self.eq(expect, md.pretty)

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
        self.eq(expect, md.pretty)

    def it_raises_with_nonstandard_inline_html_tags(self):
        md = self.dedent('''
          Below is some inline HTML with a non-standard tag

          <ngderp>
            Foo
          </ngderp>

        ''')
        self.expect(NotImplementedError, lambda: dom.markdown(md))

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

        self.four(md.first.elements)
        self.type(dom.paragraph, md.first.elements.first)
        self.type(dom.text, md.first.elements.second)
        self.type(dom.paragraph, md.first.elements.third)
        self.type(dom.text, md.first.elements.fourth)

        md = dom.markdown('''
        > This is a blockquote with two paragraphs. Lorem ipsum dolor sit amet,
        consectetuer adipiscing elit. Aliquam hendrerit mi posuere lectus.
        Vestibulum enim wisi, viverra nec, fringilla in, laoreet vitae, risus.

        > Donec sit amet nisl. Aliquam semper ipsum sit amet velit. Suspendisse
        id sem consectetuer libero luctus adipiscing.
        ''')

        self.one(md)
        self.type(dom.blockquote, md.first)

        self.four(md.first.elements)
        self.type(dom.paragraph, md.first.elements.first)
        self.type(dom.text, md.first.elements.second)
        self.type(dom.paragraph, md.first.elements.third)
        self.type(dom.text, md.first.elements.fourth)

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

        self.six(md.first.elements)
        self.type(dom.paragraph, md.first.elements.first)
        self.type(dom.text, md.first.elements.second)
        self.type(dom.blockquote, md.first.elements.third)
        self.type(dom.text, md.first.elements.fourth)
        self.type(dom.paragraph, md.first.elements[2].elements.first)
        self.type(dom.paragraph, md.first.elements.fifth)
        self.type(dom.text, md.first.elements.sixth)

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
        self.type(dom.text, md.first.elements.second)
        self.type(dom.li, md.first.elements.third.elements.second)
        self.type(dom.li, md.first.elements.third.elements.fourth)
        self.type(dom.text, md.first.elements.fourth)
        self.type(dom.p, md.first.elements.fifth)
        self.type(dom.text, md.first.elements.fourth)
        self.type(dom.p, md.first.elements.fifth)
        self.type(dom.text, md.first.elements.fifth.elements.first)
        self.type(dom.code, md.first.elements[6].elements.first)

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
          self.seven(md.first.elements)
          self.type(dom.text, md.first.elements.first)
          self.type(dom.li, md.first.elements.second)
          self.type(dom.text, md.first.elements.third)
          self.type(dom.li, md.first.elements.fourth)
          self.type(dom.text, md.first.elements.fifth)
          self.type(dom.li, md.first.elements.sixth)
          self.type(dom.text, md.first.elements.seventh)

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
        self.seven(md.first.elements)
        self.type(dom.text, md.first.elements.first)
        self.type(dom.li, md.first.elements.second)
        self.type(dom.text, md.first.elements.third)
        self.type(dom.li, md.first.elements.fourth)
        self.type(dom.text, md.first.elements.fifth)
        self.type(dom.li, md.first.elements.sixth)

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
            self.two(md.first.children)
            self.type(dom.li, md.first.children.first)
            self.type(dom.li, md.first.children.second)

        md = dom.markdown('''
        *   Bird

        *   Magic
        ''')

        self.one(md)
        self.type(dom.ul, md.first)
        self.two(md.first.children)
        self.one(md.first.children.first.children)
        self.type(dom.p, md.first.children.first.children.first)
        self.type(dom.p, md.first.children.second.children.first)

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
            self.two(md.first.children)
            self.two(md.first.children.first.children)
            self.type(dom.p, md.first.children.first.children.first)
            self.type(dom.p, md.first.children.second.children.first)

        md = dom.markdown('''
        *   A list item with a blockquote:

            > This is a blockquote
            > inside a list item.
        ''')

        self.one(md)
        self.type(dom.ul, md.first)
        self.type(dom.li, md.first.children.first)
        self.two(md.first.children.first.children)
        self.type(dom.p, md.first.children.first.children.first)
        self.type(dom.blockquote, md[0].children[0].children[1])

        md = dom.markdown('''
        *   A list item with a code block:

                <code goes here>
        ''')
        self.one(md)
        self.type(dom.ul, md.first)
        self.one(md.first.children)
        self.two(md.first.children.first.children)
        self.type(dom.p, md.first.children.first.children.first)
        self.type(dom.pre, md.first.children.first.children.second)
        self.one(md.first.children.first.children.second.children)
        self.type(
            dom.code,
            md.first.children.first.children.second.children.first
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

        self.eq(expect, md.first.pretty)

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

        self.eq(expect, md.pretty)

class test_selectors(tester):
    # TODO Running all the tests in test_selectors takes around 10
    # seconds at the time of this writting. We should run the profiler
    # on the following test:
    #
    #     python3 test.py test_selectors
    #
    # There may be some hotspots that could be optimized to reduce the
    # time spent running these tests.

    @property
    def _shakespear(self):
        if not hasattr(self, '_spear'):
            self._spear = dom.html(Shakespeare)
        return self._spear

    @property
    def _listhtml(self):
        if not hasattr(self, '_lis'):
            self._lis = dom.html(ListHtml)
        return self._lis

    def it_selects_lang(self):
        html = dom.html('''
        <html lang="en">
          <head></head>
          <body>
            <div>
              <p id="enp">
                My language is 'en' because it was specified in
                the root html tag.
              </p>
            </div>
            <section lang="fr">
               <p id="frp">Comment dites-vous "Bonjour" en Espanol?</p>
               <div>
                   <blockquote lang="es">
                     <p id="esp">
                       My language will be Spainish.
                     </p>
                   </blockquote>
               </div>
            </section>
            <section lang="DE">
              <p id="dep">German paragraph</p>
            </section>
          </body>
      </html>
        ''')

        sels = [
            'p:lang(fr)',
            'p:lang(FR)',
        ]

        for sel in sels:
            els = html[sel]
            self.one(els)
            self.type(dom.p, els.first)
            self.eq('frp', els.first.id)

        sels = [
            'p:lang(de)',
            'p:lang(DE)',
        ]
        for sel in sels:
            els = html[sel]
            self.one(els)
            self.type(dom.p, els.first)
            self.eq('dep', els.first.id)
            
        sels = [
            'p:lang(es)',
            'p:lang(ES)',
        ]
        for sel in sels:
            els = html[sel]
            self.one(els)
            self.type(dom.p, els.first)
            self.eq('esp', els.first.id)
            
        sels = [
            'p:lang(en)',
            'p:lang(EN)',
        ]
        for sel in sels:
            els = html[sel]
            self.one(els)
            self.type(dom.p, els.first)
            self.eq('enp', els.first.id)

        html = dom.html('''
        <html>
            <head></head>
            <body>
                <div lang="en">
                    <p id="enp">
                        Regural english
                    </p>
                </div>
                <section lang="en-GB-oed">
                    <p id="engboed">English, Oxford English Dictionary spelling</p>

                    <div>
                        <blockquote lang="zh-Hans">
                            <div>
                                <p id="zhh">Simplified Chinese</p>
                            </div>
                        </blockquote>
                    </div>
                </section>
            </body>
        </html>
        ''')

        sels = [
            'p:lang(en)',
            'p:lang(EN)',
        ]
        for sel in sels:
            els = html[sel]
            self.two(els)
            self.type(dom.p, els.first)
            self.eq('enp', els.first.id)
            self.type(dom.p, els.second)
            self.eq('engboed', els.second.id)

        sels = [
            'p:lang(en-GB)',
            'p:lang(en-GB-oed)',
            'p:lang(EN-GB-OED)',
            'p:lang(en-gb-oed)',
        ]

        for sel in sels:
            els = html[sel]
            self.one(els)
            self.type(dom.p, els.first)
            self.eq('engboed', els.first.id)

        sels = [
            'p:lang(zh)',
            'p:lang(zh-hans)',
            'p:lang(zh-HANS)',
        ]

        for sel in sels:
            els = html[sel]
            self.one(els)
            self.type(dom.p, els.first)
            self.eq('zhh', els.first.id)

        sels = [
            '*:lang(zh)',
            ':lang(zh-hans)',
        ]

        for sel in sels:
            els = html[sel]
            self.three(els)
            self.type(dom.blockquote, els.first)
            self.type(dom.div, els.second)
            self.type(dom.p, els.third)
            self.eq('zhh', els.third.id)

        sels = [
            'p:lang(EN-GB-)',
            'p:lang(EN-)',
            'p:lang(E)',
        ]

        for sel in sels:
            els = html[sel]
            self.zero(els)

    def it_selects_with_groups(self):
        html = self._shakespear

        sels = [
            'h2, h3',
            'H2, h3',
        ]

        for sel in sels:
            els = html[sel]

            self.two(els)
            self.type(dom.elements, els)
            self.type(dom.h2, els.first)
            self.type(dom.h3, els.second)
            self.eq(els.first.elements.first.html, 'As You Like It')
            self.eq(
                els.second.elements.first.html, 
                'ACT I, SCENE III. A room in the palace.'
            )

    def it_raises_on_invalid_identifiers(self):
        """ In CSS, identifiers (including element names, classes, and
        IDs in selectors) can contain only the characters [a-zA-Z0-9]
        and ISO 10646 characters U+00A0 and higher, plus the hyphen (-)
        and the underscore (_); they cannot start with a digit, two
        hyphens, or a hyphen followed by a digit. Identifiers can also
        contain escaped characters and any ISO 10646 character as a
        numeric code (see next item). For instance, the identifier
        “B&W?” may be written as “B\&W\?” or “B\26 W\3F”.

            -- W3C Specification
        """
        
        ''' Valids '''
        sels = [
            'id#foo123',
            'id#foo-_',
            'id#-_foo',
            'id#f-_oo',

            'id[foo123]',
            'id[foo-_]',
            'id[-_foo]',
            'id[f-_oo]',

            'id[foo=foo123]',
            'id[foo=foo-_]',
            'id[foo=-_foo]',
            'id[foo=f-_oo]',

            'id.foo123',
            'id.foo-_',
            'id.-_foo',
            'id.f-_oo',
        ]

        for sel in sels:
            self.expect(None, lambda: dom.selectors(sel))

        ''' Invalids '''
        sels = [
            'id#--foo',
            'id#123',
            'id#123foo',
            'id#-1foo',

            'id[--foo]',
            'id[123]',
            'id[123foo]',
            'id[-1foo]',

            'id[foo=--foo]',
            'id[foo=123]',
            'id[foo=123foo]',
            'id[foo=-1foo]',

            'id.--foo',
            'id.123',
            'id.123foo',
            'id.-1foo',
        ]

        for sel in sels:
            self.expect(
                dom.CssSelectorParseError, 
                lambda: dom.selectors(sel)
            )

    def it_selects_with_groups_element_to_class(self):
        html = self._shakespear
        sels = [
            'h2, .thirdClass',
            'h2, *.thirdClass',
            'h2, div.thirdClass',

            'h2[id^="023338d1"], .thirdClass',
            '[id^="023338d1"], *.thirdClass',
            '*[id^="023338d1"], div.thirdClass',

            '*.header, .thirdClass',
            '.header, *.thirdClass',
            'h2.header, div.thirdClass',
        ]

        for sel in sels:
            els = html[sel]
            self.two(els)
            self.type(dom.h2, els.first)
            self.eq('scene1', els.second.id)

        sels = [
            '.thirdClass, h2',
            '*.thirdClass, h2',
            'div.thirdClass, h2',

            '.thirdClass, h2[id^="023338d1"]',
            '*.thirdClass, [id^="023338d1"]',
            'div.thirdClass, *[id^="023338d1"]',

            '.thirdClass, *.header',
            '*.thirdClass, .header',
            'div.thirdClass, h2.header',
        ]

        for sel in sels:
            els = html[sel]
            self.two(els)
            self.eq('scene1', els.first.id)
            self.type(dom.h2, els.second)

    def it_selects_with_groups_element_to_attributes(self):
        html = self._shakespear

        sels = [
            'h2, [title=wtf]',
            'h2, *[title=wtf]',
            'h2, div[title=wtf]',

            'h2[id^="023338d1"], [title=wtf]',
            '[id^="023338d1"], *[title=wtf]',
            '*[id^="023338d1"], div[title=wtf]',

            '*.header, [title=wtf]',
            '.header, *[title=wtf]',
            'h2.header, div[title=wtf]',
        ]

        for sel in sels:
            els = html[sel]
            self.two(els)
            self.type(dom.h2, els.first)
            self.type(dom.div, els.second)
            self.eq('wtf', els.second.title)

        sels = [
            '[title=wtf], h2',
            '*[title=wtf], h2',
            'div[title=wtf], h2',

            '[title=wtf], h2[id^="023338d1"]',
            '*[title=wtf], [id^="023338d1"]',
            'div[title=wtf], *[id^="023338d1"]',

            '[title=wtf], *.header',
            '*[title=wtf], .header',
            'div[title=wtf], h2.header',
        ]

        for sel in sels:
            els = html[sel]

            self.two(els)
            self.type(dom.div, els.first)
            self.eq('wtf', els.first.title)
            self.type(dom.h2, els.second)

    def it_selects_with_groups_element_to_identifiers(self):
        html = self._shakespear

        sels = [
            '#herp,                  #speech16',
            '*#herp,                 *#speech16',
            'div#herp,               div#speech16',

            '[title=wtf],            #speech16',
            '*[title=wtf],           *#speech16',
            'div[title=wtf],         div#speech16',

            '[title=wtf].dialog,     #speech16',
            '*[title=wtf].dialog,    *#speech16',
            'div[title=wtf].dialog,  div#speech16',
        ]

        for sel in sels:
            els = html[sel]
            self.two(els)
            self.eq('herp', els.first.id)
            self.eq('speech16', els.second.id)

        sels = [
            '#speech16,     #herp                  ',
            '*#speech16,    *#herp                 ',
            'div#speech16,  div#herp               ',

            '#speech16,     [title=wtf]            ',
            '*#speech16,    *[title=wtf]           ',
            'div#speech16,  div[title=wtf]         ',

            '#speech16,     [title=wtf].dialog     ',
            '*#speech16,    *[title=wtf].dialog    ',
            'div#speech16,  div[title=wtf].dialog  ',
        ]

        for sel in sels:
            els = html[sel]
            self.two(els)
            self.eq('speech16', els.first.id)
            self.eq('herp', els.second.id)

    def it_selects_with_child_combinator(self):
        html = dom.html(AdjacencyHtml)

        ''' Two child combinators '''
        sel = 'div > p'
        els = html[sel]
        self.one(els)
        self.type(dom.p, els.first)
        self.eq('child-of-div', els.first.id)

        bads = [
            'div > xp'
            'xdiv > p'
        ]

        self.all(html[bad].isempty for bad in bads)

        ''' Three child combinators '''
        sel = 'div > p > span'
        els = html[sel]
        self.one(els)
        self.type(dom.span, els.first)
        self.eq('child-of-p-of-div', els.first.id)

        bads = [
            'xdiv > p > span'
            'div > xp > span'
            'div > p > xspan'
        ]

        self.all(html[bad].isempty for bad in bads)

        ''' A descendant combinator with two three combinators '''
        sel = 'html div > p > span'
        els = html[sel]
        self.type(dom.span, els.first)
        self.eq('child-of-p-of-div', els.first.id)

        # Change the above descendant combinator to child combinator and
        # it should produce zero results. 
        sel = 'html > div > p > span'
        els = html[sel]
        self.zero(els)

        ''' A simple child combinator expression to produce two results
        '''
        els = html['p > span']
        self.two(els)
        self.type(dom.span, els.first)
        self.type(dom.span, els.second)
        self.eq('child-of-p-of-div', els.first.id)
        self.eq('child-of-p-of-h2', els.second.id)

        # Try out some chained seletors
        sels = [
            'p > span#child-of-p-of-h2',
            'p#child-of-h2 > span#child-of-p-of-h2',
            'p#child-of-h2 > span',
            'p.p-header > span',
        ]

        for sel in sels:
            els = html[sel]
            self.one(els)
            self.type(dom.span, els.first)
            self.eq('child-of-p-of-h2', els.first.id)
    
    def it_selects_with_next_and_subsequent_sibling_combinator(self):
        html = dom.html('''
        <div>
          <p foo="bar"></p>
          <p id="1"></p>
          <p id="2"></p>
          <p id="3"></p>
          <p id="4"></p>
          <p baz=baz></p>
          <p id="5"></p>
          <p id="6"></p>
          <p id="7"></p>
          <p id="8"></p>
        </div>
        ''')

        sels = [
            'div p[foo=bar] + p ~ p[baz=baz] + p ~ p',
        ]

        for sel in sels:
            els = html[sel]
            self.three(els)
            self.eq([6, 7, 8], [int(x) for x in els.pluck('id')])

        html = dom.html('''
        <div>
          <p foo="bar">
            <div>
              <p foo="baz"></p>
              <p id="1"></p>
              <p id="2"></p>
              <p id="3"></p>
              <p id="4"></p>
            </div>
            <div>
              <p foo="baz"></p>
              <p id="5"></p>
              <p id="6"></p>
              <p id="7"></p>
              <p id="8"></p>
            </div>
          </p>
          <p foo="quux">
            <div>
              <p foo="baz"></p>
              <p id="9"></p>
              <p id="10"></p>
              <p id="11"></p>
              <p id="12"></p>
            </div>
            <div>
              <p foo="baz"></p>
              <p id="13"></p>
              <p id="14"></p>
              <p id="15"></p>
              <p id="16"></p>
            </div>
          </p>
        </div>
        ''')

        sels = [
            'p[foo=bar] p[foo=baz] ~ p',
        ]

        for sel in sels:
            els = html[sel]
            self.eight(els)
            self.eq(
                [str(x) for x in list(range(1, 9))], 
                els.pluck('id')
            )

        html = dom.html('''
        <div>
          <p foo="bar"></p>
          <p id="1"></p>
          <p id="2"></p>
          <p id="3"></p>
          <p id="4"></p>
        </div>
        ''')

        sels = [
            '*   p[foo=bar] ~ p ~ p',
            'div p[foo=bar] ~ p ~ p',
            '    p[foo=bar] ~ p ~ p',
            '*   p[foo=bar] + p ~ p',
            'div p[foo=bar] + p ~ p',
            '    p[foo=bar] + p ~ p',
        ]

        for sel in sels:
            els = html[sel]
            self.three(els)
            self.eq('2', els.first.id)
            self.eq('3', els.second.id)
            self.eq('4', els.third.id)

        html = dom.html('''
        <div>
          <p foo="bar"></p>
          <p id="1"></p>
          <p id="2"></p>
          <p id="3"></p>
          <p id="4"></p>
          <p foo="baz"></p>
          <p id="5"></p>
          <p id="6"></p>
          <p id="7"></p>
          <p id="8"></p>
        </div>
        ''')

        sels = [
            '*   p[foo=baz] ~ p ~ p',
            'div p[foo=baz] ~ p ~ p',
            '    p[foo=baz] ~ p ~ p',
            '*   p[foo=baz] + p ~ p',
            'div p[foo=baz] + p ~ p',
            '    p[foo=baz] + p ~ p',
        ]

        for sel in sels:
            els = html[sel]
            self.three(els)
            self.eq('6', els.first.id)
            self.eq('7', els.second.id)
            self.eq('8', els.third.id)

        html = dom.html('''
        <div>
          <p foo="bar"></p>
          <p id="1"></p>
          <q id="2"></q>
          <p id="3"></p>
          <q id="4"></q>
          <p id="5"></p>
          <q id="6"></q>
          <p id="7"></p>
        </div>
        ''')

        sels = [
            '*   p[foo=bar] ~ p ~ q',
            'div p[foo=bar] ~ p ~ q',
            '    p[foo=bar] ~ p ~ q',
            '*   p[foo=bar] + p ~ q',
            'div p[foo=bar] + p ~ q',
            '    p[foo=bar] + p ~ q',
        ]

        for sel in sels:
            els = html[sel]
            self.three(els)
            self.eq('2', els.first.id)
            self.eq('4', els.second.id)
            self.eq('6', els.third.id)

        html = dom.html(AdjacencyHtml)

        sels = [
            'div ~ div ~ p + p',
        ]

        for sel in sels:
            els = html[sel]
            self.one(els)
            self.eq('after-the-adjacency-anchor', els.first.id)

        sels = [
            '*#first-div   ~ p + p',
            '#first-div    ~ p + p',
            'div#first-div ~ p + p',
        ]

        for sel in sels:
            els = html[sel]
            self.two(els)
            self.eq('immediatly-before-the-adjacency-anchor', els[0].id)
            self.eq('after-the-adjacency-anchor', els[1].id)
        
    def it_selects_with_next_sibling_combinator(self):
        html = dom.html(AdjacencyHtml)

        sels = [
            'p + p + div',
            'p + p + div#adjacency-anchor',

            'p '
            ' + p#immediatly-before-the-adjacency-anchor'
            ' + div#adjacency-anchor',

            'p#before-the-adjacency-anchor'
            ' + p#immediatly-before-the-adjacency-anchor'
            ' + div#adjacency-anchor',
        ]

        for sel in sels:
            els = html[sel]
            self.one(els)
            self.eq('adjacency-anchor', els[0].id, sel)

        sels = [
            'div + p + p'
        ]

        for sel in sels:
            els = html[sel]
            self.two(els)
            self.eq('immediatly-before-the-adjacency-anchor', els[0].id)
            self.eq('after-the-adjacency-anchor', els[1].id)

        sels = [
            'div#adjacency-anchor + p + p'
        ]

        for sel in sels:
            els = html[sel]
            self.one(els)
            self.eq('after-the-adjacency-anchor', els[0].id)

        sels = [
            'div + p + p',
            'p + p',
        ]
        for sel in sels:
            els = html[sel]
            self.two(els)
            self.eq('immediatly-before-the-adjacency-anchor', els[0].id)
            self.eq('after-the-adjacency-anchor', els[1].id)

        ''' Select the <p> immediatly after #adjacency-anchor '''
        sels = [
            '#adjacency-anchor + p',
            'div#adjacency-anchor + p',
            'div#adjacency-anchor + p#immediatly-after-the-adjacency-anchor',
        ]
        for sel in sels:
            els = html[sel]
            self.one(els)
            self.eq('immediatly-after-the-adjacency-anchor', els[0].id)

        ''' These should match nothing but are similar to the above'''
        sels = [
            '#adjacency-anchor + div',
            'div#adjacency-anchor + p.id-dont-exist',
            '#adjacency-anchor + '
                'p#XXXimmediatly-after-the-adjacency-anchor',
        ]
        for sel in sels:
            els = html[sel]
            self.zero(els)

    def it_selects_with_subsequent_sibling_combinator(self):
        html = dom.html(AdjacencyHtml)

        sels = [
            'div ~ div p + q',
        ]

        for sel in sels:
            els = html[sel]
            self.one(els)
            self.eq('second-child-of-h2', els.first.id)

        sels = [
            'html > body > div#adjacency-anchor ~ p',
            'html body > div#adjacency-anchor ~ p',
            'body > div#adjacency-anchor ~ p',
            'body div#adjacency-anchor ~ p',
            'div#adjacency-anchor ~ p',
            '#adjacency-anchor ~ p',
        ]

        for sel in sels:
            els = html[sel]
            self.two(els)
            self.eq('immediatly-after-the-adjacency-anchor', els.first.id)
            self.eq('after-the-adjacency-anchor', els.second.id)

        els = html['div ~ p']
        self.four(els)
        self.eq('before-the-adjacency-anchor', els.first.id)
        self.eq('immediatly-before-the-adjacency-anchor', els.second.id)
        self.eq('immediatly-after-the-adjacency-anchor', els.third.id)
        self.eq('after-the-adjacency-anchor', els.fourth.id)

        els = html['div ~ *']
        self.five(els)
        self.eq('before-the-adjacency-anchor', els.first.id)
        self.eq('immediatly-before-the-adjacency-anchor', els.second.id)
        self.eq('adjacency-anchor', els.third.id)
        self.eq('immediatly-after-the-adjacency-anchor', els.fourth.id)
        self.eq('after-the-adjacency-anchor', els.fifth.id)

        els = html['* ~ *']
        self.all(
            type(x) not in (dom.html, dom.head, dom.h2) for x in els
        )

        els = html['head ~ body']
        self.one(els)
        self.type(dom.body, els.first)

        els = html['h2 ~ *']
        self.zero(els)



    def it_selects_with_chain_of_elements(self):
        html = self._shakespear

        sels = [
          'html body div div h2',
          'body div div h2',
          'div div h2',
          'div h2',
          'h2',
          'html div div h2',
          'html body div h2',
          'html div h2',
          'html body h2',
          'html div h2',
          'html h2',
          'body h2',
          'div h2',
          'div div h2',
        ]

        for sel in sels:
            h2s = html[sel]
            self.one(h2s)
            self.type(dom.h2, h2s.first)

            h2s = html[sel.upper()]
            self.one(h2s)
            self.type(dom.h2, h2s.first)

        sels = [
          'derp body div div h2',
          'html derp div h2',
          'html body derp div h2',
          'html body div derp h2',
          'derp div h2',
          'body derp div h2',
          'body div derp h2',
          'derp div h2',
          'div derp h2',
          'div derp',
          'html html div div h2',
          'html body body div h2',
          'html body div div div h2',
          'html body div div h2 h2',
          'body body div h2',
          'body div div div h2',
          'body div div h2 h2',
          'div div div h2',
          'div div h2 h2',
          'div h2 h2',
          'h2 h2',
          'h2 div',
          'html div body div h2',
          'html body div h2 div',
          'div body div h2',
          'body div h2 div',
          'div h2 div',
          'div body h2',
          'body body h2',
          'div html h2',
          'body wbr h2', 
          'body derp h2', 
          'wbr', 
          'derp'
        ]

        for sel in sels:
          self.zero(html[sel], sel)
          self.zero(html[sel.upper()], sel)

    def it_selects_with_chain_of_elements_and_classes(self):
        html = self._shakespear

        sels = [
            'div div.dialog',
            'div .dialog',
            'div *.dialog',
            '* *.dialog',
        ]

        for sel in sels:
            els = html[sel]
            self.count(51, els)
            self.all('dialog' in x.classes for x in els)
            self.all(type(x.parent) is dom.div for x in els)

        sels = [
            'div.dialog div.dialog div.dialog',
            'div.dialog div.dialog *.dialog',
            'div.dialog div.dialog .dialog',
            'div.dialog .dialog div.dialog',
            'div.dialog *.dialog div.dialog',
            'div.dialog div.dialog div.dialog',
            '.dialog div.dialog div.dialog',
            '*.dialog div.dialog div.dialog',
        ]

        for sel in sels:
            els = html[sel]
            self.count(49, els)
            self.all('dialog' in x.classes for x in els)
            self.all(type(x.parent) is dom.div for x in els)
            self.all(type(x.grandparent) is dom.div for x in els)

    def it_selects_with_chain_of_elements_and_pseudoclasses(self):
        html = self._shakespear

        sels = [
            'div :not(#playwright)',
            'div *:not(#playwright)',
            'div div:not(#playwright)',
        ]

        for i, sel in enumerate(sels):
            els = html(sel)
            if i.last:
                self.count(241, els)
            else:
                self.count(243, els)
            self.all(x.id != 'playwright' for x in els)
            self.all(type(x.parent) is dom.div for x in els)

    def it_selects_with_classes(self):
        html = self._shakespear

        ''' Non-existing class selector '''
        sels = [
            '*.dialogxxx',
            '.dialogxxx',
            'div.dialogxxx'
        ]

        for sel in sels:
            self.zero(html[sel])

        ''' Single class selector '''
        sels = [
            '*.dialog',
            '.dialog',
            'div.dialog'
        ]

        for sel in sels:
            # Class selectors should be case-sensitive
            self.zero(html[sel.upper()])

            els = html[sel]
            for el in els:
                self.type(dom.div, el)
                self.true('dialog' in el.classes)
            self.count(51, els, 'sel: ' + sel)

        ''' Non-existing chained classes selectors '''
        sels = [
            '*.dialog.sceneXXX',
            '.dialogXXX.scene',
            'divXXX.dialog.scene',
        ]

        for sel in sels:
            self.zero(html[sel])

        ''' Chained classes selectors '''
        sels = [
            '*.dialog.scene',
            '.dialog.scene',
            'div.dialog.scene',
        ]

        for sel in sels:
            els = html[sel]
            self.type(dom.div, els.first)
            self.true('dialog' in els.first.classes)
            self.eq('scene1', els.first.id)
            self.one(els)

    def it_selects_with_attribute(self):
        html = self._shakespear

        sels = [
            'div[foo]',
            '*[bar]',
            '[foo]',
        ]

        for sel in sels:
            self.zero(html[sel])

        sels = [
            'div[title]',
            '*[title]',
            '[title]',
        ]

        for sel in sels:
            self.one(html[sel])

    def it_selects_with_attribute_equality(self):
        ''' Select using the = operator [foo=bar]
        '''
        html = self._shakespear

        sels = [
            '[foo=bar]',
            '[title=bar]',
            '[foo=wtf]',
        ]

        for sel in sels:
            self.zero(html[sel])
            break
        else:
            self.fail('There were no `sels`')

        sels = [
            '*[title=wtf]',
            '[title=wtf]',
            '*[TITLE=wtf]',
            '[TITLE=wtf]',
        ]

        for sel in sels:
            # Attribtue value are case-sensitive
            self.zero(html[sel.replace('wtf', 'WTF')])

            els = html[sel]
            self.one(els)
            self.type(dom.div, els.first)
            self.eq('scene1.3.29', els.first.children.first.id)

        sels = [
            'div[id=speech144][class=character]',
            '*[id=speech14][class=characterxxx]',
            '[id=speech14][class=character][foo=bar]',
        ]

        for sel in sels:
            els = html[sel]
            self.zero(els)
            break
        else:
            self.fail('There were no `sels`')

        sels = [
            'div[id=speech14][class=character]',
            '*[id=speech14][class=character]',
            '[id=speech14][class=character]',
        ]

        for sel in sels:
            els = html[sel]
            self.one(els)
            self.type(dom.div, els.first)
            self.eq('ROSALIND', els.first.elements.first.html)
            break
        else:
            self.fail('There were no `sels`')

        sels = [
            '[id=speech1][class^=char]',
            '[id$=ech1][class*=aract]'
        ]

        for sel in sels:
            els = html[sel]
            self.one(els)
            self.eq('speech1', els.first.id)

        sels = [
            '[id=scene1][class~=thirdClass]',
            '[id][class~=thirdClass]'
        ]

        for sel in sels:
            els = html[sel]
            self.one(els)
            self.eq('scene1', els.first.id)

    def it_selects_with_attribute_space_seperated(self):
        ''' Select using the ~= operator [foo~=bar]
        '''
        html = self._shakespear

        sels = [
           '*[class~=thirdClass]',
           'div[class~=thirdClass]',
           '[class~=thirdClass]',
           '[class~=scene]',
        ]

        for sel in sels:
            if 'thirdClass' in sel:
                self.zero(html[sel.lower()])

            els = html[sel]
            self.one(els)
            self.type(dom.div, els.first)
            self.eq('scene1', els.first.id)

        sels = [
           '*[class~=third]',
           'div[class~=third]',
           '[class~=third]',
           '[class~="dialog scene thirdClass"]',
           '[class~="scene thirdClass"]',
        ]

        for sel in sels:
            els = html[sel]
            self.zero(els)

    def it_selects_with_attribute_startswith(self):
        ''' Select using the startswith operator [foo^=bar] 
        '''

        html = self._shakespear

        v = str()
        for c in 'test':
            v += c
            sels = [
                '*[id^=%s]'    %  v,
                'div[id^=%s]'  %  v,
                '[id^=%s]'     %  v,
            ]
            for sel in sels:
                self.zero(html[sel.replace(v, v.upper())])
                els = html[sel]
                self.one(els)
                self.type(dom.div, els.first)
                self.eq('test', els.first.id)

        sels = [
            '[id^=est]',
            '[id^=es]',
        ]

        for sel in sels:
            sels = [
                '*%s'    %  sel,
                'div%s'  %  sel,
                '%s'     %  sel,
            ]
            for sel in sels:
                els = html[sel]
                self.zero(els)

    def it_selects_with_attribute_endswith(self):
        ''' Select using the endswith operator [foo$=bar] 
        '''

        html = self._shakespear

        v = str()
        for c in reversed('dialog'):
            v = c + v
            sel = '[class$=%s]' % v
            sels = [
                '*%s'    %  sel,
                'div%s'  %  sel,
                '%s'     %  sel,
            ]
            for sel1 in sels:
                SEL = sel1.replace(sel1, sel.upper())
                self.zero(html[SEL])
                els = html[sel1]
                self.count(50, els)
                self.type(dom.div, els.first)

        sels = [
            '[id$=dialo]',
            '[id$=ialo]',
        ]

        for sel in sels:
            sels = [
                '*%s'    %  sel,
                'div%s'  %  sel,
                '%s'     %  sel,
            ]
            for sel in sels:
                els = html[sel]
                self.zero(els)

    def it_selects_with_attribute_contains(self):
        ''' Select using the contains operator [foo*=bar] 
        '''

        html = self._shakespear

        sels = [
            '*[class*=dialog]',
            'div[class*=dialog]',
            '[class*=dialog]',
            '*[class*=dialo]',
            'div[class*=dialo]',
            '[class*=dialo]',
            '*[class*=ialog]',
            'div[class*=ialog]',
            '*[class*=ialog]',
            '*[class*=ialo]',
            'div[class*=ialo]',
            '*[class*=ialo]',
        ]

        for sel in sels:
            els = html[sel]
            self.count(51, els)
            self.type(dom.div, els.first)

        sels = [
            '*[class*=idontexist]',
            'div[class*=idontexist]',
            '[class*=idontexist]',

            '*[class*=DIALOG]',
            'div[class*=DIALOG]',
            '[class*=DIALOG]',
            '*[class*=DIALO]',
            'div[class*=DIALO]',
            '[class*=DIALO]',
            '*[class*=IALOG]',
            'div[class*=IALOG]',
            '*[class*=IALOG]',
            '*[class*=IALO]',
            'div[class*=IALO]',
            '*[class*=IALO]',
        ]

        for sel in sels:
            els = html[sel]
            self.zero(els)

    def it_selects_with_attribute_hyphen_seperated(self):
        ''' Select using the hyphen-seperated operator [foo|=bar] 
        '''
        html = self._shakespear

        sels = [
            '[id|="023338d1"]',
            '[id|="023338d1-5503"]',
            '[id|="023338d1-5503-4054"]',
            '[id|="023338d1-5503-4054-98f7-c1e9c9ad390d"]',
        ]

        for sel in sels:
            els = html[sel]
            self.one(els)
            self.type(dom.h2, els.first)

        sels = [
            '[id|="023338D1"]',
            '[id|="023338D1-5503"]',
            '[id|="023338D1-5503-4054"]',
            '[id|="023338D1-5503-4054-98F7-C1E9C9AD390D"]',
        ]

        self.all(html[sel].isempty for sel in sels)

        for sel in sels:
            els = html[sel]
        els = html['[id|=test]']
        self.one(els)
        self.type(dom.div, els.first)

        sels = [
            '[id|="023338d"]',
            '[id|="023338d1-"]',
            '[id|="023338d1-5503-"]',
            '[id|="023338d1-5503-4"]',
            '[id|="023338d1-5503-4054-"]',
            '[id|="023338d1-5503-4054-9"]',
            '[id|="023338d1-5503-4054-98f7-"]',
            '[id|="023338d1-5503-4054-98f7-c"]',
            '[id|="f6836822"]',
            '[id|="f6836822-589e"]',
            '[id|="f6836822-589e-40bf-a3f7-a5c3185af4f7"]',
        ]

        for sel in sels:
            self.zero(html[sel], sel)

    def it_select_root(self):
        html = self._shakespear

        sels = [
            '*:root',
            'html:root',
            ':root',
            '*:ROOT',
            'html:ROOT',
            ':ROOT',
        ]

        for sel in sels:
            els = html[sel]
            self.one(els)
            self.type(dom.html, els.first)

        id = uuid4().hex
        html = dom.html('''
            <p id="%s">
                The following is
                <strong>
                    strong text
                </strong>
            </p>
        ''' % id)

        sels = [
            'p:root',
            ':root',
        ]

        for sel in sels:
            els = html[sel]
            self.one(els)
            self.type(dom.p, els.first, sel)

        sels = [
            'html:root',
        ]

        for sel in sels:
            els = html[sel]
            self.zero(els)

    def it_selects_nth_child(self):
        html = self._listhtml

        ''' single '''
        els = html['li:nth-child(2)']
        self.one(els)
        self.eq('1', els.first.id)

        els = html['li:NTH-CHILD(2)']
        self.one(els)
        self.eq('1', els.first.id)

        ''' even '''
        sels = [
            'li:nth-child(even)',
            'li:nth-child(EVEN)',
            'li:nth-child(2n+0)',
            'li:nth-child(2n-2)',
            'li:nth-child(2n-500)',
            'li:nth-child(2N-500)',
        ]

        for sel in sels:
            els = html[sel]
            self.six(els)
        
            for i, id in enumerate((1, 3, 5, 7, 9, 11)):
                self.eq(str(id), els[i].id)

        ''' odd '''
        sels = [
            'li:nth-child(odd)',
            'li:nth-child(ODD)',
            'li:nth-child(2n+1)',
            'li:nth-child(2n-1)',
        ]

        for sel in sels:
            els = html[sel]
            self.six(els)
        
            for i, id in enumerate((0, 2, 4, 6, 8, 10)):
                self.eq(str(id), els[i].id)

        ''' every one '''
        sels = [
            'li:nth-child(1n+0)',
            'li:nth-child(1n+1)',
        ]

        for sel in sels:
            els = html[sel]
            self.count(12, els)
        
            for i in range(11):
                self.eq(str(i), els[i].id)

        ''' every one starting at the second child'''
        els = html['li:nth-child(1n+2)']
        self.count(11, els)
    
        for i in range(11):
            self.eq(str(i + 1), els[i].id)

        ''' every one starting at the fifth child'''
        els = html['li:nth-child(1n+5)']
        self.eight(els)
        for i in range(8):
            self.eq(str(i + 4), els[i].id)

        ''' every one starting at the sixth child'''
        els = html['li:nth-child(1n+6)']
        self.seven(els)
        for i in range(7):
            self.eq(str(i + 5), els[i].id)

        els = html['li:nth-child(2n+3)']
        self.five(els)
        for i, j in enumerate([2, 4, 6, 8, 10]):
            self.eq(str(j), els[i].id)

        els = html['li:nth-child(2n-3)']
        expect = ['0', '2', '4', '6', '8', '10']
        self.count(len(expect), els)
        self.eq(expect, els.pluck('id'))

        sels = [
            'li:nth-child(5)',
        ]
        for sel in sels:
            els = html[sel]
            self.one(els)
            self.eq('4', els.first.id)

        els = html['li.my-class:nth-child(even)']
        self.one(els)
        self.eq('3', els.first.id)

        els = html['li.my-class:nth-child(odd)']
        self.zero(els)

        sels = [
            'li:nth-child(1n+0)',
            'li:nth-child(n+0)',
            'li:nth-child(N+0)',
            'li:nth-child(n)',
            'li:nth-child(N)',
        ]

        expect = [str(x) for x in range(12)]
        for sel in sels:
            els = html[sel]
            self.count(len(expect), els)
            self.eq(expect, els.pluck('id'))

        sels = [
            'li:nth-child(1n+3)',
            'li:nth-child(n+3)',
        ]

        expect = [str(x) for x in range(2,12)]
        for sel in sels:
            els = html[sel]
            self.count(len(expect), els)
            self.eq(expect, els.pluck('id'))

        sels = [
            'li:nth-child(-n+3)',
            'li:nth-child(-1n+3)',
        ]
        for sel in sels:
            sels = dom.selectors(sel)
            els = html[sel]
            self.three(els)
            for i in range(3):
                self.eq(str(i), els[i].id)

        sels = [
            'li:nth-child(-2n+3)',
        ]
        for sel in sels:
            sels = dom.selectors(sel)
            els = html[sel]
            self.two(els)
            self.eq('0', els.first.id)
            self.eq('2', els.second.id)

        sels = [
            'li:nth-child(-200n+3)',
        ]
        for sel in sels:
            sels = dom.selectors(sel)
            els = html[sel]
            self.one(els)
            self.eq('2', els.first.id)

        sels = [
            'li:nth-child(n+2):nth-child(-n+5)',
        ]
        for sel in sels:
            sels = dom.selectors(sel)
            els = html[sel]
            self.four(els)
            self.eq('1', els.first.id)
            self.eq('2', els.second.id)
            self.eq('3', els.third.id)
            self.eq('4', els.fourth.id)

        sels = [
            'li:nth-child(n+2):nth-child(odd):nth-child(-n+9)',
        ]
        expect = [str(x) for x in range(2, 10, 2)]
        for sel in sels:
            sels = dom.selectors(sel)
            els = html[sel]
            self.count(len(expect), els)
            self.eq(expect, els.pluck('id'))

        sels = [
            'li:nth-child(3n+1):nth-child(even)',
        ]
        expect = ['3', '9']
        for sel in sels:
            sels = dom.selectors(sel)
            els = html[sel]
            self.count(len(expect), els)
            self.eq(expect, els.pluck('id'))

    def it_selects_nth_last_child(self):
        html = self._listhtml

        # Selects every fourth element among any group of siblings,
        # counting backwards from the last one 
        sels = [
            'li:nth-last-child(4n)',
            'li:NTH-LAST-CHILD(4n)',
            'li:nth-last-child(4N)',
        ]

        expect = ['0', '4', '8']
        for sel in sels:
            els = html[sel]
            self.count(len(expect), els)
            self.eq(expect, els.pluck('id'))

        ''' last 2 rows '''
        sels = [
            'li:nth-last-child(-n+2)',
            'li:nth-last-child(-1n+2)'
        ]

        expect = ['10', '11']
        for sel in sels:
            els = html[sel]
            self.count(len(expect), els)
            self.eq(expect, els.pluck('id'))

        # Represents the odd rows of an HTML table: 1, 3, 5, etc.,
        # counting from the end.
        sels = [
            'li:nth-last-child(odd)',
            'li:nth-last-child(2n+1)',
        ]

        expect = [str(x) for x in range(1, 12, 2)]
        for sel in sels:
            els = html[sel]
            self.count(len(expect), els)
            self.eq(expect, els.pluck('id'))

        # Represents the even rows of an HTML table: 2, 4, 6, etc.,
        # counting from the end.
        sels = [
            'li:nth-last-child(even)',
            'li:nth-last-child(2n)',
        ]

        expect = [str(x) for x in range(0, 11, 2)]
        for sel in sels:
            els = html[sel]
            self.count(len(expect), els)
            self.eq(expect, els.pluck('id'))

        # Represents the seventh element, counting from the end.
        sels = [
            'li:nth-last-child(7)',
        ]

        expect = ['5']
        for sel in sels:
            els = html[sel]
            self.count(len(expect), els)
            self.eq(expect, els.pluck('id'))

        # Represents elements 5, 10, 15, etc., counting from the end.
        sels = [
            'li:nth-last-child(5n)',
        ]

        expect = ['2', '7']
        for sel in sels:
            els = html[sel]
            self.count(len(expect), els)
            self.eq(expect, els.pluck('id'))

        # Represents elements 4, 7, 10, 13, etc., counting from the end.
        sels = [
            'li:nth-last-child(3n+4)',
            'li:nth-last-child(3N+4)',
        ]

        expect = ['2', '5', '8']
        for sel in sels:
            els = html[sel]
            self.count(len(expect), els)
            self.eq(expect, els.pluck('id'))

        # Represents the last three elements among a group of siblings.
        sels = [
            'li:nth-last-child(-n+3)',
            'li:nth-last-child(-N+3)'
        ]

        expect = ['9', '10', '11']
        for sel in sels:
            els = html[sel]
            self.count(len(expect), els)
            self.eq(expect, els.pluck('id'))

        # Represents every <li> element among a group of siblings. This
        # is the same as a simple li selector. (Since n starts at zero,
        # while the last element begins at one, n and n+1 will both
        # select the same elements.)
        sels = [
            'li:nth-last-child(n)',
            'li:nth-last-child(n+1)',
            'li:nth-last-child(N+1)',

        ]
        expect = [str(x) for x in range(12)]
        for sel in sels:
            els = html[sel]
            self.eq(expect, els.pluck('id'))

        # Represents every <li> that is the first element among a group
        # of siblings, counting from the end. This is the same as the
        # :last-child selector.
        sels = [
            'li:nth-last-child(1)',
            'li:nth-last-child(0n+1)',
            'li:nth-last-child(0N+1)',
        ]
        expect = ['11']
        for sel in sels:
            els = html[sel]
            self.eq(expect, els.pluck('id'))

    def it_selects_nth_of_type(self):
        html = dom.html('''
		<section>
		   <h1>Words</h1>
		   <p>Little</p>
		   <p>Piggy</p>
		</section>
		''')

        els = html('p:nth-child(2)')
        self.one(els)
        self.eq('Little', els.first.elements.first.html)

        els = html('p:nth-of-type(2)')
        self.one(els)
        self.eq('Piggy', els.first.elements.first.html)

        els = html('p:NTH-OF-TYPE(2)')
        self.one(els)
        self.eq('Piggy', els.first.elements.first.html)


        html = dom.html('''
            <section>
               <h1>Words</h1>
               <h2>Words</h2>
               <p>Little</p>
               <p>Piggy</p>
            </section>
		''')

        els = html('p:nth-child(2)')
        self.zero(els)

        els = html('p:nth-of-type(2)')
        self.one(els)
        self.eq('Piggy', els.first.elements.first.html)

        # Take the ListHtml and replacing all the <ol> and its <li>s
        # with the same number of alternating <span>s and <div>s.
        html = dom.html(ListHtml)
        sec = html[0].children[0].children[0].children[0]
        ol = sec.children.first
        cnt = ol.children.count

        sec.elements.clear()

        for i in range(cnt):
            el = dom.div if i % 2 else dom.span
            el = el('This is item ' + str(i))
            el.id = str(i)
            sec.elements += el

        sels = [
            'span:nth-of-type(3)',
        ]

        for sel in sels:
            els = html[sel]
            self.one(els)
            self.eq('4', els.first.id)

        sels = [
            'span:nth-of-type(n+3)',
        ]
        expect = ['4', '6', '8', '10']
        for sel in sels:
            els = html[sel]
            self.count(len(expect), els)
            self.eq(expect, els.pluck('id'))

        sels = [
            'span:nth-of-type(-n+4)',
            'span:nth-of-type(-N+4)',
        ]

        expect = ['0', '2', '4', '6']
        for sel in sels:
            els = html[sel]
            self.count(len(expect), els)
            self.eq(expect, els.pluck('id'))

        sels = [
            'div:nth-of-type(-n+5)',
        ]

        expect = ['1', '3', '5', '7', '9']
        for sel in sels:
            els = html[sel]
            self.count(len(expect), els)
            self.eq(expect, els.pluck('id'))

        sels = [
            'span:nth-of-type(n+3):nth-of-type(-n+6)',
        ]

        expect = ['4', '6', '8', '10']
        for sel in sels:
            els = html[sel]
            self.count(len(expect), els)
            self.eq(expect, els.pluck('id'))

        sels = [
            'div:nth-of-type(n+1):nth-of-type(-n+3)',
        ]

        expect = ['1', '3', '5']
        for sel in sels:
            els = html[sel]
            self.count(len(expect), els)
            self.eq(expect, els.pluck('id'))

        sels = [
            'span:nth-of-type(n+3):nth-of-type(odd):nth-of-type(-n+6)',
        ]

        expect = ['4', '8']
        for sel in sels:
            els = html[sel]
            self.count(len(expect), els)
            self.eq(expect, els.pluck('id'))

        sels = [
            'div:nth-of-type(n+1):nth-of-type(even):nth-of-type(-n+3)',
        ]

        expect = ['3']
        for sel in sels:
            els = html[sel]
            self.count(len(expect), els)
            self.eq(expect, els.pluck('id'))

    def it_selects_nth_last_of_type(self):
        html = dom.html(ListHtml)

        sels = [
            'li:nth-last-of-type(2)',
            'li:NTH-LAST-OF-TYPE(2)',
        ]

        expect = ['10']
        for sel in sels:
            els = html[sel]
            self.count(len(expect), els)
            self.eq(expect, els.pluck('id'))

        html = dom.html('''
            <div>
                <span>This is a span.</span>
                <span>This is another span.</span>
                <em>This is emphasized.</em>
                <span>Wow, this span gets limed!!!</span>
                <s>This is struck through.</s>
                <span>Here is one last span.</span>
            </div>
        ''')

        sels = [
            'span:nth-last-of-type(2)',
        ]

        for sel in sels:
            els = html[sel]
            self.one(els)
            expect = 'Wow, this span gets limed!!!'
            self.eq(expect, els.first.elements.first.html)

    def it_selects_first_child(self):
        html = dom.html('''
            <body>
                <p id="1"> The last P before the note.</p>
                <div>
                    <p id="2"> The first P inside the note.</p>
                </div>
            </body>
        ''')

        els = html['p:first-child']
        self.two(els)
        self.eq('1', els.first.id)
        self.eq('2', els.second.id)

        els = html['p:FIRST-CHILD']
        self.two(els)
        self.eq('1', els.first.id)
        self.eq('2', els.second.id)

        html = dom.html('''
            <body>
                <p id="1"> The last P before the note.</p>
                <div class="note">
                    <h2> Note </h2>
                    <p> id="2" The first P inside the note.</p>
                </div>
            </body>
        ''')
        els = html['p:first-child']
        self.one(els)
        self.eq('1', els.first.id)
    
    def it_selects_last_child(self):
        html = dom.html('''
        <div>
            <p id="1">This text isn't selected.</p>
            <p id="2">This text is selected!</p>
        </div>

        <div>
            <p> id="3"This text isn't selected.</p>
            <h2 id="4">This text isn't selected: it's not a `p`.</h2>
        </div>
        ''')

        els = html['p:last-child']
        self.one(els)
        self.eq('2', els.first.id)

        els = html['p:LAST-CHILD']
        self.one(els)
        self.eq('2', els.first.id)

    def it_selects_first_of_type(self):
        html = dom.html('''
        <body>
            <h2 id="0">Heading</h2>
            <p id="1">Paragraph 1</p>
            <p id="2">Paragraph 2</p>
        </body>
        ''')

        els = html['p:first-of-type']
        self.one(els)
        self.eq('1', els.first.id)

        els = html['p:FIRST-OF-TYPE']
        self.one(els)
        self.eq('1', els.first.id)

        # https://developer.mozilla.org/en-US/docs/Web/CSS/:first-of-type
        html = dom.html('''
            <article>
                <div id="0">
                    This `div` is first!
                </div>
                <div>
                    This 
                    <span id="1">
                        nested `span` is first
                    </span>
                !
                </div>
                <div>
                    This 
                    <em id="2">
                        nested `em` is first
                    </em>
                    , but this 
                    <em>
                        nested `em` is last
                    </em>!
                </div>
                <div>
                    This 
                    <span id="3">
                        nested `span` gets styled
                    </span>!
                </div>
                <b id="4">
                    This `b` qualifies!
                </b>
                <div>
                    This is the final `div`.
                </div>
            </article>
        ''')

        els = html[':first-of-type']
        expect = [str(x) for x in range(5)]
        self.count(len(expect), els)
        self.eq(expect, els.pluck('id'))

        html = dom.html('''
        <dl>
            <dt id="0">gigogne</dt>
            <dd>
                <dl>
                    <dt id="1">fusée</dt>
                    <dd>multistage rocket</dd>
                    <dt>table</dt>
                    <dd>nest of tables</dd>
                </dl>
            </dd>
        </dl>
        ''')

        els = html['dt:first-of-type']
        expect = [str(x) for x in range(2)]
        self.count(len(expect), els)
        self.eq(expect, els.pluck('id'))

    def it_selects_last_of_type(self):
        html = dom.html('''
        <body>
            <h2>Heading</h2>
            <p>Paragraph 1</p>
            <p id="0">Paragraph 2</p>
        </body>
        ''')

        els = html['p:last-of-type']
        self.one(els)
        self.eq('0', els.first.id)

        els = html['p:LAST-OF-TYPE']
        self.one(els)
        self.eq('0', els.first.id)

        # https://developer.mozilla.org/en-US/docs/Web/CSS/:last-of-type
        html = dom.html('''
        <article>
            <div>This `div` is first.</div>
            <div>This <span id="0">nested `span` is last</span>!</div>
            <div>This <em>nested `em` is first</em>, but this
            <em id="1">nested `em` is last</em>!</div>
            <b id="2">This `b` qualifies!</b>
            <div id="3">This is the final `div`!</div>
        </article>
        ''')

        els = html[':last-of-type']
        expect = [str(x) for x in range(4)]
        self.count(len(expect), els)
        self.eq(expect, els.pluck('id'))

        html = dom.html('''
        <body>
            <div>
                <span>Corey,</span>
                <span>Yehuda,</span>
                <span>Adam,</span>
                <span id="0">Todd</span>
            </div>
            <div>
                <span>Jörn,</span>
                <span>Scott,</span>
                <span id="1">Timo,</span>
                <b>Nobody</b>
            </div>
        </body>
        ''')

        els = html['span:last-of-type']
        expect = [str(x) for x in range(2)]
        self.count(len(expect), els)
        self.eq(expect, els.pluck('id'))

    def it_selects_only_child(self):

        html = dom.html('''
        <div>
            <div id="0">
                I am an only child.
            </div>
        </div>
        <div>
            <div>
                I am the 1st sibling.
            </div>
            <div>
                I am the 2nd sibling.
            </div>
            <div>
                I am the 3rd sibling, 
                <div id="1">
                    but this is an only child.
                </div>
            </div>
        </div>
        ''')

        els = html[':only-child']
        expect = [str(x) for x in range(2)]
        self.count(len(expect), els)
        self.eq(expect, els.pluck('id'))

        els = html[':ONLY-CHILD']
        expect = [str(x) for x in range(2)]
        self.count(len(expect), els)
        self.eq(expect, els.pluck('id'))
        
        html = dom.html('''
        <body>

            <div><p id="0">This is a paragraph.</p></div>

            <div><span>This is a span.</span><p>This is a
            paragraph.</p></div>

        </body>
        ''')

        els = html[':only-child']
        expect = [str(x) for x in range(1)]
        self.count(len(expect), els)
        self.eq(expect, els.pluck('id'))

    def it_selects_only_of_type(self):
        sels = [
            ':only-of-type',
            ':ONLY-OF-TYPE',
            ':first-of-type:last-of-type'
            ':nth-of-type(1):nth-last-of-type(1)'
        ]

        html = dom.html('''
        <main>
            <div>I am `div` #1.</div>
            <p id="0">I am the only `p` among my siblings.</p>
            <div>I am `div` #2.</div>
            <div>I am `div` #3.
                <i id="1">I am the only `i` child.</i>
                <em>I am `em` #1.</em>
                <em>I am `em` #2.</em>
            </div>
        </main>
        ''')

        for sel in sels:
            els = html[sel]
            expect = [str(x) for x in range(2)]
            self.count(len(expect), els)
            self.eq(expect, els.pluck('id'))

        html = dom.html('''
        <body>

            <div><p id="0">This is a paragraph.</p></div>

            <div><p>This is a paragraph.</p><p>This is a
            paragraph.</p></div>

        </body>
        ''')

        for sel in sels:
            els = html[sel]
            expect = [str(x) for x in range(1)]
            self.count(len(expect), els)
            self.eq(expect, els.pluck('id'))

        html = dom.html('''
        <ul>
            <li id="0">I'm all alone!</li>
        </ul>  

        <ul>
            <li>We are together.</li>
            <li>We are together.</li>
            <li>We are together.</li>
        </ul>
        ''')

        for sel in sels:
            els = html[sel]
            expect = [str(x) for x in range(1)]
            self.count(len(expect), els)
            self.eq(expect, els.pluck('id'))

        html = dom.html('''
        <div>
          <p id="0">I'm the only paragraph element in this div.</p>  
          <ul id="1">
            <li>List Item</li>
            <li>List Item</li>
          </ul>  
        </div>

        <div>
          <p>There are multiple paragraphs inside this div.</p>  
          <p>Yes there are.</p>  
          <ul id="2">
            <li>List Item</li>
            <li>List Item</li>
          </ul>  
        </div>        
        ''')

        for sel in sels:
            els = html[sel]
            expect = [str(x) for x in range(3)]
            self.count(len(expect), els)
            self.eq(expect, els.pluck('id'))

        html = dom.html('''
        <main>
            <div>
              <p id="0">I'm the only paragraph element in this div.</p>  
              <ul id="1">
                <li>List Item</li>
                <li>List Item</li>
              </ul>  
            </div>

            <div>
              <p>There are multiple paragraphs inside this div.</p>  
              <p>Yes there are.</p>  
              <ul id="2">
                <li>List Item</li>
                <li>List Item</li>
              </ul>  
            </div> 
        </main>
        ''')

        for sel in sels:
            els = html[sel]
            expect = [str(x) for x in range(3)]
            self.count(len(expect), els)
            self.eq(expect, els.pluck('id'))

    def it_selects_empty(self):
        html = dom.html('''
        <main>
            <div id="0"><!-- I am empty. --></div>

            <div>I am not empty.</div>

            <div>
                <!-- I am empty despite the whitespace around this comment. -->
            </div>

            <div>
                <p id="1"><!-- This <p> is empty though its parent <div> is not.--></p>
            </div>
        </main>
        ''')

        els = html[':empty']
        expect = [str(x) for x in range(2)]
        self.count(len(expect), els)
        self.eq(expect, els.pluck('id'))

        els = html[':EMPTY']
        expect = [str(x) for x in range(2)]
        self.count(len(expect), els)
        self.eq(expect, els.pluck('id'))

        html = dom.html('''
        <main>
            <div id="0"></div>
            <div id="1"><!-- test --></div>
        </main>
        ''')

        els = html[':empty']
        expect = [str(x) for x in range(2)]
        self.count(len(expect), els)
        self.eq(expect, els.pluck('id'))

        html = dom.html('''
        <main>
            <div> </div>

            <div>
                <!-- test -->
            </div>

            <div>
            </div>
        </main>
        ''')

        els = html[':empty']
        self.zero(els)

    def it_selects_not(self):
        ''' Elements '''
        # Select all elements that aren't <div>s 
        sels = [
            ':not(div)',
            ':NOT(div)',
            '*:not(div)',
        ]

        for sel in sels:
            els = self._shakespear[sel]
            self.six(els)
            self.false(dom.div in [type(x) for x in els])

        ''' Classes '''
        # Select all elements that don't have the 'dialog' class
        sels = [
            ':not(.dialog)',
            '*:not(.dialog)',
            ':not(*.dialog)',
        ]
        for sel in sels:
            els = self._shakespear[sel]
            self.count(198, els)
            for el in els:
                self.false('dialog' in el.classes)

        sels = [
            'div:not(.dialog)',
            'div:not(div.dialog)',
        ]

        ''' Attributes '''
        for sel in sels:
            els = self._shakespear[sel]
            self.count(192, els)
            for el in els:
                self.false('dialog' in el.classes)
            self.all([type(x) is dom.div for x in els])

        sels = [
            'div:not([title=wtf])',
            'div:not(div[title=wtf])',
            'div:not(DIV[TITLE=wtf])',
        ]

        for sel in sels:
            els = self._shakespear[sel]
            self.count(242, els)
            self.all(el.title != 'wtf' for el in els)

        ''' Pseudoclasses '''
        # Select all odd (not even) li's

        # FIXME This selects correctly but there is an issue with the
        # parsing (ref dd6a4f93)
        # els = self._listhtml['li:not(li:nth-child(even))']
        # expect = list(range(0, 11, 2))
        # self.count(len(expect), els)
        # self.eq(expect, [int(x.id) for x in els])

        ''' Chained '''
        sels = [
            ':not(.dialog):not(h2)',
            '*:not(.dialog):not(h2)',
            '*:not(*.dialog):not(h2)',
            '*:not(*.dialog):not(H2)',
        ]

        for sel in sels:
            els = self._shakespear[sel]
            self.count(197, els)
            self.all(type(x) is not dom.h2 for x in els)
            self.all('dialog' not in x.classes for x in els)

        ''' Identity '''
        sels = [
            'div:not(#speech16)',
            'div:not(div#speech16)',
            'div:not(*#speech16)',
        ]

        for sel in sels:
            els = self._shakespear[sel]
            self.count(242, els)
            self.all(el.id != 'speech16' for el in els)

    def it_selects_with_id(self):
        html = self._shakespear
        sels = [
            '*#speech16',
            'div#speech16',
            '#speech16',
        ]

        for sel in sels:
            self.zero(html[sel.upper()])
            els = self._shakespear[sel]
            self.one(els)
            self.eq('speech16', els.first.id)

        sels = [
            '*#idontexist',
            'div#idontexist',
            '#idontexist',
        ]

        for sel in sels:
            els = html[sel]
            self.zero(els)

    def it_parses_combinators(self):
        def space(s):
            return re.sub(r'(\S)([~\+>])(\S)', r'\1 \2 \3', s)

        sub         =  dom.selector.element.SubsequentSibling
        next        =  dom.selector.element.NextSibling
        child       =  dom.selector.element.Child
        desc        =  dom.selector.element.Descendant

        ''' sub desc next '''
        sels = [
            'div ~ div p + q',
            'div~div p+q',
        ]
        for sel in sels:
            expect = space(sel)
            sels = dom.selectors(sel)
            self.eq(expect, repr(sels))
            self.eq(expect, str(sels))

            self.four(sels.first.elements)
            self.eq(None, sels.first.elements.first.combinator)
            self.eq(sub, sels.first.elements.second.combinator)
            self.eq(desc, sels.first.elements.third.combinator)
            self.eq(next, sels.first.elements.fourth.combinator)

        ''' Subsequent-sibling combinator '''
        sels = [
           'body ~ div',
           'body~div',
           'body.my-class ~ div.my-class',
           'body[foo=bar] ~ div[foo=bar]',
        ]

        for sel in sels:
            expect = space(sel)
            sels = dom.selectors(sel)
            self.eq(expect, repr(sels))
            self.eq(expect, str(sels))
            self.two(sels.first.elements)
            self.eq(None, sels.first.elements.first.combinator)
            self.eq(sub, sels.first.elements.second.combinator)

        sels = [
           'body div ~ p',
           'body div~p',
           'body.my-class div.my-class ~ p.my-class',
           'body.my-class div.my-class~p.my-class',
           'body[foo=bar] div[foo=bar]~p.my-class',
        ]

        for sel in sels:
            sels = dom.selectors(sel)
            self.eq(space(sel), repr(sels))
            self.eq(space(sel), str(sels))
            self.three(sels.first.elements)
            self.eq(None, sels.first.elements.first.combinator)
            self.eq(desc, sels.first.elements.second.combinator)
            self.eq(sub, sels.first.elements.third.combinator)

        ''' Next-sibling combinator '''
        sels = [
           'body + div',
           'body+div',

           'body.my-class + div.my-class',
           'body.my-class+div.my-class',

           'body[foo=bar] + div[foo=bar]',
           'body[foo=bar]+div[foo=bar]',
        ]

        for sel in sels:
            sels = dom.selectors(sel)
            self.eq(space(sel), repr(sels))
            self.eq(space(sel), str(sels))
            self.two(sels.first.elements)
            self.eq(None, sels.first.elements.first.combinator)
            self.eq(next, sels.first.elements.second.combinator)

        sels = [
           'body div+p',
           'body div + p',

           'body.my-class div.my-class + p.my-class',
           'body.my-class div.my-class+p.my-class',

           'body[foo=bar] div[foo=bar] + p.my-class',
           'body[foo=bar] div[foo=bar]+p.my-class',
        ]

        for sel in sels:
            sels = dom.selectors(sel)
            self.eq(space(sel), repr(sels))
            self.eq(space(sel), str(sels))
            self.three(sels.first.elements)
            self.eq(None, sels.first.elements.first.combinator)
            self.eq(desc, sels.first.elements.second.combinator)
            self.eq(next, sels.first.elements.third.combinator)

        ''' Child combinator '''
        sels = [
           'body > div',
           'body>div',

           'body.my-class>div.my-class',

           'body[foo=bar] > div[foo=bar]',
           'body[foo=bar]>div[foo=bar]',
        ]

        for sel in sels:
            sels = dom.selectors(sel)
            self.eq(space(sel), repr(sels))
            self.eq(space(sel), str(sels))
            self.two(sels.first.elements)
            self.eq(None, sels.first.elements.first.combinator)
            self.eq(child, sels.first.elements.second.combinator)

        sels = [
           'body > div > p',
           'body>div>p',

           'body.my-class > div.my-class > p.my-class',
           'body.my-class>div.my-class>p.my-class',

           'body[foo=bar] > div[foo=bar] > p.my-class',
           'body[foo=bar]>div[foo=bar]>p.my-class',
        ]

        for sel in sels:
            sels = dom.selectors(sel)
            self.eq(space(sel), repr(sels))
            self.eq(space(sel), str(sels))
            self.three(sels.first.elements)
            self.eq(None, sels.first.elements.first.combinator)
            self.eq(child, sels.first.elements.second.combinator)
            self.eq(child, sels.first.elements.third.combinator)

        sels = [
           'body div > p',
           'body div>p',

           'body.my-class div.my-class > p.my-class',
           'body.my-class div.my-class>p.my-class',

           'body[foo=bar] div[foo=bar] > p.my-class',
           'body[foo=bar] div[foo=bar]>p.my-class',
        ]

        for sel in sels:
            sels = dom.selectors(sel)
            self.eq(space(sel), repr(sels))
            self.eq(space(sel), str(sels))
            self.three(sels.first.elements)
            self.eq(None, sels.first.elements.first.combinator)
            self.eq(desc, sels.first.elements.second.combinator)
            self.eq(child, sels.first.elements.third.combinator)

        sels = [
           'body > div p',
           'body>div p',

           'body.my-class > div.my-class p.my-class',
           'body.my-class>div.my-class p.my-class',

           'body[foo=bar] > div[foo=bar] p.my-class',
           'body[foo=bar]>div[foo=bar] p.my-class',
        ]

        for sel in sels:
            sels = dom.selectors(sel)
            self.eq(space(sel), repr(sels))
            self.eq(space(sel), str(sels))
            self.three(sels.first.elements)
            self.eq(None, sels.first.elements.first.combinator)
            self.eq(child, sels.first.elements.second.combinator)
            self.eq(desc, sels.first.elements.third.combinator)

        ''' Descendant combinator '''
        sels = [
           'body div',
           'body.my-class div.my-class',
           'body[foo=bar] div[foo=bar]',
        ]

        for sel in sels:
            sels = dom.selectors(sel)
            self.eq(sel, repr(sels))
            self.eq(sel, str(sels))
            self.two(sels.first.elements)
            self.eq(None, sels.first.elements.first.combinator)
            self.eq(desc, sels.first.elements.second.combinator)

        sels = [
           'body div p',
           'body.my-class div.my-class p.my-class',
           'body[foo=bar] div[foo=bar] p[foo=bar]',
        ]

        for sel in sels:
            sels = dom.selectors(sel)
            self.eq(sel, repr(sels))
            self.eq(sel, str(sels))
            self.three(sels.first.elements)
            self.eq(None, sels.first.elements.first.combinator)
            self.eq(desc, sels.first.elements.second.combinator)
            self.eq(desc, sels.first.elements.third.combinator)

    def it_parses_chain_of_elements(self):
        ''' One '''
        sels = dom.selectors('E')
        self.repr('E', sels)
        self.str('E', sels)
        self.one(sels)
        els = sels.first.elements
        self.one(els)
        self.eq(['E'], els.pluck('element'))

        desc = dom.selector.element.Descendant
        self.none(els.first.combinator)

        ''' Two '''
        sels = dom.selectors('E F')
        self.repr('E F', sels)
        self.str('E F', sels)
        self.one(sels)
        els = sels.first.elements
        self.two(els)
        self.eq(['E', 'F'], els.pluck('element'))

        desc = dom.selector.element.Descendant
        self.none(els.first.combinator)
        self.eq(desc, els.second.combinator)
        self.repr('E F', sels)
        self.str('E F', sels)

        ''' Three '''
        sels = dom.selectors('E F G')
        self.repr('E F G', sels)
        self.str('E F G', sels)
        self.one(sels)
        els = sels.first.elements
        self.three(els)
        self.eq(['E', 'F', 'G'], els.pluck('element'))

        desc = dom.selector.element.Descendant
        self.none(els.first.combinator)
        self.eq(desc, els.second.combinator)
        self.eq(desc, els.third.combinator)
        self.repr('E F G', sels)
        self.str('E F G', sels)

    def it_parses_chain_of_elements_and_classes(self):
        ''' element to class '''
        sels = [
            'div .dialog',
            'div *.dialog',
            'div div.dialog',
        ]

        for i, sel in enumerate(sels):
            sel = dom.selectors(sel)
            self.eq('div',  sel.first.elements.first.element)
            if i.last:
                self.eq('div',  sel.first.elements.second.element)
            else:
                self.eq('*',  sel.first.elements.second.element)
            self.eq(
                'dialog', sel.first.elements.second.classes.first.value
            )

        ''' Class to element '''
        sels = [
            '.dialog div',
            '*.dialog div',
            'div.dialog div',
        ]

        for i, sel in enumerate(sels):
            sel = dom.selectors(sel)
            self.eq('div',  sel.first.elements.second.element)
            if i.last:
                self.eq('div',  sel.first.elements.first.element)
            else:
                self.eq('*',  sel.first.elements.first.element)

            self.eq(
                'dialog', sel.first.elements.first.classes.first.value
            )

    def it_parses_chain_of_elements_and_pseudoclasses(self):
        ''' Element to pseudoclasses '''
        sels = [
            'div :not(p)',
            'div *:not(p)',
            'div div:not(p)',
        ]

        for i, sel in enumerate(sels):
            sel = dom.selectors(sel)
            self.eq('div',  sel.first.elements.first.element)
            if i.last:
                self.eq('div',  sel.first.elements.second.element)
            else:
                self.eq('*',  sel.first.elements.second.element)
            self.eq(
                'not', sel.first.elements.second.pseudoclasses.first.value
            )

        ''' Element to pseudoclasses '''
        sels = [
            ':not(p) div',
            '*:not(p) div',
            'div:not(p) div',
        ]

        for i, sel in enumerate(sels):
            sel = dom.selectors(sel)
            self.eq('div',  sel.first.elements.second.element)
            if i.last:
                self.eq('div',  sel.first.elements.first.element)
            else:
                self.eq('*',  sel.first.elements.first.element)
            self.eq(
                'not', sel.first.elements.first.pseudoclasses.first.value
            )

    def it_parses_chain_of_elements_and_attributes(self):
        ''' Element to attribute '''
        sels = [
            'div [foo=bar]',
            'div *[foo=bar]',
            'div p[foo=bar]',
        ]

        for i, sel in enumerate(sels):
            sel = dom.selectors(sel)
            self.eq('div',  sel.first.elements.first.element)
            if i.last:
                self.eq('p',  sel.first.elements.second.element)
            else:
                self.eq('*',  sel.first.elements.second.element)
            self.eq(
                'foo', sel.first.elements.second.attributes.first.key
            )

            self.eq(
                'bar', sel.first.elements.second.attributes.first.value
            )

        sels = [
            '[foo=bar] div',
            '*[foo=bar] div',
            'p[foo=bar] div',
        ]

        ''' Attribute to element '''
        for i, sel in enumerate(sels):
            sel = dom.selectors(sel)
            self.eq('div',  sel.first.elements.second.element)
            if i.last:
                self.eq('p',  sel.first.elements.first.element)
            else:
                self.eq('*',  sel.first.elements.first.element)
            self.eq(
                'foo', sel.first.elements.first.attributes.first.key
            )

            self.eq(
                'bar', sel.first.elements.first.attributes.first.value
            )

    def it_parses_chain_of_elements_and_identifiers(self):
        ''' Element to identifier '''
        sels = [
            'div #my-id',
            'div *#my-id',
            'div p#my-id',
        ]

        for i, sel in enumerate(sels):
            sel = dom.selectors(sel)
            self.eq('div',  sel.first.elements.first.element)
            if i.last:
                self.eq('p',  sel.first.elements.second.element)
            else:
                self.eq('*',  sel.first.elements.second.element)

            self.eq(
                'my-id', sel.first.elements.second.id
            )

        ''' Identitifier to element '''
        sels = [
            '#my-id div',
            '*#my-id div',
            'p#my-id div',
        ]

        for i, sel in enumerate(sels):
            sel = dom.selectors(sel)
            self.eq('div',  sel.first.elements.second.element)
            if i.last:
                self.eq('p',  sel.first.elements.first.element)
            else:
                self.eq('*',  sel.first.elements.first.element)

            self.eq(
                'my-id', sel.first.elements.first.id
            )

    def it_parses_attribute_elements(self):
        sels = 'E[foo=bar] F[qux="quux"] G[garply=waldo]'
        expect = 'E[foo=bar] F[qux=quux] G[garply=waldo]'
        sels = dom.selectors(sels)
        self.repr(expect, sels)
        self.str(expect, sels)
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
        expect = 'E[foo~=bar] F[qux^=quux] G[garply$=waldo]'
        sels = dom.selectors(sels)
        self.repr(expect, sels)
        self.str(expect, sels)
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
        expect = 'E[foo=bar][qux=quux] F[garply=waldo][foo=bar]'
        sels = dom.selectors(sels)
        self.repr(expect, sels)
        self.str(expect, sels)
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

        sels = 'E[foo*=bar]'
        expect = 'E[foo*=bar]'
        sels = dom.selectors(sels)
        self.repr(expect, sels)
        self.str(expect, sels)
        self.one(sels)
        sel = sels.first

        el = sel.elements.first
        self.eq('E', el.element)
        self.one(el.attributes)
        attr = el.attributes.first
        self.eq('foo', attr.key)
        self.eq('*=', attr.operator)
        self.eq('bar', attr.value)

        sels = 'E[foo*=bar] F[baz|=qux]'
        expect = 'E[foo*=bar] F[baz|=qux]'
        sels = dom.selectors(sels)
        self.repr(expect, sels)
        self.str(expect, sels)
        self.one(sels)
        sel = sels.first

        self.two(sel.elements)
        el = sel.elements.first
        self.eq('E', el.element)
        self.one(el.attributes)
        attr = el.attributes.first
        self.eq('foo', attr.key)
        self.eq('*=', attr.operator)
        self.eq('bar', attr.value)

        el = sel.elements.second
        self.eq('F', el.element)
        self.one(el.attributes)
        attr = el.attributes.first
        self.eq('baz', attr.key)
        self.eq('|=', attr.operator)
        self.eq('qux', attr.value)

        sels = '[disabled]'
        sels = dom.selectors(sels)
        self.repr('*[disabled]', sels)
        self.str('*[disabled]', sels)
        self.one(sels)
        sel = sels.first

        self.one(sel.elements)
        el = sel.elements.first
        self.eq('*', el.element)
        self.one(el.attributes)
        attr = el.attributes.first
        self.eq('disabled', attr.key)
        self.none(attr.operator)
        self.none(attr.value)

        sels = [
            "E[foo='bar baz']",
            'E[foo="bar baz"]',
        ]

        for sel in sels:
            sels = dom.selectors(sel)
            expect = 'E[foo=bar baz]'
            self.repr(expect, sels)
            self.str(expect, sels)
            self.one(sels)
            sel = sels.first
            self.one(sel.elements)
            self.one(sel.elements.first.attributes)
            self.eq('foo', sel.elements.first.attributes.first.key)
            self.eq(
                'bar baz', 
                sel.elements.first.attributes.first.value
            )

    def it_parses_class_elements(self):
        ''' E.warning '''
        sels = expect = 'E.warning'
        sels = dom.selectors(sels)
        self.str(expect, sels)
        self.repr(expect, sels)
        self.one(sels)
        self.one(sels.first.elements)
        self.type(dom.selector.element, sels.first.elements.first)
        self.eq('E', sels.first.elements.first.element)
        self.one(sels.first.elements.first.classes)
        self.type(
          dom.selector.class_,
          sels.first.elements.first.classes.first
        )
        self.eq(
          'warning', 
          sels.first.elements.first.classes.first.value
        )

        ''' E.warning F.danger '''
        sels = expect = 'E.warning F.danger'
        sels = dom.selectors(sels)
        self.str(expect, sels)
        self.repr(expect, sels)
        self.one(sels)
        self.two(sels.first.elements)

        e = sels.first.elements.first
        self.type(dom.selector.element, e)
        self.eq('E', e.element)
        self.one(e.classes)
        self.type(dom.selector.class_, e.classes.first)
        self.eq('warning', e.classes.first.value)

        e = sels.first.elements.second
        self.type(dom.selector.element, e)
        self.eq('F', e.element)
        self.one(e.classes)
        self.type(dom.selector.class_, e.classes.first)
        self.eq('danger', e.classes.first.value)

        ''' E.warning.danger '''
        sels = expect = 'E.warning.danger'
        sels = dom.selectors(sels)
        self.str(expect, sels)
        self.repr(expect, sels)
        self.one(sels)
        self.one(sels.first.elements)

        e = sels.first.elements.first
        self.type(dom.selector.element, e)
        self.eq('E', e.element)
        self.two(e.classes)
        self.type(dom.selector.class_, e.classes.first)
        self.type(dom.selector.class_, e.classes.second)
        self.eq('warning', e.classes.first.value)
        self.eq('danger', e.classes.second.value)

        ''' E.warning.danger.fire '''
        sels = expect = 'E.warning.danger.fire'
        sels = dom.selectors(sels)
        self.str(expect, sels)
        self.repr(expect, sels)
        self.one(sels)
        self.one(sels.first.elements)

        e = sels.first.elements.first
        self.type(dom.selector.element, e)
        self.eq('E', e.element)
        self.three(e.classes)
        self.type(dom.selector.class_, e.classes.first)
        self.type(dom.selector.class_, e.classes.second)
        self.eq('warning', e.classes.first.value)
        self.eq('danger', e.classes.second.value)
        self.eq('fire', e.classes.third.value)

        ''' E.warning.danger.fire F.primary.secondary.success'''
        sels = expect = 'E.warning.danger.fire F.primary.secondary.success'
        sels = dom.selectors(sels)
        self.str(expect, sels)
        self.repr(expect, sels)
        self.one(sels)
        self.two(sels.first.elements)

        e = sels.first.elements.first
        self.type(dom.selector.element, e)
        self.eq('E', e.element)
        self.three(e.classes)
        self.type(dom.selector.class_, e.classes.first)
        self.type(dom.selector.class_, e.classes.second)
        self.eq('warning', e.classes.first.value)
        self.eq('danger', e.classes.second.value)
        self.eq('fire', e.classes.third.value)

        e = sels.first.elements.second
        self.type(dom.selector.element, e)
        self.eq('F', e.element)
        self.three(e.classes)
        self.type(dom.selector.class_, e.classes.first)
        self.type(dom.selector.class_, e.classes.second)
        self.eq('primary', e.classes.first.value)
        self.eq('secondary', e.classes.second.value)
        self.eq('success', e.classes.third.value)

    def it_parses_id_elements(self):
        eid = 'x' + uuid4().hex
        fid = 'x' + uuid4().hex
        gid = 'x' + uuid4().hex

        ''' E#id '''
        sels = expect = 'E#' + eid
        sels = dom.selectors(sels)
        self.str(expect, sels)
        self.repr(expect, sels)
        self.one(sels)
        self.one(sels.first.elements)

        e = sels.first.elements.first
        self.eq(eid, e.id)

        ''' E#id F#id'''
        sels = expect = 'E#%s F#%s' % (eid, fid)
        sels = dom.selectors(sels)
        self.str(expect, sels)
        self.repr(expect, sels)
        self.one(sels)
        self.two(sels.first.elements)

        e = sels.first.elements.first
        self.eq(eid, e.id)

        f = sels.first.elements.second
        self.eq(fid, f.id)

        ''' E#id F#id G#id'''
        sels = expect = 'E#%s F#%s G#%s' % (eid, fid, gid)
        sels = dom.selectors(sels)
        self.str(expect, sels)
        self.repr(expect, sels)
        self.one(sels)
        self.three(sels.first.elements)

        e = sels.first.elements.first
        self.eq(eid, e.id)

        f = sels.first.elements.second
        self.eq(fid, f.id)

        g = sels.first.elements.third
        self.eq(gid, g.id)

    def it_parses_nth_child(self):
        ''' E:first-child '''
        sels = 'E:first-child'
        sels = dom.selectors(sels)
        expect = 'E:first-child' 
        self.str(expect, sels)
        self.repr(expect, sels)
        self.one(sels)
        self.one(sels.first.elements)

        e = sels.first.elements.first
        self.eq('E', e.element)
        self.eq('first-child', e.pseudoclasses.first.value)

        '''E:first-child F:last-child'''
        sels = 'E:first-child F:last-child'
        sels = dom.selectors(sels)
        self.str('E:first-child F:last-child', sels)
        self.repr('E:first-child F:last-child', sels)
        self.one(sels)
        self.two(sels.first.elements)

        e = sels.first.elements.first
        self.eq('E', e.element)
        self.eq('first-child', e.pseudoclasses.first.value)

        f = sels.first.elements.second
        self.eq('F', f.element)
        self.eq('last-child', f.pseudoclasses.first.value)

    def it_parses_pseudoclass(self):
        ''' E:empty'''
        sels = 'E:empty'
        sels = dom.selectors(sels)
        self.one(sels)
        self.one(sels.first.elements)

        self.str('E:empty', sels)
        self.repr('E:empty', sels)

        pclss = sels.first.elements.first.pseudoclasses

        self.one(pclss)
        self.type(dom.selector.pseudoclasses, pclss)
        pcls = pclss.first
        self.type(dom.selector.pseudoclass, pcls)
        self.eq('empty', pcls.value)

    def it_parses_chained_pseudoclass(self):
        ''' E:empty:root'''
        sels = 'E:empty:root'
        sels = dom.selectors(sels)
        self.one(sels)
        self.one(sels.first.elements)

        self.str('E:empty:root', sels)
        self.repr('E:empty:root', sels)

        pclss = sels.first.elements.first.pseudoclasses

        self.two(pclss)
        self.type(dom.selector.pseudoclasses, pclss)

        pcls = pclss.first
        self.type(dom.selector.pseudoclass, pcls)
        self.eq('empty', pcls.value)

        pcls = pclss.second
        self.type(dom.selector.pseudoclass, pcls)
        self.eq('root', pcls.value)
        
    def it_parses_chained_argumentative_pseudo_classes(self):
        ''' E:nth-child(odd):nth-child(even) '''
        sels = 'E:nth-child(odd):nth-child(even)'
        sels = dom.selectors(sels)
        self.one(sels)
        self.one(sels.first.elements)
        self.str('E:nth-child(2n+1):nth-child(2n+0)', sels)
        self.repr('E:nth-child(2n+1):nth-child(2n+0)', sels)

    def it_parses_argumentative_pseudo_classes(self):
        ''' E:nth-child(odd) '''
        sels = 'E:nth-child(odd)'
        sels = dom.selectors(sels)
        self.one(sels)
        self.one(sels.first.elements)
        self.str('E:nth-child(2n+1)', sels)
        self.repr('E:nth-child(2n+1)', sels)

        e = sels.first.elements.first
        self.eq('E', e.element)
        self.eq('nth-child', e.pseudoclasses.first.value)
        self.eq(2, e.pseudoclasses.first.arguments.a)
        self.eq(1, e.pseudoclasses.first.arguments.b)

        ''' E:nth-child(even) '''
        sels = 'E:nth-child(even)'
        sels = dom.selectors(sels)
        self.one(sels)
        self.one(sels.first.elements)
        self.str('E:nth-child(2n+0)', sels)
        self.repr('E:nth-child(2n+0)', sels)

        e = sels.first.elements.first
        self.eq('E', e.element)
        self.eq('nth-child', e.pseudoclasses.first.value)
        self.eq(2, e.pseudoclasses.first.arguments.a)
        self.eq(0, e.pseudoclasses.first.arguments.b)

        ''' E:nth-child(2n + 1)'''
        sels = 'E:nth-child(2n + 1)'
        sels = dom.selectors(sels)
        self.str('E:nth-child(2n+1)', sels)
        self.repr('E:nth-child(2n+1)', sels)
        self.one(sels)
        self.one(sels.first.elements)

        e = sels.first.elements.first
        self.eq('E', e.element)
        self.eq('nth-child', e.pseudoclasses.first.value)
        self.eq(2, e.pseudoclasses.first.arguments.a)
        self.eq(1, e.pseudoclasses.first.arguments.b)

        '''foo:nth-child(0n + 5)'''
        sels = [
          'foo:nth-child(0n + 5)',
          'foo:nth-child(5)',
        ]

        for sel in sels:
            sels = dom.selectors(sel)
            self.str('foo:nth-child(0n+5)', sels)
            self.repr('foo:nth-child(0n+5)', sels)
            self.one(sels)
            self.one(sels.first.elements)


            e = sels.first.elements.first
            self.eq('foo', e.element)
            self.eq('nth-child', e.pseudoclasses.first.value)
            self.notnone(e.pseudoclasses.first.arguments)
            self.eq(0, e.pseudoclasses.first.arguments.a)
            self.eq(5, e.pseudoclasses.first.arguments.b)

        ''' E:nth-child(10n - 1)'''
        sels = 'E:nth-child(10n - 1)'
        sels = dom.selectors(sels)
        self.str('E:nth-child(10n-1)', sels)
        self.repr('E:nth-child(10n-1)', sels)
        self.one(sels)
        self.one(sels.first.elements)
        e = sels.first.elements.first

        self.eq(e.element, 'E')
        self.eq(e.pseudoclasses.first.value, 'nth-child')
        self.eq(10, e.pseudoclasses.first.arguments.a)
        self.eq(-1, e.pseudoclasses.first.arguments.b)

        sels = [
            'E:nth-child(n)',
            'E:nth-child(1n + 0)',
            'E:nth-child(n + 0)',
        ]

        for i, sel in enumerate(sels):
            sels = dom.selectors(sel)
            self.str('E:nth-child(1n+0)', sels, 'For: ' + sel)
            self.repr('E:nth-child(1n+0)', sels, 'For: ' + sel)
            args = sels.first.elements.first.pseudoclasses.first.arguments
            self.eq(1, args.a)
            self.eq(0, args.b)

        sels = [
            'E:nth-child(-n)',
            'E:nth-child(-1n + 0)',
        ]

        sels = [
            'E:nth-child(-n + 0)',
        ]

        for i, sel in enumerate(sels):
            sels = dom.selectors(sel)
            self.str('E:nth-child(-1n+0)', sels, 'For: ' + sel)
            self.repr('E:nth-child(-1n+0)', sels, 'For: ' + sel)
            args = sels.first.elements.first.pseudoclasses.first.arguments
            self.eq(-1, args.a)
            self.eq(0, args.b)

        sels = [
            'E:nth-child(2n)',
            'E:nth-child(2n + 0)',
        ]

        for sel in sels:
            sels = dom.selectors(sel)
            self.str('E:nth-child(2n+0)', sels, 'For: ' + sel)
            self.repr('E:nth-child(2n+0)', sels, 'For: ' + sel)
            args = sels.first.elements.first.pseudoclasses.first.arguments
            self.eq(2, args.a)
            self.eq(0, args.b)

        sel = 'E:nth-child( 3n + 1 )'
        sels = dom.selectors(sel)
        self.str('E:nth-child(3n+1)', sels)
        self.repr('E:nth-child(3n+1)', sels)
        args = sels.first.elements.first.pseudoclasses.first.arguments
        self.eq(3, args.a)
        self.eq(1, args.b)

        sel =  'E:nth-child( +3n - 2 )'
        sels = dom.selectors(sel)
        self.str('E:nth-child(3n-2)', sels)
        self.repr('E:nth-child(3n-2)', sels)
        args = sels.first.elements.first.pseudoclasses.first.arguments
        self.eq(3, args.a)
        self.eq(-2, args.b)

        sel =  'E:nth-child( -n+ 6)'
        sels = dom.selectors(sel)
        self.str('E:nth-child(-1n+6)', sels)
        self.repr('E:nth-child(-1n+6)', sels)
        args = sels.first.elements.first.pseudoclasses.first.arguments
        self.eq(-1, args.a)
        self.eq(6, args.b)

        sel = 'E:nth-child( +6 )'
        sels = dom.selectors(sel)
        self.str('E:nth-child(0n+6)', sels)
        self.repr('E:nth-child(0n+6)', sels)
        args = sels.first.elements.first.pseudoclasses.first.arguments
        self.eq(0, args.a)
        self.eq(6, args.b)

    def it_parses_lang_pseudoclass(self):
        # Helpful explaination:
        #     https://bitsofco.de/use-the-lang-pseudo-class-over-the-lang-attribute-for-language-specific-styles/

        sel =  'E:lang(fr)'
        sels = dom.selectors(sel)
        self.repr('E:lang(fr)', sels)
        self.str('E:lang(fr)', sels)
        args = sels.first.elements.first.pseudoclasses.first.arguments
        self.none(args.a)
        self.none(args.b)
        self.eq('fr', args.c)

        sel =  'E:lang(fr-be)'
        sels = dom.selectors(sel)
        self.repr('E:lang(fr-be)', sels)
        self.str('E:lang(fr-be)', sels)
        args = sels.first.elements.first.pseudoclasses.first.arguments
        self.none(args.a)
        self.none(args.b)
        self.eq('fr-be', args.c)

    def it_parses_universal_selector(self):
        sels = dom.selectors('*')
        self.str('*', sels)
        self.repr('*', sels)
        self.eq('*', sels.first.elements.first.element)

        sels = dom.selectors('*[foo=bar]')
        el = sels.first.elements.first
        self.eq('*', el.element)
        self.one(el.attributes)
        attr = el.attributes.first
        self.eq('foo', attr.key)
        self.eq('=', attr.operator)
        self.eq('bar', attr.value)

        sels = expect = '*.warning'
        sels = dom.selectors(sels)
        self.repr(expect, sels)
        self.str(expect, sels)
        self.one(sels)
        self.one(sels.first.elements)
        self.type(dom.selector.element, sels.first.elements.first)
        self.eq('*', sels.first.elements.first.element)
        self.one(sels.first.elements.first.classes)
        self.type(
          dom.selector.class_,
          sels.first.elements.first.classes.first
        )
        self.eq(
          'warning', 
          sels.first.elements.first.classes.first.value
        )

        eid = 'x' + uuid4().hex
        sels = expect = '*#' + eid
        sels = dom.selectors(sels)
        self.one(sels)
        self.one(sels.first.elements)
        self.repr(expect, sels)
        self.str(expect, sels)
        el = sels.first.elements.first
        self.eq('*', el.element)
        self.eq(eid, el.id)

        # Pseudoclasses
        sels = dom.selectors('*:root')
        el = sels.first.elements.first
        self.eq('*', el.element)
        self.one(el.pseudoclasses)
        self.eq('root', el.pseudoclasses.first.value)

        # Combine: *#1234 *.warning *.[foo=bar] *:root
        eid = 'x' + uuid4().hex
        expect = '*#' + eid
        expect += ' *.warning'
        expect += ' *[foo=bar]'
        expect += ' *:root'
        sels = dom.selectors(expect)
        self.repr(expect, sels)
        self.str(expect, sels)
        self.one(sels)
        self.four(sels.first.elements)

        el = sels.first.elements.first
        self.eq('*', el.element)
        self.eq(eid, el.id)

        el = sels.first.elements.second
        self.eq('*', el.element)
        self.eq('warning', el.classes.first.value)

        el = sels.first.elements.third
        self.eq('*', el.element)
        self.eq('foo', el.attributes.first.key)
        self.eq('bar', el.attributes.first.value)

        el = sels.first.elements.fourth
        self.eq('*', el.element)
        self.eq('root', el.pseudoclasses.first.value)

    def it_parses_implied_universal_selector(self):
        sels = dom.selectors('[foo=bar]')
        self.repr('*[foo=bar]', sels)
        self.str('*[foo=bar]', sels)
        el = sels.first.elements.first
        self.eq('*', el.element)
        self.one(el.attributes)
        attr = el.attributes.first
        self.eq('foo', attr.key)
        self.eq('=', attr.operator)
        self.eq('bar', attr.value)

        sels = '.warning'
        sels = dom.selectors(sels)
        self.repr('*.warning', sels)
        self.str('*.warning', sels)
        self.one(sels)
        self.one(sels.first.elements)
        self.type(dom.selector.element, sels.first.elements.first)
        self.eq('*', sels.first.elements.first.element)
        self.one(sels.first.elements.first.classes)
        self.type(
          dom.selector.class_,
          sels.first.elements.first.classes.first
        )
        self.eq(
          'warning', 
          sels.first.elements.first.classes.first.value
        )

        eid = 'x' + uuid4().hex
        sels = expect = '*#' + eid
        sels = dom.selectors(sels)
        self.one(sels)
        self.one(sels.first.elements)
        self.repr(expect, sels)
        self.str(expect, sels)
        el = sels.first.elements.first
        self.eq('*', el.element)
        self.eq(eid, el.id)

        # Combine: #1234 .warning [foo=bar] :root
        eid = 'x' + uuid4().hex
        expect = '*#' + eid
        expect += ' *.warning'
        expect += ' *[foo=bar]'
        expect += ' *:root'
        sels = expect.replace('*', '')
        sels = dom.selectors(sels)
        self.repr(expect, sels)
        self.str(expect, sels)
        self.one(sels)
        self.four(sels.first.elements)

        el = sels.first.elements.first
        self.eq('*', el.element)
        self.eq(eid, el.id)

        el = sels.first.elements.second
        self.eq('*', el.element)
        self.eq('warning', el.classes.first.value)

        el = sels.first.elements.third
        self.eq('*', el.element)
        self.eq('foo', el.attributes.first.key)
        self.eq('bar', el.attributes.first.value)

        el = sels.first.elements.fourth
        self.eq('*', el.element)
        self.eq('root', el.pseudoclasses.first.value)

    def it_parses_groups(self):
        # E F
        sels = dom.selectors('E, F')

        self.repr('E, F', sels)
        self.str('E, F', sels)
        self.two(sels)

        el = sels.first.elements.first
        self.type(dom.selector.element, el)
        self.eq('E', el.element)

        el = sels.second.elements.first
        self.type(dom.selector.element, el)
        self.eq('F', el.element)

        # E[foo=bar], F[baz=qux]
        sels = dom.selectors('E[foo=bar], F[baz=qux]')
        self.repr('E[foo=bar], F[baz=qux]', sels)
        self.str('E[foo=bar], F[baz=qux]', sels)
        self.two(sels)

        el = sels.first.elements.first
        self.type(dom.selector.element, el)
        self.eq('E', el.element)
        self.one(el.attributes)
        self.eq('foo', el.attributes.first.key)
        self.eq('bar', el.attributes.first.value)

        el = sels.second.elements.first
        self.type(dom.selector.element, el)
        self.eq('F', el.element)
        self.one(el.attributes)
        self.eq('baz', el.attributes.first.key)
        self.eq('qux', el.attributes.first.value)

    def it_parses_not(self):
        '''*:not(F)'''
        expect = '*:not(F)'
        sels = ':not(F)'
        sels = dom.selectors(sels)
        self.repr(expect, sels)
        self.one(sels)

        el = sels.first.elements.first
        self.one(sels.first.elements)
        self.type(dom.selector.element, el)
        self.eq('*', el.element)

        self.notnone(el.pseudoclasses.first.arguments.selectors)
        self.eq('not', el.pseudoclasses.first.value)
        sels = el.pseudoclasses.first.arguments.selectors
        self.one(sels)

        els = sels.first.elements
        self.one(els)

        el = els.first

        self.eq('F', el.element)

        '''E:not([foo=bar])'''
        expect = 'E:not(E[foo=bar])'
        sels = dom.selectors(expect)
        self.repr(expect, sels)
        self.one(sels)

        self.one(sels.first.elements)
        el = sels.first.elements.first
        self.type(dom.selector.element, el)
        self.eq('E', el.element)
        pcls = el.pseudoclasses.first

        self.type(dom.selector.pseudoclass, pcls)
        self.eq('not', pcls.value)
        sels = pcls.arguments.selectors
        self.type(dom.selectors, sels)
        self.one(sels.first.elements)
        el = sels.first.elements.first
        self.one(el.attributes)
        self.eq('foo', el.attributes.first.key)
        self.eq('=', el.attributes.first.operator)
        self.eq('bar', el.attributes.first.value)

        '''E:not(:first-of-type)'''
        expect = 'E:not(E:first-of-type)'
        sels = dom.selectors(expect)
        self.repr(expect, sels)
        self.one(sels)

        self.one(sels.first.elements)
        el = sels.first.elements.first
        self.type(dom.selector.element, el)
        pcls = el.pseudoclasses.first

        self.type(dom.selector.pseudoclass, pcls)
        self.eq('not', pcls.value)

        sels = pcls.arguments.selectors
        self.type(dom.selectors, sels)
        self.one(sels.first.elements)
        el = sels.first.elements.first
        self.eq('E', el.element)
        self.eq('first-of-type', el.pseudoclasses.first.value)

        # FIXME:dd6a4f93 There is an issue with the parsing of the not's
        # argument.
        # ''' E:not(:nth-child(2n+1)) '''
        # expect = 'E:not(E:nth-child(2n+1))'
        # sels = dom.selectors(expect)
        # self.repr(expect, sels)
        # self.one(sels)
        #
        # self.one(sels.first.elements)
        # el = sels.first.elements.first
        # self.type(dom.selector.element, el)
        # pcls = el.pseudoclasses.first
        #
        # self.type(dom.selector.pseudoclass, pcls)
        # self.eq('not', pcls.value)
        #
        # sels = pcls.arguments.selectors
        # self.type(dom.selectors, sels)
        # self.one(sels.first.elements)
        # el = sels.first.elements.first
        # self.eq('E', el.element)
        # self.eq('nth-child', el.pseudoclasses.first.value)
        # self.eq(2, el.pseudoclasses.first.arguments.a)
        # self.eq(1, el.pseudoclasses.first.arguments.b)

        ''' E:not(.warning) '''
        expect = 'E:not(E.warning)'
        sels = dom.selectors(expect)
        self.repr(expect, sels)
        self.one(sels)

        self.one(sels.first.elements)
        el = sels.first.elements.first
        self.type(dom.selector.element, el)
        pcls = el.pseudoclasses.first

        self.type(dom.selector.pseudoclass, pcls)
        self.eq('not', pcls.value)

        sels = pcls.arguments.selectors
        self.type(dom.selectors, sels)
        self.one(sels.first.elements)
        el = sels.first.elements.first
        self.eq('E', el.element)
        clss = el.classes
        self.one(clss)
        self.eq('warning', clss.first.value)

        '''*:not(F[foo=bar]:first-of-type)'''
        expect = '*:not(F[foo=bar]:first-of-type)'
        sels = ':not(F[foo=bar]:first-of-type)'
        sels = dom.selectors(sels)
        self.repr(expect, sels)
        self.one(sels)

        el = sels.first.elements.first
        self.one(sels.first.elements)
        self.type(dom.selector.element, el)
        self.eq('*', el.element)

        self.notnone(el.pseudoclasses.first.arguments.selectors)
        self.eq('not', el.pseudoclasses.first.value)
        sels = el.pseudoclasses.first.arguments.selectors
        self.one(sels)

        els = sels.first.elements
        self.one(els)

        el = els.first

        self.eq('F', el.element)

        self.one(el.attributes)
        self.eq('foo', el.attributes.first.key)
        self.eq('=', el.attributes.first.operator)
        self.eq('bar', el.attributes.first.value)

        pcls = el.pseudoclasses.first

        self.type(dom.selector.pseudoclass, pcls)
        self.eq('first-of-type', el.pseudoclasses.first.value)

    def it_raises_on_invalid_selectors(self):
        #dom.selectors('a . b'); return

        # Generic test function
        def test(sel, pos):
            try:
                dom.selectors(sel)
            except dom.CssSelectorParseError as ex:
                if pos is not None:
                    self.eq(pos, ex.pos, 'Selector: "%s"' % sel)
            except Exception as ex:
                self.fail(
                    'Invalid exception: %s "%s"' % (str(ex), sel)
                )
            else:
                self.fail('No exception: "%s"' % sel)

        ''' Invalid combinators '''

        combs = set(list('>+~'))

        ignore = set(list('[\':.'))

        # `invalids` are punctuation exculding the above combs
        invalids = set(string.punctuation) - combs - ignore

        sels = {
            'a %s b' : 2
        }

        for invalid in invalids:
            for sel, pos in sels.items():
                sel %= invalid
                if invalid == '*': continue
                test(sel, pos)

        ''' Selector groups '''
        sels = {
            'a,,b'   :  2,
            'a:,b'   :  2,
            'a(,b'   :  1,
            'a,b,,'  :  4,
            'a,b,'   :  4,
        }

        for sel, pos in sels.items():
            test(sel, pos)

        # NOTE ':not(:not(li))' fails but for the wrong reason (see
        # dd6a4f93). It should fail because the standard says that :not
        # can't have :not as its argument.  However this is not
        # happening. When the dd6a4f93 issue is fixed, we can add code
        # that explicitly raises an exception when a ':not' is found as
        # an argument to :not. This could would likely go in
        # pseudoclass.demand().

        ''' Pseudoclasses arguments '''
        sels = {
            ':nth-child()'             :  None,
            ':nth-last-child(2a)'      :  None,
            ':nth-of-type(4.4)'        :  None,
            ':nth-last-of-type(derp)'  :  None,
            ':nth-child(3x+4)'         :  None,
            ':nth-child(2n+1+)'        :  None,
            ':nth-child(*2n+1)'        :  None,
            ':nth-child(a2n+1)'        :  None,
            ':not(::)'                 :  None,
            ':not(:not(li))'           :  None,
        }

        for sel, pos in sels.items():
            test(sel, pos)

        ''' Pseudoclasses '''
        sels = {
            ':'                            :  1,
            '::'                           :  1,
            ':not-a-pseudoclass()'         :  20,
            ':not-a-pseudoclass'           :  18,
            '.my-class:not-a-pseudoclass'  :  27,
            ':empty:'                      :  7,
            ':nth-child('                  :  11,
        }

        for sel, pos in sels.items():
            test(sel, pos)

        ''' Classes '''
        sels = {
            '.'                          :  1,
            'a . b'                      :  3,
            '..my-class'                 :  1,
            '.:my-class'                 :  1,
            './my-class'                 :  1,
            '.#my-class'                 :  1,
            '.#my#class'                 :  1,
            '.my-class..my-other-class'  :  10,
            '.my-class.'                 :  10,
            '.my-class]'                 :  9,
            '.my-class['                 :  10,
            '.my-class/'                 :  10,
        }

        for sel, pos in sels.items():
            test(sel, pos)

        ''' Attributes '''
        sels = {
            '.[foo=bar]'              :  1,
            '*.[foo=bar]'             :  2,
            '.*[foo=bar]'             :  1,
            '[foo=bar'                :  8,
            'foo=bar]'                :  3,
            'div[]'                  :  4,
            'div[=]'                  :  4,
            'div[foo=]'               :  8,
            'div[=bar]'               :  4,
            'div.[foo=bar]'           :  4,
            'div:[foo=bar]'           :  4,
            'div#[foo=bar]'           :  3,
            'div[[foo=bar]'           :  4,
            'div[foo=bar]]'           :  12,
            'div[foo%bar]'            :  7,
            'div[foo%=bar]'           :  7,
            'div[foo=%bar]'           :  8,
            'div[foo===bar]'          :  9,
            'div[f/o=bar]'            :  5,
            'div[f#o=bar]'            :  5,
            'div[bar=]'               :  8,
            'div[foo=bar][foo=bar'    :  20,
            'div[foo=bar]foo=bar]'    :  15,
            'div[foo=bar][[foo=bar]'  :  13,
            'div[foo=bar][foo%bar]'   :  16,
            'div[foo=bar][foo=]'      :  17,
            'div[foo=bar].'           :  13,
        }

        for sel, pos in sels.items():
            test(sel, pos)

        ''' Leading punctuation characters should raise exceptions '''

        # These are acceptable as loading characters - they're the CSS
        # selector deliminators
        delims = list('.:[#*')

        # `invalids` are punctuation exculding the above delims
        invalids = set(string.punctuation) - set(delims)

        # Backslashes and underscores are valid, too
        invalids -= set(list('\\_'))

        for invalid in invalids:
            sel = invalid + 'div'
            test(sel, 0)

        ''' Empty strings and whitespace '''
        sels = list(string.whitespace)
        sels.append('')

        for sel in sels: 
            self.expect(
                dom.CssSelectorParseError, 
                lambda: dom.selectors(sel),
           )

########################################################################
# Test parties                                                         #
########################################################################
class test_gem(tester):
    def __init__(self):
        super().__init__()
        #gem.party.orm.recreate(recursive=True)

########################################################################
# Test gem.persons                                                     #
########################################################################
class gem_person(tester):
    def __init__(self):
        super().__init__()
        gem.party.orm.recreate(recursive=True)
        gem.address.orm.recreate()

    @staticmethod
    def getvalid():
        per = gem.person()
        per.firstname      =  uuid4().hex
        per.middlename     =  uuid4().hex
        per.lastname       =  uuid4().hex
        per.title          =  uuid4().hex
        per.suffix         =  uuid4().hex
        per.gender         =  False
        per.mothersmaiden  =  uuid4().hex
        per.maritalstatus  =  True
        per.nationalids    =  uuid4().hex
        per.isicv4         =  None
        per.dun            =  None
        return per

    def it_creates(self):
        per = self.getvalid()
        per.save()

        per1 = gem.person(per.id)

        for map in per.orm.mappings.fieldmappings:
            self.eq(
                getattr(per, map.name),
                getattr(per1, map.name)
            )

    def it_updates(self):
        # Create
        per = self.getvalid()
        per.save()

        # Load
        per = gem.person(per.id)

        # Update
        oldfirstname = per.firstname
        newfirstname = uuid4().hex

        per.firstname = newfirstname
        per.save()

        # Reload
        per1 = gem.person(per.id)

        # Test
        self.eq(newfirstname, per1.firstname)
        self.ne(oldfirstname, per1.firstname)

    def it_creates_association_to_person(self):
        bro = self.getvalid()
        sis = self.getvalid()

        # TODO Figure out a way to do this:
        #
        #     bro.siblings += sis
        bro.party_parties += gem.party_party.sibling(sis)

        self.is_(bro, bro.party_parties.last.subject)
        self.is_(sis, bro.party_parties.last.object)

        bro.save()

        bro1 = gem.person(bro.id)

        self.eq(bro.id, bro1.party_parties.last.subject.id)
        self.eq(sis.id, bro1.party_parties.last.object.id)
        
    def it_creates_association_to_company(self):
        per = self.getvalid()
        com = gem_company.getvalid()

        pp = gem.party_party()
        pp.object = com
        pp.role = 'patronize'

        per.party_parties += pp

        self.is_(per, per.party_parties.last.subject)
        self.is_(com, per.party_parties.last.object)

        per.save()

        per1 = gem.person(per.id)

        self.eq(per.id, per1.party_parties.last.subject.id)
        self.eq(com.id, per1.party_parties.last.object.id)

    def it_creates_association_to_person(self):
        bro = self.getvalid()
        sis = self.getvalid()

        # TODO Figure out a way to do this:
        #
        #     bro.siblings += sis
        bro.party_parties += gem.party_party.sibling(sis)

        self.is_(bro, bro.party_parties.last.subject)
        self.is_(sis, bro.party_parties.last.object)

        bro.save()

        bro1 = gem.person(bro.id)

        self.eq(bro.id, bro1.party_parties.last.subject.id)
        self.eq(sis.id, bro1.party_parties.last.object.id)
        
class gem_company(tester):
    def __init__(self):
        super().__init__()
        gem.party.orm.recreate(recursive=True)
        gem.address.orm.recreate()

    @staticmethod
    def getvalid():
        com = gem.company()
        com.name = uuid4().hex
        com.ein = str(uuid4().int)[:9]
        com.nationalids    =  uuid4().hex
        com.isicv4         =  'A'
        com.dun            =  None
        return com

    def it_creates(self):
        com = self.getvalid()
        com.save()

        com1 = gem.company(com.id)

        sup = com

        while sup:
            for map in sup.orm.mappings.fieldmappings:
                self.eq(
                    getattr(com, map.name),
                    getattr(com1, map.name),
                )

            sup = sup.orm.super

    def it_updates(self):
        # Create
        com = self.getvalid()
        com.save()

        # Load
        com = gem.company(com.id)

        # Update
        old, new = com.name, uuid4().hex
        com.name = new
        com.save()

        # Reload
        com1 = gem.company(com.id)

        # Test
        self.eq(new, com1.name)
        self.ne(old, com1.name)

    def it_creates_association_to_person(self):
        per = gem_person.getvalid()
        com = self.getvalid()

        pp = gem.party_party()
        pp.object = per
        pp.role = 'employ'
        pp.begin = datetime.now()

        com.party_parties += pp

        self.is_(com, com.party_parties.last.subject)
        self.is_(per, com.party_parties.last.object)

        com.save()

        com1 = gem.company(com.id)

        self.eq(com.id, com1.party_parties.last.subject.id)
        self.eq(per.id, com1.party_parties.last.object.id)

        self.one(com1.party_parties)
        pp1 = com1.party_parties.first
        for map in pp.orm.mappings.fieldmappings:
            self.eq(
                getattr(pp, map.name),
                getattr(pp1, map.name),
            )

TestHtml = tester.dedent('''
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

TestHtmlMin = '<html id="myhtml" arbit="trary"><!-- This is an HTML document --><head><!-- This is the head of the HTML document --><base href="www.example.com"></head><body><p>Lorum &amp; Ipsum Δ</p><p>This is some<strong>strong text.</strong></p><p>This too is some<strong>strong text.</strong></p></body></html>'


ListHtml = '''
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
  <body>
    <article>
      <section>
        <ol>
          <li id="0">
            <p>
              This is list item 0.
            </p>
          </li>
          <li id="1">
            <p>
              This is list item 1.
            </p>
          </li>
          <li id="2">
            <p>
              This is list item 2.
            </p>
          </li>
          <li class="my-class" id="3">
            <p>
              This is list item 3.
            </p>
          </li>
          <li id="4">
            <p>
              This is list item 4.
            </p>
          </li>
          <li id="5">
            <p>
              This is list item 5.
            </p>
          </li>
          <li id="6">
            <p>
              This is list item 6.
            </p>
          </li>
          <li id="7">
            <p>
              This is list item 7.
            </p>
          </li>
          <li id="8">
            <p>
              This is list item 8.
            </p>
          </li>
          <li id="9">
            <p>
              This is list item 9.
            </p>
          </li>
          <li id="10">
            <p>
              This is list item 10.
            </p>
          </li>
          <li id="11">
            <p>
              This is list item 11.
            </p>
          </li>
        </ol>
      </section>
    </article>
  </body>
</html>
'''

AdjacencyHtml = '''
  <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en" debug="true">
    <head>
      <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
    </head>
    <body>
      <div id="first-div">
        <p id="child-of-div">
          <span id="child-of-p-of-div">
          </span>
        </p>
      </div>
      <p id="before-the-adjacency-anchor">
      </p>
      <p id="immediatly-before-the-adjacency-anchor">
      </p>
      <div id="adjacency-anchor">
        <h2>
          <p id="child-of-h2" class="p-header">
            <span id="child-of-p-of-h2" class="span-header">
            </span>
          </p>
          <q id="second-child-of-h2">
            second child of h2
          </q>
        </h2>
      </div>
      <p id="immediatly-after-the-adjacency-anchor">
      </p>
      <p id="after-the-adjacency-anchor">
      </p>
    </body>
  </html>
'''

Shakespeare = '''
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en" debug="true">
  <head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
  </head>
  <body>
    <div id="test" class="container">
      <div class="dialog">
        <h2 id="023338d1-5503-4054-98f7-c1e9c9ad390d f6836822-589e-40bf-a3f7-a5c3185af4f7"
            class='header'>
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
          <div id="herp" title="wtf" class="dialog">
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
