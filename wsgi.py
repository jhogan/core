import json
import sys
from functools import reduce
from pprint import pprint
import traceback
import re
import os
from dbg import B
import pom

# TODO Use the following diagram as a guide to determine what status
# code to respond with:
# https://www.loggly.com/blog/http-status-code-diagram/
# (Backup: # https://stackoverflow.com/questions/3297048/403-forbidden-vs-401-unauthorized-http-responses)
class application:
    def __init__(self):
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
            self._request = request(self)
        return self._request

    def demand(self):
        self.request.demand()
           
    def __call__(self, env, sres):
        res = response()

        try:
            self.clear()

            self.environment = env

            self.demand()

            req = self.request


            if req.isget:
                res.body = req.page()
                
            elif req.ispost:
                reqdata = self.request.post

                cls, meth = self.class_, self.method

                obj = cls(self)

                data = getattr(obj, meth)()

                data = [] if data == None else data

            else:
                # TODO Change to Bad Method exception> NOTE this block
                # should be superfluous since the `self.demand` call
                # should capture this problem
                raise ValueError('Bad method')

        except Exception as ex:
            if isinstance(ex, httperror):
                res.statuscode = ex.statuscode
            else:
                res.statuscode = '500 Internal Server Error'

            # Get the stack trace
            tb = traceback.format_exception(etype=None, value=None, tb=ex.__traceback__)

            # The top and bottom of the stack trace don't correspond to frames, so remove them
            tb.pop(); tb.pop(0)

            tb = [re.split('\n +', f.strip()) for f in tb]

            data = {'_exception': repr(ex), '_traceback': tb}

        finally:
            sres(res.statuscode, res.headers)
            return iter([res.data])


class request:
    def __init__(self, app):
        self.app = app

    @property
    def environment(self):
        return self.app.environment

    @property
    def servername(self):
        return self.environment['server_name']

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
        return ws[self.path]

    @property
    def body(self):
        sz = self.size
        inp = self.environment['wsgi.input']
        return inp.read(sz).decode('utf-8')

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
            if len(self.body) == 0:
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

class response(self):
    def __init__(self, pg):
        self._page = pg

    @property
    def data(self):
        # These lines are for XHR responses
        # data = json.dumps(data)
        # data = bytes(data, 'utf-8')

    @property
    def headers(self):
        hdrs = [
            ('Content-Length', str(len(self.data))),
        ]

        # if XHR
        '''
        hdrs.append(
            ('Content-Type', 'application/json'),
            ('Access-Control-Allow-Origin', '*')
        )
        '''


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
