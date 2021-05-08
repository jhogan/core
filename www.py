# vim: set et ts=4 sw=4 fdm=marker

#######################################################################
# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2021
########################################################################

""" This module contains classes module contains the classes that
abstract the HTTP protocol, as well as WSGI and other web technologies.
"""

from dbg import B
from functools import reduce
from pprint import pprint
import auth
import dom
import entities
import exc
import file
import html as htmlmod
import json
import os
import party, ecommerce
import pdb
import primative
import re
import sys
import textwrap
import traceback
import urllib
import jwt as pyjwt
import json

# NOTE Use the following diagram as a guide to determine what status
# code to respond with:
# https://www.loggly.com/blog/http-status-code-diagram/
# (Backup: # https://stackoverflow.com/questions/3297048/403-forbidden-vs-401-unauthorized-http-responses)

class application:
    def __init__(self):
        self.breakonexception = False
        self.clear()

    def clear(self):
        self._request = None

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
        if not self._request:
            self._request = _request(self)
        return self._request

    def demand(self):
        if type(self.environment) is not dict:
            # PEP 333 insists that the environs must be a dict. The WSGI
            # server will almost certainly send a dict, but tester.py
            # likes to use its own data structure for this, so make sure
            # it always gives us a dict.
            raise TypeError('Environment must be of type "dict"')
        self.request.demand()
           
    def __call__(self, env, start_response):
        global request, response
        res = _response(self.request)
        res.headers += 'Content-Type: text/html'

        # Set global www.response
        response = res

        break_ = False

        try:
            self.clear()

            self.environment = env

            req = self.request

            request = self.request

            self.demand()

            if req.isget or req.ishead:
                data = req()
                if req.isget:
                    res.payload = data

            elif req.ispost:
                if req.isxhr:
                    reqdata = self.request.post

                    cls, meth = self.class_, self.method

                    obj = cls(self)

                    data = getattr(obj, meth)()

                    data = [] if data == None else data
                else:
                    res.payload = req()

            else:
                raise MethodNotAllowedError(
                    'Method "%s" is never allowed' % req.method
                )

        except Exception as ex:
            if self.breakonexception:
                # Immediatly raise to tester's exception handler
                break_ = True
                raise

            try:
                if self.request.isxhr:
                    # TODO When we start supporting XHR requests, the
                    # `tb` being passed here can be built with the
                    # exc.tracebacks class. See the git-log for how `tb`
                    # was originally created. Aso NOTE We will only want
                    # the traceback if we are in a non-production
                    # environment, so ensure it dosen't get returned to
                    # the client if we are.
                    data = {'_exception': repr(ex), '_traceback': tb}
                else:
                    if isinstance(ex, HttpError):
                        # HttpError are 400s and 500s

                        lang = req.language
                        path = '/%s/error/%s' % (lang, ex.status)
                        pg = req.site(path)

                        if pg:
                            pg.clear()
                            pg(ex=ex)
                        else:
                            pg = req.site['/%s/error' % lang]
                            pg.clear()
                            pg(ex=ex)

                        res.payload = pg.html
                        res.status = ex.status
                    elif isinstance(ex, HttpException):
                        # HttpException are HTTP 300s. Allow the
                        # exception to make modifications to the
                        # response.
                        ex(res)
                    else:
                        res.status = 500
                        p = dom.p()
                        p += dom.text('Error: ')
                        p += dom.span(type(ex).__name__, class_='type')
                        p += dom.text(' ')
                        p += dom.span(str(ex), class_='message')
                        req.page.flash(p)
                        res.payload = req.page.html

            except Exception as ex:
                # In case there is an exception processing the
                # exception, ensure the response is 500 with a simple
                # error message.
                res.status = 500
                res.payload = dom.dedent('''
                <p>Error processing exception: %s</p>
                ''' % str(ex))

        finally:
            if not break_:
                start_response(res.status, dict(res.headers.list))
                return iter([res.payload])

            request = None

# TODO The class name should be `request` and the main instance should
# be stored in `_reuest` at the class level. A @property called
# request.main or request.current can store the request object currently
# being processed.
request = None
class _request:
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

        :param: url ecommerce.url: The URL object containing the URL
        being accessed.
        """
        self.app           =  app
        if app:
            self.app._request  =  self

        self._payload    =  None
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

        body = self.payload
        if body:
            try:
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
        where the keys start with 'http_'.
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
        """ Return a collection of files that were uploaded in the HTTP
        request.

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
            # Currently, we will only have file in the request if we are
            # using a multipart mime type. This will change once
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
        """ Returns the authenicated user making the request. If there is
        no authenicate user, returns None.
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

        This corresponds to the ``environ`` parameter in the classic
        WSGI method call defined in PEP 333::

            def simple_app(environ, start_response):
                ...

        For the framework's main implementation of the above method, see
        ``www.application.__call__``.


        For more information about the actual environ dict, see:
        https://www.python.org/dev/peps/pep-0333/#environ-variables
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
        if self.iswsgi:
            return self.environment['server_name']

        return urllib.parse.urlparse(self._url).hostname

    @property
    def arguments(self):
        return dict(urllib.parse.parse_qsl(self.qs))

    @property
    def qs(self):
        if self.iswsgi:
            qs = self.environment['query_string']

            if not qs:
                qs = None

            return qs

        return urllib.parse.urlparse(self._url).query

    @property
    def site(self):
        """ Get the single site for this instance.
        """
        try:
            # NOTE 'server_site' is a contrived, non-HTTP environment
            # variable used by test scripts to pass in instances of site
            # objects to use.

            # TODO When the config logic is complete (eb7e5ad0) Ensure
            # that we are in a test environment before accepting this
            # variable to prevent against tampering.
            ws = self.environment['server_site']

            # Prevent circular importing by importing pom here instead
            # of at the top
            import pom
            if isinstance(ws, pom.site):
                return ws
        except KeyError:
            pass

        # Return the site object as set in the config logic
        return pom.site.getinstance()

    @property
    def page(self):
        """ Return the page that this request is GETting (POSTing to,
        etc.) 
        """
        ws = self.site
        path = self.path
        try:
            return ws[path]
        except IndexError:
            return None

    @property
    def language(self):
        ''' Return the language code. This is usually the first segment
        of the URL path. 
        '''

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
        # TODO If an exception bubbles up here, it should be logged to
        # syslog (I think).

        # Create the hit log. In the finally block, we will add some
        # concluding information by calling self.log again, such as the
        # HTTP status code.
        self.log()

        try:
            # Invoke the page
           self.page(**self.arguments)
        except HttpError as ex:
            if ex.flash:
                self.page.flash(ex.flash)
                response.status = ex.status
            else:
                raise
        finally:
            # Finish of the hit log
            self.log()

        return self.page.html

    @property
    def hit(self):
        """ Return the ``hit`` entity. If it does not yet exist for this
        request, create it.
        """
        if not self._hit:
            # Create the hit entity. No need to save it at the moment.

            self._hit = ecommerce.hit(
                path       =  self.page.path,
                isxhr      =  self.isxhr,
                qs         =  self.qs,
                method     =  self.method,
                site       =  self.site,
                language   =  self.language,
                ip         =  self.ip,
                url        =  self.referer,
                size       =  self.size,
                useragent  =  self.useragent,
            )

            if self.jwt:
                self._hit.isjwtvalid = self.jwt.isvalid
            else:
                self._hit.isjwtvalid = None

        return self._hit

    def log(self):
        """ Log the hit.
        """

        try: 
            # Get the request's ``hit`` entity
            hit = self.hit

            par = None

            # Get the users party. If no user is logged in, use the
            # anonymous user.
            if self.user:
                par = self.user.party
                hit.user = self.user
            else:
                par = party.party.anonymous

            if par is None:
                par = party.party.anonymous

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
                hit.status = response.status
            else:
                hit.begin = now

            hit.visit = visit

            # Create/update the hit
            hit.save()
        except Exception as ex:
            # Failing to log a hit shouldn't stop page invocation. We
            # should log the failure to the syslog.
            from config import config

            # TODO:4d723428 Fix the logging interface. We shouldn't have
            # to go through config to get a logging object. Also, it
            # doesn't make sense to select the first log from a
            # collection of logs. The collections of logs are actually
            # configurations of logging facilities. The first here is
            # for /var/log/syslog (there aren't any others). This is all
            # really wierd. We shoud just be able to say something like:
            #
            #     import log from logger
            #     log.exception(ex)
            #
            # The nature of the core framework is such that we would
            # normally log stuff to a database table. We wouldn't want
            # to write anything to a log file unless there was a failure
            # to write to the database. Log entries in syslog should be
            # indicate the environment that is making the entry.
            log = config().logs.first

            try:
                ua = str(self.environment['user_agent'])
            except:
                ua = str()

            try:
                ip = str(self.environment['remote_addr'])
            except:
                ua = str()

            msg = f'{ex}; ip:{ip}; ua:"{ua}"'
            log.exception(msg)

    # TODO The official word for this data is "message body", so we
    # should probably rename the property to "body".
    @property
    def payload(self):
        """ Returns the HTTP message body of the request.

        https://en.wikipedia.org/wiki/HTTP_message_body
        """

        if self._payload is None:
            # If the payload hasn't been set, we can get it from the
            # wsgi environment.
            if self.iswsgi:
                sz = self.size
                inp = self.environment['wsgi.input']
                if self.mime == 'multipart/form-data':
                    # Normally, the client won't need to get the payload
                    # for multipart data; it will usually just use
                    # `request.files`. Either way, return whan we have.
                    # We probably shouldn't memoize it since it could be
                    # holding a lot of file data.

                    # TODO We could move this outside the consequence
                    # block
                    inp.seek(0)

                    return inp.read(sz)
                else:
                    # TODO What would the mime type (content-type) be
                    # here?  (text/html?) Let's turn this else into an
                    # elif with that information.
                    self._payload = inp.read(sz).decode('utf-8')
        return self._payload

    @payload.setter
    def payload(self, v):
        self._payload = v

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
            return self.environment['path_info']


    @property
    def size(self):
        if self.iswsgi:
            try:
                return int(self.environment.get('content_length', 0))
            except ValueError:
                return 0

        return len(self.payload)

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
        if self.iswsgi:
            return self.environment['request_method'].upper()
        
        if self._method:
            return self._method.upper()

        return None

    @method.setter
    def method(self, v):
        self._method = v

    @property
    def ip(self):
        if not self._ip:
            ip = str(self.environment['remote_addr'])
            self._ip = ecommerce.ip(address=ip)
        return self._ip

    @property
    def referer(self):
        if not self._referer:
            url = str(self.environment['http_referer'])
            self._referer = ecommerce.url(address=url)
        return self._referer

    @property
    def useragent(self):
        if not self._useragent:
            if self.iswsgi:
                ua = str(self.environment['user_agent'])
                self._useragent = ecommerce.useragent(string=ua)
        return self._useragent

    @property
    def scheme(self):
        """ Return the scheme for the request, e.g., http, https, etc.
        """
        if self.iswsgi:
            return self.environment['wsgi.url_scheme'].lower()

        return urllib.parse.urlparse(self._url).scheme

    @property
    def port(self):
        """ Return the TCP port for the request, e.g., 80, 8080, 443.
        """
        if self.iswsgi:
            return int(self.environment['server_port'])

        return urllib.parse.urlparse(self._url).port

    @property
    def url(self):
        """ Return the URL for the request, for example::
            
            https://foo.net:8000/en/my/page
        """
        if self._url:
            return self._url

        scheme = self.scheme
        servername = self.servername
        if self.port:
            servername += ':' + str(self.port)

        qs = self.qs
        path = self.path

        if qs:
            path += "?{qs}"

        return urllib.parse.urlunparse([
            scheme, servername, path, None, None, None
        ])

    @property
    def isget(self):
        return self.method == 'GET'

    @property
    def ispost(self):
        return self.method == 'POST'

    @property
    def ishead(self):
        return self.method == 'HEAD'

    @property
    def isxhr(self):
        return self.content_type == 'application/json'

    @property
    def content_type(self):
        return self.environment['content_type'].strip()

    @property
    def mime(self):
        return self.content_type.split(';')[0].strip().lower()

    def demand(self):
        if not request.page:
            raise NotFoundError(self.path)

        if self.isget or self.ishead:
            if not len(self.path):
                raise www.BadRequestError('No path was given.')
            
        elif self.ispost:
            if self.mime == 'text/html' and len(self.payload) == 0:
                raise BadRequestError('No data in body of request message.')

            if self.mime == 'multipart/form-data':
                if self.files.isempty:
                    raise BadRequestError(
                        'No files given in multipart form.'
                    )
                    

            # The remaining demands will be for XHR requests only
            if not self.isxhr:
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

response = None
class _response():
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
        """
        :param: req www._request: The request object that resulted in
        this response.

        :param: res urllib.response: The response object from
        urllib.request.urlopen(). This response object (self) will wrap
        ``res``, making things more convenient for the user of
        www._response.

        :param: ex Exception: If the HTTP response is the result of an
        Exception, ``ex`` can be passed in. If it contains the status
        code, that status code will be used for the respones's status
        property.
        """
        self._payload = None
        self._status = 200
        self._page = None
        self.request = req
        self._headers = headers()
        self._response = res

        if res:
            self.status = res.status
            self.payload = res.read()
            self.headers = res.headers

        if ex:
            try:
                st = ex.status
            except AttributeError:
                self.status = 500
            else:
                self.status = st

            payload = None
            try:
                payload = ex.read()
            except AttributeError:
                pass
            else:
                self.payload = payload

            try:
                hdrs = ex.headers
            except AttributeError:
                pass
            else:
                self.headers = hdrs
    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, v):
        self._status = v

    @property
    def message(self):
        try:
            return '%i %s' % (self.status, self.Messages[self.status])
        except KeyError:
            return str(self.status)

    @property
    def contenttype(self):
        """ The content type of the body.
        """
        return self.headers['Content-Type']

    @property
    def mime(self):
        """ Returns the **type** and **subtype** portion of the mime.
        example, if ``self.contenttype`` is:
                
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
    def payload(self):
        # These lines are for XHR responses
        # payload = json.dumps(payload)
        # payload = bytes(payload, 'utf-8')
        return self._payload

    @payload.setter
    def payload(self, v):
        self._payload = v

    @property
    def json(self):
        """ If the payload is a JSON string, returns a Python list
        representing the JSON document. An exception will be raised if
        the payload cannot be deserialized as a JSON document.
        """
        return json.loads(self.payload)

    @property
    def html(self):
        """ Returns a dom.html object representing the HTML in the
        payload.
        """
        # TODO If the payload is not HTML (perhaps it's JSON or the
        # content-type isn't HTML), we should probably raise a
        # ValueError.
        return dom.html(self.payload)

    def __getitem__(self, sels):
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
        # If self._headers is not an instance of `headers`, coerse to
        # the native type.
        if not isinstance(self._headers, headers):
            self._headers = headers(self._headers)

        clen = len(self.payload) if self.payload else 0
        self._headers['Content-Length'] = clen
        
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

    def __repr__(self, pretty=False):
        r = textwrap.dedent('''
        URL:    %s
        Method: %s
        Status: %s

        %s
        ''')

        payload = self.payload
        if pretty:
            if self.mime == 'application/json':
                payload = json.dumps(json.loads(payload), indent=4)
            elif self.mime == 'text/html':
                payload = dom.html(self.payload).pretty 

        return r % (
            self.request.path,
            self.request.method,
            self.message,
            payload,
        )

    def __str__(self):
        return self.__repr__(pretty=True)

class controller:
    def __init__(self, app):
        self._app = app

    @property
    def application(self):
        return self._app

    @property
    def data(self):
        return self.application.requestdata

    @property
    def _arguments(self):
        return self.application.requestdata['args']

    def getargument(self, arg):
        args = self._arguments
        try:
            return args[arg]
        except KeyError:
            raise www.UnprocessableEntityError(
                'Argument not supplied: ' + arg
            )

class HttpException(Exception):
    def __init__(self, msg, res=None):
        super().__init__(msg)
        self.response = res

    @classmethod
    def create(cls, msg, res, _attop=True):
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

        :param: _attop bool: Since ``create`` is a recursive method,
        ``atop`` is used internally to determine when the method is at
        the top of the recursion stack.
        """
        for sub in cls.__subclasses__():
            
            # Recurse
            ex = sub.create(msg, res, _attop=False)

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
        if _attop:
            
            # If we are here, then recursing through the subclasses did
            # not result in the discovery of the correct exception
            # class. Therefore, just fall back on the genereic HTTP 500
            # InternalServerError.
            return InternalServerError(res=res)

        return None

    @property
    def phrase(self):
        return '%s %s' % (
            str(self.status), _response.Messages[self.status]
        )

    @property
    def message(self):
        return str(self)

    def __call__(self, res):
        raise NotImplementedError(
            'Processing for HTTP %s not implemented' % self.status
        )

class HttpError(HttpException):
    def __init__(self, msg=None, flash=None, res=None):
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
    def __init__(self, d=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if d:
            for k, v in d.items():
                self += header(k, v)
            
    def __setitem__(self, ix, v):
        if not isinstance(ix, str):
            return super().__setitem__(ix)

        # TODO Why can't we overwrite prior values. 
        for hdr in self:
            if hdr.name.casefold() == ix.casefold():
                break
        else:
            self += header(ix, v)

    def __getitem__(self, ix):
        if not isinstance(ix, str):
            return super().__getitem__(ix)

        for hdr in self:
            if hdr.name.casefold() == ix.casefold():
                return hdr.value
        return None

    def append(self, obj, uniq=False, r=None):
        if isinstance(obj, str):
            kvp = [x.strip() for x in obj.partition(':') if x != ':']
            if len(kvp) != 2:
                raise ValueError(
                    'Headers must be colon seperate KVPs'
                )
            return self.append(header(*kvp))

        super().append(obj=obj, uniq=uniq, r=r)

    @property
    def list(self):
        r = list()
        for hdr in self:
            r.append(hdr.tuple)
        return r

    @property
    def dict(self):
        r = dict()
        for hdr in self:
            r[hdr.name] = hdr.value
        return r

    def __str__(self):
        return '\n'.join(str(x) for x in self)

class header(entities.entity):
    def __init__(self, name, v):
        self._name = name
        self.value = v

    @property
    def name(self):
        # TODO Why do we need to lower() this. I think we should be
        # case-preserving here.
        return self._name.lower()

    def __str__(self):
        return '%s: %s' % self.tuple

    def __repr__(self):
        args = (
            type(self).__name__,
            self.name,
            str(self.value)
            
        )
        return '%s (%s: %s)"' % args

    @property
    def tuple(self):
        return (self.name, self.value)

class browsers(entities.entities):
    pass

class browser(entities.entity):
    class _tabs(entities.entities):
        def tab(self):
            t = browser._tab(self)
            self += t
            return t

    class _tab(entities.entity):
        def __init__(self, tabs):
            self.tabs = tabs

        def request(self, req):
            url = req.url

            body = req.payload

            if body:
                body = body.encode('utf-8')

            meth = req.method

            hdrs = req.headers.dict

            req1 = urllib.request.Request(
                url, body, hdrs, method=meth
            )

            req1.add_header('Content-Length', req.size)

            try:
                res = urllib.request.urlopen(req1, body)
            except Exception as ex:
                res = _response(req=req, ex=ex)
                ex1 = HttpError.create(
                    'Error requesting' , res
                )
                raise ex1
            else:
                # Return a www._response objcet representing the HTTP
                # response to the HTTP request.
                return _response(req=req, res=res)

    class _cookies(entities.entities):
        @property
        def header(self):
            """ A header object with a key of "Cookie" and a value of
            all the browser's (self) cookies safely encoded.
            """

            v = str()
            for cookie in self:
                v += '%s=%s' % (
                    cookie.name,
                    urllib.parse.quote(cookie.value)
                )

            return header(name="Cookie", v=v)

    class _cookie(entities.entity):
        def __init__(self, name, value, domain, 
            path       =  '/',    expires   =  'session',
            http_only  =  False,  same_site =  None,
        ):

            self.name     =  name;     self.value      =  value
            self.domain   =  domain;   self.path       =  path
            self.expires  =  expires;  self.http_only  =  http_only
            self.same_site = same_site

    def __init__(self):
        self.tabs = browser._tabs(self)
        self.cookies = self._cookies()
        self._useragent = None

    @property
    def useragent(self):
        if isinstance(self._useragent, ecommerce.useragent):
            pass
        elif self._useragent is None:
            pass
        else:
            self._useragent = ecommerce.useragent(
                string = self._useragent
            )

        return self._useragent

    @useragent.setter
    def useragent(self, v):
        self._useragent = v

    def tab(self):
        return self.tabs.tab()


app = application()
