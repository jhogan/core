#!/usr/bin/python3
# vim: set et ts=4 sw=4 fdm=marker

########################################################################
# Copyright (C) Jesse Hogan - All Rights Reserved                      #
# Unauthorized copying of this file, via any medium is strictly        #
# prohibited                                                           #
# Proprietary and confidential                                         #
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2021                 #
########################################################################

import apriori; apriori.model()

from dbg import B
from func import enumerate
from random import randint
from uuid import uuid4, UUID
import db
import entities
import decimal; dec=decimal.Decimal
import ecommerce
import orm
import party
import primative
import product
import tester
import uuid

def getvalidcompany(**kwargs):
    com = party.company()
    com.name = uuid4().hex
    com.ein = str(uuid4().int)[:9]
    com.nationalids    =  uuid4().hex
    com.isicv4         =  'A'
    com.dun            =  None

    for k, v in kwargs.items():
        setattr(com, k, v)
    return com

def getvalidregion():
    return party.region.create(
        ('United States of America',  party.region.Country,    'USA'),
        ('Arizona',                   party.region.State,      'AZ'),
        ('Scottsdale',                party.region.City),
        ('85281',                     party.region.Postal)
    )

class product_(tester.tester):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        orm.security().override = True

        if self.rebuildtables:
            for e in orm.orm.getentityclasses(includeassociations=True):
                if e.__module__ in ('product', ):
                    e.orm.recreate()

        orm.security().owner = ecommerce.users.root
        com = party.company(name='Carapacian')
        orm.security().proprietor = com
        com.save(com)

    @staticmethod
    def getvalid(type=None, comment=1000):
        if type is None:
            type = product.good

        prod = type()
        prod.name = uuid4().hex
        prod.introducedat = primative.date.today(days=-100)
        prod.comment = uuid4().hex * comment
        return prod

    @staticmethod
    def getvaliditem():
        pen = product.good(name='Henry #2 Pencil')
        itm = product.nonserial(quantity=1)
        itm.good = pen
        return itm

    def it_creates(self):
        for str_prod in ['good', 'service']:
            prod = getattr(product, str_prod)()

            prod.name = uuid4().hex
            prod.introducedat = primative.date.today(days=-100)
            prod.comment = uuid4().hex * 1000

            prod.save()

            prod1 = getattr(product, str_prod)(prod.id)

            props = (
                'id', 
                'name', 
                'introducedat', 
                'discontinuedat', 
                'unsupportedat', 
                'comment'
            )

            for prop in props:
                self.eq(getattr(prod, prop), getattr(prod1, prop), prop)

    def it_updates(self):
        for str_prod in ['good', 'service']:
            prod = getattr(product, str_prod)()

            prod.name = uuid4().hex
            prod.introducedat = primative.date.today(days=-100)
            prod.comment = uuid4().hex * 1000

            prod.save()

            prod1 = getattr(product, str_prod)(prod.id)

            prod1.name = uuid4().hex
            prod1.introducedat = primative.date.today(days=-200)
            prod1.discontinuedat = primative.date.today(days=+100)
            prod1.unsupportedat = primative.date.today(days=+200)
            prod1.comment = uuid4().hex * 1000

            prod1.save()

            prod2 = getattr(product, str_prod)(prod1.id)

            props = (
                'name', 
                'introducedat', 
                'discontinuedat', 
                'unsupportedat', 
                'comment'
            )

            for prop in props:
                self.ne(
                    getattr(prod, prop), 
                    getattr(prod2, prop), 
                    prop
                )
                self.eq(
                    getattr(prod1, prop), 
                    getattr(prod2, prop), 
                    prop
                )

    def it_associates_to_features(self):
        tup_colors = (
            'white',  'red',     'orange',  'blue',
            'green',  'purple',  'gray',    'cream',
        )

        tup_prods = (
            'Johnson fine grade 8½ by 11 paper',
        )

        # Create features
        feats = product.features()
        selectables = product.colors()

        for color in tup_colors:
            feats += product.color(name=color)
            
            if color in ('blue', 'gray', 'cream', 'white'):
                selectables += feats.last

        # Create products
        prods = product.products()
        for prod in tup_prods:
            prods += product.good(name=prod)


        paper, = prods[:]

        ''' Create "Johnson fine grade 8½ by 11 paper" and associate the
        selectable color features of blue, gray, cream, white. '''

        # Assign qualities

        # Fine grade
        paper.product_features += product.product_feature(
            type=product.product_feature.Required,
            feature=product.quality(name='Fine grade'),
        )

        # Extra glossy finish
        paper.product_features += product.product_feature(
            type=product.product_feature.Optional,
            feature=product.quality(name='Extra glossy finish'),
        )
            
        # Create product_feature associations
        for sel in selectables:
            pf = product.product_feature(
                type=product.product_feature.Selectable,
                feature=sel,
            )

            paper.product_features += pf

        # This product is sold in reams
        paper.measure = product.measure(name='ream')

        self.eq('ream', paper.measure.name)

        # Add dimension of 8½
        dim = product.dimension(number=8.5)
        dim.measure = product.measure(name='width')

        paper.product_features += product.product_feature(
            type=product.product_feature.Required,
            feature=dim,
        )

        paper.save()

        paper1 = product.good(paper)

        self.eq('ream', paper1.measure.name)
        self.one(paper.measure.products)
        self.one(paper1.measure.products)

        self.eq(
            paper.measure.products.first.id, 
            paper1.measure.products.first.id
        )

        self.eq('ream', product.product(paper).measure.name)

        self.one(paper.measure.products)
        self.one(product.product(paper).measure.products)

        self.eq(
            paper.measure.products.first.id,
            product.product(paper).measure.products.first.id
        )

        pfs = paper.product_features.sorted()
        pfs1 = paper1.product_features.sorted()

        self.seven(pfs1)
        self.eq(pfs.count, pfs1.count)

        for pf, pf1 in zip(pfs, pfs1):
            self.eq(pf.type, pf1.type)
            self.eq(pf.feature.name, pf1.feature.name)
            self.eq(pf.product.name, pf1.product.name)
            self.true(product.good.orm.exists(pf.product))

        # Ensure all the Selectable features were added
        sel = product.product_feature.Selectable
        self.eq(
            sorted(['white', 'cream', 'gray', 'blue']),
            sorted(x.feature.name for x in pfs1 if x.type == sel)
        )

        # Ensure all the Required features were added
        req = product.product_feature.Required
        self.eq(
            ['Fine grade'],
            [
                x.feature.name 
                for x in pfs1 
                if x.type == req and x.feature.name is not None
            ]
        )

        for x in pfs1:
            try:
                dim1 = product.dimension(x.feature)
            except db.RecordNotFoundError:
                pass
            else:
                self.none(dim1.name)
                self.eq(8.5, dim1.number)
                self.eq('width', dim1.measure.name)
                break
        else:
            self.fail("Couldn't find dimension feature")

        # Ensure all the Optional features were added
        opt = product.product_feature.Optional
        self.eq(
            ['Extra glossy finish'],
            [x.feature.name for x in pfs1 if x.type == opt]
        )

    def it_adds_a_feature_association(self):
        tup_colors = (
            'white',  'red',     'orange',  'blue',
            'green',  'purple',  'gray',    'cream',
        )

        # Create features
        feats = product.features()

        selectables = product.colors()

        for color in tup_colors:
            feats += product.color(name=color)
            
            # Capture 4 colors and associate them to `good` below
            # Selectable features.
            if color in ('blue', 'gray', 'cream', 'white'):
                selectables += feats.last

        feats.save()

        # Create products
        good = product.good(name='Johnson fine grade 8½ by 11 paper')

        # Associate `good` with the colors as Selectables.
        for sel in selectables:
            pf = product.product_feature(
                type=product.product_feature.Selectable,
                feature=sel,
                product=good
            )

            good.product_features += pf

        good.save()

        good1 = product.good(good)

        pfs1 = good1.product_features

        self.eq(
            sorted(['white', 'cream', 'gray', 'blue']),
            sorted(x.feature.name for x in pfs1)
        )

        # Associate `good1` to purple
        good1.product_features += product.product_feature(
            type=product.product_feature.Required,
            feature=product.colors(name='purple').first,
            product=good
        )

        good1.save()

        good2 = product.good(good1)

        sel = product.product_feature.Selectable
        req = product.product_feature.Required

        self.eq(
            sorted(['white', 'cream', 'gray', 'blue']),
            sorted(x.feature.name for x in pfs1 if x.type == sel)
        )

        self.eq(
            ['purple'],
            [x.feature.name for x in pfs1 if x.type == req]
        )

    def it_removes_feature_association(self):
        tup_colors = (
            'white',  'red',     'orange',  'blue',
            'green',  'purple',  'gray',    'cream',
        )

        # Create features
        feats = product.features()

        selectables = product.colors()

        for color in tup_colors:
            feats += product.color(name=color)
            
            # Capture 4 colors and associate them to `good` below
            # Selectable features.
            if color in ('blue', 'gray', 'cream', 'white'):
                selectables += feats.last

        feats.save()

        # Create products
        good = product.good(name='Johnson fine grade 8½ by 11 paper')

        # Associate `good` with the colors as Selectables.
        for sel in selectables:
            pf = product.product_feature(
                type=product.product_feature.Selectable,
                feature=sel,
                product=good
            )

            good.product_features += pf

        good.save()

        good1 = product.good(good)

        pfs1 = good1.product_features

        self.eq(
            sorted(['white', 'cream', 'gray', 'blue']),
            sorted(x.feature.name for x in pfs1)
        )

        # TODO:32d39bee I thought this was broken, but it actual removes
        # the association without removing any of the entities. We
        # should look into why this works instead of cascading the
        # deletes to the feature (color) entity.
        white = [
            x for x in good1.product_features 
            if x.feature.name == 'white'
        ][0]

        good1.product_features -= white

        pfs1 = good1.product_features
        self.eq(
            sorted(['cream', 'gray', 'blue']),
            sorted(x.feature.name for x in pfs1)
        )

        good1.save()

        good2 = product.good(good1)

        pfs1 = good2.product_features
        self.eq(
            sorted(['cream', 'gray', 'blue']),
            sorted(x.feature.name for x in pfs1)
        )

    def it_associates_product_to_suppliers(self):
        # Create products
        paper = product.good(
            name='Johnson fine grade 8½ by 11 bond paper'
        )

        pallet = product.good(
            name = "6' by 6' warehouse pallets"
        )

        # Create companies
        abc = getvalidcompany(
            name = 'ABC Corporation'
        )

        joes = getvalidcompany(
            name = "Joe's Stationary"
        )

        mikes = getvalidcompany(
            name = "Mike's Office Supply"
        )

        greggs = getvalidcompany(
            name = "Gregg's Pallet Shop"
        )

        palletinc = getvalidcompany(
            name = 'Pallets Incorporated'
        )

        warehousecomp = getvalidcompany(
            name = 'The Warehouse Company'
        )

        # Create priorities
        first = product.priority(ordinal=0)
        second = product.priority(ordinal=1)
        third = product.priority(ordinal=2)

        sps = product.supplier_products()
        sps += product.supplier_product(
            supplier  =  abc,
            product   =  paper,
            lead      =  2,
            priority  = first,
        )

        sps += product.supplier_product(
            supplier  =  joes,
            product   =  paper,
            lead      =  3,
            priority  = second,
        )

        sps += product.supplier_product(
            supplier  =  mikes,
            product   =  paper,
            lead      =  4,
            priority  =  third,
        )

        sps += product.supplier_product(
            supplier  =  greggs,
            product   =  pallet,
            lead      =  2,
            priority  =  first,
        )

        sps += product.supplier_product(
            supplier  =  palletinc,
            product   =  pallet,
            lead      =  3,
            priority  =  second,
        )

        sps += product.supplier_product(
            supplier  =  warehousecomp,
            product   =  pallet,
            lead      =  5,
            priority  =  third,
        )

        paper.save(pallet, sps, first, second, third)

        paper1 = paper.orm.reloaded()
        pallet1 = pallet.orm.reloaded()
        first = first.orm.reloaded()
        second = second.orm.reloaded()
        third = third.orm.reloaded()

        sps = paper1.supplier_products.sorted('supplier.name')
        self.eq('ABC Corporation',      sps.first.supplier.name)
        self.eq("Joe's Stationary",     sps.second.supplier.name)
        self.eq("Mike's Office Supply", sps.third.supplier.name)

        sps = pallet1.supplier_products.sorted('supplier.name')
        self.eq("Gregg's Pallet Shop",      sps.first.supplier.name)
        self.eq('Pallets Incorporated',     sps.second.supplier.name)
        self.eq('The Warehouse Company',    sps.third.supplier.name)

        sps = first.supplier_products.sorted('supplier.name')
        self.eq('ABC Corporation',      sps.first.supplier.name)
        self.eq("Gregg's Pallet Shop",  sps.second.supplier.name)
        
        sps = second.supplier_products.sorted('supplier.name')
        self.eq("Joe's Stationary",     sps.first.supplier.name)
        self.eq('Pallets Incorporated', sps.second.supplier.name)
        
        sps = third.supplier_products.sorted('supplier.name')
        self.eq("Mike's Office Supply", sps.first.supplier.name)
        self.eq('The Warehouse Company', sps.second.supplier.name)
    
    def it_creates_guildlines(self):
        # Service products will not have guidelines
        serv = self.getvalid(product.service)
        self.false(hasattr(serv, 'guidelines'))

        good = self.getvalid(product.good, comment=1)
        reg = getvalidregion()
        fac = party.facility(name='Area 51', footage=10_000)
        fac.save()
        org = getvalidcompany()

        cnt = 2
        for i in range(cnt):
            good.guidelines += product.guideline(
                end      = primative.datetime.utcnow(days=-200),
                begin    = primative.datetime.utcnow(days=+200),
                level    = randint(0, 255),
                quantity = randint(0, 255)
            )
            good.guidelines.last.region = reg
            good.guidelines.last.facility = fac
            good.guidelines.last.organization = org

        good.save()

        good1 = good.orm.reloaded()

        gls  = good.guidelines.sorted()
        gls1 = good1.guidelines.sorted()

        self.eq(cnt, gls1.count)

        for gl, gl1 in zip(gls, gls1):
            for prop in ('end', 'begin', 'level', 'quantity'):
                self.eq(getattr(gl, prop), getattr(gl1, prop))

        self.eq(gl.region.id,        gl1.region.id)
        self.eq(gl.facility.id,      gl1.facility.id)
        self.eq(gl.organization.id,  gl1.organization.id)

    def it_stores_goods_in_inventory(self):
        # Services don't have inventory representations
        serv = self.getvalid(product.service)
        self.expect(AttributeError, lambda: serv.items)

        # Goods should have a collection of inventory items
        good = self.getvalid(product.good, comment=1)
        self.expect(None, lambda: good.items)

        # Add 10 serialized inventory items for the good
        for sn in range(10000, 10005):
            good.items += product.serial(number=sn)

        good.save()

        for i in range(5):
            good.items += product.nonserial(quantity=randint(1, 100))

        good.save()

        good1 = good.orm.reloaded()

        itms  = good.items.sorted()
        itms1 = good1.items.sorted()

        self.ten(itms)
        self.ten(itms1)

        serial = 0
        nonserial = 0
        for itm, itm1 in zip(itms, itms1):
            # Downcast
            try:
                itm = product.serial(itm)
                itm1 = product.serial(itm1)
                self.eq(itm.number, itm1.number)
                serial += 1
            except db.RecordNotFoundError:
                # Must be nonserial
                itm = product.nonserial(itm)
                itm1 = product.nonserial(itm1)
                self.eq(itm.quantity, itm1.quantity)
                nonserial += 1

        self.eq(5, serial)
        self.eq(5, nonserial)

    def it_stores_goods_in_a_facility(self):
        # Create two warehouses to store the good
        abccorp = party.facility(
            name = 'ABC Corporation',
            type = party.facility.Warehouse
        )
        
        abcsub = party.facility(
            name = 'ABC Subsidiary',
            type = party.facility.Warehouse
        )

        # Create the four containers along with individual container
        # types.
        bin200 = product.containertype(
            name = 'Bin 200',
        )

        bin200.containers += product.container(
            name = 'Bin 200',
            facility = abccorp
        )

        bin400 = product.containertype(
            name = 'Bin 400',
        )

        bin400.containers += product.container(
            name = 'Bin 400',
            facility = abcsub
        )

        bin125 = product.containertype(
            name = 'Bin 125',
        )

        bin125.containers += product.container(
            name = 'Bin 125',
            facility = abccorp
        )

        bin250 = product.containertype(
            name = 'Bin 250',
        )

        bin250.containers += product.container(
            name = 'Bin 250',
            facility = abccorp
        )

        # Create the goods
        copier = self.getvalid(product.good, comment=1)
        copier.name = 'Action 250 Quality Copier'

        paper = self.getvalid(product.good, comment=1)
        paper.name = 'Johnson fine grade 8½ by 11 paper'

        pen = self.getvalid(product.good, comment=1)
        pen.name = 'Goldstein Elite Pen'

        diskette = self.getvalid(product.good, comment=1)
        diskette.name = "Jerry's box of 3½ inch diskettes"

        # Create the inventory item for the goods
        copier.items += product.serial(number=1094853)

        paper.items += product.nonserial(quantity=156)
        paper.items += product.nonserial(quantity=300)

        pen.items += product.nonserial(quantity=200)

        diskette.items += product.nonserial(quantity=500)

        # Locate the inventory item the appropriate facility
        copier.items.last.facility = abccorp
        paper.items.penultimate.container = \
            bin200.containers.last

        paper.items.last.container = \
            bin400.containers.last

        pen.items.first.container = \
            bin125.containers.last

        diskette.items.first.container = \
            bin250.containers.last

        copier.save(
            paper, paper.items,
            pen, pen.items,
            diskette, diskette.items
        )

        copieritm = copier.items.last.orm.reloaded()
        paperitm1 = paper.items.penultimate.orm.reloaded()
        paperitm2 = paper.items.ultimate.orm.reloaded()
        penitm = pen.items.first.orm.reloaded()
        disketteitm = diskette.items.first.orm.reloaded()

        self.eq(abccorp.id, copieritm.facility.id)

        # TODO:1e7dd1dd It would be nice if
        # `paperitm1.orm.super.facility` returned the same value as
        # `paperitm1.orm.super.container.facility. However, I do not
        # believe that at the moment, it is possible to override a
        # composite attribute. This would be a great nice-to-have,
        # though.
        # self.eq(abccorp.id, paperitm.facility.id)

        # 156 instances of the paper item is stored in Bin 200 at
        # abccorp. 300 are stored at Bin 400 at abcsub
        self.eq(
            bin200.containers.last.id, 
            paperitm1.container.id
        )

        self.eq(
            abccorp.id,
            paperitm1.container.facility.id
        )

        self.eq(156,  paperitm1.quantity)

        self.eq(
            bin400.containers.last.id, 
            paperitm2.container.id
        )

        self.eq(
            abcsub.id,
            paperitm2.container.facility.id
        )
        self.eq(300,  paperitm2.quantity)

        self.eq(
            bin125.containers.last.id, 
            penitm.container.id
        )

        self.eq(
            abccorp.id,
            penitm.container.facility.id
        )
        self.eq(200,  penitm.quantity)

        self.eq(
            bin250.containers.last.id, 
            disketteitm.container.id
        )

        self.eq(
            abccorp.id,
            disketteitm.container.facility.id
        )
        self.eq(500,  disketteitm.quantity)

    def it_creates_a_lot(self):
        lot = product.lot(
            createdat = primative.datetime.utcnow(),
            quantity  = 100,
            expiresat = primative.datetime.utcnow(days=100)
        )

        lot.items += self.getvaliditem()

        lot.save()

        lot1 = lot.orm.reloaded()

        for prop in ('id', 'createdat', 'quantity', 'expiresat'):
            self.eq(getattr(lot, prop), getattr(lot1, prop))

        itms = lot.items
        itms1 = lot1.items

        self.one(itms)
        self.one(itms1)

        itm = product.nonserial(itms.first)
        itm1 = product.nonserial(itms1.first)

        self.eq(itm.quantity, itm1.quantity)

        self.eq(itm.good.name, itm1.good.name)
        self.eq(itm.good.id, itm1.good.id)

    def it_assigns_status_to_inventory_item(self):
        book = self.getvalid(product.good, comment=1)
        book.name = 'The Data Model Resource Book'

        good = product.status(name='Good')
        plusgood = product.status(name='Plusgood')
        doubleplusgood = product.status(name='Doubleplusgood')

        for sn in range(6455170, 6455173):
            book.items += product.serial(number=sn)

        book.items.first.status = good
        book.items.second.status = plusgood
        book.items.third.status = doubleplusgood

        book.save(book.items)

        book1 = book.orm.reloaded()

        itms = book.items.sorted()
        itms1 = book1.items.sorted()

        self.three(itms)
        self.three(itms1)

        for itm, itm1 in zip(itms, itms1):
            self.eq(itm.status.name, itm1.status.name)
            self.eq(itm.status.id, itm1.status.id)
    
    def it_assigns_variance(self):
        book = self.getvalid(product.good, comment=1)
        book.name = 'The Data Model Resource Book'

        book.items += product.serial(number=6455170)

        book.items.last.variances += product.variance(
            date = primative.datetime.utcnow(),
            quantity = 1,
            comment = None
        )

        overage = product.reason(name='overage')

        book.items.last.variances.last.reason = overage

        book.save()

        book1 = book.orm.reloaded()

        vars = book.items.last.variances
        vars1 = book1.items.last.variances

        self.one(vars)
        self.one(vars1)

        for prop in ('id', 'date', 'quantity', 'comment'):
            self.eq(
                getattr(vars.first, prop),
                getattr(vars1.first, prop)
            )

        self.eq(vars.first.reason.id, vars1.first.reason.id)
        self.eq(vars.first.reason.name, vars1.first.reason.name)

        reasons = product.reasons(name='overage')

        self.one(reasons)

        self.eq('overage', reasons.first.name)

        self.one(reasons.first.variances)

        self.eq(vars.first.id, reasons.first.variances.first.id)

    def it_creates_categories(self):
        ''' Simple, non-recursive test '''
        cat = product.category()
        cat.name = uuid4().hex
        cat.save()

        cat1 = product.category(cat.id)
        self.eq(cat.id, cat1.id)
        self.eq(cat.name, cat1.name)

        ''' A one-level recursive test with two child categories'''
        cat_0 = product.category()
        cat_0.name = uuid4().hex

        cat_1_0 = product.category()
        cat_1_0.name = uuid4().hex

        cat_1_1 = product.category()
        cat_1_1.name = uuid4().hex

        cat_0.categories += cat_1_0
        cat_0.categories += cat_1_1

        cat_0.save()

        cat1 = product.category(cat_0.id)
        self.eq(cat_0.id, cat1.id)
        self.eq(cat_0.name, cat1.name)

        cats0 = cat_0.categories.sorted()

        cats1 = cat1.categories.sorted()

        self.two(cats1)
       
        self.eq(cats0.first.id, cats1.first.id)
        self.eq(cats0.first.name, cats1.first.name)

        self.eq(cats0.second.id, cats1.second.id)
        self.eq(cats0.second.name, cats1.second.name)

        ''' A two-level recursive test with one child categories each'''
        cat = product.category()
        cat.name = uuid4().hex

        cat_1 = product.category()
        cat_1.name = uuid4().hex

        cat_2 = product.category()
        cat_2.name = uuid4().hex

        cat.categories += cat_1
        cat_1.categories += cat_2

        cat.save()

        cat1 = product.category(cat.id)

        self.one(cat1.categories)
        self.one(cat1.categories.first.categories)

        self.eq(
            cat.categories.first.id, 
            cat1.categories.first.id, 
        )

        self.eq(
            cat.categories.first.name, 
            cat1.categories.first.name, 
        )

        self.eq(
            cat.categories.first.categories.first.id, 
            cat1.categories.first.categories.first.id, 
        )

        self.eq(
            cat.categories.first.categories.first.name, 
            cat1.categories.first.categories.first.name, 
        )

    def it_updates_categories_non_recursive(self):
        ''' Simple, non-recursive test '''
        cat = product.category()
        cat.name = uuid4().hex
        cat.save()

        cat1 = product.category(cat.id)
        cat1.name = uuid4().hex
        cat1.save()

        cat2 = product.category(cat.id)

        self.ne(cat.name, cat2.name)
        self.eq(cat1.id, cat2.id)
        self.eq(cat1.name, cat2.name)

    def it_updates_categories_recursive(self):
        ''' A two-level, recursive test '''
        # Create
        cat = product.category()
        cat.name = uuid4().hex

        cat_1 = product.category()
        cat_1.name = uuid4().hex

        cat_2 = product.category()
        cat_2.name = uuid4().hex

        cat.categories += cat_1
        cat_1.categories += cat_2

        cat.save()

        # Update
        cat1 = product.category(cat.id)
        cat1.name = uuid4().hex
        cat1.categories.first.name = uuid4().hex
        cat1.categories.first.categories.first.name = uuid4().hex
        cat1.save()

        # Test
        cat2 = product.category(cat.id)
        self.ne(cat.name, cat2.name)
        self.eq(cat1.id, cat2.id)
        self.eq(cat1.name, cat2.name)

        self.ne(cat.categories.first.name, cat2.categories.first.name)
        self.eq(cat1.categories.first.id, cat2.categories.first.id)
        self.eq(cat1.categories.first.name, cat2.categories.first.name)

        self.ne(
            cat.categories.first.categories.first.name, 
            cat2.categories.first.categories.first.name
        )

        self.eq(
            cat1.categories.first.categories.first.id, 
            cat2.categories.first.categories.first.id
        )

        self.eq(
            cat1.categories.first.categories.first.name, 
            cat2.categories.first.categories.first.name
       )

    def it_creates_association_between_product_and_category(self):
        cat = product.category()
        cat.name = uuid4().hex

        prod = product.good()
        prod.name = uuid4().hex
        prod.introducedat = primative.datetime.utcnow(days=-100)
        prod.comment = uuid4().hex * 1000
        cc = product.category_classification()
        cc.begin = primative.datetime.utcnow(days=-50)
        cc.product = prod
        cat.category_classifications += cc

        prod = product.service()
        prod.name = uuid4().hex
        prod.introducedat = primative.datetime.utcnow(days=-100)
        prod.comment = uuid4().hex * 1000
        cc = product.category_classification()
        cc.begin = primative.datetime.utcnow(days=-25)
        cc.comment = uuid4().hex * 1000
        cc.product = prod
        cat.category_classifications += cc

        cat.save()

        cat1 = product.category(cat.id)

        self.two(cat1.category_classifications)

        ccs = cat.category_classifications.sorted()
        ccs1 = cat1.category_classifications.sorted()
        
        ccs = cat.category_classifications.sorted()
        ccs1 = cat1.category_classifications.sorted()

        self.eq(ccs.first.begin, ccs1.first.begin)
        self.eq(ccs.second.begin, ccs1.second.begin)

        self.eq(ccs.first.product.name, ccs1.first.product.name)
        self.eq(ccs.second.product.name, ccs1.second.product.name)

        self.eq(ccs.first.category.name, ccs1.first.category.name)
        self.eq(ccs.second.category.name, ccs1.second.category.name)

    def it_breaks_with_two_primary_associations(self):
        """ Test to ensure that `category_classification.brokenrules`
        checks the database to ensure a product is associated with only
        one category as primary. 
        """

        ''' Test category_classifications.brokenrules '''
        cat = product.category()
        cat.name = uuid4().hex

        prod = self.getvalid()
        cc = product.category_classification()
        cc.product = prod
        cc.begin = primative.datetime.utcnow(days=-50)
        cc.isprimary = True # Ensure isprimary is True
        cat.category_classifications += cc

        # Save and reload. Another brokenrule will be added by
        # category_classifications.brokenrules to ensure that it does
        # not contain a product set as primary in two different
        # categories.
        cat.save()

        cat = product.category(cat.id)

        cc = product.category_classification()
        cc.product = prod
        cc.begin = primative.datetime.utcnow(days=-25)
        cc.comment = uuid4().hex * 1000
        self.true(cat.isvalid)
        cc.isprimary = True  # Ensure isprimary is True
        cat.category_classifications += cc

        self.two(cat.brokenrules);
        self.broken(cat, 'isprimary', 'valid')

        self.expect(entities.BrokenRulesError, lambda: cat.save())

        ''' Test category_classification.getbrokenrules '''
        cat = product.category(cat.id)
        cc = product.category_classification()
        cc.product = prod
        cc.begin = primative.datetime.utcnow(days=-25)
        cc.comment = uuid4().hex * 1000
        cc.product = prod
        cc.category = cat
        self.true(cc.isvalid)
        cc.isprimary = True  # Ensure isprimary is True
        self.one(cc.brokenrules)
        self.broken(cc, 'isprimary', 'valid')

    def it_creates_category_types(self):
        sm = party.type(name='Small organizations')

        # Small organizations have an interest in Wordpress services
        sm.category_types += product.category_type(
            begin=primative.datetime.utcnow(days=-100),
            end=primative.datetime.utcnow(days=50),
            category=product.category(name='Wordpress services')
        )

        # Small organizations have an interest in bank loans
        sm.category_types += product.category_type(
            begin=primative.datetime.utcnow(days=-100),
            end=primative.datetime.utcnow(days=50),
            category=product.category(name='Bank loans')
        )

        sm.save()

        sm1 = party.type(sm.id)

        self.two(sm1.category_types)

        sm.category_types.sort()
        sm1.category_types.sort()

        for attr in 'id', 'begin', 'end':
            self.eq(
                getattr(sm.category_types.first, attr),
                getattr(sm1.category_types.first, attr),
            )

            self.eq(
                getattr(sm.category_types.second, attr),
                getattr(sm1.category_types.second, attr),
            )

        for i in range(2):
            self.eq(
                sm.category_types[i].category.id,
                sm1.category_types[i].category.id
            )

        for i in range(2):
            self.eq(
                sm.category_types[i].type.id,
                sm1.category_types[i].type.id
            )

    def it_converts_measures(self):

        # Create three pencil products
        pen = product.product(name='Henry #2 Pencil')
        small = product.product(name='Henry #2 Pencil Small Box')
        large = product.product(name='Henry #2 Pencil Large Box')

        # Create the unit of measures for the pencil products
        each = product.measure(name='each')
        smallbox = product.measure(name='smallbox')
        largebox = product.measure(name='largebox')

        # The `pen` product's UOM will be "each"
        pen.measure = each


        # The product `small` will have a unit of measure called
        # `smallbox`
        small.measure = smallbox

        # The product `large` will have a unit of measure called
        # `largebox`
        large.measure = largebox

        # Create associations between the above unit of measures so
        # conversions between them can be done.

        # A small box is `12` pencils
        mm = product.measure_measure(
            object   =  smallbox,
            factor   =  12
        )

        # Associate each with smallbox
        each.measure_measures += mm

        # A large box is equivalent to 2 small boxes. Note the
        # association beteen `each` and `largebox` is not created. We
        # will rely on product.measure_measure to work issues like this
        # out automatically via transitive logic.
        mm = product.measure_measure(
            object   =  largebox,
            factor   =  2
        )

        smallbox.measure_measures += mm

        self.eq(
            dec(2),
            smallbox.convert(largebox)
        )

        '''
        # This can't work because we haven't yet saved the unit of
        # measure association that associates largebox with smallbox.
        # This should work once this association has been saved,
        # however.
        self.eq(
            dec(2),
            largebox.convert(smallbox)
        )
        '''

        # Save the `pen` product along with `small` and `large` in the
        # same tx
        pen.save(small, large)

        # Reload products
        pen1    =  pen.orm.reloaded()
        small1  =  small.orm.reloaded()
        large1  =  large.orm.reloaded()

        smallbox1 = smallbox.orm.reloaded()
        largebox1 = largebox.orm.reloaded()

        self.eq(
            dec(12),
            pen1.measure.convert(smallbox1)
        )

        self.eq(
            dec(24),
            pen1.measure.convert(largebox1)
        )

        self.eq(
            dec(2),
            small1.measure.convert(largebox1)
        )

        # Convert the other way. This will require .convert() to load
        # the `measure_measure` records for the `measure` passed in to
        # convert.
        self.eq(
            dec(12),
            smallbox1.convert(pen1.measure)
        )

        self.eq(
            dec(2),
            largebox1.convert(small1.measure)
        )

        self.eq(
            dec(24),
            largebox1.convert(pen1.measure)
        )

        ''' Leaving the above conversion factors declared in
        measure_measure, let's create dimension(feature) that have
        their own unit of measures and conversion factor declarations in
        measure_measures. Then we can test their conversions.'''

        paper = product.product(
            name = "Johnson fine grade 8½ by 11 paper"
        )

        dim_width = product.dimension(name='width', number=dec(8.5))
        dim_length = product.dimension(name='length', number=dec(11))

        # Create units of measure 'inches and 'centimeters' and
        # associate them with each other along with the factor number
        # that can be used to convert between them.
        inches = product.measure(name='inches')
        cent   = product.measure(name='centimeters')

        # Make the width dimension in inches
        inches.dimensions += dim_width

        # Make the length dimension in centimeters (this would be a very
        # string thing to do in real life).
        cent.dimensions += dim_length

        mm = product.measure_measure(
            subject = inches,
            object  = cent,
            factor  = dec(2.54)
        )

        paper.product_features += product.product_feature(
           feature = dim_width
        )

        # Save everything associated with the paper product. The
        # save doesn't discover the measure_measure association, so
        # throw that in as well so it gets saved.
        paper.save(mm)

        self.one(paper.product_features)
        dim_width = paper.product_features.first.feature

        # The paper's dimension(feature) knows it is measured in inches
        # via its unit of measure (`measure`) property
        self.eq(inches.id, dim_width.measure.id)

        # 8.5 inches is 21.59 centimeters.
        self.eq(dec('21.59'), dim_width.convert(cent))

        # 11 centimenters is 4.33071 inches
        d = dec('4.330708661417322834645669291')
        self.eq(d, dim_length.convert(inches))

    def it_calls_make(self):
        r = product.rating(score=product.rating.Outstanding)
        r1 = product.rating(score=product.rating.Outstanding)
        self.eq(r.id, r1.id)


    def it_creates_prices(self):
        # Create organizations
        abc = getvalidcompany(
            name = 'ABC Corporation'
        )

        joes = getvalidcompany(
            name = "Joe's Stationary"
        )

        # Create product
        paper = product.good(
            name='Johnson fine grade 8½ by 11 bond paper'
        )

        # Create government party type
        gov = party.type(
            name = 'Government'
        )

        # Create product category
        cat_paper = product.category(
            name = 'Paper',
            begin = '2001-09-01',
            end   = '2001-09-30'
        )

        # Associate product category to produt
        cc = product.category_classification(
            begin   = primative.datetime.utcnow(days=-50),
            product = paper
        )

        cat_paper.category_classifications += cc

        # Create geographic regions
        east = party.region(
            name = 'Eastern region',
            type = None
        )

        west = party.region(
            name = 'Western region',
            type = None,
        )

        hi = party.region(
            name = 'Hawaii',
            type = party.region.State,
            abbreviation = 'HI',
            region = west,
        )

        al = party.region(
            name = 'Alabama',
            type = party.region.State,
            abbreviation = 'AL',
            region = east,
        )

        # Create features
        cream = product.color(name='Cream')
        fin   = product.quality(name='Extra glossy finish')

        # Create prices

        # Base prices
        price1 = product.base(
            region        =  east,
            price         =  9.75,
            organization  =  abc,
            product       =  paper,
            quantitybreak = product.quantitybreak(
                begin = 0, 
                end   = 100
            )
        )

        price2 = product.base(
            region        =  east,
            price         =  9.00,
            organization  =  abc,
            product       =  paper,
            quantitybreak = product.quantitybreak(
                begin = 101, 
                end   = None
            )
        )

        price3 = product.base(
            region        =  west,
            price         =  8.75,
            organization  =  abc,
            product       =  paper,
            quantitybreak = product.quantitybreak(
                begin = 0, 
                end   = 100
            )
        )

        price4 = product.base(
            region        =  west,
            price         =  8.50,
            organization  =  abc,
            product       =  paper,
            quantitybreak = product.quantitybreak(
                begin = 101, 
                end   = None
            )
        )

        # Discount prices
        price5 = product.discount(
            percent       =  2,
            type          =  gov,
            product       =  paper,
            organization  =  abc
        )

        price6 = product.discount(
            percent       =  5,
            organization  =  abc,
            product       =  paper,
            category      =  cat_paper
        )

        # Surchages
        price7 = product.surcharge(
            region        =  hi,
            organization  =  abc,
            product       =  paper,
            price         =  2
        )

        price8 = product.base(
            organization  =  joes,
            product       =  paper,
            price         =  11
        )

        paper.prices += price1
        paper.prices += price2
        paper.prices += price3
        paper.prices += price4
        paper.prices += price5
        paper.prices += price6
        paper.prices += price7
        paper.prices += price8

        paper.save(
            paper.prices,        # prices
            abc, joes,           # organizations
            gov,                 # party types
            cat_paper,           # product categories
            east, west, hi, al,  # regions
            cream, fin,          # features
        )

        paper1 = paper.orm.reloaded()

        # Get first price
        pr, prs = paper.getprice(
            org  = abc,
            regs = [al],
            qty  = 20
        )

        # Despite AL being in the east, the algorith was able to find a
        # cheaper base price of $8.75 based on the quantity break. A 5%
        # discount was applied because all products in the "paper"
        # category are 5% off.
        self.eq(dec('8.3125'), pr)
        self.eq(dec('8.75'), prs.first.price)
        self.eq(dec('5'), prs.second.percent)

        # Get second price
        pr, prs = paper.getprice(
            org = abc,
            regs = [east],
        )

        # Since we didn't specify a quantity, we got the cheapest
        # eastern price of $9. 5% was taken off since this was a paper
        # product.
        self.eq(dec('8.55'), pr)
        self.eq(dec('9.00'), prs.first.price)
        self.eq(dec('5'), prs.second.percent)

        # Get third price
        pr, prs = paper.getprice(
            org  = abc,
            regs = [west],
        )

        # Without specifying the qty, we get the cheapest eastern price
        # with a 5% paper discount.
        self.eq(dec('8.075'), pr)
        self.eq(dec('8.50'), prs.first.price)
        self.eq(dec('5'), prs.second.percent)

        # Get fifth price
        pr, prs = paper.getprice(
            org  = abc,
            pts  = [gov],
            regs = [west],
        )

        # The cheapest western price was found and a paper product
        # discount was applied as well as a 2% gov discount.
        self.eq(dec('7.9135'), pr)
        self.eq(dec('8.50'), prs.first.price)
        self.eq(dec('2'), prs.second.percent)
        self.eq(dec('5'), prs.third.percent)

        # Get seventh price
        pr, prs = paper.getprice(
            org  = abc,
            regs = [hi]
        )

        # HI is in the west, so we were able to get the $8.75 base
        # price. The 5% off for all paper products was applied. A
        # surcharge of $5 was also applied since we are shipping to HI.
        self.eq(dec('10.075'), pr)
        self.eq(dec('8.50'), prs.first.price)
        self.eq(dec('5'), prs.second.percent)
        self.eq(dec('2'), prs.third.price)

        # Get eigth price
        pr, prs = paper.getprice(
            org  = joes,
        )

        # HI is in the west, so we were able to get the $8.75 base
        # price. The 5% off for all paper products was applied. A
        # surcharge of $5 was also applied since we are shipping to HI.
        self.eq(dec('10.45'), pr)
        self.eq(dec('11'), prs.first.price)
        self.eq(dec('5'), prs.second.percent)
        self.two(prs)

    def it_creates_product_estimates(self):
        good = product.good(name='Johnson fine grade 8½ by 11 paper')

        # Create regions
        ny = party.region(
            name          =  'New York',
            abbreviation  =  'N.Y.',
            type          =  party.region.State,
        )

        id = party.region(
            name          =  'Idaho',
            abbreviation  =  'I.D.',
            type          =  party.region.State,
        )

        # Create estimatetypes
        apc = product.estimatetype(
            name = 'Anticipated purchase cost'
        )

        ao = product.estimatetype(
            name = 'Administrative overhead'
        )

        fr = product.estimatetype(
            name = 'Frieght'
        )

        good.estimates += product.estimate(
            region        =  ny,
            cost          =  2,
            begin         =  primative.datetime('Jan  9,  2001'),
            estimatetype  =  apc,
        )

        good.estimates += product.estimate(
            region        =  ny,
            cost          =  dec('1.9'),
            begin         =  primative.datetime('Jan  9,  2001'),
            estimatetype  =  ao,
        )

        good.estimates += product.estimate(
            region        =  ny,
            cost          =  dec('1.5'),
            begin         =  primative.datetime('Jan  9,  2001'),
            estimatetype  =  fr,
        )

        good.estimates += product.estimate(
            region        =  ny,
            cost          =  dec('2'),
            begin         =  primative.datetime('Jan  9,  2001'),
            estimatetype  =  apc,
        )

        good.estimates += product.estimate(
            region        =  ny,
            cost          =  dec('1.1'),
            begin         =  primative.datetime('Jan  9,  2001'),
            estimatetype  =  ao,
        )

        good.estimates += product.estimate(
            region        =  ny,
            cost          =  dec('1.1'),
            begin         =  primative.datetime('Jan  9,  2001'),
            estimatetype  =  fr,
        )

        good.save()

        good1 = good.orm.reloaded()

        ests  = good.estimates.sorted()
        ests1 = good.estimates.sorted()

        self.six(ests)
        self.six(ests1)

        for est, est1 in zip(ests, ests1):
            self.eq(est.product.id, est1.product.id)
            self.eq(est.estimatetype.id, est1.estimatetype.id)
            self.eq(est.region.id, est1.region.id)
            self.eq(est.cost, est1.cost)
            self.eq(primative.date('Jan 9, 2001'), est1.begin)
            self.eq(None, est1.end)

    def it_creates_product_associations(self):
        ''' Test the Component association. Create a parent product
        called 'Office supply kit', and add child components. '''
        rent     = product.good(name='Office supply kit')

        rent.product_products += product.product_product(
            object = product.good(
                name='Johnson fine grade 8½ by 11 paper'
            ),
            quantity = 5,
        )

        rent.product_products += product.product_product(
            object  = product.good(name="Pennie's 8½ by 11 binders"),
            quantity = 5,
        )

        rent.product_products += product.product_product(
            object = product.good(name="Shwinger black ball point pen"),
            quantity = 6,
        )

        rent.save()

        rent1 = rent.orm.reloaded()

        pps = rent.product_products.sorted()
        pps1 = rent1.product_products.sorted()

        self.three(pps)
        self.three(pps1)

        for pp, pp1 in zip(pps, pps1):
            self.eq(pp.quantity, pp1.quantity)
            self.eq(rent.id, pp1.subject.id)
            self.eq(pp.object.id, pp1.object.id)
            self.eq(pp.id, pp1.id)
        
        ''' Test the Substitution association. '''
        pps = product.product_products()

        pps += product.product_product(
            subject = product.good(
                name='Small box of Henry #2 pencils'
            ),
            object = product.good(
                name='Individual Henry #2 pencil'
            ),
            quantity = 12,
        )

        pps += product.product_product(
            subject = product.good(
                name='Goldstein Elite pen'
            ),
            object = product.good(
                name="George's Elite pen"
            ),
        )

        pps.save()

        pps1 = product.product_products(
            subject__productid = pps.first.subject.id
        )

        self.one(pps1)
        self.eq(pps.first.subject.id, pps1.first.subject.id)
        self.eq(pps.first.object.id, pps1.first.object.id)
        self.eq(12, pps1.first.quantity)

        pps1 = product.product_products(
            subject__productid = pps.second.subject.id
        )

        self.one(pps1)
        self.eq(pps.second.subject.id, pps1.first.subject.id)
        self.eq(pps.second.object.id, pps1.first.object.id)
        self.eq(None, pps1.first.quantity)

if __name__ == '__main__':
    tester.cli().run()
