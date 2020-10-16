# vim: set et ts=4 sw=4 fdm=marker

# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2020

""" This module contains ``orm.entity`` objects related to the tracking
of human resource data.

These entity objects are based on the "Human Resources" chapter of "The
Data Model Resource Book".

Examples:
    See test.py for examples. 

TODO:
    
    TODO An option extention to this object model would be to include
    the POSITION TYPE CLASS and POSITION CLASSIFICATION TYPE to provide
    further classification options for positions. See figure 9.4 from
    the book.
"""

from datetime import datetime, date
from dbg import B
from decimal import Decimal as dec
from orm import text, timespan, datespan
import orm
import party
import budget
import apriori

class employeements(party.role_roles):          pass
class positions(orm.entities):                  pass
class positiontypes(apriori.types):             pass
class positionrates(orm.entities):              pass
class fulfillment_positions(orm.associations):  pass
class responsibilities(orm.entities):           pass
class responsibilitytypes(apriori.types):       pass
class validresponsibilities(apriori.types):     pass
class positionstatusus(party.statuses):         pass
class position_positions(orm.associations):     pass
class periodtypes(apriori.types):               pass
class steps(orm.entities):                      pass
class grades(orm.entities):                     pass
class histories(orm.entities):                  pass
class benefits(orm.entities):                   pass
class benefittypes(apriori.types):              pass

class employeement(party.role_role):
    """ Maintains employment information. ``employeement`` is a
    subentity of ``party.role_role`` and represents a relationship
    between the party roles of employees (``party.employee``) and an
    internal organization (``party.internal``). Note that if the
    enterprise is interested in tracking employees of external
    organizations as well, then this entity can be between
    ``party.employee`` and ``party.employeer``.
    """
    
    # A collection a payment histories for this employment. These
    # histories record the pay the employment provided to the
    # employeement for a given period (``periodtype``).
    histories = histories

    benefits = benefits

class position(orm.entity):
    """ A position is a job slot in an enterprise. In some enterprises,
    this may be referred to as an FTE or full-time equivalent.
    """

    # The datespan an organization expects the position to begin and
    # end. If the position is for an indefinate period, the ``end``
    # would be None.
    estimated = datespan(prefix='estimated')

    # The actual datespan the position slot is filled, as opposed to the
    # `estimated` datespan.
    filled = datespan

    # True if the person filling the position is sallaried, False if he
    # or she is hourly.
    salary = bool

    # True if the position is exempt under the Fair Labor Standards Act
    # (FLSA).
    exempt = bool

    fulltime = bool

    temp = bool

    # The budget item provides a possible means of athorizing a job
    # slot. One budget item may approve or fund one or more positions.
    # If a position is tied to a budget, then the position is considered
    # "authorized" when the ``budget.status`` for the budget
    # (``budget.budget``) that affects the ``budget.item`` has been
    # approved.
    item = budget.item

    responsibilities = responsibilities

class positiontype(apriori.type):
    """ Provides information for further defining and categorizing a
    job.

    Note that this is modeled after the POSITION TYPE entity in "The
    Data Model Resource Book".
    """

    # NOTE The ``name`` attribute inherited from apriori.type serves as
    # the ``title`` described in the book. This attribute is the
    # standard job title such a "Business Analyst" or "Accounting
    # Clerk".

    # The collection of ``positions`` categorized by this
    # ``positiontype``.
    positions = positions

    # A brief description of the position type
    description = text

    positionrates = positionrates

    # The *benefit percent* records the percentage of benefits that an
    # enterprise willl pay for a particular type of position.
    percent = dec

    validresponsibilities = validresponsibilities

class responsibility(orm.entity):
    """ Represents a job responsibility.

    Note that this is modeled after the POSITION RESPONSIBILITY entity
    in "The Data Model Resource Book".
    """

    # A datespan that allows the enterprise to assign and track
    # historically changing responsibilities of jobs and positions. In
    # this way, very specific and detailed job descriptions can be
    # developed, while at the same time allowing for ongonig changes.
    span = datespan
    comment = text

class responsibilitytype(apriori.type):
    responsibilities = responsibilities
    validresponsibilities = validresponsibilities

class validresponsibility(orm.entity):
    """ Represents a valid ``responsibility`` for a given position type.

    Validation rules (brokenrules) could be developed to ensure that, if
    a certain ``responsibilitytype`` is assigned as a position
    ``responsibility``, it is first identified as a
    ``validresponsibility`` for the ``responsibility`` with which the
    ``position`` is associated.
    """
    # A datespan that allows the enterprise to assign and track
    # historically changing responsibilities of jobs and positions. In
    # this way, very specific and detailed job descriptions can be
    # developed, while at the same time allowing for ongonig changes.
    span = datespan
    comment = text

class positionrate(orm.entity):
    """ The ``positionrate`` may store a rate, overtime rate, cost, or
    other type of rate depending on the needs of the organization. The
    ``positiontype`` would indicate which rate is being specified. 

    Note that this is modeled after the POSITION TYPE RATE entity in
    "The Data Model Resource Book".
    """

    # NOTE The implicit composite `periodtype` allows an enterprise to
    # define various pay period types for which rates can be recorded.
    # Examples of periodtypes include "per year", "per week", "per
    # month" and so on.

    # A datespan is included so that a history of these standard positon
    # rates can be kept. 
    span = datespan

    # The rate for the position (the book calls this ``rate``)
    amount = dec

    # Provides the ability to record reference information such as
    # "highest pay rate", "lowest pay rate", "average pay rate", and
    # "standard pay rate". This would indicate such things as the upper
    # limit, average amount paid, lower limit, and the default, standard
    # amount of pay for a type of position.
    ratetype = party.ratetype

class fulfillment_position(orm.association):
    """ The `position_fulfilments` association links a position to a
    person.  When a postion is associatied with a person, the position
    is said to be "fulfilled', i.e., the person has been employed by the
    organization (i.e., company) to fulfill the job duties of the
    position.

    Since this is an `orm.association`, multiple person entities can be
    associated with a given position. Different person entities may be
    associated to the same position over time. This allows for the
    tracking persons who occupied a given position in an organization
    over various timespans.  The begin and end dates record the
    occupation's timespan.
    
    Additionally, multiple persons can be associated to the same
    `position` within the same timespan implying that the persons
    occupy the position as part-time or half-time employees.
    """

    person    =  party.person
    position  =  position

    # The timespan of the occumation
    span = datespan

# TODO This should inherit from apriori.status which currently doesn't
# exist.
class positionstatus(party.status):
    """ Identifies the current state of a ``position``. 
    
    When a position is first identified, it is in a state of "palnned
    for". When the enterprise decides to pursue fulfillment of the
    position, it may then change to a state of "active " or "open". If
    the enterprise then decides that it no longer needs that position,
    the status may be "inactive" or "closed". A "fulfilled" status would
    not be a value because this infromation can be derived from the
    fulfillment_position entity.

    Note that this is modeled after the POSITION STATUS TYPE entity in
    "The Data Model Resource Book".
    """
    entities = positionstatusus
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.orm.ensure(expects=('name',), **kwargs)

    name = str
    positions = positions

class position_position(orm.association):
    """ A reflexive association between two ``positions`` intended to
    illustrate the way two positions are related to each other in a
    reporting structure.

    Note that this is modeled after the POSITION REPORTING STRUCTURE
    entity in "The Data Model Resource Book".
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.orm.default('comment', None)

    # Allows for tracking organizational changes through time
    span = datespan

    comment = text

    # Used to help model flexible, matrix-type reporting structures. In
    # these cases, certain positions may report to more than one position
    # at the same time. This indicator allows the enterprise to indicate
    # which reporting relationship is the overriding one.
    isprimary = bool

    # The manager of the direct ``report``
    subject = position

    # The direct report
    object = position

class periodtype(apriori.type):
    """ Classifies ``positionrates``. Examples of ``periodtype``'s
    ``name`` attribute include "per year", "per week", "per month" and
    so on.

    Note that this is modeled after the PERIOD TYPE entity in "The Data
    Model Resource Book".
    """

    positionrates = positionrates

    histories = histories

    benefits = benefits

class step(orm.entity):
    """ 
    Note that this is modeled after the SALARY STEP entity in "The Data
    Model Resource Book".
    """
    ordinal = int
    amount = dec
    modified = datetime
    positionrates = positionrates

class grade(orm.entity):
    """ 
    Note that this is modeled after the PAY GRADE entity in "The Data
    Model Resource Book".
    """
    name = str
    comment = text
    steps = steps

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.orm.default('comment', None)

class history(orm.entity):
    """ An entries in an ``employments`` collection of ``histories``.
    Each entry represents the salary of the given ``employment`` for a given
    time period. 

    Note that this is modeled after the PAY HISTORY entity in "The Data
    Model Resource Book".
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.orm.default('comment', None)

    # The datespan when the salary was in effect
    span = datespan

    # The salary itself
    amount = dec

    comment = text

class benefit(orm.entity):
    """ 
    Note that this is modeled after the PARTY BENEFIT entity in "The
    Data Model Resource Book".
    """

    # Allows the tracking of the benefit through time.
    span = datespan

    # The actual cost of the benefit (the book calls this the ``cost``).
    amount = dec

    # The actual employeer paid percentage (the book calls this the
    # ``actual employer paid percentage``). With this datum, it is
    # possible to calculate the cost not only to the employee but to the
    # enterprise as well.
    percent = dec

    # Tracks the alowable time off such as vacation and sick leave (the
    # book calls this ``available time``).
    time = int

class benefittype(apriori.type):
    """ Lists the various types of benefit types. The ``name``
    attribute (inherited from ``apriori.type``) stores values such as
    "Health", "Vacation", "Sick leave", and "401k".
    """
    description = text

    # The standard employeer paid percentage. Can be used to calculate
    # costs related to all employees with a particular benefit. Note
    # that the book refers to this as ``employeer paid percentage``.
    percent = dec

    benefits = benefits

class paycheck(invoice.disbursement):
    """ A payment from an internal organization
    (``party.internalorganization``) to an employee
    (``party.employee``).

    Note that a paycheck is a subentity of ``invoice.disbursement``
    which itself is a subentity of ``invoice.payment`` since a paycheck
    is essentially type of payment.
    """

    # The employee role of a ``party.person`` which receives the
    # paycheck.
    employee = party.employee

    # The internal organization role which issues the paycheck
    internalorganization = party.internalorganization

class methodtype(apriori.type):
    """ The payment method type used to pay an employee. The inherited
    ``name`` attribute can be values such as "cash", "check" or
    "electronic".

    Note that this entity was originally called PAYMENT METHOD TYPE in
    "The Data Model Resource Book".
    """

class preference(orm.entity):
    """ The preferences an employee will have for their paycheck. This
    includes deduction amounts, payment method types, bank name, routing
    number and account number, etc.

    Each ``preferences`` may be defined for a certain ``periodtype``.
    For example, a particular standard deduction that is desired may be
    specified for pay ``periodtypes`` of "per year", "per month", or
    "weekely".

    Note that this entity was originally called PAYROLE PREFERENCE in
    "The Data Model Resource Book".
    """

    # A span allows the tracking of preferences over time.
    span = datespan

    # Percentage of pay the employee wants designated to a particular
    # payment method type (``methodtype``) or designated for certain
    # recurring deductions that are maintained through the relationship
    # with ``deductiontype``.
    percent = dec

    # The flat amount of pay the employee wants designated to a
    # particular payment method type (``methodtype``) or designated for
    # certain recurring deductions that are maintained through the
    # relationship with ``deductiontype``. Note the book calls this the
    # ``flat amount``.
    amount = dec

    # If the implict attribute ``methodtype.name`` equals "electronic",
    # the ``routing`` number, ``account`` number and ``bank`` name may be used
    # to successfully complete the transaction.

    # The bank's routing number
    routing = int

    # The account number
    account = int

    # The name of the bank
    bank = str

