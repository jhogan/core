# vim: set et ts=4 sw=4 fdm=marker

# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2019

import orm
import entities
import primative
from datetime import datetime
from dbg import B

class products(orm.entities):
    pass

class category_classifications(orm.associations):
    @property
    def brokenrules(self):
        brs = entities.brokenrules()
        for cc in self:
            primary = None
            for cc1 in self:
                if cc.product.id == cc1.product.id:
                    if cc1.primary_:
                        if primary:
                            brs += entities.brokenrule(
                                'The product "%s" already is set to '
                                'primary in category "%s".' 
                                    % (
                                        cc1.product.name,
                                        cc.category.name
                                )
                            )
                        else:
                            primary = cc.category
                
        return brs


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
    entities = categories

    # The category's name
    name = str

    # A product category may be a child of a parent product category.
    # For example, a paper product, such as "Johnson fine grade 8 1/2 by
    # 11 bond paper" may be classified as a "paper" product which is a
    # subcategory of "office supplies", which may be a subcategory of
    # "computer supplies"
    categories = categories

class category_classification(orm.association):
    """ An association linking a product witha a category.
    """

    product  = product
    category = category

    # Indicates the timespan a product is classified under a certain
    # category. An `end` of None indicates that the product is currently
    # classified under the given category.
    begin    =  datetime
    end      =  datetime

    # TODO It would be nice if we didn't have to end `primary_` with
    # an underscore but if we don't, MySQL sees it as an syntax
    # error. It would be cool if the ORM could detect MySQL's
    # keywords being used as column names and append the underscore
    # automatically sparing the ORM user the inconvenience of
    # remembering to add the underscore (assuming and underscore is
    # the proper solution to this problem).

    # If True, the category is will be considered the primary category of
    # the product. For instance, if a product is associated with
    # multiple categories, a sales report that groups products by
    # category may take this flag into consideration.
    primary_  =  bool

    comment  =  str, 1, 65535

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.comment = None

    @property
    def brokenrules(self):
        brs = super().brokenrules

        # TODO Only one "primary" association can exist between a given
        # product and a category. See the "primary_" column.
        pid = self.product.id
        cc = category_classifications(
            product__productid=pid,
            primary_=True
        )
        if cc.ispopulated:
            brs += entities.brokenrule(
                'The product "%s" already is set to primary in '
                'category "%s".' % (
                                        self.product.name,
                                        self.category.name
                                    )
                )
        return brs

class good(product):
    pass

class service(product):
    pass
