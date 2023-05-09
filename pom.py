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
from func import getattr
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
                        # XXX Explain
                        sup.orm.mappings['owner'].value = root
                        sup.orm.mappings['owner__userid'].value = root.id
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
    var rent = e.parentNode

    var found = false
    while (rent){
        if (rent.tagName == 'NAV'){
            found = true
            break
        }
        rent = rent.parentNode
    }

    if (found){
'''

        r += f'''
        as = rent.querySelectorAll('{page.IsNavSelector}')
'''

        r += '''
        for(var a of as){
            if (a === e){
                return true
            }
        }
    }

    return false
}

function is_page_link(e){
    /* Returns true if the user clicked a page link, false otherwise.

    A page link as an anchor that links to another, internal page in the
    SPA application. The intention of clicking one in to navigate to the
    page through an XHR call. The page's HTML is put into the existing
    <main> tag, replacing <main>'s existing content.
    */
    var main = document.querySelector('main')
    var spa_path = main.getAttribute('spa-data-path')
    var href = e.getAttribute('href')

    // If href is null, it's not a page link
    if (href == null){
        return false
    }

    // If the anchor is a reference to the current page, it is not
    // considered a link
    if (href == document.location.pathname){
        return false
    }

    return href.startsWith(spa_path)
}

function ajax(e){
    // TODO Write entire handler in a try block. Otherwise we may not
    // get to `e.preventDefault()` and we end up submitting the form,
    // navigating the browser to a different pages, etc.

    /* Process the event for the given control.  */

    // The event trigger (e.g., "blur", "click", etc.)
    var trigger = e.type

    // The control that the event happened to
    var src = e.target

    // Is the element a navigation link
    var isnav = is_nav_link(src)

    // Is the element a page link
    var ispg = !isnav && is_page_link(src)

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

        }else{
            // If the user clicked a nav link, but we aren't in SPA
            // mode, allow the browser to navigate to the link in the
            // traditional (non AJAX) way.
            return;
        }
    }

    // At this point, preventDefault() because it's all AJAX from here. 
    e.preventDefault()

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

    // If the user clicked a page link
    }else if (ispg){
        html = ''
        pg = src.getAttribute('href')
    }else{
        // Concatenate the fragment's HTML
        html = ''
        wake(els)
        for(el of els){
            html += el.outerHTML
        }

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
            console.group('readyState 4; status ' + this.status)

            var els = document.querySelectorAll('.exception')
            els.forEach(e => e.remove())

            // If success...
            if (this.status < 400){
                // If no HTML was returned from the XHR request, we can
                // return. Usually, events will return HTML, however it
                // is possible that, in some cases, they will choose not
                // to.
                if(!xhr.responseText){
                    console.info('No response')
                    return
                }

                // Parse the HTML we received into a DOM object.
                var temp = document.createElement('template')
                temp.innerHTML = xhr.responseText
                els = temp.content.children

                // If a <main> tag was returned, we are doing an SPA
                // page load.
                if(els[0].tagName == 'MAIN'){
                    // Get the new <main> element
                    let new_ = els[0]

                    // Replace the current <main> element with the new_
                    // one received from the AJAX call.
                    main.parentNode.replaceChild(new_, main)

                    // Make sure event handler are hooked up to new
                    // <main> HTML.
                    listen(new_);

                    // Push the HTML of the new <main> object on to the
                    // history stack so users can get to it by clicking
                    // the browser's back button.

                    console.debug('<MAIN> pushState')

                    var url = new_.getAttribute('data-url')

                    window.history.pushState(
                        new_.outerHTML, null, url ?? pg
                    )

                    exec([new_])

                // If the element is not a <main>, we are doing a
                // regular AJAX call, i.e., we are not loading a new
                // <main> as a SPA page.
                }else{
                    // Iterate over each element and replace their
                    // client-side counterpart
                    for(el of els){
                        // Add event listeners to new HTML
                        listen(el);

                        // Get the id of the element. `el.id` doesn't
                        // work here.
                        let id = el.getAttribute('id')

                        // Use the fragment's id to find and replace
                        let old = document.querySelector('#' + id)
                        old.parentNode.replaceChild(el, old)

                        // Execute any .instructions in the HTML. If
                        // there is a set-url instruction, the URL will
                        // be set using a history.pushState.
                        exec([el])
                    }
                }
            }else{ // If there was an error...
                document.querySelectorAll('dialog').forEach(
                    e => e.remove()
                )


                // Insert the response HTML making it the first element
                // under <main>. The response HTML will have a parent
                // element with an "exception" class.
                main.insertAdjacentHTML(
                    'afterbegin', xhr.responseText
                )
            }
        }
        console.groupEnd()
    }

    // POST to the current URL
    xhr.open("POST", pg)
    xhr.setRequestHeader('Content-Type', 'application/json')
    xhr.send(JSON.stringify(d))
}
'''
        r += f'const TRIGGERS = {list(dom.element.Triggers)}'

        r += '''
// Once content has been loaded (DOMContentLoaded), we can add listeners
// to the controls.
document.addEventListener("DOMContentLoaded", function(ev) {
    listen(document.documentElement);

    els = document.querySelectorAll(
        'header>section>nav>ul>li a'
    )

    for(el of els)
        el.addEventListener('click', ajax)

    window.addEventListener('popstate', (e) => {
        // If there is no state to pop (perhaps because nothing has been
        // pushed yet), just force the browser back.

        console.group('popstate')

        if (e.state === null){
            console.debug('history.back()')
            history.back()
        }

        // Parse the HTML response
        var parser = new DOMParser()

        var new_ = parser.parseFromString(
            e.state, "text/html"
        )

        new_ = new_.querySelector('html>body>main')

        // Make sure event handler are hooked up again
        listen(new_);

        var old = document.querySelector('main')

        console.debug('replaceChild')
        old.parentNode.replaceChild(new_, old)

        console.groupEnd()
    });

    var main = document.querySelector('main')
    window.history.pushState(
        main.outerHTML, null, window.location.href
    )

    // We default to non-SPA.
    if (main.hasAttribute('spa-data-path')){
        inspa = true
    }else{
        inspa = false
    }
});

function listen(el){
    /* Takes an element `el` and examins it for any
     * data-{trigger}-handler attributes. Uses this information to
     * attach el to event the `ajax` event handler. Additionally, if
     * this is an SPA application, page links are sought and their
     * `click` events are subscribed to the the `ajax` handler.
    */

    console.group('listen')

    // For each of the standard triggers (click, blur, submit, etc.)
    for(var trig of TRIGGERS){
        
        // Create a CSS selector to find elements that have the
        // data-<trigger>-handler. These will be are subjects of the
        // event.
        sels = '[data-' + trig + '-handler]'

        // Search for the elements that match the selector
        var els = el.querySelectorAll(sels)

        // Convert the elements to an array
        els = [...els]

        // If el matches the selector, add it to the array
        if(el.matches(sels)){
            els.push(el)
        }

        // Subscribe the event trig to the ajax() function for each of
        // the elements found above
        for(var el1 of els){
            el1.addEventListener(trig, ajax)
        }
    }

    // Get page's <main>
    var main = document.getElementsByTagName('main')[0]

    // Get <main>'s spa-data-path attribute
    var spa_path = main.getAttribute('spa-data-path')

    // If this is a spa page
    if(spa_path){
        // Search for page links
        var sels = 'a[href^="' + spa_path + '"]'
        sels += ':not([data-click-handler])'
        var as = el.querySelectorAll(sels)

        // Subscribe
        for (var a of as){
            a.addEventListener('click', ajax)
        }
    }
    console.groupEnd()
}

function wake(els){
    /* Recursive through each element in `els` searching for <form>'s.
     * When found, makes them fully aware of the values that the user
     * has put in its form fields.
     * 
     * Wake solves sort of an odd problem. When user's enter data into
     * form fields, that data is not immediatly accessable in the HTML
     * returned by `el.outerHTML`. This function gets the data, and then
     * assigns the data to the <form>'s elements. Once complete, the
     * outerHTML will contain the values that the user has put into the
     * form fields.
    */

    // Iterate
    for (var el of els){

        // Recurse
        wake(el.children)

        // Ignore non-<form> elements
        if (el.tagName != 'FORM'){
            continue
        }

        // Get all elements of the <form> with a `name` attribute
        var els = el.querySelectorAll('[name]')

        for (var el of els){
            // Append a text node to <textarea> elements containing the
            // data in its .value property.
            var v = el.value

            if (el.tagName == 'TEXTAREA'){
                
                // Create text node before.
                // NOTE Do this first because removing the child nodes
                // affects el.value in some cases.
                var nd = document.createTextNode(v)

                // Clear the current text nodes
                while(el.firstChild){
                    el.removeChild(el.lastChild)
                }

                // Append
                el.appendChild(nd)
            }

            if (el.tagName == 'INPUT'){
                switch (el.getAttribute('type')){
                    case 'checkbox':
                        if (el.checked){
                            el.setAttribute('checked', true)
                        }else{
                            el.removeAttribute('checked')
                        }
                        break;

                    case 'text':
                        if (v){
                            el.setAttribute('value', v)
                        }else{
                            // If an empty string is assigned to the `value`
                            // attribute, remove it. Otherwise, it will be
                            // interpreted as a Boolean attribute when processed
                            // by the server and will equal `True` instead of
                            // ''.
                            el.removeAttribute('value')
                        }
                        break;
                }

            }
            // TODO Add support for other input elements like dropdown
            // lists, etc.
        }
    }
}

function exec(els){
    /* For each element in `els`, read the <article> with an
     * 'instructions' class for `instruction` elements.  An example of
     * an `instruction` is "set-url" which is the way server-side code
     * can cause the browser`s `window.location` to be set.
    */

    // For each element in the `els` sequence
    console.group('exec')
    for (el of els){
        
        // Get all <article class='instructions'>
        var instrss = el.querySelectorAll('.instructions')

        // For each instruction set
        for (var instrs of instrss){

            // Remove the <article class="instructions"> element from the
            // DOM first.
            instrs.remove()

            // Get all the instruction elements (<meta class="instruction").
            var instrs = instrs.querySelectorAll('.instruction')

            // For each instruction in the instruction set
            for (var instr of instrs){
                
                // If we have a `set` instruction
                if (instr.classList.contains('set')){
                    
                    // If we are setting the "url"
                    if (instr.getAttribute('name') == 'url'){

                        // Use pushState to change the url
                        var main = document.querySelector('main')
                        var url = instr.getAttribute('content')

                        console.debug('pushState to ' + url)

                        window.history.pushState(
                            main.outerHTML, null, url
                        )
                    }
                }else if (instr.classList.contains('remove')){
                    // Process a remove instruction
                    var id = instr.getAttribute('content')
                    el = document.getElementById(id)
                    el.remove()
                }
            }
        }
    }
    console.groupEnd()
}
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
        """ Called when a value is assigned to an attribute on this
        `menu`.

        Special handling is needed in the case of setting the `items`
        attribute. The setting of other attributes are handled here but
        are routed to code that handles them in a normal way.
        """

        if attr == 'items':
            try:
                # Test if an `items` object (a subclass of dom.ul) is
                # already in this `menu`'s collection of child
                # elements:
                itms = self.__dict__['items']
            except KeyError:
                # Not found so do nothing
                pass
            else:
                # Remove the item for the child elements collection.
                self.remove(itms)

            self.__dict__['items'] = v

            self += self.items
        else:
            # Handle the assignment normally if attr is not 'items'
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
        collections.
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

        TODO Comment on pgs
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

    @property
    def spa(self):
        """ If this `page` object is a subpage of a SPA, return its SPA
        `page`. Otherwise, return None.
        """
        pg = self.page
        while pg:
            if pg.isspa:
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
        """ Return a dict to be passed into the page's __call__ method
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

        Note that Boolean values, like the 1 for 'greet' are normalized
        into Python Boolean types. The normalization happens because the
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
        """ Used to initialize the page's <main> element and set its
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
        """ If eargs is None, this method calls into this `page`'s
        `main` method which the web developer writes. If the `eargs`
        parameter is set, this method calls into the event handler
        designated within eargs.

        Below is an example of calling the page's main method.

            class mypage(page):
                def main(self):
                    ...

            # Init page
            pg = mypage()

            # "Calling" the page ends up calling the main() method
            # defined above.
            pg() 

        :param: eargs dom.eventargs: If the call is triggered by an
        event, (e.g., the click of a button on a web page), eargs will
        be a dom.eventargs object. This object will contain a reference
        to the event handler needed to process the event as well as the
        HTML from the webpage from which the event was fired.

        :param: *args tuple: Do not use. If an attempt is made to use
        it, a ValueError will be raised encouraging the useng to use
        **kwargs (i.e., qsargs)

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

        # If we are not recursively being called...
        if not self._calling:
            # Pass query string arguments to the self._arguments
            # @property method
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
                # loads a subpage).  If `eargs is not None`, then we are
                # being called by an event handler. 
                isevent = bool(eargs)

                # XXX Comment
                if isevent:
                    if eargs.handler:
                        meth = getattr(self, eargs.handler)
                        with eargs.maintain():
                            meth(src=eargs.src, eargs=eargs)
                    else:
                        meth = self._mainfunc
                        meth(**self._arguments)

                    """
                    with eargs.maintain():
                        # XXX Should this and the above conditional be
                        # merged?
                        if eargs.handler:
                            meth(src=eargs.src, eargs=eargs)
                        else:
                            meth(**self._arguments)
                    """
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
                self.menus[i] = v
                break
        else:
            v.name = 'main'
            self.menus += v

    def makemain(self):
        if self.menu:
            raise ValueError('Main menu already exists')

        self.menu = menu.make(self.site.pages, name='main')

        return self.menu

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

        els = super().elements

        lbl = None
        if self.label:
            lbl = dom.label(self.label)
            els += lbl

        if type == 'textarea':
            inp = dom.textarea(name=self.name)

        elif type == 'select':
            inp = dom.select(name=self.name)
            for opt in options:
                inp += dom.option(opt[1], value=opt[0])
                if opt[0] in selected:
                    inp.last.selected = True
        else:
            inp = dom.input(name=self.name, type=type)

        if lbl:
            inp.identify()
            lbl.for_ = inp.id
            
        els += inp

        if self.placeholder:
            inp.placeholder = self.placeholder

        if self.help:
            els += dom.small(self.help)

    @property
    def input(self):
        """ Return the underlying dom.input/dom.textarea element for
        this `input` object.

        This may be a little confusing since this object is called
        pom.input. `pom.input` is actmualy a <div>. It will contain
        either one <input> or one <textarea> as a child object. That
        child object is returned by this property.
        """
        return self['input, textarea'].only

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

        # TODO A traceback would be better rendered as a <table> than a
        # <ul>

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

class card(dom.article):
    """ A `card` is an <article> that contains the data for an entity,
    typically an `orm.entity`. 

    Refer to the `orm.card` @property to see how a `card` is created to
    represent an ORM entity.
    """
    def __init__(self, *args, **kwargs):
        self.classes += 'card'
        super().__init__(*args, **kwargs)

class instructions(dom.article):
    """ A collection of `instruction` objects.
    """
    def __init__(self, *args, **kwargs):
        self.classes += 'instructions'

class instruction(dom.meta):
    """ Represents an instruction meant to be carried out by JavaScript
    in the browser.

    The instruction are smuggled into the browse by appending an
    `instructions` collection (a subclass of dom.article) to some HTML
    which is sent to the browser as a response to an XHR request. The
    JavaScript examins the HTML for these instruction and executes them
    on arrival.

    This class represents an abstract instruction. Subclasses of this
    class are intended to represent concrete instructions.

    See the `exec()` function in eventjs for implementation details.
    Also see the `element_event` method in tester.py for the "tester"
    version of this function.
    """
    def __init__(self, *args, **kwargs):
        """ Create an instruction object.
        """
        self.classes += 'instruction'

class set(instruction):
    """ Represents an instruction to set an arbitrary object's value in
    the browser tab.

    Currently, the only thing this `instruction` can set is the URL in
    the browser's location bar.  See the `exec()` function in eventjs
    for details.
    """
    def __init__(self, lhs, rhs, *args, **kwargs):
        """ Create a `set` instruction.

        :param: lhs str: The left-hand side of the assignment, i.e, the
        name of the object being assigned the value.

        :param: lhs str: The right-hand side of the assignment, i.e, the
        value being assigned.
        """
        self.lhs = lhs
        self.rhs = rhs

        self.name = lhs
        self.content = rhs

        self.classes += 'set'

        super().__init__(*args, **kwargs)

class remove(instruction):
    """ A remove instruction to be sent to the browser.

    Remove instruction instruct the JavaScript to remove the element
    defined by self.element.
    """
    def __init__(self, el, *args, **kwargs):
        """ Create a `remove` instruction.

        :param: el dom.element: The element to be removed.
        """
        self.element = el

        # Add `remove' to the `class` attribute.
        self.classes += 'remove'

        # Set the `content` attribute to the element`s id
        self.content = el.id

        super().__init__(*args, **kwargs)

class crud(page):
    """ A class to implement the display logic to create, retrieve,
    update and delete a given `orm.entity` or `orm.entities` object.
    """
    def __init__(self, 
        e, name=None, pgs=None, presentation='table', *args, **kwargs
    ):
        """ Create a `crud` page object. 

        :param: e orm.entitymeta|orm.entitiemeta: A class reference an
        instance of which will be used by this page to perform CRUD
        operations on.

        :param: name str: The name of the page.

        :param: presentation str: The presentation of the mode of the
        page, e.g., 'table' and 'cards'. Used when the `instance` is an
        entities collection. It determines what HTML semantics will be
        used to render the collection; <table> or <article> ('cards').
        """

        if presentation not in ('table', 'cards'):
            raise ValueError('Invalid presentation mode')

        self._entity        =  e
        self.presentation   =  presentation
        self._instance      =  None
        self._detail        =  None
        self._form          =  None
        self._oncomplete    =  None
        self._select        =  None
        self._onbeforesave  =  None

        super().__init__(name=name, pgs=None, *args, **kwargs)

    def clear(self):
        """ Overrides `page.clear` to set the `instance` to None so it
        is reloaded when necessary.
        """
        self._instance = None
        super().clear()

    @property
    def onbeforesave(self):
        """ An event that is triggered before this pom.crud page saves
        the instance.
        """
        if not self._onbeforesave:
            self._onbeforesave = entities.event()

        return self._onbeforesave

    @onbeforesave.setter
    def onbeforesave(self, v):
        self._onbeforesave = v

    @property
    def select(self):
        """ Returns a string of whitespace delemited fields to be added
        to this `pom.crud` page's table or card.

        By default, a None value is returned which means "select all".
        Subclasses of `pom.crud` can return their own select string, or
        they can set the property in their constructor or some other
        place.

        Select strings are similar to the list of columns in an SQL
        SELECT caluse except that commas are optional:

            'id, name, createdat'

        This will cause the table or card to contain only the `id`,
        `name` and `createdat` values from the pom.crud page's
        `instance` entity.
        
        Dot notation can be used to access composites of the entity. For
        example, if the table is showing a sales orders collection, we
        can access the customer composite of each sales order using a
        string like this:

            'number created_at customer.firstname customer.lastname'

        This will cause a table to be rendered containing the order'
        numbers, the created_at date of the order, and the name of the
        customer who placed the order. The dot notation can be of an
        infinite depth.
        """
        return self._select

    @property
    def detail(self):
        """ Returns a class reference to the pom.page that contains the
        details for an entity (which is usually contained in a table
        row) presented on this pom.crud page..
        """
        return self._detail

    @detail.setter
    def detail(self, v):
        """ Sets the detail class reference for this pom.crud page.
        """
        self._detail = v

    @property
    def oncomplete(self):
        """ Returns the path of the page that the user should be
        redirected to.
        """
        if not self._oncomplete:
            return self.path

        return self._oncomplete

    @oncomplete.setter
    def oncomplete(self, v):
        """ Sets the oncomplete property.
        """
        self._oncomplete = v

    @property
    def instance(self):
        """ Return the instance of `self.entity`, i.e., the `orm.entity`
        that this `crud` page uses to perform CRUD operations on.
        """
        return self._instance

    @instance.setter
    def instance(self, v):
        """ Set the `orm.entity` object reference for this `crud` page.
        """
        self._instance = v
        
    @property
    def entity(self):
        """ Returns the class reference to the `orm.entity` class that
        this `crud` page operates on.
        """
        # Import the module that the `orm.entity` was defined in. This
        # way, whenever a caller needs to access the class, its module
        # will have been imported and the class will be ready for
        # instantiation.
        import importlib
        importlib.import_module(self._entity.__module__)

        return self._entity

    @entity.setter
    def entity(self, v):
        """ Set the class reference to the `orm.entity` that this `crud`
        page will operate on.
        """
        self._entity = v

    def _formalize(self, tr, frm):
        """ Add a new <td> with a <form> in it to a <tr>.

        This is a private method that captures a routine task. It is
        used to replace the contents of the current `tr` with a new `td`
        that has a <form> in it. The form allows the user to edit the
        values that were in the (by definition: read-only) <tr>. This
        logic is used when the user clicks Quick Edit and when the user
        does a traditional GET on the URL that the Quick Edit links
        navigates to.
        """
        # Remove the <td>'s that are in the <tr>
        tds = tr.remove('td')

        # Create a colspan so the new form will span the length of
        # the <tr>
        colspan = max(tds.count - 1, 1)

        # Create new <td>
        td = dom.td(colspan=colspan)

        # Add <form> to <td>
        td += frm

        # Add <td> to <tr>
        tr += td

    def btnedit_onclick(self, src, eargs):
        """ An event handler to capture the `click` event triggered by
        the `card`'s edit button.

        When the user clicks the edit <button>, they will want their
        browsers to convert the `card` into a `form` so they can edit
        the entity's values. This handler gives them that form.
        """
        # Get the card or <tr> represeting the entity.
        el = eargs.html.only

        # Get the entity's id
        id = el.getattr('data-entity-id')

        # Instantiate the orm.entity and store a reference to the
        # instance. Use `orm.entity` to ensure we get the *singural*
        # entity class which we will construct with the id.
        e = self.entity.orm.entity(id)
        self.instance = e

        # Get the <form> representation of the entity
        frm = e.orm.form

        # If the browser sent us a <tr> add a new <td> to the <tr>. The
        # <td> will contain the new <form>. This is the "Quick Edit"
        # <form>.
        if isinstance(el, dom.tr):
            # Assign to tr for clarity
            tr = el

            # Replace contents of tr with frm
            self._formalize(tr, frm)

            # Make the <tr> the target of event subscriptions below
            target = tr

        # If the browser sent us a card
        elif isinstance(el, dom.article):
            if 'card' not in el.classes:
                raise TypeError('Article is not a card')

            # Return the new form
            eargs.html = frm

            # Make the new <form> the target of the following event
            # subscriptions
            target = frm

        else:
            raise TypeError('Invalid element')

        # Subscribe the form's <button type="submit> to self.frm_onsubmit
        frm.onsubmit += self.frm_onsubmit, target

        # Create a Cancel button
        btncancel = dom.button('Cancel')

        # Subscribe the button to btncancel_onclick which will discard
        # the `form` and return a `card`.
        btncancel.onclick += self.btncancel_onclick, target

        # Add button to `form`
        frm += btncancel

        ''' Add crud=edit to url '''

        # Get the url that the request was made to
        url = www.application.current.request.url

        # Set the id and crud parameters in the query string to
        # appropriate values
        url.qs['id'] = e.id.hex
        url.qs['crud'] = 'update'

        instrs = instructions()
        # Create a `set` instruction for the JavaScript in the browser
        # to carry out. This instructs the browse to replace the URL in
        # the URL bar with `url`.
        instrs += set('url', str(url))

        # Add the instructions collection to the <form> element.
        frm += instrs

    def btncancel_onclick(self, src, eargs):
        """ An event handler to be invoked when the user clicks the
        Cancel button.
        """
        # Get the <form> that was canceled.
        el = eargs.html.only

        # Get the requested url
        req = www.application.current.request
        url = req.url

        # Process completion. Return early if completion is processed.
        if self.complete(el, eargs):
            return

        # Get the entity's hex id from the form 
        # (<input hidden name="id" value="A1B2C3...")
        id = el['input[name=id]'].only.value

        # Load the orm.entity given the id from the <form>
        e = self.entity.orm.entity(id)

        # If the browser sent us a <tr>
        if isinstance(el, dom.tr):
            # Get the <tr> form the newly instantiated entity
            tr = e.orm.tr

            # Return the new <tr> to the browser
            eargs.html = tr

            # Get the <td> for the entity's id. We will add the <menu>
            # to that <td>
            td = tr['td[data-entity-attribute=id]'].only

            # Add the <menu> to the <td>
            menu = self._menu(td)

            # Get the "Quick Edit" anchor (<a rel="edit preview">)
            a = menu['a[rel~=edit][rel~=preview]'].only
            a.onclick += self.btnedit_onclick, td.closest('tr')

            td += menu

            # Update url by removing the id and crud parameters from the
            # query string. We are basically returning the crud page to
            # its plain, tabular view.

            for k in ('id', 'crud'):
                with suppress(KeyError):
                    del url.qs[k]

            # Instruct the browser to set the URL bar to `url`
            instrs = instructions()
            instrs += set('url', str(url))

            # NOTE We need to put the instr in a <td> otherwise the
            # <template>-based parser will see the instructions article
            # as a distinct child element as if it were not within the
            # <tr>.
            td = dom.td()
            td += instrs

            # Add `instructions` to `card`
            tr += td

        elif isinstance(el, dom.form):
            # Create a card article to return to the browser
            card = e.orm.card

            # Return card article to browser
            eargs.html = card

            # Subscribe the card's Edit button's onclick event to
            # self.btnedit
            card.btnedit.onclick += self.btnedit_onclick, card

            ''' Add crud=retrieve to url '''

            # Change its query string params setting `id` and `crud`
            url.qs['id'] = e.id.hex
            url.qs['crud'] = 'retrieve'

            # Instruct the browser to set the URL bar to `url`
            instrs = instructions()
            instrs += set('url', str(url))

            # Add `instructions` to `card`
            card += instrs

    def frm_onsubmit(self, src, eargs):
        """ An event handler to capture the submission of the <form> for
        this `crud` page.
        """
        # Get the <form> that was submitted
        el = eargs.html.only

        tr = None

        # If browser sent a <tr>
        if isinstance(el, dom.tr):
            tr = el

            # The <form> that is being submitted will be in the <tr>
            # that the browser sent. Obtain that so we can persist its
            # values
            frm = tr['form'].only

        # If browser sent a <form>
        elif isinstance(el, dom.form):
            # Get the form so we can persist its values
            frm = el

        # Get the input values
        inps = frm['input, textarea']

        # Use the id input (<input name=id>) to get the entity's id. Use
        # that id to try to load the entity.
        e = None

        # Get the id from the data-entity-id attribute of the <input>
        id = frm.getattr('data-entity-id')

        if id:
            try:
                # Load the entity
                e = self.entity.orm.entity(id)
            except db.RecordNotFoundError:
                pass

        # If `entity` with `id` was not found above, create a new one
        if not e:
            e = self.entity.orm.entity()

        # Assign values from the <form>'s <input>s to the entity's
        # attributes
        for inp in inps:
            if isinstance(inp, dom.textarea):
                v = inp.text

            elif isinstance(inp, dom.input):
                v = inp.value

            if v == '':
                v = None

            if inp.name == 'id':
                v = UUID(v)

            if hasattr(e, inp.name):
                setattr(e, inp.name, v)

        eargs1 = crud.operationeventargs(e=e, html=eargs.html)
        self.onbeforesave(self, eargs1)

        # Save entity to database. If an event handler set the
        # eargs1.stead attribute, save that object, otherwise just save
        # `e`.
        (eargs1.stead or e).save()

        # TODO Trigger onaftersave

        # Get the requested url
        req = www.application.current.request
        url = req.url

        # Process completion. Return early if completion is processed.
        if self.complete(el, eargs):
            return

        # If the browser sent a <tr>
        if tr:
            # Get the <tr> representation of the entity
            tr = e.orm.tr

            # Set the <tr> back to the browser
            eargs.html.first = tr

            td = tr['td[data-entity-attribute=id]'].only

            # Add a menu to the <tr>
            menu = self._menu(td)

            # Subscribe events to the menu's items
            a = menu['a[rel~=edit][rel~=preview]'].only
            a.onclick += self.btnedit_onclick, td.closest('tr')

            td += menu

            # Update url by removing the id and crud parameters from the
            # query string. We are basically returning the crud page to
            # its plain, tabular view.

            for k in ('id', 'crud'):
                with suppress(KeyError):
                    url.qs[k]

            # Instruct the browser to set the URL bar to `url`
            instrs = instructions()
            instrs += set('url', str(url))

            # NOTE We need to put the instr in a <td> otherwise the
            # <template>-based parser will see the instructions article
            # as a distinct child element as if it were not within the
            # <tr>.
            td = dom.td()
            td += instrs

            # Add `instructions` to `card`
            tr += td
        else:
            # Create a `card` to return to the browser
            card = e.orm.card

            # Return card to browser
            eargs.html.first = card

            # Create Edit button
            btnedit = dom.button('Edit', class_='edit')
            card += btnedit

            # NOTE It's unclear at the moment whether a card should have
            # an Edit anchor or an Edit <button>.

            # Subscribe the onclick event of the card's edit button to
            # self.btnedit_onclick
            btnedit.onclick += self.btnedit_onclick, card

            # Update the id and crud parameters in the browser to the
            # appropriate values.  
            if 'id' not in url.qs or url.qs['id'] != e.id.hex:
                url.qs['id'] = e.id.hex
                url.qs['crud'] = 'retrieve'

                instrs = instructions()
                # Instruct the browser to update the URL bar to `url`.
                instrs += set('url', str(url))

                card += instrs

    def complete(self, el, eargs):
        """ Processes the oncomplete query string parameter. Returns
        True if the parameters was found and processed, False otherwise.

        The `oncomplete` query string parameters is an optional
        parameter that contains the path to a page. This method loads
        that page and returns it to the browser. The intent is to return
        the user to a page when they trigger a completion event such as
        clicking a form's submit or cancel button.

        :param: el dom.element: Typicaly a dom.form which has a hidden
        element within it which contains the path to the page that the
        application wants to return to after the form has been submitted
        or canceled.
        """
        # Search for elements with the data-complete atttribute
        oncompletes = el['[data-oncomplete]']

        # There should be zero or one
        if oncompletes.issingular:

            # Read path
            path = oncompletes.only.text

            # Get the base, i.e., the object with the `pages` collection
            # where we can find the oncomplete page.
            base = self.spa or self.site

            # For each page in the spa or site 
            for pg in base.pages:
                
                # If we found a matching page
                if pg.path == path:

                    # Clear page
                    pg.clear()

                    # Run the page
                    pg()

                    # Get requested url
                    req = www.application.current.request
                    url = req.url

                    # Remove the url's query string parameters
                    for k in ('id', 'crud', 'oncomplete'):
                        with suppress(KeyError):
                            del url.qs[k]

                    # Set the URL object path property to the oncomplete
                    # page's path and instruct the browser to set the
                    # URL bar to this path.
                    url.path = req.language + pg.path

                    # Set data-url. This will be used by the JavaScript
                    # to set the URL in the browser's location bar when
                    # it performs a history.pushState
                    pg.main.setattr('data-url', url)

                    # Set data-spa-path
                    if self.spa:
                        path = self.spa.path
                        path = f'/{req.language}{path}'
                        pg.main.setattr('spa-data-path', path)

                    eargs.html = pg.main

                    # Return True because we successfully processed the
                    # completion
                    return True
            else:
                raise www.NotFoundError('Oncomplete not found')

        # No completion was found so return False
        return False

    @property
    def iscollection(self):
        """ Returns True if this pom.crud page is based on an entities
        collect.
        """
        return isinstance(self.entity, orm.entitiesmeta)

    @property
    def isitem(self):
        """ Returns True if this pom.crud page is based on an entity
        object.
        """
        return isinstance(self.entity, orm.entitymeta)

    @property
    def entity(self):
        """ The entity class or entities collection class that this
        pom.crud page is based on.
        """
        return self._entity

    @entity.setter
    def entity(self, v):
        self._entity = v

    @property
    def instance(self):
        """ Returns an instantiation of the entity that this pom.crud
        page is based on.
        """
        if not self._instance:
            if self.iscollection:
                # TODO Enable filtering of the stream
                self._instance = self.entity.orm.all

            elif self.isitem:
                if id := self.getattr('data-entity-id'):
                    self._instance = self.entity(id)
                else:
                    self._instance = self.entity()

        return self._instance

    @instance.setter
    def instance(self, v):
        self._instance = v

    def gethtml(self, id, crud, oncomplete):
        """ Create and return a DOM object (dom.element) for the page.

        This method is typically called by the `main()` method and some
        event handlers to obtain the page's HTML.

        :param: id str: The UUID, in hex format, for the entity that
        this `crud` page represents. Will be None if the page represents
        a collection of entities.

        :param: crud str: The crud operation that the HTML needs to
        support. 
            
            if crud == 'create':
                We will return an empty <form>.

            if crud == 'retrieve'
                A <table>, cards <div> or card <article> will be
                returned with the contents of the entity/entities.

            if crud == 'update':
                A <form> will be returned to edit the given entity.

        :param: oncomplete str: The path to the page to return to when
        processing has completed.
        """
        frm = False

        if id:
            self.setattr('data-entity-id', id)

        self.oncomplete = oncomplete

        # Get the presentation mode for display: 'table' or 'cards'
        pres = self.presentation

        # If the entity we are working with is a collection, load the
        # collection then return it as a <table> or a collection of
        # cards (<article class="card">)
        if self.iscollection:
            es = self.instance

            # Get the collections 'orm.table' or 'orm.cards'
            f = getattr(es, 'orm.get' + pres)
            el = f(select=self.select)

            # Get the <div>s or <td>s that correspond to entity
            # attributes within the element
            els = el['[data-entity-attribute=id]']

            if pres == 'table':
                # For each <td> in the <table>, create a coresponding
                # <menu> to contain the "Edit", "Quick Edit", etc.
                # links. Add the <menu> to the <td>
                for td in el['td:first-child']:
                    menu = self._menu(td)

                    # Get the "Quick Edit" anchor (<a rel="edit preview">)
                    a = menu['a[rel~=edit][rel~=preview]'].only
                    a.onclick += self.btnedit_onclick, td.closest('tr')

                    td += menu

            # If a browser is doing a tradtional (non-XHR) GET on the
            # the page, and the query string parameter crud is 'update',
            # use the id from the query string to add a <form> to the
            # table. This will produce a Quick Edit <form> within the
            # page.  This is equivelent to clicking the Quick Edit
            # button but does not involve XHR requests.
            if crud == 'update':
                # If an id was passed in the query strting
                if id:
                    id = UUID(hex=id)

                    for tr in el['tbody>tr']:
                        # Get the entity's id
                        attrid = tr.getattr('data-entity-id')

                        if not attrid:
                            continue

                        attrid = UUID(hex=attrid)

                        # Does the attrid match the id passed in the
                        # query string
                        if attrid == id:
                            # Get the entity's <form> representation
                            frm = es[id].orm.form

                            # Replace contents of tr with frm
                            self._formalize(tr, frm)

                            # Make the <tr> the target of event
                            # subscriptions below
                            target = tr

                            # Subscribe the form's <button type="submit>
                            # to self.frm_onsubmit
                            frm.onsubmit += self.frm_onsubmit, target

                            # Create a Cancel button
                            btncancel = dom.button('Cancel')

                            # Subscribe the button to btncancel_onclick
                            # which will discard the `form` and return a
                            # `card`.
                            btncancel.onclick += self.btncancel_onclick, target

                            # Add button to `form`
                            frm += btncancel

                            break

            # Empty state
            if els.isempty:
                el += dom.p('No items found.', class_="empty-state")

            if det := self.detail:
                # Create a path string to the details page
                path = f'{det.path}?&crud=create'
                path += f'&oncomplete={self.oncomplete}'

                # Create the "Add New" link
                el += dom.a('Add New', href=path, rel='create-form')

                # Add an Edit button to each card in the collection
                cards = el['article.card']
                for card in cards:
                    # Get the entity id in the card
                    id = card.getattr('data-entity-id')

                    # Build path
                    path = f'{det.path}?id={id}&crud=update'
                    path += f'&oncomplete={self.oncomplete}'

                    # Create Edit link
                    card += dom.a('Edit', href=path, rel='edit')

        # If the entity we are working with is an individual entity (as
        # opposed to a collectio), get the instance then return a
        # <form> or card (<article>) with the entity's contents
        # depending on `crud`.
        elif self.isitem:
            e = self.instance

            if id:
                if crud == 'create':
                    raise ValueError(
                        'Cannot create when given an id'
                    )

                elif crud == 'retrieve':
                    frm = False

                elif crud == 'update':
                    # If CRUD is 'update' and we have an id, we want to
                    # send back a form so users can update an entity
                    # object.
                    frm = True
            else:
                if crud == 'create':
                    # If CRUD is 'create' and we have no id, we want to
                    # send back a blank <form> so the user can create an
                    # entity object.
                    frm = True

                elif crud == 'retrieve':
                    raise ValueError(
                        'Cannot retrieve without id'
                    )
                    
                elif crud == 'update':
                    raise ValueError(
                        'Cannot create when given an id'
                    )

            if frm:
                # If frm is True, add a <form> for the entity to the
                # page's <main>
                el = e.orm.getform(select=self.select)

                # Capture form submission
                el.onsubmit += self.frm_onsubmit, el

                # Capture cacelation
                btncancel = dom.button('Cancel')
                btncancel.onclick += self.btncancel_onclick, el
                el += btncancel

                # If oncomplete path was passed in as a query parameter
                if oncomplete:
                    # Put the path in a hidden <span>
                    span = dom.span(oncomplete, hidden=True)
                    span.setattr('data-oncomplete', oncomplete)
                    el += span
            else:
                # If frm is None, add a card to the page so user is able
                # to read entity values.
                el = e.orm.card
                card = el

                # NOTE It's unclear at the moment whether a card should
                # have an Edit <a>nchor or an Edit <button>.

                # Create Edit button
                btnedit = dom.button('Edit', class_='edit')
                card += btnedit

                # Subscribe the Edit button to self.btnedit_onclick.
                # This allows user to get a <form> version of the card
                # so the entity can be updated.
                btnedit.onclick += self.btnedit_onclick, card

        # If there is an oncomplete page to return to
        if oncomplete:
            # Find the page
            pg = self.site.pages[oncomplete]

            # Add a "Back" button to that page
            a = dom.a('Back', href=pg.path)
            self.main += a

        # Return whichever element we created (<form>, <article>, <table>)
        # to <main>.
        return el

    def main(self, id:str=None, crud:str='retrieve', oncomplete=None):
        """ The main handler for this `crud` page.
        """
        el = self.gethtml(id=id, crud=crud, oncomplete=oncomplete)
        self.main += el

    def _menu(self, td):
        """ Create a new <menu> object that acts as a context menu for
        the <tr> of the given <td>.

        A table row <tr> for an entity can have several items such as
        "Edit', 'Quick Edit', 'Preview', 'Delete', etc. This <menu>
        provides those function for the entity represented by the td's
        parent <tr>.

        :param: td dom.td: The <td> object the menu will created for.
        """
        # TODO This can be enhanced by appending td to the menu it
        # creates. The calling code does this itself.

        # Create the menu to return
        menu = dom.menu()

        # Get entity's UUID
        id = td.parent.getattr('data-entity-id')

        # If there is a detail page...
        if det := self.detail:

            # Create an "Edit" link
            li = dom.li()

            # Create a path string to the details page
            path = f'{det.path}?id={id}&crud=update'
            path += f'&oncomplete={self.path}'

            # Create the "Edit" link
            a = dom.a('Edit', href=path, rel='edit')
            li += a
            menu += li

        # Create the Quick Edit link
        li = dom.li()
        path = f'{self.path}?id={id}&crud=update'
        a = dom.a('Quick Edit', href=path, rel='edit preview')

        li += a
        menu += li

        return menu

    class operationeventargs(entities.eventargs):
        """ An eventargs class that is used by this pom.crud class to
        pass arguments for persistence operations.
        """

        def __init__(self, e, html):
            """ Create a new `operationeventargs` object.
            """
            # The entity being saved
            self.entity = e

            # The HTML of the event that caused the operation
            self.html = html

            # The `stead` property can be used by the event handler to
            # specify an object that should be saved instead of `e`.
            self.stead = None

class dialog(dom.dialog):
    """ Inherits from dom.dialog to provide a richer set of features.
    """
    def __init__(self, 
        owner, msg, caption=None, onyes=None, onno=None, *args, **kwargs
    ):
        """ Create a pom.dialog element.

        :param: owner dom.element: The dom.element that owns the dialog
        modal.

        :param: msg str: The message to display to the user.

        :param: caption str: The message to display in the modal's
        header.

        :param: onyes tuple: When not None, instructs the dialog to
        display a "Yes" button. The first element of the tuple will be
        the server-side event handler that should be called when the
        button is clicked. The remaining elements of the tuple will be
        the elements that should be sent from the browser to the server.

        :param: onno tuple: When not None, instructs the dialog to
        display a "No" button. The first element of the tuple will be
        the server-side event handler that should be called when the
        button is clicked. The remaining elements of the tuple will be
        the elements that should be sent from the browser to the server.
        """
        self.owner    =  owner
        self.message  =  msg
        self.caption  =  caption

        # Make sure the <dialog> has the `open` attribute present.
        self.open     =  True

        # Add caption
        if caption:
            self += dom.header(caption)

        # Create <form> to be put in <dialog>
        frm = dom.form()

        # Add message
        frm += dom.p(msg)

        # Add Yes button
        if onyes:
            btn = dom.button('Yes')
            btn.setattr('data-yes', True)
            btn.onclick += onyes
            frm += btn

        # Add Yes button
        if onno:
            btn = dom.button('No')
            btn.setattr('data-no', True)
            btn.onclick += onno
            frm += btn

        self += frm
        super().__init__(*args, **kwargs)
