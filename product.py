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
import gem
import decimal

#TODO The `decimal` module should be usable as type:
#
#   class dimension:
#       number = decimal
#
# However, we currently have to do this:
#
#   class dimension:
#       number = decimal.Decimal

class products(orm.entities):
    pass

class category_classifications(orm.associations):
    # TODO:1c409d9d The ORM does not call orm.entities.brokenrules when
    # saving.

    # TODO:a082d2a9 Some work needs to be done to ensure that entity and
    # entities objects can override brokenrules correctely.
    '''
    @property
    def brokenrules(self):
        brs = entities.brokenrules()

        # Ensure that no product can be put two different categories
        # with a primary flag.
        for cc in self:
            primary = None
            for cc1 in self:
                if cc.product.id == cc1.product.id:
                    if cc1.isprimary:
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
    '''
class categories(orm.entities):            pass
class goods(products):                     pass
class services(products):                  pass
class category_types(orm.associations):    pass
class features(orm.entities):              pass
class colors(features):                    pass
class qualities(features):                 pass
class dimensions(features):                pass
class measures(orm.entities):              pass
class product_features(orm.associations):  pass

class product(orm.entity):
    """ An abstact class that models all products including products
    sold by a given enterprise, products an enterprise buys from
    suppliers, the products of an enterprise's competitors, etc. See
    the `good` and `service` subentity classes for the concrete
    implementations.
    """

    def __init__(self, *args, **kwargs):
        # TODO Do not allow the GEM user to instantiate this class;
        # product.__init__ should only be called by product.good and
        # product.services. Those subclasses can pass in an override
        # flags to bypass the NotImplementedError.
        super().__init__(*args, **kwargs)
        if self.orm.isnew:
            self.manufacturerno  =  None
            self.sku             =  None
            self.upca            =  None
            self.upce            =  None
            self.isbn            =  None
            self.comment         =  None

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

    ''' Various type of identifiers'''

    # A good's id designated by the manufacture
    manufacturerno = str

    # Stock-keeping unit (SKU) is a standard product id that distinctly
    # identifies various products.
    sku = str, 10, 10

    # Universal Product Code--American (UPCA) identifies products within
    # America.
    upca = str, 12, 12

    # Universal Product Code--Europe (UPCE) identifies products within
    # Europe.
    upce = str, 6, 6

    # International Standard Book Number is a mechanism to identify
    # specific books throughout the world
    isbn = str, 10, 10

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

    # TODO It would be nice if we didn't have to end `isprimary` with
    # an underscore but if we don't, MySQL sees it as an syntax
    # error. It would be cool if the ORM could detect MySQL's
    # keywords being used as column names and append the underscore
    # automatically sparing the ORM user the inconvenience of
    # remembering to add the underscore (assuming and underscore is
    # the proper solution to this problem).
    # UPDATE I changed 'primary_' to 'isprimary'. The TODO is still
    # valid but prepending the 'is' might to booleans may deprioritize
    # it.

    # If True, the category is will be considered the primary category of
    # the product. For instance, if a product is associated with
    # multiple categories, a sales report that groups products by
    # category may take this flag into consideration.
    isprimary  =  bool

    comment  =  str, 1, 65535

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.comment = None

    @property
    def brokenrules(self):
        brs = super().brokenrules

        # TODO Only one "primary" association can exist between a given
        # product and a category. See the "isprimary" column.
        pid = self.product.id
        cc = category_classifications(
            product__productid=pid,
            isprimary=True
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

class category_type(orm.association):
    """ An association between product.category and party.type. The
    association represents the interest that a type of party is declared
    to have in a certain product. 

    For example, a party.type called "Insurance companies" may have an
    interest in the product.category called "Insurance. A "Small
    organization" party.types may have an interest in the "Wordpress
    services" product.category.

    Interest in a product category can change over time so a `begin` and
    `end` date are included.

    Note that this class is based off the MARKET_INTEREST entity in "The
    Data Modeling Resource Book". The name "category_type" is used
    instead because it adhers to the ORM's convention on naming
    associations - consequently resulting in an unfortunate misnomer.
    """
    begin     =  datetime
    end       =  datetime
    type      =  gem.type
    category  =  category

class feature(orm.entity):
    """ Used to define the ways a product may be modified or tweaked.
    `feature` entities are associate with `product` entities via
    `product_feature` associations.
    """
    name = str

class color(feature):
    pass

class quality(feature):
    entities = qualities

class dimension(feature):
    """ A dimension is a numeric extent representing a feature of a
    product. `dimensions` are coupled with `measures`. For example, a
    product may have a `dimension.number` equal to 11 coupled with a
    `measure` entity of with a `name` of 'width'.
    """

    def __init__(self, *args, **kwargs):
        # TODO Do not allow the GEM user to instantiate this class;
        # product.__init__ should only be called by product.good and
        # product.services. Those subclasses can pass in an override
        # flags to bypass the NotImplementedError.
        super().__init__(*args, **kwargs)
        if self.orm.isnew:
            self.name = None

    number = decimal.Decimal

class measure(orm.entity):
    """ A `measure` defines the product in turms of the type of
    measurement for the product. See `dimension` for more.

    Note, this class is called UNIT_OF_MEASURE in the "The Data Modeling
    Resource Book".
    """
    abbr        =  str
    name        =  str
    dimensions  =  dimensions

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.orm.isnew:
            self.abbr = None

class product_feature(orm.association):
    """ Associates a product with a feature. The association will
    indicate whether the feature is required, standard, optional or
    selectable with the product.
    """

    ''' Types '''
    # Specifies that the feature is mandatory with the product.
    Required    =  0

    # Indicates that the feature comes as part of the standard
    # configuration of the product.
    Standard    =  1

    # Indicates the feature is an optional component.
    Optional    =  2

    # Indicates that the feature must be selected by the purchaser.
    Selectable  =  3

    ''' ORM Attributes '''
    # A timespan to indicate when this association is valid
    begin  =  datetime
    end    =  datetime

    # Use a numeric code (see the Types section above) to indicate
    # whether the associated feature is required, standard, optional or
    # selectable with the product.
    type   =  int

    # The product portion of the association
    product = product

    # The feature portion of the association
    feature = feature
