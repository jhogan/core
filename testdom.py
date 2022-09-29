#!/usr/bin/python3
import apriori; apriori.model()

from datetime import timezone, datetime, date
from dbg import B
from func import enumerate, getattr
from uuid import uuid4
import dom, www
import party
import primative
import re
import tester
import uuid
import string
import orm

########################################################################
# Test dom                                                             #
########################################################################
class dom_elements(tester.tester):
    def it_gets_text(self):
        # FIXME:fa4e6674 This is a non-trivial problem
        return
        html = dom.html('''
        <div>
            <p>
                This is a paragraph with 
                <em>
                    emphasized text
                </em>.
            </p>
            <p>
                This is a paragraph with 
                <strong>
                    strong text
                </strong>.
            </p>
        </div>
        ''')

        expect = self.dedent('''
        This is a paragraph with emphasized text.
        This is a paragraph with strong text.
        ''')

        self.eq(expect, html.text)

        html = dom.html('''
        <p>This is a paragraph with <em>emphasized text</em>.</p>
        <p>This is a paragraph with <strong>strong text</strong>.</p>
        ''')

        self.eq(expect, html.text)

        html = dom.html(Shakespeare)
        expect = self.dedent('''
        No, thy words are too precious to be cast away upon
        curs; throw some of them at me; come, lame me with reasons.
        ''')

        actual = html['#speech3+div'].text

        self.eq(expect, actual)

        html = dom.html('<p>%s</p>' % actual)
        self.eq(expect, html.text)

    def it_calls_html(self):
        html = dom.html(TestHtml, ids=False)
        self.eq(TestHtmlMin, html.html)

        htmlmin = dom.html(TestHtmlMin, ids=False)
        self.eq(html.html, htmlmin.html)

    def it_calls_pretty(self):
        def rm_uuids(els):
            for x in els.walk():
                # Remove computer generated UUID ids
                try:
                    primative.uuid(base64=x.id)
                except:
                    pass
                else:
                    del x.attributes['id']

        htmlmin = dom.html(TestHtmlMin)
        rm_uuids(htmlmin)

        self.eq(TestHtml, htmlmin.pretty)

        html = dom.html(TestHtml)
        rm_uuids(html)
        self.eq(TestHtmlMin, html.html)

    def it_removes_elements(self):
        html = dom.html(TestHtml)

        bs = html['strong']
        self.two(bs)

        bs = bs.remove()
        self.two(bs)

        self.eq([None, None], bs.pluck('parent'))

        bs = html['strong']
        self.zero(bs)

class element(tester.tester):
    def it_raises_when_same_child_is_added_more_than_once(self):
        ''' Add child to element '''
        p = dom.p()
        span = dom.span()

        def append():
            nonlocal p
            p += span

        append()

        self.expect(ValueError, append)

        def append():
            nonlocal p
            p << span

        self.expect(ValueError, append)

        ''' elements collections themselves should probably not be
        constrained from having identical elements added more than once
        '''
        ps = dom.ps()
        span = dom.span()

        ps += span
        ps += span
        ps << span
        ps.append(span)
        ps.unshift(span)
        ps.insert(0, span)
        ps.insertbefore(0, span)
        ps.insertafter(0, span)
        ps.push(span)

        self.nine(ps)
        self.all(type(x) is dom.span for x in ps)

        
    def it_raises_when_body_is_given_to_void_elements(self):
        ''' We want to get a ValueError when we add a body argument to
        an element that is marked `isvoid`. Elements that are "void",
        like <input>, <meta> and <hr> should not contain a body.
        '''

        # A tuple of void elements
        clss = (
            dom.link, dom.base, dom.img, dom.input, dom.meta, dom.hr,
        )

        for cls in clss:
            self.expect(ValueError, lambda: cls('some body text'))

    def it_gets_text(self):
        # FIXME:fa4e6674 This is a non-trivial problem
        return

        html = dom.html('''
        <div>
          <p>
            This is a paragraph with <em>emphasized</em> text.
          </p>
        </div>
        ''')
        p = html['p'].first

        expect = 'This is a paragraph with emphasized text.'
        self.eq(expect, p.text)

    def it_sets_text(self):
        html = dom.html('''
        <div>
            <p>
                This is a paragraph with 
                <em>
                    emphasized text
                </em>.
            </p>
            <p>
                This is a paragraph with 
                <strong>
                    strong text
                </strong>.
            </p>
        </div>
        ''')

        div = html['div'].first
        self.two(div.children)

        div.text = 'Some text'

        self.zero(div.children)

        self.eq('Some text', div.elements.first.value)

        expect = self.dedent('''
        <div>
          Some text
        </div>''')

        self.eq(expect, html.pretty)

    def it_class_language(self):
        html = dom.html('''
        <html lang="en">
            <head></head>
            <body>
                <div>
                    <p>
                        My language is 'en' because it was specified in
                        the root html tag.
                    </p>
                </div>
                <section lang="fr">
                    <p>Comment dites-vous "Bonjour" en Espanol?</p>

                    <div>
                        <blockquote lang="es">
                            <p>
                                My language will be Spainish.
                            </p>
                        </blockquote>
                    </div>
                </section>
            </body>
        </html>
        ''')

        p = html[0].children[1].children[0].children[0]
        self.type(dom.p, p)
        self.eq('en', p.language)

        self.type(dom.div, p.parent)
        self.eq('en', p.parent.language)

        p = html[0].children[1].children[1].children[0]
        self.type(dom.p, p)
        self.eq('fr', p.language)

        self.type(dom.section, p.parent)
        self.eq('fr', p.parent.language)

        p = html[0] \
                .children[1] \
                .children[1] \
                .children[1] \
                .children[0] \
                .children[0] 
        self.type(dom.p, p)
        self.eq('es', p.language)

        self.type(dom.blockquote, p.parent)
        self.eq('es', p.parent.language)

        html = dom.html('''
        <html>
            <head></head>
            <body>
                <div>
                    <p>
                        This document contains no 'lang' attribute so
                        all of the elements' `language` @property's
                        should be None.
                    </p>
                </div>
            </body>
        </html>
        ''')

        self.all(x.lang is None for x in html.walk())

    def it_calls_parent(self):
        p = dom.paragraph()
        self.none(p.parent)

        span = dom.span('some text')
        p += span
        self.none(p.parent)
        self.is_(p, span.parent)

        b = dom.strong('strong text')
        span += b

        self.none(p.parent)
        self.is_(p,          span.parent)
        self.is_(span,       b.parent)
        self.is_(span,       b.getparent())
        self.is_(span,       b.getparent(0))
        self.is_(p,          b.parent.parent)
        self.is_(p,          b.grandparent)
        self.is_(p,          b.getparent(1))
        self.is_(b,          b.elements.first.parent)
        self.is_(span,       b.elements.first.grandparent)
        self.is_(p,          b.elements.first.greatgrandparent)
        self.is_(p,          b.elements.first.getparent(2))

    def it_calls_siblings(self):
        p = dom.paragraph()

        txt = dom.text('some text')
        p += txt
        self.zero(txt.siblings)

        b = dom.strong('some strong text')
        p += b
        self.one(txt.siblings)
        self.is_(b, txt.siblings.first)
        self.zero(b.siblings)

        i = dom.em('some emphasized text')
        p += i
        self.two(txt.siblings)
        self.is_(b, txt.siblings.first)
        self.is_(i, txt.siblings.second)

        self.one(b.siblings)
        self.is_(i, b.siblings.first)

        self.one(i.siblings)
        self.is_(b, i.siblings.first)

    def it_raises_when_moving_elements(self):
        p = dom.paragraph()
        txt = dom.text('some text')
        p += txt

        p1 = dom.paragraph()
        self.expect(dom.MoveError, lambda: p1.__iadd__(txt))

    def it_calls_isvoid(self):
        self.false(dom.paragraph.isvoid)
        self.false(dom.paragraph().isvoid)

        self.true(dom.base.isvoid)
        self.true(dom.base().isvoid)

    def it_calls_id(self):
        p = dom.paragraph()
        uuid = uuid4().hex
        p.id = uuid
        self.one(p.attributes)
        self.eq(uuid, p.id)

    def it_gets_attribute_then_sets_the_attribute(self):
        p = dom.paragraph()

        # Get
        p.id
        self.zero(p.attributes)

        # Set
        uuid = uuid4().hex
        p.id = uuid
        self.one(p.attributes)
        self.eq(uuid, p.id)

    def it_calls_anchor_attributes(self):
        """ Since there are so many HTML classes that were originally 
        autogenerated, we will select one, `anchor` to run some basic
        tests to make sure that it is working correctely.
        """
        a = dom.anchor()
        as_ = dom.anchors()

        self.isinstance(as_, dom.elements)
        self.isinstance(a, dom.element)

        attrs = (
            'referrerpolicy',  'target',  'hreflang',
            'ping',            'media',   'href',
            'download',        'rel',     
        )

        for i, attr in enumerate(attrs):
            uuid = uuid4().hex
            setattr(a, attr, uuid)
            self.eq(uuid, getattr(a, attr))
            self.count(i + 1, a.attributes)

    def it_calls_id(self):
        p = dom.paragraph()
        id = primative.uuid(base64=p.id)
        self.isinstance(id, uuid.UUID)

    def it_appends(self):
        p = dom.p()
        em = dom.em()

        ''' It appends element '''
        p += em

        self.true(em in p.elements)

        ''' It appends text '''
        txt = 'text for p'
        p += txt

        self.eq(txt, p.text)

        ''' It appends sequence '''
        hr = dom.hr()
        br = dom.hr()

        p += hr, br
        self.is_(p.elements.penultimate, hr)
        self.is_(p.elements.ultimate, br)

    def it_unshifts(self):
        p = dom.p()
        em = dom.em()
        span = dom.span()
        p += span

        self.one(p.elements)

        ''' It prepends/unshifts element '''
        p << em

        self.two(p.elements)
        self.is_(em, p.elements.first)
        self.is_(span, p.elements.second)

        ''' It prepends/unshifts text '''
        txt = 'text for p'
        p << txt

        self.three(p.elements)
        self.eq(txt, p.text)
        self.is_(em, p.elements.second)
        self.is_(span, p.elements.third)

class test_comment(tester.tester):
    def it_calls_html(self):
        txt = 'Who wrote this crap'
        com = dom.comment(txt)

        expect = '<!--%s-->' % txt
        self.eq(expect, com.html)

class dom_script(tester.tester):
    def it_does_not_escape(self):
        body = 'A <string> with HTML "escapable" characters'

        script = dom.script(body)
        expect = f'<script>{body}</script>'
        self.eq(expect, script.html)

class dom_p(tester.tester):
    def it_calls__init___with_str_and_args(self):
        ''' With str arg '''
        hex1, hex2 = [x.hex for x in (uuid4(), uuid4())]
        p = dom.paragraph('''
        hex1: %s
        hex2: %s
        ''', hex1, hex2)
        
        expect = self.dedent('''
        <p>
          hex1: %s
          hex2: %s
        </p>
        ''', hex1, hex2)

        self.eq(expect, p.pretty)

        ''' With element arg '''
        txt = dom.text('Plain white sauce!')

        strong = dom.strong('''
            Plain white sauce will make your teeth
        ''')

        # Nest <span> into <strong>
        span = dom.span('go grey.');
        strong += span

        # NOTE The spacing is botched. This should be corrected when we
        # write tests for dom.text.
        p = dom.paragraph(txt)
        p += strong

        expect = self.dedent('''
        <p>
          Plain white sauce!
          <strong>
            Plain white sauce will make your teeth
            <span>
              go grey.
            </span>
          </strong>
        </p>
        ''')

        self.eq(expect, p.pretty)

        # Expect a ValueError if *args are given for a non-str first
        # argument
        self.expect(
          ValueError, 
          lambda: dom.paragraph(txt, 'arg1', 'arg2')
        )

    def it_calls_html(self):
        p = dom.paragraph()

        p += '''
            Plain white sauce!
        '''

        strong = dom.strong('''
            Plain white sauce will make your teeth
        ''')

        # Nest <span> into <strong>
        span = dom.span('go grey.');
        strong += span

        p += strong

        p += '''
            Doesn't matter, just throw it away!
        '''

        expect = self.dedent('''
        <p>
          Plain white sauce!
          <strong>
            Plain white sauce will make your teeth
            <span>
              go grey.
            </span>
          </strong>
          Doesn&#x27;t matter, just throw it away!
        </p>
        ''')

        self.eq(expect, p.pretty)

    def it_works_with_html_entities(self):
        p = dom.paragraph()

        p += '''
            &copy; 2020, All Rights Reserved
        '''

        expect = self.dedent('''
        <p>
          &amp;copy; 2020, All Rights Reserved
        </p>
        ''')

        self.eq(expect, p.pretty)

        expect = '<p>&amp;copy; 2020, All Rights Reserved</p>'
        self.eq(expect, p.html)

        expect = self.dedent('''
            &copy; 2020, All Rights Reserved
        ''')

        self.eq(expect, p.text)

class dom_text(tester.tester):
    def it_calls_html(self):
        txt = self.dedent('''
        <p>
          Plain white sauce!
          <strong>
            Plain white sauce will make your teeth
            <span>
              go grey.
            </span>
          </strong>
          Doesn't matter, just throw it away!
        </p>
        ''')

        expect = self.dedent('''
        &lt;p&gt;
          Plain white sauce!
          &lt;strong&gt;
            Plain white sauce will make your teeth
            &lt;span&gt;
              go grey.
            &lt;/span&gt;
          &lt;/strong&gt;
          Doesn&#x27;t matter, just throw it away!
        &lt;/p&gt;
        ''')

        self.eq(expect, dom.text(txt).html)

        self.eq(txt, dom.text(txt, esc=False).html)

    def it_calls__str__(self):
        txt = self.dedent('''
        <p>
          Plain white sauce!
          <strong>
            Plain white sauce will make your teeth
            <span>
              go grey.
            </span>
          </strong>
          Doesn't matter, just throw it away!
        </p>
        ''')

        expect = self.dedent('''
        <p>
          Plain white sauce!
          <strong>
            Plain white sauce will make your teeth
            <span>
              go grey.
            </span>
          </strong>
          Doesn't matter, just throw it away!
        </p>
        ''')

        txt = dom.text(txt)
        self.eq(expect, str(txt))

class dom_attribute(tester.tester):
    def it_raises_on_invalid_attributes(self):
        # Test for valid characters in attribute names. Based on
        # https://html.spec.whatwg.org/multipage/syntax.html#attributes-2
        p = dom.paragraph()

        def ass(name):
            p.attributes[name] = name

        # These punctuation marks are not allowed.
        invalids = ' "\'/='
        for invalid in invalids:
            for i in range(3):
                name = list('abc')
                name[i] = invalid
                self.expect(ValueError, lambda: ass(''.join(name)))

        # Non-characters are not allowed
        nonchars = range(0xfdd0, 0xfdef)
        for nonchar in nonchars:
            for i in range(3):
                name = list('abc')
                name[i] = chr(nonchar)
                self.expect(ValueError, lambda: ass(''.join(name)))

        # Control charcters are not allowed
        ctrls = range(0x007f, 0x009f)
        for ctrl in ctrls:
            for i in range(3):
                name = list('abc')
                name[i] = chr(ctrl)
                self.expect(ValueError, lambda: ass(''.join(name)))
        
    def it_deals_with_undef_attr(self):
        p = dom.paragraph()
        uuid = uuid4().hex
        attr = p.attributes[uuid]
        self.is_(p.attributes[uuid], attr)

        self.true(p.classes.count     ==  0)
        self.true(p.attributes.count  ==  0)
        self.true(len(p.classes)      ==  0)
        self.true(len(p.attributes)   ==  0)
        self.zero(p.attributes.sorted('name'))

        self.zero(list(p.attributes.reversed()))
        self.none(p.attributes.second)
        self.none(p.attributes(1))
        self.expect(IndexError, lambda: p.attributes[1])
        self.zero(p.attributes[1:1])
        
        for i, attr in p.attributes.enumerate():
            if i: # id
                self.fail()

        attr.value = uuid4().hex
        self.zero(p.classes)
        self.one(p.attributes)
        self.eq(p.attributes.first, attr)
        self.eq(p.attributes[0], attr)
        self.eq(p.attributes(0), attr)
        self.true(p.classes.count     ==  0)
        self.true(p.attributes.count  ==  1)
        self.true(len(p.classes)      ==  0)
        self.true(len(p.attributes)   ==  1)
        self.one(p.attributes.sorted('name'))
        self.one(list(p.attributes.reversed()))
        self.one(p.attributes[0:1])
        self.is_(p.attributes.first, p.attributes[0:1].first)

        for i, _ in enumerate(p.attributes):
            i += 1

        self.eq(1, i)

        uuid = uuid4().hex
        attr = p.attributes[uuid]
        self.is_(p.attributes[uuid], attr)

        self.true(p.classes.count     ==  0)
        self.true(p.attributes.count  ==  1)
        self.true(len(p.classes)      ==  0)
        self.true(len(p.attributes)   ==  1)
        self.one(p.attributes.sorted('name'))
        self.one(list(p.attributes.reversed()))
        self.notnone(p.attributes.first)
        self.none(p.attributes.second)
        self.notnone(p.attributes(0))
        self.notnone(p.attributes(0))
        self.none(p.attributes(1))
        self.none(p.attributes(1))
        self.expect(None, lambda: p.attributes[0])
        self.expect(IndexError, lambda: p.attributes[1])
        self.one(p.attributes[0:1])
        self.is_(p.attributes.first, p.attributes[0:1].first)
        
        attr.value = uuid4().hex
        self.zero(p.classes)
        self.two(p.attributes)
        self.eq(p.attributes.second, attr)
        self.eq(p.attributes[1], attr)
        self.eq(p.attributes(1), attr)
        self.true(p.classes.count     ==  0)
        self.true(p.attributes.count  ==  2)
        self.true(len(p.classes)      ==  0)
        self.true(len(p.attributes)   ==  2)
        self.two(p.attributes.sorted('name'))
        self.two(list(p.attributes.reversed()))
        self.two(p.attributes[0:2])
        self.is_(p.attributes.first, p.attributes[0:2].first)
        self.is_(p.attributes.second, p.attributes[0:2].second)

        i = 0
        for i, _ in enumerate(p.attributes):
            i += 1

        self.eq(2, i)

    def it_sets_None_attr(self):
        inp = dom.input()
        inp.attributes['disabled'] = None
        self.one(inp.attributes)

        expect = self.dedent('''
        <input disabled>
        ''')

        self.eq(expect, inp.pretty)

        inp = dom.input()
        inp.attributes.append('disabled')
        self.one(inp.attributes)
        expect = self.dedent('''
        <input disabled>
        ''')
        self.eq(expect, inp.pretty)

        inp = dom.input()
        inp.attributes += 'disabled'
        self.one(inp.attributes)
        expect = self.dedent('''
        <input disabled>
        ''')
        self.eq(expect, inp.pretty)
        
        inp = dom.input()
        inp.attributes += 'disabled', None
        self.one(inp.attributes)
        expect = self.dedent('''
        <input disabled>
        ''')
        self.eq(expect, inp.pretty)

    def it_appends_attribute(self):
        # Append attribute object
        p = dom.paragraph()
        self.zero(p.attributes)
        id = uuid4().hex
        p.attributes += dom.attribute('data-id', id)
        self.one(p.attributes)
        self.eq('data-id', p.attributes.first.name)
        self.eq(id, p.attributes.first.value)

        # Append a tuple
        name = uuid4().hex
        p.attributes += 'name', name
        self.two(p.attributes)
        self.eq('name', p.attributes.second.name)
        self.eq(name, p.attributes.second.value)

        # Append a list
        style = 'color: 8ec298'
        p.attributes += ['style', style]
        self.three(p.attributes)
        self.eq('style', p.attributes.third.name)
        self.eq(style, p.attributes.third.value)

        # It appends using kvp as argument
        title = uuid4().hex
        p.attributes.append('title', title)
        self.four(p.attributes)
        self.eq('title', p.attributes.fourth.name)
        self.eq(title, p.attributes.fourth.value)

        # It appends using indexer
        cls = uuid4().hex
        p.attributes['class'] = cls
        self.five(p.attributes)
        self.eq('class', p.attributes.fifth.name)
        self.eq(cls, p.attributes.fifth.value)

        # Append a collection of attributes:
        attrs = dom.attributes()
        attrs += 'foo', 'bar'
        attrs += 'baz', 'quux'
        p.attributes += attrs

        # it appends using a dict()
        cls = uuid4().hex
        p.attributes += {
            'lang': 'en',
            'dir': 'ltr'
        }

        self.nine(p.attributes)
        self.eq('en', p.lang)
        self.eq('ltr', p.dir)

    def it_makes_class_attribute_a_cssclass(self):
        p = dom.paragraph()
        p.attributes['class'] = 'form-group'
        cls = p.attributes['class']
        self.type(dom.cssclass, cls)

    def it_removes_attribute(self):
        # Add three attributes
        p = dom.paragraph()
        id, name, cls = [uuid4().hex for _ in range(3)]
        style = dom.attribute('style', 'color: 8ec298')
        p.attributes += 'name', name
        p.attributes += style
        p.attributes += 'class', cls
        self.three(p.attributes)

        self.true('name'  in  p.attributes)
        self.true(style   in  p.attributes)
        self.true('class' in  p.attributes)

        # Remove by str usinge method
        self.three(p.attributes)
        self.false('id' in p.attributes)

        # Remove by str using operator
        p.attributes -= 'name'
        self.two(p.attributes)
        self.false('name' in p.attributes)

        # Remove by object using operator
        p.attributes -= style
        self.one(p.attributes)
        self.false(style in p.attributes)

        del p.attributes['class']
        self.zero(p.attributes)
        self.false('class' in p.attributes)

    def it_updates_attribute(self):
        # Add three attributes
        p = dom.paragraph()
        id, name = uuid4().hex, uuid4().hex, 
        style = dom.attribute('style', 'color: 8ec298')
        cls = uuid4().hex
        p.attributes += 'data-id', id
        p.attributes += 'name', name
        p.attributes += style
        p.attributes += 'class', cls
        self.true('data-id'    in  p.attributes)
        self.true('name'  in  p.attributes)
        self.true(style   in  p.attributes)
        self.true('class' in  p.attributes)

        id, name = uuid4().hex, uuid4().hex, 
        style = dom.attribute('style', 'color: 8ec298')

        p.attributes['data-id'].value = id
        self.eq(id, p.attributes.first.value)

        cls = uuid4().hex
        p.attributes['class'] = cls
        self.eq(cls, p.attributes.fourth.value)

    def it_doesnt_append_nonunique(self):
        # Add three attributes
        p = dom.paragraph()
        id, name = uuid4().hex, uuid4().hex, 
        style = dom.attribute('style', 'color: 8ec298')
        p.attributes += 'data-id', id
        p.attributes += 'name', name
        p.attributes += style

        attrs = p.attributes
        ex = dom.AttributeExistsError

        # Append using `append` method
        self.expect(ex, lambda: attrs.append('data-id', id))
        self.expect(ex, lambda: attrs.append('name', name))
        self.expect(ex, lambda: attrs.append('style', style))

        attrs = {
            'data-id': id,
            'name': name,
        }

        for k, v in attrs.items():
            # Append using list
            def f():
                p.attributes += [k, v]
            self.expect(ex, f)

            # Append using attribute object
            def f():
                p.attributes += dom.attribute(k, v)
            self.expect(ex, f)

            # Append using tuple
            def f():
                p.attributes += k, v
            self.expect(ex, f)

            # Append using attributes collection
            def f():
                attrs = dom.attributes()
                attrs += k, v
                p.attributes += attrs
            self.expect(ex, f)

            # Append using dict
            def f():
                p.attributes += {
                    k: v
                }
            self.expect(ex, f)

class dom_cssclass(tester.tester):
    def it_deals_with_undef_attr(self):
        p = dom.paragraph()
        attr = p.attributes['class']
        self.is_(p.attributes['class'], attr)
        self.zero(p.classes)
        self.zero(p.attributes)
        
        for p in p.attributes[1:]:
            self.fail()

        attr.value = uuid4().hex
        self.one(p.classes)
        self.one(p.attributes)
        self.eq(p.attributes.first.value, attr.value)

    def it_calls_class_twice(self):
        # Calling p.classes raised an error in development. This is a
        # test to ensure the problem doesn't somehow resurface.
        p = dom.paragraph()
        self.expect(None, lambda: p.classes)
        self.expect(None, lambda: p.classes)

    def it_appends_classes(self):
        ''' Add by various methods '''
        p = dom.paragraph()
        self.eq(p.classes.html, p.attributes['class'].html)
        cls = dom.cssclass('my-class-1')
        p.attributes['class'].append(cls)
        self.is_(p.classes, p.attributes['class'])
        self.one(p.classes)
        self.true('my-class-1' in p.attributes['class'])

        expect = '<p class="my-class-1"></p>'
        self.eq(expect, p.html)

        p.classes.append('my-class-2')
        self.two(p.classes)
        self.true('my-class-2' in p.classes)

        expect = self.dedent('''
        <p class="%s">
        </p>
        ''' % ('my-class-1 my-class-2', ))
        self.eq(expect, p.pretty)

        p.classes += 'my-class-3'
        self.three(p.classes)
        self.eq(p.classes[2], 'my-class-3')

        expect = self.dedent('''
        <p class="%s">
        </p>
        ''', 'my-class-1 my-class-2 my-class-3')
        self.eq(expect, p.pretty)

        ''' Re-add the same class and expect an exception '''
        for i in range(1, 4):
            cls = 'my-class-%s' % str(i)
            self.expect(
                dom.ClassExistsError, 
                lambda: p.classes.append(dom.cssclass(cls))
            )

            self.expect(
                dom.ClassExistsError, 
                lambda: p.classes.append(cls)
            )

            def f():
                p.classes += cls

            self.expect(
                dom.ClassExistsError, 
                f
            )

    def it_adds_multiple_classes_at_a_time(self):
        ''' Add by various methods '''
        p = dom.paragraph()
        self.eq(p.classes.html, p.attributes['class'].html)

        expect = '<p></p>'
        self.eq(expect, p.html)

        p.classes += dom.cssclass('my-class-1 my-class-a')
        self.eq(p.classes.html, p.attributes['class'].html)
        self.two(p.classes)
        self.two(p.attributes['class'])

        expect = self.dedent('''
        <p class="%s">
        </p>
        ''', 'my-class-1 my-class-a')

        p.classes.append('my-class-2 my-class-b')
        self.four(p.classes)
        self.eq(p.classes.html, p.attributes['class'].html)
        self.eq(
            'class="my-class-1 my-class-a my-class-2 my-class-b"',
            p.classes.html
        )
        return

        expect = self.dedent('''
        <p class="%s">
        </p>
        ''', 'my-class-1 my-class-b')

        self.eq(expect, p.html)

        p.classes.append('my-class-2', 'my-class-c')
        self.four(p.classes)
        self.eq(
            'class="my-class-1 my-class-b my-class-2 my-class-c"',
            p.classes.html
        )

        expect = self.dedent('''
        <p class="%s">
        </p>
        ''', 'my-class-1 my-class-b my-class-2 my-class-c')

        self.eq(expect, p.html)

        p.classes += 'my-class-3', 'my-class-d'
        self.six(p.classes)

        expect = (
            'class="my-class-1 my-class-b '
            'my-class-2 my-class-c '
            'my-class-3 my-class-d"'
        )

        self.eq(expect, p.classes.html)

        p.classes += 'my-class-4 my-class-e'
        self.eight(p.classes)

        expect = (
            'class="my-class-1 my-class-b '
            'my-class-2 my-class-c '
            'my-class-3 my-class-d '
            'my-class-4 my-class-e"'
        )

        self.eq(expect, p.classes.html)

    def it_removes_classes(self):
        p = dom.paragraph()
        p.classes += 'c1 c2 c3 c4 c5 c6 c7 c8'
        self.eight(p.classes)

        p.classes.remove('c4')
        self.seven(p.classes)
        self.eq('class="c1 c2 c3 c5 c6 c7 c8"', p.classes.html)

        p.classes -= 'c3'
        self.six(p.classes)
        self.eq('class="c1 c2 c5 c6 c7 c8"', p.classes.html)

        del p.classes['c2']
        self.five(p.classes)
        self.eq('class="c1 c5 c6 c7 c8"', p.classes.html)

    def it_removes_multiple_classes(self):
        p = dom.paragraph()
        p.classes += 'c1 c2 c3 c4 c5 c6 c7 c8'
        self.eight(p.classes)

        p.classes.remove('c1 c8')
        self.six(p.classes)
        self.eq('class="c2 c3 c4 c5 c6 c7"', p.classes.html)

        p.classes -= 'c2', 'c7'
        self.four(p.classes)
        self.eq('class="c3 c4 c5 c6"', p.classes.html)

        rm = '%s %s' % (uuid4().hex, uuid4().hex)
        self.expect(IndexError, lambda: p.classes.remove(rm))

class dom_html(tester.tester):
    def it_calls_html_with_text_nodes(self):
        return 
        # TODO The first html prints .pretty with line feeds
        # (incorrectly). However, html1.pretty is free of those line
        # feeds.
        html = dom.html(Shakespeare)

        html1 = dom.html(html.html)
        self.eq(html.pretty, html1.pretty)

    def it_morphs(self):
        # When dom.html is given a string, it morphs into a subtype of
        # `elements`. When single str argument is given, it remains a
        # dom.html.
        self.type(dom.html, dom.html())
        self.type(dom.elements, dom.html('<p></p>'))
    
    def it_raises_on_unclosed_tags(self):
        html = self.dedent('''
        <body>
          <p>
        </body>
        ''')

        ex = self.expect(dom.HtmlParseError, lambda: dom.html(html))

        if type(ex) is dom.HtmlParseError:
            self.eq((2, 2), (ex.line, ex.column))

    def it_doesnt_raise_on_unnested_comment(self):
        html = self.dedent('''
          <!-- A comment -->
          <p>
            A paragraph.
          </p>
        ''')

        self.expect(None, lambda: dom.html(html))

    def it_raises_on_unexpected_text(self):
        html = self.dedent('''
          Some unexpected text
          </p>
        </body>
        ''')

        ex = self.expect(dom.HtmlParseError, lambda: dom.html(html))

        if type(ex) is dom.HtmlParseError:
            self.eq((1, 0), (ex.line, ex.column))
        
    def it_parses(self):
        els = dom.html(TestHtml, ids=False)
        self.eq(TestHtmlMin, els.html)

    def it_doesnt_parse_decls(self):
        html = '''
        <!DOCTYPE html>
        <html>
        </html>
        '''

        self.expect(NotImplementedError, lambda: dom.html(html))

    def it_doesnt_parse_unknown_decls(self):
        # TODO The below dosen't work. The fake uknown declaration is
        # interpreted as a comment. The parses `unknown_decl` method is
        # never called. I'm not sure how to create an unknown
        # declaration. I also don't know why <!DERPTYPE herp> is
        # interpreted as a comment.
        return
        html = '''
        <html>
        <!DERPTYPE herp>
        </html>
        '''
        dom.html(html)
        self.expect(NotImplementedError, lambda: dom.html(html))

    def it_doesnt_parse_processing_instructions(self):
        html = '''
        <?xml version="1.0" encoding="UTF-8" ?>
        <html>
        </html>
        '''
        self.expect(NotImplementedError, lambda: dom.html(html))

class dom_markdown(tester.tester):
    def it_parses_code(self):
        md = dom.markdown('''
        Use the `printf()` function.
        ''')
        self.type(dom.code, md.first.elements.second)
        self.eq(
            'printf()', 
            md.first.elements.second.elements.first.html
        )

        md = dom.markdown('''
        ``There is a literal backtick (`) here.``
        ''')
        self.type(dom.code, md.first.elements.first)
        self.eq(
            'There is a literal backtick (`) here.', 
            md.first.elements.first.elements.first.html
        )

        md = dom.markdown('''
        A single backtick in a code span: `` ` ``

        A backtick-delimited string in a code span: `` `foo` ``
        ''')
        self.type(dom.code, md.first.elements.second)
        self.eq('`', md.first.elements.second.elements.first.html)
        self.type(dom.code, md.second.elements.second)
        self.eq('`foo`', md.second.elements.second.elements.first.html)

        md = dom.markdown('''
        Please don't use any `<blink>` tags.
        ''')
        self.type(dom.code, md.first.elements.second)

        self.eq(
            '&lt;blink&gt;', 
            md.first.elements.second.elements.first.html
        )

        md = dom.markdown('''
        `&#8212;` is the decimal-encoded equivalent of `&mdash;`.
        ''')

        self.type(dom.code, md.first.elements.first)
        self.eq(
            '&amp;#8212;', 
            md.first.elements.first.elements.first.html
        )
        self.eq(
            '&amp;mdash;', 
            md.first.elements.third.elements.first.html
        )

    def it_parses_images(self):
        md = dom.markdown('''
        ![Alt text](/path/to/img.jpg)

        ![Alt text](/path/to/img.jpg "Optional title")
        ''')
        img = md.first.elements.first
        self.type(dom.img, img)
        self.eq('Alt text', img.alt)
        self.eq('/path/to/img.jpg', img.src)

        img = md.second.elements.first
        self.type(dom.img, img)
        self.eq('Alt text', img.alt)
        self.eq('/path/to/img.jpg', img.src)
        self.eq('Optional title', img.title)

        md = dom.markdown('''
        ![Alt text][id]

        [id]: url/to/image  "Optional title attribute"
        ''')

        img = md.first.elements.first
        self.type(dom.img, img)
        self.eq('url/to/image', img.src)
        self.eq('Optional title attribute', img.title)
        
    def it_parses_code_blocks(self):
        md = dom.markdown('''
        This is a normal paragraph:

            # This is a code block.
            print('Hello, World')
            sys.exit(0)


        This is another paragraph.
        ''')

        self.type(dom.paragraph, md.first)

        self.eq(
            'This is a normal paragraph:', 
            md.first.elements.first.html
        )

        self.type(dom.pre, md.second)
        self.type(dom.code, md.second.elements.first)

        self.type(dom.paragraph, md.third)
        self.eq(
            'This is another paragraph.', 
            md.third.elements.first.html
        )

        p1, p2 = md['p']
        pre, code = md['pre, code']

        expect = self.dedent('''
        <p>
          This is a normal paragraph:
        </p>
        <pre>
          <code>
            # This is a code block.
            print(&#x27;Hello, World&#x27;)
            sys.exit(0)
          </code>
        </pre>
        <p>
          This is another paragraph.
        </p>
        '''
        )

        self.eq(expect, md.pretty)

    def it_parses_horizontal_rules(self):
        md = dom.markdown('''
        * * *

        ***

        *****

        - - -

        ---------------------------------------
        ''')
        self.five(md)
        for hr in md:
            self.type(dom.hr, hr)

    def it_parses_inline_links(self):
        md = dom.markdown('''
        This is [an example](http://example.com/ "Title") inline link.

        [This link](http://example.net/) has no title attribute.
        ''')

        self.two(md)
        self.three(md.first.elements)
        self.type(dom.a, md.first.elements.second)
        self.two(md.first.elements.second.attributes)
        self.eq('Title', md.first.elements.second.title)
        self.eq('http://example.com/', md.first.elements.second.href)
        self.two(md.second.elements)
        self.type(dom.a, md.second.elements.first)
        self.one(md.second.elements.first.attributes)

        self.is_(None, md.second.elements.first.title)
        self.false(md.second.elements.first.attributes['title'].isdef)
        self.eq('http://example.net/', md.second.elements.first.href)

        md = dom.markdown('See my [About](/about/) page for details.')
        self.one(md)
        self.type(dom.p, md.first)
        self.type(dom.a, md.first.elements.second)
        self.eq('/about/', md.first.elements.second.href)

        defs = [
          '[id]: http://example.com/  "Optional Title Here"',

          # NOTE Single quotes don't work here which is strangly
          # consistent with a bug noted on the official Markdown page:
          # "NOTE: There is a known bug in Markdown.pl 1.0.1 which
          # prevents single quotes from being used to delimit link
          # titles."
          # (https://daringfireball.net/projects/markdown/syntax#list)
          # "[id]: http://example.com/  'Optional Title Here'",

          '[id]: http://example.com/  (Optional Title Here)',
          '[ID]: <http://example.com/>  (Optional Title Here)',

          # NOTE This should probably work, but it dosen't in mistune,
          # "You can put the title attribute on the next line and use
          # extra spaces or tabs for padding, which tends to look better
          # with longer URLs:"
          #     [id]: http://example.com/longish/path/to/resource/here
          #         "Optional Title Here"
          # '[id]: http://example.com\n             "Optional Title Here"'
        ]

        for def_ in defs:
          md = dom.markdown('''
          This is [an example][id] reference-style link.
          %s
          ''' % def_)
          self.eq('http://example.com/', md[0].elements[1].href)
          self.eq('Optional Title Here', md[0].elements[1].title)


        md = dom.markdown('''
        [Google][]
        [Google]: http://google.com/
        ''')

        self.type(dom.a, md.first.elements.first)
        self.eq('Google', md.first.elements.first.elements.first.html)

        md = dom.markdown('''
        Visit [Daring Fireball][] for more information.
        [Daring Fireball]: http://daringfireball.net/
        ''')

        self.type(dom.a, md.first.elements.second)
        self.eq('Daring Fireball', md[0].elements[1].elements[0].html)

    def it_parses_emphasis(self):
        # NOTE "emphasis" here includes both <em> and <strong>

        md = dom.markdown('''
        *single asterisks*

        _single underscores_

        **double asterisks**

        __double underscores__
        ''')
        self.type(dom.em, md.first.elements.first)
        self.type(dom.em, md.second.elements.first)
        self.type(dom.strong, md.third.elements.first)
        self.type(dom.strong, md.fourth.elements.first)

        # NOTE The second one, un_frigging_believable, correctly does
        # not result in emphasization.
        md = dom.markdown('''
        un*frigging*believable

        un_frigging_believable

        un**frigging**believable

        un__frigging__believable
        ''')
        self.type(dom.em, md.first.elements.second)
        # The second one doesn't cause emphasization so comment this
        # out.
        # self.type(dom.em, md.second.elements.second)
        self.type(dom.strong, md.third.elements.second)
        self.type(dom.strong, md.fourth.elements.second)

        md = dom.markdown('''
        \*this text is surrounded by literal asterisks\*
        ''')

        self.eq(
            '*this text is surrounded by literal asterisks*',
            md.first.elements.first.html
        )

    def it_parses_inline_html(self):
        md = dom.markdown('''
          This is a regular paragraph.

          <table>
            <tr>
              <td>Foo</td>
            </tr>
          </table>

          This is another regular paragraph.
        ''')

        self.three(md)
        self.type(dom.paragraph, md.first)
        self.type(dom.table, md.second)
        self.one(md.second.children)
        self.type(dom.tr, md.second.children.first)
        self.one(md.second.children.first.children)
        self.type(
            dom.td, 
            md.second.children.first.children.first
        )
        self.one(md.second.children.first.children.first.elements)
        self.type(
            dom.text, 
            md.second.children.first.children.first.elements.first
        )

        self.eq(
            'Foo',
            md.second.children.first.children.first.elements.first.html
        )
        self.type(dom.paragraph, md.third)

        md = dom.markdown('<http://example.com/>')
        a = md.first.elements.first
        self.type(dom.a, a)
        self.eq('http://example.com/', a.href)
        self.eq('http://example.com/', a.elements.first.html)

        # NOTE The Markdown spec says the below should obscure the email
        # address by using "randomized decimal and hex entity-encoding"
        # to conceal the address from naive spambots. However, mistune
        # does not do this and instead creates a typical mailto: link.
        # See
        # https://daringfireball.net/projects/markdown/syntax#autolink
        # for more information.
        md = dom.markdown('<address@example.com>')
        a = md.first.children.first
        self.type(dom.a, a)
        self.eq('mailto:address@example.com', a.href)
        self.eq('address@example.com', a.elements.first.html)

    def it_parses_html_entities(self):
        md = dom.markdown('AT&T')

        p = md['p'].first

        expect = self.dedent('''
        <p>
          AT&amp;T
        </p>
        ''')

        self.eq(expect, md.pretty)

        md = dom.markdown('&copy;')
        p = md['p'].first
        expect = self.dedent('''
        <p>
          &copy;
        </p>
        ''')

        self.eq(expect, md.pretty)

        md = dom.markdown('4 < 5')
        p = md['p'].first

        expect = self.dedent('''
        <p>
          4 &lt; 5
        </p>
        ''')

        self.eq(expect, md.pretty)

    def it_adds_linebreaks_to_paragraphs(self):
        # "When you do want to insert a <br /> break tag using Markdown,
        # you end a line with two or more spaces, then type return."
        # https://daringfireball.net/projects/markdown/syntax#block
        md = self.dedent('''
        This is a paragraph with a  
        hard line break.
        ''')

        md = dom.markdown(md)
        p, br = md['p, br']

        expect = self.dedent('''
        <p>
          This is a paragraph with a
          <br>
          hard line break.
        </p>
        ''')
        
        self.eq(expect, md.pretty)

    def it_raises_with_nonstandard_inline_html_tags(self):
        md = self.dedent('''
          Below is some inline HTML with a non-standard tag

          <ngderp>
            Foo
          </ngderp>

        ''')
        self.expect(NotImplementedError, lambda: dom.markdown(md))

    def it_parses_headers(self):
        # Setext-style headers 
        md = dom.markdown('''
        This is an H1
        ============

        This is an H2
        -------------
        ''')

        self.two(md)
        self.type(dom.h1, md.first)
        self.eq('This is an H1', md.first.elements.first.html)
        self.type(dom.h2, md.second)
        self.eq('This is an H2', md.second.elements.first.html)

        # Atx-style headers
        md = dom.markdown('''
        # This is an H1

        ## This is an H2

        ###### This is an H6
        ''')
        self.three(md)
        self.type(dom.h1, md.first)
        self.eq('This is an H1', md.first.elements.first.html)
        self.type(dom.h2, md.second)
        self.eq('This is an H2', md.second.elements.first.html)
        self.type(dom.h6, md.third)
        self.eq('This is an H6', md.third.elements.first.html)
    
    def it_parses_blockquotes(self):
        md = dom.markdown('''
        > This is a blockquote with two paragraphs. Lorem ipsum dolor
        > sit amet,
        > consectetuer adipiscing elit. Aliquam hendrerit mi posuere
        > lectus.
        > Vestibulum enim wisi, viverra nec, fringilla in, laoreet
        > vitae, risus.
        > 
        > Donec sit amet nisl. Aliquam semper ipsum sit amet velit.
        > Suspendisse
        > id sem consectetuer libero luctus adipiscing.
        ''')

        self.one(md)
        self.type(dom.blockquote, md.first)

        self.four(md.first.elements)
        self.type(dom.paragraph, md.first.elements.first)
        self.type(dom.text, md.first.elements.second)
        self.type(dom.paragraph, md.first.elements.third)
        self.type(dom.text, md.first.elements.fourth)

        md = dom.markdown('''
        > This is a blockquote with two paragraphs. Lorem ipsum dolor sit amet,
        consectetuer adipiscing elit. Aliquam hendrerit mi posuere lectus.
        Vestibulum enim wisi, viverra nec, fringilla in, laoreet vitae, risus.

        > Donec sit amet nisl. Aliquam semper ipsum sit amet velit. Suspendisse
        id sem consectetuer libero luctus adipiscing.
        ''')

        self.one(md)
        self.type(dom.blockquote, md.first)

        self.four(md.first.elements)
        self.type(dom.paragraph, md.first.elements.first)
        self.type(dom.text, md.first.elements.second)
        self.type(dom.paragraph, md.first.elements.third)
        self.type(dom.text, md.first.elements.fourth)

        # Nested

        md = dom.markdown('''
        > This is the first level of quoting.
        >
        > > This is nested blockquote.
        >
        > Back to the first level.
        ''')
        self.one(md)
        self.type(dom.blockquote, md.first)

        self.six(md.first.elements)
        self.type(dom.paragraph, md.first.elements.first)
        self.type(dom.text, md.first.elements.second)
        self.type(dom.blockquote, md.first.elements.third)
        self.type(dom.text, md.first.elements.fourth)
        self.type(dom.paragraph, md.first.elements[2].elements.first)
        self.type(dom.paragraph, md.first.elements.fifth)
        self.type(dom.text, md.first.elements.sixth)

        md = dom.markdown('''
        > ## This is a header.
        > 
        > 1.   This is the first list item.
        > 2.   This is the second list item.
        > 
        > Here's some example code:
        > 
        >     return shell_exec("echo $input | $markdown_script");

        ''')

        self.one(md)
        self.type(dom.blockquote, md.first)
        self.type(dom.h2, md.first.elements.first)
        self.type(dom.text, md.first.elements.second)
        self.type(dom.li, md.first.elements.third.elements.second)
        self.type(dom.li, md.first.elements.third.elements.fourth)
        self.type(dom.text, md.first.elements.fourth)
        self.type(dom.p, md.first.elements.fifth)
        self.type(dom.text, md.first.elements.fourth)
        self.type(dom.p, md.first.elements.fifth)
        self.type(dom.text, md.first.elements.fifth.elements.first)
        self.type(dom.code, md.first.elements[6].elements.first)

    def it_parses_lists(self):
        for bullet in '*', '+', '-':
          md = self.dedent('''
          ?   Red
          ?   Green
          ?   Blue
          ''')

          md = md.replace('?', bullet)

          md = dom.markdown(md)

          self.one(md)
          self.type(dom.ul, md.first)
          self.seven(md.first.elements)
          self.type(dom.text, md.first.elements.first)
          self.type(dom.li, md.first.elements.second)
          self.type(dom.text, md.first.elements.third)
          self.type(dom.li, md.first.elements.fourth)
          self.type(dom.text, md.first.elements.fifth)
          self.type(dom.li, md.first.elements.sixth)
          self.type(dom.text, md.first.elements.seventh)

        # NOTE Ordered list are created by starting the lines with
        # orditals (1., 2., etc). However, "he actual numbers you use to
        # mark the list have no effect on the HTML output Markdown
        # produces.".
        # (https://daringfireball.net/projects/markdown/syntax#list). So
        # the below test is writtes 1, 3, 2.
        md = dom.markdown('''
        1.  Bird
        3.  Parish
        2.  McHale
        ''')

        self.one(md)
        self.type(dom.ol, md.first)
        self.seven(md.first.elements)
        self.type(dom.text, md.first.elements.first)
        self.type(dom.li, md.first.elements.second)
        self.type(dom.text, md.first.elements.third)
        self.type(dom.li, md.first.elements.fourth)
        self.type(dom.text, md.first.elements.fifth)
        self.type(dom.li, md.first.elements.sixth)

        for lazy in True, False:
            if lazy:
                md = dom.markdown('''
                *   Lorem ipsum dolor sit amet, consectetuer adipiscing elit.
                Aliquam hendrerit mi posuere lectus. Vestibulum enim
                wisi, viverra nec, fringilla in, laoreet vitae, risus.
                *   Donec sit amet nisl. Aliquam semper ipsum sit amet
                velit.  Suspendisse id sem consectetuer libero luctus
                adipiscing.
                ''')
            else:
                md = dom.markdown('''
                *   Lorem ipsum dolor sit amet, consectetuer adipiscing
                    elit.  Aliquam hendrerit mi posuere lectus.
                    Vestibulum enim wisi, viverra nec, fringilla in,
                    laoreet vitae, risus.
                *   Donec sit amet nisl. Aliquam semper ipsum sit amet
                    velit.  Suspendisse id sem consectetuer libero
                    luctus adipiscing.
                ''')
            self.one(md)
            self.type(dom.ul, md.first)
            self.two(md.first.children)
            self.type(dom.li, md.first.children.first)
            self.type(dom.li, md.first.children.second)

        md = dom.markdown('''
        *   Bird

        *   Magic
        ''')

        self.one(md)
        self.type(dom.ul, md.first)
        self.two(md.first.children)
        self.one(md.first.children.first.children)
        self.type(dom.p, md.first.children.first.children.first)
        self.type(dom.p, md.first.children.second.children.first)

        for lazy in True, False:
            if lazy:
              md = dom.markdown('''
              *   This is a list item with two paragraphs.

                  This is the second paragraph in the list item. You're
              only required to indent the first line. Lorem ipsum dolor
              sit amet, consectetuer adipiscing elit.

              *   Another item in the same list.
              ''')
            else:
                md = dom.markdown('''
                1.  This is a list item with two paragraphs. Lorem ipsum
                    dolor sit amet, consectetuer adipiscing elit.
                    Aliquam hendrerit mi posuere lectus.

                    Vestibulum enim wisi, viverra nec, fringilla in,
                    laoreet vitae, risus. Donec sit amet nisl. Aliquam
                    semper ipsum sit amet velit.

                2.  Suspendisse id sem consectetuer libero luctus
                    adipiscing.

              ''')
            self.one(md)
            self.type(dom.ul if lazy else dom.ol, md.first)
            self.two(md.first.children)
            self.two(md.first.children.first.children)
            self.type(dom.p, md.first.children.first.children.first)
            self.type(dom.p, md.first.children.second.children.first)

        md = dom.markdown('''
        *   A list item with a blockquote:

            > This is a blockquote
            > inside a list item.
        ''')

        self.one(md)
        self.type(dom.ul, md.first)
        self.type(dom.li, md.first.children.first)
        self.two(md.first.children.first.children)
        self.type(dom.p, md.first.children.first.children.first)
        self.type(dom.blockquote, md[0].children[0].children[1])

        md = dom.markdown('''
        *   A list item with a code block:

                <code goes here>
        ''')
        self.one(md)
        self.type(dom.ul, md.first)
        self.one(md.first.children)
        self.two(md.first.children.first.children)
        self.type(dom.p, md.first.children.first.children.first)
        self.type(dom.pre, md.first.children.first.children.second)
        self.one(md.first.children.first.children.second.children)
        self.type(
            dom.code,
            md.first.children.first.children.second.children.first
        )

        md = dom.markdown('''
        1986\. What a great season.
        ''')
        self.one(md)
        self.type(dom.p, md.first)

    def it_parses_paragraph(self):
        ''' Parse a simple, one-line paragraph '''
        md = dom.markdown('''
        This is a paragraph.
        ''')

        self.one(md)
        self.type(dom.paragraph, md.first)
        p = md['p'].first

        expect = self.dedent('''
        <p>
          This is a paragraph.
        </p>
        ''')

        self.eq(expect, md.first.pretty)

        ''' Parse two paragraphs '''
        md = dom.markdown('''
        Parcite, mortales, dapibus temerare nefandis
        corpora! Sunt fruges, sunt deducentia ramos
        pondere poma suo tumidaeque in vitibus uvae,
        sunt herbae dulces, sunt quae mitescere flamma
        mollirique queant; nec vobis lacteus umor
        eripitur, nec mella thymi redolentia flore:
        prodiga divitias alimentaque mitia tellus
        suggerit atque epulas sine caede et sanguine praebet.

        Carne ferae sedant ieiunia, nec tamen omnes:
        quippe equus et pecudes armentaque gramine vivunt.
        At quibus ingenium est inmansuetumque ferumque,
        Armeniae tigres iracundique leones
        cumque lupis ursi, dapibus cum sanguine gaudent.
        Heu quantum scelus est in viscera viscera condi
        congestoque avidum pinguescere corpore corpus
        alteriusque animantem animantis vivere leto!
        Scilicet in tantis opibus, quas optima matrum
        terra parit, nil te nisi tristia mandere saevo
        vulnera dente iuvat ritusque referre Cyclopum,
        nec, nisi perdideris alium, placare voracis
        et male morati poteris ieiunia ventris?
        ''')

        self.two(md)
        self.type(dom.paragraph, md.first)
        self.type(dom.paragraph, md.second)

        expect = self.dedent('''
        <p>
          Parcite, mortales, dapibus temerare nefandis
          corpora! Sunt fruges, sunt deducentia ramos
          pondere poma suo tumidaeque in vitibus uvae,
          sunt herbae dulces, sunt quae mitescere flamma
          mollirique queant; nec vobis lacteus umor
          eripitur, nec mella thymi redolentia flore:
          prodiga divitias alimentaque mitia tellus
          suggerit atque epulas sine caede et sanguine praebet.
        </p>
        <p>
          Carne ferae sedant ieiunia, nec tamen omnes:
          quippe equus et pecudes armentaque gramine vivunt.
          At quibus ingenium est inmansuetumque ferumque,
          Armeniae tigres iracundique leones
          cumque lupis ursi, dapibus cum sanguine gaudent.
          Heu quantum scelus est in viscera viscera condi
          congestoque avidum pinguescere corpore corpus
          alteriusque animantem animantis vivere leto!
          Scilicet in tantis opibus, quas optima matrum
          terra parit, nil te nisi tristia mandere saevo
          vulnera dente iuvat ritusque referre Cyclopum,
          nec, nisi perdideris alium, placare voracis
          et male morati poteris ieiunia ventris?
        </p>
        ''')

        self.eq(expect, md.pretty)

class test_selectors(tester.tester):
    # TODO Running all the tests in test_selectors takes around 10
    # seconds at the time of this writting. We should run the profiler
    # on the following test:
    #
    #     python3 test.py test_selectors
    #
    # There may be some hotspots that could be optimized to reduce the
    # time spent running these tests.

    @property
    def _shakespear(self):
        if not hasattr(self, '_spear'):
            self._spear = dom.html(Shakespeare, ids=False)
        return self._spear

    @property
    def _listhtml(self):
        if not hasattr(self, '_lis'):
            self._lis = dom.html(ListHtml)
        return self._lis

    def it_selects_lang(self):
        html = dom.html('''
        <html lang="en">
          <head></head>
          <body>
            <div>
              <p id="enp">
                My language is 'en' because it was specified in
                the root html tag.
              </p>
            </div>
            <section lang="fr">
               <p id="frp">Comment dites-vous "Bonjour" en Espanol?</p>
               <div>
                   <blockquote lang="es">
                     <p id="esp">
                       My language will be Spainish.
                     </p>
                   </blockquote>
               </div>
            </section>
            <section lang="DE">
              <p id="dep">German paragraph</p>
            </section>
          </body>
      </html>
        ''')

        sels = [
            'p:lang(fr)',
            'p:lang(FR)',
        ]

        for sel in sels:
            els = html[sel]
            self.one(els)
            self.type(dom.p, els.first)
            self.eq('frp', els.first.id)

        sels = [
            'p:lang(de)',
            'p:lang(DE)',
        ]
        for sel in sels:
            els = html[sel]
            self.one(els)
            self.type(dom.p, els.first)
            self.eq('dep', els.first.id)
            
        sels = [
            'p:lang(es)',
            'p:lang(ES)',
        ]
        for sel in sels:
            els = html[sel]
            self.one(els)
            self.type(dom.p, els.first)
            self.eq('esp', els.first.id)
            
        sels = [
            'p:lang(en)',
            'p:lang(EN)',
        ]
        for sel in sels:
            els = html[sel]
            self.one(els)
            self.type(dom.p, els.first)
            self.eq('enp', els.first.id)

        html = dom.html('''
        <html>
            <head></head>
            <body>
                <div lang="en">
                    <p id="enp">
                        Regural english
                    </p>
                </div>
                <section lang="en-GB-oed">
                    <p id="engboed">English, Oxford English Dictionary spelling</p>

                    <div>
                        <blockquote lang="zh-Hans">
                            <div>
                                <p id="zhh">Simplified Chinese</p>
                            </div>
                        </blockquote>
                    </div>
                </section>
            </body>
        </html>
        ''')

        sels = [
            'p:lang(en)',
            'p:lang(EN)',
        ]
        for sel in sels:
            els = html[sel]
            self.two(els)
            self.type(dom.p, els.first)
            self.eq('enp', els.first.id)
            self.type(dom.p, els.second)
            self.eq('engboed', els.second.id)

        sels = [
            'p:lang(en-GB)',
            'p:lang(en-GB-oed)',
            'p:lang(EN-GB-OED)',
            'p:lang(en-gb-oed)',
        ]

        for sel in sels:
            els = html[sel]
            self.one(els)
            self.type(dom.p, els.first)
            self.eq('engboed', els.first.id)

        sels = [
            'p:lang(zh)',
            'p:lang(zh-hans)',
            'p:lang(zh-HANS)',
        ]

        for sel in sels:
            els = html[sel]
            self.one(els)
            self.type(dom.p, els.first)
            self.eq('zhh', els.first.id)

        sels = [
            '*:lang(zh)',
            ':lang(zh-hans)',
        ]

        for sel in sels:
            els = html[sel]
            self.three(els)
            self.type(dom.blockquote, els.first)
            self.type(dom.div, els.second)
            self.type(dom.p, els.third)
            self.eq('zhh', els.third.id)

        sels = [
            'p:lang(EN-GB-)',
            'p:lang(EN-)',
            'p:lang(E)',
        ]

        for sel in sels:
            els = html[sel]
            self.zero(els)

    def it_selects_with_groups(self):
        html = self._shakespear

        sels = [
            'h2, h3',
            'H2, h3',
        ]

        for sel in sels:
            els = html[sel]

            self.two(els)
            self.type(dom.elements, els)
            self.type(dom.h2, els.first)
            self.type(dom.h3, els.second)
            self.eq(els.first.elements.first.html, 'As You Like It')
            self.eq(
                els.second.elements.first.html, 
                'ACT I, SCENE III. A room in the palace.'
            )

    def it_raises_on_invalid_identifiers(self):
        """ In CSS, identifiers (including element names, classes, and
        IDs in selectors) can contain only the characters [a-zA-Z0-9]
        and ISO 10646 characters U+00A0 and higher, plus the hyphen (-)
        and the underscore (_); they cannot start with a digit, two
        hyphens, or a hyphen followed by a digit. Identifiers can also
        contain escaped characters and any ISO 10646 character as a
        numeric code (see next item). For instance, the identifier
        “B&W?” may be written as “B\&W\?” or “B\26 W\3F”.

            -- W3C Specification
        """
        
        ''' Valids '''
        sels = [
            'id#foo123',
            'id#foo-_',
            'id#-_foo',
            'id#f-_oo',

            'id[foo123]',
            'id[foo-_]',
            'id[-_foo]',
            'id[f-_oo]',

            'id[foo=foo123]',
            'id[foo=foo-_]',
            'id[foo=-_foo]',
            'id[foo=f-_oo]',

            'id.foo123',
            'id.foo-_',
            'id.-_foo',
            'id.f-_oo',
        ]

        for sel in sels:
            self.expect(None, lambda: dom.selectors(sel))

        ''' Invalids '''
        sels = [
            'id#--foo',
            'id#123',
            'id#123foo',
            'id#-1foo',

            'id[--foo]',
            'id[123]',
            'id[123foo]',
            'id[-1foo]',

            'id[foo=--foo]',
            'id[foo=123]',
            'id[foo=123foo]',
            'id[foo=-1foo]',

            'id.--foo',
            'id.123',
            'id.123foo',
            'id.-1foo',
        ]

        for sel in sels:
            self.expect(
                dom.CssSelectorParseError, 
                lambda: dom.selectors(sel)
            )

    def it_selects_with_groups_element_to_class(self):
        html = self._shakespear
        sels = [
            'h2, .thirdClass',
            'h2, *.thirdClass',
            'h2, div.thirdClass',

            'h2[id^="023338d1"], .thirdClass',
            '[id^="023338d1"], *.thirdClass',
            '*[id^="023338d1"], div.thirdClass',

            '*.header, .thirdClass',
            '.header, *.thirdClass',
            'h2.header, div.thirdClass',
        ]

        for sel in sels:
            els = html[sel]
            self.two(els)
            self.type(dom.h2, els.first)
            self.eq('scene1', els.second.id)

        sels = [
            '.thirdClass, h2',
            '*.thirdClass, h2',
            'div.thirdClass, h2',

            '.thirdClass, h2[id^="023338d1"]',
            '*.thirdClass, [id^="023338d1"]',
            'div.thirdClass, *[id^="023338d1"]',

            '.thirdClass, *.header',
            '*.thirdClass, .header',
            'div.thirdClass, h2.header',
        ]

        for sel in sels:
            els = html[sel]
            self.two(els)
            self.eq('scene1', els.first.id)
            self.type(dom.h2, els.second)

    def it_selects_with_groups_element_to_attributes(self):
        html = self._shakespear

        sels = [
            'h2, [title=wtf]',
            'h2, *[title=wtf]',
            'h2, div[title=wtf]',

            'h2[id^="023338d1"], [title=wtf]',
            '[id^="023338d1"], *[title=wtf]',
            '*[id^="023338d1"], div[title=wtf]',

            '*.header, [title=wtf]',
            '.header, *[title=wtf]',
            'h2.header, div[title=wtf]',
        ]

        for sel in sels:
            els = html[sel]
            self.two(els)
            self.type(dom.h2, els.first)
            self.type(dom.div, els.second)
            self.eq('wtf', els.second.title)

        sels = [
            '[title=wtf], h2',
            '*[title=wtf], h2',
            'div[title=wtf], h2',

            '[title=wtf], h2[id^="023338d1"]',
            '*[title=wtf], [id^="023338d1"]',
            'div[title=wtf], *[id^="023338d1"]',

            '[title=wtf], *.header',
            '*[title=wtf], .header',
            'div[title=wtf], h2.header',
        ]

        for sel in sels:
            els = html[sel]

            self.two(els)
            self.type(dom.div, els.first)
            self.eq('wtf', els.first.title)
            self.type(dom.h2, els.second)

    def it_selects_with_groups_element_to_identifiers(self):
        html = self._shakespear

        sels = [
            '#herp,                  #speech16',
            '*#herp,                 *#speech16',
            'div#herp,               div#speech16',

            '[title=wtf],            #speech16',
            '*[title=wtf],           *#speech16',
            'div[title=wtf],         div#speech16',

            '[title=wtf].dialog,     #speech16',
            '*[title=wtf].dialog,    *#speech16',
            'div[title=wtf].dialog,  div#speech16',
        ]

        for sel in sels:
            els = html[sel]
            self.two(els)
            self.eq('herp', els.first.id)
            self.eq('speech16', els.second.id)

        sels = [
            '#speech16,     #herp                  ',
            '*#speech16,    *#herp                 ',
            'div#speech16,  div#herp               ',

            '#speech16,     [title=wtf]            ',
            '*#speech16,    *[title=wtf]           ',
            'div#speech16,  div[title=wtf]         ',

            '#speech16,     [title=wtf].dialog     ',
            '*#speech16,    *[title=wtf].dialog    ',
            'div#speech16,  div[title=wtf].dialog  ',
        ]

        for sel in sels:
            els = html[sel]
            self.two(els)
            self.eq('speech16', els.first.id)
            self.eq('herp', els.second.id)

    def it_selects_with_child_combinator(self):
        html = dom.html(AdjacencyHtml)

        ''' Two child combinators '''
        sel = 'div > p'
        els = html[sel]
        self.one(els)
        self.type(dom.p, els.first)
        self.eq('child-of-div', els.first.id)

        bads = [
            'div > xp'
            'xdiv > p'
        ]

        self.all(html[bad].isempty for bad in bads)

        ''' Three child combinators '''
        sel = 'div > p > span'
        els = html[sel]
        self.one(els)
        self.type(dom.span, els.first)
        self.eq('child-of-p-of-div', els.first.id)

        bads = [
            'xdiv > p > span'
            'div > xp > span'
            'div > p > xspan'
        ]

        self.all(html[bad].isempty for bad in bads)

        ''' A descendant combinator with two three combinators '''
        sel = 'html div > p > span'
        els = html[sel]
        self.type(dom.span, els.first)
        self.eq('child-of-p-of-div', els.first.id)

        # Change the above descendant combinator to child combinator and
        # it should produce zero results. 
        sel = 'html > div > p > span'
        els = html[sel]
        self.zero(els)

        ''' A simple child combinator expression to produce two results
        '''
        els = html['p > span']
        self.two(els)
        self.type(dom.span, els.first)
        self.type(dom.span, els.second)
        self.eq('child-of-p-of-div', els.first.id)
        self.eq('child-of-p-of-h2', els.second.id)

        # Try out some chained seletors
        sels = [
            'p > span#child-of-p-of-h2',
            'p#child-of-h2 > span#child-of-p-of-h2',
            'p#child-of-h2 > span',
            'p.p-header > span',
        ]

        for sel in sels:
            els = html[sel]
            self.one(els)
            self.type(dom.span, els.first)
            self.eq('child-of-p-of-h2', els.first.id)
    
    def it_selects_with_next_and_subsequent_sibling_combinator(self):
        html = dom.html('''
        <div>
          <p foo="bar"></p>
          <p id="1"></p>
          <p id="2"></p>
          <p id="3"></p>
          <p id="4"></p>
          <p baz=baz></p>
          <p id="5"></p>
          <p id="6"></p>
          <p id="7"></p>
          <p id="8"></p>
        </div>
        ''')

        sels = [
            'div p[foo=bar] + p ~ p[baz=baz] + p ~ p',
        ]

        for sel in sels:
            els = html[sel]
            self.three(els)
            self.eq([6, 7, 8], [int(x) for x in els.pluck('id')])

        html = dom.html('''
        <div>
          <p foo="bar">
            <div>
              <p foo="baz"></p>
              <p id="1"></p>
              <p id="2"></p>
              <p id="3"></p>
              <p id="4"></p>
            </div>
            <div>
              <p foo="baz"></p>
              <p id="5"></p>
              <p id="6"></p>
              <p id="7"></p>
              <p id="8"></p>
            </div>
          </p>
          <p foo="quux">
            <div>
              <p foo="baz"></p>
              <p id="9"></p>
              <p id="10"></p>
              <p id="11"></p>
              <p id="12"></p>
            </div>
            <div>
              <p foo="baz"></p>
              <p id="13"></p>
              <p id="14"></p>
              <p id="15"></p>
              <p id="16"></p>
            </div>
          </p>
        </div>
        ''')

        sels = [
            'p[foo=bar] p[foo=baz] ~ p',
        ]

        for sel in sels:
            els = html[sel]
            self.eight(els)
            self.eq(
                [str(x) for x in list(range(1, 9))], 
                els.pluck('id')
            )

        html = dom.html('''
        <div>
          <p foo="bar"></p>
          <p id="1"></p>
          <p id="2"></p>
          <p id="3"></p>
          <p id="4"></p>
        </div>
        ''')

        sels = [
            '*   p[foo=bar] ~ p ~ p',
            'div p[foo=bar] ~ p ~ p',
            '    p[foo=bar] ~ p ~ p',
            '*   p[foo=bar] + p ~ p',
            'div p[foo=bar] + p ~ p',
            '    p[foo=bar] + p ~ p',
        ]

        for sel in sels:
            els = html[sel]
            self.three(els)
            self.eq('2', els.first.id)
            self.eq('3', els.second.id)
            self.eq('4', els.third.id)

        html = dom.html('''
        <div>
          <p foo="bar"></p>
          <p id="1"></p>
          <p id="2"></p>
          <p id="3"></p>
          <p id="4"></p>
          <p foo="baz"></p>
          <p id="5"></p>
          <p id="6"></p>
          <p id="7"></p>
          <p id="8"></p>
        </div>
        ''')

        sels = [
            '*   p[foo=baz] ~ p ~ p',
            'div p[foo=baz] ~ p ~ p',
            '    p[foo=baz] ~ p ~ p',
            '*   p[foo=baz] + p ~ p',
            'div p[foo=baz] + p ~ p',
            '    p[foo=baz] + p ~ p',
        ]

        for sel in sels:
            els = html[sel]
            self.three(els)
            self.eq('6', els.first.id)
            self.eq('7', els.second.id)
            self.eq('8', els.third.id)

        html = dom.html('''
        <div>
          <p foo="bar"></p>
          <p id="1"></p>
          <q id="2"></q>
          <p id="3"></p>
          <q id="4"></q>
          <p id="5"></p>
          <q id="6"></q>
          <p id="7"></p>
        </div>
        ''')

        sels = [
            '*   p[foo=bar] ~ p ~ q',
            'div p[foo=bar] ~ p ~ q',
            '    p[foo=bar] ~ p ~ q',
            '*   p[foo=bar] + p ~ q',
            'div p[foo=bar] + p ~ q',
            '    p[foo=bar] + p ~ q',
        ]

        for sel in sels:
            els = html[sel]
            self.three(els)
            self.eq('2', els.first.id)
            self.eq('4', els.second.id)
            self.eq('6', els.third.id)

        html = dom.html(AdjacencyHtml)

        sels = [
            'div ~ div ~ p + p',
        ]

        for sel in sels:
            els = html[sel]
            self.one(els)
            self.eq('after-the-adjacency-anchor', els.first.id)

        sels = [
            '*#first-div   ~ p + p',
            '#first-div    ~ p + p',
            'div#first-div ~ p + p',
        ]

        for sel in sels:
            els = html[sel]
            self.two(els)
            self.eq('immediatly-before-the-adjacency-anchor', els[0].id)
            self.eq('after-the-adjacency-anchor', els[1].id)
        
    def it_selects_with_next_sibling_combinator(self):
        html = dom.html(AdjacencyHtml)

        sels = [
            'p + p + div',
            'p + p + div#adjacency-anchor',

            'p '
            ' + p#immediatly-before-the-adjacency-anchor'
            ' + div#adjacency-anchor',

            'p#before-the-adjacency-anchor'
            ' + p#immediatly-before-the-adjacency-anchor'
            ' + div#adjacency-anchor',
        ]

        for sel in sels:
            els = html[sel]
            self.one(els)
            self.eq('adjacency-anchor', els[0].id, sel)

        sels = [
            'div + p + p'
        ]

        for sel in sels:
            els = html[sel]
            self.two(els)
            self.eq('immediatly-before-the-adjacency-anchor', els[0].id)
            self.eq('after-the-adjacency-anchor', els[1].id)

        sels = [
            'div#adjacency-anchor + p + p'
        ]

        for sel in sels:
            els = html[sel]
            self.one(els)
            self.eq('after-the-adjacency-anchor', els[0].id)

        sels = [
            'div + p + p',
            'p + p',
        ]
        for sel in sels:
            els = html[sel]
            self.two(els)
            self.eq('immediatly-before-the-adjacency-anchor', els[0].id)
            self.eq('after-the-adjacency-anchor', els[1].id)

        ''' Select the <p> immediatly after #adjacency-anchor '''
        sels = [
            '#adjacency-anchor + p',
            'div#adjacency-anchor + p',
            'div#adjacency-anchor + p#immediatly-after-the-adjacency-anchor',
        ]
        for sel in sels:
            els = html[sel]
            self.one(els)
            self.eq('immediatly-after-the-adjacency-anchor', els[0].id)

        ''' These should match nothing but are similar to the above'''
        sels = [
            '#adjacency-anchor + div',
            'div#adjacency-anchor + p.id-dont-exist',
            '#adjacency-anchor + '
                'p#ZZZimmediatly-after-the-adjacency-anchor',
        ]
        for sel in sels:
            els = html[sel]
            self.zero(els)

    def it_selects_with_subsequent_sibling_combinator(self):
        html = dom.html(AdjacencyHtml)

        sels = [
            'div ~ div p + q',
        ]

        for sel in sels:
            els = html[sel]
            self.one(els)
            self.eq('second-child-of-h2', els.first.id)

        sels = [
            'html > body > div#adjacency-anchor ~ p',
            'html body > div#adjacency-anchor ~ p',
            'body > div#adjacency-anchor ~ p',
            'body div#adjacency-anchor ~ p',
            'div#adjacency-anchor ~ p',
            '#adjacency-anchor ~ p',
        ]

        for sel in sels:
            els = html[sel]
            self.two(els)
            self.eq('immediatly-after-the-adjacency-anchor', els.first.id)
            self.eq('after-the-adjacency-anchor', els.second.id)

        els = html['div ~ p']
        self.four(els)
        self.eq('before-the-adjacency-anchor', els.first.id)
        self.eq('immediatly-before-the-adjacency-anchor', els.second.id)
        self.eq('immediatly-after-the-adjacency-anchor', els.third.id)
        self.eq('after-the-adjacency-anchor', els.fourth.id)

        els = html['div ~ *']
        self.five(els)
        self.eq('before-the-adjacency-anchor', els.first.id)
        self.eq('immediatly-before-the-adjacency-anchor', els.second.id)
        self.eq('adjacency-anchor', els.third.id)
        self.eq('immediatly-after-the-adjacency-anchor', els.fourth.id)
        self.eq('after-the-adjacency-anchor', els.fifth.id)

        els = html['* ~ *']
        self.all(
            type(x) not in (dom.html, dom.head, dom.h2) for x in els
        )

        els = html['head ~ body']
        self.one(els)
        self.type(dom.body, els.first)

        els = html['h2 ~ *']
        self.zero(els)



    def it_selects_with_chain_of_elements(self):
        html = self._shakespear

        sels = [
          'html body div div h2',
          'body div div h2',
          'div div h2',
          'div h2',
          'h2',
          'html div div h2',
          'html body div h2',
          'html div h2',
          'html body h2',
          'html div h2',
          'html h2',
          'body h2',
          'div h2',
          'div div h2',
        ]

        for sel in sels:
            h2s = html[sel]
            self.one(h2s)
            self.type(dom.h2, h2s.first)

            h2s = html[sel.upper()]
            self.one(h2s)
            self.type(dom.h2, h2s.first)

        sels = [
          'derp body div div h2',
          'html derp div h2',
          'html body derp div h2',
          'html body div derp h2',
          'derp div h2',
          'body derp div h2',
          'body div derp h2',
          'derp div h2',
          'div derp h2',
          'div derp',
          'html html div div h2',
          'html body body div h2',
          'html body div div div h2',
          'html body div div h2 h2',
          'body body div h2',
          'body div div div h2',
          'body div div h2 h2',
          'div div div h2',
          'div div h2 h2',
          'div h2 h2',
          'h2 h2',
          'h2 div',
          'html div body div h2',
          'html body div h2 div',
          'div body div h2',
          'body div h2 div',
          'div h2 div',
          'div body h2',
          'body body h2',
          'div html h2',
          'body wbr h2', 
          'body derp h2', 
          'wbr', 
          'derp'
        ]

        for sel in sels:
          self.zero(html[sel], sel)
          self.zero(html[sel.upper()], sel)

    def it_selects_with_chain_of_elements_and_classes(self):
        html = self._shakespear

        sels = [
            'div div.dialog',
            'div .dialog',
            'div *.dialog',
            '* *.dialog',
        ]

        for sel in sels:
            els = html[sel]
            self.count(51, els)
            self.all('dialog' in x.classes for x in els)
            self.all(type(x.parent) is dom.div for x in els)

        sels = [
            'div.dialog div.dialog div.dialog',
            'div.dialog div.dialog *.dialog',
            'div.dialog div.dialog .dialog',
            'div.dialog .dialog div.dialog',
            'div.dialog *.dialog div.dialog',
            'div.dialog div.dialog div.dialog',
            '.dialog div.dialog div.dialog',
            '*.dialog div.dialog div.dialog',
        ]

        for sel in sels:
            els = html[sel]
            self.count(49, els)
            self.all('dialog' in x.classes for x in els)
            self.all(type(x.parent) is dom.div for x in els)
            self.all(type(x.grandparent) is dom.div for x in els)

    def it_selects_with_chain_of_elements_and_pseudoclasses(self):
        html = self._shakespear

        sels = [
            'div :not(#playwright)',
            'div *:not(#playwright)',
            'div div:not(#playwright)',
        ]

        for i, sel in enumerate(sels):
            els = html(sel)
            if i.last:
                self.count(241, els)
            else:
                self.count(243, els)
            self.all(x.id != 'playwright' for x in els)
            self.all(type(x.parent) is dom.div for x in els)

    def it_selects_with_classes(self):
        html = self._shakespear

        ''' Non-existing class selector '''
        sels = [
            '*.dialogxxx',
            '.dialogxxx',
            'div.dialogxxx'
        ]

        for sel in sels:
            self.zero(html[sel])

        ''' Single class selector '''
        sels = [
            '*.dialog',
            '.dialog',
            'div.dialog'
        ]

        for sel in sels:
            # Class selectors should be case-sensitive
            self.zero(html[sel.upper()])

            els = html[sel]
            for el in els:
                self.type(dom.div, el)
                self.true('dialog' in el.classes)
            self.count(51, els, 'sel: ' + sel)

        ''' Non-existing chained classes selectors '''
        sels = [
            '*.dialog.sceneZZZ',
            '.dialogZZZ.scene',
            'divZZZ.dialog.scene',
        ]

        for sel in sels:
            self.zero(html[sel])

        ''' Chained classes selectors '''
        sels = [
            '*.dialog.scene',
            '.dialog.scene',
            'div.dialog.scene',
        ]

        for sel in sels:
            els = html[sel]
            self.type(dom.div, els.first)
            self.true('dialog' in els.first.classes)
            self.eq('scene1', els.first.id)
            self.one(els)

    def it_selects_with_attribute(self):
        html = self._shakespear

        sels = [
            'div[foo]',
            '*[bar]',
            '[foo]',
        ]

        for sel in sels:
            self.zero(html[sel])

        sels = [
            'div[title]',
            '*[title]',
            '[title]',
        ]

        for sel in sels:
            self.one(html[sel])

    def it_selects_with_attribute_equality(self):
        ''' Select using the = operator [foo=bar]
        '''
        html = self._shakespear

        sels = [
            '[foo=bar]',
            '[title=bar]',
            '[foo=wtf]',
        ]

        for sel in sels:
            self.zero(html[sel])
            break
        else:
            self.fail('There were no `sels`')

        sels = [
            '*[title=wtf]',
            '[title=wtf]',
            '*[TITLE=wtf]',
            '[TITLE=wtf]',
        ]

        for sel in sels:
            # Attribtue value are case-sensitive
            self.zero(html[sel.replace('wtf', 'WTF')])

            els = html[sel]
            self.one(els)
            self.type(dom.div, els.first)
            self.eq('scene1.3.29', els.first.children.first.id)

        sels = [
            'div[id=speech144][class=character]',
            '*[id=speech14][class=characterxxx]',
            '[id=speech14][class=character][foo=bar]',
        ]

        for sel in sels:
            els = html[sel]
            self.zero(els)
            break
        else:
            self.fail('There were no `sels`')

        sels = [
            'div[id=speech14][class=character]',
            '*[id=speech14][class=character]',
            '[id=speech14][class=character]',
        ]

        for sel in sels:
            els = html[sel]
            self.one(els)
            self.type(dom.div, els.first)
            self.eq('ROSALIND', els.first.elements.first.html)
            break
        else:
            self.fail('There were no `sels`')

        sels = [
            '[id=speech1][class^=char]',
            '[id$=ech1][class*=aract]'
        ]

        for sel in sels:
            els = html[sel]
            self.one(els)
            self.eq('speech1', els.first.id)

        sels = [
            '[id=scene1][class~=thirdClass]',
            '[id][class~=thirdClass]'
        ]

        for sel in sels:
            els = html[sel]
            self.one(els)
            self.eq('scene1', els.first.id)

    def it_selects_with_attribute_space_seperated(self):
        ''' Select using the ~= operator [foo~=bar]
        '''
        html = self._shakespear

        sels = [
           '*[class~=thirdClass]',
           'div[class~=thirdClass]',
           '[class~=thirdClass]',
           '[class~=scene]',
        ]

        for sel in sels:
            if 'thirdClass' in sel:
                self.zero(html[sel.lower()])

            els = html[sel]
            self.one(els)
            self.type(dom.div, els.first)
            self.eq('scene1', els.first.id)

        sels = [
           '*[class~=third]',
           'div[class~=third]',
           '[class~=third]',
           '[class~="dialog scene thirdClass"]',
           '[class~="scene thirdClass"]',
        ]

        for sel in sels:
            els = html[sel]
            self.zero(els)

    def it_selects_with_attribute_startswith(self):
        ''' Select using the startswith operator [foo^=bar] 
        '''

        html = self._shakespear

        v = str()
        for c in 'test':
            v += c
            sels = [
                '*[id^=%s]'    %  v,
                'div[id^=%s]'  %  v,
                '[id^=%s]'     %  v,
            ]
            for sel in sels:
                self.zero(html[sel.replace(v, v.upper())])
                els = html[sel]
                self.one(els)
                self.type(dom.div, els.first)
                self.eq('test', els.first.id)

        sels = [
            '[id^=est]',
            '[id^=es]',
        ]

        for sel in sels:
            sels = [
                '*%s'    %  sel,
                'div%s'  %  sel,
                '%s'     %  sel,
            ]
            for sel in sels:
                els = html[sel]
                self.zero(els)

    def it_selects_with_attribute_endswith(self):
        ''' Select using the endswith operator [foo$=bar] 
        '''

        html = self._shakespear

        v = str()
        for c in reversed('dialog'):
            v = c + v
            sel = '[class$=%s]' % v
            sels = [
                '*%s'    %  sel,
                'div%s'  %  sel,
                '%s'     %  sel,
            ]
            for sel1 in sels:
                SEL = sel1.replace(sel1, sel.upper())
                self.zero(html[SEL])
                els = html[sel1]
                self.count(50, els)
                self.type(dom.div, els.first)

        sels = [
            '[id$=dialo]',
            '[id$=ialo]',
        ]

        for sel in sels:
            sels = [
                '*%s'    %  sel,
                'div%s'  %  sel,
                '%s'     %  sel,
            ]
            for sel in sels:
                els = html[sel]
                self.zero(els)

    def it_selects_with_attribute_contains(self):
        ''' Select using the contains operator [foo*=bar] 
        '''

        html = self._shakespear

        sels = [
            '*[class*=dialog]',
            'div[class*=dialog]',
            '[class*=dialog]',
            '*[class*=dialo]',
            'div[class*=dialo]',
            '[class*=dialo]',
            '*[class*=ialog]',
            'div[class*=ialog]',
            '*[class*=ialog]',
            '*[class*=ialo]',
            'div[class*=ialo]',
            '*[class*=ialo]',
        ]

        for sel in sels:
            els = html[sel]
            self.count(51, els)
            self.type(dom.div, els.first)

        sels = [
            '*[class*=idontexist]',
            'div[class*=idontexist]',
            '[class*=idontexist]',

            '*[class*=DIALOG]',
            'div[class*=DIALOG]',
            '[class*=DIALOG]',
            '*[class*=DIALO]',
            'div[class*=DIALO]',
            '[class*=DIALO]',
            '*[class*=IALOG]',
            'div[class*=IALOG]',
            '*[class*=IALOG]',
            '*[class*=IALO]',
            'div[class*=IALO]',
            '*[class*=IALO]',
        ]

        for sel in sels:
            els = html[sel]
            self.zero(els)

    def it_selects_with_attribute_hyphen_seperated(self):
        ''' Select using the hyphen-seperated operator [foo|=bar] 
        '''
        html = self._shakespear

        sels = [
            '[id|="023338d1"]',
            '[id|="023338d1-5503"]',
            '[id|="023338d1-5503-4054"]',
            '[id|="023338d1-5503-4054-98f7-c1e9c9ad390d"]',
        ]

        for sel in sels:
            els = html[sel]
            self.one(els)
            self.type(dom.h2, els.first)

        sels = [
            '[id|="023338D1"]',
            '[id|="023338D1-5503"]',
            '[id|="023338D1-5503-4054"]',
            '[id|="023338D1-5503-4054-98F7-C1E9C9AD390D"]',
        ]

        self.all(html[sel].isempty for sel in sels)

        for sel in sels:
            els = html[sel]
        els = html['[id|=test]']
        self.one(els)
        self.type(dom.div, els.first)

        sels = [
            '[id|="023338d"]',
            '[id|="023338d1-"]',
            '[id|="023338d1-5503-"]',
            '[id|="023338d1-5503-4"]',
            '[id|="023338d1-5503-4054-"]',
            '[id|="023338d1-5503-4054-9"]',
            '[id|="023338d1-5503-4054-98f7-"]',
            '[id|="023338d1-5503-4054-98f7-c"]',
            '[id|="f6836822"]',
            '[id|="f6836822-589e"]',
            '[id|="f6836822-589e-40bf-a3f7-a5c3185af4f7"]',
        ]

        for sel in sels:
            self.zero(html[sel], sel)

    def it_select_root(self):
        html = self._shakespear

        sels = [
            '*:root',
            'html:root',
            ':root',
            '*:ROOT',
            'html:ROOT',
            ':ROOT',
        ]

        for sel in sels:
            els = html[sel]
            self.one(els)
            self.type(dom.html, els.first)

        id = uuid4().hex
        html = dom.html('''
            <p id="%s">
                The following is
                <strong>
                    strong text
                </strong>
            </p>
        ''' % id)

        sels = [
            'p:root',
            ':root',
        ]

        for sel in sels:
            els = html[sel]
            self.one(els)
            self.type(dom.p, els.first, sel)

        sels = [
            'html:root',
        ]

        for sel in sels:
            els = html[sel]
            self.zero(els)

    def it_selects_nth_child(self):
        html = self._listhtml

        ''' single '''
        els = html['li:nth-child(2)']
        self.one(els)
        self.eq('1', els.first.id)

        els = html['li:NTH-CHILD(2)']
        self.one(els)
        self.eq('1', els.first.id)

        ''' even '''
        sels = [
            'li:nth-child(even)',
            'li:nth-child(EVEN)',
            'li:nth-child(2n+0)',
            'li:nth-child(2n-2)',
            'li:nth-child(2n-500)',
            'li:nth-child(2N-500)',
        ]

        for sel in sels:
            els = html[sel]
            self.six(els)
        
            for i, id in enumerate((1, 3, 5, 7, 9, 11)):
                self.eq(str(id), els[i].id)

        ''' odd '''
        sels = [
            'li:nth-child(odd)',
            'li:nth-child(ODD)',
            'li:nth-child(2n+1)',
            'li:nth-child(2n-1)',
        ]

        for sel in sels:
            els = html[sel]
            self.six(els)
        
            for i, id in enumerate((0, 2, 4, 6, 8, 10)):
                self.eq(str(id), els[i].id)

        ''' every one '''
        sels = [
            'li:nth-child(1n+0)',
            'li:nth-child(1n+1)',
        ]

        for sel in sels:
            els = html[sel]
            self.count(12, els)
        
            for i in range(11):
                self.eq(str(i), els[i].id)

        ''' every one starting at the second child'''
        els = html['li:nth-child(1n+2)']
        self.count(11, els)
    
        for i in range(11):
            self.eq(str(i + 1), els[i].id)

        ''' every one starting at the fifth child'''
        els = html['li:nth-child(1n+5)']
        self.eight(els)
        for i in range(8):
            self.eq(str(i + 4), els[i].id)

        ''' every one starting at the sixth child'''
        els = html['li:nth-child(1n+6)']
        self.seven(els)
        for i in range(7):
            self.eq(str(i + 5), els[i].id)

        els = html['li:nth-child(2n+3)']
        self.five(els)
        for i, j in enumerate([2, 4, 6, 8, 10]):
            self.eq(str(j), els[i].id)

        els = html['li:nth-child(2n-3)']
        expect = ['0', '2', '4', '6', '8', '10']
        self.count(len(expect), els)
        self.eq(expect, els.pluck('id'))

        sels = [
            'li:nth-child(5)',
        ]
        for sel in sels:
            els = html[sel]
            self.one(els)
            self.eq('4', els.first.id)

        els = html['li.my-class:nth-child(even)']
        self.one(els)
        self.eq('3', els.first.id)

        els = html['li.my-class:nth-child(odd)']
        self.zero(els)

        sels = [
            'li:nth-child(1n+0)',
            'li:nth-child(n+0)',
            'li:nth-child(N+0)',
            'li:nth-child(n)',
            'li:nth-child(N)',
        ]

        expect = [str(x) for x in range(12)]
        for sel in sels:
            els = html[sel]
            self.count(len(expect), els)
            self.eq(expect, els.pluck('id'))

        sels = [
            'li:nth-child(1n+3)',
            'li:nth-child(n+3)',
        ]

        expect = [str(x) for x in range(2,12)]
        for sel in sels:
            els = html[sel]
            self.count(len(expect), els)
            self.eq(expect, els.pluck('id'))

        sels = [
            'li:nth-child(-n+3)',
            'li:nth-child(-1n+3)',
        ]
        for sel in sels:
            sels = dom.selectors(sel)
            els = html[sel]
            self.three(els)
            for i in range(3):
                self.eq(str(i), els[i].id)

        sels = [
            'li:nth-child(-2n+3)',
        ]
        for sel in sels:
            sels = dom.selectors(sel)
            els = html[sel]
            self.two(els)
            self.eq('0', els.first.id)
            self.eq('2', els.second.id)

        sels = [
            'li:nth-child(-200n+3)',
        ]
        for sel in sels:
            sels = dom.selectors(sel)
            els = html[sel]
            self.one(els)
            self.eq('2', els.first.id)

        sels = [
            'li:nth-child(n+2):nth-child(-n+5)',
        ]
        for sel in sels:
            sels = dom.selectors(sel)
            els = html[sel]
            self.four(els)
            self.eq('1', els.first.id)
            self.eq('2', els.second.id)
            self.eq('3', els.third.id)
            self.eq('4', els.fourth.id)

        sels = [
            'li:nth-child(n+2):nth-child(odd):nth-child(-n+9)',
        ]
        expect = [str(x) for x in range(2, 10, 2)]
        for sel in sels:
            sels = dom.selectors(sel)
            els = html[sel]
            self.count(len(expect), els)
            self.eq(expect, els.pluck('id'))

        sels = [
            'li:nth-child(3n+1):nth-child(even)',
        ]
        expect = ['3', '9']
        for sel in sels:
            sels = dom.selectors(sel)
            els = html[sel]
            self.count(len(expect), els)
            self.eq(expect, els.pluck('id'))

    def it_selects_nth_last_child(self):
        html = self._listhtml

        # Selects every fourth element among any group of siblings,
        # counting backwards from the last one 
        sels = [
            'li:nth-last-child(4n)',
            'li:NTH-LAST-CHILD(4n)',
            'li:nth-last-child(4N)',
        ]

        expect = ['0', '4', '8']
        for sel in sels:
            els = html[sel]
            self.count(len(expect), els)
            self.eq(expect, els.pluck('id'))

        ''' last 2 rows '''
        sels = [
            'li:nth-last-child(-n+2)',
            'li:nth-last-child(-1n+2)'
        ]

        expect = ['10', '11']
        for sel in sels:
            els = html[sel]
            self.count(len(expect), els)
            self.eq(expect, els.pluck('id'))

        # Represents the odd rows of an HTML table: 1, 3, 5, etc.,
        # counting from the end.
        sels = [
            'li:nth-last-child(odd)',
            'li:nth-last-child(2n+1)',
        ]

        expect = [str(x) for x in range(1, 12, 2)]
        for sel in sels:
            els = html[sel]
            self.count(len(expect), els)
            self.eq(expect, els.pluck('id'))

        # Represents the even rows of an HTML table: 2, 4, 6, etc.,
        # counting from the end.
        sels = [
            'li:nth-last-child(even)',
            'li:nth-last-child(2n)',
        ]

        expect = [str(x) for x in range(0, 11, 2)]
        for sel in sels:
            els = html[sel]
            self.count(len(expect), els)
            self.eq(expect, els.pluck('id'))

        # Represents the seventh element, counting from the end.
        sels = [
            'li:nth-last-child(7)',
        ]

        expect = ['5']
        for sel in sels:
            els = html[sel]
            self.count(len(expect), els)
            self.eq(expect, els.pluck('id'))

        # Represents elements 5, 10, 15, etc., counting from the end.
        sels = [
            'li:nth-last-child(5n)',
        ]

        expect = ['2', '7']
        for sel in sels:
            els = html[sel]
            self.count(len(expect), els)
            self.eq(expect, els.pluck('id'))

        # Represents elements 4, 7, 10, 13, etc., counting from the end.
        sels = [
            'li:nth-last-child(3n+4)',
            'li:nth-last-child(3N+4)',
        ]

        expect = ['2', '5', '8']
        for sel in sels:
            els = html[sel]
            self.count(len(expect), els)
            self.eq(expect, els.pluck('id'))

        # Represents the last three elements among a group of siblings.
        sels = [
            'li:nth-last-child(-n+3)',
            'li:nth-last-child(-N+3)'
        ]

        expect = ['9', '10', '11']
        for sel in sels:
            els = html[sel]
            self.count(len(expect), els)
            self.eq(expect, els.pluck('id'))

        # Represents every <li> element among a group of siblings. This
        # is the same as a simple li selector. (Since n starts at zero,
        # while the last element begins at one, n and n+1 will both
        # select the same elements.)
        sels = [
            'li:nth-last-child(n)',
            'li:nth-last-child(n+1)',
            'li:nth-last-child(N+1)',

        ]
        expect = [str(x) for x in range(12)]
        for sel in sels:
            els = html[sel]
            self.eq(expect, els.pluck('id'))

        # Represents every <li> that is the first element among a group
        # of siblings, counting from the end. This is the same as the
        # :last-child selector.
        sels = [
            'li:nth-last-child(1)',
            'li:nth-last-child(0n+1)',
            'li:nth-last-child(0N+1)',
        ]
        expect = ['11']
        for sel in sels:
            els = html[sel]
            self.eq(expect, els.pluck('id'))

    def it_selects_nth_of_type(self):
        html = dom.html('''
		<section>
		   <h1>Words</h1>
		   <p>Little</p>
		   <p>Piggy</p>
		</section>
		''')

        els = html('p:nth-child(2)')
        self.one(els)
        self.eq('Little', els.first.elements.first.html)

        els = html('p:nth-of-type(2)')
        self.one(els)
        self.eq('Piggy', els.first.elements.first.html)

        els = html('p:NTH-OF-TYPE(2)')
        self.one(els)
        self.eq('Piggy', els.first.elements.first.html)


        html = dom.html('''
            <section>
               <h1>Words</h1>
               <h2>Words</h2>
               <p>Little</p>
               <p>Piggy</p>
            </section>
		''')

        els = html('p:nth-child(2)')
        self.zero(els)

        els = html('p:nth-of-type(2)')
        self.one(els)
        self.eq('Piggy', els.first.elements.first.html)

        # Take the ListHtml and replacing all the <ol> and its <li>s
        # with the same number of alternating <span>s and <div>s.
        html = dom.html(ListHtml)
        sec = html[0].children[0].children[0].children[0]
        ol = sec.children.first
        cnt = ol.children.count

        sec.elements.clear()

        for i in range(cnt):
            el = dom.div if i % 2 else dom.span
            el = el('This is item ' + str(i))
            el.id = str(i)
            sec.elements += el

        sels = [
            'span:nth-of-type(3)',
        ]

        for sel in sels:
            els = html[sel]
            self.one(els)
            self.eq('4', els.first.id)

        sels = [
            'span:nth-of-type(n+3)',
        ]
        expect = ['4', '6', '8', '10']
        for sel in sels:
            els = html[sel]
            self.count(len(expect), els)
            self.eq(expect, els.pluck('id'))

        sels = [
            'span:nth-of-type(-n+4)',
            'span:nth-of-type(-N+4)',
        ]

        expect = ['0', '2', '4', '6']
        for sel in sels:
            els = html[sel]
            self.count(len(expect), els)
            self.eq(expect, els.pluck('id'))

        sels = [
            'div:nth-of-type(-n+5)',
        ]

        expect = ['1', '3', '5', '7', '9']
        for sel in sels:
            els = html[sel]
            self.count(len(expect), els)
            self.eq(expect, els.pluck('id'))

        sels = [
            'span:nth-of-type(n+3):nth-of-type(-n+6)',
        ]

        expect = ['4', '6', '8', '10']
        for sel in sels:
            els = html[sel]
            self.count(len(expect), els)
            self.eq(expect, els.pluck('id'))

        sels = [
            'div:nth-of-type(n+1):nth-of-type(-n+3)',
        ]

        expect = ['1', '3', '5']
        for sel in sels:
            els = html[sel]
            self.count(len(expect), els)
            self.eq(expect, els.pluck('id'))

        sels = [
            'span:nth-of-type(n+3):nth-of-type(odd):nth-of-type(-n+6)',
        ]

        expect = ['4', '8']
        for sel in sels:
            els = html[sel]
            self.count(len(expect), els)
            self.eq(expect, els.pluck('id'))

        sels = [
            'div:nth-of-type(n+1):nth-of-type(even):nth-of-type(-n+3)',
        ]

        expect = ['3']
        for sel in sels:
            els = html[sel]
            self.count(len(expect), els)
            self.eq(expect, els.pluck('id'))

    def it_selects_nth_last_of_type(self):
        html = dom.html(ListHtml)

        sels = [
            'li:nth-last-of-type(2)',
            'li:NTH-LAST-OF-TYPE(2)',
        ]

        expect = ['10']
        for sel in sels:
            els = html[sel]
            self.count(len(expect), els)
            self.eq(expect, els.pluck('id'))

        html = dom.html('''
            <div>
                <span>This is a span.</span>
                <span>This is another span.</span>
                <em>This is emphasized.</em>
                <span>Wow, this span gets limed!!!</span>
                <s>This is struck through.</s>
                <span>Here is one last span.</span>
            </div>
        ''')

        sels = [
            'span:nth-last-of-type(2)',
        ]

        for sel in sels:
            els = html[sel]
            self.one(els)
            expect = 'Wow, this span gets limed!!!'
            self.eq(expect, els.first.elements.first.html)

    def it_selects_first_child(self):
        html = dom.html('''
            <body>
                <p id="1"> The last P before the note.</p>
                <div>
                    <p id="2"> The first P inside the note.</p>
                </div>
            </body>
        ''')

        els = html['p:first-child']
        self.two(els)
        self.eq('1', els.first.id)
        self.eq('2', els.second.id)

        els = html['p:FIRST-CHILD']
        self.two(els)
        self.eq('1', els.first.id)
        self.eq('2', els.second.id)

        html = dom.html('''
            <body>
                <p id="1"> The last P before the note.</p>
                <div class="note">
                    <h2> Note </h2>
                    <p> id="2" The first P inside the note.</p>
                </div>
            </body>
        ''')
        els = html['p:first-child']
        self.one(els)
        self.eq('1', els.first.id)
    
    def it_selects_last_child(self):
        html = dom.html('''
        <div>
            <p id="1">This text isn't selected.</p>
            <p id="2">This text is selected!</p>
        </div>

        <div>
            <p> id="3"This text isn't selected.</p>
            <h2 id="4">This text isn't selected: it's not a `p`.</h2>
        </div>
        ''')

        els = html['p:last-child']
        self.one(els)
        self.eq('2', els.first.id)

        els = html['p:LAST-CHILD']
        self.one(els)
        self.eq('2', els.first.id)

    def it_selects_first_of_type(self):
        html = dom.html('''
        <body>
            <h2 id="0">Heading</h2>
            <p id="1">Paragraph 1</p>
            <p id="2">Paragraph 2</p>
        </body>
        ''')

        els = html['p:first-of-type']
        self.one(els)
        self.eq('1', els.first.id)

        els = html['p:FIRST-OF-TYPE']
        self.one(els)
        self.eq('1', els.first.id)

        # https://developer.mozilla.org/en-US/docs/Web/CSS/:first-of-type
        html = dom.html('''
            <article>
                <div id="0">
                    This `div` is first!
                </div>
                <div>
                    This 
                    <span id="1">
                        nested `span` is first
                    </span>
                !
                </div>
                <div>
                    This 
                    <em id="2">
                        nested `em` is first
                    </em>
                    , but this 
                    <em>
                        nested `em` is last
                    </em>!
                </div>
                <div>
                    This 
                    <span id="3">
                        nested `span` gets styled
                    </span>!
                </div>
                <b id="4">
                    This `b` qualifies!
                </b>
                <div>
                    This is the final `div`.
                </div>
            </article>
        ''')

        els = html[':first-of-type']
        expect = [str(x) for x in range(5)]
        self.count(len(expect), els)
        self.eq(expect, els.pluck('id'))

        html = dom.html('''
        <dl>
            <dt id="0">gigogne</dt>
            <dd>
                <dl>
                    <dt id="1">fusée</dt>
                    <dd>multistage rocket</dd>
                    <dt>table</dt>
                    <dd>nest of tables</dd>
                </dl>
            </dd>
        </dl>
        ''')

        els = html['dt:first-of-type']
        expect = [str(x) for x in range(2)]
        self.count(len(expect), els)
        self.eq(expect, els.pluck('id'))

    def it_selects_last_of_type(self):
        html = dom.html('''
        <body>
            <h2>Heading</h2>
            <p>Paragraph 1</p>
            <p id="0">Paragraph 2</p>
        </body>
        ''')

        els = html['p:last-of-type']
        self.one(els)
        self.eq('0', els.first.id)

        els = html['p:LAST-OF-TYPE']
        self.one(els)
        self.eq('0', els.first.id)

        # https://developer.mozilla.org/en-US/docs/Web/CSS/:last-of-type
        html = dom.html('''
        <article>
            <div>This `div` is first.</div>
            <div>This <span id="0">nested `span` is last</span>!</div>
            <div>This <em>nested `em` is first</em>, but this
            <em id="1">nested `em` is last</em>!</div>
            <b id="2">This `b` qualifies!</b>
            <div id="3">This is the final `div`!</div>
        </article>
        ''')

        els = html[':last-of-type']
        expect = [str(x) for x in range(4)]
        self.count(len(expect), els)
        self.eq(expect, els.pluck('id'))

        html = dom.html('''
        <body>
            <div>
                <span>Corey,</span>
                <span>Yehuda,</span>
                <span>Adam,</span>
                <span id="0">Todd</span>
            </div>
            <div>
                <span>Jörn,</span>
                <span>Scott,</span>
                <span id="1">Timo,</span>
                <b>Nobody</b>
            </div>
        </body>
        ''')

        els = html['span:last-of-type']
        expect = [str(x) for x in range(2)]
        self.count(len(expect), els)
        self.eq(expect, els.pluck('id'))

    def it_selects_only_child(self):

        html = dom.html('''
        <div>
            <div id="0">
                I am an only child.
            </div>
        </div>
        <div>
            <div>
                I am the 1st sibling.
            </div>
            <div>
                I am the 2nd sibling.
            </div>
            <div>
                I am the 3rd sibling, 
                <div id="1">
                    but this is an only child.
                </div>
            </div>
        </div>
        ''')

        els = html[':only-child']
        expect = [str(x) for x in range(2)]
        self.count(len(expect), els)
        self.eq(expect, els.pluck('id'))

        els = html[':ONLY-CHILD']
        expect = [str(x) for x in range(2)]
        self.count(len(expect), els)
        self.eq(expect, els.pluck('id'))
        
        html = dom.html('''
        <body>

            <div><p id="0">This is a paragraph.</p></div>

            <div><span>This is a span.</span><p>This is a
            paragraph.</p></div>

        </body>
        ''')

        els = html[':only-child']
        expect = [str(x) for x in range(1)]
        self.count(len(expect), els)
        self.eq(expect, els.pluck('id'))

    def it_selects_only_of_type(self):
        sels = [
            ':only-of-type',
            ':ONLY-OF-TYPE',
            ':first-of-type:last-of-type'
            ':nth-of-type(1):nth-last-of-type(1)'
        ]

        html = dom.html('''
        <main>
            <div>I am `div` #1.</div>
            <p id="0">I am the only `p` among my siblings.</p>
            <div>I am `div` #2.</div>
            <div>I am `div` #3.
                <i id="1">I am the only `i` child.</i>
                <em>I am `em` #1.</em>
                <em>I am `em` #2.</em>
            </div>
        </main>
        ''')

        for sel in sels:
            els = html[sel]
            expect = [str(x) for x in range(2)]
            self.count(len(expect), els)
            self.eq(expect, els.pluck('id'))

        html = dom.html('''
        <body>

            <div><p id="0">This is a paragraph.</p></div>

            <div><p>This is a paragraph.</p><p>This is a
            paragraph.</p></div>

        </body>
        ''')

        for sel in sels:
            els = html[sel]
            expect = [str(x) for x in range(1)]
            self.count(len(expect), els)
            self.eq(expect, els.pluck('id'))

        html = dom.html('''
        <ul>
            <li id="0">I'm all alone!</li>
        </ul>  

        <ul>
            <li>We are together.</li>
            <li>We are together.</li>
            <li>We are together.</li>
        </ul>
        ''')

        for sel in sels:
            els = html[sel]
            expect = [str(x) for x in range(1)]
            self.count(len(expect), els)
            self.eq(expect, els.pluck('id'))

        html = dom.html('''
        <div>
          <p id="0">I'm the only paragraph element in this div.</p>  
          <ul id="1">
            <li>List Item</li>
            <li>List Item</li>
          </ul>  
        </div>

        <div>
          <p>There are multiple paragraphs inside this div.</p>  
          <p>Yes there are.</p>  
          <ul id="2">
            <li>List Item</li>
            <li>List Item</li>
          </ul>  
        </div>        
        ''')

        for sel in sels:
            els = html[sel]
            expect = [str(x) for x in range(3)]
            self.count(len(expect), els)
            self.eq(expect, els.pluck('id'))

        html = dom.html('''
        <main>
            <div>
              <p id="0">I'm the only paragraph element in this div.</p>  
              <ul id="1">
                <li>List Item</li>
                <li>List Item</li>
              </ul>  
            </div>

            <div>
              <p>There are multiple paragraphs inside this div.</p>  
              <p>Yes there are.</p>  
              <ul id="2">
                <li>List Item</li>
                <li>List Item</li>
              </ul>  
            </div> 
        </main>
        ''')

        for sel in sels:
            els = html[sel]
            expect = [str(x) for x in range(3)]
            self.count(len(expect), els)
            self.eq(expect, els.pluck('id'))

    def it_selects_empty(self):
        html = dom.html('''
        <main>
            <div id="0"><!-- I am empty. --></div>

            <div>I am not empty.</div>

            <div>
                <!-- I am empty despite the whitespace around this comment. -->
            </div>

            <div>
                <p id="1"><!-- This <p> is empty though its parent <div> is not.--></p>
            </div>
        </main>
        ''')

        els = html[':empty']
        expect = [str(x) for x in range(2)]
        self.count(len(expect), els)
        self.eq(expect, els.pluck('id'))

        els = html[':EMPTY']
        expect = [str(x) for x in range(2)]
        self.count(len(expect), els)
        self.eq(expect, els.pluck('id'))

        html = dom.html('''
        <main>
            <div id="0"></div>
            <div id="1"><!-- test --></div>
        </main>
        ''')

        els = html[':empty']
        expect = [str(x) for x in range(2)]
        self.count(len(expect), els)
        self.eq(expect, els.pluck('id'))

        html = dom.html('''
        <main>
            <div> </div>

            <div>
                <!-- test -->
            </div>

            <div>
            </div>
        </main>
        ''')

        els = html[':empty']
        self.zero(els)

    def it_selects_not(self):
        ''' Elements '''
        # Select all elements that aren't <div>s 
        sels = [
            ':not(div)',
            ':NOT(div)',
            '*:not(div)',
        ]

        for sel in sels:
            els = self._shakespear[sel]
            self.six(els)
            self.false(dom.div in [type(x) for x in els])

        ''' Classes '''
        # Select all elements that don't have the 'dialog' class
        sels = [
            ':not(.dialog)',
            '*:not(.dialog)',
            ':not(*.dialog)',
        ]
        for sel in sels:
            els = self._shakespear[sel]
            self.count(198, els)
            for el in els:
                self.false('dialog' in el.classes)

        sels = [
            'div:not(.dialog)',
            'div:not(div.dialog)',
        ]

        ''' Attributes '''
        for sel in sels:
            els = self._shakespear[sel]
            self.count(192, els)
            for el in els:
                self.false('dialog' in el.classes)
            self.all([type(x) is dom.div for x in els])

        sels = [
            'div:not([title=wtf])',
            'div:not(div[title=wtf])',
            'div:not(DIV[TITLE=wtf])',
        ]

        for sel in sels:
            els = self._shakespear[sel]
            self.count(242, els)
            self.all(el.title != 'wtf' for el in els)

        ''' Pseudoclasses '''
        # Select all odd (not even) li's

        # FIXME This selects correctly but there is an issue with the
        # parsing (ref dd6a4f93)
        # els = self._listhtml['li:not(li:nth-child(even))']
        # expect = list(range(0, 11, 2))
        # self.count(len(expect), els)
        # self.eq(expect, [int(x.id) for x in els])

        ''' Chained '''
        sels = [
            ':not(.dialog):not(h2)',
            '*:not(.dialog):not(h2)',
            '*:not(*.dialog):not(h2)',
            '*:not(*.dialog):not(H2)',
        ]

        for sel in sels:
            els = self._shakespear[sel]
            self.count(197, els)
            self.all(type(x) is not dom.h2 for x in els)
            self.all('dialog' not in x.classes for x in els)

        ''' Identity '''
        sels = [
            'div:not(#speech16)',
            'div:not(div#speech16)',
            'div:not(*#speech16)',
        ]

        for sel in sels:
            els = self._shakespear[sel]
            self.count(242, els)
            self.all(el.id != 'speech16' for el in els)

    def it_selects_with_id(self):
        html = self._shakespear
        sels = [
            '*#speech16',
            'div#speech16',
            '#speech16',
        ]

        for sel in sels:
            self.zero(html[sel.upper()])
            els = self._shakespear[sel]
            self.one(els)
            self.eq('speech16', els.first.id)

        sels = [
            '*#idontexist',
            'div#idontexist',
            '#idontexist',
        ]

        for sel in sels:
            els = html[sel]
            self.zero(els)

    def it_parses_combinators(self):
        def space(s):
            return re.sub(r'(\S)([~\+>])(\S)', r'\1 \2 \3', s)

        sub         =  dom.selector.element.SubsequentSibling
        next        =  dom.selector.element.NextSibling
        child       =  dom.selector.element.Child
        desc        =  dom.selector.element.Descendant

        ''' sub desc next '''
        sels = [
            'div ~ div p + q',
            'div~div p+q',
        ]
        for sel in sels:
            expect = space(sel)
            sels = dom.selectors(sel)
            self.eq(expect, repr(sels))
            self.eq(expect, str(sels))

            self.four(sels.first.elements)
            self.eq(None, sels.first.elements.first.combinator)
            self.eq(sub, sels.first.elements.second.combinator)
            self.eq(desc, sels.first.elements.third.combinator)
            self.eq(next, sels.first.elements.fourth.combinator)

        ''' Subsequent-sibling combinator '''
        sels = [
           'body ~ div',
           'body~div',
           'body.my-class ~ div.my-class',
           'body[foo=bar] ~ div[foo=bar]',
        ]

        for sel in sels:
            expect = space(sel)
            sels = dom.selectors(sel)
            self.eq(expect, repr(sels))
            self.eq(expect, str(sels))
            self.two(sels.first.elements)
            self.eq(None, sels.first.elements.first.combinator)
            self.eq(sub, sels.first.elements.second.combinator)

        sels = [
           'body div ~ p',
           'body div~p',
           'body.my-class div.my-class ~ p.my-class',
           'body.my-class div.my-class~p.my-class',
           'body[foo=bar] div[foo=bar]~p.my-class',
        ]

        for sel in sels:
            sels = dom.selectors(sel)
            self.eq(space(sel), repr(sels))
            self.eq(space(sel), str(sels))
            self.three(sels.first.elements)
            self.eq(None, sels.first.elements.first.combinator)
            self.eq(desc, sels.first.elements.second.combinator)
            self.eq(sub, sels.first.elements.third.combinator)

        ''' Next-sibling combinator '''
        sels = [
           'body + div',
           'body+div',

           'body.my-class + div.my-class',
           'body.my-class+div.my-class',

           'body[foo=bar] + div[foo=bar]',
           'body[foo=bar]+div[foo=bar]',
        ]

        for sel in sels:
            sels = dom.selectors(sel)
            self.eq(space(sel), repr(sels))
            self.eq(space(sel), str(sels))
            self.two(sels.first.elements)
            self.eq(None, sels.first.elements.first.combinator)
            self.eq(next, sels.first.elements.second.combinator)

        sels = [
           'body div+p',
           'body div + p',

           'body.my-class div.my-class + p.my-class',
           'body.my-class div.my-class+p.my-class',

           'body[foo=bar] div[foo=bar] + p.my-class',
           'body[foo=bar] div[foo=bar]+p.my-class',
        ]

        for sel in sels:
            sels = dom.selectors(sel)
            self.eq(space(sel), repr(sels))
            self.eq(space(sel), str(sels))
            self.three(sels.first.elements)
            self.eq(None, sels.first.elements.first.combinator)
            self.eq(desc, sels.first.elements.second.combinator)
            self.eq(next, sels.first.elements.third.combinator)

        ''' Child combinator '''
        sels = [
           'body > div',
           'body>div',

           'body.my-class>div.my-class',

           'body[foo=bar] > div[foo=bar]',
           'body[foo=bar]>div[foo=bar]',
        ]

        for sel in sels:
            sels = dom.selectors(sel)
            self.eq(space(sel), repr(sels))
            self.eq(space(sel), str(sels))
            self.two(sels.first.elements)
            self.eq(None, sels.first.elements.first.combinator)
            self.eq(child, sels.first.elements.second.combinator)

        sels = [
           'body > div > p',
           'body>div>p',

           'body.my-class > div.my-class > p.my-class',
           'body.my-class>div.my-class>p.my-class',

           'body[foo=bar] > div[foo=bar] > p.my-class',
           'body[foo=bar]>div[foo=bar]>p.my-class',
        ]

        for sel in sels:
            sels = dom.selectors(sel)
            self.eq(space(sel), repr(sels))
            self.eq(space(sel), str(sels))
            self.three(sels.first.elements)
            self.eq(None, sels.first.elements.first.combinator)
            self.eq(child, sels.first.elements.second.combinator)
            self.eq(child, sels.first.elements.third.combinator)

        sels = [
           'body div > p',
           'body div>p',

           'body.my-class div.my-class > p.my-class',
           'body.my-class div.my-class>p.my-class',

           'body[foo=bar] div[foo=bar] > p.my-class',
           'body[foo=bar] div[foo=bar]>p.my-class',
        ]

        for sel in sels:
            sels = dom.selectors(sel)
            self.eq(space(sel), repr(sels))
            self.eq(space(sel), str(sels))
            self.three(sels.first.elements)
            self.eq(None, sels.first.elements.first.combinator)
            self.eq(desc, sels.first.elements.second.combinator)
            self.eq(child, sels.first.elements.third.combinator)

        sels = [
           'body > div p',
           'body>div p',

           'body.my-class > div.my-class p.my-class',
           'body.my-class>div.my-class p.my-class',

           'body[foo=bar] > div[foo=bar] p.my-class',
           'body[foo=bar]>div[foo=bar] p.my-class',
        ]

        for sel in sels:
            sels = dom.selectors(sel)
            self.eq(space(sel), repr(sels))
            self.eq(space(sel), str(sels))
            self.three(sels.first.elements)
            self.eq(None, sels.first.elements.first.combinator)
            self.eq(child, sels.first.elements.second.combinator)
            self.eq(desc, sels.first.elements.third.combinator)

        ''' Descendant combinator '''
        sels = [
           'body div',
           'body.my-class div.my-class',
           'body[foo=bar] div[foo=bar]',
        ]

        for sel in sels:
            sels = dom.selectors(sel)
            self.eq(sel, repr(sels))
            self.eq(sel, str(sels))
            self.two(sels.first.elements)
            self.eq(None, sels.first.elements.first.combinator)
            self.eq(desc, sels.first.elements.second.combinator)

        sels = [
           'body div p',
           'body.my-class div.my-class p.my-class',
           'body[foo=bar] div[foo=bar] p[foo=bar]',
        ]

        for sel in sels:
            sels = dom.selectors(sel)
            self.eq(sel, repr(sels))
            self.eq(sel, str(sels))
            self.three(sels.first.elements)
            self.eq(None, sels.first.elements.first.combinator)
            self.eq(desc, sels.first.elements.second.combinator)
            self.eq(desc, sels.first.elements.third.combinator)

    def it_parses_chain_of_elements(self):
        ''' One '''
        sels = dom.selectors('E')
        self.repr('E', sels)
        self.str('E', sels)
        self.one(sels)
        els = sels.first.elements
        self.one(els)
        self.eq(['E'], els.pluck('element'))

        desc = dom.selector.element.Descendant
        self.none(els.first.combinator)

        ''' Two '''
        sels = dom.selectors('E F')
        self.repr('E F', sels)
        self.str('E F', sels)
        self.one(sels)
        els = sels.first.elements
        self.two(els)
        self.eq(['E', 'F'], els.pluck('element'))

        desc = dom.selector.element.Descendant
        self.none(els.first.combinator)
        self.eq(desc, els.second.combinator)
        self.repr('E F', sels)
        self.str('E F', sels)

        ''' Three '''
        sels = dom.selectors('E F G')
        self.repr('E F G', sels)
        self.str('E F G', sels)
        self.one(sels)
        els = sels.first.elements
        self.three(els)
        self.eq(['E', 'F', 'G'], els.pluck('element'))

        desc = dom.selector.element.Descendant
        self.none(els.first.combinator)
        self.eq(desc, els.second.combinator)
        self.eq(desc, els.third.combinator)
        self.repr('E F G', sels)
        self.str('E F G', sels)

    def it_parses_chain_of_elements_and_classes(self):
        ''' element to class '''
        sels = [
            'div .dialog',
            'div *.dialog',
            'div div.dialog',
        ]

        for i, sel in enumerate(sels):
            sel = dom.selectors(sel)
            self.eq('div',  sel.first.elements.first.element)
            if i.last:
                self.eq('div',  sel.first.elements.second.element)
            else:
                self.eq('*',  sel.first.elements.second.element)
            self.eq(
                'dialog', sel.first.elements.second.classes.first.value
            )

        ''' Class to element '''
        sels = [
            '.dialog div',
            '*.dialog div',
            'div.dialog div',
        ]

        for i, sel in enumerate(sels):
            sel = dom.selectors(sel)
            self.eq('div',  sel.first.elements.second.element)
            if i.last:
                self.eq('div',  sel.first.elements.first.element)
            else:
                self.eq('*',  sel.first.elements.first.element)

            self.eq(
                'dialog', sel.first.elements.first.classes.first.value
            )

    def it_parses_chain_of_elements_and_pseudoclasses(self):
        ''' Element to pseudoclasses '''
        sels = [
            'div :not(p)',
            'div *:not(p)',
            'div div:not(p)',
        ]

        for i, sel in enumerate(sels):
            sel = dom.selectors(sel)
            self.eq('div',  sel.first.elements.first.element)
            if i.last:
                self.eq('div',  sel.first.elements.second.element)
            else:
                self.eq('*',  sel.first.elements.second.element)
            self.eq(
                'not', sel.first.elements.second.pseudoclasses.first.value
            )

        ''' Element to pseudoclasses '''
        sels = [
            ':not(p) div',
            '*:not(p) div',
            'div:not(p) div',
        ]

        for i, sel in enumerate(sels):
            sel = dom.selectors(sel)
            self.eq('div',  sel.first.elements.second.element)
            if i.last:
                self.eq('div',  sel.first.elements.first.element)
            else:
                self.eq('*',  sel.first.elements.first.element)
            self.eq(
                'not', sel.first.elements.first.pseudoclasses.first.value
            )

    def it_parses_chain_of_elements_and_attributes(self):
        ''' Element to attribute '''
        sels = [
            'div [foo=bar]',
            'div *[foo=bar]',
            'div p[foo=bar]',
        ]

        for i, sel in enumerate(sels):
            sel = dom.selectors(sel)
            self.eq('div',  sel.first.elements.first.element)
            if i.last:
                self.eq('p',  sel.first.elements.second.element)
            else:
                self.eq('*',  sel.first.elements.second.element)
            self.eq(
                'foo', sel.first.elements.second.attributes.first.key
            )

            self.eq(
                'bar', sel.first.elements.second.attributes.first.value
            )

        sels = [
            '[foo=bar] div',
            '*[foo=bar] div',
            'p[foo=bar] div',
        ]

        ''' Attribute to element '''
        for i, sel in enumerate(sels):
            sel = dom.selectors(sel)
            self.eq('div',  sel.first.elements.second.element)
            if i.last:
                self.eq('p',  sel.first.elements.first.element)
            else:
                self.eq('*',  sel.first.elements.first.element)
            self.eq(
                'foo', sel.first.elements.first.attributes.first.key
            )

            self.eq(
                'bar', sel.first.elements.first.attributes.first.value
            )

    def it_parses_chain_of_elements_and_identifiers(self):
        ''' Element to identifier '''
        sels = [
            'div #my-id',
            'div *#my-id',
            'div p#my-id',
        ]

        for i, sel in enumerate(sels):
            sel = dom.selectors(sel)
            self.eq('div',  sel.first.elements.first.element)
            if i.last:
                self.eq('p',  sel.first.elements.second.element)
            else:
                self.eq('*',  sel.first.elements.second.element)

            self.eq(
                'my-id', sel.first.elements.second.id
            )

        ''' Identitifier to element '''
        sels = [
            '#my-id div',
            '*#my-id div',
            'p#my-id div',
        ]

        for i, sel in enumerate(sels):
            sel = dom.selectors(sel)
            self.eq('div',  sel.first.elements.second.element)
            if i.last:
                self.eq('p',  sel.first.elements.first.element)
            else:
                self.eq('*',  sel.first.elements.first.element)

            self.eq(
                'my-id', sel.first.elements.first.id
            )

    def it_parses_attribute_elements(self):
        sels = 'E[foo=bar] F[qux="quux"] G[garply=waldo]'
        expect = 'E[foo=bar] F[qux=quux] G[garply=waldo]'
        sels = dom.selectors(sels)
        self.repr(expect, sels)
        self.str(expect, sels)
        self.one(sels)
        sel = sels.first

        el = sel.elements.first
        self.eq('E', el.element)
        self.one(el.attributes)
        attr = el.attributes.first
        self.eq('foo', attr.key)
        self.eq('=', attr.operator)
        self.eq('bar', attr.value)

        el = sel.elements.second
        self.eq('F', el.element)
        self.one(el.attributes)
        attr = el.attributes.first
        self.eq('qux', attr.key)
        self.eq('=', attr.operator)
        self.eq('quux', attr.value)

        el = sel.elements.third
        self.eq('G', el.element)
        self.one(el.attributes)
        attr = el.attributes.first
        self.eq('garply', attr.key)
        self.eq('=', attr.operator)
        self.eq('waldo', attr.value)

        sels = 'E[foo~=bar] F[qux^="quux"] G[garply$=waldo]'
        expect = 'E[foo~=bar] F[qux^=quux] G[garply$=waldo]'
        sels = dom.selectors(sels)
        self.repr(expect, sels)
        self.str(expect, sels)
        self.one(sels)
        sel = sels.first

        el = sel.elements.first
        self.eq('E', el.element)
        self.one(el.attributes)
        attr = el.attributes.first
        self.eq('foo', attr.key)
        self.eq('~=', attr.operator)
        self.eq('bar', attr.value)

        el = sel.elements.second
        self.eq('F', el.element)
        self.one(el.attributes)
        attr = el.attributes.first
        self.eq('qux', attr.key)
        self.eq('^=', attr.operator)
        self.eq('quux', attr.value)

        el = sel.elements.third
        self.eq('G', el.element)
        self.one(el.attributes)
        attr = el.attributes.first
        self.eq('garply', attr.key)
        self.eq('$=', attr.operator)
        self.eq('waldo', attr.value)

        # multiple attribute selectors
        sels = 'E[foo=bar][qux="quux"] F[garply=waldo][foo=bar]'
        expect = 'E[foo=bar][qux=quux] F[garply=waldo][foo=bar]'
        sels = dom.selectors(sels)
        self.repr(expect, sels)
        self.str(expect, sels)
        self.one(sels)
        sel = sels.first

        el = sel.elements.first
        self.eq('E', el.element)
        self.two(el.attributes)
        attr = el.attributes.first
        self.eq('foo', attr.key)
        self.eq('=', attr.operator)
        self.eq('bar', attr.value)
        attr = el.attributes.second
        self.eq('qux', attr.key)
        self.eq('=', attr.operator)
        self.eq('quux', attr.value)

        el = sel.elements.second
        self.eq('F', el.element)
        self.two(el.attributes)
        attr = el.attributes.first
        self.eq('garply', attr.key)
        self.eq('=', attr.operator)
        self.eq('waldo', attr.value)
        attr = el.attributes.second
        self.eq('foo', attr.key)
        self.eq('=', attr.operator)
        self.eq('bar', attr.value)

        sels = 'E[foo*=bar]'
        expect = 'E[foo*=bar]'
        sels = dom.selectors(sels)
        self.repr(expect, sels)
        self.str(expect, sels)
        self.one(sels)
        sel = sels.first

        el = sel.elements.first
        self.eq('E', el.element)
        self.one(el.attributes)
        attr = el.attributes.first
        self.eq('foo', attr.key)
        self.eq('*=', attr.operator)
        self.eq('bar', attr.value)

        sels = 'E[foo*=bar] F[baz|=qux]'
        expect = 'E[foo*=bar] F[baz|=qux]'
        sels = dom.selectors(sels)
        self.repr(expect, sels)
        self.str(expect, sels)
        self.one(sels)
        sel = sels.first

        self.two(sel.elements)
        el = sel.elements.first
        self.eq('E', el.element)
        self.one(el.attributes)
        attr = el.attributes.first
        self.eq('foo', attr.key)
        self.eq('*=', attr.operator)
        self.eq('bar', attr.value)

        el = sel.elements.second
        self.eq('F', el.element)
        self.one(el.attributes)
        attr = el.attributes.first
        self.eq('baz', attr.key)
        self.eq('|=', attr.operator)
        self.eq('qux', attr.value)

        sels = '[disabled]'
        sels = dom.selectors(sels)
        self.repr('*[disabled]', sels)
        self.str('*[disabled]', sels)
        self.one(sels)
        sel = sels.first

        self.one(sel.elements)
        el = sel.elements.first
        self.eq('*', el.element)
        self.one(el.attributes)
        attr = el.attributes.first
        self.eq('disabled', attr.key)
        self.none(attr.operator)
        self.none(attr.value)

        sels = [
            "E[foo='bar baz']",
            'E[foo="bar baz"]',
        ]

        for sel in sels:
            sels = dom.selectors(sel)
            expect = 'E[foo=bar baz]'
            self.repr(expect, sels)
            self.str(expect, sels)
            self.one(sels)
            sel = sels.first
            self.one(sel.elements)
            self.one(sel.elements.first.attributes)
            self.eq('foo', sel.elements.first.attributes.first.key)
            self.eq(
                'bar baz', 
                sel.elements.first.attributes.first.value
            )

    def it_parses_class_elements(self):
        ''' E.warning '''
        sels = expect = 'E.warning'
        sels = dom.selectors(sels)
        self.str(expect, sels)
        self.repr(expect, sels)
        self.one(sels)
        self.one(sels.first.elements)
        self.type(dom.selector.element, sels.first.elements.first)
        self.eq('E', sels.first.elements.first.element)
        self.one(sels.first.elements.first.classes)
        self.type(
          dom.selector.class_,
          sels.first.elements.first.classes.first
        )
        self.eq(
          'warning', 
          sels.first.elements.first.classes.first.value
        )

        ''' E.warning F.danger '''
        sels = expect = 'E.warning F.danger'
        sels = dom.selectors(sels)
        self.str(expect, sels)
        self.repr(expect, sels)
        self.one(sels)
        self.two(sels.first.elements)

        e = sels.first.elements.first
        self.type(dom.selector.element, e)
        self.eq('E', e.element)
        self.one(e.classes)
        self.type(dom.selector.class_, e.classes.first)
        self.eq('warning', e.classes.first.value)

        e = sels.first.elements.second
        self.type(dom.selector.element, e)
        self.eq('F', e.element)
        self.one(e.classes)
        self.type(dom.selector.class_, e.classes.first)
        self.eq('danger', e.classes.first.value)

        ''' E.warning.danger '''
        sels = expect = 'E.warning.danger'
        sels = dom.selectors(sels)
        self.str(expect, sels)
        self.repr(expect, sels)
        self.one(sels)
        self.one(sels.first.elements)

        e = sels.first.elements.first
        self.type(dom.selector.element, e)
        self.eq('E', e.element)
        self.two(e.classes)
        self.type(dom.selector.class_, e.classes.first)
        self.type(dom.selector.class_, e.classes.second)
        self.eq('warning', e.classes.first.value)
        self.eq('danger', e.classes.second.value)

        ''' E.warning.danger.fire '''
        sels = expect = 'E.warning.danger.fire'
        sels = dom.selectors(sels)
        self.str(expect, sels)
        self.repr(expect, sels)
        self.one(sels)
        self.one(sels.first.elements)

        e = sels.first.elements.first
        self.type(dom.selector.element, e)
        self.eq('E', e.element)
        self.three(e.classes)
        self.type(dom.selector.class_, e.classes.first)
        self.type(dom.selector.class_, e.classes.second)
        self.eq('warning', e.classes.first.value)
        self.eq('danger', e.classes.second.value)
        self.eq('fire', e.classes.third.value)

        ''' E.warning.danger.fire F.primary.secondary.success'''
        sels = expect = 'E.warning.danger.fire F.primary.secondary.success'
        sels = dom.selectors(sels)
        self.str(expect, sels)
        self.repr(expect, sels)
        self.one(sels)
        self.two(sels.first.elements)

        e = sels.first.elements.first
        self.type(dom.selector.element, e)
        self.eq('E', e.element)
        self.three(e.classes)
        self.type(dom.selector.class_, e.classes.first)
        self.type(dom.selector.class_, e.classes.second)
        self.eq('warning', e.classes.first.value)
        self.eq('danger', e.classes.second.value)
        self.eq('fire', e.classes.third.value)

        e = sels.first.elements.second
        self.type(dom.selector.element, e)
        self.eq('F', e.element)
        self.three(e.classes)
        self.type(dom.selector.class_, e.classes.first)
        self.type(dom.selector.class_, e.classes.second)
        self.eq('primary', e.classes.first.value)
        self.eq('secondary', e.classes.second.value)
        self.eq('success', e.classes.third.value)

    def it_parses_id_elements(self):
        eid = 'x' + uuid4().hex
        fid = 'x' + uuid4().hex
        gid = 'x' + uuid4().hex

        ''' E#id '''
        sels = expect = 'E#' + eid
        sels = dom.selectors(sels)
        self.str(expect, sels)
        self.repr(expect, sels)
        self.one(sels)
        self.one(sels.first.elements)

        e = sels.first.elements.first
        self.eq(eid, e.id)

        ''' E#id F#id'''
        sels = expect = 'E#%s F#%s' % (eid, fid)
        sels = dom.selectors(sels)
        self.str(expect, sels)
        self.repr(expect, sels)
        self.one(sels)
        self.two(sels.first.elements)

        e = sels.first.elements.first
        self.eq(eid, e.id)

        f = sels.first.elements.second
        self.eq(fid, f.id)

        ''' E#id F#id G#id'''
        sels = expect = 'E#%s F#%s G#%s' % (eid, fid, gid)
        sels = dom.selectors(sels)
        self.str(expect, sels)
        self.repr(expect, sels)
        self.one(sels)
        self.three(sels.first.elements)

        e = sels.first.elements.first
        self.eq(eid, e.id)

        f = sels.first.elements.second
        self.eq(fid, f.id)

        g = sels.first.elements.third
        self.eq(gid, g.id)

    def it_parses_nth_child(self):
        ''' E:first-child '''
        sels = 'E:first-child'
        sels = dom.selectors(sels)
        expect = 'E:first-child' 
        self.str(expect, sels)
        self.repr(expect, sels)
        self.one(sels)
        self.one(sels.first.elements)

        e = sels.first.elements.first
        self.eq('E', e.element)
        self.eq('first-child', e.pseudoclasses.first.value)

        '''E:first-child F:last-child'''
        sels = 'E:first-child F:last-child'
        sels = dom.selectors(sels)
        self.str('E:first-child F:last-child', sels)
        self.repr('E:first-child F:last-child', sels)
        self.one(sels)
        self.two(sels.first.elements)

        e = sels.first.elements.first
        self.eq('E', e.element)
        self.eq('first-child', e.pseudoclasses.first.value)

        f = sels.first.elements.second
        self.eq('F', f.element)
        self.eq('last-child', f.pseudoclasses.first.value)

    def it_parses_pseudoclass(self):
        ''' E:empty'''
        sels = 'E:empty'
        sels = dom.selectors(sels)
        self.one(sels)
        self.one(sels.first.elements)

        self.str('E:empty', sels)
        self.repr('E:empty', sels)

        pclss = sels.first.elements.first.pseudoclasses

        self.one(pclss)
        self.type(dom.selector.pseudoclasses, pclss)
        pcls = pclss.first
        self.type(dom.selector.pseudoclass, pcls)
        self.eq('empty', pcls.value)

    def it_parses_chained_pseudoclass(self):
        ''' E:empty:root'''
        sels = 'E:empty:root'
        sels = dom.selectors(sels)
        self.one(sels)
        self.one(sels.first.elements)

        self.str('E:empty:root', sels)
        self.repr('E:empty:root', sels)

        pclss = sels.first.elements.first.pseudoclasses

        self.two(pclss)
        self.type(dom.selector.pseudoclasses, pclss)

        pcls = pclss.first
        self.type(dom.selector.pseudoclass, pcls)
        self.eq('empty', pcls.value)

        pcls = pclss.second
        self.type(dom.selector.pseudoclass, pcls)
        self.eq('root', pcls.value)
        
    def it_parses_chained_argumentative_pseudo_classes(self):
        ''' E:nth-child(odd):nth-child(even) '''
        sels = 'E:nth-child(odd):nth-child(even)'
        sels = dom.selectors(sels)
        self.one(sels)
        self.one(sels.first.elements)
        self.str('E:nth-child(2n+1):nth-child(2n+0)', sels)
        self.repr('E:nth-child(2n+1):nth-child(2n+0)', sels)

    def it_parses_argumentative_pseudo_classes(self):
        ''' E:nth-child(odd) '''
        sels = 'E:nth-child(odd)'
        sels = dom.selectors(sels)
        self.one(sels)
        self.one(sels.first.elements)
        self.str('E:nth-child(2n+1)', sels)
        self.repr('E:nth-child(2n+1)', sels)

        e = sels.first.elements.first
        self.eq('E', e.element)
        self.eq('nth-child', e.pseudoclasses.first.value)
        self.eq(2, e.pseudoclasses.first.arguments.a)
        self.eq(1, e.pseudoclasses.first.arguments.b)

        ''' E:nth-child(even) '''
        sels = 'E:nth-child(even)'
        sels = dom.selectors(sels)
        self.one(sels)
        self.one(sels.first.elements)
        self.str('E:nth-child(2n+0)', sels)
        self.repr('E:nth-child(2n+0)', sels)

        e = sels.first.elements.first
        self.eq('E', e.element)
        self.eq('nth-child', e.pseudoclasses.first.value)
        self.eq(2, e.pseudoclasses.first.arguments.a)
        self.eq(0, e.pseudoclasses.first.arguments.b)

        ''' E:nth-child(2n + 1)'''
        sels = 'E:nth-child(2n + 1)'
        sels = dom.selectors(sels)
        self.str('E:nth-child(2n+1)', sels)
        self.repr('E:nth-child(2n+1)', sels)
        self.one(sels)
        self.one(sels.first.elements)

        e = sels.first.elements.first
        self.eq('E', e.element)
        self.eq('nth-child', e.pseudoclasses.first.value)
        self.eq(2, e.pseudoclasses.first.arguments.a)
        self.eq(1, e.pseudoclasses.first.arguments.b)

        '''foo:nth-child(0n + 5)'''
        sels = [
          'foo:nth-child(0n + 5)',
          'foo:nth-child(5)',
        ]

        for sel in sels:
            sels = dom.selectors(sel)
            self.str('foo:nth-child(0n+5)', sels)
            self.repr('foo:nth-child(0n+5)', sels)
            self.one(sels)
            self.one(sels.first.elements)


            e = sels.first.elements.first
            self.eq('foo', e.element)
            self.eq('nth-child', e.pseudoclasses.first.value)
            self.notnone(e.pseudoclasses.first.arguments)
            self.eq(0, e.pseudoclasses.first.arguments.a)
            self.eq(5, e.pseudoclasses.first.arguments.b)

        ''' E:nth-child(10n - 1)'''
        sels = 'E:nth-child(10n - 1)'
        sels = dom.selectors(sels)
        self.str('E:nth-child(10n-1)', sels)
        self.repr('E:nth-child(10n-1)', sels)
        self.one(sels)
        self.one(sels.first.elements)
        e = sels.first.elements.first

        self.eq(e.element, 'E')
        self.eq(e.pseudoclasses.first.value, 'nth-child')
        self.eq(10, e.pseudoclasses.first.arguments.a)
        self.eq(-1, e.pseudoclasses.first.arguments.b)

        sels = [
            'E:nth-child(n)',
            'E:nth-child(1n + 0)',
            'E:nth-child(n + 0)',
        ]

        for i, sel in enumerate(sels):
            sels = dom.selectors(sel)
            self.str('E:nth-child(1n+0)', sels, 'For: ' + sel)
            self.repr('E:nth-child(1n+0)', sels, 'For: ' + sel)
            args = sels.first.elements.first.pseudoclasses.first.arguments
            self.eq(1, args.a)
            self.eq(0, args.b)

        sels = [
            'E:nth-child(-n)',
            'E:nth-child(-1n + 0)',
        ]

        sels = [
            'E:nth-child(-n + 0)',
        ]

        for i, sel in enumerate(sels):
            sels = dom.selectors(sel)
            self.str('E:nth-child(-1n+0)', sels, 'For: ' + sel)
            self.repr('E:nth-child(-1n+0)', sels, 'For: ' + sel)
            args = sels.first.elements.first.pseudoclasses.first.arguments
            self.eq(-1, args.a)
            self.eq(0, args.b)

        sels = [
            'E:nth-child(2n)',
            'E:nth-child(2n + 0)',
        ]

        for sel in sels:
            sels = dom.selectors(sel)
            self.str('E:nth-child(2n+0)', sels, 'For: ' + sel)
            self.repr('E:nth-child(2n+0)', sels, 'For: ' + sel)
            args = sels.first.elements.first.pseudoclasses.first.arguments
            self.eq(2, args.a)
            self.eq(0, args.b)

        sel = 'E:nth-child( 3n + 1 )'
        sels = dom.selectors(sel)
        self.str('E:nth-child(3n+1)', sels)
        self.repr('E:nth-child(3n+1)', sels)
        args = sels.first.elements.first.pseudoclasses.first.arguments
        self.eq(3, args.a)
        self.eq(1, args.b)

        sel =  'E:nth-child( +3n - 2 )'
        sels = dom.selectors(sel)
        self.str('E:nth-child(3n-2)', sels)
        self.repr('E:nth-child(3n-2)', sels)
        args = sels.first.elements.first.pseudoclasses.first.arguments
        self.eq(3, args.a)
        self.eq(-2, args.b)

        sel =  'E:nth-child( -n+ 6)'
        sels = dom.selectors(sel)
        self.str('E:nth-child(-1n+6)', sels)
        self.repr('E:nth-child(-1n+6)', sels)
        args = sels.first.elements.first.pseudoclasses.first.arguments
        self.eq(-1, args.a)
        self.eq(6, args.b)

        sel = 'E:nth-child( +6 )'
        sels = dom.selectors(sel)
        self.str('E:nth-child(0n+6)', sels)
        self.repr('E:nth-child(0n+6)', sels)
        args = sels.first.elements.first.pseudoclasses.first.arguments
        self.eq(0, args.a)
        self.eq(6, args.b)

    def it_parses_lang_pseudoclass(self):
        # Helpful explaination:
        #     https://bitsofco.de/use-the-lang-pseudo-class-over-the-lang-attribute-for-language-specific-styles/

        sel =  'E:lang(fr)'
        sels = dom.selectors(sel)
        self.repr('E:lang(fr)', sels)
        self.str('E:lang(fr)', sels)
        args = sels.first.elements.first.pseudoclasses.first.arguments
        self.none(args.a)
        self.none(args.b)
        self.eq('fr', args.c)

        sel =  'E:lang(fr-be)'
        sels = dom.selectors(sel)
        self.repr('E:lang(fr-be)', sels)
        self.str('E:lang(fr-be)', sels)
        args = sels.first.elements.first.pseudoclasses.first.arguments
        self.none(args.a)
        self.none(args.b)
        self.eq('fr-be', args.c)

    def it_parses_universal_selector(self):
        sels = dom.selectors('*')
        self.str('*', sels)
        self.repr('*', sels)
        self.eq('*', sels.first.elements.first.element)

        sels = dom.selectors('*[foo=bar]')
        el = sels.first.elements.first
        self.eq('*', el.element)
        self.one(el.attributes)
        attr = el.attributes.first
        self.eq('foo', attr.key)
        self.eq('=', attr.operator)
        self.eq('bar', attr.value)

        sels = expect = '*.warning'
        sels = dom.selectors(sels)
        self.repr(expect, sels)
        self.str(expect, sels)
        self.one(sels)
        self.one(sels.first.elements)
        self.type(dom.selector.element, sels.first.elements.first)
        self.eq('*', sels.first.elements.first.element)
        self.one(sels.first.elements.first.classes)
        self.type(
          dom.selector.class_,
          sels.first.elements.first.classes.first
        )
        self.eq(
          'warning', 
          sels.first.elements.first.classes.first.value
        )

        eid = 'x' + uuid4().hex
        sels = expect = '*#' + eid
        sels = dom.selectors(sels)
        self.one(sels)
        self.one(sels.first.elements)
        self.repr(expect, sels)
        self.str(expect, sels)
        el = sels.first.elements.first
        self.eq('*', el.element)
        self.eq(eid, el.id)

        # Pseudoclasses
        sels = dom.selectors('*:root')
        el = sels.first.elements.first
        self.eq('*', el.element)
        self.one(el.pseudoclasses)
        self.eq('root', el.pseudoclasses.first.value)

        # Combine: *#1234 *.warning *.[foo=bar] *:root
        eid = 'x' + uuid4().hex
        expect = '*#' + eid
        expect += ' *.warning'
        expect += ' *[foo=bar]'
        expect += ' *:root'
        sels = dom.selectors(expect)
        self.repr(expect, sels)
        self.str(expect, sels)
        self.one(sels)
        self.four(sels.first.elements)

        el = sels.first.elements.first
        self.eq('*', el.element)
        self.eq(eid, el.id)

        el = sels.first.elements.second
        self.eq('*', el.element)
        self.eq('warning', el.classes.first.value)

        el = sels.first.elements.third
        self.eq('*', el.element)
        self.eq('foo', el.attributes.first.key)
        self.eq('bar', el.attributes.first.value)

        el = sels.first.elements.fourth
        self.eq('*', el.element)
        self.eq('root', el.pseudoclasses.first.value)

    def it_parses_implied_universal_selector(self):
        sels = dom.selectors('[foo=bar]')
        self.repr('*[foo=bar]', sels)
        self.str('*[foo=bar]', sels)
        el = sels.first.elements.first
        self.eq('*', el.element)
        self.one(el.attributes)
        attr = el.attributes.first
        self.eq('foo', attr.key)
        self.eq('=', attr.operator)
        self.eq('bar', attr.value)

        sels = '.warning'
        sels = dom.selectors(sels)
        self.repr('*.warning', sels)
        self.str('*.warning', sels)
        self.one(sels)
        self.one(sels.first.elements)
        self.type(dom.selector.element, sels.first.elements.first)
        self.eq('*', sels.first.elements.first.element)
        self.one(sels.first.elements.first.classes)
        self.type(
          dom.selector.class_,
          sels.first.elements.first.classes.first
        )
        self.eq(
          'warning', 
          sels.first.elements.first.classes.first.value
        )

        eid = 'x' + uuid4().hex
        sels = expect = '*#' + eid
        sels = dom.selectors(sels)
        self.one(sels)
        self.one(sels.first.elements)
        self.repr(expect, sels)
        self.str(expect, sels)
        el = sels.first.elements.first
        self.eq('*', el.element)
        self.eq(eid, el.id)

        # Combine: #1234 .warning [foo=bar] :root
        eid = 'x' + uuid4().hex
        expect = '*#' + eid
        expect += ' *.warning'
        expect += ' *[foo=bar]'
        expect += ' *:root'
        sels = expect.replace('*', '')
        sels = dom.selectors(sels)
        self.repr(expect, sels)
        self.str(expect, sels)
        self.one(sels)
        self.four(sels.first.elements)

        el = sels.first.elements.first
        self.eq('*', el.element)
        self.eq(eid, el.id)

        el = sels.first.elements.second
        self.eq('*', el.element)
        self.eq('warning', el.classes.first.value)

        el = sels.first.elements.third
        self.eq('*', el.element)
        self.eq('foo', el.attributes.first.key)
        self.eq('bar', el.attributes.first.value)

        el = sels.first.elements.fourth
        self.eq('*', el.element)
        self.eq('root', el.pseudoclasses.first.value)

    def it_parses_groups(self):
        # E F
        sels = dom.selectors('E, F')

        self.repr('E, F', sels)
        self.str('E, F', sels)
        self.two(sels)

        el = sels.first.elements.first
        self.type(dom.selector.element, el)
        self.eq('E', el.element)

        el = sels.second.elements.first
        self.type(dom.selector.element, el)
        self.eq('F', el.element)

        # E[foo=bar], F[baz=qux]
        sels = dom.selectors('E[foo=bar], F[baz=qux]')
        self.repr('E[foo=bar], F[baz=qux]', sels)
        self.str('E[foo=bar], F[baz=qux]', sels)
        self.two(sels)

        el = sels.first.elements.first
        self.type(dom.selector.element, el)
        self.eq('E', el.element)
        self.one(el.attributes)
        self.eq('foo', el.attributes.first.key)
        self.eq('bar', el.attributes.first.value)

        el = sels.second.elements.first
        self.type(dom.selector.element, el)
        self.eq('F', el.element)
        self.one(el.attributes)
        self.eq('baz', el.attributes.first.key)
        self.eq('qux', el.attributes.first.value)

    def it_parses_not(self):
        '''*:not(F)'''
        expect = '*:not(F)'
        sels = ':not(F)'
        sels = dom.selectors(sels)
        self.repr(expect, sels)
        self.one(sels)

        el = sels.first.elements.first
        self.one(sels.first.elements)
        self.type(dom.selector.element, el)
        self.eq('*', el.element)

        self.notnone(el.pseudoclasses.first.arguments.selectors)
        self.eq('not', el.pseudoclasses.first.value)
        sels = el.pseudoclasses.first.arguments.selectors
        self.one(sels)

        els = sels.first.elements
        self.one(els)

        el = els.first

        self.eq('F', el.element)

        '''E:not([foo=bar])'''
        expect = 'E:not(E[foo=bar])'
        sels = dom.selectors(expect)
        self.repr(expect, sels)
        self.one(sels)

        self.one(sels.first.elements)
        el = sels.first.elements.first
        self.type(dom.selector.element, el)
        self.eq('E', el.element)
        pcls = el.pseudoclasses.first

        self.type(dom.selector.pseudoclass, pcls)
        self.eq('not', pcls.value)
        sels = pcls.arguments.selectors
        self.type(dom.selectors, sels)
        self.one(sels.first.elements)
        el = sels.first.elements.first
        self.one(el.attributes)
        self.eq('foo', el.attributes.first.key)
        self.eq('=', el.attributes.first.operator)
        self.eq('bar', el.attributes.first.value)

        '''E:not(:first-of-type)'''
        expect = 'E:not(E:first-of-type)'
        sels = dom.selectors(expect)
        self.repr(expect, sels)
        self.one(sels)

        self.one(sels.first.elements)
        el = sels.first.elements.first
        self.type(dom.selector.element, el)
        pcls = el.pseudoclasses.first

        self.type(dom.selector.pseudoclass, pcls)
        self.eq('not', pcls.value)

        sels = pcls.arguments.selectors
        self.type(dom.selectors, sels)
        self.one(sels.first.elements)
        el = sels.first.elements.first
        self.eq('E', el.element)
        self.eq('first-of-type', el.pseudoclasses.first.value)

        # FIXME:dd6a4f93 There is an issue with the parsing of the not's
        # argument.
        # ''' E:not(:nth-child(2n+1)) '''
        # expect = 'E:not(E:nth-child(2n+1))'
        # sels = dom.selectors(expect)
        # self.repr(expect, sels)
        # self.one(sels)
        #
        # self.one(sels.first.elements)
        # el = sels.first.elements.first
        # self.type(dom.selector.element, el)
        # pcls = el.pseudoclasses.first
        #
        # self.type(dom.selector.pseudoclass, pcls)
        # self.eq('not', pcls.value)
        #
        # sels = pcls.arguments.selectors
        # self.type(dom.selectors, sels)
        # self.one(sels.first.elements)
        # el = sels.first.elements.first
        # self.eq('E', el.element)
        # self.eq('nth-child', el.pseudoclasses.first.value)
        # self.eq(2, el.pseudoclasses.first.arguments.a)
        # self.eq(1, el.pseudoclasses.first.arguments.b)

        ''' E:not(.warning) '''
        expect = 'E:not(E.warning)'
        sels = dom.selectors(expect)
        self.repr(expect, sels)
        self.one(sels)

        self.one(sels.first.elements)
        el = sels.first.elements.first
        self.type(dom.selector.element, el)
        pcls = el.pseudoclasses.first

        self.type(dom.selector.pseudoclass, pcls)
        self.eq('not', pcls.value)

        sels = pcls.arguments.selectors
        self.type(dom.selectors, sels)
        self.one(sels.first.elements)
        el = sels.first.elements.first
        self.eq('E', el.element)
        clss = el.classes
        self.one(clss)
        self.eq('warning', clss.first.value)

        '''*:not(F[foo=bar]:first-of-type)'''
        expect = '*:not(F[foo=bar]:first-of-type)'
        sels = ':not(F[foo=bar]:first-of-type)'
        sels = dom.selectors(sels)
        self.repr(expect, sels)
        self.one(sels)

        el = sels.first.elements.first
        self.one(sels.first.elements)
        self.type(dom.selector.element, el)
        self.eq('*', el.element)

        self.notnone(el.pseudoclasses.first.arguments.selectors)
        self.eq('not', el.pseudoclasses.first.value)
        sels = el.pseudoclasses.first.arguments.selectors
        self.one(sels)

        els = sels.first.elements
        self.one(els)

        el = els.first

        self.eq('F', el.element)

        self.one(el.attributes)
        self.eq('foo', el.attributes.first.key)
        self.eq('=', el.attributes.first.operator)
        self.eq('bar', el.attributes.first.value)

        pcls = el.pseudoclasses.first

        self.type(dom.selector.pseudoclass, pcls)
        self.eq('first-of-type', el.pseudoclasses.first.value)

    def it_raises_on_invalid_selectors(self):
        #dom.selectors('a . b'); return

        # Generic test function
        def test(sel, pos):
            try:
                dom.selectors(sel)
            except dom.CssSelectorParseError as ex:
                if pos is not None:
                    self.eq(pos, ex.pos, 'Selector: "%s"' % sel)
            except Exception as ex:
                self.fail(
                    'Invalid exception: %s "%s"' % (str(ex), sel)
                )
            else:
                self.fail('No exception: "%s"' % sel)

        ''' Invalid combinators '''

        combs = set(list('>+~'))

        ignore = set(list('[\':.'))

        # `invalids` are punctuation exculding the above combs
        invalids = set(string.punctuation) - combs - ignore

        sels = {
            'a %s b' : 2
        }

        for invalid in invalids:
            for sel, pos in sels.items():
                sel %= invalid
                if invalid == '*': continue
                test(sel, pos)

        ''' Selector groups '''
        sels = {
            'a,,b'   :  2,
            'a:,b'   :  2,
            'a(,b'   :  1,
            'a,b,,'  :  4,
            'a,b,'   :  4,
        }

        for sel, pos in sels.items():
            test(sel, pos)

        # NOTE ':not(:not(li))' fails but for the wrong reason (see
        # dd6a4f93). It should fail because the standard says that :not
        # can't have :not as its argument.  However this is not
        # happening. When the dd6a4f93 issue is fixed, we can add code
        # that explicitly raises an exception when a ':not' is found as
        # an argument to :not. This could would likely go in
        # pseudoclass.demand().

        ''' Pseudoclasses arguments '''
        sels = {
            ':nth-child()'             :  None,
            ':nth-last-child(2a)'      :  None,
            ':nth-of-type(4.4)'        :  None,
            ':nth-last-of-type(derp)'  :  None,
            ':nth-child(3x+4)'         :  None,
            ':nth-child(2n+1+)'        :  None,
            ':nth-child(*2n+1)'        :  None,
            ':nth-child(a2n+1)'        :  None,
            ':not(::)'                 :  None,
            ':not(:not(li))'           :  None,
        }

        for sel, pos in sels.items():
            test(sel, pos)

        ''' Pseudoclasses '''
        sels = {
            ':'                            :  1,
            '::'                           :  1,
            ':not-a-pseudoclass()'         :  20,
            ':not-a-pseudoclass'           :  18,
            '.my-class:not-a-pseudoclass'  :  27,
            ':empty:'                      :  7,
            ':nth-child('                  :  11,
        }

        for sel, pos in sels.items():
            test(sel, pos)

        ''' Classes '''
        sels = {
            '.'                          :  1,
            'a . b'                      :  3,
            '..my-class'                 :  1,
            '.:my-class'                 :  1,
            './my-class'                 :  1,
            '.#my-class'                 :  1,
            '.#my#class'                 :  1,
            '.my-class..my-other-class'  :  10,
            '.my-class.'                 :  10,
            '.my-class]'                 :  9,
            '.my-class['                 :  10,
            '.my-class/'                 :  10,
        }

        for sel, pos in sels.items():
            test(sel, pos)

        ''' Attributes '''
        sels = {
            '.[foo=bar]'              :  1,
            '*.[foo=bar]'             :  2,
            '.*[foo=bar]'             :  1,
            '[foo=bar'                :  8,
            'foo=bar]'                :  3,
            'div[]'                  :  4,
            'div[=]'                  :  4,
            'div[foo=]'               :  8,
            'div[=bar]'               :  4,
            'div.[foo=bar]'           :  4,
            'div:[foo=bar]'           :  4,
            'div#[foo=bar]'           :  3,
            'div[[foo=bar]'           :  4,
            'div[foo=bar]]'           :  12,
            'div[foo%bar]'            :  7,
            'div[foo%=bar]'           :  7,
            'div[foo=%bar]'           :  8,
            'div[foo===bar]'          :  9,
            'div[f/o=bar]'            :  5,
            'div[f#o=bar]'            :  5,
            'div[bar=]'               :  8,
            'div[foo=bar][foo=bar'    :  20,
            'div[foo=bar]foo=bar]'    :  15,
            'div[foo=bar][[foo=bar]'  :  13,
            'div[foo=bar][foo%bar]'   :  16,
            'div[foo=bar][foo=]'      :  17,
            'div[foo=bar].'           :  13,
        }

        for sel, pos in sels.items():
            test(sel, pos)

        ''' Leading punctuation characters should raise exceptions '''

        # These are acceptable as loading characters - they're the CSS
        # selector deliminators
        delims = list('.:[#*')

        # `invalids` are punctuation exculding the above delims
        invalids = set(string.punctuation) - set(delims)

        # Backslashes and underscores are valid, too
        invalids -= set(list('\\_'))

        for invalid in invalids:
            sel = invalid + 'div'
            test(sel, 0)

        ''' Empty strings and whitespace '''
        sels = list(string.whitespace)
        sels.append('')

        for sel in sels: 
            self.expect(
                dom.CssSelectorParseError, 
                lambda: dom.selectors(sel),
           )

TestHtml = tester.tester.dedent('''
<html id="myhtml" arbit="trary">
  <!-- This is an HTML document -->
  <head>
    <!-- This is the head of the HTML document -->
    <base href="www.example.com">
  </head>
  <body>
    <p>
      Lorum &amp; Ipsum Δ
    </p>
    <p>
      This is some
      <strong>
        strong text.
      </strong>
    </p>
    <p>
      This too is some
      <strong>
        strong text.
      </strong>
    </p>
  </body>
</html>
''')

TestHtmlMin = '<html id="myhtml" arbit="trary"><!-- This is an HTML document --><head><!-- This is the head of the HTML document --><base href="www.example.com"></head><body><p>Lorum &amp; Ipsum Δ</p><p>This is some<strong>strong text.</strong></p><p>This too is some<strong>strong text.</strong></p></body></html>'


ListHtml = '''
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
  <body>
    <article>
      <section>
        <ol>
          <li id="0">
            <p>
              This is list item 0.
            </p>
          </li>
          <li id="1">
            <p>
              This is list item 1.
            </p>
          </li>
          <li id="2">
            <p>
              This is list item 2.
            </p>
          </li>
          <li class="my-class" id="3">
            <p>
              This is list item 3.
            </p>
          </li>
          <li id="4">
            <p>
              This is list item 4.
            </p>
          </li>
          <li id="5">
            <p>
              This is list item 5.
            </p>
          </li>
          <li id="6">
            <p>
              This is list item 6.
            </p>
          </li>
          <li id="7">
            <p>
              This is list item 7.
            </p>
          </li>
          <li id="8">
            <p>
              This is list item 8.
            </p>
          </li>
          <li id="9">
            <p>
              This is list item 9.
            </p>
          </li>
          <li id="10">
            <p>
              This is list item 10.
            </p>
          </li>
          <li id="11">
            <p>
              This is list item 11.
            </p>
          </li>
        </ol>
      </section>
    </article>
  </body>
</html>
'''

AdjacencyHtml = '''
  <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en" debug="true">
    <head>
      <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
    </head>
    <body>
      <div id="first-div">
        <p id="child-of-div">
          <span id="child-of-p-of-div">
          </span>
        </p>
      </div>
      <p id="before-the-adjacency-anchor">
      </p>
      <p id="immediatly-before-the-adjacency-anchor">
      </p>
      <div id="adjacency-anchor">
        <h2>
          <p id="child-of-h2" class="p-header">
            <span id="child-of-p-of-h2" class="span-header">
            </span>
          </p>
          <q id="second-child-of-h2">
            second child of h2
          </q>
        </h2>
      </div>
      <p id="immediatly-after-the-adjacency-anchor">
      </p>
      <p id="after-the-adjacency-anchor">
      </p>
    </body>
  </html>
'''

Shakespeare = '''
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en" debug="true">
  <head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
  </head>
  <body>
    <div id="test" class="container">
      <div class="dialog">
        <h2 id="023338d1-5503-4054-98f7-c1e9c9ad390d f6836822-589e-40bf-a3f7-a5c3185af4f7"
            class='header'>
          As You Like It
        </h2>
        <div id="playwright">
          by William Shakespeare
        </div>
        <div class="dialog scene thirdClass" id="scene1">
          <h3>
            ACT I, SCENE III. A room in the palace.
          </h3>
          <div class="dialog">
            <div class="direction">
              Enter CELIA and ROSALIND
            </div>
          </div>
          <div id="speech1" class="character">
            CELIA
          </div>
          <div class="dialog">
            <div id="scene1.3.1">
              Why, cousin! why, Rosalind! Cupid have mercy! not a word?
            </div>
          </div>
          <div id="speech2" class="character">
            ROSALIND
          </div>
          <div class="dialog">
            <div id="scene1.3.2">
              Not one to throw at a dog.
            </div>
          </div>
          <div id="speech3" class="character">
            CELIA
          </div>
          <div class="dialog">
            <div id="scene1.3.3">
              No, thy words are too precious to be cast away upon
            </div>
            <div id="scene1.3.4">
              curs; throw some of them at me; come, lame me with reasons.
            </div>
          </div>
          <div id="speech4" class="character">
            ROSALIND
          </div>
          <div id="speech5" class="character">
            CELIA
          </div>
          <div class="dialog">
            <div id="scene1.3.8">
              But is all this for your father?
            </div>
          </div>
          <div class="dialog">
            <div id="scene1.3.5">
              Then there were two cousins laid up; when the one
            </div>
            <div id="scene1.3.6">
              should be lamed with reasons and the other mad
            </div>
            <div id="scene1.3.7">
              without any.
            </div>
          </div>
          <div id="speech6" class="character">
            ROSALIND
          </div>
          <div class="dialog">
            <div id="scene1.3.9">
              No, some of it is for my child&#x27;s father. O, how
            </div>
            <div id="scene1.3.10">
              full of briers is this working-day world!
            </div>
          </div>
          <div id="speech7" class="character">
            CELIA
          </div>
          <div class="dialog">
            <div id="scene1.3.11">
              They are but burs, cousin, thrown upon thee in
            </div>
            <div id="scene1.3.12">
              holiday foolery: if we walk not in the trodden
            </div>
            <div id="scene1.3.13">
              paths our very petticoats will catch them.
            </div>
          </div>
          <div id="speech8" class="character">
            ROSALIND
          </div>
          <div class="dialog">
            <div id="scene1.3.14">
              I could shake them off my coat: these burs are in my heart.
            </div>
          </div>
          <div id="speech9" class="character">
            CELIA
          </div>
          <div class="dialog">
            <div id="scene1.3.15">
              Hem them away.
            </div>
          </div>
          <div id="speech10" class="character">
            ROSALIND
          </div>
          <div class="dialog">
            <div id="scene1.3.16">
              I would try, if I could cry &#x27;hem&#x27; and have him.
            </div>
          </div>
          <div id="speech11" class="character">
            CELIA
          </div>
          <div class="dialog">
            <div id="scene1.3.17">
              Come, come, wrestle with thy affections.
            </div>
          </div>
          <div id="speech12" class="character">
            ROSALIND
          </div>
          <div class="dialog">
            <div id="scene1.3.18">
              O, they take the part of a better wrestler than myself!
            </div>
          </div>
          <div id="speech13" class="character">
            CELIA
          </div>
          <div class="dialog">
            <div id="scene1.3.19">
              O, a good wish upon you! you will try in time, in
            </div>
            <div id="scene1.3.20">
              despite of a fall. But, turning these jests out of
            </div>
            <div id="scene1.3.21">
              service, let us talk in good earnest: is it
            </div>
            <div id="scene1.3.22">
              possible, on such a sudden, you should fall into so
            </div>
            <div id="scene1.3.23">
              strong a liking with old Sir Rowland&#x27;s youngest son?
            </div>
          </div>
          <div id="speech14" class="character">
            ROSALIND
          </div>
          <div class="dialog">
            <div id="scene1.3.24">
              The duke my father loved his father dearly.
            </div>
          </div>
          <div id="speech15" class="character">
            CELIA
          </div>
          <div class="dialog">
            <div id="scene1.3.25">
              Doth it therefore ensue that you should love his son
            </div>
            <div id="scene1.3.26">
              dearly? By this kind of chase, I should hate him,
            </div>
            <div id="scene1.3.27">
              for my father hated his father dearly; yet I hate
            </div>
            <div id="scene1.3.28">
              not Orlando.
            </div>
          </div>
          <div id="speech16" class="character">
            ROSALIND
          </div>
          <div id="herp" title="wtf" class="dialog">
            <div id="scene1.3.29">
              No, faith, hate him not, for my sake.
            </div>
          </div>
          <div id="speech17" class="character">
            CELIA
          </div>
          <div class="dialog">
            <div id="scene1.3.30">
              Why should I not? doth he not deserve well?
            </div>
          </div>
          <div id="speech18" class="character">
            ROSALIND
          </div>
          <div class="dialog">
            <div id="scene1.3.31">
              Let me love him for that, and do you love him
            </div>
            <div id="scene1.3.32">
              because I do. Look, here comes the duke.
            </div>
          </div>
          <div id="speech19" class="character">
            CELIA
          </div>
          <div class="dialog">
            <div id="scene1.3.33">
              With his eyes full of anger.
            </div>
            <div class="direction">
              Enter DUKE FREDERICK, with Lords
            </div>
          </div>
          <div id="speech20" class="character">
            DUKE FREDERICK
          </div>
          <div class="dialog">
            <div id="scene1.3.34">
              Mistress, dispatch you with your safest haste
            </div>
            <div id="scene1.3.35">
              And get you from our court.
            </div>
          </div>
          <div id="speech21" class="character">
            ROSALIND
          </div>
          <div class="dialog">
            <div id="scene1.3.36">
              Me, uncle?
            </div>
          </div>
          <div id="speech22" class="character">
            DUKE FREDERICK
          </div>
          <div class="dialog">
            <div id="scene1.3.37">
              You, cousin
            </div>
            <div id="scene1.3.38">
              Within these ten days if that thou be&#x27;st found
            </div>
            <div id="scene1.3.39">
              So near our public court as twenty miles,
            </div>
            <div id="scene1.3.40">
              Thou diest for it.
            </div>
          </div>
          <div id="speech23" class="character">
            ROSALIND
          </div>
          <div class="dialog">
            <div id="scene1.3.41">
              I do beseech your grace,
            </div>
            <div id="scene1.3.42">
              Let me the knowledge of my fault bear with me:
            </div>
            <div id="scene1.3.43">
              If with myself I hold intelligence
            </div>
            <div id="scene1.3.44">
              Or have acquaintance with mine own desires,
            </div>
            <div id="scene1.3.45">
              If that I do not dream or be not frantic,--
            </div>
            <div id="scene1.3.46">
              As I do trust I am not--then, dear uncle,
            </div>
            <div id="scene1.3.47">
              Never so much as in a thought unborn
            </div>
            <div id="scene1.3.48">
              Did I offend your highness.
            </div>
          </div>
          <div id="speech24" class="character">
            DUKE FREDERICK
          </div>
          <div class="dialog">
            <div id="scene1.3.49">
              Thus do all traitors:
            </div>
            <div id="scene1.3.50">
              If their purgation did consist in words,
            </div>
            <div id="scene1.3.51">
              They are as innocent as grace itself:
            </div>
            <div id="scene1.3.52">
              Let it suffice thee that I trust thee not.
            </div>
          </div>
          <div id="speech25" class="character">
            ROSALIND
          </div>
          <div class="dialog">
            <div id="scene1.3.53">
              Yet your mistrust cannot make me a traitor:
            </div>
            <div id="scene1.3.54">
              Tell me whereon the likelihood depends.
            </div>
          </div>
          <div id="speech26" class="character">
            DUKE FREDERICK
          </div>
          <div class="dialog">
            <div id="scene1.3.55">
              Thou art thy father&#x27;s daughter; there&#x27;s enough.
            </div>
          </div>
          <div id="speech27" class="character">
            ROSALIND
          </div>
          <div class="dialog">
            <div id="scene1.3.56">
              So was I when your highness took his dukedom;
            </div>
            <div id="scene1.3.57">
              So was I when your highness banish&#x27;d him:
            </div>
            <div id="scene1.3.58">
              Treason is not inherited, my lord;
            </div>
            <div id="scene1.3.59">
              Or, if we did derive it from our friends,
            </div>
            <div id="scene1.3.60">
              What&#x27;s that to me? my father was no traitor:
            </div>
            <div id="scene1.3.61">
              Then, good my liege, mistake me not so much
            </div>
            <div id="scene1.3.62">
              To think my poverty is treacherous.
            </div>
          </div>
          <div id="speech28" class="character">
            CELIA
          </div>
          <div class="dialog">
            <div id="scene1.3.63">
              Dear sovereign, hear me speak.
            </div>
          </div>
          <div id="speech29" class="character">
            DUKE FREDERICK
          </div>
          <div class="dialog">
            <div id="scene1.3.64">
              Ay, Celia; we stay&#x27;d her for your sake,
            </div>
            <div id="scene1.3.65">
              Else had she with her father ranged along.
            </div>
          </div>
          <div id="speech30" class="character">
            CELIA
          </div>
          <div class="dialog">
            <div id="scene1.3.66">
              I did not then entreat to have her stay;
            </div>
            <div id="scene1.3.67">
              It was your pleasure and your own remorse:
            </div>
            <div id="scene1.3.68">
              I was too young that time to value her;
            </div>
            <div id="scene1.3.69">
              But now I know her: if she be a traitor,
            </div>
            <div id="scene1.3.70">
              Why so am I; we still have slept together,
            </div>
            <div id="scene1.3.71">
              Rose at an instant, learn&#x27;d, play&#x27;d, eat together,
            </div>
            <div id="scene1.3.72">
              And wheresoever we went, like Juno&#x27;s swans,
            </div>
            <div id="scene1.3.73">
              Still we went coupled and inseparable.
            </div>
          </div>
          <div id="speech31" class="character">
            DUKE FREDERICK
          </div>
          <div class="dialog">
            <div id="scene1.3.74">
              She is too subtle for thee; and her smoothness,
            </div>
            <div id="scene1.3.75">
              Her very silence and her patience
            </div>
            <div id="scene1.3.76">
              Speak to the people, and they pity her.
            </div>
            <div id="scene1.3.77">
              Thou art a fool: she robs thee of thy name;
            </div>
            <div id="scene1.3.78">
              And thou wilt show more bright and seem more virtuous
            </div>
            <div id="scene1.3.79">
              When she is gone. Then open not thy lips:
            </div>
            <div id="scene1.3.80">
              Firm and irrevocable is my doom
            </div>
            <div id="scene1.3.81">
              Which I have pass&#x27;d upon her; she is banish&#x27;d.
            </div>
          </div>
          <div id="speech32" class="character">
            CELIA
          </div>
          <div class="dialog">
            <div id="scene1.3.82">
              Pronounce that sentence then on me, my liege:
            </div>
            <div id="scene1.3.83">
              I cannot live out of her company.
            </div>
          </div>
          <div id="speech33" class="character">
            DUKE FREDERICK
          </div>
          <div class="dialog">
            <div id="scene1.3.84">
              You are a fool. You, niece, provide yourself:
            </div>
            <div id="scene1.3.85">
              If you outstay the time, upon mine honour,
            </div>
            <div id="scene1.3.86">
              And in the greatness of my word, you die.
            </div>
            <div class="direction">
              Exeunt DUKE FREDERICK and Lords
            </div>
          </div>
          <div id="speech34" class="character">
            CELIA
          </div>
          <div class="dialog">
            <div id="scene1.3.87">
              O my poor Rosalind, whither wilt thou go?
            </div>
            <div id="scene1.3.88">
              Wilt thou change fathers? I will give thee mine.
            </div>
            <div id="scene1.3.89">
              I charge thee, be not thou more grieved than I am.
            </div>
          </div>
          <div id="speech35" class="character">
            ROSALIND
          </div>
          <div class="dialog">
            <div id="scene1.3.90">
              I have more cause.
            </div>
          </div>
          <div id="speech36" class="character">
            CELIA
          </div>
          <div class="dialog">
            <div id="scene1.3.91">
              Thou hast not, cousin;
            </div>
            <div id="scene1.3.92">
              Prithee be cheerful: know&#x27;st thou not, the duke
            </div>
            <div id="scene1.3.93">
              Hath banish&#x27;d me, his daughter?
            </div>
          </div>
          <div id="speech37" class="character">
            ROSALIND
          </div>
          <div class="dialog">
            <div id="scene1.3.94">
              That he hath not.
            </div>
          </div>
          <div id="speech38" class="character">
            CELIA
          </div>
          <div class="dialog">
            <div id="scene1.3.95">
              No, hath not? Rosalind lacks then the love
            </div>
            <div id="scene1.3.96">
              Which teacheth thee that thou and I am one:
            </div>
            <div id="scene1.3.97">
              Shall we be sunder&#x27;d? shall we part, sweet girl?
            </div>
            <div id="scene1.3.98">
              No: let my father seek another heir.
            </div>
            <div id="scene1.3.99">
              Therefore devise with me how we may fly,
            </div>
            <div id="scene1.3.100">
              Whither to go and what to bear with us;
            </div>
            <div id="scene1.3.101">
              And do not seek to take your change upon you,
            </div>
            <div id="scene1.3.102">
              To bear your griefs yourself and leave me out;
            </div>
            <div id="scene1.3.103">
              For, by this heaven, now at our sorrows pale,
            </div>
            <div id="scene1.3.104">
              Say what thou canst, I&#x27;ll go along with thee.
            </div>
          </div>
          <div id="speech39" class="character">
            ROSALIND
          </div>
          <div class="dialog">
            <div id="scene1.3.105">
              Why, whither shall we go?
            </div>
          </div>
          <div id="speech40" class="character">
            CELIA
          </div>
          <div class="dialog">
            <div id="scene1.3.106">
              To seek my uncle in the forest of Arden.
            </div>
          </div>
          <div id="speech41" class="character">
            ROSALIND
          </div>
          <div class="dialog">
            <div id="scene1.3.107">
              Alas, what danger will it be to us,
            </div>
            <div id="scene1.3.108">
              Maids as we are, to travel forth so far!
            </div>
            <div id="scene1.3.109">
              Beauty provoketh thieves sooner than gold.
            </div>
          </div>
          <div id="speech42" class="character">
            CELIA
          </div>
          <div class="dialog">
            <div id="scene1.3.110">
              I&#x27;ll put myself in poor and mean attire
            </div>
            <div id="scene1.3.111">
              And with a kind of umber smirch my face;
            </div>
            <div id="scene1.3.112">
              The like do you: so shall we pass along
            </div>
            <div id="scene1.3.113">
              And never stir assailants.
            </div>
          </div>
          <div id="speech43" class="character">
            ROSALIND
          </div>
          <div class="dialog">
            <div id="scene1.3.114">
              Were it not better,
            </div>
            <div id="scene1.3.115">
              Because that I am more than common tall,
            </div>
            <div id="scene1.3.116">
              That I did suit me all points like a man?
            </div>
            <div id="scene1.3.117">
              A gallant curtle-axe upon my thigh,
            </div>
            <div id="scene1.3.118">
              A boar-spear in my hand; and--in my heart
            </div>
            <div id="scene1.3.119">
              Lie there what hidden woman&#x27;s fear there will--
            </div>
            <div id="scene1.3.120">
              We&#x27;ll have a swashing and a martial outside,
            </div>
            <div id="scene1.3.121">
              As many other mannish cowards have
            </div>
            <div id="scene1.3.122">
              That do outface it with their semblances.
            </div>
          </div>
          <div id="speech44" class="character">
            CELIA
          </div>
          <div class="dialog">
            <div id="scene1.3.123">
              What shall I call thee when thou art a man?
            </div>
          </div>
          <div id="speech45" class="character">
            ROSALIND
          </div>
          <div class="dialog">
            <div id="scene1.3.124">
              I&#x27;ll have no worse a name than Jove&#x27;s own page;
            </div>
            <div id="scene1.3.125">
              And therefore look you call me Ganymede.
            </div>
            <div id="scene1.3.126">
              But what will you be call&#x27;d?
            </div>
          </div>
          <div id="speech46" class="character">
            CELIA
          </div>
          <div class="dialog">
            <div id="scene1.3.127">
              Something that hath a reference to my state
            </div>
            <div id="scene1.3.128">
              No longer Celia, but Aliena.
            </div>
          </div>
          <div id="speech47" class="character">
            ROSALIND
          </div>
          <div class="dialog">
            <div id="scene1.3.129">
              But, cousin, what if we assay&#x27;d to steal
            </div>
            <div id="scene1.3.130">
              The clownish fool out of your father&#x27;s court?
            </div>
            <div id="scene1.3.131">
              Would he not be a comfort to our travel?
            </div>
          </div>
          <div id="speech48" class="character">
            CELIA
          </div>
          <div class="dialog">
            <div id="scene1.3.132">
              He&#x27;ll go along o&#x27;er the wide world with me;
            </div>
            <div id="scene1.3.133">
              Leave me alone to woo him. Let&#x27;s away,
            </div>
            <div id="scene1.3.134">
              And get our jewels and our wealth together,
            </div>
            <div id="scene1.3.135">
              Devise the fittest time and safest way
            </div>
            <div id="scene1.3.136">
              To hide us from pursuit that will be made
            </div>
            <div id="scene1.3.137">
              After my flight. Now go we in content
            </div>
            <div id="scene1.3.138">
              To liberty and not to banishment.
            </div>
            <div class="direction">
              Exeunt
            </div>
          </div>
        </div>
      </div>
    </div>
  </body>
</html>
'''

if __name__ == '__main__':
    tester.cli().run()
