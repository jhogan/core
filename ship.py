# vim: set et ts=4 sw=4 fdm=marker

# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2020

""" This module contains ``orm.entity`` objects related the tracking of
order shipping data.

These entity objects are based on the "Shipments" chapter of "The Data
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

class shipments(orm.entities): pass
class items(orm.entities): pass
class statuses(orm.entities): pass
class statustypes(orm.entities): pass
class shipitem_orderitems(orm.associations): pass

class shipment(orm.entity):
    """ Records the details of a shipment.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.orm.isnew:
            self.instructions = None

    # NOTE In the book, there are many subtypes to ``shipment``,
    # however, as the book says, they are listed for clarity and could
    # be infered from the organizations involved in the shipment. For
    # example, the CUSTOMER SHIPMENT is a shipment sent out to
    # customers from the enterprise. We could just have a @property
    # called ``iscustomershipment`` that looks at the parties involved
    # in the order and returned True or False based on what is
    # discovered there.

    # NOTE that the the bulitin `updatedat` field will serve as the
    # *laste updated* attribute specified in the book. This attribute
    # "provides a way to determine when the [``shipment`` entity's]
    # information was last changed because the estimated dates may
    # change frequently, although the enterprise would hope not".

    # The *estimated ship dates* indicates when the shipment is expected
    # to begin its journey to the client. This value is critical to
    # customer service personnel when an irate client calls to see what
    # happened to his or her order.
    estimatedshipat = date

    # The *estimated ready date* documents when the item is epected to
    # be ready for shipment (perhaps packaging or other preparation is
    # needed for the item).
    estimatedreadyat = date

    # The *estimated arrive date*.
    estimatedarriveat = date

    # The *estimated ship cost* may be important for billing.
    estimatedshipcost = dec

    # The *actual ship cost* may be important for billing.
    actualshipcost = dec

    # The date on which the shipment was canceled.
    canceledat = dec

    # The *handling instructions*, e.g., "fragile", "requires signature
    # upon delivery".
    instructions = text

    # The party from which the shipment is shipped.
    shipfrom = party.party

    # The party to which the shipment is destined.
    shipto = party.party

    # The address from which the shipment originates.
    shiptousing = party.address

    # The address for which the shipment is destined.
    shipfromusing = party.address

    # A contact mechanism maintained o record where queries can be made
    # to inquire about the shipent from the sender.
    inquire = party.contactmechanism

    # A contact number for the receiver to facilitate delivery just in
    # case the carrier cannot easily access or find the postal address=
    inquire = party.address

    # The collection of items (i.e., goods) that compose a shipment.
    items = items

    # The collection of statuses this shipment has been through.
    statuses = statuses

class item(orm.entity):
    """ A line item in a ``shipment``. Each ``shipment`` can have one or
    more ``items``.

    Note that this entity was originally called SHIPMENT ITEM in
    "The Data Model Resource Book".
    """

    def __init__(self, *args, **kwargs):
        # TODO Do not allow the GEM user to instantiate this class;
        # product.__init__ should only be called by product.good and
        # product.services. Those subclasses can pass in an override
        # flags to bypass the NotImplementedError.
        super().__init__(*args, **kwargs)
        if self.orm.isnew:
            self.contents = None

    # TODO Write a validation rule to ensure that one of either
    # `contents` or `good` is set but not both.

    # How many of the given ``good`` was shipped.
    quantity = dec

    # The ``product.good`` that this shipment item represents.
    #
    # An ``item` is related to a product.good rather that a product.item
    # (inventory item) because the particular inventory item may not be
    # known when scheduling the shipment. Also, the inventory items are
    # related indirectly to the shipment ``item`` through other entities
    # such as SHIPMENT RECEIPT and ITEM ISSUANCE of inventory items.
    good = product.good

    # For non-statard items that aren't kept on file, the ``good``
    # attribute will be None. However, we can describe non-standard
    # product using the ``contents`` attribute.
    contents = str

    # We create a recursive relationship here to account for the fact
    # that shipment ``items`` may be in response to other shipment
    # ``items``, for example, when an organization receives the item,
    # determines that the item is defective, and sends it back (which is
    # another shipment ``item` that is related to the orginal shipment
    # item).
    items = items

class status(orm.entity):
    """ An entity that records the state of the shipment at various
    points in time. ``status`` entries are described by the
    ``statustype`` entity..

    Note that this entity was originally called SHIPMENT STATUS in "The
    Data Model Resource Book".
    """
    entities = statuses
    
    # The date and time at which a ``shipment`` entered into this status
    begin = datetime

class statustype(orm.entity):
    """ This entity describes a shipment's ``status``. It has a
    one-to-many relationship with ``status``.

    Examples of status types include "scheduled", ""shipped", "in
    route", "delivered", and "canceled".

    Note that this entity was originally called SHIPMENT STATUS TYPE in
    "The Data Model Resource Book".
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.orm.ensure(expects=('name',), **kwargs)

    name = str

    # The collection of status entities that belong that have this
    # status type.
    statuses = statuses

class shipitem_orderitem(orm.association):
    """ This association links a shipment item (``ship.item``) with an
    order item (``order.item``). This many-to-many relationship this
    creates between the two entity objects is required to handle partial
    shipments and combined shipments.

    Note that this entity was originally called ORDER SHIPMENT in
    "The Data Model Resource Book".
    """

    # The shipment item portion of the association.
    shipitem = item

    # The order item portion of the association.
    orderitem = order.item

    # TODO Comment on this attribute
    quantity = int

