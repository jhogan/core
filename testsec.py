#!/usr/bin/python3
# vim: set et ts=4 sw=4 fdm=marker

########################################################################
# Copyright (C) Jesse Hogan - All Rights Reserved                      #
# Unauthorized copying of this file, via any medium is strictly        #
# prohibited                                                           #
# Proprietary and confidential                                         #
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2020                 #
########################################################################

# TODO Test streaming queries
# TODO Test match/full-text queries
# TODO Test eager loaded queries (I think)
# TODO Make sure testsec is being imported by test.py
# TODO Test updating records
# TODO Test deleting records
# TODO Test loading constituents, composites and associations

import orm, tester, party, db
from func import B

class engineers(orm.entities):
    pass

class engineer(orm.entity):
    name = str
    @classmethod
    def getvalid(cls):
        return cls()

    skills = str

class hackers(engineers):
    pass

class hacker(engineer):
    handle = str

class phreaks(hackers):
    pass

class phreak(hacker):
    boxes = str

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

    def it_filters_entity_based_on_proprietor(self):
        """ By default, queries should only be able to return records 
        belonging to the proprietor as defined by orm.orm.proprietor.
        """

        # Create some proprietors
        tsla = party.company(name='Tesla')
        ms = party.company(name='Microsoft')

        # If orm.orm.proprietor is None, no filtering should take place.
        # This shouldn't be allowed except for system administration
        # tasks.
        orm.orm.setproprietor(tsla)

        # Save an engineer record whose proprietor is Tesla
        eng = engineer()
        eng.save()

        # Set orm.orm.proprietor is None. We should be able to query this
        # engineer without RecordNotFoundError being thrown. We sort of
        # have "root" access because orm.orm.proprietor is None.
        orm.orm.setproprietor(None)
        self.expect(None, lambda: engineer(eng.id))

        # Set the orm.orm.proprietor to tsla. Still no problems getting
        # the Tesla engineer because the orm.orm.proprietor is Tesla.
        orm.orm.setproprietor(tsla)
        engineer(eng.id)
        self.expect(None, lambda: engineer(eng.id))

        # Now that the orm.orm.proprietor is Microsoft, we should not be
        # able to access the engineer record owned by Tesla.
        orm.orm.setproprietor(ms)
        self.expect(db.RecordNotFoundError, lambda: engineer(eng.id))

    def it_searches_entities_based_on_proprietor(self):
        engineers.orm.truncate()
        # Create some proprietors
        tsla = party.company(name='Tesla')
        ms = party.company(name='Microsoft')

        # Create some Tesla engineers
        orm.orm.setproprietor(tsla)
        engs = engineers()
        for i in range(3):
            engs += engineer(
                name   = f'Tesla engineer {i}',
                skills = 'c++'
            )

        engs.save()

        # Create some Microsoft engineers
        orm.orm.setproprietor(ms)
        for i in range(3):
            engs += engineer(
                name   = f'Microsoft engineer {i}',
                skills = 'c++'
            )

        engs.save()

        ids = engs.pluck('id')
        self.six(ids)

        # Set proprietor and run the same query. Make sure only the the
        # entities that the proprietor ows are returned
        for com in (tsla, ms):
            orm.orm.setproprietor(com)

            # Test IN operator
            engs = engineers(
                f"id in ({','.join(['%s'] * len(ids))})", ids
            )
            self.three(engs)
            for eng in engs:
                self.true(
                    eng.name.startswith(f'{com.name} engineer')
                )

            # Proprietor is currently set to {com.name}. We should be
            # able to query for all the {com.name} engineers
            engs = engineers("name LIKE %s", '%engineer%')
            self.three(engs)
            for eng in engs:
                self.true(eng.name.startswith(f'{com.name} engineer'))

            # Use a non-parameterized query. Note that this results in a
            # mixed query; i.e., partially parameterized and partially
            # not::
            #
            #   engs = engineers(
            #     "skills = 'c++', proprietor__partyid = %s", ['c70...']
            #  )
            engs = engineers("skills = 'c++'", ())
            self.three(engs)
            for eng in engs:
                self.true(eng.name.startswith(f'{com.name} engineer'))

            # Test two-value query (equality)
            engs = engineers('skills', 'c++')
            self.three(engs)
            for eng in engs:
                self.true(eng.name.startswith(f'{com.name} engineer'))

            # Test with *args
            wh = "name LIKE %s AND skills = %s"
            engs = engineers(wh, ('%engineer%',), 'c++')
            self.three(engs)
            for eng in engs:
                self.true(eng.name.startswith(f'{com.name} engineer'))

            # Test conjunctive
            wh = "name LIKE %s AND skills = %s"
            engs = engineers(wh, ('%engineer%', 'c++'))
            self.three(engs)
            for eng in engs:
                self.true(eng.name.startswith(f'{com.name} engineer'))

            # kwargs query
            engs = engineers(skills = 'c++')
            self.three(engs)
            for eng in engs:
                self.true(eng.name.startswith(f'{com.name} engineer'))

            # Literal with kwargs
            engs = engineers(
                "name LIKE '%engineer%'", (), skills = 'c++'
            )
            self.three(engs)
            for eng in engs:
                self.true(eng.name.startswith(f'{com.name} engineer'))

    def it_searches_subentities_based_on_proprietor(self):
        engineers.orm.truncate()
        hackers.orm.truncate()

        # Create some proprietors
        tsla = party.company(name='Tesla')
        ms = party.company(name='Microsoft')

        # Create some Tesla hackers
        orm.orm.setproprietor(tsla)
        hckrs = hackers()
        for i in range(3):
            hckrs += hacker(
                name   = f'Tesla hacker {i}',
                skills = 'c++',
                handle = 'Neo',
            )

        hckrs.save()

        # Create some Microsoft engineers
        orm.orm.setproprietor(ms)
        for i in range(3):
            hckrs += hacker(
                name   = f'Microsoft hacker {i}',
                skills = 'c++',
                handle = 'Neo',
            )

        hckrs.save()

        ids = hckrs.pluck('id')
        self.six(ids)

        for com in (tsla, ms):
            orm.orm.setproprietor(com)

            # Test IN operator
            hckrs = hackers(
                f"id in ({','.join(['%s'] * len(ids))})", ids
            )
            self.three(hckrs)
            for hckr in hckrs:
                self.true(
                    hckr.name.startswith(f'{com.name} hacker')
                )

            
            # Proprietor is currently set to {com.name}. We should be
            # able to query for all the {com.name} hackers
            hckrs = hackers("name LIKE %s", '%hacker%')
            self.three(hckrs)
            for hckr in hckrs:
                self.true(hckr.name.startswith(f'{com.name} hacker'))

            # Use a non-parameterized query. Note that this results in a
            # mixed query; i.e., partially parameterized and partially
            # not::
            #
            #   hckrs = hackers(
            #     "skills = 'c++', proprietor__partyid = %s", ['c70...']
            #  )
            hckrs = hackers("skills = 'c++'", ())
            self.three(hckrs)
            for hckr in hckrs:
                self.true(hckr.name.startswith(f'{com.name} hacker'))

            # Test two-value query (equality)
            hckrs = hackers('skills', 'c++')
            self.three(hckrs)
            for hckr in hckrs:
                self.true(hckr.name.startswith(f'{com.name} hacker'))

            # Test with *args
            wh = "name LIKE %s AND skills = %s"
            hckrs = hackers(wh, ('%hacker%',), 'c++')
            self.three(hckrs)
            for hckr in hckrs:
                self.true(hckr.name.startswith(f'{com.name} hacker'))

            # Test conjunctive
            wh = "name LIKE %s AND skills = %s"
            hckrs = hackers(wh, ('%hacker%', 'c++'))
            self.three(hckrs)
            for hckr in hckrs:
                self.true(hckr.name.startswith(f'{com.name} hacker'))

            # kwargs query
            hckrs = hackers(skills = 'c++')
            self.three(hckrs)
            for hckr in hckrs:
                self.true(hckr.name.startswith(f'{com.name} hacker'))

            # Literal with kwargs
            hckrs = hackers(
                "name LIKE '%hacker%'", (), skills = 'c++'
            )
            self.three(hckrs)
            for hckr in hckrs:
                self.true(hckr.name.startswith(f'{com.name} hacker'))

            # Test query with subentity column
            hckrs = hackers(handle = 'Neo')
            self.three(hckrs)
            for hckr in hckrs:
                self.true(hckr.name.startswith(f'{com.name} hacker'))

            # Test query with subentity column and superentity column
            hckrs = hackers(handle = 'Neo', skills = 'c++')
            self.three(hckrs)
            for hckr in hckrs:
                self.true(hckr.name.startswith(f'{com.name} hacker'))

    def it_searches_subsubentities_based_on_proprietor(self):
        engineers.orm.truncate()
        hackers.orm.truncate()
        phreaks.orm.truncate()

        # Create some proprietors
        tsla = party.company(name='Tesla')
        ms = party.company(name='Microsoft')

        # Create some Tesla phreaks
        orm.orm.setproprietor(tsla)
        phrs = phreaks()
        for i in range(3):
            phrs += phreak(
                name   = f'Tesla phreak {i}',
                skills = 'DTMF',
                handle = 'Captain Crunch',
                boxes = 'blue',
            )

        phrs.save()

        # Create some Microsoft engineers
        orm.orm.setproprietor(ms)
        for i in range(3):
            phrs += phreak(
                name   = f'Microsoft phreak {i}',
                skills = 'DTMF',
                handle = 'Captain Crunch',
                boxes = 'blue',
            )

        phrs.save()

        ids = phrs.pluck('id')
        self.six(ids)

        for com in (tsla, ms):
            orm.orm.setproprietor(com)

            # Test IN operator
            phrs = phreaks(
                f"id in ({','.join(['%s'] * len(ids))})", ids
            )
            self.three(phrs)
            for phr in phrs:
                self.true(
                    phr.name.startswith(f'{com.name} phreak')
                )

            # Proprietor is currently set to {com.name}. We should be
            # able to query for all the {com.name} phreaks
            phrs = phreaks("name LIKE %s", '%phreak%')
            self.three(phrs)
            for phr in phrs:
                self.true(phr.name.startswith(f'{com.name} phreak'))

            # Use a non-parameterized query. Note that this results in a
            # mixed query; i.e., partially parameterized and partially
            # not::
            #
            #   phrs = phreaks(
            #     "skills = 'c++', proprietor__partyid = %s", ['c70...']
            #  )
            phrs = phreaks("skills = 'DTMF'", ())
            self.three(phrs)
            for phr in phrs:
                self.true(phr.name.startswith(f'{com.name} phreak'))

            # Test two-value query (equality)
            phrs = phreaks('skills', 'DTMF')
            self.three(phrs)
            for phr in phrs:
                self.true(phr.name.startswith(f'{com.name} phreak'))

            # Test with *args
            wh = "name LIKE %s AND skills = %s"
            phrs = phreaks(wh, ('%phreak%',), 'DTMF')
            self.three(phrs)
            for phr in phrs:
                self.true(phr.name.startswith(f'{com.name} phreak'))

            # Test conjunctive
            wh = "name LIKE %s AND skills = %s"
            phrs = phreaks(wh, ('%phreak%', 'DTMF'))
            self.three(phrs)
            for phr in phrs:
                self.true(phr.name.startswith(f'{com.name} phreak'))

            # kwargs query
            phrs = phreaks(skills = 'DTMF')
            self.three(phrs)
            for phr in phrs:
                self.true(phr.name.startswith(f'{com.name} phreak'))

            # Literal with kwargs
            phrs = phreaks(
                "name LIKE '%phreak%'", (), skills = 'DTMF'
            )
            self.three(phrs)
            for phr in phrs:
                self.true(phr.name.startswith(f'{com.name} phreak'))

            # Test query with subsubentity column
            phrs = phreaks(boxes = 'blue')
            self.three(phrs)
            for phr in phrs:
                self.true(phr.name.startswith(f'{com.name} phreak'))


            # Test query with subentity column
            phrs = phreaks(handle = 'Captain Crunch')
            self.three(phrs)
            for phr in phrs:
                self.true(phr.name.startswith(f'{com.name} phreak'))

            # Test query with entity column.
            phrs = phreaks(skills='DTMF')
            self.three(phrs)
            for phr in phrs:
                self.true(phr.name.startswith(f'{com.name} phreak'))

    def it_makes_proprietors_self_owning(self):
        orm.orm.setproprietor(None)

        tsla = party.company(name='Tesla')

        # At this point, tsla will not have a record proprietor
        self.none(tsla.proprietor)

        orm.orm.setproprietor(tsla)

        # After setting tsla as the proprietor, tlsa, and its supers,
        # will have tsla as their proprietors.
        sup = tsla
        while sup:
            self.is_(tsla, sup.proprietor)
            sup = sup.orm.super

        tsla.save()

        sup = tsla.orm.reloaded()

        while sup:
            self.eq(tsla.id, sup.proprietor.id)
            sup = sup.orm.super

        
if __name__ == '__main__':
    tester.cli().run()
