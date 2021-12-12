#!/usr/bin/python3
import apriori; apriori.model()
from datetime import timezone, datetime, date
from dbg import B
from func import enumerate, getattr
from uuid import uuid4
import pom
import tester
import orm
import dom

import apriori; apriori.model()

class home(pom.page):
    def __init__(self):
        super().__init__()

    @property
    def name(self):
        return 'home'

    def main(self):
        self.main += dom.p('Welcome to fast.net')

class fastnets(pom.sites):
    pass

class fastnet(pom.site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.host = 'fast.net'
        self.name = 'fast.net'

        self.pages += home()

class cpu_page(tester.benchmark):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        orm.security().override = True
        if self.rebuildtables:
            es = orm.orm.getentityclasses(includeassociations=True)
            mods = (
                'party', 'ecommerce', 'pom', 'asset', 'apriori',
            )

            for e in es:
                if e.__module__ in  mods:
                    e.orm.recreate()

        fastnet.orm.recreate()

    def it_gets(self):
        ws = fastnet()
        tab = self.browser().tab()

        def f():
            return tab.get('/en/home', ws)

        #self.time(2400, 2600, f, 1)
        #self.time(1400, 1800, f, 5)
        self.time(600, 800, f, 2)

        '''
        www.py:587(__call__) ->      1    0.000    0.497  dom.py:1750(html)
                                     1    0.000    0.558  pom.py:901(__call__)
                                     1    0.000    0.000  www.py:505(arguments)
                                     2    0.000    0.000  www.py:555(page)
                                     2    0.000    2.938  www.py:649(log)
        '''

if __name__ == '__main__':
    tester.cli().run()
