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
from entities import *
import MySQLdb
from pdb import set_trace; B=set_trace
from configfile import configfile
from MySQLdb.constants.ER import BAD_TABLE_ERROR
import uuid

class dbentities(entities):
    def TRUNCATE(self):
        conn = connections.getinstance().default
        conn.query('truncate ' + self._table)

    def ALL(self):
        conn = connections.getinstance().default
        ress = conn.query('select * from ' + self._table)
        return type(self)(ress)

    @property
    def isdirty(self):
        return any([x.isdirty for x in self])

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

    def save(self):
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
            conn.rollback()
            raise
        else:
            conn.commit()
        finally:
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
                                         port=acct.port)
        return self._conn                

    def close(self):
        return self._connection.close()

    def commit(self):
        return self._connection.commit()

    def rollback(self):
        return self._connection.rollback()

    def createcursor(self):
        return self._connection.cursor()

    def _reconnect(self):
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
                    self._reconnect()
                else:
                    raise

class dbresultset(entities):
    def __init__(self, cur):
        super().__init__()
        self._cur = cur
        for r in self._cur:
            self += dbresult(r)

    @property
    def lastrowid(self):
        return self._cur.lastrowid

    def demandhasone(self):
        if not self.hasone:
            raise Exception('A single record was not found')
        return self.first

class dbresult(entity):
    def __init__(self, row):
        self._row = row

    def __iter__(self):
        for f in self._row:
            yield f

    def __getitem__(self, i):
        return self._row[0]
