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
from accounts import *
import yaml

class configfile(entity):
    _instance = None

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

    def clear(self):
        self._accounts = accounts()

    def load(self):
        self.clear()

        with open(self.file, 'r') as stream:
            self._cfg = yaml.load(stream)

        for acct in self['accounts']:
            self.accounts += account.create(acct)

    def __getitem__(self, key):
        return self._cfg[key]

    @property
    def inproduction(self):
        try:
            env = self['environment'].lower()
        except KeyError:
            raise Exception('No environment value set in config file.')
        return env in ['prd', 'production', 'live']

