from pdb import set_trace; B=set_trace
import db
from entities import brokenrules

class leads(db.dbentities):
    def __init__(self, rset=None):
        super().__init__()
        if rset != None:
            for r in rset:
                self += lead(r)

    @property
    def _table(self):
        return 'leads'

    def getunemailed():
        sql = """
        select *
        from leads
        where emailed_at is null
        """
        conn = db.connections.getinstance().default
        res = conn.query(sql)

        ls = leads()
        for r in res:
            ls += lead(r)

        return ls

class lead(db.dbentity):
    def __init__(self, v=None):
        super().__init__()

        if type(v) == int:
            sql = 'select * from leads where id = %s'
            conn = db.connections.getinstance().default
            v = conn.query(sql, (v,))

        if v == None:
            ls = [''] * 5 + [None]
            self._marknew()
        elif type(v) == db.dbresultset:
            if v.hasone:
                ls = list(v.first)
            else:
                ls = [None] * 5
            self._markold()
        elif type(v) == db.dbresult:
            ls = list(v)
            self._markold()

        self._id,      self._name, self._email, \
        self._subject,  self._message, \
        self._emailed_at = ls

    @property
    def name(self):
        return self._name
    
    @name.setter
    def name(self, v):
        return self._setvalue('_name', v, 'name')

    @property
    def subject(self):
        return self._subject
    
    @subject.setter
    def subject(self, v):
        return self._setvalue('_subject', v, 'subject')

    @property
    def email(self):
        return self._email
    
    @email.setter
    def email(self, v):
        return self._setvalue('_email', v, 'email')

    @property
    def message(self):
        return self._message
    
    @message.setter
    def message(self, v):
        return self._setvalue('_message', v, 'message')

    @property
    def emailed_at(self):
        return self._emailed_at
    
    @emailed_at.setter
    def emailed_at(self, v):
        return self._setvalue('_emailed_at', v, 'emailed_at')

    def _insert(self, cur=None):
        insert = """
        insert into leads
        values(null, %s, %s, %s, %s, %s);
        """
        conn = db.connections.getinstance().default
        args = (self.name,    self.email, self.subject, 
                self.message, self.emailed_at)
        res = conn.query(insert, args, cur)

        self._id = res.lastrowid

    def _update(self):
        sql = """
        update leads set 
        name = %s,    email = %s,
        subject = %s, message = %s, emailed_at = %s
        where id = %s;
        """
        conn = db.connections.getinstance().default
        args = (self.name,    self.email,   self.subject, 
                self.message, self.emailed_at, self.id)
        res = conn.query(sql, args)

    # TODO: This should be _delete(). Have the super class call it from
    # its delete() method.
    def delete(self):
        if not self.id:
            raise Exception("Can't delete lead.")
        sql = 'delete from leads where id = %s'
        conn = db.connections.getinstance().default
        v = conn.query(sql, (self.id,))
        
    @property
    def brokenrules(self):
        brs = brokenrules()

        brs.demand(self,  'name',     isfull=True, maxlen=50)
        brs.demand(self,  'email',    isemail=True, maxlen=50)
        brs.demand(self,  'message',  isfull=True, maxlen=1000)
        
        if self.emailed_at != None:
            brs.demand(self, 'emailed_at', isdate=True)

        return brs

    def _create(self):
        
        return """
        create table leads(
            id int(6) unsigned auto_increment primary key,
            name varchar(255) not null,
            email varchar(255) not null,
            subject varchar(255) not null,
            message text not null,
            emailed_at datetime,
        )
        """

    def _alter(self):
        r = []
        
        r.append('alter table leads '
                 '    modify column emailed_at datetime(6)')

        return r

    def __str__(self):
        r  =   'Name:     '  +  str(self.name)     +  '\n'
        r  +=  'Email:    '  +  str(self.email)    +  '\n'
        r  +=  'Subject:  '  +  str(self.subject)  +  '\n'
        r  +=  'Message:  '  +  str(self.message)  +  '\n'
        return r

    def __repr__(self):
        r = super().__repr__()
        r += ' id: ' + str(self.id)
        r += ' name: ' + self.name
        r += ' email: ' + self.email
        return r


