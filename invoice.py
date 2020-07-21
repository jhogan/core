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

Todo:
    
   TODO: There are a large number of ``item`` subentities that can be
   created and used if more precision is needed. These include subtypes
   such as INVOCIE ADJUSTMENTs, INVOICE ACQUIRING ITEMS and subtypes
   thereof.

"""
from datetime import datetime, date
from dbg import B
from decimal import Decimal as dec
from orm import text, timespan, datespan
import orm
import product
import party

class invoices(orm.entities): pass
class salesinvoices(invoices): pass
class purchaseinvoices(invoices): pass
class items(orm.entities): pass
class salesitems(items): pass
class purchaseitems(items): pass
class types(orm.entities): pass
class roles(orm.entities): pass
class roletypes(orm.entities): pass

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

    # NOTE ``seller`` and ``buyer`` are the two main, hardcoded (so to
    # speak) roles of an invoice. Other roles can be added dynamically
    # through the ``role`` entity.

    # The party to the invoice to whom money is owed. (In the book, this
    # is called the **billed from** attribute.) 
    seller = party.party

    # The party to the invoice who is recieving the bill. (In the book, this
    # is called the **billed to** attribute.)
    buyer = party.party

    # NOTE Invoices may be sent or receiviad via numerous subentities of
    # ``contactmechanism`` including ``party.phone``, ``party.email``
    # and ``party.phone`` (i.e., faxed). Invoices can also be sent
    # through snail mail (``party.adderss``).

    # The contact mechanism from which the invoice was sent. This is
    # called **send from** in the book.
    source = party.contactmechanism

    # The contact mechanism to which the invoice is addressed. This is
    # called **addressed to** in the book.
    destination = party.contactmechanism

class salesinvoice(invoice):
    """ A subentity of ``invoice`` related to a purchase order.

    Note that this entity was originally called SALES INVOICE in
    "The Data Model Resource Book".
    """

class purchaseinvoice(invoice):
    """ A subentity of ``invoice`` related to a purchase order.

    Note that this entity was originally called PURCHASE INVOICE in
    "The Data Model Resource Book".
    """

class item(orm.entity):
    """ An invoice ``item`` represents any items that are being charged.

    Each invoice ``item`` may have a many-to-one relationship to
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

class salesitem(item):
    """ An invoice item for sales order items.

    Note that this entity was originally called PURCHASE INVOICE ITEM in
    "The Data Model Resource Book".
    """

class purchaseitem(item):
    """ An invoice item for purchase order items.

    Note that this entity was originally called PURCHASE INVOICE ITEM in
    "The Data Model Resource Book".
    """
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

class role(orm.entity):
    """ Records each party involved in each ``roletype`` for an
    ``invoice``.

    """

    # The date and time that the ``person`` or ``organization`` performed
    # the role.
    datetime = datetime
    percent = dec

class roletype(orm.entity):
    """ A type of ``role``. 
    
    Examples of role include "entered by", "approver", "sender" and
    "receiver". Note that the key roles for an invoice, "seller" and
    "buyer" are hardcoded in ``invoice.seller`` and ``invoice.buyer``.
    """
    roles = roles
