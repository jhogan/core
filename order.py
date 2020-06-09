# vim: set et ts=4 sw=4 fdm=marker

# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2020

import orm
from orm import text, timespan, datespan
import entities
import primative
from datetime import datetime, date
from dbg import B
import party
from decimal import Decimal as dec

class orders(orm.entities): pass
class sales(orders): pass
class purchases(orders): pass

class order(orm.entity):
    """ The generic, abstract order class from with the `sale` and
    `purchase` classes inherit.
    """

    # The date on which the enterprise received or gave the order. This
    # is in contrast to the inherited `createdat` date which is used to
    # indicate when the order was entered into the system (called the
    # `entry date` in the "Data Modeling Resource Book").
    received = date

class sale(order):
    """ A class representing a sales order. 

    Note that this entity was originally called SALES ORDER in "The
    Data Modeling Resource Book".
    """

class purchase(order):
    """ A class representing a purchase order

    Note that this entity was originally called PURCHASE ORDER in "The
    Data Modeling Resource Book".
    """
