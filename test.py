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

class test_blog(tester):
    def __init__(self):
        super().__init__()
        blogs().RECREATE()

    def it_creates(self):
        bl = blog()
        bl.slug = 'carapacian-tech'
        bl.description = "The technical blog for Carapacian, LLC"
        self.assertTrue(bl._isnew)
        self.assertFalse(bl._isdirty)
        self.assertNone(bl.id)
        bl.save()
        self.assertTrue(type(bl.id) == uuid.UUID)
        self.assertFalse(bl._isnew)
        self.assertFalse(bl._isdirty)

        bl1 = blog(bl.id)

        self.assertFalse(bl1._isnew)
        self.assertFalse(bl1._isdirty)
        self.assertEq(bl.id, bl1.id)
        self.assertEq(bl.slug, bl1.slug)
        self.assertEq(bl.description, bl1.description)

    def it_sets_properties(self):
        slug = 'carapacian-tech'
        description = "The technical blog for Carapacian, LLC"
        bl = blog()
        bl.slug = slug
        bl.description = description
        self.assertEq(slug, bl.slug)
        self.assertEq(description, bl.description)

    def it_breaks_rules(self):
        slug = 'carapacian-tech'
        description = "The technical blog for Carapacian, LLC"
        bl = blog()
        self.assertCount(2, bl.brokenrules)
        self.assertTrue(bl.brokenrules.contains('slug', 'full'))
        self.assertTrue(bl.brokenrules.contains('description', 'full'))
        bl.slug = slug
        self.assertCount(1, bl.brokenrules)
        self.assertTrue(bl.brokenrules.contains('description', 'full'))
        bl.description = description
        self.assertCount(0, bl.brokenrules)

    def it_updates(self):
        slug = str(uuid4())
        description = "The technical blog for Carapacian, LLC"
        bl = blog()
        bl.slug = slug
        bl.description = description
        bl.save()

        bl = blog(bl.id)
        bl.description = 'new'
        bl.save()

        bl = blog(bl.id)
        self.assertEq('new', bl.description)
        self.assertEq(slug, bl.slug)

        slug = str(uuid4())
        bl.slug = slug
        bl.save()

        bl = blog(bl.id)
        self.assertEq('new', bl.description)
        self.assertEq(slug, bl.slug)

    def it_loads_as_valid(self):
        bl = blog()
        bl.slug = str(uuid4())
        bl.description = "The technical blog for Carapacian, LLC"
        bl.save()
        self.assertValid(blog(bl.id))

    def it_violates_unique_constraint_on_slug(self):
        bl = blog()
        bl.slug = 'non-unique'
        bl.description = "The technical blog for Carapacian, LLC"
        bl.save()

        bl = blog()
        bl.slug = 'non-unique'
        bl.description = "The technical blog for Carapacian, LLC"
        try:
            bl.save()
        except MySQLdb.IntegrityError as ex:
            self.assertTrue(ex.args[0] == DUP_ENTRY)
        except Exception:
            self.assertFail('Wrong exception')
        else:
            self.assertFail("Didn't raise IntegrityError")

class test_blogpostrevision(tester):
    def __init__(self):
        super().__init__()
        articlerevisions().RECREATE()
        blogpostrevisions().RECREATE()
        blogs().RECREATE()

    def it_creates(self):
        
        # Create a blog
        bl = blog()
        bl.slug = 'carapacian-tech-blog'
        bl.description = 'Carapacian Tech Blog'
        bl.save()

        title = test_article.Smallposttitle + ' - ' + str(uuid4())
        body = test_article.Smallpostbody

        rev = blogpostrevision()
        B()
        rev.title = title
        rev.body = body
        rev.blog = bl
        rev.save()

        B()
        rev1 = blogpostrevision(rev.id)

class test_article(tester):
    
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
        articlerevisions().RECREATE()

    def it_loads_as_valid(self):
        art = article()
        art.body = test_article.Smallpostbody
        title = test_article.Smallposttitle + ' - ' + str(uuid4())
        art.title  = title
        slug = re.sub(r'\W+', '-', art.title).strip('-').lower()
        art.excerpt = test_article.Smallpostexcerpt 
        art.status = article.Pending
        art.iscommentable = True
        art.save()
        art = article(art.id)
        self.assertValid(art)

    def it_saves_x_revisions_with_null_properties(self):
        art = article()
        art.body = test_article.Smallpostbody
        title = test_article.Smallposttitle + ' - ' + str(uuid4())
        art.title  = title
        slug = re.sub(r'\W+', '-', art.title).strip('-').lower()
        art.excerpt = test_article.Smallpostexcerpt 
        art.status = article.Pending
        art.iscommentable = True

        art.save()

        x = 4
        for i in range(x):
            if i < x / 2:
                art.title = None
                art.excerpt = None
                art.slug = None
            else:
                art.body = test_article.Smallpostbody  + ' Rev: ' + str(i)
                revisedtitle = title + ' Rev: ' + str(i)
                art.title = revisedtitle
                art.excerpt = test_article.Smallpostexcerpt  + ' Rev: ' + str(i)
                
            art.save()

            art = article(art.id)

            if i < x / 2:
                self.assertEq(test_article.Smallpostbody, art.body)
                self.assertEq(title, art.title)
                self.assertEq(test_article.Smallpostexcerpt, art.excerpt)
            else:
                self.assertEq(test_article.Smallpostbody + ' Rev: ' + str(i), art.body)
                self.assertEq(revisedtitle, art.title)
                self.assertEq(test_article.Smallpostexcerpt + ' Rev: ' + str(i), art.excerpt)
            self.assertEq(article.Pending, art.status)
            self.assertTrue(art.iscommentable)
            self.assertEq(slug, art.slug)

    def it_calls_body(self): 
        art = article()
        self.assertNone(art.body)
        art.save()
        self.assertEmptyString(art.body)

        art.body = test_article.Smallpostbody
        self.assertEq(test_article.Smallpostbody, art.body)

        art.save()
        self.assertEq(test_article.Smallpostbody, art.body)

        art = article(art.id)
        self.assertEq(test_article.Smallpostbody, art.body)

    def it_calls_created_at(self):
        art = article()
        self.assertNone(art.created_at)
        before = datetime.now().replace(microsecond=0)

        art.save()

        after = datetime.now().replace(microsecond=0)

        self.assertLe(before, art.created_at)
        self.assertGe(after, art.created_at)

        created_at = art.created_at

        art = article(art.id)
        self.assertEq(created_at, art.created_at)

    def it_calls_title(self):
        art = article()
        self.assertNone(art.title)

        art.save()

        self.assertEmptyString(art.title)

        art.title = test_article.Smallposttitle
        self.assertEq(test_article.Smallposttitle, art.title)

        art.save()
        self.assertEq(test_article.Smallposttitle, art.title)

        art = article(art.id)
        self.assertEq(test_article.Smallposttitle, art.title)

    def it_calls_slug(self):
        art = article()
        self.assertNone(art.slug)

        art.save()

        self.assertEmptyString(art.slug)

        slug = str(uuid4())
        art.slug = slug
        self.assertEq(slug, art.slug)

        art.save()
        self.assertEq(slug, art.slug)

        art = article(art.id)
        self.assertEq(slug, art.slug)

    def it_calls_title_and_slug(self):
        art = article()
        title = 'Herp derp'
        slug = re.sub(r'\W+', '-', title).strip('-').lower()
        art.title = title

        self.assertEq(slug, art.slug)

        art.save()
        self.assertEq(slug, art.slug)

        art = article(art.id)
        self.assertEq(slug, art.slug)

        # A duplicate title will lead to a duplicate slug (slug_cache)
        # Therefore, a broken rule will indicate this and a save 
        # won't be permited because of the unique constraint on the
        # slug_cache field
        art = article()
        art.title = title
        self.assertTrue(art.brokenrules.contains('slug_cache', 'unique'))

        try:
            art.save()
        except brokenruleserror as ex:
            brs = ex.args[1].brokenrules
            self.assertTrue(brs.contains('slug_cache', 'unique'))
        except Exception:
            self.assertFalse('brokenruleserror was not raised')
        else:
            self.assertFalse('No exception was not raised')

    def it_calls_excerpt(self):
        art = article()
        self.assertNone(art.excerpt)
        art.save()
        self.assertEmptyString(art.excerpt)

        art = article(art.id)
        self.assertEmptyString(art.excerpt)

        art = article()
        self.assertNone(art.excerpt)
        art.save()
        self.assertEmptyString(art.excerpt)
        art = article(art.id)
        self.assertEmptyString(art.excerpt)

        art = article()
        art.excerpt = test_article.Smallpostexcerpt
        self.assertEq(test_article.Smallpostexcerpt, art.excerpt)
        art.save()
        self.assertEq(test_article.Smallpostexcerpt, art.excerpt)
        art = article(art.id)
        self.assertEq(test_article.Smallpostexcerpt, art.excerpt)

    def it_calls_status(self): 
        art = article()
        self.assertNone(art.status)
        art.save()
        self.assertEq(article.Draft, art.status)
        art = article(art.id)
        self.assertEq(article.Draft, art.status)

        art = article()
        art.status = article.Pending
        self.assertEq(article.Pending, art.status)
        art.save()
        self.assertEq(article.Pending, art.status)
        art = article(art.id)
        self.assertEq(article.Pending, art.status)

    def it_calls_iscommentable(self): 
        art = article()
        self.assertNone(art.iscommentable)
        art.save()
        self.assertFalse(art.iscommentable)
        art = article(art.id)
        self.assertFalse(art.iscommentable)

        art = article()
        art.iscommentable = True
        self.assertTrue(art.iscommentable)
        art.save()
        self.assertTrue(art.iscommentable)
        art = article(art.id)
        self.assertTrue(art.iscommentable)

        art = article()
        art.iscommentable = False
        self.assertFalse(art.iscommentable)
        art.save()
        self.assertFalse(art.iscommentable)
        art = article(art.id)
        self.assertFalse(art.iscommentable)

    def it_searches_by_id(self):
        art = article()
        art.save()
        id = art.id

        art = article(id)
        self.assertEq(id,   art.id)

    def it_searches_by_slug(self):
        art = article()
        slug = str(uuid4())
        art.slug = slug
        art.save()
        id = art.id

        art = article(slug)
        self.assertEq(slug, art.slug)
        self.assertEq(id,   art.id)

    def it_calls_wont_save_if_there_are_brokenrules(self): 
        # TODO
        return
        art = article()
        try:
            art.save()
        except brokenruleserror as ex:
            self.assertIs(art, ex.object)
        except:
            msg = ('BrokenRulesError expected however a different exception '
                  ' was thrown: ' + str(type(ex)))
            self.assertFail(msg)
        else:
            self.assertFail('No exception thrown on save of invalid object.')

    def it_calls_slug_and_title(self):
        title = test_article.Smallposttitle + str(uuid4())
        slug = re.sub(r'\W+', '-', title).strip('-').lower()

        art = article()
        art.title = title
        self.assertEq(slug, art.slug)
        self.assertEq(title, art.title)
        art.save()
        self.assertEq(slug, art.slug)
        self.assertEq(title, art.title)
        art = article(art.id)
        self.assertEq(slug, art.slug)
        self.assertEq(title, art.title)
        art = article(art.id)
        self.assertEq(slug, art.slug)
        self.assertEq(title, art.title)

        title = test_article.Smallposttitle + str(uuid4())
        slug = re.sub(r'\W+', '-', title).strip('-').lower()
        art = article()
        self.assertNone(art.slug)
        self.assertEq(None, art.title) 
        art.title = title
        self.assertEq(slug, art.slug)
        self.assertEq(title, art.title)

        art.save()
        self.assertEq(title, art.title)
        self.assertEq(slug, art.slug)
        art = article(art.id)
        self.assertEq(title, art.title)
        self.assertEq(slug, art.slug)

        art = article()
        self.assertEq(None, art.title)
        art.save()
        self.assertEq('', art.title)
        self.assertEmptyString(art.slug)
        art = article(art.id)
        self.assertEmptyString(art.slug)
        self.assertEq('', art.title)

        art = article()
        art.slug = 'Herp Derp'
        self.assertEq('Herp Derp', art.slug)
        self.assertEq(None, art.title)
        art.title = title
        self.assertEq('Herp Derp', art.slug)
        art.save()
        self.assertEq(title, art.title)
        self.assertEq('Herp Derp', art.slug)
        art = article(art.id)
        self.assertEq(title, art.title)
        self.assertEq('Herp Derp', art.slug)

    def it_saves_x_revisions_with_empty_properties(self):
        art = article()
        art.body = test_article.Smallpostbody
        title = test_article.Smallposttitle + ' - ' + str(uuid4())
        art.title = title
        art.excerpt = test_article.Smallpostexcerpt 
        art.status = article.Pending
        art.iscommentable = True

        art.save()

        for i in range(2):
            art.title = ''
            art.excerpt = ''
            art.slug = ''
            art.save()

            art = article(art.id)
            self.assertEmptyString(art.title)
            self.assertEmptyString(art.excerpt)
            self.assertEq(article.Pending, art.status)
            self.assertTrue(art.iscommentable)
            self.assertEmptyString(art.slug)

    def it_saves_x_revisions(self):
        art = article()
        art.body = test_article.Smallpostbody
        title = test_article.Smallposttitle + ' - ' + str(uuid4())
        art.title = title
        art.excerpt = test_article.Smallpostexcerpt 
        art.status = article.Pending
        art.iscommentable = True

        art.save()

        created_at = art.created_at
        
        self.assertNotNone(art.id)
        self.assertEq(test_article.Smallpostbody, art.body)
        self.assertEq(title, art.title)
        self.assertEq(test_article.Smallpostexcerpt, art.excerpt)
        self.assertEq(article.Pending, art.status)
        self.assertEq(True, art.iscommentable)
        slug = re.sub(r'\W+', '-', art.title).strip('-').lower()
        self.assertEq(slug, art.slug)

        x = 20

        for i in range(x):
            id = art.id

            # Mutate the body to ensure revision patching works
            if i < 5:
                newbody = art.body + 'X'
            elif i >= 5 and i <= 10:
                newbody = ''
                for j, c in enumerate(art.body):
                    if j == i:
                        c = 'x'
                    newbody += c
            elif i > 10:
                art.slug = 'walden-or-life-in-the-woods-hard-set'
                newbody = 'X' + art.body
                
            art.body = newbody

            art.title = newtitle = test_article.Smallposttitle + ' Rev ' + str(i)
            art.excerpt = newexcerpt = test_article.Smallpostexcerpt + ' Rev ' + str(i)
            art.status = article.Publish
            art.iscommentable = i % 2 == 0
            
            art.save()

            self.assertNotNone(art.id)
            self.assertEq(id, art.id)
            self.assertEq(newbody, art.body)
            self.assertEq(created_at, art.created_at)
            self.assertEq(newtitle, art.title)
            self.assertEq(newexcerpt, art.excerpt)
            self.assertEq(article.Publish, art.status)
            self.assertEq(i % 2 == 0, art.iscommentable)
            if i > 10:
                self.assertEq('walden-or-life-in-the-woods-hard-set', art.slug)
            else:
                self.assertEq(slug, art.slug)

    def _createblogpost(self):
        art = article()
        art.body = test_article.Smallpostbody
        art.title = test_article.Smallposttitle 
        art.excerpt = test_article.Smallpostexcerpt 
        art.status = article.Pending
        art.iscommentable = True

        art.save()

        x = 20

        for i in range(x):
            id = art.id

            # Mutate the body to ensure revision patching works
            if i < 5:
                newbody = art.body + 'X'
            elif i >= 5 and i <= 10:
                newbody = ''
                for j, c in enumerate(art.body):
                    if j == i:
                        c = 'x'
                    newbody += c
            elif i > 10:
                newbody = 'X' + art.body
                
            art.body = newbody

            art.title = newtitle = test_article.Smallposttitle + ' Rev ' + str(i)
            art.excerpt = newexcerpt = test_article.Smallpostexcerpt + ' Rev ' + str(i)
            art.status = article.Publish
            art.iscommentable = i % 2 == 0
            
            art.save()
        return art

    def it_retrives_blogpost(self):
        bp1 = self._createblogpost()
        bp2 = article(bp1.id)

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
        articlerevisions().RECREATE()

    def it_fails_saving_duplicate_slug_cache(self):
        revs = articlerevisions()

        slug_cache = uuid4()
        for i in range(3):
            rev = articlerevision()
            rev.body = test_article.Smallpostbody
            rev.title = test_article.Smallposttitle
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
        articlerevisions().RECREATE()

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
        rev.body = test_article.Smallpostbody
        rev.title = test_article.Smallposttitle
        rev.save()

        rev = articlerevision(rev.id)
        self.assertValid(rev)

    def it_breaks_diff_rules(self):
        # Diff must be empty for root revisions
        rev = articlerevision()
        rev.body = test_article.Smallpostbody
        rev.title = test_article.Smallposttitle
        rev.diff = diff.diff('herp', 'derp')
        self.assertCount(1, rev.brokenrules)
        self.assertTrue(rev.brokenrules.contains('diff', 'empty'))

        # Fix
        rev.diff = None
        self.assertValid(rev)

        # Break the rule that says a diff must be of type diff.diff
        rent = articlerevision()
        rent.body = test_article.Smallpostbody
        rent.title = test_article.Smallposttitle
        rent.diff = diff.diff('herp', 'derp')

        rev._parent = rent
        rev.body = None
        rev.diff = 'wrong type'
        self.assertCount(1, rev.brokenrules)
        self.assertTrue(rev.brokenrules.contains('diff', 'valid'))

    def it_breaks_title_rules(self):
        # Root revisions must have non null titles
        rev = articlerevision()
        rev.body = test_article.Smallpostbody
        self.assertCount(1, rev.brokenrules)
        self.assertTrue(rev.brokenrules.contains('title', 'full'))

        # Non-root revisions can have null titles
        rev._parent = articlerevision()
        self.assertCount(0, rev.brokenrules)

        # Root revisions can have empty strings as titles
        rev = articlerevision()
        rev.body = test_article.Smallpostbody
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
        rev.body = test_article.Smallpostbody
        rev.title = 'X' * 500
        self.assertCount(0, rev.brokenrules)
        rev.title = 'X' * 501
        self.assertCount(1, rev.brokenrules)
        self.assertTrue(rev.brokenrules.contains('title', 'fits'))

    def it_breaks_status_rules(self):
        rev = articlerevision()
        rev.body = test_article.Smallpostbody
        rev.title = test_article.Smallposttitle
        for st in article.Statuses:
            rev.status = st
            self.assertCount(0, rev.brokenrules)

        for st in ('wrong-type', 9999, object()):
            rev.status = st
            self.assertCount(1, rev.brokenrules)
            self.assertTrue(rev.brokenrules.contains('status', 'valid'))

    def it_breaks_slug_cache_uniqueness_rule(self):
        rev = articlerevision()
        rev.body = test_article.Smallpostbody
        rev.title = test_article.Smallposttitle
        slug_cache = uuid4()
        rev.slug_cache = slug_cache
        rev.save()

        rev = articlerevision()
        rev.body = test_article.Smallpostbody
        rev.title = test_article.Smallposttitle
        rev.slug_cache = slug_cache
        self.assertTrue(rev.brokenrules.contains('slug_cache', 'unique'))

    def it_fails_saving_duplicate_slug_cache(self):
        rev = articlerevision()
        rev.body = test_article.Smallpostbody
        rev.title = test_article.Smallposttitle
        slug_cache = uuid4()
        rev.slug_cache = slug_cache

        rev.save()

        rev = articlerevision()
        rev.body = test_article.Smallpostbody
        rev.title = test_article.Smallposttitle
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
        rent.body = test_article.Smallpostbody
        rent.title = test_article.Smallposttitle
        rent.diff = diff.diff('herp', 'derp')

        # A body and a diff shouldn't exist in the same record
        rev._parent = rent
        rev.diff = diff.diff('herp', 'derp')
        rev.body = test_article.Smallpostbody
        self.assertCount(2, rev.brokenrules)
        self.assertTrue(rev.brokenrules.contains('diff', 'valid'))

        # A non-root revision should can have a body but no diff. This
        # may be useful for caching or other isssues such as a failure to
        # create a diff.
        rev.body = test_article.Smallpostbody
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
