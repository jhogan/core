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
from entities import brokenrules, brokenrule, entity, entities
import uuid
import db
import hashlib
import os
import db

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
        self._roles = roles()
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
            name varchar(255)
        )
        """

    @property
    def _table(self):
        return 'roles'

class role(db.dbentity):
    def __init__(self, o=None):
        super().__init__()
        if type(o) is db.dbresult:
            ls = list(o._row)
            self._name = ls.pop()
            self._id = uuid.UUID(bytes=ls.pop())
        else:
            self._name = None
            self._id = None
            self._marknew()

    def _insert(self, cur=None):
        self._id = uuid.uuid4()

        args = (
            self.id.bytes, 
            self.name,
        )

        insert = """
        insert into roles
        values({})
        """.format(('%s, ' * len(args)).rstrip(', '))


        self.query(insert, args, cur)
    
    def _update(self, cur=None):
        sql = """
        update roles
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

