#!/usr/bin/python3
# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2022

import apriori; apriori.model()

from datetime import timezone, datetime, date
from dbg import B, PM
from func import enumerate, getattr
from uuid import uuid4, UUID
import carapacian_com
import orm
import party
import pom
import tester

class sites(tester.tester):
    def it_inherits_from_pom_site(self):
        wss = carapacian_com.sites()
        self.isinstance(wss, pom.sites)

class site(tester.tester):
    def it_has_correct_id(self):
        # Set constant
        Id = UUID(hex='c0784fca-3fe7-45e6-87f8-e2ebbc4e7bf4')

        # Test class-level constant
        self.eq(Id, carapacian_com.site.Id)

        # Test instance
        self.eq(Id, carapacian_com.site().id)

    def it_has_correct_proprietor(self):
        cara = party.company.carapacian
        self.is_(cara, carapacian_com.site().Proprietor)

    def it_has_correct_host(self):
        Host = 'carapacian.com'
        self.eq(Host, carapacian_com.site().host)

    def it_has_correct_title(self):
        Title = 'Carapacian Sustainable Software'

        ws = carapacian_com.site()

        self.eq(Title, ws.title)

    def it_has_carapacian_as_its_proprietor(self):
        ws = carapacian_com.site()
        self.eq(ws.proprietor.id, party.company.carapacian.id)

''' Page tests '''

class home(tester.tester):
    def it_call_name(self):
        pg = carapacian_com.home()
        self.eq('index', pg.name)

    def it_GETs(self):
        ws = carapacian_com.site()
        tab = self.browser().tab()

        res = tab.get('/', ws)
        self.status(200, res)

        self.eq(f'{ws.title} | Index', res['html>head>title'].text)

    def it_has_correct_title(self):
        Title = 'Carapacian Sustainable Software | Index'

        tab = self.browser().tab()
        ws = carapacian_com.site()
        res = tab.get('/', ws)
        self.startswith(Title, res['html>head>title'].text)

if __name__ == '__main__':
    tester.cli().run()

