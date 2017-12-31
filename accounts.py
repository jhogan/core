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
# TODO Write Tests
from entities import *
class accounts(entities):
    @property
    def smtpaccounts(self):
        accts = self.where(smtpaccount)
        return smtpaccounts(accts)

    @property
    def mysqlaccounts(self):
        return self.where(mysqlaccount)

class smtpaccounts(accounts):
    @property
    def transactional(self):
        return self.where(lambda x: x.type == 'transactional')

    @property
    def marketing(self):
        return self.where(lambda x: x.type == 'marketing')
                
class account(entity):
    def __init__(self, arr):
        self._uid      = arr['uid']
        self._pwd      = arr['pwd']
        self._host     = arr['host']
        self._port     = arr['port']

    @staticmethod
    def create(arr):
        cls = arr['type'] + 'account'
        cls = getattr(sys.modules['accounts'], cls)
        acct = cls(arr)
        return acct

    @property
    def username(self):
        return self._uid

    @property
    def password(self):
        return self._pwd

    @property
    def host(self):
        return self._host

    @property
    def port(self):
        return self._port

class smtpaccount(account):
    
    def __init__(self, arr):
        super().__init__(arr)
        self._type = arr['smtp-type']

    # Transactional or marketing
    @property
    def type(self):
        return self._type

class mysqlaccount(account):
    
    def __init__(self, arr):
        super().__init__(arr)
        self._db = arr['db']

    @property
    def database(self):
        return self._db

    # Transactional or marketing
    @property
    def type(self):
        return self._type
