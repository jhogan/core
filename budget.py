# vim: set et ts=4 sw=4 fdm=marker

# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2020

""" This module contains ``orm.entity`` objects related to the tracking
of budgetary data.

These entity objects are based on the "Accounting and Budgeting"
chapter of "The Data Model Resource Book".

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
import apriori

class statuses(orm.entities): pass
class items(orm.entities): pass
class budgets(orm.entities): pass
class operatings(budgets): pass
class capitals(budgets): pass
class types(apriori.types): pass
class statustypes(apriori.types): pass
class itemtypes(apriori.types): pass
class roles(party.roles): pass
class roletypes(apriori.types): pass
class periods(orm.entities): pass
class periodtypes(apriori.types): pass

class budget(orm.entity):
    """ Describes the information about the amounts of moneys needed for
    a group of expense items over a certain period of time.  ``budget``
    are mechanism for planning the spending of money. Each ``budget``
    must be composed of one or mun budget ``item``, which stores the
    details of what exactly is being budgeted.

    A ``budget`` has a many-to-one relationship, and thus an implicit
    attribute for, the ``period``, which identifies the time
    period for which the budget applies. This may represent different
    time periods for different enterprises.

    Each ``budget`` must be composed of one or more ``items``.

    Note that this entity was originally called BUDGET in "The
    Data Model Resource Book".
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    name = str

    statuses = statuses

    items = items

    roles = roles

    periods = periods

class operating(budget):
    """ A budget subtype for expense items.

    Note that this entity was originally called OPERATING BUDGET in "The
    Data Model Resource Book".
    """

class capital(budget):
    """ A budget subtype for fixed assets and long-term items.

    Note that this entity was originally called CAPITAL BUDGET in "The
    Data Model Resource Book".
    """

class type(apriori.type):
    """  Allows for the categorizationg of other types of ``budget``s
    according to the needs of the organization.

    Note that this entity was originally called BUDGET TYPE in "The
    Data Model Resource Book".
    """
    budgets = budgets

class status(orm.entity):
    """ Each ``budget`` generally moves through various stages as the
    budget process unfolds. A ``budget`` is typically created ona a
    certain date, reviewed, submitted for approval, then accepted,
    rejected, or sent back to the submitter for modifications.

    Note that this entity was originally called BUDGET STATUS in
    "The Data Model Resource Book".
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.orm.ensure(expects=('name',), **kwargs)

    entered = date

    entities = statuses

    name = str

class statustype(apriori.type):
    statuses = statuses

class item(orm.entity):
    """ Each ``budget`` must be composed of one or more budget
    ``item``s. A budget ``item`` stores the details of exactly what is
    being budgeted.

    ``item``s may be recursively related to other ``item``s
    allowing for a hierarchy of budget item rollups (see the items
    attribute).

    Note that this entity was originally called BUDGET ITEM in
    "The Data Model Resource Book".
    """

    # NOTE There is an implicit ``itemtype`` attribute that indicates
    # the ``item``'s type.
 
    # Defines the total amount of funds required for the item within the
    # time period.
    amount = dec

    # Identifies why the items are need
    purpose = str

    # Describes why the budgeted ``amount`` of money should be expended.
    justification = text

    # ``item``s may be recursively related to other ``item``s
    # allowing for a hierarchy of budget item rollup.
    items = items

class itemtype(apriori.type):
    """ Classifies the budegtary ``item``s into types so that common
    budget item descriptions can be reused.

    Note that this entity was originally called BUDGET ITEM TYPE in
    "The Data Model Resource Book".
    """
    items = items

# TODO Is ``party.role`` the correct base type?
class role(party.role):
    """ Each ``budget`` may have many parties (``party.parties``)
    involved in various ``bugetroles``. Budget roles for parties (which
    may be a person (``party.person``) or organization
    (``party.organization``)) include the initiator of the budget
    request, the party for whom the budget is requestd, the reviewer(s)
    of a budget, and the approver of the budget.

    Note that this entity was originally called BUDGET ROLE in
    "The Data Model Resource Book".
    """
    budgets = budgets
    
class roletype(apriori.type):
    roles = roles

class period(orm.entity):
    """  Maintains possible time periods for which ``budgets`` could be
    allocated.

    Note that this entity was originally called STANDARD TIME PERIOD in
    "The Data Model Resource Book".
    """
    span = datespan

class periodtype(apriori.type):
    """Identifies the particular type used by ``budget``.

    In `standardperiod``, common period types are "month",
    "quarter", and "year".

    Note that this entity was originally called PERIOD TYPE in "The Data
    Model Resource Book".
    """
    # The collection of budetary ``periods``.
    periods = periods
