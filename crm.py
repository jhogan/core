from pdb import set_trace; B=set_trace
from db import connections, dbentity, dbentities, dbresult

class leads(dbentities):

    @staticmethod
    def getunemailed():
        sql = """
        select *
        from leads
        where emailed = %s
        """

        conn = connections.getinstance().default
        res = conn.query(sql, (False,))

        ls = leads()
        for r in res:
            ls += lead(r)

        return ls


class lead(dbentity):
    def __init__(self, v=None):
        super().__init__()

        if v == None:
            ls = [''] * 5 + [False]
        elif type(v) == dbresult:
            ls = list(v)

        self._id,      self.name,     self.email, \
        self.subject,  self.message,  self.emailed  =  ls

    def _insert(self):
        insert = """
        insert into leads
        values(null, %s, %s, %s, %s, %s);
        """
        conn = connections.getinstance().default
        conn.query(insert, (self.name, self.email, self.subject, self.message, self.emailed))

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
        r  +=  'message:  '  +  self.message  +  '\n'
        return r

