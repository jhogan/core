# vim: set et ts=4 sw=4 fdm=marker

# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2020

""" This module contains ``orm.entity`` objects related the management
of sales orders, purchase orders, etc.

These entity objects are based on the "Ordering Products" chapter of
"The Data Model Resource Book".

Examples:
    See test.py for examples. 

Todo:
    TODO: So far, the most common order entities have been declared. The
    second section of the "Ordering Products" chapter, called "Optional
    Order Model", offers data models to track order requirements
    (partially implemented), requests, quotes and agreements (the book
    calls these entities REQUIREMENTs, REQUESTs, QUOTEs and AGREEMENTs
    respectively). These can be implemented when needed.
"""

from datetime import datetime, date
from dbg import B
from decimal import Decimal as dec
from orm import text, timespan, datespan
import entities
import orm
import party
import primative
import product
import apriori

class orders(orm.entities):  pass

# TODO Write validation rule to disallow instance of `item`. Only allow
# subtypes of `item` like `salesitem` and `purchaseitem` entity objects.
# If the composite is a `purchase`, then only `purchaseitem` should be
# allowed. Likewise when the composite is a salesorder entitiy objects.
class items(orm.entities):                  pass
class salesitems(items):                    pass
class purchaseitems(items):                 pass
class salesorders(orders):                  pass
class purchaseorders(orders):               pass
class order_parties(orm.associations):      pass
class order_partytypes(apriori.types):      pass
class adjustments(orm.entities):            pass
class adjustmenttypes(apriori.types):       pass
class taxes(adjustments):                   pass
class shippings(adjustments):               pass
class miscellaneouses(adjustments):         pass
class discounts(adjustments):               pass
class surcharges(adjustments):              pass
class fees(adjustments):                    pass
class rates(orm.associations):              pass
class statuses(orm.entities):               pass
class statustypes(apriori.types):           pass
class terms(orm.entities):                  pass
class termtypes(apriori.types):             pass
class item_items(orm.associations):         pass
class requirementtypes(apriori.types):      pass
class requirement_items(orm.associations):  pass

class order(orm.entity):
    """ The generic, abstract order class from with the `salesorder` and
    `purchase` classes inherit.
    """

    # The date on which the enterprise received or gave the order. This
    # is in contrast to the inherited `createdat` date which is used to
    # indicate when the order was entered into the system (called the
    # `entry date` in "The Data Model Resource Book").
    received = date

    # The collection of `saleitems` or `purchaseitem` for this order.
    items = items

    # A collection of `adjustment` entities that can be applied to an
    # order to increase or decrease the orders price
    adjustments = adjustments

    # A collection of statuses that this order has been in, such as
    # "received", "approved" or "canceled".
    statuses = statuses

    # A collection of arrangements that a party has agreed on regrading
    # the ``order``.
    terms = terms

    @property
    def total(self):
        # FIXME This seems to produce different results each time. I
        # think it's because the the adjustments, particularlly the
        # percentage-based adjustments are applied in different orders.
        # The `adjustment` class needs an ordinal property so the order
        # in which adjustments applied can be specified. 
        
        # TODO: Most `adjustments` (`tax`, `shipping`, etc) will
        # increment the total. However, an adjustment, by definition,
        # could decrement the total. Currently, this algorithm only
        # increments the total. Some steps may need to be taken to to
        # allow adjustments to decrement the total.
        for itm in self.items:
            r += itm.total

        for adj in self.adjustments:    
            r = adj.apply(r)

        return r

class item(orm.entity):
    """ A line item of an order representing the ordering of a specific
    good or service. Each line item references exactly one product
    (``product.product``) or exactly one feature (``product.feature``).

    Terminological note: The phrase "order line item" should not be used
    to describe an ``item``. This phrase connotes a physical line on an
    order form which may encompass many other things aside from the
    items that have been ordered such as records adjustments, taxes,
    estimated freightcosts, explanations, etc. ``item`` simply
    represents the products that have been ordered.
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

    # An item can have a collection of items. When an item has a
    # constiuent item, the implication is the constient items are
    # features of the composite item.
    items = items

    adjustments = adjustments

    # A collection of arrangements that a party has agreed on regrading
    # the ``item``.
    terms = terms

    # A collection of statuses that this item has been in, such as
    # "received", "approved" or "canceled".
    statuses = statuses

    @property
    def total(self):
        return self.price * self.quantity

class salesitem(item):
    """ Represents an items for a sales order.

    Note that this entity was originally called SALES ORDER ITEM in "The
    Data Model Resource Book".
    """

    # The party that the item will be shipped to.
    shipto = party.shipto

    # The address that the item will be shipped to.
    shiptousing = party.contactmechanism

    # NOTE We may want an `installat` and `installusing` attributes if
    # installation is need.

class purchaseitem(item):
    """ Represents an items for a purchase order.

    Note that this entity was originally called PURCHASE ORDER ITEM in
    "The Data Model Resource Book".
    """

    # The party that the item will be shipped to.
    shipto = party.shiptobuyer

    # The address that the item will be shipped to.
    shiptousing = party.contactmechanism

class salesorder(order):
    """ A class representing a sales order. 

    Note that this entity was originally called SALES ORDER in "The
    Data Model Resource Book".
    """

    # NOTE The party role attributes such as `placing`, `taking`,
    # `billto` are the formal, i.e., hardcoded wasy of assigning a party
    # a role to the order. These entity objects are useful for
    # encaspulating business rules. However, a more flexable alternative
    # may be to use the order_party associaton. This association entity
    # associates a party with an order along with a role. This can
    # overcome the limitations of the formal party role entity objects.
    # For example, it could allow one or many `billto` roles where as
    # the formal role happens to limited us to one.

    # The role that placed the order. To get the actual party that
    # placed the order, we would use something like `so.placing.party`.
    placing = party.placing

    # The party role that is taken the order. An order may be taken by a
    # particular subsidiary, division or department.
    taking = party.role

    # Tho party role that is responsible for the bill.
    billto = party.billto

    # The contact mechanism the order was placed using, such as a phone
    # number or address.
    placedusing = party.contactmechanism

    # The contact mechanism the order was the order was taken from, such
    # as a phone number or address.
    takenusing = party.contactmechanism

    # The contact mechanism for the orders billto - probably a
    # party.address.
    billtousing = party.contactmechanism

class purchaseorder(order):
    """ A class representing a purchase order

    Note that this entity was originally called PURCHASE ORDER in "The
    Data Model Resource Book".
    """

    # The placing buyer is the role a party plays when it places a
    # purchase order.
    placing = party.placingbuyer

    # The supplier is the party role that takes purchase orders 
    supplier = party.supplier

    # The bill to is the role a party plays when it picks up the bill
    # for a purchase order.
    billto = party.billtopurchaser

    # The contact mechanism the purchase order was placed using, such as
    # a phone number or address.
    placedusing = party.contactmechanism

    # The contact mechanism the order was the purchase order was taken
    # from, such as a phone number or address.
    takenusing = party.contactmechanism

    # The contact mechanism for the purchase orders billto - probably a
    # party.address.
    billtousing = party.contactmechanism

class order_partytype(apriori.type):
    """ Each role is described by a roletype entity. 

    Example include: 'salesperson', 'processor', 'reviewer',
    'authorizer'.
    """
    order_parties = order_parties

class order_party(orm.association):
    """ In additional to the key order relationships (i.e., `placing`,
    `taking`, `billto`, `shipto`), many other parties could be involved
    in the order process. Examples include people giving the order, the
    person processing the order, the person approving the order, the
    parties that are scheduled to coordinate instalation, and the
    parties responsible for fulfilling the order.  An `order` is
    associated with zero or more parties via this association which is
    described by the `order_partytype` entity.

    While many times these roles will involve people, organizations may
    also play some of these roles, such as service team that is
    responsible for ensuring fulfillment of an order.

    Note that this association was originally called ORDER ROLE in "The
    Data Model Resource Book".
    """

    # The order in this association
    order = order

    # The party part of this association
    party = party.party

    # The percentage the `party` contributed to the order. This datum
    # could be used to calculate commissions.
    percent = dec

class adjustment(orm.entity):
    """ An adjustment, by price or percentage, to an order total price.
    Subtypes of adjustments include (sales) '`tax'`, '`shipping'` (and
    handling charges), '`discount'` adjustment, '`surcharge'` adjustment and
    more. An adjustment has many-to-one relationships with an '`order'`
    and an '`item'`.

    Note that this entity was originally called ORDER ADJUSTMENT in "The
    Data Model Resource Book".
    """

    # NOTE amount or percent should be specified but never both and
    # never neither. A validation rule should be written to ensure this.

    # The currency amount the order should be adjusted for.
    amount = dec

    # The percentage the orders sales price the order should be adjusted
    # for.
    percent = dec

    def apply(self, amt):
        if self.percent:
            amt -= amt * self.percent / 100
        elif self.amount:
            amt -= self.amount
        else:
            raise ValueError(
                "Can't adjust. "
                'Either price or percent must be specified.'
            )

        return amt
 
class adjustmenttype(apriori.type):
    """ Provides the ability to classify the various types of
    adjustments into detailed categories.

    Note that this entity was originally called ORDER ADJUSTMENT TYPE in
    "The Data Model Resource Book".
    """

    # The adjustments that belong to this adjustment type
    adjustments = adjustments

class tax(adjustment):
    """ Add this adjustment to an ``order``'s or an ``item``'s
    ``adjustments`` collection to apply a sales tax to the ``order`` or
    order ``item`` respectively.

    Note that this entity was originally called SALES TAX in "The Data
    Model Resource Book".
    """

class shipping(adjustment):
    """ Short for "shipping and handling charge", add this adjustment to
    an ``order``'s or an ``item``'s ``adjustments`` collection to apply
    a shipping and handling charge to the ``order`` or order ``item``
    respectively.

    Note that this entity was originally called SHIPPING AND HANDLING
    CHARGE in "The Data Model Resource Book".
    """

class miscellaneous(adjustment):
    """ Short for "miscellaneous charge", add this adjustment to
    an ``order``'s or an ``item``'s ``adjustments`` collection to apply
    any other charges that could occur to an ``order`` or order ``item``
    respectively.

    Note that this entity was originally called MISCELLANEOUS CHARGE in
    "The Data Model Resource Book".
    """

class discount(adjustment):
    """ Add this adjustment to an ``order``'s or an ``item``'s
    ``adjustments`` collection to apply a discount to an ``order`` or
    order ``item`` respectively.

    Note that this entity was originally called DISCOUNT ADJUSTMENT in
    "The Data Model Resource Book".
    """

class surcharge(adjustment):
    """ Add this adjustment to an ``order``'s or an ``item``'s
    ``adjustments`` collection to apply a surcharge to an ``order`` or
    order ``item`` respectively.

    Note that this entity was originally called SURCHARGE ADJUSTMENT in
    "The Data Model Resource Book".
    """

class fee(adjustment):
    """ Add this adjustment to an ``order``'s or an ``item``'s
    ``adjustments`` collection to apply a fee to an ``order`` or
    order ``item`` respectively.
    """

class rate(orm.association):
    """ ``rate`` stores a sales tax percentage that could very by
    ``party.region`` and also may very by ``product.category``.

    Note that this entity was originally called SALES TAX LOOKUP in
    "The Data Model Resource Book".
    """

    # The sales tax rate.
    percent = dec

    # The geographic region, such as County, City or State.
    region = party.region

    # The product category that may affect the tax rate (perhaps for a
    # special "sin tax" on tobacco or alcohol products).
    category = product.category

class status(orm.entity):
    """ An ``order`` or order ``item`` may be in a number of statuses over a
    period of time such as "received", "approved" and "canceled".
    `order` and `item` have a collection of statuses that
    track the history their status history.

    The name of the states is store in `statustype`.

    Note that this entity was originally called ORDER STATUS in "The
    Data Model Resource Book".
    """

    # The date and time when the order transitioned in to the given
    # status.
    begin = datetime

class statustype(apriori.type):
    """ Records the type of status. Typical values for the ``name``
    attribute include: "received", "approved" and "canceled".

    Note that this entity was originally called ORDER STATUS TYPE in
    "The Data Model Resource Book".
    """

    # The collection of statuses belonging to this type
    statuses = statuses

class term(orm.entity):
    """ An ``order`` or an ``item`` can have multiple ``terms``. A term
    an arrangement that a party has agreed on regarding an ``order`` or
    an ``item``.

    Note that this entity was originally called ORDER TERM in "The Data
    Model Resource Book".
    """
    
    # The term value attribute is applicale only to some of the order
    # terms, an its meaning is dependent hon the type of term.
    value = dec

class termtype(apriori.type):
    """ The ``termtype`` class categorizes ``term`` entity objects.

    Note that this entity was originally called TERM TYPE in
    "The Data Model Resource Book".
    """

    # The collection of term entity objects that belong to this
    # termtype.
    terms = terms

class item_item(orm.association):
    """ This reflexive association links a ``item`` to another.

    An example of this association occurs when a soles order itme is
    dependent on a purchase order item. For example, a distributor may
    receive a sales order but may not have enough inventory in stock to
    cover one of the items on it. In tur, the distributor may place a
    purchace order to one of its suppliers (or many POs to mayn
    suppliers) to fulfill the item that was short. In other words, the
    sales order item was "backordered" and covered by a pruchase order
    item.

    Note that this entity was originally called ORDER ITEM ASSOCIATION
    in "The Data Model Resource Book".
    """

    # NOTE We may want to create an item_item_type entity to indicate
    # the type of association this is. 

    # The first item being linked
    subject = item

    # The other item being linked
    object = item

class requirementtype(apriori.type):
    """ Defines the possible categories for the requirements.

    Possible requirement types include "project", "maintenance" and
    "production run".
    """

    # A collection of ``requirements`` that correspond to this type
    requirements = apriori.requirements

class requirement_item(orm.association):
    # TODO
    """
    Note that this entity was originally called ORDER REQUIRMENT
    COMMITMENT "The Data Model Resource Book".
    """

    quantity = dec
