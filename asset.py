# vim: set et ts=4 sw=4 fdm=marker

# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2020

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

class assets(orm.entities): pass
class assettypes(orm.entities): pass

class asset(orm.entity):
    name = str
    acquired = date
    serviced = date
    nextserviced = date
    capacity = int
    description = text

class assettype(orm.entity):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.orm.ensure(expects=('name',), **kwargs)

    name = str

    assets = assets 

