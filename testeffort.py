#!/usr/bin/python3
# vim: set et ts=4 sw=4 fdm=marker

########################################################################
# Copyright (C) Jesse Hogan - All Rights Reserved                      #
# Unauthorized copying of this file, via any medium is strictly        #
# prohibited                                                           #
# Proprietary and confidential                                         #
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2022                 #
########################################################################

"I have not failed. I've just found 10,000 ways that won't work."
# Thomas A. Edison

import apriori; apriori.model()

from dbg import B, PM, PR
from func import enumerate, getattr
from pprint import pprint
from primative import datetime, date
from uuid import uuid4, UUID
import builtins
import tester
import ecommerce
import orm
import party
import order
import db
import effort
import sys
import testproduct
import product
import shipment
import asset

class effort_(tester.tester):
    def __init__(self, *args, **kwargs):
        mods = 'product', 'effort', 'apriori', 'party', 'asset', 'order'
        super().__init__(mods=mods, *args, **kwargs)

        orm.security().owner = ecommerce.users.root

        com = party.company(name='Carapacian')
        orm.security().proprietor = com
        com.save(com)

    def it_creates_requirements(self):
        req = apriori.requirement(
            requirementtype = order.requirementtype(
                name='Production run'
            ),
            created = 'Jul 5, 2000',
            required = 'Aug 5, 2000',
            description = self.dedent('''
            Anticipated demand of 2,000 custom engraved black pens with
            gold trim.
            ''')
        )

        req.save()

        req1 = req.orm.reloaded()

        self.eq(req.id,                    req1.id)
        self.eq(req.created,               req1.created)
        self.ne(req.createdat,             req1.created)
        self.eq(req.required,              req1.required)
        self.eq(req.description,           req1.description)
        self.eq(req.created,               req1.created)
        self.eq(req.requirementtype.id,    req1.requirementtype.id)
        self.eq(req.requirementtype.name,  req1.requirementtype.name)

    def it_creates_deliverables(self):
        """ Deliverables here means assets, products and deliverables
        attached to a work ``requirement``.
        """

        # Create work requirement types
        run = effort.requirementtype(name='Production run')
        ip  = effort.requirementtype(name='Internal project')
        maint = effort.requirementtype(name='Maintenance')

        # Create product, deliverable and asset
        good = testproduct.product_.getvalid(product.good, comment=1)
        good.name = 'Engraved black pen with gold trim'

        deliv = effort.deliverable(name='2001 Sales/Marketing Plan')

        ass = shipment.asset(name='Engraving machine')

        # Create requirements

        # We need 2000 engraved pens for the anticipatde demand
        req = effort.requirement(
            description = self.dedent('''
            Anticipated demand of 2,000 custom-engraved black pens with gold trim.
            '''),
            product          =  good,
            quantity         =  2000,
            requirementtype  =  run,
        )

        req.save()

        req1 = req.orm.reloaded()
        self.eq(req.id, req1.id)
        self.eq(req.product.id, req1.product.id)
        self.eq(req.quantity, req1.quantity)
        self.eq(req.requirementtype.id, req1.requirementtype.id)
        self.none(req.deliverable)
        self.none(req1.asset)

        # We need a sales plan; call it 2001 Sales/Marketing Plan
        req = effort.requirement(
            description = self.dedent('''
            2001 Sales/Marketing Plan
            '''),
            deliverable      =  deliv,
            requirementtype  =  ip,
        )

        req.save()

        req1 = req.orm.reloaded()
        self.eq(req.id, req1.id)
        self.none(req1.product)
        self.none(req1.asset)
        self.eq(0, req1.quantity)
        self.eq(ip.id, req1.requirementtype.id)

        # We need to fixe the engraving machine 
        req = effort.requirement(
            description = self.dedent('''
            Fix engraving machine
            '''),
            requirementtype  =  maint,
            asset            =  ass
        )

        req.save()

        req1 = req.orm.reloaded()
        self.eq(req.id, req1.id)
        self.none(req1.product)
        self.none(req1.deliverable)
        self.eq(0, req1.quantity)
        self.eq(maint.id, req1.requirementtype.id)
        self.eq(ass.id, req1.asset.id)

    def it_creates_roles(self):
        abc = party.company(name='ABC Manufacturing, Inc.')

        req = effort.requirement(description='Fix equipment')

        role = effort.role(
            roletype = effort.roletype(name='Created for'),
            begin = 'Jul 5, 2000',
        )

        abc.roles += role

        req.roles += role

        req.save()

        req1 = req.orm.reloaded()

        self.eq(req.id, req1.id)
        self.eq(abc.id, req1.roles.first.party.id)
        self.eq(role.roletype.id, req1.roles.first.roletype.id)
        self.eq(req.roles.first.begin, req1.roles.first.begin)
        self.none(req1.roles.first.end)

    def it_associates_effort_with_requirment(self):
        ''' Associate using effort_requirement '''
        req50985 = effort.requirement(
           description = self.dedent('''
           Anticipated demand of 2,000 custom-engraved black pens
           with gold trim
           ''')
        )

        req51245 = effort.requirement(
           description = self.dedent('''
           Anticipated demand of 1,500 custom-engraved black pens
           with gold trim
           ''')
        )

        eff28045 = effort.productionrun(
            scheduledbegin = 'June 1, 2000',
            name = 'Production run',
            description = self.dedent('''
            Production run of 3,500 pencils
            '''),
        )

        eff28045.effort_requirements += effort.effort_requirement(
            requirement = req50985,
        )

        eff28045.effort_requirements += effort.effort_requirement(
            requirement = req51245,
        )

        eff28045.save()

        eff28045_1 = eff28045.orm.reloaded()

        ers = eff28045.effort_requirements.sorted()
        ers1 = eff28045_1.effort_requirements.sorted()

        self.two(ers)
        self.two(ers1)

        for er, er1 in zip(ers, ers1):
            self.eq(er.id, er1.id)
            self.eq(er.requirement.id, er1.requirement.id)
            self.eq(er.requirement.id, er1.requirement.id)

        ''' Associate using effort.item '''

        # Create efforts
        eff29534 = effort.productionrun(
            name = 'Production run #1 of pens',
            scheduledbegin = 'Feb 23, 2001',
        )

        eff29874 = effort.productionrun(
            name = 'Production run #2 of pens',
            scheduledbegin = 'Mar 23, 2001',
        )

        # Create requirement
        req = effort.requirement(
            description = 'Need for customized pens'
        )

        # Create work order item
        itm = effort.item(
            description = self.dedent('''
            Sales Order Item to produce 2,500 customized engraved pens.
            ''')
        )

        # Link requirement to work order item
        req.item_requirements += effort.item_requirement(
            item = itm 
        )

        # Link work order item to efforts
        itm.effort_items += effort.effort_item(
            effort = eff29874
        )

        itm.effort_items += effort.effort_item(
            effort = eff29534
        )

        req.save()

        req1 = req.orm.reloaded()

        self.eq(req.id, req1.id)

        self.one(req.item_requirements)
        self.one(req1.item_requirements)

        ir = req.item_requirements.first
        ir1 = req1.item_requirements.first

        self.eq(ir.id, ir1.id)

        self.eq(ir.item.id, ir1.item.id)

        eis = ir.item.effort_items.sorted()
        eis1 = ir1.item.effort_items.sorted()

        self.two(eis)
        self.two(eis1)

        for ei, ei1 in zip(eis, eis1):
            self.eq(ei.id, ei1.id)
            self.eq(ei.effort.id, ei1.effort.id)

    def it_associates_efforts_with_efforts(self):
        job28045 = effort.job(
            name = 'Production run #1'
        )

        act120001 = effort.activity(name='Set up production line')
        act120002 = effort.activity(name='Operate machinery')
        act120003 = effort.activity(name='Clean up machinery')
        act120004 = effort.activity(name='Quality assure goods produced')

        for act in (act120001, act120002, act120003, act120004):
            job28045.effort_efforts += effort.effort_effort(
                object = act
            )


        job28045.save()

        job28045_1 = job28045.orm.reloaded()

        ees = job28045.effort_efforts.sorted()
        ees1 = job28045_1.effort_efforts.sorted()

        self.eq(job28045.id, job28045_1.id)

        self.four(ees)
        self.four(ees1)

        for ee, ee1 in zip(ees, ees1):
            self.eq(ee.id, ee1.id)
            self.eq(ee.subject.id, ee1.subject.id)
            self.eq(ee.object.id, ee1.object.id)

    def it_associates_preceding_efforts_with_efforts(self):
        job28045 = effort.job(
            name = 'Production run #1'
        )

        act120001 = effort.activity(name='Set up production line')
        act120002 = effort.activity(name='Operate machinery')
        act120003 = effort.activity(name='Clean up machinery')
        act120004 = effort.activity(name='Quality assure goods produced')

        for act in (act120001, act120002, act120003, act120004):
            job28045.effort_efforts += effort.effort_effort(
                object = act
            )

        # Declare that "Operate machinery" activity (act120002) depends
        # on the completion of the "Set up production line' activity
        # (act120001).

        act120001.effort_efforts += \
            effort.effort_effort_precedency(
                object = act120002
            )

        job28045.save()

        job28045_1 = job28045.orm.reloaded()

        ees = job28045.effort_efforts.sorted()
        ees1 = job28045_1.effort_efforts.sorted()

        self.eq(job28045.id, job28045_1.id)

        self.four(ees)
        self.four(ees1)

        for ee, ee1 in zip(ees, ees1):
            self.eq(ee.id, ee1.id)
            self.eq(ee.subject.id, ee1.subject.id)
            self.eq(ee.object.id, ee1.object.id)

            if ee1.object.id == act120001.id:
                ees1 = ee1.object.effort_efforts
                self.one(ees1)
                self.eq(ees1.first.subject.id, act120001.id)
                self.eq(ees1.first.object.id, act120002.id)

    def it_associates_effort_to_party(self):
        # Create effort
        eff = effort.effort(name='Develop a sales and marketing plan')

        # Create persons
        dick  =  party.person(first='Dick',  last='Jones')
        bob   =  party.person(first='Bob',   last='Jenkins')
        john  =  party.person(first='John',  last='Smith')
        jane  =  party.person(first='Jane',  last='Smith')

        # Create role types
        manager = effort.effort_partytype(name='Project manager')
        admin   = effort.effort_partytype(name='Project administrator')
        member  = effort.effort_partytype(name='Team member')

        eff.effort_parties += effort.effort_party(
            party = dick,
            effort_partytype = manager,
            begin = 'Jan 2, 2001',
            end = 'Sept 15, 2001',
        )

        eff.effort_parties += effort.effort_party(
            party = bob,
            effort_partytype = admin,
        )


        eff.effort_parties += effort.effort_party(
            party = john,
            effort_partytype = member,
            begin = 'Mar 5, 2001',
            end = 'Aug 6, 2001',
            comment = 'Leaving for three-week vacation on Aug 7, 2001'
        )


        eff.effort_parties += effort.effort_party(
            party = john,
            effort_partytype = member,
            begin = 'Sept 1, 2001',
            end = 'Dec 2, 2001',
        )

        eff.effort_parties += effort.effort_party(
            party = jane,
            effort_partytype = member,
            begin = 'Aug 6, 2000',
            end = 'Sept 15, 2001',
        )

        eff.save()

        eff1 = eff.orm.reloaded()

        eps = eff.effort_parties.sorted()
        eps1 = eff1.effort_parties.sorted()

        self.five(eps)
        self.five(eps1)

        for ep, ep1 in zip(eps, eps1):
            self.eq(ep.id, ep1.id)
            self.eq(ep.effort_partytype.id, ep1.effort_partytype.id)
            self.eq(ep.begin, ep1.begin)
            self.eq(ep.end, ep1.end)

    def it_creates_status(self):
        act = effort.activity(
            name='Set up production line',
        )

        act.statuses += effort.status(
            begin = 'Jun 2 2000, 1pm',
            statustype = effort.statustype(name='Started'),
        )

        act.statuses += effort.status(
            begin = 'Jun 2 2000, 2pm',
            statustype = effort.statustype(name='Completed'),
        )

        act.save()
        act1 = act.orm.reloaded()

        self.eq(act.id, act1.id)

        sts = act.statuses.sorted()
        sts1 = act1.statuses.sorted()

        self.two(sts)
        self.two(sts1)

        for st, st1 in zip(sts, sts1):
            self.eq(st.id, st1.id)
            self.eq(st.begin, st1.begin)
            self.eq(st.statustype.id, st1.statustype.id)
            self.eq(st.statustype.name, st1.statustype.name)

    def it_creates_time_entries(self):
        # Create efforts
        eff29000 = effort.effort(
            name = 'Develop a sales and marketing plan'
        )

        eff29005 = effort.effort(
            name = 'Develop a sales and marketing plan'
        )

        # Create party
        dick = party.person(first='Dick',  last='Jones')

        # Create a role for the party to log time as
        emp = party.employee()

        dick.roles += emp

        # Create a timesheet
        ts = effort.timesheet(
            begin = 'Jan 1, 2001',
            end   = 'Jan 15, 2001',
        )

        # Assign the timesheet to the role's timesheet collection
        ts.worker = emp

        # Add `time`` entries to the timesheet for each of the efforts
        ts.times += effort.time(
            begin = 'Jan 2, 2001',
            end   = 'Jan 4, 2001',
            hours = 13,
            effort = eff29000,
        )

        ts.times += effort.time(
            begin = 'Jan 5, 2001',
            end   = 'Jan 6, 2001',
            hours = 7,
            effort = eff29005,
        )

        # Save and reload
        dick.save(ts)
        dict1 = dick.orm.reloaded()

        # Get the employee role
        emp1 = dick.roles.first

        self.eq(emp.id, emp1.id)

        # Use the employee role to get its collection of timesheets.

        # TODO:9b700e9a We should be able to call ``emp1.timesheets``
        # but the ORM doesn't suppert that yet. We are in a situation
        # where employee can't have a reference to ``timesheets`` as a
        # collection because due to the circular reference it would
        # cause.
        ts1 = effort.timesheets('worker__workerid', emp1.id).first

        self.eq(ts.id, ts1.id)

        times = ts.times.sorted()
        times1 = ts1.times.sorted()

        self.two(times)
        self.two(times1)

        for t, t1 in zip(times, times1):
            self.eq(t.id, t1.id)
            self.eq(t.begin, t1.begin)
            self.eq(t.end, t1.end)
            self.eq(t.hours, t1.hours)
            self.eq(t.comment, t1.comment)

    def it_creates_rates(self):
        # Create work effort (task)
        tsk = effort.task(name='Develop accounting programm')

        # Create types of rates
        rgbill  =  party.ratetype(name='Regular billing')
        otbill  =  party.ratetype(name='Overtime billing')
        rgpay   =  party.ratetype(name='Regular pay')
        otpay   =  party.ratetype(name='Overtime pay')

        # Create a party
        gary = party.person(first='Gary', last='Smith')

        # Associate party to work effort
        ep = effort.effort_party(
            effort = tsk,
        )

        ep.party = gary

        # Add rates to the association between effort and party
        ep.rates += party.rate(
            begin    = 'May 15, 2000',
            end      = 'May 14, 2001',
            rate     = 65,
            ratetype = rgbill,
        )

        ep.rates += party.rate(
            begin    = 'May 15, 2000',
            end      = 'May 14, 2001',
            rate     = 70,
            ratetype = otbill,
        )

        ep.rates += party.rate(
            begin    = 'May 15, 2000',
            end      = 'May 14, 2001',
            rate     = 40,
            ratetype = rgpay,
        )
        ep.rates += party.rate(
            begin    = 'May 15, 2000',
            end      = 'May 14, 2001',
            rate     = 43,
            ratetype = otpay,
        )
        ep.rates += party.rate(
            begin    = 'May 15, 2000',
            rate     = 45,
            ratetype = rgpay,
        )
        ep.rates += party.rate(
            begin    = 'May 15, 2000',
            rate     = 45,
            ratetype = otpay,
        )
        ep.save()
        ep1 = ep.orm.reloaded()

        self.eq(ep.id, ep1.id)

        rts = ep.rates.sorted()
        rts1 = ep1.rates.sorted()

        self.six(rts)
        self.six(rts1)

        for rt, rt1 in zip(rts, rts1):
            self.eq(rt.begin, rt1.begin)
            self.eq(rt.end, rt1.end)
            self.eq(rt.rate, rt1.rate)
            self.eq(rt.ratetype.id, rt1.ratetype.id)
            self.eq(rt.ratetype.name, rt1.ratetype.name)

    def it_associates_effort_with_inventory_items(self):
        # Create work effort
        tsk = effort.task(name='Assemble pencil components')

        # Create goods
        cartridge = testproduct.product_.getvalid(product.good, comment=1)
        cartridge.name = 'Pencil cartridges'

        eraser = testproduct.product_.getvalid(product.good, comment=1)
        eraser.name = 'Pencil eraser'

        label = testproduct.product_.getvalid(product.good, comment=1)
        label.name = 'Pencil label'

        # Create inventory item
        cartridge.items += product.serial(number=100020)
        cartridge = cartridge.items.last

        eraser.items += product.serial(number=100021)
        eraser = eraser.items.last

        label.items += product.serial(number=100022)
        label = label.items.last

        # Associate work effort with inventory items
        for itm in (cartridge, eraser, label):
            tsk.effort_inventoryitems += effort.effort_inventoryitem(
                quantity = 100,
                item = itm
            )

        tsk.save()

        tsk1 = tsk.orm.reloaded()

        eis = tsk.effort_inventoryitems.sorted()
        eis1 = tsk1.effort_inventoryitems.sorted()

        self.three(eis)
        self.three(eis1)

        for ei, ei1 in zip(eis, eis1):
            self.eq(ei.id, ei1.id)
            self.eq(ei.quantity, ei1.quantity)
            self.eq(ei.item.id, ei1.item.id)

    def it_creates_fixed_assets(self):
        ass = asset.asset(
            name='Pencil labeler #1',
            type = asset.type(name='Pencil-making machine'),
            acquired = 'Jun 12, 2000',
            serviced = 'Jun 12, 2000',
            nextserviced = 'Jun 12, 2001',
            capacity = 1_000_000,
            measure = product.measure(name='Pens/day')
        )

        ass.save()
        ass1 = ass.orm.reloaded()
        attrs = (
            'name', 'acquired', 'serviced', 'nextserviced',
            'capacity', 'measure.id', 'measure.name', 'type.id',
            'type.name'
        )

        for attr in attrs:
            self.eq(getattr(ass, attr), getattr(ass1, attr))
    
    def it_creates_assettypes_recursively(self):
        eq = asset.type(name='Equipment')
        eq.types += asset.type(name='Pencil-making machine')
        eq.types += asset.type(name='Pen-making machine')
        eq.types += asset.type(name='Paper-making machine')

        eq.save()
        eq1 = eq.orm.reloaded()

        self.three(eq.types)
        self.three(eq1.types)

        for typ, typ1 in zip(eq.types.sorted(), eq1.types.sorted()):
            self.eq(typ.id, typ1.id)
            self.eq(typ.name, typ1.name)

    def it_associates_effort_with_asset(self):
        eff = effort.effort(name='Label pencils')
        ass = asset.asset(name='Pencile labeler #1')

        eff.asset_efforts += effort.asset_effort(
            begin = 'Jun 12, 2000',
            end   = 'Jun 15, 2000',
        )

        eff.save()
        eff1 = eff.orm.reloaded()

        self.eq(eff.id, eff1.id)

        aes = eff.asset_efforts.sorted()
        aes1 = eff1.asset_efforts.sorted()

        self.one(aes)
        self.one(aes1)

        for ae, ae1 in zip(aes, aes1):
            self.eq(ae.id, ae1.id)
            self.eq(ae.begin, ae1.begin)
            self.eq(ae.end, ae1.end)

    def it_creates_asset_to_party_assignments(self):
        john = party.person(first='John', last='Smith')
        car = asset.asset(name='Car #25')

        john.asset_parties += party.asset_party(
            begin = 'Jan 1, 2000',
            end   = 'Jan 1, 2001',
            asset_partystatustype = party.asset_partystatustype(
                name = 'Active'
            )
        )

        john.save()
        john1 = john.orm.reloaded()

        self.eq(john.id, john1.id)

        aps = john.asset_parties.sorted()
        aps1 = john1.asset_parties.sorted()

        self.one(aps)
        self.one(aps1)

        ap = aps.first
        ap1 = aps1.first

        self.eq(ap.id, ap1.id)
        self.eq(date('Jan 1, 2000'), ap1.begin)
        self.eq(date('Jan 1, 2001'), ap1.end)
        self.eq('Active', ap1.asset_partystatustype.name)

    def it_creates_standards(self):
        ''' Test good standard '''
        # Create effort type
        pencil = effort.type(name='Large production run of pencils')

        # Create a good
        eraser = testproduct.product_.getvalid(product.good, comment=1)
        eraser.name = 'Pencil eraser'

        # Add a goods standard to the 'Large production run of pencils'
        # effort type
        pencil.goodstandards += effort.goodstandard(
            quantity = 1_000,
            cost = 2_500,
            good = eraser,
        )

        # Save, reload and test
        pencil.save()

        pencil1 = pencil.orm.reloaded()

        sts = pencil.goodstandards.sorted()
        sts1 = pencil1.goodstandards.sorted()

        st = sts.first
        st1 = sts1.first

        self.eq(st.id, st1.id)
        self.eq(1_000, st1.quantity)
        self.eq(2_500, st1.cost)
        self.eq(st.good.id, st1.good.id)
        self.eq(st.good.name, st1.good.name)

        ''' Test asset standard '''
        labeler = asset.type(name='Pencil labeler')

        pencil.assetstandards += effort.assetstandard(
            quantity = 1,
            duration = 10,
            asset = labeler,
        )

        pencil.save()

        pencil1 = pencil.orm.reloaded()

        sts = pencil.assetstandards
        sts1 = pencil1.assetstandards

        self.one(sts)
        self.one(sts1)

        st = sts.first
        st1 = sts1.first

        self.eq(st.id, st1.id)
        self.eq(1, st1.quantity)
        self.eq(10, st1.duration)
        self.eq(st.asset.id, st1.asset.id)
        self.eq(st.asset.name, st1.asset.name)

class backlog(tester.tester):
    def __init__(self, *args, **kwargs):
        mods = 'effort',
        super().__init__(mods=mods, *args, **kwargs)

        # TODO Remove when accessability properties have been
        # implemented.
        orm.security().owner = ecommerce.users.root

    @staticmethod
    def getvalid():
        bl = effort.backlog()
        bl.name = 'Maintenance Backlog'
        bl.description = 'A backlog of maintenance and tech debt items'
        bl.begin = '2020-01-01'
        bl.end = '2020-02-01'
        bl.goal = (
            'Identify and resolve technical debt and maintenance items'
            'that are not urgent but need attention.'
        )

        return bl

    def it_creates(self):
        bl = self.getvalid()

        bl.save()

        bl1 = bl.orm.reloaded()

        attrs = 'name', 'description', 'begin', 'end', 'goal'

        for attr in attrs:
            self.eq(getattr(bl, attr), getattr(bl1, attr))

    def it_updates(self):
        bl = self.getvalid()
        bl.save()

        bl1 = bl.orm.reloaded()

        bl1.name = 'Maintenance Backlog (OLD)'

        bl1.save()
        
        bl1 = bl1.orm.reloaded()

        attrs = 'description', 'begin', 'end', 'goal'

        self.eq('Maintenance Backlog (OLD)', bl1.name)

        for attr in attrs:
            self.eq(getattr(bl, attr), getattr(bl1, attr))

    def it_has_correct_types(self):
        bl = self.getvalid()

        self.type(str,   bl.name)
        self.type(str,   bl.description)
        self.type(date,  bl.begin)
        self.type(date,  bl.end)
        self.type(str,   bl.goal)

    def it_adds_a_story(self):
        bl = self.getvalid()
        st = story.getvalid()
        bl.insert(st)

        bss = bl.backlog_stories

        self.one(bss)
        bs = bss.only
        self.is_(st, bs.story)
        self.eq(0, bs.ordinal)

        bl.save()

        bl1 = bl.orm.reloaded()

        bss = bl1.backlog_stories

        self.one(bss)
        bs = bss.only
        self.eq(st.id, bs.story.id)
        self.eq(0, bs.ordinal)

    def it_adds_multiple_stories(self):
        ''' Insert multiple stories at the loweset ranking '''
        bl = self.getvalid()
        st1 = story.getvalid()
        st2 = story.getvalid()

        # This will put st1 at ordinal 0
        #
        #     ordinal | story
        #     ------- |------
        #           0 | st1
        #
        bl.insert(st1)

        ''' Insert at the begining (lowest rank) '''
        # Note that inserting st2 here ranks it lowest in the backlog
        # because the `ord` param of `insert()` defaults to zero. This
        # means st1's ordinal will be incremented from 0 to one.
        #
        #     ordinal | story
        #     ------- |------
        #           0 | st2
        #           1 | st1
        #
        bl.insert(st2)

        bss = bl.backlog_stories
        self.two(bss)

        bss.sort('ordinal')

        self.eq([0, 1], bss.pluck('ordinal'))

        for bs, st in zip(bss, [st1, st2]):
            B()
            self.is_(st, bs.story)

        bl.save()

        bl1 = bl.orm.reloaded()

        bss = bl1.backlog_stories
        bss.sort('ordinal')

        self.two(bss)

        self.eq([0, 1], bss.pluck('ordinal'))

        for bs, st in zip(bss, [st1, st2]):
            self.eq(st.id, bs.story.id)


class story(tester.tester):
    def __init__(self, *args, **kwargs):
        mods = 'effort',
        super().__init__(mods=mods, *args, **kwargs)

        # TODO Remove when accessability properties have been
        # implemented.
        orm.security().owner = ecommerce.users.root

    @staticmethod
    def getvalid():
        st = effort.story()
        st.name = 'Radical site redesign'
        st.description =  (
            'As a user,'
            "I want the site's design to be radically different,"
            "So I can have more things to complain about."
        )
        st.points = 64
        return st

    def it_creates(self):
        st = self.getvalid()

        st.save()

        st1 = st.orm.reloaded()

        attrs = 'name', 'description', 'points',

        for attr in attrs:
            self.eq(getattr(st, attr), getattr(st1, attr))

    def it_updates(self):
        st = self.getvalid()
        st.save()
        st1 = st.orm.reloaded()

        st1.name += 'X'
        st1.points = int(st1.points) * 4

        st1.save()
        st2 = st.orm.reloaded()

        self.eq(st1.name, st2.name)
        self.eq(int(st.points) * 4, int(st2.points))

    def it_has_correct_types(self):
        st = effort.story()
        st.name = 'Site redesign'
        st.description =  (
            'As a user,'
            "I want the site's design to be radically different,"
            "So I can have more things to complain about."
        )
        st.points = 16

        self.type(str,   st.name)
        self.type(str,   st.description)
        self.type(str,   st.points)

if __name__ == '__main__':
    tester.cli().run()
