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
"""

from datetime import datetime, date
from dbg import B
from decimal import Decimal as dec
from orm import text, timespan, datespan
import orm
import party
import budget
import apriori

class employeements(party.role_roles):  pass
class positions(orm.entities):          pass
class positiontypes(apriori.types):                          pass
class positionrates(orm.entities):                           pass
class position_fulfillments(orm.associations):               pass
class responsibilities(orm.entities):                           pass
class responsibilitytypes(apriori.types):                           pass
class validresponsibilities(apriori.types):                           pass

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

    # The budget item provides a possible means of athorizing a job
    # slot.
    item = budget.item

    responsibilities = responsibilities

class positiontype(apriori.type):
    """ Provides information for further defining and categorizing a
    job.

    Note that this is modeled after the POSITION TYPE entity in "The
    Data Model Resource Book".
    """

    # The collection of ``positions`` categorized by this
    # ``positiontype``.
    positions = positions

    description = text

    positionrates = positionrates

class responsibility(orm.entity):
    span = datespan
    comment = text

class responsibilitytype(apriori.type):
    responsibilities = responsibilities

class validresponsibility(orm.entity):
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

class position_fulfillment(orm.association):
    """
    The `position_fulfilments` association links a position to a person.
    When a postion is associatied with a person, the position is said to
    be "fulfilled', i.e., the person has been employed by the
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


