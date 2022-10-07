#!/usr/bin/python3
# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2022

from datetime import timezone, datetime, date
from dbg import B, PM
from func import enumerate, getattr
from uuid import uuid4, UUID
import dom
import ecommerce
import file
import party
import pom

# XXX Running ./test.py twice seems to report carapacian_com.site
# integrity see IntegrityErrors.txt as well as:
#
#     [file_directory]                                                      FAIL
#     RecordNotFoundError: RecordNotFoundError('A single record was not found') in it_creates_floaters_as_a_carapacian_property

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
        return party.company.carapacian

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
        itms += pom.menu.item('Services')
        itms += pom.menu.item('Products')
        itms += pom.menu.item('Services')

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
        btn1 = dom.button('Clickme One')
        btn2 = dom.button('Clickme Two')
        p = dom.p()
        p1 = dom.p()

        btn1.onclick += self.btnclicker_onclick, p
        btn2.onclick += self.btnclicker_onclick, p1

        self.main += btn1, btn2, p, p1

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
        lbl = dom.label('Enter only numbers: ')
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

class ticketsspa(pom.page):
    class new(pom.page):
        def main(self):
            self.main += dom.p('Create a ticket')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pages += ticketsspa.new()

    def main(self):
        self.main += dom.p('Carapacian Tickets SPA')

        ''' SPA Menu '''
        mnuspa = pom.menu(name='spa')
        self.header.menus += mnuspa

        mnuspa.items  +=  pom.menu.item('Backlog',  'backlog')
        mnuspa.items  +=  pom.menu.item('New',      'new')
        mnuspa.items  +=  pom.menu.item('Search',   'search')

    class backlog(dom.main):
        pass
        
