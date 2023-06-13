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

        def gethtml(self, id, crud, oncomplete):
            """ An override of pom.crud.gethtml to produces the HTML
            needed for this `backlogs` page.
            """
            # Get the default cards div
            div = super().gethtml(
                id=id, crud=crud, oncomplete=oncomplete
            )

            # Get instance
            es = self.instance

            # Get all backlog status types 
            types = effort.backlogstatustypes.orm.all
            fltstr = ','.join(types.pluck('name'))

            # TODO Instead of creating a filter <form> manually, we
            # should investigate creating a new `pom.filter` class that
            # inherits from dom.form and can provide nice interface to
            # control and interrogate the object's properties.
            frm = dom.form(class_='filter')

            for type in types:
                inp = dom.input(
                    type   =  'checkbox',
                    name   =  type.name,
                    value  =  type.id.hex
                )

                if type.name in self.types.pluck('name'):
                    inp.checked = True

                inp.identify()

                inp.onclick += self.chkfilters_onclick, div

                lbl = dom.label(type.name.capitalize(), for_=inp.id)
                frm += lbl
                frm += inp

            div << frm

            # For each backlog card in cards, add a table of stories
            for card in div['article.card']:
                # Get backlog id from card
                id = card.getattr('data-entity-id')
                id = UUID(id)

                bl = self.instance[id]

                # Transition state buttons
                if not bl.isclosed:
                    btn = dom.button('Close', class_='close')
                    btn.onclick += self.btnclose_onclick, card, frm
                    card += btn

                # Get the backlog-to-stories association page
                pg = self.spa.pages['backlog-stories']
                pg.clear()

                # Set its instance
                pg.instance = bl.backlog_stories
                pg(oncomplete=self.path)
                
                # TODO For some reason, calling `pg['table']` causes a
                # dom.MoveError. Ideally, we would be able to do this.
                tbl = pg.main['table'].only

                # Remove Quick Edit. Quick Edits are designed to use the
                # current page (self), but since these Quick Edits are
                # from a differnt page (pg), their href confuses the
                # JavaScript.
                as_ = tbl['menu a[rel~=edit][rel~=preview]']
                for a in as_:
                    a.closest('li').remove()

                # Get the Add New anchor
                a = tbl['[rel=create-form]'].only

                # Add a backlogid query string parameter

                # TODO It would be nice if dom.a objects had a `url`
                # property that returned a www.url that was bound to the
                # anchor. That way, we could write the below statement
                # as:
                #
                # a.url.qs['backlogid'] = card.getattr('data-entity-id')
                #
                # Event handlers within the dom.a would be responsible
                # for updating the actual a.href property, thus the same
                # results would be achieved. This would be better
                # because the currently solution could potentially
                # append multiple backlogid parameters to the query
                # sting without knowing it. This approach would reequire
                # that the www.url class can deal with URL path's
                # without the need for a scheme or domain name.
                url = www.url(a.href)
                url.qs['backlogid'] = card.getattr('data-entity-id')
                url.qs['oncomplete'] = self.path

                a.href = url.normal

                # Get each Edit element's href
                as_ = tbl['a[rel~=edit]']

                # Update each Edit elements href
                for a in as_:
                    url = www.url(a.href)

                    try:
                        id = UUID(url.qs['id'])
                    except KeyError:
                        pass
                    else:
                        for bs in bl.backlog_stories:
                            if bs.id == id:
                                url.qs['id']          =  bs.story.id
                                url.qs['backlogid']   =  bl.id.hex
                                url.qs['oncomplete']  =  self.path

                                a.href = url.normal

                                break
                        else:
                            raise ValueError('Cannot find story')

                # Add column for span handle
                tbl['thead tr'].only << dom.th(class_='handle')

                for tr in tbl['tbody tr']:
                    td = dom.td(class_='handle')
                    span = dom.span('☰') 
                    tr.dragonize(
                        ondrop = (self.tr_ondrop, tbl, tr),
                        handle = span,
                        target = tr.id,
                    )

                    td += span
                    tr << td

                # Remove the table's parent so we can make `card` its
                # new parent
                tbl.orphan()

                card += tbl
            return div

        def main(self, 
            id:str = None,     crud:str = 'retrieve', 
            oncomplete = None, types:str = None,
        ):
            """ An override of pom.crud.main. The `types` parameter, if
            given, will contain a comma seperated string of backlog
            status types to filter the backlog cards by.
            """
            super().main(id=id, crud=crud, oncomplete=oncomplete)

        def tr_ondrop(self, src, eargs):
            """ The event handler for this `backlogs` to handle a story
            being moved within the backlog.
            """
            # Get the table of stories
            tbl = eargs.html.first

            # Get the element being dropped
            trsrc = eargs.html.last

            # Get the element that the above is being dropped on
            # XXX s/trdest/trzone
            trdest = src

            tbody = tbl['tbody'].only

            trs = tbody['tr']

            # If the source is the same as the destination, do nothing.
            if trsrc.id == trdest.id:
                www.application.current.response.status = 204
                return

            # Given:
            # 
            #     Story A
            #     Story B
            #     Story C
            #
            # If we drag Story A and drop on Story B, nothing should
            # happen. The following code detects this type of situaton
            # and does nothing in response.
            for i, tr in trs.enumerate():
                if i.last:
                    break

                if tr.id == trsrc.id:
                    if tr.next.id == trdest.id:
                        www.application.current.response.status = 204
                        return
                    
            # Get the backlog_story entities associated with the source
            # and estication
            bssrc = trsrc.entity
            bsdest = trdest.entity

            # Get the destinations backlog
            bl = bsdest.backlog

            # Insert the story to change its ranking within the backlog
            # and save.
            bl.insert(bsdest.rank, bssrc.story)
            bl.save()

            # Move the <tr>s within the table so they reflect the
            # reassignment of the story's rank
            src = tbody.elements.pop(trsrc.id)
            ix = tbody.elements.getindex(trdest.id)
            tbody.elements.insert(ix, src)

            bss = bl.backlog_stories

            # For each <tr> in the table
            for tr in tbody['tr']:
                # Get the backlog that corresponds to the tr
                id = tr.getattr('data-entity-id')
                bs = bss[UUID(id)]

                # Get the 'rank' <td>
                td = tr['td[data-entity-attribute=rank]'].only

                # Get the <span> that holds the value for rank
                span = td['span.value'].only

                # Set the rank
                span.text = bs.rank
                span.text += 'XXX'

        def chkfilters_onclick(self, src, eargs):
            """ A handler for the onclick event of the backlog status
            type filters.
            """
            # Get the cards <div> that was sent
            div = eargs.element

            # Get the filter <section>
            frm = div['form.filter'].only

            # Get the filter checkboxes
            chks = frm['[checked]']

            # Create a comma seperate list of filter names
            types = chks.pluck('name')
            self.types = ','.join(types)

            div1 = self.gethtml(
                id=None, crud='retrieve', oncomplete=None
            )

            # Take the current url, clone it and set the `types` query
            # string parameter to `types`
            url = www.application.current.request.url.clone()
            url.qs['types'] = sorted(types)

            # Instruct the browser to set the location bar to `url`
            instrs = pom.instructions()
            instrs += pom.set('url', url)
            div1 += instrs

            eargs.html.first = div1

        def btnclose_onclick(self, src, eargs):
            """ A handler for the onclick event of backlog card close
            buttons.
            """
            # Get the card
            card = eargs.html.first

            # Get the filter form
            frm = eargs.html.second

            # Get the types we are filtering on frmo the filter form
            types = frm['input[type=checkbox][checked]'].pluck('name')

            # Set those types to self.types 
            self.types = types

            # Get the confirmation dialog box if there is one 
            dlgs = card['dialog']

            # If there is no dialog box. This will be the case when the
            # Close button is first clicked.
            if dlgs.isempty:
                
                # Create the dialog to prompt the user to confirm
                # closure
                card += pom.dialog(
                    card, 
                    msg = 'Are you sure you want to close the backlog?',
                    caption = 'Confirm',
                    onyes = (self.btnclose_onclick, card, frm),
                    onno = (self.btnclose_onclick, card, frm),
                )

            # If there was a dialog box
            elif dlgs.issingular:
                dlg = dlgs.only
                btn = eargs.src

                # If user clicked the Yes button
                if btn.getattr('data-yes'):
                    
                    # Get backlog id
                    id = card.getattr('data-entity-id')

                    # Get backlog
                    bl = effort.backlog(id)

                    # Close
                    bl.close()
                    bl.save()

                    if 'closed' not in self.types.pluck('name'):
                        # Remove the backlog card from the page
                        eargs.remove(card)
                    else:
                        # Just remove the Close button from the card
                        card.remove('button.close')

                # Remove the dialog box so the user won't see it anymore
                card.remove('dialog')
            
        @property
        def detail(self):
            return self.spa.pages['backlog']

        @property
        def select(self):
            if not self._select:
                return (
                    'name, description, goal, begin end'
                )
            return self._select

        @property
        def types(self):
            """ Returns the backlogstatustypes to filter on.
            """
            try:
                types = self._args['types']
            except KeyError:
                return effort.backlogstatustypes.orm.all
            else:
                if not isinstance(types, list):
                    types = [types]

                # I think this conditional could be remove with the
                # resolution of TODO:ed0df12a
                if ''.join(types) == str():
                    return effort.backlogstatustypes.orm.all

                args = types

                # Query backlogstatustypes based on the values found
                pred = 'name in (%s)'
                pred %= ', '.join(['%s'] * len(args))

                return effort.backlogstatustypes(pred, args)

        @types.setter
        def types(self, v):
            """ Set the backlogstatustypes to filter on.

            :param: v str|list|effort.backlogstatustypes|None: The
            backlogstatustypes. If str, it will be considered a
            comma-seperated string of backlogstatustype names. Setting
            `types` to None implies we want all types.
            """
            if isinstance(v, str):
                v = v.split(',')
            elif isinstance(v, effort.backlogstatustypes):
                v = v.pluck('name')
            elif isinstance(v, list):
                pass
            elif v is None:
                v = list()
            else:
                raise TypeError('Invalid type for "types"')

            self._args['types'] = v

        @property
        def instance(self):
            """ Returns a `effort.backlogs` collection. Only the
            `backlogs` matching the backlog statust types found in
            `self.types` will be returned.
            """
            if not self._instance:
                # Create an empty collection
                self._instance = effort.backlogs()

                # For each of the backlog status types
                for type in self.types:
                    
                    # Append the type's backlog collection
                    self._instance += type.backlogs

            return self._instance

    class backlog(pom.crud):
        """ A pom.crud page used to create and edit `effort.backlog`
        entity objects.
        """
        def __init__(self, *args, **kwargs):
            super().__init__(e=effort.backlog, *args, **kwargs)

    class backlog_stories(pom.crud):
        def __init__(self, *args, **kwargs):
            super().__init__(
                e=effort.backlog_stories, presentation='table', 
                *args, **kwargs
            )

        @property
        def detail(self):
            return self.spa.pages['story']

        @property
        def select(self):
            if not self._select:
                return (
                    'story.name story.points story.created'
                )
            return self._select

        @property
        def instance(self):
            """ Return the instance of this `backlog_stories` page.
            """
            # XXX Test to ensure stories are always sorted by rank
            inst = super().instance
            inst.sort('rank')
            return inst

        @instance.setter
        def instance(self, v):
            self._instance = v

    class story(pom.crud):
        def __init__(self, *args, **kwargs):
            super().__init__(e=effort.story, *args, **kwargs)
            self.onbeforesave += self.self_onbeforesave

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
                    name = 'story.backlog'
                )

                inp.setattr('data-entity-attribute', 'backlog')
                inp.input.value = bl.name
                inp.input.setattr('data-entity-id', bl.id.hex)
                inp.input.disabled = True

                frm << inp

        @property
        def detail(self):
            return self.spa.pages['story']

        @property
        def select(self):
            if not self._select:
                return 'name points description'

        def self_onbeforesave(self, src, eargs):
            st = eargs.entity

            if st.orm.isnew:
                st.created = datetime.utcnow()

            if st.backlog:
                return

            inp = eargs.html['input[name="story.backlog"]'].only
            id = inp.getattr('data-entity-id')
            bl = effort.backlog(id)
            bl.insert(st)
            eargs.stead = bl

    class search(pom.page):
        def main(self):
            self.main += dom.p('Search')
    
    ''' Class members of `site` '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Main
        self.pages += ticketsspa.backlogs()
        self.pages += ticketsspa.backlog()

        self.pages += ticketsspa.backlog_stories()
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
        mnu.items  +=  pom.menu.item(
            'Backlog',  'ticketsspa/backlogs?types=planning'
        )
        mnu.items  +=  pom.menu.item('Search',   'ticketsspa/search')
        mnu.items  +=  pom.menu.item('People',   'ticketsspa/people')

# The Css for the site. See site.styles
Css = '''
body{
    font-family: "Nunito",sans-serif;
    color: #000;
}

td .handle{
    cursor: move
}

a{
    color: #2ba74a !important;
}

tr[data-dragentered] {
    color: red;
    border-top-color: blue;
    
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

article.card table{
    grid-column: 1 / span 2;
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
