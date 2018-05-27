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
from tester import *
from table import *
import math
from configfile import configfile

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

    def it_calls_sort(self):
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

    def it_calls_sorted(self):
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

        # Append a unique knight insisting in be unique
        ni = knight('knight who says ni')
        sks &= ni
        self.assertEq(4, sks.count)
        for i, k in enumerate([fk, bk, fk, ni]):
            self.assertIs(sks[i], k)

        # Append a non-unique knight insisting in be unique
        sks &= ni
        self.assertEq(4, sks.count)
        for i, k in enumerate([fk, bk, fk, ni]):
            self.assertIs(sks[i], k)

        # Append a non-unique knight insisting in be unique using the append
        # method rather than the &= operator in order to obtain the results
        res = sks.append(ni, uniq=True)
        self.assertTrue(res.isempty)
        self.assertEq(4, sks.count)
        for i, k in enumerate([fk, bk, fk, ni]):
            self.assertIs(sks[i], k)

        # Append a non-unique collection of knights insisting they be unique
        # using the append method rather than the &= operator in order to
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
        """ The &= opreator (__iand__) wraps the append() methed setting
        the unique flag to True. So &= is like a regular append accept 
        objecs won't be appended if already exist in the collection."""

        ## Test appending one unique entity ##
        ks = knights.createthe4()
        ni = knight('knight who says ni')
        ks &= ni

        self.assertEq(5, ks.count)
        self.assertIs(ks.last, ni)

        # Test appending one non-unique entity. Nothing should sucessfully
        # be appended.

        ks = knights.createthe4()
        ks &= ks.first

        self.assertEq(4, ks.count)

        # Test appending an entities collection to an entities collection
        # where one of the entities being appended is not unique.

        ks = knights.createthe4()
        nis = knights()
        nis += knight('knight who says ni 1')
        nis += ks.first # The non-unique entity

        ks &= nis

        self.assertEq(5, ks.count)
        self.assertIs(nis.first,   ks.last)

        # Test appending an entities collection to an entities collection
        # where both of the entities being appended are not unique.
        # Nothing will be sucessfully appended
        ks = knights.createthe4()
        nis = knights()
        nis += ks.first
        nis += ks.second # The non-unique entity

        ks &= nis

        self.assertEq(4, ks.count)

        ## Ensure we get a ValueError if we append something that isn't
        ## an entity or entities type
        ks = knights.createthe4()
        try:
            ks &= 1
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
        self.assertTrue(4, ks.brokenrules.count)

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

        # Appned a duplicate entity again but with the &= operator to ensure
        # it won't be appended
        ks &= the4.first
        self.assertIs(the4.first, snare.first)
        self.assertIs(the4.second, snare.second)
        self.assertIs(the4.third, snare.third)
        self.assertEq(4, snare.count)

        # Appned a collection of duplicate entity again but with the &=
        # operator to ensure they won't be appended
        ks &= entities([the4.second, the4.third])
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
        # invokes the onadd event. Obviously, we can't subscribe to the event
        # until the object is instantiated. There needs to be a workaround
        # that doesn't involve altering the entities classes.

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
        """ A row's index property contains the 0-based ordinal, i.e., the
        first row in a table has an index of 0, the second has an index of 1,
        and so on. """

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

        l = configfile.getinstance().logs.default
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

t = testers()
t.oninvoketest += lambda src, eargs: print('# ', end='', flush=True)
t.oninvoketest += lambda src, eargs: print(eargs.method[0], flush=True)
t.run()
print(t)
