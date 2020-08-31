# vim: set et ts=4 sw=4 fdm=marker

#######################################################################
# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2020
########################################################################

from dbg import B
from functools import reduce
from pprint import pprint
import auth
import dom
import entities
import exc
import html as htmlmod
import json
import os
import pdb
import pom
import re
import sys
import textwrap
import traceback
import urllib
import party

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

request = None
class _request:
    def __init__(self, app):
        self.app           =  app
        self.app._request  =  self
        self._payload      =  None
        self._user         =  None

    @property
    def headers(self):
        """ Return a collection HTTP headers associated with this
        request. 
        
        Note that WSGI gives us the HTTP headers in its `environ` dict
        where the keys start with 'http_'.
        """

        hdrs = headers()
        for k, v in self.environment.items():
            if not k.lower().startswith('http_'):
                continue

            hdrs += header(k[5:], v)

        return hdrs

    @property
    def cookies(self):
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
    def user(self):
        """ Return the authenicated user making the request. If there is
        no authenicate user, return None.
        """

        # Get the JWT and convert it to a user 
        jwt = self.cookies('jwt')
        if jwt:
            jwt = jwt.value
            jwt = auth.jwt(jwt)

            # NOTE The JWT's sub property has a hex str
            # represetation of the user's id.
            self._user = party.user(jwt.sub)

        return self._user
                
    @property
    def environment(self):
        return self.app.environment

    @property
    def servername(self):
        return self.environment['server_name']

    @property
    def arguments(self):
        return dict(urllib.parse.parse_qsl(self.qs))

    @property
    def qs(self):
        return self.environment['query_string']

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
            if isinstance(ws, pom.site):
                return ws
        except KeyError:
            pass

        # Return the site object as set in the config logic
        return pom.site.getinstance()

    @property
    def page(self):
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
            # TODO When the language code is not given, Accept-Language can
            # be used to work out the best language.
            segs = [x for x in self.path.split('/') if x]
            if len(segs):
                return segs[0]
        except:
            return 'en'

        # Default to English
        return 'en'

    def __call__(self):
        try:
            self.page(**self.arguments)
        except HttpError as ex:
            if ex.flash:
                self.page.flash(ex.flash)
                response.status = ex.status
            else:
                raise
        return self.page.html

    @property
    def payload(self):
        if self._payload is None:
            sz = self.size
            inp = self.environment['wsgi.input']
            if self.ismultipart:
                self._payload = inp.read(sz)
            else:
                # TODO What would the mime type (content-type) be here?
                # (text/html?) Let's turn this else into an elif with
                # that information.
                self._payload = inp.read(sz).decode('utf-8')
        return self._payload

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
        return self.environment['path_info']

    @property
    def size(self):
        try:
            return int(self.environment.get('content_length', 0))
        except ValueError:
            return 0

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
        return self.environment['request_method'].upper()

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
        return self.environment['content_type']

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
                B()
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
                raise htt.NotFoundError('The class value was not supplied')

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

    def __init__(self, req):
        self._payload = None
        self._status = 200
        self._page = None
        self.request = req
        self._headers = headers()

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
    def payload(self):
        # These lines are for XHR responses
        # payload = json.dumps(payload)
        # payload = bytes(payload, 'utf-8')
        return self._payload

    @payload.setter
    def payload(self, v):
        self._payload = v

    def __getitem__(self, sels):
        return self.html[sels]

    @property
    def html(self):
        return dom.html(self.payload)

    @property
    def headers(self):
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

    def __repr__(self, pretty=False):
        r = textwrap.dedent('''
        URL:    %s
        Method: %s
        Status: %s

        %s
        ''')

        return r % (
            self.request.path,
            self.request.method,
            self.message,
            dom.html(self.payload).pretty if pretty else self.payload,
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
    @property
    def phrase(self):
        return '%s %s' % (
            str(self.status), response.Messages[self.status]
        )

    @property
    def message(self):
        return str(self)

    def __call__(self, res):
        raise NotImplementedError(
            'Processing for HTTP %s not implemented' % self.status
        )

class HttpError(HttpException):
    def __init__(self, msg=None, flash=None):
        self.flash = flash
        msg0 = self.phrase
        if msg:
            msg0 += ' - ' + msg

        super().__init__(msg0)

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

    @property
    def list(self):
        r = list()
        for hdr in self:
            r.append(hdr.tuple)
        return r

class header(entities.entity):
    def __init__(self, name, v):
        self._name = name
        self.value = v

    @property
    def name(self):
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
        pass

    class _tab(entities.entity):
        # TODO These methods will eventually be implemented to perform
        # actual HTTP requests. At the time of this writting, however,
        # these will be implemented in the testers.browser subclass
        def get(self, url):
            self._request(url)

        def post(self, url):
            self._request(url)

        def head(self, url):
            self._request(url)

        def _request(self, url):
            raise NotImplementedError('TODO')

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
        self.cookies = self._cookies()

app = application()
