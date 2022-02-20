# vim: set et ts=4 sw=4 fdm=marker

# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2022

""" This module contains ``orm.entity`` objects related the tracking of
asset data.

These entity objects are based some entities from the "Work Effort"
chapter of "The Data Model Resource Book" (though most of the entities
in that chapter are located in the effort.py module).

Examples:
    See test.py for examples. 
"""

from orm import text, timespan, datespan
from datetime import datetime, date
import orm

class assets(orm.entities):      pass
class types(orm.entities):       pass
class properties(orm.entities):  pass
class vehicles(orm.entities):    pass
class equipments(orm.entities):  pass
class others(orm.entities):      pass

class asset(orm.entity):
    """ A fixed asset.

    Note that this entity was originally called FIXED ASSET in "The Data
    Model Resource Book".
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.orm.isnew:
            self.description = None

    # Identifies the asset
    name = str

    # The date the asset was aquired, established when the asset was
    # acquired (important for deprication).
    acquired = date

    # The date the asset was serviced last (this may not be needed if
    # the this can be derived from maintenance records.
    serviced = date

    # The date the asset is scheduled to be serviced next.
    nextserviced = date

    # The production `capacity` maintains a value for the asset's
    # production capabilities.
    #
    # NOTE ``asset``s have a many-to-one relationship with
    # product.measure so there is an implit unit of ``measure``
    # attribute. This allows the ``capacity`` to be maintained in
    # various measurements such as the number of units that can be
    # produced per day.
    capacity = int

    # A description of the asset
    description = text

class property(asset):
    entities = properties

class vehicle(asset):
    pass

class equipment(asset):
    pass

class other(asset):
    pass

class type(orm.entity):
    """ Categorize fixed ``asset`` entity objects by type.

    Many kinds of assets may be important to an enterprise for various
    reasons. These can be listed using the ``type`` entity. 

    Note that this entity is recursive. This allows for a detailed
    breakdown of the various asset types. As an example, take the fixed
    asset type of "equipment". The information that a given asset is a
    piece of equipment is probably not enough in some cases. It would be
    nice to know what kind of equipment it is, should it be needed for a
    work ``effort``. In the same manner, it might be good to know that a
    "wehicle" is a "minivan" and that the "minivan" is actually a "Ford
    Aerostar". 
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.orm.ensure(expects=('name',), **kwargs)

    name = str

    assets = assets 

    # Make the entity recursive
    types = types

