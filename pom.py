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
import dom
import entities
import textwrap

# References:
#
# WAI-ARIA Authoring Practices 1.1
# https://www.w3.org/TR/wai-aria-practices/

class site(entities.entity):
    def __init__(self):
        self.pages = pages(rent=self)
        self.index = None
        self._html = None
        self._head = None
        self._lang = 'en'
        self._charset = 'utf-8'
        self._viewport = \
            'width=device-width, initial-scale=1, shrink-to-fit=no'

        self.sidebars = sidebars()

        self._title = type(self).__name__.replace('_', '-')

        # TODO Replace with `file` object when it is created. NOTE that
        # the file object will need to have an integrity property to
        # suppor the <link>'s `integrity attribute:
        #
        #     <link rel="stylesheet" 
        #           href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css"
        #           integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm"/>

        self.stylesheets = list()
        self._header = None

    def __repr__(self):
        return '%s()' % type(self).__name__

    def __str__(self):
        return repr(self)

    def __getitem__(self, path):
        return self.pages[path]

    @property
    def lang(self):
        return self._lang

    @lang.setter
    def lang(self, v):
        self._lang = v

    @property
    def charset(self):
        return self._charset

    @charset.setter
    def charset(self, v):
        self._charset = v

    @property
    def viewport(self):
        return self._viewport

    @viewport.setter
    def viewport(self, v):
        self._viewport = v

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, v):
        self._title = v

    @property
    def html(self):
        return dom.html(lang=self.lang)

    @property
    def head(self):
        self._head = dom.head()

        # NOTE Keep the charset meta at the top because: "The <meta>
        # element declaring the encoding must be inside the <head>
        # element and within the first 1024 bytes of the HTML as some
        # browsers only look at those bytes before choosing an
        # encoding."
        #     - https://developer.mozilla.org/en-US/docs/Web/HTML/Element/meta
        self._head += dom.meta(charset=self.charset)

        self._head += dom.meta(name="viewport", content=self.viewport)

        self._head += dom.title(self.title)

        for stylesheet in self.stylesheets:
            self._head += dom.link(rel="stylesheet", href=stylesheet)
        
        return self._head

    @property
    def header(self):
        if not self._header:
            self._header = header(site=self)
        return self._header


class sidebars(dom.sections):
    def __getitem__(self, ix):
        if isinstance(ix, str):
            for sb in self:
                if sb.name == ix:
                    return sb
        else:
            return super().__getitem__(ix)
    
class sidebar(dom.section):
    def __init__(self, name):
        self._name = name
        self.classes += name + '-sidebar'

    @property
    def name(self):
        return self._name

    def clone(self):
        r = type(self)(self.name)
        r += self.elements.clone()
        return r

class logo(dom.section):
    def __init__(self, o):
        super().__init__()

        if isinstance(o, str):
            self._text = o
        elif isinstance(o, file):
            # TODO Implement image-based logos when the file API is
            # available.
            raise NotImplementedError()
            self.image = file
        else:
            raise TypeError('Invalid logo type')

    def clone(self):
        el = type(self)(self.text)
        el += self.elements.clone()
        el.attributes = self.attributes.clone()
        return el

    @property
    def elements(self):
        els = super().elements
        els = dom.elements()
        els += dom.span(self._text)
        return els

    @elements.setter
    def elements(self, v):
        dom.element.elements.fset(self, v)

class menus(entities.entities, dom.section):
    def clone(self):
        mnus = type(self)()
        for mnu in self:
            mnus += mnu.clone()

        return mnus

    def __repr__(self):
        r = str()
        for mnu in self:
            r += '[%s]\n' % mnu.name
            r += repr(mnu) + '\n'
        return r

    def __getitem__(self, ix):
        if isinstance(ix, str):
            for mnu in self:
                if mnu.name == ix:
                    return mnu
        else:
            return super().__getitem__(ix)

    @property
    def elements(self):
        els = super().elements
        els.clear()

        for mnu in self:
            els += mnu

        return els

class menu(dom.nav):
    class items(entities.entities, dom.ul):
        def clone(self):
            itms = type(self)()

            for itm in self:
                itms += itm.clone()

            return itms

        def seperate(self):
            self += menu.separator()

        @property
        def elements(self):
            els = super().elements
            els.clear()

            for itm in self:
                els += itm.clone()

            return els

        def __str__(self):
            # The default is to call entities.entities.__str__, but we
            # want to call dom.ul.__str__ since it contains logic for
            # specifically formatting prettified HTML.
            return dom.ul.__str__(self)

        def __repr__(self):
            return dom.ul.__repr__(self)
            
    class item(dom.li):
        def __init__(self, o, href=None):
            self._text = self.page = None
            if isinstance(o, str):
                self._text = o
            elif isinstance(o, page):
                self.page = o
            else:
                raise TypeError('Item requires text or page object')

            self.href = href

            self.items = menu.items()

        def clone(self):
            # NOTE Don't clone self.page. The new item will point to the
            # existing page.
            o = self.page if self.page else self.text
            itm = type(self)(o, href=self.href)

            # FIXME:31b3fb5d This does not clone correctly due to the
            # problem with entities.append's inability to distinguish
            # between iterables and entity objects.  
            itm.items += self.items.clone()
            itm.attributes = self.attributes.clone()
            return itm

        def seperate(self):
            self.items.seperate()

        @property
        def text(self):
            if self._text:
                return self._text
            return self.page.name

        @property
        def elements(self):
            els = super().elements
            els.clear()
            pg = self.page
            if pg:
                els += dom.a(pg.name, href=pg.path)
            elif self.href:
                els += dom.a(self.text, href=self.href)
            else:
                els += dom.text(self.text)

            if self.items.count:
                #els += self.items
                # NOTE:78053602 Append naturally wants to flatten collection that are
                # passed to it, so set flatten to false so
                # `self.items`'s hierarchy can be preserved when
                # appending to `els`.
                #
                # <aside>
                #     `menu.items` collections inherit from `entities`
                #     and `ul` so they lead double lives as collections
                #     and as singular entity objects. So effort has to
                #     be exerted to ensure they are treated as entity
                #     objects when necessary.
                # </aside>
                els.append(self.items, flatten=False)

            return els

        def __repr__(self):
            pg = self.page
            if pg:
                return '%s (%s)' % (pg.name, pg.path)
            else:
                return self.text

    class separator(item):
        def __init__(self):
            # Using the super()'s __init__ won't work because it
            # requires a page or str object. 
            pass

        def clone(self):
            return type(self)()

        @property
        def items(self):
            raise NotImplementedError(
                "Seperator items don't have `items` collection"
            )

        def __repr__(self):
            return '---'

        @property
        def elements(self):
            els = dom.elements()
            els += dom.li()
            els += dom.hr()
            return els

    def __init__(self, name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = name
        self.aria_label = self.name.capitalize()
        self.items = menu.items()

    def clone(self):
        mnu = type(self)(self.name)
        mnu.items = self.items.clone()
        mnu.attributes = self.attributes.clone()
        return mnu

    @property
    def elements(self):
        els = super().elements
        els.clear()

        # Append flat. See ref:78053602
        # <s>els += self.items</s>
        els.append(self.items, flatten=False)
        return els

    def __repr__(self):
        itms = '\n'.join(repr(x) for x in self.items)
        itms = textwrap.indent(itms, ' ' * 2)
        return itms

class pages(entities.entities):
    def __init__(self, rent, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # The site or parent page
        self.parent = rent

    def __getitem__(self, path):
        if isinstance(path, str):
            segs = [x for x in path.split('/') if x]
            if len(segs):
                del segs[0] # Remove langage code
        elif isinstance(path, list):
            segs = path
        else:
            return super().__getitem__(path)
           
        seg = segs[0] if len(segs) else 'index'

        for pg in self:
            if pg.name == seg:
                if len(segs) > 1:
                    return pg.pages[segs[1:]]
                return pg
                
        raise IndexError('Path not found')

    def append(self, obj, uniq=False, r=None):
        obj._parentpages = self
        r = super().append(obj, uniq, r)

class page(dom.html):
    def __init__(self, name=None, pgs=None):
        self.pages = pages(rent=self)
        self._parentpages = pgs
        self._name = name
        self._callingmain = False
        self._calledmain = False
        self._body = None
        self._title = None
        self._lang = None
        self._head = None
        self._header = None
        self._sidebars = None

        try:
            self._mainfunc = self.main
        except AttributeError:
            pass

        self.main = dom.main()

    @property
    def title(self):
        if self._title is None:
            if self.site:
                self.title = '%s | %s' % self.site.title, self.Name
            self.title = self.Name

        return self._title

    @title.setter
    def title(self, v):
        self._title = v
        self.head['head>title'].remove()
        self.head += dom.title(v)

    @property
    def header(self):
        if self._header is None:
            if self.site:
                self._header = self.site.header.clone()
            else:
                self._header = dom.header()
        return self._header

    @property
    def head(self):
        if self._head is None:
            if self.site:
                self._head = self.site.head
            else:
                self._head = dom.head()

        return self._head
    
    @head.setter
    def head(self, v):
        self._head = v

    @property
    def body(self):
        if not self._body:
            self._body = dom.body()
        return self._body

    @body.setter
    def body(self, v):
        self._body = v

    @property
    def sidebars(self):
        if self._sidebars is None:
            if self.site:
                self._sidebars = self.site.sidebars.clone()
            else:
                self._sidebars = sidebars()
        return self._sidebars

    @property
    def elements(self):
        els = super().elements
        els.clear()
        ws = self.site

        if self.head:
            els += self.head

        if self.header and self.header.parent is not self.body:
            self.body += self.header

        els += self.body


        try:
            self._mainfunc
        except AttributeError:
            pass
        else:
            if not self._calledmain:
                try:
                    if not self._callingmain:
                        self._callingmain = True
                        self._mainfunc()
                finally:
                    self._callingmain = False
                    self._calledmain = True

        self.main._setparent(None)

        self.body += self.main
        self.body += self.sidebars
        return els

    @property
    def page(self):
        rent = self._parentpages

        if rent is None:
            return None

        rent = rent.parent

        if isinstance(rent, page):
            return rent

        return None

    @property
    def site(self):
        rents = self._parentpages

        if rents is None:
            return None

        rent = self._parentpages.parent

        if isinstance(rent, site):
            return rent
        elif isinstance(rent, page):
            return rent.site
        else:
            # We should never get here
            raise ValueError()

    @property
    def name(self):
        if self._name:
            return self._name
        return type(self).__name__.replace('_', '-')

    @property
    def Name(self):
        return self.name.capitalize()

    @property
    def path(self):
        r = str()
        rent = self

        while rent:
            if r:
                r = '%s/%s' % (rent.name, r)
            else:
                r = rent.name
            rent = rent.page

        # TODO Path currently only ascend to the root to concatenate
        # the pages path. However, the actual path must also contain the
        # language segment as wel ('/en/'). When the `http.request`
        # singleton is created, we can use it to get that language
        # segment and return something like:
        # 
        #     return http.request.language + '/' + r
        # or
        #     return http.request.region + '/' + r

        return '/' + r

    def __repr__(self):
        return self.path

class header(dom.header):
    # TODO Need to add an h2 and subheading parameter to constructor.
    # For semantic help, see http://html5doctor.com/howto-subheadings/
    def __init__(self, site, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.site = site
        self._menus = menus()
        self._menu = None
        self._logo = None

    def clone(self):
        hdr = type(self)(self.site)
        hdr.menus = self.menus.clone()
        hdr.menu = self.menu.clone()
        hdr.logo = self.menu.clone()
        return hdr

    @property
    def elements(self):
        els = super().elements
        els.clear()
        if self.logo:
            els += self.logo
        els += self.menus
        return els

    @property
    def logo(self):
        return self._logo

    @logo.setter
    def logo(self, v):
        self._logo = v

    @property
    def menus(self):
        if self.menu not in self._menus:
            self._menus += self.menu

        return self._menus

    @menus.setter
    def menus(self, v):
        self._menus = v

    @property
    def menu(self):
        if not self._menu:
            self._menu = self._getmenu()

        return self._menu

    @menu.setter
    def menu(self, v):
        self._menu = v

    def _getmenu(self):
        def getitems(pgs):
            r = menu.items()
            for pg in pgs:
                item = menu.item(o=pg)
                r += item

                for itm in getitems(pg.pages):
                    item.items += itm

                # FIXME:31b3fb5d This should work, however
                # entities.append will test if the object being append
                # is an entity first. If it is an entity, it will assume
                # it doesn't need to iterate over the entity.
                # 
                # The return of `getitems(pg.pages)` is a pom.menu.items
                # collection. Since `items` inherits from both
                # `entities.entities` and `dom.ul`, it is an `entity`
                # object and an `entities` object. `entitites.append()`
                # should be corrected to handle this situation.

                '''
                item.items += getitems(pg.pages)
                '''
            return r

        mnu = menu('main')
        for itm in getitems(self.site.pages):
            mnu.items += itm

        return mnu

class footer(dom.footer):
    pass

