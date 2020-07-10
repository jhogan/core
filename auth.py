# vim: set et ts=4 sw=4 fdm=marker

# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2019

from entities import entities, entity, brokenrules, brokenrule
from datetime import datetime, timedelta
from config import config
import json
from dbg import B
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

            secret = config().jwt.secret
            enc = pyjwt.encode(d, secret)
            self._token = enc.decode('utf-8')
        return self._token

    def _getvalue(self, k):
        v = getattr(self, '_' + k)
        if v is None:
            if self.token:
                secret = config().jwt.secret
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
        
