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

        # Create a blog
        bl = blog()
        bl.slug = 'carapacian-tech-blog'
        bl.description = 'Carapacian Tech Blog'
        bl.save()

        self.blog = bl

    def it_creates(self):
        bl = self.blog

        # Create blogpostrevision
        body = test_blogpost.Smallpostbody
        title = test_article.Smallposttitle + ' - ' + str(uuid4())
        slug = re.sub(r'\W+', '-', title).strip('-').lower()

        rev = blogpostrevision()
        rev.title = title
        rev.body = body
        rev.blog = bl
        rev.slug = slug
        rev.excerpt = test_article.Smallpostexcerpt
        rev.status = article.Pending
        rev.iscommentable = False
        rev.slug_cache = slug
        rev.save()

        # Relead blogpostrevision and test
        rev1 = blogpostrevision(rev.id)
        self.assertEq(rev.title, rev1.title)
        self.assertEq(rev.slug, rev1.slug)
        self.assertEq(rev.body, rev1.body)
        self.assertEq(rev.excerpt, rev1.excerpt)
        self.assertEq(rev.status, rev1.status)
        self.assertEq(rev.iscommentable, rev1.iscommentable)
        self.assertEq(rev.slug_cache, rev1.slug_cache)
        self.assertEq(bl.id, rev1.blog.id)
        self.assertTrue(rev)

    def it_instantiates(self):
        rev = blogpostrevision()
        self.assertNone(rev.id)
        self.assertNone(rev.authors)
        self.assertNone(rev.created_at)
        self.assertNone(rev.title)
        self.assertNone(rev.body)
        self.assertNone(rev.excerpt)
        self.assertEq(article.Draft, rev.status)
        self.assertFalse(rev.iscommentable)
        self.assertNone(rev.slug)
        self.assertNone(rev.blog)

    def it_fails_on_save_when_invalid(self):
        rev = blogpostrevision()
        try:
            rev.save()
        except brokenruleserror as ex:
            self.assertIs(rev, ex.object)
        except Exception as ex:
            msg = ('brokenruleserror expected however a different exception '
                  ' was thrown: ' + str(type(ex)))
            self.assertFail(msg)
        else:
            self.assertFail('No exception thrown on save of invalid object.')

    def it_fails_to_load_given_nonexistent_id(self):
        try:
            rev = blogpostrevision(uuid4())
        except Exception as ex:
            self.assertTrue(True)
        else:
            self.assertFail('Exception was not thrown')

    def it_loads_as_valid(self):
        rev = blogpostrevision()
        rev.body = test_blogpost.Smallpostbody
        rev.title = test_article.Smallposttitle + str(uuid4())
        rev.blog = self.blog
        rev.save()

        rev = blogpostrevision(rev.id)
        self.assertValid(rev)

    def it_breaks_diff_rules(self):
        # Diff must be empty for root revisions
        rev = blogpostrevision()
        rev.body = test_blogpost.Smallpostbody
        rev.title = test_article.Smallposttitle
        rev.diff = diff.diff('herp', 'derp')
        rev.blog = self.blog
        self.assertCount(1, rev.brokenrules)
        self.assertTrue(rev.brokenrules.contains('diff', 'empty'))

        # Fix
        rev.diff = None
        self.assertValid(rev)

        # Break the rule that says a diff must be of type diff.diff
        rent = blogpostrevision()
        rent.body = test_blogpost.Smallpostbody
        rent.title = test_article.Smallposttitle
        rev.blog = self.blog
        rent.diff = diff.diff('herp', 'derp')

        rev._parent = rent
        rev.body = None
        rev.diff = 'wrong type'
        self.assertCount(1, rev.brokenrules)
        self.assertTrue(rev.brokenrules.contains('diff', 'valid'))

    def it_breaks_title_rules(self):
        # Root revisions must have non null titles
        rev = blogpostrevision()
        rev.body = test_blogpost.Smallpostbody
        rev.blog = self.blog
        self.assertCount(1, rev.brokenrules)
        self.assertTrue(rev.brokenrules.contains('title', 'full'))

        # Non-root revisions can have null titles
        rev._parent = blogpostrevision()
        self.assertCount(0, rev.brokenrules)

        # Root revisions can have empty strings as titles
        rev = blogpostrevision()
        rev.body = test_blogpost.Smallpostbody
        rev.blog = self.blog
        rev.title = ''
        self.assertCount(0, rev.brokenrules)

        # Revisions titles must be strings
        rev.title = 123
        self.assertCount(1, rev.brokenrules)
        self.assertTrue(rev.brokenrules.contains('title', 'valid'))
        rev._parent = blogpostrevision() # Make non-root
        self.assertCount(1, rev.brokenrules)
        self.assertTrue(rev.brokenrules.contains('title', 'valid'))

        # Title must be less than 500 characters
        rev = blogpostrevision()
        rev.blog = self.blog
        rev.body = test_blogpost.Smallpostbody
        rev.title = 'X' * 500
        self.assertCount(0, rev.brokenrules)
        rev.title = 'X' * 501
        self.assertCount(1, rev.brokenrules)
        self.assertTrue(rev.brokenrules.contains('title', 'fits'))

    def it_breaks_status_rules(self):
        rev = blogpostrevision()
        rev.blog = self.blog
        rev.body = test_blogpost.Smallpostbody
        rev.title = test_article.Smallposttitle
        for st in article.Statuses:
            rev.status = st
            self.assertCount(0, rev.brokenrules)

        for st in ('wrong-type', 9999, object()):
            rev.status = st
            self.assertCount(1, rev.brokenrules)
            self.assertTrue(rev.brokenrules.contains('status', 'valid'))

    def it_breaks_body_rules_of_child(self):
        rent = blogpostrevision()
        rent.body = test_blogpost.Smallpostbody
        rent.title = test_article.Smallposttitle + str(uuid4())
        rent.blog = self.blog
        self.assertValid(rent)

        rev = blogpostrevision()
        rev._parent = rent
        rev.body = None
        rev.diff = diff.diff(rent.body, rent.body + '\n<b>This is strong</strong>')
        self.assertTrue(rev.brokenrules.contains('derivedbody', 'valid'))

    def it_breaks_body_rules(self):
        # Body must be full for root revisions
        rev = blogpostrevision()
        rev.blog = self.blog
        self.assertCount(2, rev.brokenrules)
        self.assertTrue(rev.brokenrules.contains('body', 'full'))
        self.assertTrue(rev.brokenrules.contains('title', 'full'))

        # Invalid HTML in body
        rev.body = '<em>This is special</i>'
        self.assertCount(2, rev.brokenrules)
        self.assertTrue(rev.brokenrules.contains('body', 'valid'))

        # Create a parent then test the child
        rent = blogpostrevision()
        rent.body = test_blogpost.Smallpostbody
        rent.title = test_article.Smallposttitle
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
    
    def it_breaks_blog_rules(self):
        # Body must be full for root revisions
        rev = blogpostrevision()
        rev.body = test_blogpost.Smallpostbody
        rev.title = test_article.Smallposttitle + str(uuid4())
        rev.blog
        self.assertCount(1, rev.brokenrules)
        self.assertTrue(rev.brokenrules.contains('blog', 'full'))

        
    def it_retrieves(self):
        rev = blogpostrevision()
        rev.blog = self.blog
        rev.body = test_article.Smallpostbody
        rev.title = test_article.Smallposttitle + str(uuid4())
        rev.save()
        rev = blogpostrevision(rev.id)
        self.assertEq(rev.id, rev.id)

class test_blogpost(tester):
    Smallpostbody = """
    <p>
        But men labor under a mistake. The better part of the man is soon plowed
        into the soil for compost. By a seeming fate, commonly called necessity,
        they are employed, as it says in an old book, laying up treasures which
        moth and rust will corrupt and thieves break through and steal. It is a
        fool's life, as they will find when they get to the end of it, if not
        before. It is said that Deucalion and Pyrrha created men by throwing
        stones over their heads behind them:-
        &nbsp;
    </p>
    <pre xml:space="preserve">           
        Inde genus durum sumus, experiensque laborum,
        Et documenta damus qua simus origine nati.
    </pre>
    <p class="nind">
        Or, as Raleigh rhymes it in his sonorous way,-
    </p>
    <pre xml:space="preserve">  
        "From thence our kind hard-hearted is, enduring pain and care,
        Approving that our bodies of a stony nature are."
    </pre>
    <p class="nind">
        So much for a blind obedience to a blundering oracle, throwing the stones
        over their heads behind them, and not seeing where they fell.
    </p>
    """
    def __init__(self):
        super().__init__()
        articlerevisions().RECREATE()
        blogpostrevisions().RECREATE()
        blogs().RECREATE()

        # Create a blog
        bl = blog()
        bl.slug = 'carapacian-tech-blog'
        bl.description = 'Carapacian Tech Blog'
        bl.save()

        self.blog = bl

    def it_loads_as_valid(self):
        bp = blogpost()
        bp.blog = self.blog
        bp.body = test_article.Smallpostbody
        title = test_article.Smallposttitle + ' - ' + str(uuid4())
        bp.title  = title
        slug = re.sub(r'\W+', '-', bp.title).strip('-').lower()
        bp.excerpt = test_article.Smallpostexcerpt 
        bp.status = article.Pending
        bp.iscommentable = True
        bp.blog = self.blog
        bp.save()

    def it_saves_x_revisions_with_null_properties(self):
        bp = blogpost()
        bp.blog = self.blog
        bp.body = test_article.Smallpostbody
        title = test_article.Smallposttitle + ' - ' + str(uuid4())
        bp.title  = title
        slug = re.sub(r'\W+', '-', bp.title).strip('-').lower()
        bp.excerpt = test_article.Smallpostexcerpt 
        bp.status = blogpost.Pending
        bp.iscommentable = True
        bp.blog = self.blog

        bp.save()

        x = 4
        for i in range(x):
            if i < x / 2:
                bp.title = None
                bp.excerpt = None
                bp.slug = None
            else:
                bp.body = test_article.Smallpostbody  + ' Rev: ' + str(i)
                revisedtitle = title + ' Rev: ' + str(i)
                bp.title = revisedtitle
                bp.excerpt = test_article.Smallpostexcerpt  + ' Rev: ' + str(i)
                
            bp.save()

            bp = blogpost(bp.id)

            if i < x / 2:
                self.assertEq(test_article.Smallpostbody, bp.body)
                self.assertEq(title, bp.title)
                self.assertEq(test_article.Smallpostexcerpt, bp.excerpt)
            else:
                self.assertEq(test_article.Smallpostbody + ' Rev: ' + str(i), bp.body)
                self.assertEq(revisedtitle, bp.title)
                self.assertEq(test_article.Smallpostexcerpt + ' Rev: ' + str(i), bp.excerpt)
            self.assertEq(blogpost.Pending, bp.status)
            self.assertTrue(bp.iscommentable)
            self.assertEq(slug, bp.slug)

    def it_calls_blog(self):
        bp = blogpost()
        self.assertTrue(bp.brokenrules.contains('blog', 'full'))

        self.assertNone(bp.blog)
        bp.blog = self.blog
        self.assertIs(self.blog, bp.blog)

        bp.save()

        bp = blogpost(bp.id)
        bp.blog
        self.assertEq(self.blog.id, bp.blog.id)

    def it_breaks_slug_cache_uniqueness_rule(self):
        bp = blogpost()
        bp.blog = self.blog
        bp.slug = 'my-slug'
        bp.save()

        bp = blogpost()
        bp.blog = self.blog
        bp.slug = 'my-slug'
        self.assertTrue(bp.brokenrules.contains('slug_cache', 'unique'))

        # Create a new blog
        bl = blog()
        bl.slug = 'some-other-tech-blog'
        bl.description = 'Some other blog'
        bl.save()

        bp.blog = bl
        self.assertZero(bp.brokenrules);

    def it_calls_revisions(self):
        # TODO Copy this to test_article
        bp = blogpost()
        bp.blog = self.blog

        self.assertCount(0, bp.revisions)

        # First save
        bp.save()
        self.assertCount(1, bp.revisions)
        self.assertType(blogpostrevisions, bp.revisions)
        for rev in bp.revisions:
            self.assertType(blogpostrevision, rev)

        self.assertEq(bp.blog.id, bp.revisions.first.blog.id)

        # ... then load
        
        bp1 = blogpost(bp.id)
        self.assertCount(1, bp1.revisions)
        self.assertEq(bp1.blog.id, bp1.revisions.first.blog.id)
        self.assertType(blogpostrevisions, bp1.revisions)
        for rev in bp1.revisions:
            self.assertType(blogpostrevision, rev)

        # Second save
        bp.save()
        self.assertCount(2, bp.revisions)
        self.assertEq(bp.blog.id, bp.revisions.first.blog.id)
        self.assertType(blogpostrevisions, bp1.revisions)
        for rev in bp1.revisions:
            self.assertType(blogpostrevision, rev)

        # ... then load
        
        # TODO: The second save should insert a revision record with a blog
        # value of None
        return
        self.assertEq(None, bp.revisions.second.blog)
        bp1 = blogpost(bp.id)
        self.assertCount(2, bp1.revisions)
        self.assertEq(bp1.blog.id, bp1.revisions.first.blog.id)
        self.assertEq(None, bp1.revisions.second.blog)

    def it_calls_body(self): 
        bp = blogpost()
        bp.blog = self.blog
        self.assertNone(bp.body)
        bp.save()
        self.assertEmptyString(bp.body)

        bp.body = test_article.Smallpostbody
        self.assertEq(test_article.Smallpostbody, bp.body)

        bp.save()
        self.assertEq(test_article.Smallpostbody, bp.body)

        bp = blogpost(bp.id)
        self.assertEq(test_article.Smallpostbody, bp.body)

    def it_calls_created_at(self):
        bp = blogpost()
        bp.blog = self.blog
        self.assertNone(bp.created_at)
        before = datetime.now().replace(microsecond=0)

        bp.blog = self.blog
        bp.save()

        after = datetime.now().replace(microsecond=0)

        self.assertLe(before, bp.created_at)
        self.assertGe(after, bp.created_at)

        created_at = bp.created_at

        bp = blogpost(bp.id)
        self.assertEq(created_at, bp.created_at)

    def it_calls_title(self):
        bp = blogpost()
        bp.blog = self.blog
        self.assertNone(bp.title)

        bp.save()

        self.assertEmptyString(bp.title)

        bp.title = test_article.Smallposttitle
        self.assertEq(test_article.Smallposttitle, bp.title)

        bp.save()
        self.assertEq(test_article.Smallposttitle, bp.title)

        bp = blogpost(bp.id)
        self.assertEq(test_article.Smallposttitle, bp.title)

    def it_calls_slug(self):
        bp = blogpost()
        bp.blog = self.blog
        self.assertNone(bp.slug)

        bp.save()

        self.assertEmptyString(bp.slug)

        slug = str(uuid4())
        bp.slug = slug
        self.assertEq(slug, bp.slug)

        bp.save()
        self.assertEq(slug, bp.slug)

        bp = blogpost(bp.id)
        self.assertEq(slug, bp.slug)

    def it_calls_title_and_slug(self):
        bp = blogpost()
        bp.blog = self.blog
        title = 'Herp derp'
        slug = re.sub(r'\W+', '-', title).strip('-').lower()
        bp.title = title

        self.assertEq(slug, bp.slug)

        bp.save()
        self.assertEq(slug, bp.slug)

        bp = blogpost(bp.id)
        self.assertEq(slug, bp.slug)

    def it_calls_excerpt(self):
        bp = blogpost()
        bp.blog = self.blog
        self.assertNone(bp.excerpt)
        bp.save()
        self.assertEmptyString(bp.excerpt)

        bp = blogpost(bp.id)
        self.assertEmptyString(bp.excerpt)

        bp = blogpost()
        bp.blog = self.blog
        self.assertNone(bp.excerpt)
        bp.save()
        self.assertEmptyString(bp.excerpt)
        bp = blogpost(bp.id)
        self.assertEmptyString(bp.excerpt)

        bp = blogpost()
        bp.blog = self.blog
        bp.excerpt = test_article.Smallpostexcerpt
        self.assertEq(test_article.Smallpostexcerpt, bp.excerpt)
        bp.save()
        self.assertEq(test_article.Smallpostexcerpt, bp.excerpt)
        bp = blogpost(bp.id)
        self.assertEq(test_article.Smallpostexcerpt, bp.excerpt)

    def it_calls_status(self): 
        bp = blogpost()
        bp.blog = self.blog
        self.assertNone(bp.status)
        bp.save()
        self.assertEq(blogpost.Draft, bp.status)
        bp = blogpost(bp.id)
        self.assertEq(blogpost.Draft, bp.status)

        bp = blogpost()
        bp.blog = self.blog
        bp.status = blogpost.Pending
        self.assertEq(blogpost.Pending, bp.status)
        bp.save()
        self.assertEq(blogpost.Pending, bp.status)
        bp = blogpost(bp.id)
        self.assertEq(blogpost.Pending, bp.status)

    def it_calls_iscommentable(self): 
        bp = blogpost()
        bp.blog = self.blog
        self.assertNone(bp.iscommentable)
        bp.save()
        self.assertFalse(bp.iscommentable)
        bp = blogpost(bp.id)
        self.assertFalse(bp.iscommentable)

        bp = blogpost()
        bp.blog = self.blog
        bp.iscommentable = True
        self.assertTrue(bp.iscommentable)
        bp.save()
        self.assertTrue(bp.iscommentable)
        bp = blogpost(bp.id)
        self.assertTrue(bp.iscommentable)

        bp = blogpost()
        bp.blog = self.blog
        bp.iscommentable = False
        self.assertFalse(bp.iscommentable)
        bp.save()
        self.assertFalse(bp.iscommentable)
        bp = blogpost(bp.id)
        self.assertFalse(bp.iscommentable)

    def it_searches_by_id(self):
        bp = blogpost()
        bp.blog = self.blog
        bp.save()
        id = bp.id

        bp = blogpost(id)
        self.assertEq(id,   bp.id)

    def it_searches_by_slug(self):
        bp = blogpost()
        bp.blog = self.blog
        slug = str(uuid4())
        bp.slug = slug
        bp.save()
        id = bp.id

        bp = blogpost(slug)
        self.assertEq(slug, bp.slug)
        self.assertEq(id,   bp.id)

    def it_calls_slug_and_title(self):
        title = test_article.Smallposttitle + str(uuid4())
        slug = re.sub(r'\W+', '-', title).strip('-').lower()

        bp = blogpost()
        bp.blog = self.blog
        bp.title = title
        self.assertEq(slug, bp.slug)
        self.assertEq(title, bp.title)
        bp.save()
        self.assertEq(slug, bp.slug)
        self.assertEq(title, bp.title)
        bp = blogpost(bp.id)
        self.assertEq(slug, bp.slug)
        self.assertEq(title, bp.title)
        bp = blogpost(bp.id)
        self.assertEq(slug, bp.slug)
        self.assertEq(title, bp.title)

        title = test_article.Smallposttitle + str(uuid4())
        slug = re.sub(r'\W+', '-', title).strip('-').lower()
        bp = blogpost()
        bp.blog = self.blog
        self.assertNone(bp.slug)
        self.assertEq(None, bp.title) 
        bp.title = title
        self.assertEq(slug, bp.slug)
        self.assertEq(title, bp.title)

        bp.save()
        self.assertEq(title, bp.title)
        self.assertEq(slug, bp.slug)
        bp = blogpost(bp.id)
        self.assertEq(title, bp.title)
        self.assertEq(slug, bp.slug)

        bp = blogpost()
        bp.blog = self.blog
        self.assertEq(None, bp.title)
        bp.save()
        self.assertEq('', bp.title)
        self.assertEmptyString(bp.slug)
        bp = blogpost(bp.id)
        self.assertEmptyString(bp.slug)
        self.assertEq('', bp.title)

        bp = blogpost()
        bp.blog = self.blog
        bp.slug = 'Herp Derp'
        self.assertEq('Herp Derp', bp.slug)
        self.assertEq(None, bp.title)
        bp.title = title
        self.assertEq('Herp Derp', bp.slug)
        bp.save()
        self.assertEq(title, bp.title)
        self.assertEq('Herp Derp', bp.slug)
        bp = blogpost(bp.id)
        self.assertEq(title, bp.title)
        self.assertEq('Herp Derp', bp.slug)

    def it_saves_x_revisions_with_empty_properties(self):
        bp = blogpost()
        bp.blog = self.blog
        bp.body = test_article.Smallpostbody
        title = test_article.Smallposttitle + ' - ' + str(uuid4())
        bp.title = title
        bp.excerpt = test_article.Smallpostexcerpt 
        bp.status = blogpost.Pending
        bp.iscommentable = True

        bp.save()

        for i in range(2):
            bp.title = ''
            bp.excerpt = ''
            bp.slug = ''
            bp.save()

            bp = blogpost(bp.id)
            bp.blog = self.blog
            self.assertEmptyString(bp.title)
            self.assertEmptyString(bp.excerpt)
            self.assertEq(blogpost.Pending, bp.status)
            self.assertTrue(bp.iscommentable)
            self.assertEmptyString(bp.slug)
            
    def it_has_valid_revisions(self):
        # TODO Ensure that each of the revisions is the revision property are
        # the correct type, etc. Ensure this is true when a blogpost is reloaded.
        # Copy this to test_article as well.
        pass

    def it_saves_x_revisions(self):
        bp = blogpost()
        bp.blog = self.blog
        bp.body = test_article.Smallpostbody
        title = test_article.Smallposttitle + ' - ' + str(uuid4())
        bp.title = title
        bp.excerpt = test_article.Smallpostexcerpt 
        bp.status = blogpost.Pending
        bp.iscommentable = True

        bp.save()

        created_at = bp.created_at
        
        self.assertNotNone(bp.id)
        self.assertEq(test_article.Smallpostbody, bp.body)
        self.assertEq(title, bp.title)
        self.assertEq(test_article.Smallpostexcerpt, bp.excerpt)
        self.assertEq(blogpost.Pending, bp.status)
        self.assertEq(True, bp.iscommentable)
        slug = re.sub(r'\W+', '-', bp.title).strip('-').lower()
        self.assertEq(slug, bp.slug)

        x = 20

        for i in range(x):
            id = bp.id

            # Mutate the body to ensure revision patching works
            if i < 5:
                newbody = bp.body + 'X'
            elif i >= 5 and i <= 10:
                newbody = ''
                for j, c in enumerate(bp.body):
                    if j == i:
                        c = 'x'
                    newbody += c
            elif i > 10:
                bp.slug = 'walden-or-life-in-the-woods-hard-set'
                newbody = 'X' + bp.body
                
            bp.body = newbody

            bp.title = newtitle = test_article.Smallposttitle + ' Rev ' + str(i)
            bp.excerpt = newexcerpt = test_article.Smallpostexcerpt + ' Rev ' + str(i)
            bp.status = blogpost.Publish
            bp.iscommentable = i % 2 == 0
            
            bp.save()

            self.assertNotNone(bp.id)
            self.assertEq(id, bp.id)
            self.assertEq(newbody, bp.body)
            self.assertEq(created_at, bp.created_at)
            self.assertEq(newtitle, bp.title)
            self.assertEq(newexcerpt, bp.excerpt)
            self.assertEq(blogpost.Publish, bp.status)
            self.assertEq(i % 2 == 0, bp.iscommentable)
            if i > 10:
                self.assertEq('walden-or-life-in-the-woods-hard-set', bp.slug)
            else:
                self.assertEq(slug, bp.slug)

    def _createblogpost(self):
        bp = blogpost()
        bp.blog = self.blog
        bp.body = test_article.Smallpostbody
        bp.title = test_article.Smallposttitle 
        bp.excerpt = test_article.Smallpostexcerpt 
        bp.status = blogpost.Pending
        bp.iscommentable = True

        bp.save()

        x = 20

        for i in range(x):
            id = bp.id

            # Mutate the body to ensure revision patching works
            if i < 5:
                newbody = bp.body + 'X'
            elif i >= 5 and i <= 10:
                newbody = ''
                for j, c in enumerate(bp.body):
                    if j == i:
                        c = 'x'
                    newbody += c
            elif i > 10:
                newbody = 'X' + bp.body
                
            bp.body = newbody

            bp.title = newtitle = test_article.Smallposttitle + ' Rev ' + str(i)
            bp.excerpt = newexcerpt = test_article.Smallpostexcerpt + ' Rev ' + str(i)
            bp.status = blogpost.Publish
            bp.iscommentable = i % 2 == 0
            
            bp.save()
        return bp

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
        except Exception as ex:
            msg = ('brokenruleserror expected however a different exception '
                  ' was thrown: ' + str(type(ex)))
            self.assertFail(msg)
        else:
            self.assertFail('No exception thrown on save of invalid object.')

    def it_fails_to_load_given_nonexistent_id(self):
        try:
            rev = articlerevision(uuid4())
        except Exception as ex:
            self.assertTrue(True)
        else:
            self.assertFail('Exception was not thrown')

    def it_loads_as_valid(self):
        rev = articlerevision()
        rev.body = test_article.Smallpostbody
        rev.title = test_article.Smallposttitle + str(uuid4())
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

    def it_retrieves(self):
        rev = articlerevision()
        rev.body = test_article.Smallpostbody
        rev.title = test_article.Smallposttitle + str(uuid4())
        rev.save()

        rev = articlerevision(rev.id)
        self.assertEq(rev.id, rev.id)

t = testers()
t.oninvoketest += lambda src, eargs: print('# ', end='', flush=True)
t.oninvoketest += lambda src, eargs: print(eargs.method[0], flush=True)
t.run()
print(t)
