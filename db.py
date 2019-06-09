# vim: set et ts=4 sw=4 fdm=marker
"""
MIT License

Copyright (c) 2016 Jesse Hogan

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
# TODO Add Tests
from configfile import configfile
from entities import *
from MySQLdb.constants.ER import BAD_TABLE_ERROR
from pdb import set_trace; B=set_trace
from table import table
import MySQLdb
import warnings
import uuid
import func
from contextlib import contextmanager

# Some errors in MySQL are classified as "warnings" (such as 'SELECT 0/0').
# This means that no exception is raised; just an error message is printed to
# stderr. We want these warnings to be proper exceptions so they
# won't go unnoticed. The below code does just that.
warnings.filterwarnings('error', category=MySQLdb.Warning)

class dbentities(entities):
    def __init__(self, ress=None):
        super().__init__()
        self._isdirty = False

        if ress:
            for res in ress:
                self += self.dbentity(res)

        # The collection may have been added to above. If that is the case, the
        # _isdirty flag will be set to True in the _self_onadd event handler.
        # Set it back to False since we are just __init__'ing the object; it
        # shouldn't be dirty at this point.

        self._isdirty = False

    def TRUNCATE(self):
        conn = connections.getinstance().default
        conn.query('truncate ' + self._table)

    def ALL(self):
        conn = connections.getinstance().default
        ress = conn.query('select * from ' + self._table)
        return type(self)(ress)

    def _self_onadd(self, src, eargs):
        super()._self_onadd(src, eargs)
        self._isdirty = True

    def _self_onremove(self, src, eargs):
        super()._self_onremove(src, eargs)
        self._isdirty = True

    @property
    def isdirty(self):
        return self._isdirty or any([x.isdirty for x in self])

    @property
    def isnew(self):
        return any([x.isnew for x in self])

    @property
    def _table(self):
        msg = '_table must be overridden'
        raise NotImplementedError(msg)

    @property
    def _create(self):
        raise NotImplementedError('_create must be overridden')

    @property
    def connection(self):
        return connections.getinstance().default

    def query(self, sql, args=None, cur=None):
        return self.connection.query(sql, args, cur=None)

    def CREATE(self):
        self.query(self._create)

    def DROP(self):
        self.query('drop table ' + self._table)

    def RECREATE(self):
        try:
            self.DROP()
        except MySQLdb.OperationalError as ex:
            try:
                errno = ex.args[0]
            except:
                raise

            if errno != BAD_TABLE_ERROR: # 1051
                raise

        self.CREATE()

    def save(self, cur=None):
        # TODO Add reconnect logic or a connection pool

        # Clone the default connection. Since transactions are commited
        # by calling commit() on the connection object, we want a new 
        # connection to ensure this transaction is atomic. I'm not sure
        # why MySQLDb uses the connection object for commits. It seems 
        # like there should be a transaction object that commit() could 
        # be called on. Either way, it seems like for now at least, we
        # will have to connect to the database each time there is a need
        # for atomic commits.
        # https://stackoverflow.com/questions/50206523/can-you-perform-multiple-atomic-commits-using-the-same-connection-with-mysqldb

        # If a cursor was not given, we will manage the atomicity of the
        # transaction here. Otherwise, we will assuming the calling code is
        # managing the atomicity.
        tx = not bool(cur)

        if not cur:
            conn = connections.getinstance().default.clone()
            cur = conn.createcursor()
        states = []
        try:
            for e in self:
                states.append((e._isnew, e._isdirty))
                e.save(cur)
        except Exception:
            for i, st in enumerate(states):
                e = self[i]
                e._isnew, e._isdirty = st
            if tx:
                conn.rollback()
            raise
        else:
            if tx:
                conn.commit()
        finally:
            if tx:
                cur.close()
                conn.close()

    def __getitem__(self, key):
        if type(key) == int or type(key) == slice:
            return self._ls[key]

        for e in self._ls:
            if hasattr(e, 'id') and type(key) == uuid.UUID :
                if e.id == key:   return e
            elif hasattr(e, 'name'):
                if e.name == key: return e

    def _tostr(self, fn=str, includeHeader=True, props=None):
        import functools

        def getattr(obj, attr, *args):
            def rgetattr(obj, attr):
                if obj:
                    return builtins.getattr(obj, attr, *args)
                return None
            return functools.reduce(rgetattr, [obj] + attr.split('.'))

        tbl = table()

        if props:
            props = ('ix', 'id') + tuple(props)
        else:
            props = ('ix', 'id')


        if includeHeader:
            r = tbl.newrow()
            for prop in props:
                r.newfield(prop)
            
        for p in self:
            r = tbl.newrow()
            for prop in props:
                if prop == 'ix':
                    v = self.getindex(p)
                else:
                    v = getattr(p, prop)
                    v = v if v else ''
                r.newfield(v)
        return str(tbl)


    def __str__(self):
        return self._tostr()

class dbentity(entity):
    # TODO Add Tests
    def __init__(self, id=None):
        super().__init__()
        self._deleteme = False
        self.onaftervaluechange  +=  self._self_onaftervaluechange

    def _marknew(self):
        self._isnew = True
        self._isdirty = False

    def _markdirty(self):
        self._isdirty = True

    def _markold(self):
        self._isnew = False
        self._isdirty = False

    def markfordeletion(self):
        self._deleteme = True

    def _self_onaftervaluechange(self, src, eargs):
        if not self.isnew:
            self._markdirty()

    @property
    def isnew(self):
        return self._isnew

    @property
    def isdirty(self):
        return self._isdirty 

    @property
    def id(self):
        return self._id

    @property
    def _table(self):
        return self._collection()._table

    @property
    def connection(self):
        return connections.getinstance().default

    def query(self, sql, args, cur=None):
        return self.connection.query(sql, args, cur)

    def save(self, cur=None):
        if not (self.isnew or self.isdirty or self._deleteme):
           return

        if self._deleteme:
            if self._isnew:
               raise Exception("Can't delete row that doesn't exist.")
            else:
                self._delete()

        if self.isvalid:
            if self.isnew:
                self._insert(cur)
            elif self.isdirty:
                self._update()
            self._isdirty = False
            self._isnew = False
        else:
            raise brokenruleserror('Won\'t save invalid object', self)

    def delete(self):
        sql = 'delete from ' + self._table + ' where id = %s'

        args = (self.id.bytes,)

        ress = self.query(sql, args)

        self._marknew()

        return ress.rowcount

class connections(entities):

    _instance = None
    def __init__(self):
        super().__init__()
        cfg = configfile.getinstance()
        accts = cfg.accounts.mysqlaccounts
        for acct in accts:
            self += connection(acct)

    @classmethod
    def getinstance(cls):
        if cls._instance == None:
            cls._instance = connections()
        return cls._instance

    @property
    def default(self):
        return self.first

class connection(entity):
    def __init__(self, acct):
        self._account = acct
        self._conn = None

    def clone(self):
        return type(self)(self._account)

    @property
    def account(self):
        return self._account

    @property
    def _connection(self):
        if not self._conn:
            acct = self.account
            self._conn = MySQLdb.connect(acct.host, acct.username, 
                                         acct.password, acct.database, 
                                         port=acct.port, charset='utf8mb4',
                                         use_unicode=True)
        return self._conn                

    def kill(self):
        try:
            _conn = self._connection
            id = _conn.thread_id()
            _conn.kill(id)
        except MySQLdb.OperationalError as ex:
            # If exception isn't 1317, 'Query execution was interrupted'),
            # re-raise
            if ex.args[0] not in (1317, 2006):
                raise

    def close(self):
        return self._connection.close()

    @property
    def isopen(self):
        return bool(self._connection.open)

    def commit(self):
        return self._connection.commit()

    def rollback(self):
        return self._connection.rollback()

    def createcursor(self):
        return self._connection.cursor()

    def reconnect(self):
        self._conn = None # force a reconnect
        self._connection

    def query(self, sql, args=None, cur=None):
        if cur != None:
            cur.execute(sql, args)
            return dbresultset(cur)

        for _ in range(2):
            try:
                conn = self._connection
                cur = conn.cursor()
                cur.execute(sql, args)
                conn.commit()
                return dbresultset(cur)
            except MySQLdb.OperationalError as ex:
                # Reconnect if the connection object has timed out and no
                # longer holds a connection to the database.
                # https://stackoverflow.com/questions/3335342/how-to-check-if-a-mysql-connection-is-closed-in-python

                try:
                    errno = ex.args[0]
                except:
                    errno = ''

                isopen = conn.open

                if errno == 2006 or not isopen:
                    msg = 'Reconnect[{0}]: errno: {1}; isopen: {2}'
                    msg = msg.format(_, errno, isopen)

                    self.log.debug('Reconnect ' + str(_))
                    self.reconnect()
                else:
                    raise

# TODO The 'db' prefix on these class names are redundant.
class dbresultset(entities):
    """ Represents a collections of rows returned from a db query. """
    def __init__(self, cur):
        super().__init__()
        self._cur = cur
        for r in self._cur:
            self += dbresult(r, self)

    @property
    def lastrowid(self):
        return self._cur.lastrowid

    @property
    def rowcount(self):
        return self._cur.rowcount

    def demandhasone(self):
        if not self.hasone:
            raise recordnotfounderror('A single record was not found')
        return self.first

    def __repr__(self):
        tbl = table()

        for i, res in func.enumerate(self):
            if i.first:
                hdr = tbl.newrow()
                for f in res.fields:
                    hdr.newfield(f.name)

            r = tbl.newrow()
            for f in res.fields:
                r.newfield(f.value)

        return str(tbl)

    def __str__(self):
        return repr(self)

class dbresult(entity):
    """ Represents a row returned from a db query. """
    def __init__(self, row, ress):
        super().__init__()
        self._row = row
        self._ress = ress
        self.fields = dbresultfields()
        for i, _ in enumerate(self._row):
            self.fields += dbresultfield(i, self)

    def __getitem__(self, i):
        if type(i) is str:
            # If i is str, it's a column name. Use the description property to
            # get the index to pass to _row
            desc = self._ress._cur.description
            i = [x[0] for x in desc].index(i)
        return self._row[i]

class dbresultfields(entities):
    pass

class dbresultfield(entity):
    """ Represents a field within a dbresult. """
    def __init__(self, ix, res):
        self.index = ix
        self.dbresult = res
    
    @property
    def name(self):
        desc = self.dbresult._ress._cur.description
        return desc[self.index][0]

    @property
    def value(self):
        return self.dbresult._row[self.index]

class recordnotfounderror(Exception):
    pass

class pool(entity):
    _default = None

    def __init__(self):
        # TODO Currently, connections.__init__() populates itself with
        # connection objects from the config file so we can't use it for
        # collecting connections objects that are in and out of the pool.
        self._in = entities()
        self._out = entities()

    @staticmethod
    def getdefault():
        if not pool._default:
            pool._default = pool()

            # Seed with one connection
            pool._default._in += connections.getinstance().default.clone()
        return pool._default

    def pull(self):
        conn = self._in.pop()

        # Grow as needed
        if not conn:
            conn = self._out.last.clone()

        self._out += conn

        return conn

    def push(self, conn):
        self._in += self._out.remove(conn)

    @contextmanager
    def take(self):
        conn = self.pull()

        yield conn

        self.push(conn)

class operationeventargs(eventargs):
    def __init__(self, e, op, sql, args):
        self.entity  =  e
        self.op      =  op
        self.sql     =  sql
        self.args    =  args

class chronicler(entity):
    _instance = None

    def __init__(self):
        self.chronicles = chronicles(self)
        self.max = 20

    @staticmethod
    def getinstance():
        if not chronicler._instance:
            chronicler._instance = chronicler()
        return chronicler._instance

    def append(self, obj):
        self.chronicles += obj

    def __iadd__(self, t):
        self.append(t)
        return self

class chronicles(entities):
    def __init__(self, chronicler=None, initial=None):
        self.chronicler = chronicler
        super().__init__(initial=initial)

    def append(self, obj, uniq=False, r=None):
        if self.chronicler and self.count == self.chronicler.max - 1:
            self.shift()
        
        super().append(obj, uniq=False, r=None)

    def where(self, p1, p2=None):
        if (type(p1), type(p2)) == (str, type(None)):
            # Passing in one argument will result in a test of p1 against
            # the value of 'op'.
            p1, p2 = 'op', p1

        return super().where(p1, p2)

    def __str__(self):
        return self._tostr(includeHeader=False)

class chronicle(entity):
    def __init__(self, e, op, sql, args):
        self.entity  =  e
        self.op      =  op
        self.sql     =  sql
        self.args    =  args

    def __str__(self):
        if self.op in ('reconnect',):
            return 'DB: ' + self.op.upper()

        args = []
        for arg in self.args:
            if type(arg) is bytes:
                try:
                    arg = uuid.UUID(bytes=arg)
                except:
                    pass
            args.append(arg)
        sql = self.sql.strip()

        r = '%s\n%s\n'
        r %= (
            sql,
            tuple(args)
        )
        return r

class executioner(entity):
    def __init__(self, exec, max=2):
        self._execute = exec
        self.max = max
        self.onbeforereconnect  =  event()
        self.onafterreconnect   =  event()
    
    def execute(self, es=None):
        pl = pool.getdefault()
        for i in range(self.max):
            conn = pl.pull()
            cur = conn.createcursor()

            try:
                if es:
                    self._execute(cur, es)
                else:
                    self._execute(cur)
            except MySQLdb.OperationalError as ex:
                # Reconnect if the connection object has timed out and no
                # longer holds a connection to the database.
                # https://stackoverflow.com/questions/3335342/how-to-check-if-a-mysql-connection-is-closed-in-python

                if i + 1 == self.max:
                    raise

                try:
                    errno = ex.args[0]
                except:
                    errno = ''

                if errno in (2006, 2013) or not conn.isopen:
                    msg = 'Reconnect[{0}]: errno: {1}; isopen: {2}'
                    msg = msg.format(i, errno, conn.isopen)
                    self.log.debug(msg)

                    eargs = operationeventargs(self, 'reconnect', None, None)
                    self.onbeforereconnect(self, eargs)

                    conn.reconnect()

                    self.onafterreconnect(self, eargs)
                else:
                    conn.rollback()
                    raise
            except Exception as ex:
                conn.rollback()
                raise
            else:
                conn.commit()
                return
            finally:
                cur.close()
                pl.push(conn)

