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
from pdb import set_trace; B=set_trace
import db
from entities import brokenrules, brokenrule, entity, entities
import uuid
from binascii import a2b_hex
from datetime import datetime
from pprint import pprint
import diff
import re
from app import controller

class articlerevisions(db.dbentities):
    def __init__(self, id=None):
        super().__init__()
        if id:
            if type(id) == uuid.UUID:
                sql = """
                select *
                from articlerevisions
                where root_id = %s
                """
                args = (id.bytes,)
            elif type(id) == str: # slug
                sql = """
                select ar1.*
                from articlerevisions ar1
                    inner join articlerevisions ar2
                        on ar1.root_id = ar2.id
                where ar2.slug_cache = %s
                """
                args = (id,)
            revs = articlerevisions()
            ress = self.query(sql, args)
            for res in ress:
                revs += articlerevision(res=res)

            for rev1 in revs:
                for rev2 in revs:
                    if rev2._parent_id == rev1.id:
                        rev2._parent = rev1
                        break

            for rev1 in revs:
                if rev1.isroot:
                    for rev2 in revs:
                        rev2._root = rev1
                # Get rid of parent_id. It's only temporarily used to
                # discover the parent object. Keeping it around may
                # lead to confusion later on.
                del rev1._parent_id 

            revs.sort()
            self += revs
        self._root = None

    def sort(self, key=None, reverse=False):
        if key != None:
            # TODO Write test
            super().sort(key=key, reverse=reverse)
        else:
            ls = [self.root]
            rent = self.root
            while len(ls) < len(self):
                for rev in self:
                    if rev.parent is rent:
                        ls.append(rev)
                        rent = rev
                        break

            self.clear()

            if reverse:
                ls.reverse()
            self += ls

    @property
    def _table(self):
        return 'articlerevisions'

    def create(self):
        parent = None if self.isempty else self.last
        rev = articlerevision(parent=parent)
        self += rev
        return rev

    @property
    def _create(self):
        return """
        create table articlerevisions(
            id binary(16) primary key,
            parent_id binary(16),
            root_id binary(16),
            title text,
            excerpt text,
            status tinyint,
            iscommentable bool,
            slug varchar(200),
            created_at datetime,
            body longtext,
            diff longtext,
            slug_cache varchar(200),
            constraint unique_slug_cache unique (slug_cache)
        )
        """

    @property
    def root(self):
        if not self._root:
            for rev in self:
                if not rev.parent:
                    self._root = rev
                    break
        return self._root

    def getlatest(self, prop):
        for rev in self.reversed():
            val = getattr(rev, prop)
            if val != None:
                return val
        return None


class articlerevision(db.dbentity):
    """ An abstract class for subtypes such as academic paper, essays,
    scientific paper, blog, encyclopedia article, marketing article, usenet
    article, spoken article, listicle, portrait, etc."""

    def __init__(self,id=None, parent=None, res=None):
        super().__init__();
        
        # TODO Only parent, id or res should be not None

        if id == None:
            self._id = None
            self._parent = parent
            self._authors = None
            self._created_at = None
            self._title = None
            self._excerpt = None
            self._status = article.Draft
            self._iscommentable = False
            self._body = None
            self._diff = None
            self._slug = None
            self._slug_cache = None
            self._previous = None
            self._subsequent = None
            self._marknew()
        elif type(id) == uuid.UUID:
            sql = 'select * from articlerevisions where id = %s';
            ress = self.query(sql, (id.bytes,))
            if not ress.hasone:
                raise Exception('Record not found: ' + str(id))
            res = ress.first

        if res != None:
            row = list(res._row)
            self._slug_cache = row.pop()
            self._diff = row.pop()

            if self._diff != None:
                self._diff = diff.diff(self._diff)

            self._body = row.pop()
            self._created_at = row.pop()
            self._slug = row.pop()
            self._iscommentable = row.pop()
            self._status = row.pop()
            self._excerpt = row.pop()
            self._title = row.pop()
            row.pop() # root_id
            parent_id = row.pop()
            if parent_id:
                self._parent_id = uuid.UUID(bytes=parent_id)
            else:
                self._parent_id = None
            self._id = uuid.UUID(bytes=row.pop())
            self._markold()

    def _update(self, cur=None):
        sql = """
        update articlerevisions
        set slug_cache = %s
        where id = %s
        """

        args = (
            self.slug_cache,
            self.id.bytes
        )

        self.query(sql, args, cur)
        
    def _insert(self, cur=None):
        id = uuid.uuid4()
        diff = None if self.diff == None else str(self.diff)
        diff = None if diff == '' else diff
        parent_id = self.parent.id.bytes if self.parent else None
        root_id = id.bytes if self.isroot else self.root.id.bytes
        self._created_at = datetime.now().replace(microsecond=0)
        self._id = id
        args = (id.bytes, 
                parent_id,
                root_id,
                self.title,
                self.excerpt,
                self.status,
                self.iscommentable,
                self.slug,
                self._created_at,
                self.body,
                diff,
                self.slug_cache)

        insert = """
        insert into articlerevisions
        values({})
        """.format(('%s, ' * len(args)).rstrip(', '))

        self.query(insert, args, cur)

        # Since this insert supports transactions, don't mutate self
        # beyond this point since, if there is a failure a some point,
        # we would need to rollback these mutations which would be difficult.

    @property
    def isroot(self):
        return self is self.root

    @property
    def root(self):
        rent = self

        while(rent.parent):
            rent = rent.parent 

        return rent

    @property
    def brokenrules(self):
        brs = brokenrules()
        if self.isroot:
            if self.body == None:
                msg = 'The body property must not be null on the root revision'
                brs += brokenrule(msg, 'body', 'full')

            if self.diff != None:
                msg = 'The root revision must contain a null diff'
                brs += brokenrule(msg, 'diff', 'empty')

            if self.title == None:
                msg = 'The title property must not be null on the root revision'
                brs += brokenrule(msg, 'title', 'full')

            if self.status not in article.Statuses:
                msg = 'The status property has an invalid value'
                brs += brokenrule(msg, 'status', 'valid')

            if self.slug_cache != None:
                sql = """
                select count(*) 
                from articlerevisions 
                where slug_cache = %s
                """
                args = [self.slug_cache]
                if self.id:
                    sql += ' and id != %s'
                    args.append(self.id.bytes)

                ress = self.query(sql, args)
                if ress.first[0] > 0:
                    msg = 'slug_cache must be unique'
                    brs += brokenrule(msg, 'slug_cache', 'unique')

        else: # non-root
            if type(self.parent) != articlerevision:
                msg = 'The parent property must be of type article'
                brs += brokenrule(msg, 'parent', 'valid')

            if self.body == None:
                if self.diff != None and type(self.diff) != diff.diff:
                    msg = 'Non-root diffs but be null or of type diff'
                    brs += brokenrule(msg, 'diff', 'valid')
            else:
                if self.diff != None:
                    msg = ('The diff of non-root revisions must be null '
                           'if the body is not null')
                          
                    brs += brokenrule(msg, 'diff', 'valid')

            if self.diff != None and self.body != None:
                msg = 'Diff must be null if body is not null'
                brs += brokenrule(msg, 'diff', 'valid')

            if self.status != None:
                if self.status not in article.Statuses:
                    msg = 'The status property has an invalid value'
                    brs += brokenrule(msg, 'status', 'valid')

        if self.title != None:
            if type(self.title) == str:
                brs.demand(self, 'title',  maxlen=500)
            else:
                msg = 'Title must be a string or a None'
                brs += brokenrule(msg, 'title', 'valid')
                
            
        return brs
                
    @property
    def authors(self):
        return self._authors

    @property
    def parent(self):
        if not hasattr(self, '_parent')  or not self._parent:
            if hasattr(self, '_parent_id') and self._parent_id:
                self._parent = type(self)(self._parent_id)
            else:
                self._parent = None
        return self._parent


    @property
    def created_at(self):
        return self._created_at

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, v):
        return self._setvalue('_title', v, 'title')

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, v):
        return self._setvalue('_status', v, 'status')

    @property
    def iscommentable(self):
        return self._iscommentable

    @iscommentable.setter
    def iscommentable(self, v):
        return self._setvalue('_iscommentable', v, 'iscommentable')

    @property
    def slug(self):
        return self._slug

    @slug.setter
    def slug(self, v):
        return self._setvalue('_slug', v, 'slug')

    @property
    def slug_cache(self):
        if self._slug_cache == '':
            # If duplipcate empty string were allowed in the database, the unique
            # contraint on `slug_cache` would be violated
            return None
        else:
            return self._slug_cache

    @slug_cache.setter
    def slug_cache(self, v):
        return self._setvalue('_slug_cache', v, 'slug_cache')

    @property
    def body(self):
        return self._body

    @property
    def derivedbody(self):
        # TODO OPT This could be cached for performance 
        diffs = []
        rev = self
        while True:
            if rev.diff:
                diffs.append(rev.diff)
            if not rev.parent:
                break;
            rev = rev.parent

        diffs.reverse()

        body = rev.body
        
        for diff in diffs:
            body = diff.applyto(body)

        return body

    @body.setter
    def body(self, v):
        return self._setvalue('_body', v, 'body')

    @property
    def diff(self):
        return self._diff

    @diff.setter
    def diff(self, v):
        return self._setvalue('_diff', v, 'diff')

    @property
    def excerpt(self):
        return self._excerpt

    @excerpt.setter
    def excerpt(self, v):
        return self._setvalue('_excerpt', v, 'excerpt')

    @property
    def iscommentable(self):
        return self._iscommentable

    @iscommentable.setter
    def iscommentable(self, v):
        return self._setvalue('_iscommentable', v, 'iscommentable')

    @property
    def slug(self):
        return self._slug

    @slug.setter
    def slug(self, v):
        return self._setvalue('_slug', v, 'slug')

class articles(entities):
    pass

class article(entity):
    Publish   = 0  # Viewable by everyone.
    Future    = 1  # Scheduled to be published in a future date.
    Draft     = 2  # Incomplete post viewable by anyone with proper user role.
    Pending   = 3  # Not yet published
    Private   = 4  # Viewable only to admins.
    Trash     = 5  # Posts in the Trash are assigned the trash status.
    Autodraft = 6  # Autosave revisions
    
    Statuses = (Publish, Future, Draft, Pending, Trash, Autodraft)

    def __init__(self, id=None):
        super().__init__()

        self._body = None
        self._title = None
        self._excerpt = None
        self._status = None
        self._iscommentable = None
        self._slug = None
        self._revisions = articlerevisions(id)
        if self._revisions.ispopulated:
            self._id = self._revisions.first.id
        else:
            self._id = None

    @property
    def id(self):
        return self._id

    @property
    def body(self):
        if not self._body:
            for rev in self._revisions:
                if rev.body != None:
                    self._body = rev.body
                elif rev.diff:
                    self._body = rev.diff.applyto(self._body)

        return self._body

    @body.setter
    def body(self, v):
        return self._setvalue('_body', v, 'body')

    @property
    def created_at(self):
        root = self._revisions.root
        if root:
            return self._revisions.root.created_at
        return None

    @property
    def title(self):
        if self._title == None:
            self._title = self._revisions.getlatest('title')
        return self._title

    @title.setter
    def title(self, v):
        return self._setvalue('_title', v, 'title')

    @property
    def excerpt(self):
        if self._excerpt == None:
            self._excerpt = self._revisions.getlatest('excerpt')
        return self._excerpt

    @excerpt.setter
    def excerpt(self, v):
        return self._setvalue('_excerpt', v, 'excerpt')

    @property
    def status(self):
        if self._status == None:
            self._status = self._revisions.getlatest('status')
        return self._status

    @status.setter
    def status(self, v):
        return self._setvalue('_status', v, 'status')

    @property
    def iscommentable(self):
        if self._iscommentable == None:
            self._iscommentable = self._revisions.getlatest('iscommentable')
        return self._iscommentable

    @iscommentable.setter
    def iscommentable(self, v):
        return self._setvalue('_iscommentable', v, 'iscommentable')

    @property
    def slug(self):
        if self._slug == None:
            self._slug = self._revisions.getlatest('slug')
            if self._slug == None:
                if self.title == None:
                    return None
                else:
                    slug = re.sub(r'\W+', '-', self.title).strip('-')
                    self._slug = slug.lower()
            # TODO: Ensure slug is unique in database
        return self._slug

    @slug.setter
    def slug(self, v):
        self._slug = None
        return self._setvalue('_slug', v, 'slug')

    def _appendrevision(self):
        n2e = lambda s: '' if s == None else s
        revs = self._revisions

        rev = revs.create()

        if rev.isroot:
            rev.body = n2e(self.body)
        else:
            rev.diff = diff.diff(rev.parent.derivedbody, self.body)
            rev.body = None
            self.body = None

        # TODO If the rev is not root, these properties should be None unless
        # they are different from previous revisions. Ensure this is tested.
        rev.title = n2e(self.title)
        rev.excerpt = n2e(self.excerpt)
        rev.status = self.status
        rev.iscommentable = self.iscommentable
        rev.slug = self.slug
        rev.root.slug_cache = rev.slug
        return rev

    @property
    def brokenrules(self):
        rev = self._appendrevision()

        try:
            return self._revisions.brokenrules
        finally: 
            self._revisions.pop()

    def save(self):
        rev = self._appendrevision()
        try:
            self._revisions.save()
        except:
            self._revisions.pop()
            raise
        else:
            self._id = rev.root.id

class blogpostrevisions(articlerevisions):
    def __init__(self, id=None):
        super().__init__(id)

    @property
    def _table(self):
        return 'blogpostrevisions'

    @property
    def _create(self):
        return """
        create table blogpostrevisions(
            id binary(16) primary key,
            articlerevisions_id binary(16),
            blog_id binary(16)
        )
        """

class blogpostrevision(articlerevision):
    def __init__(self, id=None):
        self._blog = None
        articlerevisions_id = None
        if type(id) == uuid.UUID:
            sql = 'select * from blogpostrevisions where id = %s';
            ress = self.query(sql, (id.bytes,))
            if not ress.hasone:
                raise Exception('Record not found: ' + str(id))
            res = ress.first
            row = list(res._row)
            self._blog_id = row.pop()
            articlerevisions_id = row.pop()
            self._id = row.pop()

        super().__init__(articlerevisions_id)

    def _insert(self, cur=None):
        if cur == None:
            conn = db.connections.getinstance().default.clone()
            cur = conn.createcursor()
        else:
            conn = None

        try:
            super()._insert(cur)
            
            artrevid = self.id
            self._id = uuid.uuid4()
            args = (self.id.bytes, 
                    artrevid.bytes,
                    self.blog.id.bytes,
                    )

            insert = """
            insert into blogpostrevisions
            values({})
            """.format(('%s, ' * len(args)).rstrip(', '))

            B()
            self.query(insert, args, cur)
        except Exception as ex:
            if conn == None:
                raise
            else:
                conn.rollback()
        else:
            if conn != None:
                conn.commit()
        finally:
            if conn != None:
                cur.close()
                conn.close()

    @property
    def blog(self):
        return self._blog

    @blog.setter
    def blog(self, v):
        return self._setvalue('_blog', v, 'blog')

    @property
    def brokenrules(self):
        brs = super().brokenrules
        if not self.blog:
            brs.demand(self, 'blog',  isfull=True)
        return brs


class blogs(db.dbentities):
    def __init__(self):
        super().__init__()

    @property
    def _table(self):
        return 'blogs'

    @property
    def _create(self):
        return """
        create table blogs(
            id binary(16) primary key,
            slug varchar(255),
            description varchar(255),
            constraint slug unique (slug)
        )
        """

class blog(db.dbentity):
    def __init__(self, id=None):
        super().__init__()
        self._id = id
        if id:
            sql = """
            select *
            from blogs
            where id = %s
            """
            ress = self.query(sql, (id.bytes,))
            if not ress.hasone:
                raise Exception('Record not found: ' + str(id))

            res = ress.first
            row = list(res._row)
            self._description = row.pop()
            self._slug = row.pop()
            self._id = uuid.UUID(bytes=row.pop())
            self._markold()
        else:
            self._slug = None
            self._description = None
            self._marknew()
            
    def _insert(self, cur=None):
        id = uuid.uuid4()
        self._id = id
        args = (id.bytes, 
                self.slug,
                self.description,
                )

        insert = """
        insert into blogs
        values({})
        """.format(('%s, ' * len(args)).rstrip(', '))

        self.query(insert, args, cur)

    def _update(self, cur=None):
        sql = """
        update blogs
        set slug = %s,
        description = %s
        where id = %s
        """

        args = (
            self.slug,
            self.description,
            self.id.bytes
        )

        self.query(sql, args, cur)

    @property
    def slug(self):
        return self._slug

    @slug.setter
    def slug(self, v):
        return self._setvalue('_slug', v, 'slug')

    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, v):
        return self._setvalue('_description', v, 'description')

    @property
    def brokenrules(self):
        brs = brokenrules()
        brs.demand(self, 'description',  isfull=True)
        brs.demand(self, 'slug',  isfull=True)
        return brs
            


