# vim: set et ts=4 sw=4 fdm=marker

# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2019

import orm
import primative
from datetime import datetime
from dbg import B

class products(orm.entities):
    pass

class categories(orm.entities):
    pass

class goods(products):
    pass

class services(products):
    pass

class product(orm.entity):
    """ An abstact class that models all products including products
    sold by a given enterprise, products an enterprise buys from
    suppliers, the products of an enterprise's competitors, etc. See
    the `good` and `service` subentity classes for the concrete
    implementations.
    """

    # A description of a product.
    name = str

    # The date the product was first available to be sold.
    introducedat = datetime  # TODO Make date type

    # The date that the product will not be sold any more by the
    # manufacturer.
    discontinuedat = datetime  # TODO Make date type

    # The date the product will no longer be supported by the
    # manufacturer.
    unsupportedat = datetime

    comment = str, 1, 65535 # TODO Make text type

class category(orm.entity):
    table = 'product⦀categories'
    entities = categories

    begin    =  datetime
    end      =  datetime

    # TODO It would be nice if we didn't have to end `primary_` with
    # an underscore but if we don't, MySQL sees it as an syntax
    # error. It would be cool if the ORM could detect MySQL's
    # keywords being used as column names and append the underscore
    # automatically sparing the ORM user the inconvenience of
    # remembering to add the underscore (assuming and underscore is
    # the proper solution to this problem).
    primary_  =  bool
    comment  =  str, 1, 65535

class good(product):
    pass

class service(product):
    pass
