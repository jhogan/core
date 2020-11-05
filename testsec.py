#!/usr/bin/python3
# vim: set et ts=4 sw=4 fdm=marker

########################################################################
# Copyright (C) Jesse Hogan - All Rights Reserved                      #
# Unauthorized copying of this file, via any medium is strictly        #
# prohibited                                                           #
# Proprietary and confidential                                         #
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2020                 #
########################################################################

import orm, tester, party, sec
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

class proprietor(tester.tester):
    def __init__(self):
        super().__init__()
        orm.orm.recreate(engineer, hacker, phreak)
        for e in orm.orm.getentitys(includeassociations=True):
            if e.__module__ in ('party', 'apriori'):
                e.orm.recreate()

    def it_adds_proprietor_to_entity(self):
        ''' Test class (static attribute)'''

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
        sec.proprietor = tsla

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

if __name__ == '__main__':
    tester.cli().run()
