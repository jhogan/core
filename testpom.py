#!/usr/bin/python3
# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2022
import apriori; apriori.model()

from base64 import b64decode
from contextlib import suppress
from datetime import timezone, datetime, date
from dbg import B
from entities import classproperty
from func import enumerate, getattr
from pprint import pprint
from uuid import uuid4, UUID
import asset
import auth
import dom
import ecommerce
import file
import logs
import mimetypes
import orm
import os
import party
import pom
import primative
import pytz
import tester
import www

# TODO We should get datetime and date from `primative`

class persons(orm.entities):
    pass

class person(orm.entity):
    name = str
    born = date
    bio  = orm.text

    @classmethod
    def getvalid(cls):
        e = cls()
        e.name = 'Jesse'
        e.born = '1976-04-15'
        e.bio = (
            "Hello. I'm a professional programmer"
        )
        return e

    @property
    def creatability(self):
        return orm.violations.empty

    @property
    def retrievability(self):
        return orm.violations.empty

    @property
    def updatability(self):
        return orm.violations.empty

class foonets(pom.sites):
    pass

class foonet(pom.site):
    Id = UUID(hex='68c92541-0940-4a70-8e94-55c6c58a45cc')

    Proprietor = party.company(
        id = UUID(hex='f00E37b406c4424ea351f8baf1f3500e'),
        name = 'Foonet, Inc'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.host = 'foo.net'

        # Assign the site's name (as an asset)
        self.name = 'foo.net'

        ''' Pages '''
        self.pages += home()
        self.pages += profile()
        self.pages += profiles()
        self.pages += about()
        self.pages += contact_us()
        self.pages += blogs()
        self.pages += admin()
        self.pages += spa()

        ''' Error pages '''
        pgs = self.pages['error'].pages
        pgs += _404()

        # TODO This init logic probably should mostly put in overridden
        # properties:
        #
        #   foonet.lang
        #   foonet.charset
        #   foonet.stylesheets
        #   foonet.header
        #   foonet.footer

        ''' Metadata '''
        self.lang = 'es'
        self.charset = 'iso-8859-1'
        self.stylesheets.append(
            'https://maxcdn.bootstrapcdn.com/'
                'bootstrap/4.0.0/css/bootstrap.min.css'
        )

        ''' Header '''
        self.header.logo = pom.logo('FooNet')

        ''' Header Menus '''
        mnus = self.header.menus
        mnu = self._adminmenu
        mnus += mnu

        ''' Sidebar and sidebar menu '''
        mnus = pom.menus()
        mnu = pom.menu('left-sidebar-nav')
        mnus += mnu

        mnu.items += pom.menu.item('Main page', '/')

        sb = pom.sidebar('left')
        self.sidebars += sb
        sb += mnus

    @classproperty
    def languages(cls):
        ''' A list of accepted languages by this site.
        '''
        # Always accept English
        return ['en', 'es']

    @property
    def _adminmenu(self):
        mnu = pom.menu('admin')
        mnu.items += pom.menu.item('Users')

        mnu.items.last.items \
            += pom.menu.item(self['admin/users/statistics'])

        mnu.items += pom.menu.item('Reports')

        rpt = mnu.items.last

        pg = self['admin/reports/netsales']

        rpt.items += pom.menu.item(pg)

        rpt.seperate()

        pg = self['admin/reports/accountsummary']
        rpt.items += pom.menu.item(pg)

        return mnu

    @property
    def favicon(self):
        r = file.file()
        r.name = 'favicon.ico'
        r.body = b64decode(Favicon)
        return r

class menus(tester.tester):
    def __init__(self, *args, **kwargs):
        mods = 'party', 
        super().__init__(mods=mods, *args, **kwargs)

    def it_calls_html(self):
        mnus = pom.menus()

        mnu = pom.menu(name='admin')
        mnu1 = pom.menu(name='sub')

        mnus += mnu, mnu1

        html = (
            '<section><nav aria-label="Admin"><ul></ul></nav>'
            '<nav aria-label="Sub"><ul></ul></nav></section>'
        )

        self.eq(html, mnus.html)

        ''' With items '''
        mnu.items += pom.menu.item('Users')
        mnu.items += pom.menu.item('Groups')

        html = (
            '<section><nav aria-label="Admin">'
            '<ul><li>Users</li><li>Groups</li></ul>'
            '</nav><nav aria-label="Sub">'
            '<ul></ul></nav></section>'
        )

        self.eq(html, mnus.html)

        ''' With nested items '''
        users = mnu.items.elements.first

        users.items += pom.menu.item('Add')
        users.items += pom.menu.item('Search')

        html = (
            '<section><nav aria-label="Admin">'
            '<ul><li>Users<ul><li>Add</li><li>Search</li></ul>'
            '</li><li>Groups</li></ul></nav>'
            '<nav aria-label="Sub"><ul></ul></nav></section>'
        )
        self.eq(html, mnus.html)

    def it_calls__repr__(self):
        mnus = pom.menus()

        self.eq('menus()', repr(mnus))

        ''' With menus '''
        mnu = pom.menu(name='admin')
        mnu1 = pom.menu(name='sub')

        mnus += mnu, mnu1

        expect = (
            'menus(menu(aria-label="Admin"), menu(aria-label="Sub"))'
        )
        self.eq(expect, repr(mnus))

    def it_is_a_subtype_of_section(self):
        mnus = pom.menus()
        self.isinstance(mnus, dom.section)

class menu(tester.tester):
    def it_calls_name(self):
        mnu = pom.menu(name='admin')
        self.eq('admin', mnu.name)

    def it_calls_html(self):
        mnu = pom.menu(name='admin')

        # See the NOTE:23db3900 to understand by we have an empty <ul>
        # here.
        html = '<nav aria-label="Admin"><ul></ul></nav>'
        self.eq(html, mnu.html)

        ''' With items '''
        mnu.items += pom.menu.item('File')
        mnu.items += pom.menu.item('Edit')

        html = (
            '<nav aria-label="Admin"><ul>'
            '<li>File</li><li>Edit</li></ul></nav>'
        )
        self.eq(html, mnu.html)

        ''' With nested items '''
        file = mnu.items.elements.first

        file.items += pom.menu.item('Open')
        file.items += pom.menu.item('Save')

        html = (
            '<nav aria-label="Admin"><ul>'
            '<li>File<ul>'
            '<li>Open</li>'
            '<li>Save</li></ul></li>'
            '<li>Edit</li>'
            '</ul></nav>'
        )
        self.eq(html, mnu.html)

    def it_calls__repr__(self):
        mnu = pom.menu(name='admin')
        self.eq('menu(aria-label="Admin")', repr(mnu))

    def it_calls__str__(self):
        mnu = pom.menu(name='admin')

        expect = self.dedent('''
        <nav aria-label="Admin">
          <ul>
          </ul>
        </nav>
        ''')
        self.eq(expect, str(mnu))

        ''' With items '''
        mnu.items += pom.menu.item('File')
        mnu.items += pom.menu.item('Edit')

        expect = self.dedent('''
        <nav aria-label="Admin">
          <ul>
            <li>
              File
            </li>
            <li>
              Edit
            </li>
          </ul>
        </nav>
        ''')
        self.eq(expect, str(mnu))

        ''' With nested items '''
        file = mnu.items.elements.first

        file.items += pom.menu.item('Open')
        file.items += pom.menu.item('Save')

        expect = self.dedent('''
        <nav aria-label="Admin">
          <ul>
            <li>
              File
              <ul>
                <li>
                  Open
                </li>
                <li>
                  Save
                </li>
              </ul>
            </li>
            <li>
              Edit
            </li>
          </ul>
        </nav>
        ''')
        self.eq(expect, str(mnu))

    def it_is_a_subtype_of_nav(self):
        self.isinstance(pom.menu('name'), dom.nav)

class menu_items(tester.tester):
    def __init__(self, *args, **kwargs):
        mods = (
            'party', 'asset', 'apriori', '__main__', 
            'testpom', 'pom', 'file'
        )
        super().__init__(mods=mods, *args, **kwargs)

        propr = foonet.Proprietor
        with orm.sudo(), orm.proprietor(propr):
            propr.owner = ecommerce.users.root
            
        orm.security().proprietor = foonet.Proprietor

        # Unconditionally recreate foonet's tables and supers
        foonet.orm.recreate(ascend=True)

    def it_isinstance_of_ul(self):
        itms = pom.menu.items()
        self.isinstance(itms, dom.ul)

    def it_preserves_serialized_representation(self):
        """ It was noticed that subsequent calls to menu.pretty,
        mnu.items.pretty, etc. were returning the same HTML but with
        different id's. This was because of the menus and their items
        were being cloned. Since the objects were being reinstantiated
        during cloning, the original id was lost only to be replaced by
        the new id of the new object. Some work was done to ensure that
        the ids are preserved.
        """
        ws = foonet()
        main = ws.header.makemain()

        self.eq(main.pretty,        main.pretty)
        self.eq(main.html,          main.html)
        self.eq(main.items.pretty,  main.items.pretty)
        self.eq(main.items.html,    main.items.html)

    def it_calls_append(self):
        itms = pom.menu.items()
        itms += pom.menu.item('A text item')
        itms += pom.menu.item('Another text item')

        expect = self.dedent('''
        <ul>
          <li>
            A text item
          </li>
          <li>
            Another text item
          </li>
        </ul>
        ''')

        self.eq(expect, itms.pretty)
        self.eq(expect, str(itms))

        expect = self.dedent('''
        <ul><li>A text item</li><li>Another text item</li></ul>
        ''')

        self.eq(expect, itms.html)

    def it_calls_append_on_nested_items(self):
        itms = pom.menu.items()
        itms += pom.menu.item('A')
        itms += pom.menu.item('B')

        els = itms.elements
        els.first.items += pom.menu.item('A/A')
        els.first.items += pom.menu.item('A/B')

        els.second.items += pom.menu.item('B/A')
        els.second.items += pom.menu.item('B/B')

        expect = self.dedent('''
        <ul>
          <li>
            A
            <ul>
              <li>
                A/A
              </li>
              <li>
                A/B
              </li>
            </ul>
          </li>
          <li>
            B
            <ul>
              <li>
                B/A
              </li>
              <li>
                B/B
              </li>
            </ul>
          </li>
        </ul>
        ''')

        self.eq(expect, itms.pretty)
        self.eq(expect, str(itms))

        expect = (
            '<ul><li>A<ul><li>A/A</li>'
            '<li>A/B</li></ul></li><li>B<ul>'
            '<li>B/A</li><li>B/B</li></ul></li></ul>'
        )
        self.eq(expect, itms.html)

class menu_item(tester.tester):
    def it_calls__init__(self):
        itm = pom.menu.item('A text item')
        expect = self.dedent('''
        <li>
          A text item
        </li>
        ''')
        self.eq(expect, itm.pretty)
        self.eq(expect, str(itm))

        expect = '<li>A text item</li>'
        self.eq(expect, itm.html)

    def it_calls_html(self):
        ''' Add a text item '''
        li = pom.menu.item('A menu item')
        html = '<li>A menu item</li>'
        self.eq(html, li.html)

        html = self.dedent('''
        <li>
          A menu item
        </li>
        ''')

        self.eq(html, li.pretty)

        ''' Add an anchor item '''
        li = pom.menu.item(o='A menu item', href='https://example.com')
        html = '<li><a href="https://example.com">A menu item</a></li>'
        self.eq(html, li.html)

        html = self.dedent('''
        <li>
          <a href="https://example.com">
            A menu item
          </a>
        </li>
        ''')

        self.eq(html, li.pretty)

        ''' Add an page item '''
        ws = foonet()
        pg = ws.pages.first

        li = pom.menu.item(o=pg)
        html = '<li><a href="/error">Error</a></li>'
        self.eq(html, li.html)

        html = self.dedent('''
        <li>
          <a href="/error">
            Error
          </a>
        </li>
        ''')
        self.eq(html, li.pretty)

    def it_calls_repr(self):
        ''' Add a text item '''
        li = pom.menu.item('A menu item')
        expect = "menu.item('A menu item')"
        self.eq(expect, repr(li))

        ''' Add an anchor item '''
        li = pom.menu.item(o='A menu item', href='https://example.com')
        expect = "menu.item('A menu item', href='https://example.com')"
        self.eq(expect, repr(li))

        ''' Add an page item '''
        ws = foonet()
        pg = ws.pages.first
        li = pom.menu.item(o=pg)
        expect = "menu.item('error', page='/error')"
        self.eq(expect, repr(li))

class _404(pom.page):
    def main(self, ex: www.NotFoundError):
        self.title = 'Page Not Found'
        self.main += dom.h1('Page Not Found')
        self.main += dom.h2('Foobar apologizes', class_="apology")

        self.main += dom.p(
            'Could not find <span class="resource">' +
            str(ex.resource) +
            '</span>'
        )

    @property
    def name(self):
        return type(self).__name__.replace('_', '')

class site(tester.tester):
    def __init__(self, *args, **kwargs):
        mods = 'party', 'apriori', 'file', 'asset'
        super().__init__(mods=mods, *args, **kwargs)

        orm.security().override = True

    def it_gets_public(self):
        ws = foonet()
        with orm.proprietor(ws.proprietor):
            pub = ws.public

        self.eq('public', pub.name)
        self.false(pub.orm.isnew)
        self.false(pub.orm.isdirty)
        self.false(pub.orm.ismarkedfordeletion)

        self.is_(ws.directory, pub.inode)
        self.is_(pub, ws.public)

    def it_calls__init__(self):
        ws = foonet()
        self.nine(ws.pages)

    def it_calls__repr__(self):
        self.eq('site()', repr(pom.site()))
        self.eq('site()', str(pom.site()))

        self.eq('foonet()', repr(foonet()))
        self.eq('foonet()', str(foonet()))
        
    def it_calls__getitem__(self):
        ws = foonet()
        for path in ('/', '', 'index'):
            self.type(home, ws[path])

        self.type(about, ws['/about'])
        self.type(about_team, ws['/about/team'])

    def it_raise_on_invalid_path(self):
        ws = foonet()
        self.expect(IndexError, lambda: ws['/en/index/about/teamxxx'])
        self.expect(IndexError, lambda: ws['/en/xxx'])
        self.expect(IndexError, lambda: ws['/en/derp'])

        self.expect(IndexError, lambda: ws[dom.p()])

    def it_calls_html(self):
        ws = pom.site()
        self.type(dom.html, ws.html)
        self.eq('en', ws.html.lang)

        ws = foonet()
        self.type(dom.html, ws.html)
        self.eq('es', ws.html.lang)

    def it_calls_head(self):
        ''' Foonet's head '''
        vp = 'width=device-width, initial-scale=1, shrink-to-fit=no'

        ws = foonet()

        with orm.proprietor(ws.proprietor):
            hd = ws.head
            self.one(hd.children['meta[charset=iso-8859-1]'])
            self.one(hd.children['meta[name=viewport][content="%s"]' % vp])

            titles = hd.children['title']
            self.one(titles)
            self.eq('foonet', titles.first.text)

            # Mutate ws properties to ensure they show up in .head 
            charset = uuid4().hex
            vp = uuid4().hex
            title = uuid4().hex

            ws.charset = charset
            ws.viewport = vp
            ws.title = title

            hd = ws.head
            self.one(hd.children['meta[charset="%s"]' % charset])
            self.one(hd.children['meta[name=viewport][content="%s"]' % vp])

            titles = hd.children['title']
            self.one(titles)
            self.eq(title, titles.first.text)

            ws = pom.site()
            hd = ws.head
            self.one(hd.children['meta[charset=utf-8]'])

            titles = hd.children['title']
            self.one(titles)
            self.eq('site', titles.first.text)

    def it_calls_header(self):
        ws = foonet()
        hdr = ws.header
        self.type(pom.header, hdr)

    def it_calls_admin_menu(self):
        ws = foonet()

        mnus = ws.header.menus
        mnu = mnus['[aria-label=Admin]'].only
        self.two(mnu.items.elements)

        rpt = mnu.items.second
        self.type(pom.menu.item, rpt.items.first)
        self.type(pom.menu.separator, rpt.items.second)
        self.type(pom.menu.item, rpt.items.third)

    def it_menu_has_aria_attributes(self):
        ws = foonet()

        ws.header.makemain()
        navs = ws.header['nav']
        self.two(navs)

        self.one(navs['[aria-label=Admin]'])
        self.one(navs['[aria-label=Main]'])

    def it_calls_main_menu(self):
        ws = pom.site()
        mnu = ws.header.makemain()
        self.zero(mnu.items.elements)

        ws = foonet()
        mnu = ws.header.makemain()

        self.eight(mnu.items.elements)

        self.eq(
            [
                '/index', '/profile', '/profiles', '/about', 
                '/contact-us', '/blogs', '/admin', '/spa'
            ],
            mnu.items.pluck('page.path')
        )

        self.eq(
            [
                home,        profile,  profiles,  about,
                contact_us,  blogs,    admin,     spa
            ],
            [type(x) for x in  mnu.items.pluck('page')]
        )

        blg = mnu.items.antepenultimate
        self.eq(
            ['/blogs/categories', '/blogs/posts', '/blogs/comments'],
            blg.items.pluck('page.path')
        )

        self.eq(
            [blog_categories, blog_posts, blog_comments],
            [
                type(x) 
                for x in blg.items.pluck('page')
            ]
        )

        self.eq(
            ['/blogs/comments/approved', '/blogs/comments/rejected'],
            blg.items.last.items.pluck('page.path')
        )

        self.eq(
            [blog_approved_comments, blog_rejected_comments],
            [type(x) for x in blg.items.last.items.pluck('page')]
        )

        for _ in range(2): # Ensure indempotence
            # The header's html will contain two <nav>s: one for the
            # main and one for the admin
            self.two(dom.html(ws.header.html)['nav'])
            self.two(ws.header['nav'])

            # ... and one <ul>'s under the <nav>
            self.two(dom.html(ws.header.html)['nav>ul'])
            self.two(ws.header['nav>ul'])

        # Removing a menu removes a <nav> from the header's html.
        ws.header.menus.pop()
        self.one(dom.html(ws.header.html)['nav'])
        self.one(ws.header['nav'])

    def it_mutates_main_menu(self):
        ws = foonet()
        mnu = ws.header.makemain()
        self.eight(mnu.items.elements)

        # Blogs item
        itm = mnu.items.sixth

        ''' It updates a menu item '''
        sels = dom.selectors('li > a[href="%s"]' % '/blogs/categories')
        self.one(ws.header[sels])
        self.one(mnu[sels])

        # Get /blogs/categories
        blgcat = itm.items.first

        class tags(pom.page):
            pass

        blgcat.page = tags()

        sels = dom.selectors('li > a[href="%s"]' % blgcat.page.path)
        self.one(ws.header[sels])
        self.one(mnu[sels])

        sels = dom.selectors('li > a[href="%s"]' % '/blogs/categories')
        self.zero(ws.header[sels])
        self.zero(mnu[sels])

        ''' It adds a menu item '''
        mnu.items += pom.menu.item('My Profile')

        self.nine(mnu.items.elements)

        sels = dom.selectors('li')

        self.true('My Profile' in (x.text for x in mnu[sels]))
        self.true('My Profile' in (x.text for x in ws.header.menu[sels]))

        ''' Delete the blogs munu '''
        sels = dom.selectors('li > a[href="%s"]' % itm.page.path)
        self.one(ws.header[sels])
        self.one(mnu[sels])

        # Remove the blog menu

        itms = mnu.items.remove(mnu.items.sixth)
        self.one(itms)
        self.type(pom.menu.item, itms.first)
        self.eq('blogs', itms.first.text)

        sels = dom.selectors('li > a[href="%s"]' % itm.page.path)
        self.zero(ws.header[sels])
        self.zero(mnu[sels])

    def it_assigns_principles(self):
        # Get root user
        root = ecommerce.users.root
        ws = foonet()

        def test_principles(ws):
            """ Test the id's of ws's proprietor and owner
            """
            self.eq(ws.Proprietor.id, ws.proprietor.id)

            # Assert the owner of the website is root
            # FIXME Calling ws.owner.id dosen't work here the second
            # time test_principles (after ws has been reloaded) because
            # the owner is root, and root can't be reloaded for some
            # reason.
            self.eq(root.id, ws.owner__userid)

            self.eq(ws.Proprietor.id, ws.proprietor.proprietor__partyid)
            self.eq(root.id, ws.proprietor.owner__userid)

        test_principles(ws)

        # Save website as root
        with orm.proprietor(ws.proprietor), orm.sudo():
            ws.save()

            ws = ws.orm.reloaded()
            test_principles(ws)

        aps = ws.asset_parties
        self.populated(aps)
        aps = aps.where(
            lambda x: x.asset_partystatustype.name == 'proprietor'
        )
        self.one(aps)

    def it_demands_constants_are_setup_on_site(self):
        try:
            class squatnets(pom.sites):
                pass

            class squatnet(pom.site):
                pass

            # No Id constant
            self.expect(AttributeError, squatnet)

            class squatnet(pom.site):
                Id = 'not-a-uuid-type-literal'

            self.expect(TypeError, squatnet)

            class squatnet(pom.site):
                Id = UUID(hex='a74f6395-4d91-450f-922d-8e897e1a26f8')

            # No Proprietor
            self.expect(AttributeError, squatnet)

            class squatnet(pom.site):
                Id = UUID(hex='a74f6395-4d91-450f-922d-8e897e1a26f8')
                Proprietor = object()

            self.expect(TypeError, squatnet)

            class squatnet(pom.site):
                Id = UUID(hex='a74f6395-4d91-450f-922d-8e897e1a26f8')
                Proprietor = party.party()

            self.expect(ValueError, squatnet)

        finally:
            # Forget squatnet. It can cause problems for code that looks
            # for subclasses of site since we don't bother creating a
            # table for it.
            orm.forget(squatnet)

    def it_ensures(self):
        ''' Setup '''

        # Truncate relevent tables
        es = (
            party.party,                  party.organization,
            party.legalorganization,      party.company,
            party.asset_partystatustype,  party.asset_party,
            asset.asset,                  pom.site,
            foonet,
        )
        for e in es:
            e.orm.truncate()

        ws = foonet()

        # Test foonet site
        self.eq(ecommerce.users.RootUserId, ws.owner.id)
        self.eq(foonet.Proprietor.id, ws.proprietor.id)

        self.eq((False, False, False), ws.orm.persistencestate)

        ''' Test the site's main directory '''
        with orm.proprietor(ws.proprietor):
            ws.orm.reloaded()
            self.expect(None, ws.orm.reloaded)

            dir = ws.directory
            self.expect(None, dir.orm.reloaded)
            self.eq(ws.id.hex, dir.name)
            self.eq(
                f'{file.directory.radix.path}/pom/site/{ws.id.hex}',
                dir.path
            )

            self.eq((False, False, False), dir.orm.persistencestate);

        # Test the parent directory site/
        site = dir.inode
        self.eq('site', site.name)
        self.eq((False, False, False), site.orm.persistencestate)
        self.eq(party.parties.PublicId, site.proprietor.id)
        self.eq(ecommerce.users.RootUserId, site.owner.id)

        ''' Test the association between site and its proprietor '''
        aps = ws.asset_parties
        self.populated(aps)
        aps = aps.where(
            lambda x: x.asset_partystatustype.name == 'proprietor'
        )
        self.one(aps)

        ''' Test foonet's super: `site` '''
        ws1 = ws
        ws = ws.orm.super

        self.type(pom.site, ws)
        self.eq(ecommerce.users.RootUserId, ws.owner.id)
        self.eq(foonet.Proprietor.id, ws.proprietor.id)

        self.eq((False, False, False), ws.orm.persistencestate)
        with orm.proprietor(ws.proprietor):
            self.expect(None, ws.orm.reloaded)

        # Test site's super: `asset`
        ass = ws.orm.super

        self.type(asset.asset, ass)
        self.eq(ecommerce.users.RootUserId, ass.owner.id)
        self.eq(foonet.Proprietor.id, ass.proprietor.id)

        self.eq((False, False, False), ass.orm.persistencestate)
        with orm.proprietor(ass.proprietor):
            self.expect(None, ass.orm.reloaded)

class page(tester.tester):
    def __init__(self, *args, **kwargs):
        # We will be testing with foonet so set it as the ORM's
        # proprietor
        propr = foonet.Proprietor
        with orm.sudo(), orm.proprietor(propr):
            # Assign the proprietor's owner. We need to manually ascend
            # due to TODO:6b455db7
            sup = propr
            while sup:
                sup.owner = ecommerce.users.root
                sup = sup.orm._super

        # Now we can call the constructor
        mods = (
            'party', 'ecommerce', 'pom', 
            'asset', 'apriori', 'file',
        )
        super().__init__(mods=mods, propr=propr, *args, **kwargs)

        if self.rebuildtables:
            fastnets.orm.recreate()

        orm.security().override = True
        
    def it_calls__init__(self):
        name = uuid4().hex
        pg = pom.page()
        self.zero(pg.pages)

    def it_implements_main(self):
        class stats(pom.page):
            def main(self):
                m = self.main
                m += dom.h2('Statistics')
                m += dom.p('''
                    These are the company's sales statistics:
                ''')
                self._main_snapshot = dom.html(m.html)
                self._html_snapshot = dom.html(self.html)

        pg = stats()

        self.eq('Stats', pg.title)
        self.eq('Stats', pg['html>head>title'].text)

        # Upon instantiation, the page's `main` attribute will be
        # replace with a dom.main object. A reference to the  `main`
        # method with be held in a private variable.
        self.type(dom.main, pg.main)

        # Invoking `elements` forces main to be called
        pg.elements

        # Snapshop of main tag should only include a few elements
        self.five(pg._main_snapshot.all)

        # The snapshop of the page's html will be a full document (i.e.,
        # it starts with <html>). However, since the page object hasn't
        # been attached to a site object (it will be below), the site
        # specific HTML (the <head> tag and the page <header> can not be
        # included.
        self.one(pg._html_snapshot['head'])
        self.one(pg._html_snapshot['header'])
        self.one(pg._html_snapshot['html'])
        self.one(pg._html_snapshot['html>body'])
        self.one(pg._html_snapshot['html>body>main'])
        self.one(pg._html_snapshot['html>body>main>h2'])
        self.one(pg._html_snapshot['html>body>main>p'])
        
        ''' Test page after being associated to a site object '''
        pg = stats()
        ws = foonet()
        ws.pages += pg

        # Invoking `elements` forces main to be called
        pg.elements

        # Now the _html_snapshot will have a <head> and a <header>
        # derived from the site object it was associated with.
        self.five(pg._main_snapshot.all)
        self.one(pg._html_snapshot['head'])
        self.one(pg._html_snapshot['header'])
        self.one(pg._html_snapshot['html'])
        self.one(pg._html_snapshot['html>body'])
        self.one(pg._html_snapshot['html>body>main'])
        self.one(pg._html_snapshot['html>body>main>h2'])
        self.one(pg._html_snapshot['html>body>main>p'])

        # pg will have a header and a head that is cloned from ws's
        # header and head. Ensure that they are not identical.
        self.isnot(ws.header, pg.header)
        self.isnot(ws.head, pg.head)
        self.isnot(ws.header.menus, pg.header.menus)
        self.none(ws.header.menu)
        self.none(pg.header.menu)

    def it_gets_page_with_no_main_function(self):
        ws = foonet()
        tab = self.browser().tab()
        res = tab.get('/', ws)
        msg = res['main .message'].html
        self.true('Page class needs main method' in msg)

    def it_fallsback_to_domain(self):
        import carapacian_com

        req = www.request(www.application())
        req.app.environment = {'HTTP_HOST': 'carapacian.com'}
        with orm.sudo(), orm.proprietor(party.companies.carapacian):
            self.type(carapacian_com.site, req.site)

        req = www.request(www.application())
        req.app.environment = {'HTTP_HOST': 'www.carapacian.com'}

        with orm.sudo(), orm.proprietor(party.companies.carapacian):
            self.type(carapacian_com.site, req.site)

        req = www.request(www.application())
        req.app.environment = {
            'HTTP_HOST': '380753fc.www.carapacian.com'
        }
        with orm.sudo(), orm.proprietor(party.companies.carapacian):
            self.type(carapacian_com.site, req.site)

    def it_gets_page_using_X_FORWARDED_FOR(self):
        ip = None
        class realip(pom.page):
            def main(self):
                nonlocal ip
                req = www.application.current.request
                ip = req.ip.address

        ws = foonet()
        ws.pages += realip()

        tab = self.browser().tab()

        X_FORWARDED_FOR = '84.90.32.84'

        hdrs = { 
            'X_FORWARDED_FOR': X_FORWARDED_FOR,
        }

        tab.browser.ip = None

        res = tab.get('/en/realip', ws, hdrs)
        self.status(200, res)
        self.eq(X_FORWARDED_FOR, ip)

    def it_gets_webpage_with_eventjs(self):
        class eventful(pom.page):
            def main(self):
                pass

        pg = eventful()
        ws = foonet()
        ws.pages += pg

        tab = self.browser().tab()
        res = tab.get('/en/eventful', ws)
        self.status(200, res)

        script = res['#A0c3ac31e55d48a68d49ad293f4f54e31'].only

    def it_changes_lang_from_main(self):
        lang = uuid4().hex
        class stats(pom.page):
            def main(self):
                m = self.main
                m += dom.h2('Statistics')
                m += dom.p('''
                    These are the company's sales statistics:
                ''')

                self.lang = lang

        pg = stats()

        # Invoking elements invokes stats.main()
        pg.elements

        self.eq(lang, pg.lang)
        self.eq(lang, pg.attributes['lang'].value)

        ''' Test page after being associated to a site object '''
        pg = stats()
        ws = foonet()
        ws.pages += pg

        # Invoking `elements` forces main to be called
        pg.elements

        self.eq(lang, pg.lang)
        self.eq(lang, pg.attributes['lang'].value)

    def it_changes_main_menu_from_main(self):
        class stats(pom.page):
            def main(self):
                m = self.main
                m += dom.h2('Statistics')
                m += dom.p('''
                    These are the company's sales statistics:
                ''')

                self.header.makemain()

                self.header.menu.items += pom.menu.item(
                    'Statistics',
                    href='http://www.statistics.com'
                )

        pg = stats()
        ws = foonet()
        ws.pages += pg

        # Invoking elements invokes stats.main()
        pg.elements

        self.eq('Statistics', pg.header.menu.items.last.text)

        self.eq(
            'http://www.statistics.com',
            pg.header.menu.items.last.href
        )

        sels = dom.selectors(
            'nav[aria-label=Main]>ul>li>a[href="http://www.statistics.com"]'
        )

        self.one(pg[sels])

        self.eq(
            'http://www.statistics.com',
            pg.header.menu.items.last.href
        )

    def it_changes_title_from_main(self):
        id = uuid4().hex
        class stats(pom.page):
            def main(self):
                m = self.main
                nonlocal id
                m += dom.h2('Statistics')
                m += dom.p('''
                    These are the company's sales statistics:
                ''')

                self.title = id

        pg = stats()

        # Invoking elements invokes stats.main()
        pg.elements

        self.eq(id, pg.title)
        self.eq(id, pg['head>title'].text)

        ''' Test page after being associated to a site object '''
        pg = stats()
        ws = foonet()
        ws_title = ws.title
        ws.pages += pg

        # Invoking `elements` forces main to be called
        pg.elements

        self.eq(id, pg.title)
        self.eq(id, pg['html>head>title'].text)
        self.eq(ws_title, ws.title)

    def it_clones_site_objects(self):
        ws = foonet()
        pg = ws['/blogs']
        self.notnone(pg.site)

        self.none(pg.header.menu)
        self.none(ws.header.menu)

        self.isnot(pg.header,        ws.header)
        self.isnot(pg.header.menus,  ws.header.menus)
        self.isnot(pg.head,          ws.head)

    def it_calls_site(self):
        ws = foonet(name='foo.net')
        self.is_(ws, ws['/blogs'].site)
        self.is_(ws, ws['/blogs/comments'].site)
        self.is_(ws, ws['/blogs/comments/rejected'].site)

    def it_changes_sidebars_from_main(self):
        class stats(pom.page):
            def main(self):
                m = self.main
                m += dom.h2('Statistics')
                m += dom.p('''
                    These are the company's sales statistics:
                ''')

                sb = self.sidebars['left']
                mnu = sb['nav'].first
                itm = pom.menu.item('About stats')
                mnu.items += itm

        ws = foonet()

        pg = stats()
        ws.pages += pg

        # Invoke stats.main
        pg.elements

        wsmnu = ws.sidebars['left']['nav'].first
        pgmnu = pg.sidebars['left']['nav'].first

        # Make sure the site's menu was not changed
        self.eq(wsmnu.items.count + 1, pgmnu.items.count)

        self.eq('Main page', pgmnu.items.first.text)
        self.eq('About stats', pgmnu.items.second.text)

    def it_calls_page_with_arguments(self):
        # With params and kwargs
        class time(pom.page):
            def main(self, greet: bool, tz='UTC', **kwargs):
                m = self.main

                if greet is None:
                    m += dom.p('Greeting was set to None')
                    m.last.classes += 'greeting'

                if greet:
                    m += dom.p('Greetings')
                    m.last.classes += 'greeting'

                m += dom.h2('Time')
                m += dom.i('Timezone: ' + tz)

                if len(kwargs):
                    m += dom.dl()
                    dl = m.last

                    for k in sorted(kwargs.keys()):
                        v = kwargs[k]
                        dl +=  dom.dt(k)
                        dl +=  dom.dd(v)

                m += dom.time(primative.datetime.utcnow())

        ws = foonet()

        pg = time()
        ws.pages += pg

        tab = self.browser().tab()
        # Test passing in th boolean (greet), str (tz) and kwargs(a, b)
        res = tab.get('/en/time?greet=1&tz=America/Phoenix&a=1&b=2', ws)
        self.one(res['main[data-path="/time"]'])

        ps = res['p.greeting']
        self.one(ps)

        ems = res['main>i']
        self.one(ems)

        self.eq('Timezone: America/Phoenix', ems.first.text)

        dls = res['main>dl']
        self.one(dls)

        self.eq('a', dls['dt:nth-of-type(1)'].text)
        self.eq('b', dls['dt:nth-of-type(2)'].text)

        # Test passing in th boolean (greet), let the second parameter
        # defalut to UTC and but setting some kwargs(a, b)
        res = tab.get('/en/time?greet=1&a=1&b=2', ws)

        ps = res['p.greeting']
        self.one(ps)

        ems = res['main>i']
        self.one(ems)

        self.eq('Timezone: UTC', ems.first.text)

        dls = res['main>dl']
        self.one(dls)

        self.eq('a', dls['dt:nth-of-type(1)'].text)
        self.eq('b', dls['dt:nth-of-type(2)'].text)
        
        # Test passing in th boolean (greet), let the second parameter
        # defalut to UTC and zero kwargs
        res = tab.get('/en/time?greet=1', ws)

        ps = res['p.greeting']
        self.one(ps)

        ems = res['main>i']
        self.one(ems)

        self.eq('Timezone: UTC', ems.first.text)

        dls = res['main>dl']
        self.zero(dls)

        # Test passing in no arguments
        res = tab.get('/en/time', ws)

        self.eq('Greeting was set to None', res['p.greeting'].text)

        ems = res['main>i']
        self.one(ems)
        self.eq('Timezone: UTC', ems.first.text)

        dls = res['main>dl']
        self.zero(dls)

    def it_calls_page_using_HEAD_request_method(self):
        # With params and kwargs
        class time(pom.page):
            def main(self, greet: bool, tz='UTC', **kwargs):
                m = self.main

                if greet is None:
                    m += dom.p('Greeting was set to None')
                    m.last.classes += 'greeting'

                if greet:
                    m += dom.p('Greetings')
                    m.last.classes += 'greeting'

                m += dom.h2('Time')
                m += dom.i('Timezone: ' + tz)

                if len(kwargs):
                    m += dom.dl()
                    dl = m.last

                    for k in sorted(kwargs.keys()):
                        v = kwargs[k]
                        dl +=  dom.dt(k)
                        dl +=  dom.dd(v)

                m += dom.time(primative.datetime.utcnow())

        # Test passing in no arguments
        ws = foonet()
        pg = time()
        ws.pages += pg
        tab = self.browser().tab()
        res = tab.head('/en/time', ws)
        self.eq(200, res.status)
        self.empty(res.body)

        # FIXME Content-Length should be the size of the payload
        # https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods/HEAD
        content_length = res.headers['content-length']
        self.eq(0, content_length)

    def it_calls_page_coerses_datatypes(self):
        class time(pom.page):
            def main(
                self, 
                greet:  bool,
                dt:     datetime,
                i:      int,
                pdt:    primative.datetime):

                assert type(greet) is bool
                assert type(pdt) is primative.datetime
                assert type(dt) is primative.datetime
                assert type(i) is int

                self.main += dom.h2('''
                Arguments:
                ''')

                ul = dom.ul()
                ul += dom.li('Greet: ' + str(greet))
                ul += dom.li('Datetime: ' + dt.isoformat())
                ul += dom.li('Primative Datetime: ' + pdt.isoformat())
                ul += dom.li('Integer: ' + str(i))

                self.main += ul

        ws = foonet()
        pg = time()
        ws.pages += pg

        tab = self.browser().tab()
        res = tab.get(
            '/en/time?greet=1&dt=2020-02-10&pdt=2020-02-11&i=1234', 
            ws
        )

        self.eq(
            'Greet: True', 
            res['main ul>li:nth-of-type(1)'].text
        )

        self.eq(
            'Datetime: 2020-02-10T00:00:00+00:00',
            res['main ul>li:nth-of-type(2)'].text
        )

        self.eq(
            'Primative Datetime: 2020-02-11T00:00:00+00:00',
            res['main ul>li:nth-of-type(3)'].text
        )

        self.eq(
            'Integer: 1234',
            res['main ul>li:nth-of-type(4)'].text
        )

        for v in 'derp', 2, '1010':
            path \
            = '/en/time?greet=%s&dt=2020-02-10&pdt=2020-02-11&i=1234'  

            res = tab.get(path % v, ws)

            self.status(422, res)

        path = '/en/time?greet=1&dt=2020-02-10&pdt=DERP&i=1234' 
        res = tab.get(path, ws)
        self.status(422, res)

        path = '/en/time?greet=1&dt=2020-02-10&pdt=2020-02-11&i=DERP'
        res = tab.get(path, ws)
        self.status(422, res)
        self.one(res['main[data-path="/error"]'])

    def it_calls_page_and_uses_request_object(self):
        class time(pom.page):
            def main(self):
                # Ensure we have access to the request object from page.
                qs = www.application.current.request.qs
                self.main += dom.p(
                    f'Query string from request: {qs}'
                )

        ws = foonet()
        pg = time()
        ws.pages += pg
        
        own = orm.security().owner

        tab = self.browser().tab()
        res = tab.get('/en/time?herp=derp', ws)

        # Calling the website will change the orm.security.owner to
        # 'anonymous' since we don't put valid JWT in the header. 
        self.is_(orm.security().owner, own)

        ps = res['p']
        self.one(ps)
        self.eq('Query string from request: herp=derp', ps.first.text)

    def it_posts(self):
        class time(pom.page):
            def main(self):
                frm = dom.form()
                frm += dom.h2('Change time')

                self.main += frm

                frm += pom.input(
                    name = 'time',
                    type = 'text',
                    label = 'New time', 
                    placeholder = 'Enter time here',
                    help = 'Enter time and submit'
                )

                frm += pom.input(
                    name = 'comment',
                    type = 'textarea',
                    label = 'Comment', 
                    placeholder = 'Enter comment here',
                    help = (
                        'Enter comment to indicate '
                        'why you changed the time.'
                    )
                )

                tzs = pytz.all_timezones

                frm += pom.input(
                    name = 'timezone',
                    type = 'select',
                    label = 'Time Zone', 
                    help = 'Select timezone',
                    options = [(x, x) for x in tzs],
                    selected = ['US/Arizona']
                )

                req = www.application.current.request
                if req.ispost:
                    frm.post = req.body

        # Create site
        ws = foonet()
        pg = time()
        ws.pages += pg

        # Create browser
        tab = self.browser().tab()

        # GET /en/time
        res = tab.get('/en/time', ws)

        # Select <form>s
        frms = res['main>form']
        self.one(frms)
        frm = frms.first

        time = '2020-02-11 20:44:14'
        comment = 'My Comment'

        # TODO:03ff3691 Select currently doesn't work
        # tzs = ['US/Hawaii', 'America/Detroit']
        # frm['select[name=timezone]'].first.selected = tzs

        frm['input[name=time]'].first.value = time
        frm['textarea[name=comment]'].first.text = comment
        self.one(res['main[data-path="/time"]'])

        res = tab.post('/en/time', ws=ws, frm=frm)

        # TODO: 03ff3691
        # selected = res['main>form select option[selected]']
        # for tz in tzs:
        #    self.true(tz in (x.value for x in selected))

        inps = res['main>form input[name=time]']
        self.one(inps)
        self.eq(time, inps.first.value)

        textarea = res['main>form textarea[name=comment]']
        self.one(textarea)
        self.eq(comment, textarea.first.text)

    def it_raises_im_a_teapot(self):
        rec = None
        def onlog(src, eargs):
            nonlocal rec
            rec = eargs.record

        ws = foonet()

        class pour(pom.page):
            def main(self):
                def get_pot():
                    class pot:
                        iscoffee = False
                        istea    = not iscoffee
                    return pot()

                pot = get_pot()
                if not pot.iscoffee:
                    raise www.ImATeapotError(
                        'Appearently, I am a tea pot'
                    )

        logs.log().onlog += onlog
        pg = pour()
        ws.pages += pg
        tab = self.browser().tab()
        res = tab.get('/en/' + pg.path, ws)
        self.eq(418, res.status)
        mains = res['body>main[data-path="/error"]']

        self.one(mains)

        main = mains.first
        self.eq('418', main['.status'].first.text)

        self.four(main['article.traceback>ul>li'])
        self.one(res['main[data-path="/error"]'])

        ''' Ensure the exception was logged '''
        self.eq(
            "418 I'm a teapot - Appearently, I am a tea pot", 
            rec.message
        )
        
        self.eq('ERROR', rec.levelname)

    def it_gets_favicon_creating_hit_log(self):
        ws = foonet()

        # Create a browser tab
        ip = ecommerce.ip(address='34.56.78.90')
        brw = self.browser(
            ip=ip,
            useragent = (
            'Mozilla/5.0 (iPhone; CPU iPhone OS 5_1 like Mac OS X) '
            'AppleWebKit/534.46 (KHTML, like Gecko) Version/5.1 '
            'Mobile/9B179 Safari/7534.48.3'
            )
        )

        tab = brw.tab()

        tab.referer = 'imtherefere.com'
        hit = ecommerce.hits.last
        res = tab.get('/favicon.ico', ws)
        self.ok(res)

        if hit:
            self.ne(hit.id, ecommerce.hits.last.id)

        hit = ecommerce.hits.last
        self.status(200, hit)

        # Size
        self.eq(0, hit.size)

        # JWT
        self.none(hit.isjwtvalid)

        # Page path
        self.eq('/favicon.ico', hit.path)

        # Site
        self.eq(ws.id, hit.site.id)

        # Language
        self.none(hit.language)

        # Method
        self.eq('GET', hit.method)

        # XHR
        self.false(hit.isxhr)

        # Query string
        self.none(hit.qs)

        # Referer/url
        self.eq('imtherefere.com', hit.url.address)

        # user
        self.none(hit.user)

        # User agent
        self.eq(
            hit.useragent.string, 
            brw.useragent.string
        )

        # User agent - browser
        self.eq('Mobile Safari', hit.useragent.browsertype.name)
        self.eq('5.1', hit.useragent.browsertype.version)

        # User agent - device
        self.eq('iPhone', hit.useragent.devicetype.name)
        self.eq('Apple', hit.useragent.devicetype.brand)
        self.eq('iPhone', hit.useragent.devicetype.model)

        # User agent - platform
        self.eq('iOS', hit.useragent.platformtype.name)
        self.eq('5.1', hit.useragent.platformtype.version)

        # IP address
        self.eq(ip.address, hit.ip.address)

    def it_gets_updated_favicon(self):
        """ Make sure that, when a developer changes the favicon
        (site.favicon), the favicon is changed in the database/HDD/radix
        cache as well.
        """
        ws = foonet()

        # Create a browser tab
        tab = self.browser().tab()

        # Get the original
        res = tab.get('/favicon.ico', ws)
        mime = mimetypes.guess_type('/favicon.ico', strict=False)[0]
        self.ok(res)
        self.eq(mime, res.contenttype)
        self.type(bytes, res.body)
        self.eq(b64decode(Favicon), res.body)

        body = b64decode(GoogleFavicon)

        # A new property to monkey-patch foonet with. This simulates a
        # developer changing the return value of the favicon @property.
        @property
        def favicon(self):
            r = file.file()
            r.name = 'favicon.ico'
            r.body = body
            return r

        # Get a reference to the original favicon @property so can
        # restore it in the `finally` block
        prop = foonet.__dict__['favicon']
        try:
            # Monkey-patch
            foonet.favicon = favicon

            # GET /favicon.ico
            ws = foonet()
            res = tab.get('/favicon.ico', ws)
            mime = mimetypes.guess_type('/favicon.ico', strict=False)[0]
            self.ok(res)
            self.type(bytes, res.body)

            # Ensure it matches the new GoogleFavicon (body)
            self.eq(body, res.body)

            # Test using the file API.
            favicon = ws.public['favicon.ico']
            self.eq(body, favicon.body)

            # Test against the literal file on the HDD
            with open(favicon.path, 'rb') as f:
                self.eq(body, f.read())

        finally:
            # Restore original favicon @property
            foonet.favicon = prop

    def it_gets_favicon(self):
        ws = foonet()

        # Create a browser tab
        tab = self.browser().tab()

        res = tab.get('/favicon.ico', ws)
        mime = mimetypes.guess_type('/favicon.ico', strict=False)[0]
        self.ok(res)
        self.eq(mime, res.contenttype)
        self.type(bytes, res.body)
        self.eq(b64decode(Favicon), res.body)

    def it_returns_404_when_file_doesnt_exist(self):
        """ Ensure a 404 is return when requesting a file (not a page).
        """
        ws = foonet()

        tab = self.browser().tab()
        res = tab.get('/i-dont-exist.ico', ws)
        self.status(404, res)

        # The below assertions where a mistake. Commenting out for
        # illustration. Since there is no real way to determine if a url
        # is for a file or a page at the moment (see bea5347d), the
        # response for a file that doesn't exist should be a 404 along
        # with a 404 webpage. Ideally, the user would just get a simple 
        # HTTP 404 in response.
        #self.empty(res.body)
        #content_length = res.headers['content-length']
        #self.eq(0, content_length)
    
    def it_raises_404(self):
        class derpnets(pom.sites):
            pass

        class derpnet(pom.site):
            Id = UUID(hex='4ef54e9e-2f7d-45bc-861c-3f82bd662938')

            Proprietor = party.company(
                id = UUID(hex='d20088e6-a99a-4e0e-9948-b944242e1206'),
                name = 'Derpnet, Inc'
            )

            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.host = 'derp.net'

        # We need to recreate all the tables involed in the tests below.
        # This is because `derpnet` and `foonet` are being used at the
        # same time which cause issues with the security subsystem, the
        # file sytem, and the file system cache (radix).

        # Unconditionally recreate foonet's tables and supers
        foonet.orm.recreate(ascend=True)
        derpnet.orm.recreate(ascend=True)

        # Delete all inodes and clear the _radix cache
        file.inode.orm.recreate(descend=True)
        with suppress(AttributeError):
            del file.directory._radix

        try:
            ws = derpnet()

            with orm.proprietor(ws.proprietor):
                tab = self.browser().tab()
                res = tab.get('/en/index', ws)
                self.eq(404, res.status)

                # A site will, by default, use the generic 404 page (at
                # the pom.site level). It happens to not have an
                # h2.apology element (unlike foonet; see below).
                self.zero(res['h2.apology'])

                ws = foonet()

                tab = self.browser().tab()

                with orm.proprietor(ws.proprietor):
                    res = tab.get('/en/' + 'intheix.html', ws)

                self.eq(404, res.status)
                
                # foonet has its own 404 page which has an h2.apology
                # element distinguishing it from the generic 404 page at the
                # pom.site level.
                self.one(res['h2.apology'])
                self.one(res['main[data-path="/error/404"]'])
        finally:
            orm.forget(derpnet)

    def it_gets_lingualized_links_on_error(self):
        ws = foonet()

        tab = self.browser().tab()
        res = tab.navigate('/en/i-dont-exist', ws)
        self.eq(404, res.status)

        for a in tab['header a']:
            self.startswith('/en/', a.href)

    def it_raises_im_a_302(self):
        ws = foonet()

        tab = self.browser().tab()
        res = tab.get('/en/index/google', ws)
        self.eq(302, res.status)
        self.eq('https://www.google.com', res.headers['Location'])

    def it_raises_405(self):
        ws = foonet()
        res = self.browser().tab()._request(
            pg='/en/index/google', ws=ws, frm=None, meth='DERP'
        )
        self.eq(405, res.status)
        self.eq('405', res['main .status'].first.text)
        self.one(res['main[data-path="/error"]'])

    def it_calls_language(self):
        class lang(pom.page):
            def main(self):
                lang = www.application.current.request.language
                self.main += dom.p(f'Lang: {lang}')

        ws = foonet()
        pg = lang()
        ws.pages += pg

        tab = self.browser().tab()

        tab.navigate('/en/lang', ws)
        self.one(tab['main[data-path="/lang"]'])

        self.eq('Lang: en', (tab['main p'].first.text))

        # Use Spainish (es)
        tab.navigate('/es/lang', ws)
        self.one(tab['main[data-path="/lang"]'])
        self.eq('Lang: es', (tab['main p'].first.text))
        return

        # Ensure it defauls to English
        # TODO Remove return
        tab.navigate('/lang', ws)

        self.one(tab['main[data-path="/lang"]'])
        self.eq('Lang: en', (tab['main p'].first.text))

    def it_authenticates(self):
        jwt = None
        class authenticate(pom.page):
            def main(self):
                req = www.application.current.request
                res = www.application.current.response

                # Create the login form
                frm = pom.forms.login()
                self.main += frm

                # If GET, then return; the rest is for POST
                if req.isget:
                    return

                ''' POST '''

                # Populate the form with data from the request's body
                frm.post = req.body

                uid = frm['input[name=username]'].first.value
                pwd = frm['input[name=password]'].first.value

                # Load an authenticated user
                try:
                    usr = self.site.authenticate(uid, pwd)
                except pom.site.AuthenticationError:
                    raise www.UnauthorizedError(flash='Try again')
                else:
                    hdr = auth.jwt.getSet_Cookie(usr)
                    res.headers += hdr

        class whoami(pom.page):
            """ A page to report on authenticated users.
            """
            def main(self):
                req = www.application.current.request
                usr = req.user
                jwt = req.cookies('jwt')

                if usr:
                    self.main += dom.p(jwt.value, class_='jwt')

                    self.main += dom.span(usr.name, class_='username')
                else:
                    raise www.UnauthorizedError(flash='Unauthorized')

        class logout(pom.page):
            def main(self):
                res = www.application.current.response
                # Delete the cookie by setting the expiration date in
                # the past.: 
                # https://stackoverflow.com/questions/5285940/correct-way-to-delete-cookies-server-side

                hdrs = res.headers
                hdrs += www.header('Set-Cookie', (
                    'token=; path=/; '
                    'expires=Thu, 01 Jan 1970 00:00:00 GMT'
                    )
                )

        # Set up site
        ws = foonet()
        ws.pages += authenticate()
        ws.pages += whoami()
        ws.pages += logout()

        # Create 10 users, but only save half. Since only half will be
        # in the database, the authenication logic will see them as
        # valid user. The rest won't be able to log in.
        usrs = ecommerce.users()
        for i in range(10):
            usrs += ecommerce.user()
            usrs.last.party    = party.person(name=f'Person {i}')
            usrs.last.name     = uuid4().hex
            usrs.last.password = uuid4().hex
            usrs.last.site     = ws
            if i > 5:
                usrs.last.save()

        # GET the /en/authenticate page
        tab = self.browser().tab()
        res = tab.get('/en/authenticate', ws)
        self.status(200, res)
        frm = res['form'].first

        for i, usr in usrs.enumerate():
            # Populate the login form from the /en/authenticate with
            # credentials of the current user.
            frm['input[name=username]'].first.value = usr.name
            frm['input[name=password]'].first.value = usr.password

            # Post the credentials to /en/authenticate
            res = tab.post('/en/authenticate', ws=ws, frm=frm)

            # If the user is authentic (if the user was previously saved
            # to the database...
            isauthentic = not usr.orm.isnew
            if isauthentic:
                # We should get a JWT form /en/authenticate
                self.status(200, res)
                jwt = tab.browser.cookies['jwt'].value
                jwt = auth.jwt(jwt)
                self.valid(jwt)

                # Given tab.browser has a jwt, it is considered "logged
                # in" to the site. Call the /en/whoami page to get data
                # on the logged in user.
                res = tab.get('/en/whoami', ws)
                self.status(200, res)

                # We should get back a page with the JWT in the HTML as
                # well as the user name.
                self.eq(str(jwt), res['.jwt'].first.text)
                self.eq(usr.name, res['.username'].first.text)
                
                # Calling this page logs us out, i.e., it deletes the
                # JWT cookie.
                res = tab.get('/en/logout', ws)

                # Calling /en/whoami requires that we are logged in, so
                # we will ge a 401.
                res = tab.get('/en/whoami', ws)
                self.zero(res['.jwt'])
                self.status(401, res)
            else:
                # The current user was not saved to the database so
                # logging in will fail.
                self.status(401, res)
                self.eq('Try again', res['.flash'].text)

                # Use /en/whoami to further confirm that we are not
                # logged in.
                res = tab.get('/en/whoami', ws)
                self.eq('Unauthorized', res['.flash'].text)
                self.status(401, res)

    def it_logs_hits(self):
        ''' Set up a page that tests the hit/logging facility '''

        class hitme(pom.page):
            def main(self):
                req = www.application.current.request
                req.hit.logs.write('Starting main')
                dev = req.hit.useragent.devicetype

                self.main += dom.p(f'''
                {dev.brand} {dev.name}
                ''', class_='device')

                req.hit.logs.write('Ending main')

        class signon(pom.page):
            def main(self):
                req = www.application.current.request
                res = www.application.current.response

                self.main += pom.forms.login()

                if req.isget:
                    return

                frm.post = req.body

                uid = frm['input[name=username]'].first.value
                pwd = frm['input[name=password]'].first.value

                req.hit.logs.write(f'Authenticating {uid}')
                try:
                    req.user = self.site.authenticate(uid, pwd)
                except pom.site.AuthenticationError:
                    req.hit.logs.write(f'Authenticated failed: {uid}')
                else:
                    req.hit.logs.write(f'Authenticated {uid}')

                    hdr = auth.jwt.getSet_Cookie(req.user)
                    res.headers += hdr

        # Set up site
        ws = foonet()
        ws.pages += hitme()
        ws.pages += signon()

        # Create a browser tab
        ip = ecommerce.ip(address='12.34.56.78')
        brw = self.browser(
            ip=ip,
            useragent = (
            'Mozilla/5.0 (iPhone; CPU iPhone OS 5_1 like Mac OS X) '
            'AppleWebKit/534.46 (KHTML, like Gecko) Version/5.1 '
            'Mobile/9B179 Safari/7534.48.3'
            )
        )

        tab = brw.tab()

        # NOTE The implicit variable `res` in the pages above collides
        # with the `res` variables I used below, so I change the below
        # ones to `res1`.
        ''' GET page '''
        tab.referer = 'imtherefere.com'
        res1 = tab.get('/en/hitme', ws)
        self.status(200, res1)

        ''' Load the hit and test it '''

        hit = ecommerce.hits.last

        self.notnone(hit.begin)
        self.notnone(hit.end)
        self.true(hit.begin < hit.end)
        self.status(200, hit)
        self.eq(0, hit.size)
        
        # JWT
        self.none(hit.isjwtvalid)

        # Page path
        self.eq('/hitme', hit.path)

        # Site
        self.eq(ws.id, hit.site.id)

        # Language
        self.eq('en', hit.language)

        # Method
        self.eq('GET', hit.method)

        # XHR
        self.false(hit.isxhr)

        # Query string
        self.none(hit.qs)

        # Referer/url
        self.eq('imtherefere.com', hit.url.address)

        # user
        self.none(hit.user)

        # User agent
        self.eq(
            hit.useragent.string, 
            brw.useragent.string
        )

        # Logs
        logs = hit.logs.sorted('datetime')
        self.two(hit.logs)
        self.eq('Starting main', logs.first.message)
        self.eq('Ending main', logs.second.message)

        # User agent - browser
        self.eq('Mobile Safari', hit.useragent.browsertype.name)
        self.eq('5.1', hit.useragent.browsertype.version)

        # User agent - device
        self.eq('iPhone', hit.useragent.devicetype.name)
        self.eq('Apple', hit.useragent.devicetype.brand)
        self.eq('iPhone', hit.useragent.devicetype.model)

        # User agent - platform
        self.eq('iOS', hit.useragent.platformtype.name)
        self.eq('5.1', hit.useragent.platformtype.version)

        # IP address
        self.eq(ip.address, hit.ip.address)

        # Ensure the page has access to the hit object
        self.eq(
            'Apple iPhone',
            res1['.device'].first.text
        )

        ''' Log the authentication of a user '''
        # NOTE Authentication hit logging has a bit of a twist because
        # the request starts out with no JWT or authenticated user, but
        # it ends up with one on completion of the request. The user
        # that gets authenticated should be set in the hit entity
        # (hit.user)

        # Create user
        usr = ecommerce.user(
            name = uuid4().hex,
            password = 'password1',
            site = ws,
        )

        usr.save()

        # Get user/password form
        res1 = tab.get('/en/signon', ws)
        frm = res1['form'].first

        # Set credentials
        frm['input[name=username]'].first.value = usr.name
        frm['input[name=password]'].first.value = usr.password

        # POST credentials to log in
        res1 = tab.post('/en/signon', ws=ws, frm=frm)

        hit = ecommerce.hits.last

        # JWT
        self.none(hit.isjwtvalid)

        # Page path
        self.eq('/signon', hit.path)

        # Site
        self.eq(ws.id, hit.site.id)

        # Language
        self.eq('en', hit.language)

        # Method
        self.eq('POST', hit.method)

        # XHR
        self.false(hit.isxhr)

        # Query string
        self.none(hit.qs)

        # Referer/url
        self.eq('http://foo.net:8000/en/signon', hit.url.address)

        # User
        self.eq(usr.id, hit.user.id)

        # User agent
        self.eq(
            hit.useragent.string, 
            brw.useragent.string
        )

        # Logs
        logs = hit.logs.sorted('datetime')
        self.two(hit.logs)
        self.eq(f'Authenticating {usr.name}', logs.first.message)
        self.eq(f'Authenticated {usr.name}', logs.second.message)

        # User agent - browser
        self.eq('Mobile Safari', hit.useragent.browsertype.name)
        self.eq('5.1', hit.useragent.browsertype.version)

        # User agent - device
        self.eq('iPhone', hit.useragent.devicetype.name)
        self.eq('Apple', hit.useragent.devicetype.brand)
        self.eq('iPhone', hit.useragent.devicetype.model)

        # User agent - platform
        self.eq('iOS', hit.useragent.platformtype.name)
        self.eq('5.1', hit.useragent.platformtype.version)

        # IP address
        self.eq(ip.address, hit.ip.address)

        ''' GET page as logged in user '''
        res1 = tab.get('/en/hitme', ws)
        self.status(200, res1)

        ''' Load the hit and test it '''
        hit = ecommerce.hits.last

        self.notnone(hit.begin)
        self.notnone(hit.end)
        self.true(hit.begin < hit.end)
        self.status(200, hit)
        self.eq(0, hit.size)
        
        # JWT
        self.true(hit.isjwtvalid)

        # Page path
        self.eq('/hitme', hit.path)

        # Site
        self.eq(ws.id, hit.site.id)

        # Language
        self.eq('en', hit.language)

        # Method
        self.eq('GET', hit.method)

        # XHR
        self.false(hit.isxhr)

        # Query string
        self.none(hit.qs)

        # Referer/url
        self.eq('http://foo.net:8000/en/signon', hit.url.address)

        # User
        self.eq(usr.id, hit.user.id)

        # User agent
        self.eq(
            hit.useragent.string, 
            brw.useragent.string
        )

        # Logs
        logs = hit.logs.sorted('datetime')
        self.two(hit.logs)
        self.eq('Starting main', logs.first.message)
        self.eq('Ending main', logs.second.message)

        # User agent - browser
        self.eq('Mobile Safari', hit.useragent.browsertype.name)
        self.eq('5.1', hit.useragent.browsertype.version)

        # User agent - device
        self.eq('iPhone', hit.useragent.devicetype.name)
        self.eq('Apple', hit.useragent.devicetype.brand)
        self.eq('iPhone', hit.useragent.devicetype.model)

        # User agent - platform
        self.eq('iOS', hit.useragent.platformtype.name)
        self.eq('5.1', hit.useragent.platformtype.version)

        # IP address
        self.eq(ip.address, hit.ip.address)

        # Ensure the page has access to the hit object
        self.eq(
            'Apple iPhone',
            res1['.device'].first.text
        )

        ''' Create a JWT signed with the wrong password '''

        # We would expect the hit.isjwtvalid to be False
        d = {
            'exp': primative.datetime.utcnow(hours=24),
            'sub': ecommerce.user().id.hex,
        }

        import jwt as pyjwt
        jwt = pyjwt.encode(d, 'badsecret').decode('utf-8')

        tab.browser.cookies['jwt'].value = str(jwt)

        res1 = tab.get('/en/hitme', ws)

        hit = ecommerce.hits.last

        self.notnone(hit.begin)
        self.notnone(hit.end)
        self.true(hit.begin < hit.end)

        # TODO This should be 401, I think, not 200
        self.status(200, hit)
        self.eq(0, hit.size)

        # JWT
        self.false(hit.isjwtvalid)

        # Page path
        self.eq('/hitme', hit.path)

        # Site
        self.eq(ws.id, hit.site.id)

        # Language
        self.eq('en', hit.language)

        # Method
        self.eq('GET', hit.method)

        # XHR
        self.false(hit.isxhr)

        # Query string
        self.none(hit.qs)

        # Referer/url
        self.eq('http://foo.net:8000/en/hitme', hit.url.address)

        # User
        self.none(hit.user)

        # User agent
        self.eq(
            hit.useragent.string, 
            brw.useragent.string
        )

        # Logs
        logs = hit.logs.sorted('datetime')
        self.two(hit.logs)
        self.eq('Starting main', logs.first.message)
        self.eq('Ending main', logs.second.message)

        # User agent - browser
        self.eq('Mobile Safari', hit.useragent.browsertype.name)
        self.eq('5.1', hit.useragent.browsertype.version)

        # User agent - device
        self.eq('iPhone', hit.useragent.devicetype.name)
        self.eq('Apple', hit.useragent.devicetype.brand)
        self.eq('iPhone', hit.useragent.devicetype.model)

        # User agent - platform
        self.eq('iOS', hit.useragent.platformtype.name)
        self.eq('5.1', hit.useragent.platformtype.version)

        # IP address
        self.eq(ip.address, hit.ip.address)

    def it_can_access_injected_variables(self):
        class lang(pom.page):
            def main(self):
                req = www.application.current.request
                res = www.application.current.response

                # Use req instead of www.request
                lang = req.language
                self.main += dom.span(lang, lang="lang")

                # Use res instead of www.response
                res.status = 418

        ws = foonet()
        pg = lang()
        ws.pages += pg

        tab = self.browser().tab()
        res1 = tab.get('/en/lang', ws)
        self.one(res1['span[lang=lang]'])
        self.status(418, res1)

    def it_raises_on_reserved_parameters(self):
        def flashes_ValueError(res):
            spans = res['main article.flash:nth-child(1) span.type']
            self.one(spans)
            self.eq('ValueError', spans.first.text)
            self.status(500, res)

        ''' Can't use `req` '''
        class help(pom.page):
            def main(self, req):
                pass

        ws = foonet()
        ws.pages += help()

        tab = self.browser().tab()
        res = tab.get('/en/help', ws)
        flashes_ValueError(res)

        ''' Can't use `res` '''
        class help(pom.page):
            def main(self, res):
                pass

        ws = foonet()
        ws.pages += help()

        res = tab.get('/en/help', ws)
        flashes_ValueError(res)

        ''' Can't use `usr` '''
        class help(pom.page):
            def main(self, usr):
                pass

        ws = foonet()
        ws.pages += help()

        res = tab.get('/en/help', ws)
        flashes_ValueError(res)

        ''' Can use `derp`.  '''
        # This is here just to ensure that the above tests would return
        # 200 if the parameter used was not one of the reserved
        # parameter. Above, we only test if the response is 500 so it's
        # possible that another issue is causing the problem. The below
        # test should be an exact copy of the above test except,
        # obviously for the parameter name.
        class help(pom.page):
            def main(self, derp):
                pass

        ws = foonet()
        ws.pages += help()

        res = tab.get('/en/help', ws)
        self.status(200, res)

    def it_flashes_message(self):
        ''' Test a str flash message '''
        class murphy(pom.page):
            def main(self):
                self.flash('Something went wrong')

        ws = foonet()
        ws.pages += murphy()

        tab = self.browser().tab()
        res = tab.get('/en/murphy', ws)
        arts = res['main article.flash']
        self.one(arts)

        art = arts.first

        self.eq('Something went wrong', art.text)

        ''' Test an HTML flash message by passing in a dom.element '''
        class murphy(pom.page):
            def main(self):
                ul = dom.ul()
                ul += dom.li('This went wrong')
                ul += dom.li('That went wrong')
                self.flash(ul)

        ws = foonet()
        ws.pages += murphy()

        res = tab.get('/en/murphy', ws)
        lis = res['main article.flash>ul>li']
        self.two(lis)
        
        self.eq('This went wrong', lis.first.text)
        self.eq('That went wrong', lis.second.text)

    def it_raises_flash_errors(self):
        ''' Test an HTML flash message by raising an HttpError '''
        class murphy(pom.page):
            def main(self):
                self.main += dom.h1('Checking brew type...')
                raise www.ImATeapotError(flash='Invalid brew type')

        ws = foonet()
        ws.pages += murphy()

        tab = self.browser().tab()
        res = tab.get('/en/murphy', ws)
        self.status(418, res)

        arts = res['main article.flash:nth-child(1)']
        self.one(arts)

        self.eq('Invalid brew type', arts.first.text)

    def it_responds_to_button_click(self):
        div0 = div1 = div2 = None
        class clickme(pom.page):
            def btn_onclick(self, src, eargs):
                req = www.application.current.request
                eargs.html['p'].only += dom.strong('Thanks')
                req.hit.logs += ecommerce.log(message='I got clicked')

            def btn_onclick1(self, src, eargs):
                div1, div2 = eargs.html
                div1['p'].only += dom.strong('Thanks again')
                div2['p'].only += dom.strong(
                    "No really, you're too kind"
                )

            def main(self):
                nonlocal div0, div1, div2
                self.main += (div0 := dom.div())
                div0 += dom.p()

                self.main += (div1 := dom.div())
                div1 += dom.p()

                self.main += (div2 := dom.div())
                div2 += dom.p()

                # When this button is clicked, the html for div0 will be
                # POSTed in an XHR request
                div0 += (btn := dom.button('Click me'))
                btn.onclick += self.btn_onclick, div0

                # When this button is clicked, the html for div1 and
                # div2 will be POSTed in an XHR request
                self.main += (btn := dom.button('No, click me'))
                btn.onclick += self.btn_onclick1, div1, div2

        ws = foonet()
        ws.pages += clickme()

        tab = self.browser().tab()

        # GET the clickme page
        res = tab.navigate('/en/clickme', ws)
        self.status(200, res)

        # Get the <button> from the response
        btn = tab.html['div>button'].only

        # Click the button. This will cause an XHR request back to the
        # page's btn_onclick event handler.
        btn.click()

        hit = ecommerce.hits.last
        self.eq('/clickme', hit.path)
        self.eq('POST', hit.method)
        self.true(hit.isxhr)
        self.eq(tab.html.first.language, hit.language)
        self.eq(200, hit.status)
        self.one(hit.logs)
        self.eq('I got clicked', hit.logs.first.message)
        self.none(hit.isjwtvalid)

        # Now that we've clicked the button, the tab's internal DOM
        # should have a <p> tag with the word Thanks in it due to the
        # XHR request having completed successfully.
        sel = f'#{div0.id} p strong'
        self.eq('Thanks', tab.html[sel].text)

        btn = tab.html['main>button'].only
        btn.click()

        sel = f'#{div1.id} p strong'
        self.eq('Thanks again', tab.html[sel].text)

        sel = f'#{div2.id} p strong'

        # FIXME The element's `pretty` property returns the encoded
        # apostrophy. That's not pretty at all. Additionally, using the
        # `text` node`s `value` property returns a truncated 'No really,
        # you' for some reason.
        self.eq(
            'No really, you&#x27;re too kind',
            tab.html[sel].first.elements.first.pretty
        )

    def it_responds_to_two_different_buttons_with_single_handler(self):
        div0 = div1 = div2 = None
        class clickme(pom.page):
            def btn_onclick(self, src, eargs):
                if src.text == 'Click me':
                    eargs.html['p'].only += dom.strong('Thanks')
                elif src.text == 'Click me again':
                    ps = eargs.html['div>p']
                    assert ps.count == 2
                    ps.first.text = 'Thanks again'
                    ps.second.text = 'Again... thanks'

            def main(self):
                nonlocal div0, div1, div2
                self.main += (div0 := dom.div())
                div0 += dom.p()

                self.main += (div1 := dom.div())
                div1 += dom.p()

                self.main += (div2 := dom.div())
                div2 += dom.p()

                # When this button is clicked, the html for div0 will be
                # POSTed in an XHR request
                div0 += (btn_clickme := dom.button('Click me'))
                div0 += (
                    btn_clickmeagain := dom.button('Click me again')
                )

                btn_clickme.onclick += self.btn_onclick, div0
                btn_clickmeagain.onclick += self.btn_onclick, div1, div2


        ws = foonet()
        ws.pages += clickme()

        tab = self.browser().tab()

        # GET the clickme page
        res = tab.navigate('/en/clickme', ws)

        self.status(200, res)

        # Get the <button> from the response
        btns = tab.html['div>button']

        assert btns.count == 2

        btn_clickme, btn_clickmeagain = btns

        btn_clickme.click()
        self.eq('Thanks', tab.html['#' + div0.id + '>p'].only.text)

        self.eq(
            str(), tab.html['#' + div1.id + '>p'].only.text
        )
        self.eq(
            str(), tab.html['#' + div2.id + '>p'].only.text
        )

        btn_clickmeagain.click()
        self.eq(
            'Thanks again', tab.html['#' + div1.id + '>p'].only.text
        )
        self.eq(
            'Again... thanks', tab.html['#' + div2.id + '>p'].only.text
        )

    def it_responds_to_two_different_widgets_with_single_handler(self):
        div0 = div1 = None
        class clickme(pom.page):
            def inp_onfocuschange(self, src, eargs):
                if eargs.trigger == 'focus':
                    eargs.html.only['p'].only += 'focus triggered'
                elif eargs.trigger == 'blur':
                    eargs.html.only['p'].only += 'blur triggered'
                else:
                    raise ValueError('Invalid trigger')

            def main(self):
                nonlocal div0, div1
                self.main += (div0 := dom.div())
                div0 += dom.p()

                self.main += (div1 := dom.div())
                div1 += dom.p()

                div0 += (inp := dom.input())

                inp.onblur += self.inp_onfocuschange, div1
                inp.onfocus += self.inp_onfocuschange, div0

        ws = foonet()
        ws.pages += clickme()

        tab = self.browser().tab()

        # GET the clickme page
        tab.navigate('/en/clickme', ws)

        inp = tab.html['div>input'].only

        p0 = tab.html['#' + div0.id + '>p'].only
        p1 = tab.html['#' + div1.id + '>p'].only
        self.empty(p1.text)
        self.empty(p0.text)

        inp.focus()
        inp.blur()

        p0 = tab.html['#' + div0.id + '>p'].only
        p1 = tab.html['#' + div1.id + '>p'].only
        self.eq('blur triggered', p1.text)
        self.eq('focus triggered', p0.text)

    def it_fires_event_with_no_html_fragments(self):
        handled = False
        class clickme(pom.page):
            def btn_onclick(self, src, eargs):
                nonlocal handled
                handled = True

            def main(self):
                self.main += (btn := dom.button('Click me'))
                btn.onclick += self.btn_onclick

        ws = foonet()
        ws.pages += clickme()

        tab = self.browser().tab()

        # GET the clickme page
        tab.navigate('/en/clickme', ws)

        html = tab.html.html
        btn = tab.html['main>button'].only

        btn.click()

        self.eq(html, tab.html.html)
        self.true(handled)

    def it_returns_traceback_on_exception_during_event_handling(self):
        div0 = div1 = div2 = None
        class clickme(pom.page):
            def btn_onclick(self, src, eargs):
                raise NotImplementedError("No, I'm not ready")

            def main(self):
                self.main += (btn := dom.button('Click me'))
                self.main += (div := dom.div())
                btn.onclick += self.btn_onclick, div

        ws = foonet()
        ws.pages += clickme()

        tab = self.browser().tab()

        # GET the clickme page
        tab.navigate('/en/clickme', ws)
        self.zero(tab['.exception'])

        btn = tab.html['main>button'].only

        btn.click()

        self.one(tab['main>.error-modal'])
        self.one(tab['main>.error-modal'])
        self.one(tab['main>.error-modal p.message'])
        self.one(tab['main>.error-modal details.traceback'])

    def it_replaces_correct_fragment(self):
        """ This was written due to a bug found in
        tester._browser._tab.element_event which incorrectly patched the
        DOM object. Instead of replacing the element in its current
        position, it removed the old element and appended the new
        element to the end.  This is obviously wrong because it can
        result in elements getting ordered incorrectly in the DOM. This
        test would fail when the bug was in place.
        """
        class clickme(pom.page):
            def btn_onclick(self, src, eargs):
                div = eargs.html.only
                div.text = 'I am changed'

            def main(self):
                self.main += (sec := dom.section())
                sec += (div0 := dom.div('I should be changed'))
                sec += (div1 := dom.div('I should remain unchanged'))

                self.main += (btn := dom.button('Click me'))
                btn.onclick += self.btn_onclick, div0

        ws = foonet()
        ws.pages += clickme()

        tab = self.browser().tab()

        # GET the clickme page
        res = tab.navigate('/en/clickme', ws)

        self.status(200, res)

        # Get the <button> from the response
        btn = tab.html['main>button'].only

        # Click the button. This will cause an XHR request back to the
        # page's btn_onclick event handler.
        btn.click()

        sec = tab['main>section'].only

        self.eq('I am changed', sec.elements.first.text)
        self.eq('I should remain unchanged', sec.elements.second.text)

    def it_gets_same_page_twice(self):
        """ There were issues when tests would use the same website
        object (ws) to make multiple requests to the same page. For the
        sake of automated testing, we want to make sure that there are
        no problems doing this.
        """
        ws = foonet()

        tab = self.browser().tab()

        ''' Test Non-SPA '''
        tab.navigate('/en/index', ws)
        html = tab.html.html

        self.expect(None, lambda: tab.navigate('/en/index', ws))
        html1 = tab.html.html

        self.eq(html, html1)

        ''' Test SPA '''
        tab.inspa = True
        tab.navigate('/en/spa', ws)
        html = tab.html.html

        self.expect(None, lambda: tab.navigate('/en/spa', ws))
        html1 = tab.html.html

        self.eq(html, html1)

        ''' Test subpage '''
        tab.navigate('/en/spa/subpage', ws)
        html = tab.html.html

        self.expect(None, lambda: tab.navigate('/en/spa/subpage', ws))
        html1 = tab.html.html

        self.eq(html, html1)

        ''' Test multiple events '''
        class clickme(pom.page):
            def btn_onclick(self, src, eargs):
                eargs.html['p'].only.text = primative.datetime.utcnow()

            def main(self):
                div = dom.div()
                btn = dom.button('Click me')
                self.main += div

                div += dom.p()
                div += btn

                btn.onclick += self.btn_onclick, div

        ws = foonet()
        ws.pages += clickme()

        res = tab.navigate('/en/clickme', ws)
        self.status(200, res)

        btn = tab['div>button'].only

        btn.click()
        p = tab['main>div>p'].only
        first = primative.datetime(p.text)

        btn.click()
        p = tab['main>div>p'].only
        second = primative.datetime(p.text)

        self.gt(first, second)

        ''' Test SPA subpage navigation'''
        tab.navigate('/en/spa', ws)

        # Click on the Blog menu item twice
        a_blog = tab['header>section>nav a[href|="/en/blogs"]'].only

        a_blog.click()
        attrs = tab.html['main'].only.attributes
        self.eq('/blogs', attrs['data-path'].value)

        a_blog.click()
        attrs = tab.html['main'].only.attributes
        self.eq('/blogs', attrs['data-path'].value)

        # Click on the Subpage menu item twice

        # Go back to /en/spa. The above click() would have have caused a
        # traditional page navigation to /en/blogs
        tab.navigate('/en/spa', ws)

        sel = 'nav[aria-label=Spa] a[href|="/en/spa/subpage"]'

        a_subpage = tab[sel].only

        a_subpage.click()
        attrs = tab.html['main'].only.attributes
        self.eq('/spa/subpage', attrs['data-path'].value)

        a_subpage.click()
        attrs = tab.html['main'].only.attributes
        self.eq('/spa/subpage', attrs['data-path'].value)

    def it_puts_tab_inspa_mode(self):
        ws = foonet()

        tab = self.browser().tab()

        tab.inspa = True

        # SPA pages should be put inspa mode
        tab.navigate('/en/spa', ws)
        self.true(tab.inspa)

        # Traditional pages should not be put inspa mode
        tab.navigate('/', ws)
        self.false(tab.inspa)

    def it_patches_spa_subpage_on_menu_click(self):
        ws = foonet()

        tab = self.browser().tab()

        tab.inspa = True

        # GET the clickme page
        tab.navigate('/en/spa', ws)

        attrs = tab.html['main'].only.attributes
        self.eq('/spa', attrs['data-path'].value)

        a_blog = tab['header>section>nav a[href|="/en/blogs"]'].only

        a_blog.click()
        attrs = tab.html['main'].only.attributes
        self.eq('/blogs', attrs['data-path'].value)

        # Go back to /en/spa. The above click() would have have caused a
        # traditional page navigation to /en/blogs
        tab.navigate('/en/spa', ws)
        sel = 'nav[aria-label=Spa] a[href|="/en/spa/subpage"]'
        a_subpage = tab[sel].only

        a_subpage.click()
        attrs = tab.html['main'].only.attributes
        self.eq('/spa/subpage', attrs['data-path'].value)

    def it_resolves_subpage_to_spa(self):
        """ Make sure that when a subpage of an SPA application is
        accessed with a GET, we get the full SPA with the subpage
        embedded within it.

        The SPA page itself may have menu items in its <head>, for
        example, which the subpage alone would not be aware of and could
        not produce. Thus the SPA page needs to be returned with the
        subpage embedded in its <main> tag.
        """
        ws = foonet()

        tab = self.browser().tab()

        tab.inspa = True

        # GET the subpage
        tab.navigate('/en/spa/subpage', ws)

        # Assert that main's data-path attribute is set to
        # /spa/subpage
        #
        #     <main data-path="/spa/subpage">
        #
        attrs = tab.html['main'].only.attributes
        self.eq('/spa/subpage', attrs['data-path'].value)

        # Assert there is one menu item for /spa/subpage (in the Spa
        # menu). This would only exist if we were getting the spa page;
        # the subpage would not have it.
        self.one(tab['nav[aria-label=Spa] a[href|="/en/spa/subpage"]'])

        ps = tab['main p']

        self.one(ps)

        # Make sure the one paragraph in <main> identities itself as the
        # subpage. 
        self.eq('I am the subpage', ps.only.text)

    def it_navigates_traditionally_from_nonspa_menu(self):
        before = after = None
        def tab_onbeforeunload(src, eargs):
            nonlocal before
            before = eargs

        def tab_onafterload(src, eargs):
            nonlocal after
            after = eargs

        ws = foonet()

        tab = self.browser().tab()

        # GET the subpage
        res = tab.navigate('/en/spa', ws)

        self.ok(res)

        a = tab['header nav[aria-label=Main a]'].first

        tab.onbeforeunload += tab_onbeforeunload 
        tab.onafterload += tab_onafterload 

        r = a.click()

        main = tab['main'].only

        path = main.attributes['data-path'].value
        self.eq('/index', path)
        self.eq('/en/spa', before.url.path)
        self.eq('/en/index', after.url.path)

    def it_navigates_to_pages_when_spa_is_disabled(self):
        ws = foonet()

        tab = self.browser().tab()

        # GET the clickme page
        tab.navigate('/en/spa', ws)

        self.eq('foonet | Spa', tab.html['title'].only.text)

        a_blog = tab['header>section>nav a[href|="/en/blogs"]'].only

        tab.inspa = False
        a_blog.click()

        self.eq('foonet | Blogs', tab.html['title'].only.text)

class admin(pom.page):
    def __init__(self):
        super().__init__()
        self.pages += users()
        self.pages += reports()

class users(pom.page):
    def __init__(self):
        super().__init__()
        self.pages += statistics()

class statistics(pom.page):
    def __init__(self):
        super().__init__()

    def main(self):
        pass

class reports(pom.page):
    def __init__(self):
        super().__init__()
        self.pages += netsales()
        self.pages += accountsummary()

class netsales(pom.page):
    def __init__(self):
        super().__init__()

class accountsummary(pom.page):
    pass

class home(pom.page):
    def __init__(self):
        super().__init__()
        self.pages += google('google')

    @property
    def name(self):
        return 'index'

class profiles(pom.crud):
    def __init__(self, *args, **kwargs):
        super().__init__(e=persons, *args, **kwargs)

    @property
    def detail(self):
        return self.site.pages['profile']

class profile(pom.crud):
    def __init__(self, *args, **kwargs):
        super().__init__(e=person, *args, **kwargs)

class spa(pom.spa):
    ''' Inner classes of spa '''
    class subpage(pom.page):
        def main(self):
            self.main += dom.p('I am the subpage')

    ''' Members of spa '''
    def __init__(self):
        super().__init__()
        self.pages += spa.subpage('subpage')

    def main(self):
        if not self.header.menu:
            self.header.makemain()

        self.main += dom.p('Welcome to the SPA')

        ''' Create all menu '''
        self.header.menus += pom.menu.make(self.pages, 'spa')

        mnuspa = self.header.menus['nav[aria-label=Spa]'].only

        prof = profile()
        mnuspa.items += pom.menu.item(
            'New profile', f'{prof.path}?crud=create'
        )

        profs = profiles()
        mnuspa.items += pom.menu.item(
            'Profiles', f'{profs.path}'
        )

class google(pom.page):
    def main(self, **kwargs):
        # HTTP 302 Found (i.e., redirect)
        raise www.FoundException(location="https://www.google.com")

class blogs(pom.page):
    def __init__(self):
        super().__init__()
        self.pages += blog_categories('categories')
        self.pages += blog_posts('posts')
        self.pages += blog_comments('comments')

    def main(self):
        pass

class blog_categories(pom.page):
    pass

class blog_posts(pom.page):
    pass

class blog_comments(pom.page):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pages += blog_approved_comments('approved')
        self.pages += blog_rejected_comments('rejected')

class blog_approved_comments(pom.page):
    pass

class blog_rejected_comments(pom.page):
    pass

class about(pom.page):
    def __init__(self):
        super().__init__()
        self.pages += about_team()

class about_team(pom.page):
    @property
    def name(self):
        return 'team'

class contact_us(pom.page):
    pass

class fasthome(pom.page):
    def __init__(self):
        super().__init__()

    @property
    def name(self):
        return 'home'

    def main(self):
        self.main += dom.p('Welcome to fast.net')

class fastnets(pom.sites):
    pass

class fastnet(pom.site):
    Id = UUID(hex='44327b84-5fe2-4247-a5c7-601e2a763e7b')

    Proprietor = party.company(
        id = UUID(hex='5257ee0f-305a-4b37-a52d-a366aca76bf9'),
        name = 'Fastnet, Inc'
    )
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.host = 'fast.net'
        self.name = 'fast.net'

        self.pages += fasthome()

class cpu_page(tester.benchmark):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        orm.security().override = True
        if self.rebuildtables:
            es = orm.orm.getentityclasses(includeassociations=True)
            mods = (
                'party', 'ecommerce', 'pom', 'asset', 'apriori',
            )

            for e in es:
                if e.__module__ in  mods:
                    e.orm.recreate()

        fastnet.orm.recreate()

    def it_gets(self):
        ws = fastnet()
        tab = self.browser().tab()

        def f():
            return tab.get('/en/home', ws)

        #self.time(2400, 2600, f, 1)
        #self.time(1400, 1800, f, 5)
        self.time(600, 800, f, 2)

        '''
        www.py:587(__call__) ->      1    0.000    0.497  dom.py:1750(html)
                                     1    0.000    0.558  pom.py:901(__call__)
                                     1    0.000    0.000  www.py:505(arguments)
                                     2    0.000    0.000  www.py:555(page)
                                     2    0.000    2.938  www.py:649(log)
        '''

class card(tester.tester):
    def it_calls__init__(self):
        card = pom.card()
        self.true('card' in card.classes)

    def it_calls_btnedit(self):
        # Defaults to none
        card = pom.card()
        self.none(card.btnedit)

        # Set
        btn = dom.button('Edit me')
        card.btnedit = btn

        self.true('edit' in btn.classes)

        # Get
        self.is_(btn, card.btnedit)

        # Make sure there's only one edit button
        self.one(card['button.edit'])

        # Reset with new button and test
        btn1 = dom.button('Another Edit me')
        card.btnedit = btn1
        self.is_(btn1, card.btnedit)

        # Make sure there's only one edit button
        self.one(card['button.edit'])

class crud(tester.tester):
    def __init__(self, *args, **kwargs):
        # We will be testing with foonet so set it as the ORM's
        # proprietor
        propr = foonet.Proprietor
        with orm.sudo(), orm.proprietor(propr):
            # Assign the proprietor's owner. We need to manually ascend
            # due to TODO:6b455db7
            sup = propr
            while sup:
                sup.owner = ecommerce.users.root
                sup = sup.orm._super

        super().__init__(propr=propr, *args, **kwargs)

        if self.rebuildtables:
            orm.orm.recreate(
                person,
            )

    def it_GETs_form(self):
        ws = foonet()
        tab = self.browser().tab()

        # Get form
        tab.navigate('/en/profile?crud=create', ws)

        frm = tab['form'].only

        ''' Default str '''
        '''
        <div data-entity-attribute="name">
          <label for="x_oH0njadTO2QpsceA2s3vw">
            Name
          </label>
          <input 
            name="name" 
            type="text" 
            id="x_oH0njadTO2QpsceA2s3vw" 
            minlength="1" 
            maxlength="255" 
            value=""
          >
        </div>
        '''

        div = frm['[data-entity-attribute=name]'].only
        lbl = div['label'].only
        inp = div['input'].only

        self.eq('name', inp.name)
        self.eq('text', inp.type)
        self.eq(lbl.for_, inp.id)
        self.eq('1', inp.minlength)
        self.eq('255', inp.maxlength)

        # Default date
        '''
          <div data-entity-attribute="born">
            <label for="xuPaeyvPXRt6loWYwjjX_lw">
              Born
            </label>
            <input name="born" type="date" id="xuPaeyvPXRt6loWYwjjX_lw" value="">
          </div>
        '''

        div = frm['[data-entity-attribute=born]'].only
        lbl = div['label'].only
        inp = div['input'].only

        self.eq('born', inp.name)
        self.eq('date', inp.type)
        self.eq(lbl.for_, inp.id)
        self.eq(str(), inp.value)

        # Default text
        '''
          <div data-entity-attribute="bio">
            <label for="xmubrEcPVTs2M6nLoAV_Ldw">
              Bio
            </label>
            <textarea name="bio" id="xmubrEcPVTs2M6nLoAV_Ldw" minlength="1" maxlength="65535">
            </textarea>
          </div>
        '''
        div = frm['[data-entity-attribute=bio]'].only
        lbl = div['label'].only
        inp = div['textarea'].only

        self.eq('bio', inp.name)
        self.eq(lbl.for_, inp.id)
        self.eq(str(), inp.text)
        self.eq('1', inp.minlength)
        self.eq('65535', inp.maxlength)

        # TODO Continue these tests for <select>'s, 
        # <input type=checkbox>, <input type=radio>. Test for different
        # data types as well such as `text` (blob), floats, decimal,
        # booleans, etc.

    def it_gets_from_spa(self):
        ws = foonet()
        tab = self.browser().tab()

        tab.navigate('/en/spa', ws)
        mnuspa = tab['nav[aria-label=Spa]'].only

        aprofile = mnuspa['a[href$="/profile?crud=create"]'].only

        res = self.click(aprofile, tab)
        self.h200(res)

        # TODO We should also test different crud operations here. At
        # the moment, only 'create' makes sense for a menu. We would
        # want hyperlinks for things like 'retrieve', 'update', and
        # 'delete'.

    def it_creates(self):
        ws = foonet()
        tab = self.browser().tab()

        per = person.getvalid()

        # Get form
        tab.navigate('/en/profile?crud=create', ws)

        frm = tab['form']

        for map in person.orm.mappings.fieldmappings:
            if map.name == 'createdat':
                continue

            if map.name == 'updatedat':
                continue

            v = getattr(per, map.name)
            div = frm[f'[data-entity-attribute={map.name}]']
            el = div['input, textarea'].only

            if isinstance(el, dom.input):
                el.value = getattr(per, map.name)
            elif isinstance(el, dom.textarea):
                el.text =  getattr(per, map.name)

        btnsubmit = frm['button[type=submit]'].only

        btnsubmit.click()

        card = tab['article.card'].only

        id = card['[data-entity-attribute=id] span'].only.text

        per1 = self.expect(None, lambda: person(id))

        for map in person.orm.mappings.fieldmappings:
            if map.name == 'createdat':
                continue

            if map.name == 'updatedat':
                continue

            v = getattr(per, map.name)
            v1 = getattr(per1, map.name)

            self.eq(v, v1)

    def it_retrieves(self):
        per = person.getvalid()
        per.save()

        ws = foonet()
        tab = self.browser().tab()

        # Get form
        tab.navigate(f'/en/profile?id={per.id}&crud=retrieve', ws)

        card = tab['article.card'].only

        '''
          <button class="edit" data-click-handler="btnedit_onclick" data-click-fragments="#xelp1mJ-MQBu0znR0o_E0Lg">
            Edit
          </button>
        '''

        btn = card['button.edit'].only

        self.eq('btnedit_onclick', btn.getattr('data-click-handler'))
        self.eq(card.id, btn.getattr('data-click-fragments')[1:])
        self.eq('Edit', btn.text)

        '''
          <div data-entity-attribute="name">
            <label for="xHth2cToUSfaODKVsoIDKlw">
              Name
            </label>
            <span id="xHth2cToUSfaODKVsoIDKlw">
              Jesse
            </span>
          </div>
        '''

        # Get elements
        div = card['[data-entity-attribute=name]'].only
        lbl = div['label'].only
        span = div['span'].only

        # Label
        self.eq('Name', lbl.text)

        # Span
        self.eq(per.name, span.text)
        self.eq(lbl.for_, span.id)

        '''
          <div data-entity-attribute="born">
            <label for="x25v_AqZbSiSyYu99lc1KRQ">
              Born
            </label>
            <span id="x25v_AqZbSiSyYu99lc1KRQ">
              1976-04-15
            </span>
          </div>
        '''

        # Get elements
        div = card['[data-entity-attribute=born]'].only
        lbl = div['label'].only
        span = div['span'].only

        # Label
        self.eq('Born', lbl.text)

        # Span
        self.eq(per.born, primative.date(span.text))
        self.eq(lbl.for_, span.id)

        '''
          <div data-entity-attribute="bio">
            <label for="xLDT9TgHfTOKPgQyuwx1HrQ">
              Bio
            </label>
            <span id="xLDT9TgHfTOKPgQyuwx1HrQ">
              Hello. I&#x27;m a professional programmer
            </span>
          </div>
        '''

        # Get elements
        div = card['[data-entity-attribute=bio]'].only
        lbl = div['label'].only
        span = div['span'].only

        # Label
        self.eq('Bio', lbl.text)

        # Span
        self.eq(per.bio, span.text)
        self.eq(lbl.for_, span.id)

    def it_updates(self):
        ''' Happy path '''
        per = person.getvalid()
        per.save()

        ws = foonet()
        tab = self.browser().tab()

        # Get form
        tab.navigate(f'/en/profile?id={per.id}&crud=update', ws)

        frm = tab['form'].only

        name = uuid4().hex
        bio = uuid4().hex
        born = primative.date('1413-03-04')

        frm['[data-entity-attribute=name] input'].only.value = name
        frm['[data-entity-attribute=born] input'].only.value = str(born)
        frm['[data-entity-attribute=bio] textarea'].only.text = bio

        frm['button[type=submit]'].only.click()

        per1 = per.orm.reloaded()

        self.eq(name, per1.name)
        self.eq(born, per1.born)
        self.eq(bio,  per1.bio)

        ''' Update with bad id '''
        # Get form
        tab.navigate(f'/en/profile?id={per.id}&crud=update', ws)
        frm = tab['form'].only

        name = uuid4().hex

        inp = frm['[data-entity-attribute=id] input'].only
        inp.value = 'not-a-uuid'
        frm['[data-entity-attribute=name] input'].only.value = name

        btn = frm['button[type=submit]'].only
        
        res = self.click(btn, tab)

        # NOTE Maybe this should be h422. For browsers it probably
        # doesn't matter that much, but for RPC it may.
        self.h500(res)

        type = tab['.exception span.type'].only.text
        self.eq('ValueError', type)

    def it_navigates_to_entities_page(self):
        """ Test loading a pom.page with an entities collection. We
        should get a <table> with each entity represented as <tr>s
        within the collection.
        """
        Count = 10

        ws = foonet()
        tab = self.browser().tab()

        pers = persons()
        for i in range(Count):
            per = person.getvalid()

            pers += per

        pers.save()

        # Get form
        tab.navigate('/en/profiles', ws)

        tbl = tab['main table'].only

        self.endswith('.person', tbl.getattr('data-entity'))

        trs = tbl['tbody tr']

        # We should have a <tr> for each of the persons created above
        self.ge(Count, trs.count)

        # Make sure there is a <tr> for each person
        ids = [UUID(x.getattr('data-entity-id')) for x in trs]

        for per in pers:
            self.in_(ids, per.id)
            for tr in trs:
                id = UUID(tr.getattr('data-entity-id'))
                if per.id == id:
                    break
            else:
                continue
                    
            for attr in ('name', 'bio'):
                td = tr[f'td[data-entity-attribute={attr}]'].only
                self.eq(str(getattr(per, attr)), td.text)

            td = tr['td[data-entity-attribute=id]'].only

            # Get the Quick Edit anchor
            a = td['menu li a[rel~=edit][rel~=preview]'].only

            self.eq('Quick Edit', a.text)

            # We expect the rel attribute for the Quick Edit anchor to
            # have 'edit' and 'preview'
            rels = a.getattr('rel').split()
            self.in_(rels, 'edit')
            self.in_(rels, 'preview')

            self.eq('/en/profiles', a.href)

            # Get the Edit anchor
            a = td['menu li a[rel~=edit]:not([rel~=preview])'].only

            self.eq('Edit', a.text)

            # We expect the rel attribute for the Edit anchor to
            # only have 'edit'
            self.eq('edit', a.getattr('rel'))

            expect = (
                f'/en/profile?id={per.id.hex}'
                '&crud=update&oncomplete=/profiles'
            )
            self.eq(expect, a.href)

            # TODO Test the anchor's data-click-handler and
            # data-click-fragments="#x8nMAagjHTRKQDSklK82fSQ"
            # attributes.

    def it_navigates_to_entities_clicks_quick_edit(self):
        """ Use the Quick Edit feature of a pom.crud page to get a form.
        Test the form's values.
        """
        ws = foonet()
        tab = self.browser().tab()

        # Add some persons
        pers = persons()
        for i in range(3):
            per = person.getvalid()
            pers += per

        pers.save()

        # Get form
        tab.navigate('/en/profiles', ws)

        tbl = tab['main table'].only

        # Get a random person
        per = pers.getrandom()

        # Get the <tr> from the first person created above
        sels = f'tr[data-entity-id="{per.id.hex}"]'
        tr = tbl[sels].only

        # Get Quick Edit anchor
        a = tr['a[rel~=edit][rel~=preview]'].only

        # Before the click, the table will have no <form>
        self.zero(tab['table form'])

        # Nonmally we would use self.click() but we want make user the
        # test browser is issuing the correct HTTP requests because of
        # the SPA and traditional orientations of pom.crud.
        with tab.capture() as msgs:
            a.click()

        # We should only have one
        msg = msgs.only

        # Ensure we POSTed to http://foo.net:8000/en/profiles'
        self.eq('POST', msg.request.method)
        self.eq('http://foo.net:8000/en/profiles', str(msg.request.url))

        # Ensure 200 response
        self.h200(msgs.only.response)

        # Obtain the <tr> again
        tr1 = tbl[sels].only

        # This time it will be different because the click will have
        # caused the server to replace it with a new <tr> which contains
        # a <form>.
        self.isnot(tr, tr1)

        # Let's use `tr` instead of `tr1` for the tests below
        tr = tr1

        self.endswith('.person', tr.getattr('data-entity'))
        self.eq(per.id.hex, tr.getattr('data-entity-id'))

        # Get the <td> in the <tr> that contains the <form>
        td = tr['td:first-child'].only

        # Test <td colspan="3">
        self.eq(3, int(td.getattr('colspan')))

        # Get <form>
        frm = td['form'].only

        self.endswith('.person', frm.getattr('data-entity'))

        # Get form's labels
        lbls = frm['div[data-entity-attribute] label']

        # Test them
        expect = ['Name', 'Born', 'Bio']
        self.eq(expect, lbls.pluck('text'))

        # Test the hidden id <input>
        inp = frm['div[data-entity-attribute=id] input'].only
        self.eq(per.id, UUID(inp.value))
        self.eq('hidden', inp.type)
        self.eq('id', inp.name)

        # TODO Test the rest of the attributes

        # Make sure there is one submit <button> in the form
        self.one(frm['button[type=submit]'])

        # Test the <article class="instructions>
        art = frm['article.instructions'].only

        # We should have a <meta> to set the browser's URL.
        meta = art['meta'].only

        expect = (
            'http://foo.net:8000/en/profiles'
            f'?id={per.id.hex}&crud=update'
        )

        self.eq(expect, meta.content)

        self.true('set' in meta.classes)
        self.true('instruction' in meta.classes)

        # While we are here, make sure the test browser tab's URL wach
        # changesd to meta.content.
        self.eq(meta.content, str(tab.url))

    def it_navigates_to_entities_clicks_quick_edit_and_submits(self):
        """ Use the Quick Edit feature of a pom.crud page to get a form.
        Test submitting the form.
        """
        ws = foonet()
        tab = self.browser().tab()

        # Add some persons
        pers = persons()
        for i in range(3):
            per = person.getvalid()
            pers += per

        pers.save()

        # Get form
        tab.navigate('/en/profiles', ws)

        tbl = tab['main table'].only

        # Get a random person
        per = pers.getrandom()

        # Get the <tr> from the first person created above
        sels = f'tr[data-entity-id="{per.id.hex}"]'
        tr = tbl[sels].only

        # Get Quick Edit anchor
        a = tr['a[rel~=edit][rel~=preview]'].only

        # Click "Quick Edit" to get <form>
        res = self.click(a, tab)
        self.h200(res)

        # Obtain the <tr> again
        tr = tbl[sels].only

        # Get <form>
        frm = tr['td form'].only
        id = frm.getvalue('id')

        name = uuid4().hex
        frm.setvalue('name', name)

        res = self.submit(frm, tab)
        
        # Obtain the <tr> again
        tr = tbl[sels].only

        # The form will have been replaced with the regular, read-only
        # collection of <td>s and the <menu>
        self.zero(tr['td form'])
        self.one(tr['td menu'])

        # Get the <td> with the person' name. It should be updated to
        # what we set it to in the <form>.
        name1 = tr['td[data-entity-attribute=name]'].only.text

        self.eq(name, name1)

        # The name change would have made it to the database, so reload
        # the entity and assert
        self.eq(name, per.orm.reloaded().name)

    def it_navigates_to_entities_clicks_edit_and_submits(self):
        """ Use the Edit feature of a pom.crud page goto the detail
        page. Test submitting the form on the detail page. Test editing
        form and clicking the Cancel button as well.
        """
        ws = foonet()
        tab = self.browser().tab()

        # Add some persons
        pers = persons()
        for i in range(3):
            per = person.getvalid()
            pers += per

        pers.save()

        # Get form
        tab.navigate('/en/profiles', ws)

        tbl = tab['main table'].only

        # Get a random person
        per = pers.getrandom()

        # Get the <tr> from the first person created above
        sels = f'tr[data-entity-id="{per.id.hex}"]'
        tr = tbl[sels].only

        # Get Edit anchor
        a = tr['a[rel~=edit]:not([rel~=preview])'].only

        # Click "Edit" go to the detail page
        res = self.click(a, tab)
        self.h200(res)

        # Get <main> from the detail page
        main = tab['main'].only

        # Assert its attributes
        self.eq('/profile', main.getattr('data-path'))
        self.none(main.getattr('spa-data-path'))

        # Assert the <form>'s attributes
        frm = main['form'].only
        self.endswith('.person', frm.getattr('data-entity'))
        self.eq('#' + frm.id, frm.getattr('data-submit-fragments'))

        # Set the name <input> in the <form> to a random value
        name = uuid4().hex
        frm.setvalue('name', name)

        # Submit the <form>. This will "redirect" us (so to speak) back
        # to the main, tabular pagen /profiles.
        res = self.submit(frm, tab)

        # Get the main page's <main> element
        main = tab['main'].only

        # Assert it's attributes
        self.eq('/profiles', main.getattr('data-path'))
        self.none(main.getattr('spa-data-path'))

        # Assert the tables's attributes
        tbl = main['table'].only
        self.endswith('.person', tbl.getattr('data-entity'))

        # Test the <tr> related to the name we updated
        for tr in tbl['tbody tr']:
            if tr.getattr('data-entity-id') != per.id.hex:
                continue

            # Get the "id" <td> to make sure all of its attributes are
            # correct
            td = tr['td[data-entity-attribute=id]'].only

            # Get the Quick Edit anchor
            a = td['menu li a[rel~=edit][rel~=preview]'].only
            self.eq('Quick Edit', a.text)

            # We expect the rel attribute for the Quick Edit anchor to
            # have 'edit' and 'preview'
            rels = a.getattr('rel').split()
            self.two(rels)
            self.in_(rels, 'edit')
            self.in_(rels, 'preview')

            self.eq('/en/profiles', a.href)

            # Get the Edit anchor
            a = td['menu li a[rel~=edit]:not([rel~=preview])'].only

            self.eq('Edit', a.text)

            # We expect the rel attribute for the Edit anchor to
            # only have 'edit'
            self.eq('edit', a.getattr('rel'))

            expect = (
                f'/en/profile?id={per.id.hex}'
                '&crud=update&oncomplete=/profiles'
            )
            self.eq(expect, a.href)

            # Get the "name" <td>
            td = tr['td[data-entity-attribute=name]'].only

            # Finally, make sure the new name value is in the <tr>
            self.eq(name, td.text)

            # TODO Test the anchor's data-click-handler and
            # data-click-fragments="#x8nMAagjHTRKQDSklK82fSQ"
            # attributes.

        # Make sure the name was updated in the database
        self.eq(name, per.orm.reloaded().name)

Favicon = '''
AAABAAIAEBAAAAEAIABoBAAAJgAAACAgAAABACAAqBAAAI4EAAAoAAAAEAAAACAAAAABACAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADZqDwg2ag8uAAAAAAAA
AAAAAAAAAAAAAAAAAAA2ag84AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA2ag9S
NmoP5jZqDxo2ag8CNmoPGAAAAAA2ag9sNmoP5DZqDwQAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAANmoPfjZqD/82ag+yNmoPODZqD3A2ag8yNmoP+DZqD/w2ag8UAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAADZqD1g2ag/8NmoPcDZqD/I2ag//NmoPsjZqD642ag/qNmoPBAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA2ag8QNmoPgDZqD3w2ag//NmoP/zZqD+42ag82
NmoPeAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADZqD5Q2ag+WNmoPujZq
D9A2ag94NmoP6jZqDzAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADZqDz42ag/8
NmoPqDZqD442ag+mNmoPaDZqD/Y2ag/MNmoPBgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAA2ag+CNmoPqjZqD3g2ag//NmoP/zZqD942ag9yNmoPrDZqDzoAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAA2ag9UNmoP3DZqD9g2ag9wNmoP/zZqD/82ag/KNmoPlDZqD9o2ag/MNmoPCgAA
AAAAAAAAAAAAAAAAAAAAAAAANmoPOjZqD/Q2ag//NmoPtjZqD3g2ag+aNmoPXjZqD/w2ag//
NmoPvjZqDwgAAAAAAAAAAAAAAAA2ag8oNmoPhjZqD4Q2ag9oNmoP7DZqD342ag/iNmoP9jZq
D5A2ag/UNmoPuDZqD2o2ag+ENmoPcAAAAAAAAAAANmoPBDZqD5w2ag//NmoP7jZqD3Y2ag9y
NmoP+DZqD/82ag/iNmoPQjZqD6g2ag//NmoP7DZqDzwAAAAAAAAAAAAAAAAAAAAANmoPRjZq
D5Q2ag9wNmoPFjZqD4I2ag+ANmoPXjZqDyI2ag+YNmoPeDZqDxgAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAADZqDy42ag//NmoP/zZqD7gAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA2ag8GNmoP2DZqD/82ag9qAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADZqDxg2ag9KAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAP//AAD77wAA+c8AAPoPAAD6PwAA+F8AAPhPAADyLwAA
8gcAAPFHAADKCwAAxiMAAPZvAAD+PwAA/n8AAP//AAAoAAAAIAAAAEAAAAABACAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAA2ag8eNmoPqDZqDwwAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAANmoPnjZqDz4AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADZqD342ag//NmoPngAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADZqD3Q2ag//NmoPrAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAANmoPxDZqD/82ag//NmoPYgAAAAAAAAAANmoPAjZqD1A2ag8MAAAAAAAAAAA2ag88
NmoP+jZqD/82ag/mNmoPDAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAADZqDxA2ag/sNmoP/zZqD/82ag/2NmoPQAAAAAAAAAAA
NmoPSDZqDwwAAAAANmoPJjZqD+Q2ag//NmoP/zZqD/o2ag8oAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAANmoPEDZqD+o2ag//
NmoP/zZqD/82ag+QNmoPJDZqD7g2ag+yNmoPujZqD0I2ag9gNmoP/zZqD/82ag//NmoP+jZq
DygAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAA2ag8CNmoPyjZqD/82ag//NmoP1jZqDxo2ag/KNmoP/zZqD/82ag//NmoP5jZq
DyA2ag+yNmoP/zZqD/82ag/qNmoPDgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA2ag+QNmoP/zZqD/I2ag80NmoPmjZq
D/82ag//NmoP/zZqD/82ag//NmoPwDZqDyY2ag/eNmoP/zZqD7wAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADZq
Dzg2ag//NmoPYjZqDxQ2ag//NmoP/zZqD/82ag//NmoP/zZqD/82ag//NmoPNDZqDzQ2ag//
NmoPYgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAANmoPBDZqD2o2ag80NmoPNDZqD6Q2ag//NmoP/zZqD/82ag//
NmoP/zZqD7g2ag8wNmoPQDZqD2Q2ag8WAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADZqD9I2ag/Q
NmoPIDZqD/A2ag//NmoP/zZqD/82ag/6NmoPKDZqD7o2ag/wNmoPEgAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAA2ag+ANmoP/zZqD/82ag9qNmoPVDZqD6A2ag+gNmoPoDZqD2I2ag9WNmoP/zZq
D/82ag+qAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAANmoPLjZqD/Y2ag//NmoP/zZqD5o2ag8aNmoPTjZq
D042ag9ONmoPHjZqD4I2ag//NmoP/zZqD/82ag9SAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADZqDwQ2ag/CNmoP/zZq
D/82ag/mNmoPIDZqD9A2ag//NmoP/zZqD/82ag/cNmoPHjZqD9o2ag//NmoP/zZqD+A2ag8S
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAANmoPajZqD/82ag//NmoP/zZqD2I2ag9oNmoP/zZqD/82ag//NmoP/zZqD/82ag9+
NmoPTDZqD/82ag//NmoP/zZqD5QAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA2ag9CNmoPWjZqD1o2ag9SNmoPHjZqD/I2ag//
NmoP/zZqD/82ag//NmoP/zZqD/g2ag8sNmoPUDZqD1o2ag9aNmoPUAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAANmoPYDZqD7o2ag+0
NmoPtDZqD6w2ag8mNmoPzDZqD/82ag//NmoP/zZqD/82ag//NmoP2jZqDyY2ag+oNmoPtDZq
D7Q2ag+4NmoPgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAADZqDww2ag/gNmoP/zZqD/82ag//NmoP/zZqD5I2ag86NmoP/zZqD/82ag//NmoP/zZq
D/82ag9MNmoPfjZqD/82ag//NmoP/zZqD/82ag/6NmoPIgAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAANmoPCjZqD8Q2ag//NmoP/zZqD/82ag//NmoP/DZq
Dzg2ag+eNmoP8DZqD/A2ag/wNmoPrjZqDy42ag/0NmoP/zZqD/82ag//NmoP/zZqD+I2ag8a
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAANmoPFjZq
D9Q2ag//NmoP/zZqD/82ag//NmoPojZqDw42ag9ENmoPQjZqD0Q2ag8SNmoPiDZqD/82ag//
NmoP/zZqD/82ag/qNmoPLgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADZq
Dxg2ag8YNmoPGDZqDxg2ag8SNmoPHjZqD9I2ag//NmoP/zZqD/g2ag80NmoPoDZqD+w2ag/s
NmoP7DZqD7I2ag8mNmoP7jZqD/82ag//NmoP6jZqDzY2ag8QNmoPGDZqDxg2ag8YNmoPGgAA
AAAAAAAAAAAAAAAAAAAAAAAANmoPgjZqD/g2ag/wNmoP8DZqD/A2ag+SNmoPHDZqD7Q2ag//
NmoPgjZqD0Y2ag//NmoP/zZqD/82ag//NmoP/zZqD2Q2ag9gNmoP/zZqD842ag8oNmoPbjZq
D+42ag/wNmoP8DZqD/Y2ag+UAAAAAAAAAAAAAAAAAAAAAAAAAAA2ag8MNmoPvDZqD/82ag//
NmoP/zZqD/82ag++NmoPKjZqD1I2ag8qNmoP7jZqD/82ag//NmoP/zZqD/82ag//NmoP/zZq
Dzg2ag9WNmoPJDZqD6A2ag//NmoP/zZqD/82ag//NmoPyjZqDxIAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAA2ag8ONmoPpjZqD/82ag//NmoP/zZqD/82ag/uNmoPbDZqDxg2ag+SNmoP4jZq
D/82ag//NmoP/zZqD+w2ag+gNmoPKDZqD1I2ag/cNmoP/zZqD/82ag//NmoP/zZqD7Q2ag8U
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAANmoPVjZqD7w2ag/2NmoP/zZq
D/82ag+UNmoPBgAAAAA2ag8sNmoPTDZqD4A2ag9YNmoPLjZqDwYAAAAANmoPhDZqD/w2ag//
NmoP9jZqD8Q2ag9gAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAADZqDyI2ag86NmoPLAAAAAAAAAAANmoPUjZqD+Q2ag+qNmoPhDZqD6A2ag/c
NmoPaAAAAAAAAAAANmoPKDZqDzw2ag8kAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA2ag9o
NmoP/zZqD/82ag//NmoP/zZqD/82ag92AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAADZqD1A2ag//NmoP/zZqD/82ag//NmoP/zZqD2gAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAANmoPGDZqD/A2ag//NmoP/zZq
D/82ag/6NmoPKAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAANmoPcDZqD/82ag//NmoP/zZqD4QAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAANmoPYDZqD7g2ag9sAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAP//////3/3//8/8//+P+P//h/D//4Iw//+EEP//iAj//9gN///4D///5BP/
/8Yx///D4f//hBD//4wYf//4D///CAg//gQYP/4EED//A+B//4QQ/+BEGYPwOA4H+BgMD/4P
eD///B////wf///8H////B////4f////f///////
'''

GoogleFavicon = '''
AAABAAIAEBAAAAEAIABoBAAAJgAAACAgAAABACAAqBAAAI4EAAAoAAAAEAAAACAAAAABACAAAAAA
AAAEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAP///zD9/f2W/f392P39/fn9/f35
/f391/39/ZT+/v4uAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA/v7+Cf39/Zn/////////////////
//////////////////////////39/ZX///8IAAAAAAAAAAAAAAAA/v7+Cf39/cH/////+v35/7TZ
p/92ul3/WKs6/1iqOv9yuFn/rNWd//j79v///////f39v////wgAAAAAAAAAAP39/Zn/////7PXp
/3G3WP9TqDT/U6g0/1OoNP9TqDT/U6g0/1OoNP+Or1j//vDo///////9/f2VAAAAAP///zD/////
+vz5/3G3V/9TqDT/WKo6/6LQkf/U6cz/1urO/6rUm/+Zo0r/8IZB//adZ////v7///////7+/i79
/f2Y/////4nWzf9Lqkj/Vqo4/9Xqzv///////////////////////ebY//SHRv/0hUL//NjD////
///9/f2U/f392v////8sxPH/Ebzt/43RsP/////////////////////////////////4roL/9IVC
//i1jf///////f391/39/fr/////Cr37/wW8+/+16/7/////////////////9IVC//SFQv/0hUL/
9IVC//SFQv/3pnX///////39/fn9/f36/////wu++/8FvPv/tuz+//////////////////SFQv/0
hUL/9IVC//SFQv/0hUL/96p7///////9/f35/f392/////81yfz/CrL5/2uk9v//////////////
/////////////////////////////////////////f392P39/Zn/////ks/7/zdS7P84Rur/0NT6
///////////////////////9/f////////////////////////39/Zb+/v4y//////n5/v9WYu3/
NUPq/ztJ6/+VnPT/z9L6/9HU+v+WnfT/Ul7t/+Hj/P////////////////////8wAAAAAP39/Z3/
////6Or9/1hj7v81Q+r/NUPq/zVD6v81Q+r/NUPq/zVD6v9sdvD////////////9/f2YAAAAAAAA
AAD///8K/f39w//////5+f7/paz2/11p7v88Suv/Okfq/1pm7v+iqfX/+fn+///////9/f3B/v7+
CQAAAAAAAAAAAAAAAP///wr9/f2d///////////////////////////////////////////9/f2Z
/v7+CQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAP7+/jL9/f2Z/f392/39/fr9/f36/f392v39/Zj/
//8wAAAAAAAAAAAAAAAAAAAAAPAPAADAAwAAgAEAAIABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAIABAACAAQAAwAMAAPAPAAAoAAAAIAAAAEAAAAABACAAAAAAAAAQAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAP7+/g3+/v5X
/f39mf39/cj9/f3q/f39+f39/fn9/f3q/f39yP39/Zn+/v5W////DAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAP7+
/iT9/f2c/f399f/////////////////////////////////////////////////////9/f31/f39
mv7+/iMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAP7+/gn9/f2K/f39+///////////////////////////////////////////////////////
/////////////////////f39+v39/Yf///8IAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAD+/v4k/f390v//////////////////////////////////////////////
//////////////////////////////////////////////////39/dD///8iAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA////MP39/er//////////////////////////+r05v+v
16H/gsBs/2WxSf9Wqjj/Vqk3/2OwRv99vWX/pdKV/97u2P////////////////////////////39
/ej+/v4vAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAP7+/iT9/f3q////////////////////
/+v15/+Pxnv/VKk2/1OoNP9TqDT/U6g0/1OoNP9TqDT/U6g0/1OoNP9TqDT/U6g0/36+Z//d7tf/
//////////////////////39/ej///8iAAAAAAAAAAAAAAAAAAAAAAAAAAD///8K/f390///////
///////////////E4bn/XKw+/1OoNP9TqDT/U6g0/1OoNP9TqDT/U6g0/1OoNP9TqDT/U6g0/1Oo
NP9TqDT/U6g0/1apN/+x0pv///////////////////////39/dD///8IAAAAAAAAAAAAAAAAAAAA
AP39/Yv/////////////////////sdij/1OoNP9TqDT/U6g0/1OoNP9TqDT/U6g0/1OoNP9TqDT/
U6g0/1OoNP9TqDT/U6g0/1OoNP9TqDT/YKU1/8qOPv/5wZ////////////////////////39/YcA
AAAAAAAAAAAAAAD+/v4l/f39+////////////////8Lgt/9TqDT/U6g0/1OoNP9TqDT/U6g0/1Oo
NP9utlT/n86N/7faqv+426v/pdKV/3u8ZP9UqDX/U6g0/3egN//jiUH/9IVC//SFQv/82MP/////
/////////////f39+v7+/iMAAAAAAAAAAP39/Z3////////////////q9Ob/W6w+/1OoNP9TqDT/
U6g0/1OoNP9nskz/zOXC/////////////////////////////////+Dv2v+osWP/8YVC//SFQv/0
hUL/9IVC//WQVP/++fb//////////////////f39mgAAAAD+/v4O/f399v///////////////4LH
j/9TqDT/U6g0/1OoNP9TqDT/dblc//L58P//////////////////////////////////////////
///8+v/3p3f/9IVC//SFQv/0hUL/9IVC//rIqf/////////////////9/f31////DP7+/ln/////
///////////f9v7/Cbz2/zOwhv9TqDT/U6g0/2KwRv/v9+z/////////////////////////////
//////////////////////////738//1kFT/9IVC//SFQv/0hUL/9plg////////////////////
///+/v5W/f39nP///////////////4jf/f8FvPv/Bbz7/yG1s/9QqDz/vN2w////////////////
//////////////////////////////////////////////////rHqP/0hUL/9IVC//SFQv/0hUL/
/vDn//////////////////39/Zn9/f3L////////////////R878/wW8+/8FvPv/Bbz7/y7C5P/7
/fr//////////////////////////////////////////////////////////////////ere//SF
Qv/0hUL/9IVC//SFQv/718H//////////////////f39yP39/ez///////////////8cwvv/Bbz7
/wW8+/8FvPv/WNL8///////////////////////////////////////0hUL/9IVC//SFQv/0hUL/
9IVC//SFQv/0hUL/9IVC//SFQv/0hUL/9IVC//rIqv/////////////////9/f3q/f39+v//////
/////////we9+/8FvPv/Bbz7/wW8+/993P3///////////////////////////////////////SF
Qv/0hUL/9IVC//SFQv/0hUL/9IVC//SFQv/0hUL/9IVC//SFQv/0hUL/+cGf////////////////
//39/fn9/f36////////////////B737/wW8+/8FvPv/Bbz7/33c/f//////////////////////
////////////////9IVC//SFQv/0hUL/9IVC//SFQv/0hUL/9IVC//SFQv/0hUL/9IVC//SFQv/6
xaX//////////////////f39+f39/e3///////////////8cwvv/Bbz7/wW8+/8FvPv/WdP8////
///////////////////////////////////0hUL/9IVC//SFQv/0hUL/9IVC//SFQv/0hUL/9IVC
//SFQv/0hUL/9IVC//vVv//////////////////9/f3q/f39y////////////////0bN/P8FvPv/
Bbz7/wW8+/8hrvn/+/v/////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////39/cj9/f2c////////
////////ht/9/wW8+/8FvPv/FZP1/zRJ6/+zuPf/////////////////////////////////////
////////////////////////////////////////////////////////////////////////////
/f39mf7+/lr////////////////d9v7/B7n7/yB38f81Q+r/NUPq/0hV7P/u8P3/////////////
////////////////////////////////////////////////////////////////////////////
///////////////////+/v5X////D/39/ff///////////////9tkPT/NUPq/zVD6v81Q+r/NUPq
/2Fs7//y8v7////////////////////////////////////////////09f7/////////////////
/////////////////////////////////f399f7+/g0AAAAA/f39n////////////////+Tm/P89
Suv/NUPq/zVD6v81Q+r/NUPq/1Bc7f/IzPn/////////////////////////////////x8v5/0xY
7P+MlPP////////////////////////////////////////////9/f2cAAAAAAAAAAD+/v4n/f39
/P///////////////7W69/81Q+r/NUPq/zVD6v81Q+r/NUPq/zVD6v9ZZe7/k5v0/6609/+vtff/
lJv0/1pm7v81Q+r/NUPq/zVD6v+GjvL//v7//////////////////////////////f39+/7+/iQA
AAAAAAAAAAAAAAD9/f2N/////////////////////6Cn9f81Q+r/NUPq/zVD6v81Q+r/NUPq/zVD
6v81Q+r/NUPq/zVD6v81Q+r/NUPq/zVD6v81Q+r/NUPq/zVD6v+BivL/////////////////////
///////9/f2KAAAAAAAAAAAAAAAAAAAAAP7+/gv9/f3V/////////////////////7W69/8+S+v/
NUPq/zVD6v81Q+r/NUPq/zVD6v81Q+r/NUPq/zVD6v81Q+r/NUPq/zVD6v81Q+r/P0zr/7q/+P//
/////////////////////f390v7+/gkAAAAAAAAAAAAAAAAAAAAAAAAAAP7+/ib9/f3r////////
/////////////+Xn/P94gfH/NkTq/zVD6v81Q+r/NUPq/zVD6v81Q+r/NUPq/zVD6v81Q+r/NkTq
/3Z/8f/l5/z///////////////////////39/er+/v4kAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAP7+/jL9/f3r///////////////////////////k5vz/nqX1/2p08P9IVez/OEbq/zdF6v9G
U+z/aHLv/5qh9f/i5Pz////////////////////////////9/f3q////MAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAP7+/ib9/f3V////////////////////////////////////
/////////////////////////////////////////////////////////////f390v7+/iQAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAP///wr9/f2N/f39/P//////
/////////////////////////////////////////////////////////////////////f39+/39
/Yv+/v4JAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAD+/v4n/f39n/39/ff/////////////////////////////////////////////////////
/f399v39/Z3+/v4lAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA/v7+Dv7+/lr9/f2c/f39y/39/e39/f36/f39+v39
/ez9/f3L/f39nP7+/ln+/v4OAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AP/AA///AAD//AAAP/gAAB/wAAAP4AAAB8AAAAPAAAADgAAAAYAAAAEAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACAAAABgAAAAcAAAAPAAAAD4AAAB/AAAA/4
AAAf/AAAP/8AAP//wAP/
'''
if __name__ == '__main__':
    tester.cli().run()
