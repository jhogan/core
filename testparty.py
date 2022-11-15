#!/usr/bin/python3
# vim: set et ts=4 sw=4 fdm=marker

########################################################################
# Copyright (C) Jesse Hogan - All Rights Reserved                      #
# Unauthorized copying of this file, via any medium is strictly        #
# prohibited                                                           #
# Proprietary and confidential                                         #
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2022                 #
########################################################################

import apriori; apriori.model()

from func import enumerate
from dbg import B
import orm
import party
import primative
import tester
import ecommerce
import uuid
import bot
from uuid import uuid4, UUID
from random import randint

class party_(tester.tester):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        orm.security().override = True

        if self.rebuildtables:
            es = orm.orm.getentityclasses(includeassociations=True)
            for e in es:
                if e.__module__ in ('party', 'apriori', 'hr'):
                    e.orm.recreate()

    def it_calls_creatability(self):
        with orm.override(False):
            with orm.sudo():
                usr = ecommerce.user(name='creator')
                usr.save()

            with orm.su(usr):
                par = party.party(name='derp')
                self.expect(None, par.save)

            # TODO:a22826fe At this point it is unclear how
            # unauthenicated/anonymous users should be handled.
            return 
            with orm.su(None):
                par = party.party(name='derp')
                self.expect(orm.AuthorizationError, par.save)

    def it_calls_retrievability(self):
        with orm.override(False):
            with orm.sudo():
                par = party.party(name='derp')
                usr = ecommerce.user(name='creator')
                usr.party = par
                usr1 = ecommerce.user(name='other')
                usr.save(usr1)

            with orm.su(usr):
                self.expect(None, par.orm.reloaded)

            with orm.su(usr1):
                self.expect(orm.AuthorizationError, par.orm.reloaded)

    @staticmethod
    def getvalid(first=None, last=None):
        per = party.person()

        per.first = first if first else uuid4().hex
        per.middle = uuid4().hex
        per.last = last if last else uuid4().hex
        per.title          =  uuid4().hex
        per.suffix         =  uuid4().hex
        per.mothersmaiden  =  uuid4().hex
        per.maritalstatus  =  True
        per.nationalids    =  uuid4().hex
        per.isicv4         =  None
        per.dun            =  None
        return per

    def it_creates_public_party(self):
        pub = party.parties.public
        self.eq(party.parties.PublicId, pub.id)

        # Memoizes
        self.is_(party.parties.public, pub)

        # Persisted
        self.false(pub.orm.isnew)
        self.false(pub.orm.isdirty)
        self.false(pub.orm.ismarkedfordeletion)

        # Proprietor
        self.eq(
            party.parties.public.id,
            party.parties.public.proprietor__partyid
        )

        # Owner
        self.is_(
            ecommerce.users.root,
            party.parties.public.owner,
        )

        # Attributes
        self.eq('Public', pub.name)

        # Re-memoize
        for b in (True, False):
            if b:
                # Delete the private field
                del party.parties._public
            else:
                # Nullify the private field
                party.parties._public = None

            pub1 = party.parties.public
            self.isnot(pub, pub1)
            self.eq(pub.id, pub1.id)
            self.false(pub1.orm.isnew)
            self.false(pub1.orm.isdirty)
            self.false(pub1.orm.ismarkedfordeletion)

    def it_creates_carapacian(self):
        party.company.orm.truncate()

        cara = party.company.carapacian
        self.is_(party.company.carapacian, cara)
        self.false(cara.orm.isnew)
        self.false(cara.orm.isdirty)
        self.false(cara.orm.ismarkedfordeletion)

        party.company._carapacian = None
        cara1 = party.company.carapacian
        self.isnot(cara, cara1)
        self.eq(cara.id, cara1.id)
        self.false(cara1.orm.isnew)
        self.false(cara1.orm.isdirty)
        self.false(cara1.orm.ismarkedfordeletion)

    @staticmethod
    def getvalidcompany(**kwargs):
        com = party.company()
        com.name = uuid4().hex
        com.ein = str(uuid4().int)[:9]
        com.nationalids    =  uuid4().hex
        com.isicv4         =  'A'
        com.dun            =  None

        for k, v in kwargs.items():
            setattr(com, k, v)

        return com

    @staticmethod
    def getvalidcontactmechanism(type='phone'):
        if type == 'phone':
            # Create phone number
            cm = party.phone()

            cm.area =  randint(200, 999)
            cm.line =  randint(100, 999)
            cm.line += ' '
            cm.line += str(randint(1000, 9999))

        elif type == 'email':
            cm = party.email(name='bgates@microsoft.com')
        else:
            raise TypeError('Type not supported')

        return cm

    def it_saves_physical_characteristics(self):
        hr = party.characteristictype(name='Heart rate')
        sys = party.characteristictype(name='Systolic blood preasure')
        dia = party.characteristictype(name='Diastolic blood preasure')

        per = self.getvalid()

        per.characteristics += party.characteristic(
            begin = primative.datetime('2021-03-07 08:00:00'),
            value = 118,
            characteristictype = sys,
        )

        per.characteristics += party.characteristic(
            begin = primative.datetime('2021-03-07 08:00:00'),
            value = 77,
            characteristictype = dia,
        )

        per.characteristics += party.characteristic(
            begin = primative.datetime('2021-03-07 08:00:00'),
            value = 76,
            characteristictype = hr,
        )
        
        per.save()
        per1 = per.orm.reloaded()

        chrs = per.characteristics.sorted()
        chrs1 = per1.characteristics.sorted()

        self.three(chrs)
        self.three(chrs1)

        dt = primative.datetime('2021-03-07 08:00:00')
        for chr, chr1 in zip(chrs, chrs1):
            self.eq(dt, chr1.begin)
            self.none(chr1.end)
            self.eq(chr.value, chr1.value)
            self.eq(
                chr.characteristictype.id,
                chr1.characteristictype.id
            )
            self.type(str, chr1.value)

    def it_appends_marital_status(self):
        per = self.getvalid()

        per.maritals += party.marital(
            begin = primative.datetime('19760415'),
            end   = primative.datetime('20041008'),
            type = party.marital.Single,
        )

        per.maritals += party.marital(
            begin = primative.datetime('20041009'),
            type = party.marital.Married,
        )

        per.save()

        per1 = per.orm.reloaded()

        mars = per.maritals.sorted()
        mars1 = per1.maritals.sorted()

        self.two(mars)
        self.two(mars1)

        for mar, mar1 in zip(mars, mars1):
            self.eq(mar.begin,  mar1.begin)
            self.eq(mar.end,    mar1.end)
            self.eq(mar.type,   mar1.type)

    def it_calls_gender(self):
        per = self.getvalid()
        self.none(per.gender)

        # Gender must have already been registered
        def f(per):
            per.gender = 'Male'

        self.expect(ValueError, lambda: f(per))

        party.gendertype(name='Male').save()
        party.gendertype(name='Female').save()
        party.gendertype(name='Nonbinary').save()

        per.gender = 'Male'
        self.one(per.genders)

        self.eq('Male', per.gender)

        per.save()

        per = per.orm.reloaded()

        self.one(per.genders)
        self.eq('Male', per.gender)

        per.gender = 'Female'
        self.eq('Female', per.gender)
        self.one(per.genders)

        per = per.orm.reloaded()

        # NOTE:7f6906fc The mutator per.gender will save the gender
        # object, so there is no need to call save here
        # per.save()

        self.eq('Female', per.gender)
        self.one(per.genders)

        ''' Make the Female gender a past gender and make per's current
        gender nonbinary. '''

        gen = per.genders.first
        gen.begin = primative.datetime('1980-01-01')
        gen.end   = primative.datetime('1990-01-01')

        per.genders += party.gender(
            begin       =  primative.datetime('1990-01-02'),
            end         =  None,
            gendertype  =  party.gendertypes(name='nonbinary').first,
        )

        self.eq('Nonbinary', per.gender)

        per.save()

        per1 = per.orm.reloaded()

        gens = per.genders.sorted()
        gens1 = per1.genders.sorted()

        self.two(gens)
        self.two(gens1)
        self.eq('Nonbinary', per1.gender)

        for gen, gen1 in zip(gens, gens1):
            self.eq(gen.begin, gen1.begin)
            self.eq(gen.end, gen1.end)
            self.eq(gen.gendertype.id, gen1.gendertype.id)

    def it_calls_person_name_properties(self):
        per = party.person()

        per.first = 'Joey'
        self.eq('Joey', per.first)

        per.middle = 'Middle'
        self.eq('Middle', per.middle)

        per.last = 'Armstrong'
        self.eq('Armstrong', per.last)

        per.save()

        per1 = per.orm.reloaded()

        for prop in ('first', 'middle', 'last'):
            self.eq(getattr(per, prop), getattr(per1, prop))

        names = party.nametypes.orm.all.pluck('name')

        self.three(names)
        self.true('first' in names)
        self.true('middle' in names)
        self.true('last' in names)

        ''' It uses ``name`` attribute`` '''
        per = party.person()
        per.name = 'Guido van Rossum'
        self.eq('Guido', per.first)
        self.eq('van', per.middle)
        self.eq('Rossum', per.last)
        self.eq('Guido van Rossum', per.name)
        self.eq('Guido van Rossum', per.orm._super.name)

        per.save()

        # `party.name` should equal whatever `person.name` ends up
        # being.
        part = party.party(per.id)
        self.eq('Guido van Rossum', part.name)

    def it_calls_first_middle_and_last(self):
        ''' First name '''
        per = party.person()
        per.first = 'Guido'
        self.eq('Guido', per.name)
        self.eq('Guido', per.first)
        self.eq('Guido', per.orm._super.name)

        per.save()

        per = per.orm.reloaded()
        self.eq('Guido', per.name)
        self.eq('Guido', per.orm.super.name)
        self.eq('Guido', per.first)
        self.eq('Guido', party.party(per).name)

        ''' Update first name '''
        per.first = 'Jesse'
        self.eq('Jesse', per.name)
        self.eq('Jesse', per.first)
        self.eq('Jesse', per.orm._super.name)

        per.save()

        per = per.orm.reloaded()
        self.eq('Jesse', per.name)
        self.eq('Jesse', per.first)
        self.eq('Jesse', per.orm.super.name)
        self.eq('Jesse', party.party(per).name)

        ''' Update middle name '''
        per.middle = 'James'
        self.eq('Jesse James', per.name)
        self.eq('Jesse', per.first)
        self.eq('James', per.middle)
        self.eq('Jesse James', per.orm._super.name)

        per.save()

        per = per.orm.reloaded()
        self.eq('Jesse James', per.name)
        self.eq('Jesse', per.first)
        self.eq('James', per.middle)
        self.eq('Jesse James', party.party(per).name)

        ''' Update last name '''
        per.last = 'Hogan'
        self.eq('Jesse James Hogan', per.name)
        self.eq('Jesse', per.first)
        self.eq('James', per.middle)
        self.eq('Hogan', per.last)
        self.eq('Jesse James Hogan', per.orm._super.name)

        per.save()

        per = per.orm.reloaded()
        self.eq('Jesse James Hogan', per.name)
        self.eq('Jesse', per.first)
        self.eq('James', per.middle)
        self.eq('Hogan', per.last)
        self.eq('Jesse James Hogan', party.party(per).name)

    def it_updates_person_name_from_super(self):
        """ Changing a person's super's (party) name property should
        change the persons default name (first, middle and last).
        """

        # Set the person's name an the ``person`` level
        per = party.person()
        per.name = 'Guido van Rossum'

        # FYI This will update the super's (party) name, however this
        # unit test is to ensure the reverse happens.
        self.eq(per.name, per.orm.super.name)

        per.save()

        part = party.party(per)

        # The party will have persisted the name when
        # person.save() was called.
        self.eq(per.name, part.name)

        # Now, we want to go the other way around. Set the party.name
        # property. The person.name property should be changed as a
        # result. It will allso be saved by the party.name setter.
        part.name = 'Jesse James Hogan'

        # Make sure nothing behind the scenes mutates party.name when
        # it's being set.
        self.eq(part.name, 'Jesse James Hogan')

        per = per.orm.reloaded()
        self.eq('Jesse', per.first)
        self.eq('James', per.middle)
        self.eq('Hogan', per.last)
        self.eq(per.name, 'Jesse James Hogan')
        self.eq(per.orm.super.name, 'Jesse James Hogan')


        per.orm.super.name = 'Delia Maria Lythgoe'

        # TODO:8cc3bfdc Setting super's name property does not update
        # the in-memory person objects property. This is because super
        # (party) doesn't have access to the thing it's super to (per).
        # When we add orm.sub, super will have that access and be able
        # to update the per object while it's in memory.
        self.ne('Delia', per.first)
        self.ne('Maria', per.middle)
        self.ne('Lythgo', per.last)

    def it_adds_citizenships(self):
        per = party.person(name='Jesse Hogan')

        au = party.region(
            name = 'Austria',
            type = party.region.Country
        )

        en = party.region(
            name = 'England',
            type = party.region.Country
        )

        per.citizenships += party.citizenship(
            begin   = primative.datetime('1854-05-06'),
            end     = primative.datetime('1938-05-01'),
            country = au,
        )

        per.citizenships.last.passports += party.passport(
            number = str(randint(1111111111, 99999999999)),
            issuedat = primative.datetime('2010-05-06'),
            expiresat = primative.datetime('2019-05-06'),
        )

        per.citizenships += party.citizenship(
            begin   = primative.datetime('1938-05-01'),
            end     = primative.datetime('1939-09-23'),
            country = en,
        )

        per.citizenships.last.passports += party.passport(
            number = str(randint(1111111111, 99999999999)),
            issuedat = primative.datetime('2010-05-06'),
            expiresat = primative.datetime('2019-05-06'),
        )

        per.save()

        per1 = per.orm.reloaded()

        cits = per.citizenships.sorted()
        cits1 = per1.citizenships.sorted()

        self.two(cits)
        self.two(cits1)

        for cit, cit1 in zip(cits, cits1):
            self.eq(cit.begin, cit1.begin)
            self.eq(cit.end, cit1.end)
            self.eq(cit.country.id, cit1.country.id)

            pps = cit.passports.sorted()
            pps1 = cit1.passports.sorted()

            self.one(pps)
            self.one(pps1)

            for pp, pp1 in zip(pps, pps1):
                for prop in ('number', 'issuedat', 'expiresat'):
                    self.eq( getattr(pp, prop), getattr(pp1, prop))

    def it_creates(self):
        per = self.getvalid()
        per.save()

        per1 = party.person(per.id)

        for map in per.orm.mappings.fieldmappings:
            self.eq(
                getattr(per, map.name),
                getattr(per1, map.name)
            )

    def it_updates(self):
        # Create
        per = self.getvalid()
        per.save()

        # Load
        per = party.person(per.id)

        # Update
        oldfirstname = per.first
        newfirstname = uuid4().hex

        per.first = newfirstname
        per.save()

        # Reload
        per1 = party.person(per.id)

        # Test
        self.eq(newfirstname, per1.first)
        self.ne(oldfirstname, per1.first)
        
    def it_creates_association_to_company(self):
        per = self.getvalid()
        com = party_.getvalidcompany()

        pp = party.party_party()
        pp.object = com
        pp.role = 'patronize'

        per.party_parties += pp

        self.is_(per, per.party_parties.last.subject)
        self.is_(com, per.party_parties.last.object)

        per.save()

        per1 = party.person(per.id)

        self.eq(per.id, per1.party_parties.last.subject.id)
        self.eq(com.id, per1.party_parties.last.object.id)

    def it_places_person_in_a_corporate_hierarchy(self):
        ... # TODO

    def it_creates_association_to_person(self):
        bro = self.getvalid()
        sis = self.getvalid()

        # TODO Figure out a way to do this:
        #
        #     bro.siblings += sis

        bro.party_parties += party.party_party.sibling(sis)

        self.is_(bro, bro.party_parties.last.subject)
        self.is_(sis, bro.party_parties.last.object)

        bro.save()

        bro1 = party.person(bro.id)

        self.eq(bro.id, bro1.party_parties.last.subject.id)
        self.eq(sis.id, bro1.party_parties.last.object.id)

    def it_creates_party_type(self):
        typ = party.type()
        typ.name = uuid4().hex

        for i in range(2):
            pt = party.party_type()
            pt.begin = primative.datetime.utcnow(days=-100)
            pt.party = self.getvalid()
            typ.party_types += pt

        typ.save()

        typ1 = party.type(typ.id)
        self.eq(typ.name, typ1.name)

        typ.party_types.sort() 
        typ1.party_types.sort()

        self.two(typ1.party_types)

        self.eq(
            typ.party_types.first.party.id, 
            typ1.party_types.first.party.id
        )

        self.eq(
            typ.party_types.second.party.id,
            typ1.party_types.second.party.id
        )

        self.eq(
            typ.id,
            typ1.party_types.first.type.id
        )

    def it_creates_party_roles(self):
        acme = party.company(name='ACME Corporation')

        acme.roles += party.customer(
            begin  =  primative.datetime('2006-01-01'),
            end    =  primative.datetime('2008-04-14')
        )

        acme.roles += party.supplier()

        acme.save()

        acme1 = acme.orm.reloaded()

        rls = acme.roles.sorted()
        rls1 = acme1.roles.sorted()

        self.two(rls)
        self.two(rls1)

        for rl, rl1 in zip(rls, rls1):
            rl1 = rl.orm.entity(rl1)
            self.eq(rl.begin, rl1.begin)
            self.eq(rl.end, rl1.end)

    def it_creates_role_role(self):
        # Create parties
        rent = party.company(name='ACME Corporation')
        sub  = party.company(name='ACME Subsidiary')

        # Create priority
        high = party.priority(name='high')

        # Create status
        act = party.role_role_status(name='active')

        # Create roles
        rent.roles += party.parent(
            begin     =  primative.datetime('2006-01-01'),
            end       =  None,
        )

        sub.roles += party.subsidiary(
            begin  =  primative.datetime('2006-01-01'),
            end    =  None,
        )

        # Associate the two roles created above
        sub.roles.last.role_roles += party.role_role(
            begin  =  primative.datetime('2006-01-01'),
            end    =  None,
            role_role_type = party.role_role_type(
                name = 'Organizational rollup',
                description = 'Shows that each organizational '
                              'unit may be within one or more '
                              'organization units, over time.',
            ),

            object = rent.roles.last,

            # This is a "high" priority relationship.
            priority = high,

            # This is an active relationship.
            status = act,
        )

        sub.roles.last.role_roles.last.communications += \
            party.communication(
                begin = primative.datetime('2010-02-18 12:01:23'),
                end   = primative.datetime('2010-02-18 12:49:32'),
                note  = 'Good phone call. I think we got him.',
            )

        rent.save(sub, sub.roles)

        # Reload and test
        sub1 = sub.orm.reloaded()

        rls = sub.roles
        rls1 = sub1.roles

        self.one(rls)
        self.one(rls1)

        rrs = rls.first.role_roles
        rrs1 = rls1.first.role_roles

        self.one(rrs)
        self.one(rrs1)

        self.eq(
            rrs.first.begin,
            rrs1.first.begin,
        )

        self.eq(
            rrs.first.end,
            rrs1.first.end,
        )

        self.eq(
            rrs.first.object.id,
            rrs1.first.object.id,
        )

        self.eq(
            rrs.first.priority.id,
            rrs1.first.priority.id,
        )

        self.eq(
            'high',
            rrs1.first.priority.name,
        )

        self.eq(
            rrs.first.status.id,
            rrs1.first.status.id,
        )

        self.eq(
            'active',
            rrs1.first.status.name,
        )

        self.eq(
            rrs.first.role_role_type.id,
            rrs1.first.role_role_type.id,
        )

        self.eq(
            rrs.first.role_role_type.name,
            rrs1.first.role_role_type.name,
        )

        self.eq(
            rrs.first.role_role_type.description,
            rrs1.first.role_role_type.description,
        )

        coms = rrs.first.communications.sorted()
        coms1 = rrs.first.communications.sorted()

        self.one(coms)
        self.one(coms1)

        for com, com1 in zip(coms, coms1):
            self.eq(com.id, com1.id)
            self.eq(com.begin, com1.begin)
            self.eq(com.end, com1.end)
            self.eq(com.note, com1.note)


    def it_creates_company(self):
        com = self.getvalidcompany()
        com.save()

        com1 = party.company(com.id)

        sup = com

        while sup:
            for map in sup.orm.mappings.fieldmappings:
                self.eq(
                    getattr(com, map.name),
                    getattr(com1, map.name),
                )

            sup = sup.orm.super

    def it_updates_company(self):
        # Create
        com = self.getvalidcompany()
        com.save()

        # Load
        com = party.company(com.id)

        # Update
        old, new = com.name, uuid4().hex
        com.name = new
        com.save()

        # Reload
        com1 = party.company(com.id)

        # Test
        self.eq(new, com1.name)
        self.ne(old, com1.name)

    def it_creates_association_company_to_person(self):
        per = self.getvalid()
        com = self.getvalidcompany()

        pp = party.party_party()
        pp.object = per
        pp.role = 'employ'
        pp.begin = primative.date.today()

        com.party_parties += pp

        self.is_(com, com.party_parties.last.subject)
        self.is_(per, com.party_parties.last.object)

        com.save()

        com1 = party.company(com.id)

        self.eq(com.id, com1.party_parties.last.subject.id)
        self.eq(per.id, com1.party_parties.last.object.id)

        self.one(com1.party_parties)
        pp1 = com1.party_parties.first
        for map in pp.orm.mappings.fieldmappings:
            self.eq(
                getattr(pp, map.name),
                getattr(pp1, map.name),
            )

    def it_associates_company_to_phone_numbers(self):
        com = self.getvalidcompany()

        # Create two phone numbers
        for i in range(2):

            # Create phone number
            ph = party.phone()
            ph.area = int('20' + str(i))
            ph.line = '555 5555'
            
            # Create party to contact mechanism association
            pcm                   =  party.party_contactmechanism()
            pcm.begin             =  primative.datetime('1976-01-01')
            pcm.end               =  None
            pcm.solicitations     =  False
            pcm.extension         =  None
            pcm.purpose           =  party.party_contactmechanism.roles.main
            pcm.contactmechanism  =  ph
            pcm.party             =  com

            # Add association to the company object
            com.party_contactmechanisms += pcm

        # Save, reload and test
        com.save()

        com1 = party.company(com.id)

        com.party_contactmechanisms.sort()
        com1.party_contactmechanisms.sort()

        self.two(com1.party_contactmechanisms)

        for i in range(2):
            self.eq(com.id, com1.party_contactmechanisms[i].party.id)

            self.eq(
                com.party_contactmechanisms[i].contactmechanism.id,
                com1.party_contactmechanisms[i].contactmechanism.id
            )
            ph = party.phone(
                com1.party_contactmechanisms[i].contactmechanism.id
            )

    def it_associates_company_to_email_addresses(self):
        com = self.getvalidcompany()

        #it_associates_company_to_email_addresses Create two email addressess
        for i in range(2):

            # Create email addres
            em = party.email()
            em.name = 'jimbo%s@foonet.com' % i
            
            # Create party to contact mechanism association
            priv = party.party_contactmechanism.roles.private

            pcm                   =  party.party_contactmechanism()
            pcm.begin             =  primative.datetime('1993-09-01')
            pcm.end               =  None
            pcm.solicitations     =  False
            pcm.extension         =  None
            pcm.purpose           =  priv # Private email address
            pcm.contactmechanism  =  em
            pcm.party             =  com

            # Add association to the company object
            com.party_contactmechanisms += pcm

        # Save, reload and test
        com.save()

        com1 = party.company(com.id)

        com.party_contactmechanisms.sort()
        com1.party_contactmechanisms.sort()

        self.two(com1.party_contactmechanisms)

        for i in range(2):
            self.eq(com.id, com1.party_contactmechanisms[i].party.id)

            self.eq(
                com.party_contactmechanisms[i].contactmechanism.id,
                com1.party_contactmechanisms[i].contactmechanism.id
            )

            em = party.email(
                com1.party_contactmechanisms[i].contactmechanism.id
            )

    def it_associates_company_to_postal_addresses(self):
        com = self.getvalidcompany()

        # Create two postal addressess
        for i in range(2):

            # Create postal addres
            addr = party.address()
            addr.address1 = '742 Evergreen Terrace'
            addr.address2 = None
            addr.directions = self.dedent('''
			Take on I-40 E. 
            Take I-44 E to Glenstone Ave in Springfield. 
            Take exit 80 from I-44 E
			Drive to E Evergreen St
            ''')

            ar = party.address_region()
            ar.region = self.getvalidregion()
            addr.address_regions += ar
            
            hm = party.party_contactmechanism.roles.home

            # Create party-to-contact-mechanism association
            pcm                   =  party.party_contactmechanism()
            pcm.begin             =  primative.datetime('1993-09-01')
            pcm.end               =  None
            pcm.solicitations     =  False
            pcm.extension         =  None
            pcm.purpose           =  hm
            pcm.contactmechanism  =  addr
            pcm.party             =  com

            # Add association to the company object
            com.party_contactmechanisms += pcm

        # Save, reload and test
        com.save()

        com1 = party.company(com.id)

        com.party_contactmechanisms.sort()
        com1.party_contactmechanisms.sort()

        self.two(com1.party_contactmechanisms)

        for i in range(2):
            self.eq(com.id, com1.party_contactmechanisms[i].party.id)

            self.eq(
                com.party_contactmechanisms[i].contactmechanism.id,
                com1.party_contactmechanisms[i].contactmechanism.id
            )

            addr = com.party_contactmechanisms[i].contactmechanism

            # Downcast
            addr1 = party.address(
                com1.party_contactmechanisms[i].contactmechanism.id
            )

            self.eq(addr.address1, addr1.address1)

            reg = addr.address_regions.first.region
            reg1 = addr1.address_regions.first.region

            expect = self.dedent('''
			Scottsdale, Arizona 85281
			United States of America
            ''')
            self.eq(expect, str(reg1))

            self.eq(str(reg), str(reg1))

    def it_updates_department(self):
        # todo:afa4ffc9 rewrite the below to use the role_role
        # association to associate persons to departments and divisions.
        com = self.getvalidcompany()
        self.zero(com.departments)
        com.departments += party.department(name='web')
        com.save()

        com1 = party.company(com.id)

        dep1 = com1.departments.first

        # Update departement
        dep1.name = 'web1'

        # Save
        com1.save()

        # Load and test deparment
        com1 = party.company(com.id)

        dep1 = com1.departments.first

        self.eq('web1', dep1.name)

    def it_appends_divisions_to_departments(self):
        # TODO:afa4ffc9 Rewrite the below to use the role_role
        # association to associate persons to departments and divisions.
        pass

    def it_links_contactmechanisms(self):
        # Create contact mechanisms
        ph1 = self.getvalidcontactmechanism(type='phone')
        ph2 = self.getvalidcontactmechanism(type='phone')
        em  = self.getvalidcontactmechanism(type='email')


        # Make cm_cm reference the association class
        cm_cm = party.contactmechanism_contactmechanism

        # When ph1 is busy, the number will be forwarded to ph2
        ph1.contactmechanism_contactmechanisms += cm_cm(
            event   =  cm_cm.Busy,
            do      =  cm_cm.Forward,
            object  =  ph2,
        )

        # When no one answers ph2, forward the call will be forwarded
        # to a voice recognition email.
        ph2.contactmechanism_contactmechanisms += cm_cm(
            event    =  cm_cm.Unanswered,
            do       =  cm_cm.Forward,
            object   =  em,
        )

        # This saves the cm's and the associations
        ph1.save()

        # Reload everyting
        ph1_1 = ph1.orm.reloaded()

        # Test that the first association (the first link in the chain)
        # saved properly.
        cm_cms1 = ph1.contactmechanism_contactmechanisms.sorted()
        cm_cms1_1 = ph1_1.contactmechanism_contactmechanisms.sorted()

        self.one(cm_cms1)
        self.one(cm_cms1_1)

        self.eq(cm_cms1.first.id,          cm_cms1_1.first.id)
        self.eq(cm_cms1.first.on,       cm_cms1_1.first.on)
        self.eq(cm_cms1.first.do,          cm_cms1_1.first.do)
        self.eq(cm_cms1.first.object.id,   cm_cms1_1.first.object.id)
        self.eq(cm_cms1.first.subject.id,  cm_cms1_1.first.subject.id)

        # Test that the second association (the second link in the chain)
        # saved properly.
        cm_cms1 = cm_cms1.first.object \
                    .contactmechanism_contactmechanisms \
                    .sorted()

        cm_cms1_1 = cm_cms1_1.first.object \
                        .contactmechanism_contactmechanisms \
                        .sorted()

        self.one(cm_cms1)
        self.one(cm_cms1_1)

        self.eq(cm_cms1.first.id,          cm_cms1_1.first.id)
        self.eq(cm_cms1.first.on,       cm_cms1_1.first.on)
        self.eq(cm_cms1.first.do,          cm_cms1_1.first.do)
        self.eq(cm_cms1.first.object.id,   cm_cms1_1.first.object.id)
        self.eq(cm_cms1.first.subject.id,  cm_cms1_1.first.subject.id)

    def it_associates_phone_numbers(self):
        per = self.getvalid()

        # Create two phone numbers
        for i in range(2):

            # Create phone number
            ph = party.phone()
            ph.area = int('20' + str(i))
            ph.line = '555 5555'
            
            # Create party to contact mechanism association
            pcm                   =  party.party_contactmechanism()
            pcm.begin             =  primative.datetime('1976-01-01')
            pcm.end               =  None
            pcm.solicitations     =  False
            pcm.extension         =  None
            pcm.purpose           =  party.party_contactmechanism.roles.main
            pcm.contactmechanism  =  ph
            pcm.party             =  per

            # Add association to the person object
            per.party_contactmechanisms += pcm

        # Save, reload and test
        per.save()

        per1 = party.person(per.id)

        per.party_contactmechanisms.sort()
        per1.party_contactmechanisms.sort()

        self.two(per1.party_contactmechanisms)

        for i in range(2):
            self.eq(per.id, per1.party_contactmechanisms[i].party.id)

            self.eq(
                per.party_contactmechanisms[i].contactmechanism.id,
                per1.party_contactmechanisms[i].contactmechanism.id
            )
            ph = party.phone(
                per1.party_contactmechanisms[i].contactmechanism.id
            )

    def it_associates_email_addresses(self):
        per = self.getvalid()

        # Create two email addressess
        for i in range(2):

            # Create email addres
            em = party.email()
            em.name = 'jimbo%s@foonet.com' % i
            
            # Create party to contact mechanism association
            priv = party.party_contactmechanism.roles.private

            pcm                   =  party.party_contactmechanism()
            pcm.begin             =  primative.datetime('1993-09-01')
            pcm.end               =  None
            pcm.solicitations     =  False
            pcm.extension         =  None
            pcm.purpose           =  priv # Private email address
            pcm.contactmechanism  =  em
            pcm.party             =  per

            # Add association to the person object
            per.party_contactmechanisms += pcm

        # Save, reload and test
        per.save()

        per1 = party.person(per.id)

        per.party_contactmechanisms.sort()
        per1.party_contactmechanisms.sort()

        self.two(per1.party_contactmechanisms)

        for i in range(2):
            self.eq(per.id, per1.party_contactmechanisms[i].party.id)

            self.eq(
                per.party_contactmechanisms[i].contactmechanism.id,
                per1.party_contactmechanisms[i].contactmechanism.id
            )

            em = party.email(
                per1.party_contactmechanisms[i].contactmechanism.id
            )

    def it_associates_postal_addresses(self):
        per = self.getvalid()

        # Create two postal addressess
        for i in range(2):

            # Create postal addres
            addr = party.address()
            addr.address1 = '742 Evergreen Terrace'
            addr.address2 = None
            addr.directions = self.dedent('''
			Take on I-40 E. 
            Take I-44 E to Glenstone Ave in Springfield. 
            Take exit 80 from I-44 E
			Drive to E Evergreen St
            ''')

            ar = party.address_region()
            ar.region = self.getvalidregion()
            addr.address_regions += ar
            
            hm = party.party_contactmechanism.roles.home

            # Create party-to-contact-mechanism association
            pcm                   =  party.party_contactmechanism()
            pcm.begin             =  primative.datetime('1993-09-01')
            pcm.end               =  None
            pcm.solicitations     =  False
            pcm.extension         =  None
            pcm.purpose           =  hm
            pcm.contactmechanism  =  addr
            pcm.party             =  per

            # Add association to the person object
            per.party_contactmechanisms += pcm

        # Save, reload and test
        per.save()

        per1 = party.person(per.id)

        per.party_contactmechanisms.sort()
        per1.party_contactmechanisms.sort()

        self.two(per1.party_contactmechanisms)

        for i in range(2):
            self.eq(per.id, per1.party_contactmechanisms[i].party.id)

            self.eq(
                per.party_contactmechanisms[i].contactmechanism.id,
                per1.party_contactmechanisms[i].contactmechanism.id
            )

            addr = per.party_contactmechanisms[i].contactmechanism

            # Downcast
            addr1 = party.address(
                per1.party_contactmechanisms[i].contactmechanism.id
            )

            self.eq(addr.address1, addr1.address1)

            reg = addr.address_regions.first.region
            reg1 = addr1.address_regions.first.region

            expect = self.dedent('''
			Scottsdale, Arizona 85281
			United States of America
            ''')
            self.eq(expect, str(reg1))

            self.eq(str(reg), str(reg1))

    def it_adds_purposes_to_contact_mechanisms(self):
        tbl = (
            ('ABC Corporation', 'company', '212 234 0958',    'phone',   'General phone number'),
            ('ABC Corporation', 'company', '212 334 5896',    'phone',   'Main fax number'),
            ('ABC Corporation', 'company', '212 356 4898',    'phone',   'Secondary fax number'),
            ('ABC Corporation', 'company', '100 Main Street', 'address', 'Headquarters'),
            ('ABC Corporation', 'company', '100 Main Street', 'address', 'Billing Inquires'),
            ('ABC Corporation', 'company', '500 Jerry Street','address', 'Sales Office'),
            ('ABC Corporation', 'company', 'http://abc.com',  'website', 'Central Internet Address'),

            ('ABC Subsidiary',  'company', '100 Main Street', 'address', 'Service Address'),
            ('ABC Subsidiary',  'company', '255 Fetch Street','address', 'Sales Office'),

            ('John Smith',      'person',  '212 234 9856',     'phone',   'Main office number'),
            ('John Smith',      'person',  '212 784 5893',     'phone',   'Main home number'),
            ('John Smith',      'person',  '212 384 4387',     'phone',    None),
            ('John Smith',      'person',  '345 Hamlet Place', 'address', 'Main home address'),
            ('John Smith',      'person',  '245 Main Street',  'address', 'Main work address'),

            ('Barry Goldstein',  'person',  '212 234 0045',            'phone',   'Main office number'),
            ('Barry Goldstein',  'person',  '212 234 0046',            'phone',   'Secondary office number'),
            ('Barry Goldstein',  'person',  'Bgoldstein@abc.com',      'email',   'Work email address'),
            ('Barry Goldstein',  'person',  'barry@barrypersonal.com', 'email',   'Personal email address'),
            ('Barry Goldstein',  'person',  '2985 Cordova Road',       'address', 'Main home address'),
        )

        parts = party.parties()
        cms   = party.contactmechanisms()
        for r in tbl:
            # Objectify party
            part, cls = r[0:2]
            cls = getattr(party, cls)

            for part1 in parts:
                if part == part1.name:
                    part = part1
                    break
            else:
                part, name = cls(), part
                if cls is party.person:
                    part.first = name
                part.name = name
                parts += part

            # Objectify contact mechanisms
            cm, cls= r[2:4]
            cls = getattr(party, cls)

            def test(cm, cm1, attr):
                return getattr(cm1, attr) == cm

            if  cls  is  party.phone:    attr  =  'line'
            if  cls  is  party.email:    attr  =  'name'
            if  cls  is  party.address:  attr  =  'address1'
            if  cls  is  party.website:  attr  =  'url'

            for cm1 in cms:
                if type(cm1) is not cls:
                    continue

                if test(cm, cm1, attr):
                    cm = cm1
                    break
            else:
                cm = cls(**{attr: cm})
                if cls is party.phone:
                    cm.area = None
                elif cls is party.address:
                    cm.address2 = None
                cms += cm


            # Associate party with contact mechanism
            part.party_contactmechanisms += \
                party.party_contactmechanism(
                    party = part,
                    contactmechanism = cm
                )

            pcm = part.party_contactmechanisms.last

            now = primative.datetime.utcnow
            pcm.purposes += party.purpose(
                begin       = now(days=-randint(1, 1000)),
                end         = now(days= randint(1, 1000)),
                purposetype = party.purposetype(name=r[4])
            )

        parts.save()

        parts1 = party.parties()
        for part in parts:
            parts1 += part.orm.reloaded()

        parts.sorted()
        parts1.sorted()

        self.eq(parts.count, parts1.count)

        for part, part1 in zip(parts, parts1):
            cms = part.party_contactmechanisms.sorted()
            cms1 = part1.party_contactmechanisms.sorted()

            self.eq(cms.count, cms1.count)

            for cm, cm1 in zip(cms, cms1):
                self.eq(cm.id, cm1.id)
                self.eq(cm.party.id, cm1.party.id)
                self.eq(part.id, cm1.party.id)
                self.eq(cm.contactmechanism.id, cm1.contactmechanism.id)

                self.eq(
                    cm.contactmechanism.id, 
                    cm1.contactmechanism.id
                )

                purs = cm.purposes.sorted()
                purs1 = cm1.purposes.sorted()
                self.eq(purs.count, purs1.count)

                for pur, pur1 in zip(purs, purs1):
                    self.eq(pur.id,              pur1.id)
                    self.eq(pur.begin,           pur1.begin)
                    self.eq(pur.end,             pur1.end)
                    self.eq(pur.purposetype.id,  pur1.purposetype.id)
                    self.eq(
                        pur.purposetype.name,  
                        pur1.purposetype.name
                    )
        return

        # The above `return` can be removed to print a tabularized
        # version of the nested tuple from above. This comes from the
        # reloaded party entities collection so it is a good way to
        # visually verify what the test is saving/reloading.
        tbl1 = table()
        for part in parts1:
            for pcm in part.party_contactmechanisms:
                for pur in pcm.purposes:
                    r = tbl1.newrow()
                    try:
                        r.newfield(part.name)
                    except AttributeError:
                        r.newfield(part.first)
                        
                    if party.phone.orm.exists(pcm.contactmechanism):
                        cm = party.phone(pcm.contactmechanism)
                        r.newfield(cm.line)
                    elif party.address.orm.exists(pcm.contactmechanism):
                        cm = party.address(pcm.contactmechanism)
                        r.newfield(cm.address1)
                    elif party.website.orm.exists(pcm.contactmechanism):
                        cm = party.website(pcm.contactmechanism)
                        r.newfield(cm.url)
                    elif party.email.orm.exists(pcm.contactmechanism):
                        cm = party.email(pcm.contactmechanism)
                        r.newfield(cm.address)
                    else:
                        raise TypeError()

                    r.newfield(pur.purposetype.name)

        print(tbl1)

    @staticmethod
    def getvalidaddress():
        addr = party.address()
        addr.address1 = '742 Evergreen Terrace'
        addr.address2 = None
        addr.directions = tester.dedent('''
        Take on I-40 E. 
        Take I-44 E to Glenstone Ave in Springfield. 
        Take exit 80 from I-44 E
        Drive to E Evergreen St
        ''')
        return addr

    def it_creates_facilitiy(self):
        # Building
        miniluv = party.facility(
            name = 'Miniluv', 
            type = party.facility.Building
        )

        # Floor
        miniluv.facilities += party.facility(
            name = '0',
            type = party.facility.Floor
        )

        # Room
        miniluv.facilities.last.facilities += party.facility(
            name = '101',
            type = party.facility.Room
        )

        # Footage defaults to None and we never set it above
        self.none(miniluv.footage, None)

        miniluv.save()

        miniluv1 = miniluv.orm.reloaded()

        fac = miniluv1
        self.eq(party.facility.Building, fac.type)
        self.none(fac.footage, None)
        self.eq('Miniluv', fac.name)
        self.one(fac.facilities)

        fac = fac.facilities.first
        self.eq(party.facility.Floor, fac.type)
        self.none(fac.footage, None)
        self.eq('0', fac.name)
        self.one(fac.facilities)

        fac = fac.facilities.first
        self.eq(party.facility.Room, fac.type)
        self.none(fac.footage, None)
        self.eq('101', fac.name)
        self.zero(fac.facilities)

    def it_associates_facility_with_parties(self):

        # Create a facility
        giga = party.facility(
            name = 'Giga Navada', 
            type = party.facility.Factory
        )

        # Create party
        tsla = party.company(name='Tesla')

        # Create association
        tsla.party_facilities += party.party_facility(
            party             =  tsla,
            facility          =  giga,
            facilityroletype  =  party.facilityroletype(name='owner'),
        )

        # Save and reload
        tsla.save()

        tsla1 = tsla.orm.reloaded()

        # Test
        pfs = tsla.party_facilities.sorted()
        pfs1 = tsla1.party_facilities.sorted()

        self.one(pfs)
        self.one(pfs1)

        for pf, pf1 in zip(pfs, pfs1):
            self.eq(pf.id,                   pf1.id)
            self.eq(pf.party.id,             pf1.party.id)
            self.eq(pf.facility.id,          pf1.facility.id)
            self.eq(pf.facilityroletype.id,  pf1.facilityroletype.id)

    def it_associates_facility_with_contactmechanisms(self):
        # Create a facility
        giga = party.facility(
            name = 'Giga Shanghai', 
            type = party.facility.Factory,
            footage = 9300000,
        )

        # Associate a postal address with the facility
        addr = party.address(
            address1 = '浦东新区南汇新城镇同汇路168号',
            address2 = 'D203A',
        )

        addr.address_regions += party.address_region(
            region = party.region.create(
                ('China',     party.region.Country,       'CH'),
                ('Shanghai',  party.region.Municipality,  None),
                ('Pudong',    party.region.District,      None),
            )
        )

        giga.facility_contactmechanisms += party.facility_contactmechanism(
            contactmechanism = addr,
        )

        # Associate a phone number with the facility.
        giga.facility_contactmechanisms += party.facility_contactmechanism(
            contactmechanism = party.phone(area=510, line='602-3960')
        )

        giga.save()

        giga1 = giga.orm.reloaded()

        fcms = giga.facility_contactmechanisms.sorted()
        fcms1 = giga1.facility_contactmechanisms.sorted()

        self.two(fcms)
        self.two(fcms1)

        for fcm, fcm1 in zip(fcms, fcms1):
            self.eq(fcm.id, fcm1.id)
            self.eq(fcm.facility.id, fcm1.facility.id)
            
            # Downcast
            id = fcm1.contactmechanism.id
            cm = fcm1.contactmechanism.orm.cast(party.phone)

            if cm:
                self.eq(fcm.contactmechanism.area, cm.area)
                self.eq(fcm.contactmechanism.line, cm.line)
            else:
                cm = party.address.orm.cast(id)
                cm = fcm1.contactmechanism.orm.cast(party.address)
                assert cm is not None
                self.eq(fcm.contactmechanism.address1, cm.address1)
                self.eq(fcm.contactmechanism.address2, cm.address2)

    def it_associates_party_to_communication(self):
        # This is for a simple association between party entity objects
        # and `communication` event objects. However, the book says that
        # ``communication`` events will usually be within the context of
        # a "party relationship" (``role_role``) because it is within a
        # relationship that communications usually make sense (see
        # it_associates_relationship_to_communication).
        will  =  party.person(first='William',  last='Jones')
        marc  =  party.person(first='Marc',     last='Martinez')
        john  =  party.person(first='John',     last='Smith')

        comm = party.communication(
            begin = primative.datetime('2019-03-23 13:00:00'),
            end   = primative.datetime('2019-03-23 14:00:00'),
            note  = 'A meeting between William, Marc and John',
        )

        participant = party.communicationroletype(name='participant')
        for per in (will, marc, john):
            pcs = getattr(per, 'party_communications')

            pcs += party.party_communication(
                communication          =  comm,
                communicationroletype  =  participant,
            )

        will.save(marc, john)

        will1 = will.orm.reloaded()
        marc1 = marc.orm.reloaded()
        john1 = john.orm.reloaded()

        for per1 in (will1, marc1, john1): 
            pcs1 = getattr(per1, 'party_communications')
            self.one(pcs)
            self.one(pcs1)

            self.eq(
                pcs.first.communicationroletype.id,
                pcs1.first.communicationroletype.id,
            )

            pc1 = pcs1.first

            self.eq(per1.id,      pc1.party.id)
            self.eq(comm.id,     pc1.communication.id)
            self.eq(comm.begin,  pc1.communication.begin)
            self.eq(comm.end,    pc1.communication.end)

    def it_associates_relationship_to_communication(self):
        # Create parties
        
        ## Persons
        will  =  party.person(name='Will')
        marc  =  party.person(name='Mark')
        john  =  party.person(name='John')

        ## Companies
        abc   =  party.company(name='ABC Corporation')
        acme  =  party.company(name='ACME Corporation')

        # Will Jones has an Account Management role
        will.roles += party.role(
            begin          =  primative.datetime('2016-02-12'),
            end            =  None,
            partyroletype  =  party.partyroletype(name='Account Manager'),
        )

        # Marc Martinez hase a Customer Contact role
        marc.roles += party.role(
            begin          =  primative.datetime('2014-03-23'),
            end            =  None,
            partyroletype  =  party.partyroletype(name='Customer Contact'),
        )

        # As an account manager, Will Jones is associated with Marc
        # Martinez's role as Customer Contact.
        will.roles.first.role_roles += party.role_role(
            begin   =  primative.datetime('2017-11-12'),
            object  =  marc.roles.last,
        )

        # Create objectivetypes
        isc = party.objectivetype(name='Initial sales call')
        ipd = party.objectivetype(name='Initial product demonstration')
        dop = party.objectivetype(name='Demo of product')
        sc  = party.objectivetype(name='Sales close')
        god = party.objectivetype(name='Gather order details')
        cs  = party.objectivetype(name='Customer service')
        fu  = party.objectivetype(name='Follow-up')
        css = party.objectivetype(name='Customer satisfacton survey')

        # The role_role association between Will Jones and Marc Martinez
        # will have four ``communication`` events.
        comms = will.roles.first.role_roles.last.communications

        comms += party.inperson(
            begin = primative.datetime('Jan 12, 2001, 3PM'),
        )

        comms.last.communicationstatus = \
                party.communicationstatus(name='Completed')

        comms.last.objectives += party.objective(
            objectivetype = isc
        )

        comms.last.objectives += party.objective(
            objectivetype = ipd
        )

        comms += party.webinar(
            begin = primative.datetime('Jan 30, 2001, 2PM'),
            communicationstatus = \
                party.communicationstatus(name='Completed'),
        )

        comms.last.objectives += party.objective(
            objectivetype = dop
        )

        comms += party.inperson(
            begin = primative.datetime('Feb 12, 2002, 10PM'),
            communicationstatus = \
                party.communicationstatus(name='Completed'),
        )

        comms.last.objectives += party.objective(
            objectivetype = sc
        )

        comms.last.objectives += party.objective(
            objectivetype = god
        )

        comms += party.phonecall(
            begin = primative.datetime('Feb 12, 2002, 1PM'),
            communicationstatus = \
                party.communicationstatus(name='Scheduled'),
        )

        comms.last.objectives += party.objective(
            objectivetype = cs
        )

        comms.last.objectives += party.objective(
            objectivetype = fu
        )

        comms.last.objectives += party.objective(
            objectivetype = css
        )

        will.save(marc, john)

        will1 = will.orm.reloaded()
        marc1 = marc.orm.reloaded()
        john1 = john.orm.reloaded()

        comms = will.roles.first.role_roles.first.communications
        comms1 = will1.roles.first.role_roles.first.communications

        comms.sort()
        comms1.sort()

        self.four(comms)
        self.four(comms1)

        for comm, comm1 in zip(comms, comms1):
            self.eq(comm.id, comm1.id)

            self.eq(
                comm.communicationstatus.id, 
                comm1.communicationstatus.id
            )

            self.eq(
                comm.communicationstatus.name, 
                comm1.communicationstatus.name
            )




            # FIXME:a2e32ce8
            continue




            objs  = comm.objectives.sorted()

            # FIXME:a2e32ce8 Calling comm1.objectives is raises
            # AttributeError.  This is because a strang error is
            # happening where comm1.orm.mappings doesn't have the
            # ``objective`` entitymapping, even though comm.orm.mapping
            # does. This happend when I consolidated this test into
            # `gem_party`
            objs1 = comm1.objectives.sorted()

            self.eq(objs.count,  objs1.count)
            self.gt(objs.count,  0)

            for obj, obj1 in zip(objs, objs1):
                self.eq(obj.id, obj1.id)
                self.eq(None, obj1.name)
                self.eq(obj.objectivetype.id, obj1.objectivetype.id)
                self.eq(obj.objectivetype.name, obj1.objectivetype.name)

    @staticmethod
    def getvalidregion():
        return party.region.create(
            ('United States of America',  party.region.Country,    'USA'),
            ('Arizona',                   party.region.State,      'AZ'),
            ('Scottsdale',                party.region.City),
            ('85281',                     party.region.Postal)
        )

    def it_creates(self):
        party.region.orm.recreate()

        reg = party.region.create(
            ('United States of America',  party.region.Country,    'USA'),
            ('Arizona',                   party.region.State,      'AZ'),
            ('Scottsdale',                party.region.City),
            ('85224',                     party.region.Postal)
        )

        self.eq('85224', reg.name)
        self.zero(reg.regions)

        reg = reg.region
        self.eq('Scottsdale', reg.name)
        self.one(reg.regions)

        reg = reg.region
        self.eq('Arizona', reg.name)
        self.one(reg.regions)

        reg = reg.region
        self.eq('United States of America', reg.name)
        self.one(reg.regions)
        self.none(reg.region)

        reg = party.region.create(
            ('United States of America',  party.region.Country,    'USA'),
            ('Arizona',                   party.region.State,      'AZ'),
            ('Scottsdale',                party.region.City),
            ('85254',                     party.region.Postal)
        )

    def it_associates_address_with_region(self):
        # Create address and region
        addr = self.getvalidaddress()
        reg = self.getvalidregion()

        # Create association
        ar = party.address_region()
        ar.region = reg

        # Associate
        addr.address_regions += ar

        # Save
        addr.save()

        # Reload
        addr1 = party.address(addr.id)

        # Test
        self.one(addr1.address_regions)

        reg1 = addr1.address_regions.first.region

        self.eq(reg.name, reg1.name)

    def it_creates_skills(self):
        per = party.person(first='John', last='Smith')

        per.skills += party.skill(
            years = 20,
            rating = 10,
            skilltype = party.skilltype(name='Project management')
        )

        per.skills += party.skill(
            years = 5,
            rating = 6,
            skilltype = party.skilltype(name='Marketing')
        )

        per.save()

        per1 = per.orm.reloaded()

        self.eq(per.id, per1.id)

        sks = per.skills.sorted()
        sks1 = per1.skills.sorted()

        self.two(sks)
        self.two(sks1)

        for ks, ks1 in zip(sks, sks1):
            self.eq(ks.id, ks1.id)
            self.eq(ks.years, ks1.years)
            self.eq(ks.rating, ks1.rating)
            self.eq(ks.skilltype.id, ks1.skilltype.id)

    def it_returns_same_anonymous(self):
        self.is_(
            party.party.anonymous,
            party.party.anonymous,
        )

class contactmechanism(tester.tester):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.rebuildtables:
            es = orm.orm.getentityclasses(includeassociations=True)
            mods = 'party',
            for e in es:
                if e.__module__ in mods:
                    e.orm.recreate()

        self.recreateprinciples()

    def it_calls_creatability(self):
        with orm.override(False):
            with orm.sudo():
                usr = ecommerce.user(name='anyone')
                usr.save()

            with orm.su(usr):
                name = f'{uuid4().hex}@carapacian.com'
                em = party.email(name=name)
                self.expect(None, em.save)

    def it_calls_retrievability(self):
        with orm.override(False):
            with orm.sudo():
                usr = ecommerce.user(name='someone')
                usr1 = ecommerce.user(name='someone else')
                usr.save(usr1)

            with orm.su(usr):
                name = f'{uuid4().hex}@carapacian.com'
                em = party.email(name=name)
                em.save()

            with orm.su(bot.sendbot.user):
                self.expect(None, em.orm.reloaded)

            with orm.su(usr):
                self.expect(orm.AuthorizationError, em.orm.reloaded)

class case(tester.tester):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        orm.security().override = True
        es = orm.orm.getentityclasses(includeassociations=True)

        if self.rebuildtables:
            for e in es:
                if e.__module__ in ('party', 'apriori'):
                    e.orm.recreate()

        orm.security().owner = ecommerce.users.root

        com = party.company(name='Carapacian')
        orm.security().proprietor = com
        com.save(com)

    def it_raises_on_invalid_call_of_casesstatus(self):
        self.expect(ValueError, lambda: party.casestatus('Active'))
        self.expect(None, lambda: party.casestatus(name='Active'))

    def it_associates_case_to_party(self):
        jerry = party.person(first="Jerry", last="Red")

        # Create case
        cs = party.case(
            description = 'Techinal support issue with customer: '
                          'software keeps crashing',
            casestatus = party.casestatus(name='Active')
        )

        # Associate case with party
        jerry.case_parties += party.case_party(
            case = cs,
        )

        jerry.case_parties.last.caseroletype = party.caseroletype(
           name = 'Resolution lead'
        )

        jerry.save()

        jerry1 = jerry.orm.reloaded()

        cps = jerry.case_parties
        cps1 = jerry1.case_parties

        self.one(cps)
        self.one(cps1)

        self.eq(cps.first.id,       cps1.first.id)
        self.eq(jerry.id,           cps1.first.party.id)
        self.eq(cps.first.case.id,  cps1.first.case.id)
        self.eq(cps.first.caseroletype.id,  cps1.first.caseroletype.id)

        self.eq(
            cps.first.case.casestatus.id,
            cps1.first.case.casestatus.id
        )

        self.eq(cps.first.caseroletype.id,  cps1.first.caseroletype.id)
        self.eq(
            cps.first.caseroletype.name,
            cps1.first.caseroletype.name
        )

    def it_appends_communications(self):
        # Create work effort
        eff = party.effort(
            name = 'Software patch',
            description = 'Send software patch out to customer '
                          'to correct problem'
        )

        # Create case
        cs = party.case(
            description = 'Techinal support issue with customer: '
                          'software keeps crashing',
            casestatus = party.casestatus(name='Active')
        )

        # Add `commuication` events to `case` along with communication
        # objectives, work effort associations, etc.
        cs.communications += party.communication(
            begin = primative.datetime('Sept 18 2001, 3PM'),
        )

        comm = cs.communications.last
        comm.objectives += \
            party.objective(
                objectivetype = \
                    party.objectivetype(
                        name='Technical support call'
                    )
            ) \
            + party.objective(
                objectivetype = \
                    party.objectivetype(
                        name='Technical support call'
                    )
            )

        comm.communication_efforts += party.communication_effort(
            effort = eff
        )

        cs.communications += party.communication(
            begin = primative.datetime('Sept 20 2001, 2PM'),
        )
        comm = cs.communications.last

        comm.objectives += \
            party.objective(
                objectivetype = \
                    party.objectivetype(
                        name='Send software patch'
                    )
            )

        comm.communication_efforts += party.communication_effort(
            effort = eff
        )

        cs.communications += party.communication(
            begin = primative.datetime('Sept 19 2001, 3PM'),
        )
        comm = cs.communications.last

        comm.objectives += \
            party.objective(
                objectivetype = \
                    party.objectivetype(
                        name='Techinal support follow-up'
                    )
            ) \
            + party.objective(
                objectivetype = \
                    party.objectivetype(
                        name='Call resolution'
                    )
            )

        cs.save()

        cs1 = cs.orm.reloaded()

        comms = cs.communications.sorted()
        comms1 = cs1.communications.sorted()

        self.three(comms)
        self.three(comms1)

        for comm, comm1 in zip(comms, comms1):
            self.eq(comm.id, comm1.id)
            self.eq(comm.begin, comm1.begin)

            ces = comm.communication_efforts
            ces1 = comm1.communication_efforts

            self.eq(ces.count, ces1.count)

            for ce, ce1 in zip(ces, ces1):
                self.eq(ce.id, ce1.id)
                self.eq(ce.description, ce1.description)
                self.eq(ce.effort.id, ce1.effort.id)
                self.eq(ce.communication.id, ce1.communication.id)

if __name__ == '__main__':
    tester.cli().run()
