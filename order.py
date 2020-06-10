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
import product

class orders(orm.entities):  pass

# TODO Write validation rule to disallow instance of `item`. Only alow
# subtypes of `item` like `salesitem` and `purchaseitem` entity objects.
# If the composite is a `purchase`, then only `purchaseitem` should be
# allowed. Likewise when the composite is a salesorder entitiy objects.
class items(orm.entities):   pass
class salesitems(items):     pass
class purchaseitems(items):  pass
class salesorders(orders):         pass
class purchaseorders(orders):     pass

class order(orm.entity):
    """ The generic, abstract order class from with the `salesorder` and
    `purchase` classes inherit.
    """

    # The date on which the enterprise received or gave the order. This
    # is in contrast to the inherited `createdat` date which is used to
    # indicate when the order was entered into the system (called the
    # `entry date` in the "Data Modeling Resource Book").
    received = date

    items = items

class item(orm.entity):
    """ A line item of an order representing the ordering of a specific
    good or service. Each line item references exactly one product
    (``product.product``) or exactly one feature (``product.feature``).

    The phrase "order line item" should not be used to describe an
    ``item``. This phrase connotes a physical line on an order form
    which may encompass many other things aside from the items that have
    been ordered such as records adjustments, taxes, estimated
    freightcosts, explanations, etc. ``item`` simply represents the
    products that have been ordered.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.orm.isnew:
            self.description = None
            self.comment = None
            self.instructions = None


    # For goods (product.goods), `quantity` represents the number of
    # goods ordered. For services (product.services), this represents
    # the number of hours, days or other measurement being billed. The
    # unit of measure for this quantity is determined by the unit of
    # measure that is associated with the product (see product.measure).
    quantity = dec

    # The charge for the item or rate of the service. Note that we do not
    # reference the ``product.price` entity here. This is because we
    # want to allow the user to override the calculated price with the
    # negotiated price for the order.
    price = dec

    # The date the good is expected to be delivered to the customer or
    # the expected date of service fulfillment to a customer.
    estimateddeliveredat = date

    # Stores directions for the transport of products to their
    # destinations, for example, "fragile -- handle with care", or
    # "requires signature by customer when delivering".
    instructions = text

    # Stores descriptions of items that are non-standard and would not
    # be maintain with the product.product or product.feature entity
    # objects.
    description = text

    # Allows for additional explaination of the item.
    comment = text

    # The product feature for this line item. NOTE that `product` must
    # be None if a feature is referenced.
    feature = product.feature

    # The good or service this line item references. NOTE that
    # ``feature`` must be None if a product is referenced. TODO Write a
    # validation rule that ensures either `product` or `feature` is
    # None and that one of these should not be None.
    # 
    # (NOTE We would have added `items` as a constituent of
    # `product.product` and achieved the same result with the addition
    # of a one-to-many relationship between product.product and
    # order.item. However, that would require product.py referencing
    # this order.py which would cause a circular reference issue. The
    # same could be said of the `feature` attribute above).
    product = product.product

class salesitem(item):
    """ Represents an items for a sales order.

    Note that this entity was originally called SALES ORDER ITEM in "The
    Data Modeling Resource Book".
    """

class purchaseitem(item):
    """ Represents an items for a purchase order.

    Note that this entity was originally called PURCHASE ORDER ITEM in
    "The Data Modeling Resource Book".
    """

class salesorder(order):
    """ A class representing a sales order. 

    Note that this entity was originally called SALES ORDER in "The
    Data Modeling Resource Book".
    """

class purchaseorder(order):
    """ A class representing a purchase order

    Note that this entity was originally called PURCHASE ORDER in "The
    Data Modeling Resource Book".
    """

