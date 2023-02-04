# vim: set et ts=4 sw=4 fdm=marker

#######################################################################
# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2022
########################################################################

from contextlib import suppress
from dbg import B, PM
from uuid import UUID, uuid4
from entities import classproperty
import asset, ecommerce
import datetime
import db
import dom
import entities
import ecommerce
import exc
import file
import inspect
import itertools
import orm
import os
import primative
import textwrap
import pycountry
import party
import www
import MySQLdb

# References:
#
# WAI-ARIA Authoring Practices 1.1
# https://www.w3.org/TR/wai-aria-practices/
#
# How to use structured data
# https://developers.google.com/search/docs/advanced/structured-data/intro-structured-data#structured-data

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

    # Indicates whether or not the _ensuring method is being run
    _ensuring = False

    def __init__(self, *args, **kwargs):
        """ Create a new web ``site`` object.
        """
        super().__init__(*args, **kwargs)

        # NOTE It may be unwise to put any initialization code here that
        # depends on the database. Consider putting it in the
        # site._ensure method. For example, code that realize on the
        # public/ directory (self.public) needed to be put in
        # site._ensure. This was necessary because the code that ensures
        # public/ exists needs to have the correct proprietor
        # and site entity established. Plus the directory itself needs
        # to be created in the right security context.

        self.index = None
        self._pages = None
        self._html = None
        self._head = None
        self._lang = 'en'
        self._keywords = str()
        self._description = None
        self._charset = 'utf-8'
        self._viewport = \
            'width=device-width, initial-scale=1, shrink-to-fit=no'

        self.sidebars = sidebars()

        # Give the site a default title of the class's name. 
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

        # Is the _ensure method being run. This prevents infinite
        # recursion
        if not site._ensuring:
            try:
                site._ensuring = True

                # Ensure the site is stored in the database
                self._ensure()
            finally:
                site._ensuring = False

    # Host name of the site
    host = str

    # Collection of web hits to the site
    hits = ecommerce.hits

    # Collection of users who may log in to the site
    users = ecommerce.users

    # Directory to store the site's files
    directory = file.directory

    _resources = None

    def _ensure(self):
        """ Ensure that the site object is stored in the database as
        well as its proprietor and its association with its proprietor.
        Normaly, these data will need to be saved once.

        This method is called by the constructor to ensure that every
        time a site is instantiated, its data is saved in the database.
        """

        # Only _ensure subtypes of `site`
        if type(self) is site:
            return

        ''' Demand Constants are set up '''

        try:
            self.Id
        except AttributeError:
            raise AttributeError(
                'Sites must have an Id constant attribute'
            )

        if not isinstance(self.Id, UUID):
            raise TypeError(
                "Site's Id constant is the wrong type"
            )

        try:
            self.Proprietor
        except AttributeError:
            raise AttributeError(
                'Sites must have a Proprietor constant attribute'
            )

        if not isinstance(self.Proprietor, party.party):
            raise TypeError(
                "Site's Proprietor constant is the wrong type"
            )

        ''' Save self '''

        # Get the root user
        root = ecommerce.users.root

        # Ensure as root and use the site's proprietor
        with orm.sudo(), orm.proprietor(self.Proprietor.id):
            if not self.Proprietor.name:
                raise ValueError(
                    "Site's Proprietor constant "
                    'must have an id an and a name'
                )

            ''' Create or retrieve site record '''

            insert = False
            try:
                ws = type(self)(self.Id)
            except db.RecordNotFoundError:
                insert = True
            except MySQLdb._exceptions.ProgrammingError as ex:
                if ex.args[0] == MySQLdb.constants.ER.NO_SUCH_TABLE:
                    self.orm.create()
                    insert = True
                else:
                    raise

            if insert:
                ws = type(self)(
                    id = self.Id, 
                    name = self.Proprietor.name, 
                )

                ws.directory
                ws.save()

            # Take the data in ws and copy it self
            sup = self
            wssup = ws
            while sup:
                for map in wssup.orm.mappings:
                    if isinstance(map, orm.fieldmapping):
                        # Accept fieldmapping
                        pass
                    elif isinstance(map, orm.entitymapping):
                        # Accept entitymappings unless they are security
                        # related
                        if map.isproprietor or map.isowner:
                            continue
                    else:
                        # Filter out other types
                        continue
                    
                    # Move the value in wssup's map to sup's 
                    v = wssup.orm.mappings[map.name].value
                    sup.orm.mappings[map.name].value = v

                # Make sure that self and its supers aren't flag as new,
                # dirty or markedfordeletion
                sup.orm.persistencestate = False, False, False

                # Ascend to the super/base entity
                sup = sup.orm._super
                wssup = wssup.orm.super

            ''' Ensure proprietor '''

            # Ensure that the site's proprietor exists in the database
            # as well
            try:
                propr = self.Proprietor.orm.reloaded()
            except db.RecordNotFoundError:
                propr = self.Proprietor
                sup = propr
                while sup:
                    sup.owner = root
                    sup.proprietor = propr
                    sup.orm.isnew = True
                    sup = sup.orm.super
                propr.save()
                
            ''' Associate the proprietor '''

            # Associate the site (self) to its proprietor in the
            # database via the asset_party association
            with orm.proprietor(propr):
                for ap in self.asset_parties:
                    if ap.asset_partystatustype.name == 'proprietor':
                        if ap.party.id == propr.id:
                            break
                else:
                    self.proprietor = propr

                    apst = party.asset_partystatustype(
                        name = 'proprietor'
                    )

                    ap = party.asset_party(
                        asset                  =  self,
                        party                  =  propr,
                        asset_partystatustype  =  apst,
                    )
                    self.asset_parties += ap

                    sup = self
                    while sup:
                        sup.owner = root
                        sup = sup.orm.super

                self.proprietor = propr

            # Get (or create if needed) the site's public/ directory
            # after the site has been established.
            pub = self.public

            try:
                # Get the favicon.ico file entity from public/
                favicon = pub['favicon.ico']
            except IndexError:
                # If it doesn't exist, get file from the `favicon`
                # attribute
                if favicon := self.favicon:
                    # Add the favicon.ico to public/
                    pub += favicon
            else:
                favicon.body = self.favicon.body

            # Save the site plus its associations and directories
            self.save()

    @property
    def favicon(self):
        """ When overriden by subclasses, this property returns a
        `file.file` object that contains the binary data in its body to
        represent a favicon (as would be requested automatically by
        browsers as /favicon.ico).

        By default, None is returned, since the base class can't now
        what the subclass of `site` wants the favicon to be beforehand.

        The `file` object is stored in the framework's file system when
        the `site` object is initialized. This allows developers to
        set the favicon data in this @property although it is served to
        user agents like any other file would be.
        """
        return None

    @property
    def styles(self):
        ''' This property can be overridden by subclasses to provide
        zero ore more CSS-like objects. These object are added as
        <style> elements to the <head> of `page` objects 
        
        A CSS-like object can be a simple string with some CSS in it.
        Alternatively, it can be a dom.style object or some other
        instance that the framework recognises (or is made to recognize)
        as CSS-like (perhaps some sort SASS or LESS object that can be
        complied to CSS). 

        A single instance of a CSS-like object can be returned, or an
        iterable object (such as a list or some other collection) of
        such CSS-like objects can be returned. `None` can also be
        returned implying that there are no CSS-like objects (this
        is the default).
        '''
        return None

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
        a constituent of the ``site`` class so calling the sites save()
        method will cascade the persistence operations into the
        directory and any inodes beneath it.
        """
        dir = attr()
        if dir is None:
            site = file.directories.site
            try:
                # If the web site (pom.site) hasn't been created
                # yet, attr() would have returned None (thus bringing us
                # here). However, the site's directory may be available
                # via the `site` directory because the directory may
                # exist in the database. So try to get it out of `site`
                # first. 
                dir = site[self.id.hex]
            except IndexError:
                # If it wasn't in site, create it here
                dir = file.directory(self.id.hex)
                site += dir

            attr(dir)

        return dir

    @property
    def public(self):
        """ Returns the public/ directory (`file.directory`) of this
        `site`.

        Though the directory returned is a framework entity (a
        `file.directory`), this directory is analogous to the public/
        directories that are typically found on websites. These
        directories typically contain artifacts that need to be publicly
        accessable such as CSS files, JavaScript files and favicon.ico
        files.
        """
        dir = self.directory
        try:
            pub = dir['public']
        except IndexError:
            pub = file.directory('public')
            dir += pub

        return pub

    @property
    def resources(self):
        """ Returns the sites's resources directory. If the 'resources'
        directory doesn't exist, it is created.
        """
        if not self._resources:
            # NOTE We may not need the try:except logic here if we decide to
            # implement the suggestion at bda97447 (seach git-log).
            try:
                # TODO:bef8387e It's not clear who the owner should be
                # at this point. If the site's resource directory hasn't
                # been created yet, the anonymous user might end up
                # being the owner. Or if authenticated, the owner of the
                # directory will have rights to that directory. The user
                # that ends up creating the resources directory probably
                # shouldn't have those rights. Maybe the site object
                # needs its own admin user for these types of things.
                with orm.sudo():
                    self._resources = self.directory['resources']

            except IndexError:
                resx = file.directory('resources')
                self.directory += resx
                
                # If the owner hasn't been set, make root the owner. 
                # See TODO:bef8387e above.
                with orm.sudo():
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
        # HACK: 8210b80c
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

    def __repr__(self):
        """ Return a string representation of the site object.
        """
        return '%s()' % type(self).__name__

    def __str__(self):
        """ Return a string representation of the site object.
        """
        return repr(self)

    def __getitem__(self, path):
        """ An indexer to get a page in the site:

            ws = mysite()
            about_page = ws['/en/about']

        :param: path str: The path to the web ``page``.
        """
        if path in ('/', ''):
            path = '/index'

        return self.pages[path]

    def __call__(self, path):
        """ Similar to __getitem__ except that, if the page can not be
        found, None is returned.
        """

        path = '/index' if path == '/' else path
        return self.pages(path)

    @property
    def lang(self):
        """ Returns the default language for tihs `site`.
        """
        return self._lang

    @lang.setter
    def lang(self, v):
        self._lang = v

    @classproperty
    def languages(cls):
        ''' A list of accepted languages for the site. For example:
            
            ['en', 'es', 'fr', 'de']

        Sites that wish to accept a different set of languages can
        override this property. The default is to always accept English.
        '''
        # Always accept English
        return ['en']

    @classmethod
    def _strip(cls, path):
        """ A classmethod to taka a path, and remove the language code
        in the path. For example given:

            /en/my/page

        return:

            /my/page

        The language code will only be remove if it is in the site's
        list of accepted languages. See site.languages for more.
        """

        # Break path into list
        segs = [x for x in path.split('/') if x]

        if len(segs):
            # Get the first element to see if it's a language code
            seg = segs[0]

            # If it is an accepted language code...
            if seg in cls.languages:
                # Reconstitute the path, without the language code, and
                # return it.
                return '/'.join(segs[1:])
        else:
            return None
        
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

        styles = self.styles
        if styles:
            if isinstance(styles, str):
                styles = [styles]
                
            for style in styles:
                self._head += dom.style(style)

        # Add the JavaScript event handling code as a script tag. We
        # make the `id` a UUID so it can be referenced in tests.
        self._head += dom.script(
            self._eventjs, id = 'A0c3ac31e55d48a68d49ad293f4f54e31'
        )

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

    @classproperty
    def _eventjs(cls):
        """ Returns the JavasScript a browser will use to process
        dom.events.

        See the docstring at dom.event for details on DOM event
        processing.
        """

        #// NOTE: To improve readability, you can set you editor to do
        #// syntax highlighting for JavaScript. In Vim, you can use:
        #//
        #//     set syn=javascript
        #//

        r = '''
function is_nav_link(e){
    /* Returns true if the element `e` is a "nav link",
    i.e., it is an anchor tag nested within a <nav>.
    */

    rent = e.parentNode

    found = false
    while (rent){
        if (rent.tagName == 'NAV'){
            nav = rent
            found = true
            break
        }
        rent = rent.parentNode
    }

    if (!found) return false
'''

        r += f'''
    as = rent.querySelectorAll('{page.IsNavSelector}')
'''

        r += '''
    for(a of as){
        if (a === e){
            return true
        }
    }

    return false
}

function ajax(e){
    /* Process the event for the given control.  */

    // The event trigger (e.g., "blur", "click", etc.)
    var trigger = e.type

    // The control that the event happened to
    var src = e.target

    // Is the element a navigation link
    var isnav = is_nav_link(src)

    var nav = src.closest('nav');

    // If the element being clicked is a nav link
    if (isnav){
        // If we are in SPA mode
        if (inspa){
            // Is the link from the Spa menu
            var isspanav = nav.getAttribute('aria-label') == 'Spa';

            if (!isspanav){
                // If we are in SPA mode but not in the Spa menu, allow
                // for traditional navigation.
                return;
            }

            // Prevent the browser from trying to load the HREF at the
            // navigation link. We will do that here.
            e.preventDefault()
        }else{
            // If the user clicked a nav link, but we aren't in SPA
            // mode, allow the browser to navigate to the link in the
            // traditional (non AJAX) way.
            return;
        }
    }

    // If we have an <input> with a type of "text"...
    if (src.type == 'text'){
        // Ensure the value of the <input>'s `value` attribute is set to
        // the actually in the textbox. This ensures that, when it's
        // HTML is transmitted, the "value" is send as well.
        src.setAttribute('value', src.value)
    }

    // Get all alements that are fragments for the src.
    var frag = src.getAttribute('data-' + trigger + '-fragments')
    var els = document.querySelectorAll(frag)

    // Get the name of the event handler of the trigger
    var hnd = src.getAttribute('data-' + trigger + '-handler')

    var html = null
    var pg

    // Get the page's <root>
    var main = document.getElementsByTagName('main')[0]

    // If the user clicked a nav link
    if (isnav){
        pg = src.getAttribute('href')
    }else{
        // Concatenate the fragment's HTML
        html = ''
        for(el of els)
            html += el.outerHTML

        pg = window.location.href
    }

    // Create the dictionary to send to the server
    var d = {
        'hnd':      hnd,
        'src':      src.outerHTML,
        'trigger':  trigger,
        'html':     html     
    }

    // Use XMLHttpRequest to send the XHR request 
    var xhr = new XMLHttpRequest()
    xhr.onreadystatechange = function() {
        if (this.readyState == 4){

            // If success...
            if (this.status < 400){

                // Parse the HTML response
                var parser = new DOMParser()

                var els = parser.parseFromString(
                    xhr.responseText, "text/html"
                )

                // Get the direct children under the <body> tag of the
                // HTML. These are the HTML fragments that will replace
                // current HTML fragments.
                els = els.querySelectorAll('html>body>*')

                if(inspa){
                    let new_ = els[0]
                    let url = new_.getAttribute('data-path')

                    main.parentNode.replaceChild(new_, main)
                    window.history.pushState(
                        new_.outerHTML, null, pg
                    )
                }else{ // Not inspa

                    // Iterate over each element and replace their
                    // client-side counterpart
                    for(el of els){
                        // Use the fragment's id to find and replace
                        let old = document.querySelector('#' + el.id)
                        old.parentNode.replaceChild(el, old)
                    }
                }
            }else{ // If there was an error...
                // Remove any elements with a class of 'exception'
                let els = document.querySelectorAll('.exception')
                els.forEach(e => e.remove())

                // Insert the response HTML making it the first element
                // under <main>. The response HTML will have a parent
                // element with an "exception" class.
                main.insertAdjacentHTML(
                    'afterbegin', xhr.responseText
                )
            }
        }
    }

    // POST to the current URL
    xhr.open("POST", pg)
    xhr.setRequestHeader('Content-Type', 'application/json')
    xhr.send(JSON.stringify(d))
}

// Once content has been loaded (DOMContentLoaded), we can add listeners
// to the controls.
document.addEventListener("DOMContentLoaded", function(ev) {
'''

        r += f'    trigs = {list(dom.element.Triggers)}'

        r += '''
    // For each currently supported trigger (you may
    // have to update Triggers if the event you want to
    // support doesn't exist)
    for (trig of trigs){
        var els = document.querySelectorAll(
            '[data-' + trig + '-handler]'
        )

        for(el of els)
            el.addEventListener(trig, ajax)
    }

    els = document.querySelectorAll(
        'header>section>nav>ul>li a'
    )

    for(el of els)
        el.addEventListener('click', ajax)

    window.addEventListener('popstate', (e) => {
        // Parse the HTML response
        var parser = new DOMParser()

        var new_ = parser.parseFromString(
            e.state, "text/html"
        )

        new_ = new_.querySelector('html>body>main')

        var old = document.querySelector('main')

        old.parentNode.replaceChild(new_, old)
    });

    var main = document.querySelector('main')
    window.history.pushState(
        main.outerHTML, null, window.location.pathname
    )

    // We default to non-SPA.
    if (main.hasAttribute('spa-data-path')){
        inspa = true
    }else{
        inspa = false
    }
});

'''
        #// Return the JavaScript
        return r

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
    def __init__(self, o, href=None, img=None):
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

        self.href = ecommerce.url(address=href) if href else None
        self.image = ecommerce.url(address=img) if img else None

    def clone(self):
        """ Create a new logo object based on self and return.
        """
        el = type(self)(self.text, href=self.href, img=self.image)
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
        if href := self.href:
            a = dom.a()
            a.href = href

            if img := self.image:
                a += dom.img(src=img, alt=self._text)

            els += a
        else:
            els += dom.span(self._text)
        return els

    @elements.setter
    def elements(self, v):
        dom.element.elements.fset(self, v)

class menus(dom.section):
    """ Represents a collection of ``menu`` objects
    """

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
        cls = type(self).__name__
        args = ', '.join(repr(x) for x in self)
        return f'{cls}({args})'

class menu(dom.nav):
    # TODO:c0336221 Currently, there are issues altering attributes en
    # masse with menu and its subsidiaries:
    #
    #   for itm in menu_items.all:
    #       itm.id = False
    # 
    # Part of this is an issue with the way attributes aren't properly
    # set or deleted. These issue (12c29ef9) will be addressed
    # eventually in pom.attributen code. When they are, tests should be
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

    ''' Inner classes '''
    class items(dom.ul):
        """ A collection of ``item`` objects (<li>) which contain the
        menu items.
        """
        def clone(self):
            """ Create and return an ``items`` based on self.
            """
            itms = type(self)()

            for itm in self:
                itms += itm.clone()

            return itms

        def seperate(self):
            """ Add a seperator to the list of menu items.
            """
            self += menu.separator()

    class item(dom.li):
        """ Represents an item in a menu such as a hyperlink or a
        ``seperator``.
        """
        def __init__(self, o, href=None, *args, **kwargs):
            """ Create the menu item.

            :param: o str|page: 
                If str, o is the text used for the menu item.
                If page, the menu item links to that page.

            :param: href str: The optional hyperlink to use. Used in
            conjunction with o to create a link when it is a str.
            """
            super().__init__(*args, **kwargs)

            self.href   =  href
            self._page   =  None

            if isinstance(o, str):
                if href:
                    self += dom.a(o, href=self.href)
                else:
                    self += dom.text(o)

            elif isinstance(o, page):
                self.page = o

            else:
                raise TypeError('Item requires text or page object')

            self._items = None

        @property
        def text(self):
            """ Return the text of the item.
            """
            for el in self:
                if isinstance(el, dom.text):
                    return el.value

            if a := self.a:
                return a.text

            if pg := self.page:
                return self.page.name

        @property
        def page(self):
            return self._page

        @page.setter
        def page(self, v):
            self._page = v
            a = None
            for el in self:
                if isinstance(el, dom.a):
                    a = el

            if a:
                self.elements.remove(a)

            self += dom.a(v.Name, href=v.path)
            
        @property
        def items(self):
            """ Return this `menu.items` collection of `menu.item`. It's
            this property that allows menus to be of an infinite depth.
            """
            if not self._items:
                self._items = menu.items()

                # Append the items collection to self. In DOM terms, we
                # are append a <ul> to an <li>:
                #
                #   <nav>
                #     <ul>
                #       <li>
                #         File
                #         <ul> <!-- this -->
                #           <li>
                #             Open
                #           </li>
                #         </ul>
                #      </li>
                #    </ul>
                #  </nav>
                #
                self += self._items

            return self._items

        @items.setter
        def items(self, v):
            """ Set's the items value.

            This is necessary for appends to work right.

            :param: v menu.item: The item to set.
            """
            self._items = v

        def clone(self):
            """ Create and return a new menu item based on this one.
            """

            # NOTE Don't clone self.page. The new item will point to the
            # existing page.
            o = self.page if self.page else self.text
            itm = type(self)(o, href=self.href)

            itm.items = self.items.clone()

            itm.attributes = self.attributes.clone()
            return itm

        def seperate(self):
            """ Create a seperator in this menu item's ``items`` collection.
            """
            self.items.seperate()

        def __repr__(self):
            """ Returns a string represention of the menu item.
            """
            cls = type(self).__qualname__.replace('pom.', '')

            pg = self.page
            if pg:
                return f"{cls}('{pg.name}', page='{pg.path}')"
            else:
                if a := self.a:
                    return f"{cls}('{a.text}', href='{a.href}')"
                else:
                    return f"{cls}('{self.text}')"

        @property
        def a(self):
            """ Return the anchor (dom.a) of this menu item. If no
            anchor exists yet, None is returned.

              <nav>
                <ul>
                  <li>
                    <a href="/open">Open</a>  <!-- This -->
                  </li>
                </ul>
              </nav>

            """
            as_ = self['a']
            if as_.issingular:
                return as_.only

            return None

    class separator(item):
        """ An entry in a collection of menu item that seperates one set
        from anonther.

            [O]pen
            [S]ave
            Save [A]s
            ---------
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

    ''' Class members of `menu` '''

    def __init__(self, name, *args, **kwargs):
        """ Create a new menu.

        :param: name str: The name of the menu.
        """
        super().__init__(*args, **kwargs)
        self.name = name
        self.aria_label = self.name.capitalize()

        # NOTE:23db3900 Create the items collection here. This has the
        # unfortunate side affect of causing empty menus to be rendered
        # with an empty <ul>:
        #
        #   <nav>
        #     <ul></ul>
        #   </nav>
        # 
        # We could solve this problem by lazy-loading the items using
        # a getter @property. However, the name of that method would be
        # pom.menu.items, and this has already been taken (see the
        # `items` class above).
        self.items = menu.items()

    def __setattr__(self, attr, v):
        """ XXX """
        if attr == 'items':
            try:
                itms = self.__dict__['items']
            except KeyError:
                pass
            else:
                self.remove(lambda x: x is itms)

            self.__dict__['items'] = v

            self += self.items
        else:
            object.__setattr__(self, attr, v)
        

    @classmethod
    def make(cls, pgs, name=None, itm=None):
        """ Make and return a `menu` object based on the `pages`
        collection (pgs) given. This is a recursive method so the `menu`
        will be as deeply nested as the `pgs` are.

        :param: pgs pages: A collection of pages.

        :param: name str: The name of the menu.

        :param: itm menu.item: Used internally. The menu item object
        that is currently being processed.
        """
        isrecursing = not bool(name)

        if isrecursing:
            itms = itm.items
        else:
            mnu = menu(name)
            itms = mnu.items

        for pg in pgs:
            # Don't add error pages to the menu
            if pg.name == 'error':
                continue

            itm = menu.item(o=pg)
            itms += itm

            pgs = pg.pages
            if pgs.ispopulated:
                cls.make(pgs, itm=itm)

        if not isrecursing:
            return mnu

    @property
    def ismain(self):
        return self.name == 'main'

    def clone(self):
        """ Create and return a new menu based on this menu.
        """
        mnu = type(self)(self.name)
        mnu.items = self.items.clone()
        mnu.attributes = self.attributes.clone()
        return mnu

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
        """ Return `site` object that this `pages` collection belongs
        to. 

        None is returned if the site doesn't exist or can't be found.
        """
        rent = self.parent
        while rent:
            if isinstance(rent, site):
                return rent
            rent = rent.parent

        return None

    def __getitem__(self, path):
        """ An indexer to get the page in the collection given a path.

        :param: path str|list: The path of the page to get. For example, 
            
            /en/bio/luser

        or in list form:

            ['en', 'bio', 'luser']
        """
        if isinstance(path, str):
            segs = [x for x in path.split('/') if x]

        elif isinstance(path, list):
            segs = path
        else:
            return super().__getitem__(path)
           
        seg = segs[0] if segs else None

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

        for pg in self:
            if pg.name == obj.name:
                # We want to be able to add a page even if a page with
                # the same name already exists.

                # NOTE This was appearently found useful at some point,
                # although, looking back on it, it seems like a bad idea
                # because it could conceal logic errors. It was added in
                # commit c972a46b.
                del self[pg]
                break

        super().append(obj, uniq)

class page(dom.html):
    """ Represents a web page.
    """
    ExceptedBooleansStrings = (
        ('false', '0', 'no', 'n'),
        ('true', '1', 'yes', 'y')
    )

    # The CSS selector to determine if an anchor is a nav link
    # NOTE This should do what we need it to. However, due to
    # efa5825e, we need to add a space between nav and ul. When efa5825e
    # is fixed, we should be able to uncommment this.
    #IsNavSelector = 'nav>ul>li a'
    IsNavSelector = 'nav ul>li a'

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
            # A page doesn't necessarily need a main function on
            # instantiation.  # However, an AttributeError will be
            # raised if the page is ever accessed.
            pass

        self.clear()

    def _lingualize(self, lang):
        """ XXX """
        mnus = self.header.menus
        for a in mnus['a']:

            # If the anchor has already been lingualized
            if a.href.startswith(f'/{lang}/'):
                continue

            href  =  a.href
            sep   =  os.path.sep
            a.href = os.path.join(
                sep, lang, href.lstrip(sep)
            )

    @property
    def spa(self):
        """ If this `page` object is a subpage of a SPA, return its SPA
        `page`. Otherwise, return None.
        """
        pg = self.page
        while pg:
            if isinstance(pg, spa):
                return pg

            pg = pg.page

        return None

    @property
    def isspa(self):
        """ Returns True if this `page` object is a SPA page, False
        otherwise.
        """
        return isinstance(self, spa)

    @property
    def resources(self):
        """ Return the collection of `file.resource` objects the page
        will use.
        """
        if self._resources is None:
            self._resources = file.resources()

            self.resources.onbeforeadd += self._resources_onbeforeadd

        return self._resources

    @resources.setter
    def resources(self, v):
        """ Set the collection of `file.resource` objects that this page
        will use.
        """
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
            msg = dom.p(msg)

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
            if ws := self.site:
                self._title = f'{ws.title} | {self.Name}'
            else:
                self._title = self.Name

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
                title = self._head['title'].only
            else:
                self._head = dom.head()
                self._head += (title := dom.title())

            title.text = self.title

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
        data-path attribute to the path of the page. Also is used to
        clear any state data that may continue to exist between calls to
        the same page.
        """
        self.main = dom.main()
        self.main.attributes['data-path'] = self.path
        self._called = False
        self._attemped = False

        # Invalid the header so it will be recreated (if needed) when
        # page is re-invoked.
        self._header = None

    def __call__(self, eargs=None, *args, **qsargs):
        """ This method calls into this `page`'s `main` method which the
        web developer writes.

            class mypage(page):
                def main(self):
                    ...

            # Init page
            pg = mypage()

            # "Calling" the page ends up calling the main() method
            # defined above.
            pg() 

        :param: eargs dom.eventargs: If the call is made by an event,
        (e.g., the click of a button on a web page), eargs will be a
        dom.eventargs object. This object will contain a reference to
        the event handler needed to process the event as well as the
        HTML from the webpage from which the event was fired.

        :param: *args tuple: Do not use. If an attempt is made to use
        it, a ValueError will be raised encouraging the useng to use
        **kwargs (i.e., qsargs)

        :param: *qsargs dict: A dictionary that holds the query string
        arguments the webpage is being called with. For example, if the
        URL look like:
            
            /en/time?greet=1&tz=America/Phoenix&a=1&b=2

        qsargs will be:

            {'a': '1', 'b': '2', 'greet': '1', 'tz': 'America/Phoenix'}

        """

        # A call was attemped
        self._attemped = True

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

                # If we are in a web context
                if app := www.application.current:
                    # Get the current request object
                    req = app.request
                else:
                    # It's possible to __call__ a page object directly
                    # (not through an HTTP request). In that case, the
                    # req would be None.
                    req = None
                    
                # Determine if page is being called from an event
                # trigger (e.g., when a menu item is clicked and the SPA
                # loads a subpage.  If `eargs is not None`, then we are
                # being called by an event handler. 
                isevent = bool(eargs)

                if isevent:
                    if eargs.handler:
                        meth = getattr(self, eargs.handler)
                    else:
                        meth = self._mainfunc

                    if eargs.handler:
                        meth(src=eargs.src, eargs=eargs)
                    else:
                        meth()
                else:
                    try:
                        main = self._mainfunc
                    except AttributeError as ex:
                        cls = str(type(self))
                        raise AttributeError(
                            f'Page class needs main method: {cls}'
                        ) from ex

                    # If there is an HTTP request object, set the
                    # `page`'s `lang` attribute to that of the
                    # `request`.  Remember that `page` is a subclass of
                    # dom.html, so we are basically setting the lang
                    # attribute of the <html> tag:
                    if req:
                        self.lang = req.language

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

        main = self.main
        body = self.body
        sbs = self.sidebars

        if main not in body:
            body += main

        if sbs not in body:
            body += sbs

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
        """ Return the web ``site`` that this `page` belongs to.
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

class spas(pages):
    """ A collection of `spa` pages.
    """

class spa(page):
    """ The main page of a single-page application (SPA).

    `spa` objects are used to build the main page of the SPA that get's
    loaded with an HTTP GET. As the user navigates to other pages within
    the SPA, those pages are loaded through XHR requests and their
    content replace whatever is in the main SPA page's <main> element.
    These pages are called the *subpages* of the SPA. 
    """

class header(dom.header):
    """ Represents the header portion of a web page.

    A page header contains a menus object to contain 0 or more menus in
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
        self._logo = None

    def clone(self):
        """ Create and return a ``header`` objecs based on the values in
        this ``header``.
        """
        hdr = type(self)(self.site)
        hdr.menus = self.menus.clone()

        if logo := self.logo:
            hdr.logo = logo.clone()

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
        """ The collection of menus for this ``header``.
        """
        return self._menus

    @menus.setter
    def menus(self, v):
        self._menus = v

    @property
    def menu(self):
        """ Return the main menu for this ``header`` object.
        """
        for mnu in self.menus:
            if mnu.ismain:
                return mnu

        return None

    @menu.setter
    def menu(self, v):
        for i, mnu in self.menus.enumerate():
            if mnu.ismain:
                self.menus[i] = mnu
                break
        else:
            v.name = 'main'
            self.menus += v

    def makemain(self):
        if self.menu:
            raise ValueError('Main menu already exists')

        self.menu = menu.make(self.site.pages, name='main')

        return self.menu

    @staticmethod
    def _getmenu(ws):
        # XXX Dead code?
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

        for itm in getitems(ws.pages):
            itm._parent = None
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
    """ A subclass of dom.article that renders an exception as HTML.
    """
    def __init__(self, ex, *args, **kwargs):
        """ Create the trackback article.

        :param: ex Exception: The exception to render as HTML.
        """
        super().__init__(*args, **kwargs)

        # To identify the traceback article, give the article a
        # 'traceback' class: <article class="traceback">...
        self.classes += 'traceback'

        ul = dom.ul()
        self += ul

        # Build the DOM
        for tb in exc.traces(ex):
            li = dom.li()
            ul += li
            li  +=  dom.text('File ')
            li  +=  dom.span(tb.file,    class_='file')
            li  +=  dom.text(', at ')
            li  +=  dom.span(tb.lineno,  class_='lineno')
            li  +=  dom.text(', in ')
            li  +=  dom.span(tb.name,    class_='name')

class message(dom.article):
    """ An <article> that contains a message for the user.

    The message can be a simple string message, or a report on an object
    such as an `Exception`.
    """
    def __init__(self, msg, *args, **kwargs):
        """ Create the message <article>.

        :param: msg str|Exception: The object to report the message on.
            if str:
                The message object simply displays `msg` to the user in
                a <p> tag.

            if Exception:
                The Exception's message is reported and a traceback is
                created in a <details> element.
        """
        super().__init__(*args, **kwargs)
        self.message = msg
        self._build()

    def _build(self):
        """ A private message to build the DOM object. Called during
        construction.
        """
        ex = msg = None
        if isinstance(self.message, Exception):
            ex = self.message
            msg = str(ex)
        elif isinstance(self.message, str):
            msg = self.message

        p = dom.p(class_='message')
        self += p

        if ex:
            # NOTE The JavaScript (eventjs) requires this class.
            self.classes += 'exception'

            p += dom.span(type(ex).__name__, class_='type')
            p += dom.text(': ')

            # TODO Add tests to ensure exception messages are escaped
            # properly
            p += dom.span(str(ex), class_='message')

            details = dom.details(class_='traceback')
            self += details

            details += dom.summary('Stacktrace')
            details += traceback(ex)
        else:
            p.text = msg

class _404(page):
    """ An error page to show that the requested page was not found.
    """
    # TODO I think this should inherit from ``error``.

    # NOTE Commented out reference to www.NotFoundError. When `gunicorn`
    # runs www.py, www.py imports pom.py. Referencing `www` before
    # `www.py` has been fully loaded causes a circular reference issue.
    # This is fine; it is not necessary to annotate this
    # parameter. Parameters are only necessary to annotate so that user
    # input (query strings, etc.) are defined ahead of time. This page,
    # being an exception page, is never call by the user directly.
    #def main(self, ex: www.NotFoundError):

    def main(self, ex):
        """ The main method of the page.

        :param: ex www.NotFoundError: The www.NotFoundError exception
        object that caused this error page.
        """
        self.title = 'Page Not Found'
        self.main += dom.h1('Page Not Found')

        self.main += dom.p(
            'Could not find '
            f'<span class="resource">{ex.resource}</span>'
        )

    @property
    def name(self):
        """ Return the name of the error page.
        """
        return type(self).__name__.replace('_', '')

