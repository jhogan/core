# vim: set et ts=4 sw=4 fdm=marker

# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2021

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

Base classes ``event`` and ``eventargs`` are defined here too which
allows for the defining, raising and handling of events. Their design
was inspired my C# delegates and the VB.NET event system.

The ``index`` and ``indexes`` classes create dict() based indexes of
``entity`` objects within ``entities`` collection for fast object
lookups by attributes. These indexes are useful for ``entities``
collections with large numbers of elements.

TODOs:
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

        return self._onbeforeadd

    @onbeforeadd.setter
    def onbeforeadd(self, v):
        """ Sets the onbeforeadd event for this collection.
        """
        self._onadd = v

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
        if type(key) == str:
            min = entities.mintype()
            def key1(x):
                v = getattr(x, key)
                # None's don't sort so do this
                return min if v is None else v
        elif callable(str):
            key1 = key

        self._ls.sort(key=key1, reverse=reverse)

    def sorted(self, key, reverse=False):
        if type(key) == str:
            min = entities.mintype()
            def key1(x):
                v = getattr(x, key)
                # None's don't sort so do this
                return min if v is None else v
        elif callable(str):
            key1 = key

        return type(self)(initial=sorted(self._ls, key=key1, reverse=reverse))

    def enumerate(self):
        for i, e in enumerate(self):
            yield i, e

    def clear(self):
        self.remove(self)

    def __delitem__(self, key):
        # TODO Write test. This will probably work but is only used in
        # one place at the time of this writing. We should also test for
        # `key` being a slice.
        e = self[key]
        self.remove(e)

    def remove(self, e):
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
        self.remove(e)
        return self

    def shift(self):
        return self.pop(0)

    def pop(self, ix=None):
        if self.count == 0:
            return None

        if ix == None: 
            e = self.last
            self._ls.pop()
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
        for e in reversed(self._ls):
            yield e

    def reverse(self):
        self._ls.reverse()

    @property
    def ubound(self):
        if self.isempty: return None
        return self.count - 1

    def move(self, ix, e):
        """ Insert `e` *before* the element at position `ix`.
        """
        raise NotImplementedError('TODO')

    def moveafter(self, ix, e):
        self.remove(e)
        self.insertafter(ix, e)

    def insert(self, ix, e):
        self.insertbefore(ix, e)

    def insertbefore(self, ix, e):
        # TODO Support inserting collections
        self._ls.insert(ix, e)
        try:
            self.onadd(self, entityaddeventargs(e))
        except AttributeError as ex:
            msg = str(ex)
            msg += '\n' + 'Ensure the superclass\'s __init__ is called.'
            raise AttributeError(msg)

    def insertafter(self, ix, e):
        self.insertbefore(ix + 1, e)

    def unshift(self, e):
        # TODO: Return entities object to indicate what was unshifted
        self.insertbefore(0, e)

    def push(self, e):
        self += e

    def give(self, es):
        """ Move the elements self to es. Clear es. A slice parameter
        can be used to limit what is moved. """

        # TODO: Write test
        es += self
        self.clear()

    def __contains__(self, e):
        if type(e) in (int, str):
            e = self(e)

        return self.indexes['identity'](e).ispopulated

    def __lshift__(self, a):
        self.unshift(a)
    
    def append(self, obj, uniq=False, r=None):
        # Create the return object if it hasn't been passed in
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

        self.onbeforeadd(self, entityaddeventargs(t))
        r._ls.append(t)

        self._ls.append(t)

        try:
            if      not isinstance(self, event) \
                and not isinstance(self, indexes):

                self.onadd(self, entityaddeventargs(t))
        except AttributeError as ex:
            # NOTE You can use the below line to get pdb.py to the place
            # the original exception was raised:
            #
            # import pdb
            # pdb.post_mortem(ex.__traceback__)
            msg = str(ex)
            msg += '\n' + 'Ensure the superclass\'s __init__ is called.'
            raise AttributeError(msg)

        return r

    def __iadd__(self, t):
        self.append(t)
        return self

    def __ior__(self, t):
        self.append(t, uniq=True)
        return self

    def __add__(self, es):
        r = type(self)()
        r += self
        r += es
        return r

    def __sub__(self, es):
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
        return len(self._ls)

    def getcount(self, qry):
        # TODO Test
        return self.where(qry).count

    def __len__(self):
        return self.count

    @property
    def isempty(self):
        return self.count == 0

    @property
    def issingular(self):
        return self.count == 1

    @property
    def isplurality(self):
        # TODO This should be call isplural
        return self.count > 1

    @property
    def ispopulated(self):
        # TODO This is redundant with isplurality.
        return not self.isempty

    def __repr__(self):
        return self._tostr(repr)

    def __str__(self):
        return self._tostr(str)

    def _tostr(self, fn=str, includeHeader=True):
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
        ix = self.getindex(e)
        return self(ix - 1)

    def getindex(self, e):
        """ Return the first index of e in the collection.

        This is similar to list.index except here we use the `is`
        operator for comparison instead of the `==` operator.
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
        return self(0)

    @first.setter
    def first(self, v): 
        self[0] = v

    @property
    def second(self): 
        return self(1)

    @second.setter
    def second(self, v): 
        self[1] = v

    @property
    def third(self): 
        return self(2)

    @third.setter
    def third(self, v): 
        self[2] = v
    @property
    def fourth(self): 
        return self(3)

    @fourth.setter
    def fourth(self, v): 
        self[3] = v

    @property
    def fifth(self): 
        return self(4)

    @fifth.setter
    def fifth(self, v): 
        self[4] = v

    @property
    def sixth(self): 
        return self(5)

    @sixth.setter
    def sixth(self, v): 
        self[5] = v

    @property
    def seventh(self): 
        return self(6)

    @seventh.setter
    def seventh(self, v): 
        self[6] = v


    @property
    def last(self): 
        return self(-1)

    # TODO Add tests
    @last.setter
    def last(self, v): 
        self[-1] = v

    @property
    def ultimate(self): 
        return self.last

    @ultimate.setter
    def ultimate(self, v): 
        self.last = v

    @property
    def penultimate(self): 
        return self(-2)

    @penultimate.setter
    def penultimate(self, v): 
        self[-2] = v

    @property
    def antepenultimate(self): 
        return self(-3)

    @antepenultimate.setter
    def antepenultimate(self, v): 
        self[-3] = v

    @property
    def preantepenultimate(self): 
        return self(-4)

    @preantepenultimate.setter
    def preantepenultimate(self, v): 
        self[-4] = v

    @property
    def brokenrules(self):
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
        return self.brokenrules.isempty

class entity:
    def __init__(self):
        self._onaftervaluechange = None
        self._onbeforevaluechange = None

    @property
    def onbeforevaluechange(self):
        if self._onbeforevaluechange is None:
            self._onbeforevaluechange = event()

        return self._onbeforevaluechange

    @onbeforevaluechange.setter
    def onbeforevaluechange(self, v):
        self._onbeforevaluechange = v

    @property
    def onaftervaluechange(self):
        if self._onaftervaluechange is None:
            self._onaftervaluechange = event()

        return self._onaftervaluechange

    @onaftervaluechange.setter
    def onaftervaluechange(self, v):
        self._onaftervaluechange = v

    @property
    def log(self):
        # Defer import to avoid circular dependency
        from config import config
        return config().logs.default

    def _setvalue(
        self, field, new, prop, setattr=setattr, cmp=True, strip=True
    ):
        # TODO: It's nice to strip any string because that's vitually
        # always the desired behaviour.  However, at some point, we will
        # want to preserve the whitespace on either side.  Therefore, we
        # should add a parameter (or something) to make it possible to
        # persiste an unstripped string.
        if type(new) == str and strip:
            new = new.strip()

        if cmp:
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

        if not cmp or ne:
            if hasattr(self, 'onbeforevaluechange'):
                eargs = entityvaluechangeeventargs(self, prop)
                self.onbeforevaluechange(self, eargs)

            if setattr is builtins.setattr:
                try:
                    self.__setattr__(field, new, cmp=cmp)
                except TypeError as ex:
                    msg = (
                        "wrapper __setattr__ doesn't take "
                        "keyword arguments"
                    )

                    if ex.args[0] == msg:
                        setattr(self, field, new)
                    else:
                        raise
            else:
                setattr(self, field, new)

            if hasattr(self, 'onaftervaluechange'):
                eargs = entityvaluechangeeventargs(self, prop)
                self.onaftervaluechange(self, eargs)

            # TODO: Return value is new. Add a unit tests for it.
            return new

    def add(self, e):
        es = entities()
        es += self
        es += e
        return es

    def __add__(self, t):
        return self.add(t)

    @property
    def brokenrules(self):
        return brokenrules()

    @property
    def isvalid(self):
        return self.brokenrules.isempty

class BrokenRulesError(Exception):
    def __init__(self, msg, obj):
        self.message = msg
        self.object = obj

    def __str__(self):
        obj = self.object
        r = self.message + ' '
        r += '%s at %s' % (type(obj), hex(id(obj))) + '\n'
        for br in obj.brokenrules:
            r += '\t* ' + str(br) + '\n'
        return r

    def __repr__(self):
        return str(self)

class brokenrules(entities):
    def append(self, o, r=None):
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

        # TODO A lot of lines are greater than 72 characters.

        # TODO Write unit tests
        v = getattr(e, prop)

        wrongtype = False
        if v is not None:
            if type is not None:
                if builtins.type(v) is not type:
                    self += brokenrule(
                        prop + ' is wrong type', prop, 'valid', e
                    )
                    wrongtype = True

            if instanceof is not None :
                if not isinstance(v, instanceof):
                    self += brokenrule(
                        prop + ' is wrong type', prop, 'valid', e
                    )
                    wrongtype = True

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
        for br in self:
            if (prop == None or br.property == prop) and \
               (type == None or br.type     == type):
                return True
        return False

class brokenrule(entity):
    def __init__(self, msg, prop=None, type=None, e=None):
        self.message   =  msg
        self.property  =  prop
        self.entity    =  e

        if type != None:
            if type not in ['full', 'valid', 'fits', 'empty', 'unique']:
                raise Exception('Invalid brokenrules type')
        self.type = type

    def __str__(self):
        return self.message
    
class event(entities):
    def __call__(self, src, e):
        for callable in self:
            callable(src, e)

    def append(self, fn):
        if not callable(fn):
            raise ValueError('Event must be callable')
        if isinstance(fn, event):
            raise ValueError('Attempted to append event to event collection.')
            
        self._ls.append(fn)

    def remove(self, fn):
        # This is experimental as of 20180506. Previously, events were removed
        # by the base method entities.remove(). But it was noticed that the
        # identity test wasn't matching the bound method being removed:
        #
        #    if rm is self[i]:
        #
        # Bound method id's (id(obj.method)) seem to change over time. 
        # However, an equality test does match bound method which is why
        # the code below reads:
        #
        #    if fn == self[i]
        #
        # This may also explain why it has been noticed that there have
        # been a build up of events in event collections which it would
        # seem shouldn't be there.
        if not callable(fn):
            raise ValueError('Event must be callable')

        for i in range(self.count - 1, -1, -1):
            if fn == self[i]:
                del self._ls[i]
                break

class eventargs(entity):
    pass

class entityaddeventargs(eventargs):
    def __init__(self, e):
        self.entity = e

class entityremoveeventargs(eventargs):
    def __init__(self, e):
        self.entity = e

class entityvaluechangeeventargs(eventargs):
    def __init__(self, e, prop):
        self.property = prop
        self.entity = e

class appendeventargs(eventargs):
    def __init__(self, e):
        self.entity = e

class indexes(entities):
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
    pass

def demand(sub, type=None):
    if type is not None:
        if builtins.type(sub) != type:
            msg = 'Value is of type {} instead of {}'
            msg = msg.format(str(builtins.type(sub)), str(type))
            raise TypeError(msg)
