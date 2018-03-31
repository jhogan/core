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

class dbentities(entities):
    def save(self):
        for e in self:
            e.save()

    def TRUNCATE(self):
        conn = connections.getinstance().default
        conn.query('truncate ' + self._table)

    def ALL(self):
        conn = connections.getinstance().default
        res = conn.query('select * from ' + self._table)
        return type(self)(res)

    @property
    def _table(self):
        'The _table property must be implemented'
        raise NotImplementedError(msg)

    def save(self):
        for e in self:
            e.save()

class dbentity(entity):
    # TODO Add Tests

    def __init__(self, id=None):
        super().__init__()
        self.onaftervaluechange += self._self_onaftervaluechange

    def _marknew(self):
        self._isnew = True
        self._isdirty = False

    def _markdirty(self):
        self._isnew = False
        self._isdirty = True

    def _markold(self):
        self._isnew = False
        self._isdirty = False

    def _markclean(self):
        self._isdirty = False

    def _setvalue(self, field, new, prop):
        # TODO: It's nice to strip any string because that's vitually
        # always the desired behaviour.  However, at some point, we
        # will want to save the string to the database with whitespace
        # on either side.  Therefore, we should add a parameter (or
        # something) to make it possible to persiste an unstripped
        # string.
        if type(new) == str:
            new = new.strip()
        return super()._setvalue(field, new, prop)

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

    def save(self):
        if self.isvalid:
            if self.isnew:
                self._insert()
            elif self.isdirty:
                self._update()
            self._isdirty = False
            self._isnew = False
        else:
            raise Exception('Won\'t save invalid object')

    def __repr__(self):
        r = super().__repr__()
        r += ' id: ' + str(self.id)
        r += ' name: ' + self.name
        r += ' email: ' + self.email
        return r

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

    def _reconnect(self):
        self._conn = None # force a reconnect
        self._connection

    def query(self, sql, args=None):
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

class dbresult(entity):
    def __init__(self, row):
        self._row = row

    def __iter__(self):
        for f in self._row:
            yield f
    
