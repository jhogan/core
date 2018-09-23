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
from pdb import set_trace; B=set_trace
from pprint import pprint
from table import table
import builtins
import textwrap
from uuid import uuid4, UUID
import entities as entitiesmod
import sys
import db
from MySQLdb.constants.ER import BAD_TABLE_ERROR
import MySQLdb
from enum import Enum, unique

@unique
class types(Enum):
    str = 0
    int = 1
    pk  = 2
    fk  = 3

class undef:
    pass

class entities(entitiesmod.entities):
    # TODO Make atomic
    def save(self):
        for e in self:
            e.save()

    def append(self, obj, uniq=False, r=None):
        try:
            clscomp = self.orm.composites[0]
        except IndexError:
            # No composites fonud so just pass to super().append()
            pass
        else:
            try:
                objcomp = getattr(self, clscomp.__name__)
            except Exception as ex:
                # The self collection won't always have a reference to its
                # composite.  For example: when the collection is being
                # lazy-loaded.  The lazy-loading, however, will ensure the obj
                # being appended will get this reference.
                pass
            else:
                # Assign the composite reference of this collection to the obj
                # being appended, i.e.:
                #    obj.composite = self.composite
                setattr(obj, clscomp.__name__, objcomp)

        super().append(obj, uniq, r)
        return r
    
    def load(self, p1, p2):

        # TODO Implement full WHERE and ARGS
        # Assume an equality test (p1 == p2)
        where, args = p1 + ' =%s', (p2, )

        sql = 'select * from %s where %s;' % (self.orm.table, where)

        # TODO Make db.pool variant
        # TODO Make atomic
        pool = db.pool.getdefault()

        with pool.take() as conn:
            cur = conn.createcursor()
            cur.execute(sql, args)

        ress = db.dbresultset(cur)

        for res in ress:
            self += self.orm.entity(res)

class entitymeta(type):
    def __new__(cls, name, bases, body):
        # If name == 'entity', the `class entity` statement is being executed.
        if name != 'entity':
            ormmod = sys.modules['orm']
            orm_ = orm()
            orm_.mappings = mappings(orm=orm_)

            try:
                body['entities']
            except KeyError:
                for sub in orm_.getentitiessubclasses():

                    if sub.__name__   == name + 's' and \
                       sub.__module__ == body['__module__']:

                        body['entities'] = sub
                        break
                else:
                    msg =  "Entities class coudn't be found. "
                    msg += "Either specify one or define one with a predictable name"
                    raise AttributeError(msg)

            orm_.entities = body['entities']
            orm_.entities.orm = orm_

            del body['entities']

            try:
                orm_.table = body['table']
                del body['table']
            except KeyError:
                orm_.table = orm_.entities.__name__

            body['id'] = primarykeyfieldmapping()
            for k, v in body.items():
                if isinstance(v, mapping):
                    map = v
                elif hasattr(v, 'mro') and ormmod.entities in v.mro():
                    orm_.constituents.append(v.orm.entity)
                    map = entitiesmapping(k, v)
                else:
                    continue
               
                map._name = k
                orm_.mappings += map

            for map in orm_.mappings:
                del body[map.name]

            # Make sure the mappings are sorted in the order they are
            # instantiated
            orm_.mappings.sort('_ordinal')

            # The id will be the last elment, so pop it off and unshift so it's
            # always the first element
            orm_.mappings << orm_.mappings.pop('id')

            body['orm'] = orm_

        entity = super().__new__(cls, name, bases, body)

        if name != 'entity':
            orm_.entity = entity

            # For each of this class's constituents, add this class to their
            # composite's list
            for const in orm_.constituents:
                const.orm.composites.append(entity)

                # Insert foreignkeyfieldmapping into the constituent's mappings
                # collection right after the id
                const.orm.mappings.insertafter(0, foreignkeyfieldmapping(entity))


        return entity

class entity(entitiesmod.entity, metaclass=entitymeta):
    def __init__(self, o=None):
        self.orm = self.orm.clone()
        self.orm.instance = self

        self.onbeforesave = entitiesmod.event()
        self.onaftersave = entitiesmod.event()

        if o is None:
            self.orm.isnew = True
            self.orm.isdirty = False
            self.id = uuid4()
        else:
            if type(o) is UUID:
                id = o
                sql = 'select * from {} where id = %s'
                sql = sql.format(self.orm.table)

                args = id.bytes,

                # TODO Make db.pool variant
                # TODO Make atomic
                pool = db.pool.getdefault()

                with pool.take() as conn:
                    cur = conn.createcursor()
                    cur.execute(sql, args)

                ress = db.dbresultset(cur)
                ress.demandhasone()
                res = ress.first
            elif type(o) is db.dbresult:
                res = o
            else:
                raise ValueError()

            for map in self.orm.mappings:
                if not isinstance(map, fieldmapping):
                    continue

                map.value = res[map.name]


            self.orm.isnew = False
            self.orm.isdirty = False

        super().__init__()

        # Events
        self.onaftervaluechange  +=  self._self_onaftervaluechange

    def _self_onaftervaluechange(self, src, eargs):
        if not self.orm.isnew:
            self.orm.isdirty = True

    def __dir__(self):
        return super().__dir__() + [x.name for x in self.orm.mappings]

    def __setattr__(self, attr, v):
        # Need to handle 'orm' first, otherwise the code below that
        # calls self.orm won't work.
        if attr == 'orm':
            return object.__setattr__(self, attr, v)

        map = self.orm.mappings(attr)

        if map is None:
            return object.__setattr__(self, attr, v)
        else:
            # Call entity._setvalue to take advantage of its event raising
            # code. Pass in a custom setattr function for it to call. Use
            # underscores for the paramenters since we already have the values
            # it would pass in in this method's scope - execpt for the v
            # which, may have been processed (i.e, if it is a str, it will
            # have been strip()ed. 
            def setattr(_, __, v):
                map.value = v

            self._setvalue(attr, v, attr, setattr)

    @classmethod
    def reCREATE(cls, recursive=False):
        pool = db.pool.getdefault()

        with pool.take() as conn:
            cur = conn.createcursor()
            try:
                try:
                    cls.DROP(cur)
                except MySQLdb.OperationalError as ex:
                    try:
                        errno = ex.args[0]
                    except:
                        raise

                    if errno != BAD_TABLE_ERROR: # 1051
                        raise
                cls.CREATE(cur)

                if recursive:
                    for map in cls.orm.mappings:
                        if not isinstance(map, entitiesmapping):
                            continue
                        map.entities.orm.entity.reCREATE(recursive=True)
            except:
                conn.rollback()
            else:
                conn.commit()

    @classmethod
    def DROP(cls, cur=None):
        sql = 'drop table ' + cls.orm.table + ';'

        if cur:
            cur.execute(sql)
        else:
            pool = db.pool.getdefault()
            with pool.take() as conn:
                conn.query(sql)
    
    @classmethod
    def CREATE(cls, cur=None):
        sql = cls.orm.mappings.createtable

        if cur:
            cur.execute(sql)
        else:
            pool = db.pool.getdefault()
            with pool.take() as conn:
                conn.query(sql)

    def delete(self):
        self.orm.ismarkedfordeletion = True
        self.save()

    def save(self, cur=None):
        # TODO Add reconnect logic
        # TODO Ensure connection is active

        if not self.isvalid:
            raise db.brokenruleserror("Can't save invalid object" , self)

        if self.orm.ismarkedfordeletion:
            sql, args = self.orm.mappings.getdelete()
        elif self.orm.isnew:
            sql, args = self.orm.mappings.getinsert()
        elif self.orm.isdirty:
            sql, args = self.orm.mappings.getupdate()
        else:
            sql, args = (None,) * 2

        try:
            # If we cur wasn't passed in, get a conn from the default
            # pool and create a curson
            if not cur:
                pool = db.pool.getdefault()
                conn = pool.pull()
                cur = conn.createcursor()
            else:
                # cur was passed in. Set conn to None so indicate there is no
                # need to call conn.save() or conn.rollback() in this frame
                # (see below). The frame at the top of the stack will rollback
                # or commit the transaction.
                conn = None

            # Take snapshop of before state
            n, d, r = (self.orm.isnew,                  
                        self.orm.isdirty,             
                        self.orm.ismarkedfordeletion)

            if sql:
                # Issue the query

                # Raise event
                self.onbeforesave(self, self)

                cur.execute(sql, args)

                # Update new state
                self.orm.isnew = self.orm.ismarkedfordeletion
                self.orm.isdirty, self.orm.ismarkedfordeletion = (False,) * 2

                # Raise event
                self.onaftersave(self, self)
            else:
                # If there is no sql, then the entity isn't new, dirty or 
                # marked for deletion. In that case, don't save. However, 
                # allow any constituents to be saved.
                pass

            # For each of the constituent entities classes mapped to self,
            # set the foreignkeyfieldmapping to the id of self, i.e., give
            # the child objects the value of the parent id for their
            # foreign keys
            for map in self.orm.mappings:
                if type(map) is not entitiesmapping:
                    continue

                es = map.value

                # es is None if the constituent hasn't been loaded,
                # so conditionally save()
                if es:
                    # Take snapshot of states
                    sts = []
                    for e in es:
                        sts.append((e.orm.isnew,                  
                                    e.orm.isdirty,             
                                    e.orm.ismarkedfordeletion))

                    # Iterate over each entity and save them individually
                    for e in es:
                        
                        # Set the entity's FK to self.id value
                        for map in e.orm.mappings:
                            if type(map) is foreignkeyfieldmapping:
                                if map.entity is self.orm.entity:
                                    # Set map.value to self.id. But rather than
                                    # a direct assignment, 
                                    #     map.value = self.id
                                    # use setattr() to invoke the _setvalue
                                    # logic. This ensures that the proper
                                    # events get raised, but even more
                                    # importantly, it dirties e so e's FK will
                                    # be changed in the database.  This is
                                    # mainly for instances where the
                                    # constituent is being moved to a different
                                    # composite.
                                    setattr(e, map.name, self.id)
                                    break

                        # Call save(). If there is an Exception, restore state then
                        # re-raise
                        try:
                            e.save(cur)
                        except Exception as ex:
                            # Restore states
                            for st, e in zip(sts, es):
                                e.orm.isnew,   \
                                e.orm.isdirty, \
                                e.orm.ismarkedfordeletion = st

                            raise

        except Exception as ex:
            self.orm.isnew,   \
            self.orm.isdirty, \
            self.orm.ismarkedfordeletion = n, d, r

            if conn:
                conn.rollback()
            raise
        else:
            if conn:
                conn.commit()
        finally:
            if conn:
                cur.close()
                pool.push(conn)
        
    @property
    def brokenrules(self):
        brs = entitiesmod.brokenrules()
        for map in self.orm.mappings:
            if type(map) is fieldmapping:
                if map.type == types.str:
                    brs.demand(self, map.name, type=str)
                    if map.max is undef:
                        if map.value is not None:
                            brs.demand(self, map.name, max=255)
                    else:
                        brs.demand(self, map.name, max=map.max)

                    if map.full:
                        brs.demand(self, map.name, full=True)

            elif type(map) is entitiesmapping:
                es = map.value
                if es:
                    brs += es.brokenrules

        return brs

    def __getattribute__(self, attr):
        map = None

        if attr != 'orm' and self.orm.mappings:
            map = self.orm.mappings(attr)

        # Lazy-load constituent entities map
        if type(map) is entitiesmapping:
            if map.value is None:
                es = map.entities()
                if not self.orm.isnew:
                    for map1 in map.entities.orm.mappings:
                        if type(map1) is foreignkeyfieldmapping:
                            if map1.entity is self.orm.entity:
                                break
                    else:
                        raise ValueError('FK map not found for entity')

                    es.load(map1.name, self.id.bytes)

                    # Assign the composite reference to the constituent's
                    # elements:
                    #   i.e., art.presentations.first.artist = art
                    for e in es:
                        setattr(e, self.orm.entity.__name__, self)
                map.value = es

                # Assign the composite reference to the constituent
                #   i.e., art.presentations.artist = art
                setattr(map.value, self.orm.entity.__name__, self)

        if map is None:
            return object.__getattribute__(self, attr)

        return map.value

    def __str__(self):
        # TODO Write tests

        tbl = table()

        r = tbl.newrow()
        r.newfield('property')
        r.newfield('value')

        for map in self.orm.mappings:
            r = tbl.newrow()
            if type(map) in (primarykeyfieldmapping, foreignkeyfieldmapping):
                if type(map.value) is UUID:
                    v = map.value.hex[:7]
                else:
                    v = str(map.value)
            else:
                v = str(map.value)

            r.newfield(map.name)
            r.newfield(v)

        return str(tbl)

class mappings(entitiesmod.entities):
    def __init__(self, initial=None, orm=None):
        self._orm = orm
        super().__init__(initial)

    @property
    def orm(self):
        return self._orm

    @property
    def createtable(self):
        r = 'create table ' + self.orm.table + '(\n'
        i = 0

        for map in self:
            if not isinstance(map, fieldmapping):
                continue

            if i:
                r += ',\n'
            i += 1

            r += '    ' + map.name

            if type(map) is fieldmapping:
                if map.isstr:
                    # TODO: OPT: Shouldn't this be char(16) instead of varchar(16)
                    r += ' varchar(' + str(map.max) + ')'
            elif type(map) is primarykeyfieldmapping:
                r += ' binary(16) primary key'
            elif type(map) is foreignkeyfieldmapping:
                r += ' binary(16)'

        r += '\n);'
        return r


    def getinsert(self):

        tbl = self.orm.table

        placeholder = ''
        for map in self:
            if isinstance(map, fieldmapping):
                placeholder += '%s, '

        placeholder = placeholder.rstrip(', ')

        sql = 'insert into {} values({})'.format(tbl, placeholder)

        return sql, self._getargs()

    def getupdate(self):
        set = ''
        for map in self:
            if isinstance(map, fieldmapping):
                if isinstance(map, primarykeyfieldmapping):
                    id = map.value.bytes
                else:
                    set += '%s = %%s, ' % (map.name,)

        set = set[:-2]

        sql = """
        update {}
        set {}
        where id = %s;
        """.format(self.orm.table, set)

        args = self._getargs()

        # Move the id value from the bottom to the top
        args.append(args.pop(0))
        return sql, args

    def getdelete(self):
        sql = 'delete from {} where id = %s;'.format(self.orm.table)

        return sql, [self['id'].value.bytes]

    def _getargs(self):
        r = []
        for map in self:
            if isinstance(map, fieldmapping):
                if type(map) in (primarykeyfieldmapping, foreignkeyfieldmapping):
                    r.append(map.value.bytes)
                else:
                    r.append(map.value)
        return r

    def clone(self, orm_):
        r = mappings(orm=orm_)
        for map in self:
            r += map.clone()
        return r


class mapping(entitiesmod.entity):
    ordinal = 0

    def __init__(self, name=None):
        self._name = name
        mapping.ordinal += 1
        self._ordinal = mapping.ordinal

    @property
    def name(self):
        return self._name

    def __str__(self):
        r = '{}'

        r = r.format(self.name)

        return r
    
class entitiesmapping(mapping):
    def __init__(self, name, es):
        self.entities = es
        self._value = None
        super().__init__(name)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, v):
        self._setvalue('_value', v, 'value')

    def clone(self):
        return entitiesmapping(self.name, self.entities)

class fieldmapping(mapping):

    def __init__(self, type, default=undef, max=undef, full=undef, name=None):
        self._type = type
        self._value = undef
        self._default = default
        self._max = max
        self._full = full
        super().__init__(name)

    def clone(self):
        map = fieldmapping(
            self.type,
            self.default,
            self.max,
            self.full,
            self.name
        )

        map._value = self._value

        return map

    @property
    def isstr(self):
        return self.type == types.str

    @property
    def full(self):
        if self._full is undef:
            self._full = False
        
        return self._full

    @property
    def default(self):
        return self._default

    @property
    def max(self):
        if self.type is types.str:
            if self._max is undef:
                return 255
            else:
                return self._max

    @property
    def type(self):
        t = self._type
        if t in (str, types.str):
            self._type = types.str
        return self._type

    @property
    def value(self):
        if self._value is undef:
            if self.default is undef:
                if self.type == types.str:
                    return None
            else:
                return self.default
        return self._value

    @value.setter
    def value(self, v):
        self._value = v

class foreignkeyfieldmapping(fieldmapping):
    def __init__(self, e):
        self.entity = e
        self.value = None
        super().__init__(type=types.fk)

    @property
    def name(self):
        return self.entity.__name__ + 'id'

    def clone(self):
        return foreignkeyfieldmapping(self.entity)

    @property
    def value(self):
        if type(self._value) is bytes:
            self._value = UUID(bytes=self._value)
            
        return self._value

    @value.setter
    def value(self, v):
        self._value = v

class primarykeyfieldmapping(fieldmapping):
    def __init__(self):
        super().__init__(type=types.pk)

    @property
    def name(self):
        return 'id'

    def clone(self):
        return primarykeyfieldmapping()

    @property
    def value(self):
        if type(self._value) is bytes:
            self._value = UUID(bytes=self._value)
            
        return self._value

    @value.setter
    def value(self, v):
        self._value = v


class orm:
    def __init__(self):
        self.mappings = None
        self.isnew = False
        self.isdirty = False
        self.ismarkedfordeletion = False
        self.entities = None
        self.entity = None
        self.table = None
        self.composites = []
        self.constituents = []

    def clone(self):
        r = orm()

        props = (
            'isnew',       'isdirty',      'ismarkedfordeletion',
            'entity',      'entities',     'table',
            'composites',  'constituents',
        )

        for prop in props: 
            setattr(r, prop, getattr(self, prop))

        r.mappings = self.mappings.clone(r)

        return r

    @property
    def properties(self):
        return [x.name for x in self.mappings]

    @staticmethod
    def getentitiessubclasses(cls=entities):
        r = []

        for subclass in cls.__subclasses__():
            r.append(subclass)
            r.extend(orm.getentitiessubclasses(subclass))

        return r

class saveeventargs(entitiesmod.eventargs):
    def __init__(self, e):
        self.entity = e
