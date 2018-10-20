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
    def __init__(self, initial=None):
        self.orm = self.orm.clone()
        super().__init__(initial)

    # TODO Make atomic
    def save(self):
        for e in self:
            e.save()

    def append(self, obj, uniq=False, r=None):
        try:
            clscomp = self.orm.composites[0]
        except IndexError:
            # No composites found so just pass to super().append()
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
        if hasattr(p2, '__iter__') and type(p2) is not str:
            # Perform test using the *in* operator (p1 in (p2))
            if not len(p2):
                return
            where = '{} in ({})'.format(p1, ', '.join(('%s',) * len(p2)))
            args = p2
        else:
            # Assume an equality test (p1 == p2)
            if isinstance(p2, UUID):
                p2 = p2.bytes

            where, args = p1 + ' = %s', (p2, )

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

    def _getbrokenrules(self, es):
        brs = entitiesmod.brokenrules()
        for e in self:
            brs += e._getbrokenrules(es)
        return brs

    def _self_onremove(self, src, eargs):
        self.orm.trash += eargs.entity
        self.orm.trash.last.orm.ismarkedfordeletion = True
        super()._self_onremove(src, eargs)

class entitymeta(type):
    def __new__(cls, name, bases, body):
        # If name == 'entity', the `class entity` statement is being executed.
        if name not in ('entity', 'association'):
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

                if k.startswith('__'):
                    continue
                
                if isinstance(v, mapping):
                    map = v
                elif hasattr(v, 'mro') and ormmod.entities in v.mro():

                    # TODO This temporary check was put in place where name
                    # is 'artifact' and v is the artist class. THe artist class
                    # statement hasn't been run yet.
                    # the 'artifact' cl
                    # if hasattr(v, 'orm'):
                        # orm_.constituents.append(v.orm.entity)
                    #else:
                    #   pass
                    map = entitiesmapping(k, v)
                elif type(k) is str:
                    # TODO I don't think this line ever executes. Plus, isn't k
                    # always going to be a str.
                    map = entitymapping(k, v)
                else:
                    continue
               
                map._name = k
                orm_.mappings += map

            for map in orm_.mappings:
                try:
                    del body[map.name]
                except KeyError:
                    # The orm_.mappings.__iter__ adds new mappings which won't
                    # be in body, so ignore KeyErrors
                    pass

            body['orm'] = orm_

        entity = super().__new__(cls, name, bases, body)

        if name not in ('entity', 'association'):
            orm_.entity = entity

            # Since a new entity has been created, invalidate the derived cache
            # of each mappings collection's object.  They must be recomputed
            # since they are based on the existing entity object available.
            for e in orm.getentitys():
                e.orm.mappings._populated = False


            #for const in orm_.constituents:
                #const.orm.composites.append(entity)

                #const.orm.mappings += entitymapping(name, entity)

                # Insert foreignkeyfieldmapping into the constituent's mappings
                # collection right after the id
                #const.orm.mappings.insertafter(0, foreignkeyfieldmapping(entity))

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

            if type(map) is entitymapping:
                for map in self.orm.mappings.foreignkeymappings:
                    if map.entity is v.orm.entity:
                        self._setvalue(map.name, v.id, map.name, setattr)
                        break;

    @classmethod
    def reCREATE(cls, cur=None, recursive=False, clss=None):

        # Prevent infinite recursion
        if clss is None:
            clss = []
        else:
            if cls in clss:
                return
        clss += [cls]

        try: 
            if cur:
                conn = None
            else:
                pool = db.pool.getdefault()
                conn = pool.pull()
                cur = conn.createcursor()

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
                for map in cls.orm.mappings.entitiesmappings:
                    map.entities.orm.entity.reCREATE(cur, True, clss)

                for ass in cls.orm.associations:
                    ass.entity.reCREATE(cur, True, clss)
                            
        except:
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

    def save(self, cur=None, follow                  =True, 
                             followentitymapping     =True, 
                             followentitiesmapping   =True, 
                             followassociationmapping=True):

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
            for map in self.orm.mappings if follow else tuple():

                if followentitymapping and type(map) is entitymapping:
                    # TODO: Calling map.value currenly loads the constituent.
                    # We probably shouldn't load this here unless the FK has
                    # changed.

                    # Call the entity constituent's save method. Setting
                    # followentitiesmapping to false here prevents it's
                    # child/entitiesmapping constituents from being saved. This
                    # prevents infinite recursion.
                    map.value.save(cur, followentitiesmapping=False)

                if followentitiesmapping and type(map) is entitiesmapping:

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
                                        # Set map.value to self.id. But rather
                                        # than a direct assignment, map.value =
                                        # self.id use setattr() to invoke the
                                        # _setvalue logic. This ensures that
                                        # the proper events get raised, but
                                        # even more importantly, it dirties e
                                        # so e's FK will be changed in the
                                        # database.  This is mainly for
                                        # instances where the constituent is
                                        # being moved to a different composite.
                                        setattr(e, map.name, self.id)
                                        break

                            # Call save(). If there is an Exception, restore state then
                            # re-raise
                            try:
                                e.save(cur)

                            # TODO Don't need the 'as ex' here
                            except Exception as ex:
                                # Restore states
                                for st, e in zip(sts, es):
                                    e.orm.isnew,   \
                                    e.orm.isdirty, \
                                    e.orm.ismarkedfordeletion = st
                                raise

                if followassociationmapping and type(map) is associationsmapping:
                    asses = map.value
                    for ass in asses:
                        ass.save(cur, follow=False)
                        for map in ass.orm.mappings.entitymappings:
                            if map.value is not self:
                                map.value.save(cur, followassociationmapping=False)

                    for ass in asses.orm.trash:
                        st = ass.orm.persistencestate
                        try:
                            B()
                            ass.save(cur)
                        except Exception:
                            ass.orm.persistencestate = st
                            raise

                    asses.orm.trash.clear()


        # TODO Do we need the 'as ex'
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
        return self._getbrokenrules()

    def _getbrokenrules(self, visited=None):
        brs = entitiesmod.brokenrules()

        # This "visited" logic prevents infinite recursion and duplicated
        # broken rules.
        visited = [] if visited is None else visited
        if self in visited:
            return brs
        else:
            visited += self,

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

            elif type(map) is foreignkeyfieldmapping:
                if type(map.value) is not UUID:
                    msg = '"%s" has an empty value for the foreign key "%s"'
                    msg %= self.__class__.__name__, map.name
                    brs += entitiesmod.brokenrule(msg, map.name, 'full')

            elif type(map) is entitiesmapping:
                # Currently, map.value will not load the entities on invocation
                # so we get None for es. This is good because we don't want to
                # needlessly load an object to see if it has broken rules.
                # However, if this changes, we will want to make sure that we
                # don't needlessy load this. This could lead to infinite
                # h (see it_entity_constituents_break_entity)
                es = map.value
                if es:
                    brs += es._getbrokenrules(visited)

            elif type(map) is entitymapping:
                v = map.value
                if v:
                    brs += v._getbrokenrules(visited)

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
                    # elements
                    #   i.e., art.presentations.first.artist = art
                    for e in es:
                        setattr(e, self.orm.entity.__name__, self)
                map.value = es

                # Assign the composite reference to the constituent
                #   i.e., art.presentations.artist = art
                setattr(map.value, self.orm.entity.__name__, self)

        elif type(map) is associationsmapping:
            map.composite = self
        elif map is None:
            if attr != 'orm':
                for map in self.orm.mappings.associationsmappings:
                    for map1 in map.associations.orm.mappings.entitymappings:
                        if map1.entity.orm.entities.__name__ == attr:
                            asses = getattr(self, map.name)
                            return getattr(asses, attr)

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
        super().__init__(initial)
        self._orm = orm
        self._populated = False
        self._populating = False
        self.oncountchange += self._self_oncountchange

    def _self_oncountchange(self, src, eargs):
        self._populated = False

    def __getitem__(self, key):
        self._populate()
        return super().__getitem__(key)

    def __iter__(self):
        self._populate()
        return super().__iter__()

    def _populate(self):
        if not self._populated and not self._populating:
            self._populating = True

            self.clear(derived=True)

            maps = []

            for map in self.entitymappings:
                maps += [foreignkeyfieldmapping(map.entity, derived=True)]

            for e in orm.getentitys():
                if e is self.orm.entity:
                    continue
                for map in e.orm.mappings.entitiesmappings:
                    if map.entities is self.orm.entities:
                        maps += [entitymapping(e.__name__, e, derived=True)]
                        maps += [foreignkeyfieldmapping(e, derived=True)]

            for ass in orm.getassociations():
                for map in ass.orm.mappings.entitymappings:
                    if map.entity is self.orm.entity:
                        asses = ass.orm.entities
                        maps += [associationsmapping(asses.__name__, asses, derived=True)]
                        break

            for map in maps:
                self += map
            
            for map in self:
                map.orm = self.orm
                    
            self.sort()
            self._populating = False

        self._populated = True

    def clear(self, derived=False):
        if derived:
            for map in [x for x in self if x.derived]:
                self.remove(map)
        else:
            super().clear()

    def sort(self):
        # Make sure the mappings are sorted in the order they are
        # instantiated
        super().sort('_ordinal')

        # Ensure the id is the first element
        self << self.pop('id')

        fkmaps = list(self.foreignkeymappings)

        for map in fkmaps:
            self.remove(map)
            self.insertafter(0, map)

    @property
    def foreignkeymappings(self):
        return self._generate(type=foreignkeyfieldmapping)

    @property
    def entitiesmappings(self):
        return self._generate(type=entitiesmapping)

    @property
    def entitymappings(self):
        return self._generate(type=entitymapping)

    @property
    def associationsmappings(self):
        return self._generate(type=associationsmapping)

    def _generate(self, type):
        for map in self:
            if builtins.type(map) is type:
                yield map
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

    def __init__(self, name, derived=False):
        # TODO I don't think self.orm is ever used so we can delete this line
        self.orm = None
        self._name = name
        mapping.ordinal += 1
        self._ordinal = mapping.ordinal
        self.derived = derived

    @property
    def name(self):
        return self._name

    def __str__(self):
        r = '{}'

        r = r.format(self.name)

        return r

    def clone(self):
        raise NotImplementedError('Abstract')
    
class associationsmapping(mapping):
    def __init__(self, name, ass, derived=False):
        self.associations = ass
        self._value = None
        self._composite = None
        super().__init__(name, derived)

    @property
    def composite(self):
        return self._composite

    @composite.setter
    def composite(self, v):
        self._composite = v
        
    @property
    def value(self):
        if not self._value:
            for map in self.associations.orm.mappings.foreignkeymappings:
                if map.entity is type(self.composite):
                    break
            else:
                raise ValueError('FK not found')

            asses = self.associations()
            asses.composite = self.composite
            asses.load(map.name, self.composite.id)
            self.value = asses
        return self._value

    @value.setter
    def value(self, v):
        self._setvalue('_value', v, 'value')

    def clone(self):
        return associationsmapping(self.name, self.associations, self.derived)

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

class entitymapping(mapping):
    def __init__(self, name, e, derived=False):
        self.entity = e
        self._value = None
        super().__init__(name, derived)

    @property
    def value(self):
        if not self._value:
            for map in self.orm.mappings:
                if type(map) is foreignkeyfieldmapping:
                    if map.entity is self.entity:
                        if map.value is not undef:
                            self._value = self.entity(map.value)
        return self._value

    @value.setter
    def value(self, v):
        self._setvalue('_value', v, 'value')

    def clone(self):
        return entitymapping(self.name, self.entity, derived=self.derived)

class fieldmapping(mapping):

    def __init__(self, type, default=undef, max=undef, full=undef, name=None, derived=False):
        self._type = type
        self._value = undef
        self._default = default
        self._max = max
        self._full = full
        super().__init__(name, derived)

    def clone(self):
        map = fieldmapping(
            self.type,
            self.default,
            self.max,
            self.full,
            self.name,
            self.derived
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
    def __init__(self, e, derived=False):
        self.entity = e
        self.value = None
        super().__init__(type=types.fk, derived=derived)

    @property
    def name(self):
        return self.entity.__name__ + 'id'

    def clone(self):
        return foreignkeyfieldmapping(self.entity, self.derived)

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

class ormclasseswrapper(entitiesmod.entities):
    pass

class ormclasswrapper(entitiesmod.entity):
    def __init__(self, entity):
        self.entity = entity
        super().__init__()

    def __str__(self):
        return str(self.entity)

    def __repr__(self):
        return repr(self.entity)

    @property
    def orm(self):
        return self.entity.orm

    @property
    def name(self):
        return self.entity.__name__

class composites(ormclasseswrapper):
    pass

class composite(ormclasswrapper):
    pass

class constituents(ormclasseswrapper):
    pass

class constituent(ormclasswrapper):
    pass

class orm:
    def __init__(self):
        self.mappings = None
        self.isnew = False
        self.isdirty = False
        self.ismarkedfordeletion = False
        self.entities = None
        self.entity = None
        self.table = None
        self._composits = None
        self._constituents = None
        self._associations = None
        self._trash = None

    def clone(self):
        r = orm()

        props = (
            'isnew',       'isdirty',      'ismarkedfordeletion',
            'entity',      'entities',     'table'
        )

        for prop in props: 
            setattr(r, prop, getattr(self, prop))

        r.mappings = self.mappings.clone(r)

        return r

    @property
    def persistencestate(self):
        return self.isnew, self.isdirty, self.ismarkedfordeletion

    @persistencestate.setter
    def persistencestate(self, v):
        self.isnew, self.isdirty, self.ismarkedfordeletion = v

    @property
    def trash(self):
        if not self._trash:
            self._trash = self.entities()
        return self._trash

    @trash.setter
    def trash(self, v):
        self._trash = v

    @property
    def properties(self):
        return [x.name for x in self.mappings]

    # TODO Rename to getsubclasses(of):
    @staticmethod
    def getentitiessubclasses(cls=entities):
        r = []

        for subclass in cls.__subclasses__():
            if subclass not in (associations, association):
                r.append(subclass)
            r.extend(orm.getentitiessubclasses(subclass))

        return r
    
    @staticmethod
    def getsubclasses(of):
        r = []

        for sub in of.__subclasses__():
            r.append(sub)
            r.extend(orm.getsubclasses(sub))

        return r
        
    @staticmethod
    def getassociations():
        return orm.getsubclasses(of=association)

    @staticmethod
    def getentitys():
        r = []
        for e in orm.getsubclasses(of=entity):
            if association not in e.mro():
                if e is not association:
                    r += [e]
        return r

    @property
    def associations(self):
        if not self._associations:
            self._associations = ormclasseswrapper()
            for ass in orm.getassociations():
                # TODO No need for enumerate() here
                maps = list(ass.orm.mappings.entitymappings)
                for i, map in enumerate(maps):
                    if map.entity is self.entity:
                        self._associations += ormclasswrapper(ass)

        return self._associations
            
    @property
    def composites(self):
        if not self._composits:
            self._composits = composites()
            for sub in self.getentitiessubclasses(entity):
                for map in sub.orm.mappings.entitiesmappings:
                    if map.entities.orm.entity is self.entity:
                        self._composits += composite(sub)
                        break

            for ass in self.getassociations():
                maps = list(ass.orm.mappings.entitymappings)
                for i, map in enumerate(maps):
                    if map.entity is self.entity:
                        e = maps[int(not bool(i))].entity
                        self._composits += composite(e)
                        break
                else:
                    continue
                break

        return self._composits

    @property
    def constituents(self):
        if not self._constituents:
            self._constituents = constituents()
            for map in self.mappings.entitiesmappings:
                e = map.entities.orm.entity
                self._constituents += constituent(e)

            for ass in self.getassociations():
                maps = list(ass.orm.mappings.entitymappings)
                for i, map in enumerate(maps):
                    if map.entity is self.entity:
                        e = maps[int(not bool(i))].entity
                        self._constituents += constituent(e)
                        break
                else:
                    continue
                break
        return self._constituents

class saveeventargs(entitiesmod.eventargs):
    def __init__(self, e):
        self.entity = e

class associations(entities):
    def __init__(self, initial=None):
        self.composite = None
        self._constituents = {}
        super().__init__(initial)

    def append(self, obj, uniq=False, r=None):
        if isinstance(obj, association):
            for map in obj.orm.mappings.entitymappings:
                # TODO We probably should be using the associations (self) mappings
                # collection to test the composites names. The name that matters is
                # on the LHS of the map when being defined in the association class.
                if map.name == type(self.composite).__name__:
                    setattr(obj, map.name, self.composite)
                    break;
            
        super().append(obj, uniq, r)
        return r

    def entities_onadd(self, src, eargs):
        ass = None
        for map in self.orm.mappings.entitymappings:
            if map.entity is type(eargs.entity):
                for ass in self:
                    if getattr(ass, map.name) is eargs.entity:
                        # eargs.entity already exists as a constitutent entity
                        # in this collection of associations. There is no need
                        # to add it again.
                        return

                ass = self.orm.entity()
                setattr(ass, map.name, eargs.entity)
            if map.entity is type(self.composite):
                compmap = map
        
        setattr(ass, compmap.name, self.composite)
        self += ass

    def entities_onremove(self, src, eargs):
        for map in self.orm.mappings.entitymappings:
            if map.entity is type(eargs.entity):
                for ass in self:
                    if getattr(ass, map.name) is eargs.entity:
                        break
                else:
                    continue
                break
        else:
            return

        self.remove(ass)

    def __getattr__(self, attr):
        # TODO Use the mappings collection to get __name__'s value.
        if attr == type(self.composite).__name__:
            return self.composite

        try:
            return self._constituents[attr]
        except KeyError:
            for map in self.orm.mappings.entitymappings:
                es = map.entity.orm.entities
                if es.__name__ == attr:
                    es = es()
                    es.onadd    += self.entities_onadd
                    es.onremove += self.entities_onremove
                    self._constituents[attr] = es
                    break
            else:
                raise AttributeError('Entity not found')

            for ass in self:
                es += getattr(ass, map.name)

        return self._constituents[attr]

    
class association(entity):
    @classmethod
    def reCREATE(cls, cur, recursive=False, clss=None):
        for map in cls.orm.mappings.entitymappings:
            map.entity.reCREATE(cur, recursive, clss)

        super().reCREATE(cur, recursive, clss)

