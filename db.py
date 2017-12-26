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

class dbentity(entity):
    # TODO Add Tests

    def __init__(self, id=None):
        # TODO Complete
        self.isnew = True
            
    def save(self):
        if self.isnew:
            self._insert()
        elif self.isdirty:
            self._update()

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

    def query(self, sql, args):
        for _ in range(2):
            try:
                conn = self._connection
                cur = conn.cursor()
                cur.execute(sql, args)
                conn.commit()
                return cur
            except MySQLdb.OperationalError as ex:
                print('Reconnect')
                self._reconnect()
