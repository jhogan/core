# vim: set et ts=4 sw=4 fdm=marker

#######################################################################
# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2019
########################################################################

import entities
import textwrap
import orm
import html
from dbg import B

class site(entities.entity):
    def __init__(self, name):
        self.name = name
        self.pages = pages()
        self.headers = headers()

    def header(self):
        return self.headers.default

class pages(entities.entities):
    pass

class page(entities.entity):
    def __init__(self, name):
        self.pages = pages()

class AttributeExistsError(Exception):
    pass

class ClassExistsError(Exception):
    pass

class attributes(entities.entities):
    def __iadd__(self, o):
        if type(o) in (tuple, list):
            o = attribute(o[0], o[1])
        super().__iadd__(o)
        return self

    def append(self, o, v=None, uniq=False, r=None):
        if type(o) is list:
            return super().append(o, uniq, r)
            
        if type(o) is str:
            o = attribute(o, v)

        for attr in self:
            if o.name == attr.name:
                msg = 'Attribute already exists: ' + o.name
                raise AttributeExistsError(msg)

        return super().append(o, uniq, r)

    def __getitem__(self, key):
        if not isinstance(key, str):
            return super().__getitem__(key)

        try:
            ix = self.getindex(key)
        except ValueError as ex:
            attr = None
        else:
            attr = self[ix]


        if attr:
            return attr
        else:
            if key == 'class':
                self += cssclass()
            else:
                self += key, item
            
            return self.last

    def __setitem__(self, key, item):
        if not isinstance(key, str):
            super().__setitem__(key, item)
            
        try:
            ix = self.getindex(key)
        except ValueError as ex:
            attr = None
        else:
            attr = self[ix]

        if attr:
            if isinstance(attr, cssclass):
                attr._classes = item._classes
            else:
                attr.value = item
        else:
            if key == 'class':
                self += cssclass(item)
            else:
                self += key, item

    def brokenrules(self):
        brs = brokenrules()
        if self.value is None:
            brs += 'Value is None'
        return brs
    @property
    def html(self):
        return ' '.join([x.html for x in self if x.isvalid])
        
class attribute(entities.entity):
    def __init__(self, name, v=None):
        self.name = name
        self.value = v

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
        return '%s="%s"' % (self.name, self.value)

class cssclass(attribute):
    def __init__(self, value=None):
        super().__init__('class')

        self._classes = list()

        if value:
            self += value

    def __contains__(self, e):
        return e in self._classes

    def __len__(self):
        return len(self._classes)

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

                    # TODO Remove the brackets to make the argument a generator
                    if any(x.isspace() for x in cls):
                        # TODO Test
                        raise ValueError("CSS classes can't contain whitespace")

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

    def remove(self, *clss):
        for cls in clss:
            del self._classes[cls]

    @property
    def html(self):
        clss = self._classes
        return 'class="%s"' % ' '.join(clss)

    def __repr__(self):
        return '%s(value=%s)' % (type(self).__name__, self._classes)

class elements(entities.entities):
    pass

class element(entities.entity):
    def __init__(self, str=None):
        #self.attributes = attributes()
        if str is not None:
            self.elements += text(str)

    @property
    def elements(self):
        if not hasattr(self, '_elements'):
            self._elements = elements()
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
            self._attributes = attributes()
        return self._attributes

    @attributes.setter
    def attributes(self, v):
        self._attributes = v

    def __iadd__(self, el):
        if type(el) is str:
            el = text(el)

        if not isinstance(el, element):
            raise ValueError('Invalid element type: ' + str(type(el)))

        self.elements += el
        return self

    @property
    def tag(self):
        return type(self).__name__

    @property
    def html(self):
        body = str()
        if isinstance(self, text):
            body = self.html

        for i, el in enumerate(self.elements):
            if body: body += '\n'
            body += el.html

        if isinstance(self, text):
            return body

        body = textwrap.indent(body, '  ')

        r = '<%s'
        args = [self.tag]

        B()
        if any(x for x in self.attributes if x.isvalid):
            r += ' %s'
            args.append(self.attributes.html)

        r += '>\n'
        if body:
            r += '%s\n'
            args += [body]

        r += '</%s>'
        args += [self.tag]

        return r % tuple(args)

    def __repr__(self):
        return str(self)

class paragraphs(elements):
    pass

class paragraph(element):
    def __init__(self, body=None, *args):
        if body is not None:
            if type(body) is str:
                body %= args
            elif args:
                raise ValueError('No args allowed')

            self += body

    @property
    def tag(self):
        return 'p'

class header(element):
    def __init__(self):
        self.logo = None
        self.searchbox = None
        self.notifications = None

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
    def __init__(self, str):
        self._str = str

    def __str__(self):
        return textwrap.dedent(self._str).strip()

    @property
    def html(self):
        return html.escape(
            textwrap.dedent(self._str)
        ).strip()
        
class strong(element):
    pass

class span(element):
    pass


    
    
