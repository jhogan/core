#!/usr/bin/python3
# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2022

from base64 import b64decode
from datetime import timezone, datetime, date
from dbg import B, PM
from func import enumerate, getattr
from uuid import uuid4, UUID
import db
import dom
import ecommerce
import effort
import file
import party
import pom
import www

class sites(pom.sites):
    pass

class site(pom.site):
    Id = UUID(hex='c0784fca-3fe7-45e6-87f8-e2ebbc4e7bf4')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.host = 'carapacian.com'

        self.title = 'Carapacian Sustainable Software'

        self.pages += home()
        self.pages += tickets()
        self.pages += ticketsspa()

    @property
    def Proprietor(self):
        # TODO Originally this was a constant. However, this caused
        # problems when tests scripts would import this module because
        # the below code was executed on import which caused problems
        # because the ORM's caches were prematurly filled. The current
        # solution works fine, but we should have a rethink about the
        # way proprietor's are associated with `site` classes.
        return party.companies.carapacian

    @property
    def favicon(self):
        r = file.file()
        r.name = 'favicon.ico'
        r.body = b64decode(Favicon)
        return r

    @property
    def styles(self):
        """ Return the CSS for this site. 
        """
        # The Css constant is defined at the bottom of this source file.
        return Css

    @property
    def head(self):
        if not self._head:
            hd = super().head
            hd += dom.meta(
                name = 'keywords', 
                content = 'lorem ipsum dolor sit amet'
            )

            hd += dom.meta(
                name = 'description', 
                content = 'Interdum et malesuada fames ac ante ipsum'
            )

        return self._head

    @property
    def header(self):
        hdr = super().header

        # FIXME Add logo
        '''
        hdr.logo = pom.logo(
            'Carapacian Logo',
            href = 'https://carapacian.com',
            img  = 'https://carapacian.com/images/logo.png',
        )
        '''

        hdr.menu = pom.menu(name='main')

        itms = hdr.menu.items
        itms += pom.menu.item('Services', '/services')
        itms += pom.menu.item('Products', '/products')
        itms += pom.menu.item('Tickets', '/tickets')
        itms += pom.menu.item('Tickets Spa', '/ticketsspa')

        return hdr

class home(pom.page):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
            
    def main(self):
        ''' <header> '''
        hdr = dom.header()

        span = dom.span('Nam elit ipsum, lobortis')
        span += dom.br()
        span += dom.text('ac interdum ac')

        hdr += span

        self.main += hdr

        ''' Introduction '''
        self.main += dom.section(
            id = 'introductory-section',
            body = dom.markdown('''
            Dolor sit amet
            --------------

            Lorem ipsum dolor sit amet, consectetur adipiscing elit. Ut
            maximus metus eget semper bibendum. Praesent convallis
            condimentum leo at maximus. Praesent posuere tincidunt sem,
            a porta sem vulputate interdum. Maecenas nec velit
            malesuada, fermentum nunc vitae, mollis magna. Sed suscipit
            lectus sit amet diam volutpat facilisis eget id diam. Cras
            quis velit bibendum, convallis lacus nec, ornare tortor. Nam
            porttitor, enim ut laoreet fermentum, enim ipsum tempor
            tellus, eget laoreet mi arcu eu velit. Phasellus tempor sit
            amet arcu eu finibus. Nunc non libero nec urna venenatis
            mollis nec ut lacus. Donec ut faucibus elit. Donec in justo
            quis sem congue rhoncus. Maecenas a efficitur ligula, nec
            volutpat erat. Maecenas feugiat ultrices dolor a mattis.

            Quisque nisl dui, elementum nec consectetur vel, elementum
            vel sem. Orci varius natoque penatibus et magnis dis
            parturient montes, nascetur ridiculus mus. Donec ut sodales
            nulla, in imperdiet massa. Nullam egestas euismod augue, eu
            aliquam ante facilisis vitae. Sed ultricies, nunc et feugiat
            auctor, risus velit faucibus risus, id tincidunt orci risus
            a augue. Ut lobortis neque id nisl eleifend, eu euismod
            magna viverra. Suspendisse magna leo, gravida ac dapibus at,
            pellentesque nec diam. Ut rhoncus nulla quam, in ullamcorper
            enim feugiat a. Integer accumsan dictum nunc et rhoncus. Ut
            vehicula justo non interdum rutrum. Ut in placerat metus.
            ''')
        )

        ''' Products '''
        self.main += dom.section(
            id = 'products-section',
            body = dom.markdown('''
            Donec mollis
            ------------

            ## In justo tortor ##

            Donec mollis ut urna sed porta. In justo tortor, ornare
            luctus purus et, scelerisque varius nibh. Proin diam orci,
            vulputate sit amet gravida a, finibus quis sapien. Duis
            dictum pellentesque ipsum et euismod. Mauris sit amet nisl
            quis nisl lacinia facilisis sed sed dui. Nunc molestie justo
            ut viverra semper. Curabitur ac quam nec elit lacinia
            sollicitudin sed in nulla. Donec nec consectetur ante, quis
            hendrerit odio. Sed arcu mi, venenatis nec congue id,
            dapibus eget odio. Suspendisse potenti.

            ## Integer porta dignissim ##

            Ut a mauris nec justo mattis malesuada. Integer porta
            dignissim ligula vel feugiat. Nam elit ipsum, lobortis ac
            interdum ac, elementum ac turpis. Integer vehicula sem
            justo. Sed ultricies dignissim ante vel aliquam. In vitae
            urna odio. Sed eleifend, quam quis ultrices pharetra, tortor
            lacus bibendum metus, a finibus mi sem at erat. Curabitur
            dolor nisi, tempus id libero euismod, aliquet dapibus
            tellus. Morbi ipsum massa, vestibulum sed augue et, varius
            ornare sapien. Integer suscipit erat at bibendum mollis.
            Donec feugiat turpis vitae ex tincidunt condimentum. Aliquam
            blandit volutpat arcu quis tempor. Sed fermentum sagittis
            nunc, at maximus ipsum porta vel. Nam mollis magna viverra
            pharetra faucibus.

            * Vestibulum vel felis 
            * Nec lectus varius varius
            * Ultricies a pellentesque 
            * Dignissim, vulputate rhoncus 
            * Vitae interdum accumsan 
            * Pharetra libero, eget auctor 
            * Ipsum ligula ut 
            * Duis eget purus sed leo 
            * Hendrerit dignissim in eu mauris
            * Quisque justo quam
            ''')
        )

        ''' Contact us '''
        self.main += dom.section(
            id = 'contact-us',
            body = dom.markdown('''
            Mauris eleifend
            ---------------

            <a href="mailto:nnbhquam@carapacian.com">
                Mauris eleifend
            </a> pellentesque ac nibh quam. Mauris eleifend commodo iaculis.
            Suspendisse eros risus, finibus nec nulla a, fermentum
            vehicula arcu. Maecenas rutrum sapien magna, at euismod nisl
            dapibus vitae. 
            ''')
        )

        ''' Footer '''
        self.main += dom.footer(dom.p('Maecenas Rutrum, LLC © 2021'))

    @property
    def name(self):
        return 'index'

class tickets(pom.page):
    def main(self):
        self.main += dom.p('Carapacian Tickets')

        ''' Two widgets; one handler; one fragment '''
        div = dom.div(class_='test1')
        btn1 = dom.button('Clickme One')
        btn2 = dom.button('Clickme Two')
        p = dom.p()
        p1 = dom.p()

        btn1.onclick += self.btnclicker_onclick, p
        btn2.onclick += self.btnclicker_onclick, p1

        div += btn1, btn2, p, p1
        self.main += div


        ''' No fragment '''
        btn3 = dom.button('No fragments')
        btn3.onclick += self.btnclicker_onclick2
        self.main += dom.hr(), btn3

        ''' Multiple fragments'''
        btn4 = dom.button('Multiple fragments')
        hello = dom.code('Hello,')
        world = dom.code('World')
        p = dom.p()
        btn4.onclick += self.btnclicker_onclick4, hello, world, p
        self.main += (
            dom.hr(), btn4, dom.br(), hello, dom.span(' + '), world, p
        )

        ''' Exception '''
        btn5 = dom.button('Exception')
        btn5.onclick += self.btnclicker_onclick5
        self.main += (
            dom.hr(), btn5
        )

        ''' Different events '''
        span = dom.span()
        lbl = dom.label('Input: ')
        inp = dom.input()
        inp.oninput += self.inp_oninput, span
        self.main += dom.hr(), span, dom.br(), lbl, inp

        ''' Multiple handlers'''
        # This probably shouldn't work because it would mean multiple
        # XHR call, or extra routing logic on the server-side. That
        # could be implemented, of course, but having multiple handlers
        # for one event seems like a bad idea, so we probably shouldn't
        # go out of our way to encourage it.
        #span = dom.span()
        #span1 = dom.span()
        #lbl = dom.label('Encode: ')
        #inp = dom.input()
        #inp.oninput += self.inp_oninput1, span
        #inp.oninput += self.inp_oninput2, span1
        #self.main += dom.hr(), span, dom.br(), span1, dom.br(), lbl, inp

        ''' Multiple events, single widget '''
        span = dom.span()
        span1 = dom.span()
        lbl = dom.label('Enter only numbers (tab out to validate): ')
        inp = dom.input()
        inp.oninput += self.inp_oninput3, span
        inp.onblur += self.inp_onblur, span1
        self.main += (
            dom.hr(), 
            lbl, dom.br(), span, dom.br(), 
            inp, dom.br(),
            span1
        )

    def btnclicker_onclick(self, src, eargs):
        import primative
        eargs.html['p'].only.text = str(primative.datetime.utcnow())

    def btnclicker_onclick2(self, src, eargs):
        ''' No fragment to process '''

        # Quick test; use a breakpoint
        #B()
        pass

    def btnclicker_onclick4(self, src, eargs):
        ''' No fragment to process '''
        eargs.html['p'].only.text = eargs.html['code'].text

    def btnclicker_onclick5(self, src, eargs):
        raise Exception('Derp')

    def inp_oninput(self, src, eargs):
        span = eargs.html['span'].only

        inp = src
        span.text = inp.value

    def inp_oninput1(self, src, eargs):
        span = eargs.html['span'].first
        span.text = inp.value

    def inp_oninput2(self, src, eargs):
        span = eargs.html['span'].first

        inp = src
        span.text = inp.value

    def inp_oninput3(self, src, eargs):
        span = eargs.html['span'].first

        inp = src
        span.text = inp.value

    def inp_onblur(self, src, eargs):
        span = eargs.html['span'].first
        inp = src

        span.text = 'VALID' if inp.value.isnumeric() else 'INVALID'

class ticketsspa(pom.spa):
    ''' Inner classes (pages) '''
    class ticket(pom.crud):
        def __init__(self, *args, **kwargs):
            super().__init__(effort.requirement, *args, **kwargs)

        def main(self, id:str=None, crud:str='retrieve', oncomplete=None):
            super().main(id=id, crud=crud, oncomplete=oncomplete)

            if self.instance.orm.isnew:
                self.main << dom.h1('Create a ticket')
    
    class people(pom.page):
        ''' Inner classes (pages) '''
        class new(pom.page):
            def main(self):
                self.main += dom.p('Create a person')
                self.main += dom.html('''
                <table>
                  <thead>
                    <tr>
                      <th>firstname</th>
                      <th>lastname</th>
                      <th>username</th>
                      <th>email address</th>
                      <th>dob</th>
                      <th>active</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td>William</td>
                      <td>Shakespeare</td>
                      <td>Shakespeare</td>
                      <td>
                        <a href="person?id=abc123">
                          william@shakespeare.com
                        </a>
                      </td>
                      <td>April 23, 1564</td>
                      <td>no</td>
                    </tr>
                  </tbody>
                </table>
                ''')


        ''' Class members '''
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.pages += ticketsspa.people.new()
        
        def main(self):
            self.main += dom.html('''
            <table>
              <thead>
                <tr>
                  <th>firstname</th>
                  <th>lastname</th>
                  <th>username</th>
                  <th>email address</th>
                  <th>dob</th>
                  <th>active</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>William</td>
                  <td>Shakespeare</td>
                  <td>Shakespeare</td>
                  <td>
                    <a href="person?id=abc123">
                      william@shakespeare.com
                    </a>
                  </td>
                  <td>April 23, 1564</td>
                  <td>no</td>
                </tr>
                <tr>
                  <td>Jane</td>
                  <td>Austen</td>
                  <td>JaneAusten</td>
                  <td>jane@austen.com</td>
                  <td>December 16, 1775</td>
                  <td>no</td>
                </tr>
                <tr>
                  <td>Charles</td>
                  <td>Dickens</td>
                  <td>CDickens</td>
                  <td>charles@dickens.com</td>
                  <td>February 7, 1812</td>
                  <td>no</td>
                </tr>
                <tr>
                  <td>Mark</td>
                  <td>Twain</td>
                  <td>MarkTwain</td>
                  <td>mark@twain.com</td>
                  <td>November 30, 1835</td>
                  <td>no</td>
                </tr>
                <tr>
                  <td>F. Scott</td>
                  <td>Fitzgerald</td>
                  <td>FScottF</td>
                  <td>f.scott@fitzgerald.com</td>
                  <td>September 24, 1896</td>
                  <td>no</td>
                </tr>
              </tbody>
            </table>
            ''')

    class backlogs(pom.crud):
        def __init__(self, *args, **kwargs):
            super().__init__(
                e=effort.backlogs, presentation='cards', *args, **kwargs
            )


        def main(self, 
            id:str=None, crud:str='retrieve', oncomplete=None
        ):
            """ XXX
            """
            super().main(id=id, crud=crud, oncomplete=oncomplete)

            es = self.instance

            cards = self.main['article.card']

            # For each backlog card in cards
            for card in cards:
                id = card.getattr('data-entity-id')
                id = UUID(id)

                pg = self.spa.pages['stories']
                pg.instance = es[id].backlog_stories

                pg.clear()

                pg(oncomplete=self.path)
                
                # TODO For some reason, calling `pg['table']` causes a
                # dom.MoveError. Ideally, we would be able to do this.
                tbl = pg.main['table'].only

                a = tbl['[rel=create-form]'].only
                a.href += '&backlogid=' + card.getattr('data-entity-id')

                '''
                XXX
                href = www.url(a.href)
                qs = href.qs
                qs['backlogid'] = card.getattr('data-entity-id')
                href.qs = qs
                a.href = str(href)
                '''


                tbl.orphan()

                card += tbl
            
        @property
        def detail(self):
            return self.spa.pages['backlog']

    class backlog(pom.crud):
        def __init__(self, *args, **kwargs):
            super().__init__(e=effort.backlog, *args, **kwargs)

    class stories(pom.crud):
        def __init__(self, *args, **kwargs):
            super().__init__(
                e=effort.backlog_stories, presentation='table', 
                *args, **kwargs
            )

        @property
        def detail(self):
            return self.spa.pages['story']

    class story(pom.crud):
        def __init__(self, *args, **kwargs):
            super().__init__(e=effort.story, *args, **kwargs)

        @property
        def detail(self):
            return self.spa.pages['story']

        @property
        def select(self):
            if not self._select:
                return 'name points, description, created'

        def main(self, 
            id:str=None, crud:str='retrieve', oncomplete=None,
            backlogid=None
        ):

            super().main(id=id, crud=crud, oncomplete=oncomplete)

            frm = self.main['form'].only

            if backlogid:
                bl = effort.backlog(backlogid)

                inp = pom.input(
                    type = 'text',
                    label = 'Backlog',
                    name = 'backlog'
                )

                inp.input.value = bl.name
                inp.input.setattr('data-id', bl.id.hex)
                inp.input.disabled = True

                frm << inp

    class search(pom.page):
        def main(self):
            self.main += dom.p('Search')
    
    ''' Class members of `site` '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Main
        self.pages += ticketsspa.backlogs()
        self.pages += ticketsspa.backlog()

        self.pages += ticketsspa.stories()
        self.pages += ticketsspa.story()

        self.pages += ticketsspa.ticket()
        self.pages += ticketsspa.search()
        self.pages += ticketsspa.people()

        # People
        self.pages.last.pages += ticketsspa.people.new()

    def main(self):
        self.main += dom.p('Carapacian Tickets SPA')

        ''' SPA Menu '''
        mnu = pom.menu('Spa')
        self.header.menus += mnu
        mnu.items  +=  pom.menu.item(
            'New', 'ticketsspa/ticket?crud=create'
        )
        mnu.items  +=  pom.menu.item('Backlog',  'ticketsspa/backlogs')
        mnu.items  +=  pom.menu.item('Search',   'ticketsspa/search')
        mnu.items  +=  pom.menu.item('People',   'ticketsspa/people')

# The Css for the site. See site.styles
Css = '''
body{
    font-family: "Nunito",sans-serif;
    color: #000;
}

a{
    color: #2ba74a !important;
}

p{
    text-align: justify;
}

section#contact-us p{
    text-align: initial;
}

hr.divider{
    background-color: #2ba74a;
}

h1, h2, h3, h4, h5, h6{
    font-weight: 700;
    text-transform: upper;
}

main>header>.tagline {
    text-transform: uppercase; 
    font-weight: bold;
    font-family: Vision, Ariel, sans-serif;
    color: #0F6A36;
    font-size: 1.5em;
}

body>main>header {
    text-align: center;
    margin: 2em 0;
    font-size: 1.5em;
}

main>section>:not(header){
    margin-left:1em;
}

main>section>header h2{
    color: #0F6A36;
    margin-bottom: 5px;
}

main>section>section>header{
    margin-bottom: -1em;
}

main>section>section>header h3{
    color: #0F6A36;
    font-size: 1.7em;
}

body>header, body>footer{
    background-color: rgb(25, 25, 25);
}

main>section>header h2{
    font-family: Vision, Ariel, sans-serif;
}

main>section>header{
    border-bottom: .05em green solid;
}

/* Menu/Nav Bar */ 
header menu{
    background-image: none;
    background-repeat: repeat;
    background-attachment: scroll;
    background-clip: border-box;
    background-origin: padding-box;
    background-position-x: 0%;
    background-position-y: 0%;
    background-size: auto auto;
	width: 100% !important;
    display: flex;
    justify-content: center;
    list-style-type: none;
    margin: 0;
    padding: 0;
}

header menu li:first-child img{
    width: 346px;
    height: 60px;
}

main{
    margin: auto;
    max-width: 50em;
    padding: 1em;
}

@media only screen and (max-width: 992px) {
    header menu li:first-child{
        width: 100%;
        text-align: center;
    }

    header menu{
        flex-wrap: wrap;
    }

    header menu li:not(:first-child){
        font-size: 1em;
        margin-bottom: .5em;
    }
    header menu li:nth-child(2){
        margin-left: 50px;
    }
}

@media only screen and (min-width: 992px) {
    header menu{
        flex-wrap: nowrap;
    }

    header menu li:not(:first-child){
        font-size: 1.5em;
        margin-top: 15px;
    }

    header menu li:first-child{
        flex-basis: 100%;
    }

}

@media only screen and (min-width: 1200px) {
    header menu{
        flex-wrap: nowrap;
    }


    header menu li:not(:first-child){
        font-size: 1.36em;
        margin-top: 15px;
    }
}

header menu li{
    display: inline;
    padding: 0 .5em;
}

/* Carapacian colors and weights*/
.fg-dark-green{
    color: #0F6A36;
}

.bg-dark-green{
    background-color: #0F6A36;
}

.fg-light-green{
    color: #2BA74A;
}

.bg-light-green{
    background-color: #2BA74A;
}

.fg-dark-gray{
    color: #54565B;
}

.bg-dark-gray{
    background-color: #54565B;
}

.fg-light-grey{
    color: #A8A8AA;
}

.bg-light-grey{
    background-color: #A8A8AA;
}

.font-light{
    font-weight: 300;
}

.font-heavy{
    font-weight: 700;
}

.fg-black{
    color: #000000
}

.bg-black{
    background-color: #000000
}

.fg-white{
    color: #FFFFFF
}

.bg-white{
    background-color: #FFFFFF
}

.label-primary{
    background-color: #0F6A36;
    color: #FFFFFF !important;
}

dt {
  font-size: 2rem;
}

dd {
  margin-bottom: 20px;
}

body>footer p{
    text-align: center;
}

body>footer p{
    color: #116a36;
}

article.card, form {
    display: grid;
    grid-template-columns: repeat(2, 30em);
    gap: 1em 0em;
}

form {
    grid-template-columns: repeat(1, 30em);
}

label{
    margin-right: 1em;
}
'''
        
Favicon = '''
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
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
