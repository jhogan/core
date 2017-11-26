import json
import sys
from functools import reduce
import pdb; B=pdb.set_trace
from pprint import pprint

class application:
    
    def __init__(self):
        self.clear()

    def clear(self):
        self._requestbody = None
        self._requestsize = None
        self._requestdata = None
        self._class = None
        self._method = None

    @property
    def environment(self):
        return self._env 

    @property
    def requestsize(self):
        if self._requestsize == None:
            try:
                self._requestsize = int(self.environment.get('CONTENT_LENGTH', 0))
            except(ValueError):
                self._requestsize = 0
        return self._requestsize
           
    @property
    def requestbody(self):
        if self._requestbody == None:
            reqsize = self.requestsize
            self._requestbody = self.environment['wsgi.input'].read(reqsize).decode('utf-8')
            if len(self._requestbody) == 0:
                raise http400('No data in post')
        return self._requestbody

    @property
    def requestdata(self):
        if self._requestdata == None:
            reqbody = self.requestbody

            try:
                self._requestdata = json.loads(reqbody)
            except json.JSONDecodeError as ex:
                raise http400(str(ex))
        return self._requestdata

    @property
    def class_(self):
        if self._class == None:
            try:
                reqdata = self.requestdata
                cls = reqdata['_class']
                if cls not in self.classes:
                    raise http404('Invalid class')
                self._class  = reduce(getattr, cls.split('.'), sys.modules[__name__])
            except KeyError:
                msg = 'The class value was not supplied. Check input.'
                raise ValueError(msg)
        return self._class

    @property
    def method(self):
        if self._method == None:
            try:
                reqdata = self.requestdata
                self._method = reqdata['_method']
            except KeyError:
                msg = 'The method value was not supplied. Check input.'
                raise ValueError(msg)
            if self._method[0] == '_':
                raise http404('Invalid method')
        return self._method

    @property
    def classes(self):
        return ['user']

    def __call__(self, env, sres):
        
        self.clear()
        self._env = env
        
        try:
            reqdata = self.requestdata

            cls, meth = self.class_, self.method

            data = getattr(cls, meth)(reqdata)

        except Exception as ex:
            if isinstance(ex, httperror):
                statuscode = ex.statuscode
            else:
                statuscode = '500 Internal Server Error'

            data = {'_exception': repr(ex)}

        else:
            statuscode = '200 OK'

        finally:
            data = json.dumps(data)
            data = bytes(data, 'utf-8')

            resheads=[
                ('Content-Length', str(len(data))),
                ('Content-Type', 'application/json'),
                ('Access-Control-Allow-Origin', '*'),

            ]

            sres(statuscode, resheads)
            return iter([data])

app = application()

class httperror(Exception):
    def __init__(self, statuscode, msg):
        self.statuscode = statuscode
        self.message = msg

    def __repr__(self):
        return self.message

class http404(httperror):
    def __init__(self, msg):
        super().__init__('404 Not Found', msg)

class http400(httperror):
    def __init__(self, msg):
        super().__init__('400 Bad Request', msg)

class user:

    @staticmethod
    def getuser(data):
        id = data['id']
        if id == 1:
            return {'email': 'jessehogan0@gmail.com'}
        elif id == 2:
            return {'email': 'dhogan.d@gmail.com'}
        elif id == 3:
            from time import sleep
            sleep(10)

            return {'email': 'sleepy@gmail.com'}
        else:
            raise ValueError('Invalid user id: ' + str(id))

