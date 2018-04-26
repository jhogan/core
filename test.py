# vim: set et ts=4 sw=4 fdm=marker
"""
MIT License

Copyright (c) 2016 Jesse Hogan

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
from tester import *
from configfile import configfile
from articles import *
from pdb import set_trace; B=set_trace
import MySQLdb
from MySQLdb.constants.ER import BAD_TABLE_ERROR
import re


class test_blogpost(tester):
    
    Smallposttitle = 'Walden; or, Life in the Woods'

    Smallpostbody = """When I wrote the following pages, or rather the bulk of them,
I lived alone, in the woods, a mile from any neighbor, in a house which I
had built myself, on the shore of Walden Pond, in Concord, Massachusetts,
and earned my living by the labor of my hands only. I lived there two years
and two months. At present I am a sojourner in civilized life again."""

    Smallpostexcerpt = """Walden is a book by noted transcendentalist Henry
David Thoreau. The text is a reflection upon simple living in natural
surroundings. The work is part personal declaration of independence, social
experiment, voyage of spiritual discovery, satire, and-to some degree-a
manual for self-reliance."""

    def __init__(self):
        super().__init__()
        revs = articlerevisions()
        try:
            revs.DROP()
        except MySQLdb.OperationalError as ex:
            try:
                errno = ex.args[0]
            except:
                raise

            if errno != BAD_TABLE_ERROR: # 1051
                raise

        revs.CREATE()

    def it_saves_x_revisions_with_null_properties(self):
        post = blogpost()
        post.body = test_blogpost.Smallpostbody
        post.title = test_blogpost.Smallposttitle 
        post.excerpt = test_blogpost.Smallpostexcerpt 
        post.status = blogpost.Pending
        post.iscommentable = True

        post.save()

        x = 4
        for i in range(x):
            if i < x / 2:
                post.title = None
                post.excerpt = None
                post.slug = None
            else:
                post.body = test_blogpost.Smallpostbody  + ' Rev: ' + str(i)
                post.title = test_blogpost.Smallposttitle  + ' Rev: ' + str(i)
                post.excerpt = test_blogpost.Smallpostexcerpt  + ' Rev: ' + str(i)
                
            post.save()

            post = blogpost(post.id)

            if i < x / 2:
                self.assertEq(test_blogpost.Smallpostbody, post.body)
                self.assertEq(test_blogpost.Smallposttitle, post.title)
                self.assertEq(test_blogpost.Smallpostexcerpt, post.excerpt)
            else:
                self.assertEq(test_blogpost.Smallpostbody + ' Rev: ' + str(i), post.body)
                self.assertEq(test_blogpost.Smallposttitle + ' Rev: ' + str(i), post.title)
                self.assertEq(test_blogpost.Smallpostexcerpt + ' Rev: ' + str(i), post.excerpt)
            self.assertEq(blogpost.Pending, post.status)
            self.assertTrue(post.iscommentable)
            self.assertEq('walden-or-life-in-the-woods', post.slug)

    def it_calls_iscommentable(self): 
        post = blogpost()
        post.save()
        self.assertNone(post.iscommentable)
        post = blogpost(post.id)
        self.assertNone(post.iscommentable)

        post = blogpost()
        self.assertNone(post.iscommentable)
        post.save()
        self.assertNone(post.iscommentable)
        post = blogpost(post.id)
        self.assertNone(post.iscommentable)

        post = blogpost()
        post.iscommentable = True
        self.assertTrue(post.iscommentable)
        post.save()
        self.assertTrue(post.iscommentable)
        post = blogpost(post.id)
        self.assertTrue(post.iscommentable)

        post = blogpost()
        post.iscommentable = False
        self.assertFalse(post.iscommentable)
        post.save()
        self.assertFalse(post.iscommentable)
        post = blogpost(post.id)
        self.assertFalse(post.iscommentable)

    def it_calls_status(self): 
        post = blogpost()
        post.save()
        self.assertNone(post.status)
        post = blogpost(post.id)
        self.assertNone(post.status)

        post = blogpost()
        self.assertNone(post.status)
        post.save()
        self.assertNone(post.status)
        post = blogpost(post.id)
        self.assertNone(post.status)

        post = blogpost()
        post.status = article.Pending
        self.assertEq(article.Pending, post.status)
        post.save()
        self.assertEq(article.Pending, post.status)
        post = blogpost(post.id)
        self.assertEq(article.Pending, post.status)

    def it_calls_excerpt(self):
        post = blogpost()
        post.save()
        self.assertNone(post.excerpt)
        post = blogpost(post.id)
        self.assertNone(post.excerpt)

        post = blogpost()
        self.assertNone(post.excerpt)
        post.save()
        self.assertNone(post.excerpt)
        post = blogpost(post.id)
        self.assertNone(post.excerpt)

        post = blogpost()
        post.excerpt = test_blogpost.Smallpostexcerpt
        self.assertEq(test_blogpost.Smallpostexcerpt, post.excerpt)
        post.save()
        self.assertEq(test_blogpost.Smallpostexcerpt, post.excerpt)
        post = blogpost(post.id)
        self.assertEq(test_blogpost.Smallpostexcerpt, post.excerpt)

    def it_calls_slug_and_title(self):
        slug = re.sub(r'\W+', '-', test_blogpost.Smallposttitle).strip('-').lower()

        post = blogpost()
        post.title = test_blogpost.Smallposttitle 
        self.assertEq(slug, post.slug)
        self.assertEq(test_blogpost.Smallposttitle, post.title)
        post.save()
        self.assertEq(slug, post.slug)
        self.assertEq(test_blogpost.Smallposttitle, post.title)
        post = blogpost(post.id)
        self.assertEq(slug, post.slug)
        self.assertEq(test_blogpost.Smallposttitle, post.title)
        post = blogpost(post.id)
        self.assertEq(slug, post.slug)
        self.assertEq(test_blogpost.Smallposttitle, post.title)

        post = blogpost()
        self.assertEmptyString(post.slug)
        self.assertEq(None, post.title) 
        post.title = test_blogpost.Smallposttitle 
        self.assertEq(slug, post.slug)
        self.assertEq(test_blogpost.Smallposttitle, post.title)
        post.save()
        self.assertEq(test_blogpost.Smallposttitle, post.title)
        self.assertEq(slug, post.slug)
        post = blogpost(post.id)
        self.assertEq(test_blogpost.Smallposttitle, post.title)
        self.assertEq(slug, post.slug)

        post = blogpost()
        self.assertEq(None, post.title)
        post.save()
        self.assertEq(None, post.title)
        self.assertEmptyString(post.slug)
        post = blogpost(post.id)
        self.assertEmptyString(post.slug)
        self.assertEq(None, post.title)

        post = blogpost()
        post.slug = 'Herp Derp'
        self.assertEq('Herp Derp', post.slug)
        self.assertEq(None, post.title)
        post.title = test_blogpost.Smallposttitle
        self.assertEq('Herp Derp', post.slug)
        post.save()
        self.assertEq(test_blogpost.Smallposttitle, post.title)
        self.assertEq('Herp Derp', post.slug)
        post = blogpost(post.id)
        self.assertEq(test_blogpost.Smallposttitle, post.title)
        self.assertEq('Herp Derp', post.slug)

    def it_saves_x_revisions_with_empty_properties(self):
        post = blogpost()
        post.body = test_blogpost.Smallpostbody
        post.title = test_blogpost.Smallposttitle 
        post.excerpt = test_blogpost.Smallpostexcerpt 
        post.status = blogpost.Pending
        post.iscommentable = True

        post.save()

        for i in range(2):
            post.title = ''
            post.excerpt = ''
            post.slug = ''
            post.save()

            post = blogpost(post.id)
            self.assertEmptyString(post.title)
            self.assertEmptyString(post.excerpt)
            self.assertEq(blogpost.Pending, post.status)
            self.assertTrue(post.iscommentable)
            self.assertEmptyString(post.slug)

    def it_saves_x_revisions(self):
        post = blogpost()
        post.body = test_blogpost.Smallpostbody
        post.title = test_blogpost.Smallposttitle 
        post.excerpt = test_blogpost.Smallpostexcerpt 
        post.status = blogpost.Pending
        post.iscommentable = True

        post.save()

        created_at = post.created_at
        
        self.assertNotNone(post.id)
        self.assertEq(test_blogpost.Smallpostbody, post.body)
        self.assertEq(test_blogpost.Smallposttitle, post.title)
        self.assertEq(test_blogpost.Smallpostexcerpt, post.excerpt)
        self.assertEq(article.Pending, post.status)
        self.assertEq(True, post.iscommentable)
        self.assertEq('walden-or-life-in-the-woods', post.slug)

        x = 20

        for i in range(x):
            id = post.id

            # Mutate the body to ensure revision patching works
            if i < 5:
                newbody = post.body + 'X'
            elif i >= 5 and i <= 10:
                newbody = ''
                for j, c in enumerate(post.body):
                    if j == i:
                        c = 'x'
                    newbody += c
            elif i > 10:
                post.slug = 'walden-or-life-in-the-woods-hard-set'
                newbody = 'X' + post.body
                
            post.body = newbody

            post.title = newtitle = test_blogpost.Smallposttitle + ' Rev ' + str(i)
            post.excerpt = newexcerpt = test_blogpost.Smallpostexcerpt + ' Rev ' + str(i)
            post.status = article.Publish
            post.iscommentable = i % 2 == 0
            
            post.save()

            self.assertNotNone(post.id)
            self.assertEq(id, post.id)
            self.assertEq(newbody, post.body)
            self.assertEq(created_at, post.created_at)
            self.assertEq(newtitle, post.title)
            self.assertEq(newexcerpt, post.excerpt)
            self.assertEq(article.Publish, post.status)
            self.assertEq(i % 2 == 0, post.iscommentable)
            if i > 10:
                self.assertEq('walden-or-life-in-the-woods-hard-set', post.slug)
            else:
                self.assertEq('walden-or-life-in-the-woods', post.slug)

    def _createblogpost(self):
        post = blogpost()
        post.body = test_blogpost.Smallpostbody
        post.title = test_blogpost.Smallposttitle 
        post.excerpt = test_blogpost.Smallpostexcerpt 
        post.status = blogpost.Pending
        post.iscommentable = True

        post.save()

        x = 20

        for i in range(x):
            id = post.id

            # Mutate the body to ensure revision patching works
            if i < 5:
                newbody = post.body + 'X'
            elif i >= 5 and i <= 10:
                newbody = ''
                for j, c in enumerate(post.body):
                    if j == i:
                        c = 'x'
                    newbody += c
            elif i > 10:
                newbody = 'X' + post.body
                
            post.body = newbody

            post.title = newtitle = test_blogpost.Smallposttitle + ' Rev ' + str(i)
            post.excerpt = newexcerpt = test_blogpost.Smallpostexcerpt + ' Rev ' + str(i)
            post.status = article.Publish
            post.iscommentable = i % 2 == 0
            
            post.save()
        return post

    def it_retrives_blogpost(self):
        bp1 = self._createblogpost()
        bp2 = blogpost(bp1.id)

        self.assertTrue(type(bp2.id) == uuid.UUID)
        self.assertEq(bp1.id,                bp2.id)

        self.assertEq(type(bp2.created_at),  datetime)
        self.assertEq(bp1.created_at,        bp2.created_at)

        self.assertEq(bp1.body,              bp2.body)
        self.assertEq(bp1.title,             bp2.title)
        self.assertEq(bp1.excerpt,           bp2.excerpt)
        self.assertEq(bp1.status,            bp2.status)
        self.assertEq(bp1.iscommentable,     bp2.iscommentable)

class test_articlesrevision(tester):
    def __init__(self):
        super().__init__()
        revs = articlerevisions()
        try:
            revs.DROP()
        except MySQLdb.OperationalError as ex:
            try:
                errno = ex.args[0]
            except:
                raise

            if errno != BAD_TABLE_ERROR: # 1051
                raise

        revs.CREATE()

    def it_instantiates(self):
        rev = articlerevision()
        self.assertNone(rev.id)
        self.assertNone(rev.authors)
        self.assertNone(rev.created_at)
        self.assertNone(rev.title)
        self.assertNone(rev.body)
        self.assertNone(rev.excerpt)
        self.assertNone(rev.status)
        self.assertNone(rev.iscommentable)
        self.assertNone(rev.slug)

    def it_creates_revisions(self):
        rev = articlerevision()
        before = datetime.now()
        rev.save()

        self.assertTrue(type(rev.id) == uuid.UUID)
        self.assertTrue(type(rev.created_at) == datetime)

    def it_retrieves(self):
        rev1 = articlerevision()
        rev1.save()

        rev2 = articlerevision(rev1.id)
        self.assertEq(rev1.id, rev2.id)

t = testers()
t.oninvoketest += lambda src, eargs: print('# ', end='', flush=True)
t.oninvoketest += lambda src, eargs: print(eargs.method[0], flush=True)
t.run()
print(t)
