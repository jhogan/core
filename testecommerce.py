#! /usr/bin/python3
# vim: set et ts=4 sw=4 fdm=marker

########################################################################
# Copyright (C) Jesse Hogan - All Rights Reserved                      #
# Unauthorized copying of this file, via any medium is strictly        #
# prohibited                                                           #
# Proprietary and confidential                                         #
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2020                 #
########################################################################

import ecommerce, party, product
import tester
import orm

# TODO Add `import testecommerce` to test.py

class test_ecommerce(tester.tester):
    def __init__(self):
        super().__init__()
        es = orm.orm.getentitys(includeassociations=True)
        mods = 'ecommerce', 'apriori', 'party', 'product'
        for e in es:
            if e.__module__ in mods:
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

    def it_creates_object(self):
        
        obj = ecommerce.object(
            name = 'LowRescar.jpeg',
            path = '/usr/share/LowRescar.jpeg'
        )

        obj.object_products += ecommerce.object_product(
            product = product.good(name='Sports 2001 Romonix Car')
        )

        obj.objecttype = ecommerce.objecttype(
            name = 'Low-resolution JPEG'
        )

        obj.object_purposes += ecommerce.object_purpose(
            purposetype = ecommerce.purposetype(name='web')
        )

        obj.content_objects += ecommerce.content_object(
            begin = 'January 5, 2001',
            end   = 'March 6, 2001',
            content = ecommerce.content(
                path = '/herp/derp',
                description='Related to "sports car web page"'
            )
        )

        obj.save()

        obj1 = obj.orm.reloaded()

        ops = obj.object_products.sorted()
        ops1 = obj1.object_products.sorted()

        self.one(ops)
        self.one(ops1)

        self.eq(ops.first.id, ops1.first.id)

        self.eq(obj.objecttype.id, obj1.objecttype.id)

        ops = obj.object_purposes.sorted()
        ops1 = obj1.object_purposes.sorted()

        self.one(ops)
        self.one(ops1)

        self.eq(ops.first.id, ops1.first.id)

        cos = obj.content_objects.sorted()
        cos1 = obj1.content_objects.sorted()

        self.one(cos)
        self.one(cos1)

        self.eq(cos.first.id, cos1.first.id)
        self.eq(cos.first.begin, cos1.first.begin)
        self.eq(cos.first.end, cos1.first.end)

        self.eq(cos.first.content.id, cos1.first.content.id)
        self.eq(cos.first.content.path, cos1.first.content.path)
        self.eq(
            cos.first.content.description, 
            cos1.first.content.description
        )


if __name__ == '__main__':
    tester.cli().run()
