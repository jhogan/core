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
from articles import *
from configfile import configfile
from entities import brokenruleserror
from MySQLdb.constants.ER import BAD_TABLE_ERROR, DUP_ENTRY
from pdb import set_trace; B=set_trace
from tester import *
from uuid import uuid4
import MySQLdb
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
        title = test_blogpost.Smallposttitle + ' - ' + str(uuid4())
        post.title  = title
        slug = re.sub(r'\W+', '-', post.title).strip('-').lower()
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
                revisedtitle = title + ' Rev: ' + str(i)
                post.title = revisedtitle
                post.excerpt = test_blogpost.Smallpostexcerpt  + ' Rev: ' + str(i)
                
            post.save()

            post = blogpost(post.id)

            if i < x / 2:
                self.assertEq(test_blogpost.Smallpostbody, post.body)
                self.assertEq(title, post.title)
                self.assertEq(test_blogpost.Smallpostexcerpt, post.excerpt)
            else:
                self.assertEq(test_blogpost.Smallpostbody + ' Rev: ' + str(i), post.body)
                self.assertEq(revisedtitle, post.title)
                self.assertEq(test_blogpost.Smallpostexcerpt + ' Rev: ' + str(i), post.excerpt)
            self.assertEq(blogpost.Pending, post.status)
            self.assertTrue(post.iscommentable)
            self.assertEq(slug, post.slug)

    def it_calls_body(self): 
        post = blogpost()
        self.assertNone(post.body)
        post.save()
        self.assertEmptyString(post.body)

        post.body = test_blogpost.Smallpostbody
        self.assertEq(test_blogpost.Smallpostbody, post.body)

        post.save()
        self.assertEq(test_blogpost.Smallpostbody, post.body)

        post = blogpost(post.id)
        self.assertEq(test_blogpost.Smallpostbody, post.body)

    def it_calls_created_at(self):
        post = blogpost()
        self.assertNone(post.created_at)
        before = datetime.now().replace(microsecond=0)

        post.save()

        after = datetime.now().replace(microsecond=0)

        self.assertLe(before, post.created_at)
        self.assertGe(after, post.created_at)

        created_at = post.created_at

        post = blogpost(post.id)
        self.assertEq(created_at, post.created_at)

    def it_calls_title(self):
        post = blogpost()
        self.assertNone(post.title)

        post.save()

        self.assertEmptyString(post.title)

        post.title = test_blogpost.Smallposttitle
        self.assertEq(test_blogpost.Smallposttitle, post.title)

        post.save()
        self.assertEq(test_blogpost.Smallposttitle, post.title)

        post = blogpost(post.id)
        self.assertEq(test_blogpost.Smallposttitle, post.title)

    def it_calls_slug(self):
        post = blogpost()
        self.assertNone(post.slug)

        post.save()

        self.assertEmptyString(post.slug)

        slug = str(uuid4())
        post.slug = slug
        self.assertEq(slug, post.slug)

        post.save()
        self.assertEq(slug, post.slug)

        post = blogpost(post.id)
        self.assertEq(slug, post.slug)

    def it_calls_title_and_slug(self):
        post = blogpost()
        title = 'Herp derp'
        slug = re.sub(r'\W+', '-', title).strip('-').lower()
        post.title = title

        self.assertEq(slug, post.slug)

        post.save()
        self.assertEq(slug, post.slug)

        post = blogpost(post.id)
        self.assertEq(slug, post.slug)

        # A duplicate title will lead to a duplicate slug (slug_cache)
        # Therefore, a broken rule will indicate this and a save 
        # won't be permited because of the unique constraint on the
        # slug_cache field
        post = blogpost()
        post.title = title
        self.assertTrue(post.brokenrules.contains('slug_cache', 'unique'))

        try:
            post.save()
        except brokenruleserror as ex:
            brs = ex.args[1].brokenrules
            self.assertTrue(brs.contains('slug_cache', 'unique'))
        except Exception:
            self.assertFalse('brokenruleserror was not raised')
        else:
            self.assertFalse('No exception was not raised')

    def it_calls_excerpt(self):
        post = blogpost()
        self.assertNone(post.excerpt)
        post.save()
        self.assertEmptyString(post.excerpt)

        post = blogpost(post.id)
        self.assertEmptyString(post.excerpt)

        post = blogpost()
        self.assertNone(post.excerpt)
        post.save()
        self.assertEmptyString(post.excerpt)
        post = blogpost(post.id)
        self.assertEmptyString(post.excerpt)

        post = blogpost()
        post.excerpt = test_blogpost.Smallpostexcerpt
        self.assertEq(test_blogpost.Smallpostexcerpt, post.excerpt)
        post.save()
        self.assertEq(test_blogpost.Smallpostexcerpt, post.excerpt)
        post = blogpost(post.id)
        self.assertEq(test_blogpost.Smallpostexcerpt, post.excerpt)

    def it_calls_status(self): 
        post = blogpost()
        self.assertNone(post.status)
        post.save()
        self.assertEq(article.Draft, post.status)
        post = blogpost(post.id)
        self.assertEq(article.Draft, post.status)

        post = blogpost()
        post.status = article.Pending
        self.assertEq(article.Pending, post.status)
        post.save()
        self.assertEq(article.Pending, post.status)
        post = blogpost(post.id)
        self.assertEq(article.Pending, post.status)

    def it_calls_iscommentable(self): 
        post = blogpost()
        self.assertNone(post.iscommentable)
        post.save()
        self.assertFalse(post.iscommentable)
        post = blogpost(post.id)
        self.assertFalse(post.iscommentable)

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

    def it_searches_by_id(self):
        post = blogpost()
        post.save()
        id = post.id

        post = blogpost(id)
        self.assertEq(id,   post.id)

    def it_searches_by_slug(self):
        post = blogpost()
        slug = str(uuid4())
        post.slug = slug
        post.save()
        id = post.id

        post = blogpost(slug)
        self.assertEq(slug, post.slug)
        self.assertEq(id,   post.id)

    def it_calls_wont_save_if_there_are_brokenrules(self): 
        # TODO
        return
        post = blogpost()
        try:
            post.save()
        except brokenruleserror as ex:
            self.assertIs(post, ex.object)
        except:
            msg = ('BrokenRulesError expected however a different exception '
                  ' was thrown: ' + str(type(ex)))
            self.assertFail(msg)
        else:
            self.assertFail('No exception thrown on save of invalid object.')

    def it_calls_slug_and_title(self):
        title = test_blogpost.Smallposttitle + str(uuid4())
        slug = re.sub(r'\W+', '-', title).strip('-').lower()

        post = blogpost()
        post.title = title
        self.assertEq(slug, post.slug)
        self.assertEq(title, post.title)
        post.save()
        self.assertEq(slug, post.slug)
        self.assertEq(title, post.title)
        post = blogpost(post.id)
        self.assertEq(slug, post.slug)
        self.assertEq(title, post.title)
        post = blogpost(post.id)
        self.assertEq(slug, post.slug)
        self.assertEq(title, post.title)

        title = test_blogpost.Smallposttitle + str(uuid4())
        slug = re.sub(r'\W+', '-', title).strip('-').lower()
        post = blogpost()
        self.assertNone(post.slug)
        self.assertEq(None, post.title) 
        post.title = title
        self.assertEq(slug, post.slug)
        self.assertEq(title, post.title)

        post.save()
        self.assertEq(title, post.title)
        self.assertEq(slug, post.slug)
        post = blogpost(post.id)
        self.assertEq(title, post.title)
        self.assertEq(slug, post.slug)

        post = blogpost()
        self.assertEq(None, post.title)
        post.save()
        self.assertEq('', post.title)
        self.assertEmptyString(post.slug)
        post = blogpost(post.id)
        self.assertEmptyString(post.slug)
        self.assertEq('', post.title)

        post = blogpost()
        post.slug = 'Herp Derp'
        self.assertEq('Herp Derp', post.slug)
        self.assertEq(None, post.title)
        post.title = title
        self.assertEq('Herp Derp', post.slug)
        post.save()
        self.assertEq(title, post.title)
        self.assertEq('Herp Derp', post.slug)
        post = blogpost(post.id)
        self.assertEq(title, post.title)
        self.assertEq('Herp Derp', post.slug)

    def it_saves_x_revisions_with_empty_properties(self):
        post = blogpost()
        post.body = test_blogpost.Smallpostbody
        title = test_blogpost.Smallposttitle + ' - ' + str(uuid4())
        post.title = title
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
        title = test_blogpost.Smallposttitle + ' - ' + str(uuid4())
        post.title = title
        post.excerpt = test_blogpost.Smallpostexcerpt 
        post.status = blogpost.Pending
        post.iscommentable = True

        post.save()

        created_at = post.created_at
        
        self.assertNotNone(post.id)
        self.assertEq(test_blogpost.Smallpostbody, post.body)
        self.assertEq(title, post.title)
        self.assertEq(test_blogpost.Smallpostexcerpt, post.excerpt)
        self.assertEq(article.Pending, post.status)
        self.assertEq(True, post.iscommentable)
        slug = re.sub(r'\W+', '-', post.title).strip('-').lower()
        self.assertEq(slug, post.slug)

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
                self.assertEq(slug, post.slug)

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

class test_articlesrevisions(tester):
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

    def it_fails_saving_duplicate_slug_cache(self):
        revs = articlerevisions()

        slug_cache = uuid4()
        for i in range(3):
            rev = articlerevision()
            rev.body = test_blogpost.Smallpostbody
            rev.title = test_blogpost.Smallposttitle
            rev.slug_cache = slug_cache
            revs += rev

        try:
            # Test persistent state before and after fail. The epiphany-py
            # library should have a test for this but, at the moment, it does
            # not, so we test here since it's important.
            for rev in revs:
                self.assertTrue(rev._isnew)
                self.assertFalse(rev._isdirty)
            revs.save()
        except MySQLdb.IntegrityError as ex:
            # We should get an MySQL DUP_ENTRY exception
            self.assertTrue(ex.args[0] == DUP_ENTRY)
        except Exception:
            self.assertFail('Wrong exception')
        else:
            self.assertFail("Didn't raise IntegrityError")
        finally:
            for rev in revs:
                self.assertTrue(rev._isnew)
                self.assertFalse(rev._isdirty)
        
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
        self.assertEq(article.Draft, rev.status)
        self.assertFalse(rev.iscommentable)
        self.assertNone(rev.slug)

    def it_fails_on_save_when_invalid(self):
        rev = articlerevision()
        try:
            rev.save()
        except brokenruleserror as ex:
            self.assertIs(rev, ex.object)
        except:
            msg = ('brokenruleserror expected however a different exception '
                  ' was thrown: ' + str(type(ex)))
            self.assertFail(msg)
        else:
            self.assertFail('No exception thrown on save of invalid object.')

    def it_fails_to_load_given_nonexistent_id(self):
        # TODO
        return

    def it_loads_as_valid(self):
        rev = articlerevision()
        rev.body = test_blogpost.Smallpostbody
        rev.title = test_blogpost.Smallposttitle
        rev.save()

        rev = articlerevision(rev.id)
        self.assertValid(rev)

    def it_breaks_diff_rules(self):
        # Diff must be empty for root revisions
        rev = articlerevision()
        rev.body = test_blogpost.Smallpostbody
        rev.title = test_blogpost.Smallposttitle
        rev.diff = diff.diff('herp', 'derp')
        self.assertCount(1, rev.brokenrules)
        self.assertTrue(rev.brokenrules.contains('diff', 'empty'))

        # Fix
        rev.diff = None
        self.assertValid(rev)

        # Break the rule that says a diff must be of type diff.diff
        rent = articlerevision()
        rent.body = test_blogpost.Smallpostbody
        rent.title = test_blogpost.Smallposttitle
        rent.diff = diff.diff('herp', 'derp')

        rev._parent = rent
        rev.body = None
        rev.diff = 'wrong type'
        self.assertCount(1, rev.brokenrules)
        self.assertTrue(rev.brokenrules.contains('diff', 'valid'))

    def it_breaks_title_rules(self):
        # Root revisions must have non null titles
        rev = articlerevision()
        rev.body = test_blogpost.Smallpostbody
        self.assertCount(1, rev.brokenrules)
        self.assertTrue(rev.brokenrules.contains('title', 'full'))

        # Non-root revisions can have null titles
        rev._parent = articlerevision()
        self.assertCount(0, rev.brokenrules)

        # Root revisions can have empty strings as titles
        rev = articlerevision()
        rev.body = test_blogpost.Smallpostbody
        rev.title = ''
        self.assertCount(0, rev.brokenrules)

        # Revisions titles must be strings
        rev.title = 123
        self.assertCount(1, rev.brokenrules)
        self.assertTrue(rev.brokenrules.contains('title', 'valid'))
        rev._parent = articlerevision() # Make non-root
        self.assertCount(1, rev.brokenrules)
        self.assertTrue(rev.brokenrules.contains('title', 'valid'))

        # Title must be less than 500 characters
        rev = articlerevision()
        rev.body = test_blogpost.Smallpostbody
        rev.title = 'X' * 500
        self.assertCount(0, rev.brokenrules)
        rev.title = 'X' * 501
        self.assertCount(1, rev.brokenrules)
        self.assertTrue(rev.brokenrules.contains('title', 'fits'))

    def it_breaks_status_rules(self):
        rev = articlerevision()
        rev.body = test_blogpost.Smallpostbody
        rev.title = test_blogpost.Smallposttitle
        for st in article.Statuses:
            rev.status = st
            self.assertCount(0, rev.brokenrules)

        for st in ('wrong-type', 9999, object()):
            rev.status = st
            self.assertCount(1, rev.brokenrules)
            self.assertTrue(rev.brokenrules.contains('status', 'valid'))

    def it_breaks_slug_cache_uniqueness_rule(self):
        rev = articlerevision()
        rev.body = test_blogpost.Smallpostbody
        rev.title = test_blogpost.Smallposttitle
        slug_cache = uuid4()
        rev.slug_cache = slug_cache
        rev.save()

        rev = articlerevision()
        rev.body = test_blogpost.Smallpostbody
        rev.title = test_blogpost.Smallposttitle
        rev.slug_cache = slug_cache
        self.assertTrue(rev.brokenrules.contains('slug_cache', 'unique'))

    def it_fails_saving_duplicate_slug_cache(self):
        rev = articlerevision()
        rev.body = test_blogpost.Smallpostbody
        rev.title = test_blogpost.Smallposttitle
        slug_cache = uuid4()
        rev.slug_cache = slug_cache

        rev.save()

        rev = articlerevision()
        rev.body = test_blogpost.Smallpostbody
        rev.title = test_blogpost.Smallposttitle
        rev.slug_cache = slug_cache
        
        try:
            cur = rev.connection._conn.cursor()
            # Bypass the validation check in save() to insert a record with a
            # duplicate slug_cache.
            rev._insert(cur)
        except MySQLdb.IntegrityError as ex:
            # We should get an MySQL DUP_ENTRY exception
            self.assertTrue(ex.args[0] == DUP_ENTRY)
        except Exception:
            self.assertFail('Wrong exception')
        else:
            self.assertFail("Didn't raise IntegrityError")

    def it_breaks_body_rules(self):
        # Body must be full for root revisions
        rev = articlerevision()
        self.assertCount(2, rev.brokenrules)
        self.assertTrue(rev.brokenrules.contains('body', 'full'))
        self.assertTrue(rev.brokenrules.contains('title', 'full'))

        # Create a parent then test the child
        rent = articlerevision()
        rent.body = test_blogpost.Smallpostbody
        rent.title = test_blogpost.Smallposttitle
        rent.diff = diff.diff('herp', 'derp')

        # A body and a diff shouldn't exist in the same record
        rev._parent = rent
        rev.diff = diff.diff('herp', 'derp')
        rev.body = test_blogpost.Smallpostbody
        self.assertCount(2, rev.brokenrules)
        self.assertTrue(rev.brokenrules.contains('diff', 'valid'))

        # A non-root revision should can have a body but no diff. This
        # may be useful for caching or other isssues such as a failure to
        # create a diff.
        rev.body = test_blogpost.Smallpostbody
        rev.diff = None
        self.assertValid(rev)

        
    def it_creates_revisions(self):
        # TODO
        return
        rev = articlerevision()
        before = datetime.now()
        rev.save()

        self.assertTrue(type(rev.id) == uuid.UUID)
        self.assertTrue(type(rev.created_at) == datetime)

    def it_retrieves(self):
        # TODO
        return
        rev1 = articlerevision()
        rev1.save()

        rev2 = articlerevision(rev1.id)
        self.assertEq(rev1.id, rev2.id)

t = testers()
t.oninvoketest += lambda src, eargs: print('# ', end='', flush=True)
t.oninvoketest += lambda src, eargs: print(eargs.method[0], flush=True)
t.run()
print(t)
