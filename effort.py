# vim: set et ts=4 sw=4 fdm=marker

# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2020

""" This module contains ``orm.entity`` objects related the tracking of
work effort data.

These entity objects are based on the "Work Effort" chapter of "The Data
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
import ship

class requirements(order.requirements): pass
class requirementtypes(order.requirementtypes): pass
class efforts(orm.entities): pass
class deliverables(orm.entities): pass
class deliverabletypes(orm.entities): pass
class roles(party.roles): pass
class roletypes(party.roletypes): pass

class requirement(order.requirement):
    """ Repersents the *need* to perform some type of work. This could
    be a requirment stemming from a decision to manufacture inventory
    items, deliver services, conduct a procedure, or repair an asset of
    the enterprise such as a piece of equpment or a piece of software.

    A work ``effort` is the *fulfillment* of the work ``requirement``.

    A work ``requirement`` is created when there is a need to perform
    some type of work by the enterprise, either for the enterprise or
    for an external orgariztanio, most likely a customer. Examples of
    work ``requirements`` include the following:

    - The need to manufacture a particular item because market research
      indicates an increased demand for that item beyond previous
      projections

    - The need for a piece of equipment within the enterprise to be
      repaired

    - The need for an internal project such as an analysis of existing
      operations, development of a plan, or creation of a new product or
      service

    Note that this entity was originally called WORK REQUIREMENT in "The
    Data Model Resource Book".
    """

    # TODO There is an exclusive arc across the ``deliverable``,
    # ``asset`` and ``product`` attributes because a single
    # ``requirement`` can be relate to one of these but not to all
    # three. There should be a validation rule that prevents this.

    # An optional reference to an asset. When the ``requirementtype`` is
    # "maintenence" or "repair" for example, then there is a definite
    # need to know what piece of equipment needs to be worked on.
    asset = ship.asset

    # A product (good or service) that the work ``requirment`` may be
    # for.
    product = product.product

    # NOTE An implicit ``deliverable`` attribute is made available as a
    # result of the one-to-many relationship that ``deliverable`` has to
    # ``requirement``.

    roles = roles

class requirementtype(order.requirementtype):
    """ Defines the possible categories for the requirements.

    Possible requirement types include "project", "maintenance" and
    "production run".
    """

    # A collection of ``requirements`` that correspond to this type
    requirements = requirements

class effort(orm.entity):
    """ The *fulfillment* of a work ``requirement``. This includes
    setting up and planning for the actual work that will be performed,
    as well as recording the status and information related to the
    efforts and tasks that are taking place.
    """

class deliverable(orm.entity):
    """ For ``requirements`` that have a type of "internal project", the
    ``requirement`` can have zero or more ``deliverables``. This would
    include such things as a management report, analysis document or the
    creation of a particular business method or tool. The
    ``deliverabletype`` attribute would store the type.
    """

    # A collection of ``requirements`` that have this ``deliverable`` as
    # its deliverable.
    requirements = requirements

class deliverabletype(orm.entity):
    """ Categorizes ``deliverables`` by their type. Possible types
    include "management report", "project plan", "presentation", "market
    analysis".
    """

    # TODO So many entity objects follow this pattern: An entity called
    # myentity is created, followed by myentitytype that categorizes
    # myentity. The constructor for myentitytype uses the orm.ensure
    # method to ensure a record exists for the type identifiable by
    # name.  We should have a generic ``type`` class that does this and
    # from which all these other type classes can derive.
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.orm.ensure(expects=('name',), **kwargs)

    deliverables = deliverables

class role(party.role):
    """ Contains the intersection of ``party.party``, ``requirement``
    and ``roletype``.
    """

    # A datespan to indicate the duration of the role.
    span = datespan

class roletype(party.roletype):
    """ Stores all the valid roles defined by an enterprise that could
    be related to a ``requirement``. Possible values for ``name`` would
    include "Created for', "Responsible for", "Authorized by". These
    phrases would be in reference to ``role.party``, i.e., "Created
    for ``role.party``".

    Note that this is modeled after the REQUIREMENT ROLE TYPE (also
    refered to as WORK REQUIREMENT ROLE TYPE) entity in "The Data Model
    Resource Book".
    """

    # The collection of ``roles`` matching this ``roletype``
    roles = roles
