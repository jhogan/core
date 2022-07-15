#!/usr/bin/python3
# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2022

from datetime import timezone, datetime, date
from dbg import B, PM
from func import enumerate, getattr
from uuid import uuid4, UUID
import dom
import party
import pom
import ecommerce
import file

class sites(pom.sites):
    pass

class site(pom.site):
    Id = UUID(hex='c0784fca-3fe7-45e6-87f8-e2ebbc4e7bf4')

    Proprietor = party.company.carapacian
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.host = 'carapacian.com'

        self.title = 'Carapacian Sustainable Software'

        self.keywords = 'carapacian core technical debt'

        self.metadescription = 'Your partners in technical debt managment'

        try:
            with orm.proprietor(Proprietor):
                self.resources += file.resource(
                    url = 'https://carapacian.com/css/brightlight-green.css'
                )
        except Exception as ex:
            PM(ex)

        self.pages += home()

    @property
    def header(self):
        hdr = super().header

        hdr.logo = pom.logo(
            'Carapacian Logo',
            href = 'https://carapacian.com',
            img  = 'https://carapacian.com/images/logo.png',
        )

        mnu = hdr.menu

        itms = mnu.items 

        itms.clear()

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
