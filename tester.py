from entities import *
from textwrap import dedent
from types import FunctionType
import inspect
import json
import pdb; B=pdb.set_trace
import pprint
import sys
import uuid

class invoketesteventargs(eventargs):
    def __init__(self, meth):
        self.method = meth

class testers(entities):
    def __init__(self, initial=None):
        self.oninvoketest = event()
        super().__init__(initial=initial)

    def run(self):
        for subcls in tester.__subclasses__():
            inst = subcls()
            self += inst
            for meth in subcls.__dict__.items():
                if type(meth[1]) != FunctionType: continue
                if meth[0][0] == '_': continue
                try:
                    eargs = invoketesteventargs(meth)
                    self.oninvoketest(self, eargs)
                    getattr(inst, meth[0])()
                except Exception as ex:
                    raise
                    inst._failures += failure(ex, assert_=meth[0])
        print('')

    def __str__(self):
        return self._tostr(str, includeHeader=False)

class tester(entity):
    def __init__(self):
        self._failures = failures()

    def assertUuid(self, id, msg=None):
        try: uuid.UUID(str(id), version=4)
        except ValueError: self._failures += failure()

    def assertTrue(self, actual, msg=None):
        if not actual: self._failures += failure()

    def assertFalse(self, actual, msg=None):
        if actual: self._failures += failure()

    def assertFail(self, msg=None):
        self._failures += failure()

    def assertPositive(self, actual):
        if actual < 0: self._failures += failure()

    def assertIsInstance(self, expect, actual, msg=None):
        if not isinstance(expect, actual): self._failures += failure()

    def assertEq(self, expect, actual, msg=None):
        if expect != actual: self._failures += failure()

    def assertNe(self, expect, actual, msg=None):
        if expect == actual: self._failures += failure()

    def assertGt(self, expect, actual, msg=None):
        if not (expect > actual): self._failures += failure()

    def assertLt(self, expect, actual, msg=None):
        if not (expect < actual): self._failures += failure()

    def assertIs(self, expect, actual, msg=None):
        if expect is not actual: self._failures += failure()

    def assertNone(self, o, msg=None):
        if o != None: self._failures += failure()

    def assertNotNone(self, o, msg=None):
        if o == None: self._failures += failure()

    def assertCount(self, expect, actual, msg=None):
        if expect != len(actual): self._failures += failure()

    def assertValid(self, ent):
        if not ent.isvalid:
            self._failures += failure(ent=ent)

    def assertInValid(self, ent):
        if ent.isvalid:
            self._failures += failure(ent=ent)

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
        
