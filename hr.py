# vim: set et ts=4 sw=4 fdm=marker

# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2020

""" This module contains ``orm.entity`` objects related to the tracking
of human resource data.

These entity objects are based on the "Human Resources" chapter of "The
Data Model Resource Book".

Examples:
    See test.py for examples. 

TODO:
"""

from datetime import datetime, date
from dbg import B
from decimal import Decimal as dec
from orm import text, timespan, datespan
import orm
import party

class employeement(party.role_role):
    """ Maintains employment information. ``employeement`` is a
    subentity of ``party.role_role`` and represents a relationship between
    the party roles of employees (``party.employee``) and internal
    organization (``party.internal``). Note that if the enterprise is
    interested in tracking employees of extrenal organisanions as well,
    then this entity can be between ``party.employee`` and
    ``party.employeer``.

    """
