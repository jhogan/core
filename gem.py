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

class parties(orm.entities):
    pass

class organizations(parties):
    pass

class party_addresses(orm.associations):
    pass

class persons(parties):
    pass

class address_regions(orm.associations):
    pass

class addresses(orm.entities):
    pass

class regions(orm.entities):
    pass

class party_contactmechanisms(orm.associations):
    pass

class contactmechanisms(orm.entities):
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
    """ Represents a group of people with a common purpose. Examples
    include schools, NGOs, clubs, corporations, departments, divisions,
    government agency and nonprofit organizanitions. More informal
    organizations may include teams, families, etc.
    """
    name = str

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
    Postalcode  =  0
    County      =  1
    City        =  2
    State       =  3
    Province    =  4
    Territory   =  5
    Country     =  6

    """ An instance of a geographical region. Geographical regions
    include postal codes, cities, counties, states, provinces,
    territories and countries. 

    This recursive entity. The parent-child relationship implies a
    _within_ relationship. That is to say: all regions are
    geographically within their parent. The inverse is also true: that
    all child regions are geographically within a given region.
    """
    # TODO Automatically pluralize
    entities = regions

    # The main string representation of the region. For postal codes, it
    # will be the postal code itself, e.g., "86225". For countries, the
    # name will be the name of the country, e.g., "United States".
    name = str

    # The direct child regions. Country regions will have state or
    # province regions.  City regions will have postal code regions, and
    # so on.
    regions = regions

    # A numeric code to indicate the region type 
    type = int

    abbreviation = str

class contactmechanism(orm.entity):
    pass

'''
class phone(contactmechanism):
    pass

class email(contactmechanism):
    pass

class party_contactmechanism(orm.association):
    party = part
    contactmechanism = contactmechanism

class address(orm.entity):
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
    directions = text

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

'''
