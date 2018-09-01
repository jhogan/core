from entities import *
from pprint import pprint
from textwrap import dedent
from types import FunctionType
import inspect
import json
import pdb; B=pdb.set_trace
import pprint
import sys
import uuid
from pprint import pprint
from configfile import configfile

# TODO Ensure tester.py won't run in non-dev environment

class invoketesteventargs(eventargs):
    def __init__(self, meth):
        self.method = meth

class testers(entities):
    def __init__(self, initial=None):
        self.oninvoketest = event()
        super().__init__(initial=initial)
        self.breakonexception = False


    def run(self, tu=None):
        testclass, testmethod, *_ = tu.split('.') + [None] if tu else [None] * 2

        cfg = configfile.getinstance()
        if cfg.isloaded and cfg.inproduction:
            raise Exception("Won't run in production environment.")

        for subcls in tester.__subclasses__():
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
                    eargs = invoketesteventargs(meth)
                    self.oninvoketest(self, eargs)
                    getattr(inst, meth[0])()
                except Exception as ex:
                    if self.breakonexception:
                        print(ex)
                        pdb.post_mortem(ex.__traceback__)
                    inst._failures += failure(ex, assert_=meth[0])
        print('')

    def __str__(self):
        return self._tostr(str, includeHeader=False)

class tester(entity):
    def __init__(self):
        self._failures = failures()
        self.testers = None

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

    def assertGt(self, expect, actual, msg=None):
        if not (expect > actual): self._failures += failure()

    def assertGe(self, expect, actual, msg=None):
        if not (expect >= actual): self._failures += failure()

    def assertLt(self, expect, actual, msg=None):
        if not (expect < actual): self._failures += failure()

    def assertLe(self, expect, actual, msg=None):
        if not (expect <= actual): self._failures += failure()

    def assertIs(self, expect, actual, msg=None):
        if expect is not actual: self._failures += failure()

    def assertNone(self, o, msg=None):
        if o != None: self._failures += failure()

    def none(self, o, msg=None):
        if o != None: self._failures += failure()

    def assertNotNone(self, o, msg=None):
        if o == None: self._failures += failure()

    def assertZero(self, actual):
        if len(actual) != 0: self._failures += failure()

    def zero(self, actual):
        if len(actual) != 0: self._failures += failure()

    def assertOne(self, actual):
        if len(actual) != 1: self._failures += failure()

    def one(self, actual):
        if len(actual) != 1: self._failures += failure()

    def assertTwo(self, actual):
        if len(actual) != 2: self._failures += failure()

    def two(self, actual):
        if len(actual) != 2: self._failures += failure()

    def assertThree(self, actual):
        if len(actual) != 3: self._failures += failure()

    def three(self, actual):
        if len(actual) != 3: self._failures += failure()

    def nine(self, actual):
        if len(actual) != 9: self._failures += failure()

    def ten(self, actual):
        if len(actual) != 10: self._failures += failure()

    def eleven(self, actual):
        if len(actual) != 11: self._failures += failure()

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

    def assertBroken(self, ent, prop, rule):
        if not ent.brokenrules.contains(prop, rule):
            self._failures += failure()

    def broken(self, ent, prop, rule):
        if not ent.brokenrules.contains(prop, rule):
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
        r += "[{}]{}{}".format(name, ' ' * (72 - len(name)), ok)

        if self.failures.isempty:
            return r
        return r + "\n" + self.failures._tostr(includeHeader=False) + "\n"

    @staticmethod
    def preserve(str):
        return dedent(str)[1:-1]

    def post(self, cls, meth, args):
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
    def __init__(self, cause=None, assert_=None, ent=None):
        self._assert = assert_
        self.cause = cause
        self.entity = ent
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
        
