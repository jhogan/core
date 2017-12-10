from pdb import set_trace; B=set_trace
from entities import connections, dbentity

class lead(dbentity):
    def __init__(self):
        super().__init__()
        self.name = ''
        self.subject = ''
        self.message = ''

    def save(self):

        insert = """
        insert into leads
        values(null, %s, %s, %s);
        """
        conn = connections.getinstance().default
        conn.query(insert, (self.name, self.subject, self.message))

