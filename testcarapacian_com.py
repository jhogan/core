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
import tester
import pom
import party

class sites(tester.tester):
    def it_inherits_from_pom_site(self):
        wss = carapacian_com.sites()
        self.isinstance(wss, pom.sites)

class site(tester.tester):
    def it_has_carapacian_as_its_proprietor(self):
        ws = carapacian_com.site()
        self.eq(ws.proprietor.id, party.company.carapacian.id)
        

if __name__ == '__main__':
    tester.cli().run()

