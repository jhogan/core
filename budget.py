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
import apriori
import invoice
import order
import orm
import party
import account

class statuses(orm.entities):               pass
class items(orm.entities):                  pass
class budgets(orm.entities):                pass
class operatings(budgets):                  pass
class capitals(budgets):                    pass
class types(apriori.types):                 pass
class statustypes(apriori.types):           pass
class itemtypes(apriori.types):             pass
class roles(party.roles):                   pass
class roletypes(apriori.types):             pass
class periods(orm.entities):                pass
class periodtypes(apriori.types):           pass
class revisions(orm.entities):              pass
class item_revisions(orm.associations):     pass
class reviews(orm.entities):                pass
class reviewtypes(orm.entities):            pass
class scenarios(orm.entities):              pass
class rules(orm.entities):                  pass
class budget_scenarios(orm.associations):   pass
class item_requirements(orm.associations):  pass
class item_payments(orm.associations):      pass
class itemtype_accounts(orm.associations):  pass

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

    # Making the ``budget`` entity recursive is a simple way to model
    # budegt revisions.
    #
    # Budget revisions may simply be handled by creating and
    # maintainting a whole new budeget each time a revision is needed.
    # The old budget can be relate to the next budget via this recursive
    # relationship. While simple, the disadvantage is that the whole
    # budget needs to be rerecorded, even though many of the budgeted
    # items may remain consisistent from one revision to the next. 
    #
    # For a more robust vay of revisioning budgets, see the
    # ``revision`` entity.
    budgets = budgets

    # A collection of budget revisions
    revisions = revisions

    # A collection of reviews
    reviews = reviews

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
        self.orm.default('comment', None)

    entered = date

    comment = text

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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.orm.default('justification', None)
        self.orm.default('purpose', None)

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

    # A collection of budget revisions
    revisions = revisions

    # A collection of budget ``scenarios`` for this budget ``item``
    scenarios = scenarios

    # Each ``order.item`` may be authorized via and allocated to a
    # specific budget ``item``. This relationship establishes what
    # commitments (and dollar amounts) have been made to various
    # budget ``items``.

    # FIXME:055e5c02 Before this line can be uncommented, a bug in the
    # way FKs are named by the ORM needs to be addressed. When this line
    # is uncommented, order.item.orm.mappings has two FKs named
    # `itemid`.  One of the foreign keys is for this line, the other is
    # for order.item itself since its recursive. Foreign key names
    # should be fully qualified.
    # orderitems = order.items

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
    # The collection of budgetary ``periods``.
    periods = periods

class revision(orm.entity):
    """ A budget may have one or more budget ``revisions`` over time,
    which can affect many parts of the ``budget``. Each budget
    ``revision`` may affect more than one budget ``item`` and vice
    versa, thus resulting in the many-to-many relationship between
    budget ``items`` and budget ``revisions``, resolved by the budget
    revision ``item_revisions``, which is an associative entity.

    Note that this entity was originally called BUDGET REVISION in "The Data
    Model Resource Book".
    """

    # The date the budget was revised
    revised = date

    # The version number
    number = str

class item_revision(orm.association):
    """  Each budget ``item`` may be affected by one or more budget
    revision ``item_revisions``. 

    Note that this entity was originally called BUDGET REVISION IMPACT
    in "The Data Model Resource Book".
    """

    # The budget ``item`` side of the association
    item = item

    # The budget ``revision`` side of the association
    revision = revision

    # The **revised amount** maintains the reduction or increased amount
    # of a budgeted ``item``.
    amount = dec

    # Indicates the item has been added to the budget by the budget
    # revision.  If the bool is False, the item would be considered
    # ``issubtractive``. If the bool is None, it means that the item has
    # neither been added or substracted, but rather the amount has
    # changed.
    #
    # Note that the book calls this the **add delete flag**
    # added or deleted according to the budget ``revision``.
    isadditive = bool

    # Shows why each budgeted item needed to be changed.
    reason = text

class review(orm.entity):
    """ Provides the information about which parties were involved in
    the review process via the relationship from ``review`` to party.

    Note that this entity was originally called BUDGET REVIEW in "The
    Data Model Resource Book".
    """

    # Identifies when the ``party`` was involved in the review.
    reviewed = date

    # The ``party`` involved in the review.
    party = party.party

class reviewtype(orm.entity):
    """ Indicates each ``party``'s decision regarding the budget
    ``review``.
    
    Note that this entity was originally called BUDGET REVIEW RESULT
    TYPE in "The Data Model Resource Book".
    """

    # NOTE Counterintuitivly, this should not be a subentity of
    # apriori.type because it allowes for a ``comment`` given by the
    # ``review.party``.
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.orm.default('comment', None)

    name = str

    # Allows any personal opinions about the review to be document.
    comment = text

    # The collection of reviews classified by this review type
    reviews = reviews
    
class scenario(orm.entity):
    """ Budgeted ``items`` frequently have different figures associated
    with them based on various scenarios. For example, there may be
    different moneys allocated to a budegeted ``item`` depending on
    whether the market conditieons are excellent, fair or poor. 

    Variations on the amounts budgeted are based on different budget
    ``scenarios``. Each ``scenario`` has a ``name`` that stores the type
    of scenario such as "excellent market condition", "poor market
    conditions", "worst case", "best case", "major deal signed", "no
    major deal signed". This allows maintaining multiple budgeted
    figures based on these conditions.

    Note that this entity was originally called BUDGET SCENARIO in "The
    Data Model Resource Book".
    """

    # Each ``scenario`` has a ``name`` that stores the type of scenario
    # such as "excellent market condition", "poor market conditions",
    # "worst case", "best case", "major deal signed", "no major deal
    # signed". This allows maintaining multiple budgeted figures based
    # on these conditions.
    name = str

    # A collection of budget scenario ``rules`` for this budget
    # ``scenario``.
    rules = rules

    # FIXME:8cf51c58 This causes problems for some reason. 
    # A collection of budget scenario applications for this budget
    # ``scenario``.
    # budget_scenarios = budget_scenarios

class budget_scenario(orm.associations):
    """ An association between a budget ``item`` or a ``budget`` and a
    budget ``scenario``. ``budget_scenarios``. Each ``budget`` or budget
    ``item`` may have several associations with ``scenarios``which store
    either an ammount change or a percentage change for each budget
    ``scenario``.

    Note that this entity was originally called BUDGET SCENARIO
    APPLICATION in "The Data Model Resource Book".
    """

    # Maintains the dollar amount of the change that is applied to each
    # budget ``item`` amount
    amount = dec

    # Maintains the percentage of the change that is applied to each
    # budget ``item`` amount
    percent = dec

    # The budget side of the association
    #budget = budget 

    # The budget `item` side of the association (as an alternative to
    # ``budget`` - see above)
    item = item

    # The scenario side of the association
    scenario = scenario

class rule(orm.entity):
    """ The budget scenario ``rule`` stores the standard **percentage
    change** or **amount change** with which to raise or lower the
    amounts or percentages for standard budget ``itemtypes``. These
    rules may be the default amounts or percentages tied to the budget
    item ``scenarios``; however, they may be different than the values
    for specific budgeted items because more might be known at budgeting
    time.

    Note that this entity was originally called BUDGET STANDARD RULE in
    "The Data Model Resource Book".
    """

    amount = dec
    percent = dec

class item_requirement(orm.association):
    """ An association between a budget ``item`` and a ``requirement``
    (``apriori.requirement``). A ``requirement`` may be funded via many
    budget ``items`` and vice versa through this association. This
    relationship provides information about the outstanding needs for
    the use of budgets.

    Note that this entity was originally called REQUIREMENT BUDGET
    ALLOCATION in "The Data Model Resource Book".
    """
    # The item side of the association
    item = item

    # The requirement side of the association
    requirement = apriori.requirement

    amount = dec

class item_payment(orm.association):
    """ This association allows for a many-to-many relationship between
    budget ``items`` and ``invoice.payments``. It records both
    disbursements and receipts against budget items, but only for
    disbursements that *do not have* a corresponding order associated
    with them.

    Note that this entity was originally called PAYMENT BUDGET
    ALLOCATION in "The Data Model Resource Book".
    """
    # The item side of the association
    item = item

    # The payment side of the association
    payment = invoice.payment

    amount = dec

class itemtype_account(orm.association):
    """ Associates a general ledger account (``account.account``) to a
    budget item type (``itemtype``).

    Note that this entity was originally called GL BUDGET XREF in "The
    Data Model Resource Book".
    """

    # The budget item type (``itemtype``) side of the association
    itemtype = itemtype

    # The general ledger account side of the assoociation
    account = account.account

    # The rules for how budget items map to general ledger accounts may
    # change over time. This datespanallows different mappings over
    # time.
    span = datespan

    percent = dec

