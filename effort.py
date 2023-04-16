# vim: set et ts=4 sw=4 fdm=marker

# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2022

""" This module contains ``orm.entity`` objects related the tracking of
work effort data.

These entity objects are based on the "Work Effort" chapter of "The Data
Model Resource Book".

Examples:
    See test.py for examples. 

"""

"The best way to predict the future is to invent it." 
# Alan Kay

from datetime import datetime, date
from dbg import B
from decimal import Decimal as dec
from orm import text, timespan, datespan
import apriori
import asset
import entities
import order
import orm
import party
import primative
import product
import shipment

class  requirements(apriori.requirements):                       pass
class  requirementtypes(order.requirementtypes):                 pass
class  efforts(orm.entities):                                    pass
class  programs(efforts):                                        pass
class  projects(efforts):                                        pass
class  phases(efforts):                                          pass
class  tasks(efforts):                                           pass
class  jobs(efforts):                                            pass
class  activities(efforts):                                      pass
class  productionruns(efforts):                                  pass
class  maintenences(productionruns):                             pass
class  workflows(productionruns):                                pass
class  researches(productionruns):                               pass
class  deliverables(orm.entities):                               pass
class  deliverabletypes(apriori.types):                          pass
class  roles(party.roles):                                       pass
class  roletypes(party.roletypes):                               pass
class  items(order.items):                                       pass
class  item_requirements(orm.associations):                      pass
class  effort_items(orm.associations):                           pass
class  types(apriori.types):                                     pass
class  effortpurposetypes(apriori.types):                        pass
class  effort_requirements(orm.associations):                    pass
class  effort_efforts(orm.associations):                         pass
class  effort_effort_dependencies(effort_efforts):               pass
class  effort_effort_precedencies(effort_effort_dependencies):   pass
class  effort_effort_concurrencies(effort_effort_dependencies):  pass
class  effort_parties(orm.associations):                         pass
class  effort_partytypes(party.roletypes):                       pass
class  statuses(orm.entities):                                   pass
class  statustypes(apriori.types):                               pass
class  times(orm.entities):                                      pass
class  timesheets(orm.entities):                                 pass
class  timesheetroles(orm.entities):                             pass
class  timesheetroletypes(apriori.types):                        pass
class  effort_inventoryitems(orm.associations):                  pass
class  asset_efforts(orm.associations):                          pass
class  asset_effortstatuses(orm.entities):                       pass
class  skillstandards(orm.entities):                             pass
class  goodstandards(orm.entities):                              pass
class  assetstandards(orm.entities):                             pass
class  type_types(orm.associations):                             pass
class  breakdowns(type_types):                                   pass
class  dependencies(type_types):                                 pass
class  deliverable_efforts(orm.associations):                    pass
class  effort_product_items(orm.associations):                   pass
class  backlogs(orm.entities):                                   pass
class  stories(requirements):                                    pass

class backlog_stories(orm.associations):
    """ A collection of `backlog_story` associations.

    Note that this is part of the Agile object model extention to the
    original UDM.
    """
    def _rerank(self):
        """ Ensure that the rank values of each entry in the
        collection are sequential. Used to restore the order of the
        elements after a removal. 
        """
        for i, bs in self.sorted('rank').enumerate():
            bs.rank = i

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
    Data Model Resource Book". The REQUIREMENT entity from the book is
    located in apriori.py since it is involed in other things like order
    entry (see order.py).
    """

    # TODO There is an exclusive arc across the ``deliverable``,
    # ``asset`` and ``product`` attributes because a single
    # ``requirement`` can be relate to one of these but not to all
    # three. There should be a validation rule that prevents this.

    # An optional reference to an asset. When the ``requirementtype`` is
    # "maintenance" or "repair" for example, then there is a definite
    # need to know what piece of equipment needs to be worked on.
    asset = shipment.asset

    # A product (good or service) that the work ``requirment`` may be
    # for.
    product = product.product

    # NOTE An implicit ``deliverable`` attribute is made available as a
    # result of the one-to-many relationship that ``deliverable`` has to
    # ``requirement``.
    roles = roles

    ''' Accessability '''
    @property
    def creatability(self):
        # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        # SECURITY This should not be deployed to a production
        # environment.
        # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        # TODO Implement
        # TODO Add tests
        # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        return orm.violations.empty

    @property
    def retrievability(self):
        # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        # SECURITY This should not be deployed to a production
        # environment.
        # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        # TODO Implement
        # TODO Add tests
        # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        return orm.violations.empty

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
    ``activity``, and ``task``.  The ``type`` entity is used to
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

    # A work effort my result the repair of a fixed asset.
    asset = asset.asset

class program(effort): 
    pass

class project(effort): 
    pass

class phase(effort): 
    pass

class task(effort): 
    pass

class activity(effort): 
    pass

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
    pass

class deliverable(orm.entity):
    """ For ``requirements`` that have a type of "internal project", the
    ``requirement`` can have zero or more ``deliverables``. This would
    include such things as a management report, analysis document or the
    creation of a particular business method or tool. The
    ``deliverabletype`` attribute would store the type.

    A work effort may result in the production of one or more
    ``deliverables``. When this happens, the ``effort`` is linked to the
    ``deliverable_effort`` associtation..
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.orm.isnew:
            self.description = None
    name = str
    description = text

    # A collection of ``requirements`` that have this ``deliverable`` as
    # its deliverable.
    requirements = requirements

class deliverabletype(apriori.type):
    """ Categorizes ``deliverables`` by their type. Possible types
    include "management report", "project plan", "presentation", "market
    analysis".
    """

    deliverables = deliverables

class deliverable_effort(orm.association):
    """ An association between a work ``effort`` and a ``deliverable``.
    The association will typically imply that the deliverable was
    produced by the work ``effort``.

    Note that this entity was originally called WORK EFFORT DELIVERABLE
    PRODUCED in "The Data Model Resource Book".
    """
    deliverables = deliverable
    effort = effort

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

class effort_product_item(orm.association):
    """ Associates an ``effort`` with an ``product.item``. When
    ``efforts`` are linked to ``product.items`` via this class, it
    implies that the ``product.item`` was produced as a result of the
    work ``effort``.

    Note that this entity was originally called WORK EFFORT INVENTORY
    PRODUCED in "The Data Model Resource Book".
    """
    # The work ``effort`` side of the association.
    effort = effort
    
    # The inventory item (``product.item``) side of the association. The
    # item is said to be a product of the associated work ``effort``.
    item = item

class type(apriori.type):
    """ Catagorizes the ``effort``.

    Note that this entity was originally called WORK EFFORT TYPE in "The
    Data Model Resource Book".
    """

    # The standard number of work hours for this effort type. This is an
    # estimate of how many hours it would normally take to complete this
    # ``effort``.
    hours = dec

    # A collection of work ``efforts` that match this type.
    efforts = efforts

    # A collection of skill standard entities that this work effort
    # ``type`` requires.
    skillstandards = skillstandards

    # A collection of good (as in ``product.good``) standard entities
    # that this work effort ``type`` requires.
    goodstandards = goodstandards

    # A collection of asset (as in ``asset.asset``) standard entities
    # that this work effort ``type`` requires.
    assetstandards = assetstandards

class effortpurposetype(apriori.type):
    """ A work ``effort`` tracks the work to fix or produce something
    for manufacturing and involves the allocation of resources: people
    (labor), parts (inventory), and fixed assets (eqipment). Therefore,
    each work ``effort`` may be for the purpose of a work
    ``effortpurposetype`` including ``maintenance``, ``production run``,
    ``work flow``, and ``research``. 

    Note that this entity was originally called WORK EFFORT PURPOSE TYPE
    in "The Data Model Resource Book".
    """

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

class effort_effort_precedency(effort_effort_dependency):
    """ A subassociation of ``effort_effort``, this entity declares that
    the``object`` effort is dependent on the ``subject`` effort.

    Note that this entity was originally called WORK EFFORT PRECEDENCY
    in "The Data Model Resource Book".
    """

class effort_effort_concurrency(effort_effort_dependency):
    """ A subassociation of ``effort_effort``, this entity declares that
    the``subject`` effort must be executed in parallel with the
    ``object`` effort.

    Note that this entity was originally called WORK EFFORT CONCURRENCY
    in "The Data Model Resource Book".
    """

class effort_party(orm.association):
    """ This association between ``effort`` and ``party`` entities
    provide a means by which people, or groups of people, can be
    assigned or allocated to a work ``efforts``. With this, it is
    possible to assign parties to work efforts in various roles as well
    as at various levels of the work effort.

    When scheduling an assignment of a party to an effort, managers need
    to know the qualifications of prospective parties. This is handled
    using the ``party.skills`` and ``party.skilltypes`` entities.
    ``party.skills`` contains a list of skill types, years of
    experience, and a skill rating.

    If desired, an enterprise could put in place business rules that
    require parties to be assigned at the top level of the effort -- for
    example, the overall project -- in order to be assigned to lower
    level responibilities. For this reason, a scheduled start date and
    scheduled completion date (``span.begin`` and ``span.end``) are
    included in order to schedule parties or record what actually
    occurred in terms of their assignment.

    Note that this entity was originally called WORK EFFORT PARTY
    ASSIGNMENT in "The Data Model Resource Book".
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.orm.isnew:
            self.comment = None

    # The effort and party being associated
    effort = effort
    party = party

    # The span of time through which the party's assignment to the
    # effort is valid
    span = datespan

    # A note on the party's association with the effort
    comment = text

    # The facilty that the work effort is performed at. For ``efforts``
    # that have no location recorded for them, it is assumed that they
    # occur at the facility associated with the parent ``effort`` or that
    # the location is immaterial.
    #
    # (The book offers the idea of relating effort_party to an
    # ``party.contactmechanism`` as an alternative to
    # ``party.facility`` where only the postal address or email address
    # is known for the party. However, this attribute is not currently
    # implemented.)
    facility = party.facility

    # The collection of work effort assignment ``rates``
    rates = party.rates
    
class effort_partytype(party.roletype):
    """ Describes the role that the party is playing with the effort.

    Note that this entity was originally called WORK EFFORT ROLE TYPE in
    "The Data Model Resource Book".
    """

    effort_parties = effort_parties

class status(orm.entity):
    """ Maintains the status of a work ``effort``. Also maintains the
    status of a story within a `backlog` (see backlog_story`). Examples
    include, "In progress", "Started", and "Pending".

    The status of the work ``effort`` may have an effect on the
    ``requrimentstatus``; however, they may also be independent of each
    other. For instance, a status of "completed" on the work efforts
    required to implement a `requirement` my lead to the `requirement`
    having a status of "fulfilled". They, however, may have different
    unrelated statuses, such as the `requirement`  have a status of
    "approved" and the work `effort` having a status of "in progress".

    Note that this entity was originally called WORK EFFORT STATUS in
    "The Data Model Resource Book".
    """
    begin = datetime

class statustype(apriori.type):
    """ Describes a ``status`` entity.
    """

    # The collection of status entities that this entity describes.
    statuses = statuses

class time(orm.entity):
    """ A ``time`` entry holds information about how much time was spent
    during a given period on various work ``efforts``.  This data is
    used for payroll as well as taks tracking, cost determination, and
    prehaps client billing.  

    Each ``time`` entry may be part of a ``timesheet`` that may record
    many time entries. Each ``time`` entry may be for a particular
    ``worker``, ``employee`` or ``contractor. Each ``timesheet`` may
    have several other ``parties`.
    
    Note that this is modeled after the TIME ENTRY entity in "The Data
    Model Resource Book".
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.orm.isnew:
            self.comment = None

    # The time frame that the effort was worked on
    span = timespan

    # The number of hours the effort was worked on. NOTE If other units
    # of meesures are need for time entries aside from hours, such as
    # the number of days, then we can add a ``quantity`` attribute with
    # a relationship to product.measure (unit of measure).
    hours = dec

    comment = text

class timesheet(orm.entity):
    """ A ``timesheet`` is a collection of ``time`` entries belonging to
    a ``party.worker`` role (which itself belongs to a party). The
    ``worker`` role may **submit** many timesheets over time, whicha are
    each **composed of** ``time`` entries for a particular period of
    time. Each ``time`` entry is **within** a ``timesheet`` and als tied
    back to a work ``effort``, which determines the effort to which the
    time is charged.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.orm.isnew:
            self.comment = None

    # The time frame of the time sheet
    span = datespan

    comment = text

    # The ``worker`` role to which this timesheet belongs - typically a
    # ``party.employee`` or a ``party.contractor``.
    worker = party.worker

    # The collection of ``time`` entries for this timesheet
    times = times

class timesheetrole(orm.entity):
    """ A ``timesheet`` may have several other ``parties`` in various
    ``timesheetroles`` categorized by ``timesheetroletype``.
    """

class timesheetroletype(apriori.type):
    """ Categorizes ``timesheeroles``. Examples include "approver",
    "manager", and "enterer".
    """

    # A collection of timesheetroles that match this type.
    timesheetroles = timesheetroles

class effort_inventoryitem(orm.association):
    """ An association between effort and an inventory item
    (``product.item``). 

    In order to complete certain work efforts, raw materials or other
    items may be required. This class tracks the actual use of inventory
    during the execution of a work effort.

    Note that this is based on the WORK EFFORT INVENTORY ASSIGNMENT
    entity in "The Data Model Resource Book".
    """
    
    # The ``effort`` side of the association
    effort = effort

    # The inventory item (``product.item``) side of the association
    item = product.item

    # The number of inventory items used for the work effort
    quantity = dec

class asset_effort(orm.association):
    """ Indicates which fixed ``asset`` (asset.asset) is being used for
    a work effort.

    Note that this is based on the WORK EFFORT FLXED ASSET ASSIGNMENT
    entity in "The Data Model Resource Book".
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.orm.isnew:
            self.comment = None


    # The start date and end date for the assignment. These will be very
    # important for task scheduling purposes.
    span = datespan

    # The allocated ``cost`` attribute provides a record of how much
    # cost was recorded to that work effort for the usage of that fixed
    # ``asset``. This information would be important to capture the
    # costs incurred during any work effort for usage of a fixed
    # ``asset``.
    cost = dec
    comment = text

    asset = asset.asset
    effort = effort

class asset_effortstatus(orm.entity):
    """ This class represents the status that an asset-to-effort
    relationship has. This will indicate such things as whether the
    assignment is "requested" or "assigned".

    Note that this is based on the WORK EFFORT ASSET ASSIGNMENT STATUS
    TYPE entity in "The Data Model Resource Book".
    """
    entities = asset_effortstatuses
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.orm.ensure(expects=('name',), **kwargs)

    name = str

    asset_efforts = asset_efforts
    
""" 
***
Standards classes
***

The ``effort.type`` class has a one-to-many relationship with each of
the standards classes: skillstandard, goodstandard and assetstandard.

The standards classes store information that can be used for scheduling
resources and estimating time and costs for each work effort.
Additionally, they can be used to compare actual skills, goods and fied
asset usage agains the standards.  Each of these standards entities has
attributes that define expeted needs for the type of work effort. 
"""
class skillstandard(orm.entity):
    # The associated ``party.skill``
    skill = party.skill

    # The **estimate number** of people. This records how many people of
    # this skill type are typically needod for the given work effort.
    people = dec

    # The **estimated duration** records how long the skill is needed
    # for the work ``effort.type``.
    duration = dec

    # The **estimated cost** is an estimation of how much this type of
    # skill will cost for the associated work ``effort.type``.
    cost = dec

class goodstandard(orm.entity):
    """ Relates a work effort '`types`` to the goods (``product.goods``)
    that are typically needed for that work effort. 
    
    Attribute to record estimates for the quantity and cost of the good
    can be used for ensuring that enough of those goods exist in
    inventory to execute a particular work effort.

    Note that the relationship is to ``good`` not inventory item
    (``product.item``). Because this informatios is for planning, it is
    necessary to know only the type of good needed. There is no need to
    locate an actualy inventory item in stock. If, in examining this
    information, it is determined that for a planned work ``effort``,
    the work effort `type`` will require more of a ``product.good`` than
    is currently in inventory then the enterprise will know that it
    needs to reorder that good in order to complete the planned effort.

    Another point to note is that not all work effort ``types`` will have
    inventory requirements. For example, a work effort type of "prepare
    project plan", which is a work effor associated with providing a
    service as opposed to creating products, would not have any
    inventory requirement.
    """
    # The associated ``product.good``
    good = product.good

    # The **estimated quantity** maintains how many of each good is
    # typically needed.
    quantity = dec

    # The **estimated cost** attribute maintains the estimated cost that
    # is expected for the type of work effort.
    cost = dec

class assetstandard(orm.entity):
    # The associated fixed asset
    asset = asset.type

    # The **estimated quantity** attribute determines how many of the
    # fixed assets are needed for the work effort ``type``.
    quantity = dec

    # The **estimated duration** attribute maintains how long the fixed
    # asset is typically needed for the work effort type.
    duration = dec

    # The **estimate cost** maintains the anticipated cost for the
    # given type of work effort.
    cost = dec

class type_type(orm.association):
    """ Associates a work effort ``type`` with another. The associated
    ``type`` represents the standard type ``breakdown`` and ``type``
    ``dependencies``. These represent the standard types of efforts that
    normally make up a larger type of work effort as well as the
    standard dependencies that occur.
    """
    subject = type
    object = type

class breakdown(type_type):
    """
    """

class dependency(type_type):
    """
    """

class backlog(orm.entity):
    """ Represents a agile backlog.

    A backlog is a fundamental component of the Agile development
    methodology. It is used to manage the work that needs to be done in
    a `project`, and it serves as the central repository for all the
    `stories` that need to be completed. In Agile, the backlog is
    constantly updated and prioritized based on the needs of the project
    and the feedback from stakeholders.

    The backlog is a living document that is updated regularly
    throughout the project's lifecycle. It is used to plan and execute
    sprints, which are short, focused periods of work during which a
    team completes a set of tasks from the backlog. By working through
    the backlog in a structured and prioritized manner, Agile teams can
    deliver high-quality software and meet the needs of their
    stakeholders.

    A backlog can have zero or more `stories` within it. This is
    achieved through the `backlog_story` association. Use the `insert`
    and `remove` methods to correctly add and remove `stories` to and
    from a `backlog`.

    Note that this is part of the Agile object model extention to the
    original UDM.
    """
    name         =  str
    description  =  text
    span         =  datespan
    goal         =  str

    def insert(self, rank, st=None):
        """ Puts the story `st` into this `backlog`.

        Note that this operation is transient. You will need to call the
        `save()` method on this `backlog` in order to persist the changes
        to the database.

        The `rank` parameter contains the rank the story should have in
        the backlog. For example, the following creates a backlog and
        a story and inserts the story into the backlog at index 3:
            
            bl = backlog()
            st = story()
            bl.insert(3, st)

        The method can be called with just the `st` argument and no
        `rank` argument. In this case, `rank` defaults to 0.

            # Insert at position 0
            bl.insert(st)

            #  Does the same as above.
            bl.insert(0, st)

        It's possible to change the rank of story within a backlog by
        reinserting. 
            
            # Insert at position 0
            bl.insert(0, st)

            # Move the story to position 10 by reinsterting
            bln.insert(10, st)

        Note that `insert` should not be used to move a story from one
        backlog to another. Use the `move` method for that.

        :param: rank int: The position in the backlog to put the story.
        If the story already exists in the backlog, this parameter can
        change the position.

        :param: st story: The story to add or move.
        """

        # Implement the single-argument behavior
        if not st:
            st = rank
            # Recurse using a default rank of 0
            return self.insert(rank=0, st=st)

        # Get this backlogs collection of `backlog_stories 
        bss = self.backlog_stories

        # Sort by rank
        bss.sort('rank')

        # If the story exists in the collection, we are doing a
        # replacement operation:
        replacing = st.id in bss.pluck('story.id')

        # If we are not replacing, we are adding the story to the
        # collection.
        adding = not replacing

        # Iterate over the backlog_stories collection.
        for bs in bss:
            if replacing:
                if bs.story.id == st.id:
                    for bs1 in bss:
                        if rank == bs1.rank:

                            # Replace rank values
                            bs1.rank, bs.rank = bs.rank, rank
                            break
            elif adding:
                # Increment all rank greater than or equal to rank
                if bs.rank >= rank:
                    bs.rank += 1

        # Add to the collection at `rank`
        if adding:
            bss += backlog_story(rank=rank, story=st)

    def remove(self, st):
        """ Remove the story from this backlog. Returns a collection of
        stories that were successfully removed.

        :param: st story: The story to remove from this backlog.
        """
        rms = stories()

        # Get backlog_stories and sort by rank
        bss = self.backlog_stories
        bss.sort('rank')

        # For each backlog_story
        for bs in bss:
            # If we find a match
            if st.id == bs.story.id:
                # Remove it
                bss.remove(bs)
                rms += bs.story
                break

        bss._rerank()

        return rms

    @property
    def stories(self):
        """ Returns a collection of stories within this backlog.

        Note that adding or removing this collection will not have an
        impact on this backlog as an ORM entity model. To make changes
        that can be persisted, you must use the `backlog_stories`
        association collection. This property is intended for
        convenient, read-only access.
        """
        sts = stories()

        for bss in self.backlog_stories:
            sts += bss.story
        return sts

    ''' Accessability '''
    @property
    def creatability(self):
        # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        # SECURITY This should not be deployed to a production
        # environment.
        # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        # TODO Implement
        # TODO Add tests
        # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        return orm.violations.empty

    @property
    def retrievability(self):
        # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        # SECURITY This should not be deployed to a production
        # environment.
        # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣

        # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        # TODO Implement
        # TODO Add tests
        # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        return orm.violations.empty

    @property
    def updatability(self):
        # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        # SECURITY This should not be deployed to a production
        # environment.
        # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣

        # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        # TODO Implement
        # TODO Add tests
        # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        return orm.violations.empty

class story(requirement):
    """ A class representing a user story in an Agile development
    environment. 

    A story can be placed in a product or sprint `backlog` (see the
    `backlog` class on how this is done). `stories` are related to
    `backlogs` through the `backlog_story` association. Note, however,
    there is a one-to-many relationship between `backlogs` and
    `stories`. The associations entity is necessary for ranking the
    stories within the `backlog` through the association's `rank`
    attribute.

    Stories in Agile
    ================
    In Agile software development, a "story" refers to a small, discrete
    unit of work that represents a specific feature or functionality to
    be developed. Stories are a fundamental part of Agile methodology,
    and they help teams to plan, prioritize, and track their work in a
    structured way.

    Typically, a story is written in a specific format called a user
    story, which is a concise description of a feature or requirement
    from the perspective of the end user. A user story typically follows
    the format of "As a [type of user], I want [a feature] so that [a
    benefit or outcome]". The user story format is designed to capture
    the essential details of a feature or requirement in a way that is
    easy to understand and prioritize.

    Stories are usually written by product owners or stakeholders, and
    they are added to a `backlog` of work to be completed by the
    development team. The `backlog` is a prioritized list of stories that
    the team will work on, with the most important stories at the top of
    the list. When a story is selected for development, it is broken
    down into smaller tasks or sub-tasks that can be completed in a
    single sprint, which is a short period of time during which the team
    works to complete a set of tasks or stories.

    As the team works on each story, they update the story's status in
    the project management tool, which helps to track progress and
    identify any issues or roadblocks that need to be addressed. Once a
    story is completed, it is tested and reviewed before being marked as
    "done" and moved to the next stage of development. The process of
    working through the backlog of stories and completing them in
    sprints is repeated until all of the required features and
    functionality have been developed and the product is ready for
    release.
    """

    # A short title for the story
    name = str

    # The number of points for the story.
    points = dec

    # TODO Add a priorities collection and an attribute that returns
    # the. This should be like a statuses collection in that it can
    # reference a priority type entity.
    # latest priorty assigned by a user.
    # priorities = priorities
    # @orm.attr(int)
    # def priority(self):
    #    # return latest from self.priorities

    @property
    def backlog(self):
        """ Returns the `backlog` object associated with this
        `story`.
        """
        for bss in self.backlog_stories:
            if bl := bss.backlog:
                return bl

        return None

    def move(self, from_, to):
        """ Move this `story` object from the `from_` backlog, to the
        `to` backlog.

        Note that this operation is transient. You will need to call the
        `save()` method on this `story` in order to persist the changes
        to the database.
        """
        for bss in from_.backlog_stories:
            if bss.story.id == self.id:
                from_.backlog_stories.remove(bss)

        to.insert(self)

class backlog_story(orm.association):
    """ Assoicates a `backlog` with a `story`.
    """
    # The story
    story = story

    # Th backlog
    backlog = backlog

    # The ranking of the `story` within the `backlog`. A rank of 0
    # ranks the story as the lowest in the backlog, a rank of 1
    # ranks the story one higher than the lowest in the backlog, and so
    # on. 
    rank = int

    # A collection of statuses that a story goes through within a
    # backlog. For example, in a sprint backlog, a story would go
    # through statuses such as TODO, IN-PROGRESS, QA, TESTING, STAGING
    # and finally DONE.
    statuses = statuses

    ''' Accessability '''
    @property
    def creatability(self):
        # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        # SECURITY This should not be deployed to a production
        # environment.
        # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        # TODO Implement
        # TODO Add tests
        # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        return orm.violations.empty

    @property
    def retrievability(self):
        # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        # SECURITY This should not be deployed to a production
        # environment.
        # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣

        # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        # TODO Implement
        # TODO Add tests
        # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        return orm.violations.empty

    @property
    def updatability(self):
        # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        # SECURITY This should not be deployed to a production
        # environment.
        # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣

        # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        # TODO Implement
        # TODO Add tests
        # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        return orm.violations.empty

