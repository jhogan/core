from pdb import set_trace; B=set_trace
import db
from entities import brokenrules, entity
import uuid
from binascii import a2b_hex
from datetime import datetime
from pprint import pprint
import diff
import re

class articlerevisions(db.dbentities):
    def __init__(self, id=None):
        super().__init__()
        if id:
            sql = """
            select *
            from articlerevisions
            where root_id = %s
            """
            ress = self.query(sql, (id.bytes,))
            for res in ress:
                self += articlerevision(res=res)

            for rev1 in self:
                for rev2 in self:
                    if rev2._parent_id == rev1.id:
                        rev2._parent = rev1
                        break

            for rev1 in self:
                if rev1.isroot:
                    for rev2 in self:
                        rev2._root = rev1
                # Get rid of parent_id. It's only temporarily used to
                # discover the parent object. Keeping it around may
                # lead to confusion later on.
                del rev1._parent_id 
                    
                    
    
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
            diff longtext
        )
        """

    @property
    def root(self):
        for rev in self:
            if not rev.parent:
                return rev

class articlerevision(db.dbentity):
    """ An abstract class for subtypes such as academic paper, essays,
    scientific paper, blog, encyclopedia article, marketing article, usenet
    article, spoken article, listicle, portrait, etc."""

    def __init__(self, parent=None, id=None, res=None):
        super().__init__();
        
        # TODO Only parent, id or res should be not None

        if id == None:
            self._id = None
            self._parent = parent
            self._authors = None
            self._created_at = None
            self._title = None
            self._excerpt = None
            self._status = None
            self._iscommentable = None
            self._body = None
            self._diff = None
            self._slug = None
            self._previous = None
            self._subsequent = None
            self._marknew()
        elif type(id) == uuid.UUID:
            sql = 'select * from articlerevisions where id = %s';
            v = self.query(sql, (id.bytes,))
            if v.hasone:
                ls = list(v.first)
            else:
                raise Exception('Record not found: ' + str(id))

            self._created_at = ls.pop()
            self._id         = uuid.UUID(bytes=ls.pop())

        if res != None:
            row = list(res._row)
            self._diff = diff.diff(row.pop())
            self._body = row.pop()
            self._create_at = row.pop()
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

    def _insert(self):
        insert = """
        insert into articlerevisions
        values(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        id = uuid.uuid4()
        diff = None if self.diff == None else str(self.diff)
        parent_id = self.parent.id.bytes if self.parent else None
        root_id = id.bytes if self.isroot else self.root.id.bytes
        self._created_at = datetime.now()
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
                diff)
        res = self.query(insert, args)
        self._id = id

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
    def authors(self):
        return self._authors

    @property
    def parent(self):
        return self._parent

    @property
    def created_at(self):
        return self._created_at

    @created_at.setter
    def created_at(self, v):
        return self._setvalue('_created_at', v, 'created_at')

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
    def body(self):
        return self._body

    @property
    def derivedbody(self):
        # TODO OPT This could be cached for performance 
        diffs = []
        rev = self
        while rev.diff:
            diffs.append(rev.diff)
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

class blogrevisions(articlerevisions):
    pass

class blogrevision(articlerevision):
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

        if id == None:
            self._revisions = blogrevisions()
            self._body = None
            self._title = None
            self._excerpt = None
            self._status = None
            self._iscommentable = None
            self._slug = None
        else:
            self._revisions = blogrevisions(id)
            self._body = None

        self._id = id

    @property
    def id(self):
        return self._id

    @property
    def body(self):
        if not self._body:
            for rev in self._revisions:
                if rev.body:
                    self._body = rev.body
                else:
                    self._body = rev.diff.applyto(self._body)

        return self._body

    @body.setter
    def body(self, v):
        return self._setvalue('_body', v, 'body')

    @property
    def created_at(self):
        return self._revisions.root.created_at

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, v):
        return self._setvalue('_title', v, 'title')

    @property
    def excerpt(self):
        return self._excerpt

    @excerpt.setter
    def excerpt(self, v):
        return self._setvalue('_excerpt', v, 'excerpt')

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
        if not self._slug:
            return re.sub(r'\W+', '-', self.title).strip('-').lower()
            # TODO: Ensure slug is unique in database
        return self._slug

    @slug.setter
    def slug(self, v):
        self._slug = None
        return self._setvalue('_slug', v, 'slug')

    def save(self):
        # TODO Don't save titles, excerpts, etc. if they are repeats of
        # previous revisions.
        revs = self._revisions

        rev = revs.create()

        if rev.parent:
            rev.diff = diff.diff(rev.parent.derivedbody, self.body)
            rev.body = None
            self.body = None
        else:
            rev.body = self.body

        rev.title = self.title
        rev.excerpt = self.excerpt
        rev.status = self.status
        rev.iscommentable = self.iscommentable
        rev.slug = self.slug

        rev.save()

        self._id = rev.root.id

class blogpost(article):
    pass
