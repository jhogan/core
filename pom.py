# vim: set et ts=4 sw=4 fdm=marker

#######################################################################
# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2020
########################################################################

from dbg import B
import entities
import dom
class site(entities.entity):
    def __init__(self):
        self.pages = pages(rent=None)
        self.index = None
        self._html = None
        self._head = None
        self._lang = 'en'
        self._charset = 'utf-8'
        self._viewport = \
            'width=device-width, initial-scale=1, shrink-to-fit=no'

        self._title = type(self).__name__.replace('_', '-')

        # TODO Replace with `file` object when it is created. NOTE that
        # the file object will need to have an integrity property to
        # suppor the <link>'s `integrity attribute:
        #
        #     <link rel="stylesheet" 
        #           href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css"
        #           integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm"/>

        self.stylesheets = list()

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
        return header(site=self)

class menus(entities.entities):
    @property
    def html(self):
        return dom.elements(x.html for x in self)

    @property
    def pretty(self):
        return dom.elements(x.pretty for x in self)

class menu(entities.entity):
    class items(entities.entities):
        @property
        def html(self):
            ol = dom.ol()
            for itm in self:
                ol += itm.html
            return ol
            
    class item(entities.entity):
        def __init__(self, pg):
            self.page = pg
            self.items = menu.items()

        @property
        def text(self):
            return self.page.name

        @property
        def html(self):
            li = dom.li()
            pg = self.page
            li += dom.a(pg.name, href=pg.path)
            if self.items.count:
                li += self.items.html
            return li

    def __init__(self):
        self.items = menu.items()

    @property
    def html(self):
        nav = dom.nav()
        nav += self.items.html
        return nav
            
    @property
    def pretty(self):
        ...

class pages(entities.entities):
    def __init__(self, rent, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent = rent

    def __getitem__(self, path):
        if isinstance(path, str):
            segs = [x for x in path.split('/') if x]
            if len(segs):
                del segs[0] # Remove langage code
        elif isinstance(path, list):
            segs = path
        else:
            raise TypeError('Path must be a string or list')
           
        seg = segs[0] if len(segs) else 'index'

        for pg in self:
            if pg.name == seg:
                if len(segs) > 1:
                    return pg.pages[segs[1:]]
                return pg
                
        raise IndexError('Path not found')

    def append(self, obj, uniq=False, r=None):
        obj.parent = self.parent
        r = super().append(obj, uniq, r)

class page(entities.entity):
    def __init__(self, name=None):
        self.pages = pages(self)
        self.parent = None
        self._name = name

    @property
    def name(self):
        if self._name:
            return self._name
        return type(self).__name__.replace('_', '-')

    @property
    def path(self):
        r = str()
        rent = self

        while rent:
            if r:
                r = '%s/%s' % (rent.name, r)
            else:
                r = rent.name
            rent = rent.parent

        # TODO Path currently only ascend to the root to concatenate
        # the pages path. However, the actual path must also contain the
        # language segment as wel ('/en/'). When the Http.Request
        # singleton is created, we can use it to get that language
        # segment and return something like:
        # 
        #     return Http.Request.language + '/' + r
        # or
        #     return Http.Request.regioun + '/' + r

        return '/' + r

class header(dom.header):
    def __init__(self, site, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.site = site
        self._menus = menus()
        self._menu = None

    def pull(self):
        # TODO Implement elements.remove()
        # ref: 844bf86d
        # self['nav'].remove()
        self += self.menus.html

    @property
    def html(self):
        self.pull()
        return super().html

    @property
    def pretty(self):
        self.pull()
        return super().pretty

    @property
    def menus(self):
        if self.menu not in self._menus:
            self._menus += self.menu

        return self._menus
    @property
    def menu(self):
        if not self._menu:
            self._menu = self._getmenu()

        return self._menu

    def _getmenu(self):
        def getitems(pgs):
            r = menu.items()
            for pg in pgs:
                item = menu.item(pg=pg)
                r += item
                item.items += getitems(pg.pages)
            return r

        mnu = menu()
        mnu.items += getitems(self.site.pages)

        return mnu

