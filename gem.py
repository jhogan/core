# vim: set et ts=4 sw=4 fdm=marker

# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2019

# TODO Checkout http://wiki.goodrelations-vocabulary.org/Quickstart for
# an standard for ecommerce markup when marking up parties, places, etc.

import orm
import primative
from datetime import datetime
from dbg import B

class parties(orm.entities):
    pass

class organizations(parties):
    pass

class legalorganizations(organizations):
    pass

class companies(legalorganizations):
    pass

class party_parties(orm.associations):
    pass

class party_addresses(orm.associations):
    pass

class persons(parties):
    pass

class address_regions(orm.associations):
    pass

class regions(orm.entities):
    pass

class party_contactmechanisms(orm.associations):
    pass

class contactmechanisms(orm.entities):
    pass

class phones(contactmechanisms):
    pass

class emails(contactmechanisms):
    pass

class addresses(contactmechanisms):
    pass

class party(orm.entity):
    entities = parties
    
    # A party may have 0 or more national id numbers. For example, an
    # organization may have one or more Federal Taxpayer Identification
    # Numbers. A person could have an SSN number and/or other related
    # identitier from different locales.
    nationalids = str

    # The Dun & Bradstreet DUNS number for identifying an organization
    # or business person.
    dun = str

    #https://en.wikipedia.org/wiki/International_Standard_Industrial_Classification
    #https://schema.org/isicV4
    # The International Standard of Industrial Classification of All
    # Economic Activities (ISIC), Revision 4 code for a particular
    # organization, business person, or place.
    isicv4 = str, 1, 1

class organization(party):
    """ An abstract class representing a group of people with a common
    purpose. Subtypes may include schools, NGOs, clubs, corporations,
    departments, divisions, government agency and nonprofit
    organizanitions. More informal organizations may include teams,
    families, etc.
    """
    name = str

class legalorganization(organization):
    # The Employer Identification Number (EIN), also known as the
    # Federal Employer Identification Number (FEIN) or the Federal Tax
    # Identification Number, is a unique nine-digit number assigned by
    # the Internal Revenue Service (IRS) to business entities operating
    # in the United States for the purposes of identification. 

    # NOTE This will need to be it's own entity object since EINs are
    # specific to the USA.
    ein = str, 9, 9
    
class company(legalorganization):
    entities = companies

class person(party):
    firstname      =  str
    middlename     =  str
    lastname       =  str
    title          =  str
    suffix         =  str
    gender         =  bool
    mothersmaiden  =  str
    maritalstatus  =  bool

    # TODO
    # passport = passport

class region(orm.entity):
    PostalCode  =  0
    County      =  1
    City        =  2
    State       =  3
    Province    =  4
    Territory   =  5
    Country     =  6

    def __init__(self, *args, **kwargs):
        # TODO abbreviation is a standard string but we want to default
        # it to None. This should be done in the constructor, however,
        # the advent of the kwargs parameter for entities makes this
        # expression "default 'abbreviation' to None" a bit crytic and
        # hard to remember. We need to devise an easier way to default
        # attributes.

        super().__init__(*args, **kwargs)

    @staticmethod
    def create(*args):
        regs = root = None
        for tup in args:
            name = tup[0]
            type = tup[1]
            abbr = tup[2] if len(tup) > 2 else None

            found = False
            if regs:
                for reg in regs:
                    if reg.name == name and reg.type == type:
                        found = True
                        break

            if not found:
                regs1 = regions(name=name, type=type)
                if regs1.hasone:
                    reg = regs1.last
                    if regs:
                        regs += reg
                    found = True
                    if not root:
                        root = reg

            if not found:
                reg = region()
                reg.name = name
                reg.type = type
                reg.abbreviation = abbr
                if regs:
                    regs += reg

                if not root:
                    root = reg

            regs = reg.regions

        root and root.save()
        return reg
        

    """ An instance of a geographical region. Geographical regions
    include postal codes, cities, counties, states, provinces,
    territories and countries. 

    This recursive entity. The parent-child relationship implies a
    _within_ relationship. That is to say: all regions are
    geographically within their parent. The inverse is also true: that
    all child regions are geographically within a given region.
    """

    # The direct child regions. Country regions will have state or
    # province regions.  City regions will have postal code regions, and
    # so on.
    regions = regions

    # TODO Automatically pluralize
    entities = regions

    # The main string representation of the region. For postal codes, it
    # will be the postal code itself, e.g., "86225". For countries, the
    # name will be the name of the country, e.g., "United States".
    name = str

    # A numeric code to indicate the region type 
    type = int

    abbreviation = str


class contactmechanism(orm.entity):
    """ An abstract class representing a mechanism through which a party
    or facility can be contacted. Subtypes include ``phone``, ``email``,
    ``address`` and so on.
    """

class phone(contactmechanism):
    """ Represents a phone number contact mechanism.
    """

    # The area code as defined by the North American Numbering Plan.
    # This should probably be None for phone numbers outside of North
    # America and the Caribean. NOTE many of the numbers within the 200,
    # 999 range are currently considered invalid. The should probably
    # result in `brokenrules` if given. See
    # https://en.wikipedia.org/wiki/List_of_North_American_Numbering_Plan_area_codes
    area = int, 200, 999

    # The phone number excluding the country code, area code and
    # extension. (See `party_contactmechanism` for `extension`.)
    line = str

class email(contactmechanism):
    address = str

class party_contactmechanism(orm.association):
    class roles:
        main = 0
        home = 1
        private = 2

    # The date range through which this contactmechanism applied to the
    # given ``party``.
    begin          =  datetime
    end            =  datetime

    # If True, indicates that the mechanism may be called for
    # solicitation purposes. If False, the mechanism may not be called
    # for solicitation purposes. It will default to `None` meaning that
    # no preference on solicitation has been given, which is
    # functionally equivalent to True.
    solicitations  =  bool
    
    # TODO Multiple comments should be made about the contact mechanism.
    # Ensure the `comment` entity can polymorphically record comments on
    # contactmechanism types

    # The line extension
    extension = str

    # The reflective association properties, i.e.,
    # party-to-contactmechanism
    party = party
    contactmechanism = contactmechanism

    # The purpose that the contactmechanism is currently being used by
    # the party. (Exmples: 'mobile', 'main fax', 'general',
    # 'headquarters', 'billing inquiries', 'sales office', 'central
    # internet address', 'service address', 'main office number', 'main
    # home number', 'secondary office number', 'work email address',
    # 'personal email address', 'main home address')
    role = int

class address(contactmechanism):
    """ A postal address.
    """

    # TODO Automatically pluralize
    entities = addresses

    # Address line 1
    address1 = str

    # Address line 2
    address2 = str

    # A reference to a geographical region. This will usually be a
    # postal code region from which the other regions (city, state,
    # etc.) may be obtained.
    regions = regions

    # Prosaic directions to the address

    # FIXME The following line results in an exception from MySQL:
    #     _mysql_exceptions.OperationalError: (1074, "Column length too
    #     big for column 'directions' (max = 16383); use BLOB or TEXT
    #     instead")
    #directions = str, 1, 65535
    directions = str, 1, 65536

class address_region(orm.association):
    """ An association between a postal address (``address``) and a
    geographic region (``region``).
    """
    address = address
    region = region

class party_address(orm.association):
    """ An association between a party (person or organization) and a
    postal address.
    """
    entities  =  party_addresses
    party     =  party
    address   =  address
    begin     =  datetime
    end       =  datetime

class party_party(orm.association):
    entities = party_parties
    subject  =  party
    object   =  party
    role     =  str
    begin    =  datetime
    end      =  datetime

    @classmethod
    def sibling(cls, per):
        pp = cls()
        pp.object = per
        pp.role = 'sibling'
        pp.begin = None
        pp.end = None
        return pp

    # TODO Write brokenrules @property that ensures valid roles are
    # selected (among other things)
