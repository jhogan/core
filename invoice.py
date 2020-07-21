# vim: set et ts=4 sw=4 fdm=marker

# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2020

""" This module contains ``orm.entity`` objects related to the tracking of
invoice data.

These entity objects are based on the "Invoicing" chapter of "The Data
Model Resource Book".

Examples:
    See test.py for examples. 

"""
from datetime import datetime, date
from dbg import B
from decimal import Decimal as dec
from orm import text, timespan, datespan
import orm
import product

class invoices(orm.entities): pass
class items(orm.entities): pass
class types(orm.entities): pass

class invoice(orm.entity):
    """ The ``invoice`` maintains header information abut the
    transaction. Each invoice has a one-to-many relationship with
    the ``item`` entity (see the ``items`` attribute) which maintains
    the details of each item that is being charged.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.orm.default('message', None)
        self.orm.default('description', None)

    # The date the invoice was created (not to be confused with the
    # inherited ``createdat`` attribute which is the date the invoice record was
    # inserted into the table). This will be an important piece of
    # information used in tracking the progress of the invoice when a
    # client calls to discuss his or her bill. 
    created = date

    # A note or message to the customer on the invoice
    message = text

    # Describes the nature of the invoice, e.g., "Fulfillment of office
    # supply order".
    description = text
    items = items

class item(orm.entity):
    """ An invoice ``item`` represents any items that are being charged.

    Each invoince ``item`` may have a many-to-one relationship to
    either ``product.product`` or ``product.feature``. It may also be
    related to a serialzied inventory item (see the ``serial``
    attribute) because maintainng the actual instance of the product
    that was bought with its serial number may be useful. (For instance,
    computer manufacturers often record the serial number of the
    computer that was bought and invoiced.)

    If the item represets a one-time charge item that is not catalogued,
    then the ``description`` attribute with the ``invoice`` entity may
    be used to record what was charged.

    Each invoice ``item`` may be categorized by an invoice item
    ``type``, which could include values such as "invoice adjustment",
    "invoice item adjustment", "invoice product item", "invoice product
    feature item", invoice work effort item", or "invoice time entry
    item".

    Invoice ``items`` has a recursive relationship with itself. See the
    comment at the ``items`` attribute for more.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.orm.default('description', None)

    # Indicates whether this item is taxable. The taxability of an item
    # could vary depending on many circumstaces, such as the source and
    # destination of the shipment or the tax status of the purchasing
    # organization. 
    istaxable = bool

    # If the item is for an adjustment, ``percent`` stores the
    # percentage of the adjustment, such as .07 for sales tax
    percent = dec

    # The quantity of items being billed. The ``quantity`` is optional
    # because there may only be an ``amount`` and not a ``quantity`` for
    # the ``item`` such as ``features`` where the ``quantity`` really
    # isn't necessary and is not applicable.
    quantity = dec

    # The amount of items being billed
    amount = dec
    description = text
    feature = product.feature
    serial = product.serial
    product = product.product

    # A recursive collection of invoice ``items``. Each invoice ``item``
    # has a recursive relationship as it may be adujusted by one or more
    # other invoice ``items11, which would be an of invoice item
    # ``type`` "invoice item adjustment". Each invoice ``item`` may also
    # be sold with other invoice ``items`` that would be of type
    # "invoice product feature item".
    #
    # When ``feature`` is set in the ``item``, the recursive
    # relationship **sold with ** should be recorded in order to
    # indicate that the feature was invoiced for a specific invoice
    # ``item`` that was for a ``product``.
    items = items

class type(orm.entity):
    """ Each invoice ``item`` may be categorized by an invoice item
    ``type``. The value for the ``name`` attribute  could include values
    such as "invoice adjustment", "invoice item adjustment", "invoice
    product item", "invoice product feature item", invoice work effort
    item", or "invoice time entry item". If an item is for an
    adjustment, value could include "miscellaneous charge", "sales tax",
    "discount adujustment", "shipping and handling charges", "surchange
    adujustment", and "fee".
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.orm.ensure(expects=('name',), **kwargs)

    name = str
    items = items

