# vim: set et ts=4 sw=4 fdm=marker

# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2021

# TODO Write Tests
from entities import *
class accounts(entities):
    @property
    def smtpaccounts(self):
        accts = self.where(smtpaccount)
        return smtpaccounts(accts)

class smtpaccounts(accounts):
    @property
    def transactional(self):
        return self.where(lambda x: x.type == 'transactional')

    @property
    def marketing(self):
        return self.where(lambda x: x.type == 'marketing')
                
class account(entity):
    def __init__(self, username, password, host, port):
        self._uid   =  username
        self._pwd   =  password
        self._host  =  host
        self._port  =  port

    @property
    def username(self):
        return self._uid

    @property
    def password(self):
        return self._pwd

    @password.setter
    def password(self, v):
        self._pwd = v

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

class mysql(account):
    def __init__(self, database, port=3306, *args, **kwargs):
        super().__init__(port=port, *args, **kwargs)
        self._db = database

    @property
    def database(self):
        return self._db

    def __repr__(self):
        return self.url

    def __str__(self):
        return self.url

    @property
    def url(self):
        if self.port == 3306:
            args = self.username, self.host, self.database
            return 'mysql://%s@%s/%s' % args

        args = self.username, self.host, self.port, self.database
        return 'mysql://%s@%s:%s/%s' % args
