# vim: set et ts=4 sw=4 fdm=marker

#######################################################################
# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2022
########################################################################

from contextlib import suppress
from dbg import B
from entities import classproperty
from func import enumerate
from textwrap import dedent, indent
import entities
import file
import operator
import builtins
import orm
import primative
import re
import string
import sys
import uuid

"The Web is a detail."
# Robert C. Martin

"""
Contains classes that implement an object-oriented interface to HTML
document.

This implementation is similar to the WHATWG DOM standarded implemented
in web browsers to read and manipulate DOM objects with JavaScript,
although no effort is made to conform to that standard. The API is
similar to other object models in the Core, making use of @property
methods, indexers (__getitem__), operator overloading (+=), etc.

Each HTML5 element (e.g., <form>, <a>, etc.), is represented by a class
that inherits from the ``element`` base class. Each of these subclasses
has a corresponding collection class when there is a need to present
elements bundled by type. For example, the ``form`` class has a
``forms`` collection class.

Each element subclass has a @property getter and setter for each of the
HTML5 attributes of the element. Only standard HTML5 attributes are
available as properties, although the ``attributes`` collection of any
element can be used to get around this in case there is a legitamate
need.

The following is an example of how to create a basic HTML5 document::

    import dom

    # Create the root tag (<html>)
    html = dom.html()

    # Create the <head> and <body>
    head = dom.head()
    body = dom.body()

    # Append head and body to html
    html += head
    html += body

    # Add a <title> to head
    head += dom.title('My Home Page')
    
    # Let's give the body an id attribute, i.e., <body id="my-id">
    body.id = 'my-id'

    # Above, body has an id property, because the id attribute is a
    # standard HTML5 attribute of all elements. However, bgcolor is a
    # depricated attribute, so we have to use the ``attributes``
    # collection. Of course we shouldn't use depricated properties, but
    # if we have to for some reason, this is how.
    body.attributes['bgcolor'] = 'black'

    # The HTML string for this can be captured using the ``html``
    # property.
    print(html.html)

    # The above wouldn't have linefeeds or tabs and would be suitable
    # for consumption by a program like a browser or some other parser.
    # To get a nice output for human consumption, use the ``pretty``
    # property::
    >>> print(html.pretty)
    <html>
        <head>
            <title>
        </head>
        <body id="my-id" bgcolor="black">
        <=body>
    </html>

    # In addition to building HTML document, we can use the ``html``
    # class to build a DOM from an HTML string:

    # Parse the html.html string to build html1
    html1 = dom.html(html.html)

    # Both DOMs will produces the same HTML.
    assert html.html == html1.html

TODOs

    TODO:10d9a676 Add a `document` class similar to the standard
    JavaScrip DOM's `document` object. Currently, when we deal with
    complete DOM objects, we use the `html` class (which represents the
    <html> tag). For the most part this works because almost everything
    in an HTML document comes under the <html> tag. However, it is
    impossible to capture <!DOCTYPE> declarations using this structure
    because <html> must be a sibling of <!DOCTYPE>. The JavaScript DOM
    uses the `document` object to act as the parent object of <!DOCTYPE>
    and <html>. Currently, to get the <!DOCTYPE> declaration in the HTML
    that is emitted to the browser, there are some HACKs that prepend
    "<!DOCTYPE html>" to the output. This works for the most part and
    keeps browser consoles from complaining that the page is being
    rendered in "quirks mode". However, being hacks these solutions
    don't adequetly capture the abstraction of a DOM document. For
    instance, there is no way to indicate which DTD needs to be used
    (the hacks always defaults standard mode (`html`)).  When correcting
    this, be sure to grep for the snowflake 10d9a676 as there are
    several other places that reference this TODO.
"""

# References:
#
#     Google: Managing multi-regional and multilingual sites
#     https://support.google.com/webmasters/answer/182192?hl=en
#
#     List of ISO 639-1 codes
#     https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes
#
#     Page component reference: 
#     https://webstyleguide.com/wsg3/6-page-structure/3-site-design.html
#
#     The PO Format
#     http://pology.nedohodnik.net/doc/user/en_US/ch-poformat.html?
#
#     Syncing files with lsyncd
#     https://www.digitalocean.com/community/tutorials/how-to-mirror-local-and-remote-directories-on-a-vps-with-lsyncd

class attributes(entities.entities):
    """ Represents a collection of attributes for HTML5 elements.
    """
    def __init__(self, el=None, *arg, **kwargs):
        """ Create an attributes collection.

        :param: el element: The HTML5 DOM element to associate the
        collection with.
        """
        super().__init__(*arg, **kwargs)
        self.element = el
        
    def __iadd__(self, *o):
        """ Append an attribute to the collection via the += operator::

            # Create an element
            p = dom.p()

            # Append an attribute using +=
            p.attributes += attribute('id', 'my-id-value')

        :param: *o object(s): The *o parameters allows for a number of
        different ways to append attributes. See the docstring at
        attributes.append for more ways to append. 
        """
        for o in o:
            if type(o) in (tuple, list):
                o = attribute.create(*o)
            super().__iadd__(o)
        return self

    def clone(self):
        """ Returns a cloned version of the attributes collection.
        """
        attrs = type(self)(self.element)
        for attr in self:
            attrs += attr.clone()
        return attrs
            
    def append(self, o, v=None, uniq=False):
        """ Append an attribute to the collection. 

        :param: o object: The attribute being appended. o can be a
        number of types:

            attribute
            ---------
            The most obvious way to append an attribute to a collection
            is to simple append an attribute objects:

                # Create a <p>
                p = dom.p()

                # Create an attribute object: id="my-id-value"
                attr = dom.attribute('id', 'my-id-value')

                # Append the object such that <p> becomes 
                # <p id="my-id-value"></p>
                p.attributes += attr

            tuple
            -----
            The above could have been append as a tuple instead::

                p.attributes += id', 'my-id-value'

            list
            ----
            List work similarly::

                p.attributes += [id', 'my-id-value']

            dict
            ----
            With dict's we can add multiple attrs in one line::

                p.attributes += {
                    'id':    'my-id-value',
                    'title': 'my-title-value',
                }

            attributes collections
            ----------------------
            With attributes collections we can also add multiple attrs
            in one line::

                attrs = dom.attributes()
                attrs += 'id', 'my-id-value'
                attrs += 'title', 'my-title-value'
                p.attributes += attrs
                
        :param: uniq bool: If True, an append will only happen if the
        attribute is not already in the collection.
        """

        # TODO Some elements like <meta>, <br/>, etc., should not be
        # allowed to have content appended to them. An exception should
        # be raised when that happens, or maybe the document's `invaild`
        # property should be True.
            
        if type(o) is str:
            o = attribute(o, v)

        if type(o) is dict:
            for k, v in o.items():
                self += k, v
            return

        if hasattr(o, '__iter__'):
            return super().append(o, uniq)

        for attr in self:
            if o.name == attr.name:
                msg = 'Attribute already exists: ' + o.name
                raise AttributeExistsError(msg)

        return super().append(o, uniq)

    def __getitem__(self, key):
        """ Returns an `attribute` object based on the given `key`.

        :param: key int|slice|str: The index value used to find the
        item
            If the `key` is an `int`, return the attribute based on its
            position in the collection. (Note that in these examples,
            `attrs` represents an attribute's collection)::

                assert attrs[0] is attrs.first

            If the `key` is a slice, return a slice of the attributes::

                assert attrs[0:2] == (attrs.first, attrs.second)

            If the `key` is a str, return the attribute object by name::
                
                attr = attribute(name='checked', value=True)
                attrs += attr

                attr is attrs['checked']

            Note that __getitem__ can also be used to set create new
            attributes::
                
                attr = attrs['newattr']
                attr.value = 'newvalue'

                assert 'newvalue' == attrs['newattr']
        """

        if isinstance(key, int):
            return self._defined[key]
                
        if isinstance(key, slice):
            return type(self)(self.element, initial=self._defined[key])

        if not isinstance(key, str):
            return super().__getitem__(key)

        try:
            ix = self.getindex(key)
        except ValueError as ex:
            if key == 'class':
                # Look for undefined classes
                for attr in self._ls:
                    if attr.name == 'class':
                        break
                else:
                    attr = None
            else:
                attr = None
        else:
            attr = self._ls[ix]

        if attr:
            return attr
        else:
            if key == 'class':
                self += cssclass()
            else:
                self += attribute(key)
            
            return self._ls[-1]

    def __setitem__(self, key, item):
        """ Sets an `attribute` object based on the given `key`::

            attrs['checked'] = True

        :param: key int|str: 
            if int:
                key is used like a normal list indexer:
                    
                    # Assign `attr` to first element of attrs
                    attrs[0] = attr

            if str:
                key is assumed to be the name of an attribute:
                
                # <p id="my-id-value">
                p.attributes['id'] = 'my-id-value'
        """

        if not isinstance(key, str):
            super().__setitem__(key, item)
            
        for attr in self._ls:
            if attr.name == key:
                break
        else:
            attr = None

        if attr:
            if isinstance(attr, cssclass):
                if isinstance(item, str):
                    attr.value = item
                else:
                    attr._classes = item._classes
            else:
                attr.value = item
        else:
            if key == 'class':
                self += cssclass(item)
            else:
                self += key, item

    def reversed(self):
        """ Returns a generator of (defined) attributes
        in reversed order. (See `attribute.isdef`)

            # Print attributes in reverse order
            for attr in p.attributes.reversed():
                print(attr)
        """
        for e in reversed(self._defined):
            yield e

    @property
    def _defined(self):
        ''' Return a list of attributes that have values. (See
        `attribute.isdef` for more information)
        '''
        return [x for x in self._ls if x.isdef]

    def __iter__(self):
        ''' A standard iterator that only returns defined attributes.
        (See `attribute.isdef`)
        '''
        for attr in self._defined:
            yield attr

    def __contains__(self, attr):
        """ A __contains__ override that only considers defined
        attributes. (See `attribute.isdef`)
        """
        if isinstance(attr, str):
            return attr in [x.name for x in self._defined]
        else:
            return attr in self._defined

    @property
    def count(self):
        """ Returns the number of (defined) attributes. 
        """
        return len(self)

    def __len__(self):
        """ Returns the number of (defined) attributes. (See
        `attribute.isdef`)
        """
        return len(self._defined)

    @property
    def html(self):
        """ Returns an HTML representation of the attributes. This is
        appropriate for concatenating to other DOM representations.
        """
        return ' '.join(x.html for x in self if x.isvalid)
        
class attribute(entities.entity):
    """ A object that represents an HTML5 attribute. An attribute will
    have a name and usually a value::

        <element name="value">

    Boolean attributes can have a value of None to indicate they are
    present in the HTML but have to value assigned to them. For example,
    the following creates an ``input`` element that would be render as
    follows in HTML: <input type="checkbox" checked>

        inp = dom.input()
        inp.attributes['type'] = checkbox
        inp.attributes['checked'] = None
    """

    class undef:
        """ A class used to indicate that an attribute has not been
        defined.
        """
        pass

    def __init__(self, name, v=undef):
        """ Create an `attribute` with an optional value.
        """
        self.name = name
        self.value = v

    def clone(self):
        """ Returns a new `attribute` object with the name and value of
        this `attribute` object.
        """
        return type(self)(self.name, self.value)

    @property
    def name(self):
        """ Returns name of the attribute.
        """
        return self._name

    @name.setter
    def name(self, v):
        """ Sets the name of the attribute.
        """
        if any(x in ' "\'/=' for x in v):
            raise ValueError('Invalid character in attribute name')

        if any(ord(x) in range(0xfdd0, 0xfdef) for x in v):
            raise ValueError('Invalid character in attribute name')

        if any(ord(x) in range(0x007f, 0x009f) for x in v):
            raise ValueError('Invalid character in attribute name')

        self._name = v

    @property
    def value(self):
        """ Returns the value of the attribute.
        """
        if self.isdef:
            if self._value is None:
                return None
            return str(self._value)
        return None

    @value.setter
    def value(self, v):
        """ Sets the value of the attribute.
        """
        # TODO We should raise ValueError if v contains an ambiguous
        # ampersand.
        # https://html.spec.whatwg.org/multipage/syntax.html#attributes-2

        # TODO Setting attributes to boolean values has not been tested.
        # See the comment below to understand the intention of boolean
        # values in this context and write tests to ensure that
        # everytihng works as expected.

        # If v is a True, set it to None. This has the effect of
        # including the attribute but with no value, e.g.,
        # 
        #     inp = input(required=True)
        #
        # The above produces
        #
        #     <input required>
        #
        # Inversely, if v is False, set it to undef to remove the
        # attribute. So the following code
        #
        #     inp.required = False
        #
        # will remove the required attribute.
        #
        #     <input>
        if v is True:
            v = None
        elif v is False:
            v = attribute.undef

        self._value = v

    @property
    def isdef(self):
        """ Returns True if an attribute is defined, False otherwise. An
        undefined attribute can be created by indexing the `attributes`
        collection without setting a `value`::

            id = attrs['id']

        Here, the `attrs` now has an attribute called 'id' that has no
        value. Since it has no value, its presense within `attrs` is
        concealed from the user:

            assert attrs.count == 0

        If the use decides later to give `id` a value, the `attrs`
        collection will reveal the attribute to the user::
            
            assert attrs.count == 0
            id.value = 'myvalue'
            assert attrs.count == 1

        The `isdef` property is used by the logic that conceals the
        undefined attributes from the user.
        """
        return self._value is not attribute.undef

    @staticmethod
    def create(name, v=undef):
        """ A staticmethod to create an ``attribute`` or ``cssclass``
        given a name and an optional value. Unlike `attribute`'s
        constructor, a cssclass will be returned if name == 'class'.
        """
        if name == 'class':
            return cssclass(v)

        return attribute(name, v)

    def __repr__(self):
        """ Returns a str (non-HTML) representation of the attribute.
        """
        r = "%s(name='%s', value='%s')"
        r %= type(self).__name__, self.name, self.value
        return r

    def __str__(self):
        """ Returns a str (non-HTML) representation of the attribute
        ('attr="value"').
        """
        r = '%s="%s"'
        r %= self.name, self.value
        return r

    @property
    def html(self):
        """ Returns a string of HTML representing the attribute.
        Example::
            
            attributename="attribute-value"
        """

        if self.value is None:
            return self.name

        return '%s="%s"' % (self.name, self.value)

class cssclass(attribute):
    """ An subtype of `attribute` specificaly for the "class" attribute.
    """
    def __init__(self, v=None):
        """ Create a "class" attribute object.
        """
        super().__init__('class')

        self._classes = list()

        if v:
            self += v

    def __contains__(self, e):
        """ Returns True if e is the collection of classes.
        """
        return e in self._classes

    def __len__(self):
        """ Returns the number of classes.
        """
        return len(self._classes)
    
    @property
    def count(self):
        """ Returns the number of classes.
        """
        return len(self)

    def __bool__(self):
        """ Returns True.

        By default, if __len__ returns 0, the object is falsey. If the
        object exists (as a non-None property, for example), it should be
        True. So it should always be truthy.
        """
        return True

    def __getitem__(self, ix):
        """ Returns the CSS class given an index number.
        """
        return self._classes[ix]

    def __iadd__(self, o):
        """ Allows the appending of a CSS class using the += operator.
        See cssclass.append for more.

        :param: o as str|cssclass: The name of a CSS class or a cssclass
        object.

        """
        self.append(o)
        return self

    def append(self, *clss):
        """ Append one or more CSS classes.

            div = dom.div()

            # All of the following do the same. Each would be render in
            # HTML as <div class="col-xs-4" />
            div.classes.append('col-xs-4')
            div.classes.append(dom.cssclass('col-xs-4'))
            div.attributes['class'].append(dom.cssclass('col-xs-4'))

        You can also append multiple at the same time::

            # All the following do the same. Each would be render in
            # HTML as: <div class="my-class-1 my-class-a" />
            div.classes.append('my-class-1 my-class-a')
            div.classes.append('my-class-1', 'my-class-a')
            div.classes += dom.cssclass('my-class-1 my-class-a')
            div.classes += 'my-class-1', 'my-class-a'
            div.classes += 'my-class-1 my-class-a'

        :param *clss list<str|cssclass|iterable>: A list of str,
        cssclass, or iterables that can be considered resolvable to CSS
        classes.
        """
        for cls in clss:
            if isinstance(cls, str):
                for cls in cls.split():
                    if cls in self._classes:
                        raise ClassExistsError(
                            'Class already exists: ' + cls
                        )
                    self._classes.append(cls)
            elif isinstance(cls, cssclass):
                self.append(*cls._classes)
            elif hasattr(cls, '__iter__'):
                self.append(cls)
            else:
                raise ValueError('Invalid type: ' + type(clss).__name__)

    def __delitem__(self, *clss):
        """ Allows the del operator to be used to delete a CSS class from
        the collection. Assuming `p` has a CSS class called
        'my-class', you can delete it with the following code::

            # Before: <p class="my-class my-other-class">
            del p.classes['my-class']

            # After: <p class="my-other-class">

        The *clss indexer can be anything passed to cssclass.remove. See
        its document string for a full list of argument tyes that can be
        used to delete CSS classes this way.

        :param: *clss TODO: Add comments from cssclass.remove
        """
        self.remove(*clss)

    def __isub__(self, o):
        """ Allows the -= operator to be used to delete a CSS class from
        the collection. 

        Assuming `p` has a CSS class called 'my-class', you can delete
        it with the following code::

            # Before: <p class="my-class my-other-class">
            del p.classes -= 'my-class'

            # After: <p class="my-other-class">

        The o argument can be anything passed to cssclass.remove. See
        its docstring for a full list of argument types that can be used
        to delete CSS classes this way.

        :param: o TODO: Add comments from cssclass.remove
        """
        self.remove(o)
        return self

    def remove(self, *clss):
        """ Removes a CSS class from the collection::

            # Given:
            assert p.html == '<p class="c1 c2 c3 c4 c5 c6 c7 c8"></p>'
            # The following three lines would do the same thing: remove
            # the 'c5' CSS class from p
            p.classes.remove('c5')
            p.classes -= 'c5'
            del p.classes['c5']
            assert p.html == '<p class="c1 c2 c3 c4 c6 c7 c8"></p>'

            # You can also remove multiple classes in one line using
            # space seperated classes
            p.classes.remove('c1 c8')
            self.eq('class="c2 c3 c4 c6 c7"', p.classes.html)

            p.classes -= 'c2', 'c7'
            self.eq('class="c3 c4 c5 c6"', p.classes.html)

        :param: *clss str| list<str|iterables>: The CSS class to remove.
            if str:
                The str is interpreted as one or more CSS classes, e.g.,
                "my-class" or "my-class my-other-cass"

            if list:
                Each element in the list will be interpeted as a
                string. You could do something like the following::
                    tag.classes.remove('my-class', 'my-other-class')

                    # or

                    tag.classes.remove(*['my-class', 'my-other-class'])

                    # or

                    tag.classes.remove(['my-class', 'my-other-class'])
        """
        for cls in clss:
            if isinstance(cls, str):
                for cls in cls.split():
                    if cls not in self._classes:
                        raise IndexError('Class not found: ' + cls)
                    self._classes.remove(cls)
            elif hasattr(cls, '__iter__'):
                for cls in cls:
                    self.remove(cls)
            else:
                raise ValueError(
                    'Class wrong type: ' + type(cls).__name__
                )

    @property
    def isdef(self):
        """ Returns True if the 'class' attribute is defined, False
        otherwise. (See the docstring at attribute.isdef for more).
        """
        return bool(self._classes)

    @property
    def value(self):
        """ Returns a space seperated list of the CSS classes collected
        in this attribute.

        If the attribute (self) is not defined, the attribute.undef
        class is returned to indicate that the value is undefined. See
        cssclass.isdef.
        """
        if not self.isdef:
            return attribute.undef
        return ' '.join(self._classes)

    @value.setter
    def value(self, v):
        """ Set's the value of the class attribute.
        """
        if v is None:
            self._classes = list()
        elif v is not attribute.undef:
            self._classes = v.split()

    @property
    def html(self):
        """ Returns the HTML representation of the CSS class:

            class="my-class my-other-class"
        """
        return 'class="%s"' % self.value

    def __repr__(self):
        """ Returns a representation of this object::

            cssclass(value='my-class my-other-class')
        """
        return '%s(value=%s)' % (type(self).__name__, self._classes)

class elements(entities.entities):
    """ Represents a collection of HTML5 ``element`` objects.

    This class can be used to store any collection of elements. However,
    for each HTML5 element, there is a collection class that inherits 
    from ``elements`` which are more approprite for storing collection
    that only contain that element::

        # Create a paragraphs collection
        ps = dom.p()

        # Assert that ``dom.p`` inherits form ``elements``
        assert isinstance(ps, elements)

        # Add paragraph object (<p>) to the paragraphs collection
        ps += dom.p()
        ps += dom.p()
    """
    # TODO:12c29ef9 Write and test mass attribute assignment logic:
    #
    #     chks.checked = True  # Check all checked attributes
    # 
    #     del htmls.id # Remove all attribute in els collection
    #
    # When this is complete, c0336221 can be attended to.

    # TODO All html should pass the W3C validation service at:
    # https://validator.w3.org/#validate_by_input

    @property
    def root(self):
        """ Returns the root ``element`` that this collection is under.
        In typical HTML documents, this would be the ``element``
        corresponding to the <html> tag at the root. This isn't
        necessarly always the case, though,  since we could be using a
        fragment of an HTML document, or a non-standard HTML document
        that doesn't have <html> as its root.
        """
        if self.parent:
            return self.parent.root
        return None

    @classmethod
    def getby(cls, tag):
        """ Given the str ``tag``, search through all the ``element``
        subclasses and return the first one that matches the tag name.

            header = dom.elements.getby('header')
            assert header is dom.header

        This is useful for when you don't know what element you want so
        you need to use a str variable to make it dynamic.
        """
        # TODO This method should be in ``element`` not ``elements``
        # since it returns an element.
        for el in element.__subclasses__():
            if el.tag == tag:
                return el
        return None

    def clone(self):
        """ Create a new instance of this ``elements`` collection, clone
        each of self's elements into the new collection, and return it.
        """
        els = type(self)()
        for e in self:
            els += e.clone()

        return els

    @property
    def text(self):
        """ Get the combined text contents of each element in the
        collection.
        """
        # NOTE This should match the functionality of jQuery's `.text()`
        # as closely as possible - except for the `.text(function)`
        # overload.

        return '\n'.join(x.text for x in self)

    @text.setter
    def text(self, v):
        for x in self:
            x.text = v

    def remove(self, e=None):
        """ Removes ``e`` from the given collection. If is is not
        provided, removes each of the elements in this collection from
        their parent.

        :param: e element: The element to remove.
        """
        if e is not None:
            return super().remove(e)

        rms = elements()
        for e in self.reversed():
            rent = e.parent
            if rent:
                e._parent = None
                rms += rent.elements.remove(e)
        return rms

    def __getitem__(self, sel):
        ''' Get elements by an ordinal index or by a CSS3 selector.
        Given `els` is an ``elements`` collection::
            
            # Get the first element of the collection of elememnts
            el = els[0]

            # Get the first 2 elements from the collection of elememnts
            els = els[0:2]

            # Get all <span> elements that are immediate children of
            # <p>, where <p> is a child or grandchild of a <div> with a
            # class of of 'my-class'.
            els = els['div.my-class p > span']

            # Same as above except pass a selectors object instead of a
            # selector string.
            sels = selectors('div.my-class p > span')
            els = els[sels]

        :param: sel int|slice|str|selectors: The indexer value.
        '''

        if isinstance(sel, int) or isinstance(sel, slice):
            return super().__getitem__(sel)

        elif isinstance(sel, str):
            sels = selectors(sel)

        elif isinstance(sel, selectors):
            sels = sel
        else:
            raise TypeError('Invalid type: ' + type(sel).__name__)

        return sels.match(self)

    @property
    def children(self):
        """ Returns a new ``elements`` collection containing all
        immediate children in this collection. Note that ``comment`` and
        ``text`` nodes are excluded.
        """
        initial = (
            x for x in self if type(x) not in (comment, text)
        )
        return elements(initial=initial)

    def getchildren(self):
        """ Return a new ``elements`` collection containing all elements
        underneath this ``elements`` collection. Note that ``comment``
        and ``text`` nodes are excluded.
        """
        els = elements()
        for el in self.children:
            els += el
            els += el.getchildren(recursive=True)
        return els

    def genchildren(self):
        """ Return a generator that will yield all elements
        underneath this ``elements`` collection. Note that ``comment``
        and ``text`` nodes are excluded.
        """
        for el in self:
            yield el
            yield from el.genchildren(recursive=True)

    def walk(self):
        """ Return a generator that yield all elements underneath this
        ``elements`` including ``comment`` and ``text`` nodes.
        """
        for el in self:
            yield el
            yield from el.genelements(recursive=True)

    @property
    def all(self):
        """ Return a new ``elements`` collection containing all elements
        underneath this ``elements`` including ``comment`` and ``text``
        nodes.

        Note that for performance reasons, it is preferable to use the
        walk() method when iterating instead::

            for el in self.walk():
                ...

        self.walk produces a generator and therefore does not require a
        call to entities.append for each element it generates. Use all()
        for cases where you want to have an ``elements`` collection to
        work with and performance isn't an issue.
        """
        els = elements()
        for el in self.walk():
            els += el
        return els

    @property
    def pretty(self):
        """ Return a str containing a user-friendly, HTML rendering of
        the elements using indenting and linefeeds for readability.
        """
        return '\n'.join(x.pretty for x in self)

    @property
    def html(self):
        """ Returns the HTML representation of the ``elements`` and
        their children.

        Note that there won't be any linefeeds or indentation to make
        the HTML human-friendly. The HTML is intended for a browser or
        some other parser. For a human-friendly version, use the
        ``elements.pretty`` property.
        """
        return ''.join(x.html for x in self)

    @property
    def parent(self):
        """ Returns the parent element of this collection of elements.
        """
        if not hasattr(self, '_parent'):
            self._parent = None

        return self._parent

    def _setparent(self, v):
        if self.parent:
            raise MoveError('Parent already set')
        self._parent = v

    def _text2element(self, txt):
        """ Convert a str (txt) to a text node and return it. 

        Used by self.append and self.unshift.

        :param: txt str|element: 
            if str:
                The text to convert to a node.

            if element:
                Simply return the element that was passed in.
        """

        if type(txt) is str:
            # If we are appending a text node to a <script> tag, we
            # don't want to do any HTML escaping. Escaping the
            # contents of a <script> tag (e.g., JavaScript, JSON,
            # etc) means the quotes and angle brakets would be
            # garbled thus rending the script uninterpretable, e.g.,
            # console.log(&#x27;Hello, world&#x27;)
            esc = not isinstance(self.parent, script)
            return text(txt, esc=esc)

        return txt

    def _demandadditions(self, obj):
        """ Raise exception is there is an issue obj being appended to
        self.elements. 

        Used by self.append and self.unshift.

        :param: obj element|sequence: The element(s) to append.
        """
        if isinstance(self.parent, text):
            raise NotImplementedError(
                "Can't append to a text node"
            )

        pass_ = False
        if isinstance(obj, element):
            pass_ = True
        elif hasattr(obj, '__iter__'):
            # NOTE This could be elements, lists or generators.
            pass_ = True

        if not pass_:
            raise TypeError('Invalid element type: ' + str(type(obj)))

    def append(self, obj, *args, **kwargs):
        """ Appends an element to this object's `elements` collection.

        :param: obj str|element|sequence The element to append.

            if str:
                Convert to text node and append the node.

            if element:
                Append the element.

            if sequence:
                Append each element in the sequence.

        """
        # Convert object to text node if it is a str
        obj = self._text2element(obj)

        # Raise exception if the obj is invalid
        self._demandadditions(obj)

        super().append(obj, *args, **kwargs)

    def unshift(self, obj):
        """ Prepend an element to this object's `elements` collection.

        :param: obj str|element|sequence The element to preappend.

            if str:
                Convert to text node and prepend the node.

            if element:
                Prepend the element.

            if sequence:
                Prepend each element in the sequence.
        """

        # Convert object to text node if it is a str
        obj = self._text2element(obj)

        # Raise exception if the obj is invalid
        self._demandadditions(obj)

        # TODO: Return entities object to indicate what was unshifted
        super().unshift(e=obj)

    def __contains__(self, e):
        """ Returns True if e is in this `elements` collection, False
        otherwise. 

            assert e not in es

            es += e

            assert e in es

        Typically, e will be of type `element` (a subclass of `entity`).
        However, other types can be used.

        :param e entity|str|int|iterable: The entity being sought.
            if entity:
                Simply return True if the entity is in self.

            if iterable:
                Iterate over each entity. If all entity are in self,
                return True, False otherwise.

            if int:
                Use e as an index value. If the index is found, return
                True.

            if str:
                Detremine if an entity in self with an `id` or `name`
                attribute equals e. If so, return True, False otherwise.
        """
        # element objects are iterable, so handle here. The super()
        # (entities.entities) handles iterables differently.
        if isinstance(e, element):
            # TODO:28b5a63a Shouldn't this be `any` instead of `all`.
            return bool(len(self) and all(e is x for x in self))

        return super().__contains__(e)
        
class element(entities.entity):
    """ An abstract class from which all HTML5 elements inherit.

        # Create a paragraph (<p>) class 
        p = dom.p()
        # Assert that ``dom.p`` inherits form ``element``
        assert isinstance(ps, element)

    Attributes
    ----------
    Though the HTML attributes of an element can be accessed by the
    element's ``attributes`` collection, standard HTML5 attributes will
    be (or should be) defined as @property's on the element::

        import dom
        td = dom.td()

        # Standard, non-depricated attributes work like this
        td.colspan = 1
        assert td.colspan == 1

        # Non-standard or depricated attributes won't work as
        # @property's.
        try:
            td.abbr = 'tla'
        except AttributeError:
            assert True
        else:
            assert False

        # However, if you really want to use a non-standard or
        # depricated attribute, you can use the attributes collection::
        tr.attributes['attr'] = 'tla'
        assert tr.attributes['abbr'] == 'tla'

        :abbr: el
    """
    # A void element is an element whose content model never allows it
    # to have contents under any circumstances. Void elements can have
    # attributes.
    #
    # The following is a complete list of the void elements in HTML:
    #    area, base, br, col, command, embed, hr, img, input, keygen,
    #    link, meta, param, source, track, wbr
    #
    # See https://www.w3.org/TR/2011/WD-html-markup-20110113/syntax.html
    # for more about void elements.
    isvoid = False

    # TODO Prevent adding nonstandard elements to a given element. For
    # example, <p> can only have "phrasing content" according to the
    # HTML5 standard.

    # TODO Put beneath constructor
    @staticmethod
    def _getblocklevelelements():
        """ Returns a tuple of block-level, HTML5 ``element`` classes
        e.g.: (address, article, aside, ...).
        """
        return (
            address,   article,     aside,   blockquote,  dd,
            details,   dialog,      div,     dl,          dt,
            fieldset,  figcaption,  figure,  footer,      form,
            h1,        h2,          h3,      h4,          h5,
            h6,        header,      hr,      li,          main,
            nav,       ol,          p,       pre,         sections,
            table,     ul,
        )

    def __init__(self, body=None, **kwargs):
        """ Create an HTML5 DOM element.

        :param: str|element|elements: The body of the element. If str,
        the body is added as a text node. If ``element`` or ``elements`,
        those elements are added as the body.

        :param: id bool:object (optional): 
            If the 'id' is bool:
                if True, a random id will be assigned to the id
                attribute of the element.

                If False, 
                    Don't assign a random id. 

                If the id is neither
                    bool True or False, but still exists, we will allow
                    it to be treated just like any other attribute
                    being assigned in the constructor:
            
                el = element(id=123, class="order-data")
                assert el.id == 123

        :param: kwargs KVP: Zero or more arbitrary arguments can be
        assigned via the constructor::

            el = element(id=123, foo='bar', herp='derp')
            assert el.id == 123
            assert el.foo == 'bar'
            assert el.herp == 'derp'

        Note that ideally, these will be standard HTML5 attributes, but
        that is not required.

        """
        if self.isvoid and body is not None:
            # If self.isvoid, the `body` parameter would be meaningless.
            # In this case, if body is not None, we should raise an
            # exception.
            raise ValueError(
                f'{type(self)} elements can not accept a body because '
                'it is void'
            )

        try:
            id = kwargs['id']
        except KeyError:
            pass
        else:
            if id is True:
                self.id = primative.uuid().base64
                del kwargs['id']
            elif id is False:
                del kwargs['id']

        self._revs = None

        if body is not None:
            if isinstance(body, element):
                pass
            elif isinstance(body, elements):
                pass
            else:
                body = str(body)

            self += body

        with suppress(KeyError):
            kwargs['class'] = kwargs.pop('class_')

        # TODO If a key in kwargs is not an attribute of the given
        # element, it should throw an AttributeError::
        #
        #     for k, v in kwargs.items():
        #         if not hasattr(self, k):
        #             raise AttributeError()
        #         else:
        #             setattr(self, k, v)

        # Check len here to make things a little faster
        if len(kwargs):
            # Add kwargs to attributes collection
            self.attributes += kwargs

    ''' The event triggers and handlers for any dom.element. '''

    # A tuple of supported trigger methods. These correspond to DOM
    # methods, such as element.focus(), which trigger a corresponding
    # event (onfocus).
    Triggers = 'click', 'focus', 'blur', 'input',

    # NOTE If you need to add a new trigger/event (e.g., input/oninput,
    # keydown/onkeydown), Make sure you add the trigger to the
    # Triggers tuple above.

    @property
    def onclick(self):
        """ Returns the `onclick` event for this element.
        """
        return self._on('click')

    @onclick.setter
    def onclick(self, v):
        setattr(self, '_onclick', v)

    def click(self):
        """ Triggers the `click` event for this element.
        """
        return self._trigger('click')()

    @property
    def onfocus(self):
        """ Returns the `onfocus` event for this element.
        """
        return self._on('focus')

    @onfocus.setter
    def onfocus(self, v):
        setattr(self, '_onfocus', v)

    def focus(self):
        """ Triggers the `focus` event for this element.
        """
        return self._trigger('focus')()

    @property
    def onblur(self):
        """ Returns the `onblur` event for this element.
        """
        return self._on('blur')

    @onblur.setter
    def onblur(self, v):
        setattr(self, '_onblur', v)

    def blur(self):
        """ Triggers the `blur` event for this element.
        """
        return self._trigger('blur')()

    @property
    def oninput(self):
        """ Returns the `oninput` event for this element.
        """
        return self._on('input')

    @oninput.setter
    def oninput(self, v):
        setattr(self, '_oninput', v)

    def input(self):
        """ Triggers the `input` event for this element.
        """
        return self._trigger('input')()

    def _on(self, ev):
        """ Return a memoized dom.event object for this event named by
        `ev`.

        :param: ev str: The name of the event, e.g., 'focus', 'blur'.
        """
        # Name the private instance variable for the event.
        priv = '_on' + ev

        if not hasattr(self, priv):
            # Create and memoize event
            setattr(self, priv, event(self, ev))

        # Return memozied event
        return getattr(self, priv)

    def _trigger(self, trigger):
        """ Return a callable that itself calls the event corresponding
        the trigger. 

        :param: trigger str: The name of the trigger method such as
        'focus' or blur.
        """
        def f():
            # Get the event
            onevent = getattr(self, 'on' + trigger)

            # Create the event arguments
            eargs = eventargs(el=self, trigger=trigger)

            # Trigger the event
            onevent(self, eargs)

        return f

    ''' end of triggers and handlers '''

    def remove(self, el=None):
        """ Removes ``el`` from this ``element``'s child elements.

        :param: el element: The element that we want to remove. If not
        given, the element itself (i.e, self) is removed from the DOM.
        """
        if el:
            # Remove el from self's child elements.
            return self.elements.remove(el)
        else:
            # This block causes `.remove` to behave more like jQuery's
            # version in that you can just call the `.remove` method on
            # an element and it removes itself from the DOM.
            return self.parent.remove(self)

    def identify(self, recursive=False):
        """ Assigns a new, random values to the id attribute of this
        HTML5 elements and all of its descendants. The id value is a
        UUID encoded in Base64 with an 'x' prepended to it.

        :param: recursive bool: If True, walk the DOM tree run
        `identify` on each element. Note that this is currently
        untested functionality.
        """

        if not self.id:
            # Set to a random identifier. Prepend an x because HTML5's
            # specification dosen't allow id attributes to start with
            # numbers.
            self.id = 'x' + primative.uuid().base64

        if not recursive:
            return

        for el in self.walk():
            # NOTE untested
            el.identify()
        
    @property
    def isblocklevel(self):
        """ Returns True if this element is a block-level element; False
        otherwise.
        """
        return type(self) in self._getblocklevelelements()

    def clone(self):
        """ Returns a new instance of this element with cloned child
        elements and cloned attributes.
        """
        el = type(self)()
        el += self.elements.clone()
        el.attributes = self.attributes.clone()
        return el

    def clear(self):
        """ Removes all child elements from this element effectively
        emptying the element's body.
        """
        self.elements.clear()

    def _elements_onadd(self, src, eargs):
        """ When an element is appended to self, this event handler will
        ensure that self is the parent of the element.
        """
        el = eargs.entity
        el._setparent(self)

    def _elements_onbefore(self, src, eargs):
        """ Occurs before an element is added to this element's
        `elements` collection.
        """
        # Raise exception if the element being added already exists in
        # self._elements. 
        #
        # NOTE We need to use the private _elements collection because
        # an infinite recursion exception will occur otherwise. This is
        # because the subclasses of element override its `elements`
        # collection. In side these overrides, children are added thus
        # causing us to get here. Then, calling `self.elements` here
        # recurses back into the override, thus causing the infinite
        # recursion.
        if hasattr(self, '_elements'):
            if eargs.entity in self._elements:
                rent = type(self._elements.parent)
                child = type(eargs.entity)
                raise ValueError(
                    f'Cannot add the same child node ({child}) twice to '
                    f'parent {rent}'
                )
        
    def __getitem__(self, ix):
        # Pass CSS selector to elements collection
        els = elements()
        els += self
        return els[ix]

    def pop(self):
        """ Remove the `element` from the top of the collection and
        return it.
        """
        # TODO Support the `ix` argument (see entities.entities.pop).
        return self.elements.pop()

    def __iter__(self):
        """ Return the iterator from the `elements` attribute of this
        `element` object. This allow the `element` to be iterable:

            ul = dom.ul()
            li = dom.li()

            ul += li

            for li1 in ul:
                assert li is li1
                break
            else:
                assert False
                
        """
        yield from self.elements

    def enumerate(self):
        """ Returns the enumerator from this `element` object's
        `elements` attribute. This allows us to do the following:

            ul = dom.ul()
            li = dom.li()
            li1 = dom.li()

            ul += li0
            ul += li1

            for i, li in ul.enumerate():
                if i == 0:
                    assert li is li0
                eleif i == 1:
                    assert li is li1
                else:
                    assert False
        """
        yield from self.elements.enumerate()

    @property
    def text(self):
        """ Get the combined text contents of each element recursively.
        """
        # NOTE This should match the functionality of jQuery's `.text()`
        # as closely as possible - except for the `.text(function)`
        # overload.

        # FIXME:fa4e6674 This is a non-trivial problem

        r = ''
        blk = False
        for el in self.walk():
            blk = blk or el.isblocklevel
            if isinstance(el, text):
                if r:
                    r += '\n' if blk else ''

                r += ' ' + el.value

                blk = False
        return re.sub('\s+', ' ', r).strip()

    @text.setter
    def text(self, v):
        """ Set the text of this `element`.

        :param: v object: Normally, v will be a str since we are setting
        a text attribute. Regardless, any object can be used to set this
        value. The str() function will be used to convert the object
        into a string.
        """
        self.elements.clear()

        v = str(v)

        self += text(v)

    @property
    def language(self):
        """ Returns the "content language" of the element. The content
        language is the language identified by the ``lang`` attribute of
        the element or the closest ancestor. The content language is
        the value selected by the :lang() pseudoclass.

        Examples::
            “en” for English
            “zh-Hans” for Chinese
            "en-GB-oxendict" for English, Oxford English Dictionary spelling
        """
        lang = self.lang

        if lang:
            return lang

        rent = self.parent

        if rent:
            return rent.language

        return None

    @property
    def id(self):
        """ Defines a unique identifier which must be unique to the
        whole document. Its purpose is to identify the element when
        linking (using a fragment identifier), scripting, or styling
        (with CSS). [_moz_global_attributes]
        """
        return self.attributes['id'].value

    @id.setter
    def id(self, v):
        self.attributes['id'] = v

    @property
    def dir(self):
        """ Returns the value of the the dir global attribute. dir is an
        enumerated attribute that indicates the directionality of the
        element's text.

        It can have the following values:

            * ltr, which means left to right and is to be used for
            languages that are written from the left to the right (like
            English);

            * rtl, which means right to left and is to be used for
            languages that are written from the right to the left (like
            Arabic);

            * auto, which lets the user agent decide. It uses a basic
            algorithm as it parses the characters inside the element
            until it finds a character with a strong directionality,
            then applies that directionality to the whole element.
        """
        return self.attributes['dir'].value

    @dir.setter
    def dir(self, v):
        self.attributes['dir'] = v

    @property
    def lang(self):
        """ The lang global attribute helps define the language of an
        element: the language that non-editable elements are written in,
        or the language that the editable elements should be written in
        by the user. The attribute contains a single “language tag” in
        the format defined in Tags for Identifying Languages (BCP47)
        at https://www.ietf.org/rfc/bcp/bcp47.txt

        https://developer.mozilla.org/en-US/docs/Web/HTML/Global_attributes/lang
        """
        return self.attributes['lang'].value

    @lang.setter
    def lang(self, v):
        self.attributes['lang'] = v

    @property
    def title(self):
        """ Returns the value of the title global attribute. title
        contains text representing advisory information related to the
        element it belongs to.
        """
        return self.attributes['title'].value

    @title.setter
    def title(self, v):
        self.attributes['title'] = v

    @property
    def aria_label(self):
        """ The aria-label attribute is used to define a string that
        labels the current element. Use it in cases where a text label
        is not visible on the screen. If there is visible text labeling
        the element, use aria-labelledby instead.

        This attribute can be used with any typical HTML element; it is
        not limited to elements that have an ARIA role assigned.

        https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/ARIA_Techniques/Using_the_aria-label_attribute
        """
        return self.attributes['aria-label'].value

    @aria_label.setter
    def aria_label(self, v):
        self.attributes['aria-label'] = v

    @property
    def root(self):
        """ Returns the root element of the document.

        A search is performed starting at this element's parent,
        ascending the DOM until an element with no parent is found. That
        element is the root element and it will be returned. If self has
        no parent, it will be considered the root and will be returned.
        """
        ans = self.ancestors
        if ans.count:
            return ans.last

        return self
    
    @property
    def isroot(self):
        """ Returns True if self is the root element; False otherwise.
        """
        return self is self.root

    @property
    def parent(self):
        """ The parent element of this element.

        When an element is append to another element, the first element
        is considered the second element's parent::

            p = dom.p('I am the parent')
            span = dom.span('I am the child')

            p += span

            span.parent is p
        """
        if not hasattr(self, '_parent'):
            self._parent = None

        return self._parent

    @property
    def grandparent(self):
        """ The parent of the parent. If no grandparent element exist,
        None will be returned.
        """
        return self.getparent(1)

    @property
    def greatgrandparent(self):
        """ The parent of the parent of the parent. If no
        great-grandparent element exist, None will be returned.
        """
        return self.getparent(2)

    @property
    def ancestors(self):
        """ Returns an ``elements`` collection with the element's
        lineage. See the docstring at getancestors() for more.
        """
        return self.getancestors()

    def getancestors(self, accompany=False):
        """ Returns an ``elements`` collection with the element's
        lineage. For example, if the DOM is structured like this::

            <html>
                <head>
                    <title>
                        I'm the title
                    </title>
                </head>
            </html>

        The ``elements``` collection returned for the <title> would be
        <head> then title::

            title.getancestors().first is head
            title.getancestors().second is html
        
        If accompany is True, the first element is self::

            title.getancestors().second is title
            title.getancestors().second is head
            title.getancestors().third is html

        :param: accompany bool: If True, the first element returned is
        self.
        """
        els = elements()

        if accompany:
            rent = self
        else:
            rent = self.parent

        while rent:
            els += rent
            rent = rent.parent

        return els

    def getparent(self, num=0):
        """ Returns the the parent element of the object. If num is 0,
        the immediate parent is returned, if 1 the grandparent, and so
        on. 

        Consider using properties like ``parent`` and ``grandparent``
        to get the parent element that you want. This method is useful
        when you don't know ahead of time how far up the the tree you
        need to go.

        :param: num int: The number of parents to skip to get to the
        desired parent: if num==0: return immediate parent, if num==1:
        return grandparent, and so on.
        """
        rent = self.parent

        for _ in range(num):
            try:
                rent = rent.parent
            except AttributeError:
                return None

        return rent

    def _setparent(self, v):
        if v and self.parent and self.parent is not v:
            raise MoveError('Parent already set')
        self._parent = v

    def getsiblings(self, accompany=False):
        """ Returns an ``elements`` collection containing all the sibling
        of this element.

        :param: accompany bool: If True, this element will be the
        first entry in the collection returned.
        """
        # NOTE we may want a gensiblings method for performance reason.
        # TODO s/includeself/accompany/
        els = elements()
        rent = self.parent

        if rent:
            for el in rent.genchildren():
                if not accompany and el is self:
                    continue
                els += el
        return els

    @property
    def siblings(self):
        """ Returns an ``elements`` collection containing all the sibling
        of this element.
        """
        return self.getsiblings()

    @property
    def previous(self):
        """ Return the immediately preceding sibling.
        """
        sibs = self.getsiblings(accompany=True)

        # If it only has self
        if sibs.issingular: 
            return None

        ix = sibs.getindex(self) - 1

        if ix < 0:
            return None

        return sibs(ix)

    @property
    def preceding(self):
        """ Return an elements collection containing all the siblings
        that precede this element.
        """
        els = elements()
        for el in self.getsiblings(accompany=True):
            if el is self:
                break
            els += el
        return els

    @property
    def next(self):
        """ Return the immediately following sibling.
        """
        raise NotImplementedError()

        # NOTE The below may work but has not been tested
        sibs = self.getsiblings(accompany=True)
        ix = sibs.getindex(self)
        return sibs(ix + 1)
                
    @property
    def children(self):
        """ Returns a new ``elements`` collection containing all the
        direct child elements of this element. Note that comment and
        text nodes are not included. To get comment and text nodes as
        well, use ``elements``.

        Also note that this property builds and returns a new elements
        collection. If you only want to itereate over the direct
        children of the element, it would be more perfomant to use
        genchildren since it returns a generator::
            
            for el in els.genchildren():
                ...

        """
        return elements(initial=self.genchildren())

    def getchildren(self, recursive=False):
        """ Returns a new ``elements`` collection containing all the
        child elements of this element. Note that comment and text nodes
        are not included. To get comment and text nodes as well, use
        ``getelements``.

        :param: recursive bool: If True, the collection will contain all
        child elements beneath this element; not just the the immediate
        child elements.
        """
        els = elements()
        for el in self.children:
            els += el

            if recursive:
                els += el.getchildren(recursive=True)
        return els

    def genchildren(self, recursive=False):
        """ Return a generator that can be used to iterate over to get
        all elements except for **comments and text nodes** beneath this
        element within the DOM.

        :param: recursive bool: When True, descend the DOM tree to the
        leaf nodes. When False, only yield the direct children of the
        element.
        """
        for el in self.elements:
            if isinstance(el, comment):
                continue 

            if isinstance(el, text):
                continue

            yield el

            if recursive:
                yield from el.genchildren(recursive=True)

    @property
    def all(self):
        """ Return an elements collection that, when iterated over, will
        produce each of the elements recursively in this element.

        Note that for performance reasons, it is preferable to use the
        walk() method instead. It produces a generator and therefore
        does not require a call to entities.append for each element it
        generates. Use all() for cases where you want to have an
        elements collection to work with and performance isn't an issue.
        """
        return self.getelements(recursive=True)

    def walk(self):
        """ Return a generator that, when iterated over, will produce
        each of the elements recursively in this element.
        """
        return self.genelements(recursive=True)

    def getelements(self, recursive=False):
        """ Returns a new ``elements`` collection containing all the
        child elements of this element. Note that comment and text nodes
        are included as well. To exclude comment and text nodes as well,
        use ``getchildren``.

        :param: recursive bool: If True, the collection will contain all
        child elements beneath this element; not just the the immediate
        child elements.
        """
        els = elements()
        for el in self.elements:
            els += el

            if recursive:
                els += el.getelements(recursive=True)

        return els

    def genelements(self, recursive=False):
        """ Return a generator that, when iterated over, will produce
        each this elements's child elements.

        :param: recursive bool: When True, descend the DOM tree to the
        leaf nodes. When False, only yield the direct children of the
        element.
        """
        for el in self.elements:
            yield el
            if recursive:
                yield from el.genelements(recursive=True)

    @property
    def elements(self):
        """ Returns the ``elements`` collection containing all the
        child elements of this element. Note that comment and text nodes
        are included as well. To exclude comment and text nodes as well,
        use ``children``.
        """
        if not hasattr(self, '_elements'):
            self._elements = elements()
            self._elements.onbeforeadd += self._elements_onbefore
            self._elements.onadd += self._elements_onadd
            self._elements._setparent(self)
        return self._elements
                
    @elements.setter
    def elements(self, v):
        self._elements = v

    @property
    def classes(self):
        """ Returns the class attribute.
        """
        return self.attributes['class']

    @classes.setter
    def classes(self, v):
        self.attributes['class'] = v

    @property
    def attributes(self):
        """ Returns the class attribute.
        """
        if not hasattr(self, '_attributes'):
            self._attributes = attributes(self)
        return self._attributes

    @attributes.setter
    def attributes(self, v):
        self._attributes = v

    def __contains__(self, el):
        return el in self.elements

    def __lshift__(self, el):
        """ Overrides the << operator to insert ``el` at the begining of
        this element's `elements` collection.

        :param: el str|element:
            if el is str:
                A new text node will be created with el as the text
                node's text property. The text node will be unshfted
                into the child elements collection.

            if el is element:
                The el will simply be unshifted onto the child elements
                collection.
        """
        self.elements << el
        return self

    def __iadd__(self, el):
        """ Push ``el` at the top of the elements collection.

        :param: el str|element|sequence:
            if el is str:
                A new text node will be created with el as the text
                node's text property. The text node will be unshfted
                into the child elements collection.

            if el is element:
                The el will simply be pushed onto the child elements
                collection.

            if el is sequence:
                If el is a sequence, such as a tuple or an elements
                collection, each element in the sequence will be
                appended to the child elements collection.
        """
        self.elements += el
        return self

    @classproperty
    def tag(cls):
        """ Returns the name of the element.

            # Invoked as a classproperty
            assert 'head' == dom.head.tag

            # Invoked as an regular (instance) @property
            assert 'head' == dom.head().tag

        Note that subclasses of elements will always return the HTML5
        tag name:

            class lead(dom.p):
                pass

            assert 'p' == lead.tag
        """
        if type(cls) is not type:
            cls = type(cls)

        for typ in cls.__mro__:
            if typ is element:
                return prev.__name__
            prev = typ

    @property
    def pretty(self):
        """ Return a str containing a user-friendly representation of
        the element. If the element is a text node, only the text will
        be returned. For all other element types, the return string will
        be an HTML representation of the element with its child elements
        nested, using indenting and linefeeds for readability.
        """
        body = str()
        if isinstance(self, text):
            body = self.html

        # Iterate through all the child elements
        # TODO Remove enumerate; i is not being used.
        for i, el in enumerate(self.elements):
            if body: body += '\n'
            body += el.pretty

        # If this element is a text node, just return the body we've
        # built
        if isinstance(self, text):
            return body

        # Use textwrapper.indent on the body
        body = indent(body, '  ')

        # Build the start tag
        r = '<%s'
        args = [self.tag]

        # Append outer tags attributes
        if self.attributes.count:
            r += ' %s'
            args.append(self.attributes.html)

        # Close first tag
        r += '>'

        # If not void, line feed
        if not self.isvoid:
            r += '\n'

        # If there is a body, add it to return
        if body:
            r += '%s\n'
            args += [body]

        if self.isvoid:
            pass
            #r += '>'
        else:
            # If not void, add closing tag
            r += '</%s>'
            args += [self.tag]

        return r % tuple(args)

    @property
    def html(self):
        """ Returns the HTML representation of the element and its
        children.

        Note that there won't be any linefeeds or indentation to make
        the HTML human-friendly. The HTML is intended for a browser or
        for some other parser. For a human-friendly version, use the
        ``element.pretty`` property.
        """
        body = str()

        if isinstance(self, text):
            body = self.html

        for i, el in builtins.enumerate(self.elements):
            body += el.html

        if isinstance(self, text):
            return body

        r = '<%s'
        args = [self.tag]

        if self.attributes.count:
            r += ' %s'
            args.append(self.attributes.html)

        r += '>'

        if body:
            r += '%s'
            args += [body]

        if not self.isvoid:
            r += '</%s>'
            args += [self.tag]

        return r % tuple(args)

    @property
    def last(self):
        return self.elements.last
        
    def __str__(self):
        return self.pretty

    def __repr__(self):
        r = '%s(%s)'
        attrs = ' '.join(str(x) for x in self.attributes)
        r %= type(self).__name__, attrs
        return r

class headers(elements):
    """ A class used to contain a collection of ``header`` elements.
    """

class header(element):
    """ The <header> HTML element represents introductory content,
    typically a group of introductory or navigational aids. It may
    contain some heading elements but also a logo, a search form, an
    author name, and other elements.
    """

class titles(elements):
    """ A class used to contain a collection of ``title`` elements.
    """

class title(element):
    """ The <title> HTML element defines the document's title that is
    shown in a browser's title bar or a page's tab. It only contains
    text; tags within the element are ignored.  
    """

class smalls(elements):
    """ A class used to contain a collection of ``small`` elements.
    """

class small(element):
    """ The <small> HTML element represents side-comments and small
    print, like copyright and legal text, independent of its styled
    presentation. By default, it renders text within it one font-size
    smaller, such as from small to x-small.
    """

class ps(elements):
    """ A class used to contain a collection of ``p`` elements.
    """

class p(element):
    """ The <p> HTML element represents a paragraph. Paragraphs are
    usually represented in visual media as blocks of text separated from
    adjacent blocks by blank lines and/or first-line indentation, but
    HTML paragraphs can be any structural grouping of related content,
    such as images or form fields.
    """

# TODO:dea3866d Remove this line. Since we will likely ``import dom``
# instead of `from dom import p`, we don't need to create a
# user-friendly alias for p. Instantiating like this should work fine::
#
#    ### from dom import p, a, div
#    import dom
#    p = dom.p('This is a paragraph')
#    p1 = dom.p('This is another paragraph')

class addresses(elements):
    """ A class used to contain a collection of ``address`` elements.
    """

class address(element):
    """The <address> HTML element indicates that the enclosed HTML
    provides contact information for a person or people, or for an
    organization.
    """

class asides(elements):
    """ A class used to contain a collection of ``aside`` elements.
    """

class aside(element):
    """ The <aside> HTML element represents a portion of a document
    whose content is only indirectly related to the document's main
    content. Asides are frequently presented as sidebars or call-out
    boxes.
    """

class dialogs(elements):
    """ A class used to contain a collection of ``dialog`` elements.
    """

class dialog(element):
    """ The <dialog> HTML element represents a dialog box or other
    interactive component, such as a dismissible alert, inspector, or
    subwindow.

    Note that this element isn't supported by Firefox or Safari.
    """
    # TODO The tabindex attribute must not be used on the <dialog>
    # element. See
    # https://developer.mozilla.org/en-US/docs/Web/HTML/Element/dialog

class figcaptions(elements):
    """ A class used to contain a collection of ``figcaption`` elements.
    """

class figcaption(element):
    """ The <figcaption> HTML element represents a caption or legend
    describing the rest of the contents of its parent <figure> element.
    """

class figures(elements):
    """ A class used to contain a collection of ``figure`` elements.
    """

class figure(element):
    """ The <figure> HTML element represents self-contained content,
    potentially with an optional caption, which is specified using the
    <figcaption> element. The figure, its caption, and its contents are
    referenced as a single unit.
    """

class articles(elements):
    """ A class used to contain a collection of ``article`` elements.
    """

class article(element):
    """ The HTML <article> element represents a self-contained
    composition in a document, page, application, or site, which is
    intended to be independently distributable or reusable (e.g., in
    syndication). Examples include: a forum post, a magazine or
    newspaper article, or a blog entry.  
    """

class sections(elements):
    """ A class used to contain a collection of ``section`` elements.
    """

class section(element):
    """ The HTML <section> element represents a standalone section —
    which doesn't have a more specific semantic element to represent it
    — contained within an HTML document. Typically, but not always,
    sections have a heading.
    """

class footers(elements):
    """ A class used to contain a collection of ``footer`` elements.
    """

class footer(element):
    """ The <footer> HTML element represents a footer for its nearest
    sectioning content or sectioning root element. A <footer> typically
    contains information about the author of the section, copyright data
    or links to related documents.
    """

class text(element):
    """ Represents a text node in an HTML document.

    See the following for information about a text nodes:
        
        https://developer.mozilla.org/en-US/docs/Web/API/Text
    """
    def __init__(self, v, esc=True, *args, **kwargs):
        """ Create the text node.

        :param: v str: The value of the text node; i.e., the text
        itself.

        :param: esc bool: Convert the characters &, < and > in v to
        HTML-safe sequences. 
        """
        super().__init__(*args, **kwargs)

        self._value = v

        # We may want to do this in the html accessor
        self._html = v
        if esc:
            import html as htmlmod
            self._html = htmlmod.escape(self._value)

    def clone(self):
        """ Create a new text node with the same text value as this text
        node.
        """
        el = type(self)(self._value)

        # We can't append elements to a text node
        if not isinstance(self, text):
            # TODO Is it possible to get here?
            el += self.elements.clone()

        # TODO I'm not sure how text nodes could even have attributes.
        # We may want to remove this and prevent text nodes from having
        # attributes. There may be some special cases where this makes
        # sense but I've forgotten about them at the moment.
        el.attributes = self.attributes.clone()

        return el

    def __str__(self):
        """ Return the text value of the text node.
        """
        return self.value

    @property
    def html(self):
        """ Returns the HTML representation of the text node.  For
        effeciency, needless whitespace will be removed.
        """
        return dedent(self._html).strip('\n')

    @html.setter
    def html(self, v):
        self._html = v

    @property
    def value(self):
        """ Return the text value of the text node.
        """
        return self._value

class wbrs(elements):
    """ A class used to contain a collection of ``wbr`` elements.
    """

class wbr(element):
    """The HTML <wbr> element represents a word break opportunity—a
    position within text where the browser may optionally break a line,
    though its line-breaking rules would not otherwise create a break at
    that location.

    https://developer.mozilla.org/en-US/docs/Web/HTML/Element/wbr
    """
    pass

wordbreaks = wbrs
wordbreak = wbr

class brs(elements):
    """ A class used to contain a collection of ``br`` elements.
    """

class br(element):
    """ The HTML <br> element produces a line break in text
    (carriage-return). It is useful for writing a poem or an address,
    where the division of lines is significant.

    https://developer.mozilla.org/en-US/docs/Web/HTML/Element/br
    """
    isvoid=True
    tag = 'br'

class comments(elements):
    """ A class used to contain a collection of ``comment`` nodes.
    """

class comment(element):
    """ Represents an HTML comment.
    """
    tag = '<!---->'
    def __init__(self, txt, *args, **kwargs):
        """ Create the comment.

        :param: txt str: The comment itself.
        """
        super().__init__(*args, **kwargs)
        self._text = txt

    @property
    def html(self):
        """ Returns an HTML representation of the comment.
        """
        return '<!--%s-->' % self._text

    @property
    def pretty(self):
        """ Returns an human-friendly representation of the comment.
        """
        return '<!--%s-->' % self._text
    
class forms(elements):
    """ A class used to contain a collection of ``form`` elements.
    """

class form(element):
    """ Represents an HTML <form> element.
    """
    @property
    def post(self):
        """ Returns a percent-encoded ASCII text string containing the
        value of the input elements (input, select and textarea) in the
        form.
        """

        # Get input elements
        els = self['input, select, textarea']

        # Build dict with values of input elements
        d = dict()
        for el in els:
            if isinstance(el, input):
                d[el.name] = el.value
            elif isinstance(el, select):
                opts = el['[selected]']
                for opt in opts:
                    try:
                        d[el.name].append(opt.value)
                    except Exception as ex:
                        d[el.name] = list([opt.value])

            elif isinstance(el, textarea):
                d[el.name] = el.text

        # Convert the dict to a percent-encoded ASCII text string and
        # return.
        # See https://docs.python.org/3/library/urllib.request.html#urllib-examples
        import urllib.parse
        return urllib.parse.urlencode(d, doseq=True).encode('ascii')

    @post.setter
    def post(self, v):
        """ Sets the value of the form elements in the form with a query
        string.
        
        :param: v str: A query string given as a string argument (data of
        type application/x-www-form-urlencoded). 
        """
        import urllib.parse
        d = urllib.parse.parse_qs(v)

        for k, v in d.items():
            el = self['[name=%s]' % k].first
            if isinstance(el, input):
                el.value = v[0]
            elif isinstance(el, select):
                el.selected = v
            elif isinstance(el, textarea):
                el.text = v[0]

    @property
    def method(self):
        """ Returns the method attribute of the form. 

        For example, if the form were represented like this in HTML:
            
            <form method="GET">
                ...
            </form>

        then 'GET' would be returned.
        """
        # TODO We should probably always return as uppercase for the
        # sake of consistency and predictability
        return self.attributes['method'].value

    @method.setter
    def method(self, v):
        self.attributes['method'].value = v

    @property
    def novalidate(self):
        """ This boolean attribute indicates that the form shouldn't be
        validated when submitted. If this attribute is not set (and
        therefore the form is validated), it can be overridden by a
        formnovalidate attribute on a <button>, <input type="submit">,
        or <input type="image"> element belonging to the form.
        """
        # TODO:369795a1 @property's for boolean attribute should return
        # True or False and their setters should accept only True and
        # False. If a user really wants to violate the boolean nature of
        # an attribute (e.g., <form novalidate="novalidate">) then they
        # can use the attributes collection directly
        # (frm.attributes['novalidate'] = 'novalidate').
        return self.attributes['novalidate'].value

    @novalidate.setter
    def novalidate(self, v):
        # TODO:369795a1 
        self.attributes['novalidate'].value = v

    @property
    def accept_charset(self):
        """ Space-separated character encodings the server accepts. The
        browser uses them in the order in which they are listed. The
        default value means the same encoding as the page. (In previous
        versions of HTML, character encodings could also be delimited by
        commas.)
        """
        return self.attributes['accept-charset'].value

    @accept_charset.setter
    def accept_charset(self, v):
        self.attributes['accept-charset'].value = v

    @property
    def action(self):
        """The URL that processes the form submission. This value can be
        overridden by a formaction attribute on a <button>, <input
        type="submit">, or <input type="image"> element.
        """
        return self.attributes['action'].value

    @action.setter
    def action(self, v):
        self.attributes['action'].value = v

    @property
    def target(self):
        """ Indicates where to display the response after submitting the
        form. In HTML 4, this is the name/keyword for a frame. In HTML5,
        it is a name/keyword for a browsing context (for example, tab,
        window, or iframe). The following keywords have special
        meanings:

            _self (default): Load into the same browsing context as the
            current one.

            _blank: Load into a new unnamed browsing context.

            _parent: Load into the parent browsing context of the
            current one. If no parent, behaves the same as _self.

            _top: Load into the top-level browsing context (i.e., the
            browsing context that is an ancestor of the current one and
            has no parent). If no parent, behaves the same as _self.

            This value can be overridden by a formtarget attribute on a
            <button>, <input type="submit">, or <input type="image">
            element.
        """
        return self.attributes['target'].value

    @target.setter
    def target(self, v):
        self.attributes['target'].value = v

    @property
    def enctype(self):
        """ If the value of the method attribute is post, enctype is the
        MIME type of the form submission. Possible values:

            - application/x-www-form-urlencoded: The default value.

            - multipart/form-data: Use this if the form contains <input>
              elements with type=file.  

            - text/plain: Introduced by HTML5 for debugging purposes.

        This value can be overridden by formenctype attributes on
        <button>, <input type="submit">, or <input type="image">
        elements.
        """
        return self.attributes['enctype'].value

    @enctype.setter
    def enctype(self, v):
        self.attributes['enctype'].value = v

    @property
    def name(self):
        """ The name of the form. The value must not be the empty
        string, and must be unique among the form elements in the forms
        collection that it is in, if any.
        """
        return self.attributes['name'].value

    @name.setter
    def name(self, v):
        self.attributes['name'].value = v

    @property
    def autocomplete(self):
        """ Indicates whether input elements can by default have their
        values automatically completed by the browser. autocomplete
        attributes on form elements override it on <form>. Possible
        values:

            off: The browser may not automatically complete entries.
            (Browsers tend to ignore this for suspected login forms)

            on: The browser may automatically complete entries.
        """
        return self.attributes['autocomplete'].value

    @autocomplete.setter
    def autocomplete(self, v):
        self.attributes['autocomplete'].value = v

class links(elements):
    """ A class used to contain a collection of ``link`` elements.
    """

class link(element):
    """ The <link> HTML element specifies relationships between the
    current document and an external resource. This element is most
    commonly used to link to stylesheets, but is also used to establish
    site icons (both "favicon" style icons and icons for the home screen
    and apps on mobile devices) among other things.
    """
    isvoid = True
    @property
    def crossorigin(self):
        """ This enumerated attribute indicates whether CORS must be
        used when fetching the resource. CORS-enabled images can be
        reused in the <canvas> element without being tainted. The
        allowed values are: 

            anonymous

                A cross-origin request (i.e. with an Origin HTTP header)
                is performed, but no credential is sent (i.e. no cookie,
                X.509 certificate, or HTTP Basic authentication). If the
                server does not give credentials to the origin site (by
                not setting the Access-Control-Allow-Origin HTTP header)
                the resource will be tainted and its usage restricted.  

            use-credentials

                A cross-origin request (i.e. with an Origin HTTP header)
                is performed along with a credential sent (i.e. a
                cookie, certificate, and/or HTTP Basic authentication is
                performed). If the server does not give credentials to
                the origin site (through
                Access-Control-Allow-Credentials HTTP header), the
                resource will be tainted and its usage restricted.

        If the attribute is not present, the resource is fetched without
        a CORS request (i.e. without sending the Origin HTTP header),
        preventing its non-tainted usage. If invalid, it is handled as
        if the enumerated keyword anonymous was used. See CORS settings
        attributes for additional information.
        """
        return self.attributes['crossorigin'].value

    @crossorigin.setter
    def crossorigin(self, v):
        self.attributes['crossorigin'].value = v

    @property
    def referrerpolicy(self):
        """ A string indicating which referrer to use when fetching the
        resource:
        """
        return self.attributes['referrerpolicy'].value

    @referrerpolicy.setter
    def referrerpolicy(self, v):
        self.attributes['referrerpolicy'].value = v

    @property
    def integrity(self):
        """ Contains inline metadata — a base64-encoded cryptographic
        hash of the resource (file) you’re telling the browser to fetch.
        The browser can use this to verify that the fetched resource has
        been delivered free of unexpected manipulation. 
        """
        return self.attributes['integrity'].value

    @integrity.setter
    def integrity(self, v):
        self.attributes['integrity'].value = v

    @property
    def hreflang(self):
        """ This attribute indicates the language of the linked
        resource. It is purely advisory. Allowed values are specified by
        RFC 5646: Tags for Identifying Languages (also known as BCP 47).
        Use this attribute only if the href attribute is present.
        """
        return self.attributes['hreflang'].value

    @hreflang.setter
    def hreflang(self, v):
        self.attributes['hreflang'].value = v

    @property
    def importance(self):
        """ Indicates the relative fetch priority for the resource.

        See: https://developers.google.com/web/updates/2019/02/priority-hints
        """
        return self.attributes['importance'].value

    @importance.setter
    def importance(self, v):
        self.attributes['importance'].value = v

    @property
    def media(self):
        """ This attribute specifies the media that the linked resource
        applies to. Its value must be a media type / media query. This
        attribute is mainly useful when linking to external stylesheets
        — it allows the user agent to pick the best adapted one for the
        device it runs on.
        """
        return self.attributes['media'].value

    @media.setter
    def media(self, v):
        self.attributes['media'].value = v

    @property
    def href(self):
        """ This attribute specifies the URL of the linked resource. A
        URL can be absolute or relative.
        """
        return self.attributes['href'].value

    @href.setter
    def href(self, v):
        self.attributes['href'].value = v

    @property
    def sizes(self):
        """ This attribute defines the sizes of the icons for visual
        media contained in the resource. It must be present only if the
        rel contains a value of icon or a non-standard type such as
        Apple's apple-touch-icon.
        """
        return self.attributes['sizes'].value

    @sizes.setter
    def sizes(self, v):
        self.attributes['sizes'].value = v

    @property
    def rel(self):
        """ This attribute names a relationship of the linked document
        to the current document. The attribute must be a space-separated
        list of link type values.
        """
        return self.attributes['rel'].value

    @rel.setter
    def rel(self, v):
        self.attributes['rel'].value = v

class buttons(elements):
    """ A class used to contain a collection of ``button`` elements.
    """

class button(element):
    @property
    def formtarget(self):
        """ If the button is a submit button, this attribute is an
        author-defined name or standardized, underscore-prefixed keyword
        indicating where to display the response from submitting the
        form. This is the name of, or keyword for, a browsing context (a
        tab, window, or <iframe>). If this attribute is specified, it
        overrides the target attribute of the button's form owner.
        """
        return self.attributes['formtarget'].value

    @formtarget.setter
    def formtarget(self, v):
        self.attributes['formtarget'].value = v

    @property
    def formaction(self):
        """ The URL that processes the information submitted by the
        button. Overrides the action attribute of the button's form
        owner. Does nothing if there is no form owner.
        """
        return self.attributes['formaction'].value

    @formaction.setter
    def formaction(self, v):
        self.attributes['formaction'].value = v

    @property
    def autofocus(self):
        """ This Boolean attribute specifies that the button should have
        input focus when the page loads. Only one element in a document
        can have this attribute.
        """
        # TODO:369795a1 @
        return self.attributes['autofocus'].value

    @autofocus.setter
    def autofocus(self, v):
        self.attributes['autofocus'].value = v

    @property
    def type(self):
        """ The default behavior of the button. Possible values are:
        submit, reset and button.
        """
        return self.attributes['type'].value

    @type.setter
    def type(self, v):
        self.attributes['type'].value = v

    @property
    def formnovalidate(self):
        """ If the button is a submit button, this Boolean attribute
        specifies that the form is not to be validated when it is
        submitted. If this attribute is True, it overrides the
        novalidate attribute of the button's form owner.
        """
        # TODO:369795a1 @
        return self.attributes['formnovalidate'].value

    @formnovalidate.setter
    def formnovalidate(self, v):
        self.attributes['formnovalidate'].value = v

    @property
    def form(self):
        """ The <form> element to associate the button with (its form
        owner). The value of this attribute must be the id of a <form>
        in the same document. (If this attribute is not set, the
        <button> is associated with its ancestor <form> element, if
        any.)
        """
        return self.attributes['form'].value

    @form.setter
    def form(self, v):
        self.attributes['form'].value = v

    @property
    def name(self):
        """ The name of the button, submitted as a pair with the
        button’s value as part of the form data, when that button is
        used to submit the form.
        """
        return self.attributes['name'].value

    @name.setter
    def name(self, v):
        self.attributes['name'].value = v

    @property
    def formenctype(self):
        """ If the button is a submit button (it's inside/associated
        with a <form> and doesn't have type="button"), specifies how to
        encode the form data that is submitted. 
        """
        return self.attributes['formenctype'].value

    @formenctype.setter
    def formenctype(self, v):
        self.attributes['formenctype'].value = v

    @property
    def disabled(self):
        """ This Boolean attribute prevents the user from interacting
        with the button: it cannot be pressed or focused.
        """
        # TODO:369795a1 @
        return self.attributes['disabled'].value

    @disabled.setter
    def disabled(self, v):
        self.attributes['disabled'].value = v

    @property
    def value(self):
        """ Defines the value associated with the button’s name when
        it’s submitted with the form data. This value is passed to the
        server in params when the form is submitted using this button.
        """
        return self.attributes['value'].value

    @value.setter
    def value(self, v):
        self.attributes['value'].value = v

    @property
    def formmethod(self):
        """ If the button is a submit button (it's inside/associated
        with a <form> and doesn't have type="button"), this attribute
        specifies the HTTP method used to submit the form. Possible
        values: POST and GET.
        """
        return self.attributes['formmethod'].value

    @formmethod.setter
    def formmethod(self, v):
        self.attributes['formmethod'].value = v

class navs(elements):
    """ A class used to contain a collection of ``nav`` elements.
    """

class nav(element):
    """ The <nav> HTML element represents a section of a page whose
    purpose is to provide navigation links, either within the current
    document or to other documents. Common examples of navigation
    sections are menus, tables of contents, and indexes.
    """

class lis(elements):
    """ A class used to contain a collection of ``li`` elements.
    """

class li(element):
    """ The <li> HTML element is used to represent an item in a list. It
    must be contained in a parent element: an ordered list (<ol>), an
    unordered list (<ul>), or a menu (<menu>). In menus and unordered
    lists, list items are usually displayed using bullet points. In
    ordered lists, they are usually displayed with an ascending counter
    on the left, such as a number or letter.
    """
    @property
    def value(self):
        """ This integer attribute indicates the current ordinal value
        of the list item as defined by the <ol> element. The only
        allowed value for this attribute is a number, even if the list
        is displayed with Roman numerals or letters. List items that
        follow this one continue numbering from the value set. The value
        attribute has no meaning for unordered lists (<ul>) or for menus
        (<menu>).
        """
        return self.attributes['value'].value

    @value.setter
    def value(self, v):
        self.attributes['value'].value = v

class outputs(elements):
    """ A class used to contain a collection of ``output`` elements.
    """

class output(element):
    """ The <output> HTML element is a container element into which a
    site or app can inject the results of a calculation or the outcome
    of a user action.
    """
    @property
    def for_(self):
        """ A space-separated list of other elements’ ids, indicating
        that those elements contributed input values to (or otherwise
        affected) the calculation.
        """
        return self.attributes['for'].value

    @for_.setter
    def for_(self, v):
        self.attributes['for'].value = v

    @property
    def form(self):
        """ The <form> element to associate the output with (its form
        owner). The value of this attribute must be the id of a <form>
        in the same document. (If this attribute is not set, the
        <output> is associated with its ancestor <form> element, if
        any.)
        """
        return self.attributes['form'].value

    @form.setter
    def form(self, v):
        self.attributes['form'].value = v

    @property
    def name(self):
        """ The element's name. Used in the form.elements API.
        """
        return self.attributes['name'].value

    @name.setter
    def name(self, v):
        self.attributes['name'].value = v

class fieldsets(elements):
    """ A class used to contain a collection of ``fieldset`` elements.
    """

class fieldset(element):
    """ The <fieldset> HTML element is used to group several controls as
    well as labels (<label>) within a web form.
    """
    @property
    def form(self):
        """ This attribute takes the value of the id attribute of a
        <form> element you want the <fieldset> to be part of, even if it
        is not inside the form. Please note that usage of this is
        confusing — if you want the <input> elements inside the
        <fieldset> to be associated with the form, you need to use the
        form attribute directly on those elements.
        """
        return self.attributes['form'].value

    @form.setter
    def form(self, v):
        self.attributes['form'].value = v

    @property
    def name(self):
        """ The name associated with the group.
        """
        return self.attributes['name'].value

    @name.setter
    def name(self, v):
        self.attributes['name'].value = v

    @property
    def disabled(self):
        """ If this boolean attribute is set, all form controls that are
        descendants of the <fieldset>, are disabled, meaning they are
        not editable and won't be submitted along with the <form>. They
        won't receive any browsing events, like mouse clicks or
        focus-related events. By default browsers display such controls
        grayed out. Note that form elements inside the <legend> element
        won't be disabled.
        """
        # TODO:369795a1
        return self.attributes['disabled'].value

    @disabled.setter
    def disabled(self, v):
        self.attributes['disabled'].value = v

class tfoots(elements):
    """ A class used to contain a collection of ``tfoot`` elements.
    """

class tfoot(element):
    """ The <tfoot> HTML element defines a set of rows summarizing the
    columns of the table.
    """

class params(elements):
    """ A class used to contain a collection of ``param`` elements.
    """

class param(element):
    """ The <param> HTML element defines parameters for an <object>
    element.
    """
    @property
    def name(self):
        """ Name of the parameter.
        """
        return self.attributes['name'].value

    @name.setter
    def name(self, v):
        self.attributes['name'].value = v

    @property
    def value(self):
        """ Specifies the value of the parameter.
        """
        return self.attributes['value'].value

    @value.setter
    def value(self, v):
        self.attributes['value'].value = v

class as_(elements):
    """ A class used to contain a collection of ``a`` elements.
    """

class a(element):
    """ The <a> HTML element (or anchor element), with its href
    attribute, creates a hyperlink to web pages, files, email addresses,
    locations in the same page, or anything else a URL can address.

    Content within each <a> should indicate the link's destination. If
    the href attribute is present, pressing the enter key while focused
    on the <a> element will activate it.
    """
    def __init__(self, body=None, *args, **kwargs):
        """ Create an anchor element.

        :param: body file.file|str|element|elements: This override deals
        with body as a file.file type. For the other types, consult the
        docstring at element.__init__.

        When the body is a file.file type, the path of the file can be
        used as the href. The basename of the file.file becomes the text
        of of the node.
        """
        # NOTE The body as file.file version of the constructor could
        # use a lot more work. The file.basename doesn't seem to exist,
        # and it's not clear at the moment if file.path would amount to
        # a correct (relative) url. As a side note, we should also
        # except body as ecommerce.url for obvious reason. We should
        # also test if body is file.resource because, in that case, we
        # do have a url property that would be appropriate for self.href
        # assuming body.local is False.
        if isinstance(body, file.file):
            self.href = body.path
            body = body.basename

        super().__init__(body, *args, **kwargs)

    @property
    def referrerpolicy(self):
        """ How much of the referrer to send when following the link.
        """
        return self.attributes['referrerpolicy'].value

    @referrerpolicy.setter
    def referrerpolicy(self, v):
        self.attributes['referrerpolicy'].value = v

    @property
    def target(self):
        """ Where to display the linked URL, as the name for a browsing
        context (a tab, window, or <iframe>).
        """
        return self.attributes['target'].value

    @target.setter
    def target(self, v):
        self.attributes['target'].value = v

    @property
    def hreflang(self):
        """ Hints at the human language of the linked URL. No built-in
        functionality. Allowed values are the same as the global
        ``lang`` attribute (``element.lang``).
        """
        return self.attributes['hreflang'].value

    @hreflang.setter
    def hreflang(self, v):
        self.attributes['hreflang'].value = v

    @property
    def ping(self):
        """ A space-separated list of URLs. When the link is followed,
        the browser will send POST requests with the body PING to the
        URLs. Typically for tracking.
        """
        return self.attributes['ping'].value

    @ping.setter
    def ping(self, v):
        self.attributes['ping'].value = v

    @property
    def media(self):
        """ The media attribute specifies what media or device the
        linked document is optimized for.  This attribute is used to
        specify that the target URL is designed for special devices
        (like iPhone), speech or print media.  This attribute can accept
        several values.  Only used if the href attribute is present.
        Note: This attribute is purely advisory.
        """
        return self.attributes['media'].value

    @media.setter
    def media(self, v):
        self.attributes['media'].value = v

    @property
    def href(self):
        """ The URL that the hyperlink points to. Links are not
        restricted to HTTP-based URLs — they can use any URL scheme
        supported by browsers.
        """
        return self.attributes['href'].value

    @href.setter
    def href(self, v):
        self.attributes['href'].value = v

    @property
    def download(self):
        """ Prompts the user to save the linked URL instead of
        navigating to it.
        """
        return self.attributes['download'].value

    @download.setter
    def download(self, v):
        self.attributes['download'].value = v

    @property
    def rel(self):
        """ The relationship of the linked URL as space-separated link
        types.
        """
        return self.attributes['rel'].value

    @rel.setter
    def rel(self, v):
        self.attributes['rel'].value = v

    @property
    def type(self):
        """ Hints at the linked URL’s format with a MIME type. No
        built-in functionality.
        """
        return self.attributes['type'].value

    @type.setter
    def type(self, v):
        self.attributes['type'].value = v

anchors = as_
anchor = a

class audios(elements):
    """ A class used to contain a collection of ``audio`` elements.
    """

class audio(element):
    """ The <audio> HTML element is used to embed sound content in
    documents. It may contain one or more audio sources, represented
    using the src attribute or the <source> element: the browser will
    choose the most suitable one. It can also be the destination for
    streamed media, using a MediaStream.
    """
    @property
    def crossorigin(self):
        """ This enumerated attribute indicates whether to use CORS to
        fetch the related audio file.
        """
        return self.attributes['crossorigin'].value

    @crossorigin.setter
    def crossorigin(self, v):
        self.attributes['crossorigin'].value = v

    @property
    def loop(self):
        """ A Boolean attribute: if specified, the audio player will
        automatically seek back to the start upon reaching the end of
        the audio.
        """
        # TODO:369795a1

        return self.attributes['loop'].value

    @loop.setter
    def loop(self, v):
        self.attributes['loop'].value = v

    @property
    def buffered(self):
        return self.attributes['buffered'].value

    @buffered.setter
    def buffered(self, v):
        self.attributes['buffered'].value = v

    @property
    def src(self):
        """ The URL of the audio to embed. This is subject to HTTP
        access controls. This is optional; you may instead use the
        <source> element within the audio block to specify the audio to
        embed.
        """
        return self.attributes['src'].value

    @src.setter
    def src(self, v):
        self.attributes['src'].value = v

    @property
    def controls(self):
        """ If this attribute is present, the browser will offer
        controls to allow the user to control audio playback, including
        volume, seeking, and pause/resume playback.
        """
        return self.attributes['controls'].value

    @controls.setter
    def controls(self, v):
        self.attributes['controls'].value = v

    @property
    def autoplay(self):
        """ A Boolean attribute: if specified, the audio will
        automatically begin playback as soon as it can do so, without
        waiting for the entire audio file to finish downloading.
        """
        # TODO:369795a1
        return self.attributes['autoplay'].value

    @autoplay.setter
    def autoplay(self, v):
        self.attributes['autoplay'].value = v

    @property
    def muted(self):
        """ A Boolean attribute that indicates whether the audio will be
        initially silenced. Its default value is false.
        """
        # TODO:369795a1
        return self.attributes['muted'].value

    @muted.setter
    def muted(self, v):
        self.attributes['muted'].value = v

    @property
    def preload(self):
        """ This enumerated attribute is intended to provide a hint to
        the browser about what the author thinks will lead to the best
        user experience.
        """
        return self.attributes['preload'].value

    @preload.setter
    def preload(self, v):
        self.attributes['preload'].value = v

class bases(elements):
    """ A class used to contain a collection of ``base`` elements.
    """

class base(element):
    """ The HTML <base> element specifies the base URL to use for all
    relative URLs contained within a document. There can be only one
    <base> element in a document.
    """
    isvoid = True

    @property
    def target(self):
        """ A keyword or author-defined name of the default browsing
        context to show the results of navigation from <a>, <area>, or
        <form> elements without explicit target attributes.
        """
        return self.attributes['target'].value

    @target.setter
    def target(self, v):
        self.attributes['target'].value = v

    @property
    def href(self):
        """ The base URL to be used throughout the document for relative
        URLs. Absolute and relative URLs are allowed.
        """
        return self.attributes['href'].value

    @href.setter
    def href(self, v):
        self.attributes['href'].value = v

class imgs(elements):
    """ A class used to contain a collection of ``img`` elements.
    """

class img(element):
    """ The <img> HTML element embeds an image into the document.
    """
    isvoid = True
    @property
    def crossorigin(self):
        """ Indicates if the fetching of the image must be done using a
        CORS request. Image data from a CORS-enabled image returned from
        a CORS request can be reused in the <canvas> element without
        being marked "tainted".
        """
        return self.attributes['crossorigin'].value

    @crossorigin.setter
    def crossorigin(self, v):
        self.attributes['crossorigin'].value = v

    @property
    def referrerpolicy(self):
        """ A string indicating which referrer to use when fetching the
        resource.
        """
        return self.attributes['referrerpolicy'].value

    @referrerpolicy.setter
    def referrerpolicy(self, v):
        self.attributes['referrerpolicy'].value = v

    @property
    def loading(self):
        """ Indicates how the browser should load the image.
        """
        return self.attributes['loading'].value

    @loading.setter
    def loading(self, v):
        self.attributes['loading'].value = v

    @property
    def height(self):
        """ The intrinsic height of the image, in pixels. Must be an
        integer without a unit.
        """
        return self.attributes['height'].value

    @height.setter
    def height(self, v):
        self.attributes['height'].value = v

    @property
    def intrinsicsize(self):
        """ This attribute tells the browser to ignore the actual
        intrinsic size of the image and pretend it’s the size specified
        in the attribute. Specifically, the image would raster at these
        dimensions and naturalWidth/naturalHeight on images would return
        the values specified in this attribute.
        """
        return self.attributes['intrinsicsize'].value

    @intrinsicsize.setter
    def intrinsicsize(self, v):
        self.attributes['intrinsicsize'].value = v

    @property
    def src(self):
        """ The image URL. Mandatory for the <img> element. On browsers
        supporting srcset, src is treated like a candidate image with a
        pixel density descriptor 1x, unless an image with this pixel
        density descriptor is already defined in srcset, or unless
        srcset contains w descriptors.
        """
        return self.attributes['src'].value

    @src.setter
    def src(self, v):
        self.attributes['src'].value = v

    @property
    def ismap(self):
        """ This boolean attribute indicates that the image is part of a
        server-side map. If so, the coordinates where the user clicked
        on the image are sent to the server.
        """
        # TODO:369795a1
        return self.attributes['ismap'].value

    @ismap.setter
    def ismap(self, v):
        self.attributes['ismap'].value = v

    @property
    def importance(self):
        """ Priority Hints can be set for resources in HTML by
        specifying an importance attribute on a <script>, <img>, or
        <link> element (though other elements such as <iframe> may see
        support later). 
        
        https://developers.google.com/web/updates/2019/02/priority-hints
        """
        return self.attributes['importance'].value

    @importance.setter
    def importance(self, v):
        self.attributes['importance'].value = v

    @property
    def usemap(self):
        """ The partial URL (starting with #) of an image map associated
        with the element.
        """
        return self.attributes['usemap'].value

    @usemap.setter
    def usemap(self, v):
        self.attributes['usemap'].value = v

    @property
    def alt(self):
        """ Defines an alternative text description of the image.
        """
        return self.attributes['alt'].value

    @alt.setter
    def alt(self, v):
        self.attributes['alt'].value = v

    @property
    def sizes(self):
        """ One or more strings separated by commas, indicating a set of
        source sizes.
        """
        return self.attributes['sizes'].value

    @sizes.setter
    def sizes(self, v):
        self.attributes['sizes'].value = v

    @property
    def width(self):
        """ The intrinsic width of the image in pixels. Must be an
        integer without a unit.
        """
        return self.attributes['width'].value

    @width.setter
    def width(self, v):
        self.attributes['width'].value = v

    @property
    def srcset(self):
        """ One or more strings separated by commas, indicating possible
        image sources for the user agent to use.
        """
        return self.attributes['srcset'].value

    @srcset.setter
    def srcset(self, v):
        self.attributes['srcset'].value = v

    @property
    def decoding(self):
        """ Provides an image decoding hint to the browser.
        """
        return self.attributes['decoding'].value

    @decoding.setter
    def decoding(self, v):
        self.attributes['decoding'].value = v

# TODO:dea3866d
images = imgs
image = img

class trs(elements):
    """ A class used to contain a collection of ``trs`` elements.
    """

class tr(element):
    """ The <tr> HTML element defines a row of cells in a table. The
    row's cells can then be established using a mix of <td> (data cell)
    and <th> (header cell) elements.
    """

class objects(elements):
    """ A class used to contain a collection of ``trs`` elements.
    """

class object(element):
    """ The <object> HTML element represents an external resource, which
    can be treated as an image, a nested browsing context, or a resource
    to be handled by a plugin.
    """
    @property
    def data(self):
        """ The address of the resource as a valid URL. At least one of
        data and type must be defined.
        """
        return self.attributes['data'].value

    @data.setter
    def data(self, v):
        self.attributes['data'].value = v

    @property
    def type(self):
        """ The content type of the resource specified by data. At least
        one of data and type must be defined.
        """
        return self.attributes['type'].value

    @type.setter
    def type(self, v):
        self.attributes['type'].value = v

    @property
    def height(self):
        """ The height of the displayed resource, in CSS pixels.
        (Absolute values only. NO percentages)
        """
        return self.attributes['height'].value

    @height.setter
    def height(self, v):
        self.attributes['height'].value = v

    @property
    def form(self):
        """ The form element, if any, that the object element is
        associated with (its form owner). The value of the attribute
        must be an ID of a <form> element in the same document.
        """
        return self.attributes['form'].value

    @form.setter
    def form(self, v):
        self.attributes['form'].value = v

    @property
    def name(self):
        """ The name of valid browsing context.
        """
        return self.attributes['name'].value

    @name.setter
    def name(self, v):
        self.attributes['name'].value = v

    @property
    def usemap(self):
        """ A hash-name reference to a <map> element; that is a '#'
        followed by the value of a name of a map element.
        """
        return self.attributes['usemap'].value

    @usemap.setter
    def usemap(self, v):
        self.attributes['usemap'].value = v

    @property
    def width(self):
        """ The width of the display resource, in CSS pixels.  (Absolute
        values only. NO percentages)
        """
        return self.attributes['width'].value

    @width.setter
    def width(self, v):
        self.attributes['width'].value = v


class cols(elements):
    """ A class used to contain a collection of ``col`` elements.
    """

class col(element):
    """ The <col> HTML element defines a column within a table and is
    used for defining common semantics on all common cells. It is
    generally found within a <colgroup> element.
    """
    @property
    def span(self):
        """ This attribute contains a positive integer indicating the
        number of consecutive columns the <col> element spans. If not
        present, its default value is 1.
        """
        return self.attributes['span'].value

    @span.setter
    def span(self, v):
        self.attributes['span'].value = v

class maps(elements):
    """ A class used to contain a collection of ``map`` elements.
    """

class map(element):
    """ The <map> HTML element is used with <area> elements to define an
    image map (a clickable link area).
    """
    @property
    def name(self):
        """ The name attribute gives the map a name so that it can be
        referenced. The attribute must be present and must have a
        non-empty value with no space characters. The value of the name
        attribute must not be equal to the value of the name attribute
        of another <map> element in the same document. If the id
        attribute is also specified, both attributes must have the same
        value.
        """
        return self.attributes['name'].value

    @name.setter
    def name(self, v):
        self.attributes['name'].value = v

class embeds(elements):
    """ A class used to contain a collection of ``embed`` elements.
    """

class embed(element):
    """ The <embed> HTML element embeds external content at the
    specified point in the document. This content is provided by an
    external application or other source of interactive content such as
    a browser plug-in.
    """
    @property
    def type(self):
        """ The MIME type to use to select the plug-in to instantiate.
        """
        return self.attributes['type'].value

    @type.setter
    def type(self, v):
        self.attributes['type'].value = v

    @property
    def height(self):
        """ The displayed height of the resource, in CSS pixels. This
        must be an absolute value; percentages are not allowed.
        """
        return self.attributes['height'].value

    @height.setter
    def height(self, v):
        self.attributes['height'].value = v

    @property
    def src(self):
        """ The URL of the resource being embedded.
        """
        return self.attributes['src'].value

    @src.setter
    def src(self, v):
        self.attributes['src'].value = v

    @property
    def width(self):
        """ The displayed width of the resource, in CSS pixels. This
        must be an absolute value; percentages are not allowed.
        """
        return self.attributes['width'].value

    @width.setter
    def width(self, v):
        self.attributes['width'].value = v

class meters(elements):
    """ A class used to contain a collection of ``embed`` elements.
    """

class meter(element):
    """ The <meter> HTML element represents either a scalar value within
    a known range or a fractional value.
    """
    @property
    def min(self):
        """ The lower numeric bound of the measured range. This must be
        less than the maximum value (max attribute), if specified.  If
        unspecified, the minimum value is 0.
        """
        return self.attributes['min'].value

    @min.setter
    def min(self, v):
        self.attributes['min'].value = v

    @property
    def optimum(self):
        """ This attribute indicates the optimal numeric value. It must
        be within the range (as defined by the min attribute and max
        attribute). When used with the low attribute and high attribute,
        it gives an indication where along the range is considered
        preferable. For example, if it is between the min attribute and
        the low attribute, then the lower range is considered preferred.
        The browser may color the meter's bar differently depending on
        whether the value is less than or equal to the optimum value.
        """
        return self.attributes['optimum'].value

    @optimum.setter
    def optimum(self, v):
        self.attributes['optimum'].value = v

    @property
    def high(self):
        """ The lower numeric bound of the high end of the measured
        range. This must be less than the maximum value (max attribute),
        and it also must be greater than the low value and minimum value
        (low attribute and min attribute, respectively), if any are
        specified. If unspecified, or if greater than the maximum value,
        the high value is equal to the maximum value.
        """
        return self.attributes['high'].value

    @high.setter
    def high(self, v):
        self.attributes['high'].value = v

    @property
    def form(self):
        """ The <form> element to associate the <meter> element with
        (its form owner). The value of this attribute must be the id of
        a <form> in the same document. If this attribute is not set, the
        <meter> is associated with its ancestor <form> element, if any.
        This attribute is only used if the <meter> element is being used
        as a form-associated element, such as one displaying a range
        corresponding to an <input type="number">.
        """
        return self.attributes['form'].value

    @form.setter
    def form(self, v):
        self.attributes['form'].value = v

    @property
    def max(self):
        """ The upper numeric bound of the measured range. This must be
        greater than the minimum value (min attribute), if specified. If
        unspecified, the maximum value is 1.
        """
        return self.attributes['max'].value

    @max.setter
    def max(self, v):
        self.attributes['max'].value = v

    @property
    def value(self):
        """ The current numeric value. This must be between the minimum
        and maximum values (min attribute and max attribute) if they are
        specified. If unspecified or malformed, the value is 0. If
        specified, but not within the range given by the min attribute
        and max attribute, the value is equal to the nearest end of the
        range.
        """
        return self.attributes['value'].value

    @value.setter
    def value(self, v):
        self.attributes['value'].value = v

    @property
    def low(self):
        """ The upper numeric bound of the low end of the measured
        range. This must be greater than the minimum value (min
        attribute), and it also must be less than the high value and
        maximum value (high attribute and max attribute, respectively),
        if any are specified. If unspecified, or if less than the
        minimum value, the low value is equal to the minimum value.
        """
        return self.attributes['low'].value

    @low.setter
    def low(self, v):
        self.attributes['low'].value = v

class times(elements):
    """ A class used to contain a collection of ``time`` elements.
    """

class time(element):
    """ The <time> HTML element represents a specific period in time. It
    may include the datetime attribute to translate dates into
    machine-readable format, allowing for better search engine results
    or custom features such as reminders.

    It may represent one of the following:

        * A time on a 24-hour clock.

        * A precise date in the Gregorian calendar (with optional time and
        timezone information).

        * A valid time duration.
    """
    def __init__(self, dt=None, *args, **kwargs):
        """ Create a <time> element.

        :param: dt primative.datetime: The datetime object intended to
        be used for the `datetime` attribute.
        """
        super().__init__(*args, *kwargs)

        if dt is None:
            return

        if not isinstance(dt, primative.datetime):
            raise TypeError(
                'Use primative.datettime to ensure timezone '
                'information is provided'
            )

        self.datetime = dt.isoformat()
        self.text = dt.replace(microsecond=0, tzinfo=None).isoformat(' ')

    @property
    def datetime(self):
        """ This attribute indicates the time and/or date of the element
        and must be in one of the formats described below.
        """
        # TODO;fb7d1e8c Ensure this @property only accepts and returns
        # primative.datetime values
        return self.attributes['datetime'].value

    @datetime.setter
    def datetime(self, v):
        self.attributes['datetime'].value = v

class bodies(elements):
    """ A class used to contain a collection of ``body`` elements.
    """

class body(element):
    """ The <body> HTML element represents the content of an HTML
    document. There can be only one <body> element in a document.
    """

class progresses(elements):
    """ A class used to contain a collection of ``progress`` elements.
    """

class progress(element):
    """ The <progress> HTML element displays an indicator showing the
    completion progress of a task, typically displayed as a progress
    bar.
    """

    @property
    def max(self):
        """ This attribute describes how much work the task indicated by
        the progress element requires. The max attribute, if present,
        must have a value greater than 0 and be a valid floating point
        number. The default value is 1.
        """
        return self.attributes['max'].value

    @max.setter
    def max(self, v):
        self.attributes['max'].value = v

    @property
    def value(self):
        """ This attribute specifies how much of the task that has been
        completed. It must be a valid floating point number between 0
        and max, or between 0 and 1 if max is omitted. If there is no
        value attribute, the progress bar is indeterminate; this
        indicates that an activity is ongoing with no indication of how
        long it is expected to take.
        """
        return self.attributes['value'].value

    @value.setter
    def value(self, v):
        self.attributes['value'].value = v

class commands(elements):
    """ A class used to contain a collection of ``command`` elements.
    """

class command(element):
    """ The command element represents a command that the user can
    invoke.  A command can be part of a context menu or toolbar, using
    the menu element, or can be put anywhere else in the page, to define
    a keyboard shortcut.
    """

    # NOTE This is sort of an oddball. It appears to only be supported
    # by IE, although it is part of the HTML5 standard.
    @property
    def radiogroup(self):
        """ The radiogroup attribute gives the name of the group of
        commands that will be toggled when the command itself is
        toggled, for commands whose type attribute has the value
        "radio". The scope of the name is the child list of the parent
        element. The attribute must be omitted unless the type attribute
        is in the Radio state.
        """
        return self.attributes['radiogroup'].value

    @radiogroup.setter
    def radiogroup(self, v):
        self.attributes['radiogroup'].value = v

    @property
    def icon(self):
        """ The icon attribute gives a picture that represents the
        command. If the attribute is specified, the attribute's value
        must contain a valid non-empty URL potentially surrounded by
        spaces.
        """
        return self.attributes['icon'].value

    @icon.setter
    def icon(self, v):
        self.attributes['icon'].value = v

    @property
    def type(self):
        """ The type IDL attribute must reflect the content attribute of
        the same name, limited to only known values.
        """
        return self.attributes['type'].value

    @type.setter
    def type(self, v):
        self.attributes['type'].value = v

    @property
    def checked(self):
        """ The checked attribute is a boolean attribute that, if
        present, indicates that the command is selected. The attribute
        must be omitted unless the type attribute is in either the
        Checkbox state or the Radio state.
        """
        # TODO:369795a1
        return self.attributes['checked'].value

    @checked.setter
    def checked(self, v):
        self.attributes['checked'].value = v

    @property
    def disabled(self):
        return self.attributes['disabled'].value

    @disabled.setter
    def disabled(self, v):
        self.attributes['disabled'].value = v

class blockquotes(elements):
    """ A class used to contain a collection of ``blockquote`` elements.
    """

class blockquote(element):
    """ The <blockquote> HTML element indicates that the enclosed text
    is an extended quotation. Usually, this is rendered visually by
    indentation. A URL for the source of the quotation may be given
    using the cite attribute, while a text representation of the source
    can be given using the <cite> element.
    """
    @property
    def cite(self):
        """ A URL that designates a source document or message for the
        information quoted. This attribute is intended to point to
        information explaining the context or the reference for the
        quote.
        """
        return self.attributes['cite'].value

    @cite.setter
    def cite(self, v):
        self.attributes['cite'].value = v

class options(elements):
    """ A class used to contain a collection of ``option`` elements.
    """

class option(element):
    """ The <option> HTML element is used to define an item contained in
    a <select>, an <optgroup>, or a <datalist> element. As such,
    <option> can represent menu items in popups and other lists of items
    in an HTML document.
    """
    @property
    def label(self):
        """ This attribute is text for the label indicating the meaning
        of the option. If the label attribute isn't defined, its value
        is that of the element text content.
        """
        return self.attributes['label'].value

    @label.setter
    def label(self, v):
        self.attributes['label'].value = v

    @property
    def disabled(self):
        """ If this Boolean attribute is set, this option is not
        checkable. Often browsers grey out such control and it won't
        receive any browsing event, like mouse clicks or focus-related
        ones. If this attribute is not set, the element can still be
        disabled if one of its ancestors is a disabled <optgroup>
        element.
        """
        # TODO:369795a1
        return self.attributes['disabled'].value

    @disabled.setter
    def disabled(self, v):
        self.attributes['disabled'].value = v

    @property
    def selected(self):
        """ If present, this Boolean attribute indicates that the option
        is initially selected. If the <option> element is the descendant
        of a <select> element whose multiple attribute is not set, only
        one single <option> of this <select> element may have the
        selected attribute.
        """
        # TODO:369795a1
        return self.attributes['selected'].value

    @selected.setter
    def selected(self, v):
        if v:
            self.attributes['selected'].value = None
        else:
            del self.attributes['selected']

    @property
    def value(self):
        """ The content of this attribute represents the value to be
        submitted with the form, should this option be selected. If this
        attribute is omitted, the value is taken from the text content
        of the option element.
        """
        return self.attributes['value'].value

    @value.setter
    def value(self, v):
        self.attributes['value'].value = v

class canvass(elements):
    """ A class used to contain a collection of ``canvas`` elements.
    """

class canvas(element):
    """ Use the HTML <canvas> element with either the canvas scripting
    API or the WebGL API to draw graphics and animations.
    """
    @property
    def height(self):
        """ The height of the coordinate space in CSS pixels. Defaults
        to 150.
        """
        return self.attributes['height'].value

    @height.setter
    def height(self, v):
        self.attributes['height'].value = v

    @property
    def width(self):
        """ The width of the coordinate space in CSS pixels. Defaults to
        300.
        """
        return self.attributes['width'].value

    @width.setter
    def width(self, v):
        self.attributes['width'].value = v

class uls(elements):
    """ A class used to contain a collection of ``ul`` elements.
    """

class ul(element):
    """ The <ul> HTML element represents an unordered list of items,
    typically rendered as a bulleted list.
    """

# TODO:dea3866d
unorderedlists = uls
unorderedlist = ul

class ols(elements):
    """ A class used to contain a collection of ``ol`` elements.
    """

class ol(element):
    """ The <ol> HTML element represents an ordered list of items —
    typically rendered as a numbered list.
    """
    @property
    def reversed(self):
        """ This Boolean attribute specifies that the list’s items are
        in reverse order. Items will be numbered from high to low.
        """
        # TODO:369795a1
        return self.attributes['reversed'].value

    @reversed.setter
    def reversed(self, v):
        self.attributes['reversed'].value = v

    @property
    def start(self):
        """ An integer to start counting from for the list items. Always
        an Arabic numeral (1, 2, 3, etc.), even when the numbering type
        is letters or Roman numerals. For example, to start numbering
        elements from the letter "d" or the Roman numeral "iv," use
        start="4".
        """
        return self.attributes['start'].value

    @start.setter
    def start(self, v):
        self.attributes['start'].value = v

    @property
    def type(self):
        """ Sets the numbering type:

              * a for lowercase letters
              * A for uppercase letters
              * i for lowercase Roman numerals
              * I for uppercase Roman numerals
              * 1 for numbers (default)

           The specified type is used for the entire list unless a
           different type attribute is used on an enclosed <li> element.

           Note: Unless the type of the list number matters (like legal
           or technical documents where items are referenced by their
           number/letter), use the CSS list-style-type property instead.
        """
        return self.attributes['type'].value

    @type.setter
    def type(self, v):
        self.attributes['type'].value = v

class tracks(elements):
    """ A class used to contain a collection of ``track`` elements.
    """

class track(element):
    """ The <track> HTML element is used as a child of the media
    elements, <audio> and <video>. It lets you specify timed text tracks
    (or time-based data), for example to automatically handle subtitles.
    The tracks are formatted in WebVTT format (.vtt files) — Web Video
    Text Tracks.
    """
    @property
    def default(self):
        """ This attribute indicates that the track should be enabled
        unless the user's preferences indicate that another track is
        more appropriate. This may only be used on one track element per
        media element.
        """
        return self.attributes['default'].value

    @default.setter
    def default(self, v):
        self.attributes['default'].value = v

    @property
    def label(self):
        return self.attributes['label'].value

    @label.setter
    def label(self, v):
        """ A user-readable title of the text track which is used by the
        browser when listing available text tracks.
        """
        self.attributes['label'].value = v

    @property
    def src(self):
        """ Address of the track (.vtt file). Must be a valid URL. This
        attribute must be specified and its URL value must have the same
        origin as the document — unless the <audio> or <video> parent
        element of the track element has a crossorigin attribute.
        """
        return self.attributes['src'].value

    @src.setter
    def src(self, v):
        self.attributes['src'].value = v

    @property
    def srclang(self):
        """ Language of the track text data. It must be a valid BCP 47
        language tag. If the kind attribute is set to subtitles, then
        srclang must be defined.
        """
        return self.attributes['srclang'].value

    @srclang.setter
    def srclang(self, v):
        self.attributes['srclang'].value = v

    @property
    def kind(self):
        """ How the text track is meant to be used. If omitted the
        default kind is subtitles. 
        """
        return self.attributes['kind'].value

    @kind.setter
    def kind(self, v):
        self.attributes['kind'].value = v

class dels(elements):
    """ A class used to contain a collection of ``del`` elements.
    """

class del_(element):
    """ The <del> HTML element represents a range of text that has been
    deleted from a document. This can be used when rendering "track
    changes" or source code diff information, for example. The <ins>
    element can be used for the opposite purpose: to indicate text that
    has been added to the document.
    """
    @property
    def datetime(self):
        """ This attribute indicates the time and date of the change and
        must be a valid date string with an optional time. If the value
        cannot be parsed as a date with an optional time string, the
        element does not have an associated time stamp. For the format
        of the string without a time, see Date strings. The format of
        the string if it includes both date and time is covered in Local
        date and time strings.
        """
        # TODO;fb7d1e8c Ensure this @property only accepts and returns
        # primative.datetime values
        return self.attributes['datetime'].value

    @datetime.setter
    def datetime(self, v):
        self.attributes['datetime'].value = v

    @property
    def cite(self):
        """ A URI for a resource that explains the change (for example,
        meeting minutes).
        """
        return self.attributes['cite'].value

    @cite.setter
    def cite(self, v):
        self.attributes['cite'].value = v

class tbodys(elements):
    """ A class used to contain a collection of ``tbody`` elements.
    """

class tbody(element):
    """ The <tbody> HTML element encapsulates a set of table rows (<tr>
    elements), indicating that they comprise the body of the table
    (<table>).
    """

class inss(elements):
    """ A class used to contain a collection of ``ins`` elements.
    """

class ins(element):
    """ The <ins> HTML element represents a range of text that has been
    added to a document. You can use the <del> element to similarly
    represent a range of text that has been deleted from the document.
    """
    @property
    def datetime(self):
        """ This attribute indicates the time and date of the change and
        must be a valid date with an optional time string. If the value
        cannot be parsed as a date with an optional time string, the
        element does not have an associated time stamp. For the format
        of the string without a time, see Format of a valid date string.
        The format of the string if it includes both date and time is
        covered in Format of a valid local date and time string.
        """
        # TODO;fb7d1e8c Ensure this @property only accepts and returns
        # primative.datetime values
        return self.attributes['datetime'].value

    @datetime.setter
    def datetime(self, v):
        self.attributes['datetime'].value = v

    @property
    def cite(self):
        """ This attribute defines the URI of a resource that explains
        the change, such as a link to meeting minutes or a ticket in a
        troubleshooting system.
        """
        return self.attributes['cite'].value

    @cite.setter
    def cite(self, v):
        self.attributes['cite'].value = v

class textareas(elements):
    """ A class used to contain a collection of ``textarea`` elements.
    """

class textarea(element):
    """ The <textarea> HTML element represents a multi-line plain-text
    editing control, useful when you want to allow users to enter a
    sizeable amount of free-form text, for example a comment on a review
    or feedback form.
    """

    @property
    def readonly(self):
        """ This Boolean attribute indicates that the user cannot modify
        the value of the control. Unlike the disabled attribute, the
        readonly attribute does not prevent the user from clicking or
        selecting in the control. The value of a read-only control is
        still submitted with the form.
        """
        # TODO:369795a1
        return self.attributes['readonly'].value

    @readonly.setter
    def readonly(self, v):
        self.attributes['readonly'].value = v

    @property
    def dirname(self):
        return self.attributes['dirname'].value

    @dirname.setter
    def dirname(self, v):
        self.attributes['dirname'].value = v

    @property
    def cols(self):
        """ The visible width of the text control, in average character
        widths. If it is specified, it must be a positive integer. If it
        is not specified, the default value is 20.
        """
        return self.attributes['cols'].value

    @cols.setter
    def cols(self, v):
        self.attributes['cols'].value = v

    @property
    def required(self):
        """ This attribute specifies that the user must fill in a value
        before submitting a form.
        """
        return self.attributes['required'].value

    @required.setter
    def required(self, v):
        self.attributes['required'].value = v

    @property
    def spellcheck(self):
        """ Specifies whether the <textarea> is subject to spell
        checking by the underlying browser/OS. The value can be:

            true: Indicates that the element needs to have its spelling
            and grammar checked.

            default: Indicates that the element is to act according to
            a default behavior, possibly based on the parent element's
            own spellcheck value.

            false: Indicates that the element should not be spell
            checked.
        """
        return self.attributes['spellcheck'].value

    @spellcheck.setter
    def spellcheck(self, v):
        self.attributes['spellcheck'].value = v

    @property
    def rows(self):
        """ The number of visible text lines for the control.
        """
        return self.attributes['rows'].value

    @rows.setter
    def rows(self, v):
        self.attributes['rows'].value = v

    @property
    def autofocus(self):
        """ This Boolean attribute lets you specify that a form control
        should have input focus when the page loads. Only one
        form-associated element in a document can have this attribute
        specified.
        """
        # TODO:369795a1
        return self.attributes['autofocus'].value

    @autofocus.setter
    def autofocus(self, v):
        self.attributes['autofocus'].value = v

    @property
    def enterkeyhint(self):
        return self.attributes['enterkeyhint'].value

    @enterkeyhint.setter
    def enterkeyhint(self, v):
        self.attributes['enterkeyhint'].value = v

    @property
    def form(self):
        """ The form element that the <textarea> element is associated
        with (its "form owner"). The value of the attribute must be the
        id of a form element in the same document. If this attribute is
        not specified, the <textarea> element must be a descendant of a
        form element. This attribute enables you to place <textarea>
        elements anywhere within a document, not just as descendants of
        form elements.
        """
        return self.attributes['form'].value

    @form.setter
    def form(self, v):
        self.attributes['form'].value = v

    @property
    def placeholder(self):
        """ A hint to the user of what can be entered in the control.
        Carriage returns or line-feeds within the placeholder text must
        be treated as line breaks when rendering the hint.

        Note: Placeholders should only be used to show an example of the
        type of data that should be entered into a form; they are not a
        substitute for a proper <label> element tied to the input.
        """
        return self.attributes['placeholder'].value

    @placeholder.setter
    def placeholder(self, v):
        self.attributes['placeholder'].value = v

    @property
    def minlength(self):
        return self.attributes['minlength'].value

    @minlength.setter
    def minlength(self, v):
        self.attributes['minlength'].value = v

    @property
    def name(self):
        """ The name of the control.
        """
        return self.attributes['name'].value

    @name.setter
    def name(self, v):
        self.attributes['name'].value = v

    @property
    def maxlength(self):
        """ The maximum number of characters (UTF-16 code units) that
        the user can enter. If this value isn't specified, the user can
        enter an unlimited number of characters.
        """
        return self.attributes['maxlength'].value

    @maxlength.setter
    def maxlength(self, v):
        """ The minimum number of characters (UTF-16 code units)
        required that the user should enter.
        """
        self.attributes['maxlength'].value = v

    @property
    def disabled(self):
        """ This Boolean attribute indicates that the user cannot
        interact with the control. If this attribute is not specified,
        the control inherits its setting from the containing element,
        for example <fieldset>; if there is no containing element when
        the disabled attribute is set, the control is enabled.
        """
        # TODO:369795a1
        return self.attributes['disabled'].value

    @disabled.setter
    def disabled(self, v):
        self.attributes['disabled'].value = v

    @property
    def wrap(self):
        """ Indicates how the control wraps text. Possible values are:
        hard: The browser automatically inserts line breaks
        (CR+LF) so that each line has no more than the width of
        the control; the cols attribute must also be specified for
        this to take effect.

        soft: The browser ensures that all line breaks in the
        value consist of a CR+LF pair, but does not insert any
        additional line breaks.

        off: Like soft but changes appearance to white-space: pre
        so line segments exceeding cols are not wrapped and the
        <textarea> becomes horizontally scrollable.

        If this attribute is not specified, soft is its default value.
        """
        return self.attributes['wrap'].value

    @wrap.setter
    def wrap(self, v):
        self.attributes['wrap'].value = v

    @property
    def autocomplete(self):
        """ This attribute indicates whether the value of the control
        can be automatically completed by the browser. Possible values
        are:

              * off: The user must explicitly enter a value into this field for
              every use, or the document provides its own
              auto-completion method; the browser does not automatically
              complete the entry.

              * on: The browser can automatically complete the value based on
              values that the user has entered during previous uses.

        If the autocomplete attribute is not specified on a
        <textarea> element, then the browser uses the autocomplete
        attribute value of the <textarea> element's form owner. The
        form owner is either the <form> element that this <textarea>
        element is a descendant of or the form element whose id is
        specified by the form attribute of the input element. For
        more information, see the autocomplete attribute in <form>.
        """

        # TODO Convert this property to a boolean one, such that it only
        # accepts and returns only True or False. The actual value for
        # the attribute would still be 'off' and 'on'.
        return self.attributes['autocomplete'].value

    @autocomplete.setter
    def autocomplete(self, v):
        self.attributes['autocomplete'].value = v

    @property
    def inputmode(self):
        """ Global value valid for all elements, it provides a hint to
        browsers as to the type of virtual keyboard configuration to use
        when editing this element or its contents. Values include none,
        text, tel, url, email, numeric, decimal, and search.
        """
        return self.attributes['inputmode'].value

    @inputmode.setter
    def inputmode(self, v):
        self.attributes['inputmode'].value = v

    @property
    def autocorrect(self):
        """ This attribute indicates whether the value of the control
        can be automatically completed by the browser. Possible values
        are:

            * off: The user must explicitly enter a value into this field for
            every use, or the document provides its own auto-completion
            method; the browser does not automatically complete the
            entry.

            * on: The browser can automatically complete the value based on
            values that the user has entered during previous uses.

        If the autocomplete attribute is not specified on a <textarea>
        element, then the browser uses the autocomplete attribute value
        of the <textarea> element's form owner. The form owner is either
        the <form> element that this <textarea> element is a descendant
        of or the form element whose id is specified by the form
        attribute of the input element. For more information, see the
        autocomplete attribute in <form>.
		"""
        # TODO:369795a1
        return self.attributes['autocorrect'].value

    @autocorrect.setter
    def autocorrect(self, v):
        self.attributes['autocorrect'].value = v

class captions(elements):
    """ A class used to contain a collection of ``caption`` elements.
    """

class caption(element):
    """ The <caption> HTML element specifies the caption (or title) of a
    table.
    """

class inputs(elements):
    """ A class used to contain a collection of ``input`` elements.
    """

class input(element):
    """ The <input> HTML element is used to create interactive controls
    for web-based forms in order to accept data from the user; a wide
    variety of types of input data and control widgets are available,
    depending on the device and user agent. The <input> element is one
    of the most powerful and complex in all of HTML due to the sheer
    number of combinations of input types and attributes.
    """
    isvoid = True

    @property
    def min(self):
        """ Valid for date, month, week, time, datetime-local, number,
        and range, it defines the most negative value in the range of
        permitted values. If the value entered into the element is less
        than this this, the element fails constraint validation. If the
        value of the min attribute isn't a number, then the element has
        no minimum value.

        This value must be less than or equal to the value of the max
        attribute. If the min attribute is present but is not specified
        or is invalid, no min value is applied. If the min attribute is
        valid and a non-empty value is less than the minimum allowed by
        the min attribute, constraint validation will prevent form
        submission. See Client-side validation for more information.

        There is a special case: if the data type is periodic (such as
        for dates or times), the value of max may be lower than the
        value of min, which indicates that the range may wrap around;
        for example, this allows you to specify a time range from 10 PM
        to 4 AM.
        """
        return self.attributes['min'].value

    @min.setter
    def min(self, v):
        self.attributes['min'].value = v

    @property
    def readonly(self):
        """ A Boolean attribute which, if present, indicates that the
        user should not be able to edit the value of the input.  The
        readonly attribute is supported by the text, search, url, tel,
        email, date, month, week, time, datetime-local, number, and
        password input types.
        """

        return self.attributes['readonly'].value

    @readonly.setter
    def readonly(self, v):
        self.attributes['readonly'].value = v

    @property
    def formtarget(self):
        """ Browsing context for form submission. Valid for the image
        and submit input types only.
        """
        return self.attributes['formtarget'].value

    @formtarget.setter
    def formtarget(self, v):
        self.attributes['formtarget'].value = v

    @property
    def dirname(self):
        """ Valid for text and search input types only, the dirname
        attribute enables the submission of the directionality of the
        element. When included, the form control will submit with two
        name/value pairs: the first being the name and value, the second
        being the value of the dirname as the name with the value of ltr
        or rtl being set by the browser.

            <form action="page.html" method="post">
                <label>
                    Fruit: 
                    <input type="text" name="fruit" dirname="fruit.dir" value="cherry">
                </label>
                <input type="submit"/>
            </form>
            <!-- page.html?fruit=cherry&fruit.dir=ltr -->

        When the form above is submitted, the input cause both the
        name/value pair of fruit=cherry and the dirname / direction pair
        of fruit.dir=ltr to be sent.
        """
        return self.attributes['dirname'].value

    @dirname.setter
    def dirname(self, v):
        self.attributes['dirname'].value = v

    @property
    def required(self):
        """ required is a Boolean attribute which, if present, indicates
        that the user must specify a value for the input before the
        owning form can be submitted. The required attribute is
        supported by text, search, url, tel, email, date, month, week,
        time, datetime-local, number, password, checkbox, radio, and
        file inputs.
        """
        return self.attributes['required'].value

    @required.setter
    def required(self, v):
        self.attributes['required'].value = v

    @property
    def formaction(self):
        """ URL to use for form submission  Valid for the image and
        submit input types only.
        """
        return self.attributes['formaction'].value

    @formaction.setter
    def formaction(self, v):
        self.attributes['formaction'].value = v

    @property
    def multiple(self):
        """ The Boolean multiple attribute, if set, means the user can
        enter comma separated email addresses in the email widget or can
        choose more than one file with the file input. See the email and
        file input type.
        """
        return self.attributes['multiple'].value

    @multiple.setter
    def multiple(self, v):
        self.attributes['multiple'].value = v

    @property
    def capture(self):
        """ Introduced in the HTML Media Capture specification and valid
        for the file input type only, the capture attribute defines
        which media—microphone, video, or camera—should be used to
        capture a new file for upload with file upload control in
        supporting scenarios. See the file input type.
        """
        return self.attributes['capture'].value

    @capture.setter
    def capture(self, v):
        self.attributes['capture'].value = v

    @property
    def autofocus(self):
        """ A Boolean attribute which, if present, indicates that the
        input should automatically have focus when the page has finished
        loading (or when the <dialog> containing the element has been
        displayed).

        Note: An element with the autofocus attribute may gain focus
        before the DOMContentLoaded event is fired.

        No more than one element in the document may have the autofocus
        attribute. If put on more than one element, the first one with
        the attribute receives focus.

        The autofocus attribute cannot be used on inputs of type hidden,
        since hidden inputs cannot be focused.

        Warning: Automatically focusing a form control can confuse
        visually-impaired people using screen-reading technology and
        people with cognitive impairments. When autofocus is assigned,
        screen-readers "teleport" their user to the form control without
        warning them beforehand.

        Use careful consideration for accessibility when applying the
        autofocus attribute. Automatically focusing on a control can
        cause the page to scroll on load. The focus can also cause
        dynamic keyboards to display on some touch devices. While a
        screen reader will announce the label of the form control
        receiving focus, the screen reader will not announce anything
        before the label, and the sighted user on a small device will
        equally miss the context created by the preceding content.
        """
        return self.attributes['autofocus'].value

    @autofocus.setter
    def autofocus(self, v):
        self.attributes['autofocus'].value = v

    @property
    def type(self):
        """ How an <input> works varies considerably depending on the value
        of its type attribute, hence the different types are covered in
        their own separate reference pages. If this attribute is not
        specified, the default type adopted is text.

        The available types are as follows: button, checkbox, color, date,
        datetime-local, email, file, hidden, image, month, number, password,
        radio, range, reset, search, submit, tel, text, time, url, week, 
        """
        return self.attributes['type'].value

    @type.setter
    def type(self, v):
        self.attributes['type'].value = v

    @property
    def step(self):
        """ Valid for the numeric input types, including number,
        date/time input types, and range, the step attribute is a number
        that specifies the granularity that the value must adhere to.
        """
        return self.attributes['step'].value

    @step.setter
    def step(self, v):
        self.attributes['step'].value = v

    @property
    def height(self):
        """ Valid for the image input button only, the height is the
        height of the image file to display to represent the graphical
        submit button. See the image input type.
        """
        return self.attributes['height'].value

    @height.setter
    def height(self, v):
        self.attributes['height'].value = v

    @property
    def src(self):
        """ Valid for the image input button only, the src is string
        specifying the URL of the image file to display to represent the
        graphical submit button. See the image input type.
        """
        return self.attributes['src'].value

    @src.setter
    def src(self, v):
        self.attributes['src'].value = v

    @property
    def accept(self):
        """ Valid for the file input type only, the accept attribute
        defines which file types are selectable in a file upload
        control. See the file input type.
        """
        return self.attributes['accept'].value

    @accept.setter
    def accept(self, v):
        self.attributes['accept'].value = v

    @property
    def size(self):
        """ Valid for email, password, tel, url and text input types
        only. Specifies how much of the input is shown. Basically
        creates same result as setting CSS width property with a few
        specialities. The actual unit of the value depends on the input
        type. For password and text, it is a number of characters (or em
        units) with a default value of 20, and for others, it is pixels.
        CSS width takes precedence over size attribute.
        """
        return self.attributes['size'].value

    @size.setter
    def size(self, v):
        self.attributes['size'].value = v

    @property
    def pattern(self):
        """ The pattern attribute, when specified, is a regular
        expression that the input's value must match in order for the
        value to pass constraint validation. It must be a valid
        JavaScript regular expression, as used by the RegExp type, and
        as documented in our guide on regular expressions; the 'u' flag
        is specified when compiling the regular expression, so that the
        pattern is treated as a sequence of Unicode code points, instead
        of as ASCII. No forward slashes should be specified around the
        pattern text.

        If the pattern attribute is present but is not specified or is
        invalid, no regular expression is applied and this attribute is
        ignored completely. If the pattern attribute is valid and a
        non-empty value does not match the pattern, constraint
        validation will prevent form submission.

        Note: If using the pattern attribute, inform the user about the
        expected format by including explanatory text nearby. You can
        also include a title attribute to explain what the requirements
        are to match the pattern; most browsers will display this title
        as a tooltip. The visible explanation is required for
        accessibility. The tooltip is an enhancement.
		"""
        return self.attributes['pattern'].value

    @pattern.setter
    def pattern(self, v):
        self.attributes['pattern'].value = v

    @property
    def formnovalidate(self):
        """ Bypass form control validation for form submission. Valid
        for the image and submit input types only.
        """
        return self.attributes['formnovalidate'].value

    @formnovalidate.setter
    def formnovalidate(self, v):
        self.attributes['formnovalidate'].value = v

    @property
    def form(self):
        """ A string specifying the <form> element with which the input
        is associated (that is, its form owner). This string's value, if
        present, must match the id of a <form> element in the same
        document. If this attribute isn't specified, the <input> element
        is associated with the nearest containing form, if any.

        The form attribute lets you place an input anywhere in the
        document but have it included with a form elsewhere in the
        document.

        Note: An input can only be associated with one form.
        """
        return self.attributes['form'].value

    @form.setter
    def form(self, v):
        self.attributes['form'].value = v

    @property
    def checked(self):
        """ Valid for both radio and checkbox types, checked is
        a Boolean attribute. If present on a radio type, it indicates
        that the radio button is the currently selected one in the group
        of same-named radio buttons. If present on a checkbox type, it
        indicates that the checkbox is checked by default (when the page
        loads). It does not indicate whether this checkbox is currently
        checked: if the checkbox’s state is changed, this content
        attribute does not reflect the change. (Only the
        HTMLInputElement’s checked IDL attribute is updated.)

        Note: Unlike other input controls, a checkboxes and radio
        buttons value are only included in the submitted data if they
        are currently checked. If they are, the name and the value(s) of
        the checked controls are submitted.

        For example, if a checkbox whose name is fruit has a value of
        cherry, and the checkbox is checked, the form data submitted
        will include fruit=cherry. If the checkbox isn't active, it
        isn't listed in the form data at all. The default value for
        checkboxes and radio buttons is on.
        """
        return self.attributes['checked'].value

    @checked.setter
    def checked(self, v):
        self.attributes['checked'].value = v

    @property
    def placeholder(self):
        return self.attributes['placeholder'].value

    @placeholder.setter
    def placeholder(self, v):
        self.attributes['placeholder'].value = v

    @property
    def minlength(self):
        """ Valid for text, search, url, tel, email, and password, it
        defines the minimum number of characters (as UTF-16 code units)
        the user can enter into the entry field. This must be an
        non-negative integer value smaller than or equal to the value
        specified by maxlength. If no minlength is specified, or an
        invalid value is specified, the input has no minimum length.

        The input will fail constraint validation if the length of the
        text entered into the field is fewer than minlength UTF-16 code
        units long, preventing form submission.  See Client-side
        validation for more information.
        """
        return self.attributes['minlength'].value

    @minlength.setter
    def minlength(self, v):
        self.attributes['minlength'].value = v

    @property
    def list(self):
        """ The value given to the list attribute should be the id of a
        <datalist> element located in the same document. The <datalist>
        provides a list of predefined values to suggest to the user for
        this input. Any values in the list that are not compatible with
        the type are not included in the suggested options. The values
        provided are suggestions, not requirements: users can select
        from this predefined list or provide a different value.

        It is valid on text, search, url, tel, email, date, month, week,
        time, datetime-local, number, range, and color.

        Per the specifications, the list attribute is not supported by
        the hidden, password, checkbox, radio, file, or any of the
        button types.

        Depending on the browser, the user may see a custom color
        palette suggested, tic marks along a range, or even a input that
        opens like a <select> but allows for non-listed values.  Check
        out the browser compatibility table for the other input types.

        See the <datalist> element.
        """
        return self.attributes['list'].value

    @list.setter
    def list(self, v):
        self.attributes['list'].value = v

    @property
    def max(self):
        """ Valid for date, month, week, time, datetime-local, number,
        and range, it defines the greatest value in the range of
        permitted values. If the value entered into the element exceeds
        this, the element fails constraint validation. If the value of
        the max attribute isn't a number, then the element has no
        maximum value.

        There is a special case: if the data type is periodic (such as
        for dates or times), the value of max may be lower than the
        value of min, which indicates that the range may wrap around;
        for example, this allows you to specify a time range from 10 PM
        to 4 AM.
        """
        return self.attributes['max'].value

    @max.setter
    def max(self, v):
        self.attributes['max'].value = v

    @property
    def name(self):
        """ A string specifying a name for the input control. This name
        is submitted along with the control's value when the form data
        is submitted.

        Consider the name a required attribute (even though it's not).
        If an input has no name specified, or name is empty, the input's
        value is not submitted with the form! (Disabled controls,
        unchecked radio buttons, unchecked checkboxes, and reset buttons
        are also not sent.)

        There are two special cases:

        1. _charset_ : If used as the name of an <input> element of type
        hidden, the input's value is automatically set by the user agent
        to the character encoding being used to submit the form.  2.
        isindex: For historical reasons, the name isindex is not
        allowed.

        The name attribute creates a unique behavior for radio buttons.

        Only one radio button in a same-named group of radio buttons can
        be checked at a time. Selecting any radio button in that group
        automatically deselects any currently-selected radio button in
        the same group. The value of that one checked radio button is
        sent along with the name if the form is submitted,

        When tabbing into a series of same-named group of radio buttons,
        if one is checked, that one will receive focus. If they aren't
        grouped together in source order, if one of the group is
        checked, tabbing into the group starts when the first one in the
        group is encountered, skipping all those that aren't checked. In
        other words, if one is checked, tabbing skips the unchecked
        radio buttons in the group. If none are checked, the radio
        button group receives focus when the first button in the same
        name group is reached.

        Once one of the radio buttons in a group has focus, using the
        arrow keys will navigate through all the radio buttons of the
        same name, even if the radio buttons are not grouped together in
        the source order.

        When an input element is given a name, that name becomes a
        property of the owning form element's HTMLFormElement.elements
        property. If you have an input whose name is set to guest and
        another whose name is hat-size, the following code can be used:

            let form = document.querySelector("form");

            let guestName = form.elements.guest; let hatSize =
            form.elements["hat-size"];

        When this code has run, guestName will be the HTMLInputElement
        for the guest field, and hatSize the object for the hat-size
        field.

        Warning: Avoid giving form elements a name that corresponds to a
        built-in property of the form, since you would then override the
        predefined property or method with this reference to the
        corresponding input.
        """
        return self.attributes['name'].value

    @name.setter
    def name(self, v):
        self.attributes['name'].value = v

    @property
    def maxlength(self):
        """ Valid for text, search, url, tel, email, and password, it
        defines the maximum number of characters (as UTF-16 code units)
        the user can enter into the field. This must be an integer value
        0 or higher. If no maxlength is specified, or an invalid value
        is specified, the field has no maximum length. This value must
        also be greater than or equal to the value of minlength.

        The input will fail constraint validation if the length of the
        text entered into the field is greater than maxlength UTF-16
        code units long. By default, browsers prevent users from
        entering more characters than allowed by the maxlength
        attribute. See Client-side validation for more information.
        """
        return self.attributes['maxlength'].value

    @maxlength.setter
    def maxlength(self, v):
        self.attributes['maxlength'].value = v

    @property
    def usemap(self):
        """ The usemap attribute specifies an image as a client-side
        image map (an image map is an image with clickable areas).
        """
        return self.attributes['usemap'].value

    @usemap.setter
    def usemap(self, v):
        self.attributes['usemap'].value = v

    @property
    def formenctype(self):
        """ Form data set encoding type to use for form submission. Only
        valid for image and submit input types.
        """
        return self.attributes['formenctype'].value

    @formenctype.setter
    def formenctype(self, v):
        self.attributes['formenctype'].value = v

    @property
    def disabled(self):
        """ A Boolean attribute which, if present, indicates that the
        user should not be able to interact with the input. Disabled
        inputs are typically rendered with a dimmer color or using some
        other form of indication that the field is not available for
        use.

        Specifically, disabled inputs do not receive the click event,
        and disabled inputs are not submitted with the form.

        Note: Although not required by the specification, Firefox will
        by default persist the dynamic disabled state of an <input>
        across page loads. Use the autocomplete attribute to control
        this feature.
        """
        return self.attributes['disabled'].value

    @disabled.setter
    def disabled(self, v):
        self.attributes['disabled'].value = v

    @property
    def alt(self):
        """ Valid for the image button only, the alt attribute provides
        alternative text for the image, displaying the value of the
        attribute if the image scr is missing or otherwise fails to
        load.
        """
        return self.attributes['alt'].value

    @alt.setter
    def alt(self, v):
        self.attributes['alt'].value = v

    @property
    def width(self):
        """ Valid for the image input button only, the width is the
        width of the image file to display to represent the graphical
        submit button.
        """
        return self.attributes['width'].value

    @width.setter
    def width(self, v):
        self.attributes['width'].value = v

    @property
    def autocomplete(self):
        """ (Not a Boolean attribute!) The autocomplete attribute takes
        as its value a space-separated string that describes what, if
        any, type of autocomplete functionality the input should
        provide. A typical implementation of autocomplete recalls
        previous values entered in the same input field, but more
        complex forms of autocomplete can exist. For instance, a browser
        could integrate with a device's contacts list to autocomplete
        email addresses in an email input field.

        The autocomplete attribute is valid on hidden, text, search,
        url, tel, email, date, month, week, time, datetime-local,
        number, range, color, and password. This attribute has no effect
        on input types that do not return numeric or text data, being
        valid for all input types except checkbox, radio, file, or any
        of the button types.
        """
        return self.attributes['autocomplete'].value

    @autocomplete.setter
    def autocomplete(self, v):
        self.attributes['autocomplete'].value = v

    @property
    def value(self):
        """ The input control's value. When specified in the HTML, this
        is the initial value, and from then on it can be altered or
        retrieved at any time using JavaScript to access the respective
        HTMLInputElement object's value property. The value attribute is
        always optional, though should be considered mandatory for
        checkbox, radio, and hidden.
        """
        return self.attributes['value'].value

    @value.setter
    def value(self, v):
        self.attributes['value'].value = v

    @property
    def formmethod(self):
        """ HTTP method to use for form submission. Valid for the image
        and submit input types only.
        """
        return self.attributes['formmethod'].value

    @formmethod.setter
    def formmethod(self, v):
        self.attributes['formmethod'].value = v

class ths(elements):
    """ A class used to contain a collection of ``th`` elements.  """

class th(element):
    """ The <th> HTML element defines a cell as header of a group of
    table cells. The exact nature of this group is defined by the scope
    and headers attributes.
    """
    @property
    def scope(self):
        """ This enumerated attribute defines the cells that the header
        (defined in the <th>) element relates to. It may have the
        following values:

              * row: The header relates to all cells of the row it belongs
              to.

              * col: The header relates to all cells of the column it
              belongs to.

              * rowgroup: The header belongs to a rowgroup and relates to
              all of its cells. These cells can be placed to the right
              or the left of the header, depending on the value of the
              dir attribute in the <table> element.

              * colgroup: The header belongs to a colgroup and relates to
              all of its cells.

        If the scope attribute is not specified, or its value is not
        row, col, or rowgroup, or colgroup, then browsers
        automatically select the set of cells to which the header
        cell applies.
        """
        return self.attributes['scope'].value

    @scope.setter
    def scope(self, v):
        self.attributes['scope'].value = v

    @property
    def colspan(self):
        """ This attribute contains a non-negative integer value that
        indicates for how many columns the cell extends. Its default
        value is 1. Values higher than 1000 will be considered as
        incorrect and will be set to the default value (1).
        """
        return self.attributes['colspan'].value

    @colspan.setter
    def colspan(self, v):
        self.attributes['colspan'].value = v

    @property
    def headers(self):
        """ This attribute contains a list of space-separated strings,
        each corresponding to the id attribute of the <th> elements that
        apply to this element.
        """
        return self.attributes['headers'].value

    @headers.setter
    def headers(self, v):
        self.attributes['headers'].value = v

    @property
    def rowspan(self):
        """ This attribute contains a non-negative integer value that
        indicates for how many rows the cell extends. Its default value
        is 1; if its value is set to 0, it extends until the end of the
        table section (<thead>, <tbody>, <tfoot>, even if implicitly
        defined), that the cell belongs to. Values higher than 65534 are
        clipped down to 65534.
        """
        return self.attributes['rowspan'].value

    @rowspan.setter
    def rowspan(self, v):
        self.attributes['rowspan'].value = v

class tds(elements):
    """ A class used to contain a collection of ``td`` elements.
    """

class td(element):
    """ The HTML <td> element defines a cell of a table that contains
    data. It participates in the table model.

    https://developer.mozilla.org/en-US/docs/Web/HTML/Element/td
    """

    @property
    def colspan(self):
        """ This attribute contains a non-negative integer value that
        indicates for how many columns the cell extends. Its default
        value is 1. Values higher than 1000 will be considered as
        incorrect and will be set to the default value (1).
        """
        return self.attributes['colspan'].value

    @colspan.setter
    def colspan(self, v):
        self.attributes['colspan'].value = v

    @property
    def headers(self):
        """ This attribute contains a list of space-separated strings,
        each corresponding to the id attribute of the <th> elements that
        apply to this element.
        """
        return self.attributes['headers'].value

    @headers.setter
    def headers(self, v):
        self.attributes['headers'].value = v

    @property
    def rowspan(self):
        """ This attribute contains a non-negative integer value that
        indicates for how many rows the cell extends. Its default value
        is 1; if its value is set to 0, it extends until the end of the
        table section (<thead>, <tbody>, <tfoot>, even if implicitly
        defined), that the cell belongs to. Values higher than 65534 are
        clipped down to 65534.
        """
        return self.attributes['rowspan'].value

    @rowspan.setter
    def rowspan(self, v):
        self.attributes['rowspan'].value = v

class theads(elements):
    """ A class used to contain a collection of ``thead`` elements.  """

class thead(element):
    """ The <thead> HTML element defines a set of rows defining the head
    of the columns of the table.
    """

class metas(elements):
    """ A class used to contain a collection of ``meta`` elements.  """

class meta(element):
    """ The <meta> HTML element represents metadata that cannot be
    represented by other HTML meta-related elements, like <base>,
    <link>, <script>, <style> or <title>.
    """
    isvoid = True
    @property
    def charset(self):
        """ This attribute declares the document's character encoding.
        If the attribute is present, its value must be an ASCII
        case-insensitive match for the string "utf-8", because UTF-8 is
        the only valid encoding for HTML5 documents. <meta> elements
        which declare a character encoding must be located entirely
        within the first 1024 bytes of the document.
        """
        return self.attributes['charset'].value

    @charset.setter
    def charset(self, v):
        self.attributes['charset'].value = v

    @property
    def content(self):
        """ This attribute contains the value for the http-equiv or name
        attribute, depending on which is used.
        """
        return self.attributes['content'].value

    @content.setter
    def content(self, v):
        self.attributes['content'].value = v

    @property
    def name(self):
        """ The name and content attributes can be used together to
        provide document metadata in terms of name-value pairs, with the
        name attribute giving the metadata name, and the content
        attribute giving the value.
        """
        return self.attributes['name'].value

    @name.setter
    def name(self, v):
        self.attributes['name'].value = v

    @property
    def http_equiv(self):
        """ Defines a pragma directive.
        """
        return self.attributes['http-equiv'].value

    @http_equiv.setter
    def http_equiv(self, v):
        self.attributes['http-equiv'].value = v

class styles(elements):
    """ A class used to contain a collection of ``style`` elements."""

class style(element):
    """ The <style> HTML element contains style information for a
    document, or part of a document. It contains CSS, which is applied
    to the contents of the document containing the <style> element.

    The <style> element must be included inside the <head> of the
    document. If you include multiple <style> and <link> elements in
    your document, they will be applied to the DOM in the order they are
    included in the document — make sure you include them in the correct
    order, to avoid unexpected cascade issues.

    In the same manner as <link> elements, <style> elements can include
    media attributes that contain media queries, allowing you to
    selectively apply internal stylesheets to your document depending on
    media features such as viewport width.
    """
    @property
    def title(self):
        """ This attribute specifies alternative style sheet sets.
        """
        return self.attributes['title'].value

    @title.setter
    def title(self, v):
        self.attributes['title'].value = v

    @property
    def media(self):
        """ This attribute defines which media the style should be
        applied to. Its value is a media query, which defaults to all if
        the attribute is missing.
        """
        return self.attributes['media'].value

    @media.setter
    def media(self, v):
        self.attributes['media'].value = v

    @property
    def nonce(self):
        """ A cryptographic nonce (number used once) used to allow
        inline styles in a style-src Content-Security-Policy. The server
        must generate a unique nonce value each time it transmits a
        policy. It is critical to provide a nonce that cannot be guessed
        as bypassing a resource’s policy is otherwise trivial.
        """
        return self.attributes['nonce'].value

    @nonce.setter
    def nonce(self, v):
        self.attributes['nonce'].value = v

class datas(elements):
    """ A class used to contain a collection of ``data`` elements."""

class data(element):
    """ The <data> HTML element links a given piece of content with a
    machine-readable translation. If the content is time- or
    date-related, the <time> element must be used.
    """
    @property
    def value(self):
        """ This attribute specifies the machine-readable translation of
        the content of the element.
        """
        return self.attributes['value'].value

    @value.setter
    def value(self, v):
        self.attributes['value'].value = v

class labels(elements):
    """ A class used to contain a collection of ``label`` elements."""

class label(element):
    """ The <label> HTML element represents a caption for an item in a
    user interface.
    """
    @property
    def for_(self):
        """ The value of the for attribute must be a single id for a
        label form-related element in the same document as the
        <label> element. So, any given label element can be associated
        with only one form control.

        The first element in the document with an id attribute matching
        the value of the for attribute is the labeled control for this
        label element — if the element with that id is actually a
        labelable element.  If it is not a labelable element, then the
        for attribute has no effect. If there are other elements that
        also match the id value, later in the document, they are not
        considered.

        Multiple label elements can be given the same value for their
        for attribute; doing so causes the associated form control (the
        form control that for value references) to have multiple labels.

        Note: A <label> element can have both a for attribute and a
        contained control element, as long as the for attribute points
        to the contained control element.
        """
        return self.attributes['for'].value

    @for_.setter
    def for_(self, v):
        self.attributes['for'].value = v

    @property
    def form(self):
        """ The form attribute specifies the form the label belongs to.

        The value of this attribute must be equal to the id attribute of
        a <form> element in the same document. 
        """
        return self.attributes['form'].value

    @form.setter
    def form(self, v):
        self.attributes['form'].value = v

class summaries(elements):
    """ A class used to contain a collection of ``summary`` elements.
    """

class summary(element):
    """ The <summary> HTML element specifies a summary, caption, or
    legend for a <details> element's disclosure box. Clicking the
    <summary> element toggles the state of the parent <details> element
    open and closed.
    """

class detailss(elements):
    """ A class used to contain a collection of ``details`` elements."""

class details(element):
    """ The <details> HTML element creates a disclosure widget in which
    information is visible only when the widget is toggled into an
    "open" state. A summary or label must be provided using the
    <summary> element.

    A disclosure widget is typically presented onscreen using a small
    triangle which rotates (or twists) to indicate open/closed status,
    with a label next to the triangle. The contents of the <summary>
    element are used as the label for the disclosure widget.
    """
    @property
    def open(self):
        """ This Boolean attribute indicates whether or not the details
        — that is, the contents of the <details> element — are currently
        visible. The details are shown when this attribute exists, or
        hidden when this attribute is absent. By default this attribute
        is absent which means the details are not visible.
        """
        return self.attributes['open'].value

    @open.setter
    def open(self, v):
        self.attributes['open'].value = v

class tables(elements):
    """ A class used to contain a collection of ``table`` elements."""

class table(element):
    """ The <table> HTML element represents tabular data — that is,
    information presented in a two-dimensional table comprised of rows
    and columns of cells containing data.
    """

class trs(elements):
    """ A class used to contain a collection of ``tr`` elements."""

class tr(element):
    """ The <tr> HTML element defines a row of cells in a table. The
    row's cells can then be established using a mix of <td> (data cell)
    and <th> (header cell) elements.
    """

class selects(elements):
    """ A class used to contain a collection of ``tr`` elements."""

class select(element):
    """ The <select> HTML element represents a control that provides a
    menu of options:
    """
    @property
    def selected(self):
        """ Returns a list of the ``option`` elements that were marked as
        seleted (<option selected>My Option</option>).
        """
        r = list()
        for el in self:
            if not isinstance(el, option):
                continue

            if el.selected is not undef:
                el.append(el.value)

        return r

    @selected.setter
    def selected(self, v):
        """ Set the ``option`` elements to selected if their value
        properties is in the v list.

        :param: v list<str>|tuple<str>: A list or tuple of str values.
        If an option has a value that is in this list, the option
        element will be marked as selected.
        """
        for el in self:
            if not isinstance(el, option):
                continue

            el.selected = False

            if el.value in v:
                el.selected = True
            
    @property
    def required(self):
        """ A Boolean attribute indicating that an option with a
        non-empty string value must be selected.
        """
        return self.attributes['required'].value

    @required.setter
    def required(self, v):
        self.attributes['required'].value = v

    @property
    def multiple(self):
        """ This Boolean attribute indicates that multiple options can
        be selected in the list. If it is not specified, then only one
        option can be selected at a time. When multiple is specified,
        most browsers will show a scrolling list box instead of a single
        line dropdown.
        """
        return self.attributes['multiple'].value

    @multiple.setter
    def multiple(self, v):
        self.attributes['multiple'].value = v

    @property
    def autofocus(self):
        """ This Boolean attribute lets you specify that a form control
        should have input focus when the page loads. Only one form
        element in a document can have the autofocus attribute.
        """
        return self.attributes['autofocus'].value

    @autofocus.setter
    def autofocus(self, v):
        self.attributes['autofocus'].value = v

    @property
    def size(self):
        """ If the control is presented as a scrolling list box (e.g.
        when multiple is specified), this attribute represents the
        number of rows in the list that should be visible at one time.
        Browsers are not required to present a select element as a
        scrolled list box.  The default value is 0.
        """
        return self.attributes['size'].value

    @size.setter
    def size(self, v):
        self.attributes['size'].value = v

    @property
    def form(self):
        """ The <form> element to associate the <select> with (its form
        owner). The value of this attribute must be the id of a <form>
        in the same document. (If this attribute is not set, the
        <select> is associated with its ancestor <form> element, if
        any.)

        This attribute lets you associate <select> elements to <form>s
        anywhere in the document, not just inside a <form>. It can also
        override an ancestor <form> element.
        """
        return self.attributes['form'].value

    @form.setter
    def form(self, v):
        self.attributes['form'].value = v

    @property
    def name(self):
        """ This attribute is used to specify the name of the control.
        """
        return self.attributes['name'].value

    @name.setter
    def name(self, v):
        self.attributes['name'].value = v

    @property
    def disabled(self):
        """ This Boolean attribute indicates that the user cannot
        interact with the control. If this attribute is not specified,
        the control inherits its setting from the containing element,
        for example <fieldset>; if there is no containing element with
        the disabled attribute set, then the control is enabled.
        """
        return self.attributes['disabled'].value

    @disabled.setter
    def disabled(self, v):
        self.attributes['disabled'].value = v

    @property
    def autocomplete(self):
        """ A DOMString providing a hint for a user agent's autocomplete
        feature. See The HTML autocomplete attribute for a complete list
        of values and details on how to use autocomplete.
        """
        return self.attributes['autocomplete'].value

    @autocomplete.setter
    def autocomplete(self, v):
        self.attributes['autocomplete'].value = v

class optgroups(elements):
    """ A class used to contain a collection of ``optgroup`` elements."""

class optgroup(element):
    """ The <optgroup> HTML element creates a grouping of options within
    a <select> element.
    """
    @property
    def label(self):
        """ The name of the group of options, which the browser can use
        when labeling the options in the user interface. This attribute
        is mandatory if this element is used.
        """
        return self.attributes['label'].value

    @label.setter
    def label(self, v):
        self.attributes['label'].value = v

    @property
    def disabled(self):
        """ If this Boolean attribute is set, none of the items in this
        option group is selectable. Often browsers grey out such control
        and it won't receive any browsing events, like mouse clicks or
        focus-related ones.
        """
        return self.attributes['disabled'].value

    @disabled.setter
    def disabled(self, v):
        self.attributes['disabled'].value = v

class qs(elements):
    """ A class used to contain a collection of ``q`` elements."""

class q(element):
    """ The <q> HTML element indicates that the enclosed text is a short
    inline quotation. Most modern browsers implement this by surrounding
    the text in quotation marks. This element is intended for short
    quotations that don't require paragraph breaks; for long quotations
    use the <blockquote> element.
    """
    @property
    def cite(self):
        """ The value of this attribute is a URL that designates a
        source document or message for the information quoted. This
        attribute is intended to point to information explaining the
        context or the reference for the quote.
        """
        return self.attributes['cite'].value

    @cite.setter
    def cite(self, v):
        self.attributes['cite'].value = v

class sources(elements):
    """ A class used to contain a collection of ``source`` elements."""

class source(element):
    """ The <source> HTML element specifies multiple media resources for
    the <picture>, the <audio> element, or the <video> element. It is an
    empty element, meaning that it has no content and does not have a
    closing tag. It is commonly used to offer the same media content in
    multiple file formats in order to provide compatibility with a broad
    range of browsers given their differing support for image file
    formats and media file formats.
    """
    @property
    def type(self):
        """ The MIME media type of the resource, optionally with a
        codecs parameter.
        """
        return self.attributes['type'].value

    @type.setter
    def type(self, v):
        self.attributes['type'].value = v

    @property
    def src(self):
        """ Required for <audio> and <video>, address of the media
        resource. The value of this attribute is ignored when the
        <source> element is placed inside a <picture> element.
        """
        return self.attributes['src'].value

    @src.setter
    def src(self, v):
        self.attributes['src'].value = v

    @property
    def media(self):
        """ Media query of the resource's intended media.
        """
        return self.attributes['media'].value

    @media.setter
    def media(self, v):
        self.attributes['media'].value = v

    @property
    def sizes(self):
        return self.attributes['sizes'].value

    @sizes.setter
    def sizes(self, v):
        self.attributes['sizes'].value = v

    @property
    def srcset(self):
        """ A list of one or more strings separated by commas indicating
        a set of possible images represented by the source for the
        browser to use.
        """
        return self.attributes['srcset'].value

    @srcset.setter
    def srcset(self, v):
        self.attributes['srcset'].value = v

class scripts(elements):
    """ A class used to contain a collection of ``script`` elements."""

class script(element):
    """ The <script> HTML element is used to embed executable code or
    data; this is typically used to embed or refer to JavaScript code.
    The <script> element can also be used with other languages, such as
    WebGL's GLSL shader programming language and JSON.
    """
    def __init__(self, body=None, *args, **kwargs):
        """ Create a script element.

        :param: body str|file.resource: 

            if str:
                `body` will be the text within the script tag.
            
            if file.resource:
                A file resource object used to set the
                script's `src` attribute.
        """
        # If a file.resource was given
        if isinstance(body, file.resources):
            res = body
            body = None
            self.site.resources &= res
            self.src = res.url
            if res.local:
                res.save()
                if res.exists:
                    self.src = res.public

            self.integrity = res.integrity
            self.crossorigin = res.crossorigin
            
        super().__init__(body, *args, **kwargs)

    @property
    def crossorigin(self):
        """ Normal script elements pass minimal information to the
        window.onerror for scripts which do not pass the standard CORS
        checks. To allow error logging for sites which use a separate
        domain for static media, use this attribute. See CORS settings
        attributes for a more descriptive explanation of its valid
        arguments.
        """

        return self.attributes['crossorigin'].value

    @crossorigin.setter
    def crossorigin(self, v):
        self.attributes['crossorigin'].value = v

    @property
    def referrerpolicy(self):
        """ Indicates which referrer to send when fetching the script,
        or resources fetched by the script.
        """
        return self.attributes['referrerpolicy'].value

    @referrerpolicy.setter
    def referrerpolicy(self, v):
        self.attributes['referrerpolicy'].value = v

    @property
    def integrity(self):
        """ This attribute contains inline metadata that a user agent
        can use to verify that a fetched resource has been delivered
        free of unexpected manipulation. See Subresource Integrity.
        """
        return self.attributes['integrity'].value

    @integrity.setter
    def integrity(self, v):
        self.attributes['integrity'].value = v

    @property
    def defer(self):
        """  This Boolean attribute is set to indicate to a browser that
        the script is meant to be executed after the document has been
        parsed, but before firing DOMContentLoaded.

        Scripts with the defer attribute will prevent the
        DOMContentLoaded event from firing until the script has loaded
        and finished evaluating.

        Warning: This attribute must not be used if the src attribute is
        absent (i.e. for inline scripts), in this case it would have no
        effect.

        The defer attribute has no effect on module scripts — they defer
        by default.

        Scripts with the defer attribute will execute in the order in
        which they appear in the document.

        This attribute allows the elimination of parser-blocking
        JavaScript where the browser would have to load and evaluate
        scripts before continuing to parse.  async has a similar effect
        in this case.
        """
        return self.attributes['defer'].value

    @defer.setter
    def defer(self, v):
        self.attributes['defer'].value = v

    @property
    def type(self):
        """ This attribute indicates the type of script represented.
        """
        return self.attributes['type'].value

    @type.setter
    def type(self, v):
        self.attributes['type'].value = v

    @property
    def src(self):
        """ This attribute specifies the URI of an external script; this
        can be used as an alternative to embedding a script directly
        within a document.
        """
        return self.attributes['src'].value

    @src.setter
    def src(self, v):
        self.attributes['src'].value = v

    @property
    def importance(self):
        """ Priority Hints can be set for resources in HTML by
        specifying an importance attribute on a <script>, <img>, or
        <link> element (though other elements such as <iframe> may see
        support later). 
        
        https://developers.google.com/web/updates/2019/02/priority-hints
        """
        return self.attributes['importance'].value

    @importance.setter
    def importance(self, v):
        self.attributes['importance'].value = v

    @property
    def nonce(self):
        """ A cryptographic nonce (number used once) to allow scripts in
        a script-src Content-Security-Policy. The server must generate a
        unique nonce value each time it transmits a policy. It is
        critical to provide a nonce that cannot be guessed as bypassing
        a resource's policy is otherwise trivial.
        """
        return self.attributes['nonce'].value

    @nonce.setter
    def nonce(self, v):
        self.attributes['nonce'].value = v

    @property
    def nomodule(self):
        """ This Boolean attribute is set to indicate that the script
        should not be executed in browsers that support ES2015 modules —
        in effect, this can be used to serve fallback scripts to older
        browsers that do not support modular JavaScript code.
        """
        return self.attributes['nomodule'].value

    @nomodule.setter
    def nomodule(self, v):
        self.attributes['nomodule'].value = v

    @property
    def async_(self):
        """ For classic scripts, if the async attribute is present, then
        the classic script will be fetched in parallel to parsing and
        evaluated as soon as it is available.

        For module scripts, if the async attribute is present then the
        scripts and all their dependencies will be executed in the defer
        queue, therefore they will get fetched in parallel to parsing
        and evaluated as soon as they are available.

        This attribute allows the elimination of parser-blocking
        JavaScript where the browser would have to load and evaluate
        scripts before continuing to parse. defer has a similar effect
        in this case.

        This is a boolean attribute: the presence of a boolean attribute
        on an element represents the true value, and the absence of the
        attribute represents the false value.
        """
        return self.attributes['async'].value

    @async_.setter
    def async_(self, v):
        self.attributes['async'].value = v

class videos(elements):
    """ A class used to contain a collection of ``video`` elements."""

class video(element):
    """ The <video> HTML element embeds a media player which supports
    video playback into the document. You can use <video> for audio
    content as well, but the <audio> element may provide a more
    appropriate user experience.
    """
    @property
    def disableremoteplayback(self):
        """ A Boolean attribute used to disable the capability of remote
        playback in devices that are attached using wired (HDMI, DVI,
        etc.) and wireless technologies (Miracast, Chromecast, DLNA,
        AirPlay, etc).
        """
        return self.attributes['disableremoteplayback'].value

    @disableremoteplayback.setter
    def disableremoteplayback(self, v):
        self.attributes['disableremoteplayback'].value = v

    @property
    def disablepictureinpicture(self):
        """ Prevents the browser from suggesting a Picture-in-Picture
        context menu or to request Picture-in-Picture automatically in
        some cases.
        """
        return self.attributes['disablepictureinpicture'].value

    @disablepictureinpicture.setter
    def disablepictureinpicture(self, v):
        self.attributes['disablepictureinpicture'].value = v

    @property
    def crossorigin(self):
        """ This enumerated attribute indicates whether to use CORS to
        fetch the related video.
        """
        return self.attributes['crossorigin'].value

    @crossorigin.setter
    def crossorigin(self, v):
        self.attributes['crossorigin'].value = v

    @property
    def loop(self):
        """ A Boolean attribute; if specified, the browser will
        automatically seek back to the start upon reaching the end of
        the video.
        """
        return self.attributes['loop'].value

    @loop.setter
    def loop(self, v):
        self.attributes['loop'].value = v

    @property
    def buffered(self):
        return self.attributes['buffered'].value

    @buffered.setter
    def buffered(self, v):
        self.attributes['buffered'].value = v

    @property
    def height(self):
        """ The height of the video's display area, in CSS pixels
        (absolute values only; no percentages.)
        """
        return self.attributes['height'].value

    @height.setter
    def height(self, v):
        self.attributes['height'].value = v

    @property
    def src(self):
        """ The URL of the video to embed. This is optional; you may
        instead use the <source> element within the video block to
        specify the video to embed.
        """
        return self.attributes['src'].value

    @src.setter
    def src(self, v):
        self.attributes['src'].value = v

    @property
    def controlslist(self):
        """ The controlslist attribute, when specified, helps the
        browser select what controls to show on the media element
        whenever the browser shows its own set of controls (e.g. when
        the controls attribute is specified).
        """
        return self.attributes['controlslist'].value

    @controlslist.setter
    def controlslist(self, v):
        self.attributes['controlslist'].value = v

    @property
    def controls(self):
        """ If this attribute is present, the browser will offer
        controls to allow the user to control video playback, including
        volume, seeking, and pause/resume playback.
        """
        return self.attributes['controls'].value

    @controls.setter
    def controls(self, v):
        self.attributes['controls'].value = v

    @property
    def poster(self):
        """ A URL for an image to be shown while the video is
        downloading. If this attribute isn't specified, nothing is
        displayed until the first frame is available, then the first
        frame is shown as the poster frame.
        """
        return self.attributes['poster'].value

    @poster.setter
    def poster(self, v):
        self.attributes['poster'].value = v

    @property
    def width(self):
        """ The width of the video's display area, in CSS pixels
        (absolute values only; no percentages).
        """
        return self.attributes['width'].value

    @width.setter
    def width(self, v):
        self.attributes['width'].value = v

    @property
    def playsinline(self):
        """ A Boolean attribute indicating that the video is to be
        played "inline", that is within the element's playback area.
        Note that the absence of this attribute does not imply that the
        video will always be played in fullscreen.
        """
        return self.attributes['playsinline'].value

    @playsinline.setter
    def playsinline(self, v):
        self.attributes['playsinline'].value = v

    @property
    def autopictureinpicture(self):
        """ A Boolean attribute which if true indicates that the element
        should automatically toggle picture-in-picture mode when the
        user switches back and forth between this document and another
        document or application.
        """
        return self.attributes['autopictureinpicture'].value

    @autopictureinpicture.setter
    def autopictureinpicture(self, v):
        self.attributes['autopictureinpicture'].value = v

    @property
    def autoplay(self):
        """ A Boolean attribute; if specified, the video
        automatically begins to play back as soon as it can do so
        without stopping to finish loading the data.
        """
        return self.attributes['autoplay'].value

    @autoplay.setter
    def autoplay(self, v):
        self.attributes['autoplay'].value = v

    @property
    def muted(self):
        """ A Boolean attribute that indicates the default setting of
        the audio contained in the video. If set, the audio will be
        initially silenced. Its default value is false, meaning that the
        audio will be played when the video is played.
        """
        return self.attributes['muted'].value

    @muted.setter
    def muted(self, v):
        self.attributes['muted'].value = v

    @property
    def preload(self):
        """ This enumerated attribute is intended to provide a hint to
        the browser about what the author thinks will lead to the best
        user experience with regards to what content is loaded before
        the video is played.
        """
        return self.attributes['preload'].value

    @preload.setter
    def preload(self, v):
        self.attributes['preload'].value = v

class htmls(elements):
    """ A class used to contain a collection of ``html`` elements."""

class html(element):
    """ This is two different classes depending on how it is
    instantiated. If no ``html`` argument is passed to the constructor,
    the class is simply a representation of the <html> tag. 
    The <html> HTML element represents the root (top-level element) of
    an HTML document, so it is also referred to as the root element. All
    other elements must be descendants of this element.

    However, if a str is given as the ``html`` argument to the
    constructor, the argument is assumed to be a string of HTML.
    ``self`` morphs into a ``elements`` collection. The collection
    will contain the results of the parsed HTML.

        # When no ``html`` argument is used, we can build an HTML
        # document from scratch:
        import dom
        html = dom.html()                  # Create <html>
        assert isinstance(html, dom.html)  # It's an html object
        html += head = dom.head()          # Create and append <head>
        head += dom.title('My Title')      # Create and append <title>
        html += dom.body()                 # Append a <body> to <html>

    However, using the ``html`` parameter, we can use dom.html as a
    parser:

        html = '''
        <html>
            <head>
                <title>My Title</title>
            </head>
        </html>
        '''

        # Parse html str into an elements collection
        html1 = dom.html(html=html)

        # Type is morphed to dom.elements
        assert isinstance(html1, dom.elements)  

        # html1 is now a DOM object so we can use CSS3 selectors,
        # iterate over it, etc.
        html1['html head title'].text == 'My Title'
    """

    def __init__(self, html=None, ids=False, *args, **kwargs):
        """ Create HTML element, parses HTML string depending on whether
        or not `html` is provided (see docstring for this class)

        :param: html str: If provided, the html is parsed. See docstring
        for class.

        :param: ids bool: If True, each element added to the DOM is
        given a randomly generated id attribute. If False, no id
        attribute is set.
        """
        if isinstance(html, str):
            # Morph the object into an `elements` object
            htmlparser = self._gethtmlparser()
            self.__class__ = elements
            super(elements, self).__init__(*args, **kwargs)

            # Assume the input str is HTML and convert the elements in
            # the HTML sting into a collection of `elements` objects.
            prs = htmlparser(convert_charrefs=False, ids=ids)
            prs.feed(html)
            if prs.stack:
                raise HtmlParseError('Unclosed tag', frm=prs.stack[-1])
                
            # The parsed HTML elements tree becomes this `elements`'s
            # (self) collection's constituents.
            self += prs.elements
        else:
            super().__init__(*args, **kwargs)

    @staticmethod
    def _gethtmlparser():
        """ Return the htmlparser class. 

        This was put in a static method only so we could lazy-load the
        HTMLParser in order to shave a few ms off the startup time.
        """

        from html.parser import HTMLParser

        class htmlparser(HTMLParser):
            """ A private HTML parsing class. This is used by the dom.html class
            to parse HTML into a DOM object. 

            The actual parsing is done by the HTMLParser class that's built into
            Python (from which this object inherits). Once the document has been
            parsed (initiated by the ``feed`` method), the ``elements`` property
            will contain the a DOM structure of the HTML document.
            """
            def __init__(self, ids=False, *args, **kwargs):
                """ Create the parser.

                :param: ids bool: If True, each element created is given a UUID
                encoded as a base64 string. If False, no id is given.
                """
                super().__init__(*args, **kwargs)
                self.ids = ids
                self.elements = elements()
                self.stack = list()

            def handle_starttag(self, tag, attrs):
                """ This is called by HTMLParser each time it encounters a start
                tag. We take that tag and add it to the DOM.
                """

                # Get an element class based on the tag
                el = elements.getby(tag=tag)

                # NOTE This seems a little strict. If we were scraping a page we
                # would probably want it to be forgiving of non-standard tags.
                if not el:
                    raise NotImplementedError(
                        'The <%s> tag has no DOM implementation' % tag
                    )

                # Instantiate
                el = el(id=self.ids)

                # Assign HTML attributes
                for attr in attrs:
                    el.attributes[attr[0]] = attr[1]

                # Push element on top of stack
                try:
                    cur = self.stack[-1]
                except IndexError:
                    self.elements += el
                else:
                    cur[0] += el
                finally:
                    if not el.isvoid:
                        self.stack.append([el, self.getpos()])

            def handle_comment(self, data):
                """ This method is called when a comment is encountered (e.g.,
                <!--comment-->).
                """

                try:
                    cur = self.stack[-1]
                except IndexError:
                    self.elements += comment(data)
                else:
                    cur[0] += comment(data)

            def handle_endtag(self, tag):
                """ This method is called to handle the end tag of an element
                (e.g., </div>).
                """
                try:
                    cur = self.stack[-1]
                except IndexError:
                    pass
                else:
                    if cur[0].tag == tag:
                        self.stack.pop()

            def handle_data(self, data):
                """ This method is called to process arbitrary data (e.g. text
                nodes and the content of <script>...</script> and
                <style>...</style>).
                """
                try:
                    cur = self.stack[-1]
                except IndexError:
                    if not data.isspace():
                        raise HtmlParseError(
                            'No element to add text to', [None, self.getpos()]
                        )
                else:
                    last = cur[0].elements.last
                    if type(last) is text:
                        last.html += data
                    else:
                        cur[0] += data

            def handle_entityref(self, name):
                """ This method is called to process a named character reference
                of the form &name; (e.g. &gt;), where name is a general entity
                reference (e.g. 'gt').
                """
                try:
                    cur = self.stack[-1]
                except IndexError:
                    raise HtmlParseError(
                        'No element to add text to', [None, self.getpos()]
                    )
                else:
                    txt = text('&%s;' % name, esc=False)
                    last = cur[0].elements.last
                    if type(last) is text:
                        last.html += txt.value
                    else:
                        cur[0] += txt

            def handle_charref(self, name):
                """ This method is called to process decimal and hexadecimal
                numeric character references of the form &#NNN; and &#xNNN;. For
                example, the decimal equivalent for &gt; is &#62;, whereas the
                hexadecimal is &#x3E;; in this case the method will receive '62'
                or 'x3E'. This method is never called if convert_charrefs is
                True.
                """
                # TODO: This was added after the main html tests were written
                # (not sure why it was left behind). We should write tests that
                # target it specifically.

                # TODO: There is a lot of shared logic between this handler and
                # handle_entityref, handle_data, etc. We can start thinking
                # about consolidating this logic.
                try:
                    cur = self.stack[-1]
                except IndexError:
                    raise HtmlParseError(
                        'No element to add text to', [None, self.getpos()]
                    )
                else:
                    txt = text('&#%s;' % name, esc=False)
                    last = cur[0].elements.last
                    if type(last) is text:
                        last.html += txt.value
                    else:
                        cur[0] += txt

            def handle_decl(self, decl):
                """ This method is called to handle an HTML doctype declaration
                (e.g. <!DOCTYPE html>).

                The decl parameter will be the entire contents of the
                declaration inside the <!...> markup (e.g. 'DOCTYPE html').
                """
                # HACK:10d9a676 we need to fully support DOCTYPEs, not
                # just the standard mode doc type. See TODO:10d9a676.
                if decl == 'DOCTYPE html':
                    return

                raise NotImplementedError(
                    'HTML doctype declaration are not implemented'
                )

            def unknown_decl(self, data):
                """ This method is called when an unrecognized declaration is
                read by the parser.

                The data parameter will be the entire contents of the
                declaration inside the <![...]> markup. It is sometimes useful
                to be overridden by a derived class. The base class
                implementation does nothing.
                """
                raise NotImplementedError(
                    'HTML doctype declaration are not implemented'
                )

            def handle_pi(self, decl):
                """ Method called when a processing instruction is encountered.
                The data parameter will contain the entire processing
                instruction. For example, for the processing instruction <?proc
                color='red'>, this method would be called as handle_pi("proc
                color='red'"). It is intended to be overridden by a derived
                class; the base class implementation does nothing.

                NOTE: The HTMLParser class uses the SGML syntactic rules for
                processing instructions. An XHTML processing instruction using
                the trailing '?' will cause the '?' to be included in data.
                """
                raise NotImplementedError(
                    'Processing instructions are not implemented'
                )

        return htmlparser

        @property
        def manifest(self):
            """ Specifies the URI of a resource manifest indicating
            resources that should be cached locally.
            """
            return self.attributes['manifest'].value

        @manifest.setter
        def manifest(self, v):
            self.attributes['manifest'].value = v

        @property
        def version(self):
            """ Specifies the version of the HTML Document Type Definition
            that governs the current document. This attribute is not needed,
            because it is redundant with the version information in the
            document type declaration.
            """
            return self.attributes['version'].value

        @version.setter
        def version(self, v):
            self.attributes['version'].value = v

        @property
        def xmlns(self):
            """ Specifies the XML Namespace of the document. Default value
            is "http://www.w3.org/1999/xhtml". This is required in documents
            parsed with XML parsers, and optional in text/html
            documents.
            """
            return self.attributes['xmlns'].value

        @xmlns.setter
        def xmlns(self, v):
            self.attributes['xmlns'].value = v

class h1s(elements):
    """ A class used to contain a collection of ``h1`` elements."""

class h1(element):
    """ <h1> is the highest section level heading.
    """

class h2s(elements):
    """ A class used to contain a collection of ``h2`` elements."""

class h2(element):
    """ <h2> is the second highest section level heading.
    """

class h3s(elements):
    """ A class used to contain a collection of ``h3`` elements."""

class h3(element):
    """ <h3> is the third highest section level heading.
    """

class h4s(elements):
    """ A class used to contain a collection of ``h4`` elements."""

class h4(element):
    """ <h4> is the fourth highest section level heading.
    """

class h5s(elements):
    """ A class used to contain a collection of ``h5`` elements."""

class h5(element):
    """ <h5> is the fifth highest section level heading.
    """

class h6s(elements):
    """ A class used to contain a collection of ``h6`` elements."""

class h6(element):
    """ <h6> is the six highest section level heading.
    """

# TODO:dea3866d
heading1 = h1
heading2 = h2
heading3 = h3
heading4 = h4
heading5 = h5
heading6 = h6

class heads(elements):
    """ A class used to contain a collection of ``head`` elements."""

class head(element):
    """ The <head> HTML element contains machine-readable information
    (metadata) about the document, like its title, scripts, and style
    sheets.
    """

class hrs(elements):
    """ A class used to contain a collection of ``hr`` elements."""

class hr(element):
    """ The <hr> HTML element represents a thematic break between
    paragraph-level elements: for example, a change of scene in a story,
    or a shift of topic within a section.
    """
    isvoid = True
    @property
    def align(self):
        """ Sets the alignment of the rule on the page. If no value is
        specified, the default value is left.
        """
        return self.attributes['align'].value

    @align.setter
    def align(self, v):
        self.attributes['align'].value = v

    @property
    def color(self):
        """ Sets the color of the rule through color name or hexadecimal
        value.
        """
        return self.attributes['color'].value

    @color.setter
    def color(self, v):
        self.attributes['color'].value = v

    @property
    def noshade(self):
        """ Sets the rule to have no shading.
        """
        return self.attributes['noshade'].value

    @noshade.setter
    def noshade(self, v):
        self.attributes['noshade'].value = v

    @property
    def size(self):
        """ Sets the height, in pixels, of the rule.
        """
        return self.attributes['size'].value

    @size.setter
    def size(self, v):
        self.attributes['size'].value = v

    @property
    def width(self):
        """ Sets the length of the rule on the page through a pixel or
        percentage value.
        """
        return self.attributes['width'].value

    @width.setter
    def width(self, v):
        self.attributes['width'].value = v

class areas(elements):
    """ A class used to contain a collection of ``area`` elements."""

class area(element):
    """ The <area> HTML element defines an area inside an image map that
    has predefined clickable areas. An image map allows geometric areas
    on an image to be associated with hypertext link.
    """
    @property
    def referrerpolicy(self):
        """ A string indicating which referrer to use when fetching the
        resource.
        """
        return self.attributes['referrerpolicy'].value

    @referrerpolicy.setter
    def referrerpolicy(self, v):
        self.attributes['referrerpolicy'].value = v

    @property
    def target(self):
        """ A keyword or author-defined name of the browsing context to
        display the linked resource.
        """
        return self.attributes['target'].value

    @target.setter
    def target(self, v):
        self.attributes['target'].value = v

    @property
    def coords(self):
        """ The coords attribute details the coordinates of the shape
        attribute in size, shape, and placement of an <area>. This
        attribute must not be used if shape is set to default.
        """
        return self.attributes['coords'].value

    @coords.setter
    def coords(self, v):
        self.attributes['coords'].value = v

    @property
    def hreflang(self):
        """ Indicates the language of the linked resource. Allowed
        values are defined by RFC 5646: Tags for Identifying Languages
        (also known as BCP 47). Use this attribute only if the href
        attribute is present.
        """
        return self.attributes['hreflang'].value

    @hreflang.setter
    def hreflang(self, v):
        self.attributes['hreflang'].value = v

    @property
    def ping(self):
        """ Contains a space-separated list of URLs to which, when the
        hyperlink is followed, POST requests with the body PING will be
        sent by the browser (in the background). Typically used for
        tracking.
        """
        return self.attributes['ping'].value

    @ping.setter
    def ping(self, v):
        self.attributes['ping'].value = v

    @property
    def href(self):
        return self.attributes['href'].value

    @href.setter
    def href(self, v):
        """ The hyperlink target for the area. Its value is a valid URL.
        This attribute may be omitted; if so, the <area> element does
        not represent a hyperlink.
        """
        self.attributes['href'].value = v

    @property
    def alt(self):
        """ A text string alternative to display on browsers that do not
        display images. The text should be phrased so that it presents
        the user with the same kind of choice as the image would offer
        when displayed without the alternative text. This attribute is
        required only if the href attribute is used.
        """
        return self.attributes['alt'].value

    @alt.setter
    def alt(self, v):
        self.attributes['alt'].value = v

    @property
    def download(self):
        """ This attribute, if present, indicates that the author
        intends the hyperlink to be used for downloading a resource. See
        <a> for a full description of the download attribute.
        """
        return self.attributes['download'].value

    @download.setter
    def download(self, v):
        self.attributes['download'].value = v

    @property
    def rel(self):
        """ For anchors containing the href attribute, this attribute
        specifies the relationship of the target object to the link
        object. The value is a space-separated list of link types
        values. The values and their semantics will be registered by
        some authority that might have meaning to the document author.

        The default relationship, if no other is given, is void.  Use
        this attribute only if the href attribute is present.
        """
        return self.attributes['rel'].value

    @rel.setter
    def rel(self, v):
        self.attributes['rel'].value = v

    @property
    def shape(self):
        """ The shape of the associated hot spot. The specifications for
        HTML defines the values rect, which defines a rectangular
        region; circle, which defines a circular region; poly, which
        defines a polygon; and default, which indicates the entire
        region beyond any defined shapes.
        """
        return self.attributes['shape'].value

    @shape.setter
    def shape(self, v):
        self.attributes['shape'].value = v

class colgroups(elements):
    """ A class used to contain a collection of ``colgroup`` elements."""

class colgroup(element):
    """ The <colgroup> HTML element defines a group of columns within a
    table.
    """
    @property
    def span(self):
        """ This attribute contains a positive integer indicating the
        number of consecutive columns the <colgroup> element spans. If
        not present, its default value is 1.
        """
        return self.attributes['span'].value

    @span.setter
    def span(self, v):
        self.attributes['span'].value = v

class iframes(elements):
    """ A class used to contain a collection of ``iframe`` elements."""

class iframe(element):
    """ The <iframe> HTML element represents a nested browsing context,
    embedding another HTML page into the current one.
    """
    @property
    def csp(self):
        return self.attributes['csp'].value

    @csp.setter
    def csp(self, v):
        """ A Content Security Policy enforced for the embedded
        resource. See HTMLIFrameElement.csp for details.
        """
        self.attributes['csp'].value = v

    @property
    def referrerpolicy(self):
        """ Indicates which referrer to send when fetching the frame's
        resource.
        """
        return self.attributes['referrerpolicy'].value

    @referrerpolicy.setter
    def referrerpolicy(self, v):
        self.attributes['referrerpolicy'].value = v

    @property
    def loading(self):
        """ Indicates how the browser should load the iframe, eagor or
        lazy.
        """
        return self.attributes['loading'].value

    @loading.setter
    def loading(self, v):
        self.attributes['loading'].value = v

    @property
    def srcdoc(self):
        """ Inline HTML to embed, overriding the src attribute. If a
        browser does not support the srcdoc attribute, it will fall back
        to the URL in the src attribute.
        """
        return self.attributes['srcdoc'].value

    @srcdoc.setter
    def srcdoc(self, v):
        self.attributes['srcdoc'].value = v

    @property
    def height(self):
        """ The height of the frame in CSS pixels. Default is 150."""
        return self.attributes['height'].value

    @height.setter
    def height(self, v):
        self.attributes['height'].value = v

    @property
    def src(self):
        """ The URL of the page to embed. Use a value of about:blank to
        embed an empty page that conforms to the same-origin policy.
        Also note that programmatically removing an <iframe>'s src
        attribute (e.g. via Element.removeAttribute()) causes
        about:blank to be loaded in the frame in Firefox (from version
        65), Chromium-based browsers, and Safari/iOS.
        """
        return self.attributes['src'].value

    @src.setter
    def src(self, v):
        self.attributes['src'].value = v

    @property
    def importance(self):
        """ Priority Hints can be set for resources in HTML by
        specifying an importance attribute on a <script>, <img>, or
        <link> element (though other elements such as <iframe> may see
        support later). 
        
        https://developers.google.com/web/updates/2019/02/priority-hints
        """
        return self.attributes['importance'].value

    @importance.setter
    def importance(self, v):
        self.attributes['importance'].value = v

    @property
    def allow(self):
        """ Specifies a feature policy for the <iframe>. The policy
        defines what features are available to the <iframe> based on the
        origin of the request (e.g. access to the microphone, camera,
        battery, web-share API, etc.).
        """
        return self.attributes['allow'].value

    @allow.setter
    def allow(self, v):
        self.attributes['allow'].value = v

    @property
    def name(self):
        """ A targetable name for the embedded browsing context. This
        can be used in the target attribute of the <a>, <form>, or
        <base> elements; the formtarget attribute of the <input> or
        <button> elements; or the windowName parameter in the
        window.open() method.
        """
        return self.attributes['name'].value

    @name.setter
    def name(self, v):
        self.attributes['name'].value = v

    @property
    def width(self):
        """ The width of the frame in CSS pixels. Default is 300.
        """
        return self.attributes['width'].value

    @width.setter
    def width(self, v):
        self.attributes['width'].value = v

    @property
    def sandbox(self):
        """ Applies extra restrictions to the content in the frame. The
        value of the attribute can either be empty to apply all
        restrictions, or space-separated tokens to lift particular
        restrictions.
        """
        return self.attributes['sandbox'].value

    @sandbox.setter
    def sandbox(self, v):
        self.attributes['sandbox'].value = v

class pres(elements):
    """ A class used to contain a collection of ``pre`` elements."""

class pre(element):
    """ The <pre> HTML element represents preformatted text which is to
    be presented exactly as written in the HTML file. The text is
    typically rendered using a non-proportional, or "monospaced, font.
    Whitespace inside this element is displayed as written.
    """
    @property
    def col(self):
        """ Contains the preferred count of characters that a line
        should have. It was a non-standard synonym of width. To achieve
        such an effect, use CSS width instead.
        """
        return self.attributes['col'].value

    @col.setter
    def col(self, v):
        self.attributes['col'].value = v

    @property
    def width(self):
        """ Contains the preferred count of characters that a line
        should have. Though technically still implemented, this
        attribute has no visual effect; to achieve such an effect, use
        CSS width instead.
        """
        return self.attributes['width'].value

    @width.setter
    def width(self, v):
        self.attributes['width'].value = v

    @property
    def wrap(self):
        """ Is a hint indicating how the overflow must happen. In modern
        browser this hint is ignored and no visual effect results in its
        present; to achieve such an effect, use CSS white-space instead.
        """
        return self.attributes['wrap'].value

    @wrap.setter
    def wrap(self, v):
        self.attributes['wrap'].value = v


class strongs(elements):
    """ A class used to contain a collection of ``strong`` elements."""

class strong(element):
    """ The <strong> HTML element indicates that its contents have
    strong importance, seriousness, or urgency. Browsers typically
    render the contents in bold type.
    """

class ss(elements):
    """ A class used to contain a collection of ``s`` elements."""

class s(element):
    """ The HTML <s> element renders text with a strikethrough, or a
    line through it. Use the <s> element to represent things that are no
    longer relevant or no longer accurate. However, <s> is not
    appropriate when indicating document edits; for that, use the <del>
    and <ins> elements, as appropriate.

    https://developer.mozilla.org/en-US/docs/Web/HTML/Element/s
    """

class ems(elements):
    """ A class used to contain a collection of ``em`` elements."""

class em(element):
    """ The HTML <em> element which marks text that has stress emphasis.
    This element can be nested, with each level of nesting
    indicating a greater degree of emphasis. 

    See: https://developer.mozilla.org/en-US/docs/Web/HTML/Element/em
    """

class is_(elements):
    """ A class used to contain a collection of ``i`` elements."""

class i(element):
    """ The HTML <i> element represents a range of text that is set off
    from the normal text for some reason. Some examples include
    technical terms, foreign language phrases, or fictional character
    thoughts. It is typically displayed in italic type.

    https://developer.mozilla.org/en-US/docs/Web/HTML/Element/i
    """

class bs(elements):
    """ A class used to contain a collection of ``i`` elements."""

class b(element):
    """ The HTML Bring Attention To element (<b>) is used to draw the
    reader's attention to the element's contents, which are not
    otherwise granted special importance. This was formerly known as the
    Boldface element, and most browsers still draw the text in boldface.
    However, you should not use <b> for styling text; instead, you
    should use the CSS font-weight property to create boldface text, or
    the <strong> element to indicate that text is of special importance.

    https://developer.mozilla.org/en-US/docs/Web/HTML/Element/b
    """

class divs(elements):
    """ A class used to contain a collection of ``div`` elements."""

class div(element):
    """ The HTML Content Division element (<div>) is the generic
    container for flow content. It has no effect on the content or
    layout until styled using CSS.
    """

class spans(elements):
    """ A class used to contain a collection of ``span`` elements."""

class span(element):
    """ The <span> HTML element is a generic inline container for
    phrasing content, which does not inherently represent anything. It
    can be used to group elements for styling purposes (using the class
    or id attributes), or because they share attribute values, such as
    lang. It should be used only when no other semantic element is
    appropriate. <span> is very much like a <div> element, but <div> is
    a block-level element whereas a <span> is an inline element.
    """

class mains(elements):
    """ A class used to contain a collection of ``main`` elements."""

class main(element):
    """ The <main> HTML element represents the dominant content of the
    <body> of a document. The main content area consists of content that
    is directly related to or expands upon the central topic of a
    document, or the central functionality of an application.
    """

class dls(elements):
    """ A class used to contain a collection of ``dl`` elements."""

class dl(element):
    """ The HTML <dl> element represents a description list. The element
    encloses a list of groups of terms (specified using the <dt>
    element) and descriptions (provided by <dd> elements). Common uses
    for this element are to implement a glossary or to display metadata
    (a list of key-value pairs).
    """

class dts(elements):
    """ A class used to contain a collection of ``dt`` elements."""

class dt(element):
    """ The HTML <dt> element specifies a term in a description or
    definition list, and as such must be used inside a <dl> element. It
    is usually followed by a <dd> element; however, multiple <dt>
    elements in a row indicate several terms that are all defined by the
    immediate next <dd> element.
    """

class dds(elements):
    """ A class used to contain a collection of ``dd`` elements."""

class dd(element):
    """ The HTML <dd> element provides the description, definition, or
    value for the preceding term (<dt>) in a description list (<dl>).
    """

    @property
    def nowrap(self):
        """ If the value of this attribute is set to yes, the definition
        text will not wrap. The default value is no.
        """
        return self.attributes['nowrap'].value

    @nowrap.setter
    def nowrap(self, v):
        self.attributes['nowrap'].value = v

class codes(elements):
    """ A class used to contain a collection of ``code`` elements."""

class code(element):
    """ The <code> HTML element displays its contents styled in a
    fashion intended to indicate that the text is a short fragment of
    computer code. By default, the content text is displayed using the
    user agent's default monospace font.
    """

class codeblocks(codes):
    """ A class used to contain a collection of ``codeblock`` elements."""

class codeblock(code):
    """ A subtype of `code` which represents a block of code instead of
    of inline code. The CSS class of `block' is added to distinguish it
    from inline <code> elements.

    CSS will be needed to cause preserve whitespace, e.g.,::

        code.block{
          white-space: pre
        }

    """

    # TODO Now that .html renders ugly, the whitespace is no longer an
    # issue. So the next step is to ensure that <pre> tags is added to
    # surround the <code> element. Also, `codeblock` should probably no
    # longer inherit from `code` anymore. If anything, it should inherit
    # from `pre`, but I don't know if that make much sense; maybe it
    # should just inherit from `element`. Not sure at this point. Also,
    # we don't need to add a CSS class called 'block' since 'pre > code'
    # would probably be equivalent to '.codeblock'.
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.classes += 'block'

class markdown(elements):
    """ Converts Markdown text into a DOM object::

        import dom

        # Parse markdown; md will contain the resulting DOM
        md = dom.markdown('''
            This is an H1
            ============

            This is an H2
            -------------
        ''')
        
        # Use DOM to get the <h1> and the <h2>
        assert md.first.elements.first.html == 'This is an H1'
        assert md.first.elements.second.html == 'This is an H2'

        # Note that the elements are the correct type
        assert type(md.first.elements.first) is dom.h1
        assert type(md.first.elements.second) is dom.h2
    """
    def __init__(self, text):
        """ Parse Markdown.

        :param: text str: The string of Markdown to parse.
        """
        super().__init__(self)

        # NOTE Importing mistune is slow - probably because it's upfront
        # compiling of regex expressions. Therefore, we import here to
        # improve startup performance.
        from mistune import Markdown

        # Use mistune.Markdown to convert to HTML. Then use dom.html to
        # convert to DOM. Append that DOM to self.
        self += html(Markdown()(dedent(text).strip()))

class selectors(entities.entities):
    """ Represents a selection group of CSS3 selectors. Selection groups
    are seperated by commas in CSS3 selector strings. For example, in
    the string::

        'p, div'

    the p would represent one entry of the selector group (represented
    by a ``selector`` object) and div would represent an second entry.
    """

    # NOTE that portions of this object model, namely the parts dealing
    # with tokenizing CSS strings, were copied from Ian Bicking's
    # 'cssselect' project (https://github.com/scrapy/cssselect).
    # Some modifications have been made to the code to better fit the
    # framework's standards. See LICENCE_cssselect.

    ''' Inner classes '''

    class token(tuple):
        """ A private class to represent the tokens in a CSS selector.
        """
        def __new__(cls, type, value, pos):
            """ Create the token instance.
            
            :param: type str: The type of token, e.g., 'IDENT', 'HASH',
            'STRING', 'NUMBER', etc.

            :param: value str: The token itself.

            :param: pos int: The zero-based position in the selectors
            string where the token occured.
            """
            obj = tuple.__new__(cls, (type, value))
            obj.pos = pos
            return obj

        def __repr__(self):
            """ Return a string representation of the token,
            """
            return "<%s '%s' at %i>" % (self.type, self.value, self.pos)

        # Create property objects for type and value
        type = property(operator.itemgetter(0))
        value = property(operator.itemgetter(1))

    class eof(token):
        """ A special type of token used to indicate that parsing has
        been completed.
        """
        def __new__(cls, pos):
            """ Create the token instance.
            """
            return selectors.token.__new__(cls, 'EOF', None, pos)

        def __repr__(self):
            """ Return a string representation of the token,
            """
            return '<%s at %i>' % (self.type, self.pos)

    ''' Class members '''

    cache = dict()
    def __init__(self, sel=None, cache=True, *args, **kwargs):
        """ Instantiate and parse the CSS3 selector string (sel).

        Note that selectors is a collection class. Consider the
        following CSS selector::

            p#pid, div.my-class

        The above represents two seperate selectors delinated by a
        comma. When parsing the above CSS selector, two `selector`
        objects wil be added to this collection. The first will be for 

            p#pid

        and the second will be for 

            div.my-class

        Of course, most selector strings will only have one selector
        object since most CSS selectors don't use a comma.
        """

        # NOTE on caching: Adding caching improved performance but not
        # that much. In the test suite, the "not" pseudoclass
        # instantiates the `selectors` object the most and it disables
        # caching because it mutates the `selectors`` object. I tried
        # cloning so 'not' could have it's own `selectors` object to
        # work with but cloning the entire selectors tree was just as
        # costly in terms of performance.
        super().__init__(*args, **kwargs)
        self._sel = sel.strip()

        # If cache, parse the CSS3 selector then cache self in the cache
        # dict.
        if cache:
            try:
                # Has it already been cached?
                sels = selectors.cache[self._sel]
            except KeyError:
                # The selector string hasn't been parsed and cached so
                # do that here.
                self._parse()
                selectors.cache[self._sel] = self
            else:
                # Add each of the `selector`` objects from the cached
                # ``selectors`` collection to self.
                for sel in sels:
                    self += sel
        else:
            # Sometimes we don't want to use a cached object,
            # particularly when we are mutating the selectors object.
            # See selector.pseudoclass.arguments.selectors.
            self._parse()

    def clone(self):
        """ Clone the entire selectors tree. 

        Note: currently not being used and probably doesn't work. The
        'parse' parameter should be changed to cache=False. Other than
        that, this clone method, and all the clone methods it invokes to
        clone the selectors tree, should work.
        """

        raise NotImplementedError('See note in docstring');
        sels = selectors(self._sel, parse=False)
        for sel in self:
            sels += sel.clone()
        return sels
    
    @staticmethod
    def tokenize(s):
        """ Tokenize a CSS selection string.
        """
        err = CssSelectorParseError

        # Set up regex
        class macros:
            unicode_escape = r'\\([0-9a-f]{1,6})(?:\r\n|[ \n\r\t\f])?'
            escape = unicode_escape + r'|\\[^\n\r\f0-9a-f]'
            string_escape = r'\\(?:\n|\r\n|\r|\f)|' + escape
            nonascii = r'[^\0-\177]'
            nmchar = '[_a-z0-9-]|%s|%s' % (escape, nonascii)
            nmstart = '[_a-z]|%s|%s' % (escape, nonascii)

        def compile(pattern):
            return re.compile(pattern % vars(macros), re.IGNORECASE)\
                    .match

        re_whitespace = compile(r'[ \t\r\n\f]+')
        re_number     = compile(r'[+-]?(?:[0-9]*\.[0-9]+|[0-9]+)')
        re_hash       = compile('#(?:%(nmchar)s)+')
        re_id         = compile('-?(?:%(nmstart)s)(?:%(nmchar)s)*')
        re_strbyquo = {
            "'": compile(r"([^\n\r\f\\']|%(string_escape)s)*"),
            '"': compile(r'([^\n\r\f\\"]|%(string_escape)s)*'),
        }

        sub_simple_esc = re.compile(r'\\(.)').sub
        sub_uni_esc = re.compile(macros.unicode_escape, re.I).sub
        sub_nl_esc =re.compile(r'\\(?:\n|\r\n|\r|\f)').sub

        # Same as r'\1', but faster on CPython
        replace_simple = operator.methodcaller('group', 1)

        # Define sum functions
        def replace_unicode(match):
            codepoint = int(match.group(1), 16)
            if codepoint > sys.maxunicode:
                codepoint = 0xFFFD
            return _unichr(codepoint)

        def unescape_ident(value):
            value = sub_uni_esc(replace_unicode, value)
            value = sub_simple_esc(replace_simple, value)
            return value

        # Begin interation over the selector string, yielding a token
        # object each time one is encounter
        pos = 0
        len_s = len(s)
        while pos < len_s:
            match = re_whitespace(s, pos=pos)
            if match:
                yield selectors.token('S', ' ', pos)
                pos = match.end()
                continue

            match = re_id(s, pos=pos)
            if match:
                value = sub_simple_esc(replace_simple,
                        sub_uni_esc(replace_unicode, match.group()))
                yield selectors.token('IDENT', value, pos)
                pos = match.end()
                continue

            match = re_hash(s, pos=pos)
            if match:
                value = sub_simple_esc(replace_simple,
                        sub_uni_esc(replace_unicode, match.group()[1:]))
                yield selectors.token('HASH', value, pos)
                pos = match.end()
                continue

            quote = s[pos]
            if quote in re_strbyquo:
                match = re_strbyquo[quote](s, pos=pos + 1)
                if not match:
                    raise err(
                        'Should have found at least an empty match',
                        pos=pos
                    )
                end_pos = match.end()
                if end_pos == len_s:
                    raise err('Unclosed string', pos=pos)
                if s[end_pos] != quote:
                    raise err('Invalid string', pos=pos)
                value = sub_simple_esc(replace_simple,
                        sub_uni_esc(replace_unicode,
                        sub_nl_esc('', match.group())))
                yield selectors.token('STRING', value, pos)
                pos = end_pos + 1
                continue

            match = re_number(s, pos=pos)
            if match:
                value = match.group()
                yield selectors.token('NUMBER', value, pos)
                pos = match.end()
                continue

            pos2 = pos + 2
            if s[pos:pos2] == '/*':
                pos = s.find('*/', pos2)
                if pos == -1:
                    pos = len_s
                else:
                    pos += 2
                continue

            yield selectors.token('DELIM', s[pos], pos)
            pos += 1

        if not pos:
            raise err('Falsy position')

        yield selectors.eof(pos)

    def _parse(self):
        """ Parse the CSS3 selector string provided by the constructor
        (``sel``)
        """

        ''' Validation '''

        # Assign to err to make lines shorter
        err = CssSelectorParseError
        badtrail = set(string.punctuation) - set(list(')]*'))
        badlead = '>+~'

        # Raise on empty selectors
        if not self._sel or not self._sel.strip():
            raise err('Empty selector')

        valid_identifier = re.compile('^[a-zA-Z\-_][a-zA-Z0-9\-_]')
        starts_with_hyphen_then_number = re.compile('^\-[0-9]')

        def demand_valid_identifiers(id):
            """ Raises a CssSelectorParseError if the identifier is
            invalid.

            :param id str: The identifier to test.

            """
            # NOTE See the following for official validation rules:
            # https://www.w3.org/TR/CSS21/syndata.html#value-def-identifier
            def throw():
                raise err('Invalid identifier', tok)

            if not valid_identifier.match(id):
                # Identifiers must start with a letter, - or _.
                throw()

            if id.startswith('--'):
                # if the first character is a hyphen, the second
                # character must2 be a letter or underscore, and the
                # name must be at least 2 characters long.
                throw()
                
            if starts_with_hyphen_then_number.match(id):
                # if the first character is a hyphen, the second
                # character must2 be a letter or underscore, and the
                # name must be at least 2 characters long.
                throw()

        def element(element):
            """ Create and return a new selector.element object given
            the `element`.

            :param: element str: An HTML element, presumably one found
            in a CSS selector. For example, 'p' is the first and only
            element found in the CSS selector 'p:lang(fr)'.
            """
            if not element.isalnum() and element != '*':
                raise ValueError('Elements must be alphanumeric')

            el = selector.element()
            el.element = element

            # Set the numeric value for the combinator 
            # (' ', '>', '+', # '~') that precedes the element.
            el.combinator = comb
            return el

        # Create and append the first selector. We will always have one
        # unless the CSS selector string is invalid.
        sel = selector()
        self += sel
        el = comb = attr = cls = pcls = args = None

        prev = None

        # Iterate over each token in the CSS selector string
        for tok in self.tokenize(self._sel):
            
            # If this is the last token (eof) break the loop, but first
            # check for unclosed tokens, e,g., 'input[name=username'
            if isinstance(tok, selectors.eof):
                if attr:
                    # e.g., '[foo=bar'
                    raise err('Attribute not closed', tok)

                if not el:
                    # e.g., 'a,b,'
                    raise err( 'Attribute not closed', tok)

                if prev.value in badtrail: 
                    # If the last token in the string is in the badtrail
                    # list
                    raise err(tok)

                if pcls and not pcls.hasvalidname:
                    # Raise error if we are using a pseudoclass with a
                    # bad name, e.g., ':not-a-pseudoclass()'
                    raise err(
                        'Invalid pseudoclass "%s"' % pcls.value, tok
                    )
                break

            if not prev and tok.value in badlead:
                # A bad leading token was found, e.g., "~div"
                raise err(tok)

            # If we are building pseudoclass selector arguments
            if args:
                if tok.value == ')':
                    # We are done with collecting the arguments so set
                    # args to None to indicate this.
                    args = None
                elif tok.type == 'HASH':
                    # If token type is a hash (a id selectors such a
                    # #my-id), prepend a #
                    args += '#' + tok.value
                    continue
                elif tok.type != 'S':
                    # If token type is not whitespace (S), append token.
                    args += tok.value
                    continue

            # If the token is a CSS selector identifier (names of
            # elements, names of pseudoclasses, etc.)
            if tok.type == 'IDENT':

                # If we are in an element (div, p, etc) selector
                if el:
                    # If we are in an attribute ([key=value]) selector
                    if attr:
                        # Set key and value of attribute. Note that some
                        # attribute selectors only have a key because
                        # they are selecting for boolean attributes:
                        #
                        #     <p hidden lang="en">
                        #
                        # would be match by
                        #
                        #     p[hidden] or p[lang=en]
                        #
                        # The first selector would have 'hidden' as the
                        # key.
                        for attr1 in ['key', 'value']:
                            if getattr(attr, attr1) is None:
                                setattr(attr, attr1, tok.value)
                                break
                        else:
                            # NOTE We probably will never get here, but
                            # just in case...
                            CssSelectorParseError(tok)
                    
                    # If we are in a class (.my-class) selector
                    elif cls:
                        cls.value = tok.value

                    # If we are in a pseudoclass (:lang()) selector 
                    elif pcls:
                        pcls.value = tok.value

                # Else we are not in an element selector we will want to
                # create a new one baised on this this IDENT token.
                else:
                    try:
                        # Create the element selector
                        el = element(tok.value)
                    except Exception as ex:
                        msg = (
                           str(ex) +
                           '\nYou may have forgotten brackets around '
                           'an attribute selector.'
                        )
                        raise err(msg, tok)
                    sel.elements += el

            # If the token type is a string, such a the string value of
            # of an attribute selector: p[name="string token"]
            elif tok.type == 'STRING':
                if attr:
                    attr.value = tok.value

            # If the token is a hash, i.e., an id selector: p#my-hash
            elif tok.type == 'HASH':
                # If we are in a class or attribute selector, a hash
                # token would be an error.
                if cls or attr:
                    raise err(tok)
                    
                # If we aren't in an element, then the universal
                # selector is implied - #my-hash is the same as
                # *#my-hash
                if not el:
                    el = element('*')
                    sel.elements += el

                if not el.id:
                    # Raise exception if the token is not a valid
                    # identifier
                    demand_valid_identifiers(tok.value)

                # Set the token's value to the element's id attribute
                el.id = tok.value

            # If the token is whitespace
            elif tok.type == 'S':
                # If we are in an element
                if el:
                    # If we have no args
                    if not args:
                        # Take us out of the element
                        el = None

                        # Set the combinator to Descendant (the
                        # default combinator when whitespace is used
                        # instead of < + or ~)
                        comb = selector.element.Descendant

                # If we are in a class selector, but we have whitespace,
                # there must be a syntax error with the CSS selector,
                # e.g., 'p . myclass' (this might have been a typo for
                # 'p .myclass' or 'p.myclass').
                if cls and not cls.value:
                    raise err(tok)
                    
            elif tok.type == 'NUMBER':
                # Interpet numbers as identifiers and raise an exception
                # if the are invalid (I think numbers are always invalid)
                demand_valid_identifiers(tok.value)

            # If the token is a delimiter (a special character forming
            # the CSS selector such as the brackets for an attribute
            # selector)
            elif tok.type == 'DELIM':    
                v = tok.value

                # If we are in an element
                if el:
                    # If we ar not in an attribute selector and the
                    # delimiter is a combinator
                    if not attr and v in '>+~':
                        # The combinator indicates we are no longer in an
                        # element
                        el = None

                        # Get the numeric value for the combinator
                        comb = selector.element.str2comb(v)

                    # If we aren't in an attribute, pseudoclass or class
                    # selector
                    elif not (attr or pcls or cls):
                        # Raise if invalid delimiter
                        if v not in ''.join('*[:.,'):
                            raise err(tok)

                    # If we are in a class selector but there is no
                    # value for the class selector, raise because it's
                    # syntax error - consider 'id.--foo'
                    if cls and cls.value is None:
                        raise err(tok)

                    # If we are in a pseudoclasses selector but there is
                    # no value for the class selector, raise because
                    # it's syntax error - consider 'a:,b'
                    if pcls and pcls.value is None:
                        raise err(tok)

                # Else we aren't in an element
                else:
                    # If the token is a conbinator
                    if v in '>+~':
                        # Get numeric value of combinator
                        comb = selector.element.str2comb(v)

                    # Else token is not combinator
                    else:
                        if v not in '*[:.':
                            # Syntax error - consider 'a & b'
                            raise err(tok)

                # We should only see a ] if we are in an attribute
                if not attr and v == ']':
                    raise err(tok)

                # A comma indicates a new selector - consider
                # 'p.somclass, div.someclass'
                if tok.value == ',':
                    # Create and append the selector to this collection
                    sel = selector()
                    self += sel

                    # args stores the arguments for pseudoclasses. See
                    # selector.pseudoclass.arguments.
                    args = None

                    # An instance of selector.attribute. Stores
                    # attributes collected during parsing.
                    attr = None

                    el = comb = cls = pcls = None

                # If we are in an attribute selector
                if attr:
                    # If we are closing the attribute selector
                    if tok.value == ']':

                        # Make sure it's valid
                        if attr.operator and attr.value is None:
                            raise err(tok)

                        if attr.key is None:
                            raise err(tok)

                        # Indicating we are no longer in an attribute
                        # selector
                        attr = None

                    # If we are trying to open an attribute selector
                    # while we have one open
                    elif tok.value == '[':
                        raise err('Attribute already opened', tok)

                    # Else we are building the attribute selector
                    else:
                        # Stringify operator
                        if attr.operator is None:
                            attr.operator = ''

                        # Concatentate operater with token
                        attr.operator += tok.value
                        op = attr.operator

                        # Demand attribute is valid at this point
                        if len(op) == 1:
                            if attr.key is None:
                                raise err(tok)
                            if op not in ''.join('=~|*^$'):
                                raise err(tok)
                        elif len(op) == 2:
                            if op[1] != '=':
                                raise err(tok)
                        elif len(op) > 2:
                            raise err(tok)

                # Else we are not in an attirbute
                else:
                    # If tok is [, we are starting an attribute
                    # selector (p[key=val]). If we are not in an element, create a
                    # univeral selector element to attach the attribute
                    # selector to because [key=val] implies *[key=val]
                    if tok.value == '[':
                        if not el:
                            # The universal selector was implied
                            # (.[foo=bar]) so create it.
                            el = element('*')
                            sel.elements += el

                        attr = selector.attribute()
                        el.attributes += attr

                    # Universal selector
                    elif tok.value == '*':
                        el = selector.element()
                        el.element = '*'
                        el.combinator = comb
                        sel.elements += el

                # If token is . we must me starting a class selector
                # (.my-class)
                if tok.value == '.':
                    # If we are not in an element, create a universal
                    # one (.my-class is equivalent to *.myclass)
                    if not el:
                        # The universal selector was implied (.my-class)
                        # so create it.
                        el = element('*')
                        sel.elements += el
                    cls = selector.class_()
                    el.classes += cls

                # If tok is : we must be starting a pseudoclass
                # (p:lang(fr))
                elif tok.value == ':':
                    # If we are not in an element, the universal
                    # element is implied, so create it (:lang(fr))
                    if not el:
                        el = element('*')
                        sel.elements += el
                    pcls = selector.pseudoclass()
                    el.pseudoclasses += pcls
                    
                    # Since we are in a new pseudoclass, we are out of
                    # any other simple selector so nullify those
                    # references.
                    comb = attr = cls = args = None

                # If the token is an open paran, we are in a
                # pseudoclass's arguments. Set args to indicate that so
                # the next iteration will know to start collecting
                # arguments.
                elif tok.value == '(':
                    args = pcls.arguments
                elif tok.value in ('+',  '-'):
                    if args:
                        # NOTE We don't appear to ever get here
                        args += tok.value

            prev = tok

        # Raise error if any of the selectors we added during parsing
        # are invalid
        self.demand()

    def demand(self):
        """ Raise error if self is invalid
        """
        for sel in self:
            sel.demand()

    def match(self, els):
        """ Given a collection of elements (els), return the subset
        which is matched by any of the selector objects in this
        selectors collection.

        This is the main entry point for performing a CSS selection on
        an DOM object. Here is a demonstration of the match method being
        called.

            # Build DOM object
            div = dom.div()

            # Add some <p>s to the <div>
            div += dom.p()
            div += dom.p()

            # Create a selectors object that selects just the <p>s
            sels = dom.selectors('p')

            # Use the selectors object to select just the <p>s
            els = sel.match(div)

            # Demonstrate that we got just the <p>s
            assert els.count == 2
            assert els.first is div.first
            assert els.second is div.second

        Note that this is the unconventional, longhanded way to perform
        a selection. It would have been better to pass a selector string
        to the div indexer like this::

            els = div['p']

        The above creates the selectors object and calls the match
        method behind the scenes.

        :param: els dom.elements: Any collection of elements. This
        includes hierarchically constructed collections, i.e., DOM
        objects.
        """
        r = elements()

        # For each selector object in this collection
        for sel in self:
            # Call that selector object's match method

            # FIXME:9aec36b4 It's possible for two or more selectors to
            # match the same element. In that case, r gets the same
            # element twice.  For example, if `els` is a DOM with one
            # <section> tag in it, then calling this method like this:
            #
            #     els = sel.match('section, section, section')
            #
            # adds the same <section> element three times:
            #
            #     assert els.count == 3
            #     assert els.first is els.second
            #     assert els.second is els.third
            #
            # We should only add unique elements, possible using the &=
            # operator here instead of the += operator.

            r += sel.match(els)

        return r

    def __repr__(self):
        """ A string representation of this selectors object. 
        """
        return ', '.join(str(x) for x in self)

    def __str__(self):
        """ A string representation of the selectors object. 
        """
        return repr(self)

class selector(entities.entity):
    """ Represents a single selector. In the following example, two
    ``selector`` objects would be created and appended to the
    ``selectors`` class::

        p#my-id, p#my-other-id

    Usually, only one selector object needs to be created and appended
    to the ``selectors`` collection object because, obviously, CSS
    selectors only occasionally have commas.
    """

    ''' Inner classes '''

    class _simples(entities.entities):
        """ An inner class representing a collection of ``simples``.
        """
        def __init__(self, *args, **kwargs):
            self.element = kwargs.pop('el')
            super().__init__(*args, **kwargs)

        def clone(self, el):
            """ Create and return an object based on the state of self.
            """
            cls = type(self)
            smps = cls(el=el)
            for smp in self:
                smps += smp.clone()
            return smps

        def __str__(self):
            return repr(self)

        def __repr__(self):
            return ' '.join(str(x) for x in self)

        def __iadd__(self, smp):
            super().__iadd__(smp)
            smp.element = self.element
            return self

    class simple(entities.entity):
        """ The abstract class for the different types of selectors in a
        CSS3 selector string such as "type" and "universal" selectors
        (``selector.element``), attribute selectors
        (``selector.attribute``), class selectors (``selector.class_``),
        and pseudoclass selectors (``selector.pseudoclass``).

        See
        https://www.w3.org/TR/2011/REC-css3-selectors-20110929/#simple-selectors-dfn
        for terminological explanation. 

        Note that ID selectors don't have their own class. The id
        attribute of selector.element is used for selecting elements
        based on id.
        """
        def __init__(self):
            self.element = None

        def __str__(self):
            return repr(self)

        def clone(self):
            raise NotImplementedError(
                'Must be implemented by subclass'
            )

    class elements(entities.entities):
        """ A collection of ``selector.element`` objects.
        """
        def demand(self):
            """ Raise error if self is invalid
            """
            for el in self:
                el.demand()

        def __repr__(self):
            """ A string representation of this collection.
            """
            r = str()
            for i, el in self.enumerate():
                if i:
                    r += ' '
                r += str(el)
            return r

    class element(entities.entity):
        """ Represents the element/tag portions of a selector string,
        along with its ``simple`` constiuents such as its attribute,
        class and pseudoclass selectors. The preceding combinator for
        the element is captured here as well::

        p.my-class, p[key-value].my-other-class

        The above CSS selector would be parsed down to two different
        element selectors. The first would be the 'p' element (stored in
        the `element` property) and it's `classes` collection. The next
        would be another p element with the attribute selector stored in
        the `attributes` collection and the class selector stored in the
        `classes` collection.
        """

        # Constants representing the various selectors. See
        # https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_Selectors#combinators
        Descendant         =  0  # Default (represented by whitespace)
        Child              =  1  # Represented by >
        NextSibling        =  2  # Represented by +
        SubsequentSibling  =  3  # Represents by ~

        def __init__(self):
            # A string representing the tag name
            self.element        =  None

            # Representss which combinator preceded the element
            self.combinator     =  None

            # A collection of attribute selectors 
            self.attributes     =  selector.attributes(el=self)

            # A collection of class selectors 
            self.classes        =  selector.classes(el=self)

            # A collection of pseudoclass selectors 
            self.pseudoclasses  =  selector.pseudoclasses(el=self)

            # The id portion of an element selection (p#my-id)
            self.id             =  None

        def clone(self):
            """ Create and return an object based on the state of self.
            """
            el = selector.element()
            el.element = self.element
            el.combinator = self.combinator
            el.attributes += self.attributes.clone(el=el)
            el.classes += self.classes.clone(el=el)
            el.pseudoclasses += self.pseudoclasses.clone(el=el)
            el.id = self.id
            return el

        @staticmethod
        def comb2str(comb):
            """ A static method to return the string representation of
            the combinator.

            :param: comb int: One of the combinator constance (see
            above).
            """
            return [' ', '>', '+', '~'][comb]

        @staticmethod
        def str2comb(comb):
            """ A static method to return the int representation of
            the combinator.

            :param: comb str: A combinator, e.g., ' ', '>', '+', '~'.
            """
            return [' ', '>', '+', '~'].index(comb)

        def match(self, els):
            """ Returns that subset ef the dom.element objects in `els`
            which match this CSS selector.

            :param: els dom.elements|dom.element: A dom.element or a
            collection of dom.elements (i.e, a DOM object) to be
            matched.
            """
            if isinstance(els, element):
                return bool(self.match([els]).count)
            
            if els is None:
                return False

            r = elements()

            for el in els:
                # Test the element,i.e., tag name
                if self.element.lower() not in ('*', el.tag):
                    continue

                # Test the classes collection against the given element
                if not self.classes.match(el):
                    continue

                # Test the attributes collection against the given
                # element
                if not self.attributes.match(el):
                    continue

                # Test the pseudoclasses collection against the given
                # element
                if not self.pseudoclasses.match(el):
                    continue

                # Test the element's id
                if self.id and self.id != el.id:
                    continue

                r += el

            return r

        def demand(self):
            """ Raise error if self is invalid
            """
            ess = self.classes, self.attributes, self.pseudoclasses

            for es in ess:
                es.demand()

        @property
        def str_combinator(self):
            """ Return the string representation of the combinator.
            """
            return self.comb2str(self.combinator)

        def __repr__(self):
            """ A string representation of this element selector.
            """
            r = str()

            # Combinator
            if self.combinator not in (None, selector.element.Descendant):
                r += self.str_combinator + ' '

            # Tag
            if self.element is not None:
                r += self.element

            # Id
            if self.id is not None:
                r += '#' + self.id

            # Attributes
            if self.attributes.count:
                r += str(self.attributes)

            # Classes
            if self.classes.count:
                r += str(self.classes)

            # Pseudoclasses
            if self.pseudoclasses.count:
                r += str(self.pseudoclasses)

            return r

    ''' Members of `selector` '''

    def __init__(self):
        """ Create a new ``selector`` object assigning it an empty
        ``selector.elements`` collection.
        """
        self.elements = selector.elements()

    def clone(self):
        """ Create and return an object based on the state of self.
        """
        sel = selector()
        for el in self.elements:
            sel.elements += el.clone()
        return sel

    def match(self, els, el=None, smps=None):
        """ Of the elements in the `els` collection, return a new
        elements collection containing those elements that match this
        selector.

        :param: els dom.elements: A collection of elements, usually a
        DOM object.
        """
        # Get the last element. We match the next element depending on
        # the combinator. For example, if we have a Descendant
        # combinator:
        #
        #     div p
        #
        # We want to first find all the <p> elements - the *last*
        # element - in `els`. For each of the <p> elements we find, we
        # can use it's ``ancestors`` property to determine if it is
        # under a div. Similar logic is used for the other combinators.
        last = self.elements.last

        # Recursively match els' children
        els1 = last.match(els.getchildren())

        # Create a collection of elements to remove later. These will be
        # the elements that were match by the above match but ended up
        # being rejected because preceding simple selectors didn't
        # match. So if we have 'div p', all the <p>s would have been
        # selected, and the <p>s that weren't under a <div> would be
        # added to rms to be removed.
        rms = elements()

        # For each of the elements matched above
        for el1 in els1:
            comb = last.combinator
            orig = el1

            # For each element above the last element in reverse order
            for i, smp in enumerate(self.elements[:-1].reversed()):

                # If combinator is Descendant (whitespace)
                if comb in (selector.element.Descendant, None):
                    for i, an in el1.ancestors.enumerate():
                        if smp.match(an):
                            el1 = an
                            break
                    else:
                        rms += orig
                        break

                # Else if combinator is Child (>)
                elif comb == selector.element.Child:
                    an = el1.parent
                    if smp.match(an):
                        el1 = an
                    else:
                        rms += orig
                        break

                # Else if combinator is NextSibling (+)
                elif comb == selector.element.NextSibling:
                    if smp.match(el1.previous):
                        el1 = el1.previous
                    else:
                        rms += orig
                        break

                # Else if combinator is SubsequentSibling (~)
                elif comb == selector.element.SubsequentSibling:
                    els2 = selectors(repr(self.elements[:-1 - i])).match(els)
                    for precs in el1.preceding:
                        if precs in els2:
                            el1 = precs
                            break
                    else:
                        rms += orig
                        break
                else:
                    raise ValueError('Invalid combinator')

                comb = smp.combinator

        els1.remove(rms)
        
        return els1

    def demand(self):
        """ Raise error if this selector is invalid.
        """
        self.elements.demand()

    def __repr__(self):
        """ Return a string representation of this selector.
        """
        return repr(self.elements)

    def __str__(self):
        """ Return a string representation of this selector.
        """
        return repr(self)

    class attributes(_simples):
        """ Represents a collection of selector.attribute objects.
        """
        def __repr__(self):
            """ Return a string representation of this attributes
            selector collection.
            """
            return ''.join(str(x) for x in self)

        def match(self, el):
            """ Returns True if el matechs all the attribute selectors
            in this collection.
            """
            return all(x.match(el) for x in self)

        def demand(self):
            """ Raise error if this attribute selector collection is
            invalid.  Although... currently there is nothing that would
            indicate that it is invalid.
            """
            pass

    class attribute(simple):
        """ Represents an attribute selector.

        In CSS selector strings, attribute selectors are denoted by
        brackets::

            p[name=myname]

        In the above, the attribute selector would capture the string
        'name' in self.key, the operator '=' in self.operator, and
        'myname' in self.value.
        """
        def __init__(self):
            """ Create the attribute selector.
            """
            self.key       =  None
            self.operator  =  None
            self.value     =  None

        def clone(self):
            """ Create and return an object based on the state of self.
            """
            attr = selector.attribute()
            attr.key       =  self.key
            attr.operator  =  self.operator
            attr.value     =  self.value
            return attr

        def __repr__(self):
            """ Return a string representation of this attribute
            selector.
            """
            k   =  self.key       or  ''
            op  =  self.operator  or  ''
            v   =  self.value     or  ''
            return '[%s%s%s]' % (k, op, v)

        def match(self, el):
            """ Returns true if the dom.element 'el' has an attribute
            that matches this selector, False otherwise.

            :param: el dom.element: A dom.element to test the selector
            against.
            """
            for attr in el.attributes:
                if attr.name.lower() == self.key.lower():
                    op = self.operator
                    if op is None:
                        if not self.value:
                            return True

                    elif op == '=':
                        if attr.value == self.value:
                            return True

                    elif op == '~=':
                        if self.value in attr.value.split():
                            return True

                    elif op == '^=':
                        if attr.value.startswith(self.value):
                            return True

                    elif op == '$=':
                        if attr.value.endswith(self.value):
                            return True

                    elif op == '*=':
                        if self.value in attr.value:
                            return True

                    elif op == '|=':
                        els = attr.value.split('-')
                        for i in range(len(els)):
                            v = '-'.join(els[0:i+1])
                            if self.value == v:
                                return True

                        els = attr.value.split()
                        if len(els) and self.value == els[0]:
                            return True

            return False

    class classes(_simples):
        """ A collection of ``class_`` selectors.
        """
        def __repr__(self):
            """ Returns a string representation of this class selectors.
            """
            return ''.join(str(x) for x in self)

        def match(self, el):
            """ Returns True if all the class selectors in this
            collection match el.

            :param: el dom.element: A DOM element to test.
            """
            return all(x.match(el) for x in self)

        def demand(self):
            """ Raise an exception if self is invalid.
            """
            # NOTE There are no tests for this at the moment. We just
            # need to implement the method so it conforms to the
            # interface.

    class class_(simple):
        """ Represents a class selector.

        In the expression:

            p.my-class

        The string 'my-class' would be assigned to self.value.
        self.match would return true for any element that has that
        class.
        """
        def __init__(self):
            """ Create the class selector.
            """
            self.value = None

        def clone(self):
            """ Create and return an object based on the state of self.
            """
            cls = selector.class_()
            cls.value = self.value
            return cls

        def __repr__(self):
            """ Returns a string representation of this class selector.
            """
            return '.' + self.value

        def match(self, el):
            """ Return True if el has a class that matches this class
            selector, False otherwise.

            :param: el dom.element: The element againt which the class
            selector is tested.
            """
            return self.value in el.classes

    class pseudoclasses(_simples):
        """ Represents a collection of ``pseudoclass`` selectors.
            :v
        """
        def __repr__(self):
            """ Returns a string representation of this pseudoclasses
            collection.
            """
            return ''.join(str(x) for x in self)

        def match(self, el):
            """ Return True if el has a pseudoclass that matches this
            pseudoclass selector, False otherwise.

            :param: el dom.element: The element againt which the class
            selector is tested.
            """
            return all(x.match(el) for x in self)

        def demand(self):
            """ Raise an exception if this pseudoclasses collection
            contains a pseudoclass that is invalid.
            """
            for pcls in self:
                pcls.demand()

    class pseudoclass(simple):
        """ Represents a tree-structural pseudoclass selector.

        Consider:
            
            p:first-child

        In the above CSS selector, the string 'first-child' would
        be assigned to self.value.

        :abbr: pcls
        """
        validnames = (
            'root',         'nth-child',         'nth-last-child',
            'nth-of-type',  'nth-last-of-type',  'first-child',
            'last-child',   'first-of-type',     'last-of-type',
            'only-child',   'only-of-type',      'empty',
            'not',          'lang',
        )

        ''' Inner classes '''

        class arguments(element):
            """ Represents a pseudoclasses arguments.

            Consider:
                    
                    li:nth-child(2n+0)

            In the above example, the nth-child pseudclass would have
            two arguments: 2 and 0. 2 would be assigned to self.a and 0
            would be assigned to self.b.

            :abbr: args
            """
            def __init__(self, pcls):
                """ Create the arguments object.

                :param: pcls selector.pseudoclass: The pseudoclass to
                which this argument object belongs.
                """
                self.string       =  str()
                self._a           =  None
                self._b           =  None
                self.pseudoclass  =  pcls

            def clone(self, pcls):
                """ Create and return an object based on the state of self.
                """
                args = selector.pseudoclass.arguments(pcls)
                args.string = self.string
                args._a = self._a
                args._b = self._b
                return args

            def __iadd__(self, str):
                """ Append to the text of the argument string.

                :param: str str: The string to append to self.string.
                """
                self.string += str
                return self

            @property
            def a(self):
                """ Returns the first argument in the arguments object:

                Given: 

                    li:nth-child(2n+0)

                2 is returned.
                """
                # Ensure self.string has been parsed.
                self._parse()
                return self._a

            @property
            def b(self):
                """ Returns the second argument in the arguments object:

                Given: 

                    li:nth-child(2n+0)

                0 is returned.
                """
                # Ensure self.string has been parsed.
                self._parse()
                return self._b

            @property
            def c(self):
                """ Return the argument to the lang pseudoclass.

                Given:
                        
                    p.lang(fr)

                'fr' is returned
                """
                if self.pseudoclass.value != 'lang':
                    raise NotImplementedError(
                        'Only lang pseudoclass has C argument'
                    )
                return self.string

            @property
            def selectors(self):
                """ When this ``arguments`` object  represents a :not
                pseudoclass, this method returns a selector object for
                the selector being negatively selected for. For
                example, given the following CSS selector::

                    :not(p)

                The 'p' is the argument to the :not pseudoclass. This
                property would create a selector based on that argument,
                and return it.

                `None` is returned if the pseudoclass is not a :not
                pseudoclass.
                """
                if self.pseudoclass.value.lower() != 'not':
                    return None

                # For :not() pseudoclass, parse the arguments to
                # :not() like any other selector. 
                sels = selectors(self.string, cache=False)

                # The parser will add a universal selector (*) to each
                # simple selector. 
                el = self.pseudoclass.element.element
                if el != '*':
                    for sel in sels:
                        for el1 in sel.elements:
                            el1.element = el

                return sels

            def _parse(self):
                """ Parses the value held in self.string (which contains
                the pseudoclasses arguments as developed by the author of the CSS
                selector), into values for a and b @property's.
                """
                # Store in err for concision
                err = CssSelectorParseError

                # The argument to :lang pseudoclasses (the 'fr' in
                # :lang(fr), for example) is returned by the c property.
                # No parsing needs to be done for :lang.
                if self.pseudoclass.value == 'lang':
                    return

                # Init
                a = b = None

                # Get the str to parse
                s = self.string

                # If the argument is 'odd', e.g., nth-child(odd), set
                # a,b=2,1 because nth-child(odd) is equivalent to
                # nth-child(2n+1)
                if s.lower() == 'odd':
                    a, b = 2, 1

                # Elif the argument is 'even', e.g., nth-child(even), set
                # a,b=2,0 because nth-child(even) is equivalent to
                # nth-child(2n+0)
                elif s.lower() == 'even':
                    a, b = 2, 0
                elif len(s) == 1:
                    # nth-child(n) is equivalent to li:nth-child(1n+0)
                    if s.lower() == 'n':
                        a, b = 1, 0
                    else:
                        try:
                            i = int(s)
                        except ValueError:
                            pass
                        else:
                            # nth-child(2) is equivalent to nth-child(0n+2)
                            a, b = 0, i
                elif len(s) == 2:
                    try:
                        if s[0] in ('+', '-'):
                            try:
                                i = int(s)
                            except ValueError:
                                pass
                            else:
                                # e.g., nth-child(+6) is equivalent to
                                # nth-child(0n+6)
                                a, b = 0, i
                        elif s[1].lower() != 'n':
                            raise err(
                                'Invalid pseudoclass argument: "%s"' % s
                            )
                        else:
                            # e.g., nth-last-child(4n) is equivalent to
                            # nth-last-child(4n+0)
                            a, b = int(s[0]), 0
                    except ValueError:
                        raise err(
                            'Invalid pseudoclass argument: "%s"' % s
                        )
                else:
                    # Match pseudoclass arguments like :nth-child(2n+0)
                    m = re.match(
                        '(\+|-)?([0-9]+)?[nN] *(\+|-) *([0-9])+$', s
                    )

                    # If a match was made
                    if m:
                        gs = m.groups()

                        # If all four groups were matched
                        if len(gs) == 4:
                            
                            # If no sign was specified in the argemuntes
                            # (e.g., 2n+0)
                            if gs[0] is None:
                                gs = list(gs)

                                # Default to a plus sign if no sign was
                                # found.
                                gs[0] = '+'

                            # TODO gs[0] can't be None here so no need
                            # to test it.
                            
                            # If the arguments start with a numeric
                            # value (e.g., nth-child(+1n+0))
                            if gs[0] is not None and gs[1] is not None:
                                # Set a to the first numeric value
                                a = int(gs[0] + gs[1])

                            # If the arguments don't start off with a
                            # numeric value (e.g., nth-child(n+0))
                            if a is None:
                                # Default a to 1
                                a = int(gs[0] + '1')

                            # Set be to the second and last value (i.e.
                            # the 2 in :nth-child(1n+2)(
                            b = int(gs[2] + gs[3])

                # Make a and b the corresponding property values of this
                # object.
                self._a, self._b = a, b

            def __repr__(self):
                """ Return a string representation of the arguments.
                """
                pcls = self.pseudoclass.value
                if pcls == 'lang':
                    return '(%s)' % self.string
                elif pcls == 'not':
                    return '(%s)' % repr(self.selectors)

                a = str(self.a)
                b = str(self.b)

                if self.a is None and self.b is None:
                    return ''

                if self.b >= 0:
                    b = '+' + b

                return '(%sn%s)' % (a, b)

        ''' Class members of ``pseudoclass`` '''

        def __init__(self):
            """ Create a pseudoclass object.
            """
            # Invoke selector._simple.__init__
            super().__init__()

            # Init the value
            self.value = None

            # Set the arguments property to an instance of `argument`
            self.arguments = selector.pseudoclass.arguments(self)

        def clone(self):
            """ Create and return an object based on the state of self.
            """
            pcls = selector.pseudoclass()
            pcls.value = self.value
            pcls.arguments = self.arguments.clone(pcls=pcls)
            return pcls

        def demand(self):
            """ Raise an exception if pseudoclass is invalid.
            """
            err = CssSelectorParseError

            # If this represents an nth-* pseudoclass, we should have an
            # a and b property in the arguments.
            if self.value.lower().startswith('nth-'):
                if self.arguments.a is None or self.arguments.b is None:
                    raise err(
                        'Error in argument(s) to pseudoclass '
                        '"%s"' % self.value
                    )
            # If this is a :not pseudoclass...
            elif self.value.lower() == 'not':
                # If the pseudoclass is 'not', then invoke its
                # 'arguments.selectors'. That will cause :not's
                # arguments to be parse. If there is a pares error in
                # not's arguments (stored as a str in
                # self.arguments.string), invoking this property will
                # raise the CssSelectorParseError.
                self.arguments.selectors

        def __repr__(self):
            """ Return a str representation of this pseudoclass object.
            """
            r = ':' + self.value
            r += repr(self.arguments)
            return r

        def _match_lang(self, el):
            """ Called by self.match to determine if el matches this
            pseudoclass selector when it is :lang(). See self.match for
            more details.

            :param: el dom.element: The DOM element being tested.
            """
            langs = el.language
            if langs is None:
                return

            args = self.arguments.c.lower().split('-')
            langs = langs.lower().split('-')

            if len(args) > len(langs):
                return False

            for arg, lang in zip(args, langs):
                if arg != lang:
                    return False
            
            return args[0] == langs[0]

        def _match_root(self, el):
            """ Called by self.match to determine if el matches this
            pseudoclass selector when it is :root(). See self.match for
            more details.

            :param: el dom.element: The DOM element being tested.
            """
            return el is el.root

        def _match_nth_child_starting_at(self, begining, el, oftype):
            """ Called by the self._match_nth_* methods to determine if
            el matches this pseudoclass selector. See the
            self._match_nth* methods for more for more details.

            :param: el dom.element: The DOM element being tested.
            """
            a, b = self.arguments.a, self.arguments.b

            sibs = el.getsiblings(accompany=True)
            sibs.remove(lambda x: type(x) is text)

            if not begining:
                sibs.reverse()

            if oftype:
                sibs.remove(lambda x: type(x) is not type(el))

            n = 0
            while True:
                ix = a * n + b - 1

                sib = sibs(ix)
                if not sib or n > sibs.count:
                    break
                
                if ix >= 0 and sib is el:
                    return True

                n += 1

            return False

        def _match_nth_child(self, el):
            """ Called by self.match to determine if el matches this
            pseudoclass selector when it is :nth-child(). See self.match
            for more details.

            :param: el dom.element: The DOM element being tested.
            """
            return self._match_nth_child_starting_at(
                begining=True, el=el, oftype=False
            )

        def _match_nth_last_child(self, el):
            """ Called by self.match to determine if el matches this
            pseudoclass selector when it is :nth-last-child(). See
            self.match for more details.

            :param: el dom.element: The DOM element being tested.
            """
            return self._match_nth_child_starting_at(
                begining=False, el=el, oftype=False
            )

        def _match_nth_of_type(self, el):
            """ Called by self.match to determine if el matches this
            pseudoclass selector when it is :nth-of-type(). See
            self.match for more details.

            :param: el dom.element: The DOM element being tested.
            """
            return self._match_nth_child_starting_at(
                begining=True, el=el, oftype=True
            )

        def _match_nth_last_of_type(self, el):
            """ Called by self.match to determine if el matches this
            pseudoclass selector when it is
            :not(). See self.match for more details.

            :param: el dom.element: The DOM element being tested.
            """
            return self._match_nth_child_starting_at(
                begining=False, el=el, oftype=True
            )

        def _match_first_child(self, el):
            """ Called by self.match to determine if el matches this
            pseudoclass selector when it is
            :first-child(). See self.match for more details.

            :param: el dom.element: The DOM element being tested.
            """
            sibs = el.getsiblings(accompany=True)

            sibs.remove(lambda x: type(x) is text)
            return sibs.first is el

        def _match_last_child(self, el):
            """ Called by self.match to determine if el matches this
            pseudoclass selector when it is
            :last-child(). See self.match for more details.

            :param: el dom.element: The DOM element being tested.
            """
            sibs = el.getsiblings(accompany=True)
            sibs.remove(lambda x: type(x) is text)
            return sibs.last is el

        def _match_x_of_type(self, el, last=False):
            sibs = el.getsiblings(accompany=True)
            sibs.remove(lambda x: type(x) is text)

            if last:
                sibs = sibs.reversed()

            for sib in sibs:
                if type(sib) is type(el):
                    return sib is el
                        
            return False

        def _match_first_of_type(self, el):
            """ Called by self.match to determine if el matches this
            pseudoclass selector when it is :first-of-type(). See
            self.match for more details.

            :param: el dom.element: The DOM element being tested.
            """
            return self._match_x_of_type(el=el)

        def _match_last_of_type(self, el):
            """ Called by self.match to determine if el matches this
            pseudoclass selector when it is :last-of-type(). See
            self.match for more details.

            :param: el dom.element: The DOM element being tested.
            """
            return self._match_x_of_type(el=el, last=True)

        def _match_only_child(self, el):
            """ Called by self.match to determine if el matches this
            pseudoclass selector when it is :only-child(). See
            self.match for more details.

            :param: el dom.element: The DOM element being tested.
            """
            sibs = el.getsiblings(accompany=True)
            return sibs.where(lambda x: type(x) is not text).issingular

        def _match_only_of_type(self, el):
            """ Called by self.match to determine if el matches this
            pseudoclass selector when it is :only-of-type(). See
            self.match for more details.

            :param: el dom.element: The DOM element being tested.
            """
            sibs = el.getsiblings(accompany=True)
            return sibs.where(lambda x: type(x) is type(el)).issingular

        def _match_empty(self, el):
            """ Called by self.match to determine if el matches this
            pseudoclass selector when it is :not-empty(). See self.match
            for more details.

            :param: el dom.element: The DOM element being tested.
            """

            # `comments` elements don't matter when it comes to
            # emptiness but `text' elements actually do. This includes
            # text with just whitespace. Processing instructions matter
            # too but we don't support them in the DOM.
            els = el.elements.where(lambda x: type(x) is not comment)
            return els.isempty

        def _match_not(self, el):
            """ Called by self.match to determine if el matches this
            pseudoclass selector when it is :not(). See self.match for
            more details.

            :param: el dom.element: The DOM element being tested.
            """
            m = self.arguments.selectors[0].elements[0].match
            m = m(el)
            return not m

        def match(self, el):
            """ Returns True if el matches this pseudoclass selector
            object, False otherwise.

            :param: el dom.element: The DOM element being tested.
            """
            if type(el) in (text, comment):
                return False

            # Get name of the actual CSS pseudoclass (e.g., 'nth-child')
            pcls = self.value.replace('-', '_').lower()
            
            # Delegate to a private pseudoclass-specific method
            return getattr(self, '_match_' + pcls)(el)

        @property
        def hasvalidname(self):
            return self.value.lower() in self.validnames

class AttributeExistsError(Exception):
    """ Raised when the same attribute is added to an ``element``'s
    collection more than once.
    """

class ClassExistsError(Exception):
    """ Raised when the same class is added to an ``element``'s
    class attribute more than once.
    """

class HtmlParseError(Exception):
    """ Raised when there is an error during the parsing of an HTML
    document.
    """
    def __init__(self, msg=None, frm=None):
        """ Create the exception:

        :param: msg str: The error message.

        :param: frm list: A list indiating the element and position of
        the element in the HTML document where parsing failed:

            [p(id="8biJP_qTQYa_Jb3A_1lrgQ"), (2, 2)]

        Here the parsing failed at a p element with an id of
        8biJP_qTQYa_Jb3A_1lrgQ. The (2, 3) tuple indicates the line (2)
        and offset (3) where the parsing failed. This tuple comes from
        HTMLParser.getpos(). See the line, column and element
        @property's below.
        """
        # TODO We should call Super().__init__ and pass the message
        # using through *args.
        self._frame = frm
        self._msg = msg

    @property
    def line(self):
        """ Returns the line number where the parsing failed.
        """
        frm = self._frame

        if not frm:
            return None

        return frm[1][0]

    @property
    def column(self):
        """ Returns the column number where the parsing failed.
        """
        frm = self._frame

        if not frm:
            return None

        return frm[1][1]

    @property
    def element(self):
        """ Returns the element object where the parsing failed.
        """
        frm = self._frame

        if not frm:
            return None

        return frm[0]
       
    def __str__(self):
        """ Returns a string representation of the exception.
        """
        r = self._msg
        if self._frame:

            if self.element:
                r += ' <%s>' % self.element.tag

            r += ' at line %s column %s' % (self.line, self.column)
        return r

class MoveError(ValueError):
    """ An exception raised when an element is moved incorrecty from one
    DOM to another.
    """

class CssSelectorParseError(SyntaxError):
    """ An error raised during the parsing of a CSS selector string.
    """

    def __init__(self, o, tok=None, pos=None):
        """ Create a CssSelectorParseError.

        :param: o seectors.token|str: If a selectors.token, o is a reference
        to the token where the error occured. If o is a str, it is just the
        error message.

        :param: tok seectors.token: A reference to the token where the error
        occured.

        :param: pos int: The position in the CSS selector string where the
        parse error occured.
        """
        self._pos = pos
        self.token = tok
        if isinstance(o, selectors.token):
            self.token = o
            tok = self.token
            super().__init__(
                'Unexpected token "%s" at %s' % (tok.value, tok.pos)
            )
        elif isinstance(o, str):
            super().__init__(o)
        else:
            raise TypeError('Invalid argument')

    @property
    def pos(self):
        """ The position in the CSS selector string where the parse
        error occured.
        """
        if self._pos is not None:
            return self._pos

        if self.token:
            return self.token.pos

        return None

class event(entities.event):
    """ Represents an event for DOM objects.

    DOM objects need events in the same way that all entities.entities
    and entities.entity objects need events. However, DOM object are
    unique in that their events, though triggered by the client, can be
    handled on the server side. This subclass of entities.event supports
    that ability.
    """

    """
    The below illustrates what the HTML looks like to make events
    happen. 

        <html>
            <main>
                <button data-click-fragments="#r2nd0m" 
                        data-click-handler='btn_onclick'>
                    Click me
                </button>
                <div id="#r2nd0m">
                    I will be sent to the server-side event handler for
                    modification.
                <div>
            </main>
        </html>

    Elements that need event handling have two attributes that are named
    after the following pattern: data-<event>-handler and
    data-<event>-fragments.  The <event> is the name of the event that
    should be handled; in the above example, the 'click' event' of the
    <button> is being handled.  The data-<event>-handler attribute
    indicates which method on the page object is the server-side event
    handler. The data-<event>-fragments attribute contain the id
    value(s) of the element's in the document that should be sent to the
    server-side event handler. The element(s)'s outerHTML is sent. The
    server-side handler is free to view and modifier these HTML
    fragments. The modified versions are returned to the browser and are
    used to replace the original version.

    In real browsers, this process is managed by the JavaScript that is
    returned from pom.site._eventjs.  Additionally, a Python
    implementation for this logic is available at
    tester.browser._tab.element_event. This Python-only implementation
    makes it possible to write automated tests to ensure events are
    handled correctly.

    This example shows two different <button>s declared to send their
    click event to the same server-side event handler:

        <main>
            <button 
                data-click-handler="btn_onclick" 
                data-click-fragments="#x5vK2fqVsRGGJy5JtHsXggw">
                Click me
            </button>
            <button 
                data-click-handler="btn_onclick" 
                data-click-fragments="#xw7bdDL1BS5aUfCB7hFk3xA, #xO5g0ZY5sRuSshlA2Y0jiRA">
                Click me again
            </button>
            <div id="x5vK2fqVsRGGJy5JtHsXggw"></div>
            <div id="xw7bdDL1BS5aUfCB7hFk3xA"></div>
            <div id="xO5g0ZY5sRuSshlA2Y0jiRA"></div>
        </main>

    Notice that the first button sends the first <div> but the second
    <button> sends the second and third <div> (a comma is used to
    seperate the id values instead of whitespace because that makes the
    data-<event>-fragments value a proper CSS3 selector).

    An element can also be declared to have two different events sent to
    the same event handler:
        <main>
            <input 
                data-blur-handler="inp_onfocuschange" 
                data-blur-fragments="#xBGH5zf5WRmqyP_QT4l2vqw" 
                data-focus-handler="inp_onfocuschange" 
                data-focus-fragments="#xphe7_ybRSeSgxK_PGrPZ2A"
            >
            <div id="xphe7_ybRSeSgxK_PGrPZ2A"></div>
            <div id="xBGH5zf5WRmqyP_QT4l2vqw"></div>
        </main>

    Here, we have the onblur and onfocus events sent to the
    inp_onfocuschange server-side event handler. These different events
    are able to send different HTML fragments as can be seen above.
    """
    def __init__(self, el, name, *args, **kwargs):
        """ Create a dom.event.

        :param: el dom.element: The element to which the event will
        occur. This would typically be a UI widget like a <button>.

        :param: name str: The name of the event, such as 'click' or
        'blur'.
        """
        self.element   =  el

        # The elements for which it will be possible for the event
        # handler(s) to mutate in response to the event occuring.
        self.elements = elements()

        self.name      =  name

        super().__init__(*args, **kwargs)

    def __iadd__(self, t):
        """ Implement the += operator. See the docstring at
        ``entities.append`` for details.
        """
        if isinstance(t, tuple):
            obj = t[0]
            els = t[1:]
        else:
            obj = t
            els = tuple()

        self.append(obj=obj, els=els)
        return self

    def append(self, obj, els=None, *args, **kwargs):
        """ Appends event handlers to the event.

        In the standard entities.event class, handlers are appended
        using this idiom:

            def handler(src, eargs):
                ...

            ev = event()
            ev += handler

        With DOM events, we want to specify the DOM elements that should
        be sent to the server-side event handler so it can manipulate
        them. We do that with a tuple:

            class mypage(pom.page):
                def btnok_click(src, eargs):
                    # Server-side event
                    mydiv = eargs.html.first
                    mydiv += dom.p('A modification')

                def main():
                    mydiv = dom.div()
                    btnok = dom.button()

                    # Use the += append operator to specify server-side
                    # handler and elements.
                    btnok.onclick += btnok_click, mydiv, ...

        Note that mydiv is a DOM object, however, the outer HTML for
        that DOM object will be sent back up to the server and then
        re-objectified into a DOM object.

        :param: obj callable: A reference to the server-side event
        handler (e.g. btnok_click).

        :param: els tuple: The collection of dom.elements whose HTML
        representation will be sent to the server. This tuple can
        contain zero elements when there is no need for any HTML to be
        sent:

            def main():
                ...
                btnok.onclick += btnok_click

        `els` can be None if a conventional (non-JavaScript)
        subscription to an event is being made.
        """

        if isinstance(els, tuple):
            # This is for subscribing DOM events (i.e., XHR events). The
            # alternative block deals with conventional event
            # subscription.

            f = obj

            # Get the element's attirbutes collection
            attrs = self.element.attributes

            hnd = f.__func__.__name__
            attrs[f'data-{self.name}-handler'] = hnd

            if els:
                ids = list()
                for el in els:
                    # Append to the event's elements collection
                    self.elements += el

                    # Ensure there is a unique identifier for the element
                    el.identify()

                    # Collect that identifier
                    ids.append(f'#{el.id}')

                # Set the element's data-<event-name>-fragments attribute to
                # the comma seprated list of ids. NOTE that using a comma,
                # along with the hash(es), makes the value for this
                # attribute a valid CSS selector, which will be useful later
                # on.
                attrs[f'data-{self.name}-fragments'] = ', '.join(ids)

        else:
            # Conventional event subscription.
            f = obj

        super().append(f)

class eventargs(entities.eventargs):
    """ The eventargs class for DOM events. This object is used to move
    data from the browser to the server-side event handler.
    """

    def __init__(self, 
        el=None, trigger=None, hnd=None, src=None, html=None
    ):
        """ Create an eventargs object.

        :param: el dom.element: The element that is causing
        the event.  This is usualy a DOM object running in a browser
        that is the subject of an event.

        :param: trigger str: The name of the method that triggered the
        event. Usually, events happen to elements, but an element can
        fire it's own event with a method. Consider:

            btn = dom.button()
            btn.click()

        In this case, the `trigger` would be 'click'.

        :param: hnd str: The name of the event handler this eventargs is
        destined for.

        :param: src dom.element: The element that was the subject of the
        event.

        :param: html dom.elements: A collection of DOM objects from
        the browser's DOM that the event handler would like to view or
        manipulate.
        """

        # Get the dom.html class reference so we can use it to parse
        # HTML.
        domhtml = sys.modules['dom'].html

        if el is not None:
            if trigger is None:
                raise ValueError(
                    'if el is not None, there must be a value for '
                    'trigger'
                )

            if hnd is not None or src is not None or html is not None:
                raise ValueError(
                    'if el is not None, hnd, src and html must be None'
                )


            # Get ids from data-{trigger}-fragments, look up their data
            # fragments in `el` DOM.
            if ids := el.attributes[f'data-{trigger}-fragments'].value:
                html = el.root[ids]
            else:
                # If there is no data-{trigger}-fragments attribute, set
                # `html` to None.
                html = None

            hnd = el.attributes[f'data-{trigger}-handler'].value

            src = el

        if html and not isinstance(html, elements):
            html = domhtml(html)

        if not isinstance(src, element):
            src = domhtml(src).only

        self.handler  =  hnd
        self.src      =  src
        self.html     =  html

        # The name of the method that triggered the event
        self.trigger  =  trigger

    def __repr__(self):
        r = type(self).__name__
        if (html := self.html) is not None:
            html = html[:10] + (html[10:] and '...')
            html += f"'{html}'"

        r += '('
        r += f'handler={self.handler}, '
        r += f'html={html}, '
        r += f'src={self.src!r}, '
        r += f"trigger='{self.trigger}'"
        r += ')'
        return r


