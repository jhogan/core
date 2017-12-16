from pdb import set_trace; B=set_trace
from db import connections, dbentity, dbentities

class leads(dbentities):

    @staticmethod
    def getunemailed():
        sql = """
        select *
        from leads
        where emailed = %s
        """

        conn = connections.getinstance().default
        cur = conn.query(sql, (False,))

        ls = leads()
        for r in cur:
            ls += lead(r)

        return ls


class lead(dbentity):
    def __init__(self):
        super().__init__()
        self.name = ''
        self.subject = ''
        self.message = ''

    def _insert(self):
        insert = """
        insert into leads
        values(null, %s, %s, %s);
        """
        conn = connections.getinstance().default
        conn.query(insert, (self.name, self.subject, self.message))

