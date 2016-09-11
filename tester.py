from things import *
import pdb; B=pdb.set_trace
import uuid
import inspect
from types import FunctionType
from textwrap import dedent

class testers(things):
    def __init__(self):
        for subcls in tester.__subclasses__():
            inst = subcls()
            self += inst
            for meth in subcls.__dict__.items():
                if type(meth[1]) != FunctionType: continue
                if meth[0][0] == '_': continue
                try:
                    getattr(inst, meth[0])()
                except Exception as ex:
                    inst._failures += failure(ex, assert_=meth[0])
        print('')

class tester(thing):
    def __init__(self):
        self._failures = failures()

    def assertUuid(self, id, msg=None):
        try: uuid.UUID(str(id), version=4)
        except ValueError: self._failures += failure()

    def assertEq(self, expect, actual, msg=None):
        if expect != actual: self._failures += failure()

    def assertIs(self, expect, actual, msg=None):
        if expect is not actual: self._failures += failure()

    def assertNone(self, o, msg=None):
        if o != None: self._failures += failure()

    def assertNotNone(self, o, msg=None):
        if o == None: self._failures += failure()

    def assertCount(self, expect, actual, msg=None):
        if expect != len(actual): self._failures += failure()

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
        return r + "\n" + str(self.failures) + "\n"

    @staticmethod
    def preserve(str):
        return dedent(str)[1:-1]

class failures(things):
    pass

class failure(thing):
    def __init__(self, cause=None, assert_=None):
        self._assert = assert_
        self.cause = cause
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

    def __str__(self):
        if self.cause:
            r = "{}: {} in {}".format(self.cause.__class__.__name__,
                                        str(self.cause),
                                        self._assert)
        else:
            r = "{} in {} at {}".format(self._assert, self._test, self._line)
            if hasattr(self,'_expect'):
                r += "\nexpect: " + str(self._expect)
                r += "\nactual: " + str(self._actual)
        return r
        
