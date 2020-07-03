# vim: set et ts=4 sw=4 fdm=marker

# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2020

""" This module contains ``orm.entity`` objects which caused referential
issue in their natural homes. 

For example, the the ``requirement`` class should be in the order.py.
However, product.py wants a ``requirment`` class that subclasses
``order.requirement``; and this cannot be, because product.py can't
``import`` order.py because it would create a circular reference
(order.py ``import``s product.py). The ``apriory.py`` module imports no
GEM class and can therefore house classes that any and all GEM classes
may depend on.

"""
import orm
from orm import text, date
from decimal import Decimal as dec

class requirements(orm.entities):         pass
class requirement(orm.entity):
    """ A ``requirement`` is an organization's need for *anything*.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.orm.isnew:
            self.reason = None

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
    created = date

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
