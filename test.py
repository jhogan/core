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


class test_blogpost(tester):
    
    Smallposttitle = 'Walden'
    Smallpostbody = """When I wrote the following pages, or rather the bulk of them,
I lived alone, in the woods, a mile from any neighbor, in a house which I
had built myself, on the shore of Walden Pond, in Concord, Massachusetts,
and earned my living by the labor of my hands only. I lived there two years
and two months. At present I am a sojourner in civilized life again."""

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

    def it_saves_one_revision(self):
        return 
        post = blogpost()
        post.body = test_blogpost.Smallpostbody
        post.save()

    def it_saves_two_revision(self):
        post = blogpost()
        post.body = test_blogpost.Smallpostbody
        post.save()

        post.body += 'some added data'
        post.save()

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
        self.assertNone(rev.previous)
        self.assertNone(rev.subsequent)

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
