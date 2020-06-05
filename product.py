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
from decimal import Decimal as dec

#TODO The `decimal` module should be usable as type:
#
#   class dimension:
#       number = decimal
#
# However, we currently have to do this:
#
#   class dimension:
#       number = decimal.Decimal

# TODO We should have a timespan type: 
#
# Instead of:
#
# class doorbell(entity):
#     begin = datetime
#     end   = datetime
#
# We should be able to type:
#
# class doorbell(entity):
#     datespan = True
#
# There should only be one span per class. The span should be availble
# as an object of the class that exposes certain helper methods.
#
#    
#     db = doorbell()
#     db.span.iscurrent
#     db.span.getiscurrent(somedate)
# 
# This method and property should regard the None value for `begin` as
# infinite into the past and a None value for `end` as infinite into the
# future.

# TODO We should have a date data type and a time data type


class products(orm.entities): pass

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
class qualities(features):                 pass
class colors(features):                    pass
class dimensions(features):                pass
class sizes(features):                     pass
class brands(features):                    pass
class softwares(features):                 pass
class hardwares(features):                 pass
class billings(orm.entities):              pass
class measures(orm.entities):              pass
class measure_measures(orm.associations):  pass
class feature_features(orm.associations):  pass
class product_features(orm.associations):  pass
class supplier_products(orm.associations): pass
class priorities(orm.entities):            pass
class ratings(orm.entities):               pass
class guidelines(orm.entities):            pass
class items(orm.entities):                 pass
class serials(items):                      pass
class nonserials(items):                   pass
class lots(items):                         pass
class containers(orm.entities):            pass
class containertypes(orm.entities):        pass
class statuses(orm.entities):              pass
class variances(orm.entities):             pass
class reasons(orm.entities):               pass

class prices(orm.entities):
    def getprice(self, org, regs=None, pts=None, qty=None):
        # FIXME This algorithm is not complete and has multiple issues.
        # For example, ordervalues, saletype and product features
        # constraints have not been implemented. However, more
        # problematic is that there conditional logic between these
        # constraints has not been implemeted. 
        #
        # For example, the algorithm should test price entries that
        # match a region and a price break, but that is not currently
        # done. Also, whether this should be a conjunctive test in the
        # first place may need to be parameterized. For example, a
        # product manager may want to define custom conditional logic
        # for finding the right price. Also, if no match is found it's
        # unclear at the momemnt how a fallback price could work.
        #
        # I think the best way to solve these problems is to wait for a
        # real world problem to present itself, then use that problem to
        # create a simple solution with the long term goal in mind of
        # being able to provide a complete implementation of the
        # algorithm.


        regs = None if regs is None else gem.regions(initial=regs) 
        pts  = list() if pts  is None else gem.types(initial=pts) 
            
        bases = prices()
        discounts = prices()
        surcharges = prices()

        for pr in self:
            # TODO We have to check the database to see what subtype pr
            # is. It would be better if the price collection had its 
            # subtypes loaded already. Alternatively, subtypes may be
            # over kill for prices. It would seem a `type` property
            # would be better, but I haven't decided on that.

            # TODO:b62ec864 We should not have to put `.orm.super`
            # here

            # Go up a level so for all pr, `type(pr) is product.price`
            if pr.orm.super:
                pr = pr.orm.super

            if base.orm.exists(pr):
                prs = bases
            elif discount.orm.exists(pr):
                prs = discounts
            elif surcharge.orm.exists(pr):
                prs = surcharges
            else:
                raise TypeError(
                    'Type could not be determined '
                    'for price "%s": %s' % (pr.id, type(pr).__name__)
                )

            for cat in self.product.categories:
                if pr.category in cat:
                    prs += pr

            if pr.organization.id != org.id:
                continue

            if regs is None:
                prs += pr
            else:
                for reg in regs:
                    if pr.region and reg in pr.region:
                       prs += pr

            if qty is not None and pr.quantitybreak and \
                    qty in pr.quantitybreak:
                prs += pr

            # TODO:b62ec864 We should not have to put `.orm.super`
            # here
            pt = pr.type
            if pt and pt.id in (x.id for x in pts):
                prs += pr
            
        if not bases.count:
            raise ValueError('Could not find a base price')

        def f(x):
            if x.percent is None:
                return x.price
            else:
                return x.percent

        basepr = bases.min(f)

        pr = basepr.price

        def apply(prs, additive):
            nonlocal pr
            for pr1 in prs:
                if additive:
                    if pr1.percent is None:
                        pr += pr1.price
                    else:
                        pr += (pr * (pr1.percent * dec('.01')))
                else:
                    if pr1.percent is None:
                        pr -= pr1.price
                    else:
                        pr -= (pr * (pr1.percent * dec('.01')))

        apply(discounts, additive=False)
        apply(surcharges, additive=True)

        return pr, basepr + discounts + surcharges
                
    
class bases(prices):                       pass
class discounts(prices):                   pass
class surcharges(prices):                  pass
class suggesteds(prices):                  pass
class onetimes(prices):                    pass
class recurrings(prices):                  pass
class utilizations(prices):                pass
class quantitybreaks(prices):              pass
class values(prices):                      pass
class salestypes(prices):                  pass
class estimates(prices):                   pass
class estimatetypes(prices):               pass
class product_products(orm.associations):  pass

class product(orm.entity):
    """ An abstact class that models all products including products
    sold by a given enterprise, products an enterprise buys from
    suppliers, the products of an enterprise's competitors, etc. See
    the `good` and `service` subentity classes for the concrete
    implementations.

    Unit of Measures
    ----------------
    Products have a composite called ``measure``.

        henrys_2_pencile.measure
    
    This is an instance of the ``product.measure`` class. ``measure`` is
    short for unit of measure. The composite unit of measure is the
    quantity the product is sold in. For example, the product
    henrys_2_pencile are sold individually so we can assign a unit of
    measure call each::

        henrys_2_pencile.measure = product.measure(name="each")

    Quantities can be converted into each other. Say we have another
    product called "Small Box of Henry's #2 penciles" and we wanted to
    see how many pencils that actually is. We can do this

        assert
            12,
            smallbox_of_henrys_2_penciles.measure.convert(henrys_2_pencile.measure)

    Here we see that there are 12 individual pencils in a small box of
    Henry's #2 pencile. This can be useful for inventory reporting.

    Note: The unit of measure class `measure` comes into play in the
    `dimension(feature)` as well. In this case, the product is
    associated with the `dimension(feature)` as a constituent instead of
    a composite.

    Inventory
    ---------

    The `good` subentity of `product` has concrete inventory item
    representations in product.serial an product.nonserial classes. See
    those entity objects for more information.
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

    comment = text

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

    # A collection of feature interactions to which this product
    # provides context.

    # TODO:An error occurs when we uncomment this line. This is probably
    # due to the fact that one-to-many relationships are not supported
    # currently between entity objects and association objects. (See
    # 167d775b and 28a4a305). When this relationship is supported, we can
    # uncomment this line and the
    # PRODUCT FEATURE INTERACTION/feature_features association can be
    # tested in gem_product_product.
    # feature_features = feature_features

    # The pricing components for this product.
    prices = prices

    # The many estimated costs of a product.
    estimates = estimates

    def getprice(self, org, regs=None, pts=None, qty=None):
        """ Return the least expensive price of a product for an
        organization (`org`) selling the product given the regions
        (`regs`) and quantity (`qty`) and party type (`pts).

        :param: regs regions: A collection (list, tuple, regions) of
        gem.region object that will be used to find the lowest base
        price and highest discounts for the total price.

        :param: qty int: The quantity of the product used to find the
        lowest base prices and highest discounts the product has by
        querying its quantity break entity.

        :param: pts gem.types: A collection (list, tuple,
        gem.party_types) of gem.type entities that will be used to find
        the lowes base price and highest discount prices for the total
        price.
        """
        return self.prices.getprice(
            org  = org,
            regs = regs, 
            pts  = pts,
            qty  = qty,
        )

class category(orm.entity):
    """ A recursive entity to categories products.

    Note that this entity was originally called PRODUCT CATEGORY in "The
    Data Modeling Resource Book".
    """
    entities = categories

    # The category's name
    name = str

    # A product category may be a child of a parent product category.
    # For example, a paper product, such as "Johnson fine grade 8 1/2 by
    # 11 bond paper" may be classified as a "paper" product which is a
    # subcategory of "office supplies", which may be a subcategory of
    # "computer supplies"
    categories = categories

    # These price components (`prices`) are associated with and
    # dependent on this category.
    prices = prices

    def __contains__(self, other):
        """ If `other` is in the category, True is returned; False
        otherwise. Note that since category is recursive, other is "in"
        self if it has the same id as self or if it has the id of a
        member of self's ancestry.

        For example, give a hierarchy of product categories that looks
        like this:

            Category: electronics / computers /laptops

        We could assert the following for the above categories::

            assert laptop in laptop 
            assert laptop in computer 
            assert laptop in electronics 
        """
        # TODO:d45c34a0 These methods should be automatically available
        # for any recursive entity.
        if not other:
            return False

        return other.id in (x.id for x in (self + self.ancestry))
        
    @property
    def ancestry(self):
        """ Return a collection of category entities that are the
        lineage of `self` starting with `self`'s parent, then
        grandparent, and so on.
        """

        # TODO:d45c34a0 These methods should be automatically available
        # for any recursive entity.
        cats = categories()
        
        cat = self.category

        while cat:
            cats += cat
            cat = cat.category

        return cats


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
    """ Goods are items that are usually (but not always) tangible, such
    as pens, salt, apples, and hats. Instance of a good as concrete
    inventory item are represented by the product.serial an
    product.nonserial classes.
    """

    # A collection of guidelines for the repurchase of a good
    guidelines = guidelines

    # The concrete inventory items located in a warehouse or the like.
    items = items

class service(product):
    """ Services are activities provided by other people, who include
    doctors, lawn care workers, dentists, barbers, waiters, or online
    servers, a book, a digital videogame or a digital movie.
    """
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

    Note that this class is based off the MARKET INTEREST entity in "The
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

    Note that this entity was originally called PRODUCT FEATURE in "The
    Data Modeling Resource Book".
    """
    name = str

    # The many estimated costs of a product feature.
    estimates = estimates

class quality(feature):
    """ A feature to classify a product by value such as "grade A" or
    "grade B".  For service products, such as a consutant, this may
    represent "expert" or "junior". 
    """
    entities = qualities

class color(feature):
    """ A feature that describes the color of a good. A good may have
    more than one color option, but a different color may also denote
    that it is a seperate good.
    """
    pass

class dimension(feature):
    """ A dimension is a numeric extent representing a feature of a
    product. `dimensions` are coupled with `measures`. For example, a
    product may have a `dimension.number` equal to 11 coupled with a
    `measure` entity with a `name` of 'width', for example.
    """

    def __init__(self, *args, **kwargs):
        # TODO Do not allow the GEM user to instantiate this class;
        # product.__init__ should only be called by product.good and
        # product.services. Those subclasses can pass in an override
        # flags to bypass the NotImplementedError.
        super().__init__(*args, **kwargs)
        if self.orm.isnew:
            self.name = None

    number = dec

    def convert(self, meas):
        """ Returns the value of the `dimension` converted to the unit
        of measure `meas`. Note that the conversion factor must be
        discoverable within the `measure_measures` association.

        :param: meas product.measure: The unit of measure that the
        dimension.number will be converted to.
        """
        f, dir = self.measure.convert(meas, dir=True)

        if dir:
            return f * self.number
        else:
            return self.number / f

class size(feature):
    """ A feature to specify how large or small a product is in more
    general terms than `dimension`. Examples include: "extra large",
    "large", "medium" or "small".
    """
    pass

class brand(feature):
    """ A feature that describes the marketing name tied to the `good`,
    such as "Buick" for a General Motors vehicle. Note that the brand
    name may be different from the manufacturer's name.
    """
    pass

class software(feature):
    """ A feature that allows additional software to be added to
    products or allows certain software setting to be specified for a
    product. For instance, software dollor limits could be set for
    products that are based on usage, such as meters. Another example
    could be the setting of software preferences for a software package
    or hardware purchase.
    """
    pass

class hardware(feature):
    """ A feature that allows for the specification of certain
    components that are included or that may be added to a product --
    for example, a cover for a printer.
    """
    pass
    
class billing(feature):
    """ A feature that specifies the standard types of terms that may be
    associated with a product, such as recording that an Internet access
    service may be available with either monthly or quarterly billing.
    """
    pass

class measure(orm.entity):
    """ A `measure` defines the product in terms of the type of
    measurement for the product. See `dimension` for more.

    Note, this class is called UNIT OF MEASURE in the "The Data Modeling
    Resource Book".
    """
    abbr        =  str
    name        =  str

    # A unit of measure can have zero or more dimension(feature) entity
    # objects as constituents
    dimensions  =  dimensions
    products    =  products

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.orm.isnew:
            self.abbr = None

    def convert(self, meas, dir=False, _selfonly=None, _measonly=None):
        """ Convert from the current unit of measure (``self``) to the
        ``product.measure`` paramater ``meas``. If data is found to
        calculate the conversion (the conversion data is stored in the
        ``measure_measure`` association) a ``Decimal`` value is
        returned. Otherwise, a ValueError is raised. Note that this
        algorithm will resolve transitive conversion associations (see
        comments).

        :param: meas product.measure: The unit of measure that the
        the current unit of measure will be converted to.

        :param: dir bool: If True, a tuple be returned instead of a
        Decimal. The tuple's first element will be the Decimal that
        would have been returned if dir was False. The second element
        will be the a bool.  The bool will be True if the factor was
        discovered going from subject to object in measure_measures;
        False otherwise. The direction is import for some calling code
        so the decision to multiply or divide the factor can be made
        (see `dimension.convert()`).
        """

        # NOTE This algorithm was relatively difficult to get to work
        # with three entries in measure_measures. There may be more bugs
        # discovered when more edge cases are tested.

        # When recursing, we won't want to enter into a different loop.
        if _selfonly in (True, None) and _measonly in (False, None):

            # Look to see if there is a match found between ``meas`` and
            # mm.object.
            for mm in self.measure_measures:
                if mm.object.id == meas.id:
                    
                    # Immediately return the Decmial `factor`
                    if dir:
                        return mm.factor, True
                    else:
                        return mm.factor
                else:
                    # No match was found so `try` recursing. This is for
                    # transitive logic. For example, say you have the
                    # following measure associations in measure_measures
                    # 
                    #  subject   object    factor
                    #  -------   ------    ------
                    #  each      smallbox  12
                    #  smallbox  largebox  2
                    #
                    # Above we can see that "each" is associated with
                    # "smallbox", and "smallbox" is associated with
                    # "largebox". Thus, there is a transitive and
                    # implicit association between "each" and "largebox"
                    # with a factor of 12 * 2. The recursive call below
                    # resolves this and calculates the factor.

                    try:
                        f = mm.object.convert(meas, _selfonly=True)
                    except ValueError:
                        pass
                    else:
                        return f * mm.factor

        # When recursing, we won't want to enter into a different loop.
        if _selfonly in (False, None) and _measonly in (True, None):
            # We weren't able to find an association with
            # self.measure_measures, so we can try going backwards with
            # `meas.measure_measures`. This is the logic tha gets used
            # when we convert the opposite way from the above loop.
            #
            # For example:
            #
            #     smallbox.convert(largebox) 
            #
            #     vs.
            #
            #     largebox.convert(smallbox) 

            for mm in meas.measure_measures:
                subid, objid = mm.subject.id, mm.object.id
                if subid == meas.id and (
                        objid == self.id or _measonly
                    ):
                    if dir:
                        return mm.factor, False
                    else:
                        return mm.factor
                else:
                    # TODO Consolidate this with above logic
                    try:
                        f = mm.object.convert(mm.object, _measonly=True)
                    except ValueError:
                        pass
                    else:
                        return f * mm.factor

        raise ValueError(
            'Data could not be found to make the conversion.'
        )

class feature_feature(orm.association):
    """ This reflexive associations store references to two
    different `features`. The `type` property values `Incompatibility` and
    `Dependency` will determine whether or not the features are
    incompatible or dependent on one another respectively within the
    context of the implicit `product` composite. (Note that the product
    entity has a collection of `feature_features` which automatically
    gives `feature_feature` a `product` composite.)

    Note that this entity was originally called
    PRODUCT FEATURE INTERACTION in "The Data Modeling Resource Book".
    """

    # Constants for the `type` property. Do not change the values for
    # they are used in database entries.

    # Declares that the `subject` feature is incompatable with the
    # `object` feature.
    Incompatibility = 0

    # Declares that the `subject` feature is incompatable with the
    # `object` feature.
    Dependency = 1

    # The type property. Valid value are
    # feature_feature.Incompatibility and feature_feature.Dependency.
    # TODO Write validation rules to ensure a valid type is selected.
    type = int

    # The first feature. The meaning of the order is determined by the
    # `type` property.
    subject = feature

    # The second feature. The meaning of the order is determined by the
    # `type` property.
    object = feature

class measure_measure(orm.association):
    """ An associative entity that privides the capability to use a
    common unit of measure (i.e., `subject`) to calculate how much inventory
    an enterprise has in another unit of measure (i.e., `object`). The
    attribute `factor` is the conversion factor is the number to
    multiply `subject` by to get the `object`.

    For example, there may be several products for Henry #2 penciles
    that have different units of measure such as "each", "small box",
    and "large box". In many cases, organizations need to show total
    inventories, costs, and sales for all of a product regardless of its
    unit of measure (`product.measure`). By defining a common unit of
    measure, (such as "each", and including a conversion `factor`, e.g.,
    12 for "small box" and 24 for "large box"), it is possible to
    determine the total amount of Henry #2 penciles there are in
    inventory and how many have been sold.
    """

    subject  =  measure
    object   =  measure
    factor   =  dec

class product_feature(orm.association):
    """ Associates a product with a feature. The association will
    indicate whether the feature is required, standard, optional or
    selectable with the product.

    Note that this entity was originally called
    PRODUCT FEATURE APPLICABILITY in "The Data Modeling Resource Book".
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

class supplier_product(orm.association):
    """ Since products can be sold by one or more suppliers and a
    supplier can sell more than one product, the ``supplier_product``
    association is used to store this many-to-many relationship.
    """

    # The participating entity objects of the associations. Note that
    # the supplier will usually be a gem.company subtype of
    # `gem.organization`. We will make it simply an `organization` to
    # prodive the greatest flexability.
    supplier  =  gem.organization
    product   =  product

    # The begin and end datetimes indicate the timespan that the
    # supplier offered by the `supplier`
    begin     =  datetime
    end       =  datetime

    # The `lead` is the average amount of time in days it takes a
    # supplier to ship an order to a customer location from the time of
    # order. Note that the actual average can be calculated by analysing
    # the order an shipping data, however, the `lead` time is still
    # provided here because some suppliers quote a standard amout of
    # delivery for each product.
    lead      =  int

class priority(orm.entity):
    """ This class privides information to track the priority of which
    supplier to order a given product from first, second third and so
    on. There is a one-to-many relationship between the
    ``supplier_products`` association and this class.

    Note that the original name for this class from "The Data Model
    Resource Book was called PREFERENCE TYPE.
    """
    entities = priorities

    # TODO Since there is a finite number of priorities, we should
    # fallowing the model of the `product.rating` type which autosaves
    # the the record to the database in the construct if it needs too.
    # See product.rating.__init__ and product.rating.brokenrules. This
    # pattern may become so redundant that it could be encapsulated in a
    # method like orm.ensure()

    # The ordinal indicating the priority. A priority of 0 indicates the
    # highest prioritity. 1 would be the second highest, and so one.
    ordinal = int

    supplier_products = supplier_products

class rating(orm.entity):
    """ This class is used to rate the overall performance for each
    product by its supplier. 

    Note you will never need to save() the rating object. If the rating
    is in the database already, it will be discovered by the constructor
    and returned. If it is not in the database, it will be created
    automatically within the constructor.

    Note that the original name for this class from "The Data Model
    Resource Book was called RATING TYPE.
    """

    # TODO When 167d775b and 28a4a305 are resolved, we can begin
    # writing tests in it_associates_product_to_suppliers to add
    # ratings to supplier_products. As of now, that feature shouldn't
    # work.

    # Possible values for the `score`
    Outstanding  =  0
    Good         =  1
    Fair         =  2
    Poor         =  3
    Bad          =  4
    Terrible     =  5

    # The score given to a supplier_products record. The "constants"
    # above can be used as values for the score.
    score = int

    # A given rating can have zero or more supplier_products records.
    supplier_products = supplier_products

    def __init__(self, *args, **kwargs):
        """ Create record if it doesnt exist. Return record if or if it
        doesn not exist.
        """
        super().__init__(*args, **kwargs)

        try:
            # We are expecting score to be given by the user
            score = kwargs['score']
        except KeyError:
            # When loading via the orm.populate() method, score won't be
            # passed in. Just return.
            return

        # See if the rating is in the db
        rs = ratings(score=score)

        if rs.count:
            # If it is, we it's value to self
            self.id = rs.first.id
            self.score = rs.first.score

            # The record isn't new or dirty so set all peristance state
            # variables to false.
            self.orm.persistencestate = (False,) * 3
        else:
            # Save immediately. There is no need for the user to save
            # manually because there are only several rating objects
            # that will ever exist. We just pretend like they always
            # exist and are accessable via the construct with no fuss.
            self.save()

        
    @property
    def brokenrules(self):
        # TODO I think this needs to be changed to
        # _getbrokenrules(guestbook) so the guestbook can be pased to
        # the super object.
        brs = super().brokenrules
        valid = (
            rating.Outstanding,
            rating.Good,
            rating.Fair,
            rating.Poor,
            rating.Bad,
            rating.Terrible,
        )

        if self.score not in valid:
            brs += 'Invalid score: %s' % str(self.score)

        return brs

class guideline(orm.entity):
    """ This entity provides information on how to best repurchase
    products. A `product.good` will have zero-or-more guideline entries.
    `product.services` generally do not get repurchase based on this
    type of guildline.

    The reorder guildlines may vary based on whether the product need is
    for a particular `party.region`, such as for a certain state,
    facility, such as for a specific plant, and/or for a particular
    internal organization, such as a `party.division`.

    Note that this class is based off the REORDER GUILDLINE entity in "The
    Data Modeling Resource Book".
    """

    # A timespan to indicate when the guildelines are valid
    begin = datetime
    end   = datetime

    # The quantity at which the good needs to be reordered or
    # reproduced.
    level = int

    # The recommended amount of the good to order. This may have been
    # derived by analysis to determine the moset efficient quantity. The
    # `level` and the `quantity` may be for goods the enterprise is
    # buying or for goods that the enterprise is selling because some
    # firms let the vendor monitor the stock levels of inventory and do
    # the appropriate ordering.
    quantity = int

    # The geographical region (postal code, state, etc) that the
    # guildline is for.
    region = gem.region

    # The facility the guildline is for
    facility = gem.facility

    # TODO This should be interalorganization, but that does not exist
    # yet in the party module.
    # The internal organization the guideline is for
    organization = gem.organization

class item(orm.entity):
    """ The `item` is the abstract base class for `serial` and
    `nonserial`. Both `serial` and `nonserial` are inventory items
    meaning they are the physical occurance of a `good` at a location.

    Note that this is based of the INVENTORY ITEM entity in "The Data
    Model Resource Book".
    """
    
    # The facility this inventory item is located in. Alternatively, the
    # item could be located in a ``container`` which itself is located
    # within a facility.
    facility = gem.facility

    # A collection of variances, i.e., a history of shrinkage and
    # overages that were noticed during physical inspection of the
    # inventory item.
    variances = variances

class serial(item):
    """ An inventory item that tracks a serial number. 

    Note that this is based on the SERIALIZED INVENTORY ITEM entity in
    "The Data Model Resource Book".
    """

    # The serial number for this inventory item
    number = str

class nonserial(item):
    """ An inventory item that has no serial number. Rather, the items
    are grouped together and the `quantity` on hand attribute is
    maintained by their location.

    Note that this is based on the SERIALIZED INVENTORY ITEM entity in
    "The Data Model Resource Book".
    """

    # The quantity on head for this nonserialized inventory item.
    quantity = int

class lot(orm.entity):
    """ Represents a lot. A lot is a grouping of `items` of the same
    type generally used to track inventory items back to their source.
    """

    # TODO The user should be allowed to create the createdat field
    # because that will get created by the metaclass anyway. This should
    # throw an error. Same for `updatedat`.

    # The date the lot was created
    createdat = datetime

    # The quantity of items represented by the lot
    quantity = int

    # The date the lot expires
    expiresat = datetime

    # The inventory items the lot represents
    items = items

class container(orm.entity):
    """ Containers contain inventory items (``items``). Containers are
    located within a facility. (Alternatively, an inventory item can
    simply be located within a facility with no container if that makes
    more sense). `containers` are further defined by they their
    container type property.
    """

    # The name or description of the container
    name = str

    # The inventory items stored in this container
    items = items

    # The facility in which the container is currently located. 
    facility = gem.facility

class containertype(orm.entity):
    """ This class allows for the definition of containers.
    """

    # The name of the container type
    name = str

    # Instances of containers matching this type.
    containers = containers

class status(orm.entity):
    """ Status maintains the current condition of an inventory item
    (`item`). It allows for the item to be marken as "good", "being
    repaired", "slighly damaged", "defective", "scrap" and so on.

    Note that this entity was originally called
    INVENTORY ITEM STATUS TYPE in "The Data Modeling Resource Book".
    """

    entities = statuses

    # The name of the status, i.e., "good", "being
    # repaired", "slighly damaged", "defective", "scrap"
    name = str

    # The items declared to have this status
    items = items

class variance(orm.entity):
    """ This entity keeps a history of inventory item (``item``)
    shrinkage or overages that were noticed during physical inventories
    or inspections of the item.

    Note that this entity was originally called ITEM VARIANCE in "The
    Data Modeling Resource Book".
    """

    # The physical inventory date, i.e., the date that the item variance
    # was discovered.
    date = datetime

    # The difference between quantity of items within inventory
    # items (which is 1 for serialized items and the quantity on hand for
    # non-serialized items) and the physical inventory at the time of
    # the physical inventory date (variance.date).
    quantity = int

    # Variance entries can be assigend a standard reason (see the
    # ``reason`` entity). However, when the standard reasons don't
    # suffice to explain the variance, this comment field can be used.
    # For example, if the enterprise discovered that there was a loss of
    # inventory items due to theft, this field can record the date the
    # theft was discovered, the amount of the product that was stolen,
    # and the specific details behind the theft. 
    comment = text

class reason(orm.entity):
    """ The ``reason`` entity provides standard explanations of the
    ``variance`` to the inventory ``item``'s on-hand amount. Possible
    values may include "theft", "shrinkage", "unknown variance" and
    "ruined goods". The ``variance.comment`` allowl for additional
    non-standard explanations.
    """

    # The name or description of the reason such as "theft",
    # "shrinkage", "unknown variance," "ruined goods", etc.
    name = str

    # The collection of inventory item variances that have this
    # standard reason.
    variances = variances

class price(orm.entity):
    """ The price of a product. See `price`'s subtypes for more.

    Note that this entity was originally called PRICE COMPONENT in "The
    Data Modeling Resource Book".
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # TODO:a95ef3d8
        if self.orm.isnew:
            for prop in ('comment', 'percent', 'price'):
                try:
                    kwargs[prop]
                except KeyError:
                    setattr(self, prop, None)


    # NOTE "The Data Modeling Resource Book" specifies each of the
    # subentity objects. However, it also says, "These represents the
    # common variables for pricing; however, the enterprise needs to
    # determine if these variables are applicable or if there are other
    # pricing variables for the enterprise." This makes me wonder if
    # there should be a `pricetypes` entity such that users can enter
    # their own types of prices.

    # This timespan indicate the starting an ending dates for which the
    # price component is valid.
    begin = datetime
    end   = datetime

    # The `price` maintains a dollar amount. It, along with the
    # `percent` attribute can be used to record discounts or quantity
    # breaks.  Each of the subentity objects of `price` record a value
    # in either the price attribute or the percent attribute but not
    # both. TODO Write a rule that one of these has to be None and the
    # other has too be non-None.
    price =  dec
    percent = dec

    # Allows each price component to be annotated, for example, "special
    # discount provided to increase sales".
    comment = text

    # Each `price` can be based on many variables or combinations of
    # thes varibables. These variables include a geographic `region`,
    # `party.type`, `product.category`, `break`, `ordervalue` and
    # `salestype`.

    # The geographic region composite allows pricing to be dependent on
    # geographic region. 
    region = gem.region

    # The party.type composite allows the price to be dependent of the
    # classification of the party buying the goods such as special
    # pricing for minority parties or governmental organizations.
    type = gem.type

    # NOTE The above `region` and `type` properties are defined here
    # because they are from the party module. If it weren't for the
    # circulular reference proplem that would happen, these composite
    # references would have come implitily as a result of creating a
    # constituent entities collection on those classes (i.e.,
    # gem.region.prices, gem.type.prices). For entities where this "use-
    # to-define" relationship won't cause a circular reference,
    # constituent collections have been created. See
    # product.category.prices, product.break.prices,
    # product.ordervalue.prices and product.salestype.prices.

    # A price component can be specified for different organizations
    # because it is possible for multiple organizations to supply the
    # same product.
    organization = gem.organization

class base(price):
    """ The starting price for a product.

    Note that this entity was originally called BASE PRICE in "The
    Data Modeling Resource Book".
    """
    pass

class discount(price):
    """ This entity stores a valid reduction to the base price.

    Note that this entity was originally called DISCOUNT COMPONENT in
    "The Data Modeling Resource Book".
    """

class surcharge(price):
    """ This entity adds on possible charges to the price of a product.

    Note that this entity was originally called SURCHARGE COMPONENT in
    "The Data Modeling Resource Book".
    """
    pass

class suggested(price):
    """ This entity adds on possible charges to the price of a product.

    Note that this entity was originally called
    MANUFACTURER SUGGESTED PRICE in "The Data Modeling Resource Book".
    """
    pass

class onetime(price):
    """ This price component indicates that the charge is applied one
    time.

    Note that this entity was originally called ONE TIME CHARGE in "The
    Data Modeling Resource Book".
    """
    pass

class recurring(price):
    """ This price component indicates that the charge is based on a per
    time frequencey measure (per hour, per day, per month).

    Note that this entity was originally called RECURRING CHARGE in "The
    Data Modeling Resource Book".
    """
    pass
  
class utilization(price):
    """ This price component indicates that the charge is based on a
    unit of measure (`measure`) such as per a certain quantity of
    "internet hits" to describe the charge for Web hosting services.

    Note that this entity was originally called UTILIZATION CHARGE in
    "The Data Modeling Resource Book".
    """
    quantity = int

class quantitybreak(orm.entity):
    """ The quantitybreak entity stores various ranges of quantity
    breaks in the begin and end attributes. This allows a price
    component (`price`) to be dependent on a range of quantities being
    purchased for the given product.

    Note that this entity was originally called QUANTITY BREAK in
    "The Data Modeling Resource Book".
    """

    begin = int
    end   = int

    # These price components (`prices`) are associated with and
    # dependent on this quantity break.
    prices = prices

    def __contains__(self, qty):
        return (self.begin is None or qty >= self.begin) and \
               (self.end   is None or qty <= self.end)

class value(orm.entity):
    """ This class represent an order's value. It allows different
    pricing levels based on total amounts of orders.

    Note that this entity was originally called ORDER VALUE in "The Data
    Modeling Resource Book".
    """

    # The span an order's total amount can fall in to be applicable for
    # this order `value`.
    begin = dec
    end   = dec

    # These price components (`prices`) are associated with and
    # dependent on this order value.
    prices = prices

class salestype(orm.entity):
    """ This classs allows different pricing based on different methods
    of selling; for instance, Internet-based sales may have a different
    price than retail-based salse or catalog-based sales.

    Note that this entity was originally called SALES TYPE in "The Data
    Modeling Resource Book".
    """

    # The name or description for this sales type
    name = str

    # These price components (`prices`) are associated with and
    # dependent on this sales type.
    prices = prices

class estimate(orm.entity):
    """ This class maintains information on each product and its many
    estimated costs.

    Note that this entity was originally called ESTIMATED PRODUCT COST
    in "The Data Modeling Resource Book".
    """

    # NOTE There is a one-to-many relationship between
    # `product.product` and `product.estimate` (see
    # `product.product.estimates`) There is also a one-to-many
    # relationship between `product.feature` and `product.estimate`
    # (see `product.feature.estimates`).

    # Product costs can vary by season or over time, so a timespan
    # is included to show the time period for which the cost is valid.
    begin = datetime
    end   = datetime

    # The estimated cost
    cost  = dec

    # A cost component may vary based on where the costs are incurred and
    # hence a cost component can have a region composite. For instance,
    # manufacturing costs may be less expensive in a plant located in
    # one country versus another.
    region = gem.region

    # The estimated costs may, in some cases, vary by organization. If
    # the organization is trackting and comparing tho costs for multiple
    # suppliers, then the enterprise may want to be able to record
    # seperate costs for each organization; hence the optional
    # relationship to an organization composite.
    organization = gem.organization

class estimatetype(orm.entity):
    """ This entity specifies what tpo of cost an ``estimate`` is.

    Note that this entity was originally called COST COMPONENT TYPE
    in "The Data Modeling Resource Book".
    """

    # The name or description of the estimate type
    name = str

    # The collection of estimates declared to be of this entity object's
    # type.
    estimates = estimates

class product_product(orm.association):
    """ A reflexive association between a product and another product.
    The ``type`` attribute defines the type of association. See the
    comments for the ``type`` constants below for an explainaion of each
    relationship type.

    Note that this entity was originally called PRODUCT ASSOCIATION
    in "The Data Modeling Resource Book".
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.orm.isnew:
            props = 'comment', 'instruction', 'reason', 'quantity'
            for prop in props:
                try:
                    kwargs[prop]
                except KeyError:
                    setattr(self, prop, None)

    # TODO When subassociations are supported, it will be more elegant
    # to use subtypes instead of a ``type`` property attribute since the
    # subassociations have different properties from each other. As it
    # stands, some entries will always have None values for some
    # attributes if the type does not support a given attribute.
    # TODO Validation rules will have to be writen to support these
    # constraints. See the type constants below for more information.

    ''' Type constants. Please do not change values as they are stored in
    the database.
    '''

    # Indicates that the `subject` is a marketing package and the
    # `object` is part of that package. 
    #
    # The `begin`, `end`, `reason`, `quantity` and `instruction`
    # attributes can be used with Marketing associations.
    Marketing        =  0

    # Indicates that the `object` can serve as a substitute for the
    # `subject`. A product may be substituted by many other products.
    # For example, perhaps a certain pen within an office desk set may
    # be used as a substitue in many circumstances. The `begin` and
    # `end` dates can be used to specify the time frames that products
    # may be substituted for each other. The `quantity` attribute allows
    # a product to be substituted for a certain quantity of another
    # product. (See PRODUCT SUBSTITUTE in "The Data Modeling Resource
    # Book" for examples). The `comment` attribute provides additional
    # information regarding the substution of a product; for example,
    # "try not to substitute with this product if it can be avoided as
    # the product is of a lower quality than the standard product".
    #
    # The `quantity`, `begin`, `end`, `reason`, `quantity` and `comment`
    # attributes can be used for Substitute associations.
    Substitute       =  1

    # An Obsolesence association indicates that the `subject` is about
    # to be, or has already been superseeded by the `object`. 
    #
    # The `superceededat` and `reason` attributes can be non-None values
    # for this type.
    Obsolesence      =  2

    # A Complement association indicates that the `subject` product is
    # complemented by the `object` product. This may be used by a
    # recommendation engine to make suggestions on a given order.
    #
    # The `begin`, `end`, `reason` attributes can be used with
    # Complement associations.
    Complement       =  3

    # An Incompatibility association indicates that the `object` product
    # may not be used with the `subject` product. For instance, a
    # "Barry's pen refill" may not be compatible with the product
    # "Goldstein Elite Pen"; it would be good to let customers know
    # this by maintaining this information and using it at the time of
    # an order.
    #
    # The `begin`, `end` and `reason` attributes can be used for
    # Incompatibility associations.
    Incompatibility  =  4

    # The Component property indicates that the `subject` product is
    # made up the product in the `object` field. A product can be made up
    # of more than one other product; alternatively, a product may be
    # used in several other products. For example, an office dek set may
    # consist of a pen, pencil, calendar, clock, and wood base. Any one
    # of these components may be used in the assembly of another
    # product. Service organizations may also assemble one or more of
    # their services into a product and, alternateviely, use the same
    # service in may product offerings.
    #
    # The `begin`, `end`, `quantity`, `instruction` and `comment`
    # attributes can be used for Component associations.
    Component        =  5

    # A timespan whose meaning is determined by the value of the `type`
    # attribute.
    begin = datetime
    end   = datetime

    # Used when the `type` attribute is set to Obsolesence. Indicates
    # the date the `subject` will be, or has already been, superceeded
    # by the `object`.
    superceededat = datetime

    reason = text

    # When the `type` is Component, the `instruction` attribute explains
    # how to assemble the products.
    instruction = text

    # Used when the `type` attribute is set to Substitute. The `comment`
    # attribute provides additional information regarding the
    # substitution of a product; for example, "try not to substitute
    # with this product if it can be avoided as the product is of a
    # lower quality than the standard product".
    comment = text

    # When `type` is Component, the `quantity` attribute indicates how
    # many of a certain product are used in the assembly of another
    # product. When the `type` is Substitute, the `quantity` attribute
    # allows a product to be substituted for a certain quanity of
    # another product.
    quantity = int

    # Indicates the `type` of association. See the constants above for
    # more information.
    type = int

    subject = product
    object  = product
