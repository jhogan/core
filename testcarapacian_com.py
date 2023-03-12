#!/usr/bin/python3
# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2022

import apriori; apriori.model()

from datetime import timezone, datetime, date
from dbg import B, PM
from func import enumerate, getattr
from uuid import uuid4, UUID
from decimal import Decimal as dec
import carapacian_com
import db
import effort
import orm
import party
import pom
import primative
import random
import tester

class sites(tester.tester):
    def __init__(self, *args, **kwargs):
        mods = 'file', 'asset', 
        super().__init__(mods=mods, *args, **kwargs)
    def it_inherits_from_pom_site(self):
        wss = carapacian_com.sites()
        self.isinstance(wss, pom.sites)

class site(tester.tester):
    def __init__(self, *args, **kwargs):
        mods = 'file', 'asset', 
        super().__init__(mods=mods, *args, **kwargs)

    def it_has_correct_id(self):
        # Set constant
        Id = UUID(hex='c0784fca-3fe7-45e6-87f8-e2ebbc4e7bf4')

        # Test class-level constant
        self.eq(Id, carapacian_com.site.Id)

        # Test instance
        self.eq(Id, carapacian_com.site().id)

    def it_has_correct_proprietor(self):
        cara = party.companies.carapacian
        self.is_(cara, carapacian_com.site().Proprietor)

    def it_has_correct_host(self):
        Host = 'carapacian.com'
        self.eq(Host, carapacian_com.site().host)

    def it_has_correct_title(self):
        Title = 'Carapacian Sustainable Software'

        ws = carapacian_com.site()

        self.eq(Title, ws.title)

    def it_has_carapacian_as_its_proprietor(self):
        ws = carapacian_com.site()
        self.eq(ws.proprietor.id, party.companies.carapacian.id)

''' Page tests '''

class home(tester.tester):
    def __init__(self, *args, **kwargs):
        mods = 'file', 'asset', 
        super().__init__(mods=mods, *args, **kwargs)

    def it_calls_name(self):
        pg = carapacian_com.home()
        self.eq('index', pg.name)

    def it_GETs(self):
        ws = carapacian_com.site()
        tab = self.browser().tab()

        res = tab.get('/', ws)
        self.status(200, res)

        self.eq(f'{ws.title} | Index', res['html>head>title'].text)

    def it_renders_menu(self):
        ws = carapacian_com.site()
        tab = self.browser().tab()

        res = tab.navigate('/', ws)
        self.status(200, res)

        mnus = tab['header>section>nav[aria-label=Main]']
        self.one(mnus)

    def it_has_correct_title(self):
        Title = 'Carapacian Sustainable Software | Index'

        tab = self.browser().tab()
        ws = carapacian_com.site()
        res = tab.get('/', ws)
        self.startswith(Title, res['html>head>title'].text)

class tickets(tester.tester):
    def __init__(self, *args, **kwargs):
        mods = 'file', 'asset', 
        super().__init__(mods=mods, *args, **kwargs)

    def it_calls_name(self):
        pg = carapacian_com.tickets()
        self.eq('tickets', pg.name)

    def it_GETs(self):
        ws = carapacian_com.site()
        tab = self.browser().tab()

        res = tab.get('/en/tickets', ws)
        self.status(200, res)

        self.eq(f'{ws.title} | Tickets', res['html>head>title'].text)

    def it_has_correct_title(self):
        Title = 'Carapacian Sustainable Software | Tickets'

        tab = self.browser().tab()
        ws = carapacian_com.site()
        res = tab.get('/en/tickets', ws)
        self.startswith(Title, res['html>head>title'].text)

    def it_responds_to_button_click(self):
        # NOTE This test is intended for the development of basic AJAX
        # functionality in a real browser. As /en/tickets evolves, we
        # will need to remove this test and the "Click Me" button logic.
        tab = self.browser().tab()
        ws = carapacian_com.site()

        res = tab.navigate('/en/tickets', ws)
        self.ok(res)
        btn, btn1 = tab.html['.test1 button']

        p, p1 = tab.html['.test1 p']
        self.empty(p.text + p1.text)

        btn.click()
        btn1.click()

        p, p1 = tab.html['.test1 p']

        dt = primative.datetime(p.text)
        dt1 = primative.datetime(p1.text)
        today = primative.datetime.utcnow().date
        
        self.gt(dt, dt1)
        self.eq(dt.date, today)
        self.eq(dt1.date, today)

class ticketsspa(tester.tester):
    def it_calls_name(self):
        pg = carapacian_com.ticketsspa.ticket()
        self.eq('ticket', pg.name)

    def it_GETs(self):
        ws = carapacian_com.site()
        tab = self.browser().tab()

        res = tab.get('/en/ticketsspa', ws)
        self.status(200, res)

class ticketsspa_ticket(tester.tester):
    def __init__(self, *args, **kwargs):
        propr = carapacian_com.site().Proprietor
        super().__init__(propr=propr, *args, **kwargs)

    def it_GETs(self):
        ws = carapacian_com.site()
        tab = self.browser().tab()

        res = tab.navigate('/en/ticketsspa/ticket?crud=create', ws)
        self.status(200, res)

        frm = tab['form'].only
        inps = frm['input, textarea']
        expect = [
            'id',        'created',      'required',  'budget',
            'quantity',  'description',  'reason'
        ]
        actual = inps.pluck('name')

        self.eq(expect, actual)

    def it_creates(self):
        ws = carapacian_com.site()
        tab = self.browser().tab()

        res = tab.navigate('/en/ticketsspa/ticket?crud=create', ws)
        self.status(200, res)

        frm = tab['form'].only

        
        inps = frm['input, textarea']

        ''' Test with main fields populated '''
        id         =  frm['input[name=id]'].only
        desc       =  inps['[name=description]'].only
        created    =  inps['[name=created]'].only
        required   =  inps['[name=required]'].only
        budget     =  inps['[name=budget]'].only
        qty        =  inps['[name=quantity]'].only
        reason     =  inps['[name=reason]'].only
        btnsubmit  =  frm['button[type=submit]'].only

        id = id.value

        desc.text = self.dedent('''
            As a user,
            I would like the password field to be masked,
            So ne'er-do-well can shoulder surf my password.
        ''')

        reason.text = self.dedent('''
            This feature is necessary to for security compliance.
        ''')

        self.expect(
            db.RecordNotFoundError, lambda: effort.requirement(id)
        )

        res = self.click(btnsubmit, tab)
        self.ok(res)

        req = self.expect(
            None, lambda: effort.requirement(id)
        )

        self.eq(id, req.id.hex)

        self.eq(desc.text, req.description)

        self.eq(reason.text, req.reason)

        self.none(req.asset)
        self.none(req.product)
        self.zero(req.roles)

    def it_creates_and_updates_qs(self):
        ws = carapacian_com.site()
        tab = self.browser().tab()

        res = tab.navigate('/en/ticketsspa/ticket?crud=create', ws)
        self.status(200, res)

        frm = tab['form'].only

        inp = frm['input[name=id]'].only

        inps = frm['input, textarea']

        desc = inps['[name=description]'].only
        reason = inps['[name=reason]'].only

        desc.text = self.dedent('''
            As a user,
            I would like the password field to be masked,
            So ne'er-do-well can shoulder surf my password.
        ''')

        btnsubmit = frm['button[type=submit]'].only

        res = self.click(btnsubmit, tab)
        self.ok(res)

        art = res.html.first
        id = art.attributes['data-entity-id'].value

        self.eq(f'id={id}&crud=retrieve', tab.url.query)

        self.eq(id, tab.url.qs['id'][0])

    def it_edits(self):
        ws = carapacian_com.site()
        tab = self.browser().tab()

        req = effort.requirement()
        req.save()

        res = tab.navigate(f'/en/ticketsspa/ticket?id={req.id}', ws)
        self.status(200, res)

        btnedit = res['button.edit'].only

        btnedit.click()

if __name__ == '__main__':
    tester.cli().run()
