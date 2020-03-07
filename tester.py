# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2020

from configfile import configfile
from contextlib import contextmanager, suppress
from dbg import B
from entities import *
from pprint import pprint
from textwrap import dedent
from timer import stopwatch
from types import FunctionType
import argparse
import dom
import inspect
import json
import pdb
import pom
import pprint
import primative
import io
import sys
import textwrap
import urllib
import uuid
import http

# TODO Ensure tester.py won't run in non-dev environment

# TODO When creating the file API, consider
# wsgiref.util.FileWrapper(filelike, blksize)

class invoketesteventargs(eventargs):
    def __init__(self, cls, meth):
        self.class_ = cls
        self.method = meth

class testers(entities):
    def __init__(self, initial=None):
        self.oninvoketest = event()
        super().__init__(initial=initial)
        self.breakonexception = False

    def run(self, tu=None):
        # TODO testclass and testmethod would probably be better as
        # global variables. That would allow us to have a `testmethods`
        # property (see the TODO below).

        testclass, testmethod, *_ = tu.split('.') + [None] if tu else [None] * 2

        cfg = configfile.getinstance()
        if cfg.isloaded and cfg.inproduction:
            raise Exception("Won't run in production environment.")

        for subcls in self.testerclasses:
            if testclass and subcls.__name__ != testclass:
                continue

            inst = subcls()
            inst.testers = self
            self += inst

            for meth in subcls.__dict__.items():

                if type(meth[1]) != FunctionType: continue
                if meth[0][0] == '_': continue
                if testmethod and testmethod != meth[0]:
                    continue
                try:
                    eargs = invoketesteventargs(subcls, meth)
                    self.oninvoketest(self, eargs)
                    getattr(inst, meth[0])()
                except Exception as ex:
                    if self.breakonexception:
                        print(ex)
                        pdb.post_mortem(ex.__traceback__)
                    inst._failures += failure(ex, assert_=meth[0])
                finally:
                    inst.eventregistrations.unregister()
        print('')

    @property
    def testerclasses(self):
        return tester.__subclasses__()

    @property
    def ok(self):
        # TODO Remove brackets. Also, shouldn't any be replaced with
        # all... not really sure.

        return any([x.ok for x in self])

    def __str__(self):
        return self._tostr(str, includeHeader=False)

class tester(entity):
    class _browsers(http.browsers):
        pass

    class _browser(http.browser):
        def __init__(self, t, *args, **kwargs):
            self.tester = t

        class _tabs(http.browser._tabs):
            def __init__(self, brw, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.browser = brw

            def tab(self):
                t = tester._browser._tab(self)
                self += t
                return t

        class _tab(http.browser._tab):
            def __init__(self, tabs):
                self.tabs = tabs

            @property
            def browser(self):
                return self.tabs.browser

            def get(self, pg, ws):
                return self._request(pg=pg, ws=ws, meth='GET')

            def post(self, pg, ws, frm):
                return self._request(pg=pg, ws=ws, frm=frm, meth='POST')

            def head(self, pg, ws):
                return self._request(pg=pg, ws=ws, meth='HEAD')

            def _request(self, pg, ws, frm=None, meth='GET'):
                if not isinstance(pg, str):
                    raise TypeError('pg parameter must be a str')

                if not isinstance(ws, pom.site):
                    raise TypeError('ws parameter must be a pom.site')

                if frm and not isinstance(frm, dom.form):
                    raise TypeError('frm parameter must be a dom.form')

                def create_environ(env=None):
                    # TODO We may want to leverage
                    # `wsgiref.util.setup_testing_defaults(environ)`# here

                    # TODO Should content_length be an empty str. Maybe it should be
                    # 0 by default, or more likely, it should be removed from this
                    # dict.
                    d = {
                        'content_length': '',
                        'content_type': 'application/x-www-form-urlencoded',
                        'http_accept': '*/*',
                        'http_host': '127.0.0.0:8000',
                        'http_user_agent': 'tester/1.0',
                        'raw_uri': '/',
                        'remote_addr': '52.52.249.177',
                        'remote_port': '43130',
                        'script_name': '',
                        'server_port': '8000',
                        'server_protocol': 'http/1.1',
                        'server_software': 'gunicorn/19.4.5',
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
                        d['http_cookie'] = cookies.header.value

                    if env:
                        for k, v in env.items():
                            d[k] = v
                    
                    return http.headers(d)


                st, hdrs = None, None
                
                def start_response(st0, hdrs0):
                    nonlocal st
                    nonlocal hdrs
                    st, hdrs = st0, hdrs0

                url = urllib.parse.urlparse(pg)

                pg = ws(url.path)

                pg and pg.clear()

                if meth == 'POST':
                    inp = io.BytesIO(frm.post)

                    env = create_environ({
                        'content_length':  len(frm.post),
                        'wsgi.input':      inp,
                    })
                else: 
                    env = create_environ()

                env['path_info']       =  url.path
                env['query_string']    =  url.query
                env['server_name']     =  ws.host
                env['server_site']     =  ws
                env['request_method']  =  meth

                # Create WSGI app
                app = http.application()

                # Create request. Associate with app.
                req = http._request(app)

                app.breakonexception = \
                    self.browser.tester.testers.breakonexception
                
                # Make WSGI call

                # NOTE PEP 0333 insist that the environment variables
                # passed in must be a dict so we convert `env` which is
                # an http.headers object.
                iter = app(dict(env.list), start_response)

                res = http._response(req) 
                res._status = st
                res._headers = http.headers(hdrs)
                res.payload = next(iter)

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

                return res

        def __init__(self, tester, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.tester = tester
            self.tabs = tester._browser._tabs(self)

        def tab(self):
            return self.tabs.tab()


    def __init__(self):
        self._failures = failures()
        self.testers = None
        self.eventregistrations = eventregistrations()

    def browser(self):
        return tester._browser(self)

    def print(self, *args, **kwargs):
        print(*args, **kwargs)

    @property
    def ok(self):
        return self.failures.isempty

    @staticmethod
    def dedent(str, *args):
        return textwrap.dedent(str).strip() % args

    def register(self, event, handler):
        self.eventregistrations.register(event, handler)

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
            raise ValueError('Assert type instead')

        try: 
            uuid.UUID(str(id), version=4)
        except ValueError: 
            self._failures += failure()

    def uuid(self, id, msg=None):
        if isinstance(id, uuid.UUID):
            raise ValueError('Assert type instead')

        try: 
            uuid.UUID(str(id), version=4)
        except ValueError: 
            self._failures += failure()

    def assertTrue(self, actual, msg=None):
        if type(actual) != bool:
            raise ValueError('actual must be bool')

        if not actual: self._failures += failure()

    def true(self, actual, msg=None):
        if type(actual) != bool:
            raise ValueError('actual must be bool')

        if not actual: self._failures += failure()

    def assertTruthy(self, actual, msg=None):
        if not actual: self._failures += failure()

    def assertFalse(self, actual, msg=None):
        if type(actual) != bool:
            raise ValueError('actual must be bool')

        if actual: self._failures += failure()

    def false(self, actual, msg=None):
        if type(actual) != bool:
            raise ValueError('actual must be bool')

        if actual: self._failures += failure()

    def assertFalsey(self, actual, msg=None):
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
        if type(actual) is not expect: self._failures += failure()

    def assertEq(self, expect, actual, msg=None):
        if expect != actual: self._failures += failure()

    def eq(self, expect, actual, msg=None):
        if expect != actual: self._failures += failure()

    def assertNe(self, expect, actual, msg=None):
        if expect == actual: self._failures += failure()

    def ne(self, expect, actual, msg=None):
        if expect == actual: self._failures += failure()

    def assertGt(self, expect, actual, msg=None):
        if not (expect > actual): self._failures += failure()

    def gt(self, expect, actual, msg=None):
        if not (expect > actual): self._failures += failure()

    def assertGe(self, expect, actual, msg=None):
        if not (expect >= actual): self._failures += failure()

    def ge(self, expect, actual, msg=None):
        if not (expect >= actual): self._failures += failure()

    def assertLt(self, expect, actual, msg=None):
        if not (expect < actual): self._failures += failure()

    def assertLe(self, expect, actual, msg=None):
        if not (expect <= actual): self._failures += failure()

    def lt(self, expect, actual, msg=None):
        if not (expect < actual): self._failures += failure()

    def le(self, expect, actual, msg=None):
        if not (expect <= actual): self._failures += failure()

    def assertIs(self, expect, actual, msg=None):
        if expect is not actual: self._failures += failure()

    def is_(self, expect, actual, msg=None):
        if expect is not actual: self._failures += failure()

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

    def assertCount(self, expect, actual, msg=None):
        if expect != len(actual): self._failures += failure()

    def count(self, expect, actual, msg=None):
        if expect != len(actual): self._failures += failure()

    def assertValid(self, ent):
        v = ent.isvalid
        if type(v) != bool:
            raise Exception('invalid property must be a boolean')
        if not v:
            self._failures += failure(ent=ent)

    def valid(self, ent):
        v = ent.isvalid
        if type(v) != bool:
            raise Exception('invalid property must be a boolean')
        if not v:
            self._failures += failure(ent=ent)

    def assertInValid(self, ent):
        v = ent.isvalid
        if type(v) != bool:
            raise Exception('invalid property must be a boolean')
        if v:
            self._failures += failure(ent=ent)

    def invalid(self, ent):
        v = ent.isvalid
        if type(v) != bool:
            raise Exception('invalid property must be a boolean')
        if v:
            self._failures += failure(ent=ent)

    def assertBroken(self, ent, prop, rule):
        if not ent.brokenrules.contains(prop, rule):
            self._failures += failure()

    def broken(self, ent, prop, rule):
        if not ent.brokenrules.contains(prop, rule):
            self._failures += failure()

    def unique(self, ls):
        if len(ls) != len(set(ls)): self._failures += failure()

    def expect(self, expect, fn, msg=None):
        try:
            if not callable(fn):
                raise NotCallableError((
                    'The fn parameter must be a callable object. '
                    'Consider using a function or lambda instead of '
                    'a: ' + type(fn).__name__
                ))

            fn()

        except Exception as ex:
            if type(ex) is not expect:
                self._failures += failure(actual=ex)
        else:
            if expect is not None:
                self._failures += failure(actual=None)

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
        r += "[{}]{}{}".format(name, ' ' * (72 - len(name) - 4), ok)

        if self.failures.isempty:
            return r
        return r + "\n" + self.failures._tostr(includeHeader=False) + "\n"

    @staticmethod
    def preserve(str):
        return dedent(str)[1:-1]

    @staticmethod
    def _createenv(env=None):
        # TODO Should content_length be an empty str. Maybe it should be
        # 0 by default, or more likely, it should be removed from this
        # dict.

        # TODO We may want to leverage
        # `wsgiref.util.setup_testing_defaults(environ)` here
        d = {
			'content_length': '',
			'content_type': 'application/x-www-form-urlencoded',
			'http_accept': '*/*',
			'http_host': '127.0.0.0:8000',
			'http_user_agent': 'tester/1.0',
			'raw_uri': '/',
			'remote_addr': '52.52.249.177',
			'remote_port': '43130',
			'script_name': '',
			'server_port': '8000',
			'server_protocol': 'http/1.1',
			'server_software': 'gunicorn/19.4.5',
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

        if env:
            for k, v in env.items():
                d[k] = v
        
        return http.headers(d)

    def status(self, st, res):
        if st != res.status: self._failures += failure()

    def head(self, pg, ws):
        return self._request(pg=pg, ws=ws, meth='HEAD')

    def get(self, pg, ws):
        return self._request(pg=pg, ws=ws, frm=None, meth='GET')

    def post(self, pg, ws, frm):
        return self._request(pg=pg, ws=ws, frm=frm, meth='POST')

    def _request(self, pg, ws, frm=None, meth='GET'):
        if not isinstance(pg, str):
            raise TypeError('pg parameter must be a str')

        if not isinstance(ws, pom.site):
            raise TypeError('ws parameter must be a pom.site')

        if frm and not isinstance(frm, dom.form):
            raise TypeError('frm parameter must be a dom.form')

        st, hdrs = None, None
        
        def start_response(st0, hdrs0):
            nonlocal st
            nonlocal hdrs
            st, hdrs = st0, hdrs0

        url = urllib.parse.urlparse(pg)

        pg = ws(url.path)

        pg and pg.clear()

        if meth == 'POST':
            inp = io.BytesIO(frm.post)

            env = self._createenv({
                'content_length':  len(frm.post),
                'wsgi.input':      inp,
            })
        else: 
            env = self._createenv()

        env['path_info']       =  url.path
        env['query_string']    =  url.query
        env['server_name']     =  ws.host
        env['server_site']     =  ws
        env['request_method']  =  meth

        # Create WSGI app
        app = http.application()

        # Create request. Associate with app.
        req = http._request(app)

        app.breakonexception = self.testers.breakonexception

        # Make WSGI call
        # NOTE PEP 0333 insist that the environment variables passed in
        # must be a dict so we convert `env` which is an http.headers
        # object.
        iter = app(dict(env.list), start_response)

        res = http._response(req) 
        res._status = st
        res._headers = http.headers(hdrs)
        res.payload = next(iter)

        return res

    def xhrpost(self, cls, meth, args):
        # NOTE This is currently unused and is left here for now for
        # reference purposese. It was used as a generic XHR endpoint. It
        # was originally called 'post' but post is now used for
        # traditional HTTP POSTs. This will all likely change in the
        # future.

        # TODO Consider using the _request() method
        import app

        body = {
            '__class': cls,
            '__method': meth,
            '__args': args,
        }

        def sres(statuscode0, resheads0):
            global statuscode
            global resheads
            statuscode, resheads = statuscode0, resheads0

        # TODO Use the self._createenv() method to build the env
        # variable.
        env= {
			'content_length': len(body),
			'content_type': 'application/x-www-form-urlencoded',
			'http_accept': '*/*',
			'http_host': '127.0.0.0:8000',
			'http_user_agent': 'tester/1.0',
			'path_info': '/',
			'query_string': '',
			'raw_uri': '/',
			'remote_addr': '52.52.249.177',
			'remote_port': '43130',
			'request_method': 'post',
			'script_name': '',
			'server_name': '172.31.9.64',
			'server_port': '8000',
			'server_protocol': 'http/1.1',
			'server_software': 'gunicorn/19.4.5',
			'gunicorn.socket': None,
			'wsgi.errors': None,
			'wsgi.file_wrapper': None,
			'wsgi.input': body,
			'wsgi.multiprocess': False,
			'wsgi.multithread': False,
			'wsgi.run_once': False,
			'wsgi.url_scheme': 'http',
			'wsgi.version': (1, 0)
		}

        app.app.breakonexception = self.testers.breakonexception
        iter = app.app(env, sres)

        for body in iter:
            body = body.decode('utf-8')
            body = json.loads(body)
            statusmessage = statuscode
            statuscode0 = int(statuscode[:3])
            return httpresponse(statuscode0, statusmessage, resheads, body)

class eventregistrations(entities):
    def register(self, event, handler):
        er = eventregistration(event, handler)
        er.register()
        self += er

    def unregister(self):
        for er in self:
            er.unregister()
        self.clear()

class eventregistration(entity):
    def __init__(self, event, handler):
        self.event = event
        self.handler = handler
        super().__init__()

    def register(self):
        self.event += self.handler

    def unregister(self):
        self.event -= self.handler

class httpresponse(entity):
    def __init__(self, statuscode, statusmessage, headers, body):
        self.statuscode = statuscode
        self.statusmessage = statusmessage
        self.headers = headers
        self.body = body

    @property
    def brokenrules(self):
        brs = brokenrules()
        if self.statuscode < 200 or self.statuscode > 400:
            brs += brokenrule('Status code is not valid: ' + str(self.statuscode))

        if self.body['__exception']:
            brs += brokenrules('Exception was returned');

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
            
class failures(entities):
    pass

class failure(entity):
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
                self._message = inspect.getargvalues(stack[1][0])[3]['msg']
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
        # If we are instantiating, convert the @classmethod cli.run to the
        # instance method cli._run. This makes it possible to call the run()
        # method either as cli.run() or cli().run(). This also works with
        # subclasses of cli. This makes it convenient for unit test developers
        # who may or may not want to customize or override the default
        # implementation.
        #
        # See M. I. Wright's comment at:
        # https://stackoverflow.com/questions/28237955/same-name-for-classmethod-and-instancemethod
        self.run = self._run
        
        self._testers = None

        self.parseargs()

        self.registertraceevents()

    @property
    def testers(self):
        if self._testers is None:
            self._testers = testers()
        return self._testers

    @classmethod
    def run(cls):
        cls().run()

    def _run(self):
        ts = self.testers

        # Run tests
        ts.run(self.args.testunit)

        # Show results
        print(ts)

        # Return exit code (0=success, 1=fail)
        sys.exit(int(not ts.ok))

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
        p = argparse.ArgumentParser()
        p.add_argument('testunit',  help='The test class or method to run',  nargs='?')
        p.add_argument('-b', '--break-on-exception', action='store_true', dest='breakonexception')
        self.args = p.parse_args()

        self.testers.breakonexception = self.args.breakonexception

    def registertraceevents(self):
        ts = self.testers
        ts.oninvoketest += lambda src, eargs: print('# ', end='', flush=True)

        def f(src, eargs):
            print(eargs.class_.__name__ + '.' + eargs.method[0], flush=True)

        ts.oninvoketest += f

class NotCallableError(Exception):
    pass
