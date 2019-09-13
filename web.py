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

class undef:
    pass

class classproperty(property):
    # TODO This is in orm.py, too. It should be be moved to a central
    # location.

    ''' Add this decorator to a method and it becomes a class method
    that can be used like a property.'''

    def __get__(self, cls, owner):
        # If cls is not None, it will be the instance. If there is an
        # instance, we want to pass that in instead of the class
        # (owner). This makes it possible for classproperties to act
        # like classproperties and regular properties at the same time.
        # See the conditional at entities.count.
        obj = cls if cls else owner
        return classmethod(self.fget).__get__(None, obj)()

# TODO All html should pass the W3C validation service at:
# https://validator.w3.org/#validate_by_input
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
                self += attribute(key)
            
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

    @property
    def _defined(self):
        return [x for x in self._ls if x.value is not undef]

    def __iter__(self):
        for attr in self._defined:
            yield attr

    def __contains__(self, attr):
        if isinstance(attr, str):
            return attr in [x.name for x in self._defined]
        else:
            return attr in self._defined

    def __len__(self):
        return len(self._defined)

    @property
    def html(self):
        return ' '.join([x.html for x in self if x.isvalid])
        
class attribute(entities.entity):
    def __init__(self, name, v=undef):
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
        if self.value is None:
            return self.name

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
    def value(self):
        if not self._classes:
            return undef
        return ' '.join(self._classes)

    @value.setter
    def value(self, v):
        if v is None:
            self._classes = list()
        elif v is not undef:
            self._classes = v.split()

    @property
    def html(self):
        return 'class="%s"' % self.value

    def __repr__(self):
        return '%s(value=%s)' % (type(self).__name__, self._classes)

class elements(entities.entities):
    @classmethod
    def getby(cls, tag):
        for el in element.__subclasses__():
            if el.tag == tag:
                return el
        return None

class element(entities.entity):
    def __init__(self, str=None):
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

    @classproperty
    def tag(cls):
        if type(cls) is type:
            return cls.__name__
        return type(cls).__name__

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

    def _demandvalid(self, attr):
        try:
            tags = html5attrs[attr]
        except KeyError:
            raise AttributeError(
                'Invalid HTML5 attribute: ' + attr
            )
        else:
            if not(tags == '*' or self.tag in tags.split()):
                raise AttributeError(
                    'Invalid attritute for <%s>' % self.tag
                )

    def __getattr__(self, attr):
        try:
            object.__getattribute__(self, attr)
        except AttributeError:
            self._demandvalid(attr)
            return self.attributes[attr].value

    def __setattr__(self, attr, v):
        try:
            self._demandvalid(attr)
        except AttributeError:
            object.__setattr__(self, attr, v)
        else:
            self.attributes[attr].value = v
                
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

    @classproperty
    def tag(cls):
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

class inputs(elements):
    pass

class input(element):
    pass

class blockquotes(elements):
    pass

class blockquote(element):
    pass

class dels(elements):
    pass

class del_(element):
    pass

class inss(elements):
    pass

class ins(element):
    pass

class qs(elements):
    pass

class q(element):
    pass

class audios(elements):
    pass

class audio(element):
    pass

class videos(elements):
    pass

class video(element):
    pass

class optgroups(elements):
    pass

class optgroup(element):
    pass

class options(elements):
    pass

class option(element):
    pass

class tracks(elements):
    pass

class track(element):
    pass

class tds(elements):
    pass

class td(element):
    pass

class ths(elements):
    pass

class th(element):
    pass

class scripts(elements):
    pass

class script(element):
    pass

class selects(elements):
    pass

class select(element):
    pass

class meters(elements):
    pass

class meter(element):
    pass

class progresss(elements):
    pass

class progress(element):
    pass

class labels(elements):
    pass

class label(element):
    pass

class outputs(elements):
    pass

class output(element):
    pass

class forms(elements):
    pass

class form(element):
    pass

class as_(elements):
    pass

class a(element):
    pass

class areas(elements):
    pass

class area(element):
    pass

class textareas(elements):
    pass

class textarea(element):
    pass

class buttons(elements):
    pass

class button(element):
    pass

class imgs(elements):
    pass

class img(element):
    pass

class times(elements):
    pass

class time(element):
    pass

class iframes(elements):
    pass

class iframe(element):
    pass

class detailss(elements):
    pass

class details(element):
    pass

# TODO Since this would conflict with Python's bulitin `object` object,
# uncomment these and ensure everything works as expected.
'''
class objects(elements):
    pass

class object(element):
    pass
'''

class commands(elements):
    pass

class command(element):
    pass

class cols(elements):
    pass

class col(element):
    pass

class colgroups(elements):
    pass

class colgroup(element):
    pass

class fieldsets(elements):
    pass

class fieldset(element):
    pass

class keygens(elements):
    pass

class keygen(element):
    pass

class metas(elements):
    pass

class meta(element):
    pass

class tables(elements):
    pass

class table(element):
    pass

class basefonts(elements):
    pass

class basefont(element):
    pass

class fonts(elements):
    pass

class font(element):
    pass

class hrs(elements):
    pass

class hr(element):
    pass

class links(elements):
    pass

class link(element):
    pass

class bases(elements):
    pass

class base(element):
    pass

class htmls(elements):
    pass

class html(element):
    pass

class bodys(elements):
    pass

class body(element):
    pass

class marquees(elements):
    pass

class marquee(element):
    pass

class tbodys(elements):
    pass

class tbody(element):
    pass

class tfoots(elements):
    pass

class tfoot(element):
    pass

class trs(elements):
    pass

class tr(element):
    pass

class sources(elements):
    pass

class source(element):
    pass

class maps(elements):
    pass

class map(element):
    pass

class params(elements):
    pass

class param(element):
    pass

class datas(elements):
    pass

class data(element):
    pass

class lis(elements):
    pass

class li(element):
    pass

class ols(elements):
    pass

class ol(element):
    pass

class applets(elements):
    pass

class applet(element):
    pass

class canvass(elements):
    pass

class canvas(element):
    pass

class embeds(elements):
    pass

class embed(element):
    pass

class styles(elements):
    pass

class style(element):
    pass

class menus(elements):
    pass

class menu(element):
    pass

class bgsounds(elements):
    pass

class bgsound(element):
    pass

class captions(elements):
    pass

class caption(element):
    pass

class theads(elements):
    pass

class thead(element):
    pass


    
html5attrs = {
    'accept': 'form input',
    'accept-charset': 'form',
    'accesskey': '*',
    'action': 'form',
    'align': 'applet caption col colgroup hr iframe img table tbody td tfoot  th thead tr',
    'allow': 'iframe',
    'alt': 'applet area img input',
    'async': 'script',
    'autocapitalize': '*',
    'autocomplete': 'form input select textarea',
    'autofocus': 'button input keygen select textarea',
    'autoplay': 'audio video',
    'background': 'body table td th',
    'bgcolor': 'body col colgroup marquee table tbody tfoot td th tr',
    'border': 'img object table',
    'buffered': 'audio video',
    'challenge': 'keygen',
    'charset': 'meta script',
    'checked': 'command input',
    'cite': 'blockquote del ins q',
    'class': '*',
    'code': 'applet',
    'codebase': 'applet',
    'color': 'basefont font hr',
    'cols': 'textarea',
    'colspan': 'td th',
    'content': 'meta',
    'contenteditable': '*',
    'contextmenu': '*',
    'controls': 'audio video',
    'coords': 'area',
    'crossorigin': 'audio img link script video',
    'csp':	'iframe',
    'data': 'object',
    'data-': '*',
    'datetime': 'del ins time',
    'decoding': 'img',
    'default': 'track',
    'defer': 'script',
    'dir': '*',
    'dirname': 'input textarea',
    'disabled': 'button command fieldset input keygen optgroup option select textarea',
    'download': 'a area',
    'draggable': '*',
    'dropzone': '*',
    'enctype': 'form',
    'enterkeyhint': 'textarea',
    'for': 'label output',
    'form': 'button fieldset input keygen label meter object output progress select textarea',
    'formaction': 'input button',
    'formenctype': 'button input',
    'formmethod': 'button input',
    'formnovalidate': 'button input',
    'formtarget': 'button input',
    'headers': 'td th',
    'height': 'canvas embed iframe img input object video',
    'hidden': '*',
    'high': 'meter',
    'href': 'a area base link',
    'hreflang': 'a area link',
    'http-equiv': 'meta',
    'icon': 'command',
    'id': '*',
    'importance': 'iframe img link script',
    'integrity': 'link script',
    'intrinsicsize': 'img',
    'inputmode': 'textarea',
    'ismap': 'img',
    'itemprop': '*',
    'keytype': 'keygen',
    'kind': 'track',
    'label': 'optgroup option track',
    'lang': '*',
    'language': 'script',
    'loading': 'img iframe',
    'list': 'input',
    'loop': 'audio bgsound marquee video',
    'low': 'meter',
    'manifest': 'html',
    'max': 'input meter progress',
    'maxlength': 'input textarea',
    'minlength': 'input textarea',
    'media': 'a area link source style',
    'method': 'form',
    'min': 'input meter',
    'multiple': 'input select',
    'muted': 'audio video',
    'name': 'button form fieldset iframe input keygen object output select textarea map meta param',
    'novalidate': 'form',
    'open': 'details',
    'optimum': 'meter',
    'pattern': 'input',
    'ping': 'a area',
    'placeholder': 'input textarea',
    'poster': 'video',
    'preload': 'audio video',
    'radiogroup': 'command',
    'readonly': 'input textarea',
    'referrerpolicy': 'a area iframe img link script',
    'rel': 'a area link',
    'required': 'input select textarea',
    'reversed': 'ol',
    'rows': 'textarea',
    'rowspan': 'td th',
    'sandbox': 'iframe',
    'scope': 'th',
    'scoped': 'style',
    'selected': 'option',
    'shape': 'a area',
    'size': 'input select',
    'sizes': 'link img source',
    'slot': '*',
    'span': 'col colgroup',
    'spellcheck': '*',
    'src': 'audio embed iframe img input script source track video',
    'srcdoc': 'iframe',
    'srclang': 'track',
    'srcset': 'img source',
    'start': 'ol',
    'step': 'input',
    'style': '*',
    'summary': 'table',
    'tabindex': '*',
    'target': 'a area base form',
    'title': '*',
    'translate': '*',
    'type': 'button input command embed object script source style menu',
    'usemap': 'img input object',
    'value': 'button data input li meter option progress param',
    'width': 'canvas embed iframe img input object video',
    'wrap': 'textarea',
}
