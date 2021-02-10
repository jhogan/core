# vim: set et ts=4 sw=4 fdm=marker

# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2020

"""
General entity classes for the Persistia ERP.
"""

import party
from entities import classproperty

class departments(party.departments):
    pass

class department(party.department):
    # TODO Ensure that there can be only one ERP Administration
    # department.
    @classproperty
    def erp(cls):
        Name = 'ERP Administration'
        deps = departments(name=Name)

        if deps.count:
            return deps.first
        else:
            return department(name=Name)

            

