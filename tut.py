# vim: set et ts=4 sw=4 fdm=marker
"""
MIT License

Copyright (c) 2016 Jesse Hogan

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
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




print(testers())
