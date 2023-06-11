# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2022

"The only way to go fast is to go well"
# Robert C. Martin

from config import config
from contextlib import contextmanager, suppress
from dbg import B, PM, PR
from entities import classproperty
from pprint import pprint
from textwrap import dedent
from types import FunctionType
import builtins
import db
import dbg
import dom
import ecommerce
import entities
import file
import gc
import inspect
import io
import json
import logs
import os
import party
import pdb
import pom
import primative
import re
import resource
import sys
import textwrap
import time
import timeit
import uuid
import www

""" This module provides integration testing and benchmarking for the
core framework, web pages, and any other code in the core repository.

TODOs:
    TODO Ensure tester.py won't run in non-dev environment
    
    TODO When creating the file API, consider
    wsgiref.util.FileWrapper(filelike, blksize)

    TODO Add option to randomize tests. Test should be executed in a
    random order by default. This had previously been the case prior to
    Python 3.6 and we were able to catch certain types of bugs due to
    this.

    TODO Remove all the assert* methods. Replace their invocations with
    the terser names, i.e., s/assertEquals/eq/.

    TODO If the class or method given to test can't be found, print an
    error message and exit with an exit code greater than 0.
"""

class invoketesteventargs(entities.eventargs):
    def __init__(self, cls, meth):
        self.class_ = cls
        self.method = meth

class testers(entities.entities):
    def __init__(self, initial=None):
        self.onbeforeinvoketest = entities.event()

        super().__init__(initial=initial)
        self.breakonexception = False

        # If True, only run performance tests
        self.performance = False

        # The tester class to run. If not set, all tester classes will
        # be run
        self.class_ = None

        # The method/test to run. If not set, all tests in self.class_
        # will be run if set.
        self.method = None

        # Profile self.method
        self.profile = False

    def run(self):
        """ Run the tester class
        """

        # Don't run in production
        if config().inproduction:
            raise Exception("Won't run in production environment.")

        logs.info('Getting tester subclasses ...')
        clss = self.subclasses

        # For each of the tester subclasses
        logs.info('Iterating over subclasses ...')
        for cls in clss:
            # If class was given, but cls isn't that class, skip
            if self.class_ and cls.__name__ != self.class_:
                continue

            # Is cls a benchmark test
            if isbenchmark := benchmark in cls.__mro__:
                if self.performance:
                    # If cls is benchmark and self.performance is True, then
                    # run test
                    pass
                else:
                    if self.class_:
                        # If cls is benchmark and we have a specific
                        # test to run, run test
                        pass
                    else:
                        # If cls is benchmark but we don't want to run
                        # performance tests, skip cls
                        continue
            else:
                if self.performance:
                    # If we are running performance only
                    # (self.performance), and the class is not a
                    # benchmark, then skip.
                    continue

            try:
                # Instantiate the current tester class
                inst = cls(self)
            except TypeError as ex:
                raise TypeError(
                    'Be sure pass *args and **kwargs to '
                    f'super().__init__ from '
                    f'{cls.__name__}.__init__: {ex}'
                )

            # TODO Capture exceptions here and collected any tester
            # class that failed construction. An exception in a tests
            # summary should be display at the end of the tests run just
            # where we would expected to find assertion errors and
            # exceptions that occured in the test. Currently, the tests
            # just stall since there is no generic `except Exception`
            # block to deal with this; they just bubble up, uncaught,
            # and terminate the process.

            # Set the tester classes `testers` method to self so it
            # knows what its collection is
            inst.testers = self

            # Add the tester class to this testers object
            self += inst

            # Iterate over each method in the tester class
            for meth in cls.__dict__.items():
                # Skip items that are not methods
                if type(meth[1]) is not FunctionType:
                    continue

                # Skip methods that begin with a _
                if meth[0][0] == '_':
                    continue

                # If self.method was set, filter based on that
                if self.method and self.method != meth[0]:
                    continue

                try:
                    # Raise event
                    eargs = invoketesteventargs(cls, meth)
                    self.onbeforeinvoketest(self, eargs)

                    # Get the thes method (note that we will invoke it
                    # later)
                    f = getattr(inst, meth[0])

                    if self.profile:
                        # Run test under profiler
                        dbg.profile(f)
                    else:
                        # Just run test
                        f()

                except Exception as ex:
                    # breakonexception will usually be True because the
                    # -b flag was given
                    if self.breakonexception:
                        # Print exception and put the user in the
                        # debugger at the point where the exception
                        # occured.
                        print(ex)
                        pdb.post_mortem(ex.__traceback__)

                    # For benchmark tests, just raise exception.
                    # Otherwise, record the exception as a failure the
                    # same way failed assertions are recorded.
                    if isbenchmark:
                        raise
                    else:
                        inst._failures += failure(ex, assert_=meth[0])

        logs.info('Test complete')

    @property
    def subclasses(self):
        """ Return a list of all subclasses of tester.
        """

        # Create a recursive function so we can go n-levels deep in the
        # inheritance tree
        def getsubclasses(cls, ls):
            for cls in cls.__subclasses__():
                if cls not in (benchmark, ):
                    ls.append(cls)
                getsubclasses(cls, ls)

        # Create a list to capture the subclasses
        r = list()

        # Call recursive function
        getsubclasses(tester, r)

        # Return list
        return r

    @property
    def isok(self):
        return all(x.isok for x in self)

    def __str__(self):
        return self._tostr(str, includeHeader=False)

class principle(entities.entity):
    """ A singleton to manage the creation of test principles such as
    test users, test companies, etc.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        """ Create the singleton.
        """
        if not cls._instance:
            cls._instance = super(principle, cls).__new__(
                cls, *args, **kwargs
            )

        return cls._instance

    def __init__(self, *args, **kwargs):
        """ Create the singleton along with the principles. 
        """
        # Since we are a singleton, we only want to run __init__ once,
        # so return if the isinitialized attribute is set.
        if hasattr(self, 'isinitialized'):
            return
        
        super().__init__(*args, **kwargs)

        # Create principles
        self.create()

        self.isinitialized = True

    def create(self, recreate=False):
        """ Create the principles, i.e., the test user, company and
        proprietor.

        :param: recreate bool: If True, recerate the test user, test
        company and the standard Carapacian company
        (ecommerce.companies.carapacian).
        """
        logs.info('Creating principles ...')

        iscreated = hasattr(self, 'iscreated')

        # Make sure the needed table exist
        import ecommerce
        ecommerce.user.orm.create(ignore=True)

        # Make sure party.party and all subentities have existing tables
        import party
        clss = party.party.orm.getsubentities(accompany=True)

        for cls in clss:
            cls.orm.create(ignore=True)

        if hasattr(self, 'isinitialized'):
            if recreate and iscreated:
                # del user and company to force a recreation
                del self._user
                del self._company

        # Retrieve the user and company - creating them if necessary
        usr = self.user
        com = self.company

        # Create the proprietor. Make the company created above its
        # proprietor
        import orm
        with orm.sudo():
            with orm.proprietor(com):
                com.save()
                usr.proprietor = com
                usr.save()

        if recreate:
            import party
            # Carapacian will recreate itself when called as long as its
            # private field is None
            party.companies._carapacian = None

        self.iscreated = True

    def recreate(self):
        """ Rereate the principles, i.e., the test user, company and
        carapacian company (ecommerce.companies.carapacian).
        """
        self.create(recreate=True)

    @property
    def user(self):
        """ Return a test user object. Ensure its in the database if it
        is not already.
        """
        Id = uuid.UUID(hex='574d42d099374fa7a008b885a9a77a9a')
        if not hasattr(self, '_user'):
            import orm, db
            with orm.sudo():
                try:
                    self._user = ecommerce.user(Id)
                except db.RecordNotFoundError:
                    self._user = ecommerce.user(id=Id, name='stduser0')

        return self._user

    @property
    def company(self):
        """ Return a test company object. Ensure its in the database if
        it is not already.
        """
        Id = uuid.UUID(hex='574d42d0625e4b2ba79e28d981616545')
        if not hasattr(self, '_company'):
            import party, orm, db

            with orm.sudo():
                try:
                    self._company = party.company(Id)
                except db.RecordNotFoundError:
                    self._company = party.company(
                        id=Id, name='Standard Company 0'
                    )

        return self._company

class tester(entities.entity):
    def __init__(self, testers, mods=None, user=None, propr=None):
        """ Create the tester abstract object.

        :param: testers testers: A reference to the testers collection
        that this instance will be a part of.

        :param: mods tuple<str>: A tuple of strings containing module
        names. Each module will be scanned for entity classes and those
        entity classes will have their tables rebuilt.
        """
        import orm
        self._failures = failures()
        self.assessments = assessments(self)
        self.testers = testers

        # Rebuild tables in `mods`
        if mods and self.rebuildtables:
            logs.info(f'Rebuilding tables for {mods}')
            
            for mod in mods:
                mod = __import__(mod,  globals(), locals())
                logs.info(f'Rebuilding for module: {mod}')

                for _, cls in inspect.getmembers(mod):
                    try:
                        mro = cls.__mro__
                    except AttributeError:
                        # Many member of a module (basically anything
                        # that's not a class) will not have a __mro__.
                        continue
                    else:
                        if orm.entity in mro:
                            cls.orm.recreate(descend=True)

                        if cls is ecommerce.user:
                            try:
                                # If we have rebuilt the users table, we
                                # will want to invalidate reference to
                                # user objects
                                del ecommerce.users._root
                            except AttributeError:
                                # ecommerce.users._root is
                                # monkey-patched on memoization, so it
                                # want necessarily be there (see
                                # ecommerce.users.root)
                                pass

            # If we are deleting all the tables it the file module,
            # invalidate the radix cache since it will be a store of the
            # data in those tables.
            if 'file' in mods:
                # Clear radix cache
                with suppress(AttributeError):
                    del file.directory._radix

            if 'party' in mods:
                with suppress(AttributeError):
                    del party.parties._public

        # Create and set principles at ORM level for testing
        sec = orm.security()
        sec.user       = user  if user  else self.user
        sec.proprietor = propr if propr else self.company

        # If propr was passed in
        if propr:
            # Ensure that propr is properly persisted
            with orm.override(), orm.sudo():
                try:
                    # Try reloading...
                    propr.orm.reloaded()
                except db.RecordNotFoundError:
                    # Save propr if it doesn't exist in database
                    propr.save()
                else:
                    # If it already exists in database, ensure that the
                    # persistencestate reflects this.
                    sup = propr
                    while sup:
                        sup.orm.persistencestate = False, False, False
                        sup = sup.orm._super
            
    def recreateprinciples(self):
        principle().recreate()

    @property
    def user(self):
        return principle().user

    @property
    def company(self):
        return principle().company

    @property
    def rebuildtables(self):
        try:
            testers = self.testers
        except AttributeError as ex:
            raise AttributeError(
                'The testers attribute is not available. '
                "Make sure that you are calling super()'s constructor "
                "in the subclass's constructor before doing "
                'anything else.'
            ) from ex
        else:
            return self.testers.rebuildtables

    class _browsers(www.browsers):
        pass

    class _browser(www.browser):
        # TODO This appears to be a duplicate and should be removed
        def __init__(self, t, *args, **kwargs):
            self.tester = t

        ''' Inner classes '''
        class messages(entities.entities):
            """ A class to collect browser `messages`
            """

        class message(entities.entity):
            """ Represents a browser message.

            A browser message is a request/response pairing. Each time
            the browser tab navigates to a URL, or an XHR request is
            made in the browser tab, a request is made. This request
            makes up the request portion of a message. If the webserver
            responds with something (which, of course, will usually be
            the case), that response will become the response portion of
            the message. 

            `messages` are basically the entries in the table when you
            go to a real browser's "Network" tab in dev tools.

            These `tester` `tab` objects should always be recording
            requests/respeone's as `message` object collected in the
            `tab`'s `messages` collection.
            """
            def __init__(self, req=None, res=None, *args, **kwargs):
                super().__init__(*args, **kwargs)

                self.request = req
                self.response = res

            def __repr__(self):
                """ Return a representation of this `message` object.
                """
                res = self.response
                req = self.request
                r = type(self).__name__ + '('
                r += 'status=' + str(res.status) if res else str(None) 
                r += ', method=' + req.method
                r += ', url=' + str(req.url)
                r += ')'
                return r

        class _tabs(www.browser._tabs):
            """ A collection of test browser tabs.

            :abbr: tabs
            """
            def __init__(self, brw, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.browser = brw

            def tab(self):
                t = tester._browser._tab(self)
                self += t
                return t

        class _tab(www.browser._tab):
            """ Represents a tab in the test browser. The tab makes the
            actual "HTTP" request and preserves the responses HTML in
            its own DOM (.html).

            :abbr: tab
            """

            def __init__(self, tabs):
                """ Create a new test browser tab.
                """
                super().__init__(tabs)
                self._referer  =  None
                self._html     =  None
                self._page     =  None
                self._site     =  None

                # XXX
                self.transfer  = None

                # We are not in SPA mode by default. The `inspa`
                # analogue for a real browser tab would be something
                # like a global JavaScript variable. The user may be
                # given the option of turning SPA mode on or off. This
                # would be a useful option to give users for a number of
                # reasons:
                #
                #   * They are using a text-based browser like `links`
                #     that has no JavaScript support.
                #
                #   * They are using a legacy browser that has poor
                #     JavaScript support.
                #   
                #   * They have JavaScript support disable -- perhaps
                #     for security reasons.
                # 
                #   * The "browser" is actually a bot, such as a web
                #     crawler, whose willingness to execute JavaScript is
                #     not well understood. In this case, you may want to
                #     let the crawler index the page as if the site were a
                #     multi-page application.
                #
                self.inspa     =  False

                self._onbeforeunload = None
                self._onafterload = None
                self.url = None

                # Create a `messages` collection to captures the
                # request/responses that the `tab` makes.
                self.messages = tester._browser.messages()

                self.onafterload += self.self_onafterload

            def default_event(self, src, eargs):
                """ This is the default event handler for all supported
                browser events.

                For example, when a user "click" a hyperlink, this
                method will be called.

                Note that currently, only some events are handled,
                namely hyperclick clicks. Also note that events that
                would be handled by a JavaScript event handler would
                first go to the `element_event` handler first and then
                be routed to their Python event handler. 

                :param: src dom.element: The DOM element that triggered
                the event.

                :param: src dom.eventargs: The `dom.eventargs` which
                contain the arguments for this event.
                """

                # If element_event called eargs.preventDefault,
                # eargs.cancel will be True.
                if eargs.cancel:
                    return

                # If a user clicked a hyperlink (dom.a) navigate the tab
                # to the the new URL.
                if isinstance(eargs.src, dom.a):
                    pg = src.attributes['href'].value
                    self.navigate(pg=pg, ws=self.site)

            @property
            def page(self):
                """ Return the pom.page object this browser tab is
                currently requesting.
                """
                return self._page

            @page.setter
            def page(self, v):
                self._page = v

            def element_event(self, src, eargs):
                """ This event handler catches all events that happen to
                elements in the _tab's DOM (.html), examins the elements
                and uses information found within the elements to
                properly route execution to the "server-side" event
                handler that is intended to capture the event.

                :param: src dom.element: The DOM element that triggered
                the event.

                :param: src dom.eventargs: The `dom.eventargs` which
                contain the arguments for this event.
                """

                ''' Inner functions '''

                def is_nav_link(e):
                    """ Returns True if the element `e` is a "nav link",
                    i.e., it is an anchor tag nested within a <nav>:

                        <nav>
                            <ul>
                                <li
                                    <a>I'm a nav link</a>
                                </li>
                                <ul>
                                    <li>
                                        <a>I'm a nav link from a submenu</a>
                                    </li>
                                </ul>
                            </ul>
                        </nav>
                    """
                    rent = e.parent

                    while rent:
                        if type(rent) is dom.nav:
                            nav = rent
                            break
                        rent = rent.parent
                    else:
                        return False

                    as_ = rent[pom.page.IsNavSelector]
                    for a in as_:
                        if a is e:
                            return True

                    return False

                def replace(this, that):
                    """ Take `this` and replace it with `that`.

                    :param: this str|dom.selector A CSS selector that
                    identifies a unique element in self that should be
                    replaced.

                    :param: that dom.elements The elements to will
                    replace `this`.
                    """

                    # Find the element object
                    this = self.html[this].only

                    # Get the parent
                    rent = this.parent

                    # TODO The below could be done in one line. Taking
                    # insperation from the *real* DOM (the
                    # JavaScript-based one in browsers), which has a
                    # `node.replaceChild` method,  we could add a
                    # `replacechild` method to `dom.element`.

                    # Get the ordinal index of this as a child of it
                    # parent.
                    ix = rent.elements.getindex(this)

                    # Remove `this` from its parent and thus the DOM
                    # self.
                    this.remove()

                    # Put `that` where `this` was
                    rent.elements.insert(ix, that)

                def exec(el):
                    """ Read the <article> with an 'instructions' class
                    for `instruction` elements.

                    An example of an `instruction` is set-url which is the
                    way Python code can cause JavaScript code running in
                    the browser to set the browser`s `window.location`.
                    """
                    instrss = el['.instructions']

                    for instrs in instrss:
                        instrs = instrs['.instruction']

                        for instr in instrs:
                            # If we have a 'set' instruction
                            if 'set' in instr.classes:
                                attr = instr.getattr('name')
                                if attr == 'url':
                                    attr = instr.getattr('content')
                                    url = www.url(attr)
                                    self.url = url

                            elif 'remove' in instr.classes:
                                id = instr.getattr('content')
                                el = self['#' + id].only
                                el.remove()

                ''' Method logic '''

                isnav = is_nav_link(src)
                nav = src.closest('nav')

                if isnav:
                    pg = src.attributes['href'].value
                    if self.inspa:
                        attr = nav.attributes['aria-label']
                        isspanav = attr.value == 'Spa'

                        if not isspanav:
                            return

                    else:
                        # If the user clicked a nav link, but we aren't
                        # in SPA mode, allow the browser to navigate to
                        # the link in the traditional (non AJAX) way.
                        if not self.inspa and isnav:
                            self.navigate(pg=pg, ws=self.site)
                            return

                    html = None
                else:
                    # eargs.html is None when there is no HTML being
                    # sent by the browser.
                    html = eargs.html.html if eargs.html else None
                    pg = self.page

                # Cancel default event handling
                eargs.preventDefault()

                # If eargs.handler is 'None', we hav a null handler. No
                # XHR request should, therefore, be made so return.
                if eargs.handler == 'None':
                    return

                # Create a JSON object to send in the XHR request
                body = {
                    'hnd':      eargs.handler,
                    'html':     html,
                    'src':      src.html,
                    'trigger':  eargs.trigger,
                }

                # Make the XHR request to the page (pg) (or for the page
                # if we are refreshing a subpage for an SPA) and site
                # that the tab is currently pointing to.
                res = self.xhr(pg, self.site, json=body)

                # If the event was unsucessful, append a "modal" to the
                # <main> element of the tab's HTML.
                if res.status >= 400:
                    # TODO Instead of a div, we can use the pom.modal
                    # class when it is written.
                    self.html['main'].only += (mod := dom.div())
                    mod.classes += 'error-modal'
                    mod += res.html.only

                elif isinstance(res.html.first, dom.main):
                    # Replace the <main> element with the response
                    # (res.html)
                    main = res.html.only
                    replace(this='main', that=main)
                    self.listen(res.html)

                    self.url = main.getattr('data-url')
                else:
                    # If no HTML fragments were sent... 
                    if not eargs.html:
                        # ... there can be nothing to replace
                        return

                    # Get the fragement of html in the tab that is the
                    # subject of the event from the tab's DOM (.html)
                    ids = list('#' + x.id for x in eargs.html)
                    for i, id in enumerate(ids):
                        el = res.html[i]
                        replace(id, res.html[i])
                        exec(el)

                    self.listen(res.html)

            def listen(self, el):
                """ Takes an element `el` and examins it for any
                data-{trigger}-handler attributes. Uses this information
                to subscribe el to this tab's event handlers
                self.element_event and self.default_event.These handlers
                will route the element's event to the appropriate
                handler.

                Note that this is analogous to the `listen()` function
                in the eventjs JavaScript.

                :param: el dom.element: The root of the DOM tree that
                will be examined for elements whose events will be
                subscribed to handlers.
                """
                sels = ', '.join(
                    [
                        f'[data-{x}-handler]' 
                        for x in dom.element.Triggers
                    ]
                )
                    
                targets = el[sels]

                # We need to remove the duplicates because of the bug
                # FIXME:9aec36b4
                targets = set(targets)

                for target in targets:
                    for attr in target.attributes:
                        matches = re.match(
                            'data-([a-z]+)-handler',
                            attr.name
                        )
                        if matches:
                            ev = 'on' + matches[1]
                            ev = getattr(target, ev)
                            ev.append(obj=self.element_event)

                # Subscribe to element_event for each <nav> anchor tag's
                # click event.
                as_ = el[pom.page.IsNavSelector]
                for a in as_:
                    ev = a.onclick
                    ev.append(obj=self.element_event)

                # Subscribe to default_event for each anchor tag's click
                # event.
                as_ = el['a']
                for a in as_:
                    ev = a.onclick
                    ev.append(obj=self.default_event)

            def self_onafterload(self, src, eargs):
                """ The event handler that is invoked after the browser
                tab has loaded a new document.
                """

                # Add event handlers to elements in the tab's DOM.
                self.listen(self.html)

            # TODO The ability for a tab to maintain its own internal
            # DOM should exist in the browser.tab base class in `www.py`
            # as well as here.
            @property
            def html(self):
                """ Returns the `tab`'s DOM object.
                """
                return self._html

            @html.setter
            def html(self, v):
                """ When we set a new HTML DOM for the tab, we want to
                make sure all elements that have attributes that match
                the pattern data-<event>-handler are hooked up to the
                the tab's main event handler], `element_event` so that
                actions that happen to those elements can be properly
                routed to the server-side event handler that wants to
                receive the event.

                In addition to those elements that are declared to have
                server-side event handlers, we also register the click
                event of each menu item (<nav> link) so we can have
                testing support for SPA navigation.
                """
                self._html = v

                main = v['main'].only
                self.inspa = main.hasattr('spa-data-path')

            @property
            def referer(self):
                """ The http_referer associated with the tab. When the
                tab makes the request, a ``referer`` may be assigned to
                the tab. After the request has been made, the referrer
                should be set to the current URL.  

                rtype: ecommerce.url
                """
                if self._referer:
                    if isinstance(self._referer, ecommerce.url):
                        pass
                    elif self._referer is None:
                        pass
                    else:
                        self._referer = ecommerce.url(
                            address=self._referer
                        )

                return self._referer

            @referer.setter
            def referer(self, v):
                self._referer = v

            @property
            def browser(self):
                return self.tabs.browser

            def __getitem__(self, sel):
                """ Returns a list of elements in the tab's internal DOM
                that match the CSS selector `sel`.

                :param: sel str|dom.selectors: The CSS selector as a
                string or a dom.selectors object.
                """
                return self.html[sel]

            def __str__(self):
                r = str(self.html)

                # TODO Add URL to return
                # r += str(self.url)
                return r

            def navigate(self, pg, ws):
                """ Issues an HTTP GET request for a page (`pg`) on
                the  webserver (ws). The response is used to update the
                tab's internal DOM (self.html). The www.response object
                is returned if needed.

                :param: pg www.url|pom.page|str: The page, or url of the
                page, to GET.

                :param: ws pom.site: The site to get the page from.
                """

                eargs = www.browser.loadeventargs(url=self.url)
                self.onbeforeunload(self, eargs)

                pg = str(pg)

                res = self.get(pg, ws)
                self.html = res.html

                self.url = www.url(
                    f'http://{ws.host}:8000/{pg.lstrip("/")}'
                )

                eargs = www.browser.loadeventargs(url=self.url)
                self.onafterload(self, eargs)
                return res

            def get(self, pg, ws, hdrs=None):
                """ Issues an HTTP GET request for the page `pg` to the
                site `ws`. The responses object from the request is
                returned.

                Note that `get` will not alter the `tab`'s internal DOM
                (afterall, browser tab's make requests all the time that
                don't alter the HTML structure of the DOM). If you want
                to point the `tab` to a URl for it to GET and load into
                its internal DOM, use the `navigate` method.
                
                :param: pg pom.page|str: The page to GET.

                :param: ws pom.site: The site to get the page from.
                """
                return self._request(pg=pg, ws=ws, meth='GET', hdrs=hdrs)

            def xhr(self, pg, ws, json=None):
                """ Issues an XHR (AJAX) request to a server. The
                response object from the request is returned.

                XHR requests are HTTP POSTs. They usually contain JSON
                data. XHR requests route server-side event handling from
                the browser, perform page changes for SPA pages, and can
                facilitate general RPC request.

                :param: pg pom.page|str: In server-side event handling,
                the page object that contains the event handler. In SPA
                page changes, this is the pg we want to change the SPA
                to.

                :param: ws pom.site: The site to post to.

                :parson: json dict: The body, encoded as a dict, to be
                POSTed as the request's body.
                """
                from json import dumps

                body = dumps(json)

                # Setting the Content-Type header to application/json
                # basically flags the request as XHR.
                hdrs = www.headers(
                    {'CONTENT_TYPE': 'application/json'}
                )

                return self._request(
                    pg=pg, ws=ws, body=body, meth='POST', hdrs=hdrs
                )
                
            def post(self, pg, ws, body=None, frm=None, files=None):
                """ Issues an HTTP POST request to a page (`pg`) on
                the  webserver (ws). The response object is retured.

                :param: pg pom.page|str: The page to POST to.

                :param: ws pom.site: The site to get the page from.

                :param: body str: The data being posted.

                :param: body dom.frm: The dom.form which contains the
                data being posted.

                :param: body file.file|file.files: The files being
                posted.
                """

                # Make sure we have a collection of files
                if files:
                    files = files.orm.collectivize()

                return self._request(
                    pg=pg,    ws=ws,        body=None,
                    frm=frm,  files=files,  meth='POST'
                )

            def head(self, pg, ws):
                """ Issues an HTTP HEAD request for a page (`pg`) on
                the  webserver (ws). 

                :param: pg pom.page|str: The page object.

                :param: ws pom.site: The website.
                """
                return self._request(pg=pg, ws=ws, meth='HEAD')

            def _request(
                self, pg, ws, 
                body=None, frm=None, files=None, meth='GET', hdrs=None
            ):
                """ Issues an HTTP request to or for a page (`pg`) on
                the  webserver (ws). The response object is retured.

                :param: pg pom.page|str: The page to request.

                :param: ws pom.site: The site to send the request to.

                :param: body str: The data being sent in a POST.

                :param: body dom.frm: The dom.form which contains the
                data being POSTed.

                :param: body file.file|file.files: The files being
                POSTed.

                :param: hdrs www.headers: A collection of headers to be
                appended to the request.
                """

                arg_hdrs = www.headers(hdrs) if hdrs else None

                isa = isinstance
                if not isa(pg, str) and not isa(pg, pom.page):
                    raise TypeError(
                        'pg parameter must be a str or page'
                    )

                if not isa(ws, pom.site):
                    raise TypeError('ws parameter must be a pom.site')

                if frm and not isa(frm, dom.form):
                    raise TypeError('frm parameter must be a dom.form')

                def create_environ(env=None):
                    d = {
                        'CONTENT_TYPE': 'application/x-www-form-urlencoded',
                        'HTTP_ACCEPT': '*/*',
                        'HTTP_USER_AGENT': 'tester/1.0',
                        'RAW_URI': '/',
                        'REMOTE_PORT': '43130',
                        'SCRIPT_NAME': '',
                        'SERVER_PORT': '8000',
                        'SERVER_PROTOCOL': 'http/1.1',
                        'SERVER_SOFTWARE': 'gunicorn/19.4.5',
                        'gunicorn.socket': None,
                        'wsgi.errors': None,
                        'wsgi.file_wrapper': None,
                        'wsgi.input': '',
                        'wsgi.multiprocess': False,
                        'wsgi.multithread': False,
                        'wsgi.run_once': False,
                        'wsgi.url_scheme': 'http',
                        'wsgi.version': (1, 0)
                    }

                    cookies = self.browser.cookies
                    if cookies.count:
                        d['HTTP_COOKIE'] = cookies.header.value

                    # Merge env into d
                    if env:
                        d.update(env)
                    
                    # Merge the HTTP request headers in `arg_hdrs` into
                    # the environ dict. According to WSGI, actual HTTP
                    # request headers should be preceeded by an 'HTTP_'.
                    if arg_hdrs:
                        for hdr in arg_hdrs:
                            name = hdr.name.replace('-', '_').upper()

                            d['HTTP_' + name] = hdr.value

                            # Some standard WSGI environ keys overlap
                            # with standard HTTP request headers. In
                            # that case, add the WSGI version. So if we
                            # have a HTTP header of Content-Type, we
                            # should add that to the WSGI environ dict
                            # as 'HTTP_CONTENT_TYPE' and 'CONTENT_TYPE'.
                            # See:
                            #     https://wsgi.readthedocs.io/en/latest/definitions.html
                            #     https://developer.mozilla.org/en-US/docs/Glossary/Request_header
                            if name in ('CONTENT_TYPE',):
                                d[name] = hdr.value

                    return d

                st, hdrs = None, None
                def start_response(st0, hdrs0):
                    nonlocal st
                    nonlocal hdrs
                    st, hdrs = st0, hdrs0

                if isinstance(pg, str):
                    import urllib
                    url = urllib.parse.urlparse(pg)

                    pg = type(ws)._strip(url.path)

                    pg = ws(pg)
                    path = url.path
                    qs = url.query

                elif isinstance(pg, pom.page):
                    path = f'/{pg.language}{pg.path}'
                    qs = str()

                if pg:
                    pg.clear()
                    # If the pom.page calls into another pom.page, such as
                    # when the page redirects, this test browser tab should
                    # become aware of this and change self.page. This event
                    # handling loging captures that this.
                    # page will become the 
                    changed = False
                    def pg_onafterpagechange(src, eargs):
                        nonlocal changed
                        changed = True

                        self.page = eargs.page
                        
                    # Subscribe to event
                    pg.onafterpagechange += pg_onafterpagechange

                if meth == 'POST':
                    if body:
                        if isa(body, str):
                            body = body.encode('utf-8')

                        inp = io.BytesIO(body)

                        env = create_environ({
                            'CONTENT_LENGTH':  str(len(body)),
                            'wsgi.input':      inp,
                        })
                        
                    elif files and files.count:
                        boundry = uuid.uuid4().hex
                        inp = io.BytesIO()

                        boundry = f'--{boundry}'
                        for file in files:
                            inp.write(bytes(
                            f'--{boundry}\r\n'
                            'Content-Disposition: form-data;'
                            f'name=file;'
                            f'filename={file.name}\r\n'
                            'Content-Type:application/octet-stream\r\n\r\n',
                            'utf-8'
                            ))

                            inp.write(file.body)

                        inp.write(bytes(f'\r\n\r\n--{boundry}', 'utf-8'))

                        inp.seek(0)

                        env = create_environ({
                            'CONTENT_TYPE':  (
                                'multipart/form-data; '
                                f'boundry={boundry}'
                            ),
                            'CONTENT_LENGTH': len(inp.getvalue()),
                            'wsgi.input': inp,
                        })
                    else:
                        inp = io.BytesIO(frm.post)

                        env = create_environ({
                            'CONTENT_LENGTH':  len(frm.post),
                            'wsgi.input':      inp,
                        })
                else: 
                    env = create_environ()

                env['PATH_INFO']       =  path
                env['QUERY_STRING']    =  qs
                env['SERVER_NAME']     =  ws.host
                env['SERVER_SITE']     =  ws
                env['REQUEST_METHOD']  =  meth
                env['REMOTE_ADDR']     =  self.tabs.browser.ip
                env['HTTP_REFERER']    =  self.referer
                env['USER_AGENT']      =  self.browser.useragent

                # Create WSGI app
                app = www.application()

                # Create request. Associate with app.
                req = www.request(app)

                # Record the request/response in a `message` object 
                msg = tester._browser.message(req=req)
                self.messages += msg

                app.breakonexception = \
                    self.browser.tester.testers.breakonexception
                
                # Make WSGI call
                iter = app(env, start_response)

                res = www.response(req) 

                msg.response = res

                # Just get the status code from st (which contains the
                # entire phrase, i.e., '200 OK'). In the future, we may
                # have a res.message setter that can parse this out, but
                # that would only be necessary if we want to include
                # non-standard phrases such as '502 Bad Database
                # Connection' instead of the standard '502 Bad Gateway'.
                res._status = st.split()[0]
                res._headers = www.headers(hdrs)

                res.body = next(iter)

                # Deal with the set-cookie header
                hdr = res.headers('set-cookie')

                if hdr:
                    cookie = dict(x.split('=') for x in hdr.split('; '))
                    jwt = cookie['token']
                    exp = cookie['expires']
                    path = cookie['path']
                    domain = ws.title
                    exp = primative.datetime(exp)
                    delete = exp < primative.datetime.utcnow()

                    if delete:
                        self.browser.cookies.remove('jwt')
                    else:
                        cookie = tester._browser._cookie(
                            name='jwt',     value=jwt,
                            domain=domain,  path=path,
                        )
                        self.browser.cookies += cookie 

                self.referer = req.url

                # If there was a page passed in and the page was not
                # changed by a redirect (see above).
                if pg and not changed:
                    self.page = pg

                self.site = ws
                return res

            @contextmanager
            def capture(self):
                """ A context manager the browser `messages` generated
                by an event - such as a button click.

                This is used by tests to determine what the HTTP
                response of a dom.event is.
                """
                msgs = tester._browser.messages()

                def messages_onadd(src, eargs):
                    nonlocal msgs
                    e = eargs.entity
                    msgs += e
                    
                try:
                    self.messages.onadd += messages_onadd
                    yield msgs
                finally:
                    self.messages.onadd -= messages_onadd

        ''' Class members of browser'''
        def __init__(
            self, tester, ip=None, useragent=None, *args, **kwargs
        ):
            super().__init__(*args, **kwargs)
            self.tester = tester
            self.tabs = tester._browser._tabs(self)

            # Assign the browser a default useragent string
            if not useragent:
                useragent = (
                'Mozilla/5.0 (iPhone; CPU iPhone OS 5_1 like Mac OS X) '
                'AppleWebKit/534.46 (KHTML, like Gecko) Version/5.1 '
                'Mobile/9B179 Safari/7534.48.3'
                )

            # Assign the test browser a default ip
            if not ip:
                ip = ecommerce.ip(address='10.10.10.10')

            self.ip = ecommerce.ip(address=ip)

            self.useragent = ecommerce.useragent(string=useragent) 

    def browser(self, *args, **kwargs):
        return tester._browser(self, *args, **kwargs)

    @property
    def isok(self):
        return self.failures.isempty

    @staticmethod
    def dedent(str, *args):
        return textwrap.dedent(str).strip() % args

    def all(self, actual, msg=None):
        if not all(actual):
            self._failures += failure()

    def assertFull(self, actual, msg=None):
        if type(actual) != str or actual.strip() == '':
            self._failures += failure()

    def full(self, actual, msg=None):
        if type(actual) != str or actual.strip() == '':
            self._failures += failure()

    def assertEmpty(self, o, msg=None):
        if o != '': self._failures += failure()

    def empty(self, o, msg=None):
        if o != '': self._failures += failure()
        
    def assertUuid(self, id, msg=None):
        if isinstance(id, uuid.UUID):
            raise builtins.ValueError('Assert type instead')

        try: 
            uuid.UUID(str(id), version=4)
        except builtins.ValueError: 
            self._failures += failure()

    def uuid(self, id, msg=None):
        if isinstance(id, uuid.UUID):
            raise builtins.ValueError('Assert type instead')

        try: 
            uuid.UUID(str(id), version=4)
        except builtins.ValueError: 
            self._failures += failure()

    def assertTrue(self, actual, msg=None):
        if type(actual) is not bool:
            raise builtins.ValueError('actual must be bool')

        if not actual: self._failures += failure()

    def true(self, actual, msg=None):
        if type(actual) is not bool:
            raise builtins.ValueError('actual must be bool')

        if not actual: self._failures += failure()

    def assertTruthy(self, actual, msg=None):
        if not actual: self._failures += failure()

    def truthy(self, actual, msg=None):
        if not actual: self._failures += failure()

    def assertFalse(self, actual, msg=None):
        if type(actual) is not bool:
            raise builtins.ValueError('actual must be bool')

        if actual: self._failures += failure()

    def false(self, actual, msg=None):
        if type(actual) is not bool:
            raise builtins.ValueError('actual must be bool')

        if actual: self._failures += failure()

    def assertFalsey(self, actual, msg=None):
        if actual: self._failures += failure()

    def falsey(self, actual, msg=None):
        if actual: self._failures += failure()

    def assertFail(self, msg=None):
        self._failures += failure()

    def fail(self, msg=None):
        self._failures += failure()

    def assertPositive(self, actual):
        if actual < 0: self._failures += failure()

    def assertIsInstance(self, expect, actual, msg=None):
        if not isinstance(expect, actual): self._failures += failure()

    def isinstance(self, expect, actual, msg=None):
        if not isinstance(expect, actual): self._failures += failure()

    def assertType(self, expect, actual, msg=None):
        if type(actual) is not expect: self._failures += failure()

    def type(self, expect, actual, msg=None):
        if not isinstance(expect, type):
            name = type(expect).__name__
            raise TypeError(
                'expect must be of type `type`; receieved: '
                f'"{name}"'
            )

        if type(actual) is not expect: self._failures += failure()

    def assertEq(self, expect, actual, msg=None):
        if expect != actual: self._failures += failure()

    def eq(self, expect, actual, msg=None):
        if expect != actual: self._failures += failure()

    def startswith(self, expect, actual, msg=None):
        if not actual.startswith(expect): self._failures += failure()

    def endswith(self, expect, actual, msg=None):
        if not actual.endswith(expect): self._failures += failure()

    def assertNe(self, expect, actual, msg=None):
        if expect == actual: self._failures += failure()

    def ne(self, expect, actual, msg=None):
        if expect == actual: self._failures += failure()

    # TODO The gt, lt, etc. are the opposite
    #
    #     def gt(self, expect, actual, msg=None):
    #         if not (expect > actual): self._failures += failure()
    #         # should be
    #         if not (expect < actual): self._failures += failure()
    def assertGt(self, expect, actual, msg=None):
        if not (expect > actual): self._failures += failure()

    def gt(self, expect, actual, msg=None):
        if not (expect < actual): self._failures += failure()

    def assertGe(self, expect, actual, msg=None):
        if not (expect >= actual): self._failures += failure()

    def ge(self, expect, actual, msg=None):
        with suppress(TypeError):
            actual = len(actual)

        if not (expect <= actual): self._failures += failure()

    def assertLt(self, expect, actual, msg=None):
        if not (expect < actual): self._failures += failure()

    def assertLe(self, expect, actual, msg=None):
        if not (expect <= actual): self._failures += failure()

    def lt(self, expect, actual, msg=None):
        if not (actual < expect): self._failures += failure()

    def le(self, expect, actual, msg=None):
        if not (actual <= expect): self._failures += failure()

    def assertIs(self, expect, actual, msg=None):
        if expect is not actual: self._failures += failure()

    def is_(self, expect, actual, msg=None):
        if expect is not actual: self._failures += failure()

    def in_(self, expect, actual, msg=None):
        if actual not in expect: self._failures += failure()

    def notin(self, expect, actual, msg=None):
        if actual in expect: self._failures += failure()

    def isnot(self, expect, actual, msg=None):
        if expect is actual: self._failures += failure()

    def assertNone(self, o, msg=None):
        if o != None: self._failures += failure()

    def none(self, o, msg=None):
        if o != None: self._failures += failure()

    def assertNotNone(self, o, msg=None):
        if o == None: self._failures += failure()

    def notnone(self, o, msg=None):
        if o == None: self._failures += failure()

    def assertZero(self, actual):
        if len(actual) != 0: self._failures += failure()

    def zero(self, actual, msg=None):
        if len(actual) != 0: self._failures += failure()

    def multiple(self, actual, msg=None):
        if len(actual) == 0: self._failures += failure()

    def assertOne(self, actual):
        if len(actual) != 1: self._failures += failure()

    def one(self, actual, msg=None):
        if len(actual) != 1: self._failures += failure()

    def assertTwo(self, actual):
        if len(actual) != 2: self._failures += failure()

    def two(self, actual):
        if len(actual) != 2: self._failures += failure()

    def assertThree(self, actual):
        if len(actual) != 3: self._failures += failure()

    def three(self, actual):
        if len(actual) != 3: self._failures += failure()

    def four(self, actual, msg=None):
        if len(actual) != 4: self._failures += failure()

    def five(self, actual):
        if len(actual) != 5: self._failures += failure()

    def six(self, actual):
        if len(actual) != 6: self._failures += failure()

    def seven(self, actual):
        if len(actual) != 7: self._failures += failure()

    def eight(self, actual):
        if len(actual) != 8: self._failures += failure()
        
    def nine(self, actual):
        if len(actual) != 9: self._failures += failure()

    def ten(self, actual):
        if len(actual) != 10: self._failures += failure()

    def eleven(self, actual):
        if len(actual) != 11: self._failures += failure()

    def twelve(self, actual):
        if len(actual) != 12: self._failures += failure()

    def populated(self, actual):
        if len(actual) == 0: self._failures += failure()

    def assertCount(self, expect, actual, msg=None):
        if expect != len(actual): self._failures += failure()

    def count(self, expect, actual, msg=None):
        if expect != len(actual): self._failures += failure()

    def assertValid(self, ent):
        v = ent.isvalid
        if type(v) is not bool:
            raise Exception('invalid property must be a boolean')
        if not v:
            self._failures += failure(ent=ent)

    def valid(self, ent):
        v = ent.isvalid
        if type(v) is not bool:
            raise Exception('invalid property must be a boolean')
        if not v:
            self._failures += failure(ent=ent)

    def assertInValid(self, ent):
        v = ent.isvalid
        if type(v) is not bool:
            raise Exception('invalid property must be a boolean')
        if v:
            self._failures += failure(ent=ent)

    def invalid(self, ent):
        v = ent.isvalid
        if type(v) is not bool:
            raise Exception('invalid property must be a boolean')
        if v:
            self._failures += failure(ent=ent)

    def assertBroken(self, ent, prop, rule):
        if not ent.brokenrules.contains(prop, rule):
            self._failures += failure()

    def broken(self, ent, prop, rule):
        if not ent.brokenrules.contains(prop, rule):
            self._failures += failure()

    @contextmanager
    def brokentest(self, brs):
        def test2str(attr, type, e, msg=None):
            return (
                f'message: "{msg if msg else ""}", '
                f'attr: "{attr}", '
                f'type: "{type}", '
                f'entity: {builtins.type(e)}'
            )

        class tester:
            def __init__(self, brs):
                self.brokenrules = brs
                self.found = entities.brokenrules()
                self.tested = list()
                self.dups = list()
                self.unfound = list()

            def __call__(self, e, attr, type, msg=None):
                test = attr, type, e
                if test in self.tested:
                    self.dups.append(test)
                    return

                self.tested.append(test)
                
                for br in self.brokenrules:
                    if br.entity is e:
                        if br.property == attr:
                            if br.type == type:
                                if not msg or br.message == msg:
                                    self.found += br
                                    break
                else:
                    self.unfound.append(test2str(attr, type, e, msg))

        if isinstance(brs, entities.entity):
            # If brs is an entity, get itl broken rule
            brs = brs.brokenrules
        elif isinstance(brs, entities.brokenrules):
            # This is what we would expect
            pass
        else:
            raise TypeError(
                f'Cannot test brokenrules on type {type(brs)}'
            )
        t = tester(brs)
        yield t

        msg = str()
        for br in t.unfound:
            msg += f'Cannot find brokenrule for: {br}\n'

        for br in t.brokenrules:
            for br1 in t.found:
                if br.entity == br1.entity:
                    if br.property == br1.property:
                        if br.type == br1.type:
                            break
            else:
                msg += f'Untested: {br!r}\n'

        reported = list()
        for br in t.brokenrules:
            cnt = 0
            for br1 in t.brokenrules:
                if br.entity == br1.entity:
                    if br.property == br1.property:
                        if br.type == br1.type:
                            cnt = cnt + 1
            if cnt > 1:
                tup = br.property, br.property, br.entity
                if tup not in reported:
                    reported.append(tup)
                    msg += f'{cnt - 1} duplicate of {br!r}\n'

        for test in t.dups:
            msg += f'Duplicate test: {test2str(*test)}\n'

        if msg:
            # HACK:42decc38 The below gets around the fact that
            # tester.py can't deal with stack offsets at the moment.
            # TODO Correct the above HACK.
            msg = f"test in %s at %s\n{msg}" % inspect.stack()[2][2:4]
            self._failures += failure()


    def unique(self, ls):
        if len(ls) != len(set(ls)): self._failures += failure()

    def expect(self, expect, fn, msg=None):
        # NOTE expect swallows exceptions, so passing -b flag to tester
        # won't cause a break where fn() raises an exception (assuming
        # it does).
        try:
            if not callable(fn):
                raise TypeError((
                    'The fn parameter must be a callable object. '
                    'Consider using a function or lambda instead of '
                    'a: ' + type(fn).__name__
                ))

            # Invoke the callable. If we expect no exception (expect is
            # None), return the value.
            r = fn()

        except Exception as ex:
            if expect is None or type(ex) is not expect:
                self._failures += failure(actual=ex)

            return None
        else:
            if expect is not None:
                self._failures += failure(actual=None)

            return r

    def repr(self, expect, actual, msg=None):
        if repr(actual) != expect:
            self._failures += failure()

    def str(self, expect, actual, msg=None):
        if str(actual) != expect:
            self._failures += failure()

    @property
    def failures(self):
        return self._failures

    def __str__(self):
        if self.failures.isempty:
            r = ''
            ok = 'pass'
        else:
            r = '\n'
            ok = 'FAIL'

        name = self.__class__.__name__
        file = sys.modules[self.__class__.__module__].__file__

        file = file.lstrip('./')

        file = os.path.basename(file)

        test = f'({file}) [{name}]'

        r += "{}{}{}".format(test, ' ' * (72 - len(test) - 4), ok)

        if self.failures.isempty:
            return r
        return r + "\n" + self.failures._tostr(includeHeader=False) + "\n"

    # TODO Remove preserve. It should be called dedent.
    @staticmethod
    def preserve(str):
        return dedent(str)[1:-1]

    def status(self, st, res):
        if st != res.status: 
            msg = f'Actual status: {res.status}'
            
            self._failures += failure()

    def ok(self, res):
        if res.status != 200:
            msg = f'Actual status: {res.status}'
            
            self._failures += failure()

    def h200(self, res):
        if res.status != 200:
            msg = f'Actual status: {res.status}'
            
            self._failures += failure()

    def h500(self, res):
        if res.status != 500:
            msg = f'Actual status: {res.status}'
            
            self._failures += failure()

    def _trigger(self, trig, e, tab, count):
        """ A private method to call the `trig` trigger method on `e`.
        Return the last response the browser recorded.

        Testing the return value is important for tests to ensure that
        dom.events were successful.

        :param: trig str: The name of the trigger, e.g., 'click',
        'submit', 'blur', etc.

        :param e dom.element: The target of the event.

        :param: tab www.browser._tab: The browser tab in which the event
        is triggered.

        :param: count int: The number of HTTP requests that the trigger
        is intended to cause.
        """
        trig = getattr(e, trig)

        with tab.capture() as msgs:
            trig()

        if msgs.count != count:
            raise ValueError(
                'Incorrect HTTP messages count. '
                f'Expected: {count} Actual: {msgs.count}'
            )

        if last := msgs.last:
            return last.response

        return None

    @contextmanager
    def dragstart(self, e, tab, count=1):
        """ XXX
        """
        tab.transfer = dom.transfer()
        tx = tab.transfer

        B()
        yield self._trigger('dragstart', e, tab, count)

        ishnd = 'handle' in self.classes

        if ishnd:
            id = e.getattr('data-drag-target')
            target = self.root['#' + id]
            tx.set('text/html', target.html)

        yield tx

        self.transfer = None

    def drop(self, zone):
        """ XXX
        """
        src = tx.get('text/html')
        src = dom.html(src)
        zone.drop(src)
                    
    def submit(self, e, tab, count=1):
        """ Call the click() trigger method on a form (`e`). Return the
        last response the browser recorded.

        :param: e dom.form|dom.button: The `form` element or submit
        button of a form.

        :param: tab www.browser._tab: The browser tab in which the event
        is triggered.

        :param: count int: The number of HTTP requests that the trigger
        is intended to cause.
        """
        if isinstance(e, dom.form):
            e = e['button[type=submit]'].only
            return self.click(e, tab, count)
            
        return self._trigger('submit', e, tab, count)

    def click(self, e, tab, count=1):
        """ Call the click() trigger method on `e`. Return the last
        response the browser recorded.

        Testing the return value is important for tests to ensure that
        dom.events were successful.

        :param: e dom.form|dom.button: The element on which to invoke
        the trigger.

        :param: tab www.browser._tab: The browser tab in which the event
        is triggered.

        :param: count int: The number of HTTP requests that the trigger
        is intended to cause.
        """
        return self._trigger('click', e, tab, count)

class benchmark(tester):
    """ A type of tester class that represents benchmark/performance
    tests.
    """

    def time(self, 
        min, max, callable, 
        number=None, msg=None, setup='pass'
    ):
        """ Determine the time it takes to call `actual`. The average
        time to call `actual` in milliseconds is returned as a floating
        point number.

        :param: min float|int: The minimum time the test was expected to
        take.

        :param: max float|int: The maximum time the test was expected to
        take.

        :param: callable callable: The function or lambda to benchmark.

        :param: number int: The number of times to repeat the invocation
        of `callable`. We want to call `callable` a number of times to
        get an average call time.

        :param: msg str: The message used when reporting failures
        (currently unused).

        :return: float: The time it took, on average, to run callable.
        """

        # Create the Timer and execute
        timer = timeit.Timer(stmt=callable, setup=setup)
        actual = timer.timeit(number)

        # Convert results to milliseconds
        actual *= 1000

        # Divide by number to get the average number of seconds it takes
        # to invoke the callable once.
        actual /= number

        # Record the assesment for future reporting
        self.assessments += assessment(min, max, actual)

        # If debug mode
        if self.testers.profile:
            
            # Get the stringified assesment we added above and remove
            # extraneous whitespace
            ass = ' '.join(str(self.assessments.last).split())

            # Print assement
            print(f'\n* {ass}\n')

            # Profile and break
            PR(callable)

        # Return the average time to run `actual` in milliseconds
        return actual

    def __str__(self):
        """ Return a report of the benchmarks assessments.
        """
        return str(self.assessments)

class httpresponse(entities.entity):
    # TODO:ed602720 Is this dead code. Shouldn't we be using
    # www.response for this.
    def __init__(self, statuscode, statusmessage, headers, body):
        self.statuscode = statuscode
        self.statusmessage = statusmessage
        self.headers = headers
        self.body = body

    @property
    def brokenrules(self):
        brs = entities.brokenrules()
        if self.statuscode < 200 or self.statuscode > 400:
            brs += brokenrule('Status code is not valid: ' + str(self.statuscode))

        if self.body['__exception']:
            brs += entities.brokenrules('Exception was returned');

        return brs

    def hasbrokenrule(self, prop, type=None, msg=None):
        brs = self.body['__brokenrules']

        for br in brs:
            if br['property'] != prop:
                continue

            if type != None:
                try:
                    if br['type'] != type:
                        continue
                except KeyError:
                    continue

            if msg != None:
                try:
                    if msg != br['message']:
                        continue
                except KeyError:
                   continue

            return True
        return False

    def __str__(self):
        r = self.statusmessage + '\n'
        for hdr in self.headers:
            r += hdr[0] + ': ' + hdr[1] + '\n'
        r += pprint.pformat(self.body)
        return r
            
class assessments(entities.entities):
    """ Contains a collections of benchmark assessments.
    """
    def __init__(self, tester, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tester = tester

    def __str__(self):
        r = type(self.tester).__name__
        r += '\n'
        for ass in self:
            r += f'{ass}'

        return r

class assessment(entities.entity):
    """ Represents an assessment of a benchmark.

    An assesment records the unit (method or function) that was
    assessed, the duration that it was expected to run in, and the
    actual time it took to complete.
    """

    def __init__(self, min, max, actual, *args, **kwargs):
        """ Create an assessment.

        :param: min float|int: Along with max, represents the range of
        milliseconds that was expected for the test to run.

        :param: max float|int: Along with min, represents the range of
        milliseconds that was expected for the test to run.

        :param: actual float: The duration, in milliseconds, the unit took.
        """
        super().__init__(*args, **kwargs)

        # Record object state
        self.min = min
        self.max = max
        self.actual = actual

        # Use instrospection to get the class (tester) and method that
        # created the assessment. This should represent the unit that
        # was assessed.
        frm = sys._getframe()
        while frm := frm.f_back:
            # Get the class
            self.tester = frm.f_locals['self']

            # Get the method being assessed
            self.method = frm.f_code.co_name

            # Make sure the class and method was an actual benchmark
            # test.
            isbenchmark = isinstance(self.tester, benchmark)
            if isbenchmark and self.method.startswith('it_'):
                break
        else:
            raise Exception('Cannot find benchmark class')
        
    def __str__(self):
        """ Reports the details of the assessment.
        """
        r = f'\t{self.method:50}'
        range = f'({self.min:.2f}-{self.max:.2f})'
        r += f' {range:14} [{self.actual:.2f}]  '
        if self.actual < self.min:
            r += 'LOW'
        elif self.actual > self.max:
            r += 'HIGH'
        else: 
            r += 'pass'

        return f'{r}\n'
    
class failures(entities.entities):
    pass

class failure(entities.entity):
    def __init__(self, cause=None, assert_=None, ent=None, actual=None):
        self._assert = assert_
        self.cause = cause
        self.entity = ent
        self._actual = actual
        if not cause:
            stack = inspect.stack()
            self._assert = stack[1][3]
            self._test   = stack[2][3]
            self._line   = stack[2][2]
            try:
                self._expect = inspect.getargvalues(stack[1][0])[3]['expect']
            except KeyError:
                pass

            try:
                self._actual = inspect.getargvalues(stack[1][0])[3]['actual']
            except KeyError:
                pass

            try:
                msg = inspect.getargvalues(stack[1][0])[3]['msg']

                if isinstance(msg, str) or msg is None:
                    self._message = msg
                else:
                    self._message = None
                    raise TypeError(
                        'Assertion message must be of type str'
                    )
            except KeyError:
                pass

    def __str__(self):
        if self.cause:
            r = "{}: {} in {}".format(self.cause.__class__.__name__,
                                        repr(self.cause),
                                        self._assert)
        else:
            r = "{} in {} at {}".format(self._assert, self._test, self._line)
            if hasattr(self,'_expect'):
                r += "\nexpect: " + repr(self._expect)
                r += "\nactual: " + repr(self._actual)

            if hasattr(self, '_message') and self._message != None:
                r += "\nmessage: " + self._message

            if self.entity:
                for br in self.entity.brokenrules:
                    r += "\n - " + str(br)
        return r
        
class cli:
    def __init__(self):
        self.start = time.time()
        # If we are instantiating, convert the @classmethod cli.run to
        # the instance method cli._run. This makes it possible to call
        # the run() method either as cli.run() or cli().run(). This also
        # works with subclasses of cli. This makes it convenient for
        # unit test developers who may or may not want to customize or
        # override the default implementation.
        #
        # See M. I. Wright's comment at:
        # https://stackoverflow.com/questions/28237955/same-name-for-classmethod-and-instancemethod
        self.run = self._run
        
        self._testers = None

        # Subscribe to the logger so we are given a heads up when a test
        # causes a log message to be written
        logs.log().onlog += self._log_onlog

        self.parseargs()

    def _log_onlog(self, src, eargs):
        """ Print log messages that tests cause to stdout. These
        messages would typically be logged to syslog and would probably
        go unnoticed if we didn't print them here.
        """
        rec = eargs.record
        print(f'{self.seconds:.3f} {rec.levelname} {rec.message}')

    @property
    def seconds(self):
        return time.time() - self.start

    @property
    def testers(self):
        if self._testers is None:
            self._testers = testers()
            self._testers.onbeforeinvoketest += self._testers_onbeforeinvoketest
        return self._testers

    @classmethod
    def run(cls):
        cls().run()

    def _run(self):
        ts = self.testers

        # Run tests
        ts.run()

        # Show results
        print(ts)

        # Return exit code (0=success, 1=fail)
        sys.exit(int(not ts.isok))

    def parseargs(self):
        # TODO Consider adding a -t to run whichever test has been
        # selected a certain number of times. Currently, to run a test
        # an infinate amount of times, we do this:
        #
        #     while true; do python3 test.py test_orm.it_runs; done
        #
        # It would be better to run write this as:
        #
        #     python3 test.py test_orm.it_runs -t0
        #
        # or mayby:
        #
        #     python3 test.py test_orm.it_runs --inf
        #
        # Or if we wanted to run the test 10 times, we could do this:
        #
        #     python3 test.py test_orm.it_runs -t10
        #
        # Running test multiple times is important for capturing
        # problems that happen sporadically.

        ts = self.testers
        epilog = textwrap.dedent('''
        Examples:

            # Run all tests
            ./test.py

            # Run all file tests
            ./testfile.py

            # Run all tests in the test_orm class inside of test.py
            ./test.py test_orm

            # Run the 'it_instantiates' test in the test_orm class
            # inside of test.py
            ./test.py test_orm.it_instantiates

            # Break into debugger if there is an exception
            ./test.py -b

            # Only run performance tests. Exclude all the regular logic
            # tests
            ./test.py -p

            # Run test_orm.it_instantiates under profile
            ./test.py test_orm.it_instantiates:p
            '''
        )

        import argparse
        p = argparse.ArgumentParser(
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=epilog
        )

        p.add_argument(
            'test',
            help=(
                'The test class and/or method to run. For example: '
                "'my_tester_class' or 'my_tester_class.my_test_method'"
            ),
            nargs='?'
        )

        p.add_argument(
            '-b', 
            '--break', 
            action='store_true', 
            dest='breakonexception',
            help='break into pdb on uncaught exceptions',
        )

        p.add_argument(
            '-t',                 
            '--rebuild',
            action='store_true',  
            dest='rebuildtables',
            help="rebuild tables (default)",
        )

        p.add_argument(
            '-T',                  
            '--dont-rebuild',
            action='store_false',  
            dest='rebuildtables',
            help="don't rebuild tables"
        )

        p.add_argument(
            '-p',                  
            '--performance',
            action='store_true',  
            dest='performance',
            help="run performance tests only"
        )

        p.set_defaults(rebuildtables=True)

        self.args = p.parse_args()

        self.testers.breakonexception = self.args.breakonexception
        self.testers.rebuildtables = self.args.rebuildtables
        self.testers.performance = self.args.performance

        # Get the test subject. It will be in the following format:
        # 
        #    class[.method[:flags]] 
        if test := self.args.test:
            # Get the class
            test = test.split('.')
            self.testers.class_ = test.pop(0)
            if test:
                # Get the method
                test = test.pop().split(':')
                self.testers.method = test.pop(0)
                if test:
                    # Set properties based on flags (i.e., 'p')
                    flags = test.pop()

                    # Validate flags
                    for flag in flags:
                        if flag not in ('p',):
                            raise builtins.ValueError(
                                f'Invalid flag: "{flag}"'
                            )

                    self.testers.profile = 'p' in flags

    def _testers_onbeforeinvoketest(self, src, eargs):
        ''' Get tracked objects count '''
        cnts = list()

        # Collect garbage
        gc.collect()

        # Get the counts for each generation of objects tracked by the
        # cyclical garbage collector
        for i in range(3):
            cnts.append(f'{len(gc.get_objects(generation=i)):,}')

        cnts = f"[{' '.join(cnts)}]"

        ''' Get memory usage '''
        mbs = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        mbs = int(mbs / 1000)
        cls = eargs.class_.__name__
        meth = eargs.method[0]

        # Print stats with current test method being tested
        print(f'{self.seconds:.3f} {cnts} {mbs}MB -- {cls}.{meth}', flush=True)

class ValueError(builtins.ValueError):
    """ An exception raised by test units to indicate that the values in
    the testing environment are invalid.
    """
    pass
