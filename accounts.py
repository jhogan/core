# vim: set et ts=4 sw=4 fdm=marker

# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2020

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

    def __str__(self):
        user = str(self.username)
        host = str(self.host)
        port = str(self.port)

        return user + '@' + host + ':' + port

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
