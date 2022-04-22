#!/usr/bin/python3
# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2022

from datetime import timezone, datetime, date
from dbg import B
from func import enumerate, getattr
from uuid import uuid4
import pom
import dom

class sites(pom.sites):
    pass

class site(pom.site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.pages += home()

class home(pom.page):
    def main(self):
        pass

    @property
    def name(self):
        return 'index'
