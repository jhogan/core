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
import www

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

        id = UUID(id.value)

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

        self.eq(id.hex, req.id.hex)

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

        self.eq(id, tab.url.qs['id'])

    def it_edits(self):
        ws = carapacian_com.site()
        tab = self.browser().tab()

        req = effort.requirement()
        req.save()

        res = tab.navigate(f'/en/ticketsspa/ticket?id={req.id}', ws)
        self.status(200, res)

        btnedit = res['button.edit'].only

        btnedit.click()

class ticketsspa_backlogs(tester.tester):
    def __init__(self, *args, **kwargs):
        # TODO Make sure we can run ticketsspa_backlogs alone
        #
        #    ./testcarapacian_com.py ticketsspa_backlogs
        # 
        # This sometimes works but, for some reason, will fail when ensuring
        # carapacian_com.site() and claim that it can't load the root
        # user even though it does exist in the database.
        propr = carapacian_com.site().Proprietor
        mods = 'effort',
        super().__init__(mods=mods, propr=propr, *args, **kwargs)

    def it_GETs(self):
        ws = carapacian_com.site()
        tab = self.browser().tab()

        import testeffort
        bls = testeffort.backlog.getvalid(10)
        bls.save()
        
        res = tab.navigate('/en/ticketsspa/backlogs', ws)
        self.status(200, res)

        cards = tab['article.card[data-entity="effort.backlog"]']

        self.ge(10, cards.count)

        for bl in bls:
            for card in cards:
                id = card.getattr('data-entity-id')
                if bl.id.hex == id:
                    break
            else:
                self.fail('backlog not found in cards collection')
                break

            # Edit
            a = card['a[rel=edit]'].only
            expect = www.url(
                '/en/ticketsspa/backlog'
                f'?id={id}&crud=update&oncomplete=/ticketsspa/backlogs'
            )
            self.eq(expect, www.url(a.href))


            tbl = card['table'].only

            self.eq('effort.backlog_story', tbl.getattr('data-entity'))

            ths = tbl['thead tr th']

            hdrs = [x.text for x in ths]

            self.in_(hdrs, 'name')
            self.in_(hdrs, 'points')
            self.in_(hdrs, 'created')

            self.one(tbl['p.empty-state'])

            # Add New 
            a = tbl['a[rel=create-form]'].only
            expect = (
                '/en/ticketsspa/story'
                '?&crud=create'
                '&oncomplete=/ticketsspa/backlogs'
                f'&backlogid={bl.id.hex}'
            )
            self.eq(expect, a.href)

    def it_gets_filter_form(self):
        ws = carapacian_com.site()
        tab = self.browser().tab()

        # Do this to make sure the backlogstatustypes records have been
        # created first. If they don't exist, the <form> will have
        # nothing to filter on since it pulls from these records to
        # create the checkboxes.
        import testeffort
        bl = testeffort.backlog.getvalid()
        assert bl.inplanning
        bl.save()
        bl.close()
        bl.save()

        # Navigate
        res = tab.navigate('/en/ticketsspa/backlogs', ws)
        self.status(200, res)

        frm = tab['form.filter']
        self.one(frm)

        flt = frm.only
        types = effort.backlogstatustypes.orm.all

        names = sorted(types.pluck('name'))

        chks = flt['input[type=checkbox]']

        names1 = sorted(chks.pluck('name'))

        self.eq(names, names1)

        for chk in chks:
            lbls = frm[f'label[for={chk.id}]']
            self.one(lbls)
            lbl = lbls.only
            self.eq(chk.name.capitalize(), lbl.text)

    def it_GETs_filtered(self):
        ws = carapacian_com.site()
        tab = self.browser().tab()

        import testeffort
        bls = testeffort.backlog.getvalid(4)

        for i, bl in bls.enumerate():
            if i.even:
                bl.close()

        bls.save()

        # Unfiltered
        res = tab.navigate('/en/ticketsspa/backlogs', ws)
        self.status(200, res)

        flt = tab['div.cards form.filter'].only

        chkinplanning = flt['[name=planning]'].only
        chkisclosed = flt['[name=closed]'].only

        self.true(chkinplanning.checked)
        self.true(chkisclosed.checked)

        cards = tab['article.card[data-entity="effort.backlog"]']

        self.ge(4, cards)

        for bl in bls:
            for card in cards:
                id = card.getattr('data-entity-id')
                if bl.id.hex == id:
                    self.true(bl.inplanning or bl.isclosed)

                    if bl.isclosed:
                        self.zero(card['button.close'])
                    elif bl.inplanning:
                        self.one(card['button.close'])
                    break
            else:
                self.fail('Cannot find backlog')


        res = tab.navigate('/en/ticketsspa/backlogs?types=planning', ws)
        self.status(200, res)

        flt = tab['div.cards form.filter'].only

        chkinplanning = flt['[name=planning]'].only
        chkisclosed = flt['[name=closed]'].only

        self.true(chkinplanning.checked)
        self.false(chkisclosed.checked)

        cards = tab['article.card[data-entity="effort.backlog"]']

        self.ge(2, cards)

        for bl in bls:
            for card in cards:
                id = card.getattr('data-entity-id')
                if bl.id.hex == id:
                    self.true(bl.inplanning)
                    self.one(card['button.close'])
                    break
            else:
                self.true(bl.isclosed)

        res = tab.navigate('/en/ticketsspa/backlogs?types=closed', ws)
        self.status(200, res)

        flt = tab['div.cards form.filter'].only

        chkinplanning = flt['[name=planning]'].only
        chkisclosed = flt['[name=closed]'].only

        self.false(chkinplanning.checked)
        self.true(chkisclosed.checked)

        cards = tab['article.card[data-entity="effort.backlog"]']

        self.ge(2, cards)

        for bl in bls:
            for card in cards:
                id = card.getattr('data-entity-id')
                if bl.id.hex == id:
                    self.true(bl.isclosed)
                    self.zero(card['button.close'])
                    break
            else:
                self.true(bl.inplanning)

    def it_filters_then_adds_and_edits(self):
        ws = carapacian_com.site()
        tab = self.browser().tab()

        import testeffort

        # Ensure that the backlog status types exist
        effort.backlogstatustype(name='closed')
        effort.backlogstatustype(name='planning')

        url = www.url('/en/ticketsspa/backlogs')

        # Navigate to unfiltered page
        res = tab.navigate(url, ws)
        self.h200(res)

        self.eq(url.path, tab.url.path)

        self.endswith('/en/ticketsspa/backlogs', str(tab.url))

        types = 'planning', 'closed', 'both', None

        def get_checkboxes():
            flt = tab['div.cards form.filter'].only
            chkinplanning = flt['[name=planning]'].only
            chkisclosed = flt['[name=closed]'].only
            return chkinplanning, chkisclosed
            
        prev = None
        for type in types:
            chkinplanning, chkisclosed = get_checkboxes()

            if type == 'planning':
                res = self.click(chkisclosed, tab)
                self.h200(res)

                chkinplanning, chkisclosed = get_checkboxes()

                self.true(chkinplanning.checked)
                self.false(chkisclosed.checked)

            elif type == 'closed':
                self.click(chkinplanning, tab)
                self.h200(res)

                chkinplanning, chkisclosed = get_checkboxes()
                self.true(chkinplanning.checked)
                self.true(chkisclosed.checked)


                self.click(chkinplanning, tab)
                self.h200(res)

                chkinplanning, chkisclosed = get_checkboxes()
                self.false(chkinplanning.checked)
                self.true(chkisclosed.checked)

            elif type == 'both':
                self.click(chkinplanning, tab)
                self.h200(res)

                chkinplanning, chkisclosed = get_checkboxes()

                self.true(chkinplanning.checked)
                self.true(chkisclosed.checked)

            elif type is None:
                self.click(chkinplanning, tab)
                self.h200(res)

                chkinplanning, chkisclosed = get_checkboxes()
                self.false(chkinplanning.checked)
                self.true(chkisclosed.checked)

                self.click(chkisclosed, tab)
                self.h200(res)

                chkinplanning, chkisclosed = get_checkboxes()
                self.true(chkinplanning.checked)
                self.true(chkisclosed.checked)
            else:
                assert False, 'Invalid type'

            ''' Create new '''
            btnadd = tab['div.cards>a[rel=create-form]'].only

            res = self.click(btnadd, tab)
            self.h200(res)

            frm = tab['form'].only

            name = uuid4().hex

            frm.setvalue('name', name)

            res = self.submit(frm, tab)
            self.h200(res)

            bl = effort.backlogs(name=name).only

            if prev:
                # Make sure the new bl doesn't match the previously
                # created one. This bug cropped up because
                # pom.crud.clear() did not delete the page's
                # data-entity-id attribute.
                self.ne(bl.id, prev.id)

            prev = bl

            spans = tab[
                'article.card [data-entity-attribute=name] span'
            ]

            for span in spans:
                if span.text == name:
                    break
            else:
                if chkinplanning.checked:
                    self.fail(f'Cannot find span for type "{type}"')

                continue

            ''' Edit the newly created '''
            btnedit = span.closest('article')['a[rel=edit]'].only
            res = self.click(btnedit, tab)
            self.h200(res)

            frm = tab['form'].only

            self.eq(bl.name, frm.getvalue('name'))

            name = uuid4().hex

            frm.setvalue('name', name)

            res = self.submit(frm, tab)
            self.h200(res)

            spans = tab['article.card [data-entity-attribute=name] span']

            for span in spans:
                if span.text == name:
                    break
            else:
                self.fail(f'Cannot find span for type {type}')

    def it_filters(self):
        ws = carapacian_com.site()
        tab = self.browser().tab()

        import testeffort
        bls = testeffort.backlog.getvalid(4)

        for i, bl in bls.enumerate():
            if i.even:
                bl.close()

        bls.save()

        # Filter by inplanning
        res = tab.navigate(
            '/en/ticketsspa/backlogs?types=planning&types=closed', ws
        )
        self.h200(res)

        flt = tab['div.cards form.filter'].only

        chkinplanning = flt['[name=planning]'].only
        chkisclosed = flt['[name=closed]'].only

        self.true(chkinplanning.checked)
        self.true(chkisclosed.checked)

        # Filter by inplanning
        res = tab.navigate('/en/ticketsspa/backlogs?types=planning', ws)
        self.h200(res)

        flt = tab['div.cards form.filter'].only

        chkinplanning = flt['[name=planning]'].only
        chkisclosed = flt['[name=closed]'].only

        self.true(chkinplanning.checked)
        self.false(chkisclosed.checked)

        # Filter by none (which is also both)
        res = tab.navigate('/en/ticketsspa/backlogs', ws)
        self.h200(res)

        self.expect(KeyError, lambda: tab.url.qs['types'])

        flt = tab['div.cards form.filter'].only

        chkinplanning = flt['[name=planning]'].only
        chkisclosed = flt['[name=closed]'].only

        self.true(chkinplanning.checked)
        self.true(chkisclosed.checked)

        # Unclick chkinplanning
        res = self.click(chkinplanning, tab)
        self.h200(res)

        self.eq('closed', tab.url.qs('types'))

        cards = tab['article.card[data-entity="effort.backlog"]']

        self.ge(2, cards)

        for card in cards:
            id = card.getattr('data-entity-id')
            bl = effort.backlog(id)
            self.false(bl.inplanning)
            self.true(bl.isclosed)

        # Filter by both inplanning and isclosed
        flt = tab['div.cards form.filter'].only

        chkinplanning = flt['[name=planning]'].only
        chkisclosed = flt['[name=closed]'].only

        self.false(chkinplanning.checked)
        self.true(chkisclosed.checked)

        res = self.click(chkisclosed, tab)
        self.h200(res)

        self.none(tab.url.qs('types'))

        cards = tab['article.card[data-entity="effort.backlog"]']

        self.ge(4, cards)

        flts = [False] * 2
        for card in cards:
            id = card.getattr('data-entity-id')
            bl = effort.backlog(id)
            if bl.inplanning:
                flts[0] = True
            elif bl.isclosed:
                flts[1] = True

        self.eq([True] * 2, flts)

        # Filter by only isclosed
        flt = tab['div.cards form.filter'].only

        chkinplanning = flt['[name=planning]'].only
        chkisclosed = flt['[name=closed]'].only

        self.true(chkinplanning.checked)
        self.true(chkisclosed.checked)

        res = self.click(chkinplanning, tab)
        self.h200(res)

        self.eq('closed', tab.url.qs('types'))

        cards = tab['article.card[data-entity="effort.backlog"]']

        self.ge(2, cards)

        for card in cards:
            id = card.getattr('data-entity-id')
            bl = effort.backlog(id)
            self.true(bl.isclosed)
            self.false(bl.inplanning)

        # Uncheck both filters. Paradoxically, this should have the same
        # affect as selecting both.
        flt = tab['div.cards form.filter'].only

        chkinplanning = flt['[name=planning]'].only
        chkisclosed = flt['[name=closed]'].only

        self.false(chkinplanning.checked)
        self.true(chkisclosed.checked)

        # Unselect is closed
        res = self.click(chkisclosed, tab)
        self.h200(res)

        self.none(tab.url.qs('types'))

        cards = tab['article.card[data-entity="effort.backlog"]']

        self.ge(4, cards)

        flts = [False] * 2
        for card in cards:
            id = card.getattr('data-entity-id')
            bl = effort.backlog(id)
            if bl.inplanning:
                flts[0] = True
            elif bl.isclosed:
                flts[1] = True

        self.eq([True] * 2, flts)

    def it_closes_backlog(self):
        ws = carapacian_com.site()
        tab = self.browser().tab()

        import testeffort

        # Ensure that the backlog status types exist
        effort.backlogstatustype(name='closed')
        effort.backlogstatustype(name='planning')

        N = 3
        bls = testeffort.backlog.getvalid(N)
        bls.save()

        flts = (
            str(),
            'types=planning',
        )
        
        for i, flt in enumerate(flts):
            res = tab.navigate(f'/en/ticketsspa/backlogs?{flt}', ws)
            self.status(200, res)

            cards = tab['article.card[data-entity="effort.backlog"]']

            # Get a backlog from the ones we created above
            for bl in bls:
                if bl.orm.reloaded().inplanning:
                    break
            else:
                assert 'Cannot find open backlog'

            # Get it's corresponding card
            card = cards[f'[data-entity-id="{bl.id.hex}"]'].only

            # Get Close button
            btnclose = card['button.close'].only

            # Click the "Close" button
            res = self.click(btnclose, tab)
            self.h200(res)

            # Get the card again
            cards = tab[f'[data-entity-id="{bl.id.hex}"]']

            card = cards.only

            # Get the <dialog> confirmation modal
            dia = tab['dialog'].only
            self.true(dia.open)

            btnno = dia['button[data-no]'].only

            res = self.click(btnno, tab)
            self.h200(res)

            # Make sure the card still exists
            self.one(tab[f'[data-entity-id="{bl.id.hex}"]'])

            # The <dialog> box should have been removed
            self.zero(tab['dialog'])

            # The backlog should not be closed
            self.false(bl.orm.reloaded().isclosed)

            # Click the "Close" button
            btnclose = card['button.close'].only

            res = self.click(btnclose, tab)
            self.h200(res)

            # Get the <dialog> confirmation modal
            dia = tab['dialog'].only
            self.true(dia.open)

            # Confirm the closure of the backlog
            btnyes = dia['button[data-yes]'].only
            res = self.click(btnyes, tab)
            self.h200(res)

            # Get the card again
            cards = tab[f'[data-entity-id="{bl.id.hex}"]']

            if flt in ('types=closed', str()):
                # The card should still be displayed because we are
                # filtering on closed or we are not filtering on types.
                self.one(cards)

                card = cards.only

                # Get Close button
                btns = card['button.close']

                # The Close button should have been removed
                self.zero(btns)

            elif flt == 'types=planned':
                # We are filtering out closed backlogs so we should no
                # see the card
                self.zero(cards)

            # The backlog should be closed now
            self.true(bl.orm.reloaded().isclosed)

            # The <dialog> box should have been removed
            self.zero(tab['dialog'])

    def it_navigates_to_story(self):
        ws = carapacian_com.site()
        tab = self.browser().tab()

        import testeffort
        bls = testeffort.backlog.getvalid(3)
        bls.save()
        
        # Load the backlogs page
        res = tab.navigate('/en/ticketsspa/backlogs', ws)

        cards = tab['article.card[data-entity="effort.backlog"]']
        card = cards.getrandom()
        tbl = card['table[data-entity="effort.backlog_story"]'].only

        a = tbl['a[rel=create-form]'].only

        # Click on [Add New] (story)
        res = self.click(a, tab)
        self.h200(res)

        main = tab['main'].only
        self.eq('/ticketsspa/story', main.getattr('data-path'))

        # Get the form to create a new story
        frm = main['form'].only

        inp = frm['[data-entity-attribute=name] input'].only

        name = uuid4().hex
        inp.value = name

        # Submit the form
        res = self.submit(frm, tab)
        self.h200(res)

        main = tab['main'].only

        # We should be back at the backlogs page because of the
        # oncomplete
        self.eq('/ticketsspa/backlogs', main.getattr('data-path'))

        id = card.getattr('data-entity-id')

        # Get the backlog card from the new page that batches the
        # original backlog card's id
        card = main[f'.card[data-entity-id="{id}"]'].only

        tbl = card['table'].only
        trs = tbl['tr[data-entity="effort.backlog_story"]']

        # Search the <table> in the new backlog card for a value span
        # that contains the randomly generated `name` from above. This
        # will prove that the story was added to the backlog.
        spans = trs['td span.value']
        for span in spans:
            td = span.closest('td')

            if td.getattr('data-entity-attribute') != 'name':
                continue

            if span.text == name:
                break
        else:
            self.fail('Cannot find story')

if __name__ == '__main__':
    tester.cli().run()
