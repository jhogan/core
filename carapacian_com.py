#!/usr/bin/python3
# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2022

from datetime import timezone, datetime, date
from dbg import B
from func import enumerate, getattr
from uuid import uuid4, UUID
import dom
import party
import pom
import ecommerce

class sites(pom.sites):
    pass

class site(pom.site):
    Id = UUID(hex='c0784fca-3fe7-45e6-87f8-e2ebbc4e7bf4')

    Proprietor = party.company.carapacian
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.host = 'carapacian.com'
        
        self.pages += home()

    @property
    def header(self):
        hdr = super().header

        mnu = hdr.menu

        itms = mnu.items 
        itms += pom.menu.item('Services')
        itms += pom.menu.item('Products')
        itms += pom.menu.item('Services')

        return hdr


class home(pom.page):
    def main(self):
        pass

    @property
    def name(self):
        return 'index'
