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
from decimal import Decimal as dec
from func import enumerate
from random import randint
from uuid import uuid4, UUID
import ecommerce
import entities
import order
import orm
import party
import primative
import product
import tester
import uuid

def getvalidproduct(type=None, comment=1000):
    if type is None:
        type = product.good

    prod = type()
    prod.name = uuid4().hex
    prod.introducedat = primative.date.today(days=-100)
    prod.comment = uuid4().hex * comment
    return prod

def getvalidperson(first=None, last=None):
    per = party.person()

    per.first = first if first else uuid4().hex
    per.middle = uuid4().hex
    per.last = last if last else uuid4().hex
    per.title          =  uuid4().hex
    per.suffix         =  uuid4().hex
    per.mothersmaiden  =  uuid4().hex
    per.maritalstatus  =  True
    per.nationalids    =  uuid4().hex
    per.isicv4         =  None
    per.dun            =  None
    return per

class order(tester.tester):
    def __init__(self, *args, **kwargs):
        mods = 'order', 'party', 'product', 'third'
        super().__init__(mods=mods, *args, **kwargs)

        orm.security().override = True

        # TODO Principles are create in tester so we probably don't need
        # the below
        orm.security().owner = ecommerce.users.root

        com = party.company(name='Carapacian')
        orm.security().proprietor = com
        com.save(com)

    def it_creates_salesorder(self):
        ''' Create products '''
        # Goods
        paper = getvalidproduct(product.good, comment=1)
        paper.name='Johnson fine grade 8½ by 11 bond paper'

        pen = getvalidproduct(product.good, comment=1)
        pen.name = 'Goldstein Elite Pen'

        diskette = getvalidproduct(product.good, comment=1)
        diskette.name = "Jerry's box of 3½ inch diskettes"

        georges = getvalidproduct(product.good, comment=1)
        georges.name = "George's Elite pen"

        kit = getvalidproduct(product.good, comment=1)
        kit.name = 'Basic cleaning supplies kit'

        # Service
        cleaning = getvalidproduct(product.service, comment=1)
        cleaning.name = 'Hourly office cleaning service'

        ''' Create features '''
        gray    =  product.color(name='gray')
        blue    =  product.color(name='blue')
        glossy  =  product.quality(name='Extra glossy finish')
        autobill = product.billing(name='Automatically charge to CC')

        ''' Create orders '''
        so_1  =  order.salesorder()
        so_2  =  order.salesorder()
        po    =  order.purchaseorder()

        ''' Add items to orders '''
        so_1.items += order.salesitem(
            product = paper,
            quantity = 10,
            price = dec('8.00')
        )

        # Add a feature item for the paper. We want the paper to be
        # `gray` and `glossy`.
        so_1.items.last.items += order.salesitem(feature=gray)
        so_1.items.last.items += order.salesitem(
            feature = glossy, 
            price   = 2.00
        )

        so_1.items += order.salesitem(
            product = pen,
            quantity = 4,
            price = dec('12.00')
        )
        so_1.items.last.items += order.salesitem(feature=blue)

        so_1.items += order.salesitem(
            product = diskette,
            quantity = 6,
            price = dec('7.00')
        )

        so_2.items += order.salesitem(
            product = georges,
            quantity = 10,
            price = dec('10.00')
        )

        po.items += order.purchaseitem(
            product = cleaning,
            quantity = 12,
            price = dec('15.00')
        )
        po.items.last.items += order.salesitem(feature=autobill)

        po.items += order.purchaseitem(
            product = kit,
            quantity = 1,
            price = dec('10.00')
        )

        so_1.save(so_2, po)

        so_1_1 = so_1.orm.reloaded()
        so_2_1 = so_2.orm.reloaded()
        po1    = po.orm.reloaded()

        self.three(so_1.items)
        self.three(so_1_1.items)

        self.one(so_2.items)
        self.one(so_2_1.items)

        self.two(po.items)
        self.two(po1.items)

        gen = zip(so_1.items.sorted(), so_1_1.items.sorted())
        for itm, itm1 in gen:
            self.eq(itm.id, itm1.id)

            # The paper product had a gray and glossy feature added
            if itm1.product.id == paper.id:
                feats1 = itm1.items
                names = feats1.pluck('feature.name')
                self.two(feats1)
                self.true('gray' in names)
                self.true('Extra glossy finish' in names)
            # The pen product had a blue feature added
            elif itm1.product.id == pen.id:
                feats1 = itm1.items
                names = feats1.pluck('feature.name')
                self.one(feats1)
                self.true('blue' in names)

        gen = zip(so_2.items.sorted(), so_2_1.items.sorted())
        for itm, itm1 in gen:
            self.eq(itm.id, itm1.id)

        gen = zip(po.items.sorted(), po1.items.sorted())
        for itm, itm1 in gen:
            self.eq(itm.id, itm1.id)
            # The cleaning service billing feature added to it
            if itm1.product.id == cleaning.id:
                feats1 = itm1.items
                names = feats1.pluck('feature.name')
                self.one(feats1)
                self.true('Automatically charge to CC' in names)

    def it_uses_roles(self):
        """ A company called ACME will play a `placing` role (they act as
        th placing customer) to a sales order.
        """


        ''' Create parties involved in order '''
        acme = party.company(name='ACME Company')
        sub  = party.company(name='ACME Subsidiary')

        ''' Create contact mechanisms '''
        acmeaddr = party.address(
            address1='234 Stretch Street',
            address2='New York, New York',
        )

        acmesubaddr = party.address(
            address1='100 Main Street',
            address2='New York, New York',
        )

        acmeshipto = party.address(
            address1='Drident Avenue',
            address2='New York, New York',
        )

        # Create order
        so  =  order.salesorder()

        # Create a good for the sales item
        paper = getvalidproduct(product.good, comment=1)
        paper.name='Johnson fine grade 8½ by 11 bond paper'
        so.items += order.salesitem(
            product = paper,
            quantity = 10,
            price = dec('8.00')
        )

        ''' Create roles involved in order '''
        placing = party.placing()
        internal = party.internal()
        billto = party.billto()
        shipto = party.shipto()

        ''' Associate roles to the order '''
        so.placing  =  placing
        so.taking   =  internal
        so.billto   =  billto

        # Ship this sales item to Acme Company
        so.items.last.shipto = shipto

        ''' Associate contact mechanism to the order '''
        so.placedusing  =  acmeaddr
        so.takenusing   =  acmesubaddr
        so.billtousing  =  acmeaddr

        ''' Associate contact mechanism to the order item'''
        so.items.last.shiptousing = acmeaddr

        ''' Associate roles to the parties '''
        # Acme is places the order and Acme Subsidiary takes the order.
        acme.roles  +=  placing
        sub.roles   +=  internal
        acme.roles  +=  billto
        acme.roles  +=  shipto

        so.save()

        so1 = so.orm.reloaded()

        placing1 = so1.placing
        self.eq(placing.id, placing1.id)

        acme1 = placing1.party
        self.eq(acme.id, acme1.id)

        internal1 = so1.taking
        self.eq(internal.id, internal1.id)

        sub1 = internal1.party
        self.eq(sub.id, sub1.id)

        billto1 = so1.billto
        self.eq(billto.id, billto1.id)

        acme1 = billto1.party
        self.eq(acme.id, acme1.id)

        acmeaddr1     =  so1.placedusing
        acmesubaddr1  =  so1.takenusing
        acmeaddr2     =  so1.billtousing

        self.eq(acmeaddr.id,     acmeaddr1.id)
        self.eq(acmesubaddr.id,  acmesubaddr1.id)
        self.eq(acmeaddr.id,     acmeaddr2.id)


        itm = so1.items.first.orm.cast(order.salesitem)
        shipto1 = itm.shipto
        self.eq(shipto.id, shipto1.id)

        acme1 = shipto1.party
        self.eq(acme.id, acme1.id)

        shiptousing1 = itm.shiptousing
        self.eq(acmeaddr.id, shiptousing1.id)

    def it_uses_non_formal_roles(self):
        """ In addition to the formal order.roles (billto,
        shipto, taking, etc.) tested in it_uses_roles, we can also use
        the order.order_party to associate arbitrary roles between
        parties and orders. The actual roles are described by
        order_partytype, while the association is taken maintained by
        order_party.  """

        # Create roles
        salesperson  =  order.order_partytype(name='Salesperson')
        processor    =  order.order_partytype(name='Processor')
        reviewer     =  order.order_partytype(name='Reviewer')
        authorizer   =  order.order_partytype(name='Authorizer')

        # Create parties
        johnjones  =  getvalidperson(first='John',   last='Jones')
        nancy      =  getvalidperson(first='Nancy',  last='Barker')
        frank      =  getvalidperson(first='Frank',  last='Parks')
        joe        =  getvalidperson(first='Joe',    last='Williams')
        johnsmith  =  getvalidperson(first='John',   last='Smith')

        # Create sales order
        so = order.salesorder()

        # Associate roles
        so.order_parties += order.order_party(
            percent = 50,
            order_partytype = salesperson,
            party = johnjones
        )

        so.order_parties += order.order_party(
            percent = 50,
            order_partytype = salesperson,
            party = nancy
        )

        so.order_parties += order.order_party(
            order_partytype = processor,
            party = frank
        )

        so.order_parties += order.order_party(
            order_partytype = reviewer,
            party = joe
        )

        so.order_parties += order.order_party(
            order_partytype = authorizer,
            party = johnsmith,
        )

        so.save()

        so1 = so.orm.reloaded()

        ops = so.order_parties.sorted()
        ops1 = so1.order_parties.sorted()

        self.five(ops)
        self.five(ops1)

        for op, op1 in zip(ops, ops1):
            self.eq(op.id, op1.id)
            self.eq(op.percent, op1.percent)
            self.eq(op.party.id, op1.party.id)
            self.eq(op.order_partytype.id, op1.order_partytype.id)

    def it_creates_purchaseorder(self):
        """ Creating a purchase order is very similar to creating a
        sales order (see it_creates_salesorder). The difference is that
        the `purchaseorder` entity is used intead of the `salesorder`
        entity and `purchaseitem` is used instead of `salesitem`. The
        `purchaseorder` entity has slightly different party roles
        (`shiptobuyer` instead of `shipto`(customer), etc.).  However,
        purchuse orders use the same order_party, order_partytype and
        contactmechanism classes that salesorders use.  """

        ''' Create parties involved in purchase order '''
        sub      = party.company(name='ABC Subsidiary')
        ace      = party.company(name='Ace Cleaning Services')
        abccorp  = party.company(name='ABC Corporation')
        abcstore = party.company(name='ABC Retail Store')

        ''' Create contact mechanisms '''
        subaddr = party.address(
            address1='100 Main Street',
            address2='New York, New York',
        )

        aceaddr = party.address(
            address1='3590 Cottage Avenue',
            address2='New York, New York',
        )

        abccorpaddr = party.address(
            address1='100 Main Street',
            address2='New York, New York',
        )

        abcstoreaddr = party.address(
            address1='2345 Johnson Blvd',
            address2='New York, New York',
        )

        ''' Create purchase order '''
        po  =  order.purchaseorder()

        ''' Create roles involved in order '''
        shipto           =  party.shiptobuyer()
        placing          =  party.placingbuyer()
        supplier         =  party.supplier()
        billto           =  party.billtopurchaser()

        ''' Create a good for the sales item '''
        paper = getvalidproduct(product.good, comment=1)
        paper.name='Johnson fine grade 8½ by 11 bond paper'
        po.items += order.purchaseitem(
            product = paper,
            quantity = 10,
            price = dec('8.00'),
            shipto = shipto,
        )

        ''' Associate roles to the order '''
        po.placing   =  placing
        po.supplier  =  supplier
        po.billto    =  billto

        ''' Associate contact mechanism to the order '''
        po.placedusing  =  subaddr
        po.takenusing   =  aceaddr
        po.billtousing  =  abccorpaddr

        ''' Associate contact mechanism to the order item'''
        po.items.last.shiptousing = abcstoreaddr

        ''' Associate roles to the parties '''
        sub.roles       +=  placing
        ace.roles       +=  supplier
        abccorp.roles   +=  billto
        abcstore.roles  +=  shipto

        po.save()

        po1 = po.orm.reloaded()

        placing1 = po1.placing
        self.eq(placing.id, placing1.id)

        sub1 = placing1.party
        self.eq(sub.id, sub1.id)

        supplier1 = po1.supplier
        self.eq(supplier.id, supplier1.id)

        ace1 = supplier1.party
        self.eq(ace.id, ace1.id)

        billto1 = po1.billto
        self.eq(billto.id, billto1.id)

        abccorp1 = billto1.party
        self.eq(abccorp.id, abccorp1.id)

        subaddr1      =  po1.placedusing
        aceaddr1      =  po1.takenusing
        abccorpaddr1  =  po1.billtousing

        self.eq(subaddr.id,      subaddr1.id)
        self.eq(aceaddr.id,      aceaddr1.id)
        self.eq(abccorpaddr.id,  abccorpaddr1.id)

        itm = po1.items.first.orm.cast(order.purchaseitem)
        shipto1 = itm.shipto
        self.eq(shipto.id, shipto1.id)

        abcstore1 = shipto1.party
        self.eq(abcstore.id, abcstore1.id)

        abcstoreaddr1 = itm.shiptousing
        self.eq(abcstoreaddr.id, abcstoreaddr1.id)

    def it_applies_adjustments(self):
        so = order.salesorder()

        ''' Create a good for the sales item '''
        diskette = getvalidproduct(product.good, comment=1)
        diskette.name = "Jerry's box of 3½ inch diskettes"

        ''' Add good to sales order '''
        so.items += order.salesitem(
            product = diskette,
            quantity = 10,
            price = 5
        )

        so.adjustments += order.discount(
            amount = 1
        )

        so.adjustments += order.discount(
            percent = 10
        )

        so.adjustments += order.surcharge(
            amount = 10,
            adjustmenttype = order.adjustmenttype(
                name = 'Delivery outside normal geographic area'
            ),
        )

        so.adjustments += order.fee(
            amount = 1.5,
            adjustmenttype = order.adjustmenttype(
                name = 'Order processing fee'
            ),
        )

        so.save()

        so1 = so.orm.reloaded()

        adjs = so.adjustments.sorted()
        adjs1 = so1.adjustments.sorted()

        self.four(adjs)
        self.four(adjs1)

        adjtype = 0
        for adj, adj1 in zip(adjs, adjs1):
            self.eq(adj.id, adj1.id)
            self.eq(adj.amount, adj1.amount)
            self.eq(adj.percent, adj1.percent)

            if adj.adjustmenttype:
                self.eq(adj.adjustmenttype.id, adj1.adjustmenttype.id)
                self.eq(
                    adj.adjustmenttype.name,
                    adj1.adjustmenttype.name
                )
                adjtype += 1

            else:
                self.none(adj1.adjustmenttype)

        self.eq(2, adjtype)

    def it_applies_adjustments_to_salesitem(self):
        so = order.salesorder()

        ''' Create a good for the sales item '''
        diskette = getvalidproduct(product.good, comment=1)
        diskette.name = "Jerry's box of 3½ inch diskettes"

        ''' Add good to sales order '''
        so.items += order.salesitem(
            product = diskette,
            quantity = 10,
            price = 5
        )

        itm = so.items.last

        itm.adjustments += order.discount(
            amount = 1
        )

        itm.adjustments += order.discount(
            percent = 10
        )

        itm.adjustments += order.surcharge(
            amount = 10,
            adjustmenttype = order.adjustmenttype(
                name = 'Delivery outside normal geographic area'
            ),
        )

        itm.adjustments += order.fee(
            amount = 1.5,
            adjustmenttype = order.adjustmenttype(
                name = 'Order processing fee'
            ),
        )

        so.save()

        so1 = so.orm.reloaded()

        adjs = so.items.last.adjustments.sorted()
        adjs1 = so1.items.last.adjustments.sorted()

        self.four(adjs)
        self.four(adjs1)

        adjtype = 0
        for adj, adj1 in zip(adjs, adjs1):
            self.eq(adj.id, adj1.id)
            self.eq(adj.amount, adj1.amount)
            self.eq(adj.percent, adj1.percent)

            if adj.adjustmenttype:
                self.eq(adj.adjustmenttype.id, adj1.adjustmenttype.id)
                self.eq(
                    adj.adjustmenttype.name,
                    adj1.adjustmenttype.name
                )
                adjtype += 1

            else:
                self.none(adj1.adjustmenttype)

        self.eq(2, adjtype)

    def it_populates_rate_table(self):
        cat = product.category()
        cat.name = uuid4().hex

        reg = party.region.create(
            ('United States of America',  party.region.Country,    'USA'),
            ('Arizona',                   party.region.State,      'AZ'),
            ('Scottsdale',                party.region.City),
            ('85224',                     party.region.Postal)
        )

        rt = order.rate(
            percent = 7.0,
            region = reg,
        )

        rt.save()

        rt1 = rt.orm.reloaded()

        self.eq(rt.id, rt1.id)
        self.eq(rt.region.id, rt1.region.id)
        self.none(rt.category)
        self.none(rt1.category)

        rt = order.rate(
            percent = 7.0,
            region = reg,
            category = cat,
        )

        rt.save()

        rt1 = rt.orm.reloaded()

        self.eq(rt.id, rt1.id)
        self.eq(rt.region.id, rt1.region.id)
        self.eq(rt.category.id, rt1.category.id)

    def it_records_statuses(self):
        ''' Create sales order '''
        so = order.salesorder()

        ''' Create statutes '''
        received = order.statustype(name='Recieved')
        approved = order.statustype(name='Approved')
        canceled = order.statustype(name='Canceled')

        ''' Create a good for the sales item '''
        diskette = getvalidproduct(product.good, comment=1)
        diskette.name = "Jerry's box of 3½ inch diskettes"

        ''' Add good to sales order '''
        so.items += order.salesitem(
            product = diskette,
            quantity = 10,
            price = 5
        )

        # Get the sales item
        itm = so.items.last

        so.statuses += order.status(
            begin = primative.datetime('2020-01-04 13:11:23'),
            statustype = received,
        )

        itm.statuses += order.status(
            begin = primative.datetime('2020-01-04 13:11:24'),
            statustype = received,
        )

        so.statuses += order.status(
            begin = primative.datetime('2020-01-04 13:11:25'),
            statustype = received,
        )

        itm.statuses += order.status(
            begin = primative.datetime('2020-01-04 13:11:26'),
            statustype = approved,
        )

        so.save()
        
        so1 = so.orm.reloaded()

        es = (
            (so, so1),
            (so.items.first, so1.items.first)
        )

        for e, e1 in es:
            sts  = e.statuses.sorted()
            sts1 = e1.statuses.sorted()

            self.two(sts)
            self.two(sts1)

            for st, st1 in zip(sts, sts1):
                self.eq(st.id, st1.id)
                self.eq(st.statustype.id, st1.statustype.id)

    def it_creates_terms(self):
        # Create an order
        so = order.salesorder()

        # Add a term to the order
        so.terms += order.term(
            value = 25,
            termtype = order.termtype(
                name = 'Percentage cancellation charge'
            )
        )

        # Add another term to the order
        so.terms += order.term(
            value = 10,
            termtype = order.termtype(
                name = 'Days within which one may cancel order '
                       'without a penalty'
            )
        )

        # Create a product for the order
        pen = getvalidproduct(product.good, comment=1)
        pen.name ='Henry #2 Pencil'

        # Add an item
        so.items += order.salesitem(
            product = pen
        )

        # Add a term to the item
        so.items.last.terms += order.term(
            quantity = 1,
            price = 5,
        )

        # Assign a termtype to the term
        so.items.last.terms.last.termtype = order.termtype(
            name = 'No exchange or refunds once delivered'
        )

        so.save()

        so1 = so.orm.reloaded()

        trms = so.terms.sorted()
        trms1 = so1.terms.sorted()

        self.two(trms)
        self.two(trms1)

        for trm, trm1 in zip(trms, trms1):
            self.eq(trm.id, trm1.id)
            self.eq(trm.termtype.id, trm1.termtype.id)
            self.eq(trm.termtype.name, trm1.termtype.name)

        trms = so.items.first.terms
        trms1 = so1.items.first.terms

        self.one(trms)
        self.one(trms1)

        self.eq(trms.first.id, trms1.first.id)
        self.eq(trms.first.termtype.id, trms1.first.termtype.id)
        self.eq(trms.first.termtype.name, trms1.first.termtype.name)

    def it_associates_item_with_item(self):
        so = order.salesorder()

        # Create a product for the order
        pen = getvalidproduct(product.good, comment=1)
        pen.name ='Henry #2 Pencil'

        # Add an item
        so.items += order.salesitem(
            product = pen,
            quantity = 20,
        )

        po = order.purchaseorder()

        # Add an item
        po.items += order.purchaseitem(
            product = pen,
            quantity = 100,
        )

        ii = order.item_item(
            subject = so.items.last,
            object  = po.items.last,
        )

        ii.save()

        itm = so.items.last
        itm1 = so.items.last.orm.reloaded()

        iis  = itm.item_items
        iis1 = itm1.item_items

        self.one(iis)
        self.one(iis1)

        self.eq(
            iis.first.subject.id,
            iis1.first.subject.id,
        )

        self.eq(
            iis.first.object.id,
            iis1.first.object.id,
        )

if __name__ == '__main__':
    tester.cli().run()
