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
from entities import entities, entity, brokenrules, brokenrule
from pdb import set_trace; B=set_trace
from datetime import datetime, timedelta
from configfile import configfile
import json
import jwt as pyjwt


class jwt(entity):
    def __init__(self, tok=None, ttl=24):
        super().__init__()
        self._exp = datetime.utcnow() + timedelta(hours=ttl)
        self._token = tok
        self._iss = None
        self.onaftervaluechange += self._self_onaftervaluechange

    def _self_onaftervaluechange(self, src, eargs):
        # If a property is changes, set _token to None so self.token recreates
        # the token. Otherwise, we would get the same token despite a change a
        # property.
        self._token = None
        
    @property
    def exp(self):
        return self._getvalue('exp')

    @property
    def iss(self):
        return self._getvalue('iss')

    @iss.setter
    def iss(self, v):
        return self._setvalue('_iss', v, 'iss')
            
    @property
    def token(self):
        if self._token is None:
            d = {}
            for prop in 'exp', 'iss':
                v = getattr(self, '_' + prop)
                if v is not None:
                    d[prop] = v

            secret = configfile.getinstance()['jwt-secret']
            enc = pyjwt.encode(d, secret)
            self._token = enc.decode('utf-8')
        return self._token

    def _getvalue(self, k):
        v = getattr(self, '_' + k)
        if v is None:
            if self.token:
                secret = configfile.getinstance()['jwt-secret']
                d = pyjwt.decode(self.token, secret)
                try:
                    return d[k]
                except KeyError:
                    return None
            return None
        else:
            return v

    @property
    def brokenrules(self):
        brs = brokenrules()

        try:
            pyjwt.decode(self.token)
        except pyjwt.exceptions.DecodeError as ex:
            brs += brokenrule('Invaild token.', 'token', 'valid')

        return brs

    def __str__(self):
        return  self.token
        
