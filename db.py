# vim: set et ts=4 sw=4 fdm=marker

# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2019

# TODO Add Tests
from entities import *
from MySQLdb.constants.ER import BAD_TABLE_ERROR
import _mysql_exceptions
import table as tblmod
import MySQLdb
import warnings
import uuid
import func
from contextlib import contextmanager
from dbg import B
from config import config
import accounts

# Some errors in MySQL are classified as "warnings" (such as 'SELECT
# 0/0').  This means that no exception is raised; just an error message
# is printed to stderr. We want these warnings to be proper exceptions
# so they won't go unnoticed. The below code does just that.
warnings.filterwarnings('error', category=MySQLdb.Warning)

class dbentities(entities):
    def __init__(self, ress=None):
        super().__init__()
        self._isdirty = False

        if ress:
            for res in ress:
                self += self.dbentity(res)

        # The collection may have been added to above. If that is the
        # case, the _isdirty flag will be set to True in the _self_onadd
        # event handler.  Set it back to False since we are just
        # __init__'ing the object; it shouldn't be dirty at this point.

        self._isdirty = False

    def TRUNCATE(self):
        conn = connections.getinstance().default
        conn.query('truncate ' + self._table)

    def ALL(self):
        conn = connections.getinstance().default
        ress = conn.query('select * from ' + self._table)
        return type(self)(ress)

    def _self_onadd(self, src, eargs):
        super()._self_onadd(src, eargs)
        self._isdirty = True

    def _self_onremove(self, src, eargs):
        super()._self_onremove(src, eargs)
        self._isdirty = True

    @property
    def isdirty(self):
        return self._isdirty or any([x.isdirty for x in self])

    @property
    def isnew(self):
        return any([x.isnew for x in self])

    @property
    def _table(self):
        msg = '_table must be overridden'
        raise NotImplementedError(msg)

    @property
    def _create(self):
        raise NotImplementedError('_create must be overridden')

    @property
    def connection(self):
        return connections.getinstance().default

    def query(self, sql, args=None, cur=None):
        return self.connection.query(sql, args, cur=None)

    def CREATE(self):
        self.query(self._create)

    def DROP(self):
        self.query('drop table ' + self._table)

    def RECREATE(self):
        try:
            self.DROP()
        except MySQLdb.OperationalError as ex:
            try:
                errno = ex.args[0]
            except:
                raise

            if errno != BAD_TABLE_ERROR: # 1051
                raise

        self.CREATE()

    def save(self, cur=None):
        # TODO Add reconnect logic or a connection pool

        # Clone the default connection. Since transactions are commited
        # by calling commit() on the connection object, we want a new 
        # connection to ensure this transaction is atomic. I'm not sure
        # why MySQLDb uses the connection object for commits. It seems 
        # like there should be a transaction object that commit() could 
        # be called on. Either way, it seems like for now at least, we
        # will have to connect to the database each time there is a need
        # for atomic commits.
        # https://stackoverflow.com/questions/50206523/can-you-perform-multiple-atomic-commits-using-the-same-connection-with-mysqldb

        # If a cursor was not given, we will manage the atomicity of the
        # transaction here. Otherwise, we will assuming the calling code is
        # managing the atomicity.
        tx = not bool(cur)

        if not cur:
            conn = connections.getinstance().default.clone()
            cur = conn.createcursor()
        states = []
        try:
            for e in self:
                states.append((e._isnew, e._isdirty))
                e.save(cur)
        except Exception:
            for i, st in enumerate(states):
                e = self[i]
                e._isnew, e._isdirty = st
            if tx:
                conn.rollback()
            raise
        else:
            if tx:
                conn.commit()
        finally:
            if tx:
                cur.close()
                conn.close()

    def __getitem__(self, key):
        if type(key) == int or type(key) == slice:
            return self._ls[key]

        for e in self._ls:
            if hasattr(e, 'id') and type(key) == uuid.UUID :
                if e.id == key:   return e
            elif hasattr(e, 'name'):
                if e.name == key: return e

    def _tostr(self, fn=str, includeHeader=True, props=None):
        import functools

        def getattr(obj, attr, *args):
            def rgetattr(obj, attr):
                if obj:
                    return builtins.getattr(obj, attr, *args)
                return None
            return functools.reduce(rgetattr, [obj] + attr.split('.'))

        tbl = tblmod.table()

        if props:
            props = ('ix', 'id') + tuple(props)
        else:
            props = ('ix', 'id')


        if includeHeader:
            r = tbl.newrow()
            for prop in props:
                r.newfield(prop)
            
        for p in self:
            r = tbl.newrow()
            for prop in props:
                if prop == 'ix':
                    v = self.getindex(p)
                else:
                    v = getattr(p, prop)
                    v = v if v else ''
                r.newfield(v)
        return str(tbl)


    def __str__(self):
        return self._tostr()

class dbentity(entity):
    # TODO Add Tests
    def __init__(self, id=None):
        super().__init__()
        self._deleteme = False
        self.onaftervaluechange  +=  self._self_onaftervaluechange

    def _marknew(self):
        self._isnew = True
        self._isdirty = False

    def _markdirty(self):
        self._isdirty = True

    def _markold(self):
        self._isnew = False
        self._isdirty = False

    def markfordeletion(self):
        self._deleteme = True

    def _self_onaftervaluechange(self, src, eargs):
        if not self.isnew:
            self._markdirty()

    @property
    def isnew(self):
        return self._isnew

    @property
    def isdirty(self):
        return self._isdirty 

    @property
    def id(self):
        return self._id

    @property
    def _table(self):
        return self._collection()._table

    @property
    def connection(self):
        return connections.getinstance().default

    def query(self, sql, args, cur=None):
        return self.connection.query(sql, args, cur)

    def save(self, cur=None):
        if not (self.isnew or self.isdirty or self._deleteme):
           return

        if self._deleteme:
            if self._isnew:
               raise Exception("Can't delete row that doesn't exist.")
            else:
                self._delete()

        if self.isvalid:
            if self.isnew:
                self._insert(cur)
            elif self.isdirty:
                self._update()
            self._isdirty = False
            self._isnew = False
        else:
            raise BrokenRulesError('Won\'t save invalid object', self)

    def delete(self):
        sql = 'delete from ' + self._table + ' where id = %s'

        args = (self.id.bytes,)

        ress = self.query(sql, args)

        self._marknew()

        return ress.rowcount

class connections(entities):
    _instance = None
    def __init__(self):
        super().__init__()
        cfg = config()
        for acct in cfg.accounts:
            if isinstance(acct, accounts.mysql):
                self += connection(acct)

    @classmethod
    def getinstance(cls):
        if cls._instance == None:
            cls._instance = connections()
        return cls._instance

    @property
    def default(self):
        return self.first

class connection(entity):
    def __init__(self, acct):
        self._account = acct
        self._conn = None

    def clone(self):
        return type(self)(self._account)

    @property
    def account(self):
        return self._account

    def __repr__(self):
        conn = self._connection
        return '%s (Open: %s)' % (self.account.url, str(bool(conn.open)))

    @property
    def _connection(self):
        if not self._conn:
            acct = self.account
            self._conn = MySQLdb.connect(acct.host, acct.username, 
                                         acct.password, acct.database, 
                                         port=acct.port, charset='utf8mb4',
                                         use_unicode=True)
        return self._conn                

    def kill(self):
        try:
            _conn = self._connection
            id = _conn.thread_id()
            _conn.kill(id)
        except MySQLdb.OperationalError as ex:
            # If exception isn't 1317, 'Query execution was interrupted'),
            # re-raise
            if ex.args[0] not in (1317, 2006):
                raise

    def close(self):
        return self._connection.close()

    @property
    def isopen(self):
        return bool(self._connection.open)

    def commit(self):
        return self._connection.commit()

    def rollback(self):
        return self._connection.rollback()

    def createcursor(self):
        return self._connection.cursor()

    def reconnect(self):
        self._conn = None # force a reconnect
        self._connection

    def query(self, sql, args=None, cur=None):
        if cur != None:
            cur.execute(sql, args)
            return dbresultset(cur)

        for _ in range(2):
            conn = None
            try:
                conn = self._connection
                cur = conn.cursor()
                cur.execute(sql, args)
                conn.commit()
                return dbresultset(cur)
            except MySQLdb.OperationalError as ex:
                # Reconnect if the connection object has timed out and no
                # longer holds a connection to the database.
                # https://stackoverflow.com/questions/3335342/how-to-check-if-a-mysql-connection-is-closed-in-python

                try:
                    errno = ex.args[0]
                except:
                    errno = ''

                isopen = conn and conn.open

                if errno == 2006 or not isopen:
                    msg = 'Reconnect[{0}]: errno: {1}; isopen: {2}'
                    msg = msg.format(_, errno, isopen)

                    self.log.debug('Reconnect ' + str(_))
                    self.reconnect()
                else:
                    raise


# TODO The 'db' prefix on these class names are redundant.
class dbresultset(entities):
    """ Represents a collections of rows returned from a db query. """
    def __init__(self, cur):
        super().__init__()
        self._cur = cur
        for r in self._cur:
            self += dbresult(r, self)

    @property
    def lastrowid(self):
        return self._cur.lastrowid

    @property
    def rowcount(self):
        return self._cur.rowcount

    def demandhasone(self):
        if not self.hasone:
            raise RecordNotFoundError('A single record was not found')
        return self.first

    def __repr__(self):
        tbl = tblmod.table()

        for i, res in func.enumerate(self):
            if i.first:
                hdr = tbl.newrow()
                for f in res.fields:
                    hdr.newfield(f.name)

            r = tbl.newrow()
            for f in res.fields:
                r.newfield(f.value)

        return str(tbl)

    def __str__(self):
        return repr(self)

class dbresult(entity):
    """ Represents a row returned from a db query. """
    def __init__(self, row, ress):
        super().__init__()
        self._row = row
        self._ress = ress
        self.fields = dbresultfields()
        for i, _ in enumerate(self._row):
            self.fields += dbresultfield(i, self)

    def __getitem__(self, i):
        if type(i) is str:
            # If i is str, it's a column name. Use the description property to
            # get the index to pass to _row
            desc = self._ress._cur.description
            i = [x[0] for x in desc].index(i)
        return self._row[i]

class dbresultfields(entities):
    pass

class dbresultfield(entity):
    """ Represents a field within a dbresult. """
    def __init__(self, ix, res):
        self.index = ix
        self.dbresult = res
    
    @property
    def name(self):
        desc = self.dbresult._ress._cur.description
        return desc[self.index][0]

    @property
    def value(self):
        return self.dbresult._row[self.index]

class RecordNotFoundError(Exception):
    pass

class pool(entity):
    _default = None

    def __init__(self):
        # TODO Currently, connections.__init__() populates itself with
        # connection objects from the config file so we can't use it for
        # collecting connections objects that are in and out of the pool.
        self._in = entities()
        self._out = entities()

    @staticmethod
    def getdefault():
        if not pool._default:
            pool._default = pool()

            # Seed with one connection
            pool._default._in += connections.getinstance().default.clone()
        return pool._default

    def pull(self):
        conn = self._in.pop()

        # Grow as needed
        if not conn:
            conn = self._out.last.clone()

        self._out += conn

        return conn

    def push(self, conn):
        self._in += self._out.remove(conn)

    @contextmanager
    def take(self):
        conn = self.pull()

        yield conn

        self.push(conn)

class operationeventargs(eventargs):
    def __init__(self, e, op, sql, args):
        self.entity  =  e
        self.op      =  op
        self.sql     =  sql
        self.args    =  args

class chronicler(entity):
    _instance = None

    def __init__(self):
        self.chronicles = chronicles(self)
        self.max = 20

    @staticmethod
    def getinstance():
        if not chronicler._instance:
            chronicler._instance = chronicler()
        return chronicler._instance

    @contextmanager
    def snapshot(dev=True):
        def chr_onadd(src, eargs):
            nonlocal chrs
            chrs += eargs.entity

        chr = chronicler.getinstance()
        chrs = chronicles()
        chr.chronicles.onadd += chr_onadd

        yield chrs

        if dev == True:
            print(chrs)
        elif not dev:
            pass
        else:
            # TODO Write to device 'dev'
            pass

    def append(self, obj):
        self.chronicles += obj

    def __iadd__(self, t):
        self.append(t)
        return self

class chronicles(entities):
    def __init__(self, chronicler=None, initial=None):
        self.chronicler = chronicler
        super().__init__(initial=initial)

    def clone(self):
        r = chronicles()
        for chron in self:
            r += chron.clone()
        return r

    def append(self, obj, uniq=False, r=None):
        if self.chronicler and self.count == self.chronicler.max - 1:
            self.shift()
        
        super().append(obj, uniq=False, r=None)

    def where(self, p1, p2=None):
        if (type(p1), type(p2)) == (str, type(None)):
            # Passing in one argument will result in a test of p1 against
            # the value of 'op'.
            p1, p2 = 'op', p1

        return super().where(p1, p2)

    def __str__(self):
        return self._tostr(includeHeader=False)

class chronicle(entity):
    def __init__(self, e, op, sql, args):
        self.entity  =  e
        self.op      =  op
        self.sql     =  sql
        self.args    =  args

    def __str__(self):
        if self.op in ('reconnect',):
            return 'DB: ' + self.op.upper()

        args = []
        for arg in self.args:
            if type(arg) is bytes:
                try:
                    arg = uuid.UUID(bytes=arg)
                except:
                    pass
            args.append(arg)
        sql = self.sql.strip()

        r = '%s\n%s\n'
        r %= (
            sql,
            tuple(args)
        )
        return r

    def clone(self):
        return chronicle(self.entity, self.op, self.sql, self.args)

# TODO s/executioner/executor/
class executioner(entity):
    def __init__(self, exec, max=2):
        self._execute = exec
        self.max = max
        self.onbeforereconnect  =  event()
        self.onafterreconnect   =  event()
    
    def __call__(self, es=None):
        self.execute(es)

    def execute(self, es=None):
        pl = pool.getdefault()
        for i in range(self.max):
            conn = pl.pull()
            cur = conn.createcursor()

            try:
                if es:
                    self._execute(cur, es)
                else:
                    self._execute(cur)
            except MySQLdb.OperationalError as ex:
                # Reconnect if the connection object has timed out and no
                # longer holds a connection to the database.
                # https://stackoverflow.com/questions/3335342/how-to-check-if-a-mysql-connection-is-closed-in-python

                if i + 1 == self.max:
                    raise

                try:
                    errno = ex.args[0]
                except:
                    errno = ''

                if errno in (2006, 2013) or not conn.isopen:
                    msg = 'Reconnect[{0}]: errno: {1}; isopen: {2}'
                    msg = msg.format(i, errno, conn.isopen)
                    self.log.debug(msg)

                    eargs = operationeventargs(self, 'reconnect', None, None)
                    self.onbeforereconnect(self, eargs)

                    conn.reconnect()

                    self.onafterreconnect(self, eargs)
                else:
                    conn.rollback()
                    raise
            except Exception as ex:
                conn.rollback()
                raise
            else:
                conn.commit()
                return
            finally:
                cur.close()
                pl.push(conn)

def exec(sql, args=None):
    exec = executioner(
        lambda cur: cur.execute(sql, args)
    )

    exec()

class catelogs(entities):
    pass

class catelog(entity):
    @property
    def tables(self):
        return tables()

class tables(entities):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        with pool.getdefault().take() as conn:
            sql = '''
            select *
            from information_schema.columns
            where table_schema = %s;
            '''

            ress = conn.query(sql, (conn.account.database,))

            # TODO The below could be unindented to allow the pool the
            # recover its connection.
            tbls = dict()
            for res in ress:

                fld = res.fields['TABLE_NAME']
                name = fld.value

                try:
                    ress1 = tbls[name]
                except KeyError:
                    ress1 = list()
                    tbls[name] = ress1

                ress1.append(res) 

            for name, ress in tbls.items():
                self += table(name=name, ress=ress)

    def drop(self):
        for tbl in self:
            tbl.drop()

class table(entity):
    def __init__(self, name=None, ress=None, load=True):
        self.name = name
        self.columns = columns(tbl=self, ress=ress, load=load)

    def clone(self):
        tbl = table(name=self.name, load=False)
        tbl.columns += self.columns.clone(self)
        return tbl

    def __repr__(self):
        r = 'CREATE TABLE %s (\n'
        for i, col in self.columns.enumerate():
            if not i.first:
                r += ',\n'
            r += '    %s' % str(col)
        r += '\n)'
        return r % self.name

    def drop(self):
        exec(f'DROP TABLE `{self.name}`')

class columns(entities):
    def __init__(self, 
            tbl=None, ress=None, load=False, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.table = tbl

        # Don't load if there is no ``table``. We probably just want to
        # use ``columns`` for collecting ``column`` objects
        if load:
            pl = pool.getdefault()
            with pl.take() as conn:

                sql = '''select *
                from information_schema.columns
                where table_schema = %s
                    and table_name = %s
                '''
                ress = conn.query(
                    sql, (conn.account.database, tbl.name)
                )

            if not ress.count:
                # If no columns were returned then tbl.name doesn't
                # exist in the database, so throw the kind of
                # exception MySQLdb would.
                raise _mysql_exceptions.OperationalError(
                    BAD_TABLE_ERROR, 'Table not found'
                )

        if ress is not None:
            for res in ress:
                self += column(res)

    def clone(self, tbl):
        cols = columns(tbl=tbl, load=False)
        for col in self:
            cols += col.clone()

        return cols

class column(entity):
    _attrs = (
        'name',       'ordinal',  'type',       'max',
        'key',        'type',     'precision',  'scale',
        'columntype'
    )

    def __init__(self, res=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.columntype = None
        if res:
            self.populate(res)

    def clone(self):
        col = column()

        for attr in self._attrs:
            setattr(col, attr, getattr(self, attr))

        return col

    @property
    def issigned(self):
        ints = (
            'tinyint',
            'smallint',
            'mediumint',
            'int',
            'bigint',
        )

        if self.type not in ints:
            return None

        if self.columntype:
            t = self.columntype
        else:
            t = self.type

        if ' unsigned' in t:
            return False
        else:
            return True
            
    def populate(self, res):
        if isinstance(res, dbresult):
            flds = res.fields
            self.name = flds['COLUMN_NAME'].value
            self.ordinal = flds['ORDINAL_POSITION'].value
            self.type = flds['DATA_TYPE'].value
            self.max = flds['CHARACTER_MAXIMUM_LENGTH'].value
            self.key = flds['COLUMN_KEY'].value
            self.columntype = flds['COLUMN_TYPE'].value
            if self.type == 'datetime':
                self.precision = flds['DATETIME_PRECISION'].value
            else:
                self.precision = flds['NUMERIC_PRECISION'].value
            self.scale = flds['NUMERIC_SCALE'].value
        elif res is not None:
            # If res looks like a column, we can use the column class`s
            # attributes (``column._attrs``)

            for attr in self._attrs:
                try:
                    v = getattr(res, attr)
                except AttributeError:
                    if attr != 'key':
                        raise
                else:
                    # NOTE orm.mapping has a dbtype property that returns a
                    # string version of the type, which is what we want.
                    # I believe this is slated to be corrected, so we
                    # may want to move this conditional when
                    # mapping.type returns a string version.
                    if attr == 'type' and not isinstance(v, str):
                        v = res.dbtype

                    # mapping.ordinal means something different than
                    # column.ordinal, so lets just set it to None
                    if attr == 'ordinal':
                        v = None

                    setattr(self, attr, v)

            if not hasattr(self, 'key'):
                if self.name == 'id':
                    self.key = 'pri'
                else:
                    self.key = None

    def __repr__(self):
        r = 'column(' 
        for i, attr in enumerate(self._attrs):
            if not i.first:
                r += ', '
            r += f'{attr}={getattr(self, attr)}'
        r += ')'
        return r

    def __str__(self):
        return '%s %s' % (self.name, self.definition)


    @property
    def isprimary(self):
        return self.key and self.key.lower() == 'pri'

    @property
    def definition(self):
        """ The portion of a CREATE TABLE or ALTER TABLE statement that
        would define a column::

        ALTER TABLE mytable
            ADD mybit BIT   -- "mybit BIT' is the definition
                ---------
        """
        ints = (
            'tinyint',
            'smallint',
            'mediumint',
            'int',
            'bigint',
        )

        r = self.type

        if self.type == 'datetime':
            r += f'({self.precision})'
        elif self.type == 'decimal':
            r += f'({self.precision}, {self.scale})'
        elif self.type in ('binary', 'varchar', 'char'):
            r += f'({self.max})'
        elif self.type in ints:
            if not self.issigned:
                r += f" {'' if self.issigned else 'unsigned'}"

        if self.isprimary:
            r += ' primary key'

        return r
