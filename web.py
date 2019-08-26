# vim: set et ts=4 sw=4 fdm=marker

#######################################################################r
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

class attributes(entities.entities):
    def __iadd__(self, o):
        if type(o) in (tuple, list):
            o = attribute(o[0], o[1])
        super().__iadd__(o)
        return self

    def append(self, o, v=None, uniq=False, r=None):
        if type(o) is str:
            o = attribute(o, v)

        if self(o.name) is not None:
            msg = 'Attribute already exists: ' + o.name
            raise AttributeExistsError(msg)

        return super().append(o, uniq, r)

class attribute(entities.entity):
    def __init__(self, name, v):
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

class elements(entities.entities):
    pass

class element(entities.entity):
    def __init__(self, str=None):
        self.attributes = attributes()
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
        args = list(self.tag)
        if self.attributes.count:
            r += ' %s'
            args.append(self.attributes)

        r += '>\n%s\n</%s>'
        args += [body, self.tag]

        return r % args

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


    
    
