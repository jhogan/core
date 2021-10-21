# vim: set et ts=4 sw=4 fdm=marker

# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2021

"Entities must not be multiplied beyond necessity"
# John Punch

""" This module contains the ``entities`` class - an important class
designed to maintain collections of ``entity`` subclass instances
(``entity`` is also contained in this module). The ``entities`` class
can be thought of as a smart ``list`` while ``entity`` subclasse
instances are collected as the elements of that list. Many of the other
classes in the core framework inherit from ``entities`` and ``entity`` -
most notebly ``orm.entities`` and ``orm.entity``.

This module also containes the ``brokenrule`` and ``brokenrules``
classes which provide a way to collect validation errors an ``entity``
or ``entities`` object may have.

Base classes ``event`` and ``eventargs`` are defined here, too, which
allows for the defining, raising and handling of events. Their design
was inspired my C# delegates and the VB.NET event system.

The ``index`` and ``indexes`` classes create dict() based indexes of
``entity`` objects within ``entities`` collection for fast object
lookups by attributes. These indexes are useful for ``entities``
collections with large numbers of elements.
"""
from datetime import datetime
from random import randint, sample
import re
import sys
import builtins
from pprint import pprint
from functools import total_ordering
import decimal
import string
from func import getattr, enumerate
from dbg import B

# TODO Throughout the code base, we should look for instances of:
#
#     if x == None
#     if x != None
#     if x == False
#     if x == True
# 
# And replace the (in)equality operator (== and !=) with the identity
# operator (is and is not).

# TODO This seems misplaced. Maybe we should have a module called dec.py
# for miscellaneous decorators.

class classproperty(property):
    ''' Add this decorator to a method and it becomes a class method
    that can be used like a property.
    '''

    def __get__(self, cls, owner):
        # If cls is not None, it will be the instance. If there is an
        # instance, we want to pass that in instead of the class
        # (owner). This makes it possible for classproperties to act
        # like classproperties and regular properties at the same time.
        # See the conditional at entities.count.
        obj = cls if cls else owner
        return classmethod(self.fget).__get__(None, obj)()

class entities:
    """ An abstract class that serves a container for other classes::

        # Create an entities and two entity objects
        ents = entities()
        ent = entity()
        ent1 = entity()

        # Note that the lengthe of ents is currently 0 because we
        # haven't added anything to it.
        assert len(ents) == 0   # Noncanonical form
        assert ents.count == 0  # Canonical form

        # Append ent and ent1
        ents.append(ent)  # Noncanonical form
        ents += ent1      # Canonical form

        # Assert that ent and ent1 are the first and second elements
        # respectively.
        assert ents[0] is ent       Noncanonical form
        assert ents[1] is ent1  

        assert ents.first is ent    Canonical form
        assert ents.second is ent1

        assert len(ents) == 2       Noncanonical form
        assert ents.count == 2      Canonical form

    As you can see, the ``entities`` instance aboves acts similar to a
    list(). ``entities`` acts and quacks like a Python list to the
    extent possible. This allows it to be more flexible. However, as you
    can see above, the canonical forms are prefered because they are
    easier to read and type.

    While you could use ``entities`` and ``entity`` directly, they are
    almost always subclassed. Subclassed ``entities`` are much more
    powerful than simple arrays because subclasses can encapsulate
    attribute and behavior logic::

        class files(entities):
            @property
            def size(self):
                return sum(x.size for x in self)

            def delete(self):
                for f in self:
                    f.delete()

        class file(entity):
            def __init__(self, path, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.path = path

            def size(self):
                return os.path.getsize(self.path)

            def delete(self):
                os.remove(self.path)

    Above, we have a `files` collection to collect `file` objects.  We
    can use the files class to calculate the total size of the files and
    delete them all in one line.

        # Create a files collection and add the herp and derp files
        fs = files()
        fs += file('/tmp/herp')
        fs += file('/tmp/derp')

        # Get the size of the file combined
        assert fs.size == fs.first.size + fs.second.size

        # Delete both files
        fs.delete()
    """
    def __init__(self, initial=None):
        """ Create an instance of an ``entities`` collection.

        Subclasses of ``entities``, if they override __init__ will want
        to ensure this method is called::

            class myent(entities):
                def __init__(self, *args, **kwargs):
                    
                    # Do this otherwise the entities class will break
                    super().__init__(*args, **kwargs)
                    
                    # Custome stuff
                    ...

        :param: initial iterable: An interable, such as a list, tuple,
        or ``entities`` collection, which will populate the entities
        class.
        """

        # TODO We could make _ls lazy-loaded property. This way
        # subclasses wouldn't break if they don't call super.__init__()
        #
        #     @property
        #     def _ls(self):
        #         # The naming is a little off here
        #         if self._private_ls is None:
        #             self._private_ls = list()
        #         return self._private_ls

        self._ls = list()

        # Append initial collection
        if initial is not None:
            self.append(initial)

    def __bool__(self):
        """ Returns True.

        An entities class will always return True. Unlike a list, you
        should not test if an entities collection has elements by seeing
        if its truthy. Rather, you should call it `isplurality`
        property:

            # Dont do this
            if myents:
                # We must have elements in myents

            # Rather, do this
            if myents.isplurality
        """
        # An entities collection will always pass a truth test
        return True

    def _self_onadd(self, src, eargs):
        """ An event handler that runs every time an entity is added to
        the collection.

        Updates the index with the new entity and raises the
        oncountchange event. Also subscribes the entity being added to
        the onbeforevaluechange and onaftervaluechange events.
        """
        for ix in self.indexes:
            ix += eargs.entity

        if hasattr(eargs.entity, 'onbeforevaluechange'):
            eargs.entity.onbeforevaluechange += \
                self._entity_onbeforevaluechange 

        if hasattr(eargs.entity, 'onaftervaluechange'):
            eargs.entity.onaftervaluechange += \
                self._entity_onaftervaluechange 

        self.oncountchange(self, eventargs())
            
    def _self_onremove(self, src, eargs):
        """ An event handler that runs every time an entity is removed
        from the collection.

        Removes the entity from the index and raises the oncountchange
        event. Also unsubscribes the entity from the onbeforevaluechange
        and onaftervaluechange events.
        """
        for ix in self.indexes:
            ix -= eargs.entity

        if hasattr(eargs.entity, 'onbeforevaluechange'):
            eargs.entity.onbeforevaluechange -= \
                self._entity_onbeforevaluechange 

        if hasattr(eargs.entity, 'onaftervaluechange'):
            eargs.entity.onaftervaluechange -= \
                self._entity_onaftervaluechange 

        self.oncountchange(self, eventargs())

    def _entity_onbeforevaluechange(self, src, eargs):
        """ An event handler invoked before a change is made to a value
        on one of the collected entity objects.  Used to remove the
        entity from the property-based index (_entity_onaftervaluechange
        will add the entity to the correct index). Also raises the
        collection's onbeforevaluechange.
        """

        # Raise an analogous event for the collection itself
        self.onbeforevaluechange(src, eargs)
        for ix in self.indexes:
            if ix.property == eargs.property:
                ix.remove(eargs.entity)

    def _entity_onaftervaluechange(self, src, eargs):
        """ An event handler invoked after a change is made to a value
        on one of the collected entity objects.  Used to update the
        index for the property that was changed. Also raises the
        collection's onaftervaluechange event.
        """

        # Raise an analogous event for the collection itself
        self.onaftervaluechange(src, eargs)
        for ix in self.indexes:
            if ix.property == eargs.property:
                ix += eargs.entity

    @property
    def onbeforeadd(self):
        """ Returns the onbeforeadd event for this collection.
        """
        if not hasattr(self, '_onbeforeadd'):
            self._onbeforeadd = event()
            # There is no implementation of self._self_onbeforeadd, but
            # we can uncomment the below line when there is.
            #self.onbeforeadd += self._self_onbeforeadd

        return self._onbeforeadd

    @onbeforeadd.setter
    def onbeforeadd(self, v):
        """ Sets the onbeforeadd event for this collection.
        """
        self._onbeforeadd = v

    # TODO onadd should be renamed to onafteradd
    @property
    def onadd(self):
        """ Returns the onadd event for this collection.
        """
        if not hasattr(self, '_onadd'):
            self._onadd = event()
            self.onadd += self._self_onadd

        return self._onadd

    @onadd.setter
    def onadd(self, v):
        """ Sets the onadd event for this collection.
        """
        self._onadd = v

    @property
    def onremove(self):
        """ Returns the onremove event for this collection.
        """
        if not hasattr(self, '_onremove'):
            self._onremove = event()
            self.onremove += self._self_onremove
        return self._onremove

    @onremove.setter
    def onremove(self, v):
        """ Sets the onremove event for this collection.
        """
        self._onremove = v

    @property
    def oncountchange(self):
        """ Returns the oncountchange event for this collection.
        """
        if not hasattr(self, '_oncountchange'):
            self._oncountchange = event()
        return self._oncountchange

    @oncountchange.setter
    def oncountchange(self, v):
        """ Sets the oncountchange event for this collection.
        """
        self._oncountchange = v

    @property
    def onbeforevaluechange(self):
        """ Returns the onbeforevaluechange event for this collection.
        """
        if not hasattr(self, '_onbeforevaluechange'):
            self._onbeforevaluechange = event()
        return self._onbeforevaluechange

    @onbeforevaluechange.setter
    def onbeforevaluechange(self, v):
        """ Sets the onbeforevaluechange event for this collection.
        """
        self._onbeforevaluechange = v

    @property
    def onaftervaluechange(self):
        """ Returns the onaftervaluechange event for this collection.
        """
        if not hasattr(self, '_onaftervaluechange'):
            self._onaftervaluechange = event()
        return self._onaftervaluechange

    @onaftervaluechange.setter
    def onaftervaluechange(self, v):
        """ Sets the onaftervaluechange event for this collection.
        """
        self._onaftervaluechange = v

    @property
    def indexes(self):
        """ Lazy-loads and returns the collection of indexes objects for
        this entities collection.
        """
        if not hasattr(self, '_indexes'):
            self._indexes = indexes(type(self))

            ix = index(name='identity', keyfn=lambda e: e)
            ix.indexes = self._indexes
            self._indexes._ls.append(ix)
        return self._indexes

    @indexes.setter
    def indexes(self, v):
        """ Sets the index collection for this entities collection.
        
        This setter is intended to permit the += operator to be used
        to add indexes to the entities.indexes collection. Normally, you
        wouldn't want to set the indexes collection this way; the
        corresponding getter creates and returns the indexes collection
        for this entities collection.
        """
        self._indexes = v

    def __call__(self, ix):
        """ Provides an indexer using the () operator. Similar to the
        __getitem__ indexer but returns None if the entity doesn't
        exist::

            # Create a collection with one entry
            myents = entities()
            myent = entity()
            myents += myent

            # Use () operator as indexer
            assert myents(0) is myent
            assert myents(1) is None

        This is a convenient alternative to the square bracket indexer
        (__getitem__) for cases where it's desirable to work with
        potential None return values instead of trapping IndexError's.
        """
        try: 
            return self[ix]
        except IndexError: 
            return None

    def __iter__(self):
        """ Provides a basic iterator for the collection

            # Create a collection with some entries
            myents = entities()
            myents += entity()
            myents += entity()

            # Interate
            for myent in myents:
                ...
        """
        for t in self._ls:
            yield t

    def head(self, number=10):
        """ Returns the first `number` entries from the collection.

        :param: number int: The number of entries to return.
        """
        if number <= 0:
            return type(self)()

        return type(self)(initial=self[:number])

    def tail(self, number=10):
        """ Returns the last `number` entries from the collection.

        :param: number int: The number of entries to return.
        """
        if number <= 0:
            return type(self)()
            
        cnt = self.count
        start = cnt - number
        return type(self)(initial=self[start:cnt])

    def pluck(self, *ss):
        """ Returns a list elements from the collection for the given
        field names::

            # Create a collection with two entity object where the first
            # has a `name` of Alice, `age` 30, and the second has a
            # `name` of Bob, `age` 31.
            ents = entities()
            for i, name in enumerate('Alice', 'Bob'):
                ent = entity()
                ent.name = name
                ent.age = i + 30
                ents += ent

            # Pluck the names
            assert ents.pluck('name') == ['Alice', 'Bob]

        You can also pass multiple property names. The result will be a
        nested lists for each of the property names::

            assert ents.pluck('name', 'age') == \
                [ ['Alice', 30], ['Bob', 31] ]

        You can also use replacement fields to create lists of formatted
        strings::

            assert ents.pluck('{name}: {age}') == \
                ['Alice: 30', 'Bob: 31']

        Conversion flags can be used to uppercase, lowercase, title
        case, capitalize, strip, reverse and truncate the replacement
        fields::

            assert ents.pluck('{name!u}') == ['ALICE', 'BOB']

        Above, 'u' is used to uppercase the names. Here is a complete
        list of conversion flags::

            u - UPPER CASE
            l - lower case
            c - Capitalize
            t - Title Case
            s - strip whitespace
            r - Reverse string

        A number can be used as a conversion flag to truncate the
        field::

            assert ents.pluck('{name!2}') == ['AL', 'BO']

        You can also nest field names::

            assert ents.pluck('name.__class__') == [str, str]

        Here, we are just plucking the __class__ property of the str
        object, which of course is str. You can use as many dots as
        necessary. This feature becomes more useful in highly nested
        objects models. Consider an order object that has a customer
        object as a parent::

            # Demonstrate the name of the customers
            assert ords.first.customer.name == 'Alice'
            assert ords.second.customer.name == 'Bob'

            # Pluck
            assert ords.pluck('customer.name') == ['Alice', 'Bob']

        Here, `ords` is a collection of `order` objects. Each has a
        customer object associated with it. The customer object has a
        name - which is what we are after.
        """

        # TODO We may want to return an entities collection here if all
        # the items that were plucked were entities. This is because,
        # currently, since we return a `list`, we can't do chained
        # plucks, e.g., 
        #
        # sng.artist_artists.pluck('object').pluck('orm.super')
        #
        # However, list()s should continue to be returned if any of the
        # elements are not entitiy objects. On the other hand, we could
        # have a `primativeentity` class that can wrap a primative
        # value. This would make it possible to always return an
        # entities collection, i.e.:
        #
        #     v = str(getattr(e, prop))
        #     if primativeentity.isprimative(v):
        #         es += primativeentity(v)
        #
        # We may want to write an algorithm to determine the most
        # generic entity in a collection of entities. This would allow
        # us to create an entities collection object that is the most
        # specialized for the given list of entities as possible.
        #
        # Also, for the above line to work, I think would should make
        # sure we are using rgetattr() instead of getattr. 
        class formatter(string.Formatter):
            def convert_field(self, v, conv):
                if conv:
                    if conv == "u":
                        return str(v).upper()
                    elif conv == "l":
                        return str(v).lower()
                    elif conv == "c":
                        return str(v).capitalize()
                    elif conv == "t":
                        return str(v).title()
                    elif conv == "s":
                        return str(v).strip()
                    elif conv == "r":
                        return str(v)[::-1]
                    elif conv.isdigit():
                        return str(v)[:int(conv)]

                return super().convert_field(v, conv)

        ls = list()

        if len(ss) == 1:
            s = ss[0]
        elif hasattr(ss, '__iter__'):
            for s in ss:
                ls.append(self.pluck(s))
                
            return [list(e) for e in zip(*ls)]
        else:
            raise ValueError()

        for e in self:
            if '{' in s:
                args = dict()
                for prop in dir(e):

                    # NOTE Ignoring these props because the process
                    # stalled when plucking from a recursive orm entity.
                    # Feel free to include these props here if you are
                    # able to correct that. See the `pluck` lines in
                    # it_saves_recursive_entity.
                    if prop in ('__dict__', 
                                'onaftervaluechange',
                                'onbeforevaluechange',
                                '_onaftervaluechange',
                                '_onbeforevaluechange'):
                        continue

                    args[prop] = str(getattr(e, prop))

                fmt = formatter()
                ls.append(formatter().format(s, **args))
            else:
                ls.append(getattr(e, s))

        return ls

    def getrandom(self, returnIndex=False):
        if self.isempty: return None
        ix = randint(0, self.ubound)
        if returnIndex:
            return self[ix], ix
        else:
            return self[ix]

    def getrandomized(self):
        """ Return a randomized version of self."""
        return type(self)(initial=sample(self._ls, self.count))

    def max(self, key):
        """ Return the entity with the maximum value defined in the key
        lambda. If no entities are in the collection, None is returned.
        If two entities tie as the max, the first in the collection will
        be returned.
        
        Note that this is modeled on the builtin `max()` function in
        Python.

        For example, given an entities collection of houses each with a
        proprety called ``price``, we can get the priciest house in the
        collection by doing the following::

            priciest = houses.max(key=lambda x: x.price)
        """

        # TODO Add the `default` argument like the builtin `max()`

        return self._minmax(min=False, key=key)

    def min(self, key):
        """ Return the entity with the minimum value defined in the key
        lambda. If no entities are in the collection, None is returned.
        If two entities tie as for min, the first entity in the
        collection will be returned.
        
        Note that this is modeled on the builtin `min()` function in
        Python.

        For example, given an entities collection of houses each with a
        proprety called ``price``, we can get the cheapest house in the
        collection by doing the following::

            cheapest = houses.min(key=lambda x: x.price)
        """

        # TODO Add the `default` argument like the builtin `min()`
        return self._minmax(min=True, key=key)

    def _minmax(self, min, key):
        """ Consolidates logic used by ``entities.max`` and
        ``entities.min``.
        """
        extreme = None
        for e in self:
            if extreme:
                if min:
                    if key(e) < key(extreme):
                        extreme = e
                else:
                    if key(e) > key(extreme):
                        extreme = e
            else:
                extreme = e
        return extreme

    def where(self, p1, p2=None):
        """ Returns an entities collection containing a subset of
        ``self`` based on the conditions provided by the parameters.

        :param: p1 type|str|callable:
            if type:
                If p1 is a ``type``, the subset will only include items
                from ``self`` that are the exact type:

                # Get all products from ``prods`` where the subtype of
                # product is a ``service``. This would presumably
                # exclude all the ``goods``.
                srvs = prods.where(service)

                # Assert
                for prod in prods1:
                    assert type(prod) is service

            if str:
                If p1 is a str, then it is used in conjunction with p2
                to select all entity objects that have a given attribute
                value pairing::
                    
                    # Get all products that have a category attribute
                    # equal to 'Accessories'
                    prods1 = prods.where('category', 'Accessories')

                    # Assert
                    for prod in prods1:
                        assert prod.category == 'Accessories'

            if callable:
                If p1 is a callable, the callable is used to test each
                entity for inclusion for the subset::

                    # Create the callable
                    def f(e):
                        return e.name.startswith('Hammer')

                    # Pass the callable to ``where``
                    prods1 = prods.where(f)

                    # Assert that the callable selected only products
                    # whose name starts with 'Hammer'
                    for prod in prods1:
                        assert prod.name.startswith('Hammer')
        """
        if type(p1) == type:
            cls = self.__class__
            return cls([x for x in self if type(x) == p1])

        if type(p1) is str:
            # TODO Write test for this condition

            if p2 is None:
                raise ValueError()

            # If p1 is a str, it is an attribute and we should test it
            # against p2
            attr, operand = p1, p2
            def fn(e):
                return getattr(e, attr) == operand
        else:
            fn = p1

        es = type(self)()
        for e in self:
            if fn(e): es += e

        return es

    @total_ordering
    class mintype:
        def __le__(self, e): return True
        def __eq__(self, e): return (self is e)

    # TODO Test reverse parameter
    # TODO It would be cool if ``key`` could be a nested attribute the
    # way rgetattr() works:
    #
    #     inv.terms.sort('termtype.name')
    def sort(self, key, reverse=False):
        """ Sort the items of the collection in place.

        Use ``sorted`` if you want a new, sorted collection to be
        returned while leaving the current collection unsorted.

        :param key str|callable: 
            if str:
                If ``key`` is a str, it is assumed that key is the name
                of an attribute of each of the objects in the collection
                so the collection will be sorted on that attribute::

                   # Sort the goods collection based on name
                   goods.sort('name')

                   # Printing the goods' names will be done in
                   # alphabetical order
                   for good in goods:
                       print(good.name)

            if callable:
                If key specifies a callable, the callable is used to
                extract a comparison key from each element in
                collection::
                    
                    # Sort goods in a case-insensitive way
                    goods.sort(lambda x: x.name.casefold())

                    # Printing the goods' names will be done in
                    # alphabetical order without regard to the name's
                    # case
                    for good in goods:
                        print(good.name)

        :param: reverse bool: If set to True, then the elements are
        sorted as if each comparison were reversed.
        """
        if type(key) == str:
            min = entities.mintype()
            def key1(x):
                v = getattr(x, key)
                # None's don't sort so do this
                return min if v is None else v
        elif callable(str):
            # TODO:2fff5b9e This is wrong even though it works. We are
            # testing if the str bulitin is callable, which it is, so as
            # long as key is not str, key will be assaigned to key1. The
            # above should be changed to `elif callable(key)` and their
            # should be an `else` that raises a TypeError.
            key1 = key

        self._ls.sort(key=key1, reverse=reverse)

    def sorted(self, key, reverse=False):
        """ Returns a entities collection containing the elements of
        this collection sorted by the ``key``.

        This method works exactly as ``entities.sort`` does except that,
        instead of sorting the collection in place, a new, sorted
        collection is return, and no changes are made to the current
        collection (``self``).

        See the parameter descriptions at ``entities.sort`` for details.
        """
        if type(key) == str:
            min = entities.mintype()
            def key1(x):
                v = getattr(x, key)
                # None's don't sort so do this
                return min if v is None else v
        elif callable(str):
            # TODO:2fff5b9e This is wrong even though it works. We are
            # testing if the str bulitin is callable, which it is, so as
            # long as key is not str, key will be assaigned to key1. The
            # above should be changed to `elif callable(key)` and their
            # should be an `else` that raises a TypeError.
            key1 = key

        return type(self)(initial=sorted(self._ls, key=key1, reverse=reverse))

    def enumerate(self):
        """ Returns an enumeration object similar to the way the PYthon
        builtin ``enumerate()`` does::

            # Print each entity in es preceded by a zero-based index
            for i, e in es.enumerate():
                print(i, e)

        Note that behind this method uses func.enumerate() instead of
        the builtins.enumerate, so you can use its features::

            for i, e in es.enumerate():
                if i.first:
                    print(f'{e} is the first object in the collection')
                
                if i.last
                    print(f'{e} is the last object in the collection')
        """
        for i, e in enumerate(self):
            yield i, e

    def clear(self):
        """ Remove each element in teh collection.

        Note that this method uses ``entities.remove`` is used which
        means that the onremove event will be called for each of the
        elements removed.
        """
        self.remove(self)

    def __delitem__(self, key):
        """ Remove an element using an indexer::

            # Remove the fourth element from the collection.
            del es[3]

        Note that this method uses ``entities.remove`` is used which
        means that the onremove event will be called for the element
        removed.
        """
        # TODO Write test. This will probably work but is only used in
        # one place at the time of this writing. We should also test for
        # `key` being a slice.
        e = self[key]
        self.remove(e)

    def remove(self, e):
        """ Remove ``e`` from the collection.

        Typically, ``e`` is simple an entity object presumend to be in
        the collection. If it is found in the collection, it will be
        removed, and the onremove event will be raised.

        ``e`` can be other types object objects as well such as
        ``entities``, ``callables``, ``int``s and ``str``. The behavor
        for removing these types is detailed in the :param: section
        below.

        :param: e entity|entities|callable|int|str: The entity or a
        way of referencing entity objects to be removed.
            
            Given:
                assert isinstance(es, entities)

                assert  es.first.name   =  'berp'
                assert  es.second.name  =  'derp'
                assert  es.third.name   =  'gerp'
                assert  es.fourth.name  =  'herp'
                assert  es.fifth.name   =  'merp'
                assert  es.sixth.name   =  'perp'

            if entity:
                If e is an entity, it will simply be removed, if it
                exists in the collection, and the onremove event will be
                raised.

                    # Remove gerp
                    es.remove(es.third)

            if entities:
                if e is an entities collection, each entity in e will be
                removed from the collection. Each removal will result in
                onremove being raised.

                    # Remove herp and merp
                    rms = es.where(
                        lambda x: x.name == 'herp' or x.name == 'merp'
                    )
                    es.remove(rms)

            if callable:
                if e is a callable, e will be pased to self.where. Each
                entity in the resulting entities collection will remove.
                
                    # Remove derp
                    es.remove(lambda x: x.startswith('d'))

            if int:
                if e is an int, e will be passed to the indexor. The
                resulting entity will be removed and onremove will be
                raised.

                    # Remove perp
                    es.remove(-1)

            if str
                if e is a str, it will be pased to sel.getindex and the
                resulting index will be passed to the indexor to be
                removed.

                    # Remove berp
                    es.remove('berp')
        """
        if isinstance(e, entities):
            rms = e
        elif isinstance(e, entity):
            rms = [e]
        elif callable(e) and not isinstance(self, event):
            rms = self.where(e)
        elif isinstance(e, int):
            rm = self._ls[e]
            del self._ls[e]
            self.onremove(self, entityremoveeventargs(rm))
            return
        elif isinstance(e, str):
            ix = self.getindex(e)
            return self.remove(ix)
        else:
            rms = [e]

        for i in range(self.count - 1, -1, -1):
            for rm in rms:
                if rm is self[i]:
                    del self._ls[i]
                    self.onremove(self, entityremoveeventargs(rm))
                    break

        return type(self)(rms)

    def __isub__(self, e):
        """ Allows entities to be removed from the collection using the
        -= operator::

            e = es.last         # Get last entity in collecton
            es -= e             # Remove it
            assert e not in es  # assert its no longer there

        :param: e entity|entities|callable|int|str: The entity or a
        way of referencing entity objects to be removed. For example, a
        collection of entities can be removed in one line::

            # Get half the entities from es and put them in es1
            es1 = es.where(lambda x: x.getindex() % 2)

            # Remove those entities en es1 from es
            es -= es1
        
        ``e`` can be a number of different things. Since this method is
        a thin wrapper around self.remove, see the documentation for the
        ``e`` parameter in that method's docstring for more options.
        """
        self.remove(e)
        return self

    def shift(self):
        """ Remove the first element in the collection and return it. If
        the collection is empty, None will be returned.
        """
        return self.pop(0)

    def pop(self, ix=None):
        """ Removes an element from the collection and returns it. If no
        arguments are provided, the last element of the collection is
        removed and returned. 

        Note that the onremove event will be raised if an element is
        removed. 

        :param: ix NoneType|int|str: The index or a why of describing
        what will be remove.
            
            if int:
                The ix is an int, the element is searched for by its
                index, removed and returned.

            if NoneType:
                If ix receives no arguments, or the argument is None,
                the last element of the collection will be removed and
                returned.

            if str:
                If ix is a str, self.getindex is used to convert ix into
                a numeric index value. That values is used to look up
                the element by index. The element is then removed from
                the collection and returned.
        """

        # TODO I think that None should be returned if no element is
        # found. For example, if ix is an int that doesn't
        # represent an element in the collection, an IndexError is
        # currently raised. I think that in that case, None should be
        # returned and the onremove event should not be raised.
        if self.count == 0:
            return None

        if ix == None: 
            e = self.last
            self._ls.pop()      # TODO Why don't we get e from this line
        elif type(ix) is int:
            e = self[ix]
            self._ls.pop(ix)
        elif type(ix) is str:
            ix = self.getindex(ix)
            e = self[ix]      
            self._ls.pop(ix)

        eargs = entityremoveeventargs(e)
        self.onremove(self, eargs)
        return e

    def reversed(self):
        """ Return a generator that allows the collection to be
        iterated over starting from the end to the beginning::

            for e in es.reversed():
                # The first e to be printed will be the last element in
                # es, the second will be the penultimate, and so on.
                print(e)

        To reverse the order of the ordering of the collection in place,
        see the ``entities.reverse()`` method.
        """
        for e in reversed(self._ls):
            yield e

    def reverse(self):
        """ Reverses the order of the elements within the collection.
        Returns nothing::

            # Given a collection of 3
            assert es.count == 3

            # Get the elements
            first   =  es.first
            second  =  es.second
            third   =  es.third

            # In-place reverse elements
            es.reverse()

            # es has been reversed
            assert third   is  es.first
            assert second  is  es.second
            assert first   is  es.third
        """
        self._ls.reverse()

    @property
    def ubound(self):
        """ Return the number of the items in the collection minus 1. If
        there are no elements, None is returned.

        ``ubound`` is based on the old BASIC function of the same name.
        For some use cases, its semantics can be of value since, by
        definition, its value is exactly the largest value that
        can be given to the indexer without error, i.e., the *upper
        bound*::

            assert es.ispopulated
            es[es.ubound]      # Never an IndexError
            es[es.ubound + 1]  # Always and IndexError

        However, for the overwhelming majority of use cases, this is the
        wrong property to use and ``entities.count`` should be used
        instead.
        """
        if self.isempty: return None
        return self.count - 1

    def move(self, ix, e):
        """ NOTE Currently not implemented.
        
        Remove ``e`` from the collection, causing the onremove event to
        fire, then insert it before the element at index ``ix`` in the
        collection.

        :param: ix int: The index the element will be moved before.

        :param: e entity: The entity to move.
        """
        raise NotImplementedError('TODO')

    def moveafter(self, ix, e):
        """ Remove ``e`` from the collection, causing the onremove event to
        fire, then insert it after the element at index ``ix`` in the
        collection.

        :param: ix int: The index the element will be moved after.

        :param: e entity: The entity to move.
        """
        self.remove(e)
        self.insertafter(ix, e)

    def insert(self, ix, e):
        """ Insert the entity ``e`` into the collection before the
        element at index `ix`. This method is identical to
        ``entities.insertbefore``.

        :param: ix int: The index of the element that ``e`` will be
        inserted before.

        :param: e entity: The entity to be inserted.
        """
        self.insertbefore(ix, e)

    def insertbefore(self, ix, e):
        """ Insert the entity ``e`` into the collection before the
        element at index `ix`. 

        :param: ix int: The index of the element that ``e`` will be
        inserted before.

        :param: e entity: The entity to be inserted.
        """
        # TODO Support inserting collections
        self._ls.insert(ix, e)
        try:
            self.onadd(self, entityaddeventargs(e))
        except AttributeError as ex:
            msg = str(ex)
            msg += '\n' + 'Ensure the superclass\'s __init__ is called.'
            raise AttributeError(msg)

    def insertafter(self, ix, e):
        """ Insert the entity ``e`` into the collection after the
        element at index `ix`. 

        :param: ix int: The index of the element that ``e`` will be
        inserted after.

        :param: e entity: The entity to be inserted.
        """
        self.insertbefore(ix + 1, e)

    def unshift(self, e):
        """ Insert the entity ``e`` at the begining of the collection.

        Note that the name ``unshift`` is barrowed from Perl to imply
        pushing an element onto the beginning of a stack (i.e., an array
        or list). This is useful when stack semantics are needed.
        However, within the Core framework, the << operator should be
        used::

            # Only when stack sementics are needed.
            es.unshift(e)

            # Otherwise, use the << operator
            es << e

            # For ether of the above, the following can be asserted:
            assert es.first is e

        :param: e entity: The entity to be inserted.
        """
        # TODO: Return entities object to indicate what was unshifted
        self.insertbefore(0, e)

    def push(self, e):
        """ Append ``e`` to the end of the collection.

        Note that the name ``push`` is barrowed from Perl to imply
        pushing an element onto the beginning of a stack (i.e., an array
        or list). This is useful when stack semantics are needed.
        However, within the Core framework, the += operator should be
        used::

            # Only when stack sementics are needed.
            es.push(e)

            # Otherwise, use the += operator
            es += e

            # For ether of the above, the following can be asserted:
            assert es.last is e

        :param e entity: The entity being pushed.
        """
        self += e

    def give(self, es):
        """ Move the elements self to es. Clear es. A slice parameter
        can be used to limit what is moved. """

        # TODO: Write test
        es += self
        self.clear()

    def __contains__(self, e):
        """ Returns True if ``e`` is in ``es``::

            assert e not in es

            es += e

            assert e in es

        :param e entity: The entity being sought.
        """
        if type(e) in (int, str):
            e = self(e)

        return self.indexes['identity'](e).ispopulated

    def __lshift__(self, e):
        """ Implements the << operator. See the docstring at
        ``entities.unshift`` for details.

        :param e entity: The entity being unshifted.
        """
        self.unshift(e)
    
    def append(self, obj, uniq=False, r=None):
        """ Appends ``obj`` to the end of the collection.

        The name append is based of Python's list's ``append`` method.
        It is useful when you want an entities collection to behave like
        a list. However, the canonical way to append to a collection is
        to use the += operator::
            
            # Behave like a list
            es.append(e)

            # Canonical 
            es += e

            # Either of the above lines will allow the following to be
            # asserted

            assert es.last is e

        :param: obj entity: The entity being appended.

        :param: uniq bool: If True, an append will only happen if the
        entity is not already in the collection.

        :param: r entities: For internal use only.
        """

        # Create the return object if it hasn't been passed in
        # TODO s/==/is/
        if r == None:
            # We use a generic entities class here because to use the subclass
            # (type(self)()) would cause errors in subclasses that demanded
            # positional arguments be supplied.
            r = entities()

        if isinstance(obj, entity):
            t = obj

        elif hasattr(obj, '__iter__'):
            for t in obj:
                if uniq:
                    if t not in self:
                        self.append(t, r=r)
                else:
                    self.append(t, r=r)
            return r
        else: 
            raise ValueError(
                'Unsupported object appended: ' + str(type(obj))
            )

        if uniq and t in self:
            return r

        r._ls.append(t)

        self.onbeforeadd(self, entityaddeventargs(t))

        self._ls.append(t)

        self.onadd(self, entityaddeventargs(t))

        return r

    def __iadd__(self, t):
        """ Implement the += operator. See the docstring at
        ``entities.append`` for details.
        """
        self.append(t)
        return self

    def __ior__(self, e):
        """ Implements the |= operator on collections. ``e`` will be
        appended to the collection unless it already exists in the
        collection. This is the canonical way to do unique appends

            assert e not in es

            # Noncanonical
            es.append(e, uniq=True)

            # Canonical 
            es |= e

            # Either of the above lines will allow the following to be
            # asserted
            assert es.last is e
        """
        self.append(e, uniq=True)
        return self

    def __add__(self, es):
        """ Implements the + operator. This operator combines two
        colections together and returns a new collection with the
        elements from the first two::

            # e is in es; e1 is in es1
            assert e in es
            assert e1 in es1

            # Add them together to get es2
            es2 = es + es1

            # es2 now contains e and e1
            assert e in es2
            assert e1 in es2

        :param: es entity|entities: The entity object or the entities
        collection used to concatentate with self.
        """
        r = type(self)()
        r += self
        r += es
        return r

    def __sub__(self, es):
        """ Implement the - operator. The - operator removes an entity
        object, or a collection of entity objects, from the existing
        entities collection producing a new entities collection of the
        same type. 

            # e1 is in es and es1
            assert e in es
            assert e1 in es
            assert e1 in es1

            # Subtract the elements from es that are in es1 (e1)
            es2 = es - es1

            # Alternatively, we could have done: es2 = es - e1

            # es2 will contain e but not e1
            assert e in es2
            assert e1 not in es2

        :param: es entity|entities: The entity object or the entities
        collection used to subtract from self.
        """
        r = type(self)()

        # If es is not an iterable, such as an entitities collection,
        # assume it is an entity object and convert it into a collection
        # of one.
        if not hasattr(es, '__iter__'):
            es = entities([es])

        for e in self:
            if e not in es:
                r += e
        return r

    @property
    def count(self):
        """ Returns the number of elements in the collection.

        Note: if list semantics are needed, the builtin len() function
        can be used instead::
            
            assert len(es) == es.count

        However, the ``count`` property is the prefered way to get the
        collection's count within the framework.
        """
        return len(self._ls)

    def getcount(self, qry):
        """ The the count of elements after filtering with a where
        predicate. The following can always be asserted::

            # Given p is a where predicate
            assert es.count(p) == es.where(p).count

        See the ``where`` method for details on the where predicate.
        """
        # TODO Test
        return self.where(qry).count

    def __len__(self):
        """ Returns the number of elements in the collection. This is a
        Python magic function that allows getting the collection's count
        with the builtin len() function.

            es = entities()
            assert len(es) == 0

            es += e

            assert len(es) == 1

        Note: if list semantics are needed, the builtin len() function
        can be should be used.  However, the ``count`` property is the
        prefered way to get the collection's count within the framework.
            
            assert len(es) == es.count
        """
        return self.count

    @property
    def isempty(self):
        """ Returns True if there are no elements in the collection.

        Both statements are equivalent, but the later is prefered

            if es.count == 0:
                ...

            if es.isempty:
                ...
        """
        return self.count == 0

    @property
    def issingular(self):
        """ Returns True if there is exactly one element in the
        collection.

        Both statements are equivalent, but the later is prefered

            if es.count == 1:
                ...

            if es.issingular:
                ...
        """
        return self.count == 1

    @property
    def isplurality(self):
        """ Returns True if there is 2 or more elements in the
        collection.

        Both statements are equivalent, but the later is prefered

            if es.count > 1
                ...

            if es.isplurality::
                ...
        """
        # TODO This should be call isplural
        return self.count > 1

    @property
    def ispopulated(self):
        """ Returns True if there is 1 or more elements in the
        collection.

        Both statements are equivalent, but the later is prefered

            if es.count >= 1
                ...

            if es.ispopulated::
                ...
        """
        return not self.isempty

    def __repr__(self):
        """ Returns a string representation of the collection and each
        of the elements in it.
        """
        return self._tostr(repr)

    def __str__(self):
        """ Returns a string representation of the collection and each
        of the elements in it.
        """
        return self._tostr(str)

    def _tostr(self, fn=str, includeHeader=True):
        """ Returns a string representation of the collection and each
        of the elements in it.

        :param: fn: callable: Each element is passed to this function to
        get its string representation. By default, the function is the
        builtin str() function.

        :param: includeHeader bool: Include a header in the string
        representation. 
        """
        if includeHeader:
            r = '%s object at %s' % (type(self), hex(id(self)))

            try:
                r += ' count: %s\n' % self.count
            except:
                # self.count can raise exceptions (e.g., on object
                # initialization) so `try` to include it.
                pass
            indent = ' ' * 4 
        else:
            r = ''
            indent = ''

        try:
            for i, t in enumerate(self):
                r += indent + fn(t) + '\n'
        except Exception as ex:
            # If we aren't able to enumerate (perhaps the self._ls hasn't been
            # set), just ignore.
            pass

        return r

    def __setitem__(self, key, item):
        """ Implements an indexer that can be assigned an element.

            es[0] = e
            assert es.first is e

        The ``key`` can be a slice and the ``item`` can be an iterable::

            # Create a collection and add a couple of elements to it
            es = entities()
            es += element()
            es += element()

            # Assign the first two elements of es to the first two
            # positions of es1.
            es1[:1] = es

            assert es1.first is es.first
            assert es1.second is es.second
        """
        e = self[key]
        self._ls[key]=item

        # If key is a slice. then what was removed and what was added
        # could have been an iterable. Therefore, we need to convert
        # them to iterables then raise the onadd and onremove events for
        # each entity that had been removed and added.
        items  =  item  if  hasattr(item,  '__iter__')  else  [item]
        es     =  e     if  hasattr(e,     '__iter__')  else  [e]
            
        for e, item in zip(es, items):
            if item is e:
                continue
            self.onremove(self, entityremoveeventargs(e))

        # TODO: Don't raise onadd unless `item is in es`. See the
        # onremove logic below.
        for item in items:
            self.onadd(self, entityaddeventargs(item))

    def __getitem__(self, key):
        """ Implements an indexer for the collection::

            # Create a collection and add an entity to it
            es = entities()
            e = entity()
            es =+ e

            # Use the indexer to access the first element and assert it
            # is e.
            assert e is es[0]

        If an element can't be found, an IndexError is raised.

        Above, ``key`` is an int. However, key can also be a slice or a
        str. See below for details.

        :param: key int|slice|str: The index value.
            if int:
                The value is used as a zero-based index, and gets an
                element from the collection the same way as indexing a
                Python list does.

            if slice:
                Works the same as passing a slice to a Python list::

                    # Get the first two elements from the
                    # collection.
                    es1 = es[0:2]

                    # A new collection is created and returned.
                    assert type(es1) is type(es)

            if str:
                Assumes each element has an ``id`` property. The index
                value will be tested against the value of this property
                and the first one found will be used::

                    es = entities()
                    for s in ('herp', 'derp'):
                        es += entity()
                        es.last.id = s

                    assert es['herp'] is es.first
                    assert es['derp'] is es.second

                If the elements do not have an id property, their
                ``name`` property will be used. If they have neither,
                an IndexError will be raise.
        """
        if isinstance(key, int):
            return self._ls[key]

        if isinstance(key, slice):
            return type(self)(initial=self._ls[key])

        try:
            ix = self.getindex(key)
        except ValueError as ex:
            raise IndexError(str(ex))

        return self[ix]

    def getprevious(self, e):
        """ Get the element that comes before ``e``.

            # Assuming es is a collection that has two or more elements
            assert es.getprevious(es.second) is es.first
            assert es.getprevious(es.last) is es.penultimate

        :param: e entity: The entity immediatly after which the return
        value will exist in the collection.
        """
        ix = self.getindex(e)
        return self(ix - 1)

    def getindex(self, e):
        """ Return the first index of e in the collection.

        This is similar to list.index except here we use the `is`
        operator for comparison instead of the `==` operator when ``e``
        is an instance of ``entity``. See below for details on the way
        getindex(e) works when ``e`` is a str.

        If entity cannot be found in the collection, a ValueError will
        be raised.

        :param: e entity|str:
            if entity:
                Returns the index number of ``e`` in the collection.

            if str:
                Searches the collection for an element where the id
                attribute equals ``e``. If found, returns the index
                number for that entity. If the element does not have an
                ``id`` attribute, its ``name`` attribute is used
                instead. If elements have neither, a ValueError will be
                raised.
        """

        # TODO:OPT We may be able to cache this and invalidate the cache
        # using the standard events
        if isinstance(e, entity):
            for ix, e1 in enumerate(self):
                if e is e1: return ix
        elif type(e) is str:
            # TODO Write test
            for i, e1 in enumerate(self._ls):
                if hasattr(e1, 'id'):
                    if e1.id == e:   return i
                elif hasattr(e1, 'name'):
                    if e1.name == e: return i

        # Raise ValueError in imitation of list.index()'s behavior
        raise ValueError("'{}' is not in the collection".format(e))

    @property
    def first(self): 
        """ Returns the first element in the collection. If the
        collection is empty, None is returned.
        """
        return self(0)

    @first.setter
    def first(self, v): 
        """ Sets the first element of the collection.
        """
        self[0] = v

    @property
    def second(self): 
        """ Returns the second element in the collection. If has fewer
        than 2 elements, None is returned.
        """
        return self(1)

    @second.setter
    def second(self, v): 
        """ Sets the second element of the collection.
        """
        self[1] = v

    @property
    def third(self): 
        """ Returns the second element in the collection. If has fewer
        than 3 elements, None is returned.
        """
        return self(2)

    @third.setter
    def third(self, v): 
        """ Sets the third element of the collection.
        """
        self[2] = v

    @property
    def fourth(self): 
        """ Returns the second element in the collection. If has fewer
        than 4 elements, None is returned.
        """
        return self(3)

    @fourth.setter
    def fourth(self, v): 
        """ Sets the fourth element of the collection.
        """
        self[3] = v

    @property
    def fifth(self): 
        """ Returns the second element in the collection. If has fewer
        than 5 elements, None is returned.
        """
        return self(4)

    @fifth.setter
    def fifth(self, v): 
        """ Sets the fifth element of the collection.
        """
        self[4] = v

    @property
    def sixth(self): 
        """ Returns the second element in the collection. If has fewer
        than 6 elements, None is returned.
        """
        return self(5)

    @sixth.setter
    def sixth(self, v): 
        """ Sets the sixth element of the collection.
        """
        self[5] = v

    @property
    def seventh(self): 
        """ Returns the second element in the collection. If has fewer
        than 7 elements, None is returned.
        """
        return self(6)

    @seventh.setter
    def seventh(self, v): 
        """ Sets the seventh element of the collection.
        """
        self[6] = v

    @property
    def last(self): 
        """ Return the last element in the collection. If the collection
        has zero elements, None will be returned.
        """
        return self(-1)

    # TODO Add tests
    @last.setter
    def last(self, v): 
        """ Set the last element in the collection.
        """
        self[-1] = v

    @property
    def ultimate(self): 
        """ A synonym of entities.last. 
        """
        return self.last

    @ultimate.setter
    def ultimate(self, v): 
        """ A synonym of entities.last. 
        """
        self.last = v

    @property
    def penultimate(self): 
        """ Returns the second-to-the-last element of the collection.
        """
        return self(-2)

    @penultimate.setter
    def penultimate(self, v): 
        """ Sets the second last element in the collection.
        """
        self[-2] = v

    @property
    def antepenultimate(self): 
        """ Returns the third last element in the collection.
        """
        return self(-3)

    @antepenultimate.setter
    def antepenultimate(self, v): 
        """ Sets the third last element in the collection.
        """
        self[-3] = v

    @property
    def preantepenultimate(self): 
        """ Returns the fourth last element in the collection.
        """
        return self(-4)

    @preantepenultimate.setter
    def preantepenultimate(self, v): 
        """ Sets the fourth last element in the collection.
        """
        self[-4] = v

    @property
    def brokenrules(self):
        """ Collates the broken rules for each of the elements in the
        collection and returns them as a new ``brokenrules`` collection.
        """
        r = brokenrules()
        for e in self:
            brs = e.brokenrules
            if not isinstance(brs, brokenrules):
                msg = 'Broken rule is an invalid type. '
                msg += 'Ensure you are using the @property decorator '
                msg += 'and the property is returning a brokenrules '
                msg += 'collection.'
                raise ValueError(msg)
            r += brs
        return r

    @property
    def isvalid(self):
        """ Returns True if there are no broken rules in the collection;
        False otherwise.
        """
        return self.brokenrules.isempty

class entity:
    """ The base class for all entity objects.

    It's recommend that only derivations of ``entity`` be used in
    ``entities`` collection::

        # Create a products entities collection class
        class products(entities):
            pass

        # Create a product entity class
        class product(entity):
            pass

        # Instantiate the products collection
        ps = products()

        # Now we can add product entity objects to it
        ps += product()
        ps += product()

    Perhaps the most noteable feature of the ``entity`` class is its
    ability to define broken rules. Let's recreate the ``product`` class
    from above so it has a brokenrules collection::

        class product(entity):
            def __init__(self):
                self.price = float()
                self.name = str()

            @property
            def brokenrules(self):
                brs = brokenrules()

                if not isinstance(self.name, str):
                    brs += "'name' must be a str"

                if not isinstance(self.price, float):
                    brs += "'price' must be a float"

                return brs

    Now the entity can report on its own validity. This features is
    called entity-centric validation::
        
        # Product will be valid on instantiation
        prod = product()
        assert prod.isvalid
        assert prod.brokenrules.isempty

        # Lets assign the wrong types to name and price
        prod.name = int()
        prod.price = str()
        assert not prod.isvalid  # invalid
        assert prod.brokenrules.count == 2  # Two broken rules
    
    According to the ``brokenrules`` property defined in the ``product`
    class above, we shouldn't be able to a a name attribute that is not
    a str, or a price attribute that is not a float. Consequently,
    assigning an int to ``name`` and a str to ``price`` causes two
    broken rules to be reported. Note that Broken rules are by no means
    limited to type checking; any logic that can be used to ensure an
    object is valid can and should go in the brokenrules property.
    The meaning of validity is arbitrary. It can mean that the object is
    prepared to enter a different system, such a a third-party API. In
    practices, validity typically means the object is ready to be saved
    to the database.

    Derived entity/entities pairings are useful for many things, but
    their most frequent use is probably the ORM classes ``orm.entities``
    and ``orm.entity``. From these classes, all the General Entity Model
    (GEM) classes derive, basically making up the entire entity and data
    models for the framework.
    """
    def __init__(self):
        self._onaftervaluechange = None
        self._onbeforevaluechange = None

    @property
    def onbeforevaluechange(self):
        """ Returns the entity's ``event`` object that should be fired
        before the value of one of the entity's attributes changes. See
        entity._setvalue().
        """
        if self._onbeforevaluechange is None:
            self._onbeforevaluechange = event()

        return self._onbeforevaluechange

    @onbeforevaluechange.setter
    def onbeforevaluechange(self, v):
        self._onbeforevaluechange = v

    @property
    def onaftervaluechange(self):
        """ Returns the entity's ``event`` object that should be fired
        after the value of one of the entity's attributes changes. See
        entity._setvalue().
        """
        if self._onaftervaluechange is None:
            self._onaftervaluechange = event()

        return self._onaftervaluechange

    @onaftervaluechange.setter
    def onaftervaluechange(self, v):
        self._onaftervaluechange = v

    def _setvalue(
        self, field, new, prop, setattr=setattr, cmp=True, strip=True
    ):
        """ A private method that is called to change the value of one
        of the entity's attributes.

        :param: field str: The name of the attribute to change.

        :param: new object: The new value that the attribute should be
        changed to.

        :param: prop str: The name of attribute being changed. Note that
        ``field`` is the actual attribute being change, while ``prop``
        can be more descriptive. For example::

            self._setvalue('_iss', v, 'iss')

        Above, '_iss' is the private attribute to be assigned ``new``,
        while 'iss' is just the public name. 

        :param: setattr callable: The function to use for the call to
        ``setattr``. By default, it is the ``builtins.setattr``
        function, but a user may wish to supply a custom setter
        function.

        :param: cmp bool: Indicates whether ``new`` should be compared
        to the current value. We may not want to compare because getting
        the current value may cause an unnecessary lazy-load of the
        attribute.

        :param: strip bool: If ``new`` is a str, the value will be
        striped by default. This is just a nice feature since most user
        input assumes that trailing whitespace will removed. Setting
        ``strip`` to False will preserve the trailing whitespace.
        """

        # TODO The parameters for this method use non-canonical names.
        # We should: s/new/v and s/field/attr

        # Strip
        if type(new) == str and strip:
            new = new.strip()

        # If we should compare
        if cmp:
            # Get the current value of the attribute
            old = getattr(self, field)

            # old and new are not equal if they are of different type -
            # unless one of those types is NoneType. In other words,
            # setting a previously None value to a non-None value should
            # count as a value change - and vice-versa. However, if
            # neither value is None, a difference in type and equality
            # should exist to count as value change. For example, if old
            # is int(0) and new is bool(False), a value change is
            # happening even though the equality (according to Python)
            # is the same (falsey).
            if old is None or new is None:
                ne = old != new
            else:
                ne = old != new or type(old) is not type(new)

        # If we didn't compare, or we did compare and found that the
        # current value did not equal (ne) the new value.
        if not cmp or ne:
            
            # Raise the onbeforevaluechange event
            if hasattr(self, 'onbeforevaluechange'):
                eargs = entityvaluechangeeventargs(self, prop)
                self.onbeforevaluechange(self, eargs)

            if setattr is builtins.setattr:
                try:
                    self.__setattr__(field, new, cmp=cmp)
                except TypeError as ex:
                    msg = (
                        'wrapper __setattr__() takes no '
                        'keyword arguments'
                    )

                    if ex.args[0] == msg:
                        setattr(self, field, new)
                    else:
                        raise
            else:
                # Use custom setattr
                setattr(self, field, new)

            if hasattr(self, 'onaftervaluechange'):
                eargs = entityvaluechangeeventargs(self, prop)
                self.onaftervaluechange(self, eargs)

            # TODO: Return value is new. Add a unit tests for it.
            return new

    def add(self, e):
        """ Return a new collection with self and e contained in it.

            e = entity()
            e1 = entity()
            es = e.add(e1)

            assert es.first is e
            assert es.second is e1

            The canonical way to do this, however, would be to use the +
            operator. See the docstring at __add__ for that notation.
        """
        es = entities()
        es += self
        es += e
        return es

    def __add__(self, t):
        """ Implement the + operator to Return a new collection with
        self and e contained in it.

            e = entity()
            e1 = entity()
            es = e + e1

            assert es.first is e
            assert es.second is e1
        """
        return self.add(t)

    @property
    def brokenrules(self):
        """ Return an empty brokenrules collection indicating there are
        no validation errors. Classes that inherit from ``entity`` are
        expected to override this property to return any of their broken
        rules.
        """
        return brokenrules()

    @property
    def isvalid(self):
        """ Indicates the entity is valid.

        Validity usually, and by default, means that there are no broken
        rules. It's up to the class that inherits from ``entity`` to
        define what validity is. orm.entity objects, for example,
        defines validity as the state it is in when all its attributes
        are valid and the object can be safely saved to the database.
        """
        return self.brokenrules.isempty

class BrokenRulesError(Exception):
    """ An exception that is raised when an attempt to use an invalid
    object is made at the wrong time. A typical example is trying to
    save an invalid orm.entity (entity.isvalid == False) to the database
    when it is reporting broken rules from its ``brokenrules`` property.
    """
    def __init__(self, msg, obj):
        """ Create the exception.

        :param: msg str: A brief error message.

        :param: msg str: The invalid object. The invalid object's
        ``brokenrules`` collection will be the place to look for the
        actual broken rules.
        """
        self.message = msg
        self.object = obj

    def __str__(self):
        """ A string representation of the exception along with the
        broken rules.
        """
        obj = self.object
        r = self.message + ' '
        r += '%s at %s' % (type(obj), hex(id(obj))) + '\n'
        for br in obj.brokenrules:
            r += '\t* ' + str(br) + '\n'
        return r

    def __repr__(self):
        """ A string representation of the exception along with the
        broken rules.
        """
        return str(self)

class brokenrules(entities):
    """ A collection of broken rules objects.
    """

    def append(self, o, r=None):
        """ Append a broken rule to the collection.

        Rather than using the append method, use the += operator::

            brs.append('Non-Canonically appended')
            brs += 'Canonically appended'

        :param: o str|brokenrule: The broken rules to append. If o is a
        str, it is converted to a ``brokenrule``.
        """
        if isinstance(o, str):
            o = brokenrule(o)
        super().append(o, r)

    def demand(self, e, prop, 
                     full=False, 
                     isemail=False, 
                     isdate=False,
                     min=None,
                     max=None,
                     precision=None,
                     scale=None,
                     type=None,
                     instanceof=None):

        """ Adds a ``brokenrules`` object to ``self`` if the parameters
        indicate that the value of ``prop`` is invalid::

            # Create a brokenrules collection
            brs = brokenrules()

            # Create an entity. Assign a str to the phonenumber
            # attribute. Later we will demand that the phonenumber
            # should have been an int.
            e = entity()
            e.phonenumber = '234-5678'

            # Demand that the phonenumber attribute is an int.
            brs.demand(e, 'phonenumber', type=int)

            # Since its not, a broken rule will have been added
            assert brs.count == 1

        :param: e object: The entity that has the attribute being
        tested.

        :param: prop str: The attribute being tested.

        :param: full bool: Demand that the value is a non-empty str

        :param: isemail bool: Demand that the value looks like an email
        address.

        :param: isdate bool: Demand that the value of the attr is a
        datetime.

        :param: min int: Demand that the value is greater than min. If
        value is a str, bytes, bytearray, the length must be greater
        than min. If value is int or datetime, the value must be
        greater than min.

        :param: max int: Demand that the value is less than max. If
        value is a str, bytes, bytearray, the length must be less
        than max. If value is int or datetime, the value must be
        less than max.

        :param: precision int: Demand that the length of the precision
        of the attribute's value is greater ``precision``. ``type`` must
        be float or decimal.Decimal.

        :param: scale int: Demand that the length of the scale
        of the attribute's value is greater ``scale``. ``type`` must
        be float or decimal.Decimal.

        :param: type type: Demand that the value of the attr is the type
        ``type``. Compare to the ``isinstance`` parameter.

        :param: isinstance type: Demand that the value of the attr is an
        instance of ``instanceof``. Compare to the ``type`` parameter.
        """

        # TODO A lot of lines are greater than 72 characters.

        # TODO Write unit tests

        # TODO Rename prop to attr to be consistent with the frameworks
        # naming convention

        # Get the value of the attribute
        v = getattr(e, prop)

        wrongtype = False
        if v is not None:
            
            # Test the type argument
            if type is not None:
                if builtins.type(v) is not type:
                    self += brokenrule(
                        prop + ' is wrong type', prop, 'valid', e
                    )
                    wrongtype = True

            # Test the instance of argument
            if instanceof is not None:
                if not isinstance(v, instanceof):
                    self += brokenrule(
                        prop + ' is wrong type', prop, 'valid', e
                    )
                    wrongtype = True

        # If ``type`` is a float or decimal, test the ``precision`` and
        # ``scale`` parameter.
        if not wrongtype and type in (float, decimal.Decimal):
            strv = str(v).lstrip('-')
            parts = strv.split('.')

            try:
                decpart = parts[1]
            except IndexError:
                decpart = ''

            msg = None

            if len(strv) - 1 > precision:
                msg = 'number is too long'

            if len(decpart) > scale:
                msg = 'decimal part is too long'

            if msg:
                self += brokenrule(msg, prop, 'fits', e)

        # Test that the value is a non-empty str
        if full:
            if (
                (builtins.type(v) == str and v.strip() == '')
                or v is None
            ):
                self += brokenrule(prop + ' is empty', prop, 'full', e)

        if isemail:
            pattern = r'[^@]+@[^@]+\.[^@]+'
            if v == None or not re.match(pattern, v):
                self += brokenrule(
                    prop + ' is invalid', prop, 'valid', e
                )

        if not wrongtype:
            for i, limit in enumerate((max, min)):
                if limit is not None:
                    try:
                        broke = False
                        if builtins.type(v) in (str, bytes, bytearray):
                            if i == 0:
                                broke = len(v) > limit
                            else:
                                broke = len(v) < limit
                        elif (
                            builtins.type(v) is int 
                            or isinstance(v, datetime)
                        ):
                            if i:
                                broke = v < limit
                            else:
                                broke = v > limit
                    except TypeError:
                        # If len(v) raises a TypeError then v's length
                        # can't be determined because it is the wrong
                        # type (perhaps it's an int). Silently ignore.
                        # It is the calling code's responsibility to
                        # ensure that the correct type is passed in for
                        # the cases where the 'type' argument is False.
                        pass
                    else:
                        # property can only break the 'fits' rule if it
                        # hasn't broken the 'full' rule. E.g., a
                        # property can be a string of whitespaces which
                        # may break the 'full' rule. In that case, a
                        # broken 'fits' rule would't make sense.
                        if broke:
                            if not self.contains(prop, 'full'):
                                types = (str, bytes, bytearray)
                                if builtins.type(v) in types:
                                    if i == 0:
                                        msg = prop 
                                        msg += ' is too long'
                                    else:
                                        msg = prop
                                        msg += ' is too short'
                                elif (
                                    builtins.type(v) is int 
                                    or isinstance(v, datetime)
                                ):
                                    msg = prop + ' is out of range'
                                else:
                                    raise NotImplementedError()

                                self += brokenrule(msg, prop, 'fits', e)

        if isdate:
            if builtins.type(v) != datetime:
                self += brokenrule(prop + " isn't a date", prop, 'valid', e)

    def contains(self, prop=None, type=None):
        """ Test if this collection contains a broken rule with an
        attribute caled ``prop`` and/or a broken rule with a type of
        ``type``::
            if brs.contains('email', 'full'):
                ...

        :param: prop str: The broken rule's attribute.

        :param: type str: The type of broken rule ('full', 'valid',
        'fits', 'empty', 'unique').

        """
        for br in self:
            if (prop == None or br.property == prop) and \
               (type == None or br.type     == type):
                return True
        return False

class brokenrule(entity):
    """ Represents a broken rule.

    A broken rule is an instance of a business rule that has been violated
    within an entity objects. Usually, this is a validation rule. 
    
    For example, lets say we have a ``customer`` object that has an
    email address property::

        cust = customer()
        cust.email = 'jhogan'

    The above email address doesn't look correct. Where is the @ sign
    and the TLD? We wouldn't want this customer to be saved to the
    database as it stand now::

        assert cust.brokenrules.ispopulated

        try:
            cust.save()
        except db.BrokenRulesError:
            assert True
        else:
            assert False

    Looks like the customer object has detected the broken rule. Lets
    look at the first broken rule in the collection::

        assert cust.brokenrules.first.message == 'email is invalid'

    The author of the customer class has ensured that badly formatted
    email addresses are detected. We can use the brokenrules collection
    here to report to the user the problem. Perhaps they are adding a
    new customer to the database using a form. In this case, the UI
    developer can tell them which form field is having the problem.

    Note that you will usually see broken rules handled in an a more
    standardized way by classes that inherit from orm.entity. However,
    there still is the option of creating classes that inherit directly
    from entities.entities, and those classes can generate brokenrules
    however they like.
    """
    def __init__(self, msg, prop=None, type=None, e=None):
        """ Creates a new broken rule.

        :param: msg str: The human readable message explaining the
        validation error.

        :param: prop str: The name of the attribute that is invalid.

        :param: type str: The type of broken rule ('full', 'valid',
        'fits', 'empty', 'unique')

        :param: e entities.enitites: The entity that this broken rule
        applies to.
        """
        self.message   =  msg
        self.property  =  prop
        self.entity    =  e

        if type is not None:
            if type not in ('full', 'valid', 'fits', 'empty', 'unique'):
                raise Exception('Invalid brokenrules type')

        self.type = type

    def __str__(self):
        """ A string representation of the broken rule.
        """
        return self.message

    def __repr__(self):
        e = type(self.entity)
        e = f'{e.__module__}.{e.__name__}'
        r = f'{type(self).__name__}(\n'
        r += f"    message = '{self.message}',\n"
        r += f"    property = '{self.property}',\n"
        r += f"    type = '{self.type}',\n"
        r += f"    entity = <{e}>,\n"
        r += ')'
        return r
    
class event(entities):
    """ Represents an event.

    Events are fired by objects to inform interested code of an event
    that happend to the object. 
    
    For example, the ``entities`` collection has an event called
    ``onadd``. Whenever an item is added to a collection, the event is
    fired. 

        # Create event handler
        def main_onadd(src, eargs):
            print(f'A {type(eargs.entity)} was appended')

        # Create an entities instance
        es = entities()

        # Subscribe to the onadd event
        es.onadd += main_onadd

        # Append a new entity. This will cause the main_onadd function
        # above to be invoked
        es += entity()

    Notably, multiple event handlers can subscribe to an event. In the
    above code could we could have had multiple event handler invoked
    simply by adding more subscriptions::

        def main_onadd1(self, src, eargs):
            print(f'Hello')

        # Subscribe main_onadd1 to es.onadd. 
        es.onadd += main_onadd

        # Append a new entity. Now, main_onadd and main_onadd1 will be
        # called in that order.
        es += entity()

    Event handlers must conform to the signature discribed above::

        # For function or static methods
        def handler(src, eargs):

        # For instance methods
        def handler(self, src, eargs):

    The src parameter is a reference to the object that fired the event.
    The eargs parameter is an instance of a subclass of ``eventargs``.
    ``eventarg`` subclasses contain the information needed by a specific
    event. For example, the eventargs that onadd uses is called
    ``entityaddeventargs``. This object contains the ``entity`` attribute
    used above in the handler.
    """
    def __call__(self, src, e):
        """ Fires the event. Any subscribers (event handlers) to this
        event will be invoked.

        :param: src object: The source of the event. This is usually a
        reference to the object that fired the event.

        :param: e eventarg: An instance of a subtype of eventargs. This
        contains the specific arguments needed to be passed to the event
        handlers for any given event.
        """

        # TODO Rename e to eargs here to be consistent with convention.

        # The ``event`` itself is a collection of callables. Simply
        # interate over self and call each event handler one at a time.
        for callable in self:
            callable(src, e)

    def append(self, fn):
        """ Subscribe an event handler to the event. The event handler
        will be appended to the event object's internal collection of
        subscribers which will be invoked when the event is fired.

        :param: fn callable: The event handler being subscribed to the
        event. This can be any callable with the signature::

            def fn(src: object, eargs: eventargs)
        """
        # TODO Rename fn to f to conform to conventions
        if not callable(fn):
            raise ValueError('Event must be callable')

        if isinstance(fn, event):
            raise ValueError('Attempted to append event to event collection.')
            
        self._ls.append(fn)

    def remove(self, fn):
        """ Unsubscribe an event handler from this event. Once the
        handler is unsubscribed, it will no longer be invoked when the
        event is fired.

        Note that as with subscribing, the -= operator is used to
        unsubscribe from an event.

            # Create a handler
            def myhandler(src, eargs):
                ...

            # Create an entities collection
            es = entities()

            # Subscribe the handler to the onadd event
            es.onadd += myhandler

            # Unsubscribe the handler from the onadd event
            es.onadd -= myhandler

        :param: fn callable: The event handler that needs to be
        unsubscribed.
        """
        # TODO Rename fn to f to conform to conventions
        if not callable(fn):
            # TODO Change to TypeError
            raise ValueError('Event must be callable')

        for i in range(self.count):
            # NOTE It was noticed that an identity test (i.e, test that
            # use the is operator) wouldn't match the bound method being
            # removed.  Bound method id's (id(obj.method)) seem to
            # change over time.  However, an equality test does match
            # bound method which is why we use the equality operator
            # below.
            if fn == self[i]:
                del self._ls[i]
                break

class eventargs(entity):
    """ The base class for all event argument classes. 

    An event argument class encapsulates the data passed to event
    handlers by the code that fires the event. For example, an
    ``entityaddeventargs`` object is passed to any event handler that
    subscribes to the entities.onadd event whenever an entity is
    appended. See the docstring at entityaddeventargs for code that
    details the way eventargs work.
    """

class entityaddeventargs(eventargs):
    """ The eventargs class called after an entity is succesfully
    appended to an entities collection::

        # Create the event handler. `eargs` will be a reference to the
        # entityaddeventargs object created by the ``entities`` class.
        def i_handle_the_on_add_event(src, eargs):
            
            # Assert eargs type
            assert type(eargs) is entityaddeventargs

            # Notice that eargs's `entity` attribute is a reference to
            # the entity that is added.
            assert eargs.entity.name == 'The added one'

        # Create an entity and call in "The added one"
        e = entity()
        e.name = 'The added one'

        # Create entities collection
        es = entities()

        # Append the entity to es. This will end up invoking
        # i_handle_the_on_add_event. It's eargs argument will have an
        # attribute called `entity` which is a reference `e`. That's how
        # it will know what was appended.
        es += e
    """
    def __init__(self, e):
        """ Create the eventarg.

        :param: e entity: The entity being appended.
        """
        self.entity = e

class entityremoveeventargs(eventargs):
    """ The eventargs class called after an entity is succesfully
    removed from an entities collection::
    """
    def __init__(self, e):
        """ Create the eventarg.

        :param: e entity: The entity being removed.
        """
        self.entity = e

class entityvaluechangeeventargs(eventargs):
    """ The eventargs class called when the value of an attribute in an
    ``entity`` is changed. Used by both the onbeforevaluechange and
    onaftervaluechange.
    """
    def __init__(self, e, prop):
        """ Create the eventarg.

        :param: e entity: The entity whose attribute is being assigned a
        new value.

        :param: prop str: The name of the attribute that is being
        changed.
        """
        # TODO Change prop to attr to conform to convention
        self.property = prop
        self.entity = e

# TODO Remove this eventargs. This appears to be dead code.
class appendeventargs(eventargs):
    def __init__(self, e):
        self.entity = e

class indexes(entities):
    """ A collection of index objects.
    """
    def __init__(self, cls):
        super().__init__()
        self.class_ = cls
        
    def __getitem__(self, name):
        if type(name) == int:
            return super().__getitem__(name)

        for ix in self:
            if ix.name == name:
                return ix
        return None

    def append(self, ix, uniq=None, r=None):
        ix.indexes = self
        return super().append(ix, uniq, r)
        
class index(entity):
    """ Represents an index.

    ``entities`` collection use indexes to speed search operations on
    themselves. Indexes on collections work similarly to the way
    database indexes work on tables; they can dramatically speed up the
    process of searching for a subset of the collection that matches
    certain attributes. The speed result is ultimately achieved by
    searching the keys of a dict instead of iterating over each item in
    the collection and comparing its attributes to a certain value.

    Indexes are useful when working with very large collections.
    Collection tend not to be very useful for everyday business/database
    applications. They were originally designed to optimize algorithms
    that processed collections with thousands of elmentents in them.

    See ``entities.indexes`` for the default collection of indexes that
    entities use. 
    """
    def __init__(self, name=None, keyfn=None, prop=None):
        self._ix = {}
        self.name = name
        self.keyfunction = keyfn
        self.property = prop

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        if type(name) == int:
            raise ValueError('"name" cannot be an int')
        self._name = name

    def append(self, e):
        ix     = self._ix

        val = self.keyfunction(e)
        key = index._getkey(val)

        try:
            vals = ix[key]
        except KeyError:
            ix[key] = vals = []

        vals.append(e)

    @staticmethod
    def _getkey(val):
        # TODO: Since lists aren't hashable, we convert the list to a
        # string.  This isn't ideal since using (0, 1) as the index
        # value on retrieval is the same as using [0, 1].

        # Try to return a hashable version of the value
        if val.__hash__:
            return val
        elif type(val) == list:
            return tuple(val)
        else:
            return id(val)

    def __iadd__(self, e):
        self.append(e)
        return self

    def remove(self, e):
        ix     = self._ix

        val = self.keyfunction(e)
        key = index._getkey(val)

        vals = ix[key]

        for i, e1 in enumerate(vals):
            if e is e1:
                del vals[i]
                break
                
        if not len(vals):
            del ix[key]

    def __isub__(self, e):
        self.remove(e=e)
        return self

    def __call__(self, val, limit=None):
        try:
            return self[val, limit]
        except KeyError:
            return self.indexes.class_()

    def getlist(self, val, limit=None):
        key = index._getkey(val)

        ls = self._ix[key]
        return ls[:limit]

    def __getitem__(self, args):
        if type(args) == tuple:
            val, limit = args
        else:
            val, limit = args, None

        cls = self.indexes.class_
        es = cls()

        # Don't use the constructor's initial parameter. It relies on a 
        # correct implementation of __init__ in the subclass. 
        for e in self.getlist(val, limit):
            es += e
        return es

    def __len__(self):
        return len(self._ix)

class InProgressError(Exception):
    """ Raised when an operation is already in progress and should
    therefore not be attempted at the moment.
    """

# TODO This appears to be dead code. Please remove.
def demand(sub, type=None):
    if type is not None:
        if builtins.type(sub) != type:
            msg = 'Value is of type {} instead of {}'
            msg = msg.format(str(builtins.type(sub)), str(type))
            raise TypeError(msg)
