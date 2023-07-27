# vim: set et ts=4 sw=4 fdm=marker

# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2022

""" This module contains ``orm.entity`` objects which caused referential
issue in their natural homes. 

For example, the ``requirement`` class should be in the order.py.
However, product.py wants a ``requirment`` class that subclasses
``order.requirement``; and this cannot be, because product.py can't
``import`` order.py because it would create a circular reference
(order.py ``import``s product.py). The ``apriori.py`` module imports no
GEM class and can therefore house classes that any and all GEM classes
may depend on.
"""

import orm
from orm import text, date, datetime
from decimal import Decimal as dec
from dbg import B
import primative

def model():
    """ Import all the entity module.

    Invoking this function is a requirement for any excecutable, such as
    test.py, bot.py, testmessage.py, or any process that relies on the
    General Entity Model (GEM). All GEM modules need to be loaded *ab
    initio* so introspection can be used to reflect on their data
    definitions (i.e., orm.entity.__subclasses__() needs to be able to
    return every GEM entity class). If modules are left out, the full
    entity model cannot be constructed since there will be missing
    parts. Issues may show up in unexpected places, such as foreign keys
    missing in CREATE TABLE statements.

    Any module that contains orm.entity classes, and that form the
    General Entity Model, should be imported here. Since entity modules
    are rarely added, this function will rarely be modified. However,
    whenever a GEM module is added, be sure to import here. 

    Note that to use the module in an executable, you will still need to
    import it there in order to get it in the executable's namespace.
    """
    import account
    import apriori
    import asset
    import bot
    import budget
    import ecommerce
    import effort
    import file
    import hr
    import invoice
    import message
    import order
    import party
    import product
    import shipment
    import third
    import carapacian_com

class requirements(orm.entities):  pass
class logs(orm.entities):          pass
class types(orm.entities):         pass
class logtypes(types):             pass

class requirement(orm.entity):
    """ A ``requirement`` is an organization's need for *anything*.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.orm.isnew:
            self.reason = None
            self.description = None

    # IMPLEMENTATION NOTE: The Ordering Product chapter of "The Data
    # Model Resource Book" presents a optional "Requirements" model for
    # requirements related to order ``items``. **This data model has not
    # been implemented here yet**. This single class has only been
    # implemented here to function as a superentity to
    # ``effort.requirement``.

    # Defines the need of the requirement. ``description`` allows for a
    # full explanation and comments for the requirment.
    description = text

    # Specifies when the requirement was first created (not to be
    # confused with ``createdat`` which is an implicit attribute
    # indicating the datetime the record was created)
    # 
    # Note the the data type in UDM was original `data`. However, to
    # support certain `requirements`, such as `effort.stories`, we need
    # more resolution in order to capture the time portion.
    created = datetime

    # The date by which the requirement item is needed.
    required = date

    # Identities thow much money is allocated for fulfilling the
    # requirement (originally called: *estimated budget*)
    budget = dec

    # Determines the number of items needed in the requirement and
    # allows the requirement to specify the several products or things
    # are need. For instance there may be a requirement to hire 3
    # programmers.
    quantity = dec

    # Explains why there is a need for the requirements
    reason = text

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


class type(orm.entity):
    """  An abstract entity to describe the type of another class. This
    class is used when a entity needs a many-to-one class that
    classifies the entity. For example, say there is an entity called
    party:
        
        class parties(orm.entities):
            ...

        class party(orm.entity):
            ...

    We can use a subtype of ``apriori.type`` to classify ``party``
    entities into types:
        
        class partytype(apriori.type):
            # A collection of parties. This declaration links
            # `partytype` to `party`.
            parties = parties

    The ``name`` attribute of type, along with the subtype itself, form
    a unique key to distinguish each ``type`` subentity.

    An import note about type entity objects is that they are
    self-ensuring. That means that, upon intantiation, they're saved to
    the database unless they already exist. See the example below:

        # Example of how to use the `partytype` mentioned above.

        part = party.party(name='My party of three')

        # NOTE Upon instantiation, party.type will ensure that a 'Dinner
        # party` entry exist in the database.
        #
        # Also note that the ``type``'s ''name'' attribute is used as
        # the key to the type.

        part.partytype = party.type(name='Dinner party')

        # Now we save party and its association with party.type. Note
        # that this will not save the ``partytype`` compostie entity
        # because that was already done during the instantiation above.
        part.save()

        # The party.type can be iterated over to get all the entities
        # classified by it. It only has one in the database at this
        # point, so we will assert that it has classified `part` as a
        # "Dinner party".
        assert part.id == party.type(name='Dinner party').first.id
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        try:
            expects = kwargs['expects']
        except KeyError:
            expects = ('name',)
        else:
            del kwargs['expects']

        self.orm.ensure(expects=expects, **kwargs)

    # The name of the type. This is used as a key that the contructor
    # will use when it ensure the record exists.
    name = str

    @property
    def creatability(self):
        # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        # SECURITY This should not be deployed to a production
        # environment.
        # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        return orm.violations.empty

    @property
    def retrievability(self):
        # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        # SECURITY This should not be deployed to a production
        # environment.
        # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        return orm.violations.empty

class log(orm.entity):
    """ The entity for log messages.
    """
    
    # TODO Surprisingly, the datetime field for this was left out. It
    # should probably be called `created`. We shouldn't rely on the
    # built in `createdat` or `updateat` fields, since those have
    # slightly different implications.

    # The log message itself
    message = text

    @property
    def creatability(self):
        # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        # SECURITY This should not be deployed to a production
        # environment.
        # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        return orm.violations.empty

    @property
    def retrievability(self):
        # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        # SECURITY This should not be deployed to a production
        # environment.
        # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        return orm.violations.empty

class logtype(type):
    logs = logs

    @property
    def creatability(self):
        # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        # SECURITY This should not be deployed to a production
        # environment.
        # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        return orm.violations.empty

    @property
    def retrievability(self):
        # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        # SECURITY This should not be deployed to a production
        # environment.
        # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        return orm.violations.empty

class statuses(orm.entities):                                
    """ XXX
    """
    def open(self, type):
        """ XXX
        """
        for st in self:
            # TODO We may want to make this optional
            if st.iscurrent:
                raise db.IntegrityError(
                    'There is already an open status'
                )

        if isinstance(type, str):
            B()
            type = statustype(name=type)

        self += status(
            statustype  =  type,
            begin       =  primative.datetime.utcnow(),
            end         =  None
        )

class status(orm.entity):
    """ Throughout the GEM, there are many statuses for many
    entity objects (e.g., orders status, shipment status, work effort
    status, and so on.). Each of these will be have their on subentity
    classes, e.g., ``party.role_role_status``.

    Note that this is modeled after the STATUS TYPE entity in "The Data
    Model Resource Book".
    """
    time = orm.timespan

class statustypes(types):
    """ XXX
    """

class statustype(type):
    """ XXX
    """
    statuses = statuses

