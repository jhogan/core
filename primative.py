# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2020
import datetime as stddatetime
import dateutil.parser
import dateutil

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


