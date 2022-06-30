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

class sites(pom.sites):
    pass

class site(pom.site):
    Id = UUID(hex='c0784fca-3fe7-45e6-87f8-e2ebbc4e7bf4')

    B()
    Proprietor = party.company.carapacian
    def __init__(self, *args, **kwargs):
        B()
        super().__init__(*args, **kwargs)
        
        self.pages += home()

class home(pom.page):
    def main(self):
        pass

    @property
    def name(self):
        return 'index'
