from pdb import set_trace; B=set_trace
import db
from entities import brokenrules

class leads(db.dbentities):
    def __init__(self, rset=None):
        super().__init__()
        if rset != None:
            for r in rset:
                self += lead(r)


    @staticmethod
    def getunemailed():
        sql = """
        select *
        from leads
        where emailed = %s
        """
        conn = db.connections.getinstance().default
        res = conn.query(sql, (None,))

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
        elif type(v) == db.dbresultset:
            if v.hasone:
                ls = list(v.first)
            else:
                ls = [None] * 5

        self._id,      self.name, self.email, \
        self.subject,  self.message, \
        self.emailed = ls

    def _insert(self):
        insert = """
        insert into leads
        values(null, %s, %s, %s, %s, %s);
        """
        conn = db.connections.getinstance().default
        res = conn.query(insert, (self.name, self.email, self.subject, self.message, self.emailed))

        self._id = res.lastrowid

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
        
        if self.emailed != None:
            brs.demand(self, 'emailed', isdate=True)


        return brs

    def _create(self):
        
        return """
        create table leads(
            id int(6) unsigned auto_increment primary key,
            name varchar(255) not null,
            email varchar(255) not null,
            subject varchar(255) not null,
            message text not null,
            emailed bit not null
        )
        """

    def __str__(self):
        r  =   'Name:     '  +  self.name     +  '\n'
        r  +=  'Email:    '  +  self.email    +  '\n'
        r  +=  'Subject:  '  +  self.subject  +  '\n'
        r  +=  'Message:  '  +  self.message  +  '\n'
        return r

