# vim: set et ts=4 sw=4 fdm=marker

# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2020

# TODO Write Tests
from accounts import *
from entities import *
from logs import *
from pprint import pprint
import os
import yaml

class configfile(entity):
    _instance = None

    def __init__(self):
        self.isloaded = False
        try:
            self.file = os.environ['EPIPHANY_YAML']
        except KeyError:
            pass

    @classmethod
    def getinstance(cls):

        if cls._instance == None:
            cls._instance = configfile()

        return cls._instance

    @property
    def file(self):
        return self._file

    @file.setter
    def file(self, v):
        self._file = v
        self.load()
    
    @property
    def accounts(self):
        return self._accounts

    @accounts.setter
    def accounts(self, v):
        self._accounts = v

    @property
    def logs(self):
        return self._logs

    @logs.setter
    def logs(self, v):
        self._log = v

    def clear(self):
        self._accounts = accounts()
        self._logs = logs()
        self.isloaded = False

    def load(self):
        self.clear()

        try:
            with open(self.file, 'r') as stream:
                self._cfg = yaml.load(stream)

            for acct in self['accounts']:
                self.accounts += account.create(acct)

            for d in self['logs']:
                l = log.create(d)
                self.logs += l
        except:
            raise
        else:
            self.isloaded = True

    def __getitem__(self, key):
        return self._cfg[key]

    @property
    def inproduction(self):
        try:
            env = self['environment'].lower()
        except KeyError:
            raise Exception('No environment value set in config file.')
        return env in ['prd', 'production', 'live']

