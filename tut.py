# vim: set et ts=4 sw=4 fdm=marker

# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2019

from pdb import set_trace; B=set_trace
from tester import *

class test_entities(tester):
    def it_appends(self):
        class gods(entities):
            pass

        class god(entity):
            def __init__(self, name):
                self.name = name

            def __str__(self):
                return self.name

        norse_pantheon = gods()
        self.assertEq(norse_pantheon.count, 0)

        thor = god('Thor')
        odin = god('Odin')

        norse_pantheon.append(thor)
        norse_pantheon.append(odin)

        self.assertEq(norse_pantheon.count, 2)

        norse_pantheon.clear()

        self.assertEq(norse_pantheon.count, 0)
        self.assertTrue(norse_pantheon.isempty)

        norse_pantheon += thor
        norse_pantheon += odin
        self.assertEq(norse_pantheon.count, 2)

        norse_pantheon.clear()

        norse_pantheon += thor + odin
        self.assertEq(norse_pantheon.count, 2)

        self.assertIs(norse_pantheon[0], thor)
        self.assertIs(norse_pantheon[1], odin)

        self.assertIs(norse_pantheon['Thor'], thor)
        self.assertIs(norse_pantheon['Odin'], odin)

        self.assertIs(norse_pantheon.first, thor)
        self.assertIs(norse_pantheon.second, odin)

        for g in norse_pantheon:
            print(g.name)

        print(norse_pantheon)

    def it_calls_where(self):
        class deities(entities):
            pass

        class deity(entity):
            def __init__(self, name, gender):
                self.name = name
                self.gender = gender

            def __str__(self):
                return self.name

        pantheon = deities()
        pantheon  +=  deity('Aphrodite',   'female')
        pantheon  +=  deity('Apollo',      'male')
        pantheon  +=  deity('Ares',        'male')
        pantheon  +=  deity('Artemis',     'female')
        pantheon  +=  deity('Athena',      'female')
        pantheon  +=  deity('Demeter',     'female')
        pantheon  +=  deity('Hades',       'male')
        pantheon  +=  deity('Hephaestus',  'male')
        pantheon  +=  deity('Hera',        'female')
        pantheon  +=  deity('Hermes',      'male')
        pantheon  +=  deity('Hestia',      'female')
        pantheon  +=  deity('Poseidon',    'male')
        pantheon  +=  deity('Zeus',        'male')

        gods = pantheon.where(lambda x: x.gender == 'male')  
        goddesses = pantheon.where(lambda x: x.gender == 'female')  

        assert isinstance(gods, entities)
        assert isinstance(goddesses, entities)

        assert gods.count == 7
        assert goddesses.count == 6

        gods = pantheon.where(lambda x: x.name[0] == 'A' and x.gender == 'male')
        assert gods.count == 2
        assert gods[0].name == 'Apollo'
        assert gods[1].name == 'Ares'

    def it_determine_validity(self):
        
        class deities(entities):
            pass

        class deity(entity):
            def __init__(self, name, gender):
                self.name = name
                self.gender = gender

            def __str__(self):
                return self.name

        pantheon = deities()
        zeus = deity('Zeus', 'male')

        assert pantheon.isvalid 
        assert pantheon.brokenrules.count == 0

        assert zeus.isvalid 
        assert zeus.brokenrules.count == 0

        class deity(entity):
            def __init__(self, name, gender):
                self.name = name
                self.gender = gender

            @property
            def brokenrules(self):
                brs = brokenrules()
                if self.gender not in ('female', 'male'):
                    brs += '{} is an invalid gender.'.format(self.gender)

                if type(self.name) != str:
                    brs += 'Deity names must be strings.'

                return brs

            def __str__(self):
                return self.name

        zeus = deity(42, None)

        assert not zeus.isvalid

        assert str(zeus.brokenrules) == 'None is an invalid gender.\nDeity names must be strings.'

        pantheon = deities()
        pantheon += zeus

        assert not pantheon.isvalid
        assert str(pantheon.brokenrules) == 'None is an invalid gender.\nDeity names must be strings.'

        class deity(entity):
            def __init__(self, name, gender):
                self.name = name
                self.gender = gender
                self.children = deities()

            @property
            def brokenrules(self):
                brs = brokenrules()
                if self.gender not in ('female', 'male'):
                    brs += '{} is an invalid gender for "{}".'.format(self.gender, self.name)

                if type(self.name) != str:
                    brs += 'Deity names must be strings.'

                brs += self.children.brokenrules

                return brs

            def __str__(self):
                return self.name

        zeus = deity('Zeus', 'male')
        zeus.children += deity('Aeacus', 'm')
        zeus.children += deity('Angelos', 'female')
        zeus.children += deity('Aphrodite', 'female')
        zeus.children += deity('Apollo', 'male')
        zeus.children += deity('Ares', 'male')
        zeus.children += deity('Artemis', 'f')
        zeus.children += deity('Athena', 'female')

        assert not zeus.isvalid
        assert str(zeus.brokenrules) == 'm is an invalid gender for "Aeacus".\nf is an invalid gender for "Artemis".'




print(testers())
