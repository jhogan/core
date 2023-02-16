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
import carapacian_com
import db
import effort
import orm
import party
import pom
import primative
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

    def it_call_name(self):
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

    def it_call_name(self):
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
    def it_call_name(self):
        # XXX Shouldn't this me carapacian_com.ticketsspa
        pg = carapacian_com.tickets()
        self.eq('tickets', pg.name)

    def it_GETs(self):
        ws = carapacian_com.site()
        tab = self.browser().tab()

        res = tab.get('/en/ticketsspa', ws)
        self.status(200, res)

class ticketsspa_new(tester.tester):
    def it_call__init__(self):
        pg = carapacian_com.ticketsspa.new()

        inps = pg['form textarea[name=description]']
        self.one(inps)

        # XXX:aa98969e Continue testing the various inputs

    def it_GETs(self):
        ws = carapacian_com.site()
        tab = self.browser().tab()

        res = tab.navigate('/en/ticketsspa/new', ws)
        self.status(200, res)

        frms = tab['form']
        self.one(frms)

        inps = tab['form textarea[name=description]']
        self.one(inps)

        # XXX:aa98969e Continue testing the various inputs

    def it_creates(self):
        ws = carapacian_com.site()
        tab = self.browser().tab()

        res = tab.navigate('/en/ticketsspa/new', ws)
        self.status(200, res)

        frm = tab['form'].only

        inp = frm['input[name=id]'].only

        id = inp.value
        
        inps = frm['input, textarea']

        desc = inps['[name=description]'].only
        reason = inps['[name=reason]'].only

        desc.text = self.dedent('''
            As a user,
            I would like the password field to be masked,
            So ne'er-do-well can shoulder surf my password.
        ''')

        reason.text = self.dedent('''
            This feature is necessary to for security compliance.
        ''')

        btnsubmit = frm['button[type=submit]'].only

        self.expect(
            db.RecordNotFoundError, lambda: effort.requirement(id)
        )

        # XXX We need to find a way to get the results of a button
        # click. We need to be able to do stuff like this:
        #
        #     res = btnsubmit.click()
        #     self.ok(res)
        #     
       
        btnsubmit.click()

        req = self.expect(
            None, lambda: effort.requirement(id)
        )

        self.eq(id, req.id.hex)

        # XXX This breaks
        #self.eq(desc.text, req.description)

        self.eq(reason.text, req.reason)

        self.none(req.asset)
        self.none(req.product)
        self.zero(req.roles)

    def it_creates_and_updates_qs(self):
        ws = carapacian_com.site()
        tab = self.browser().tab()

        res = tab.navigate('/en/ticketsspa/new', ws)
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

        with tab.capture() as msgs:
            btnsubmit.click()
            self.ok(msgs.last.response)

        B()
        qs = tab.url.qs

        self.one(qs)

        inp = frm['input[name=id]'].only
        id = inp.value

        self.eq(id, tab.url.qs['id'])


if __name__ == '__main__':
    tester.cli().run()
