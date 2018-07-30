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
from entities import brokenrules, brokenrule, entity, entities, event, eventargs
from MySQLdb.constants.ER import DUP_ENTRY
from parties import user, users, person, persons
from pdb import set_trace; B=set_trace
from pprint import pprint
from table import table
from html.parser import HTMLParser
from hashlib import md5
import builtins
import db
import diff
import re
import sys
import textwrap
import uuid
import xml.sax

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

            # Populate collection
            try:
                for res in ress:
                    self += entity(res=res)
            finally:
                self._isdirty = False

            self.sort()

    def _assignparents(self):
        # Find and assign parent
        for rev1 in self:
            for rev2 in self:
                if rev2._parentid == rev1.id:
                    rev2._parent = rev1
                    break

    def sort(self, key=None, reverse=False):
        if key is None:

            if self.isempty:
                return

            self._assignparents()
            ls = [self.root]
            rent = self.root
            while len(ls) < len(self):
                for rev in self:
                    if rev.parent is rent:
                        ls.append(rev)
                        rent = rev
                        break

            if reverse:
                ls.reverse()

            try:
                self.clear()
                self += ls
            finally:
                self._isdirty = False
        else:
            # TODO Write test
            super().sort(key=key, reverse=reverse)

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
            titlecache text,
            excerpt text,
            status tinyint,
            iscommentable bool,
            slug varchar(200),
            createdat datetime,
            body longtext,
            bodycache longtext,
            diff longtext,
            slugcache varchar(200),
            authorid binary(16),
            authorcache text,
            fulltext(titlecache, bodycache, authorcache)
        )
        """
    def __str__(self):
        import functools

        def getattr(obj, attr, *args):
            def rgetattr(obj, attr):
                if obj:
                    return builtins.getattr(obj, attr, *args)
                return None
            return functools.reduce(rgetattr, [obj] + attr.split('.'))

        tbl = table()

        r = tbl.newrow()
        r.newfield('ix')
        r.newfield('id')
        r.newfield('createdat')
        r.newfield('parentid')
        r.newfield('rootid')
        r.newfield('title')
        r.newfield('excerpt')
        r.newfield('status')
        r.newfield('iscommentable')
        r.newfield('slug')
        r.newfield('body')
        r.newfield('author')

        for rev in self:
            id        =  str(rev.id)[:7]         if  rev.id      else  ''
            parentid  =  str(rev.parent.id)[:7]  if  rev.parent  else  ''
            rootid    =  str(rev.root.id)[:7]

            title     =  textwrap.shorten(rev.title,   width=40, placeholder='...')
            excerpt   =  textwrap.shorten(rev.excerpt, width=40, placeholder='...')
            slug      =  textwrap.shorten(rev.slug,    width=40, placeholder='...')

            author = rev.author.fullname if rev.author else ''
            bodylen = len(rev.body) if rev.body else 'null'

            r = tbl.newrow()
            r.newfield(self.getindex(rev))
            r.newfield(id)
            r.newfield(rev.createdat)
            r.newfield(parentid)
            r.newfield(rootid)
            r.newfield(title)
            r.newfield(excerpt)
            r.newfield(article.st2str(rev.status))
            r.newfield(rev.iscommentable)
            r.newfield(slug)
            r.newfield(bodylen)
            r.newfield(author)

        return str(tbl)

    @property
    def root(self):
        for rev in self:
            if not rev.parent:
                return rev
        return None

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
            self._id             =  None
            self._parent         =  parent
            self._createdat      =  None
            self._title          =  None
            self._titlecache     =  None
            self._excerpt        =  None
            self._status         =  article.Draft
            self._iscommentable  =  False
            self._body           =  None
            self._bodycache      =  None
            self._diff           =  None
            self._slug           =  None
            self._slugcache      =  None
            self._authorid       =  None
            self._authorcache    =  None
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
            if type(res) is db.dbresult:
                row = list(res._row)
            else:
                row = res

            self._authorcache = row.pop()
            self._authorid = row.pop()
            if self._authorid:
                self._authorid = uuid.UUID(bytes=self._authorid)
            self._slugcache = row.pop()
            self._diff = row.pop()

            if self._diff != None:
                self._diff = diff.diff(self._diff)

            self._bodycache = row.pop()
            self._body = row.pop()
            self._createdat = row.pop()
            self._slug = row.pop()
            self._iscommentable = bool(row.pop())
            self._status = row.pop()
            self._excerpt = row.pop()
            self._titlecache = row.pop()
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
        r  +=  'Created:        '  +  str(self.createdat)      +  '\n'  if  self.createdat      else  ''
        r  +=  'Title:          '  +  str(self.title)          +  '\n'  if  self.title          else  ''
        r  +=  'Excerpt:        '  +  str(self.excerpt)        +  '\n'  if  self.excerpt        else  ''
        r  +=  'Status:         '  +  str(self.status)         +  '\n'  if  self.status         else  ''
        r  +=  'IsCommentable:  '  +  str(self.iscommentable)  +  '\n'  if  self.iscommentable  else  ''
        r  +=  'Body:           '  +  str(len(self.body))      +  '\n'  if  self.body           else  ''
        r  +=  'Diff:           '  +  len(str(self.diff))      +  '\n'  if  self.diff           else  ''
        r  +=  'Slug:           '  +  str(self.slug)           +  '\n'  if  self.slug           else  ''
        r  +=  'SlugCache:      '  +  str(self.slugcache)      +  '\n'  if  self.slug           else  ''
        r  +=  'Author:         '  +  str(self.author.name)    +  '\n'  if  self.author         else  ''

        return r

    def _update(self, cur=None):
        sql = """
        update articlerevisions
        set createdat = %s,
        slugcache     = %s,
        authorcache   = %s,
        titlecache    = %s,
        bodycache     = %s
        where id      = %s
        """

        args = (
            self.createdat,
            self.slugcache,
            self.authorcache,
            self.titlecache,
            self.bodycache,
            self.id.bytes
        )

        self.query(sql, args, cur)

        if self.author:
            self.author.save(cur)
        
    def _insert(self, cur=None):
        if self._id:
            id = self.id
        else:
            id = uuid.uuid4()
        diff = None if self.diff == None else str(self.diff)
        diff = None if diff == '' else diff
        parentid = self.parent.id.bytes if self.parent else None
        rootid = id.bytes if self.isroot else self.root.id.bytes
        self._createdat = datetime.now().replace(microsecond=0)
        self._id = id

        if self.author:
            if self.author._isnew or self.author._isdirty:
                self.author.save(cur)
            authorid = self.author.id.bytes
        else:
            authorid = None # Anonymous

        args = (id.bytes, 
                parentid,
                rootid,
                self.title,
                self.titlecache,
                self.excerpt,
                self.status,
                self.iscommentable,
                self.slug,
                self._createdat,
                self.body,
                self.bodycache,
                diff,
                self.slugcache,
                authorid,
                self.authorcache)

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
    def authorcache(self):
        return self._authorcache

    @authorcache.setter
    def authorcache(self, v):
        return self._setvalue('_authorcache', v, 'authorcache')

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
    def titlecache(self):
        return self._titlecache

    @titlecache.setter
    def titlecache(self, v):
        return self._setvalue('_titlecache', v, 'titlecache')

    @property
    def bodycache(self):
        return self._bodycache

    @bodycache.setter
    def bodycache(self, v):
        return self._setvalue('_bodycache', v, 'bodycache')

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
        return self._slugcache

    @slugcache.setter
    def slugcache(self, v):
        return self._setvalue('_slugcache', v, 'slugcache')

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
    def __init__(self, ids=None):
        super().__init__()
        if ids:
            for id in ids:
                self += article(id)

    def __str__(self):
        import functools

        def getattr(obj, attr, *args):
            def rgetattr(obj, attr):
                if obj:
                    return builtins.getattr(obj, attr, *args)
                return None
            return functools.reduce(rgetattr, [obj] + attr.split('.'))

        tbl = table()

        r = tbl.newrow()
        r.newfield('ix')
        r.newfield('id')
        r.newfield('createdat')
        r.newfield('title')
        r.newfield('excerpt')
        r.newfield('status')
        r.newfield('iscommentable')
        r.newfield('slug')
        r.newfield('body')
        r.newfield('author')
        r.newfield('tags')

        for i, art in enumerate(self):
            id        =  str(art.id)[:7]         if  art.id      else  ''

            title     =  textwrap.shorten(art.title,   width=40, placeholder='...')
            excerpt   =  textwrap.shorten(str(art.excerpt), width=40, placeholder='...')
            slug      =  textwrap.shorten(art.slug,    width=40, placeholder='...')

            author = art.author.fullname if art.author else ''
            bodylen = len(art.body) if art.body else 'null'

            r = tbl.newrow()
            r.newfield(i)
            r.newfield(id)
            r.newfield(art.createdat.date())
            r.newfield(title)
            r.newfield(excerpt)
            r.newfield(art.statusstr)
            r.newfield(art.iscommentable)
            r.newfield(slug)
            r.newfield(bodylen)
            r.newfield(author)
            r.newfield(' '.join(art.tags.pluck('name')))
        return str(tbl)

    def _self_onadd(self, src, eargs):
        super()._self_onadd(src, eargs)
        self._isdirty = True

    def _self_onremove(self, src, eargs):
        super()._self_onremove(src, eargs)
        self._isdirty = True

    @property
    def isdirty(self):
        return self._isdirty or any([x.isdirty for x in self])

    @property
    def isnew(self):
        return any([x.isnew for x in self])

    def save(self, cur=None):
        # If no cursor was given, we will manage the tx here
        tx = not bool(cur)
        if not cur:
            conn = db.connections.getinstance().default.clone()
            cur = conn.createcursor()

        try:
            for art in self:
                art.save(cur)
        except Exception:
            if tx:
                conn.rollback()
            raise
        else:
            if tx:
                conn.commit()
        finally:
            if tx:
                cur.close()
                conn.close()

    def ALL(self):
        return articles.search()
        
    @staticmethod
    def search(str=None, author=None, ids=None):
        # Return articles that were edited by the user 'author'

        if str is not None:
            # Do a fulltext search on the articles' cache fields
            sql = """
            select *
            from articlerevisions art
                left join blogpostrevisions bp
                    on art.id = bp.id
            where 
                art.rootid in (
                    select art.id
                    from articlerevisions art
                    where 
                        art.id = art.rootid and
                        match(titlecache, bodycache, authorcache)
                        against (%s in natural language mode)
                )
            """

            args = str,
            
        elif author is not None:
            # If author doesn't exist in the database yet, just return an empty
            # articles collection.
            if not author.id:
                return articles()
          
            # Query all articlerevisions and potential blogpostrevisions edited
            # by 'author'
            sql = """
            select *
            from articlerevisions art
                left join blogpostrevisions bp
                    on art.id = bp.id
            where art.authorid = %s
            """
            args = (author.id.bytes,)

        elif ids is not None:
            # If we got passed an iterable of ids, just return an empty
            # articles collection.
            if len(ids) == 0:
                return articles()

            # Query all articlerevisions and potential blogpostrevisions that
            # have 'ids'
            sql = """
            select *
            from articlerevisions art
                left join blogpostrevisions bp
                    on art.id = bp.id
            where art.rootid in ({})
            """.format(', '.join(['%s'] * len(ids)))
            args = [id.bytes for id in ids]
        else:
            sql = """
            select *
            from articlerevisions art
                left join blogpostrevisions bp
                    on art.id = bp.id
            """
            args = ()
        
        ress = db.connections.getinstance().default.query(sql, args)

        # Create a dict to hold a collection of revision collections. The key
        # will be the rootid of the articlerevisions record, which is the id
        # for the article itself.
        revss = {}
        for res in ress:
            r = list(res._row)

            # art holds the fields from articlerevisions. bp holds the fields
            # from blogpostrevisions if any were found.
            art, bp = r[:16], r[16:]

            rootid = art[2]

            # If a non-null value was returned for the blogpostrevisions.id
            # field, then this must be a blogpostrevision subtype of article.
            isbprev = bool(bp[0])

            # Get the revs collection from the dict. If one doesn't exist,
            # create it.
            try:
                revs = revss[rootid]
            except KeyError:
                if isbprev:
                    revs = revss[rootid] = blogpostrevisions()
                else:
                    revs = revss[rootid] = articlerevisions()

            # Give the art array to the correct articlerevision type so that
            # the __init__ will hydrate the fields with its values.
            if isbprev:
                revs += blogpostrevision(res=art)
            else:
                revs += articlerevision(res=art)

        # Now that we have the revisions collections hydrated, create articles
        # and assign the revision collections to those new article. We return
        # the articles collection we create here.
        arts = articles()
        for rootid, revs in revss.items():
            # Choose the correct subtype based on the revisions collection's
            # subtype.
            isbp = type(revs) is blogpostrevisions
            if isbp:
                art = blogpost()
            else:
                art = article()

            art._id = uuid.UUID(bytes=rootid)

            revs.sort()
            art._revisions = revs

            art._tags_mm_articles = tags_mm_articles(art)
            for mm in art._tags_mm_articles:
                art.tags += tag(mm.tagid)

            arts += art

        arts._isdirty = False


        return arts

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

        # id may be a str slug. Wait for self._id to be assign below (using the
        # first revision) before assuming it is the real uuid for this entity.
        self._id             =  id

        self._body           =  None
        self._title          =  None
        self._excerpt        =  None
        self._status         =  None
        self._iscommentable  =  None
        self._slug           =  None
        self._revisions      =  None
        self._author         =  None
        self._tags           =  None

        if self.revisions.ispopulated:
            self._id = self.revisions.first.id

        self._tags_mm_articles = tags_mm_articles(self)

        for mm in self._tags_mm_articles:
            self.tags += tag(mm.tagid)

    @property
    def revisions(self):
        if not self._revisions:
            self._revisions = articlerevisions(self._id)
        return self._revisions

    @property
    def isdirty(self):
        if self.revisions.isempty:
            return False

        if self.revisions.isdirty:
            return True

        revs = self.revisions
        props = 'body', 'title', 'excerpt', 'status', 'iscommentable'

        for prop in props:
            v = getattr(self, prop)
            if v != revs.getlatest(prop):
                return True

        author = revs.getlatest('author')
        if self.author:
            if author:
                if self.author.name    != author.name or \
                   self.author.service != author.service:
                    return True
            else:
                return True
        else:
            if author:
                return True

        return False

    @property
    def isnew(self):
        # TODO: Write tests
        return any([x.isnew for x in self.revisions])

    @property
    def tags(self):
        if not self._tags:
            self._tags = tags()
        return self._tags

    @tags.setter
    def tags(self, v):
        self._tags = v

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

    @staticmethod
    def str2st(str):
        # TODO Write test

        # TODO Centralize the list of status strings

        try:
            return ('Publish', 'Future', 'Draft', 'Pending',
                    'Private', 'Trash',  'Autodraft').index(str.capitalize())
        except:
            return None

    @staticmethod
    def st2str(st):
        # TODO Write test
        if st is None:
            return None
        return (
            'Publish',
            'Future',
            'Draft',
            'Pending',
            'Private',
            'Trash',
            'Autodraft')[st]

    @property
    def statusstr(self):
        # TODO Write test
        return self.st2str(self.status)

    @statusstr.setter
    def statusstr(self, v):
        # TODO Write test
        st= self.str2st(v)
        self.status = st
        return self.statusstr

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
            rev._id = self._id
            rev.body = n2e(self.body)
        else:
            rev.diff = diff.diff(rev.parent.derivedbody, self.body)
            rev.body = None

        # TODO If the rev is not root, these properties should be None unless
        # they are different from previous revisions. Ensure this is tested.
        rev.title = n2e(self.title)
        rev.excerpt = n2e(self.excerpt)
        rev.status = self.status
        rev.iscommentable = self.iscommentable
        rev.slug = self.slug
        rev.author = self.author

        # Root caching
        rev.root.slugcache  = rev.slug
        rev.root.titlecache = rev.title

        if rev.isroot:
            rev.root.bodycache  = rev.body
        else:
            rev.root.bodycache  = rev.derivedbody

        if rev.author:
            rev.root.authorcache = self._authorcache(rev.author)

        return rev

    def save(self, cur=None):
        rev = self._appendrevision()
        try:
            self.revisions.save(cur)
        except:
            # TODO Here we need to use self.revisions.last to assign values to
            # the cache attributes (e.g., slugcache) of the self.revisions.root
            # revision
            self.revisions.pop()
            root = self.revisions.root
            if root:
                author           =  self.revisions.getlatest('author')

                root.authorcache =  self._authorcache(author)
                root.slugcache   =  self.revisions.getlatest('slug')
                root.titlecache  =  self.revisions.getlatest('title')
                root.bodycache   =  self.revisions.last.derivedbody

            raise
        else:
            self._id = rev.root.id

        self._tags_mm_articles.attach(self.tags)
        self._tags_mm_articles.save()

    @staticmethod
    def _authorcache(u):
        if not u:
            return ''

        cache = u.name
        p = u.person
        if p:
            cache += ' ' + p.fullname
            cache += ' ' + p.email
        return cache

    @property
    def root(self):
        # TODO Write test
        for rev in self.revisions:
            if rev.isroot:
                return rev
        return None

    def __str__(self):
        # TODO Write tes
        def shorten(str):
            str = builtins.str(str)
            return textwrap.shorten(str, width=65, placeholder='...')

        def indent(str):
            str = builtins.str(str)
            return textwrap.indent(str, ' ' * 4)

        r = """
Id:           {}
Author:       {}
Created:      {}
Commentable:  {}
Status:       {}
Title:        {}
Excerpt:      {}
Body:         {}
Tags:         {}
"""
        id = self.id if self.id else ''
        author = self.author.fullname if self.author else ''

        tags = ' '.join([str(t) for t in self.tags])

        r = r.format(id, 
                     author,
                     str(self.createdat),
                     str(self.iscommentable),
                     self.statusstr,
                     shorten(self.title),
                     shorten(self.excerpt),
                     shorten(self.body),
                     tags,
                     )

        r += '\nRevisions\n'
        r += str(self.revisions)

        return r

class blogposts(articles):
    def __init__(self, id=None):
        super().__init__(id)

    @staticmethod
    def search(str=None, author=None, ids=None):
        arts = articles.search(str=str, author=author, ids=ids)
        bps = blogposts()

        for art in arts:
            if type(art) is blogpost:
                bps += art

        return bps


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

    def __str__(self):

        def shorten(str):
            str = builtins.str(str)
            return textwrap.shorten(str, width=65, placeholder='...')

        def indent(str):
            return textwrap.indent(str, ' ' * 4)

        r = """
Id:           {}
Author:       {}
Created:      {}
Commentable:  {}
Blog:         {}
Status:       {}
Title:        {}
Excerpt:      {}
Body:         {}
Tags:         {}
"""
        id = self.id if self.id else ''
        author = self.author.fullname if self.author else ''

        tags = ' '.join([str(t) for t in self.tags])

        blog = self.blog.slug if self.blog else ''

        r = r.format(id, 
                     author,
                     str(self.createdat),
                     str(self.iscommentable),
                     blog,
                     self.statusstr,
                     shorten(self.title),
                     shorten(str(self.excerpt)),
                     shorten(self.body),
                     tags,
                     )

        r += '\nRevisions\n'
        r += str(self.revisions)

        return r

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
            if not self._id:
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

            # TODO: This should probably be: conn.query()
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

    class balancetester(HTMLParser):
        def __init__(self, html=None):
            super().__init__()
            self.starttags = []
            self.feed(html)

        def handle_starttag(self, tag, attrs):
            self.starttags.append(tag)

        def handle_endtag(self, tag):
            laststarttag = self.starttags.pop()
            if tag != laststarttag:
                line, ch = self.getpos()
                msg = "Can't close <{}> with </{}> at {},{}"
                msg = msg.format(laststarttag, tag, line, ch)
                raise Exception(msg)

    @property
    def brokenrules(self):
        brs = super().brokenrules

        if self.isroot:
            if self.body != None:
                try: 
                    blogpostrevision.balancetester(self.body)
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

                    args = [self.slugcache, self.blog.id.bytes]
                    
                    if self.id:
                        sql += ' and a.id != %s'
                        args.append(self.id.bytes)

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
                try: 
                    blogpostrevision.balancetester(self.derivedbody)
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
        self.onimportstatuschange = event()
        self.onrequestauthormap = event()
        self.onitemimport = event()
        self.onitemimporterror = event()
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

    class wxrhandler(xml.sax.ContentHandler):

        class statuschangeeventargs(eventargs):
            def __init__(self, handler):
                self.locator = handler._locator
                self.handler = handler
                self.lineno = self.locator.getLineNumber()

        class onaddeventargs(eventargs):
            def __init__(self, item):
                self.item = item

        class onerroreventargs(eventargs):
            def __init__(self, item, ex=None):
                self.item = item
                self.exception = ex

        class requestauthormapeventargs(eventargs):
            def __init__(self, importpersons, creators):
                # importpersons are person objects created from scanning the
                # WXR file. creators are user objects that the caller will
                # map to a given importpersons object. The mapping is based on
                # the the order of the two collection objects, e.g.,
                # importpersons.first maps to creators.first, and so on.
                self.importpersons = importpersons
                self.creators = creators

        def __init__(self, b):
            self.tags = []
            self.lastattrs = None
            self.importpersons = persons()
            self.creators = users()
            self.item = None
            self.blog = b
            self.importtags = tags()

            # Events
            self.onstatuschange = event()
            self.onrequestauthormap = event()
            self.onadd = event()
            self.onerror = event()

        def startElement(self, tag, attrs):
            eargs = blog.wxrhandler.statuschangeeventargs(self)
            self.onstatuschange(self, eargs)

            self.tags.append(tag)
            self.lastattrs = attrs
            if tag == 'wp:author':
                p = person()
                p.users += user()
                self.importpersons += p
            elif tag == 'wp:tag':
                # Instead of `self.importtag += tag()`, we must use the more
                # verbose version of this because the 'tag' variable already
                # exists in this scope.
                self.importtags += sys.modules[self.__module__].tag()
            elif tag == 'item':
                
                # If we are at an <item>, let's make sure we ask the caller to
                # map the authors found in the WXR to users in the system.
                creators = self.creators
                importpersons = self.importpersons
                while creators.count < importpersons.count:
                    eargs = blog.wxrhandler.requestauthormapeventargs
                    eargs = eargs(importpersons, creators)
                    self.onrequestauthormap(self, eargs)

                self.item = {}

        def characters(self, content):
            tag = self.tags[-1]
            if tag == 'wp:author_login':
                p = self.importpersons.last
                p.users.first.name = content
            elif tag == 'wp:author_email':
                p = self.importpersons.last
                p.email = content
            elif tag == 'wp:author_first_name':
                p = self.importpersons.last
                p.firstname = content
            elif tag == 'wp:author_last_name':
                p = self.importpersons.last
                p.lastname = content
            elif tag == 'wp:author_display_name':
                p = self.importpersons.last
                p.users.first.displayname = content
            elif tag == 'wp:tag_name':
                self.importtags.last.name = content.replace(' ', '')

            if self.item is not None:
                try:
                    # The hashtags for a post look like this: 
                    #    <category domain="post_tag" nicename="debugging">
                    #       <![CDATA[my-tag-name]]>
                    #    </category>
                    # When the 'tag' is 'category', use a comma to chain them 
                    # since WordPress disallows commas in tags
                    iscategory = tag == 'category'
                    if iscategory:
                        # If tag is a post_tag. The alternative is for the
                        # 'domain' attr to be set to 'category'. We are not
                        # currently collecting categories; just tags.
                        if ('domain', 'post_tag') in self.lastattrs.items():
                            content = content.replace(' ', '')
                            self.item[tag] += ',' + content
                    else:
                        self.item[tag] += content

                except KeyError:
                    self.item[tag] = content

        def endElement(self, tag):
            tag = self.tags[-1]
            if tag == 'wp:tag':
                self.importtags.last.save()
            elif tag == 'item':
                d = self.item
                art = None
                if d['wp:post_type'] == 'post':
                    art = blogpost()
                    art.blog = self.blog
                elif d['wp:post_type'] == 'page':
                    art = article()

                if art:
                    art.title = d['title']

                    creator = d['dc:creator']
                    for i, p in enumerate(self.importpersons):
                        if p.users.first.name == creator:
                            art.author = self.creators[i]

                    content = None
                    try:
                        content = d['content:encoded']
                    except KeyError:
                        pass
                    
                    if content:
                        prs = blog.wppostparser()
                        prs.feed(content)
                        body = str(prs) + '\n'

                        # Close out any tags that are remaining.
                        for tag in prs.tags:
                            body += '</' + tag + '>\n'

                        art.body = body
                    
                    art.statusstr = d['wp:status']
                    art.iscommentable = d['wp:comment_status'] == 'open'

                    # Hash the <guid> value (the url of the blog post), and make it the id 
                    # of the article.
                    art._id = uuid.UUID(bytes=md5((d['guid'].encode('utf-8'))).digest())

                    try:
                        hashtags = d['category'].split(',')
                    except KeyError:
                        pass
                    else:
                        for hashtag in hashtags:
                            art.tags += self.importtags[hashtag]

                    try:
                        art.excerpt = d['excerpt:encoded']
                    except KeyError:
                        art.excerpt = ''

                    try:
                        if art.isvalid:
                            art.save()

                            # Parse date and convert to local timezone. Update
                            # the revision to contain that as its createat
                            # date.
                            fmtdts = ( 
                                ('%a, %d %b %Y %H:%M:%S %z', d['pubDate']),
                                ('%Y-%m-%d %H:%M:%S',        d['wp:post_date']), 
                            )
                            
                            for fmt, dt in fmtdts:
                                try:
                                    dt = datetime.strptime(dt, fmt)
                                    break
                                except ValueError:
                                    pass
                            else:
                                raise Exception("Can't find a create date")

                            if dt.tzinfo:
                                dt = dt.astimezone(tz=None)
                            rev = art.revisions.root
                            rev._createdat = dt

                            # Explicitly dirty since we are updating a private
                            # member.
                            rev._isdirty = True
                            rev.save()
                            self.onadd(self, blog.wxrhandler.onaddeventargs(art))
                        else:
                            self.onerror(self, blog.wxrhandler.onerroreventargs(art))
                    except Exception as ex:
                        self.onerror(self, blog.wxrhandler.onerroreventargs(art, ex))

                self.item = None

            self.tags.pop()

    class wppostparser(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=False)
            self.html = []
            self.tags = []

        def __str__(self):
            return ''.join(self.html)

        def handle_starttag(self, tag, attrs):

            html = '<' + tag
            for i, kvp in enumerate(attrs):
                html += ' ' + kvp[0] + '="' + kvp[1] + '"'
            html += '>'
            self.html.append(html)
            self.tags.append(tag)

        def handle_endtag(self, tag):
            tags = self.tags

            html = '</{}>'.format(tag)
            self.html.append(html)

            tags.pop()

        def handle_data(self, data):
            
            inp = 'p' in self.tags

            if '\n\n' not in data:
                if not self.tags:
                    data = '\n<p>\n' + data
                    self.tags.append('p')
                self.html.append(data)
                return

            lines = [line
                     for line in data.split('\n\n') 
                     if line.strip() != '']

            for i, line in enumerate(lines):
                if 'p' in self.tags:
                    if i < len(lines) - 1 or data[-2:] == '\n\n':
                        line += '\n</p>\n'
                        self.tags.pop()
                else:
                    line = '\n<p>\n' + line
                    self.tags.append('p')

                lines[i] = line

            self.html.append('\n'.join(lines))

    def import_(self, path):
        handler = blog.wxrhandler(self)

        if self.onrequestauthormap.count == 0:
            msg = 'An subscription to the onrequestauthormap event must be made'
            raise Exception(msg)

        handler.onstatuschange     += lambda src, eargs: self.onimportstatuschange(src, eargs)
        handler.onrequestauthormap += lambda src, eargs: self.onrequestauthormap  (src, eargs)
        handler.onadd              += lambda src, eargs: self.onitemimport        (src, eargs)
        handler.onerror            += lambda src, eargs: self.onitemimporterror   (src, eargs)

        prs = xml.sax.make_parser()

        prs.setContentHandler(handler)
        prs.parse(path)

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

        self._tags_mm_articles = None
        self._articles = None

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

    @property
    def isdirty(self):
        return super().isdirty or \
               self.articles.isdirty

    @property
    def _collection(self):
        return tags

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

        # If articles have been loaded, save them.
        if self._articles:
            self.articles.save()
            self._tags_mm_articles.attach(self.articles)
            self._tags_mm_articles.save()


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

        if self._articles:
            self.articles.save()
            self._tags_mm_articles.attach(self.articles)
            self._tags_mm_articles.save()

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
        if brs.count == 0 and re.match('^[a-z0-9-]+\Z', self.name) is None:
            msg = 'name must be a string of lowercase letters'
            brs += brokenrule(msg, 'name', 'valid')

        if self.isnew:
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

    @property
    def articles(self):
        if not self._articles:
            mm = self._get_tags_mm_articles()
            ids = mm.pluck('articleid')
            self._articles = articles.search(ids=ids)
        return self._articles

    @articles.setter
    def articles(self, v):
        return self._setvalue('_articles', v, 'articles')

    def _get_tags_mm_articles(self):
        if not self._tags_mm_articles:
           self._tags_mm_articles = tags_mm_articles(self) 
        return self._tags_mm_articles

    def __str__(self):
        if self.name is None:
            return ''
        else:
            return '#' + self.name

class tags_mm_articles(db.dbentities):
    def __init__(self, obj=None):
        super().__init__()

        if isinstance(obj, article):
            self._article = obj
        elif isinstance(obj, tag):
            self._tag = obj

        if obj and obj.id:
            if isinstance(obj, article):
                sql = 'select * from tags_mm_articles where articleid = %s'
            elif isinstance(obj, tag):
                sql = 'select * from tags_mm_articles where tagid = %s'

            args = obj.id.bytes,

            ress = self.query(sql, args)
            for res in ress:
                self += tag_mm_article(res)

    @property
    def _create(self):
        return """
        create table tags_mm_articles(
            id binary(16) primary key,
            tagid binary(16),
            articleid binary(16)
        )
        """

    def attach(self, es):
        isart = isinstance(es, articles)
        istag = isinstance(es, tags)

        for mm in self:
            for e in es:
                if mm.tagid == e.id:
                    break;
            else:
                mm.markfordeletion()

        for e in es:
            for mm in self:
                if mm.tagid == e.id:
                    break
            else:
                mm = tag_mm_article()

                mm.tagid      =  e.id  if  istag  else  self.tag.id
                mm.articleid  =  e.id  if  isart  else  self.article.id
                self += mm

    @property
    def _table(self):
        return 'tags_mm_articles'

    @property
    def article(self):
        return self._article

    @property
    def tag(self):
        return self._tag

class tag_mm_article(db.dbentity):
    def __init__(self, res=None):
        super().__init__()
        if res:
            row = list(res._row)
            self._id         =  uuid.UUID(bytes=row.pop(0))
            self._tagid      =  uuid.UUID(bytes=row.pop(0))
            self._articleid  =  uuid.UUID(bytes=row.pop(0))
            self._markold()
        else:
            self._id         =  None
            self._tagid      =  None
            self._articleid  =  None
            self._marknew()

    def _insert(self, cur=None):
        self._id = uuid.uuid4()

        args = (
            self.id.bytes, 
            self.tagid.bytes,
            self.articleid.bytes,
        )

        insert = """
        insert into tags_mm_articles
        values({})
        """.format(('%s, ' * len(args)).rstrip(', '))

        self.query(insert, args, cur)

    @property
    def brokenrules(self):
        brs = brokenrules()
        brs.demand(self, 'tagid', isfull=True, type=uuid.UUID)
        return brs

    def _delete(self, cur=None):
        sql = """
        delete from tags_mm_articles
        where id = %s
        """
        args = (
            self.id.bytes,
        )

        self.query(sql, args, cur)

    @property
    def _collection(self):
        return tags_mm_articles

    @property
    def tagid(self):
        return self._tagid

    @tagid.setter
    def tagid(self, v):
        return self._setvalue('_tagid', v, 'tagid')
    
    @property
    def articleid(self):
        return self._articleid

    @articleid.setter
    def articleid(self, v):
        return self._setvalue('_articleid', v, 'articleid')
    
