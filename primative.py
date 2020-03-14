# vim: set et ts=4 sw=4 fdm=marker

# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2020
import datetime as stddatetime
import dateutil.parser
import dateutil
from uuid import UUID, uuid4
from base64 import urlsafe_b64decode, urlsafe_b64encode

class datetime(stddatetime.datetime):
    def __new__(cls, *args, **kwargs):

        dt = args[0]
        if type(dt) is str:
            return datetime(dateutil.parser.parse(args[0]))
        elif type(dt) is stddatetime.datetime:
            return datetime(dt.year,        dt.month,    dt.day,
                            dt.hour,        dt.minute,   dt.second,
                            dt.microsecond, dt.tzinfo)
            
        return stddatetime.datetime.__new__(cls, *args, **kwargs)

    def astimezone(self, tz=None):
        if type(tz) is str:
            tz = dateutil.tz.gettz(tz)
        return datetime(super().astimezone(tz))

    @staticmethod
    def utcnow():
        r = datetime(stddatetime.datetime.utcnow())

        # Make aware
        r = r.replace(tzinfo=stddatetime.timezone.utc)

        return r

    def add(self, **kwargs):
        return self + stddatetime.timedelta(**kwargs)

class uuid(UUID):
    def __init__(self, base64=None, *args, **kwargs):
        if len(args) or len(kwargs) or base64:
            if base64:
                kwargs['bytes']= urlsafe_b64decode(base64 + '==')
            super().__init__(*args, **kwargs)
        else:
            int = uuid4().int
            super().__init__(int=int, version=4)

    @property
    def base64(self):
        return urlsafe_b64encode(self.bytes).rstrip(b'=').decode('ascii')

        
        

