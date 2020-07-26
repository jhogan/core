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
import shipment

class invoices(orm.entities): pass
class salesinvoices(invoices): pass
class purchaseinvoices(invoices): pass
class items(orm.entities): pass
class salesitems(items): pass
class purchaseitems(items): pass
class types(orm.entities): pass
class roles(orm.entities): pass
class roletypes(orm.entities): pass
class accounts(orm.entities): pass
class account_roles(orm.associations): pass
class account_roletypes(orm.entities): pass
class statuses(party.statuses): pass
class statustypes(orm.entities): pass
class terms(orm.entities): pass
class termtypes(orm.entities): pass
class invoiceitem_shipmentitems(orm.associations): pass

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

    # A collection of statuses for the ``invoice``
    statuses = statuses

    # A collection of terms associated with the ``invoice``
    terms = terms

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
    Each invoice ``item`` may include moneys that are owed from shipment
    items (`shipment.item``), work efforts (``effort.effort``), time entries
    (``effort.time``) or order items (``order.item``).

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

    # A collection of terms associated with the ``item``
    terms = terms

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

class account(orm.entity):
    """ The billing ``account`` entity provides a mechanism for grouping
    different types of items on different invoice.

    The typical way to bill a customer is by sending an invoice. An
    alternative is to use a billing ``account``. This method of billing
    is used only in certain circumstances for specific types of
    businesses. For example, a client might want one account for his
    or her office supplies and another account for furniture purchase.

    Note that this is modeled after the BILLING ACCOUNT entity in "The
    Data Model Resource Book".
    """

    # The span of time for whit the billing ``account`` is active.
    span = datespan

    # Used to identify the nature of the billing ``account.
    description = text

    # In order to determine where to send the invoice, the account in
    # quastion must, be related to a contact mechanism. 
    contactmechanism = party.contactmechanism

class account_role(orm.association):
    """ An intersection between ``party`` and a billing ``account` allowing
    for maintenance of the various parties involved on the account.

    Note that this is modeled after the BILLING ACCOUNT ROLE entity in
    "The Data Model Resource Book".
    """
    
    # The ``party`` side of the association
    party = party.party

    # The billing ``account`` side of the association
    account = account

    # The span of time when the ``party`` became active on the
    # ``account``.
    span = datespan

class account_roletype(orm.entity):
    """ The billing account role (``account_role``) allows each
    ``party`` to play a billing ``account`` role type
    (``account_roletype``) in the ``account``. Roles could include
    "primary payer", indicating the main party that is supposed to pay,
    or "secondary payer", indicating other parties that could pay in
    case of of default. Other roles include, "customer service
    representative", "manager", and "sale representative" that could be
    involved with the account as well. An invoice may be billed to
    either a billing account or directly to a party (``invoice.buyer``)

    Note that this is modeled after the BILLING ACCOUNT ROLE TYPE entity
    in "The Data Model Resource Book".
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.orm.ensure(expects=('name',), **kwargs)

    name = str

    account_roles = account_roles

class status(party.status):
    """ Tracks the changes to an ``invoice``'s status over time.
    Examples of ``status`` include "sent", "void", and "approved".
    "Paid" is not a valid status because that can be determined via
    payment transactions.

    Note that this is modeled after the INVOICE STATUS in "The Data
    Model Resource Book".
    """

    entities = statuses

    # TODO ``assigned`` is a pretty good name for this concept. Ensure
    # that other status classes use this name; or, better yet, use
    # ``assigned`` in the base class (``party.status``)
    # The datetime that the status took effect
    assigned = datetime

# TODO I guess there isn't a party.statustype at the moment.
class statustype(orm.entity):
    """ Categorizes ``statuses``.

    Note that this is modeled after the INVOICE STATUS TYPE in "The Data
    Model Resource Book".
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.orm.ensure(expects=('name',), **kwargs)

    name = str

    # The collection of invoice statuses categorized by this status type
    statuses = statuses

class term(orm.entity):
    """ A term or condition for an invoice. ``invoice.invoice``  and
    ``invoice.item`` have collections of ``terms``.

    Note that this is modeled after the INVOICE TERM in "The Data Model
    Resource Book".
    """
    value = dec

class termtype(orm.entity):
    """ Categorizes a term.

    Note that this is modeled after the INVOICE TERM in "The Data Model
    Resource Book".
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.orm.ensure(expects=('name',), **kwargs)

    name = str

    # The collection of ``terms`` categorized by this ``termtype``.
    terms = terms

class invoiceitem_shipmentitem(orm.association):
    """ Associates an invoice ``item`` with a shipment item
    (``shipment.item``). 
    """

    invoiceitem = item
    shipmentitem = shipment.item
