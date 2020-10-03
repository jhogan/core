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

class employeement(party.role_role):
    """ Maintains employment information. ``employeement`` is a
    subentity of ``party.role_role`` and represents a relationship
    between the party roles of employees (``party.employee``) and an
    internal organization (``party.internal``). Note that if the
    enterprise is interested in tracking employees of external
    organizations as well, then this entity can be between
    ``party.employee`` and ``party.employeer``.
    """

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
    span = datespan
    rate = dec

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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.orm.ensure(expects=('name',), **kwargs)

    name = str
    positions = positions
