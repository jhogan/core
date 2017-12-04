from entities import *
from pdb import set_trace; B=set_trace
import MySQLdb

class lead(entity):
    def __init__(self):
        self.name = ''
        self.subject = ''
        self.message = ''

    def save(self):

        insert = """
        insert into leads
        values(null, %s, %s, %s);
        """

        db = MySQLdb.connect('localhost', 'www', pwd, 'main')
        cur = db.cursor()
        B()
        cur.execute(insert, (self.name, self.subject, self.message))
        db.commit()

        db.close()


        
        
        

