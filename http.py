# vim: set et ts=4 sw=4 fdm=marker

#######################################################################
# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2020
########################################################################

import json
import sys
from functools import reduce
from pprint import pprint
import traceback
import re
import os
from dbg import B
import dom
import pom
import textwrap
import urllib
import pdb

# TODO Use the following diagram as a guide to determine what status
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
        self.request.demand()
           
    def __call__(self, env, start_response):
        global request
        res = response(self.request)
        break_ = False

        try:
            self.clear()

            self.environment = env

            req = self.request

            request = self.request

            self.demand()

            if req.isget:
                res.data = req()
            elif req.ispost:
                if req.isxhr:
                    reqdata = self.request.post

                    cls, meth = self.class_, self.method

                    obj = cls(self)

                    data = getattr(obj, meth)()

                    data = [] if data == None else data
                else:
                    res.data = req()

            else:
                # TODO Change to Bad Method exception> NOTE this block
                # should be superfluous since the `self.demand` call
                # should capture this problem
                raise ValueError('Bad method')

        except Exception as ex:
            if self.breakonexception:
                # Immediatly raise to tester's exception handler
                break_ = True
                raise

            if isinstance(ex, HttpError):
                res.status = ex.status
            else:
                res.status = 500

            # Get the stack trace
            tb = traceback.format_exception(
                etype=None, value=None, tb=ex.__traceback__
            )

            # The top and bottom of the stack trace don't correspond to
            # frames, so remove them
            tb.pop(); tb.pop(0)

            tb = [re.split('\n +', f.strip()) for f in tb]

            if self.request.isxhr:
                data = {'_exception': repr(ex), '_traceback': tb}
            else:
                if isinstance(ex, HttpError):
                    # TODO Don't hard code language code (/en)
                    pg = req.site('/en/error/%s' % ex.status)

                    if pg:
                        pg(ex=ex)
                    else:
                        pg = req.site['/en/error']
                        pg(ex=ex)

                    res.status = ex.status
                    res.data = pg.html

        finally:
            if not break_:
                start_response(res.status, res.headers)
                return iter([res.data])

            request = None

request = None
class _request:
    def __init__(self, app):
        self.app = app
        self.app._request = self
        self._payload = None

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

    def __call__(self):
        self.page(**self.arguments)
        return self.page.html

    @property
    def payload(self):
        if self._payload is None:
            sz = self.size
            # TODO We should probably convert the self.environment dict
            # to something that can supports case-insensitive indexing
            # since case will probably cause problems in the future.
            # The http.headers class may be good for this, though I'm
            # not sure if WSGI environmen variables are technically HTTP
            # headers. Note that the WSGI protocals has it that the
            # environ variable should be a dict so we shoud still
            # support environs as a dict, we just don't need to preserve
            # it as a simple dict internally.
            inp = self.environment['wsgi.input']
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
    def post(self):
        return json.loads(self.body)

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
        return self.environment['request_method']

    @property
    def isget(self):
        # TODO self.method will always be uppercase, so there's no need
        # to casefold()
        return self.method.casefold() == 'get'

    @property
    def ispost(self):
        # TODO self.method will always be uppercase, so there's no need
        # to casefold()
        return self.method.casefold() == 'post'

    @property
    def isxhr(self):
        return self.content_type == 'application/json'

    @property
    def content_type(self):
        return self.environment['content_type']

    def demand(self):
        if not request.page:
            raise NotFoundError(self.path)
        if self.isget:
            if not len(self.path):
                raise http.BadRequestError('No path was given.')
            
        elif self.ispost:
            if len(self.payload) == 0:
                raise http.BadRequestError('No data in body of request message.')

            # The remaining demands will be for XHR requests only
            if not self.isxhr:
                return

            try:
                post = self.post
            except json.JSONDecodeError as ex:
                raise http.BadRequestError(str(ex))

            try:
                cls = post['_class']
            except KeyError:
                raise htt.NotFoundError('The class value was not supplied')

            try:
                meth = self.postmethod
            except KeyError:
                raise ValueError('The method value was not supplied')

            if meth[0] == '_':
                raise http.ForbiddenError('Invalid method.')

            try:
                import ctrl
            except ImportError as ex:
                raise ImportError('Error importing controller: ' + str(ex))

        else:
            # TODO:f824d92b It's currently hard to test this. When we
            # consolidate code from the different request methods in
            # tester.py (post(), get(), head(), etc) we may be able to
            # use the resulting private request method to alter the
            # request_method to something arbitrary.

            raise MethodNotAllowedError(
                'Method "%s" is never allowed' % self.method
            )

class response():
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
        self._data = None
        self._status = 200
        self._page = None
        self.request = req
        self._headers = None

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
    def data(self):
        # TODO Call this property "payload"

        # These lines are for XHR responses
        # data = json.dumps(data)
        # data = bytes(data, 'utf-8')
        return self._data

    @data.setter
    def data(self, v):
        self._data = v

    def __getitem__(self, sels):
        return self.html[sels]

    @property
    def html(self):
        return dom.html(self.data)

    @property
    def headers(self):
        if self._headers is not None:
            return self._headers

        hdrs = [
        ]

        if self.data is not None:
            hdrs.append(
                ('Content-Length', str(len(self.data)))
            )

        # if XHR
        '''
        hdrs.append(
            ('Content-Type', 'application/json'),
            ('Access-Control-Allow-Origin', '*')
        )
        '''

        return hdrs

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
            dom.html(self.data).pretty if pretty else self.data,
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
            raise http.UnprocessableEntityError(
                'Argument not supplied: ' + arg
            )

class HttpError(Exception):
    def __init__(self, msg=None):
        msg0 = self.phrase
        if msg:
            msg0 += ' - ' + msg

        super().__init__(msg0)

    @property
    def phrase(self):
        return '%s %s' % (
            str(self.status), response.Messages[self.status]
        )

    @property
    def message(self):
        return str(self)

class MultipleChoicesException(HttpError):
    status = 300

class MovedPermanentlyException(HttpError):
    status = 301

class FoundException(HttpError):
    status = 302

class SeeOtherException(HttpError):
    status = 303

class NotModifiedException(HttpError):
    status = 304

class UseProxyException(HttpError):
    status = 305

class SwitchProxyException(HttpError):
    status = 306

class TemporaryRedirectException(HttpError):
    status = 307

class PermanentRedirectException(HttpError):
    status = 308

class BadRequestError(HttpError):
    status = 400

class UnauthorizedError(HttpError):
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
app = application()
