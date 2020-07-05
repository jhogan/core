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
import apriori

class requirements(apriori.requirements):                      pass
class requirementtypes(order.requirementtypes):                pass
class efforts(orm.entities):                                   pass
class programs(efforts):                                       pass
class projects(efforts):                                       pass
class phases(efforts):                                         pass
class tasks(efforts):                                          pass
class jobs(efforts):                                           pass
class activities(efforts):                                     pass
class productionruns(efforts):                                 pass
class maintenences(productionruns):                            pass
class workflows(productionruns):                               pass
class researches(productionruns):                              pass
class deliverables(orm.entities):                              pass
class deliverabletypes(orm.entities):                          pass
class roles(party.roles):                                      pass
class roletypes(party.roletypes):                              pass
class items(order.items):                                      pass
class item_requirements(orm.associations):                     pass
class effort_items(orm.associations):                          pass
class efforttypes(orm.entities):                               pass
class effortpurposetypes(orm.entities):                        pass
class effort_requirements(orm.associations):                   pass
class effort_efforts(orm.associations):                        pass
class effort_effort_dependencies(effort_efforts):              pass
class effort_effort_precedencies(effort_effort_dependencies):  pass
class effort_effort_concurrency(effort_effort_dependencies):   pass
class effort_parties(orm.associations):                        pass
class effort_partytypes(orm.entities):                         pass
class statuses(orm.entities):                                  pass
class statustypes(orm.entities):                               pass

class requirement(apriori.requirement):
    """ Represents the *need* to perform some type of work. This could
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

    Work efforts may fulfill an internal commitment to do work, or they
    may fulfill an external requirement such as a sales order item
    (``order.salesitem``). The work effort may result from scenarios
    such as :
        
        - A work requirment.
        - A customer orders an item that needs to be manufactured.
        - A service that was sold now needs to be performed.
        - A customer places an order to repair or service an item that
          was previously sold to him or her.

    ``efforts`` are used to fulfill the requirments of either a work
    ``requirement`` or work order ``item`. 

    Work ``efforts` are subtyped according to its level of detail.
    Possible subtypes include ``program``, ``project``, ``phase``,
    ``activity``, and ``task``.  The ``efforttype`` entity is used to
    include more types if necessary. 

    Note that this entity was originally called WORK EFFORT in "The
    Data Model Resource Book".
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.terms = None
        self.description = None

    # The name for the overall work effort, such as a project name
    name = str

    # A detailed description of the effort
    description = text

    # To facility project tracing, the enterprise may want to list
    # scheduled start and end date, and estimated hourse for the effort
    scheduled = datespan(prefix='scheduled')

    # Funding or time limits may be imposed under certain circumstances
    # by various agencies, so ``effort``s includ **total dollars
    # allowed** and **total hours allowed**.
    dollarsallowed = dec
    hoursallowed   = dec

    # The actual start datetime, actual completion datetime, and actual
    # hoursestored to track efficiency.
    actual = timespan(prefix='actual')

    # The actual hours the work effort took.
    hours = dec

    # If there is a need for any special terms that anyone needs to know
    # about, those can be recorded as well.
    terms = text

    # A work effort may be associated with zero or one facility, i.e.,
    # the work may occure at aphysical structure such as a particular
    # building, room, or floor.. Since ``effort`` is a recursive entity,
    # if facility is None, the work effort is assumed to take place a
    # the closest parent that has a non-None ``facility`` attribute.
    facility = party.facility

    # Make ``efforts`` recursive. Work efforts can be associated with
    # other work efforts using the reflexive association
    # ``effort_effort`` and its subassociations..  However, the
    # recursive relationship created with the ``efforts`` attribute
    # belowe is reserved for redos. As the book puts it, "The
    # one-to-many recursion around WORK EFFORT provides for work efforts
    # to be redone by other work efforts and to capture this
    # relationshipt."
    efforts = efforts

    # The collection of statuses that this effort has been in 
    statuses = statuses

class program(effort): 
    pass

class project(effort): 
    pass

class phase(effort): 
    pass

class task(effort): 
    pass

class activity(effort): 
    entities = activities

class job(effort):
    pass

class productionrun(effort): 
    """ "A group of similar or related goods that is produced by using a
    particular group of manufacturing procedures, processes or
    conditions. The most desirable size of a production run required by
    a business will depend on the consumer demand for the good produced,
    as well as how much it costs to set up production and carry excess
    inventory."
        -- http://www.businessdictionary.com/definition/production-run.html

    Note that this entity was originally called PRODUCTION RUN in "The
    Data Model Resource Book".
    """
    # Maintains the expected quantity for the production run
    expected = dec

    # Records the actual production from the production run
    produced = dec

    rejected = dec

class maintenance(productionrun): 
    entities = maintenences

class workflow(productionrun): 
    pass

class research(productionrun): 
    entities = researches

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

class item(order.item):
    """ The work order ``item`` represents the commment to complete some
    work. Work order ``items`` usually result from work ``requirements``
    however, they can result from certain ``product.requirements`` such
    as for a product that needs to be manufactured. jj

    Note that this entity was originally called WORK ORDER ITEM in "The
    Data Model Resource Book".
    """

class item_requirement(orm.association):
    """ Associates an ``item`` with a ``requirement`` entity.
    
    Note that this entity was originally called ORDER REQUIREMENT
    COMMITMENT in "The Data Model Resource Book".
    """

    item = item
    requirement = requirement

class effort_item(orm.association):
    """ Associates an ``effort`` with an ``item``.

    Note that this entity was originally called WORK ORDER ITEM
    FULFILLMENT in "The Data Model Resource Book".
    """

    # The work ``effort`` side of the association.
    effort = effort
    
    # The work order ``item`` side of the association. The above work
    # ``effort`` is said to be the fulliment of the work ``item``
    item = item

class efforttype(orm.entity):
    """ Catagorizes the ``effort``.

    Note that this entity was originally called WORK EFFORT TYPE in "The
    Data Model Resource Book".
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.orm.ensure(expects=('name',), **kwargs)

    name = str

    # The standard number of work hours for this effort type. This is an
    # estimate of how many hours it would normally take to complete this
    # ``effort``.
    hours = dec

    # A collection of work ``efforts` that match this type.
    efforts = efforts

class effortpurposetype(orm.entity):
    """ A work ``effort`` tracks the work to fix or produce something
    for manufacturing and involves the allocation of resources: people
    (labor), parts (inventory), and fixed assets (eqipment). Therefore,
    each work ``effort`` may be for the purpose of a work
    ``effortpurposetype`` including ``maintenance``, ``production run``,
    ``work flow``, and ``research``. 

    Note that this entity was originally called WORK EFFORT PURPOSE TYPE
    in "The Data Model Resource Book".
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.orm.ensure(expects=('name',), **kwargs)

    name = str

    # A collection of work ``efforts` that match this type.
    efforts = efforts

class effort_requirement(orm.association):
    """ Associates an effort with a requirement.

    Note that this entity was originally called WORK REQUIREMENT
    FULFILLMENT in "The Data Model Resource Book".
    """
    effort = effort
    requirement = requirement

class effort_effort(orm.association):
    """ Associates an effort with another effort

    Note that this entity was originally called WORK EFFORT ASSOCIATION
    in "The Data Model Resource Book".
    """
    # The subjective side of the relationship
    subject = effort

    # The objective side of the relationship
    object = effort

class effort_effort_dependency(effort_effort):
    """ A subassociation of ``effort_effort``, this entity declares that
    the``object`` effort is dependent on or concurrent with another
    effort. See its subentity classes for more information.

    Note that this entity was originally called WORK EFFORT DEPENDENCY
    in "The Data Model Resource Book".
    """
    entities = effort_effort_dependencies

class effort_effort_precedency(effort_effort_dependency):
    """ A subassociation of ``effort_effort``, this entity declares that
    the``object`` effort is dependent on the ``subject`` effort.

    Note that this entity was originally called WORK EFFORT PRECEDENCY
    in "The Data Model Resource Book".
    """
    entities = effort_effort_precedencies

class effort_effort_concurrency(effort_effort_dependency):
    """ A subassociation of ``effort_effort``, this entity declares that
    the``subject`` effort must be executed in parallel with the
    ``object`` effort.

    Note that this entity was originally called WORK EFFORT CONCURRENCY
    in "The Data Model Resource Book".
    """
    entities = effort_effort_concurrency

class effort_party(orm.association):
    """ This association between ``effort`` and ``party`` entities
    provide a means by which people, or groups of people, can be
    assigned or allocated to a work ``efforts``. With this, it is
    possible to assign parties to work efforts in various roles as well
    as at various levels of the work effort.

    Note that this entity was originally called WORK EFFORT PARTY
    ASSIGNMENT in "The Data Model Resource Book".
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.orm.isnew:
            self.comment = None

    entities = effort_parties

    # The effort and party being associated
    effort = effort
    party = party

    # The span of time through which the party's assignment to the
    # effort is valid
    span = datespan

    # A note on the party's association with the effort
    comment = text

class effort_partytype(orm.entity):
    """ Describes the role that the party is playing with the effort.

    Note that this entity was originally called WORK EFFORT ROLE TYPE in
    "The Data Model Resource Book".
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.orm.ensure(expects=('name',), **kwargs)

    name = str

    effort_parties = effort_parties

class status(orm.entity):
    """ Maintains the status of a work ``effort``. Examples include, "In
    progress", "Started", and "Pending".

    The status of the work ``effort`` may have an effect on the
    ``requrimentstatus``; however, they may also be independent of each
    other. For instance, a status of "completed" on the work efforts
    required to implement a requirement ma lead to the requirement
    having a status of "fulfilled". They, however, may have different
    unrelated statuses, such as the requirement  have a status of
    "approved" and the work effort having a status of "in progress".

    Note that this entity was originally called WORK EFFORT STATUS in
    "The Data Model Resource Book".
    """
    entities = statuses

    begin = datetime

class statustype(orm.entity):
    """ Describes a ``status`` entity.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.orm.ensure(expects=('name',), **kwargs)

    name = str

    # The collection of status entities that this entity describes.
    statuses = statuses

