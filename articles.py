from pdb import set_trace; B=set_trace
import db
from entities import brokenrules, entity
import uuid
from binascii import a2b_hex
from datetime import datetime

class articlerevisions(db.dbentities):
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
            created_at datetime
        )
        """

class articlerevision(db.dbentity):
    """ An abstract class for subtypes such as academic paper, essays,
    scientific paper, blog, encyclopedia article, marketing article, usenet
    article, spoken article, listicle, portrait, etc."""

    def __init__(self, id=None):
        super().__init__();

        if id == None:
            self._id = None
            self._authors = None
            self._created_at = None
            self._title = None
            self._body = None
            self._excerpt = None
            self._status = None
            self._iscommentable = None
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

            B()
            self._created_at = ls.pop()
            self._id         = uuid.UUID(bytes=ls.pop())

    def _insert(self):
        insert = """
        insert into articlerevisions
        values(%s, %s)
        """
        # id = uuid.uuid4().hex
        # id = a2b_hex(id)
        id = uuid.uuid4()
        self._created_at = datetime.now()
        args = (id.bytes, self._created_at)
        res = self.query(insert, args)
        self._id = id

    @property
    def subsequent(self):
        return self._subsequent

    @property
    def previous(self):
        return self._previous

    @property
    def authors(self):
        return self._authors

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
    def body(self):
        return self._body

    @body.setter
    def body(self, v):
        return self._setvalue('_body', v, 'body')

    @property
    def excerpt(self):
        return self._excerpt

    @excerpt.setter
    def excerpt(self, v):
        return self._setvalue('_excerpt', v, 'excerpt')

    @property
    def status(self):
        """ Similar to wp_post.post_status. See
        https://codex.wordpress.org/Post_Status"""
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

