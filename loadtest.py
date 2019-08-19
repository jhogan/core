# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2019

from configfile import configfile
from pdb import Pdb
from tester import *
from uuid import uuid4
import dateutil
import orm

# Set conditional break points
def B(x=True):
    if x: 
        #Pdb().set_trace(sys._getframe().f_back)
        from IPython.core.debugger import Tracer; 
        Tracer().debugger.set_trace(sys._getframe().f_back)

class persons(orm.entities):
    pass

class person(orm.entity):
    firstname = str
    lastname = str

class test_load(stresstester):
    def __init__(self):
        super().__init__()
        person.reCREATE()

    def create_records(self):
        with self.within(4000) as t:
            for i in range(1000000):
                p = person()
                p.firstname = uuid4().hex
                p.lastname = uuid4().hex
                p.save()
                if i % 1000 == 0:

                    if i:
                        self.print(i, end=' ')
                        with self.time() as sw:
                            person(id)
                            self.print(sw.milliseconds)

                    id = p.id


            

stresscli.run()
