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
import re
import primative
import dateutil
import decimal
from datetime import datetime


@unique
class types(Enum):
    pk        =  0
    fk        =  1
    str       =  2
    int       =  3
    datetime  =  4
    bool      =  5
    float     =  6
    decimal   =  7
    bytes     =  8

class undef:
    pass

class entities(entitiesmod.entities):
    re_alphanum_ = re.compile('^[A-Za-z_]+$')

    def __init__(self, initial=None, _p2=None, *args, **kwargs):
        self.orm = self.orm.clone()
        self.orm.instance = self

        self.onbeforereconnect  =  entitiesmod.event()
        self.onafterreconnect   =  entitiesmod.event()

        load = type(initial) is str
        load = load or (initial is None and (_p2 or args or kwargs))
        if load:
            super().__init__()
            _p1 = '' if initial == None else initial
            self.load(_p1, _p2, *args, **kwargs)
            return

        super().__init__(initial=initial)

    def __getitem__(self, key):
        r = super().__getitem__(key)
        if hasattr(r, '__iter__'):
            return type(self)(initial=r)
        return r

    def sort(self, key=None, reverse=False):
        key = 'id' if key is None else key
        super().sort(key, reverse)

    def sorted(self, key=None, reverse=False):
        key = 'id' if key is None else key
        return super().sorted(key, reverse)
    
    def save(self, *es):
        exec = db.executioner(self._save)
        exec.execute(es)

    def _save(self, cur, es=None):
        for e in self:
            e._save(cur)

        for e in self.orm.trash:
            e._save(cur)

        if es:
            for e in es:
                e._save(cur)

    def delete(self):
        for e in self:
            e.delete()
        
    def give(self, es):
        sts = self.orm.persistencestates
        super().give(es)

        # super().give(es) will mark the entities for deletion
        # (ismarkedfordeletion) since it removes entities from collections.
        # However, giving an entity to another collection is a matter of
        # updating its foreign key/composite. So restore the original
        # persistencestates of the entities then make sure they are all still
        # dirty (isdirty). This will keep them from being deleted unless that
        # had previously been explitly marked for deletion.

        es.orm.persistencestates = sts
        for e in es:
            e.orm.isdirty = True

    def append(self, obj, uniq=False, r=None):
        if isinstance(obj, entities):
            for e in obj:
                self.append(e, r=r)
            return

        for clscomp in self.orm.composites:
            try:
                objcomp = getattr(self, clscomp.__name__)

            except Exception as ex:
                # The self collection won't always have a reference to its
                # composite.  For example: when the collection is being
                # lazy-loaded.  The lazy-loading, however, will ensure the obj
                # being appended will get this reference.
                continue
            else:
                # Assign the composite reference of this collection to the obj
                # being appended, i.e.:
                #    obj.composite = self.composite
                setattr(obj, clscomp.__name__, objcomp)

        super().append(obj, uniq, r)
        return r

    def load(self, _p1='', _p2=None, *args, **kwargs):
        # TODO: Use full-text index when available
        p1, p2 = _p1, _p2

        if p2 is None and p1 != '':
            raise ValueError('Missing arguments collection')

        args = list(args)
        for k, v in kwargs.items():
            if p1: 
                p1 += ' and '
            p1 += '%s = %%s' % k
            args.append(v)

        p2isscaler = p2isiter = False

        if p2 is not None:
            if type(p2) is not str and hasattr(p2, '__iter__'):
                p2isiter = True
            else:
                p2isscaler = True

        if p2 is not None:
            if p2isscaler:
                if self.re_alphanum_.match(p1):
                    # If p1 looks like a simple column name (alphanums,
                    # underscores, no operators) assume the user is doing a
                    # simple equailty test (p1 == p2)
                    p1 += ' = %s'
                args = [p2] + args
            else: # tuple, list, etc
                args = list(p2) + args

        args = [x.bytes if type(x) is UUID else x for x in args]

        p1 = orm.introduce(p1, args)

        sql = 'SELECT * FROM %s WHERE %s;' % (self.orm.table, p1)

        ress = None
        def exec(cur):
            nonlocal ress
            cur.execute(sql, args)
            ress = db.dbresultset(cur)

        exec = db.executioner(exec)

        exec.onbeforereconnect += \
            lambda src, eargs: self.onbeforereconnect(src, eargs)
        exec.onafterreconnect  += \
            lambda src, eargs: self.onafterreconnect(src, eargs)

        exec.execute()

        for res in ress:
            e = self.orm.entity(res)
            self += e
            eargs = db.operationeventargs(e, 'retrieve', sql, args)
            e.onafterload(self, eargs)
            e.orm.persistencestate = (False,) * 3

    def _getbrokenrules(self, es=None, followentitymapping=True):
        brs = entitiesmod.brokenrules()
        for e in self:
            brs += e._getbrokenrules(es, followentitymapping=followentitymapping)
        return brs

    def _self_onremove(self, src, eargs):
        self.orm.trash += eargs.entity
        self.orm.trash.last.orm.ismarkedfordeletion = True
        super()._self_onremove(src, eargs)
                    
    def getindex(self, e):
        if isinstance(e, entity):
            for ix, e1 in enumerate(self):
                if e.id == e1.id: return ix
            e, id = e.orm.entity.__name__, e.id
            raise ValueError("%s[%s] is not in the collection" % (e, id))

        super().getindex(e)

    def __repr__(self):
        hdr = '%s object at %s count: %s\n' % (type(self), 
                                               hex(id(self)), 
                                               self.count)

        tbl = table()
        r = tbl.newrow()
        r.newfield('Address')
        r.newfield('ID')
        r.newfield('Broken Rules')

        for e in self:
            r = tbl.newrow()
            r.newfield(hex(id(e)))
            r.newfield(str(e))
            b = ''
            for br in e.brokenrules:
                b += '%s:%s ' % (br.property, br.type)
            r.newfield(b)

        return '%s\n%s' % (hdr, tbl)

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
                for sub in orm_.getsubclasses(of=entities):

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
            body['createdat'] = fieldmapping(datetime)
            body['updatedat'] = fieldmapping(datetime)

            for k, v in body.items():

                if k.startswith('__'):
                    continue
                
                if isinstance(v, mapping):
                    map = v
                elif hasattr(v, 'mro'):
                    mro = v.mro()
                    if ormmod.entities in mro:
                        map = entitiesmapping(k, v)
                    elif ormmod.entity in mro:
                        map = entitymapping(k, v)
                    else:
                        raise ValueError()
                else:
                    if type(v) is ormmod.attr.wrap:
                        map = v.mapping
                    else:
                        continue
               
                map._name = k
                orm_.mappings += map

            for map in orm_.mappings:
                try:
                    prop = body[map.name]
                    if type(prop) is ormmod.attr.wrap:
                        #body[map.name] = prop.property
                            
                        body[map.name] = prop
                    else:
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

        return entity

class entity(entitiesmod.entity, metaclass=entitymeta):
    def __init__(self, o=None):
        self.orm = self.orm.clone()
        self.orm.instance = self

        self.onbeforesave       =  entitiesmod.event()
        self.onaftersave        =  entitiesmod.event()
        self.onafterload        =  entitiesmod.event()
        self.onbeforereconnect  =  entitiesmod.event()
        self.onafterreconnect   =  entitiesmod.event()

        self.onaftersave       +=  self._self_onaftersave
        self.onafterload       +=  self._self_onafterload
        self.onafterreconnect  +=  self._self_onafterreconnect

        if o is None:
            self.orm.isnew = True
            self.orm.isdirty = False
            self.id = uuid4()
        else:
            if type(o) is UUID:
                res = self._load(o)
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

        # Post super().__init__() events
        self.onaftervaluechange  +=  self._self_onaftervaluechange

    def __getitem__(self, args):
        if type(args) is str:
            try:
                return getattr(self, args)
            except AttributeError as ex:
                raise IndexError(str(ex))

        vals = []

        for arg in args:
            vals.append(self[arg])

        return tuple(vals)

    def __call__(self, args):
        try:
            return self[args]
        except IndexError:
            return None

    def __setitem__(self, k, v):
        map = self.orm.mappings(k)
        if map is None:
           super = self.orm.super
           if super:
               map = super.orm.mappings[k]
           else:
               raise IndexError("Map index doesn't exist: %s" % (k,))
        
        map.value = v

    def _load(self, id):
        sql = 'SELECT * FROM {} WHERE id = _binary %s'
        sql = sql.format(self.orm.table)

        args = id.bytes,

        ress = None
        def exec(cur):
            nonlocal ress
            cur.execute(sql, args)
            ress = db.dbresultset(cur)

        exec = db.executioner(exec)

        exec.onbeforereconnect += \
            lambda src, eargs: self.onbeforereconnect(src, eargs)
        exec.onafterreconnect  += \
            lambda src, eargs: self.onafterreconnect(src, eargs)

        exec.execute()

        ress.demandhasone()
        res = ress.first

        eargs = db.operationeventargs(self, 'retrieve', sql, args)
        self.onafterload(self, eargs)

        return res
    
    def _self_onafterload(self, src, eargs):
        self._add2chronicler(eargs)

    def _self_onaftersave(self, src, eargs):
        self._add2chronicler(eargs)

    def _self_onafterreconnect(self, src, eargs):
        self._add2chronicler(eargs)

    def _add2chronicler(self, eargs):
        chron = db.chronicler.getinstance()
        chron += db.chronicle(eargs.entity, eargs.op, eargs.sql, eargs.args)

    def _self_onaftervaluechange(self, src, eargs):
        if not self.orm.isnew:
            self.orm.isdirty = True

    def __dir__(self):
        ls = super().__dir__() + self.orm.properties

        # Remove duplicates. If an entity has an explicit attribute, the name
        # of the attribute will come in from the call to super().__dir__()
        # while the name of its associated map will come in through
        # self.orm.properties
        return list(set(ls))

    def __setattr__(self, attr, v, cmp=True):
        # Need to handle 'orm' first, otherwise the code below that
        # calls self.orm won't work.
        
        if attr == 'orm':
            return object.__setattr__(self, attr, v)

        map = self.orm.mappings(attr)

        if map is None:
            super = self.orm.super
            if super and super.orm.mappings(attr):
                super.__setattr__(attr, v, cmp)
            else:
                return object.__setattr__(self, attr, v)
        else:
            # Call entity._setvalue to take advantage of its event raising
            # code. Pass in a custom setattr function for it to call. Use
            # underscores for the paramenters since we already have the values
            # it would pass in in this method's scope - execpt for the v
            # which, may have been processed (i.e, if it is a str, it will
            # have been strip()ed. 
            def setattr0(_, __, v):
                map.value = v

            self._setvalue(attr, v, attr, setattr0, cmp=cmp)

            if type(map) is entitymapping:
                e = v.orm.entity
                while True:
                    for map in self.orm.mappings.foreignkeymappings:
                        if map.entity is e:
                            self._setvalue(map.name, v.id, map.name, setattr0, cmp=cmp)
                            break;
                    else:
                        e = e.orm.super
                        continue
                    break

                # If self is a subentity (i.e., concert), we will want to set
                # the superentity's (i.e, presentation) composite map to it's
                # composite class (i.e., artist) value. 
                selfsuper = self.orm.super
                attrsuper = self.orm.mappings(attr).value.orm.super

                if selfsuper and attrsuper:
                    maps = selfsuper.orm.mappings
                    attr = maps(attrsuper.__class__.__name__).name
                    setattr(selfsuper, attr, attrsuper)

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
                # TODO Use executioner
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

                for sub in cls.orm.subclasses:
                    sub.reCREATE(cur)
                            
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
        # TODO Use executioner
        sql = 'drop table ' + cls.orm.table + ';'

        if cur:
            cur.execute(sql)
        else:
            pool = db.pool.getdefault()
            with pool.take() as conn:
                conn.query(sql)
    
    @classmethod
    def CREATE(cls, cur=None):
        # TODO Use executioner
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

    def save(self, *es):
        # Create a callable to call self._save(cur) and the _save(cur)
        # methods on earch of the objects in *es.
        def save(cur):
            self._save(cur)
            for e in es:
                e._save(cur)

        # Create an executioner object with the above save() callable
        exec = db.executioner(save)

        # Register reconnect events of then executioner so they can be re-raised
        exec.onbeforereconnect += \
            lambda src, eargs: self.onbeforereconnect(src, eargs)
        exec.onafterreconnect  += \
            lambda src, eargs: self.onafterreconnect(src, eargs)

        # Call then executioner's exec methed which will call the exec() callable
        # above. executioner.execute will take care of dead, pooled connection,
        # and atomicity.
        exec.execute()
        
    def _save(self, cur=None, follow                  =True, 
                              followentitymapping     =True, 
                              followentitiesmapping   =True, 
                              followassociationmapping=True):

        if not self.orm.ismarkedfordeletion and not self.isvalid:
            raise db.brokenruleserror("Can't save invalid object" , self)

        if self.orm.ismarkedfordeletion:
            crud = 'delete'
            sql, args = self.orm.mappings.getdelete()
        elif self.orm.isnew:
            crud = 'create'
            self.createdat = self.updatedat = primative.datetime.utcnow()
            sql, args = self.orm.mappings.getinsert()
        elif self.orm._isdirty:
            self.updatedat = primative.datetime.utcnow()
            crud = 'update'
            sql, args = self.orm.mappings.getupdate()
        else:
            crud = None
            sql, args = (None,) * 2

        try:
            # Take snapshop of before state
            st = self.orm.persistencestate

            if sql:
                # Issue the query

                # Raise event
                eargs = db.operationeventargs(self, crud, sql, args)
                self.onbeforesave(self, eargs)

                cur.execute(sql, args)

                # Update new state
                self.orm.isnew = self.orm.ismarkedfordeletion
                self.orm.isdirty, self.orm.ismarkedfordeletion = (False,) * 2

                # Raise event
                self.onaftersave(self, eargs)
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
                    # Call the entity constituent's save method. Setting
                    # followentitiesmapping to false here prevents it's
                    # child/entitiesmapping constituents from being saved. This
                    # prevents infinite recursion. 
                    if map.isloaded:
                        map.value._save(cur, followentitiesmapping=False,
                                             followassociationmapping=False)

                if followentitiesmapping and type(map) is entitiesmapping:

                    es = map.value

                    # es is None if the constituent hasn't been loaded,
                    # so conditionally save()
                    if es:
                        # Take snapshot of states
                        sts = es.orm.persistencestates

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
                                # If self was deleted, delete each child
                                # constituents. Here, cascade deletes are
                                # hard-code.
                                if crud == 'delete':
                                    e.orm.ismarkedfordeletion = True
                                # If the previous operation on self was a
                                # delete, don't ascend back to self
                                # (followentitymapping == False). Doing so will
                                # recreate self in the database.
                                e._save(cur, followentitymapping=(crud!='delete'))
                            except Exception:
                                # Restore states
                                es.orm.persistencestates = sts
                                raise
                
                        for e in es.orm.trash:
                            trashst = e.orm.persistencestate
                            try:
                                e._save(cur)
                            except Exception:
                                e.orm.persistencestate = trashst
                                raise

                        # TODO If there is a rollback, shouldn't the entities
                        # be restored to the trash collection. Also, shouldn't
                        # deleting the associations trash (see below) do the
                        # same restoration.
                        es.orm.trash.clear()
                            
                if followassociationmapping and type(map) is associationsmapping:
                    if map.isloaded:
                        # For each association then each trashed association
                        for asses in map.value, map.value.orm.trash:
                            for ass in asses:
                                ass._save(cur, follow=False)
                                for map in ass.orm.mappings.entitymappings:
                                    if map.isloaded:
                                        if map.value is self:
                                            continue
                                        e = map.value
                                        e._save(cur, followassociationmapping=False)

                        asses.orm.trash.clear()

                if type(map) is foreignkeyfieldmapping:
                    if map.value is undef:
                        map.value = None
                        #undefmaps.append(map)

            super = self.orm.super
            if super:
                if crud == 'delete':
                    super.orm.ismarkedfordeletion = True
                super._save(cur)

        except Exception:
            self.orm.persistencestate = st
            raise
        
    # These are the limits of the MySQL datetime type
    mindatetime=primative.datetime('1000-01-01 00:00:00.000000+00:00')
    maxdatetime=primative.datetime('9999-12-31 23:59:59.999999+00:00')

    @property
    def brokenrules(self):
        return self._getbrokenrules()

    def _getbrokenrules(self, guestbook=None, followentitymapping=True):
        brs = entitiesmod.brokenrules()

        # This "guestbook" logic prevents infinite recursion and duplicated
        # brokenrules.
        guestbook = [] if guestbook is None else guestbook
        if self in guestbook:
            return brs
        else:
            guestbook += self,

        super = self.orm.super
        if super:
            brs += super._getbrokenrules(
                guestbook, 
                followentitymapping=followentitymapping
            )

        for map in self.orm.mappings:
            if type(map) is fieldmapping:
                t = map.type
                if t == types.str:
                    brs.demand(
                        self, 
                        map.name, 
                        type=str, 
                        min=map.min, 
                        max=map.max
                   )

                elif t == types.int:
                    brs.demand(self, map.name, min=map.min, max=map.max, 
                                     type=int)
                elif t == types.bool:
                    brs.demand(self, map.name, type=bool)

                elif t == types.float:
                    brs.demand(self, map.name, 
                                     type=float, 
                                     min=map.min, 
                                     max=map.max, 
                                     precision=map.precision,
                                     scale=map.scale)

                elif t == types.decimal:
                    brs.demand(self, map.name, 
                                     type=decimal.Decimal, 
                                     min=map.max, 
                                     max=map.min, 
                                     precision=map.precision,
                                     scale=map.scale)

                elif t == types.bytes:
                    brs.demand(self, 
                        map.name, 
                        type=bytes,
                        max=map.max, 
                        min=map.min
                    )

                elif t == types.datetime:
                    brs.demand(self, 
                        map.name, 
                        instanceof=datetime,
                        min=type(self).mindatetime,
                        max=type(self).maxdatetime,
                    )

            elif type(map) is entitiesmapping:
                # Currently, map.value will not load the entities on invocation
                # so we get None for es. This is good because we don't want to
                # needlessly load an object to see if it has broken rules.
                # However, if this changes, we will want to make sure that we
                # don't needlessy load this. This could lead to infinite
                # h (see it_entity_constituents_break_entity)
                es = map.value
                if es:
                    brs += es._getbrokenrules(guestbook, 
                        followentitymapping=followentitymapping
                    )

            elif followentitymapping and type(map) is entitymapping:
                if map.isloaded:
                    v = map.value
                    if v:
                        brs += v._getbrokenrules(guestbook, 
                            followentitymapping=followentitymapping
                        )

        return brs

    def __getattr__(self, attr):
        map = None

        # self.orm.instance is set in entity.__init__. If the user overrides
        # __init__ and doesn't call the base __init__, self.orm.instance is
        # never set. Do a quick check here to inform the user if they forgot to
        # call the base __init__
        if self.orm.isstatic:
            msg = 'orm is static. '
            msg += 'Ensure the overridden __init__ called the base __init__'
            raise ValueError(msg)

        if attr != 'orm' and self.orm.mappings:
            map = self.orm.mappings(attr)
            if not map:
                super = self.orm.super
                if super:
                    # TODO Before begining an ascent up the inheritence
                    # hierarchy, we need to first ensure that the attr is a map
                    # in that hierarchy; not just in the super. So the below
                    # line should be something like:
                    #     self.getmap(attr, recursive=True)
                    map = super.orm.mappings(attr)
                    if map:
                        if type(map) is entitymapping:
                            # We don't want an entitymapping from a super
                            # returned.  This would mean conc.artist would
                            # work. But concerts don't have artists;
                            # presentations do. Concerts have singers.
                            msg = "'%s' object has no attribute '%s'"
                            msg %= self.__class__.__name__, attr
                            raise AttributeError(msg)
                            
                        v = getattr(super, map.name)
                        # Assign the composite reference to the constituent
                        #   i.e., sng.presentations.singer = sng
                        if type(map) is entitiesmapping:
                            es = v
                            for e in (es,) +  tuple(es):
                                if not hasattr(e, self.orm.entity.__name__):
                                    setattr(e, self.orm.entity.__name__, self)
                        return v

        # Lazy-load constituent entities map
        if type(map) is entitiesmapping:
            if map.value is None:
                es = map.entities()
                if not self.orm.isnew:

                    # Get the FK map of the entities constituent. 
                    for map1 in map.entities.orm.mappings.foreignkeymappings:
                        e = self.orm.entity
                        while e:
                            if map1.entity is e:
                                break

                            # If not found, go up the inheritance tree and try again
                            super = e.orm.super
                            e = super.orm.entity if super else None
                        else:
                            continue
                        break
                    else:
                        raise ValueError('FK map not found for entity')

                    es.load(map1.name, self.id)

                    def setattr1(e, attr, v):
                        e.orm.mappings(attr).value = v

                    # Assign the composite reference to the constituent's
                    # elements
                    #   i.e., art.presentations.first.artist = art
                    for e in es:
                        attr = self.orm.entity.__name__

                        # Set cmp to False and use a custom setattr. Simply
                        # calling setattr(e, attr, self) would cause e.attr to
                        # be loaded from the database for comparison when __setattr__
                        # calls _setvalue.  However, the composite doesn't need
                        # to be loaded from the database.
                        e._setvalue(attr, self, attr, cmp=False, setattr=setattr1)

                        # Since we just set e's composite, e now thinks its
                        # dirty.  Correct that here.
                        e.orm.persistencestate = (False,) * 3
                map.value = es

                # Assign the composite reference to the constituent
                #   i.e., art.presentations.artist = art
                setattr(map.value, self.orm.entity.__name__, self)

                # Assign the superentities composite reference to the
                # constituent i.e., art.concert.artist = art
                super = self.orm.super
                if super:
                    setattr(map.value, super.orm.entity.__name__, super)

        elif type(map) is associationsmapping:
            map.composite = self

        elif map is None:
            if attr != 'orm':
                for map in self.orm.mappings.associationsmappings:
                    for map1 in map.associations.orm.mappings.entitymappings:
                        if map1.entity.orm.entities.__name__ == attr:
                            asses = getattr(self, map.name)
                            return getattr(asses, attr)

            msg = "'%s' object has no attribute '%s'"
            raise AttributeError(msg % (self.__class__.__name__, attr))

        return map.value

    def __repr__(self):
        tbl = table()

        for map in self.orm.mappings:
            r = tbl.newrow()
            v = getattr(self, map.name)
            if type(map) in (primarykeyfieldmapping, foreignkeyfieldmapping):
                if type(map.value) is UUID:
                    v = v.hex[:7]
                else:
                    v = str(v)
            else:
                try:
                    if type(map) in (entitiesmapping, associationsmapping):
                        es = v
                        if es:
                            brs = es._getbrokenrules(
                                es=None, 
                                followentitymapping=False
                            )
                            args = es.count, brs.count
                            v = 'Count: %s; Broken Rules: %s' % args
                        else:
                            v = str(es)
                    else:
                        v = str(v)
                except Exception as ex:
                    v = '(%s)' % str(ex)

            r.newfield(map.name)
            r.newfield(v)

        tblbr = table()

        if not self.isvalid:
            r = tblbr.newrow()
            r.newfield('property')
            r.newfield('type')
            r.newfield('message')


            for br in self.brokenrules:
                r = tblbr.newrow()
                r.newfield(br.property)
                r.newfield(br.type)
                r.newfield(br.message)
            
        return '%s\n%s\n%s\n%s' % (super().__repr__(), 
                                   str(tbl), 
                                   'Broken Rules', 
                                   str(tblbr))

    def __str__(self):
        r = '(%s)' % (self.id.hex[:7])

        if hasattr(self, 'name'):
            r += '"%s"' % self.name

        return r
            
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
                maps.append(foreignkeyfieldmapping(map.entity, derived=True))

            for e in orm.getentitys():
                if e is self.orm.entity:
                    continue
                for map in e.orm.mappings.entitiesmappings:
                    if map.entities is self.orm.entities:
                        maps.append(entitymapping(e.__name__, e, derived=True))
                        maps.append(foreignkeyfieldmapping(e, derived=True))

            for ass in orm.getassociations():
                for map in ass.orm.mappings.entitymappings:
                    if map.entity is self.orm.entity:
                        asses = ass.orm.entities
                        map = associationsmapping(asses.__name__, asses, derived=True)
                        maps.append(map)
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

        # Ensure builtins attr's come right after id
        for attr in reversed(('id', 'createdat')):
            try:
                attr = self.pop(attr)
            except ValueError:
                # attr hasn't been added to self yet
                pass
            else:
                self << attr

        # Insert FK maps right after PK map
        fkmaps = list(self.foreignkeymappings)
        fkmaps.sort(key=lambda x: x.name)
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

        for i, map in enumerate(self):
            if not isinstance(map, fieldmapping):
                continue

            if i:
                r += ',\n'

            r += '    ' + map.name

            if isinstance(map, fieldmapping):
                r += ' ' + map.dbtype

        r += '\n) '
        r += 'ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;'
        return r

    def getinsert(self):
        tbl = self.orm.table

        placeholder = ''
        for map in self:
            if isinstance(map, fieldmapping):
                placeholder += '%s, '

        placeholder = placeholder.rstrip(', ')

        sql = 'INSERT INTO {} VALUES ({});'.format(tbl, placeholder)

        args = self._getargs()

        sql = orm.introduce(sql, args)

        return sql, args

    def getupdate(self):
        set = ''
        for map in self:
            if isinstance(map, fieldmapping):
                if isinstance(map, primarykeyfieldmapping):
                    id = map.value.bytes
                else:
                    set += '%s = %%s, ' % (map.name,)

        set = set[:-2]

        sql = """UPDATE {}
SET {}
WHERE id = %s;
        """.format(self.orm.table, set)

        args = self._getargs()

        # Move the id value from the bottom to the top
        args.append(args.pop(0))

        sql = orm.introduce(sql, args)
        return sql, args

    def getdelete(self):
        sql = 'DELETE FROM {} WHERE id = %s;'.format(self.orm.table)

        args = self['id'].value.bytes,

        sql = orm.introduce(sql, args)

        return sql, args

    def _getargs(self):
        r = []
        for map in self:
            if isinstance(map, fieldmapping):
                keymaps = primarykeyfieldmapping, foreignkeyfieldmapping
                if type(map) in keymaps and isinstance(map.value, UUID):
                    r.append(map.value.bytes)
                else:
                    v = map.value if map.value is not undef else None
                    if v is not None:
                        if map.isdatetime:
                            v = v.replace(tzinfo=None)
                        elif map.isbool:
                            v = int(v)
                    r.append(v)
        return r

    def clone(self, orm_):
        r = mappings(orm=orm_)
        for map in self:
            r += map.clone()
        return r

class mapping(entitiesmod.entity):
    ordinal = 0

    def __init__(self, name, derived=False):
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

    @property
    def value(self):
        raise NotImplementedError('Value should be implemented by the subclass')

    @value.setter
    def value(self, v):
        raise NotImplementedError('Value should be implemented by the subclass')

    @property
    def isloaded(self):
        return self._value not in (None, undef)

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
                        if map.value not in (undef, None):
                            self._value = self.entity(map.value)
        return self._value

    @value.setter
    def value(self, v):
        self._setvalue('_value', v, 'value')

    def clone(self):
        return entitymapping(self.name, self.entity, derived=self.derived)

class attr:
    class wrap:
        def __init__(self, *args, **kwargs):
            args = list(args)
            self.fget = args.pop()
            self.args = args
            self.kwargs = kwargs

        @property
        def mapping(self):
            kwargs = self.kwargs
            for i, arg in enumerate(self.args):
                if i == 0:
                    ix = 'type'
                else:
                    # TODO
                    raise NotImplementedError()

                kwargs[ix] = arg

            return fieldmapping(**kwargs)

        def __get__(self, e, etype=None):
            name = self.fget.__name__
            def attr(v=undef):
                if v is undef:
                    try:
                        return e.orm.mappings[name].value
                    except IndexError:
                        # If it's not in the subentity's mapping collection,
                        # make a regular getattr() call on e's super. 
                        super = e.orm.super
                        if super:
                            return getattr(super, name)
                else:
                    e.__setattr__(name, v, cmp=False)
                    return v

            self.fget.__globals__['attr'] = attr
            return self.fget(e)

    def __init__(self, *args, **kwargs):
        self.args = list(args)
        self.kwargs = kwargs

    def __call__(self, meth):
        self.args.append(meth)
        w = attr.wrap(*self.args, **self.kwargs)
        return w

class fieldmapping(mapping):
    def __init__(self, type,       
                       min=None,  
                       max=None, 
                       m=None,
                       d=None,
                       name=None,  
                       derived=False):

        self._type       =  type
        self._value      =  undef
        self._min        =  min
        self._max        =  max
        self._precision  =  m
        self._scale      =  d

        super().__init__(name, derived)

    def clone(self):
        map = fieldmapping(
            self.type,
            self.min,
            self.max,
            self.precision,
            self.scale,
            self.name,
            self.derived
        )

        map._value = self._value

        return map

    @property
    def isstr(self):
        return self.type == types.str

    @property
    def isdatetime(self):
        return self.type == types.datetime

    @property
    def isbool(self):
        return self.type == types.bool

    @property
    def isint(self):
        return self.type == types.int

    @property
    def isfloat(self):
        return self.type == types.float

    @property
    def isdecimal(self):
        return self.type == types.decimal

    @property
    def isbytes(self):
        return self.type == types.bytes

    @property
    def isfixed(self):
        if self.isint or self.isfloat or self.isdecimal:
            return True

        if self.isbytes or self.isstr:
            return self.max == self.min
        return False

    @property
    def min(self):
        if self.isstr:
            if self._min is None:
                return 1

        elif self.isint:
            if self._min is None:
                return -2147483648

        elif self.isfloat:
            if self._min is None:
                return -self.max
            else:
                return float(self._min)

        elif self.isdecimal:
            if self._min is None:
                return -self.max
            else:
                return decimal.Decimal(self._min)

        elif self.isdatetime:
            ... # TODO?
        elif self.isbytes:
            ... # TODO?

        return self._min

    @property
    def precision(self):
        if not (self.isfloat or self.isdecimal):
            return None

        if self._precision is None:
            return 12

        return self._precision

    @property
    def scale(self):
        if not (self.isfloat or self.isdecimal):
            return None

        if self._scale is None:
            return 2

        return self._scale
        
    @property
    def max(self):
        t = self.type
        if self.isstr:
            if self._max is None:
                return 255
            else:
                return self._max

        elif self.isint:
            if self._max is None:
                return 2147483647
            else:
                return self._max

        elif self.isfloat or self.isdecimal:
            m, d = self.precision, self.scale
            str = '9' * m
            str = '%s.%s' % (str[:m-d], str[:d])
            return float(str) if self.isfloat else decimal.Decimal(str)

        elif t is types.bytes:
            if self._max is None:
                return 255
            return self._max

    @property
    def type(self):
        t = self._type
        if t in (str, types.str):
            return types.str
        elif t in (int, types.int):
            return types.int
        elif t in (bool, types.bool):
            return types.bool
        elif hasattr(t, '__name__') and t.__name__ == 'datetime':
            return types.datetime
        elif t in (float,):
            return types.float
        elif hasattr(t, '__name__') and t.__name__.lower() == 'decimal':
            return types.decimal
        elif t in (bytes,):
            return types.bytes
        return self._type

    @property
    def signed(self):
        if self.type not in (types.int, types.float, types.decimal):
            raise ValueError()

        return self.min < 0
    
    @property
    def dbtype(self):
        if self.isstr:
            if self.max <= 65535:
                if self.isfixed:
                    return 'char(' + str(self.max) + ')'
                else:
                    return 'varchar(' + str(self.max) + ')'
            else:
                return 'longtext'

        elif self.isint:
            if self.min < 0:
                if    self.min  >=  -128         and  self.max  <=  127:
                    return 'tinyint'
                elif  self.min  >=  -32768       and  self.max  <=  32767:
                    return 'smallint'
                elif  self.min  >=  -8388608     and  self.max  <=  8388607:
                    return 'mediumint'
                elif  self.min  >=  -2147483648  and  self.max  <=  2147483647:
                    return 'int'
                elif  self.min  >=  -2**63       and  self.max  <=  2**63-1:
                    return 'bigint'
                else:
                    raise ValueError()
            else:
                if self.max  <=  255:
                    return 'tinyint unsigned'
                elif self.max  <=  65535:
                    return 'smallint unsigned'
                elif self.max  <=  16777215:
                    return 'mediumint unsigned'
                elif self.max  <=  4294967295:
                    return 'int unsigned'
                elif self.max  <=  (2 ** 64) - 1:
                    return 'bigint unsigned'
                else:
                    raise ValueError()
        elif self.isdatetime:
            return 'datetime(6)'
        elif self.isbool:
            return 'bit'
        elif self.isfloat:
            return 'double(%s, %s)' % (self.precision, self.scale)
        elif self.isdecimal:
            return 'decimal(%s, %s)' % (self.precision, self.scale)
        elif self.isbytes:
            if self.isfixed:
                return 'binary(%s)' % self.max
            else:
                return 'varbinary(%s)' % self.max
        else:
            raise ValueError()

    @property
    def value(self):
        if self._value is undef:
            if self.isint:
                return int()
            elif self.isbool:
                return bool()
            elif self.isfloat:
                return float()
            elif self.isdecimal:
                return decimal.Decimal()
            elif self.isstr:
                return str()
            elif self.isbytes:
                return bytes()
            else:
                return None
        
        if self._value is not None:
            if self.isdatetime:
                try:
                    if type(self._value) is str:
                        self._value = primative.datetime(self._value) 
                    elif not isinstance(self._value, primative.datetime):
                        self._value = primative.datetime(self._value)
                except:
                    pass
                else:
                    utc = dateutil.tz.gettz('UTC')
                    if self._value.tzinfo and self._value.tzinfo is not utc:
                        self._value = self._value.astimezone(utc)
                    else:
                        self._value = self._value.replace(tzinfo=utc)
            elif self.isbool:
                if type(self._value) is bytes:
                    # Convert the bytes string fromm MySQL's bit type to a
                    # bool.
                    v = self._value
                    self._value = bool.from_bytes(v, byteorder='little')

            elif self.isint:
                try:
                    self._value = int(self._value)
                except:
                    pass
            elif self.isfloat:
                try:
                    self._value = round(float(self._value), self.scale)
                except:
                    pass

            elif self.isdecimal:
                try:
                    d = decimal.Decimal(str(self._value))
                except:
                    pass
                else:
                    self._value = round(d, self.scale)

            elif self.isbytes:
                try:
                    self._value = bytes(self._value)
                except:
                    pass

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
    def dbtype(self):
        return 'binary(16)'

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
    def dbtype(self):
        return 'binary(16) primary key'

    @property
    def value(self):
        # If a super instance exists, use that because we want a subclass and
        # its super class to share the same id. Here we use ._super instead of
        # .super because we don't want the invoke the super accessor because it
        # calls the id accessor (which calls this accessor). This leads to
        # infinite recursion. This, of course, assumes that the .super accessor
        # has previously been called.

        super = self.orm._super
        if super:
            return super.id

        if type(self._value) is bytes:
            self._value = UUID(bytes=self._value)
            
        return self._value

    @value.setter
    def value(self, v):
        self._value = v

class ormclasseswrapper(entitiesmod.entities):
    def append(self, obj, uniq=False, r=None):
        if isinstance(obj, type):
            obj = ormclasswrapper(obj)
        elif isinstance(obj, ormclasswrapper):
            pass
        else:
            raise ValueError()
        super().append(obj, uniq, r)
        return r

class ormclasswrapper(entitiesmod.entity):
    def __init__(self, entity):
        self.entity = entity
        super().__init__()

    def __str__(self):
        return str(self.entity)

    def __repr__(self):
        return repr(self.entity)

    def __getattr__(self, attr):
        return getattr(self.entity, attr)

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
        self.mappings             =  None
        self.isnew                =  False
        self._isdirty             =  False
        self.ismarkedfordeletion  =  False
        self.entities             =  None
        self.entity               =  None
        self.table                =  None
        self._composits           =  None
        self._constituents        =  None
        self._associations        =  None
        self._trash               =  None
        self._subclasses          =  None
        self._super               =  None
        self._base                =  undef
        self.instance             =  None

    def clone(self):
        r = orm()

        props = (
            'isnew',       '_isdirty',      'ismarkedfordeletion',
            'entity',      'entities',     'table'
        )

        for prop in props: 
            setattr(r, prop, getattr(self, prop))

        r.mappings = self.mappings.clone(r)

        return r

    @staticmethod
    def introduce(sql, args):
        """Use args to add introducers (_binary, et. al.) before the %s in
        sql."""

        # Where the arg is binary (bytearray or bytes), replace '%s' with
        # '_binary %s' so it's clear to MySQL where the UTF8 SQL string 
        # becomes pure binary not intended for character decoding.
        return sql % tuple(
            [
                '_binary %s' if type(x) in (bytearray, bytes) else '%s' 
                for x in args
            ]
        )
    @property
    def isdirty(self):
        if self._isdirty:
            return True

        if self.super:
            return self.super.orm.isdirty

        return False

    @isdirty.setter
    def isdirty(self, v):
        self._isdirty = v

    @property
    def persistencestates(self):
        es = self.instance
        if not isinstance(es, entities):
            msg = 'Use with entities. For entity, use persistencestate'
            raise ValueError(msg)
            
        sts = []
        for e in es:
            sts.append(e.orm.persistencestate)
        return sts

    @persistencestates.setter
    def persistencestates(self, sts):
        es = self.instance
        if not isinstance(es, entities):
            msg = 'Use with entities. For entity, use persistencestate'
            raise ValueError(msg)

        for e, st in zip(es, sts):
            e.orm.persistencestate = st

    @property
    def persistencestate(self):
        es = self.instance
        if not isinstance(es, entity):
            msg = 'Use with entity. For entities, use persistencestates'
            raise ValueError(msg)
        return self.isnew, self.isdirty, self.ismarkedfordeletion

    @persistencestate.setter
    def persistencestate(self, v):
        es = self.instance
        if not isinstance(es, entity):
            msg = 'Use with entity. For entities, use persistencestates'
            raise ValueError(msg)
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
        props = [x.name for x in self.mappings]

        for map in self.mappings.associationsmappings:
            for map1 in map.associations.orm.mappings.entitymappings:
                if self.entity is not map1.entity:
                    props.append(map1.entity.orm.entities.__name__)


        super = self.super
        if super:
            props += [x for x in super.orm.properties if x not in props]

        return props

    @staticmethod
    def getsubclasses(of):
        r = []

        for sub in of.__subclasses__():
            if sub not in (associations, association):
                r.append(sub)
            r.extend(orm.getsubclasses(sub))

        return r

    @staticmethod
    def issub(obj1,  obj2):
        if not (isinstance(obj1, type) and isinstance(obj2, type)):
            msg = 'Only static types are currently supported'
            raise NotImplementedError(msg)

        cls1, cls2 = obj1, obj2

        super = cls2

        while super:
            if super is cls1:
                return True
            super = super.orm.super

        return False
        

    @property
    def super(self):
        """ For orms that have no instance, return the super class of
        orm.entity.  If orm.instance is not None, return an instance of that
        objects super class.  A super class here means the base class of of an
        entity class where the base itself is not entity, but rather a subclass
        of entity. So if class A inherits directly from entity, it will have a
        super of None. However if class B inherits from A. class B will have a
        super of A."""
        if self._super:
            return self._super

        if self._base is not undef:
            return self._base

        if self.entity:
            bases = self.entity.__bases__
            try:
                base = bases[0]
            except IndexError:
                base = None

            if base in (entity, association):
                self._base = None
                return self._base

            if self.isstatic:
                self._base = base
                return self._base

            elif self.isinstance:
                if self.isnew:
                    self._super = base()
                else:
                    e = self.instance
                    if e.id is not undef:
                        self._super = base(e.id)

                return self._super

        return None

    @property
    def isstatic(self):
        return self.instance is None

    @property
    def isinstance(self):
        return self.instance is not None

    @property
    def subclasses(self):
        if self._subclasses is None:
            clss = ormclasseswrapper()
            for sub in orm.getsubclasses(of=self.entity):
                clss += sub
            self._subclasses = clss
        return self._subclasses
        
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
                for map in ass.orm.mappings.entitymappings:
                    if map.entity is self.entity:
                        self._associations += ormclasswrapper(ass)

        return self._associations
            
    @property
    def composites(self):
        if not self._composits:
            self._composits = composites()
            for sub in self.getsubclasses(of=entity):
                for map in sub.orm.mappings.entitiesmappings:
                    if map.entities.orm.entity is self.entity:
                        self._composits += composite(sub)
                        break

            for ass in self.getassociations():
                maps = list(ass.orm.mappings.entitymappings)
                for i, map in enumerate(maps):
                    if orm.issub(map.entity, self.entity):
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
                # TODO We probably should be using the association's (self) mappings
                # collection to test the composites names. The name that matters is
                # on the LHS of the map when being defined in the association class.
                if map.name == type(self.composite).__name__:
                    setattr(obj, map.name, self.composite)
                    break;
            
        super().append(obj, uniq, r)
        return r

    def _self_onremove(self, src, eargs):
        """ This event handler occures when an association is removed from an
        assoctions collection. When this happens, we want to remove the
        association's constituent entity (the non-composite entity) from its
        pseudocollection class - but only if it hasn't already been marked for
        deletion (ismarkedfordeletion). If it has been marked for deletion,
        that means the psuedocollection class is invoking this handler - so
        removing the constituent would result in infinite recursion.  """

        ass = eargs.entity

        for i, map in enumerate(ass.orm.mappings.entitymappings):
            if map.entity is not type(self.composite):
                e = map.value
                if not e.orm.ismarkedfordeletion:
                    es = getattr(self, e.orm.entities.__name__)
                    es.remove(e)
                    break
            
        super()._self_onremove(src, eargs)

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

