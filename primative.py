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

""" This module provides overrides for basic datatypes (primatives) such
as datetime. The goal is to make these (typically) builtin datatypes
more user-friendly and better able to meet the needs of the framework
and the framework's users.
"""

class datetime(stddatetime.datetime):
    """ A datetime class that inherits from Python's standard datetime
    class. You will usually use this class instead of the standarad
    datetime class since it provides a more conveniente user experience
    and can be further customized to meet needs of the framework.
    """
    def __new__(cls, *args, **kwargs):
        """ Create a new primative.datetime.

        :param: *args[0] str|datetime.datetime: A datetime used to
        create the new primative.datetime. If it's a str, it will be
        parsed (hopefully correctly) by the powerful dateutil.parser
        library. A format string will not be needed. The timezone will
        default to UTC. 

        A standard Python datetime can also be used.

        Note that you can also instatiate this object the same way you
        would instantiate a Python datetime object. See the
        documentation at 

            https://docs.python.org/3/library/datetime.html#datetime-objects

        for details.
        """
        dt = args[0]
        if type(dt) is str:
            # Parse the datetime as a string

            # TODO When parsing a date str, the returned datetime is
            # naive. It currently defaults to UTC. However, we should
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
            # Instantiate given a standard Python datetime
            return datetime(dt.year,        dt.month,    dt.day,
                            dt.hour,        dt.minute,   dt.second,
                            dt.microsecond, dt.tzinfo)
            
        # Instantiate using the same arguments that would be given to a
        # standard Python datetime object.
        return stddatetime.datetime.__new__(cls, *args, **kwargs)

    def astimezone(self, tz=None):
        """ Return a new primative.datetime object with new tzinfo
        specified by 'tz', adjusting the date and time data so the
        result is the same time as self, but in tz’s local time.

        :param: tz str|tzinfo: The new tzinfo. If tz is a str, the
        string is parsed into a tzinfo object.
        """
        if type(tz) is str:
            tz = dateutil.tz.gettz(tz)
        return datetime(super().astimezone(tz))

    @staticmethod
    def utcnow(**kwargs):
        """ Return the current UTC primative.datetime.

        Note that unlike the utcnow() method on Python's standard
        datetime object, the datetime that is returned is aware, i.e.,
        it knows that its timezone is UTC.

        :param: kwargs **dict: The same arguments that can be passed to
        Python's standard timedelta constructor can be pased to this
        method in order to offset the time into the future or the past.
        For expample, to get a primative.datetime in UTC for the moment
        30 days prior to now, you could write::

            a_month_ago = primative.datetime.utcnow(days = -30)

        See the documentation for the timedelta constructor for more
        details on its parameters at 
        https://docs.python.org/3/library/datetime.html#timedelta-objects
        """
        r = datetime(stddatetime.datetime.utcnow())

        # Make aware
        r = r.replace(tzinfo=stddatetime.timezone.utc)

        r = r.add(**kwargs)
        return r

    @staticmethod
    def now(tz=False):
        """ Return a primative.datetime adjusted for the current
        timezone. 

        TODO Currently not implemneted.
        """
        # TODO tz should probably default to None. I'm not sure why I
        # defaulted it to False.

        # Demand that tz is not False. 
        if tz is False:
            raise ValueError(
                'Use `.utcnow` or pass in a timezone'
            )

        # TODO Return a datetime for the given local. If tz is None, we
        # can default to the system's timezone.
        raise NotImplementedError()

    def add(self, **kwargs):
        """ Return a new primative.datetime with time added to the self. 

        :param: kwargs **dict: The same arguments that can be passed to
        Python's standard timedelta constructor can be pased to this
        method in order to offset the time into the future or the past.
        For expample, to get a primative.datetime in UTC for the moment
        10 seconds into the future::

            # Get the current time
            dt = primative.datetime.utcnow()

            # Add 10 seconds to the current time
            dt = dt + datetime.timedelta(seconds = 10)

        See the documentation for the timedelta constructor for more
        details on its parameters at 
        https://docs.python.org/3/library/datetime.html#timedelta-objects
        """
        return self + stddatetime.timedelta(**kwargs)

    def __add__(self, td):
        """ Override the __add__ method of the standard Python datetime
        class in order to return a primative.datetime instead:

        :param: td timedelta: The amount of time to add to self.
        """
        td = super().__add__(td)
        return datetime(td)

    @property
    def date(self):
        """ Convert the curent primative.datetime to a primative.date.
        """
        return date(self)

class date(stddatetime.date):
    """ A date class that inherits from Python's standard date class.
    """
    def __new__(cls, *args, **kwargs):
        """ Create a new date, naive (timezone unaware) object.

        :param: args[0] str|date|datetime Create the date object based
        on date information contained in the argument. If the type is a
        date like object, its `year`, `month` and `day` properties are
        used for the new date.
            
            import datetime, primative

            # str
            dt = primative.date('2022/02/28)

            # date
            dt = date.date(2022, 02, 28)
            dt = primative.date(dt)

            # date
            dt = date.datetime.utcnow()
            dt = primative.date(dt)

        If the above types aren't found in args[0], the default
        constructor for Python's standard date class is used::

            year, month, day = 2022, 02, 28
            dt = primative.date(year, month, day)
        """
        dt = args[0]
        if type(dt) is str:
            dt = datetime(dt)

            # TODO Explain why we insist on the date being naive here
            dt = dt.replace(tzinfo=None)
            dt = dt.date
            return dt

        elif isinstance(dt, date) or isinstance(dt, datetime) or \
                 type(dt) is stddatetime.date:
            return date(dt.year, dt.month, dt.day)

        dt = stddatetime.date.__new__(cls, *args, **kwargs)
        return dt

    def add(self, **kwargs):
        """ Return a new primative.date with time added to the self. 

        :param: kwargs **dict: The same arguments that can be passed to
        Python's standard timedelta constructor can be pased to this
        method in order to offset the date into the future or the past.
        For expample, to get a primative.date 10 days into the future::

            # Get the current date
            dt = primative.date.today()

            # Add 10 days to the current date
            dt = dt + datetime.timedelta(days = 10)

        See the documentation for the timedelta constructor for more
        details on its parameters at 
        https://docs.python.org/3/library/datetime.html#timedelta-objects
        """
        return self + stddatetime.timedelta(**kwargs)

    def __add__(self, dt):
        """ Override the __add__ method of the standard Python date
        class in order to return a primative.date instead:

        :param: td timedelta: The amount of time to add to self.
        """
        dt = super().__add__(dt)
        return date(dt)

    @staticmethod
    def today(**kwargs):
        """ A static method to get and return today's date object.

        The arguments you would supply to timedelta can be used to
        offset the date into the past or the future.  See the
        documentation for the timedelta constructor for more details on
        its parameters at 
        https://docs.python.org/3/library/datetime.html#timedelta-objects
        """
        r = date(stddatetime.date.today())

        r = r.add(**kwargs)
        return r

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
