# vim: set et ts=4 sw=4 fdm=marker

# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2019

# NOTE Checkout http://wiki.goodrelations-vocabulary.org/Quickstart for
# an standard for ecommerce markup when marking up parties, places, etc.

# References:
#   
#   HR Glossary
#   This can be useful for discovering nouns that could become ORM
#   entity objects. It can also help refine current HR related GEM
#   objects.
#   https://www.hr360.com/Resource-Center/HR-Terms.aspx

from datetime import datetime
from dbg import B
from decimal import Decimal as dec
from orm import text, datespan, timespan
import apriori
import asset
import builtins
import hashlib
import orm
import os
import primative

''' Parties '''

''' orm.entities classes '''
class users(orm.entities):                                   pass
class parties(orm.entities):                                 pass
class types(apriori.types):                                  pass
class roles(orm.entities):                                   pass
class workers(roles):                                        pass
class employees(workers):                                    pass
class contractors(workers):                                  pass
class role_role_types(apriori.types):                        pass
class statuses(orm.entities):                                pass
class role_role_statuses(statuses):                          pass
class priorities(orm.entities):                              pass
class role_roles(orm.associations):                          pass
class personals(roles):                                      pass
class organizationals(roles):                                pass
class suppliers(organizationals):                            pass
class organizationalunits(organizationals):                  pass
class internals(organizationals):                            pass
class subsidiaries(organizationalunits):                     pass
class parents(organizationalunits):                          pass
class roletypes(apriori.types):                              pass
class partyroletypes(roletypes):                             pass

# FIXME This is a duplicate of a previously declared classe
class employees(personals):                                  pass
class customers(personals):                                  pass
class billtos(customers):                                    pass
class placings(customers):                                   pass
class placingbuyers(customers):                              pass
class billtopurchasers(customers):                           pass
class shiptobuyers(customers):                               pass
class shiptos(customers):                                    pass
class party_types(orm.associations):                         pass
class organizations(parties):                                pass
class legalorganizations(organizations):                     pass
class companies(legalorganizations):                         pass
class units(organizations):                                  pass
class departments(units):                                    pass
class divisions(units):                                      pass
class jobs(orm.entities):                                    pass
class party_parties(orm.associations):                       pass
class party_addresses(orm.associations):                     pass
class maritals(parties):                                     pass
class names(parties):                                        pass
class genders(parties):                                      pass
class gendertypes(apriori.types):                            pass
class characteristics(parties):                              pass
class characteristictypes(apriori.types):                    pass
class nametypes(apriori.types):                              pass
class persons(parties):                                      pass
class address_regions(orm.associations):                     pass
class regions(orm.entities):                                 pass
class passports(orm.entities):                               pass
class citizenships(orm.entities):                            pass
class contactmechanism_contactmechanisms(orm.associations):  pass
class contactmechanisms(orm.entities):                       pass
class phones(contactmechanisms):                             pass
class emails(contactmechanisms):                             pass
class websites(contactmechanisms):                           pass
class party_contactmechanisms(orm.associations):             pass
class purposes(orm.entities):                                pass
class purposetypes(apriori.types):                           pass
class addresses(contactmechanisms):                          pass
class facilities(orm.entities):                              pass
class facilityroletypes(apriori.types):                      pass
class facility_contactmechanisms(orm.associations):          pass
class party_facilities(orm.entities):                        pass
class objectives(orm.entities):                              pass
class objectivetypes(apriori.types):                         pass
class communications(orm.entities):                          pass
class party_communications(orm.associations):                pass
class inpersons(communications):                             pass
class webinars(communications):                              pass
class phonecalls(communications):                            pass
class communicationroletypes(roletypes):                     pass
class communicationstatuses(statuses):                       pass
class efforts(orm.entities):                                 pass
class cases(orm.entities):                                   pass
class case_parties(orm.associations):                        pass
class caseroletypes(roletypes):                              pass
class casestatuses(statuses):                                pass
class communication_efforts(orm.associations):               pass
class skills(orm.entities):                                  pass
class skilltypes(apriori.types):                             pass
class rates(orm.entities):                                   pass
class ratetypes(apriori.types):                              pass
class asset_parties(orm.associations):                       pass
class asset_partystatustypes(apriori.types):                 pass

''' Parties '''

class user(orm.entity):
    name     =  str
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._password = None

    @orm.attr(bytes, 16, 16)
    def salt(self):
        self._sethash()
        return attr()

    @orm.attr(bytes, 32, 32)
    def hash(self):
        self._sethash()
        return attr()

    def _sethash(self):
        hash = self.orm.mappings['hash']
        salt = self.orm.mappings['salt']

        if hash.value and salt.value:
            return

        hash.value, salt.value = self._gethash()

    def _gethash(self, pwd=None):
        if not pwd:
            pwd = self.password

        if not pwd:
            return None, None

        salt = self.orm.mappings['salt'].value

        if not salt:
            salt = os.urandom(16)

        pwd  = bytes(pwd, 'utf-8')
        algo = 'sha256'
        iter = 100000
        fn   = hashlib.pbkdf2_hmac

        hash = fn(algo, pwd, salt, iter)
        return hash, salt

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, v):
        self.hash = self.salt = None
        self._password = v

    def ispassword(self, pwd):
        # Ensure self._salt is set so _gethash doesn't make one up
        self._sethash()
        hash, _ = self._gethash(pwd)
        return hash == self.hash

    @staticmethod
    def authenticate(name, password):
        usrs = users(name=name)
        if usrs.hasplurality:
            raise ValueError('Multiple users found')

        if usrs.hasone:
            usr = usrs.first
            if usr.ispassword(password):
                return usr

        return None

class party(orm.entity):
    """ ``party`` is the abstract class under which two important classes
    exists: ``organization`` and ``person``. 
    
    This class contains the common data types between organizations and
    persons. These include such data as credit ratings, addresses, phone
    numbers, fax numbers, email addresses etc. 
    
    Organization and people can also be parties to contracts, buyers,
    sellers, responsible parties, or members of other organizations. For
    example, membership organizations (like a computer users group) may
    keep similar information on their corporate members and their
    individual members.  Contracts can usually specify an organization
    or a person as a contracted party. The customer for a sales order
    may be either an organization or a person.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.orm.default('nationalids', None)
        self.orm.default('isicv4', None)
        self.orm.default('dun', None)

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

    # A collection of party roles this party plays.
    roles = roles

    # A collection of skills belonging to this party
    skills = skills

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
    pass

class department(unit):
    # TODO:afa4ffc9 Now that we are using role_role to associates
    # parties with each other, the entity objects `divisions` will no
    # longer have a many-to-one relationship with `department`;
    # `departments` will have a relationships with `divisions`.
	pass

class legalorganization(organization):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.orm.default('ein', None)

    # The Employer Identification Number (EIN), also known as the
    # Federal Employer Identification Number (FEIN) or the Federal Tax
    # Identification Number, is a unique nine-digit number assigned by
    # the Internal Revenue Service (IRS) to business entities operating
    # in the United States for the purposes of identification. 

    # NOTE This will need to be it's own entity object since EINs are
    # specific to the USA.
    ein = str, 9, 9

class company(legalorganization):
    """ A business entity that conducts a value of exchange of goods or
    services with customers. The end goal of a company is to produce a
    profit.
    """

    # NOTE that in "The Data Model Resource Book", this entity is
    # called CORPORATION. However, a corporation may actually be a
    # subtype of company since all corporations are companies but not
    # all companies are corporations. See the following link for the
    # differences between companies and corporations:
    # https://www.upcounsel.com/difference-between-corporation-and-company

    # TODO:afa4ffc9 Now that we are using role_role to associates
    # parties with each other, the entity objects `department` will no
    # longer have a many-to-one relationship with `company`; `persons`
    # will have an `employee` relationships with `departments` and
    # `divisons`.
    departments = departments

class marital(orm.entity):
    """ Allowes for the maintenence of changes to a person's marital
    status.

    Note that this entity is based on the MARITAL STATUS entity in "The
    Data Model Resource Book".
    """

    # Type constants. NOTE Do not change the value of these constants
    # since they are meaningful to existing database entries.
    Single     =  0
    Married    =  1
    Divorced   =  2
    Seperated  =  3
    Widowed    =  4

    # A datespan for when the marital status is valid.
    vaild = datespan

    # The type of marital status. See constants above.
    type = int

class name(orm.entity):
    """ The name entity stores a person's name and the time period
    during which it is valid.

    Note that this is modeled after the PERSON NAME entity in "The Data
    Model Resource Book".
    """

    # The datespan during which the person's name is vaild
    valid = datespan

    # A portion (first, middle, last) of the person's name. Which
    # portion of the name will be determined by the nametype composite.
    name  = str

    # The name of the group that this name belongs to. Typically, this
    # will just be 'default', however, there are some other situations
    # that might require a group to be named. For example, an English
    # database might want Sigmund Freud's default name to be "Sigmund
    # Freud" while preservings the name he was born with as "née".
    #
    #  name       type    metanym  begin  end
    #  ----       ----    -------  -----  ---
    #  Sigismund  first   née      1853   1939
    #  Schlomo    second  née      1853   1939
    #  Freud      third   née      1853   1939
    #  Sigmund    first   default  1938   1939
    #  Freud      second  default  1938   1939
    metanym = str

class gender(orm.entity):
    """ Maintains a history of gender identification a person has
    chosen.
    """

    # The span of time this gender was assigend to a person
    assigned = datespan

class gendertype(apriori.type):
    # A collection of genders corresponding to this type
    genders = genders

class characteristic(orm.entity):
    """ Provides a means to store the history of a person's physical
    charcteristics such as height and weight. This history is also
    useful in the health-related fields. The details of each
    characteristic are stored in the ``characteristictype`` composite
    which could have `name`s such as "height", "weight", "blood
    preasure" and so on.

    Note that this entity is based on the PHYSICAL CHARACTERISTIC entity
    in "The Data Model Resource Book".
    """

    # A timespan indicating when the characteristic is valid
    valid = timespan

    # Maintains the characteristic's measurement such as a height of
    # 6'1.
    value = str

class characteristictype(apriori.type):
    """ The details of a characteristic are stored here.   The ``name``
    of the characteristic would include values such as "height",
    "weight' or "blood preasure".

    Note that this entity is based on the PHYSICAL CHARACTERISTIC TYPE
    entity in "The Data Model Resource Book".
    """

    # A collection of characteristics matich this type
    characteristics = characteristics

class nametype(apriori.type):
    """ This entity maintains the type of name stored in the ``name``
    class. Typical types of names include 'first', 'middle', 'last',
    'prefix', 'suffix', 'nickname', etc.
    """

    # The collection of `name` entity objects that are assigned this
    # name type.
    names = names

class person(party):
    """ A ``person``, like an ``organization``, is a subtype of
    ``party``. 
    
    Persons are usually considered individuals of the homo sapien
    species, but the more general definition of "person" may be more
    appropriate for this entity::
    
        A being that has certain capacities or attributes such as
        reason, morality, consciousness or self-consciousness, and being
        a part of a culturally established form of social relations such
        as kinship, ownership of property, or legal responsibility

        - Wikipedia

    This would include other species of animals makeing the ``person``
    suitable for veterinarian patients, inmates of an animal shelter,
    etc.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for prop in ('maiden', 'comment', 'social'):
            self.orm.default(prop, None)

    # The person's birth date
    birthedat = datetime

    # The person's mother's maiden name
    maiden = str

    # The person's social security number
    social = str

    # A comment on the person.
    comment = text

    # A collection of names associate with this person.
    names = names

    # TODO:1e4db655 Add a name property that results in the first and
    # last name being accessed or mutated.
    #
    #     self.name = 'John Smith'
    # 
    #     assert self.name == 'John Smith'
    #     assert self.first == 'John'
    #     assert self.last == 'Smith'
    @property
    def first(self):
        """ Get first name of the person.
        """

        # NOTE See self._getname() for more information

        name = self._getname('first')
        return name.name if name else None

    @first.setter
    def first(self, v):
        """ Set first name of the person.
        """

        self._setname(v, 'first')

    @property
    def middle(self):
        """ Get middle name of the person.
        """
        # NOTE See self._getname() for more information

        name = self._getname('middle')
        return name.name if name else None

    @middle.setter
    def middle(self, v):
        """ Set middle name of the person.
        """

        self._setname(v, 'middle')

    @property
    def last(self):
        """ Get last name of the person.
        """
        # NOTE See self._getname() for more information

        name = self._getname('last')
        return name.name if name else None

    @last.setter
    def last(self, v):
        """ Set last name of the person.
        """

        self._setname(v, 'last')

    def _getname(self, ord):
        """ Get the name given an ordinal (``ord``) such as ``first``,
        ``middle``, `last``.
        """

        now = primative.datetime.utcnow()

        for name in self.names:
            nt = name.nametype
            if nt.name == ord and \
                (name.begin is None or name.begin >= now) and \
                (name.end   is None or name.end   <= now) and \
                name.metanym == 'default':
                return name

        return None

    def _setname(self, v, ord):
        type = nametype(name=ord)
        for n in self.names:
            if n.nametype.id == type.id:
                n.name = v
                break
        else:
            self.names += name(name=v)
            self.names.last.nametype = type
            self.names.last.metanym = 'default'

    # A collection of citizenship history entity objcets for this
    # person.
    citizenships = citizenships

    # A collection of physical characteristics for this person.
    characteristics = characteristics

    # A collection of marital history
    maritals = maritals

    # A collection of gender history
    genders = genders

    @property
    def gender(self):
        gen = self._getgender()
        if gen:
            return gen.gendertype.name

        return None

    @gender.setter
    def gender(self, v):
        gen = self._getgender()

        gts = gendertypes(name=v)

        if gts.isempty:
            raise ValueError('Gender type not found: "%s"' % v)

        gt = gts.first

        if gen:
            # NOTE:7f6906fc Changing the composite (gendertype) does not
            # dirty the gen's collection (self.genders), so we have to
            # call save() here. Not sure if this is a serious bug.
            gen.gendertype = gt
            gen.save()
        else:
            gen = gender()
            gen.gendertype = gt
            self.genders += gen

    def _getgender(self):
        now = primative.datetime.utcnow()
        for gen in self.genders:
            # No date has been assigned so we will assume this is the
            # default.
            if gen.begin is None and gen.end is None:
                return gen

            if gen.begin <= now and \
               (gen.end is None or gen.end >= now):
                return gen

        return None

class region(orm.entity):
    """ This class represents geographical regions such as a postal code,
    city, state, province, territory or country. It is a recurive
    entity meaning that, for example, that a postal code entry will
    have a parent that is a city entry. The city entry will have a
    parent state entry and so on.
    
    Note that this entity is based on the GEOGRAPHIC BOUNDRY entity in
    "The Data Model Resource Book".
    """

    # NOTE These values are fixed numeric codes that are saved to the
    # database. They should never be changed for an existing production
    # environment.
    Postal        =  0  # Postal code/zip code
    County        =  1
    City          =  2
    State         =  3
    District      =  4
    Municipality  =  5
    Province      =  6
    Territory     =  7
    Country       =  8

    def __init__(self, *args, **kwargs):
        # TODO The constructor should be rewritten so that it is modeled
        # after product.rating. The constructor should check to see if
        # the requested region is in the database already. If it's not,
        # the region should be saved by the constructor. If it is, the
        # constuctor should initialize the objects properties to the one
        # found in the database. The static `create` method should be
        # refactored to work within the constructor. Note that this
        # patter seems has emerged a second time already. There should
        # probably be a method call orm.ensure() that the constructor
        # can call to perform these steps.

        super().__init__(*args, **kwargs)
        self.orm.default('abbreviation', None)
                
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

    def __contains__(self, other):
        # TODO Should orm.entities.__contains__ go by the entity's id
        # such that the following would work:
        #
        #     return self in regions(initial=self + self.ancestry)

        return other.id in [x.id for x in self + self.descendents]

    @property
    def ancestry(self):
        """ Return a collection of regions that are the lineage of
        `self` starting with `self`'s parent, then grandparent, and so
        on.
        """

        # TODO:d45c34a0 These methods should be automatically available
        # for any recursive entity.
        regs = regions()
        
        reg = self.region

        while reg:
            regs += reg
            reg = reg.region

        return regs

    @property
    def descendents(self):
        """ Return a collection of regions that are the descendents of
        `self` starting with `self`'s childre, the children these
        children, and so on.
        """

        # TODO:d45c34a0 These methods should be automatically available
        # for any recursive entity.
        r = regions()

        def recurse(reg):
            nonlocal r

            regs = reg.regions
            if regs.count:
                r += regs
                for reg in regs:
                    recurse(reg)
            else:
                return

        recurse(self)

        return r


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

        if self.type == self.Postal:
            args['zip'] = self.name
            if args['country'] == 'United States of America':
                fmt = '{city}, {state} {zip}\n{country}'
            else:
                raise NotImplementedError()
        else:
            raise NotImplementedError()

        return fmt.format(**args)

class passport(orm.entity):
    """ A passport ussued within a `citizinship` entity for a `person`
    """

    # The number of the passport
    number = str

    # The date the passport was issued at
    issuedat = datetime

    # The date the passport expires
    expiresat = datetime

class citizenship(orm.entity):
    """ Indicates citizenship to a particular country. 
    """

    # The datespan for when this citizenship is valid
    vaild = datespan

    # TODO Add validaton logic to ensure the region is a country.
    # The country that the citizenship is for. Note this is a `region`
    # which must have a `type` of Country.
    country = region

    # A collection of passports issued for this citizenship
    passports = passports

class contactmechanism(orm.entity):
    """ An abstract class representing a mechanism through which a party
    or facility can be contacted. Subtypes include ``phone``, ``email``,
    ``address`` and so on.

    Note that this is modeled after the CONTACT MECHANISM entity in "The
    Data Model Resource Book".
    """

class contactmechanism_contactmechanism(orm.association):
    # TODO Write docstring

    # Constants for `event`
    Busy        =  0
    Unanswered  =  1

    # Constants for `do`
    Forward = 0

    on       =  int
    do       =  int
    subject  =  contactmechanism
    object   =  contactmechanism

class phone(contactmechanism):
    """ In addition to phones, this contact mechanism includes any access via
    telecommunications lines such as fax machines, modems and pagers.

    Note that this is modeled after the TELECOMMUNICATIONS NUMBER entity
    in "The Data Model Resource Book".
    """

    # The area code as defined by the North American Numbering Plan.
    # This should probably be None for phone numbers outside of North
    # America and the Caribean. NOTE many of the numbers within the 200,
    # 999 range are currently considered invalid. They should probably
    # result in `brokenrules` if given. See
    # https://en.wikipedia.org/wiki/List_of_North_American_Numbering_Plan_area_codes
    area = int, 200, 999

    # The phone number excluding the country code, area code and
    # extension. (See `party_contactmechanism` for `extension`.)
    line = str

class website(contactmechanism):
    """ Represents a website as a contact.
    """
    url = str

class email(contactmechanism):
    """ Represents a email address contact mechanism.

    Note that this is modeled after the ELECTRONIC ADDRESS entity in
    "The Data Model Resource Book".
    """
    address = str

class communication(orm.entity):
    """ An object to record any type of contact between parties within a
    relationship (see `role_role`). For example, phone calls, meetings,
    emails, and so on.

    Note that this is modeled after the COMMUNICATION EVENT entity in
    "The Data Model Resource Book".
    """

    # NOTE Unlike most begin/end pairs, these should actually be
    # datetime; not date types since we are tracking the exact time of
    # day a communication should happen.

    # The timespan that the communication event took place
    span = timespan

    # Notes about the communication event
    note  = text

class party_contactmechanism(orm.association):
    """ This class associates a party with a contact mechanism. It shows
    which contact mechanisms are related to which parties.

    Note that this is modeled after the PARTY CONTACT MECHANISM entity
    in "The Data Model Resource Book".
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.orm.default('extension', None)

    # TODO These should probably just be constants.
    class roles:
        main = 0
        home = 1
        private = 2

    # The date range through which this contactmechanism applied to the
    # given ``party``.
    span = datespan

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

    # NOTE According to the book, a PARTY CONTACT MACHANISM must have
    # one or more PARTY CONTACT MECHANISM PURPOSEs. I would have thought
    # it would be zero or more. We may want to consider creating a
    # validation rule to ensure that one `purpose` has been added for each
    # party_contactmechanism.

    # The collection of purposes that this association between `party`
    # and `contactmechanism` have.
    purposes = purposes

class purpose(orm.entity):
    """ Each contact mechanism for each party may have many purposes.
    For instance, an address might be used as a mailing address, a
    headquarters address, a service addresss, and so on.  People
    sometimes have a single number for both their phone and fax needs. 

    This class is on the many-side of a one-to-many relationship with
    party_contactmechanism, allowing one or more purposes to be assigend
    to each party_contactmechanism association.

    Note this class only store the datespan to indicate when the purpose
    is vaild. The ``purposetype`` entity has a ``name`` attribute
    providing human-readable information about the actual purpose.

    Note that this is modeled after the PARTY CONTACT MECHANISM PURPOSE
    entity in "The Data Model Resource Book".
    """
    span = datespan

class purposetype(apriori.type):
    """ ``purposetype`` has a one-to-many relationship with ``purpose``.
    The ``purposetype`` class allows for the ability to describe the
    purpose of contact mechanism purposes (``purpose``).
    """

    # The purposes that match this purposetype.
    purposes = purposes

class address(contactmechanism):
    """ Maintains all postal addresses used by an enterprise.

    Note that this is modeled after the POSTAL ADDRESS entity in "The
    Data Model Resource Book".
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.orm.isnew:
            self.directions = None

    # TODO s/address(\d)/line\1/
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

    Note that this is modeled after the POSTAL ADDRESS BOUNDRY entity in
    "The Data Model Resource Book".
    """
    address = address
    region = region

class party_address(orm.association):
    """ An association between a party (person or organization) and a
    postal address.

    Note that this is modeled after the PARTY POSTAL ADDRESS entity in
    "The Data Model Resource Book".
    """
    entities  =  party_addresses
    party     =  party
    address   =  address
    span      =  datespan

class party_party(orm.association):
    subject  =  party
    object   =  party
    role     =  str

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.orm.default('role', None)

    span = datespan

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

class type(apriori.type):
    """ A type of party. Examples of party types include:
            Minority-owned business
            Manufacturer
            Woman-owned business
            Mail order firm
            Small organization
            Medium-sized organization
            Large organization
            Janitorial service organization
            8a organizations
            Service organization
            Marketing service prodived
            Hispanic
            African American
            Income classification
        
        A party can be classified by more than one type so the
        party_type association is used.

        Note that this is modeled after the PARTY TYPE entity in "The
        Data Model Resource Book".
    """
    # TODO I think there should be a `parties = parties` line here


class classification:
    """ ``party`` entity objects are classifiend into various categories
    using the ``classification`` entity, which stores each category into
    which parties may belong.

    Note that this is modeled after the PARTY CLASSIFICATION entity in
    "The Data Model Resource Book".
    """
    # TODO

class role(orm.entity):
    """ The role entity defines how a ``party`` acts or, in other words,
    what roles the party plays in the context of the enterprises's
    environment.

    Note that this is modeled after the PARTY ROLE entity in
    "The Data Model Resource Book".
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Each (party) role may be described by one and only one
        # `partyroletype`. TODO Write validation rule for this.
        name = builtins.type(self).__name__
        self.partyroletype = partyroletype(name=name)

    # The datespan through which this role is valid. This timespan may
    # be optional because many of the timeframes for the roles will be
    # dependent on (and can be derived from) the (party) relationship. 
    span = datespan

class role_role_type(apriori.type):
    """ Describe the type of relationship a role_role association
    declares.

    Note that this is modeled after the PARTY RELATIONSHIP TYPE entity
    in "The Data Model Resource Book".
    """

    # Describes in more detail the meaning behind this type of
    # relationship. For example, assuming the the `name` attribute is
    # "customer relationship", the `description` might be "where the
    # customer has purchased or used purchasing products fro an internal
    # organization".
    description = text

# TODO Since ``status`` is a universal concept in data modeling, the
# main status class should probably go in the apriori.py file. The same
# may be true of ``statustype``
class status(orm.entity):
    """ Throughout the GEM, there are many statuses for many
    entity objects (e.g., orders status, shipment status, work effort
    status, and so on.). Each of these will be have their on subentity
    classes, e.g., ``party.role_role_status``.

    Note that this is modeled after the STATUS TYPE entity in "The Data
    Model Resource Book".
    """

    # NOTE Given that this abstract class can be used in many different
    # modules of the GEM, we may need to consider a centralized place
    # for these more "global" types. However, up to this moment, I have
    # not yet encountered another class that would require this type of
    # centralization.

class role_role_status(status):
    """ Defines the current state of the role-to-role relationship
    (`role_role``).  Examples include "active", "inactive", or
    "pursueing more involvement".
    
    Note that this is modeled after the PARTY RELATIONSHIP STATUS TYPE
    entity in "The Data Model Resource Book".
    """

    entities = role_role_statuses

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.orm.ensure(expects=('name',), **kwargs)

    # FIXME:167d775b:28a4a305. The class wants to have a one-to-many
    # relationship on the role_role association, however that
    # relationship type is not currently supported. 
    name = str

class priority(orm.entity):
    """ The ``priority`` entity establishesh the relative importance of
    a party relationship (a ``role_role`` entry) to the organization
    that owns the ``role_role`` entity. Examples may include "very
    high", "high", "medium" and "low".

    Note that this is modeled after the PRIORITY TYPE entity in "The
    Data Model Resource Book".
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.orm.ensure(expects=('name',), **kwargs)

    name = str

    # FIXME:167d775b:28a4a305. The class wants to have a one-to-many
    # relationship on the role_role association, however that
    # relationship type is not currently supported. 

    ordinal = int

class role_role(orm.association):
    """ This class associates a party's role with the role of another
    party. This association allows a party to be related to other
    parties and maintains the respective roles in the relationship.

    This association has a role_role_type composite that describes the
    type of role-to-role association being declared.

    The grammar of this association can be understood with the following
    example:
    
        The ``company`` "ABC Subsidiary" has a ``role`` called
        "Subsidiary".  That role is the ``subject`` of a ``role_role``
        association. In that association, the ``object`` attribute
        references a ``role`` called "Parent Corporation" which belongs
        to "ABC Corporation". 

        To put it in plainer English: ABC Subsidiary has a subsidiary
        role that is associated with ABC Corporation's Parent
        Corporation role, i.e., ABC Subsidiary is the subsidiary of ABC
        Corporation.

    Note that this is modeled after the PARTY RELATIONSHIP entity in
    "The Data Model Resource Book".
    """

    # A timespan to indicate when the relationship between roles are
    # valid.
    vaild = datespan

    # The subjective role. 
    subject = role

    # The objective role
    object  = role

    # The type of the role_role relationship. 

    # FIXME Normally, we would create an attribute called
    # `role_role_type.role_roles` to achieve this same relationship.
    # However, currently one-to-many relationships are not supported
    # between entity objects and association objects. When they are
    # supported, we can make the appropriate corrections. See FIXME
    # 167d775b and 28a4a305.
    role_role_type = role_role_type

    # FIXME As with the role_role_type composite above, we would prefer
    # to have the `priority` class have constituents of role_roles
    # declared to achieve the below composite implitely.
    priority = priority

    # FIXME See the FIXMEs for `priority` and `role_role_type`. The
    # same problem exists for `role_role_status`
    status = role_role_status

    communications = communications

class personal(role):
    """ A personal role is a role that a person plays with other
    ``party`` entity object. Subtypes of ``personal`` include
    ``employee`, ``contractor``, ``familial`` and ``contact``.

    Note that this is modeled after the PERSON ROLE entity in
    "The Data Model Resource Book".
    """

class organizational(role):
    """ Like the ``personal(role)`` entity object, the
    organization(role) entity has several subtype roles such as
    (distribution) ``channel``, ``partner``, ``competitor``,
    ``household`, (regulatory) ``agency``, ``supplier`` and
    ``association``.

    Note that this is modeled after the ORGANIZATION ROLE entity in "The
    Data Model Resource Book".
    """

class supplier(organizational):
    """ A supplier(organizational(role)) implies the role of a supplier
    -- an enterprise tha may or does provide products (goods and/or
    services) to an enterprise.

    `suppliers` are the party role that takes purchase orders (see
    `order.purchaseorder`.
    """

class organizationalunit(organizational):
    """ An organizational unit identifies the form of an organization
    and is useful to identify parts of organization as well as
    maintenance of organizational structure. This role may be further
    subtyped as parent organization, subsidiary, departement, division,
    or other organization units to cover more unique types of
    organizations as well as maintenance of organizational structure..
    """

class internal(organizational):
    """ The internal organizational role.

    Note that this entity was originally called INTERNAL ORGANIZATION in "The
    Data Model Resource Book".
    """

class subsidiary(organizationalunit):
    """ An organizational unit role a company plays to indicate that
    they are owned by a parent organization.
    """

class parent(organizationalunit):
    """ An organizational unit role a company plays to indicate that
    the organization ownes a subsidiary (see the 
    ``subsidiary(organizationalunit)`` entity).
    """

class worker(personal):
    """ Represents the role of anyone who performs work. May be an
    ``employee`` or ``contractor``.
    """

class employee(worker):
    """ A party role implying legal employment with an enterprise.
    """

class contractor(worker):
    """ A worker role implying a contractor.
    """


# TODO Add subtypes of ``organizational``: (distribution) ``channel``,
# ``partner``, ``competitor``, ``household`, (regulatory) ``agency`` and
# ``association``.

# TODO Since roletype is used as a base class in many other places in
# the GEM, we may consider moving it to apriori.py.
class roletype(apriori.type):
    """ Stores a name for a role type.

    Note that this is modeled after the ROLE TYPE entity in "The
    Data Model Resource Book".
    """

class partyroletype(roletype):
    """ Each party role (the classes that inherit from ``party.role``)
    may be described by one and only one ``partyroletype``.  The
    ``partyroletype`` inherits from ``roletype`` and has an ``name``
    that stores available values of role types.

    Note that this is modeled after the PARTY ROLE TYPE entity in "The
    Data Model Resource Book".
    """

    # TODO:ddfffc45
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.orm.ensure(expects=('name',), **kwargs)

    # FIXME:167d775b:28a4a305. The class wants to have a one-to-many
    # relationship on the party_contactmechanisms association, however
    # that relationship type is not currently supported. 
    # party_contactmechanisms = party_contactmechanisms

# TODO Add ``familial`` and ``contact`` subtypes to personal(role).

class customer(role):
    """ A role indicating a party that has purchased, been shipped, or
    used products from an enterprise. Subtypes of the customer role
    include ``billto`` (purchased), ``shipto`` (been shipped)  and
    ``enduser`` (used products).
    """

class billto(customer):
    """ A role indicating a party that has purchased a product from
    another party.

    Note that this entity was originally called BILL TO CUSTOMER in "The
    Data Model Resource Book".
    """ 
    entities = billtos


class placing(customer):
    """ A role indicating a party that has places an order to another
    party.

    Note that this entity was originally called PLACING CUSTOMER in "The
    Data Model Resource Book".
    """

class placingbuyer(customer):
    """ The placing buyer is the role a party plays when it places a
    purchase order.

    Note that this entity was originally called PLACING BUYER in "The
    Data Model Resource Book".
    """

class billtopurchaser(customer):
    """ The bill to purchaser is the role a party plays when it picks up
    the bill for a purchase order.

    Note that this entity was originally called BILL TO PURCHASER in
    "The Data Model Resource Book".
    """

class shiptobuyer(customer):
    """ The ship to buyer is the role a pary plays when it is intended
    to receive the purchase order.

    Note that this entity was originally called SHIP TO PURCHASER in
    "The Data Model Resource Book".
    """

class placingbuyer(customer):
    """ 

    Note that this entity was originally called PLACING BUYER in "The
    Data Model Resource Book".
    """

class shipto(customer):
    """ A role indicating a party that should recieve the order.

    Note that this entity was originally called SHIP TO CUSTOMER in "The
    Data Model Resource Book".
    """
    entities = shiptos

class party_type(orm.association):
    """ An association between `party` and `type`. 

    Note that this is modeled after the PARTY CLASSIFICATION entity in
    "The Data Model Resource Book".
    """

    # `begin` and `end` are used to track the history of the
    # classifaction over time. For example, a business may "graduate"
    # from 8A (minority startup) program.
    span = datespan

    # A reference to the party
    party  =  party

    # A reference to the party type (`party.type`)
    type   =  type

class facility(orm.entity):
    """ Provides a structure to record information about physical
    facilities. Type of facilities include warehouses, plants,
    buildings, floors, offices, room. 
    
    The class is recursive meaning that some entries will have a parent
    property that allows you to get the facility that the current
    facility is within. For example the parent of a *room* facility will
    be a *floor* facility. The *floor* facility will may have a
    *building* as its parent facility.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.orm.default('footage', None)
            
    # NOTE These values can't change because they are persisted to the
    # database.
    # Constants to describe the various types of facilities
    Warehouse  =  0
    Plant      =  1
    Factory    =  2
    Building   =  3
    Floor      =  4
    Office     =  5
    Room       =  6

    # The name of the facility
    name = str

    # The square footage of the facility
    footage = int

    # The type of facility. This field corresponst to the constants
    # defined above.
    type = int

    # A facility will have zero or more facilities within itself making
    # this a recursive entity. For example, a building may have multiple
    # `Floor` facilities and each of those `Floor` facilities may have
    # multiple `Room` facilities.
    facilities = facilities

    # TODO There should probably be brokenrules to ensure commonsense
    # notions such as: A `Room` may be within a `Floor`, but a `Floor`
    # may not be within a `Room`.

class facilityroletype(apriori.type):
    """ The role being played between a party and a facility. For
    instance, certain parties may *use* the facility, *lease* the
    facility, *rent* the faculity, or *own* the facility. This entity
    stores those possible values. It is used by the party_facility
    association.

    Note that this is modeled after the FACILITY ROLE TYPE entity in
    "The Data Model Resource Book".
    """

class facility_contactmechanism(orm.association):
    """ This class associates a facility with a contact mechanism. It shows
    which contact mechanisms are related to which facilities.

    Each ``facility`` may be contacted via one or more
    ``contactmechanisms``. A ``Plant`` facility may be contacted using
    several types of contact mechanisms such as phone, fax, email, postal
    address, and so on. The ``facility`` could have more than one of
    these ``contactmechanism``; for example, it may have a street postal
    address of 100 Smith Street and another of PO BOX 1234.

    Note that this is modeled after the FACILITY CONTACT MECHANISM entity
    in "The Data Model Resource Book".
    """

    # The facility being associated with a contact mechanism.
    facility = facility

    # The contact mechanism (phone, email, address, etc) being
    # associated with a facility.
    contactmechanism = contactmechanism

class party_facility(orm.association):
    """ Associates a ``party`` with a ``facility`` to indicate the role
    the party plays with the facility. The actual role is stored in the
    ``party_facility.facilityroletype`` entity.

    Note that this is modeled after the FACILITY ROLE entity in
    "The Data Model Resource Book".
    """

    # The party being associated to a facility
    party = party

    # The facility being associated to a party
    facility = facility

    # The role being played between the `party` and the `facility`

    # TODO When one-to-many relationships are supported for
    # associations, we should replace the following two lines with the
    # following modification to facilityroletype and party
    # respectively.
    #
    #     class facilityroletype
    #         party_facilities = party_facilities 
    #
    #     class party
    #         party_facilities = party_facilities 

    facilityroletype = facilityroletype

    party = party

class objective(orm.entity):
    """ The objective or purpose of a ``communication`` event.

    Note that this is modeled after the COMMUNICATION EVENT PURPOSE
    entity in "The Data Model Resource Book".
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.orm.default('name', None)

    # The name or description of the `communication`'s objective such as
    # "This is a critical sales call that must turn client around"
    name = str

class objectivetype(apriori.type):
    """ Indicates the ``communication``'s ``objective`` type.
    """

    objectives = objectives

class communication(orm.entity):
    """ This entity provides a history of the various communications
    that have been made or will be made between parties. It records
    the interchange of information between parties via some type of
    contact such as a phone call, meeting, videoconference, and so on.
    It may be within the context of a particular party relationship
    (``role_role``), or it may be between many parties in which case the
    ``party_communication`` is used to describe the roles of
    parties. For contact events that involve more than two parties (for
    instance , a meeting or seminar), ``party_communication`` may
    define the parties and the rolse they play with the event
    (facilitator, participant, note taker, etc.)

    Note that this is modeled after the COMMUNICATION EVENT entity in
    "The Data Model Resource Book".
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.orm.isnew:
            self.note = None

    # A timespan to indicate the duration of the communication. 
    duration = timespan

    # The `note` describes the contact. An example a note may be
    # "initial sales call went well and customer seemed interested in
    # moving forward quickly with a demonstration of the Thingamajig
    # product."
    note = text

    objectives = objectives

class inperson(communication):
    """ A type of a ``communication`` event where the communication
    happens face-to-face.

    Note that this is modeled after the FACE-TO-FACE COMMUNICATION
    entity in "The Data Model Resource Book".
    """

class webinar(communication):
    """ A type of a ``communication`` where a presentation or some other
    exchange of information can be delivered over a party's website.

    Note that this is modeled after the WEBSITE COMMUNICATION
    entity in "The Data Model Resource Book".
    """

class phonecall(communication):
    """ A type of a ``communication`` where the particants exchange
    information over a phone call.

    Note that this is modeled after the PHONE COMMUNICATION
    entity in "The Data Model Resource Book".
    """

class communicationroletype(roletype):
    """ Indicates the role that a party has in a ``communication``
    event.
    """

    # TODO This __init__ could probably be put in ``roletype``. Then we
    # could remove partyroletype.__init__ as well.
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.orm.ensure(expects=('name',), **kwargs)

    # FIXME:167d775b:28a4a305. The class wants to have a one-to-many
    # relationship on the ``party_communication`` association, however
    # that relationship type is not currently supported.
    # party_contactmechanisms = party_contactmechanisms

class party_communication(orm.association):
    """ When a ``communication`` is between multiple parties, the
    ``party_communication`` class is used to describe the roles of
    parties. It defines the parties and the roles they play with the
    event (facilitator, participant, note taker, etc.)

    Note that this is modeled after the COMMUNICATION EVENT ROLE entity
    in "The Data Model Resource Book".
    """

    party = party
    communication = communication
        
    # TODO:167d775b:28a4a305 We can remove this when these issues are
    # resolved
    communicationroletype = communicationroletype

class communicationstatus(status):
    """ The communicationstatus entity maintains the state of a
    ``communication`` event. Example statuses include "scheduled", "in
    progres", and "completed".

    Note that this is modeled after the COMMUNICATION EVENT STATUS TYPE
    entity in "The Data Model Resource Book".
    """

    # TODO:9247b532 The ``name`` attribute should be in ``status``, not
    # here.  Same for any other subclasses of ``status`` like
    # ``role_role_status``. Let's move that attribute and the __init__
    # below into ``status``.
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.orm.ensure(expects=('name',), **kwargs)

    name = str

    entities = communicationstatuses

    # The collection of ``communication`` events that have this status
    communications = communications

class effort(orm.entity):
    """ A work effort.

    Note that this is modeled after the WORK EFFORT entity in "The Data
    Model Resource Book".
    """
    # TODO This will need to be moved into the work effor module. This
    # may create a circular dependency issue with the party/party module
    # that will need to be resolved.
    name = str
    description = text

    # Scheduled begin and end date
    scheduled = datespan

    # Total dollars allowed
    dollars = int

    # Total hourse allowed
    hours = dec

    # Estimated hours
    estimate = dec

class case(orm.entity):
    """ A case collects a series of ``communication`` events regarding a
    particular issue.
    """

    # NOTE ``case`` and its subsideries may need to be moved into
    # the work effort module. Although, maybe not if it is mearly a
    # collection of ``communication`` events -- ``communication`` events
    # happy to be in the party module.
    
    # The description of the case
    description = text

    # The start datetime of the case
    # TODO Write a test to ensure that this remains a datetime and
    # doesn't become a date.
    begin = datetime

    # A collection of ``communication`` events corresponding to this
    # case.
    communications = communications

class casestatus(status):
    """ The status of a ``case``. There is a one-to-many relationship
    between a ``casestatus`` and a ``case``.

    Note that this is modeled after the CASE STATUS TYPE entity in "The
    Data Model Resource Book".
    """

    entities = casestatuses

    # TODO:9247b532 The ``name`` attribute should be in ``status``, not
    # here.  Same for any other subclasses of ``status`` like
    # ``role_role_status``. Let's move that attribute and the __init__
    # below into ``status``.
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.orm.ensure(expects=('name',), **kwargs)

    # The name of the status ('In Progress', 'Completed', etc)
    name = str

    # All the cases that that has this status status 
    cases = cases

class case_party(orm.association):
    """ Each ``case`` may have zero or more associations with ``party``
    entity to record the role a party has to the case such as: who is
    responsible for the ``case``, who checks the quality of service
    within the ``case``, who is the customer for the ``case`` and so on.
    Note that the  ``caseroletype`` entity stores the actual role that
    the ``party`` plays within a ``case``.

    Note that this is modeled after the CASE ROLE entity in "The Data
    ModeModel Resource Book".
    """

    # The case being associated to the party
    case = case

    # The party being associated to the case
    party = party

class caseroletype(roletype):
    """ ``caseroletype`` has a one-to-many relationship with
    ``case_party``.  It defines the role that the ``party`` is playing
    with regards to the ``case`` in ``case_party``.

    For example, Jerry Red may be playing the role of "resolution lead"
    to the ``case`` 68dceb32 while Joe Schmoe would be playing the role
    of "case customer" and Larry Assure would be playing the role of
    "quality assurance manager".
    """

    # TODO:ddfffc45 This __init__ should be moved to ``roletype``. The
    # same is true of ``partyroletype``.
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.orm.ensure(expects=('name',), **kwargs)

    # The collection of case_party associations that are assigned this
    # role type.
    case_parties = case_parties

class communication_effort(orm.association):
    """ An association between a ``communication`` event and a work
    ``effort``.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.orm.isnew:
            self.description = None

    # A note or description for the association 
    description = text

    # The effort being associated to the ``communication`` event
    effort = effort

    # The communication event being associated to the ``effort``
    communication = communication

class skill(orm.entity):
    """ A skill a party has along with the years of experience in that
    skill.

    Note that this entity was originally called SKILL in "The Data Model
    Resource Book" and was introduced in the Work Effort chapter rather
    than the People and Organizations chapter.
    """

    # The *years of experience* tells how many years that the person or
    # organization has been involved in this skill.
    years = dec

    # The rating indicates how proficient the party is in the skill.
    rating = dec

class skilltype(apriori.type):
    """ Describes the ``skill``.

    Note that this entity was originally called SKILL TYPE in
    "The Data Model Resource Book" and was introduced in the Work Effort
    chapter rather than the People and Organizations chapter.
    """

    # The collection of skills matching this skill type
    skills = skills

class rate(orm.entity):
    """ The ``rate`` entity may store a rate, overtime rate, cost, or
    other type of rate depending on the needs of the organization. The
    ``party.ratetype`` would indicate which rate is being specified. 

    Note that this is modeled after the WORK EFFORT ASSIGNMENT RATE
    entity in "The Data Model Resource Book".
    """
    span = datespan
    rate = dec

class ratetype(apriori.type):
    """ Provides the ability to classify the various types of rates to
    alllow the flexibility to capture different types of rates such as
    billing rates, payroll rates (amount that needs to be paid to the
    worker), costs, overtime rates, and so on.

    Regrading the ``name`` attribute a ``name`` of "biling rate"
    establishes how much is billed and whether it is to be billed to an
    external or internal organization. A ``name`` of "cost" determines
    how much will be used as the cost basis to calculate how much the
    work is costing.

    Note that this entity was originally called RATE TYPE in
    "The Data Model Resource Book" and was introduced in the Work Effort
    chapter rather than the People and Organizations chapter.
    """

    # The collection of rates matching this rates type
    rates = rates

class asset_party(orm.association):
    """ Represents the assignment or *checking out* of a fixed asset
    (``asset.asset``) to a ``party``.

    Note that this is modeled after the PARTY ASSET ASSIGNMENT
    TYPE entity in "The Data Model Resource Book".
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.orm.isnew:
            self.comment = None

    # The ``party`` side of the association.
    party = party

    # The ``asset`` side of the association.
    asset = asset.asset

    # The time frame for the assignment or check out 
    span = datespan

    # The allocated cost of the assignment
    cost = dec

    # A comment
    comment = text

class asset_partystatustype(apriori.type):
    """ Provides information about the assignment (``asset_party``) of a
    fixed asset (``asset.asset``) to a ``party.

    Note that this is modeled after the PARTY ASSET ASSIGN STATUS
    TYPE entity in "The Data Model Resource Book".
    """

    # The collection of asset-to-party assignments that this status type
    # represents.
    asset_parties = asset_parties

