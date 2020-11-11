#!/usr/bin/python3
# vim: set et ts=4 sw=4 fdm=marker

########################################################################
# Copyright (C) Jesse Hogan - All Rights Reserved                      #
# Unauthorized copying of this file, via any medium is strictly        #
# prohibited                                                           #
# Proprietary and confidential                                         #
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2020                 #
########################################################################

import ecommerce, party
import tester
import orm

class test_ecommerce(tester.tester):
    def __init__(self):
        super().__init__()
        es = orm.orm.getentitys(includeassociations=True)
        for e in es:
            if e.__module__ in ('ecommerce', 'apriori', 'party'):
                e.orm.recreate()

    def it_connects_users_to_addresses(self):
        usr = ecommerce.user(name='jsmith')
        usr.party = party.person(name='John Smith')
        usr.address = ecommerce.address(
            url='www.travel_bookings_made_very_easy.com'
        )

        usr.preferences += ecommerce.preference(
            key = 'show top five', value = True
        )

        usr.save()

        usr1 = usr.orm.reloaded()

        self.eq(usr.party.id, usr1.party.id)
        self.eq(usr.address.id, usr1.address.id)
        self.eq(usr.id, usr1.id)

        prefs = usr.preferences.sorted()
        prefs1 = usr1.preferences.sorted()

        self.one(prefs)
        self.one(prefs1)

        for pref, pref1 in zip(prefs, prefs1):  
            self.eq(pref.id, pref1.id)

if __name__ == '__main__':
    tester.cli().run()
