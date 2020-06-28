# vim: set et ts=4 sw=4 fdm=marker

# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2020

""" This module contains ``orm.entity`` objects related the tracking of
work effort data.

These entity objects are based on the "Work Effort" chapter of "The Data
Model Resource Book".

Examples:
    See test.py for examples. 

"""

from datetime import datetime, date
from dbg import B
from decimal import Decimal as dec
from orm import text, timespan, datespan
import entities
import order
import orm
import party
import primative
import product

