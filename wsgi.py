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

# TODO:16dcc94a Change wsgi.py to http.py
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

            self.demand()

            req = self.request

            request = self.request

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

            if isinstance(ex, httperror):
                res.status = ex.statuscode
            else:
                res.status = 500

            # Get the stack trace
            tb = traceback.format_exception(etype=None, value=None, tb=ex.__traceback__)

            # The top and bottom of the stack trace don't correspond to frames, so remove them
            tb.pop(); tb.pop(0)

            tb = [re.split('\n +', f.strip()) for f in tb]

            data = {'_exception': repr(ex), '_traceback': tb}

        finally:
            if not break_:
                start_response(res.message, res.headers)
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
        return ws[path]

    def __call__(self):
        self.page(**self.arguments)
        return self.page.html

    @property
    def payload(self):
        if self._payload is None:
            sz = self.size
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
    def size(self):
        try:
            return int(self.environment.get('CONTENT_LENGTH', 0))
        except ValueError:
            return 0

    @property
    def post(self):
        return json.loads(self.body)

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
        return self.method.casefold() == 'get'

    @property
    def ispost(self):
        return self.method.casefold() == 'post'

    def demand(self):
        if self.isget:
            if not len(self.path):
                raise http400('No path was given.')
            
        elif self.ispost:
            if len(self.payload) == 0:
                raise http400('No data in body of request message.')

            if self.method == 'get':
                return

            try:
                post = self.post
            except json.JSONDecodeError as ex:
                raise http400(str(ex))

            try:
                cls = post['_class']
            except KeyError:
                raise http404('The class value was not supplied')

            try:
                meth = self.postmethod
            except KeyError:
                raise ValueError('The method value was not supplied')

            if meth[0] == '_':
                raise http403('Invalid method.')

            try:
                import ctrl
            except ImportError as ex:
                raise ImportError('Error importing controller: ' + str(ex))

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
            self.request.page.path,
            self.request.method,
            self.message,
            dom.html(self.data).pretty if pretty else self.data,
        )

    def __str__(self):
        return self.__repr__(pretty=True)

class httperror(Exception):
    def __init__(self, statuscode, msg):
        self.statuscode = statuscode
        self.message = msg

    def __repr__(self):
        return self.message

class http422(httperror):
    def __init__(self, msg):
        super().__init__('422 Unprocessable Entity', msg)


class http404(httperror):
    def __init__(self, msg):
        super().__init__('404 Not Found', msg)

class http403(httperror):
    def __init__(self, msg):
        super().__init__('403 Forbidden', msg)


class http401(httperror):
    def __init__(self, msg):
        super().__init__('401 Unauthorized', msg)

class http400(httperror):
    def __init__(self, msg):
        super().__init__('400 Bad Request', msg)

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
            raise http422('Argument not supplied: ' + arg)

app = application()
