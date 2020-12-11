#! /usr/bin/python3
# vim: set et ts=4 sw=4 fdm=marker

########################################################################
# Copyright (C) Jesse Hogan - All Rights Reserved                      #
# Unauthorized copying of this file, via any medium is strictly        #
# prohibited                                                           #
# Proprietary and confidential                                         #
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2020                 #
########################################################################

from dbg import B
import ecommerce, party, product
import orm
import tester
import primative

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

    def it_creates_needs(self):
        per = party.person(name='Web Surfer')
        prosp = party.prospect()

        per.roles += prosp

        need = party.need(
            name = None,
            needtype = party.needtype(
                name='Information packet requested'
            ),
            communication = party.communication(
                note = 'Web site request for information packet'
            )
        )

        need.save()

        need1 = need.orm.reloaded()

        self.eq(need.id, need1.id)
        self.eq(need.needtype.id, need1.needtype.id)
        self.eq(need.communication.id, need1.communication.id)

    def it_creates_visits(self):
        parties = party.parties()

        anon = party.party.anonymous
        parties += anon
        visitor = ecommerce.visitor()
        anon.roles += visitor

        visitor.visits += ecommerce.visit(
            begin = '12/31/1999 23:50:00',
            end   = '1/1/2000 00:10:53',
        )

        visitor.visits.last.hits += ecommerce.hit(
            datetime = '12/31/1999 23:50:00',
            size = 100,
            ip = ecommerce.ip(address='10.10.10.1'),
            # useragent = 
            # content = 
        )

        parties.save()

        for par in parties:
            vistor = par.roles.first
            for visit in visitor.visits:
                visit1 = visit.orm.reloaded()
                self.eq(visit.begin, visit1.begin)
                self.eq(visit.end, visit1.end)

                for hit in visit1.hits:
                    self.eq(hit.datetime, hit.datetime)
                    self.eq(hit.size, hit.size)
                    self.eq(hit.ip.id, hit.ip.id)

    def it_ensures_url(self):
        address = 'https://www.thedailywtf.com'
        url = ecommerce.url(address=address)
        self.false(url.orm.isnew)

        url1 = ecommerce.url(address=address)

        self.eq(url.id, url1.id)
        self.eq(address, url.address)
        self.eq(address, url1.address)

        url1 = ecommerce.url(url1.id)

        self.eq(url.id, url1.id)
        self.eq(address, url.address)

    def it_ensures_ips(self):
        ip = ecommerce.ip(address='127.0.0.2')
        self.false(ip.orm.isnew)

        ip1 = ecommerce.ip(address='127.0.0.2')

        self.eq(ip.id, ip1.id)
        self.eq('127.0.0.2', ip.address)
        self.eq('127.0.0.2', ip1.address)

        ip1 = ecommerce.ip(ip1.id)

        self.eq(ip.id, ip1.id)
        self.eq('127.0.0.2', ip.address)

    def it_ensures_browsertype(self):
        brw = ecommerce.browsertype(
            name = 'Mozilla',
            version = '5.2',
        )
        self.false(brw.orm.isnew)

        brw1 = ecommerce.browsertype(
            name = 'Mozilla',
            version = '5.2',
        )

        self.eq(brw.id,       brw1.id)
        self.eq('Mozilla',    brw1.name)
        self.eq('5.2',       brw1.version)
        self.eq(brw.name,     brw1.name)
        self.eq(brw.version,  brw1.version)

    def it_ensures_devicetype(self):
        B()
        dev = ecommerce.devicetype(
            name = 'iPhone',
            brand = 'Apple',
            model = 'iPhone',
        )
        self.false(dev.orm.isnew)

        dev1 = ecommerce.devicetype(
            name  = 'iPhone',
            brand = 'Apple',
            model = 'iPhone',
        )

        self.eq(dev.id,       dev1.id)
        self.eq('iPhone',    dev1.name)
        self.eq('Apple',       dev1.brand)
        self.eq('iPhone',       dev1.model)

    def it_calls__str__(self):
        ip = ecommerce.ip(address='127.0.0.2')
        self.eq('127.0.0.2', str(ip))

class test_visits(tester.tester):

    def it_calls_current(self):
        per = party.person(name='Henry Ford')

        visitor = per.visitor

        visits = visitor.visits 

        now = primative.datetime.utcnow()
        visitor.visits += ecommerce.visit(
            begin = now.add(hours=-1)
        )

        self.none(visitor.visits.current)

        visitor.visits += ecommerce.visit(
            begin = now
        )

        visit = visitor.visits.current

        self.is_(visitor.visits.last, visit)

class test_visit(tester.tester):

    def it_calls_iscurrent(self):
        now = primative.datetime.utcnow()

        visit = ecommerce.visit(
            begin = now.add(minutes=-60),
            end = None
        )

        self.false(visit.iscurrent)

        visit = ecommerce.visit(
            begin = now.add(minutes=-45),
            end = None
        )

        self.false(visit.iscurrent)

        visit = ecommerce.visit(
            begin = now.add(minutes=-25),
            end = None
        )

        self.true(visit.iscurrent)

        visit = ecommerce.visit(
            begin = now.add(minutes=-25),
            end = now.add(minutes=-15)
        )

        self.false(visit.iscurrent)

if __name__ == '__main__':
    tester.cli().run()
