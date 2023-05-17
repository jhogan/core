# vim: set et ts=4 sw=4 fdm=marker

#######################################################################
# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2022
########################################################################

""" This module contains classes that abstract the HTTP protocol, as
well as WSGI and other web technologies.

A major class in this module is the ``browser`` class. This is the
class to use when we need to make HTTP requests to third party services
(see third.py). For most cases, ``browser`` should be used as an
alternative to urllib.request.urlopen() (it currently wraps this call).
A subclass of ``browser`` in tester.py allows unit tests to be written
against pom.page object, effectively making it possible and convenient
to test the web pages exposed by WSGI web application within the
framework.

The ``request`` and ``response`` objects correspond to HTTP request and
response messages. They contain ``headers`` collections which collect
``header`` object that represent HTTP headers. Support for maintaning
cookies within the ``browser`` is provided by the ``cookie`` object.
Exception classes corresponding to HTTP status codes 3xx, 4xx and 5xx
are also provided in this module.
"""

from config import config
from dbg import B, PM
from entities import classproperty
from functools import reduce
from pprint import pprint
import apriori
import auth
import dom
import ecommerce
import entities
import exc
import file
import html
import json
import logs
import orm
import os
import party
import pdb
import pom
import primative
import re
import sys
import textwrap
import traceback

# NOTE Use the following diagram as a guide to determine what status
# code to respond with:
# https://www.loggly.com/blog/http-status-code-diagram/
# (Backup: # https://stackoverflow.com/questions/3297048/403-forbidden-vs-401-unauthorized-http-responses)

# TODO:24129f2a When a request is made, check the `hits` entity to see
# if an IP address has made too many requests in a given timeframe. If
# so, retun a 429 Too Many Requests response. Otherwise, the site is
# vulnerable to anyone using `ab` or `hey`.

class application:
    """ Represents a WSGI application.
    """
    def __init__(self):
        """ Create a WSGI application.
        """
        self.breakonexception = False

        # Clear the request object.
        self.clear()

    def clear(self):
        """ Clear state data currently maintained by the WSGI
        application.
        """
        self._request = None
        self._response = None

    _current = None

    @classmethod
    def _set_current(cls, v):
        cls._current = v

    @classproperty
    def current(cls):
        return cls._current

    @property
    def environment(self):
        """ The WSGI environ dict.

        This corresponds to the ``environ`` parameter in the classic
        WSGI method call defined in PEP 333::

            def simple_app(environ, start_response):
                ...

        For the framework's main implementation of the above method, see
        the ``__call__`` method.

        For more information about the actual environ dict, see:
        https://www.python.org/dev/peps/pep-0333/#environ-variables
        """
        return self._env 

    @environment.setter
    def environment(self, v):
        self._env = v

    @property
    def request(self):
        """ The HTTP request object that this application is currently
        processing.
        """
        if not self._request:
            self._request = request(self)
        return self._request

    @property
    def response(self):
        """ The HTTP response object that this application is currently
        processing.
        """
        return self._response

    @response.setter
    def response(self, v):
        self._response = v

    def demand(self):
        """ Raise an exception if the current state of the WSGI
        application object, or any of its constituents, are invalid.
        """
        if type(self.environment) is not dict:
            # PEP 333 insists that the environs must be a dict. The WSGI
            # server will almost certainly send a dict, but tester.py
            # likes to use its own data structure for this, so make sure
            # it always gives us a dict.
            raise TypeError('Environment must be of type "dict"')

        self.request.demand()
           
    def __call__(self, env, start_response):
        """ The main WSGI method.

        In an actual WSGI environment, this method is called by the WSGI
        server. However, unit tests will invoke this method when testing
        web pages (see tester._browser._request).

        :param: env dict: From the official WSGI documentation: 

            The [env] parameter is a dictionary object, containing
            CGI-style environment variables. This object must be a
            builtin Python dictionary (not a subclass, UserDict or other
            dictionary emulation), and the application is allowed to
            modify the dictionary in any way it desires. The dictionary
            must also include certain WSGI-required variables (described
            in a later section), and may also include server-specific
            extension variables, named according to a convention that
            will be described below."

        :param: start_response callable: A callable defined by the
        WSGI standard to invoke in order to return a response to the
        WSGI server and ultimately the user agent.
        """

        # Set the WSGI environ dict
        self.environment = env

        # Ensure that the GEM has been fully imported
        import apriori; apriori.model()

        break_ = False

        res = None

        sec = orm.security()

        # Back up the existing owner. We will restore it in the
        # `finally` block.
        own = sec.owner

        try:
            # Clear state data currently maintained by the WSGI
            # application.
            self.clear()

            type(self)._set_current(self)

            # Set the owner to anonymous. 
            # TODO This doesn't address how an authenticated user would
            # be set.
            sec.owner = ecommerce.users.anonymous

            # Get a reference to the application HTTP request object
            req = self.request

            ws = self.request.site

            propr = ws.proprietor

            sec.proprietor = propr

            # Raise an exception if the current state of the WSGI
            # application object, or any of its constituents, are
            # invalid.
            self.demand()

            # Make the actual request and get the response object
            res = req()

        except Exception as ex:
            # Log exception to syslog
            logs.exception(ex)

            # If tester.py set the WSGI app to breakonexception.
            if self.breakonexception:
                # Immediatly raise to tester's exception handler.
                break_ = True
                raise

            if not res:
                res = response(req)
                res.headers += 'Content-Type: text/html'

            try:
                if self.request.isxhr:
                    # Create an <article> that explains the exception
                    # and gives traceback information. The article can
                    # be presented to the user (as a modal, for example)
                    # by the JavaScript.
                    res.body = pom.message(ex).html

                    if isinstance(ex, HttpError):
                        res.status = ex.status

                    elif isinstance(ex, HttpException):
                        # Allow the exception to make modifications to
                        # the response.
                        ex(res)

                    else:
                        # Set to the generic 500 status code
                        res.status = InternalServerError.status
                else:
                    # If the exception was an HttpError, i.e, an HTTP
                    # 400s or 500s error...
                    if isinstance(ex, HttpError):
                        # Call the sites error page for the given
                        # status 
                        path = f'/error/{ex.status}'
                        pg = req.site(path)

                        # If the page was provided by the site
                        if pg:
                            # Clear and invoke the page
                            pg.clear()
                            pg(ex=ex)

                            # FIXME:bea5347d Make argument req.language.
                            # Currently it returns None because we don't
                            # use the /files/ prefix to distinguish
                            # between files and pages.
                            request.lingualize('en', pg)

                        # Else if no page was provided by the site
                        else:
                            # Use the default error page, e.g.,
                            # /en/error
                            pg = req.site['error']

                            # TODO This alternative block is redundant
                            # with the consequent block

                            # Clear and invoke
                            pg.clear()
                            pg(ex=ex)

                        # Use the response form the page's invocation to
                        # set the fields of the response object
                        res.body = pg.html
                        res.status = ex.status

                    # If the exception is an HttpException i.e., HTTP
                    # 300s. 
                    elif isinstance(ex, HttpException):
                        # Allow the exception to make modifications to
                        # the response.
                        ex(res)

                    # If the exception was a non-HTTP exception
                    else:
                        # Create a response to report a default 500
                        # Internal Server Error
                        res.status = 500
                        msg = pom.message(ex)

                        # Getting get.page can sometimes raise an error
                        # because it calls req.site which may have
                        # trouble establishing itself if it is not set
                        # up correctly.
                        try:
                            pg = req.page
                        except Exception:
                            # HACK:10d9a676 We shoudn't have to prepend
                            # DOCTYPE here. See TODO:10d9a676.
                            res.body = f'<!DOCTYPE html>\n{msg.html}'
                        else:
                            pg.flash(msg)
                            # HACK:10d9a676 We shoudn't have to prepend
                            # DOCTYPE here. See TODO:10d9a676.
                            res.body = f'<!DOCTYPE html>\n{pg.html}'

            # In there was an exception processing the exception,
            # ensure the response is 500 with a simple error message.
            except Exception as ex:
                res.status = 500
                res.body = pom.message(ex).html

        finally:
            sec.owner = own

            if not break_:
                # Use the WSGI start_response to send the HTTP status
                # and headers back to the browser.
                # TODO Instead of the stock HTTP reason phrase, we could
                # respond with the exception's message here, although
                # the exception message should be delivered somewhere in
                # the payload.
                start_response(res.message, res.headers.list)

                # Return the responses body to the browser in accordance
                # with the WSGI protocol
                return iter([bytes(res)])

            type(self)._set_current(None)

# NOTE The request class tries to be a generic HTTP request class and a
# WSGI request class at the same time. We may want to add a new subclass
# of request call `wsgirequest` that would encapsulate the WSGI logic so
# we can get it out of the regular `request` class.
class request(entities.entity):
    """ Represents an HTTP request.

    The class is designed represent any HTTP request. However, there a
    special consideration made incoming requests in a WSGI context. When
    incoming HTTP request are made to the website, this class will be
    used to encapsulate the request - typically in a WSGI context.
    Alternatively, outgoing reuest, such as those made by the third.py
    module to third party RESTful APIs, will use this class.
    """
    def __init__(self, app=None, url=None):
        """ Construct an HTTP request.

        :param: app application: The WSGI application object for this
        request.

        :param: url www.url: The URL object representing the URL being
        requested.
        """

        if url and not isinstance(url, sys.modules['www'].url):
            raise TypeError(
                'Invalid url type'
            )

        self.app           =  app
        if app:
            self.app._request  =  self

        self._body    =  None
        self._user       =  None
        self._files      =  None
        self._useragent  =  None
        self._hit        =  None
        self._ip         =  None
        self._referer    =  None
        self._headers    =  None
        self._url        =  url
        self._method     =  None
        self._useragent  =  None
        self._site       =  None

    @property
    def forfile(self):
        """ Return True if the request is for a file, False otherwise.

        Most requests will be for a page (a subclass of pom.page) and
        not a file (a subclass of inode.file). When a request is made
        for a page, the `page` class is instantiated and called, and its
        resultant HTML is returned. When a request for a file is made,
        the framework's file system (governed by file.py) will return
        the file's body to the requestor (if it can be found).
        """
        return self.path and not self.page

    @property
    def forpage(self):
        """ If this request is for a page (`pom.page`), return True. If
        it is for a file (file.file) return False.

        See `request.forfile` for more.
        """

        # TODO:bea5347d To distinguish between page and file request, we
        # should at least see if the first element of the path (e.g.,
        # '/en/index') is an ISO language code (probably ISO 639-1)
        # probably using the pycountry package.
        #
        # However, this gets us halfway there. What if there is a
        # directory under public/ called en/. If we wanted to get the
        # file:
        #
        #     GET /en/some.txt
        #
        # this URL would be interpreted as a page request and probably
        # return 404.
        #
        # Testing the Accept request header
        # (https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Accept)
        # and developing a content negotiation strategy
        # (https://developer.mozilla.org/en-US/docs/Web/HTTP/Content_negotiation)
        # may be the solution here.
        return not self.forfile

    def __repr__(self):
        """ A string representation of the HTTP request.
        """
        return str(self)

    def __str__(self):
        """ A string representation of an HTTP request. The string
        should be reminiscent of the text output for a request in a
        browser's "developer tools".
        """

        r = textwrap.dedent(f'''
        Request URL: {self.url}
        :authority: {self.url}
        :method: {self.method}
        :path: {self.url.path}
        :scheme: {self.url.scheme}
        ''')

        r = r.rstrip()

        if self.headers.count:
            r += f'\n{str(self.headers)}'

        ua = self.useragent
        if ua:
            r += f'\n{ua}'

        body = self.body
        if body:
            try:
                # TODO If body is JSON, it should return as dict, so
                # there is no need to call json.loads on it.
                body = json.dumps(json.loads(body), indent=2)
            except:
                pass

            r += f'\n\n{body}'

        return r

    @property
    def headers(self):
        """ Return a collection HTTP headers associated with this
        request. 
        
        Note that WSGI gives us the HTTP headers in its `environ` dict
        where the keys start with 'http_'. This property uses that dict
        to produce headers for that subset. Note that other headers can
        be added at any point.
        """

        if not self._headers:
            self._headers = headers()
            if self.iswsgi:
                for k, v in self.environment.items():
                    if not k.lower().startswith('http_'):
                        continue

                    self._headers += header(k[5:], v)

        return self._headers

    @headers.setter
    def headers(self, v):
        self._headers = v

    @property
    def files(self):
        """ Return a collection of files (``file.files``) that were
        uploaded in the HTTP request.

        Note that currently, a very rough implementation of a
        multipart/form-data parser is implemented. This is used for
        tests but hasn't been tried with real world POSTs (the kind an
        actual browser would send and a real webserver would receive). 

        A future version will parse out the file data that is sent in
        JSON format. This will be the normal way to transfer files to
        the web server from a browser. The multipart/form-data parser is
        just an ad hoc way that some tests are currently using to send
        file data.
        """
        if self._files is not None:
            return self._files

        fs = file.files()

        if self.mime != 'multipart/form-data':
            # Currently, we will only have files in the request if we
            # are using a multipart mime type. This will change once
            # event-based input is complete.
            return fs

        content_type = self.content_type.split(';')

        if len(content_type) < 2:
            raise BadRequestError(
                "Can't find 'boundry' in Content-Type"
            )

        try:
            boundry = bytes(content_type[1].split('=')[1], 'utf-8')
        except Exception as ex:
            raise BadRequestError(
                f"Can't parse boundry ({ex})"
            )

        boundry = '--' + boundry.decode('utf')
        offset = content_type = None
        inp = self.environment['wsgi.input']
        inp.seek(0)
        while True:
            ln = inp.readline()

            if not ln:
                break

            ln = ln.rstrip(b'\n\r')

            if not content_type:
                ln = ln.decode('utf-8')

            if content_type and ln == bytes(boundry, 'utf-8'):
                if offset is not None:
                    tell = inp.tell()
                    size = tell - offset
                    size -= len(boundry) + len('\r\n\r\n')
                    inp.seek(offset)
                    fs += file.file()
                    fs.last.name = filename
                    fs.last.body = inp.read(size)
                    content_type = content_disposition = offset = None
                    inp.seek(tell)

            elif isinstance(ln, bytes):
                continue

            elif ln.startswith('Content-Disposition'):
                parts = ln.split(';')
                content_disposition = parts[0].split(':')[1].strip()
                name = parts[1].split('=')[1].strip()
                filename = parts[2].split('=')[1].strip()

            elif ln.startswith('Content-Type'):
                content_type = ln.split(':')[1].strip()
                ln = inp.readline()
                if ln.strip(b'\n\r'):
                    raise BadRequestError(
                        'Missing empty line'
                    )
                offset = inp.tell()

            self._files = fs
        return fs

    @property
    def cookies(self):
        """ Returns a ``cookies`` collection object containing each of
        the cookies in the HTTP request's 'cookies' header.
        """
        r = browser._cookies()
        for hdr in self.headers:
            if hdr.name != 'cookie':
                continue

            for cookie in hdr.value.split('; '):
                k, v = cookie.split('=')
                r += browser._cookie(k, v, domain=None)
                break
        return r

    @property
    def jwt(self):
        """ Look in the HTTP request's cookies collection for a JWT
        cookie.. If found, convert the JWT cookie's str value to an
        auth.jwt object and return.  If no JWT cookie is found, return
        None.
        """
        jwt = self.cookies('jwt')
        if jwt:
            jwt = jwt.value
            jwt = auth.jwt(jwt)

        return jwt

    @property
    def user(self):
        """ Returns the authenicated user making the request. If there
        is no authenicate user, returns None.
        """

        if not self._user:

            # Get the JWT and convert it to a user 
            jwt = self.jwt

            if jwt:
                if not jwt.isvalid:
                    # If the JWT is bad (can't be decoded), return None.
                    return None
                else:
                    # Load user based on JWT's 'sub' value.  NOTE The
                    # JWT's sub property has a hex str represetation of
                    # the user's id.
                    self._user = ecommerce.user(jwt.sub)

        return self._user

    @user.setter
    def user(self, v):
        self._user = v
                
    @property
    def environment(self):
        """ The WSGI environ dict.

        This corresponds to the ``environ`` parameter in the WSGI method
        call defined in PEP 333::

            def simple_app(environ, start_response):
                ...

        For the framework's main implementation of the above method, see
        ``www.application.__call__``.

        For more information about the actual environ dict, see:
        https://www.python.org/dev/peps/pep-0333/#environ-variables

        Note that this property is similar but not the same as the
        `headers` property.
        """
        return self.app.environment

    @property
    def iswsgi(self):
        """ Returns True if the request is for a WSGI app.

        Typical incoming requests to the framework will be intended for
        the WSGI interface. However, this is a general purpose HTTP
        request object, so for other use cases, this method will return
        False.
        """
        return self.app is not None

    @property
    def servername(self):
        """ The hostname of the URL.

        When the request is for a WSGI app, the value of the SERVER_NAME
        environment varible is returned.
        """
        if self.iswsgi:
            return self.environment['SERVER_NAME']

        return self._url.host

    @property
    def arguments(self):
        """ Returns the query string parameters for this request object
        as a dict.
        """
        import urllib
        d = urllib.parse.parse_qs(self.qs)
        for k, ls in d.items():
            if len(ls) == 1:
                d[k] = ls[0]
                
        return d
                
    @property
    def qs(self):
        """ Returns the query string portion of the URL being requested.

        When the request is for a WSGI app, the value of the
        QUERY_STRING environment varible is returned.

        If there is no query string, None is returned.
        """
        if self.iswsgi:
            qs = self.environment['QUERY_STRING']

            if not qs:
                qs = None

            return qs

        return self._url.query

    @property
    def site(self):
        """ Get the single site (``pom.site``) for this instance.
        """
        if not self._site:
            # Prevent circular importing by importing pom here instead
            # of at the top
            import pom

            ws = None
            try:
                ws = self.environment['HTTP_HOST']
            except KeyError:
                if config().indevelopment:
                    try:
                        # NOTE 'SERVER_SITE' is a contrived, non-HTTP
                        # environment variable used by test scripts to
                        # pass an instances of site objects to use.
                        ws = self.environment['SERVER_SITE']
                    except KeyError:
                        pass
                else:
                    # TODO Raise a useful Exception here if, for some
                    # reason, the user agent doesn't provide an
                    # HTTP_HOST. 
                    ...

            # If ws is a string, look for the website module that
            # matches the string. The website module will have the
            # `site` class, so get that class and use it to instantiate
            # a site object.
            if isinstance(ws, str):
                host, sep, port = ws.partition(':')

                # Split host name on '.'
                hosts = host.split('.')

                # Loop to fallback on less specific domains, i.e, try
                # x.x.example.com, then try x.example.tld, then try
                # example.tld, then raise ModuleNotFoundError none were
                # successfully imported.
                while len(hosts):
                    # Convert host name from . seperate to _ seperated
                    # since modules can't have dots in them (they can,
                    # but it can be problematic).
                    host = '_'.join(hosts)

                    try:
                        # Try to import `host` module
                        mod = __import__(host,  globals(), locals())
                    except ModuleNotFoundError:
                        if len(hosts) > 2:
                            # Pop the first subdomain off the list and
                            # try again
                            hosts.pop(0)
                        else:
                            # There are no subdomains, so accept that we
                            # can't import host
                            raise
                    else:
                        # Instantiate the site object in the host module
                        ws = getattr(mod, 'site')()
                        break

            if isinstance(ws, pom.site):
                self._site =  ws
            else:
                raise TypeError('Invalid site type')

        return self._site

    @property
    def page(self):
        """ Return the page that this request is GETting, POSTing to,
        etc. 
        """
        ws = self.site

        # Get the path with the language code removed
        path = self.getpath()

        try:
            return ws[path]
        except IndexError:
            return None

    @property
    def language(self):
        ''' Return the language code for this request.

        The language code is usually given in the URL:

            https://www.example.com/en/home

        Above, 'en' is the `language` and would be returned.

        For HTTP requests intended to get or retrieve a file, there
        usually would be no language. In that case, None is returned.
        '''

        # Return None if this request is for a file.
        if self.forfile:
            return None

        try:
            # TODO When the language code is not given, Accept-Language
            # can be used to work out the best language.
            segs = [x for x in self.path.split('/') if x]
            if len(segs):
                return segs[0]
        except:
            return 'en'

        # Default to English
        return 'en'

    def __call__(self):
        """ Makes the HTTP request which this `request` object was
        created to make.

        When the request is for a WSGI app, a determination is made as
        to whether the request is for a web page (`pom.page`) or for a
        file in the framework's file system (`file.file').

        If a page is being requested, we pass in the query string
        parameters as arguments to the page. When the page is completed
        processing, the `response` will be returned containing the HTML
        generated by calling the page.

        If a file is being requested, the `response` object will contain
        the data for the file.

        The `response` object will be created here and assigned to the
        global response variable (www.application.current.response)
        making it accessible to all areas of the application (useful to
        `pom.page` objects). 
        """

        # Create the hit log. In the `finally` block, we will add some
        # concluding information to the log (such as the HTTP status
        # code) by calling self.log a second time.
        self.log()

        # If the request is in response to a dom.event, create the
        # eventargs object that will pass the following to the
        # server-side event handler:
        #
        #     hnd: The name of the event handler.
        #
        #     html:  The collection of DOM subtrees that were selected
        #     to be passed to the event handler.
        # 
        #     src: The DOM object, such as the <button> or <input>,
        #     that was the subject of the event.
        #
        #     trigger: The name of the method that caused the event. For
        #     example, if the `click()` method of a <button> caused the
        #     event, trigger would be 'click'.
        #
        res = response(self)
        application.current.response = res

        eargs = None
        if self.isevent:
            # Create an eventargs object given the corresponding data in
            # this request.
            eargs = dom.eventargs(
                hnd      =  self.body['hnd'],
                html     =  self.body['html'],
                src      =  self.body['src'],
                trigger  =  self.body['trigger'],
            )

        try:
            # If the request is for a page (pom.page)
            if self.forpage:
                # Get a reference to the page that this request is
                # targeting.
                pg = self.page

                # Clear the page before we invoke it. This is for when
                # test scripts use the same website object to make
                # subsequent calls to the same page. The website object
                # will use the same page object and the page will
                # raise an exception because it has already been called.
                pg.clear()

                # If we are dealing with a page, the content-type will
                # be text/html.
                res.headers += 'Content-Type: text/html'

                # Call the page passing in the eventargs (if any) and
                # the arguments for the page.
                pg(eargs=eargs, **self.arguments)

                # Get the main SPA application page for the page if
                # there is one.
                if spa := pg.spa:
                    # Clear page. See the comment above on why we clear.
                    spa.clear()

                    # If one exists, call it
                    spa()

                    # Embed the sub page's contents into the SPA pages
                    # <main> tag.
                    spa.main = pg.main

                    # We want to return the SPA page, so make it the
                    # `pg` so its contents will be returned by the
                    # code below.
                    pg = spa

                    # Get the spa pages's path
                    path = spa.path
                elif pg.isspa:
                    # Get the requested page's path
                    path = pg.path
                else:
                    # No data-spa-path because we aren't dealing with a
                    # spa page.
                    path = None

                if path:
                    # Add a data-spa-path to the <main> element
                    path = f'/{self.language}{path}'
                    main = pg['html>body>main'].only
                    main.attributes += 'spa-data-path', path

                lang = self.language

                # Add the language code to any anchors, i.e., add
                # the 'en' to /en/path/to/page.
                self.lingualize(lang, pg)

                if not self.ishead:
                    # If we are processing an event
                    if self.isevent:
                        # If that event is for a "page" change in an SPA
                        if self.isspa:
                            # Set the outer HTML of the page's <main>
                            # element to the response's body
                            res.body = pg.main.html
                        else:
                            # If this is for a regular event, assigned
                            # the eventarg's HTML to the response body.
                            # Presumably, this eventarg was modified by
                            # the above call to pg.
                            if eargs.html:
                                self.lingualize(lang, eargs.html)
                                res.body = eargs.html.html
                    else:
                        # HACK:10d9a676 We shoudn't have to prepend
                        # DOCTYPE here. See TODO:10d9a676.
                        res.body = f'<!DOCTYPE html>\n{pg.html}'

            elif self.forfile:
                # ... if the request is for a file from the framework's
                # file system.
                path = None
                path = self.path
                pub = self.site.public

                try:
                    # Try to get the file from the website's public
                    # directory
                    file = pub[path]
                except Exception as ex:
                    # Raise a 404 if not found
                    raise NotFoundError(path) from ex
                else:
                    # On success, use the file's mimetpe fo the
                    # respones's Content-Type header.
                    res.headers += 'Content-Type: ' + file.mime

                    if not self.ishead:
                        # Assign the file data to the response object
                        res.body = file.body
            else:
                # This should never happen
                raise ValueError(
                    'Request is neither for a page or a file'
                )

        except HttpError as ex:
            # Set the responses status to the exception's status. 
            res.status = ex.status

            # If the page raised an HTTPError with a flash message, add
            # the flash message to the page's HTML.

            if self.forpage and ex.flash:
                self.page.flash(ex.flash)
                res.body = pg.main.html
            else:
                raise

        finally:
            # Finish of the hit log
            self.log()

        # Return the response object
        return res

    @staticmethod
    def lingualize(lang, e):
        """ Iterate over the each anchor tag under `e` and ensure
        that `lang` is prepended to each anchor's HREF.

            # Assuming `lang` is 'en'
            assert lang == 'en'

            # An anchor befor lingualization
            <a href="/some/path">link</a>

            # An anchor after lingualization
            <a href="/en/some/path">link</a>

        Note that this method is idempotent, i.e., calling it multiple
        times has the same effect on the `page` object as calling it
        once.

        :param: lang str: The two character language code to use.

        :param: e dom.element: The element to lingualize.
        """
        for a in e['a']:
            # If the anchor has already been lingualized
            if a.href.startswith(f'/{lang}/'):
                continue

            href  =  a.href
            sep   =  os.path.sep
            a.href = os.path.join(
                sep, lang, href.lstrip(sep)
            )

    @property
    def hit(self):
        """ Return the ``hit`` entity. If it does not yet exist for this
        request, create it.
        """
        if not self._hit:
            # Create the hit entity. No need to save it at the moment.

            try:
                path = self.page.path
            except:
                path = self.path

            self._hit = ecommerce.hit(
                path       =  path,
                isxhr      =  self.isxhr,
                qs         =  self.qs,
                method     =  self.method,
                site       =  self.site,
                language   =  self.language,
                ip         =  self.ip,
                size       =  self.size,
            )

            # Conditionally assign these hit attributes because of
            # 6028ce62
            if ref := self.referer:
                self._hit.url = ref

            if ua := self.useragent:
                self._hit.useragent = ua

            if self.jwt:
                self._hit.isjwtvalid = self.jwt.isvalid
            else:
                self._hit.isjwtvalid = None

        return self._hit

    def log(self):
        """ Log the hit.
        """
        try: 
            with orm.sudo():
                # Get the request's ``hit`` entity
                hit = self.hit

                par = None

                # Get the user's party. If no user is logged in, use the
                # anonymous user.
                if self.user:
                    par = self.user.party
                    hit.user = self.user
                else:
                    par = party.parties.anonymous

                if par is None:
                    par = party.parties.anonymous

                # Get the party's visitor role
                visitor = par.visitor

                # Get the party's visitor role's current visit
                visit = visitor.visits.current

                # Get the current time in UTC
                now = primative.datetime.utcnow()

                # Create a new ``visit`` if a current one doesn't not exist
                if not visit:
                    visit = ecommerce.visit(
                        begin = now
                    )
                    visitor.visits += visit

                # If the hit is new, the begin date will be None meaning it
                # is not ``inprogress``. If that's the case, set the begin
                # date. Otherwise, we can conclude the hit with the end
                # datetime and HTTP status.
                if hit.inprogress:
                    hit.end = now
                    hit.status = self.app.response.status
                else:
                    hit.begin = now

                hit.visit = visit

                # Create/update the hit
                hit.save()
        except Exception as ex:
            # Failing to log a hit shouldn't stop page invocation.
            # Instead we log the failure to the syslog.

            # NOTE Write code here that can't raise an another exception
            try:
                ua = str(self.environment['USER_AGENT'])
            except:
                ua = str()

            try:
                ip = str(self.environment['REMOTE_ADDR'])
            except:
                ip = str()

            msg = f'{ex}; ip:{ip}; ua:"{ua}"'

            logs.exception(msg)

    @property
    def body(self):
        """ Returns the HTTP message body of the request.

        https://en.wikipedia.org/wiki/HTTP_message_body
        """

        if self._body is None:
            # If the body hasn't been set, we can get it from the
            # WSGI environment.
            if self.iswsgi:
                sz = self.size
                inp = self.environment['wsgi.input']
                if self.mime == 'multipart/form-data':
                    # Normally, the client won't need to get the body
                    # for multipart data; it will usually just use
                    # `request.files`. Either way, return whan we have.

                    # NOTE: We probably shouldn't memoize it since it
                    # could be holding a lot of file data.
                    inp.seek(0)

                    return inp.read(sz)
                elif self.mime == 'application/x-www-form-urlencoded':
                    self._body = inp.read(sz).decode('utf-8')

                elif self.mime == 'application/json':
                    self._body = inp.read(sz).decode('utf-8')
                    self._body = json.loads(self._body)
                else:
                    # NOTE This block doesn't appear to be used at the
                    # moment
                    self._body = inp.read(sz)

        return self._body

    @body.setter
    def body(self, v):
        self._body = v

    @property
    def path(self):
        """ Corresponds to the WSGI PATH_INFO environment variable:

        PATH_INFO
            The remainder of the request URL's "path", designating the
            virtual "location" of the request's target within the
            application. This may be an empty string, if the request URL
            targets the application root and does not have a trailing
            slash.
        """
        if self.iswsgi:
            path = self.environment['PATH_INFO']
            if path == '/':
                path = '/en/index'
            return path

        return self._url.path


    def getpath(self, lang=False):
        """ Get the path. By default get the path with the language code
        removed.

        Usually, if you want the path, you would just call the
        `request.path` @property. However, that property returns the
        path with the language code. `getpath` is useful for when you
        want the language code removed.

        :param: lang bool: If True, preserve the language code in the
        path. If False, remove the language code before returning.
        """
        path = self.path
        if lang:
            return path

        return type(self.site)._strip(path)

    @property
    def size(self):
        """ The contents of any Content-Length fields in the HTTP
        request. If empty, return 0. In non-WSGI requests, returns the
        length of the body.
        """
        if self.iswsgi:
            try:
                return int(self.environment.get('CONTENT_LENGTH', 0))
            except ValueError:
                return 0

        # NOTE This appears to be ambiguous. In the WSGI version,
        # shouldn't we also be returning the size of the body.

        return len(self.body)

    @property
    def class_(self):
        cls = self.data['_class'] 
        return reduce(getattr, cls.split('.'), sys.modules['ctrl'])

    @property
    def postmethod(self):
        # NOTE This is the "method" used in POSTs. It's not the request
        # method (post, get, head, etc). The request method is found at
        # `request.method`
        return post['_method']

    @property
    def method(self):
        """ Returns the HTTP verb, such as GET, POST, PATCH, etc, used
        in the HTTP request.
        """
        if self.iswsgi:
            return self.environment['REQUEST_METHOD'].upper()
        
        if self._method:
            return self._method.upper()

        return None

    @method.setter
    def method(self, v):
        self._method = v

    @property
    def ip(self):
        """ Returns an ``ecommerce.ip`` address object corresponding to
        the REMOTE_ADDR WSGI environment variblable.
        """
        if not self._ip:
            ip = self.environment['REMOTE_ADDR']

            # REMOTE_ADDR will be empty when using a reverse proxy like
            # Nginx. If that's the case, fall back on
            # HTTP_X_FORWARDED_FOR. NOTE This is true when using UNIX
            # sockets. It's not clear to me what REMOTE_ADDR would be if
            # Gunicorn were listening on an IP socket. From Gunicorn's
            # documentation, it would likely be the the IP of the Nginx
            # proxy Thus the following logic would need to change if,
            # for some reason, we switch from UNIX to IP sockets.
            if not ip:
                try:
                    ip = self.environment['HTTP_X_FORWARDED_FOR']
                except:
                    ip = str()
            self._ip = ecommerce.ip(address=ip)
        return self._ip

    @property
    def referer(self):
        """ Returns an ``ecommerce.url`` object corresponding to the
        HTTP_REFERER of the HTTP request.
        """
        if not self._referer:
            try:
                url = self.environment['HTTP_REFERER']
            except KeyError:
                return None
            except Exception as ex:
                logs.exception(f"Can't get HTTP_REFERER: {ex}")
            else:
                url = str(url)

            self._referer = ecommerce.url(address=url)
        return self._referer

    @property
    def useragent(self):
        """ Returns an ``ecommerce.useragent`` object corresponding to
        the USER_AGENT HTTP environment variable for this HTTP request.
        """
        if not self._useragent:
            if self.iswsgi:
                try:
                    ua = str(self.environment['USER_AGENT'])
                except KeyError:
                    return None
                except Exception as ex:
                    logs.exception(f"Can't get USER_AGENT: {ex}")
                else:
                    ua = str(ua)

                self._useragent = ecommerce.useragent(string=ua)
        return self._useragent

    @property
    def scheme(self):
        """ Return the scheme for the request, e.g., http, https, etc.
        """
        if self.iswsgi:
            return self.environment['wsgi.url_scheme'].lower()

        import urllib
        return urllib.parse.urlparse(str(self._url)).scheme

    @property
    def port(self):
        """ Return the TCP port for the request, e.g., 80, 8080, 443.
        """
        if self.iswsgi:
            return int(self.environment['SERVER_PORT'])

        return self._url.port

    @property
    def url(self):
        """ Return a www.url object representing the target URL of the
        this `request`.
        """

        if not self._url:
            self._url = url()

        self._url.scheme = self.scheme
        self._url.host = self.servername
        self._url.port = self.port
        self._url.path = self.path
        self._url.query = self.qs

        return self._url

    @property
    def isget(self):
        """ Returns True if the request's HTTP method is GET.
        """
        return self.method == 'GET'

    @property
    def ispost(self):
        """ Returns True if the request's HTTP method is POST.
        """
        return self.method == 'POST'

    @property
    def ishead(self):
        """ Returns True if the request's HTTP method is HEAD.
        """
        return self.method == 'HEAD'

    @property
    def isxhr(self):
        """ Returns True if request is intended as an XMLHttpRequest
        (XHR).
        """
        return self.content_type == 'application/json'

    @property
    def content_type(self):
        """ Return the Content-Type of the request.
        """
        # TODO This should check self.headers['content-type'] if it
        # can't be found in the WSGI environment.
        try:
            return self.environment['CONTENT_TYPE'].strip()
        except KeyError:
            return None

    @property
    def mime(self):
        """ Return the mime type of the request.
        """
        return self.content_type.split(';')[0].strip().lower()

    @property
    def isevent(self):
        """ Returns True if this ``_request`` is an XHR request for a
        dom.event, such as a <button> being clicked. Returns False if
        the request is a non-dom.event, such as a conventional HTTP GET,
        POST, etc.
        """

        # dom.events are encoded as JSON
        if not self.content_type == 'application/json':
            return False

        if not isinstance(self.body, dict):
            return False

        # A dom.event would specify the name of an event handler (hnd)
        # in its request body.
        try:
            self.body['hnd']
        except:
            # If there is any issue, like a KeyError, then it's not an
            # event.
            return False
        else:
            return True
            
    @property
    def isspa(self):
        """ Returns True if this ``_request`` is an XHR request for
        an SPA subpage. 
        """
        if not self.isevent:
            return False

        return self.body['hnd'] is None

    # TODO Rename to '_demand' since this is a private method
    def demand(self):
        """ Causes an exception to be raised if the request is not
        complete or is incorrectly constructed.
        """

        if request.forfile:
            pass

        elif not request.page:
            # If the site associated with the request doesn't have a page in
            # its index, raise a 404
            raise NotFoundError(self.path)

        if self.isget or self.ishead:
            if not len(self.path):
                raise www.BadRequestError('No path was given.')
            
        elif self.ispost:
            if self.mime == 'text/html' and len(self.body) == 0:
                raise BadRequestError('No data in body of request message.')

            if self.mime == 'multipart/form-data':
                if self.files.isempty:
                    raise BadRequestError(
                        'No files given in multipart form.'
                    )

            # The remaining demands will be for XHR requests only
            if not self.isxhr:
                return

            # The remaining demands will be for non-event XHR requests
            # only
            if self.isevent:
                return

            try:
                post = self.post
            except json.JSONDecodeError as ex:
                raise www.BadRequestError(str(ex))

            try:
                cls = post['_class']
            except KeyError:
                raise NotFoundError('The class value was not supplied')

            try:
                meth = self.postmethod
            except KeyError:
                raise ValueError('The method value was not supplied')

            if meth[0] == '_':
                raise www.ForbiddenError('Invalid method.')

            try:
                import ctrl
            except ImportError as ex:
                raise ImportError('Error importing controller: ' + str(ex))

        else:
            raise MethodNotAllowedError(
                'Method "%s" is never allowed' % self.method
            )

class response(entities.entity):
    Messages = {
        200: 'OK',
		201: 'Created',
		202: 'Accepted',
		203: 'Non-Authoritative Information',
		204: 'No Content',
		205: 'Reset Content',
		206: 'Partial Content',
		207: 'Multi-Status',
		208: 'Already Reported',
		226: 'IM Used',

		300: 'Multiple Choices',
		301: 'Moved Permanently',
		302: 'Found',
		303: 'See Other',
		304: 'Not Modified',
		305: 'Use Proxy',
		306: 'Switch Proxy',
		307: 'Temporary Redirect',
		308: 'Permanent Redirect',

		400: 'Bad Request',
		401: 'Unauthorized',
		402: 'Payment Required',
		403: 'Forbidden',
		404: 'Not Found',
		405: 'Method Not Allowed',
		406: 'Not Acceptable',
		407: 'Proxy Authentication Required',
		408: 'Request Timeout',
		409: 'Conflict',
		410: 'Gone',
		411: 'Length Required',
		412: 'Precondition Failed',
		413: 'Payload Too Large',
		414: 'URI Too Long',
		415: 'Unsupported Media Type',
		416: 'Range Not Satisfiable',
		417: 'Expectation Failed',
		418: 'I\'m a teapot',
		421: 'Misdirected Request',
		422: 'Unprocessable Entity',
		423: 'Locked',
		424: 'Failed Dependency',
		425: 'Too Early',
		426: 'Upgrade Required',
		428: 'Precondition Required',
		429: 'Too Many Requests',
		431: 'Request Header Fields Too Large',
		451: 'Unavailable For Legal Reasons',

		500: 'Internal Server Error',
		501: 'Not Implemented',
		502: 'Bad Gateway',
		503: 'Service Unavailable',
		504: 'Gateway Timeout',
		505: 'HTTP Version Not Supported',
		506: 'Variant Also Negotiates',
		507: 'Insufficient Storage',
		508: 'Loop Detected',
		510: 'Not Extended',
		511: 'Network Authentication Required',

		# The following codes are not specified by any standard. 
		103: 'Checkpoint',
		218: 'This is fine',
		419: 'Page Expired',
		420: 'Method Failure',
		420: 'Enhance Your Calm',
		430: 'Request Header Fields Too Large',
		450: 'Blocked by Windows Parental Controls',
		498: 'Invalid Token',
		499: 'Token Required',
		509: 'Bandwidth Limit Exceeded',
		529: 'Site is overloaded',
		530: 'Site is frozen',
		598: 'Network read timeout error',

        # Microsoft's Internet Information Services web server expands
        # the 4xx error space to signal errors with the client's
        # request. 
		440: 'Login Time-out',
		449: 'Retry With',

        # The nginx web server software expands the 4xx error space to
        # signal issues with the client's request.
		444: 'No Response',
		494: 'Request header too large',
		495: 'SSL Certificate Error',
		496: 'SSL Certificate Required',
		497: 'HTTP Request Sent to HTTPS Port',

        # Cloudflare's reverse proxy service expands the 5xx series of
        # errors space to signal issues with the origin server.[90] 
		520: 'Web Server Returned an Unknown Error',
		521: 'Web Server Is Down',
		522: 'Connection Timed Out',
		523: 'Origin Is Unreachable',
		524: 'A Timeout Occurred',
		525: 'SSL Handshake Failed',
		526: 'Invalid SSL Certificate',
		527: 'Railgun Error',

        # Amazon's Elastic Load Balancing adds a few custom 4xx return
        # codes 
		460: '',
		463: ''
    }

    def __init__(self, req, res=None, ex=None):
        """ Create an HTTP response.

        :param: req www.request: The www.request object that resulted in
        this response.

        :param: res urllib.response: The response object from
        urllib.request.urlopen(). This response object (self) will wrap
        ``res``, making things more convenient for the user of
        www.response.

        :param: ex Exception: If the HTTP response is the result of an
        Exception, ``ex`` can be passed in. If it contains the status
        code, that status code will be used for the respones's
        ``status`` property.
        """
        self._body = None
        self._html = None
        self._status = 200
        self._page = None
        self.request = req
        self._headers = headers()
        self._response = res

        if res:
            self.status = res.status
            self.body = res.read()
            self.headers = res.headers

        if ex:
            try:
                st = ex.status
            except AttributeError:
                self.status = 500
            else:
                self.status = st

            body = None
            try:
                body = ex.read()
            except AttributeError:
                pass
            else:
                self.body = body

            try:
                hdrs = ex.headers
            except AttributeError:
                pass
            else:
                self.headers = hdrs
    @property
    def status(self):
        """ The HTTP status code of the response.
        """
        return int(self._status)

    @status.setter
    def status(self, v):
        self._status = v

    @property
    def message(self):
        """ Returns a string containing the HTTP status code of the
        response and the standard message/phrase corresponding to the
        status code.
        """
        try:
            return '%i %s' % (self.status, self.Messages[self.status])
        except KeyError:
            return str(self.status)

    # TODO Rename to content_type to reflect hyphen put in the header
    # Content-Type
    @property
    def contenttype(self):
        """ The content type of the body.
        """
        # TODO This should probably be renamed to content_type to match
        # the request class's property.
        return self.headers['Content-Type']

    @property
    def mime(self):
        """ Returns the **type** and **subtype** portion of the mime.
        For example, if ``self.contenttype`` is:
                
            text/html; charset=UTF-8

        only the string 'text/html' will be returned.
        """
        ct = self.contenttype
        if ct:
            return ct.split(';')[0].lower()
        return None

    @property
    def mimetype(self):
        """ Returns the **type** portion of the mime string. For
        example, if ``self.mime`` is:
                
            image/jpeg

        only the string 'image' will be returned.
        """
        mime = self.mime
        if mime:
            return mime.split('/')[0]
        return None

    @property
    def body(self):
        """ Returns the body of the response.
        """
        # These lines are for XHR responses
        # body = json.dumps(body)
        # body = bytes(body, 'utf-8')

        if isinstance(self._body, str):
            if self._body:
                if not self._body.endswith('\n'):
                    # Ensure a newline is at the end of the response
                    # body simply to make working with tools like the
                    # `curl` command more convenient.
                    self._body += '\n'

        return self._body

    @body.setter
    def body(self, v):
        if self._body != v:
            if isinstance(v, bytes) and self.mimetype == 'text':
                self._body = v.decode('utf-8')
            else:
                self._body = v
            self._html = None

    @property
    def json(self):
        """ If the body is a JSON string, returns a Python list
        representing the JSON document. An exception will be raised if
        the body cannot be deserialized as a JSON document.
        """
        return json.loads(self.body)

    @property
    def html(self):
        """ Returns a dom.elements collection representing the HTML in
        the body.
        """
        # TODO If the body is not HTML (perhaps it's JSON or the
        # content-type isn't HTML), we should probably raise a
        # ValueError.
        if self._html is None:
            self._html = dom.html(self.body)

        return self._html

    def __getitem__(self, sels):
        """ Returns the portion of the response body corresponding to
        the selector (``sels``).

        :param: sels str: If the body contains JSON data, the ``sels``
        parameter should be a string used to select from the list
        returned by json.loads. For example, the following are the
        same::
            
            self['MySelector']
            json.loads(self.body)['MySelector']

        When the body contains HTML, the select should be a CSS3
        selector::

            # Select all <p> tags
            ps = self['p']

            # Select all <em>'s elements in <span> element with a class
            # of 'my-class'
            ems = self['span.my-class em']
        """
        if self.mime == 'application/json':
            return self.json[sels]
        elif self.mime == 'text/html':
            return self.html[sels]
        else:
            raise ValueError(
                'Cannot __getitem__ from www.response with mime type '
                f'of "{self.mime}"'
            )

    @property
    def headers(self):
        """ Returns the ``headers`` collection object associated with
        this HTTP response.
        """
        # If self._headers is not an instance of `headers`, coerse to
        # the native type.
        if not isinstance(self._headers, headers):
            self._headers = headers(self._headers)

        self._headers['Content-Length'] = len(bytes(self))
        
        # if XHR
        '''
        hdrs.append(
            ('Content-Type', 'application/json'),
            ('Access-Control-Allow-Origin', '*')
        )
        '''

        return self._headers

    @headers.setter
    def headers(self, v):
        self._headers = v

    def __bytes__(self):
        """ Returns the `body` of this `respones` converted to a `bytes`
        object.
        """

        # Get the body
        body = self.body

        if not body:
            # If self is a response to a HEAD request, body will be
            # None, so assign empty str for the bytes() function below.
            body = ''

        if isinstance(body, bytes):
            # If body is already a bytes object, just return it
            return body
        else:
            # Assume body is a UTF-8 str
            return bytes(body, 'UTF-8')

    def __repr__(self, pretty=False):
        """ Returns a string representation of this HTTP response
        object.

        :param: pretty bool: If True, prettifies the body if the
        body is JSON or HTML.
        """

        # TODO Shouldn't ``pretty`` default to True?

        r = textwrap.dedent('''
        URL:    %s
        Method: %s
        Status: %s

        %s
        ''')

        body = self.body
        if pretty:
            if self.mime == 'application/json':
                body = json.dumps(json.loads(body), indent=4)
            elif self.mime == 'text/html':
                body = dom.html(self.body).pretty 

        return r % (
            self.request.path,
            self.request.method,
            self.message,
            body,
        )

    def __str__(self):
        """ Returns a string representation of this HTTP response
        object.
        """
        return self.__repr__(pretty=True)

class HttpException(Exception):
    """ An abstract class for HTTP Exception. 
    
    Direct subclasses of ``HttpException`` are those that represent
    status codes in the 300s.  ``HttpError`` is also a subclass of
    ``HttpException``. Its subclasses represent status codes in the 400s
    and 500s. Thus, an ``HttpException`` is not necessarily
    representative of an error; it represents any *exceptional*
    response, like a 301 Moved Premanently, 404 Not Found or a 500
    Internal Server Error.
    """
    def __init__(self, msg, res=None):
        super().__init__(msg)
        self.response = res

    @classmethod
    def create(cls, msg, res, _atop=True):
        """ Creates and returns a subclass of ``cls`` that corresponds
        to thet HTTP ``status`` property in ``res``. 

        It's usually best to call ``create`` off the HttpException
        class::
            
            HttpException.create(msg, res)

        This ensures that all direct and indirect subclasses are tested.
        However, it is possible to limit the scope to the descendents of
        a particular subclass::

            HttpError.create(msg, res)

        :param: msg str: The error message for the exception.

        :param: res www.response: The HTTP response object.

        :param: _atop bool: Since ``create`` is a recursive method,
        ``atop`` is used internally to determine when the method is at
        the top of the recursion stack.
        """
        for sub in cls.__subclasses__():
            
            # Recurse
            ex = sub.create(msg, res, _atop=False)

            # Return if the sub was able to create one
            if ex:
                return ex

            try:
                st = sub.status
            except AttributeError:
                continue
            else:
                if res.status == st:
                    return sub(msg=msg, res=res)

        # If we are at the top call of this recursive method...
        if _atop:
            
            # If we are here, then recursing through the subclasses did
            # not result in the discovery of the correct exception
            # class. Therefore, just fall back on the genereic HTTP 500
            # InternalServerError.
            return InternalServerError(res=res)

        return None

    @property
    def phrase(self):
        """ Returns a string with the status code and the standard HTTP
        phrase for the error message, e.g.: '404 Not Found'.
        """
        return '%s %s' % (
            str(self.status), response.Messages[self.status]
        )

    @property
    def message(self):
        """ Returns the string given to as the ``msg`` in during
        instantiation::

            msg = 'Cannot brew'
            ex = ImATeapotError(msg=msg)
            assert ex.message == msg
        """
        return str(self)

    def __call__(self, res):
        raise NotImplementedError(
            'Processing for HTTP %s not implemented' % self.status
        )

class HttpError(HttpException):
    """ The abstract class for HTTP errors.

    Subclasses of HttpError correspond to client errors (400–499) and
    server errors (500–599).
    """
    def __init__(self, msg=None, flash=None, res=None):
        """ Creates an HttpError instance.

        :param: msg str: The error message.

        :param: flash str: A message intended to be flashed to the user
        explaining the error.

        :param: res www.response: The ``response`` corresponding to this
        HttpError.
        """
        self.flash = flash
        msg0 = self.phrase
        if msg:
            msg0 += ' - ' + msg

        super().__init__(msg=msg0, res=res)

class MultipleChoicesException(HttpException):
    status = 300

class MovedPermanentlyException(HttpException):
    status = 301

class FoundException(HttpException):
    def __init__(self, location):
        self.location = location
    
    status = 302

    def __call__(self, res):
        res.headers['Location'] = self.location
        res.status = 302

class SeeOtherException(HttpException):
    status = 303

class NotModifiedException(HttpException):
    status = 304

class UseProxyException(HttpException):
    status = 305

class SwitchProxyException(HttpException):
    status = 306

class TemporaryRedirectException(HttpException):
    status = 307

class PermanentRedirectException(HttpException):
    status = 308

class BadRequestError(HttpError):
    status = 400

class UnauthorizedError(HttpError):
    """ The HTTP 401 Unauthorized client error status response code
    indicates that the request has not been applied because it lacks
    valid authentication credentials for the target resource.

    This status is sent with a WWW-Authenticate header that contains
    information on how to authorize correctly.

    https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/401
    """

    # TODO As the documentation above states, we may want to set the
    # WWW-Authenticate header.
    # (https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/WWW-Authenticate)

    status = 401

class PaymentRequiredError(HttpError):
    status = 402

class ForbiddenError(HttpError):
    status = 403

class NotFoundError(HttpError):
    def __init__(self, resource, msg=None):
        self.resource = resource
        super().__init__(msg)

    status = 404

    @property
    def message(self):
        return str(self) + '"%s"' % str(self.resource)

class MethodNotAllowedError(HttpError):
    status = 405

class NotAcceptableError(HttpError):
    status = 406

class ProxyAuthenticationRequiredError(HttpError):
    status = 407

class RequestTimeoutError(HttpError):
    status = 408

class ConflictError(HttpError):
    status = 409

class GoneError(HttpError):
    status = 410

class LengthRequiredError(HttpError):
    status = 411

class PreconditionFailedError(HttpError):
    status = 412

class PayloadTooLargeError(HttpError):
    status = 413

class URITooLongError(HttpError):
    status = 414

class UnsupportedMediaTypeError(HttpError):
    status = 415

class RangeNotSatisfiableError(HttpError):
    status = 416

class ExpectationFailedError(HttpError):
    status = 417

class ImATeapotError(HttpError):
    status = 418

class PageExpiredError(HttpError):
    status = 419

class EnhanceYourCalmError(HttpError):
    status = 420

class MisdirectedRequestError(HttpError):
    status = 421

class UnprocessableEntityError(HttpError):
    status = 422

class LockedError(HttpError):
    status = 423

class FailedDependencyError(HttpError):
    status = 424

class TooEarlyError(HttpError):
    status = 425

class UpgradeRequiredError(HttpError):
    status = 426

class PreconditionRequiredError(HttpError):
    status = 428

class TooManyRequestsError(HttpError):
    status = 429

class RequestHeaderFieldsTooLargeError(HttpError):
    status = 430

class RequestHeaderFieldsTooLargeError(HttpError):
    status = 431

class LoginTimeoutError(HttpError):
    status = 440

class NoResponseError(HttpError):
    status = 444

class RetryWithError(HttpError):
    status = 449

class BlockedByWindowsParentalControlsError(HttpError):
    status = 450

class UnavailableForLegalReasonsError(HttpError):
    status = 451

class Error(HttpError):
    status = 460

class Error(HttpError):
    status = 463

class RequestHeaderTooLargeError(HttpError):
    status = 494

class SSLCertificateError(HttpError):
    status = 495

class SSLCertificateRequiredError(HttpError):
    status = 496

class HTTPRequestSentToHTTPSPortError(HttpError):
    status = 497

class InvalidTokenError(HttpError):
    status = 498

class TokenRequiredError(HttpError):
    status = 499

class InternalServerError(HttpError):
    status = 500

class NotImplementedError(HttpError):
    status = 501

class BadGatewayError(HttpError):
    status = 502

class ServiceUnavailableError(HttpError):
    status = 503

class GatewayTimeoutError(HttpError):
    status = 504

class HTTPVersionNotSupportedError(HttpError):
    status = 505

class VariantAlsoNegotiatesError(HttpError):
    status = 506

class InsufficientStorageError(HttpError):
    status = 507

class LoopDetectedError(HttpError):
    status = 508

class BandwidthLimitExceededError(HttpError):
    status = 509

class NotExtendedError(HttpError):
    status = 510

class NetworkAuthenticationRequiredError(HttpError):
    status = 511

class WebServerReturnedanUnknownError(HttpError):
    status = 520

class WebServerIsDownError(HttpError):
    status = 521

class ConnectionTimedOutError(HttpError):
    status = 522

class OriginIsUnreachableError(HttpError):
    status = 523

class ATimeoutOccurredError(HttpError):
    status = 524

class SSLHandshakeFailedError(HttpError):
    status = 525

class InvalidSSLCertificateError(HttpError):
    status = 526

class RailgunError(HttpError):
    status = 527

class SiteIsOverloadedError(HttpError):
    status = 529

class SiteIsFrozenError(HttpError):
    status = 530

class NetworkReadTimeoutError(HttpError):
    status = 598

class headers(entities.entities):
    """ A collection of HTTP headers. 
    
    Headers are components of HTTP requests and responses messages and,
    therefore, are constiuents of the ``request`` and ``response``
    objects (viz. www.request.headers and www.response.headers).
    """
    def __init__(self, *args, **kwargs):
        """ Creates a `headers` collection.

        :param: d sequence: There are a number of ways to initialize the
        headers collection. For example, the following produces the same
        headers collection:

            # list<tuple>
            hdrs = headers([
                ('Content-Type', 'application/json'), 
                ('Accept-Encoding', 'gzip, deflate, br')
            ])

            # tuple<tuple>
            hdrs = headers((
                ('Content-Type', 'application/json'), 
                ('Accept-Encoding', 'gzip, deflate, br')
            })

            # dict
            hdrs = headers({
                'Content-Type': 'application/json',
                'Accept-Encoding': 'gzip, deflate, br'
            })

            # headers
            hdrs = headers(headers([
                ('Content-Type', 'application/json'), 
                ('Accept-Encoding', 'gzip, deflate, br')
            ]))

        :param: kwargs dict: You can also use **kwargs::

            hdrs = headers(
                content_type = 'application/json',
                accept_encoding': 'gzip, deflate, br'
            )

            Note that content_type and accept_encoding will be converted
            to content-type and accept-encoding. If you really want an
            underscore, use the sequence arguments as described above.

            You can mix the sequence arguments with the kwargs as well.
            hdrs = headers(
                (('Content_Type, 'application/json'))
                accept_encoding': 'gzip, deflate, br'
            )
        """

        # If the first argument is another instance of `headers`,
        # convert it to a list<tuple> and populate this instance with
        # its values just as if we were given a list<tuple>.
        try:
            hdrs = args[0]
        except IndexError:
            pass
        else:
            if isinstance(hdrs, headers):
                args = [hdrs.list]

        args = list(args)
        try:
            d = args.pop(0)
            try:
                d = dict(d)
            except KeyError:
                pass
        except IndexError:
            d = dict()

        for k, v in kwargs.items():
            # kwargs can't use hyphens, so we will interpret underscores
            # as hyphens since that is conventionaly how headers names
            # are seperated.
            k = k.replace('_', '-')
            d.update({k: v})

        super().__init__(*args)
        for k, v in d.items():
            self += header(k, v)
            
    def __setitem__(self, ix, v):
        """ If ix is a str, allows for indexer notation to set a headers
        value::

            hdrs = headers()
            assert hdrs.count == 0

            hdrs['Content-Type'] == 'text/html'

            assert hdrs.count == 1

            assert hdrs['Content-Type'] == 'text/html'

        If ix is not a str, default indexer logic is used::

            assert hdrs[0].name == 'Content-Type'
            assert hdrs[0].value == 'text/html'

        NOTE The implementation looks a little buggy. See the TODO's if
        the above explanations is inaccurate.
        """
        if isinstance(ix, int):
            for i, hdr in self.enumerate():
                if i == ix:
                    hdr.value = v
                    break
            else:
                raise IndexError(
                    f'Index out of range: {ix}'
                )
        else:
            for hdr in self:
                if hdr.name.casefold() == ix.casefold():
                    hdr.value = v
                    break
            else:
                self += header(ix, v)

    def __getitem__(self, ix):
        """ Provides indexer logic for the ``headers`` class. See the
        docstring at __setitem__ for details.
        """
        if not isinstance(ix, str):
            return super().__getitem__(ix)

        for hdr in self:
            if hdr.name.casefold() == ix.casefold():
                return hdr.value
        return None

    def append(self, obj, uniq=False):
        """ Allows colon seperate strings to be appended as new
        ``header`` objects::

            hdrs = headers()

            # Call append() using += operator
            hdrs += 'Content-Type: text/html'  
            
            assert hdrs.first.name == 'Content-Type'
            assert hdrs.first.value == 'text/html'

        :param: obj str|header: The header to append. The header can be
        a ``header`` object or a string as described above.

        :param: uniq bool: Only append the header if it is unique.
        """
        if isinstance(obj, str):
            kvp = [x.strip() for x in obj.partition(':') if x != ':']
            if len(kvp) != 2:
                raise ValueError(
                    'Headers must be colon seperate KVPs'
                )
            return self.append(header(*kvp))

        super().append(obj=obj, uniq=uniq)

    @property
    def list(self):
        """ Returns the headers in this collection as a list() object.
        Each entry in the list is a tuple containing the header's name
        and value::

            [
                ('Content-Type', 'text/html'),
                ('Referer', 'https://en.wikipedia.org/wiki/Hypertext_Transfer_Protocol')
            ]
        """
        r = list()
        for hdr in self:
            r.append(hdr.tuple)
        return r

    @property
    def dict(self):
        """ Returns the headers in this collection as a dict() object.
        Each entry in the dict has for its key the name of the header,
        and for its value the value of the header::

            {
                'Content-Type': 'text/html',
                'Referer': 'https://en.wikipedia.org/wiki/Hypertext_Transfer_Protocol'
            }
        """
        r = dict()
        for hdr in self:
            r[hdr.name] = hdr.value
        return r

    def __str__(self):
        """ Returns a string representation of the headers::

            "Content-Type: text/html\nReferer: https://en.wikipedia.org"
        """
        return '\n'.join(str(x) for x in self)

class header(entities.entity):
    """ An object representing a header for HTTP response and
    request messages.::

        hdr = header(name='content-type', v='text/html')

        assert hdr.name == 'content-type'
        assert hdr.value == 'text/html'
    """
    def __init__(self, name, v):
        """ Constructs an HTTP header.

            hdr = header(name='content-type', v='text/html')

            assert hdr.name == 'content-type'
            assert hdr.value == 'text/html'
        """
        self._name = name
        self.value = v

    @property
    def name(self):
        """ The headers name.
        """
        # TODO Why do we need to lower() this. I think we should be
        # case-preserving here. Or, maybe we could get "name" to conform
        # to the standard way headers are cased, i.e, first characters,
        # and any character after a hyphen are uppercase.
        return self._name.lower()

    def __str__(self):
        """ Returns a string representation of the header. This is the
        standard string representation expected of a header, i.e., the
        name followed by a colon, then its value, e.g.::

            'content-type: text/html'
        """
        return '%s: %s' % self.tuple

    def __repr__(self):
        """ A string representation of the object and its values::

            header(content-type: text/html)
        """
        args = (
            type(self).__name__,
            self.name,
            str(self.value)
            
        )
        return '%s(%s: %s)"' % args

    @property
    def tuple(self):
        """ A tuple representation of the header:

            ('content-type', 'text/html')
        """
        return (str(self.name), str(self.value))

class browsers(entities.entities):
    """ A collection of ``browser`` objects.
    """
    pass

class browser(entities.entity):
    """ Represents a web browser.

    Like graphical browsers, the ``browser`` object maintains a
    collection of ``_tabs``::

        brw = browser()

        # "open" two tabs
        t1 = brw.tab()
        t2 = brw.tab()

    Like tabs in graphical browser, these tabs can make HTTP requests.
    First we construct the ``request`` object and pass it to the tab's
    ``request`` method.

        req = www.request(url='https://www.google.com')
        res = t1.request(req)

    The ``request`` method returns a ``response`` object.

    The ``browser`` itself contains a ``cookies`` collections which,
    among other things, can cause the ``browser`` to be authenticated
    to a give web site, by storing a JWT issued by the web site upon
    login.
    """
    class _tabs(entities.entities):
        """ Represents a collection of browser tabs.
        """

        def tab(self):
            """ Create and return a new ``_tab`` object. The tab object
            is stored in this ``_tabs`` collection.
            """
            t = browser._tab(self)
            self += t
            return t

    class _tab(entities.entity):
        """ Represents a tab in the browsers.

        ``tab`` object are used to make HTTP requests, using their
        ``request()`` method.
        """
        def __init__(self, tabs):
            """ Create a new tab object.

            :param: tabs _tabs: A reference to the tabs collection that
            this tab is a part of. This can be used to get back to the
            browser object itself.
            """
            self.tabs = tabs
            self._url = None

        @property
        def url(self):
            """ Return a `www.url` object that represents the url this
            `tab` is pointing to. Analogous to the location bar in a
            browser.
            """
            # Make sure we always return a www.url even if self._url was
            # set to a str
            if self._url is not None:
                self._url = url(self._url)

            return self._url

        @url.setter
        def url(self, v):
            self._url = v

        @property
        def onbeforeunload(self):
            """ Return the tab event that is triggered immediatly
            before the tab is "unloaded" when it navigates to a new
            URL.
            """
            if not self._onbeforeunload:
                self._onbeforeunload = entities.event()

            return self._onbeforeunload

        @onbeforeunload.setter
        def onbeforeunload(self, v):
            self._onbeforeunload = v

        @property
        def onafterload(self):
            """ Return the tab event that is triggered immediatly
            after the tab navigates to a new URL and the DOM is
            loaded.
            """
            if not self._onafterload:
                self._onafterload = entities.event()
            return self._onafterload

        @onafterload.setter
        def onafterload(self, v):
            self._onafterload = v

        def request(self, req):
            """ Makes an HTTP request. Returns a www.response object
            containing data the HTTP server returned.

            :param: req www.request: The request object. This object
            contains the data, such as the HTTP method, body (body),
            and headers used to make the HTTP request.
            """
            # TODO ``req`` should be able to be a str containing a url
            # or an ecommerce.url object for convenient. These would be
            # converted to ``request`` objects with a ``method`` of GET.
            url = req.url

            body = req.body

            if body:
                body = body.encode('utf-8')

            meth = req.method

            hdrs = req.headers.dict

            import urllib.request
            req1 = urllib.request.Request(
                str(url), body, hdrs, method=meth
            )

            req1.add_header('Content-Length', req.size)

            try:
                res = urllib.request.urlopen(req1, body)
            except Exception as ex:
                res = response(req=req, ex=ex)
                ex1 = HttpError.create(
                    'Error requesting' , res
                )
                raise ex1
            else:
                # Return a www.response objcet representing the HTTP
                # response to the HTTP request.
                return response(req=req, res=res)

    class _cookies(entities.entities):
        """ A class representing a collection of ``cookie`` objects.
        """

        @property
        def header(self):
            """ Creates and returns header object with a key of "Cookie"
            and a value of all the browser's (self) cookies safely
            encoded.
            """
            import urllib
            v = str()
            for cookie in self:
                v += '%s=%s' % (
                    cookie.name,
                    urllib.parse.quote(cookie.value)
                )

            return header(name="Cookie", v=v)

    class _cookie(entities.entity):
        """ Represents an HTTP cookie.

        The cookie object can be stored in the ``browser`` object in its
        ``cookies`` collection.
        """
        def __init__(self, name, value, domain, 
            path       =  '/',    expires   =  'session',
            http_only  =  False,  same_site =  None,
        ):
            """ Creates an HTTP cookie.

            :param: path str: Indicates a URL path that must exist in
            the requested URL in order to send the cookie header.

            :param: expires str: Indicates the date at which a cookie
            should expire. Permanent cookies are deleted at a date
            specified by this argument.
            """

            self.name     =  name;     self.value      =  value
            self.domain   =  domain;   self.path       =  path
            self.expires  =  expires;  self.http_only  =  http_only
            self.same_site = same_site

    class loadeventargs(entities.eventargs):
        def __init__(self, url):
            self.url = url

    def __init__(self):
        """ Create an instance of a browser.
        """
        # TODO The _tabs class doesn't have an __init__. I think the
        # intention of passing self to tabs is so the tabs collection
        # can have a reference back to the browser, which makes a lot of
        # sense, but this doesn't seem to be correctly implemented.
        self.tabs = browser._tabs(self)
        self.cookies = self._cookies()
        self._useragent = None

    @property
    def useragent(self):
        """ Returns an ecommerce.useragent object representing the
        useragent this browser is claiming it is.
        """
        if isinstance(self._useragent, ecommerce.useragent):
            pass
        elif self._useragent is None:
            pass
        else:
            # Coerse if private member is a str
            self._useragent = ecommerce.useragent(
                string = self._useragent
            )

        return self._useragent

    @useragent.setter
    def useragent(self, v):
        self._useragent = v

    def tab(self):
        """ Create a new tab, append it to the ``browse``'s tabs
        collection, and return the new tab.
        """
        return self.tabs.tab()

class urls(entities.entities):
    """ A collection of `url` objects.
    """

class url(entities.entity):
    """ Represents a URL.

    This class can be used to parse a URL string and easily parse out
    parts of the URL:

        >>> url = www.url('https://www.google.com?s=Test')
        >>> assert url.scheme == 'https'
        >>> assert url.host == 'www.google.com'
        >>> assert url.query == 's=Test'

    We can alse use the object's setters to build or mutate an `url`
    object.

        >>> url = www.url()
        >>> url.scheme = 'https'
        >>> url.host = 'www.google.com'
        >>> url.query = 's=Test'
        >>> assert str(url) == 'https://www.google.com?s=Test'
        
    """

    # These dummy scheme and host constants help us parse URL's that
    # don't have those parts. For example, if we only want to parse the
    # path portion of a URL, these variable can used with `urlunparse`.
    DummyScheme = '98a98061eb73489583f76a472eac5432'
    DummyHost   = '49ce02ef5d594a95ba531ee5fe6d45fa'

    def __init__(self, name=None, *args, **kwargs):
        """ Create a URL object.

        :param: name str: The URL string.
        """
        self._scheme    =  None
        self._host      =  None
        self._path      =  None
        self._query     =  None
        self._fragment  =  None
        self._username  =  None
        self._password  =  None
        self._port      =  None
        self.name       =  name
        super().__init__(*args, **kwargs)

    def clone(self):
        """ Return a new `url` instance equivalent to this `url`.
        """
        return type(self)(str(self))

    @property
    def name(self):
        """ Return the URL string.
        """
        from urllib.parse import urlunparse

        # Get scheme
        scheme = self.scheme

        # Get host
        host = self.host or str()

        # Deal with username and passwords
        if uid := self.username:
            if pwd := self.password:
                host = f'{uid}:{pwd}@{host}'
            else:
                host = f'{uid}@{host}'
        elif pwd := self.password:
            host = f':{pwd}@{host}'

        if port := self.port:
            if scheme == 'http':
                if port != 80:
                    host += f':{port}'
            elif scheme == 'https':
                if port != 443:
                    host += f':{port}'
            else:
                host += f':{port}'

        # Create a tuple to pass to urlunparse
        tup = (
            scheme     or  self.DummyScheme,
            host       or  self.DummyHost,
            self.path  or  '',
            '',
            self.query,
            self.fragment,
        )

        # Convert tuple into a url string
        r = urlunparse(tup)
        
        # Remove any of the dummy data
        dummy = f'{self.DummyScheme}://'
        r = r.replace(dummy, str(), 1)

        dummy = self.DummyHost
        r = r.replace(dummy, str(), 1)

        return  r

    @name.setter
    def name(self, v):
        """ Set the URL string.
        """
        import urllib.parse

        # XXX Test instantiating www.url with a www.url as an argument
        # to the constructor:
        #
        #     url = 'www.google.com'
        #     url = www.url(url)
        #     url = www.url(url)

        v = str(v)
        prs = urllib.parse.urlparse(v)

        self.scheme    =  prs.scheme
        self.host      =  prs.hostname
        self.path      =  prs.path
        self.query     =  prs.query
        self.fragment  =  prs.fragment
        self.username  =  prs.username
        self.password  =  prs.password
        self.port      =  prs.port
        
    def __truediv__(self, other):
        """ Overrides the / operator to allow for path joining

            wiki = url(name='https://www.wikipedia.org/') 
            py = wiki / 'wiki/Python'

            assert py.name == 'https://www.wikipedia.org/wiki/Python'
        """
        # TODO Add tests
        name = os.path.join(str(self), other)

        return url(name)

    @property
    def scheme(self):
        """ Returns the scheme (sometimes refered to as the protocol)
        portion of the URL. 

        Given the URL "scheme://netloc/path;parameters?query#fragment",
        "scheme" would be returned.
        """
        if not self._scheme:
            return None

        return self._scheme

    @scheme.setter
    def scheme(self, v):
        """ Set the scheme.
        """
        self._scheme = v

    @property
    def host(self):
        """ Returns the hostname portion of the URL. 

        Given the URL "scheme://netloc/path;parameters?query#fragment",
        "netloc" would be returned.
        """
        return self._host

    @host.setter
    def host(self, v):
        """ Set the host.
        """
        self._host = v

    @property
    def path(self):
        """ Returns the path portion of the URL.

        Given the URL:
            scheme://netloc:1234/path/to/resource;parameters?query#fragment

        returns: '/path/to/resource;parameters'
        """
        if not self._path:
            return None

        return self._path

    @path.setter
    def path(self, v):
        """ Set the path.
        """
        self._path = v

    def getpath(self, lang=True):
        """ Return the path portion of this `url`. By default, the
        behavior is identical to self.path.

        :param: lang bool: If False, return a path with the language
        code removed.
        """
        paths = [x for x in self.path.split('/') if x]

        if not lang:
            if paths:
                # TODO Use pycountry to search for all ISO country codes
                if paths[0] in ('en', 'es'):
                    paths.pop(0)

        return '/' + '/'.join(paths)

    @property
    def query(self):
        """ Returns a string representation of the query string in the
        URL (if there is one).

        See also the `qs` attribute.
        """
        if not self._query:
            return None

        return self._query

    @query.setter
    def query(self, v):
        """ Set the query string.
        """
        self._query = v

    @property
    def fragment(self):
        """ Return the fragment portion (the part after the #) of the
        URL. 
        """
        if not self._fragment:
            return None

        return self._fragment

    @fragment.setter
    def fragment(self, v):
        self._fragment = v

    @property
    def username(self):
        """ Return the username portion of the URL.
        """
        if not self._username:
            return None

        return self._username

    @username.setter
    def username(self, v):
        """ Set the username portion of the URL.
        """
        self._username = v

    @property
    def password(self):
        """ Return the password portion of the URL.
        """
        if not self._password:
            return None

        return self._password

    @password.setter
    def password(self, v):
        """ Set the password portion of the URL.
        """
        self._password = v

    @property
    def port(self):
        """ Returns the port portion of the URL as an int.

        Given the URL "scheme://netloc:1234/path;parameters?query#fragment",
        1234 would be returned.
        """
        if not self._port:
            if self.scheme == 'http':
                return 80
            if self.scheme == 'https':
                return 443

        return self._port

    @port.setter
    def port(self, v):
        """ Set the port portion of the url.
        """
        self._port = v

    @property
    def paths(self):
        """ Returns a list of path elements in the URL.

        Given the URL:
        
             scheme://netloc:1234/path/to/resource?query#fragment
        
        The return would be:
       
            ['path', 'to', 'resource']
        """
        # TODO Write tests

        return [x for x in self.path.split(os.sep) if x]

    @property
    def qs(self):
        """ Return a dict containing the keys and values in the URL's
        query sting (if there is one).

            >>> url(address='https://google.com?s=test').qs
            {'s': ['test']}

        """
        # TODO:872fd252 Ideally, we should be able to use the qs
        # property in a way that is similar to a dict:
        #
        #     id = url.qs['id']
        #     del url.qs['id'[
        #     url.qs['search'] = 'Men's shoes'
        #
        # This could be done by having this method return an object that
        # overrides __getitem__ and __setitem__ and keeps the parameters
        # in an internal data structure. We should be able to make it
        # backwords compatible with the current inteface if done
        # correctly.
        import urllib.parse
        kvps = entities.kvps()

        qs = urllib.parse.parse_qs(self.query)
        for k, v in qs.items():
            if len(v) == 1:
                v = v[0]
            elif len(v) == 0:
                v = None

            kvps += entities.kvp(k=k, v=v)

        kvps.onafterset += self._kvps_onafterset
        kvps.onremove += self._kvps_onremove

        return kvps

    @qs.setter
    def qs(self, v):
        """ Set the qs attribute to `v`.
        """
        if isinstance(v, entities.kvps):
            self.qs = v.dict()
            return
                
        from urllib.parse import urlencode as enc
        self.query = enc(v, doseq=True)

    def _kvps_onafterset(self, src, eargs):
        """ Handles the kvps' onafterset event.
        """

        # Whenever an item is set or added to the kvps collection,
        # convert the kvps (src) into a `dict` and assin it to this
        # `url`'s qs property
        self.qs = src.dict()

    def _kvps_onremove(self, src, eargs):
        """ Handles the kvps' onremove event.
        """
        # Whenever an item is deleted from the kvps collection, convert
        # the kvps (src) into a `dict` and assign it to this `url`'s qs
        # property
        self.qs = src.dict()

    def __eq__(self, url):
        """ Returns True if `url` is equivalent to this www.url.

        Equivalence is case-insensitive with regard to scheme and host,
        but the resource (i.e., path, query string parameters, query
        string paramter values, fragments) is case-sensitive.

        The sequence of query string parameters is irrelevant to
        equivalence. The sequence of query string paramter array is
        relevent to equivalent.

        The following URLs are equivalent:

            url('HTtp://eXample.org:8181?a=1&a=3&B=2')

            url('http://example.org:8181?B=2&a=1&a=3')

        whereas the following is not equal due to mismatch in the
        ordering of the array parameter a's values.

            url('http://example.org:8181?B=2&a=3&a=1')

            url('http://example.org:8181?B=2&a=1&a=3')

        Note that port numbers are infered from the scheme if not given
        so the following URLs will be equivalent:

            url('http://example.org')

            url('http://example.org:80')
        """

        return self.normal == url.normal

    @property
    def normal(self):
        """ Return a normalized version of this `www.url` object as a
        string.

            * The scheme and host are lowercased.

            * Port numbers are always included. If the port number was
              not provided, it will be infered from the scheme.

            * Case in path names are preserved.

            * Query parameters returned are alphabetized. For example:
                
                url = www.url('example.org?b=1&a=2')
                assert 'example.org?a=2&b=1' == url.normal

        Note that __eq__ uses `normal` because it assumes if two `url`
        objects normalize to the same string, they must be equivalent.
        """
        r = str()

        from socket import getservbyname, getservbyport

        if scheme := self.scheme:
            scheme = scheme.casefold()

            if port := self.port:
                pass
            else:
                with suppress(OSError):
                    port = getservbyname(scheme, 'tcp')
                    
        else:
            if port := self.port:
                with suppress(OSError):
                    scheme = getservbyport(scheme, 'tcp')

        if scheme:
            r += scheme.casefold() + '://'

        if host := self.host:
            r += host.casefold()

            if port:
                r += ':' + str(port)

        if path := self.path:
            r +=  path

        kvps = self.qs

        kvps.sort('name')

        for i, kvp in kvps.enumerate():
            if i.first:
                r += '?'

            vs = kvp.value
            if not isinstance(vs, list):
                vs = [vs]

            for j, v in enumerate(sorted(vs)):
                r += kvp.name + '=' + v

                if j + 1 < len(vs) or not i.last:
                    r += '&'

        if self.fragment:
            r += '#' + self.fragment

        return r
    def __str__(self):
        """ Return the URL string.
        """
        return self.name

    def __repr__(self):
        """ Return a programmer-friendly representation of this URL
        object.
        """
        r = type(self).__name__ 

        attrs = (
            'scheme',  'username',  'password',  'host',
            'port',    'path',      'query',     'fragment',
        )

        r += '('

        for attr in attrs:
            v = getattr(self, attr)
            r += f'{attr}='
            if isinstance(v, str):
                r += f'"{v}"'
            else:
                r += f'{v}'

            r += ', '
        
        r = r.rstrip(', ')
        r += ')'
        return r

