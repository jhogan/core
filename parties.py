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
from entities import brokenrules, brokenrule, entity, entities
from pdb import set_trace; B=set_trace
import db
import db
import hashlib
import os
import re
import uuid

class persons(db.dbentities):
    @property
    def _create(self):
        return """
        create table persons(
            id binary(16) primary key,
            firstname varchar(255),
            middlename varchar(255),
            lastname varchar(255),
            email varchar(255),
            phone varchar(255)
        )
        """

    @property
    def _table(self):
        return 'persons'

class person(db.dbentity):
    def __init__(self, id=None):
        super().__init__()
        self._id = id
        if id == None:
            self._firstname = None
            self._middlename = None
            self._lastname = None
            self._email = None
            self._phone = None
            self._marknew()
        else:
            sql = """
            select *
            from persons
            where id = %s
            """

            args = (
                self.id.bytes,
            )

            ress = self.query(sql, args)
            res = ress.demandhasone()
            row = list(res)
            self._phone = row.pop()
            self._email = row.pop()
            self._lastname = row.pop()
            self._middlename = row.pop()
            self._firstname = row.pop()
            self._markold()

    def _update(self, cur=None):
        sql = """
        update persons
        set firstname = %s,
        middlename = %s,
        lastname = %s,
        email = %s,
        phone = %s
        where id = %s
        """

        args = (
            self.firstname,
            self.middlename,
            self.lastname,
            self.email,
            self.phone,
            self.id.bytes
        )

        self.query(sql, args, cur)
        
    def _insert(self, cur=None):
        self._id = uuid.uuid4()

        args = (
            self.id.bytes, 
            self.firstname,
            self.middlename,
            self.lastname,
            self.email,
            self.phone,
        )

        insert = """
        insert into persons
        values({})
        """.format(('%s, ' * len(args)).rstrip(', '))


        self.query(insert, args, cur)

    @property
    def firstname(self):
        return self._firstname

    @firstname.setter
    def firstname(self, v):
        return self._setvalue('_firstname', v, 'firstname')

    @property
    def middlename(self):
        return self._middlename

    @middlename.setter
    def middlename(self, v):
        return self._setvalue('_middlename', v, 'middlename')

    @property
    def lastname(self):
        return self._lastname

    @lastname.setter
    def lastname(self, v):
        return self._setvalue('_lastname', v, 'lastname')

    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, v):
        return self._setvalue('_email', v, 'email')

    @property
    def phone(self):
        return self._phone

    @phone.setter
    def phone(self, v):
        return self._setvalue('_phone', v, 'phone')

    @property
    def fullname(self):
        return self.firstname + ' ' + self.lastname

    @property
    def name(self):
        return self.fullname
   
    @property
    def brokenrules(self):
        brs = brokenrules()
        brs.demand(self, 'firstname',  maxlen=255)
        brs.demand(self, 'middlename', maxlen=255)
        brs.demand(self, 'lastname',   isfull=True, maxlen=255)
        brs.demand(self, 'email',      isemail=True, maxlen=255)
        brs.demand(self, 'phone',      maxlen=255)
        return brs

class users(db.dbentities):
    @property
    def _create(self):
        return """
        create table users(
            id binary(16) primary key,
            service varchar(266),
            name varchar(255),
            password binary(32),
            salt binary(16)
        )
        """

    @property
    def _table(self):
        return 'users'

class user(db.dbentity):
    def __init__(self, o=None):
        super().__init__()
        self._password = None
        if o == None:
            self._service = None
            self._name = None
            self._hash = None
            self._salt = None
            self._id   = None
            self._marknew()
        elif type(o) == uuid.UUID or type(o) == db.dbresult:
            if type(o) == uuid.UUID:
                sql = """
                select * from users where id = %s
                """
                args = (
                    o.bytes,
                )

                ress = self.query(sql, args)
                res = ress.demandhasone()
            else:
                res = o
            row = list(res)
            self._salt = row.pop()
            self._hash = row.pop()
            self._name = row.pop()
            self._service = row.pop()
            self._id = uuid.UUID(bytes=row.pop())
            self._markold()

        self._roles_mm_objects = roles_mm_objects(self)

        self._roles = roles()
        self._roles.onadd    += self._roles_onchg
        self._roles.onremove += self._roles_onchg
        for mm in self._roles_mm_objects:
            self._roles += role(mm.roleid)

    def _roles_onchg(self, src, eargs):
        self._markdirty()

    @property
    def _collection(self):
        return users

    @staticmethod
    def load(uid, srv):
            sql = """
            select * 
            from users 
            where name = %s and service = %s
            """
            args = (
                uid, srv
            )

            ress = db.connections.getinstance().default.query(sql, args)
            if ress.isempty:
                return None
            else:
                res = ress.demandhasone()
                return user(res)

    def _insert(self, cur=None):
        self._id = uuid.uuid4()

        args = (
            self.id.bytes, 
            self.service,
            self.name,
            self.hash,
            self.salt,
        )

        insert = """
        insert into users
        values({})
        """.format(('%s, ' * len(args)).rstrip(', '))


        self.query(insert, args, cur)

        self._roles_mm_objects.attach(self.roles)
        self._roles_mm_objects.save()

    def _update(self, cur=None):
        sql = """
        update users
        set service = %s,
        name = %s,
        password = %s,
        salt = %s,
        where id = %s
        """
        args = (
            self.service,
            self.name,
            self.hash,
            self.salt,
            self.id.bytes
        )

        self.query(sql, args, cur)

        self.roles.save(cur)
        
    @property
    def roles(self):
        return self._roles
    
    @roles.setter
    def roles(self, v):
        return self._setvalue('_roles', v, 'roles')

    @property
    def service(self):
        return self._service

    @service.setter
    def service(self, v):
        return self._setvalue('_service', v, 'service')

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, v):
        return self._setvalue('_name', v, 'name')

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, v):
        return self._setvalue('_password', v, 'password')

    def _getpasswordhash(self, pwd=None):
        pwd = pwd if pwd else self.password
        salt = self._salt if self._salt else os.urandom(16)
        pwd = bytes(pwd, 'utf-8')
        algo = 'sha256'
        iter = 100000
        fn = hashlib.pbkdf2_hmac
        hash = fn(algo, pwd, salt, iter)
        return hash, salt

    def _setpasswordhash(self):
        if self._hash and self._salt:
            return

        hash, salt = self._getpasswordhash()
        self._hash = hash
        self._salt = salt

    def ispassword(self, pwd):
        # Ensure self._salt is set so we _getpasswordhash doesn't make one up
        self._setpasswordhash()
        hash, salt = self._getpasswordhash(pwd)
        if hash == self.hash:
            return True
        return False

    @property
    def salt(self):
        self._setpasswordhash()
        return self._salt

    @property
    def hash(self):
        self._setpasswordhash()
        return self._hash
        

    @property
    def brokenrules(self):
        # TODO Enuser that a username and service are unique
        brs = brokenrules()
        brs.demand(self, 'name', isfull=True, maxlen=255)
        brs.demand(self, 'service', isfull=True, maxlen=255)

        # Query database for existing user only if name and service are already
        # valid.
        if brs.isempty:
            u = user.load(self.name, self.service)
            if u:
                brs += brokenrule('A user with that name and service already exist', 'name', 'unique')
                
        return brs

class roles_mm_objects(db.dbentities):
    def __init__(self, obj=None):
        super().__init__()
        self._object = obj

        if obj:
            if not self.object._isnew:
                sql = """
                select *
                from roles_mm_objects
                where objectid = %s and
                objectname = %s
                """
                args = (
                    self.object.id.bytes,
                    self.object._table,
                )

                ress = self.query(sql, args)

                for res in ress:
                    self += role_mm_object(res)

    def attach(self, rs):
        for mm in self:
            for r in rs:
                if mm.role.id == r.id:
                    break;
            else:
                mm.markdeleted()

        for r in rs:
            for mm in self:
                if mm.roleid == r.id:
                    break
            else:
                mm = role_mm_object()
                mm.roleid = r.id
                mm.objectid = self.object.id
                mm.objectname = self.object._table
                self += mm

    @property
    def _create(self):
        return """
        create table roles_mm_objects(
            id binary(16) primary key,
            roleid binary(16),
            objectid binary(16),
            objectname varchar(255)
        )
        """

    @property
    def _table(self):
        return 'roles_mm_objects'

    @property
    def object(self):
        return self._object

class role_mm_object(db.dbentity):
    def __init__(self, res=None):
        super().__init__()
        if res:
            row = list(res)
            self._id         = uuid.UUID(bytes=row.pop(0))
            self._roleid     = uuid.UUID(bytes=row.pop(0))
            self._objectid   = uuid.UUID(bytes=row.pop(0))
            self._objectname = row.pop(0)
            self._markold()
        else:
            self._id         = None
            self._roleid     = None
            self._objectid   = None
            self._objectname = None
            self._marknew()


    def _insert(self, cur=None):
        self._id = uuid.uuid4()

        args = (
            self.id.bytes, 
            self.roleid.bytes,
            self.objectid.bytes,
            self.objectname,
        )

        insert = """
        insert into roles_mm_objects
        values({})
        """.format(('%s, ' * len(args)).rstrip(', '))


        self.query(insert, args, cur)


    @property
    def _collection(self):
        return roles_mm_objects

    @property
    def roleid(self):
        return self._roleid

    @roleid.setter
    def roleid(self, v):
        return self._setvalue('_roleid', v, 'roleid')
    
    @property
    def objectid(self):
        return self._objectid

    @objectid.setter
    def objectid(self, v):
        return self._setvalue('_objectid', v, 'objectid')
    
    @property
    def objectname(self):
        return self._objectname

    @objectname.setter
    def objectname(self, v):
        return self._setvalue('_objectname', v, 'objectname')
    
class roles(db.dbentities):
    def __init__(self, ress=None):
        super().__init__()
        if ress:
            for res in ress:
                self += role(res)

    @property
    def _create(self):
        return """
        create table roles(
            id binary(16) primary key,
            name varchar(255),
            capabilities text
        )
        """

    @property
    def _table(self):
        return 'roles'

class role(db.dbentity):
    def __init__(self, o=None):
        super().__init__()
        res = None
        if type(o) is uuid.UUID:
            self._id = o
            sql = """
            select *
            from roles
            where id = %s
            """
            args = (
                self.id.bytes,
            )

            ress = self.query(sql, args)
            res = ress.demandhasone()
        elif type(o) is db.dbresult:
            res = o
        else:
            self._name = None
            self._id = None
            self._marknew()

        if res:
            ls = list(res._row)
            self._capabilities = capabilities(ls.pop())
            self._name = ls.pop()
            self._id = uuid.UUID(bytes=ls.pop())
            self._markold()
        else:
            self._capabilities = capabilities()

        self._capabilities.onadd += self._capabilities_onchg
        self._capabilities.onremove += self._capabilities_onchg
    
    def _capabilities_onchg(self, src, eargs):
        self._markdirty()

    def _insert(self, cur=None):
        self._id = uuid.uuid4()

        args = (
            self.id.bytes, 
            self.name,
            str(self.capabilities),
        )

        insert = """
        insert into roles
        values({})
        """.format(('%s, ' * len(args)).rstrip(', '))


        self.query(insert, args, cur)
    
    def _update(self, cur=None):
        sql = """
        update roles
        set name = %s,
        capabilities = %s
        where id = %s
        """
        args = (
            self.name,
            str(self.capabilities),
            self.id.bytes,
        )

        self.query(sql, args, cur)

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, v):
        return self._setvalue('_name', v, 'name')

    @property
    def capabilities(self):
        return self._capabilities

    @capabilities.setter
    def capabilities(self, v):
        return self._setvalue('_capabilities', v, 'capabilities')

class capabilities(entities):
    def __init__(self, caps=None):
        super().__init__()
        if caps:
            for cap in caps.split():
                self += capability(cap)

    def append(self, obj, uniq=False, r=None):
        if type(obj) is str:
            return self.append(capability(obj))
        elif type(obj) is capability:
            # Only allow capabilities with unique names
            for cap in self:
                if cap.name == obj.name:
                    break
            else:
                return super().append(obj)
        else:
            raise ValueError('Only str and capability can be appended')

    def remove(self, obj):
        if type(obj) is str:
            cap = self(obj)
            if cap:
                return self.remove(cap)
            return None
        elif type(obj) is capability:
            super().remove(obj)
        else:
            raise ValueError('Only str and capability can be removed')

    # Don't allow other ways to add to collection
    def insert(self):
        raise NotImplementedError()
    def insertbefore(self):
        raise NotImplementedError()
    def insertafter(self):
        raise NotImplementedError()
    def unshift(self):
        raise NotImplementedError()
    def shift(self):
        raise NotImplementedError()
    def push(self):
        raise NotImplementedError()
    def pop(self):
        raise NotImplementedError()

    def __str__(self):
        return ' '.join(self.pluck('name'))

class capability(entity):
    def __init__(self, v):
        self._name = v

    @property
    def name(self):
        if type(self._name) == str:
            return self._name.strip()
        return self._name

    @name.setter
    def name(self, v):
        return self._setvalue('_name', v, 'name')

    @property
    def brokenrules(self):
        brs = brokenrules()
        brs.demand(self, 'name', isfull=True, istype=str)

        n = self.name
        if type(n) is str and bool(re.match('^.*\s+.*$', n)):
            brs += brokenrule('Name must contain no whitespace', 'name', 'valid')

        return brs



