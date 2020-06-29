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

class shipments(orm.entities):                pass
class items(orm.entities):                    pass
class statuses(orm.entities):                 pass
class statustypes(orm.entities):              pass
class shipitem_orderitems(orm.associations):  pass
class item_features(orm.associations):        pass
class packages(orm.entities):                 pass
class item_packages(orm.associations):        pass
class roletypes(party.roletypes):             pass
class roles(party.roles):                     pass
class receipts(orm.entities):                 pass
class reasons(orm.entities):                  pass
class issuances(orm.entities):                pass
class picklists(orm.entities):                pass
class picklistitems(orm.entities):            pass
class issuanceroles(party.roles):             pass
class issuanceroletypes(party.roletypes):     pass
class documents(orm.entities):                pass
class documenttypes(orm.entities):            pass
class bols(documents):                        pass
class slips(documents):                       pass
class exports(documents):                     pass
class manifests(documents):                   pass
class portcharges(documents):                 pass
class taxandtarrifs(documents):               pass
class hazardouses(documents):                 pass
class routes(orm.entities):                   pass
class types(orm.entities):                    pass
class carriers(party.organizationals):        pass
class assets(orm.entities):                   pass
class vehicals(orm.entities):                 pass

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

    # A collection of shipping documents for this shipment.
    documents = documents

    # A collection of routes describing the journey that comprise the
    # shipment.
    routes = routes

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

    # A shipment item may have multiple issuances.
    issuances = issuances

    # A collection of shipping documents for this shipping item.
    documents = documents

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

class item_feature(orm.association):
    item = item
    feature = product.feature

class package(orm.entity):
    """ A package, such as a box, carton or container used to ship a
    good. An ``item`` may be packaged within one or more ``package``
    entity and vice-versa hence the associative entity ``item_package``.

    Note that this entity was originally called SHIPMENT PACKAGE in "The
    Data Model Resource Book".
    """

    # The date and time the package was created. Not to be confused with
    # `createdat`, which is the time the ``package`` record was created.
    created = datetime
        
    # An external id for the package such as its barcode id.
    packageid = str

    # Each shipment ``package `` is received via one or more shipment
    # ``receipts`` that store the details of the receipt.
    receipts = receipts

    # A collection of shipping documents for this packages.
    documents = documents

class item_package(orm.association):
    """ Creates a many-to-many relationship between ``item`` and
    ``package``.

    Note that this entity was originally called PACKAGING CONTENT in
    "The Data Model Resource Book".
    """

    # The the shipping item
    item = item

    # The package the item is shipped in.
    package = package

    # Determines how many items are in th package
    quantity = dec

class roletype(party.roletype):
    """ Describes the ``role`` being played by a party. 
    """

class role(party.role):
    """ For each ``receipt``, there could be multiple shipment receipt
    ``roles`` such as the person signing for the receipt, the inspector
    of the goods, the person responsible for storing the receipt within
    the inventory, the receiving manager, and the organization that is
    receiving the item.

    Note that this entity was originally called SHIPMENT RECEIPT ROLE in
    "The Data Model Resource Book".
    """

class receipt(orm.entity):
    """ Each shipment ``package`` is received via one or more shipment
    ``receipts`` that store the details of the receipt.

    Note that this entity was originally called SHIPMENT RECEIPT in
    "The Data Model Resource Book".
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.orm.isnew:
            self.description = None

    # The exact date and time the receipt occured
    receivedat = datetime

    # The relationship to ``product.good`` maintains what was received
    # for standard goods (see ``description`` for non-standard goods).
    good = product.good

    # Maintains what was received for non-standard items that would not
    # be maintaind as a `product.good` within the entity model - for
    # instance, for one-time purchases.
    description = str

    # Represents the quantity of the ``good`` (or non-standard good
    # reference in ``description``) that the organization determined to
    # be acceptable to receive.
    accepted = dec

    # Represents the quantity of the ``good`` (or non-standard good
    # reference in ``description``) that the organization determined to
    # be unacceptable to receive.
    rejected = dec

    # The collection of roles for the receipt. See ``role`` for more.
    roles = roles

    # The collection of rejection ``reasons`` for this receipt. (see
    # ``reason`` for more).
    reasons = reasons

class reason(orm.entity):
    """ Stores an explanation of why certain items may not be accepted.

    Note that this entity was originally called REJECTION REASON in
    "The Data Model Resource Book".
    """

    description = str

class issuance(orm.entity):
    """ A item ``issuance` is the act of pulling ``product.items` from
    inventory. These items are usually pulled in order to be shipped
    (though this is not always the case, such as when an item is pulled
    from inventory for use in the same location that the item had been
    stored in.)


    Note that this entity was originally called ITEM ISSUANCE in
    "The Data Model Resource Book".
    """

    # The date and time the item was issued
    issuedat = datetime

    # The number of items issued
    quantity = dec

    inventoryitem = product.item

    # NOTE A one-to-many relationship exists between ``item`` and
    # ``issuance``; therefore an implicit ``item`` attribute is
    # available at runtime.

    inventoryitem = product.item

class picklist(orm.entity):
    """ Based on shipment needs, which could be obtaind by reviewing the
    a ``shipment`` and its ``items``, a ``picklist`` is generated,
    identifying the plan for picking from inventory. Each `picklist``
    will have a collection of ``picklistitems`` that store the quantity
    of goods needed and are to be picked from each inventory item
    (``product.item``) in order to meet the shipment need.

    Note that this is based of the PACKLIST entity in "The Data
    Model Resource Book".
    """
    # The date and time the picklist was created. Not to be confused
    # with implicit ``createdat``, which is the date and time the
    # ``picklist`` record was created.
    created = datetime

    items = picklistitems

class picklistitem(orm.entity):
    """ A line item of a ``picklist``.

    Note that this is based of the PACKLIST ITEM entity in "The Data
    Model Resource Book".
    """
    # The invetory item 
    item = product.item

    # The quantity of this picklist item
    quantity = dec

class issuancerole(party.role):
    """ Each item ``issuance` may have mayn people involved in this
    process and therefore may have many ``issuanceroles`` for each party
    involved; each role is described by the ``issuanceroletype``.
    """

class issuanceroletype(party.roletype):
    """ Describes the ```issuancerole```
    """

class document(orm.entity):
    """ Shipments often are required to carry shipment documents for
    various reasons. Some reason are practical in nature,such as to
    easily identify the contens of packages with a packing slip or bills
    of lading to identify the contents of shipments. Som reas are
    reguralted, such as tak, tariff, or export documentations.

    Depending on the type of shipping document (subentity objcets of
    ``document``), the documentment may be related to the ``shipment``,
    the ``item`` or the ``package``.
    """

    # IMPLEMENTATION NOTE: Currently, ``document`` inherits from
    # ``orm.entity``. However, the book indicates that this class should
    # inherit from a general ``document`` class (where as the current
    # class would mearly be a subentity for _shipping documents_. This
    # has currently not been implemented because it is not clear what
    # module the generic ``document`` class would go in.This has
    # currently not been implemented because it is not clear what module
    # the generic ``document`` class would go in.

    description = str

class documenttype(orm.entity):
    """ Provides for other types of documents than the standard ones
    (the subentities of ``document``).

    Note that this entity was originally called DOCUMENT TYPE in
    "The Data Model Resource Book".
    """

    name = str

    # The collection of documents that this class describes
    documents = documents

class bol(document):
    """ A bill of lading document.

    The bill of lading is a required document to move a freight
    shipment. The bill of lading (BOL) works as a receipt of freight
    services, a contract between a freight carrier and shipper and a
    document of title. The bill of lading is a legally binding document
    providing the driver and the carrier all the details needed to
    process the freight shipment and invoice it correctly.

    Note that this entity was originally called BILL OF LADING in
    "The Data Model Resource Book".
    """

class slip(document):
    """ A packaging slip document.

    Note that this entity was originally called PACKAGING SLIP in
    "The Data Model Resource Book".
    """

class export(document):
    """ A export document.

    Note that this entity was originally called EXPORT DOCUMENTATION in
    "The Data Model Resource Book".
    """

class manifest(document):
    """ A shipping manifest document.

    Note that this entity was originally called MANIFEST in
    "The Data Model Resource Book".
    """

class portcharge(document):
    """ A port charges document.

    Note that this entity was originally called PORT CHARGES DOCUMENT in
    "The Data Model Resource Book".
    """

class taxandtarrif(document):
    """ A tax and tarrif shipping document.

    Note that this entity was originally called TAX AND TARIFF DOCUMENT  in
    "The Data Model Resource Book".
    """

class hazardous(document):
    """ A hazardous materials shipping document.

    Note that this entity was originally called HAZARDOUS MATERIALS
    DOCUMENT in "The Data Model Resource Book".
    """
    entities = hazardouses

class route(orm.entity):
    """ Maintains information about each leg of the journey for a
    ``shipment``. It identifies the particular portions of the journey along
    which a shipment travels. It identifies the particular portions of
    the journey along which a shipment travels.

    Each route is describe by a shipment method ``type`` entity, which
    identifies it as ground, cargo ship, air, etc. An implicite ``type`
    attribute will be available for each route object::
        
        rt = route()
        rt.type = type(name='air')

    Note that this entity was originally called SHIPMENT ROUTE SEGMENT
    in "The Data Model Resource Book".
    """

    # The source facility from which this route originates. Note that
    # this relationships to ``facility`, as well as ``destination`` are
    # optional because the enterprise may not have the will and means to
    # track each physical location to and from which the shipment
    # travels. The relationship would probably not be needed for
    # enterprises that always use external carriers to ship their goods.
    source = party.facility

    # The destination facility to which this route terminates
    destination = party.facility

class type(orm.entity):
    """ A type of shipment method such as ground, first-class air,
    train, truck, cargo ship or air.

    Note that this entity was originally called SHIPMENT METHOD TYPE in
    "The Data Model Resource Book".
    """

    # The name of the shipment method, e.g., 'ground', 'cargo ship', or
    # 'air'.
    name = str

    # The shipment ``route`` segments that this type describes.
    routes = routes

class carrier(party.organizational):
    """ An organizational role where a party acts as a carrier.
    Shipments must be shipped by a particular ``carrier`` , even if that
    carrier is part of the enterprise itself.
    """

class asset(orm.entity):
    """ A fixed asset.

    IMPLEMETATION NOTE/TODO: FIXED ASSET is defined in the Work Effort
    chapter. It was prematurly introduced in the shipping chapter so its
    subentity, VEHICAL could be introduced. Since FIXED ASSET is in a
    future chapter, it's still up in the air as to where ``asset``
    should go to prevent circular reference issues - perhaps it makes
    sense to put it in product.py so shipment.py and effort.py can
    access it. Either way, this is all TBD.

    Note that this entity was originally called FIXED ASSET in
    "The Data Model Resource Book".
    """
    name = str

class vehical(orm.entity):
    """ Optionally, the ``vehicle`` involved in a shipment ``route``
    segment may be tracked. This is usually done in circumstances where
    the enterprise maintanis its own fleet. If the enterprise uses
    external carrieres, the enterprise would probably not need to track
    the vehical. Each shipment ``route`` segment will track zero or one
    vehical.
    """

    # IMPLEMENTATION NOTE: Information that enterprises may want to keep
    # about the `vehicle`` would be the statistics behind the use of the
    # vehicle, such as the *start mileage** and *end mileage* (if
    # appropriate) and amount of *fuel used*. For detailed tracking, one
    # may also want to track the date and time a particular vehicle
    # picked up a shipment and when it unloaded it. With this
    # information, it can easily be determined in what order multiple
    # vehicles were used to deliver a single shipment and how long it
    # took, including transfers.

    # The shipment ``route`` segments that this vehical is involved in
    # to transport the given ``shipment``.
    # routes = routes
