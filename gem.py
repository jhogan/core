# vim: set et ts=4 sw=4 fdm=marker

# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2019

import orm
from primative import datetime

class partytypes(orm.entities):
    pass

class partytype(orm.entity):
    pass

class parties(orm.entities):
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
    isicv4 = char, min=1, max=1

class organizations(parties):
    pass

class organization(party):
    """ Represents a group of people with a common purpose. Examples
    include schools, NGOs, clubs, corporations, departments, divisions,
    government agency and nonprofit organizanitions. More informal
    organizations may include teams, families, etc.
    """
    name = str


class persons(parties):
    pass

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

class partyclassifications(orm.associations):
    pass

class partyclassification(orm.association):
    partytype  =  partytype
    party      =  party
    from       =  datetime
    to         =  datetime
