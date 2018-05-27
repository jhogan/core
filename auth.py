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
from entities import entities, entity
from pdb import set_trace; B=set_trace
from datetime import datetime, timedelta
from configfile import configfile
import json
import jwt as pyjwt


class jwt(entity):
    def __init__(self, ttl=24):
        self._exp = datetime.utcnow() + timedelta(hours=ttl)

    @property
    def exp(self):
        return self._exp

    @property
    def token(self):
        
        d = {}
        for prop in 'exp',:
            d[prop] = getattr(self, prop)

        secret = configfile.getinstance()['jwt-secret']
        enc = pyjwt.encode(d, secret)
        return enc.decode('utf-8')

    def __str__(self):
        return  self.token
        
