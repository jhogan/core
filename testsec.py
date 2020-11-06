#!/usr/bin/python3
# vim: set et ts=4 sw=4 fdm=marker

########################################################################
# Copyright (C) Jesse Hogan - All Rights Reserved                      #
# Unauthorized copying of this file, via any medium is strictly        #
# prohibited                                                           #
# Proprietary and confidential                                         #
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2020                 #
########################################################################

import orm, tester, party, db
from func import B

class engineers(orm.entities):
    pass

class engineer(orm.entity):
    @classmethod
    def getvalid(cls):
        return cls()
        
class hackers(engineers):
    pass

class hacker(engineer):
    pass

class phreaks(hackers):
    pass

class phreak(hacker):
    pass

class systems(orm.entities):
    pass

class system(orm.entity):
    pass

class proprietor(tester.tester):
    def __init__(self):
        super().__init__()
        orm.orm.recreate(engineer, hacker, phreak)
        for e in orm.orm.getentitys(includeassociations=True):
            if e.__module__ in ('party', 'apriori'):
                e.orm.recreate()

    def it_adds_proprietor_to_entity(self):
        ''' Test class (static attribute)'''
        orm.orm.setproprietor(None)

        # Test the map
        map = engineer.orm.mappings['proprietor']
        self.eq('proprietor', map.name)
        self.type(orm.entitymapping, map)

        # Ensure only one
        self.one([
            x for x in engineer.orm.mappings 
            if x.name == 'proprietor'
        ])

        # proprietor should be a `party`
        self.is_(party.party, map.entity)

        ''' Test object '''
        eng = engineer.getvalid()

        map = eng.orm.mappings['proprietor']
        self.eq('proprietor', map.name)
        self.isnot(
            engineer.orm.mappings['proprietor'],
            map
        )
        self.type(orm.entitymapping, map)

        # Ensure only one
        self.one([
            x for x in eng.orm.mappings 
            if x.name == 'proprietor'
        ])

        self.none(eng.proprietor)

        proprietor = party.person(name='Malcolm McLaren')

        eng.proprietor = proprietor

        eng.save()

        eng1 = eng.orm.reloaded()

        self.eq(eng.id, eng1.id)
        self.eq(eng.proprietor.id, eng1.proprietor.id)

    def it_adds_proprietor_to_subentity(self):
        ''' Test class (static attribute)'''
        orm.orm.setproprietor(None)

        # Test the map
        map = hacker.orm.mappings['proprietor']
        self.eq('proprietor', map.name)
        self.type(orm.entitymapping, map)

        # Ensure only one
        self.one([
            x for x in hacker.orm.mappings 
            if x.name == 'proprietor'
        ])

        # proprietor should be a `party`
        self.is_(party.party, map.entity)

        ''' Test object '''
        hckr = hacker.getvalid()

        map = hckr.orm.mappings['proprietor']
        self.eq('proprietor', map.name)
        self.isnot(
            hacker.orm.mappings['proprietor'],
            map
        )
        self.type(orm.entitymapping, map)

        # Ensure only one
        self.one([
            x for x in hckr.orm.mappings 
            if x.name == 'proprietor'
        ])

        self.none(hckr.proprietor)

        proprietor = party.person(name='Malcolm McLaren')

        hckr.proprietor = proprietor

        hckr.save()

        hckr1 = hckr.orm.reloaded()

        self.eq(hckr.id, hckr1.id)
        self.eq(hckr.proprietor.id, hckr1.proprietor.id)

        # NOTE The super's proprietor is None. This is inaccurate and
        # probably would be for almost any given situation. I'm not sure
        # what to do about it at the moment. Maybe `proprietor` should
        # be an @orm.attr getter that looks up and down the graph for a
        # proprietor.
        self.none(hckr.orm.super.proprietor)

    def it_adds_proprietor_to_subsubentity(self):
        ''' Test class (static attribute)'''
        orm.orm.setproprietor(None)

        # Test the map
        map = phreak.orm.mappings['proprietor']
        self.eq('proprietor', map.name)
        self.type(orm.entitymapping, map)

        # Ensure only one
        self.one([
            x for x in phreak.orm.mappings 
            if x.name == 'proprietor'
        ])

        # proprietor should be a `party`
        self.is_(party.party, map.entity)

        ''' Test object '''
        phr = phreak.getvalid()

        map = phr.orm.mappings['proprietor']
        self.eq('proprietor', map.name)
        self.isnot(
            phreak.orm.mappings['proprietor'],
            map
        )
        self.type(orm.entitymapping, map)

        # Ensure only one
        self.one([
            x for x in phr.orm.mappings 
            if x.name == 'proprietor'
        ])

        self.none(phr.proprietor)

        proprietor = party.person(name='Malcolm McLaren')

        phr.proprietor = proprietor

        phr.save()

        phr1 = phr.orm.reloaded()

        self.eq(phr.id, phr1.id)
        self.eq(phr.proprietor.id, phr1.proprietor.id)

        # NOTE The super's proprietor is None. This is inaccurate and
        # probably would be for almost any given situation. I'm not sure
        # what to do about it at the moment. Maybe `proprietor` should
        # be an @orm.attr getter that looks up and down the graph for a
        # proprietor.
        self.none(phr.orm.super.proprietor)
        self.none(phr.orm.super.orm.super.proprietor)

    def it_sets_proprietor_from_sec(self):
        """
        """
        tsla = party.company(name='Tesla')
        orm.orm.setproprietor(tsla)

        ''' Test object '''
        eng = engineer.getvalid()

        self.is_(tsla, eng.proprietor)

        eng.save()

        # Ensure it can be changed after a save()
        eng = eng.orm.reloaded()

        self.eq(tsla.id, eng.proprietor.id)

        malcolm = party.person(name='Malcolm McLaren')
        eng.proprietor = malcolm

        self.is_(malcolm, eng.proprietor)
        eng.save()

        eng = eng.orm.reloaded()
        self.eq(malcolm.id, eng.proprietor.id)

    def it_propogates_proprietor_to_supers(self):
        """ When an subentity is newly created, it's supers should have
        the same proprietor.
        """
        tsla = party.company(name='Tesla')
        orm.orm.setproprietor(tsla)

        # Test without saving.
        phr = phreak()
        self.eq(tsla.id, phr.orm.super.orm.super.proprietor.id)
        self.eq(tsla.id, phr.orm.super.proprietor.id)

        # Save immediatly then test
        phr = phreak()
        phr.save()

        eng = engineer(phr)
        self.eq(tsla.id, eng.proprietor.id)

        hckr = hacker(phr)
        self.eq(tsla.id, hckr.proprietor.id)

        # TODO If eng's or hckr's proprietor were changed at this point,
        # it's supers and subs should be updated with the new
        # proprietor. Let's wait to see if this is an actual need. The
        # ui developer could do this manually if it ever comes
        # up; though I'm not really sure what's best at this point.

    def it_filters_based_on_proprietor(self):
        """ By default, queries should only be able to return records 
        belonging to the proprietor as defined by sec.proprietor.
        """

        # Create som proprietors
        tsla = party.company(name='Tesla')
        ms = party.company(name='Microsoft')

        # If sec.proprietor is None, no filtering should take place.
        # This shouldn't be allowed except for system administration
        # tasks.
        sec.proprietor = tsla

        # Save an engineer record whose proprietor is Tesla
        eng = engineer()
        eng.save()

        # Set sec.proprietor is None. We should be able to query this
        # engineer without RecordNotFoundError being thrown. We sort of
        # have "root" access because sec.proprietor is None.
        sec.proprietor = None
        self.expect(None, lambda: engineer(eng.id))

        # Set the sec.proprietor to tsla. Still no problems getting
        # the Tesla engineer because the sec.proprietor is Tesla.
        sec.proprietor = tsla
        engineer(eng.id)
        self.expect(None, lambda: engineer(eng.id))

        # Now that the sec.proprietor is Microsoft, we should not be
        # able to access the engineer record owned by Tesla.
        sec.proprietor = ms
        self.expect(db.RecordNotFoundError, lambda: engineer(eng.id))

if __name__ == '__main__':
    tester.cli().run()
