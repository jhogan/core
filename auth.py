# vim: set et ts=4 sw=4 fdm=marker

# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2020

from configfile import configfile
from datetime import datetime, timedelta
from dbg import B
from entities import entities, entity, brokenrules, brokenrule
import json
import jwt as pyjwt

class jwt(entity):
    def __init__(self, tok=None, ttl=24):
        super().__init__()
        self._exp = datetime.utcnow() + timedelta(hours=ttl)
        self._token = tok
        self._iss = None
        self._sub = None
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
    def sub(self):
        """ "The "sub" (subject) claim identifies the principal that is
        the subject of the JWT.  The claims in a JWT are normally
        statements about the subject.  The subject value MUST either be
        scoped to be locally unique in the context of the issuer or be
        globally unique.  The processing of this claim is generally
        application specific.  The "sub" value is a case-sensitive
        string containing a StringOrURI value.  Use of this claim is
        OPTIONAL."  

                       - https://tools.ietf.org/html/rfc7519#section-4.1

        For the most part, this will be used to store the user's id:

            jwt.sub = gem.user(name='luser').id.hex
        """
        return self._getvalue('sub')

    @sub.setter
    def sub(self, v):
        return self._setvalue('_sub', v, 'sub')
            
    @property
    def token(self):
        if self._token is None:
            d = {}
            for prop in 'exp', 'iss', 'sub':
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
            secret = configfile.getinstance()['jwt-secret']
            pyjwt.decode(self.token, secret)
        except pyjwt.exceptions.DecodeError as ex:
            brs += brokenrule('Invaild token.', 'token', 'valid')

        return brs

    def __str__(self):
        return  self.token
        
