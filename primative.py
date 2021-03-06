# vim: set et ts=4 sw=4 fdm=marker

# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2021
from base64 import urlsafe_b64decode, urlsafe_b64encode
from dateutil.tz import gettz
from dbg import B
from uuid import UUID, uuid4
import datetime as stddatetime
import dateutil
import dateutil.parser

class datetime(stddatetime.datetime):
    def __new__(cls, *args, **kwargs):

        dt = args[0]
        if type(dt) is str:
            # TODO When parsing a date str, the returned datetime is
            # naive. It should probably default to UTC. We should
            # except a `tz` argument to specify the timezone since
            # dateutil.parser.parse doesn't seem to be able to parse a
            # timezone, i.e., the following won't work:
            #
            #     dateutil.parser.parse('Jan 9 2001, UTC')
            #
            # Often, we will be parsing dates that the user provided so
            # we will probably need to use their timezones. The
            # programmer will need to convert to UTC if the data is
            # destined for the DB. The ORM should reject non-UTC
            # datetimes (I don't believe it currently does that). If
            # their is a TZ in the datetime, the orm can convert to UTC
            # automatically.

            dt = datetime(dateutil.parser.parse(args[0]))
            tz = dateutil.tz.gettz('UTC')
            dt = dt.replace(tzinfo=tz)
            return dt

        elif isinstance(dt, stddatetime.datetime):
            return datetime(dt.year,        dt.month,    dt.day,
                            dt.hour,        dt.minute,   dt.second,
                            dt.microsecond, dt.tzinfo)
            
        return stddatetime.datetime.__new__(cls, *args, **kwargs)

    def astimezone(self, tz=None):
        if type(tz) is str:
            tz = dateutil.tz.gettz(tz)
        return datetime(super().astimezone(tz))

    @staticmethod
    def utcnow(**kwargs):
        r = datetime(stddatetime.datetime.utcnow())

        # Make aware
        r = r.replace(tzinfo=stddatetime.timezone.utc)

        r = r.add(**kwargs)
        return r

    @staticmethod
    def now(tz=False):
        # Demand that tz is not False. 
        if tz is False:
            raise ValueError(
                'Use `.utcnow` or pass in a timezone'
            )

        # TODO Return a datetime for the given local. If tz is None, we
        # can default to the system's timezone.
        raise NotImplementedError()

    def add(self, **kwargs):
        return self + stddatetime.timedelta(**kwargs)

    def __add__(self, dt):
        dt = super().__add__(dt)
        return datetime(dt)

    @property
    def date(self):
        return date(self)

class date(stddatetime.date):
    def __new__(cls, *args, **kwargs):
        dt = args[0]
        if type(dt) is str:
            dt = datetime(dt)
            dt = dt.replace(tzinfo=None)
            dt = dt.date
            return dt

        # TODO All the conditionals have the same consequence so chain
        # them disjunctively
        elif isinstance(dt, date):
            return date(dt.year, dt.month, dt.day)
        elif isinstance(dt, datetime):
            return date(dt.year, dt.month, dt.day)
        elif type(dt) is stddatetime.date:
            return date(dt.year, dt.month, dt.day)

        dt = stddatetime.date.__new__(cls, *args, **kwargs)
        return dt

    def add(self, **kwargs):
        return self + stddatetime.timedelta(**kwargs)

    @staticmethod
    def today(**kwargs):
        r = date(stddatetime.date.today())

        r = r.add(**kwargs)
        return r

    def add(self, **kwargs):
        return self + stddatetime.timedelta(**kwargs)

    def __add__(self, dt):
        dt = super().__add__(dt)
        return date(dt)

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
