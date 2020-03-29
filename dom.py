# vim: set et ts=4 sw=4 fdm=marker

#######################################################################
# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2020
########################################################################

from contextlib import suppress
from dbg import B
from entities import classproperty
from func import enumerate
from html.parser import HTMLParser
from mistune import Markdown
from textwrap import dedent, indent
import entities
import html as htmlmod
import operator
import orm
import primative
import re
import string
import sys
import urllib.parse
import uuid

"""
An implementation of the HTML5 DOM.
"""

"""
.. _moz_global_attributes https://developer.mozilla.org/en-US/docs/Web/HTML/Global_attributes
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
    def __init__(self, el=None, *arg, **kwargs):
        super().__init__(*arg, **kwargs)
        self.element = el
        
    """ Represents a collection of attributes for HTML5 elements.
    """
    def __iadd__(self, *o):
        """ Append an attribute to the collection via the += operator.
        """
        for o in o:
            if type(o) in (tuple, list):
                o = attribute.create(*o)
            super().__iadd__(o)
        return self

    def clone(self):
        """ Return a cloned version of the attributes collection.
        """
        attrs = type(self)(self.element)
        for attr in self:
            attrs += attr.clone()
        return attrs
            
    def append(self, o, v=None, uniq=False, r=None):
        """ Append an attribute to the collection. 
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
            return super().append(o, uniq, r)

        for attr in self:
            if o.name == attr.name:
                msg = 'Attribute already exists: ' + o.name
                raise AttributeExistsError(msg)

        return super().append(o, uniq, r)

    def __getitem__(self, key):
        """ Returns an `attribute` object based on the given `key`.

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
        """

        if not isinstance(key, str):
            super().__setitem__(key, item)
            
        try:
            ix = self.getindex(key)
        except ValueError as ex:
            attr = None
        else:
            attr = self._ls[ix]

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
        """
        for e in reversed(self._defined):
            yield e

    @property
    def _defined(self):
        ''' Return a list of attributes that have values. (See
        `attribute.isdef`)
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
    present. For example, the following represents the subsequent HTML::

        inp = dom.input()
        inp.attributes['type'] = checkbox
        inp.attributes['checked'] = None
        
        ---

        <input type="checkbox" checked>

    """

    class undef:
        """ Used to indicate that an attribute has not been defined.
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
        # TODO We should raise ValueError if v contains an ambigous
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
        """ Determines whther an attribute is defined. An undefined
        attribute can be created by the indexing the `attributes`
        collection without setting a the `value`::

            id = attrs['id']

        Here, the `attrs` now has an attribute called 'id' that has no
        value. Since it has no value, it presense within `attrs` is
        concealed from the user:

            assert attrs.count == 0

        If the use decides later to give `id` a value, the `attrs`
        collection will reveal the attribute to the user::
            
            assert attrs.count == 0
            id.value = 'myvalue'
            assert attrs.count == 1

        The `isdef` property is used by the logic that conceals the
        undefined attributes from the use.
        """
        return self._value is not attribute.undef

    @staticmethod
    def create(name, v=undef):
        """ A staticmethod to creates a attribute or cssclass given a
        name and an optional value. Unline `attribute`'s constructor, a
        cssclass will be returned if name = 'class'.
        """
        if name == 'class':
            return cssclass(v)

        return attribute(name, v)

    def __repr__(self):
        r = "%s(name='%s', value='%s')"
        r %= type(self).__name__, self.name, self.value
        return r

    def __str__(self):
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
        return e in self._classes

    def __len__(self):
        return len(self._classes)
    
    @property
    def count(self):
        return len(self)

    def __bool__(self):
        # By default, if __len__ returns 0, the object is falsey. If the
        # object exists (as a nonNone property, for example), it should
        # be True. So it should always be truthy.
        return True

    def __getitem__(self, ix):
        return self._classes[ix]

    def __iadd__(self, o):
        self.append(o)
        return self

    def append(self, *clss):
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
        self.remove(*clss)

    def __isub__(self, o):
        self.remove(o)
        return self

    def remove(self, *clss):
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
        return bool(self._classes)

    @property
    def value(self):
        if not self.isdef:
            return attribute.undef
        return ' '.join(self._classes)

    @value.setter
    def value(self, v):
        if v is None:
            self._classes = list()
        elif v is not attribute.undef:
            self._classes = v.split()

    @property
    def html(self):
        return 'class="%s"' % self.value

    def __repr__(self):
        return '%s(value=%s)' % (type(self).__name__, self._classes)

class elements(entities.entities):
    # TODO:12c29ef9 Write and test mass attribute assignment logic:
    #
    #     chks.checked = True  # Check all checked attributes
    # 
    #     del htmls.id # Remove all attribute in els collection
    #
    # When this is complete, c0336221 can be attended to.

    # TODO All html should pass the W3C validation service at:
    # https://validator.w3.org/#validate_by_input

    def _self_onadd(self, src, eargs):
        super()._self_onadd(src, eargs)

        # If `self` has no root then `self` is likely being used to
        # collect elements for non-tree purposes such as collecting the
        # ancestors of an element or the matches of a CSS selector
        # selection.. In this case, there is no need to note the
        # revision.
        if not self.root:
            return 

        # If the element being appended has a parent, then we don't want
        # to create a revision entry for it. If this is the case, the
        # element is being collected for non-tree purposes, such as when
        # when an `element.elements` method creates a collection of
        # elements to return to its caller
        if not eargs.entity.isroot:
            return

        # Add an `Append` revision entry to the root's revision
        # collection.
        revs = self.root._revisions
        sub = self.parent
        obj = eargs.entity
        if isinstance(sub, text):
            # If we are appending an element to a text node, we need to
            # replace (Remove then Append) the text node's parent. This
            # is because text nodes don't have id attributes that can be
            # expressed in HTML.
            rent = sub.parent
            grent = sub.grandparent

            if rent:
                revs.revision(revision.Remove, sub=grent, obj=rent)

                rent = rent.clone()
                rent.reidentify()

                revs.revision(revision.Append, sub=grent, obj=rent)
                revs += rent._revisions

            else:
                # Sometimes self.parent won't have a parent. Because the
                # DOM is small.
                pass

        else:
            # If we are appending an element to a non-text element,
            # simply log the append.
            revs.revision(revision.Append, sub=sub, obj=obj)

        # Nullify the revision collection of the element being appended.
        # But before doing that, add it to the self's root's
        # revisions collection.
        revs = eargs.entity._revisions
        eargs.entity._revisions = None
        self.root._revisions += revs

    def _self_onremove(self, src, eargs):
        super()._self_onadd(src, eargs)

        # This code is also in _self_add. See the comment there for why
        # we exculde logging on this condition.
        if not self.root:
            return

        revs = self.root._revisions
        revs.revision(revision.Remove, self.parent, eargs.entity)

    @property
    def root(self):
        if self.parent:
            return self.parent.root
        return None

    @classmethod
    def getby(cls, tag):
        for el in element.__subclasses__():
            if el.tag == tag:
                return el
        return None

    def clone(self):
        els = type(self)()
        for e in self:
            els += e.clone()

        return els

    @property
    def text(self):
        """ Get the combined text contents of each element.
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
        ''' Get elements by an ordinal index or a CSS3 selector.

        Examples::
            
            # Get the first element of the collection of elememnts
            el = els[0]

            # Get the first 2 elements from the collection of elememnts
            els = els[0:2]

            # Get all <span> elements that are immediate children of <p>
            # where the <p> is a child or grandchild of a <div> with a
            # class of of 'my-class'.
            els = els['div.my-class p > span']

            # Same as above except pass a selectors object instead of a
            # selector string.
            sels = selectors('div.my-class p > span')
            els = els[sels]
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
        initial = (
            x for x in self if type(x) not in (comment, text)
        )
        return elements(initial=initial)

    def getchildren(self):
        els = elements()
        for el in self.children:
            els += el
            els += el.getchildren(recursive=True)
        return els

    @property
    def all(self):
        els = elements()
        for el in self:
            els += el
            els += el.getelements(recursive=True)
        return els

    @property
    def pretty(self):
        return '\n'.join(x.pretty for x in self)

    @property
    def html(self):
        return ''.join(x.html for x in self)

    @property
    def parent(self):
        if not hasattr(self, '_parent'):
            self._parent = None
        return self._parent

    def _setparent(self, v):
        if self.parent:
            raise MoveError('Parent already set')
        self._parent = v

    def append(self, *args, **kwargs):
        if isinstance(self.parent, text):
            raise NotImplementedError(
                "Can't append to a text node"
            )
        super().append(*args, **kwargs)
        
class element(entities.entity):
    # There must be a closing tag on elements by default. In cases,
    # such as the `base` element, there should not be a closing tag so
    # `isvoid` is set to True

    # "A void element is an element whose content model never allows it
    # to have contents under any circumstances. Void elements can have
    # attributes. [...]
    # The following is a complete list of the void elements in HTML:
    #     area, base, br, col, command, embed, hr, img, input, keygen,
    #     link, meta, param, source, track, wbr [...]
    # Optionally, a "/" character, which may be present only if the
    # element is a void element. [...]
    # Void elements only have a start tag; end tags must not be
    # specified for void elements. [...]
    # A non-void element must have an end tag, unless the subsection for
    # that element in the HTML elements section of this reference
    # indicates that its end tag can be omitted."
    # The above is from:
    #   https://www.w3.org/TR/2011/WD-html-markup-20110405/syntax.html
    isvoid = False

    # TODO Prevent adding nonstandard elements to a given element. For
    # example, <p> can only have "phrasing content" according to the
    # HTML5 standard.

    @staticmethod
    def _getblocklevelelements():
        return (
            address,   article,     aside,   blockquote,  dd,
            details,   dialog,      div,     dl,          dt,
            fieldset,  figcaption,  figure,  footer,      form,
            h1,        h2,          h3,      h4,          h5,
            h6,        header,      hgroup,  hr,          li,
            main,      nav,         ol,      p,           pre,
            sections,  table,       ul,
        )

    def __init__(self, body=None, *args, **kwargs):
        # TODO If self.isvoid, the `body` parameter would be
        # meaningless. In this case, if body is not None, we should
        # throw a TypeError.

        try:
            id = kwargs['id']
        except KeyError:
            # TODO If isinstance(self, text) or isinstance(self,
            # comment), should probably shouldn't be assigning an id.
            self.id = primative.uuid().base64
        else:
            if id is not False:
                self.id = primative.uuid().base64
                del kwargs['id']
        self._revs = None
        if body is not None:
            if     not isinstance(body, element) \
               and not isinstance(body, elements):

                body = str(body)

            if type(body) is str:
                body %= args
            elif args:
                raise ValueError('No args allowed')

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

        self.attributes += kwargs

    def remove(self, el):
        return self.elements.remove(el)

    def reidentify(self):
        self.id = primative.uuid().base64

        for el in self.all:
            self.id = primative.uuid().base64
        
    def apply(self, revs):
        for rev in revs:

            # Get the subject element of the revision from the DOM
            id = rev.subject.id
            els = self['[id="%s"]' % id]
            if els.isempty:
                raise ValueError("Can't find [id=\"%s\"]" % id) 
            elif els.hasplurality:
                raise ValueError(
                    "Multiple elements for [id=\"%s\"]" % id
                ) 

            sub = els.first

            if rev.type == revision.Append:
                # NOTE We can't use # as a selector. The ids are base64
                # encoding so sometimes they will start with a number.
                # This is fine in HTML5 but the # selector token won't
                # permit id selections that start with a number. (See
                # https://benfrain.com/when-and-where-you-can-use-numbers-in-id-and-class-names/)
                # The proper way to do this is to just use attribute
                # selection
                # 
                # Bad: #3QuaWRdCg
                # Good: [id="3QuaWRdCg"]

                obj = rev.object.clone()
                obj.elements.clear()

                sub += obj
            elif rev.type == revision.Remove:
                sels = '[id="%s"]' % rev.object.id
                obj = self[sels]
                sub.remove(obj)

    @property
    def isblocklevel(self):
        return type(self) in self._getblocklevelelements()

    def clone(self):
        el = type(self)()
        el += self.elements.clone()
        el.attributes = self.attributes.clone()
        return el

    def clear(self):
        self.elements.clear()

    def _elements_onadd(self, src, eargs):
        el = eargs.entity
        el._setparent(self)

    def __getitem__(self, ix):
        # Pass CSS selector to elements collection
        els = elements()
        els += self
        return els[ix]
        return self.elements[ix]

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
        for el in self.all:
            blk = blk or el.isblocklevel
            if isinstance(el, text):
                if r:
                    r += '\n' if blk else ''

                r += ' ' + el.value

                blk = False
        return re.sub('\s+', ' ', r).strip()

    @text.setter
    def text(self, v):
        self.elements.clear()
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
        """ Defines a unique identifier (ID) which must be unique in the
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
        """ The dir global attribute is an enumerated attribute that
        indicates the directionality of the element's text.

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
        """ The title global attribute contains text representing
        advisory information related to the element it belongs to.
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
        ans = self.ancestors
        if ans.count:
            return ans.last

        return self
    
    @property
    def isroot(self):
        return self is self.root

    @property
    def _revisions(self):
        if not self.isroot:
            raise ValueError(
                'Only root elements have revisions. '
                'Use element.root.revisions instead'
            )
        if self._revs is None:
            self._revs = revisions(self)
        return self._revs

    @_revisions.setter
    def _revisions(self, v):
        self._revs = v

    @property
    def parent(self):
        if not hasattr(self, '_parent'):
            self._parent = None
        return self._parent

    @property
    def grandparent(self):
        return self.getparent(1)

    @property
    def greatgrandparent(self):
        return self.getparent(2)

    @property
    def ancestors(self):
        return self.getancestors()

    def getancestors(self, includeself=False):
        els = elements()

        if includeself:
            rent = self
        else:
            rent = self.parent

        while rent:
            els += rent
            rent = rent.parent

        return els

    def getparent(self, num=0):
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

    def getsiblings(self, includeself=False):
        els = elements()
        rent = self.parent

        if rent:
            for el in rent.children:
                if not includeself and el is self:
                    continue
                els += el
        return els

    @property
    def siblings(self):
        return self.getsiblings()

    @property
    def previous(self):
        sibs = self.getsiblings(includeself=True)

        # If it only has self
        if sibs.hasone: 
            return None

        ix = sibs.getindex(self) - 1

        if ix < 0:
            return None

        return sibs(ix)

    @property
    def preceding(self):
        els = elements()
        for el in self.getsiblings(includeself=True):
            if el is self:
                break
            els += el
        return els

    @property
    def next(self):
        raise NotImplementedError()

        # NOTE The below may work but has not been tested
        sibs = self.getsiblings(includeself=True)
        ix = sibs.getindex(self)
        return sibs(ix + 1)
                
    @property
    def children(self):
        initial = (
            x for x in self.elements if type(x) not in (comment, text)
        )
        return elements(initial=initial)

    def getchildren(self, recursive=False):
        els = elements()
        for el in self.children:
            els += el

            if recursive:
                els += el.getchildren(recursive=True)
        return els

    @property
    def all(self):
        return self.getelements(recursive=True)

    def getelements(self, recursive=False):
        els = elements()
        for el in self.elements:
            els += el

            if recursive:
                els += el.getelements(recursive=True)

        return els

    @property
    def elements(self):
        if not hasattr(self, '_elements'):
            self._elements = elements()
            self._elements.onadd += self._elements_onadd
            self._elements._setparent(self)
        return self._elements
                
    @elements.setter
    def elements(self, v):
        self._elements = v

    @property
    def classes(self):
        return self.attributes['class']

    @classes.setter
    def classes(self, v):
        self.attributes['class'] = v

    @property
    def attributes(self):
        if not hasattr(self, '_attributes'):
            self._attributes = attributes(self)
        return self._attributes

    @attributes.setter
    def attributes(self, v):
        self._attributes = v

    def __lshift__(self, el):
        if type(el) is str:
            el = text(el)

        if not isinstance(el, element) and not isinstance(el, elements):
            raise ValueError('Invalid element type: ' + str(type(el)))

        self.elements << el
        return self

    def __iadd__(self, el):
        # TODO There is some redunancy between this and __lshift__.
        # Also, shouldn't this redundent logic be put in the overrides
        # element.append and element.insertbefore (which don't actually
        # exist at the time of this writing).
        if type(el) is str:
            el = text(el)

        if not isinstance(el, element) and not isinstance(el, elements):
            raise ValueError('Invalid element type: ' + str(type(el)))

        self.elements += el
        return self

    @classproperty
    def tag(cls):
        if type(cls) is not type:
            cls = type(cls)

        for typ in cls.__mro__:
            if typ is element:
                return prev.__name__
            prev = typ

    @property
    def pretty(self):
        body = str()
        if isinstance(self, text):
            body = self.html

        for i, el in enumerate(self.elements):
            if body: body += '\n'
            body += el.pretty

        if isinstance(self, text):
            return body

        body = indent(body, '  ')

        r = '<%s'
        args = [self.tag]

        if self.attributes.count:
            r += ' %s'
            args.append(self.attributes.html)

        r += '>'
        if not self.isvoid:
            r += '\n'

        if body:
            r += '%s\n'
            args += [body]

        if self.isvoid:
            pass
            #r += '>'
        else:
            r += '</%s>'
            args += [self.tag]

        return r % tuple(args)

    @property
    def html(self):
        body = str()

        if isinstance(self, text):
            body = self.html

        for i, el in enumerate(self.elements):
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
    pass

class header(element):
    pass

class titles(elements):
    pass

class title(element):
    pass

class smalls(elements):
    pass

class small(element):
    pass

class ps(elements):
    pass

class p(element):
    pass

paragraph = p

class addresses(elements):
    pass

class address(element):
    pass

class asides(elements):
    pass

class aside(element):
    pass

class dialogs(elements):
    pass

class dialog(element):
    pass

class figcaptions(elements):
    pass

class figcaption(element):
    pass

class figures(elements):
    pass

class figure(element):
    pass

class hgroups(elements):
    pass

class hgroup(element):
    pass

class articles(elements):
    pass

class article(element):
    """ The HTML <article> element represents a self-contained
    composition in a document, page, application, or site, which is
    intended to be independently distributable or reusable (e.g., in
    syndication). Examples include: a forum post, a magazine or
    newspaper article, or a blog entry.  
    
    https://developer.mozilla.org/en-US/docs/Web/HTML/Element/article
    """
    pass

class sections(elements):
    pass

class section(element):
    """ The HTML <section> element represents a standalone section —
    which doesn't have a more specific semantic element to represent it
    — contained within an HTML document. Typically, but not always,
    sections have a heading.
    
    https://developer.mozilla.org/en-US/docs/Web/HTML/Element/section
    """
    pass

class footers(elements):
    pass

class footer(element):
    # Reference:
    # https://www.orbitmedia.com/blog/website-footer-design-best-practices/
    def __init__(self):
        self.copyright = copyright()
    
    def sitemap(self):
        # Derived or overridden
        pass

    def privacypolicy(self):
        raise NotImplementedError('Author must override') 

    def termsofuse(self):
        raise NotImplementedError('Author must override') 

    def contact(self):
        # Derived or overridden
        pass

    def address(self):
        # Derived or overridden
        pass

    def phonenumbers(self):
        # Derived or overridden
        pass

    def socialmedia(self):
        # Derived or overridden
        pass

class text(element):
    def __init__(self, v, esc=True, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._value = v
        self._html = v

        if esc:
            self._html = htmlmod.escape(self._value)

    def clone(self):
        el = type(self)(self._value)

        # We can't append elements to a text node
        if not isinstance(self, text):
            el += self.elements.clone()
        el.attributes = self.attributes.clone()

        return el

    def __str__(self):
        return self.value

    @property
    def html(self):
        return dedent(self._html).strip('\n')

    @html.setter
    def html(self, v):
        self._html = v

    @property
    def value(self):
        return self._value

class wbrs(elements):
    pass

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

class breaks(elements):
    pass

class break_(element):
    """ The HTML <br> element produces a line break in text
    (carriage-return). It is useful for writing a poem or an address,
    where the division of lines is significant.

    https://developer.mozilla.org/en-US/docs/Web/HTML/Element/br
    """
    isvoid=True
    tag = 'br'

class comments(elements):
    pass

class comment(element):
    tag = '<!---->'
    def __init__(self, txt, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._text = txt

    @property
    def html(self):
        return '<!--%s-->' % self._text

    @property
    def pretty(self):
        return '<!--%s-->' % self._text
    
class forms(elements):
    pass

class form(element):
    @property
    def post(self):
        els = self['input, select, textarea']

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

        # See https://docs.python.org/3/library/urllib.request.html#urllib-examples
        return urllib.parse.urlencode(d, doseq=True).encode('ascii')

    @post.setter
    def post(self, v):
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
        return self.attributes['method'].value

    @method.setter
    def method(self, v):
        self.attributes['method'].value = v

    @property
    def novalidate(self):
        return self.attributes['novalidate'].value

    @novalidate.setter
    def novalidate(self, v):
        self.attributes['novalidate'].value = v

    @property
    def accept_charset(self):
        return self.attributes['accept-charset'].value

    @accept_charset.setter
    def accept_charset(self, v):
        self.attributes['accept-charset'].value = v

    @property
    def action(self):
        return self.attributes['action'].value

    @action.setter
    def action(self, v):
        self.attributes['action'].value = v

    @property
    def target(self):
        return self.attributes['target'].value

    @target.setter
    def target(self, v):
        self.attributes['target'].value = v

    @property
    def accept(self):
        return self.attributes['accept'].value

    @accept.setter
    def accept(self, v):
        self.attributes['accept'].value = v

    @property
    def enctype(self):
        return self.attributes['enctype'].value

    @enctype.setter
    def enctype(self, v):
        self.attributes['enctype'].value = v

    @property
    def name(self):
        return self.attributes['name'].value

    @name.setter
    def name(self, v):
        self.attributes['name'].value = v

    @property
    def autocomplete(self):
        return self.attributes['autocomplete'].value

    @autocomplete.setter
    def autocomplete(self, v):
        self.attributes['autocomplete'].value = v

class links(elements):
    pass

class link(element):
    isvoid = True
    @property
    def crossorigin(self):
        return self.attributes['crossorigin'].value

    @crossorigin.setter
    def crossorigin(self, v):
        self.attributes['crossorigin'].value = v

    @property
    def referrerpolicy(self):
        return self.attributes['referrerpolicy'].value

    @referrerpolicy.setter
    def referrerpolicy(self, v):
        self.attributes['referrerpolicy'].value = v

    @property
    def integrity(self):
        return self.attributes['integrity'].value

    @integrity.setter
    def integrity(self, v):
        self.attributes['integrity'].value = v

    @property
    def hreflang(self):
        return self.attributes['hreflang'].value

    @hreflang.setter
    def hreflang(self, v):
        self.attributes['hreflang'].value = v

    @property
    def importance(self):
        return self.attributes['importance'].value

    @importance.setter
    def importance(self, v):
        self.attributes['importance'].value = v

    @property
    def media(self):
        return self.attributes['media'].value

    @media.setter
    def media(self, v):
        self.attributes['media'].value = v

    @property
    def href(self):
        return self.attributes['href'].value

    @href.setter
    def href(self, v):
        self.attributes['href'].value = v

    @property
    def sizes(self):
        return self.attributes['sizes'].value

    @sizes.setter
    def sizes(self, v):
        self.attributes['sizes'].value = v

    @property
    def rel(self):
        return self.attributes['rel'].value

    @rel.setter
    def rel(self, v):
        self.attributes['rel'].value = v

class buttons(elements):
    pass

class button(element):
    @property
    def formtarget(self):
        return self.attributes['formtarget'].value

    @formtarget.setter
    def formtarget(self, v):
        self.attributes['formtarget'].value = v

    @property
    def formaction(self):
        return self.attributes['formaction'].value

    @formaction.setter
    def formaction(self, v):
        self.attributes['formaction'].value = v

    @property
    def autofocus(self):
        return self.attributes['autofocus'].value

    @autofocus.setter
    def autofocus(self, v):
        self.attributes['autofocus'].value = v

    @property
    def type(self):
        return self.attributes['type'].value

    @type.setter
    def type(self, v):
        self.attributes['type'].value = v

    @property
    def formnovalidate(self):
        return self.attributes['formnovalidate'].value

    @formnovalidate.setter
    def formnovalidate(self, v):
        self.attributes['formnovalidate'].value = v

    @property
    def form(self):
        return self.attributes['form'].value

    @form.setter
    def form(self, v):
        self.attributes['form'].value = v

    @property
    def name(self):
        return self.attributes['name'].value

    @name.setter
    def name(self, v):
        self.attributes['name'].value = v

    @property
    def formenctype(self):
        return self.attributes['formenctype'].value

    @formenctype.setter
    def formenctype(self, v):
        self.attributes['formenctype'].value = v

    @property
    def disabled(self):
        return self.attributes['disabled'].value

    @disabled.setter
    def disabled(self, v):
        self.attributes['disabled'].value = v

    @property
    def value(self):
        return self.attributes['value'].value

    @value.setter
    def value(self, v):
        self.attributes['value'].value = v

    @property
    def formmethod(self):
        return self.attributes['formmethod'].value

    @formmethod.setter
    def formmethod(self, v):
        self.attributes['formmethod'].value = v

class navs(elements):
    pass

class nav(element):
    pass

class lis(elements):
    pass

class li(element):
    @property
    def value(self):
        return self.attributes['value'].value

    @value.setter
    def value(self, v):
        self.attributes['value'].value = v

listitems = lis
listitem = li

class outputs(elements):
    pass

class output(element):
    @property
    def for_(self):
        return self.attributes['for'].value

    @for_.setter
    def for_(self, v):
        self.attributes['for'].value = v

    @property
    def form(self):
        return self.attributes['form'].value

    @form.setter
    def form(self, v):
        self.attributes['form'].value = v

    @property
    def name(self):
        return self.attributes['name'].value

    @name.setter
    def name(self, v):
        self.attributes['name'].value = v

class fieldsets(elements):
    pass

class fieldset(element):
    @property
    def form(self):
        return self.attributes['form'].value

    @form.setter
    def form(self, v):
        self.attributes['form'].value = v

    @property
    def name(self):
        return self.attributes['name'].value

    @name.setter
    def name(self, v):
        self.attributes['name'].value = v

    @property
    def disabled(self):
        return self.attributes['disabled'].value

    @disabled.setter
    def disabled(self, v):
        self.attributes['disabled'].value = v

class tfoots(elements):
    pass

class tfoot(element):
    @property
    def bgcolor(self):
        return self.attributes['bgcolor'].value

    @bgcolor.setter
    def bgcolor(self, v):
        self.attributes['bgcolor'].value = v

    @property
    def align(self):
        return self.attributes['align'].value

    @align.setter
    def align(self, v):
        self.attributes['align'].value = v

class params(elements):
    pass

class param(element):
    @property
    def name(self):
        return self.attributes['name'].value

    @name.setter
    def name(self, v):
        self.attributes['name'].value = v

    @property
    def value(self):
        return self.attributes['value'].value

    @value.setter
    def value(self, v):
        self.attributes['value'].value = v

class as_(elements):
    pass

class a(element):
    @property
    def referrerpolicy(self):
        return self.attributes['referrerpolicy'].value

    @referrerpolicy.setter
    def referrerpolicy(self, v):
        self.attributes['referrerpolicy'].value = v

    @property
    def target(self):
        return self.attributes['target'].value

    @target.setter
    def target(self, v):
        self.attributes['target'].value = v

    @property
    def hreflang(self):
        return self.attributes['hreflang'].value

    @hreflang.setter
    def hreflang(self, v):
        self.attributes['hreflang'].value = v

    @property
    def ping(self):
        return self.attributes['ping'].value

    @ping.setter
    def ping(self, v):
        self.attributes['ping'].value = v

    @property
    def media(self):
        return self.attributes['media'].value

    @media.setter
    def media(self, v):
        self.attributes['media'].value = v

    @property
    def href(self):
        return self.attributes['href'].value

    @href.setter
    def href(self, v):
        self.attributes['href'].value = v

    @property
    def download(self):
        return self.attributes['download'].value

    @download.setter
    def download(self, v):
        self.attributes['download'].value = v

    @property
    def rel(self):
        return self.attributes['rel'].value

    @rel.setter
    def rel(self, v):
        self.attributes['rel'].value = v

    @property
    def shape(self):
        return self.attributes['shape'].value

    @shape.setter
    def shape(self, v):
        self.attributes['shape'].value = v

anchors = as_
anchor = a

class audios(elements):
    pass

class audio(element):
    @property
    def crossorigin(self):
        return self.attributes['crossorigin'].value

    @crossorigin.setter
    def crossorigin(self, v):
        self.attributes['crossorigin'].value = v

    @property
    def loop(self):
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
        return self.attributes['src'].value

    @src.setter
    def src(self, v):
        self.attributes['src'].value = v

    @property
    def controls(self):
        return self.attributes['controls'].value

    @controls.setter
    def controls(self, v):
        self.attributes['controls'].value = v

    @property
    def autoplay(self):
        return self.attributes['autoplay'].value

    @autoplay.setter
    def autoplay(self, v):
        self.attributes['autoplay'].value = v

    @property
    def muted(self):
        return self.attributes['muted'].value

    @muted.setter
    def muted(self, v):
        self.attributes['muted'].value = v

    @property
    def preload(self):
        return self.attributes['preload'].value

    @preload.setter
    def preload(self, v):
        self.attributes['preload'].value = v

class bases(elements):
    pass

class base(element):
    """ The HTML <base> element specifies the base URL to use for all
    relative URLs contained within a document. There can be only one
    <base> element in a document.
    """
    isvoid = True

    @property
    def target(self):
        return self.attributes['target'].value

    @target.setter
    def target(self, v):
        self.attributes['target'].value = v

    @property
    def href(self):
        return self.attributes['href'].value

    @href.setter
    def href(self, v):
        self.attributes['href'].value = v

class imgs(elements):
    pass

class img(element):
    isvoid = True
    @property
    def crossorigin(self):
        return self.attributes['crossorigin'].value

    @crossorigin.setter
    def crossorigin(self, v):
        self.attributes['crossorigin'].value = v

    @property
    def referrerpolicy(self):
        return self.attributes['referrerpolicy'].value

    @referrerpolicy.setter
    def referrerpolicy(self, v):
        self.attributes['referrerpolicy'].value = v

    @property
    def loading(self):
        return self.attributes['loading'].value

    @loading.setter
    def loading(self, v):
        self.attributes['loading'].value = v

    @property
    def height(self):
        return self.attributes['height'].value

    @height.setter
    def height(self, v):
        self.attributes['height'].value = v

    @property
    def intrinsicsize(self):
        return self.attributes['intrinsicsize'].value

    @intrinsicsize.setter
    def intrinsicsize(self, v):
        self.attributes['intrinsicsize'].value = v

    @property
    def src(self):
        return self.attributes['src'].value

    @src.setter
    def src(self, v):
        self.attributes['src'].value = v

    @property
    def ismap(self):
        return self.attributes['ismap'].value

    @ismap.setter
    def ismap(self, v):
        self.attributes['ismap'].value = v

    @property
    def importance(self):
        return self.attributes['importance'].value

    @importance.setter
    def importance(self, v):
        self.attributes['importance'].value = v

    @property
    def usemap(self):
        return self.attributes['usemap'].value

    @usemap.setter
    def usemap(self, v):
        self.attributes['usemap'].value = v

    @property
    def align(self):
        return self.attributes['align'].value

    @align.setter
    def align(self, v):
        self.attributes['align'].value = v

    @property
    def alt(self):
        return self.attributes['alt'].value

    @alt.setter
    def alt(self, v):
        self.attributes['alt'].value = v

    @property
    def sizes(self):
        return self.attributes['sizes'].value

    @sizes.setter
    def sizes(self, v):
        self.attributes['sizes'].value = v

    @property
    def width(self):
        return self.attributes['width'].value

    @width.setter
    def width(self, v):
        self.attributes['width'].value = v

    @property
    def border(self):
        return self.attributes['border'].value

    @border.setter
    def border(self, v):
        self.attributes['border'].value = v

    @property
    def srcset(self):
        return self.attributes['srcset'].value

    @srcset.setter
    def srcset(self, v):
        self.attributes['srcset'].value = v

    @property
    def decoding(self):
        return self.attributes['decoding'].value

    @decoding.setter
    def decoding(self, v):
        self.attributes['decoding'].value = v

images = imgs
image = img

class tablerows(elements):
    pass

class tablerow(element):
    @property
    def bgcolor(self):
        return self.attributes['bgcolor'].value

    @bgcolor.setter
    def bgcolor(self, v):
        self.attributes['bgcolor'].value = v

    @property
    def align(self):
        return self.attributes['align'].value

    @align.setter
    def align(self, v):
        self.attributes['align'].value = v

class applets(elements):
    pass

class applet(element):
    @property
    def code(self):
        return self.attributes['code'].value

    @code.setter
    def code(self, v):
        self.attributes['code'].value = v

    @property
    def codebase(self):
        return self.attributes['codebase'].value

    @codebase.setter
    def codebase(self, v):
        self.attributes['codebase'].value = v

    @property
    def align(self):
        return self.attributes['align'].value

    @align.setter
    def align(self, v):
        self.attributes['align'].value = v

    @property
    def alt(self):
        return self.attributes['alt'].value

    @alt.setter
    def alt(self, v):
        self.attributes['alt'].value = v

class objects(elements):
    pass

class object(element):
    @property
    def data(self):
        return self.attributes['data'].value

    @data.setter
    def data(self, v):
        self.attributes['data'].value = v

    @property
    def type(self):
        return self.attributes['type'].value

    @type.setter
    def type(self, v):
        self.attributes['type'].value = v

    @property
    def height(self):
        return self.attributes['height'].value

    @height.setter
    def height(self, v):
        self.attributes['height'].value = v

    @property
    def form(self):
        return self.attributes['form'].value

    @form.setter
    def form(self, v):
        self.attributes['form'].value = v

    @property
    def name(self):
        return self.attributes['name'].value

    @name.setter
    def name(self, v):
        self.attributes['name'].value = v

    @property
    def usemap(self):
        return self.attributes['usemap'].value

    @usemap.setter
    def usemap(self, v):
        self.attributes['usemap'].value = v

    @property
    def width(self):
        return self.attributes['width'].value

    @width.setter
    def width(self, v):
        self.attributes['width'].value = v

    @property
    def border(self):
        return self.attributes['border'].value

    @border.setter
    def border(self, v):
        self.attributes['border'].value = v

class cols(elements):
    pass

class col(element):
    @property
    def bgcolor(self):
        return self.attributes['bgcolor'].value

    @bgcolor.setter
    def bgcolor(self, v):
        self.attributes['bgcolor'].value = v

    @property
    def span(self):
        return self.attributes['span'].value

    @span.setter
    def span(self, v):
        self.attributes['span'].value = v

    @property
    def align(self):
        return self.attributes['align'].value

    @align.setter
    def align(self, v):
        self.attributes['align'].value = v

class maps(elements):
    pass

class map(element):
    @property
    def name(self):
        return self.attributes['name'].value

    @name.setter
    def name(self, v):
        self.attributes['name'].value = v

class embeds(elements):
    pass

class embed(element):
    @property
    def type(self):
        return self.attributes['type'].value

    @type.setter
    def type(self, v):
        self.attributes['type'].value = v

    @property
    def height(self):
        return self.attributes['height'].value

    @height.setter
    def height(self, v):
        self.attributes['height'].value = v

    @property
    def src(self):
        return self.attributes['src'].value

    @src.setter
    def src(self, v):
        self.attributes['src'].value = v

    @property
    def width(self):
        return self.attributes['width'].value

    @width.setter
    def width(self, v):
        self.attributes['width'].value = v

class meters(elements):
    pass

class meter(element):
    @property
    def min(self):
        return self.attributes['min'].value

    @min.setter
    def min(self, v):
        self.attributes['min'].value = v

    @property
    def optimum(self):
        return self.attributes['optimum'].value

    @optimum.setter
    def optimum(self, v):
        self.attributes['optimum'].value = v

    @property
    def high(self):
        return self.attributes['high'].value

    @high.setter
    def high(self, v):
        self.attributes['high'].value = v

    @property
    def form(self):
        return self.attributes['form'].value

    @form.setter
    def form(self, v):
        self.attributes['form'].value = v

    @property
    def max(self):
        return self.attributes['max'].value

    @max.setter
    def max(self, v):
        self.attributes['max'].value = v

    @property
    def value(self):
        return self.attributes['value'].value

    @value.setter
    def value(self, v):
        self.attributes['value'].value = v

    @property
    def low(self):
        return self.attributes['low'].value

    @low.setter
    def low(self, v):
        self.attributes['low'].value = v

class times(elements):
    pass

class time(element):
    def __init__(self, dt=None, *args, **kwargs):
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
        return self.attributes['datetime'].value

    @datetime.setter
    def datetime(self, v):
        self.attributes['datetime'].value = v

class bodies(elements):
    pass

class body(element):
    @property
    def bgcolor(self):
        return self.attributes['bgcolor'].value

    @bgcolor.setter
    def bgcolor(self, v):
        self.attributes['bgcolor'].value = v

    @property
    def background(self):
        return self.attributes['background'].value

    @background.setter
    def background(self, v):
        self.attributes['background'].value = v

class progresses(elements):
    pass

class progress(element):
    @property
    def form(self):
        return self.attributes['form'].value

    @form.setter
    def form(self, v):
        self.attributes['form'].value = v

    @property
    def max(self):
        return self.attributes['max'].value

    @max.setter
    def max(self, v):
        self.attributes['max'].value = v

    @property
    def value(self):
        return self.attributes['value'].value

    @value.setter
    def value(self, v):
        self.attributes['value'].value = v

class commands(elements):
    pass

class command(element):
    @property
    def radiogroup(self):
        return self.attributes['radiogroup'].value

    @radiogroup.setter
    def radiogroup(self, v):
        self.attributes['radiogroup'].value = v

    @property
    def icon(self):
        return self.attributes['icon'].value

    @icon.setter
    def icon(self, v):
        self.attributes['icon'].value = v

    @property
    def type(self):
        return self.attributes['type'].value

    @type.setter
    def type(self, v):
        self.attributes['type'].value = v

    @property
    def checked(self):
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
    pass

class blockquote(element):
    @property
    def cite(self):
        return self.attributes['cite'].value

    @cite.setter
    def cite(self, v):
        self.attributes['cite'].value = v

class options(elements):
    pass

class option(element):
    @property
    def label(self):
        return self.attributes['label'].value

    @label.setter
    def label(self, v):
        self.attributes['label'].value = v

    @property
    def disabled(self):
        return self.attributes['disabled'].value

    @disabled.setter
    def disabled(self, v):
        self.attributes['disabled'].value = v

    @property
    def selected(self):
        return self.attributes['selected'].value

    @selected.setter
    def selected(self, v):
        if v:
            self.attributes['selected'].value = None
        else:
            del self.attributes['selected']

    @property
    def value(self):
        return self.attributes['value'].value

    @value.setter
    def value(self, v):
        self.attributes['value'].value = v

class canvass(elements):
    pass

class canvas(element):
    @property
    def height(self):
        return self.attributes['height'].value

    @height.setter
    def height(self, v):
        self.attributes['height'].value = v

    @property
    def width(self):
        return self.attributes['width'].value

    @width.setter
    def width(self, v):
        self.attributes['width'].value = v

class uls(elements):
    pass

class ul(element):
    pass

unorderedlists = uls
unorderedlist = ul

class ols(elements):
    pass

class ol(element):
    @property
    def reversed(self):
        return self.attributes['reversed'].value

    @reversed.setter
    def reversed(self, v):
        self.attributes['reversed'].value = v

    @property
    def start(self):
        return self.attributes['start'].value

    @start.setter
    def start(self, v):
        self.attributes['start'].value = v

class keygens(elements):
    pass

class keygen(element):
    @property
    def autofocus(self):
        return self.attributes['autofocus'].value

    @autofocus.setter
    def autofocus(self, v):
        self.attributes['autofocus'].value = v

    @property
    def form(self):
        return self.attributes['form'].value

    @form.setter
    def form(self, v):
        self.attributes['form'].value = v

    @property
    def name(self):
        return self.attributes['name'].value

    @name.setter
    def name(self, v):
        self.attributes['name'].value = v

    @property
    def disabled(self):
        return self.attributes['disabled'].value

    @disabled.setter
    def disabled(self, v):
        self.attributes['disabled'].value = v

    @property
    def keytype(self):
        return self.attributes['keytype'].value

    @keytype.setter
    def keytype(self, v):
        self.attributes['keytype'].value = v

    @property
    def challenge(self):
        return self.attributes['challenge'].value

    @challenge.setter
    def challenge(self, v):
        self.attributes['challenge'].value = v

class tracks(elements):
    pass

class track(element):
    @property
    def default(self):
        return self.attributes['default'].value

    @default.setter
    def default(self, v):
        self.attributes['default'].value = v

    @property
    def label(self):
        return self.attributes['label'].value

    @label.setter
    def label(self, v):
        self.attributes['label'].value = v

    @property
    def src(self):
        return self.attributes['src'].value

    @src.setter
    def src(self, v):
        self.attributes['src'].value = v

    @property
    def srclang(self):
        return self.attributes['srclang'].value

    @srclang.setter
    def srclang(self, v):
        self.attributes['srclang'].value = v

    @property
    def kind(self):
        return self.attributes['kind'].value

    @kind.setter
    def kind(self, v):
        self.attributes['kind'].value = v

class dels(elements):
    pass

class del_(element):
    @property
    def datetime(self):
        return self.attributes['datetime'].value

    @datetime.setter
    def datetime(self, v):
        self.attributes['datetime'].value = v

    @property
    def cite(self):
        return self.attributes['cite'].value

    @cite.setter
    def cite(self, v):
        self.attributes['cite'].value = v

class tbodys(elements):
    pass

class tbody(element):
    @property
    def bgcolor(self):
        return self.attributes['bgcolor'].value

    @bgcolor.setter
    def bgcolor(self, v):
        self.attributes['bgcolor'].value = v

    @property
    def align(self):
        return self.attributes['align'].value

    @align.setter
    def align(self, v):
        self.attributes['align'].value = v

class inss(elements):
    pass

class ins(element):
    @property
    def datetime(self):
        return self.attributes['datetime'].value

    @datetime.setter
    def datetime(self, v):
        self.attributes['datetime'].value = v

    @property
    def cite(self):
        return self.attributes['cite'].value

    @cite.setter
    def cite(self, v):
        self.attributes['cite'].value = v

class textareas(elements):
    pass

class textarea(element):
    @property
    def readonly(self):
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
        return self.attributes['cols'].value

    @cols.setter
    def cols(self, v):
        self.attributes['cols'].value = v

    @property
    def required(self):
        return self.attributes['required'].value

    @required.setter
    def required(self, v):
        self.attributes['required'].value = v

    @property
    def rows(self):
        return self.attributes['rows'].value

    @rows.setter
    def rows(self, v):
        self.attributes['rows'].value = v

    @property
    def autofocus(self):
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
        return self.attributes['form'].value

    @form.setter
    def form(self, v):
        self.attributes['form'].value = v

    @property
    def placeholder(self):
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
        return self.attributes['name'].value

    @name.setter
    def name(self, v):
        self.attributes['name'].value = v

    @property
    def maxlength(self):
        return self.attributes['maxlength'].value

    @maxlength.setter
    def maxlength(self, v):
        self.attributes['maxlength'].value = v

    @property
    def disabled(self):
        return self.attributes['disabled'].value

    @disabled.setter
    def disabled(self, v):
        self.attributes['disabled'].value = v

    @property
    def wrap(self):
        return self.attributes['wrap'].value

    @wrap.setter
    def wrap(self, v):
        self.attributes['wrap'].value = v

    @property
    def autocomplete(self):
        return self.attributes['autocomplete'].value

    @autocomplete.setter
    def autocomplete(self, v):
        self.attributes['autocomplete'].value = v

    @property
    def inputmode(self):
        return self.attributes['inputmode'].value

    @inputmode.setter
    def inputmode(self, v):
        self.attributes['inputmode'].value = v

class captions(elements):
    pass

class caption(element):
    @property
    def align(self):
        return self.attributes['align'].value

    @align.setter
    def align(self, v):
        self.attributes['align'].value = v

class inputs(elements):
    pass

class input(element):
    isvoid = True
    @property
    def min(self):
        return self.attributes['min'].value

    @min.setter
    def min(self, v):
        self.attributes['min'].value = v

    @property
    def readonly(self):
        return self.attributes['readonly'].value

    @readonly.setter
    def readonly(self, v):
        self.attributes['readonly'].value = v

    @property
    def formtarget(self):
        return self.attributes['formtarget'].value

    @formtarget.setter
    def formtarget(self, v):
        self.attributes['formtarget'].value = v

    @property
    def dirname(self):
        return self.attributes['dirname'].value

    @dirname.setter
    def dirname(self, v):
        self.attributes['dirname'].value = v

    @property
    def required(self):
        return self.attributes['required'].value

    @required.setter
    def required(self, v):
        self.attributes['required'].value = v

    @property
    def formaction(self):
        return self.attributes['formaction'].value

    @formaction.setter
    def formaction(self, v):
        self.attributes['formaction'].value = v

    @property
    def multiple(self):
        return self.attributes['multiple'].value

    @multiple.setter
    def multiple(self, v):
        self.attributes['multiple'].value = v

    @property
    def autofocus(self):
        return self.attributes['autofocus'].value

    @autofocus.setter
    def autofocus(self, v):
        self.attributes['autofocus'].value = v

    @property
    def type(self):
        return self.attributes['type'].value

    @type.setter
    def type(self, v):
        self.attributes['type'].value = v

    @property
    def step(self):
        return self.attributes['step'].value

    @step.setter
    def step(self, v):
        self.attributes['step'].value = v

    @property
    def height(self):
        return self.attributes['height'].value

    @height.setter
    def height(self, v):
        self.attributes['height'].value = v

    @property
    def src(self):
        return self.attributes['src'].value

    @src.setter
    def src(self, v):
        self.attributes['src'].value = v

    @property
    def accept(self):
        return self.attributes['accept'].value

    @accept.setter
    def accept(self, v):
        self.attributes['accept'].value = v

    @property
    def size(self):
        return self.attributes['size'].value

    @size.setter
    def size(self, v):
        self.attributes['size'].value = v

    @property
    def pattern(self):
        return self.attributes['pattern'].value

    @pattern.setter
    def pattern(self, v):
        self.attributes['pattern'].value = v

    @property
    def formnovalidate(self):
        return self.attributes['formnovalidate'].value

    @formnovalidate.setter
    def formnovalidate(self, v):
        self.attributes['formnovalidate'].value = v

    @property
    def form(self):
        return self.attributes['form'].value

    @form.setter
    def form(self, v):
        self.attributes['form'].value = v

    @property
    def checked(self):
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
        return self.attributes['minlength'].value

    @minlength.setter
    def minlength(self, v):
        self.attributes['minlength'].value = v

    @property
    def list(self):
        return self.attributes['list'].value

    @list.setter
    def list(self, v):
        self.attributes['list'].value = v

    @property
    def max(self):
        return self.attributes['max'].value

    @max.setter
    def max(self, v):
        self.attributes['max'].value = v

    @property
    def name(self):
        return self.attributes['name'].value

    @name.setter
    def name(self, v):
        self.attributes['name'].value = v

    @property
    def maxlength(self):
        return self.attributes['maxlength'].value

    @maxlength.setter
    def maxlength(self, v):
        self.attributes['maxlength'].value = v

    @property
    def usemap(self):
        return self.attributes['usemap'].value

    @usemap.setter
    def usemap(self, v):
        self.attributes['usemap'].value = v

    @property
    def formenctype(self):
        return self.attributes['formenctype'].value

    @formenctype.setter
    def formenctype(self, v):
        self.attributes['formenctype'].value = v

    @property
    def disabled(self):
        return self.attributes['disabled'].value

    @disabled.setter
    def disabled(self, v):
        self.attributes['disabled'].value = v

    @property
    def alt(self):
        return self.attributes['alt'].value

    @alt.setter
    def alt(self, v):
        self.attributes['alt'].value = v

    @property
    def width(self):
        return self.attributes['width'].value

    @width.setter
    def width(self, v):
        self.attributes['width'].value = v

    @property
    def autocomplete(self):
        return self.attributes['autocomplete'].value

    @autocomplete.setter
    def autocomplete(self, v):
        self.attributes['autocomplete'].value = v

    @property
    def value(self):
        return self.attributes['value'].value

    @value.setter
    def value(self, v):
        self.attributes['value'].value = v

    @property
    def formmethod(self):
        return self.attributes['formmethod'].value

    @formmethod.setter
    def formmethod(self, v):
        self.attributes['formmethod'].value = v

class ths(elements):
    pass

class th(element):
    @property
    def scope(self):
        return self.attributes['scope'].value

    @scope.setter
    def scope(self, v):
        self.attributes['scope'].value = v

    @property
    def colspan(self):
        return self.attributes['colspan'].value

    @colspan.setter
    def colspan(self, v):
        self.attributes['colspan'].value = v

    @property
    def bgcolor(self):
        return self.attributes['bgcolor'].value

    @bgcolor.setter
    def bgcolor(self, v):
        self.attributes['bgcolor'].value = v

    @property
    def align(self):
        return self.attributes['align'].value

    @align.setter
    def align(self, v):
        self.attributes['align'].value = v

    @property
    def headers(self):
        return self.attributes['headers'].value

    @headers.setter
    def headers(self, v):
        self.attributes['headers'].value = v

    @property
    def rowspan(self):
        return self.attributes['rowspan'].value

    @rowspan.setter
    def rowspan(self, v):
        self.attributes['rowspan'].value = v

    @property
    def background(self):
        return self.attributes['background'].value

    @background.setter
    def background(self, v):
        self.attributes['background'].value = v

class tabledatas(elements):
    pass

class tabledata(element):
    """ The HTML <td> element defines a cell of a table that contains
    data. It participates in the table model.

    https://developer.mozilla.org/en-US/docs/Web/HTML/Element/td
    """

    tag = 'td'
    @property
    def colspan(self):
        return self.attributes['colspan'].value

    @colspan.setter
    def colspan(self, v):
        self.attributes['colspan'].value = v

    @property
    def headers(self):
        return self.attributes['headers'].value

    @headers.setter
    def headers(self, v):
        self.attributes['headers'].value = v

    @property
    def rowspan(self):
        return self.attributes['rowspan'].value

    @rowspan.setter
    def rowspan(self, v):
        self.attributes['rowspan'].value = v

class theads(elements):
    pass

class thead(element):
    @property
    def align(self):
        return self.attributes['align'].value

    @align.setter
    def align(self, v):
        self.attributes['align'].value = v

class metas(elements):
    pass

class meta(element):
    isvoid = True
    @property
    def charset(self):
        return self.attributes['charset'].value

    @charset.setter
    def charset(self, v):
        self.attributes['charset'].value = v

    @property
    def content(self):
        return self.attributes['content'].value

    @content.setter
    def content(self, v):
        self.attributes['content'].value = v

    @property
    def name(self):
        return self.attributes['name'].value

    @name.setter
    def name(self, v):
        self.attributes['name'].value = v

    @property
    def http_equiv(self):
        return self.attributes['http-equiv'].value

    @http_equiv.setter
    def http_equiv(self, v):
        self.attributes['http-equiv'].value = v

class styles(elements):
    pass

class style(element):
    @property
    def type(self):
        return self.attributes['type'].value

    @type.setter
    def type(self, v):
        self.attributes['type'].value = v

    @property
    def media(self):
        return self.attributes['media'].value

    @media.setter
    def media(self, v):
        self.attributes['media'].value = v

    @property
    def scoped(self):
        return self.attributes['scoped'].value

    @scoped.setter
    def scoped(self, v):
        self.attributes['scoped'].value = v

class datas(elements):
    pass

class data(element):
    @property
    def value(self):
        return self.attributes['value'].value

    @value.setter
    def value(self, v):
        self.attributes['value'].value = v

class labels(elements):
    pass

class label(element):
    @property
    def for_(self):
        return self.attributes['for'].value

    @for_.setter
    def for_(self, v):
        self.attributes['for'].value = v

    @property
    def form(self):
        return self.attributes['form'].value

    @form.setter
    def form(self, v):
        self.attributes['form'].value = v

class detailss(elements):
    pass

class details(element):
    @property
    def open(self):
        return self.attributes['open'].value

    @open.setter
    def open(self, v):
        self.attributes['open'].value = v

class tables(elements):
    pass

class table(element):
    @property
    def bgcolor(self):
        return self.attributes['bgcolor'].value

    @bgcolor.setter
    def bgcolor(self, v):
        self.attributes['bgcolor'].value = v

    @property
    def summary(self):
        return self.attributes['summary'].value

    @summary.setter
    def summary(self, v):
        self.attributes['summary'].value = v

    @property
    def align(self):
        return self.attributes['align'].value

    @align.setter
    def align(self, v):
        self.attributes['align'].value = v

    @property
    def border(self):
        return self.attributes['border'].value

    @border.setter
    def border(self, v):
        self.attributes['border'].value = v

    @property
    def background(self):
        return self.attributes['background'].value

    @background.setter
    def background(self, v):
        self.attributes['background'].value = v


class tablerows(elements):
    pass

class tablerow(element):
    tag = 'tr'

class selects(elements):
    pass

class select(element):
    @property
    def selected(self):
        r = list()
        for el in self:
            if not isinstance(el, option):
                continue

            if el.selected is not undef:
                el.append(el.value)

        return r

    @selected.setter
    def selected(self, v):
        for el in self:
            if not isinstance(el, option):
                continue

            el.selected = False

            if el.value in v:
                el.selected = True
            
    @property
    def required(self):
        return self.attributes['required'].value

    @required.setter
    def required(self, v):
        self.attributes['required'].value = v

    @property
    def multiple(self):
        return self.attributes['multiple'].value

    @multiple.setter
    def multiple(self, v):
        self.attributes['multiple'].value = v

    @property
    def autofocus(self):
        return self.attributes['autofocus'].value

    @autofocus.setter
    def autofocus(self, v):
        self.attributes['autofocus'].value = v

    @property
    def size(self):
        return self.attributes['size'].value

    @size.setter
    def size(self, v):
        self.attributes['size'].value = v

    @property
    def form(self):
        return self.attributes['form'].value

    @form.setter
    def form(self, v):
        self.attributes['form'].value = v

    @property
    def name(self):
        return self.attributes['name'].value

    @name.setter
    def name(self, v):
        self.attributes['name'].value = v

    @property
    def disabled(self):
        return self.attributes['disabled'].value

    @disabled.setter
    def disabled(self, v):
        self.attributes['disabled'].value = v

    @property
    def autocomplete(self):
        return self.attributes['autocomplete'].value

    @autocomplete.setter
    def autocomplete(self, v):
        self.attributes['autocomplete'].value = v

class optgroups(elements):
    pass

class optgroup(element):
    @property
    def label(self):
        return self.attributes['label'].value

    @label.setter
    def label(self, v):
        self.attributes['label'].value = v

    @property
    def disabled(self):
        return self.attributes['disabled'].value

    @disabled.setter
    def disabled(self, v):
        self.attributes['disabled'].value = v

class bgsounds(elements):
    pass

class bgsound(element):
    @property
    def loop(self):
        return self.attributes['loop'].value

    @loop.setter
    def loop(self, v):
        self.attributes['loop'].value = v

class basefonts(elements):
    pass

class basefont(element):
    @property
    def color(self):
        return self.attributes['color'].value

    @color.setter
    def color(self, v):
        self.attributes['color'].value = v

class qs(elements):
    pass

class q(element):
    @property
    def cite(self):
        return self.attributes['cite'].value

    @cite.setter
    def cite(self, v):
        self.attributes['cite'].value = v

class sources(elements):
    pass

class source(element):
    @property
    def type(self):
        return self.attributes['type'].value

    @type.setter
    def type(self, v):
        self.attributes['type'].value = v

    @property
    def src(self):
        return self.attributes['src'].value

    @src.setter
    def src(self, v):
        self.attributes['src'].value = v

    @property
    def media(self):
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
        return self.attributes['srcset'].value

    @srcset.setter
    def srcset(self, v):
        self.attributes['srcset'].value = v

class scripts(elements):
    pass

class script(element):
    @property
    def crossorigin(self):
        return self.attributes['crossorigin'].value

    @crossorigin.setter
    def crossorigin(self, v):
        self.attributes['crossorigin'].value = v

    @property
    def referrerpolicy(self):
        return self.attributes['referrerpolicy'].value

    @referrerpolicy.setter
    def referrerpolicy(self, v):
        self.attributes['referrerpolicy'].value = v

    @property
    def integrity(self):
        return self.attributes['integrity'].value

    @integrity.setter
    def integrity(self, v):
        self.attributes['integrity'].value = v

    @property
    def defer(self):
        return self.attributes['defer'].value

    @defer.setter
    def defer(self, v):
        self.attributes['defer'].value = v

    @property
    def type(self):
        return self.attributes['type'].value

    @type.setter
    def type(self, v):
        self.attributes['type'].value = v

    @property
    def charset(self):
        return self.attributes['charset'].value

    @charset.setter
    def charset(self, v):
        self.attributes['charset'].value = v

    @property
    def src(self):
        return self.attributes['src'].value

    @src.setter
    def src(self, v):
        self.attributes['src'].value = v

    @property
    def importance(self):
        return self.attributes['importance'].value

    @importance.setter
    def importance(self, v):
        self.attributes['importance'].value = v

    @property
    def language(self):
        return self.attributes['language'].value

    @language.setter
    def language(self, v):
        self.attributes['language'].value = v

    @property
    def async(self):
        return self.attributes['async'].value

    @async.setter
    def async(self, v):
        self.attributes['async'].value = v

class videos(elements):
    pass

class video(element):
    @property
    def crossorigin(self):
        return self.attributes['crossorigin'].value

    @crossorigin.setter
    def crossorigin(self, v):
        self.attributes['crossorigin'].value = v

    @property
    def loop(self):
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
        return self.attributes['height'].value

    @height.setter
    def height(self, v):
        self.attributes['height'].value = v

    @property
    def src(self):
        return self.attributes['src'].value

    @src.setter
    def src(self, v):
        self.attributes['src'].value = v

    @property
    def controls(self):
        return self.attributes['controls'].value

    @controls.setter
    def controls(self, v):
        self.attributes['controls'].value = v

    @property
    def poster(self):
        return self.attributes['poster'].value

    @poster.setter
    def poster(self, v):
        self.attributes['poster'].value = v

    @property
    def width(self):
        return self.attributes['width'].value

    @width.setter
    def width(self, v):
        self.attributes['width'].value = v

    @property
    def autoplay(self):
        return self.attributes['autoplay'].value

    @autoplay.setter
    def autoplay(self, v):
        self.attributes['autoplay'].value = v

    @property
    def muted(self):
        return self.attributes['muted'].value

    @muted.setter
    def muted(self, v):
        self.attributes['muted'].value = v

    @property
    def preload(self):
        return self.attributes['preload'].value

    @preload.setter
    def preload(self, v):
        self.attributes['preload'].value = v

class marquees(elements):
    pass

class marquee(element):
    @property
    def bgcolor(self):
        return self.attributes['bgcolor'].value

    @bgcolor.setter
    def bgcolor(self, v):
        self.attributes['bgcolor'].value = v

    @property
    def loop(self):
        return self.attributes['loop'].value

    @loop.setter
    def loop(self, v):
        self.attributes['loop'].value = v

class htmls(elements):
    pass

class html(element):
    def __init__(self, html=None, ids=True, *args, **kwargs):
        if isinstance(html, str):
            # Morph the object into an `elements` object
            self.__class__ = elements
            super(elements, self).__init__(*args, **kwargs)

            # Assume the input st is HTML and convert the elements in
            # the HTML sting into a collection of `elements` objects.
            prs = _htmlparser(convert_charrefs=False, ids=ids)
            prs.feed(html)
            if prs.stack:
                raise HtmlParseError('Unclosed tag', frm=prs.stack[-1])
                
            # The parse HTML elements tree becomes this `elements`
            # collection's constituents.
            self += prs.elements
        else:
            super().__init__(*args, **kwargs)

    @property
    def manifest(self):
        return self.attributes['manifest'].value

    @manifest.setter
    def manifest(self, v):
        self.attributes['manifest'].value = v

class _htmlparser(HTMLParser):
    def __init__(self, ids=True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ids = ids
        self.elements = elements()
        self.stack = list()

    def handle_starttag(self, tag, attrs):
        el = elements.getby(tag=tag)
        if not el:
            raise NotImplementedError(
                'The <%s> tag has no DOM implementation' % tag
            )
        el = el(id=self.ids)
        for attr in attrs:
            el.attributes[attr[0]] = attr[1]

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
        try:
            cur = self.stack[-1]
        except IndexError:
            self.elements += comment(data)
        else:
            cur[0] += comment(data)

    def handle_endtag(self, tag):
        try:
            cur = self.stack[-1]
        except IndexError:
            pass
        else:
            if cur[0].tag == tag:
                self.stack.pop()

    def handle_data(self, data):
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

    def handle_decl(self, decl):
        raise NotImplementedError(
            'HTML doctype declaration are not implemented'
        )

    def unknown_decl(self, data):
        raise NotImplementedError(
            'HTML doctype declaration are not implemented'
        )

    def handle_pi(self, decl):
        raise NotImplementedError(
            'Processing instructions are not implemented'
        )

class h1s(elements):
    pass

class h1(element):
    """ <h1> is the highest section level heading.
    """
    pass

class h2s(elements):
    pass

class h2(element):
    """ <h2> is the second highest section level heading.
    """
    pass

class h3s(elements):
    pass

class h3(element):
    """ <h3> is the third highest section level heading.
    """
    pass

class h4s(elements):
    pass

class h4(element):
    """ <h4> is the fourth highest section level heading.
    """
    pass

class h5s(elements):
    pass

class h5(element):
    """ <h5> is the fifth highest section level heading.
    """
    pass

class h6s(elements):
    pass

class h6(element):
    """ <h6> is the six highest section level heading.
    """
    pass

heading1 = h1
heading2 = h2
heading3 = h3
heading4 = h4
heading5 = h5
heading6 = h6

class heads(elements):
    pass

class head(element):
    pass

class hrs(elements):
    pass

class hr(element):
    isvoid = True
    @property
    def align(self):
        return self.attributes['align'].value

    @align.setter
    def align(self, v):
        self.attributes['align'].value = v

    @property
    def color(self):
        return self.attributes['color'].value

    @color.setter
    def color(self, v):
        self.attributes['color'].value = v

hrules = hrs
hrule = hr

class fonts(elements):
    pass

class font(element):
    @property
    def color(self):
        return self.attributes['color'].value

    @color.setter
    def color(self, v):
        self.attributes['color'].value = v

class areas(elements):
    pass

class area(element):
    @property
    def referrerpolicy(self):
        return self.attributes['referrerpolicy'].value

    @referrerpolicy.setter
    def referrerpolicy(self, v):
        self.attributes['referrerpolicy'].value = v

    @property
    def target(self):
        return self.attributes['target'].value

    @target.setter
    def target(self, v):
        self.attributes['target'].value = v

    @property
    def coords(self):
        return self.attributes['coords'].value

    @coords.setter
    def coords(self, v):
        self.attributes['coords'].value = v

    @property
    def hreflang(self):
        return self.attributes['hreflang'].value

    @hreflang.setter
    def hreflang(self, v):
        self.attributes['hreflang'].value = v

    @property
    def ping(self):
        return self.attributes['ping'].value

    @ping.setter
    def ping(self, v):
        self.attributes['ping'].value = v

    @property
    def media(self):
        return self.attributes['media'].value

    @media.setter
    def media(self, v):
        self.attributes['media'].value = v

    @property
    def href(self):
        return self.attributes['href'].value

    @href.setter
    def href(self, v):
        self.attributes['href'].value = v

    @property
    def alt(self):
        return self.attributes['alt'].value

    @alt.setter
    def alt(self, v):
        self.attributes['alt'].value = v

    @property
    def download(self):
        return self.attributes['download'].value

    @download.setter
    def download(self, v):
        self.attributes['download'].value = v

    @property
    def rel(self):
        return self.attributes['rel'].value

    @rel.setter
    def rel(self, v):
        self.attributes['rel'].value = v

    @property
    def shape(self):
        return self.attributes['shape'].value

    @shape.setter
    def shape(self, v):
        self.attributes['shape'].value = v

class colgroups(elements):
    pass

class colgroup(element):
    @property
    def bgcolor(self):
        return self.attributes['bgcolor'].value

    @bgcolor.setter
    def bgcolor(self, v):
        self.attributes['bgcolor'].value = v

    @property
    def span(self):
        return self.attributes['span'].value

    @span.setter
    def span(self, v):
        self.attributes['span'].value = v

    @property
    def align(self):
        return self.attributes['align'].value

    @align.setter
    def align(self, v):
        self.attributes['align'].value = v

class iframes(elements):
    pass

class iframe(element):
    @property
    def csp(self):
        return self.attributes['csp'].value

    @csp.setter
    def csp(self, v):
        self.attributes['csp'].value = v

    @property
    def referrerpolicy(self):
        return self.attributes['referrerpolicy'].value

    @referrerpolicy.setter
    def referrerpolicy(self, v):
        self.attributes['referrerpolicy'].value = v

    @property
    def loading(self):
        return self.attributes['loading'].value

    @loading.setter
    def loading(self, v):
        self.attributes['loading'].value = v

    @property
    def srcdoc(self):
        return self.attributes['srcdoc'].value

    @srcdoc.setter
    def srcdoc(self, v):
        self.attributes['srcdoc'].value = v

    @property
    def height(self):
        return self.attributes['height'].value

    @height.setter
    def height(self, v):
        self.attributes['height'].value = v

    @property
    def src(self):
        return self.attributes['src'].value

    @src.setter
    def src(self, v):
        self.attributes['src'].value = v

    @property
    def importance(self):
        return self.attributes['importance'].value

    @importance.setter
    def importance(self, v):
        self.attributes['importance'].value = v

    @property
    def allow(self):
        return self.attributes['allow'].value

    @allow.setter
    def allow(self, v):
        self.attributes['allow'].value = v

    @property
    def name(self):
        return self.attributes['name'].value

    @name.setter
    def name(self, v):
        self.attributes['name'].value = v

    @property
    def align(self):
        return self.attributes['align'].value

    @align.setter
    def align(self, v):
        self.attributes['align'].value = v

    @property
    def width(self):
        return self.attributes['width'].value

    @width.setter
    def width(self, v):
        self.attributes['width'].value = v

    @property
    def sandbox(self):
        return self.attributes['sandbox'].value

    @sandbox.setter
    def sandbox(self, v):
        self.attributes['sandbox'].value = v

class pres(elements):
    pass

class pre(element):
    pass

class strongs(elements):
    pass

class strong(element):
    pass

class ss(elements):
    pass

class s(element):
    """ The HTML <s> element renders text with a strikethrough, or a
    line through it. Use the <s> element to represent things that are no
    longer relevant or no longer accurate. However, <s> is not
    appropriate when indicating document edits; for that, use the <del>
    and <ins> elements, as appropriate.

    https://developer.mozilla.org/en-US/docs/Web/HTML/Element/s
    """
    pass

strikethroughs = ss
strikethrough = s

class ems(elements):
    """ A collection of ``emphasis`` elements.
    """
    pass

class em(element):
    """ The HTML <em> element which marks text that has stress emphasis.
    This element can be nested, with each level of nesting
    indicating a greater degree of emphasis. 

    See: https://developer.mozilla.org/en-US/docs/Web/HTML/Element/em
    """
    pass

emphases = ems
emphasis = em

class is_(elements):
    pass

class i(element):
    """ The HTML <i> element represents a range of text that is set off
    from the normal text for some reason. Some examples include
    technical terms, foreign language phrases, or fictional character
    thoughts. It is typically displayed in italic type.

    https://developer.mozilla.org/en-US/docs/Web/HTML/Element/i
    """
    pass

italics = is_
italic = i

class bs(elements):
    pass

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
    pass

bolds = bs
bold = b

class divs(elements):
    pass

class div(element):
    """ The HTML Content Division element (<div>) is the generic
    container for flow content. It has no effect on the content or
    layout until styled using CSS.
    """
    pass

divisions = divs
division = div

class spans(elements):
    pass

class span(element):
    pass

class mains(elements):
    pass

class main(element):
    pass

class dls(elements):
    pass

class dl(element):
    """ The HTML <dl> element represents a description list. The element
    encloses a list of groups of terms (specified using the <dt>
    element) and descriptions (provided by <dd> elements). Common uses
    for this element are to implement a glossary or to display metadata
    (a list of key-value pairs).

    https://developer.mozilla.org/en-US/docs/Web/HTML/Element/dl
    """
    pass

descriptionlists = dls
descriptionlist = dl

class dts(elements):
    pass

class dt(element):
    """ The HTML <dt> element specifies a term in a description or
    definition list, and as such must be used inside a <dl> element. It
    is usually followed by a <dd> element; however, multiple <dt>
    elements in a row indicate several terms that are all defined by the
    immediate next <dd> element.

    https://developer.mozilla.org/en-US/docs/Web/HTML/Element/dt
    """
    pass

definitionlists = dts
definitionlist  = dt

class dds(elements):
    pass

class dd(element):
    """ The HTML <dd> element provides the description, definition, or
    value for the preceding term (<dt>) in a description list (<dl>).

    https://developer.mozilla.org/en-US/docs/Web/HTML/Element/dd
    """
    pass

descriptiondetails = dds
descriptiondetail  = dd


class codes(elements):
    pass

class code(element):
    pass

class codeblocks(codes):
    pass

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
    # would probably be equivelent to '.codeblock'.
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.classes += 'block'

class markdown(elements):
    def __init__(self, text):
        super().__init__(self)
        self += html(Markdown()(dedent(text).strip()))

class selectors(entities.entities):
    """ Represents a seection group of CSS3 selectors. Selection groups
    are seperated by commas in CSS3 selector strings. For example, in
    the string::

        'p, div'

    the p would represent one entry of the selector group (represented
    by a ``selector`` object) and div would represent an second entry.
    """

    class token(tuple):
        def __new__(cls, type, value, pos):
            obj = tuple.__new__(cls, (type, value))
            obj.pos = pos
            return obj

        def __repr__(self):
            return "<%s '%s' at %i>" % (self.type, self.value, self.pos)

        def is_delim(self, *values):
            return self.type == 'DELIM' and self.value in values

        type = property(operator.itemgetter(0))
        value = property(operator.itemgetter(1))

        def css(self):
            if self.type == 'STRING':
                return repr(self.value)
            else:
                return self.value

    class eof(token):
        def __new__(cls, pos):
            return selectors.token.__new__(cls, 'EOF', None, pos)

        def __repr__(self):
            return '<%s at %i>' % (self.type, self.pos)


    def __init__(self, sel=None, *args, **kwargs):
        """ Instantiate and parse the CSS3 selector string (``sel``), i.e., ::

            p#pid, div.my-class
        """
        super().__init__(*args, **kwargs)
        self._sel = sel.strip()
        self._parse()
    
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
        err = CssSelectorParseError
        badtrail = set(string.punctuation) - set(list(')]*'))
        badlead = '>+~'

        if not self._sel or not self._sel.strip():
            raise err('Empty selector')

        valid_identifier = re.compile('^[a-zA-Z\-_][a-zA-Z0-9\-_]')
        starts_with_hyphen_then_number = re.compile('^\-[0-9]')

        def demand_valid_identifiers(id):
            def throw():
                raise err('Invalid identifier', tok)

            if not valid_identifier.match(id):
                throw()

            if id.startswith('--'):
                throw()
                
            if starts_with_hyphen_then_number.match(id):
                throw()

        def element(element):
            if not element.isalnum() and element != '*':
                raise ValueError('Elements must be alphanumeric')

            el = selector.element()
            el.element = element
            el.combinator = comb
            return el

        sel = selector()
        self += sel
        el = comb = attr = cls = pcls = args = None

        prev = None
        for tok in self.tokenize(self._sel):
            if isinstance(tok, selectors.eof):
                if attr:
                    raise err('Attribute not closed', tok)

                if not el:
                    raise err( 'Attribute not closed', tok)

                if prev.value in badtrail: 
                    raise err(tok)

                if pcls and not pcls.hasvalidname:
                    raise err(
                        'Invalid pseudoclass "%s"' % pcls.value, tok
                    )
                break

            if not prev and tok.value in badlead:
                raise err(tok)

            if args:
                if tok.value == ')':
                    args = None
                elif tok.type == 'HASH':
                    args += '#' + tok.value
                    continue
                elif tok.type != 'S':
                    args += tok.value
                    continue

            if tok.type == 'IDENT':
                if el:
                    if attr:
                        for attr1 in ['key', 'value']:
                            if getattr(attr, attr1) is None:
                                setattr(attr, attr1, tok.value)
                                break
                        else:
                            # NOTE We probably will never get here, but
                            # just in case...
                            CssSelectorParseError(tok)
                    elif cls:
                        cls.value = tok.value
                    elif pcls:
                        pcls.value = tok.value
                else:
                    try:
                        el = element(tok.value)
                    except Exception as ex:
                        msg = (
                           str(ex) +
                           '\nYou may have forgotten brackets around '
                           'an attribute selector.'
                        )
                        raise err(msg, tok)
                    sel.elements += el

            elif tok.type == 'STRING':
                if attr:
                    attr.value = tok.value
            elif tok.type == 'HASH':
                if cls or attr:
                    raise err(tok)
                    
                if not el:
                    # Universal selector was implied (#myid) so create it.
                    el = element('*')
                    sel.elements += el

                if not el.id:
                    demand_valid_identifiers(tok.value)

                el.id = tok.value

            elif tok.type == 'S':
                if el:
                    if not args:
                        el = None
                        comb = selector.element.Descendant
                if cls and not cls.value:
                    raise err(tok)
                    
            elif tok.type == 'NUMBER':
                demand_valid_identifiers(tok.value)

            elif tok.type == 'DELIM':    
                v = tok.value
                if el:
                    if not attr and v in '>+~':
                        el = None
                        comb = selector.element.str2comb(v)
                    elif not (attr or pcls or cls):
                        if v not in ''.join('*[:.,'):
                            raise err(tok)

                    if cls and cls.value is None:
                        raise err(tok)

                    if pcls and pcls.value is None:
                        raise err(tok)
                else:
                    if v in '>+~':
                        comb = selector.element.str2comb(v)
                    else:
                        if v not in '*[:.':
                            raise err(tok)

                if not attr and v == ']':
                    raise err(tok)

                if tok.value == ',':
                    sel = selector()
                    self += sel
                    el = comb = attr = cls = pcls = args = None

                if attr:
                    if tok.value == ']':
                        if attr.operator and attr.value is None:
                            raise err(tok)

                        if attr.key is None:
                            raise err(tok)

                        attr = None
                    elif tok.value == '[':
                        raise err('Attribute already opened', tok)
                    else:
                        if attr.operator is None:
                            attr.operator = ''

                        attr.operator += tok.value

                        op = attr.operator

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
                else:
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

                if tok.value == '.':
                    if not el:
                        # The universal selector was implied (.my-class)
                        # so create it.
                        el = element('*')
                        sel.elements += el
                    cls = selector.class_()
                    el.classes += cls
                elif tok.value == ':':
                    if not el:
                        # The universal selector was implied (.root)
                        # so create it.
                        el = element('*')
                        sel.elements += el
                    pcls = selector.pseudoclass()
                    el.pseudoclasses += pcls
                    comb = attr = cls = args = None
                elif tok.value == '(':
                    args = pcls.arguments
                elif tok.value in ('+',  '-'):
                    if args:
                        args += tok.value
                    

            prev = tok

        self.demand()

    def demand(self):
        """ Raise error if self is invalid
        """
        for sel in self:
            sel.demand()

    def match(self, els):
        r = elements()
        for sel in self:
            r += sel.match(els)

        return r

    def __repr__(self):
        return ', '.join(str(x) for x in self)

    def __str__(self):
        return repr(self)

class selector(entities.entity):
    class _simples(entities.entities):
        def __init__(self, *args, **kwargs):
            self.element = kwargs.pop('el')
            super().__init__(*args, **kwargs)

        def __str__(self):
            return repr(self)

        def __repr__(self):
            return ' '.join(str(x) for x in self)

        def __iadd__(self, smp):
            super().__iadd__(smp)
            smp.element = self.element
            return self

    class simple(entities.entity):
        def __init__(self):
            self.element = None

        def __str__(self):
            return repr(self)

    class elements(entities.entities):
        def demand(self):
            """ Raise error if self is invalid
            """
            for el in self:
                el.demand()

        def __repr__(self):
            r = str()
            for i, el in self.enumerate():
                if i:
                    r += ' '
                r += str(el)
            return r

    class element(entities.entity):
        Descendant         =  0
        Child              =  1
        NextSibling        =  2
        SubsequentSibling  =  3

        def __init__(self):
            self.element        =  None
            self.combinator     =  None
            self.attributes     =  selector.attributes(el=self)
            self.classes        =  selector.classes(el=self)
            self.pseudoclasses  =  selector.pseudoclasses(el=self)
            self.id             =  None

        @staticmethod
        def comb2str(comb):
            return [' ', '>', '+', '~'][comb]

        @staticmethod
        def str2comb(comb):
            return [' ', '>', '+', '~'].index(comb)

        def match(self, els):
            if isinstance(els, element):
                return bool(self.match([els]).count)
            
            if els is None:
                return False

            r = elements()

            for el in els:
                if self.element.lower() not in ('*', el.tag):
                    continue

                if not self.classes.match(el):
                    continue

                if not self.attributes.match(el):
                    continue

                if not self.pseudoclasses.match(el):
                    continue

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
            return self.comb2str(self.combinator)


        def __repr__(self):
            r = str()
            if self.combinator not in (None, selector.element.Descendant):
                r += self.str_combinator + ' '

            if self.element is not None:
                r += self.element

            if self.id is not None:
                r += '#' + self.id

            if self.attributes.count:
                r += str(self.attributes)

            if self.classes.count:
                r += str(self.classes)

            if self.pseudoclasses.count:
                r += str(self.pseudoclasses)

            return r

    def __init__(self):
        self.elements = selector.elements()

    def match(self, els, el=None, smps=None):
        last = self.elements.last
        els1 = last.match(els.getchildren())
        rms = elements()

        for el1 in els1:
            comb = last.combinator
            orig = el1
            for i, smp in enumerate(self.elements[:-1].reversed()):
                if comb in (selector.element.Descendant, None):
                    for i, an in el1.ancestors.enumerate():
                        if smp.match(an):
                            el1 = an
                            break
                    else:
                        rms += orig
                        break
                elif comb == selector.element.Child:
                    an = el1.parent
                    if smp.match(an):
                        el1 = an
                    else:
                        rms += orig
                        break
                elif comb == selector.element.NextSibling:
                    if smp.match(el1.previous):
                        el1 = el1.previous
                    else:
                        rms += orig
                        break
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
        """ Raise error if self is invalid
        """
        self.elements.demand()

    def __repr__(self):
        return repr(self.elements)

    def __str__(self):
        return repr(self)

    class attributes(_simples):
        def __repr__(self):
            return ''.join(str(x) for x in self)

        def match(self, el):
            return all(x.match(el) for x in self)

        def demand(self):
            pass

    class attribute(simple):
        def __init__(self):
            self.key       =  None
            self.operator  =  None
            self.value     =  None

        def __repr__(self):
            k   =  self.key       or  ''
            op  =  self.operator  or  ''
            v   =  self.value     or  ''
            return '[%s%s%s]' % (k, op, v)

        def match(self, el):
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
        def __repr__(self):
            return ''.join(str(x) for x in self)

        def match(self, el):
            return all(x.match(el) for x in self)

        def demand(self):
            pass

    class class_(simple):
        def __init__(self):
            self.value = None

        def __repr__(self):
            return '.' + self.value

        def match(self, el):
            return self.value in el.classes

    class pseudoclasses(_simples):
        def __repr__(self):
            return ''.join(str(x) for x in self)

        def match(self, el):
            return all(x.match(el) for x in self)

        def demand(self):
            for pcls in self:
                pcls.demand()

    class pseudoclass(simple):
        validnames = (
            'root',         'nth-child',         'nth-last-child',
            'nth-of-type',  'nth-last-of-type',  'first-child',
            'last-child',   'first-of-type',     'last-of-type',
            'only-child',   'only-of-type',      'empty',
            'not',          'lang',
        )

        class arguments(element):
            def __init__(self, pcls):
                self.string       =  str()
                self._a           =  None
                self._b           =  None
                self.pseudoclass  =  pcls

            def __iadd__(self, str):
                self.string += str
                return self

            @property
            def a(self):
                self._parse()
                return self._a

            @property
            def b(self):
                self._parse()
                return self._b

            @property
            def c(self):
                if self.pseudoclass.value != 'lang':
                    raise NotImplementedError(
                        'Only lang pseudoclass has C argument'
                    )
                return self.string

            @property
            def selectors(self):
                if self.pseudoclass.value.lower() != 'not':
                    return None

                # For :not() pseudoclass, parse the arguments to
                # :not() like any other selector. 
                sels = selectors(self.string)

                # The parser will add a universal selector (*) to each
                # simple selector. 
                el = self.pseudoclass.element.element
                if el != '*':
                    for sel in sels:
                        for el1 in sel.elements:
                            el1.element = el

                return sels

            def _parse(self):
                err = CssSelectorParseError
                if self.pseudoclass.value == 'lang':
                    return

                a = b = None
                s = self.string
                if s.lower() == 'odd':
                    a, b = 2, 1
                elif s.lower() == 'even':
                    a, b = 2, 0
                elif len(s) == 1:
                    if s.lower() == 'n':
                        a, b = 1, 0
                    else:
                        try:
                            i = int(s)
                        except ValueError:
                            pass
                        else:
                            a, b = 0, i
                elif len(s) == 2:
                    try:
                        # E:nth-child(2n)
                        if s[0] in ('+', '-'):
                            try:
                                i = int(s)
                            except ValueError:
                                pass
                            else:
                                a, b = 0, i
                        elif s[1].lower() != 'n':
                            raise err(
                                'Invalid pseudoclass argument: "%s"' % s
                            )
                        else:
                            a, b = int(s[0]), 0
                    except ValueError:
                        raise err(
                            'Invalid pseudoclass argument: "%s"' % s
                        )
                else:
                    m = re.match(
                        '(\+|-)?([0-9]+)?[nN] *(\+|-) *([0-9])+$', s
                    )
                    if m:
                        gs = m.groups()

                        if len(gs) == 4:
                            if gs[0] is None:
                                gs = list(gs)
                                gs[0] = '+'

                            if gs[0] is not None and gs[1] is not None:
                                a = int(gs[0] + gs[1])

                            # gs[0] would be None for 'n+0'
                            if a is None:
                                a = int(gs[0] + '1')

                            b = int(gs[2] + gs[3])

                self._a, self._b = a, b

            def __repr__(self):
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

        def __init__(self):
            super().__init__()
            self.value = None
            self.arguments = selector.pseudoclass.arguments(self)

        def demand(self):
            err = CssSelectorParseError
            if self.value.lower().startswith('nth-'):
                if self.arguments.a is None or self.arguments.b is None:
                    raise err(
                        'Error in argument(s) to pseudoclass '
                        '"%s"' % self.value
                    )
            elif self.value.lower() == 'not':
                # If the pseudoclass is 'not', then invoke its
                # 'arguments.selectors'. That will cause not's arguments
                # to be parse. If there is a pares error in not's
                # arguments (stored as a str in self.arguments.string),
                # invoking this property will raise the
                # CssSelectorParseError.
                self.arguments.selectors

        def __repr__(self):
            r = ':' + self.value
            r += repr(self.arguments)
            return r

        def _match_lang(self, el):
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
            return el is el.root

        def _match_nth_child_starting_at(self, begining, el, oftype):
            a, b = self.arguments.a, self.arguments.b

            sibs = el.getsiblings(includeself=True)
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
            return self._match_nth_child_starting_at(
                begining=True, el=el, oftype=False
            )

        def _match_nth_last_child(self, el):
            return self._match_nth_child_starting_at(
                begining=False, el=el, oftype=False
            )

        def _match_nth_of_type(self, el):
            return self._match_nth_child_starting_at(
                begining=True, el=el, oftype=True
            )

        def _match_nth_last_of_type(self, el):
            return self._match_nth_child_starting_at(
                begining=False, el=el, oftype=True
            )

        def _match_first_child(self, el):
            sibs = el.getsiblings(includeself=True)
            sibs.remove(lambda x: type(x) is text)
            return sibs.first is el

        def _match_last_child(self, el):
            sibs = el.getsiblings(includeself=True)
            sibs.remove(lambda x: type(x) is text)
            return sibs.last is el

        def _match_x_of_type(self, el, last=False):
            sibs = el.getsiblings(includeself=True)
            sibs.remove(lambda x: type(x) is text)

            if last:
                sibs = sibs.reversed()

            for sib in sibs:
                if type(sib) is type(el):
                    return sib is el
                        
            return False

        def _match_first_of_type(self, el):
            return self._match_x_of_type(el=el)

        def _match_last_of_type(self, el):
            return self._match_x_of_type(el=el, last=True)

        def _match_only_child(self, el):
            sibs = el.getsiblings(includeself=True)
            return sibs.where(lambda x: type(x) is not text).hasone

        def _match_only_of_type(self, el):
            sibs = el.getsiblings(includeself=True)
            return sibs.where(lambda x: type(x) is type(el)).hasone

        def _match_empty(self, el):

            # `comments` elements don't matter when it comes to
            # emptiness but `text' elements actually do. This includes
            # text with just whitespace. Processing instructions matter
            # too but we don't support them in the DOM.
            els = el.elements.where(lambda x: type(x) is not comment)
            return els.isempty

        def _match_not(self, el):
            m = self.arguments.selectors[0].elements[0].match
            m = m(el)
            return not m

        def match(self, el):
            if type(el) in (text, comment):
                return False

            pcls = self.value.replace('-', '_').lower()
            
            return getattr(self, '_match_' + pcls)(el)

        @property
        def hasvalidname(self):
            return self.value.lower() in self.validnames

class revisions(entities.entities):
    def __init__(self, el=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.element = el

    def revision(self, type, sub, obj):
        self += revision(type, sub, obj)

class revision(entities.entity):
    Append = 0
    Remove = 1
    def __init__(self, type, sub, obj):
        self.id = uuid.uuid4()
        self.type = type
        self.subject = sub
        self.object = obj

    def __repr__(self):
        r = '%s(type=%s, subject=<%s id="%s">, object=<%s id="%s">)' 
        return r % (
            type(self).__name__,
            self.str_type,
            type(self.subject).__name__,
            self.subject.id,
            type(self.object).__name__,
            self.object.id,
        )

    @property
    def str_type(self):
        return (
            'Append',
            'Remove',
        )[self.type]
            
class AttributeExistsError(Exception):
    pass

class ClassExistsError(Exception):
    pass

class HtmlParseError(Exception):
    def __init__(self, msg=None, frm=None):
        self._frame = frm
        self._msg = msg

    @property
    def line(self):
        frm = self._frame

        if not frm:
            return None

        return frm[1][0]

    @property
    def column(self):
        frm = self._frame

        if not frm:
            return None

        return frm[1][1]

    @property
    def element(self):
        frm = self._frame

        if not frm:
            return None

        return frm[0]
       
    def __str__(self):
        r = self._msg
        if self._frame:

            if self.element:
                r += ' <%s>' % self.element.tag

            r += ' at line %s column %s' % (self.line, self.column)
        return r

class MoveError(ValueError):
    pass

class CssSelectorParseError(SyntaxError):
    def __init__(self, o, tok=None, pos=None):
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
        if self._pos is not None:
            return self._pos

        if self.token:
            return self.token.pos

        return None

