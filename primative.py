# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2019
import datetime as stddatetime
import dateutil.parser
import dateutil
from dbg import B

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
        # can defalut to the systems timezone.
        raise NotImplementedError()

    def add(self, **kwargs):
        return self + stddatetime.timedelta(**kwargs)
