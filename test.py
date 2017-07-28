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

class knights(entities):
    @staticmethod
    def createthe4():
        ks = knights()
        ks += knight('Lancelot')
        ks += knight('Authur')
        ks += knight('Galahad')
        ks += knight('Bedevere')
        return ks

class knight(entity):
    def __init__(self, name):
        self.name = name

    @property
    def brokenrules(self):
        brs = brokenrules()
        if type(self.name) != str:
            brs += brokenrule("Names must be strings")
        return brs

    def __repr__(self):
        return super().__repr__() + ' ' + self.name

    def __str__(self):
        return self.name

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
        """ The entities.reversed() method returns an entities collection
        containing the same entity objects but in reversed order. """

        ks = knights.createthe4()
        ks1 = ks.reversed()

        self.assertCount(ks1.count,  ks)

        self.assertIs(knights,       type(ks1))

        self.assertIs(ks1.first,     ks.last)
        self.assertIs(ks1.last,      ks.first)
        self.assertIs(ks1.second,    ks.third)
        self.assertIs(ks1.third,     ks.second)

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
        class sillyknights(knights):
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
                return super().append(obj, uniq,  r=r)

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

    def it_gets__list(self):
        """ The _list property is a 'private' property representing
        the underlying Python list object used to store the entities."""
        ks = knights.createthe4()

        for i, k in enumerate(ks):
            self.assertIs(ks._list[i], k)

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
        s = """Lancelot
Authur
Galahad
Bedevere
"""
        self.assertEq(s, str(ks))

        ks.clear()

        self.assertEq('', str(ks))

    def it_calls__repr__(self):
        """ The __repr__ method will return a concatenation of the results
        of each entities __repr__ invocation followed by a line ending."""

        ks = knights.createthe4()

        for i, l in enumerate(repr(ks).splitlines()):
            self.assertEq(l, repr(ks[i]))

        ks.clear()

        self.assertEq('', repr(ks))

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

    def it_calls__getitems(self):
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
        self.assertIs(ks[2], ks.penultimate)
        self.assertIs(ks[1], ks.antepenultimate)

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
        self.assertNone(ks.penultimate)
        self.assertNone(ks.antepenultimate)

        # Ensure ordinals return sensible results with a collection of 1
        ni = knight('knight who says ni 1')
        ks += ni
        self.assertIs(ni, ks.first)
        self.assertIs(ni, ks.last)
        self.assertNone(ks.second)
        self.assertNone(ks.third)
        self.assertNone(ks.fourth)
        self.assertNone(ks.penultimate)
        self.assertNone(ks.antepenultimate)

        # Ensure ordinals return sensible results with a collection of 2
        ni1 = knight('knight who says ni 2')
        ks += ni1
        self.assertIs(ni, ks.first)
        self.assertIs(ni1, ks.second)
        self.assertIs(ni1, ks.last)
        self.assertIs(ni, ks.penultimate)
        self.assertNone(ks.third)
        self.assertNone(ks.fourth)
        self.assertNone(ks.antepenultimate)

        # Ensure ordinals return sensible results with a collection of 3
        ni2= knight('knight who says ni 2')
        ks += ni2
        self.assertIs(ni, ks.first)
        self.assertIs(ni1, ks.second)
        self.assertIs(ni2, ks.third)
        self.assertIs(ni2, ks.last)
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

        self.assertCount(4, snare)
        self.assertIs(rst, snare.first)
        self.assertIs(nd, snare.second)
        self.assertIs(rd, snare.third)
        self.assertIs(rth, snare.fourth)

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
        class sillyknights(knights):
            def __init__(self, initial=None):
                super().__init__(initial);
                self.indexes += index(name='name', keyfn=lambda k: k.name)

        the4 = knights.createthe4()
        sk = sillyknights()

        sk += the4.first

        ks = sk.indexes['name'][the4.first.name]

        self.assertTrue(ks.hasone)
        self.assertIs(ks.first, sk.first)
        self.assertEq(sillyknights, type(ks))

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

        self.assertEq(10, tbl.rows.count)
        self.assertEq(20, tbl.columns.count)
        self.assertEq(20, tbl.rows.first.fields.count)
        for r in tbl:
            for f in r:
                self.assertNone(f.value)
        

        # Instatiate a table with 10 rows and 20 columns. All the fields'
        # values should be the knight set by the initval argument.
        k = knights.createthe4().first
        tbl = table(x=10, y=20, initval=k)

        self.assertEq(10, tbl.rows.count)
        self.assertEq(20, tbl.columns.count)
        self.assertEq(20, tbl.rows.first.fields.count)
        for r in tbl:
            for f in r:
                self.assertIs(k, f.value)

    def it_calls_newrow(self):
        # Ensure newrow creates a row in the table and returns it
        tbl = table()
        r = tbl.newrow()
        self.assertEq(1, tbl.rows.count)
        self.assertIs(tbl.rows.first, r)

    def it_gets_columns(self):
        tbl = table(x=10, y=20)
        cs = tbl.columns
        self.assertEq(columns, type(cs))

    def it_calls_count(self):
        k = knights.createthe4().first
        tbl = table(x=10, y=20, initval=k)

        # TODO Wait for indexs to be reimplemented
        # self.assertEq(20 * 10, tbl.count(k))

    def it_call_where(self):
        the4 = knights.createthe4()
        tbl = table(x=10, y=20)
        r = tbl.newrow()
        r.newfield(the4.first)
        r.newfield(the4.second)

        # TODO Write when indexes have been reimplemented
        # fs = tbl.where(knight)
        # self.assertEq(2, fs.count)

        fs = tbl.where(lambda v: type(v) == knight)
        self.assertEq(2, fs.count)
        self.assertEq(fields, type(fs))
        self.assertIs(the4.first, fs.first.value)
        self.assertIs(the4.second, fs.second.value)

        # TODO Write when indexes have been reimplemented
        # fs = tbl.where(the4.first)
        # self.assertEq(1, fs.count)
        # self.assertEq(2, fs.count)

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
        f = tbl.rows.first.fields.first
        try:
            tbl.slice(center=f, radius="123")
            self.assertFail('The radius should be an int')
        except TypeError:
            self.assertTrue(True)
        except Exception as ex:
            self.assertFail('Incorrect exception raised: ' + str(type(ex)))
        
        

t = testers()
t.oninvoketest += lambda src, eargs: print('#', end='', flush=True)
t.run()
print(t)



