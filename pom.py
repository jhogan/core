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
import asset, ecommerce
import datetime
import dom
import entities
import exc
import file
import inspect
import itertools
import orm
import primative
import textwrap
import www

# References:
#
# WAI-ARIA Authoring Practices 1.1
# https://www.w3.org/TR/wai-aria-practices/

class sites(asset.assets): 
    """ A collection of web ``site`` objects.
    """

class site(asset.asset):
    """ A ``site`` object represents a web site.

    ``site`` object consiste of a hierarchy of web ``page`` objects to
    store the pages in the web ``site``, as well as other constituent
    entities such as a ``directory`` object to store file the web site
    uses, a ``hits`` collection to record the hits to the web ``site``,
    a ``users`` collection to track the web ``site``'s user, and so on.

    Note that site objects ultimately inherit from orm.entity so they
    are persisted to the database along with their constituents.
    """
    def __init__(self, *args, **kwargs):
        """ XXX
        """
        super().__init__(*args, **kwargs)
        self.index = None
        self._pages = None
        self._html = None
        self._head = None
        self._lang = 'en'
        self._charset = 'utf-8'
        self._viewport = \
            'width=device-width, initial-scale=1, shrink-to-fit=no'

        self.sidebars = sidebars()

        # Give the site a default titel of the class's name. 
        self._title = type(self).__name__.replace('_', '-')

        # TODO Use the site.directory inodes model to reference
        # resources (file.resources) now that it is has been
        # implemented. 
        #
        #     <link rel="stylesheet" 
        #           href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css"
        #           integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm"/>

        self.stylesheets = list()
        self._header = None

    # Host name of the site
    host = str

    # Collection of web hits to the site
    hits = ecommerce.hits

    # Collection of users who may log in to the site
    users = ecommerce.users

    # Directory to store the site's files
    directory = file.directory

    _resources = None

    @orm.attr(file.directory)
    def directory(self):
        """ Returns the site's main directory.

        This directory is a good place to put the site's main resource
        artifacts like CSS and JavaScript libraries. It's also a good
        place to store other files belonging to the site such as the
        site's logo and the site's user avatars (although the
        ecommerce.user.directory entity would be a better place to store
        user specific files).

        Note that this returns a ``directory`` from the file module so
        it behaves like a file-sytem directory and an ORM entity. It is
        a constituent of the ``site`` class so calling the site`s save()
        method will cascade the persistence operations into the
        directory and any inodes beneath it.
        """
        dir = attr()
        if dir is None:
            dir = file.directory(f'/pom/site/{self.id.hex}')
            attr(dir)
        return dir

    @property
    def resources(self):
        """ Returns the sites's resources directory. If the 'resources'
        directory doesn't exist, it is created.
        """
        # We may not need the try:except logic here if we decide to
        # implement the suggestion at bda97447 (seach git-log)
        if not self._resources:
            try:
                self._resources = self.directory['resources']
            except IndexError:
                resx = file.directory('resources')
                self.directory += resx
                resx.save()
                self._resources = resx
        return self._resources

    @resources.setter
    def resources(self, v):
        if v is self.resources:
            return

        self.resources.inodes = v

    class AuthenticationError(ValueError):
        pass

    def authenticate(self, name, pwd):
        """ Find a user in the site with the user name of ``name``. Test
        that the user's password hashes to the same value as `pwd`. If
        so, return the user. Otherwise we raise an AuthenticationError.

        :param: name str: The user name.

        :param: pwd str: The password.
        """

        # Get the foreign key column name in users that maps to the
        # ``site`` entity (e.g., siteid).
        # 
        #     site.get_users(name=name)
        # STOPGAP: 8210b80c
        for map in ecommerce.users.orm.mappings.foreignkeymappings:
            if map.entity is site:
                siteid = map.name
                break
        else:
            raise ValueError('Cannot find site mapping')

        # Get the user with the given user name
        usrs = ecommerce.users(
            name = name,
            siteid = self.id
        )

        # If there are more that one there is a data integrity issue
        if usrs.isplurality:
            raise ValueError('Multiple users found')

        # Good; we found one. Let's test the password and return the
        # usr.  Otherwise, we will raise an exception to signify
        # authentication failed.
        if usrs.issingular:
            usr = usrs.first
            if usr.ispassword(pwd):
                return usr

        raise self.AuthenticationError(
            f'Incorrect password for {name} for {self.name}'
        )

    @property
    def pages(self):
        """ Return the collection of pages.
        """
        if not self._pages:
            self._pages = pages(rent=self)
            self._pages += error()
        return self._pages

    @pages.setter
    def pages(self, v):
        self._pages = v

    @classmethod
    def getinstance(cls):
        """ Get the single site instance for this session.
        """
        # TODO The site's host will be derived from a configuration file
        # setting.
        return cls('foo.net')

    def __repr__(self):
        """ Return a string representation of the site object.
        """
        return '%s()' % type(self).__name__

    def __str__(self):
        """ Return a string representation of the site object.
        """
        return repr(self)

    def __getitem__(self, path):
        """ An indexer to get a page in the site::

            ws = mysite()
            about_page = ws['/en/about']

        :param: path str: The path to the web ``page``.
        """
        return self.pages[path]

    def __call__(self, path):
        """ Similar to __getitem__ except that, if the page can not be
        found, None is returned.
        """

        # NOTE We may not need the try:except here because the pages
        # collection will do the same thing if we use its __call__
        # method::
        #
        #     return self.pages(path)

        try:
            return self.pages[path]
        except IndexError:
            return None

    @property
    def lang(self):
        return self._lang

    @lang.setter
    def lang(self, v):
        self._lang = v

    @property
    def languages(self):
        ''' A list of accepted languages for the site. For example::`
            
            ['en', 'es', 'fr', 'de']

            Sites that wish to accept a different set of languages can
            override this property. The default is to always accept
            English.
        '''

        # Always accept English
        return ['en']

    @property
    def charset(self):
        """ Specifies the default character set of the web site.
        """
        return self._charset

    @charset.setter
    def charset(self, v):
        self._charset = v

    @property
    def viewport(self):
        """ Specifies the default viewport of the web site.
        """
        return self._viewport

    @viewport.setter
    def viewport(self, v):
        self._viewport = v

    @property
    def title(self):
        """ Specifies the default title of the web site.
        """
        return self._title

    @title.setter
    def title(self, v):
        self._title = v

    @property
    def html(self):
        """ Specifies the default <html> element of the web site's
        pages.
        """
        return dom.html(lang=self.lang)

    @property
    def head(self):
        """ Specifies the default <head> element of the web site's
        pages.
        """
        self._head = dom.head()

        # NOTE Keep the charset meta at the top because: "The <meta>
        # element declaring the encoding must be inside the <head>
        # element and within the first 1024 bytes of the HTML as some
        # browsers only look at those bytes before choosing an
        # encoding."
        # - https://developer.mozilla.org/en-US/docs/Web/HTML/Element/meta
        self._head += dom.meta(charset=self.charset)

        self._head += dom.meta(name="viewport", content=self.viewport)

        self._head += dom.title(self.title)

        for stylesheet in self.stylesheets:
            self._head += dom.link(rel="stylesheet", href=stylesheet)

        # TODO Consolidate with page.head
        for res in self.resources:
            src = res.relative if res.local else str(res.url)

            if res.mime == 'application/javascript':
                el = dom.script(
                    integrity = res.integrity, 
                    crossorigin = res.crossorigin,
                    src = src
                )
            elif res.mimetype == 'text/css':
                raise NotImplementedError('TODO')

            self._head += el

        return self._head

    @property
    def header(self):
        """ Specifies the default <header> element of the web site's
        pages.
        """
        if not self._header:
            self._header = header(site=self)
        return self._header

class forms:
    """ ``forms`` acts as a namespace to get to standard forms that a
    developer can access and reuse, such as the login form.
    """
    class login(dom.form):
        """ A standard log in form.
        """
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # TODO:GETTEXT

            self += dom.h1('Please sign in')

            # TODO Add 'for' attribute to <label>
            self += dom.label('Username')

            # Username
            self += dom.input(
                name='username',   type='text',
                label='Username',  placeholder='Username',
                required=True,     autofocus=True,
                class_ = 'form-control'
            )

            # TODO Add 'for' attribute to <label>
            self += dom.label('Password')

            self += dom.input(
                name='password',  type='password',
                label='Password', placeholder='Password',
                required=True,    class_='form-control'
            )

            self += dom.button('Sign in', class_='btn', type="Submit")

class sidebars(dom.sections):
    """ Represents a collection of webpage ``sidebar`` objects.
    """
    def __getitem__(self, ix):
        if isinstance(ix, str):
            for sb in self:
                if sb.name == ix:
                    return sb
        else:
            return super().__getitem__(ix)
    
class sidebar(dom.section):
    """ Represents a sidebare on a web page.

    A sidebar is a column placed to the right or left of a
    webpage's primary content area. Sidebars are commonly used to display
    various types of supplementary information for users, such as
    nav links, ads, email sign-up forms, social media links, etc.
    """
    def __init__(self, name, *args, **kwargs):
        """ Create a sidebar.

        :param: name str: The name of the sidebar
        """
        super().__init__(*args, **kwargs)
        self._name = name
        self.classes += name + '-sidebar'

    @property
    def name(self):
        """ Return the name of the sidebar.
        """
        return self._name

    def clone(self):
        """ Create and return a clone of self
        """
        r = type(self)(self.name)
        r += self.elements.clone()
        return r

class logo(dom.section):
    """ Represents the organization's logo presented on a web page,
    typically in the page's header.
    """
    def __init__(self, o):
        """ Create a logo page object.

        :param: o str: The text to display in the logo
        """
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
        """ Create a new logo object based on self and return.
        """
        el = type(self)(self.text)
        el += self.elements.clone()
        el.attributes = self.attributes.clone()
        return el

    @property
    def elements(self):
        """ Return the logo section's elements collection.
        """
        els = super().elements
        els = dom.elements()

        # Add the text span here. See constructor.
        els += dom.span(self._text)
        return els

    @elements.setter
    def elements(self, v):
        dom.element.elements.fset(self, v)

class menus(entities.entities, dom.section):
    """ Represents a collection of ``menu`` objects
    """

    def __init__(self, *args, **kwargs):
        """ Create the menus collection.
        """
        entities.entities.__init__(self, *args, **kwargs)
        dom.section.__init__(self)

    def clone(self):
        """ Create and return a ``menus`` collection based on this one.
        """
        mnus = type(self)()
        for mnu in self:
            mnus += mnu.clone()

        return mnus

    def __repr__(self):
        """ A string representation of this ``menus`` collection.
        """
        r = str()
        for mnu in self:
            r += '[%s]\n' % mnu.name
            r += repr(mnu) + '\n'
        return r

    def __getitem__(self, ix):
        """ Implement an indexer so the menus can be accessed by name::

            # Get the desert menu
            mnu = mymenus['desert']
        """

        # TODO I'm pretty sure this is how entities.__getitem__ works
        # already.
        if isinstance(ix, str):
            for mnu in self:
                if mnu.name == ix:
                    return mnu
        else:
            return super().__getitem__(ix)

    @property
    def elements(self):
        """ Return the menu's child elements.
        """
        els = super().elements
        els.clear()

        for mnu in self:
            els += mnu

        return els

class menu(dom.nav):
    # TODO:c0336221 Currently, there issues altering attributes en masse
    # with menu and its subsidiaries:
    #
    #   for itm in menu_items.all:
    #       itm.id = False
    # 
    # Part of this is an issue with the way attributes aren't properly
    # set or deleted. These issue (12c29ef9) will be addressed
    # eventually in pom.attributen code. When thes are, tests should be
    # written to ensure that mass assignments of attributes work for
    # menus because there are issues with the way menu and its
    # subsidiaries clone and memoizes elements.
    #
    # A good test would be to change and remove the id attribute from
    # all elements of a menu:
    #       
    #     main_menus.id = 'derp' # Currently dosen't work
    #     
    #     # and 
    #
    #     del main_menus.id # Currently dosen't work

    # TODO This should inherit from dom.menu, not dom.nav

    class items(dom.lis):
        """ A collection of ``item`` objects (<li>) which contain the
        menu items.
        """
        def __init__(self, *args, **kwargs):
            """ Create the menu item.
            """
            super().__init__(*args, **kwargs)

            self._els = dom.elements()

            # Start the menu off with an unorded list
            self._ul = dom.ul()
            self._els += self._ul

        def clone(self):
            """ Create and return an ``items`` based on self.
            """
            itms = type(self)()

            # Preserve ID's
            # TODO Should all attributes of the ul be preserved?
            # Probably.
            if self._ul.id is not None:
                itms._ul.id = self._ul.id

            for itm in self:
                itms += itm.clone()

            return itms

        def seperate(self):
            """ Add a seperator to the list of menu items.
            """
            self += menu.separator()

        @property
        def elements(self):
            """ Return the elements under the first element of this
            collection.
            """
            ul = self._els.first
            ul.elements.clear()
            for itm in self:
                self._ul += itm.clone()

            return self._els

        @property
        def html(self):
            """ Return an HTML representation of this element formatted
            for a computer (no unnecssary whitespace).
            """
            return ''.join(x.html for x in self.elements)

        @property
        def pretty(self):
            """ Return an HTML representation of this element formatted
            for human consumption.
            """
            return '\n'.join(x.pretty for x in self.elements)

        def __str__(self):
            """ A string representation of the collection.
            """
            # The default is to call entities.entities.__str__, but we
            # want to call dom.ul.__str__ since it contains logic for
            # specifically formatting prettified HTML.
            return dom.ul.__str__(self)

        def __repr__(self):
            """ A string representation of the collection.
            """
            return dom.ul.__repr__(self)

    class item(dom.li):
        """ Represents an item in a menu such as a hyperlink or a
        ``seperator``.
        """
        def __init__(self, o, href=None, *args, **kwargs):
            """ Create the menu item.

            :param: o str|page: 
                If str, o is the text used for the menu item.
                If page, the menu item links to that page.

            :param: o str: The optional hyperlink to use. Used in
            conjunction with o to create a link when it is a str.
            """
            super().__init__(*args, **kwargs)

            self.href = href
            self._text = self.page = None
            if isinstance(o, str):
                self._text = o
                if href:
                    self.body = dom.a(self.text, href=self.href)
                else:
                    self.body = dom.text(self.text)
            elif isinstance(o, page):
                self.page = o
                self.body = dom.a(self.page.name, href=self.page.path)
            else:
                raise TypeError('Item requires text or page object')

            self.items = menu.items()

        def clone(self):
            """ Create and return a new menu item based on this one.
            """
            # NOTE Don't clone self.page. The new item will point to the
            # existing page.
            o = self.page if self.page else self.text
            itm = type(self)(o, href=self.href)

            if self.body.id is not None:
                itm.body.id = self.body.id

            itm.items += self.items.clone()

            # Preserve ID's
            # TODO Should all attributes of the ul be preserved?
            # Probably.

            if self.items._ul.id is not None:
                itm.items._ul.id = self.items._ul.id

            itm.attributes = self.attributes.clone()
            return itm

        def seperate(self):
            """ Create a seperator in this menu item's ``items`` collection.
            """
            self.items.seperate()

        @property
        def text(self):
            """ Return the text of the item.
            """
            if self._text:
                return self._text
            return self.page.name

        @property
        def elements(self):
            """ Returns the child elements of this colletion.
            """
            els = super().elements
            els.clear()
            pg = self.page
            if self.body:
                els += self.body

            if self.items.count:
                els += self.items.elements

            return els

        def __repr__(self):
            """ Returns a string represention of the menu item.
            """
            pg = self.page
            if pg:
                return '%s (%s)' % (pg.name, pg.path)
            else:
                return self.text

    class separator(item):
        """ An entry in a collection of menu item that seperates one set
        from anonther.

            [O]pen
            [S]ave
            Save [A]s
            --------
            [Q]uit

        In the above text version of a menu, the line of dashes
        seperates one set of file operations (Open, Save and Save As)
        from the Quit operation.

        Though the above menu resembles that of a desktop applicanion's
        file menu, web page menus have a need for a seperator as well.
        The HTML element used to represent a seperator is an HTML menu
        is a <br>.
        """

        def __init__(self, *args, **kwargs):
            """ Create the seperator object.
            """
            # Using the super()'s __init__ won't work because
            # item.__init__ requires a page or str object. We call
            # item's super's (li) constructor instead.
            dom.li.__init__(self, *args, **kwargs)

        def clone(self):
            """ Create a new seperator and return it.
            """
            return type(self)()

        @property
        def items(self):
            """ Raise a NotImplementedError.

            A seperators would not have a nested set of menu items.
            """
            raise NotImplementedError(
                "Seperator items don't have `items` collection"
            )

        def __repr__(self):
            """ Return a textual representation of a menu seperator.
            """
            return '---'

        @property
        def elements(self):
            """ Return the elements of the seperator
            """
            els = dom.elements()
            els += dom.li()
            els += dom.hr()
            return els

    def __init__(self, name, *args, **kwargs):
        """ Create a new menu.

        :param: name str: The name of the menu.
        """
        super().__init__(*args, **kwargs)
        self.name = name
        self.aria_label = self.name.capitalize()
        self.items = menu.items()

    def clone(self):
        """ Create and return a new menu based on this menu.
        """
        mnu = type(self)(self.name)
        mnu.items = self.items.clone()
        mnu.attributes = self.attributes.clone()
        return mnu

    @property
    def elements(self):
        """ Returns the child elements of this menu.
        """
        els = super().elements
        els.clear()

        els += self.items.elements
        return els

    def __repr__(self):
        """ A string representation of this menu.
        """
        itms = '\n'.join(repr(x) for x in self.items)
        itms = textwrap.indent(itms, ' ' * 2)
        return itms

class pages(entities.entities):
    """ A collection of ``page`` objects.
    """
    def __init__(self, rent, *args, **kwargs):
        """ Create a new pages collection.

        :param: rent page|site: The parent page or site of this page
        colection.
        """
        super().__init__(*args, **kwargs)
        self.parent = rent

    @property
    def site(self):
        """ The site that this pages collection belongs to. 

        None is returned if the site doesn't exist or can't be found.
        """
        rent = self.parent
        while rent:
            if isinstance(rent, site):
                return rent
            rent = rent.parent

        return None

    def __getitem__(self, path):
        """ An indexer to get the page in teh collection given a path.

        :param: path str|list: The path of the page to get. For example, 
            
            /en/bio/luser

        or in list form:

            ['en', 'bio', 'luser']
        """
        if isinstance(path, str):
            segs = [x for x in path.split('/') if x]
            if len(segs):
                del segs[0] #
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
        """ Add a page to the pages collection.

        Note that you will normally add a page using the += operator
        which calls into this method.

            pgs = pages()
            pgs += page('new-page')

        :param: obj page: The page to add.
        """
        obj._parentpages = self
        obj.name in [x.name for x in self]
        for pg in self:
            if pg.name == obj.name:
                del self[pg.path]
                break
        super().append(obj, uniq)

class page(dom.html):
    """ Represents a web page.
    """
    ExceptedBooleansStrings = (
        ('false', '0', 'no', 'n'),
        ('true', '1', 'yes', 'y')
    )

    def __init__(self, name=None, pgs=None, *args, **kwargs):
        """ Create a web page.

        :param: name str: The name of the page.
        """
        super().__init__(*args, **kwargs)

        self._pages        =  None
        self._parentpages  =  pgs
        self._name         =  name
        self._calling      =  False
        self._called       =  False
        self._attemped     =  False  # A call was attemped
        self._body         =  None
        self._title        =  None
        self._lang         =  None
        self._head         =  None
        self._header       =  None
        self._sidebars     =  None
        self._args         =  dict()
        self._resources    =  None
        
        try:
            self._mainfunc = self.main
        except AttributeError:
            pass

        self.clear()

    @property
    def resources(self):
        """ Return a collection of resource objects the page will use.
        """
        if self._resources is None:
            self._resources = file.resources()

            self.resources.onbeforeadd += self._resources_onbeforeadd

        return self._resources

    @resources.setter
    def resources(self, v):
        self._resources = v

    def _resources_onbeforeadd(self, scr, eargs):
        """ An event handler to capture the moment before a resource is
        added to the page's resources collection.
        """
        if eargs.entity.local:
            raise ValueError(
                'Page-level resources cannot be saved. Use a '
                'site-level resource instead.'
            )

    def flash(self, msg):
        """ Add a flash message to the top of the page.

        :param: msg str: The text to put in the flash message.
        """
        if isinstance(msg, str):
            msg = dom.paragraph(msg)

        art = dom.article(msg, class_="flash")

        self.main << art
        
    @property
    def title(self):
        """ The page's title.

        This corresponds to the <title> tag found in the <head> of a
        typical HTML document.

        If no title for the page is set, a default title is constructed
        from the site's title and the page's name.
        """
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
    def pages(self):
        """ Returns a collection of child pages of this page.
        """
        if self._pages is None:
            self._pages = pages(rent=self)
        return self._pages

    @pages.setter
    def pages(self, v):
        self._pages = v

    @property
    def header(self):
        """ The header section of the page.

        If left unset, the sites header will be used. This will likely
        include the site's main menu, logo and things of that nature.
        """
        if self._header is None:
            if self.site:
                self._header = self.site.header.clone()
            else:
                self._header = dom.header()
        return self._header

    @property
    def head(self):
        """ The <head> section of the page.

        If left unset, the sites <head> section will be used. 

        The page's ``resources`` collection will be scanned for typical
        files that go in the head, such as URL's to JavaScript and CSS
        files. These will be added a <script> and <link> elements to the
        <head> as would be expected.
        """
        if self._head is None:
            if self.site:
                self._head = self.site.head
            else:
                self._head = dom.head()

            for res in self.resources:
                if res.mime == 'application/javascript':
                    src = res.relative if res.local else str(res.url)

                    if src in self._head['script'].pluck('src'):
                        continue

                    el = dom.script(
                        integrity = res.integrity, 
                        crossorigin = res.crossorigin,
                        src = src
                    )
                elif res.mimetype == 'text/css':
                    raise NotImplementedError('TODO')
                else:
                    raise TypeError(f'Invalid mime type: {res.mimetype}')

                self._head += el

        return self._head
    
    @head.setter
    def head(self, v):
        self._head = v

    @property
    def body(self):
        """ The <body> of the page.
        """
        if not self._body:
            self._body = dom.body()
        return self._body

    @body.setter
    def body(self, v):
        self._body = v

    @property
    def sidebars(self):
        """ A collection of sidebars for the page.
        """
        if self._sidebars is None:
            if self.site:
                self._sidebars = self.site.sidebars.clone()
            else:
                self._sidebars = sidebars()
        return self._sidebars

    @property
    def _arguments(self):
        """ Return a dict to be pased into the page's __call__ method
        using the ** notation.

            self._mainfunc(**self._arguments)

        The arguments are a dict version of the query string found in
        the URL for the page. So for example, a URL with a path and
        query string such as:

            /en/time?greet=1&tz=America/Phoenix&a=1&b=2
        
        would call the /en/time page's __call__ method with something
        like this::

            {'greet': True, 'a': '1', 'b': '2'}

        This dict would be return by this @property.

        Note that boolean valuse, like the 1 for 'greet' are normalized
        into Python boolean types. The normalization happens because the
        parameter list for the /en/time's main() method are examined and
        their annotations are used.

            class time(pom.page):
                def main(self, greet: bool, tz='UTC', **kwargs):

        In this example, 'greet' will be True, tz will keep it's default
        of UTC and **kwargs will contain the values for a and b:

            {'a': '1', 'b': '2'}
        """
        # If a parameter is required by the page (it's in `params`) but
        # was not given by the client in the query string, ensure that
        # the parameter is in the args and set to None. If this is not
        # done, a TypeError would be thrown by pages that require
        # argument due to them being specified in its parameter list
        # without a default.

        # Get parameters for self._mainfunc
        params = inspect.signature(self._mainfunc).parameters.items()

        # If there are no params to _mainfunc, then clear _args because
        # _mainfunc can accept no args
        if not len(params):
            self._args = dict()

        kwargs = False
        reserved = 'req res usr'.split()
        for k, v in params:
            if k in reserved:
                raise ValueError(
                    '"%s" cannot be used as a parameter to the main '
                    'method in page "%s".' % (k, type(self))
                )
                
            if v.kind == v.VAR_KEYWORD:
                # A kwargs (VAR_KEYWORD) parameter was found
                kwargs = True
                continue 

            if v.default is not inspect.Parameter.empty:
                continue

            if k not in self._args:
                # If no argument was given for the parameter, create it
                # and set it to None. This way, None gets passed as an
                # argument to the parameter instead of nothing which
                # would cause a TypeError.
                self._args[k] = None

            if v.annotation is not inspect._empty:
                arg = self._args[k]

                # If the parameter has an annotation (a type hint) use
                # the type hint to coerce the string to the hinted type.
                if v.annotation is bool:
                    # Interpret '1' and 'true' (case insensitive) as
                    # True, otherwise the value will be interpreted as
                    # False.
                    if isinstance(arg, str):
                        arg = arg.casefold()
                        expected = self.ExceptedBooleansStrings

                        flattened = list(itertools.chain(*expected))
                        str_flattened = ', '.join(flattened)

                        if arg not in flattened:
                            raise www.UnprocessableEntityError(
                                'Query string parameter '
                                '"%s" must be one of the '
                                'following: %s' % (k, str_flattened)
                            )
                        self._args[k] = arg in expected[1]
                elif datetime.datetime in v.annotation.mro():
                    try:
                        v = primative.datetime(arg)
                    except Exception as ex:
                        raise www.UnprocessableEntityError(
                            'Query string parameter '
                            '"%s" must be a datetime.' % (k,)
                        )
                        
                    else:
                        self._args[k] = v

                elif v.annotation in (int, float):
                    # Use the constructor of the class (v.annotation) to
                    # coerce the data. This works well for types like
                    # int, float, etc. This should also works with UUID
                    # if the uuid is a simple hex representation
                    # (uuid4().hex).
                    try:
                        v = v.annotation(arg)
                    except Exception as ex:
                        t = v.annotation.__name__
                        raise www.UnprocessableEntityError(
                            'Query string parameter '
                            '"%s" must be of type "%s".' % (k, t)
                        )
                    else:
                        self._args[k] = v

        # If a **kwargs parameter (VAR_KEYWORD) was not found:
        if not kwargs:
            # Delete any of the _args that don't have a corresponding
            # parameter
            for k in list(self._args):
                if k not in dict(params):
                    del self._args[k]

        return self._args

    @_arguments.setter
    def _arguments(self, v):
        self._args = v

    def clear(self):
        """ Used to initialize the page's <main> element and set it's
        data-path attribute to the path of the page.
        """
        # NOTE "clear" is a bit of a misnomer. Maybe this should be
        # renamed to 'init' or something.
        self.main = dom.main()
        self.main.attributes['data-path'] = self.path
        self._called = False
        self._attemped = False

    def __call__(self, eargs=None, *args, **qsargs):
        """ This method calls into the page's `main` method that the
        web developer writes.

            class mypage(page):
                def main(self):
                    ...

            # Init page
            pg = mypage()

            # "Calling" the page ends up calling the main() method
            # defined above.
            pg() 
        """

        self._attemped = True  # A call was attemped

        if len(args):
            raise ValueError('Use kwargs when calling page object')

        if self._called:
            raise ValueError(
                'Double execution. Call "page.clear" method before '
                'second call.'
            )

        if not self._calling:
            self._arguments = qsargs

            try:
                self._calling = True

                req = www.request
                if req.isevent:
                    getattr(self, eargs.handler)(
                        src=eargs.src, eargs=eargs
                    )
                else:
                    # Inject global variables into main()
                    globs = self._mainfunc.__func__.__globals__
                    globs['req'] = www.request
                    globs['res'] = www.response

                    # Call page's main method. It's called `_mainfunc`
                    # here but the web developer will call it `main`.
                    self._mainfunc(**self._arguments)
                self._called = True
            finally:
                self._calling = False

    @property
    def elements(self):
        """ Return the HTML element underneath the page (i.e.,
        underneath the <html> element in the DOM).
        """
        els = super().elements
        els.clear()

        if self.head:
            els += self.head

        self.body.elements.remove()

        if self.header and self.header.parent is not self.body:
            self.body += self.header

        els += self.body

        # If a call has not been attemped, call here
        self._attemped or self(**self._arguments)

        self.main._setparent(None)

        self.body += self.main
        self.body += self.sidebars
        return els

    @property
    def page(self):
        """ Return the parent page of this page object.
        """
        rent = self._parentpages

        if rent is None:
            return None

        rent = rent.parent

        if isinstance(rent, page):
            return rent

        return None

    @property
    def site(self):
        """ Return the web ``site`` that this page belongs to.
        """
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
        """ Return the name of the page.

        c.f. page.Name

        """
        if self._name:
            return self._name
        return type(self).__name__.replace('_', '-')

    @property
    def Name(self):
        """ Return a capitalize version of the page's name. 

        c.f. page.name
        """
        return self.name.capitalize()

    @property
    def path(self):
        """ Return the path of the page, e.g., '/about/team'
        """ 
        r = str()
        rent = self

        while rent:
            if r:
                r = '%s/%s' % (rent.name, r)
            else:
                r = rent.name
            rent = rent.page

        return '/' + r

    def __repr__(self):
        """ Return a string representation of the page.
        """
        r = f'{type(self).__name__}('
        r += f'id={self.id} path={self.path}'
        r += ')'
        return r

class header(dom.header):
    """ Represents the header portion of a web page.

    A page header contains a menus object to contain 0 or more menues in
    the header, one main menu, and a logo.
    """
    # TODO Need to add an h2 and subheading parameter to constructor.
    # For semantic help, see http://html5doctor.com/howto-subheadings/
    def __init__(self, site, *args, **kwargs):
        """ Create the ``header`` page bject
        """
        super().__init__(*args, **kwargs)
        self.site = site
        self._menus = menus()
        self._menu = None
        self._logo = None

    def clone(self):
        """ Create and return a ``header`` objecs based on the values in
        this ``header``.
        """
        hdr = type(self)(self.site)
        hdr.menus = self.menus.clone()
        hdr.menu = self.menu.clone()
        hdr.logo = self.menu.clone()
        return hdr

    @property
    def elements(self):
        """ The child elements of this header element.
        """
        els = super().elements
        els.clear()
        if self.logo:
            els += self.logo
        els += self.menus
        return els

    @property
    def logo(self):
        """ The headers logo.
        """
        return self._logo

    @logo.setter
    def logo(self, v):
        self._logo = v

    @property
    def menus(self):
        """ The collection of menues for this ``header``.
        """
        if self.menu not in self._menus:
            self._menus += self.menu

        return self._menus

    @menus.setter
    def menus(self, v):
        self._menus = v

    @property
    def menu(self):
        """ Return the main menu for this ``header`` object.
        """
        if not self._menu:
            self._menu = self._getmenu()

        return self._menu

    @menu.setter
    def menu(self, v):
        self._menu = v

    def _getmenu(self):
        """ Create and return a menu based on the site's pages.
        """
        def getitems(pgs):
            """ Recursively build and return a menu based on the site's
            pages.
            """
            r = menu.items()
            for pg in pgs:

                # Don't add error pages to the menu
                if pg.name == 'error':
                    continue

                item = menu.item(o=pg)
                r += item

                item.items += getitems(pg.pages)

            return r

        mnu = menu('main')

        for itm in getitems(self.site.pages):
            mnu.items += itm

        return mnu

# TODO We need a footers collection complement
class footer(dom.footer):
    """ Represents a page's footer.
    """

# TODO We need an inputs collection complement
class input(dom.div):
    """ Represents any text input, vis. an <input type=text>, a
    <textarea> a <select> or a <datalist>.
    """
    # TODO Add functionality to create a <datalist>
    def __init__(self,              
            name,              type,       label=None,
            placeholder=None,  help=None,  options=None,
            selected=None,     *args,      **kwargs
        ):
        """ Create an ``input`` object.

        :param: name str: The name of the object. Used for the 'name'
        attribute of the element.

        :param: type str: The type of input element: 'textarea',
        'select', input, etc.

        :param: label str: The text for a <lable> element that
        corresponds to this input element.

        :param: placeholder str: The text to set the placeholder
        attribute to.

        :param: help str: A help message that corresponds to this input
        field.

        :param: options sequence<sequence<str, str>>: For 'select' input
        types, a collection of 2 element sequences, the first element
        containing the options value, the second containing the options
        key.

        :param: selected sequence: For 'select' input types. If the
        value in `options` is in `selected`, the option is marked
        selected (<option selected>).
        key.

        """
        super().__init__(*args, **kwargs)

        self.name         =  name
        self.label        =  label
        self.placeholder  =  placeholder
        self.help         =  help
        self.type         =  type

        # TODO Ensure that 'type' is valid. In addition to text and
        # email, type can also be textarea and datalist.
        self.classes += 'form-group'

        els = super().elements

        if self.label:
            # TODO Add the 'for' attribute to <label>
            els += dom.label(self.label)

        if type == 'textarea':
            inp = dom.textarea(name=self.name)
        elif type == 'select':
            inp = dom.select(name=self.name)
            for opt in options:
                inp += dom.option(opt[1], value=opt[0])
                if opt[0] in selected:
                    inp.last.selected = True
        else:
            inp = dom.input(name=self.name)

        els += inp

        if self.placeholder:
            inp.placeholder = self.placeholder

        if self.help:
            els += dom.small(self.help)

class error(page):
    """ A page intended to show an error message. 

    Usually error pages are called when another page raises a
    www.HttpError exception. This page will be used to capture the
    exceptions details and present it to the user.
    """
    @property
    def pages(self):
        """ A collection of error pages. Usually, the error pages will
        correspond to an HTTP error code. A default 404 page is added
        default since it is so common.
        """
        if not self._pages:
            self._pages = super().pages
            self._pages += _404()
        return self._pages
        
    def main(self, ex):
        """ The main function for the page.

        :param: ex www.HttpException: The exception that caused this
        page to be invoked.
        """
        args = (
            ex.phrase,
            ex.status,
            ex.message
        )

        self.title = ex.phrase

        self.main += dom.h1('''
            An unexpected error was encountered.
        ''')

        self.main += dom.span(ex.status, class_='status')
        self.main += dom.span(ex.message, class_='message')
        self.main += traceback(ex)

class traceback(dom.article):
    """ A subclass of dom.article that renders an exception as a HTML.
    """
    def __init__(self, ex, *args, **kwargs):
        """ Create the trackback article.

        :param: ex Exception: The exception to render as HTML.
        """
        # TODO When we can determine if we are in production or not, we
        # can return immediately if we are in production since the
        # end user will not need the stack trace and it will reveal
        # details about the code we don't necessarily want revealed. A
        # bool argument can be used to force the trace back to be
        # created, however.

        super().__init__(*args, **kwargs)

        # To identify the traceback article, give the article a
        # 'traceback' class: <article class="traceback">...
        self.classes += 'traceback'

        # Build the DOM
        for tb in exc.traces(ex):
            div = dom.div()
            self += div
            div  +=  dom.text('File ')
            div  +=  dom.span(tb.file,    class_='file')
            div  +=  dom.text(', at ')
            div  +=  dom.span(tb.lineno,  class_='lineno')
            div  +=  dom.text(', in ')
            div  +=  dom.span(tb.name,    class_='name')

class _404(page):
    """ An error page to show that the requested page was not found.
    """
    # NOTE I think this shoud inherit from ``error``.
    def main(self, ex: www.NotFoundError):
        """ The main method of the page.

        :param: ex www.NotFoundError: The www.NotFoundError exception
        object that caused this error page.
        """
        self.title = 'Page Not Found'
        self.main += dom.h1('Page Not Found')

        self.main += dom.paragraph('''
        Could not find <span class="resource">%s</span>
        ''', ex.resource)

    @property
    def name(self):
        """ Return teh name of the error page.
        """
        return type(self).__name__.replace('_', '')

