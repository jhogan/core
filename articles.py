# vim: set et ts=4 sw=4 fdm=marker
"""
MIT License

Copyright (c) 2018 Jesse Hogan

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
from app import controller
from binascii import a2b_hex
from datetime import datetime
from entities import brokenrules, brokenrule, entity, entities
from parties import user
from pdb import set_trace; B=set_trace
from pprint import pprint
import db
import diff
import parsers
import re
import uuid

class articlerevisions(db.dbentities):
    def __init__(self, id=None, entity=None):
        super().__init__()
        entity = articlerevision if entity == None else entity
        if id:
            if type(id) == uuid.UUID:
                sql = """
                select *
                from articlerevisions
                where rootid = %s
                """
                args = (id.bytes,)
            elif type(id) == str: # slug
                sql = """
                select ar1.*
                from articlerevisions ar1
                    inner join articlerevisions ar2
                        on ar1.rootid = ar2.id
                where ar2.slugcache = %s
                """
                args = (id,)
            revs = articlerevisions()
            ress = self.query(sql, args)

            # Create collection
            for res in ress:
                #revs += articlerevision(res=res)
                revs += entity(res=res)

            # Find and assign parent
            for rev1 in revs:
                for rev2 in revs:
                    if rev2._parentid == rev1.id:
                        rev2._parent = rev1
                        break

            # Find and assign the root revision
            for rev1 in revs:
                if rev1.isroot:
                    for rev2 in revs:
                        rev2._root = rev1
                # Get rid of parentid. It's only temporarily used to
                # discover the parent object. Keeping it around may
                # lead to confusion later on.
                del rev1._parentid 

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

    # TODO: Remove underscores in fields
    @property
    def _create(self):
        return """
        create table articlerevisions(
            id binary(16) primary key,
            parentid binary(16),
            rootid binary(16),
            title text,
            excerpt text,
            status tinyint,
            iscommentable bool,
            slug varchar(200),
            createdacreatedat datetime,
            body longtext,
            diff longtext,
            slugcache varchar(200),
            authorid binary(16)
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

    def __init__(self, id=None, parent=None, res=None):
        super().__init__();
        
        # TODO Only parent, id or res should be not None

        self._author = None

        if id == None:
            self._id = None
            self._parent = parent
            self._createdat = None
            self._title = None
            self._excerpt = None
            self._status = article.Draft
            self._iscommentable = False
            self._body = None
            self._diff = None
            self._slug = None
            self._slug_cache = None
            self._authorid = None
            self._marknew()
        elif type(id) == uuid.UUID:
            sql = 'select * from articlerevisions where id = %s';
            ress = self.query(sql, (id.bytes,))
            if not ress.hasone:
                raise Exception('Record not found: ' + str(id))
            res = ress.first
        else:
            raise ValueError('id is of the wrong type')

        if res != None:
            row = list(res._row)
            self._authorid = row.pop()
            if self._authorid:
                self._authorid = uuid.UUID(bytes=self._authorid)
            self._slug_cache = row.pop()
            self._diff = row.pop()

            if self._diff != None:
                self._diff = diff.diff(self._diff)

            self._body = row.pop()
            self._createdat = row.pop()
            self._slug = row.pop()
            self._iscommentable = bool(row.pop())
            self._status = row.pop()
            self._excerpt = row.pop()
            self._title = row.pop()
            row.pop() # rootid
            parentid = row.pop()
            if parentid:
                self._parentid = uuid.UUID(bytes=parentid)
            else:
                self._parentid = None
            self._id = uuid.UUID(bytes=row.pop())
            self._markold()

    def __str__(self):
        r  =   ''
        r  +=  'Parent:         '  +  str(self.parent.id)      +  '\n'  if  self.parent         else  ''
        r  +=  'Created:        '  +  str(self.createdat)     +  '\n'  if  self.createdat     else  ''
        r  +=  'Title:          '  +  str(self.title)          +  '\n'  if  self.title          else  ''
        r  +=  'Excerpt:        '  +  str(self.excerpt)        +  '\n'  if  self.excerpt        else  ''
        r  +=  'Status:         '  +  str(self.status)         +  '\n'  if  self.status         else  ''
        r  +=  'IsCommentable:  '  +  str(self.iscommentable)  +  '\n'  if  self.iscommentable  else  ''
        r  +=  'Body:           '  +  str(len(self.body))      +  '\n'  if  self.body           else  ''
        r  +=  'Diff:           '  +  len(str(self.diff))      +  '\n'  if  self.diff           else  ''
        r  +=  'Slug:           '  +  str(self.slug)           +  '\n'  if  self.slug           else  ''
        r  +=  'SlugCache:      '  +  str(self.slugcache)     +  '\n'  if  self.slug           else  ''
        r  +=  'Author:         '  +  str(self.author.name)    +  '\n'  if  self.author         else  ''
        return r

    def _update(self, cur=None):
        sql = """
        update articlerevisions
        set slugcache = %s
        where id = %s
        """

        args = (
            self.slugcache,
            self.id.bytes
        )

        self.query(sql, args, cur)
        
    def _insert(self, cur=None):
        id = uuid.uuid4()
        diff = None if self.diff == None else str(self.diff)
        diff = None if diff == '' else diff
        parentid = self.parent.id.bytes if self.parent else None
        rootid = id.bytes if self.isroot else self.root.id.bytes
        self._createdat = datetime.now().replace(microsecond=0)
        self._id = id

        if self.author:
            if self.author._isnew or self.author._isdirty:
                self.author.save()
            authorid = self.author.id.bytes
        else:
            authorid = None # Anonymous
        
        args = (id.bytes, 
                parentid,
                rootid,
                self.title,
                self.excerpt,
                self.status,
                self.iscommentable,
                self.slug,
                self._createdat,
                self.body,
                diff,
                self.slugcache,
                authorid)

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

        else: # non-root
            if type(self) == articlerevision and \
               type(self.parent) != articlerevision:
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
    def author(self):
        if not self._author:
            if self._authorid:
                self._author = user(self._authorid)
        return self._author

    @author.setter
    def author(self, v):
        return self._setvalue('_author', v, 'author')

    @property
    def parent(self):
        if not hasattr(self, '_parent')  or not self._parent:
            if hasattr(self, '_parentid') and self._parentid:
                self._parent = type(self)(self._parentid)
            else:
                self._parent = None
        return self._parent

    @property
    def createdat(self):
        return self._createdat

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
    def slugcache(self):
        return self._slug_cache

    @slugcache.setter
    def slugcache(self, v):
        return self._setvalue('_slug_cache', v, 'slugcache')

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
        self._revisions = None
        self._id = id
        self._author = None

        if self.revisions.ispopulated:
            self._id = self.revisions.first.id

    @property
    def revisions(self):
        if not self._revisions:
            self._revisions = articlerevisions(self._id)
        return self._revisions

    @property
    def id(self):
        return self._id

    @property
    def body(self):
        if not self._body:
            for rev in self.revisions:
                if rev.body != None:
                    self._body = rev.body
                elif rev.diff:
                    self._body = rev.diff.applyto(self._body)

        return self._body

    @body.setter
    def body(self, v):
        return self._setvalue('_body', v, 'body')

    @property
    def createdat(self):
        root = self.revisions.root
        if root:
            return self.revisions.root.createdat
        return None

    @property
    def title(self):
        if self._title == None:
            self._title = self.revisions.getlatest('title')
        return self._title

    @title.setter
    def title(self, v):
        return self._setvalue('_title', v, 'title')

    @property
    def excerpt(self):
        if self._excerpt == None:
            self._excerpt = self.revisions.getlatest('excerpt')
        return self._excerpt

    @excerpt.setter
    def excerpt(self, v):
        return self._setvalue('_excerpt', v, 'excerpt')

    @property
    def status(self):
        if self._status == None:
            self._status = self.revisions.getlatest('status')
        return self._status

    @status.setter
    def status(self, v):
        return self._setvalue('_status', v, 'status')

    @property
    def iscommentable(self):
        if self._iscommentable == None:
            self._iscommentable = self.revisions.getlatest('iscommentable')
        return self._iscommentable

    @iscommentable.setter
    def iscommentable(self, v):
        return self._setvalue('_iscommentable', v, 'iscommentable')

    @property
    def slug(self):
        if self._slug == None:
            self._slug = self.revisions.getlatest('slug')
            if self._slug == None:
                if self.title == None:
                    return None
                else:
                    slug = re.sub(r'\W+', '-', self.title).strip('-')
                    self._slug = slug.lower()
        return self._slug

    @slug.setter
    def slug(self, v):
        self._slug = None
        return self._setvalue('_slug', v, 'slug')

    @property
    def author(self):
        if self._author == None:
            authorid = self.revisions.getlatest('_authorid')
            if authorid is not None:
                self._author = user(authorid)
        return self._author

    @author.setter
    def author(self, v):
        return self._setvalue('_author', v, 'author')

    @property
    def brokenrules(self):
        rev = self._appendrevision()

        try:
            return self.revisions.brokenrules
        finally: 
            self.revisions.pop()

    def _appendrevision(self):
        n2e = lambda s: '' if s == None else s
        revs = self.revisions

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
        rev.root.slugcache = rev.slug
        rev.author = self.author
        return rev

    def save(self):
        rev = self._appendrevision()
        try:
            self.revisions.save()
        except:
            self.revisions.pop()
            raise
        else:
            self._id = rev.root.id

class blogposts(articles):
    def __init__(self, id=None):
        super().__init__(id)

class blogpost(article):

    def __init__(self, id=None):
        super().__init__(id)
        self._blog = None

    @property
    def revisions(self):
        if not self._revisions:
            self._revisions = blogpostrevisions(self._id)
        return self._revisions

    @property
    def blog(self):
        if self._blog == None:
            self._blog = self.revisions.getlatest('blog')
        return self._blog


    @blog.setter
    def blog(self, v):
        return self._setvalue('_blog', v, 'blog')

    def _appendrevision(self):
        rev = super()._appendrevision()
        rev.blog = self.blog
        return rev

class blogpostrevisions(articlerevisions):
    def __init__(self, id=None, entity=None):
        entity = blogpostrevision if entity == None else entity
        super().__init__(id, entity=entity)

    @property
    def _table(self):
        return 'blogpostrevisions'

    def create(self):
        parent = None if self.isempty else self.last
        rev = blogpostrevision(parent=parent)
        self += rev
        return rev

    @property
    def _create(self):
        return """
        create table blogpostrevisions(
            id binary(16) primary key,
            blogid binary(16)
        )
        """

class blogpostrevision(articlerevision):
    def __init__(self, id=None, parent=None, res=None):
        self._blog = None
        self._blog_id = None
        self._id = id
        self._load()

        super().__init__(id, parent=parent, res=res)

    def _load(self):
        id = self._id
        if type(id) == uuid.UUID:
            sql = 'select * from blogpostrevisions where id = %s';
            ress = self.query(sql, (id.bytes,))
            if not ress.hasone:
                raise Exception('Record not found: ' + str(id))
            res = ress.first
            row = list(res._row)
            self._blog_id = uuid.UUID(bytes=row.pop())

    def _insert(self, cur=None):
        if cur == None:
            conn = db.connections.getinstance().default.clone()
            cur = conn.createcursor()
        else:
            conn = None

        try:
            self._id = uuid.uuid4()
            blogid = self.blog.id.bytes if self.blog else None
            super()._insert(cur)
            args = (self.id.bytes, 
                    blogid
                    )

            insert = """
            insert into blogpostrevisions
            values({})
            """.format(('%s, ' * len(args)).rstrip(', '))

            self.query(insert, args, cur)
        except Exception as ex:
            if conn != None:
                conn.rollback()
            raise
        else:
            if conn != None:
                conn.commit()
        finally:
            if conn != None:
                cur.close()
                conn.close()

    @property
    def blog(self):
        if not self._blog:
            if not self._blog_id:
                if self.id and not self._isnew: 
                    self._load()
            if self._blog_id:
                self._blog = blog(self._blog_id)
        return self._blog

    @blog.setter
    def blog(self, v):
        return self._setvalue('_blog', v, 'blog')

    @property
    def brokenrules(self):
        brs = super().brokenrules

        if self.isroot:
            if self.body != None:
                p = parsers.htmlparser(self.body)
                try:
                    p.demandbalance()
                except Exception as ex:
                    brs += brokenrule(str(ex), 'body', 'valid')

            if self.blog:
                # TODO Why should slug or slugcache ever be allowed to be an
                # empty string?
                if self.slugcache != None and self.slugcache != '':
                    sql = """
                    select count(*)
                    from articlerevisions a
                       inner join blogpostrevisions b
                           on a.id = b.id
                    where 
                        a.slugcache = %s and
                        b.blogid = %s
                    """
                    args = self.slugcache, self.blog.id.bytes

                    ress = self.query(sql, args)
                    if ress.first[0] > 0:
                        msg = 'slugcache must be unique'
                        brs += brokenrule(msg, 'slugcache', 'unique')
            else:
                brs.demand(self, 'blog',  isfull=True)

        else:
            if type(self.parent) != blogpostrevision:
                msg = 'The parent property must be of type blogpostrevision'
                brs += brokenrule(msg, 'parent', 'valid')

            if type(self.diff) == diff.diff:
                p = parsers.htmlparser(self.derivedbody)
                try:
                    p.demandbalance()
                except Exception as ex:
                    brs += brokenrule(str(ex), 'derivedbody', 'valid')


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

class tags(db.dbentities):

    @property
    def _create(self):
        return """
        create table tags(
            id binary(16) primary key,
            name varchar(255),
            unique(name)
        )
        """

    @property
    def _table(self):
        return 'tags'

    @property
    def dbentity(self):
        return tag

    def __str__(self):
        return self._tostr(includeHeader=True, props=('name',))

class tag(db.dbentity):
    def __init__(self, o=None):
        super().__init__()
        if o == None:
            self._id    =  None
            self._name  =  None
            self._marknew()
        else:
            if type(o) == uuid.UUID:
                sql = 'select * from tags where id = %s'

                args = (
                    o.bytes,
                )

                ress = self.query(sql, args)
                res = ress.demandhasone()
            else:
                res = o
            row = list(res)
            self._name = row.pop()
            bytes = row.pop()
            if bytes:
                self._id = uuid.UUID(bytes=bytes)
                self._markold()
            else:
                self._id = None
                self._marknew()

    def __iter__(self):
        if self.id:
            yield self.id.bytes
        else:
            yield None
        yield self.name

    def _insert(self, cur=None):
        self._id = uuid.uuid4()
        args = (self._id.bytes, 
                self.name
                )

        insert = """
        insert into tags
        values({})
        """.format(('%s, ' * len(args)).rstrip(', '))

        self.query(insert, args, cur)

    def _update(self, cur=None):
        sql = """
        update tags
        set name = %s
        where id = %s
        """

        args = (
            self.name,
            self.id.bytes
        )

        self.query(sql, args, cur)

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, v):
        return self._setvalue('_name', v, 'name')

    @property
    def brokenrules(self):
        brs = brokenrules()
        brs.demand(self, 'name', isfull=True)

        # If name is full and it isn't strickly a string of lowercase
        # characters
        if brs.count == 0 and re.match('^[a-z]+\Z', self.name) is None:
            msg = 'name must be a string of lowercase letters'
            brs += brokenrule(msg, 'name', 'valid')

        sql = """
        select *
        from tags
        where name = %s
        """

        args = (self.name,)

        ress = db.connections.getinstance().default.query(sql, args)

        if ress.count > 0:
            brs += brokenrule('Name must be unique', 'name', 'unique')

        return brs

    def __str__(self):
        if self.name is None:
            return ''
        else:
            return '#' + self.name
    

