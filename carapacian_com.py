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
import party
import pom
import ecommerce
import file

class sites(pom.sites):
    pass

class site(pom.site):
    Id = UUID(hex='c0784fca-3fe7-45e6-87f8-e2ebbc4e7bf4')

    Proprietor = party.company.carapacian
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.host = 'carapacian.com'

        self.title = 'Carapacian Sustainable Software'

        self.pages += home()
    
    @property
    def head(self):
        if not self._head:
            hd = super().head
            hd += dom.meta(
                name = 'keywords', 
                content = 'carapacian core technical debt'
            )

            hd += dom.meta(
                name = 'description', 
                content = 'Your partners in technical debt managment'
            )

            csss = [
             'https://carapacian.com/css/brightlight-green.css',
             'https://carapacian.com/css/carapacian.css',
            ]

            for css in csss:
                hd += dom.link(rel='stylesheet', href=css)

        return self._head

    @property
    def header(self):
        hdr = super().header

        hdr.logo = pom.logo(
            'Carapacian Logo',
            href = 'https://carapacian.com',
            img  = 'https://carapacian.com/images/logo.png',
        )

        mnu = hdr.menu

        itms = mnu.items 

        itms.clear()

        itms += pom.menu.item('Services')
        itms += pom.menu.item('Products')
        itms += pom.menu.item('Services')

        return hdr

class home(pom.page):
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
