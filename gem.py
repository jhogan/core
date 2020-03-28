# vim: set et ts=4 sw=4 fdm=marker

# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2019

# TODO Checkout http://wiki.goodrelations-vocabulary.org/Quickstart for
# an standard for ecommerce markup when marking up parties, places, etc.

# TODO Rename this to 'party.py'

# TODO Put GEM entities in /gem folder. 

# TODO Prefix table names with name of module:
#
#     party__party
#     party__organization
#     product__product
#     product__category

# References:
#   
#   HR Glossary
#   This can be useful for discovering nouns that could become ORM
#   entity objects. It can also help refine current HR related GEM
#   objects.
#   https://www.hr360.com/Resource-Center/HR-Terms.aspx

import orm
import primative
from datetime import datetime
from dbg import B

''' Parties '''
class parties(orm.entities):
    pass

class organizations(parties):
    pass

class legalorganizations(organizations):
    pass

class companies(legalorganizations):
    pass

class units(organizations):
    pass

class departments(units):
    pass

class divisions(units):
    pass

class jobs(orm.entities):
    pass

class positions(orm.entities):
    pass

class position_fulfillments(orm.associations):
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

''' Parties '''
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

class unit(organization):
    """ This abstract class represents business unit of a
    legalorganization. Concrete subclass include `division` and
    `department`
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Units wouldn't have these so nullify them to prevent
        # brokenrules.
        self.dun          =  None
        self.nationalids  =  None
        self.isicv4       =  None

class division(unit):
    positions = positions

class job(orm.entity):
    """ Maintains information associated the actual `positions` an
    employee may take. 
    
    Note that in the "The Data Model Resource Book", this entity is
    refered to as the POSTITION_TYPE entity. "job" was chosen for its
    name since "job" is only one word and "POSTITION_TYPE" is obviously
    two words.
    """
    title = str
    description = str, 1, 65535
    
    # The below was noted in the book but is currently not implemented.
    # benefit_percentage = dec

    # A collection of positions generated from this job
    positions = positions

class position(orm.entity):
    """ A position is a job slot in an enterprise. 
    """

    # The datetime an organization expects the job to begin
    estimatedbegan = datetime

    # The datetime an organization expects the job to end
    estimatedend = datetime

    # The actual datetime the position slot is filled by an employee
    begin = datetime

    # The actual datetime the position slot is terminated
    end = datetime

    salary = bool

    fulltime = bool

class department(unit):
    divisions = divisions

class legalorganization(organization):
    # The Employer Identification Number (EIN), also known as the
    # Federal Employer Identification Number (FEIN) or the Federal Tax
    # Identification Number, is a unique nine-digit number assigned by
    # the Internal Revenue Service (IRS) to business entities operating
    # in the United States for the purposes of identification. 

    # NOTE This will need to be it's own entity object since EINs are
    # specific to the USA.
    ein = str, 9, 9

    # A collection of job positions the legalorganization has.
    positions = positions
    
class company(legalorganization):
    entities = companies
    departments = departments

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

class position_fulfillment(orm.association):
    """
    The `position_fulfilments` association links a position to a person.
    When a postion is associatied with a person, the position is said to
    be "fulfilled', i.e., the person has been employed by the
    organization (i.e., company) to fulfill the job duties of the
    position.

    Since this is an `orm.association`, multiple person entities can be
    associated with a given position. Different person entities may be
    associated to the same position over time. This allows for the
    tracking persons who occupied a given position in an organization
    over various timespans.  The begin and end dates record the
    occupation's timespan.
    
    Additionally, multiple persons can be associated to the same
    `position` within the same timespan implying that the persons
    occupy the position as part-time or half-time employees.
    """

    person    =  person
    position  =  position
    begin     =  datetime
    end       =  datetime

class region(orm.entity):
    # NOTE These values are fixed numeric codes that are saved to the
    # database. They should never be changed for an existing production
    # environment.
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
        # expression "default 'abbreviation' to None" a bit cryptic and
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

    @property
    def country(self):
        if self.type == self.Country:
            return self

        for an in self.ancestors:
            if an.type == self.Country:
                return an

        return None

    @property
    def ancestors(self):
        rent = self.region
        while rent:
            yield rent
            rent = rent.region

    def __str__(self):
        # NOTE The following may be a good reference to format regions
        # as well as addresses: https://en.wikipedia.org/wiki/Address

        args = dict()
        for an in self.ancestors:
            if an.type == self.City:
                args['city'] = an.name
            elif an.type == self.State:
                args['state'] = an.name
            elif an.type == self.Country:
                args['country'] = an.name

        if self.type == self.PostalCode:
            args['zip'] = self.name
            if args['country'] == 'United States of America':
                fmt = '{city}, {state} {zip}\n{country}'
            else:
                raise NotImplementedError()
        else:
            raise NotImplementedError()

        return fmt.format(**args)

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

    def __str__(self):
        ars = self.address_regions
        reg = ars.first.region if ars.count else None

        if reg and reg.country:
            if reg.country.name == 'United States of America':
                fmt = '{line1}{line2}{region}'
            else:
                raise NotImplementedError()
        else:
            raise NotImplementedError()

        args = dict()
        args['line1'] = self.address1
        if self.address2:
            args['line2'] = '\n' + self.address2
        else:
            args['line2'] = str()

        if reg:
            args['region'] = '\n' + str(reg)
        else:
            args['region'] = str()

        return fmt.format(**args)

    # TODO Enfore rule that an address can be associated with only one
    # address.

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

