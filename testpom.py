#!/usr/bin/python3
import apriori; apriori.model()

from datetime import timezone, datetime, date
from contextlib import suppress
from dbg import B
from func import enumerate, getattr
from uuid import uuid4, UUID
import auth
import asset
import dom
import ecommerce
import logs
import os
import file
import orm
import party
import pom
import primative
import pytz
import tester
import www

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
        self.pages += about()
        self.pages += contact_us()
        self.pages += blogs()
        self.pages += admin()

        ''' Error pages '''
        pgs = self.pages['/en/error'].pages
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

        ''' Footer  '''

    @property
    def _adminmenu(self):
        mnu = pom.menu('admin')
        mnu.items += pom.menu.item('Users')

        mnu.items.last.items \
            += pom.menu.item(self['/en/admin/users/statistics'])

        mnu.items += pom.menu.item('Reports')

        rpt = mnu.items.last

        pg = self['/en/admin/reports/netsales']

        rpt.items += pom.menu.item(pg)

        rpt.seperate()

        pg = self['/en/admin/reports/accountsummary']
        rpt.items += pom.menu.item(pg)

        return mnu

class pom_menu_item(tester.tester):
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

class _404(pom.page):
    def main(self, ex: www.NotFoundError):
        self.title = 'Page Not Found'
        self.main += dom.h1('Page Not Found')
        self.main += dom.h2('Foobar apologizes', class_="apology")

        self.main += dom.paragraph('''
        Could not find <span class="resource">%s</span>
        ''', ex.resource)

    @property
    def name(self):
        return type(self).__name__.replace('_', '')

class pom_menu_items(tester.tester):
    def __init__(self, *args, **kwargs):
        mods = 'party', 'asset', 'apriori', '__main__', 'testpom', 'pom', 'file'
        super().__init__(mods=mods, *args, **kwargs)

        propr = foonet.Proprietor
        with orm.sudo(), orm.proprietor(propr):
            propr.owner = ecommerce.users.root
            
        orm.security().proprietor = foonet.Proprietor

        # Unconditionally recreate foonet's tables and supers
        foonet.orm.recreate(ascend=True)


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
        mnu = pom.menu('main')
        main = ws.header.menus['main']
        mnu.items += main.items

        self.eq(main.pretty,        main.pretty)
        self.eq(mnu.pretty,         mnu.pretty)
        self.eq(main.html,          main.html)
        self.eq(mnu.html,           mnu.html)
        self.eq(main.items.pretty,  main.items.pretty)
        self.eq(mnu.items.pretty,   mnu.items.pretty)
        self.eq(main.items.html,    main.items.html)
        self.eq(mnu.items.html,     mnu.items.html)

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

        itms.first.items += pom.menu.item('A/A')
        itms.first.items += pom.menu.item('A/B')

        itms.second.items += pom.menu.item('B/A')
        itms.second.items += pom.menu.item('B/B')

        ids = (
            itms._ul.id,
            itms.first.id,
            itms.first.items._ul.id,
            itms.first.items.first.id,
            itms.first.items.second.id,
            itms.second.id,
            itms.second.items._ul.id,
            itms.second.items.first.id,
            itms.second.items.second.id,
        )
        ids = tuple(
            [itms._ul.id] + \
            [x.id for x in itms.all if type(x) is not dom.text]
        )
        
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

class site(tester.tester):
    def __init__(self, *args, **kwargs):
        mods = 'party', 'apriori'
        super().__init__(mods=mods, *args, **kwargs)

        orm.security().override = True
    
    def it_calls__init__(self):
        ws = foonet()
        self.six(ws.pages)

    def it_appends_menu_items(self):
        ws = foonet()
        mnu = pom.menu('main')
        main = ws.header.menus['main']
        mnu.items += main.items

        uls = dom.html(mnu.items.html)['ul>li']
        self.count(17, uls)

        self.eq(main.items.html, mnu.items.html)
        self.eq(main.items.pretty, mnu.items.pretty)
        
    def it_calls__repr__(self):
        self.eq('site()', repr(pom.site()))
        self.eq('site()', str(pom.site()))

        self.eq('foonet()', repr(foonet()))
        self.eq('foonet()', str(foonet()))
        
    def it_calls__getitem__(self):
        ws = foonet()
        for path in ('/', '', '/en/index'):
            self.type(home, ws[path])

        self.type(about, ws['/en/about'])
        self.type(about_team, ws['/en/about/team'])

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
        mnu = mnus['admin']
        self.two(mnu.items)

        rpt = mnu.items.second
        self.type(pom.menu.item, rpt.items.first)
        self.type(pom.menu.separator, rpt.items.second)
        self.type(pom.menu.item, rpt.items.third)

    def it_menu_has_aria_attributes(self):
        ws = foonet()

        navs = ws.header['nav']
        self.two(navs)

        self.one(navs['[aria-label=Admin]'])
        self.one(navs['[aria-label=Main]'])

    def it_calls_main_menu(self):
        ws = pom.site()
        mnu = ws.header.menu
        self.zero(mnu.items)

        ws = foonet()
        mnu = ws.header.menu
        self.five(mnu.items)

        self.eq(
            ['/index', '/about', '/contact-us', '/blogs', '/admin'],
            mnu.items.pluck('page.path')
        )

        self.eq(
            [home, about, contact_us, blogs, admin],
            [type(x) for x in  mnu.items.pluck('page')]
        )

        blg = mnu.items.penultimate
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
        mnu = ws.header.menu
        self.five(mnu.items)

        # blogs item
        itm = mnu.items.fourth

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
        self.six(mnu.items)

        sels = dom.selectors('li')
        self.true('My Profile' in (x.text for x in mnu[sels]))
        self.true('My Profile' in (x.text for x in ws.header[sels]))

        ''' Delete the blogs munu '''
        sels = dom.selectors('li > a[href="%s"]' % itm.page.path)
        self.one(ws.header[sels])
        self.one(mnu[sels])

        # Remove the blog menu
        itms = mnu.items.remove(mnu.items.fourth)
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

    def it_demands_contants_are_setup_on_site(self):
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

    def it_ensures(self):
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

        # Test foonet
        self.eq(ecommerce.users.RootUserId, ws.owner.id)
        self.eq(foonet.Proprietor.id, ws.proprietor.id)

        self.eq((False, False, False), ws.orm.persistencestate)
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

        aps = ws.asset_parties
        self.populated(aps)
        aps = aps.where(
            lambda x: x.asset_partystatustype.name == 'proprietor'
        )
        self.one(aps)

        # Test foonet's super: `site`
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
            propr.owner = ecommerce.users.root
            
        # Now we can call the constructor
        mods = 'party', 'ecommerce', 'pom', 'asset', 'apriori', 'file'
        super().__init__(mods=mods, propr=propr, *args, **kwargs)

        if self.rebuildtables:
            fastnets.orm.recreate()

        # Unconditionally recreate foonet's tables and supers
        foonet.orm.recreate(ascend=True)

        # Clear radix cache
        with suppress(AttributeError):
            del file.directory._radix

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
        self.isnot(ws.header.menu, pg.header.menu)

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
        self.ne('Statistics', ws.header.menu.items.last.text)

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
        pg = ws['/en/blogs']
        self.notnone(pg.site)

        self.isnot(pg.header,        ws.header)
        self.isnot(pg.header.menu,   ws.header.menu)
        self.isnot(pg.header.menus,  ws.header.menus)
        self.isnot(pg.head,          ws.head)

    def it_calls_site(self):
        ws = foonet(name='foo.net')
        self.is_(ws, ws['/en/blogs'].site)
        self.is_(ws, ws['/en/blogs/comments'].site)
        self.is_(ws, ws['/en/blogs/comments/rejected'].site)

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
                mnu.items += pom.menu.item('About stats')

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
        self.none(res.body)
        self.eq(200, res.status)

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
                self.main +=  dom.p('''
                    Query string from request: %s
                    ''', www.request.qs
                )

        ws = foonet()
        pg = time()
        ws.pages += pg
        
        tab = self.browser().tab()
        res = tab.get('/en/time?herp=derp', ws)

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

                if www.request.ispost:
                    frm.post = www.request.body

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

        pg = pour()
        ws.pages += pg
        tab = self.browser().tab()
        res = tab.get('/en/' + pg.path, ws)
        self.eq(418, res.status)
        mains = res['body>main[data-path="/error"]']

        self.one(mains)

        main = mains.first
        self.eq('418', main['.status'].first.text)

        self.four(main['article.traceback>div'])
        self.one(res['main[data-path="/error"]'])

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

        # Unconditionally recreate foonet's tables and supers
        foonet.orm.recreate(ascend=True)
        derpnet.orm.recreate(ascend=True)

        try:
            ws = derpnet()
            with orm.proprietor(ws.proprietor):
                tab = self.browser().tab()
                res = tab.get('/en' + '/index', ws)
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
                lang = www.request.language
                self.main += dom.p('''
                Lang: %s
                ''' % lang)

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
                global res
                # Create the login form
                frm = pom.forms.login()
                self.main += frm

                # If GET, then return; the rest is for POST
                if req.isget:
                    return

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
                usr = req.user
                jwt = req.cookies('jwt')

                if usr:
                    self.main += dom.p(jwt.value, class_='jwt')

                    self.main += dom.span(usr.name, class_='username')
                else:
                    raise www.UnauthorizedError(flash='Unauthorized')

        class logout(pom.page):
            def main(self):
                global res
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
            isauthentic =  not usr.orm.isnew
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
                req.hit.logs.write('Starting main')
                dev = req.hit.useragent.devicetype

                self.main += dom.p(f'''
                {dev.brand} {dev.name}
                ''', class_='device')

                req.hit.logs.write('Ending main')


        class signon(pom.page):
            def main(self):
                self.main += pom.forms.login()

                if req.isget:
                    return

                frm.post = req.body

                uid = frm['input[name=username]'].first.value
                pwd = frm['input[name=password]'].first.value

                req.hit.logs.write(f'Authenticating {uid}')
                try:
                    www.request.user = self.site.authenticate(uid, pwd)
                except pom.site.AuthenticationError:
                    req.hit.logs.write(f'Authenticated failed: {uid}')
                else:
                    req.hit.logs.write(f'Authenticated {uid}')

                    hdr = auth.jwt.getSet_Cookie(www.request.user)
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

        # NOTE The implicit variable `res` in the pages above collide
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
        # it ends up with one on completion of the request. The user that
        # gets authenticated should be set in the hit entity (hit.user)

        # Create user
        usr = ecommerce.user(
            name = 'luser',
            password = 'password1',
            site = ws,
        )

        usr.save()

        # Get user/password form
        res1 = tab.get('/en/signon', ws)
        frm = res1['form'].first

        # Set credentials
        frm['input[name=username]'].first.value = 'luser'
        frm['input[name=password]'].first.value = 'password1'

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

    def it_can_accesses_injected_variables(self):
        class lang(pom.page):
            def main(self):
                assert req is www.request
                assert res is www.response

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
        self.status(418, res)

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
        tab.navigate('/en/clickme', ws)

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
        tab.navigate('/en/clickme', ws)

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

        self.eq(tab.html.html, html)
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
        self.one(tab['main>.error-modal .message'])
        self.one(tab['main>.error-modal .traceback'])

    def it_replaces_correct_fragment(self):
        """ This was written due to a bug found in
        tester._browser._tab.element_event which incorrectly patched the
        DOM object. Instead of replacing the element in it's current
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
        tab.navigate('/en/clickme', ws)

        self.status(200, res)

        # Get the <button> from the response
        btn = tab.html['main>button'].only

        # Click the button. This will cause an XHR request back to the
        # page's btn_onclick event handler.
        btn.click()

        sec = tab['main>section'].only

        self.eq('I am changed', sec.elements.first.text)
        self.eq('I should remain unchanged', sec.elements.second.text)

    def it_patches_page_on_menu_click(self):
        class spa(pom.page):
            def main(self):
                self.main += dom.p('Welcome to the SPA')

        ws = foonet()
        ws.pages += spa()

        tab = self.browser().tab()

        tab.inspa = True

        # GET the clickme page
        tab.navigate('/en/spa', ws)
        attrs = tab.html['main'].only.attributes
        self.eq('/spa', attrs['data-path'].value)

        a_blog = tab['header>nav a[href|="/blogs"]'].only

        a_blog.click()
        attrs = tab.html['main'].only.attributes
        self.eq('/blogs', attrs['data-path'].value)

    def it_navigates_to_pages_when_spa_is_disabled(self):
        class spa(pom.page):
            def main(self):
                self.main += dom.p('Welcome to the SPA')

        ws = foonet()
        ws.pages += spa()

        tab = self.browser().tab()

        # GET the clickme page
        tab.navigate('/en/spa', ws)

        self.eq('foonet | Spa', tab.html['title'].only.text)

        a_blog = tab['header>nav a[href|="/blogs"]'].only

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

if __name__ == '__main__':
    tester.cli().run()
