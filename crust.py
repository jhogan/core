#!/usr/bin/python3 -i
# vim: set et ts=4 sw=4 fdm=marker

# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2019

from MySQLdb.constants.CR import COMMANDS_OUT_OF_SYNC
from config import config
from dbg import B
from func import enumerate
import db
import effort
import entities
import order
import orm
import os
import party
import pathlib
import product
import invoice
import pygments
import pygments.formatters
import pygments.lexers
import shipment
import tempfile
import textwrap
import account
import MySQLdb

def dbg(code):
    try:
        exec(code)
    except Exception as ex:
        print(ex)
        pdb.post_mortem(ex.__traceback__)

def rf(file):
    p = pathlib.Path(file)
    return p.read_text()

def wf(file, txt):
    p = pathlib.Path(file)
    return p.write_text(txt)

class undef: 
    pass

class command:
    class onaskeventargs(entities.eventargs):
        def __init__(self, msg, yesno, default, **kwargs):
            self.message   =  msg
            self.yesno     =  yesno
            self.default   =  default
            self.kwargs    =  kwargs
            self.response  =  None

    def __init__(self, onask=None):
        self.onask = entities.event()

        if onask:
            self.onask += onask
        else:
            self.onask += self.self_onask

    @property
    def formatter(self):
        if not hasattr(self, '_formatter'):
            self._formatter = pygments.formatters.TerminalFormatter()
        return self._formatter

    @property
    def mysqllexer(self):
        if not hasattr(self, '_mysqllexer'):
            self._mysqllexer = pygments.lexers.MySqlLexer()
        return self._mysqllexer

    class Abort(Exception):
        pass

    def print(self, msg='', lang=None, end='\n'):
        if lang:
            if lang not in ('sql',):
                raise ValueError("Supported languages: 'sql'")

            if lang == 'sql':
                lex = self.mysqllexer

            msg = pygments.highlight(msg, lex, self.formatter)

        print(msg, end=end)

    def self_onask(self, src, eargs):
        msg      =  eargs.message
        default  =  eargs.default
        yesno    =  eargs.yesno
        kwargs   =  eargs.kwargs

        res = None
        while not res:
            res = input(f'{msg} ').lower()
            if not res and default is not undef:
                eargs.response = default

        if yesno:
            if res in ('y', 'yes'):
                eargs.response = 'yes'
            elif res in ('n', 'no'):
                eargs.response = 'no'

        for k, v in kwargs.items():
            if res == v:
                eargs.response = k

        if not eargs.response:
            eargs.response = res

    def ask(self, msg, yesno=True, default=undef, **kwargs):
        eargs = self.onaskeventargs(
            msg=msg, yesno=yesno, default=default, **kwargs
        )

        self.onask(self, eargs)

        return eargs.response

class migration(command):
    """ A command to interactively walk a user through the migration
    process. It first scans the database table and compares them to all 
    orm.entity models. DDL is generated and presented to the user for
    each of the tables that need to be CREATed, ALTERed or DROPed. The
    user then reviews the DDL, is given the option of editing the DDL,
    then ask if the DDL should be executed by the database.
    """

    class migrants(entities.entities):
        """ A collection of ``migrant`` objects.
        """

        @staticmethod
        def _key(mig):
            """ Defines the sort order of the migrant:
                    0 - Tables that must be altered (A)
                    1 - Tables that must be dropped (D)
                    2 - Tables that must be created (C)
            """
            e = mig.entity
            if isinstance(e, db.table):
                return 1
            else:
                return 0 if e.orm.dbtable else 2

        def sort(self):
            """ Sorts the migrants using migrants._key.
            """
            super().sort(key=self._key)

        def sorted(self):
            """ Returns a sorted collection of migrants using
            migrants._key.
            """
            return super().sorted(key=self._key)

    class migrant(entities.entity):
        """ An entity that needs to be migrated. The entity may be a
        db.table object or an orm.entity. The main purpose of this class
        is to make working with db.table and orm.entity objects
        polymorphic. For instance, we can call the ``migraant.name``
        property to get the name of the entity which would be different
        depending on whether or not the entity is a db.table or a
        orm.entity (see the ``name`` property for more clarity).
        """

        def __init__(self, e, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.entity = e

        @property
        def istable(self):
            return isinstance(self.entity, db.table)

        @property
        def isormentity(self):
            return not self.istable

        @property
        def name(self):
            e = self.entity
            if self.istable:
                return e.name
            else:
                return f'{e.__module__}.{e.__name__}'

        def __repr__(self):
            return f'{self.operation} {self.name}'

        @property
        def operation(self):
            """ The DDL operation that should be performed on the
            migrant::
                
                D = DROP
                A = ALTER
                C = CREATE
            """
            if self.istable:
                return 'D'
            else:
                return 'A' if self.entity.orm.dbtable else 'C'

        @property
        def ddl(self):
            """ The DDL required to migrate the migrant.
            """

            if self.istable:
                return f'DROP TABLE `{self.name}`;'
            else:
                ddl = self.entity.orm.altertable
                if ddl:
                    return ddl
                else:
                    return self.entity.orm.createtable

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._todo      =  migration.migrants()
        self._done      =  migration.migrants()
        self._skipped   =  migration.migrants()
        self._failed    =  migration.migrants()
        self._isscaned  =  False
        self._tmp       =  None

        try:
            # Call self which initiates the process starting with a scan
            # of the orm entities and database tables.
            self()
        except command.Abort:
            pass
        except:
            raise
        finally:
            self.destructor()

    def counts(self, e=None):
        """ Print out the status the todo, done, skipped and failed
        migrants. If ``e`` is set, that migrant will get an arrow beside
        it to indicate it is the entity currently being subjected to
        the migration process.
        """
        self.print()
        def show(es):
            """ Print out information about the migration collection (``es``).
            """
            self.print(f'({es.count})', end='')
            if es.count:
                self.print(':')
            else:
                self.print()

            for e1 in es:
                if e and e is e1:
                    self.print('->  ', end='')
                else:
                    self.print('    ', end='')

                self.print(
                    f'{e1.operation} '
                    f'{e1.name} '
                )

            self.print()

        # Show status information for todo, done, skipped and failed
        # migrants.
        todo    =  self.todo
        done    =  self.done
        skipped =  self.skipped
        failed  =  self.failed

        self.print('todo', end='')
        show(todo)

        self.print('done', end='')
        show(done)

        self.print('skipped', end='')
        show(skipped)

        self.print('failed', end='')
        show(failed)
    
    def destructor(self):
        """ Clean up resources of the ``migration`` command.
        """

        # If there is a tmp file, delete it.
        if self._tmp is not None:
            os.remove(self._tmp)

    @property
    def tmp(self):
        """ Create a tmp file file in the file system and return a
        reference. 
        """

        # Memoize so we only have to worry about one tmp file throughout
        # the whole process.
        if not self._tmp:
            _, self._tmp = tempfile.mkstemp()
        return self._tmp

    @property
    def editor(self):
        """ Return a path to an editor. Default to Vim.
        """
        return os.getenv('EDITOR', '/usr/bin/vim')

    def exec(self, e=None, ddl=None):
        """ Send the DDL to the database for execution. If there is an
        exception during the execution, offer the user the option of
        editing the DDL.
        """
        while True:
            try:
                ddl = ddl or e.ddl
                orm.orm.exec(ddl)
            except Exception as ex:
                if type(ex) is MySQLdb.ProgrammingError:
                    if ex.args[0] == COMMANDS_OUT_OF_SYNC:
                        # This exception happens when the `commit`
                        # method is called afte we send multiple DDL
                        # statements to MySQL at once (typically by
                        # selecting [a]ll).  The DDL operations are
                        # performed correctly so we can just return.
                        # It's as if MySQL is saying, "You can't commit
                        # multiple DDLs because transactional support
                        # isn't implemented for them at the moment".
                        return
                
                self.print(f'\n{ex}\n\n')
                res = self.ask(
                    'Press [e]dit, [i]gnore or [q]uit...',
                    edit='e', ignore='i', quit='q'
                )
                if res == 'edit':
                    ddl = self.edit(ddl=ddl)
                    continue
                elif res == 'ignore':
                    raise
                elif res == 'quit':
                    raise self.Abort()
            else:
                return

    def all(self):
        """ Concatenate the DDL from all the ``todo`` migrants into one
        DDL script, print out the script (usually to stdout), apply the
        DDL or allow the user the option of editing.
        """

        def usage():
            """ Print help information.
            """
            self.print(textwrap.dedent("""
            y - yes, apply DDL
            n - no, do not apply DDL
            q - quit migration
            e - manually edit the current DDL
            h - print help
            """))

        def abort():
            """ Ignoring an exception from *all** implies that the user
            wants to abort the process, so add all the todo's to
            skipped, print out the counts and end the command.
            """
            self.print('You have chosen to ignore. Bye.')
            self.skipped += self.todo
            self.counts()
            raise self.Abort()

        # Concatenate DDL from each of the migrants into one DDL string.
        ddls = str()
        for mig in self.todo:
            e = mig.entity
            ddl = f'{mig.ddl}\n'
            if ddl.startswith('ALTER'):
                ddls += f'\n/*\n{e.orm.migration.table!s}*/\n\n'
            else:
                ddls += '\n'

            ddls += ddl

        # Print to stdout
        self.print(ddls, lang='sql')

        ddl = ddls.strip()
        while True:
            res = self.ask(
                f'Execute the above DDL? [yqeh]', 
                yesno=True, quit='q', edit='e', help='h'
            )

            if res == 'yes':
                try:
                    self.exec(ddl=ddl)
                    return
                except self.Abort:
                    raise
                except:
                    abort()
                 
            elif res == 'edit':
                ddl = self.edit(ddl=ddl)
                try:
                    self.exec(ddl=ddl)
                except self.Abort:
                    raise
                except:
                    # self.exec will only raise an exception if the user
                    # has chosen to ignore that happen within the
                    # method. So we are here because the user has
                    # ignored the exception caused by executing the
                    # concatenated DDL. In that case, print a summary
                    # and exit the command.
                    abort()
                return
            elif res == 'quit':
                raise self.Abort()
            elif res == 'help':
                usage()

    def edit(self, e=None, ddl=None):
        """ Put the DDL from `e` or the DDL rom `ddl` into an editor for the
        user to make changes. Return the edited DDL.
        """
        if not ddl:
            ddl = e.ddl

            # Add a commented-out comparison table to the DDL for the
            # user's convenience.
            if ddl.startswith('ALTER'):
                tbl = e.orm.migration.table
                ddl += f'\n\n/* Model-to-table comparison: \n{tbl}\n*/'
        
        # Write the ALTER TABLE to the tmp file
        with open(self.tmp, 'w') as f:
            f.write(ddl)

        # Add syntax highlighting if the editor is Vim.
        flags = ''
        basename = os.path.basename(self.editor)
        if basename in ('vi', 'vim'):
            flags = '-c "set syn=sql"'
        if flags:
            flags = f' {flags} '

        # Run the editor.
        os.system(f'{self.editor}{flags}{self.tmp}')

        # Read back in the edited file
        with open(self.tmp, mode='r') as f:
            ddl = f.read()

        return ddl

    def scan(self):
        """ Scan for orm entities and add them as migrants to the
        ``todo`` list.
        """
        if not self._isscaned:
            self.print('Scanning for entities to migrate ...\n')

            try:
                for e in orm.migration().entities:
                    self._todo += migration.migrant(e=e)
            except:
                raise
            finally:
                self._isscaned = True

            es = self.todo

            es.sort()

            if es.count:
                self.print(f'There are {es.count} entities to migrate:')

            for e in es:
                self.print(
                    f'    {e.operation} {e.name}'
                )

            self.print()

    @property
    def todo(self):
        """ Return a list of migrants that have yet to be processe"""

        # Make sure we've scanned and collected all the migrants.
        self.scan()

        # The returned todo migration won't include migrants that have
        # been done, failed or skipped.
        es = self._todo - self.done - self.failed - self.skipped

        # Ensure todo migrants are sorted (see migratants.sort)
        es.sort()
        return es

    @property
    def done(self):
        """ Migrants that have been successfully migrated.
        """
        return self._done

    @done.setter
    def done(self, v):
        self._done = v
        
    @property
    def skipped(self):
        """ Migrants that were skipped.
        """
        return self._skipped

    @skipped.setter
    def skipped(self, v):
        self._skipped = v

    @property
    def failed(self):
        """ Migrants that failed, likely because of a syntax error in
        the DDL.
        """
        return self._failed

    @failed.setter
    def failed(self, v):
        self._failed = v

    def __call__(self):
        """ Start the processes .
        """
        def usage():
            print(textwrap.dedent("""
            y - yes, apply DDL
            n - no, do not apply DDL
            q - quit migration
            a - apply this DDL and all later DDL
            e - manually edit the current DDL
            s - show current DDL
            c - show counts
            h - print help
            """))


        def show(mig):
            """ Show the DDL and comarison table of the migrant (mig).
            """
            e = mig.entity
            ddl = mig.ddl
            if ddl.startswith('ALTER'):
                self.print(f'\n{e.orm.migration.table!s}')
            else:
                self.print()

            self.print(ddl, lang='sql')

            return ddl

        self.scan()
        es = self.todo

        if not es.count:
            self.print('Model matches database. Bye.\n')
            raise self.Abort()

        # Work through each of the migrants in the todo list
        for i, e in es.enumerate():
            ddl = show(e)

            while True:
                # Offer the user to apply the migrant's DDL (y), show
                # the DDL, show information about the process (c), show
                # usage (h), concatenate the DDLs (a), quit the process
                # (q) or edit the current DDL (e).
                res = self.ask(
                    'Apply this DDL [y,n,q,a,e,s,c,h]?', yesno=True, 
                    quit='q', all='a', edit='e', show='s', help='h',
                    counts='c'
                )

                if res == 'show':
                    show(e)
                elif res == 'help':
                    usage()
                elif res == 'counts':
                    self.counts(e)
                else:
                    if res in ('yes', 'no', 'quit', 'all', 'edit'):
                        break

            if res == 'yes':
                try:
                    self.exec(ddl=ddl)
                except:
                    self.failed += e
                else:
                    self.done += e

            elif res == 'no':
                self.skipped += e
                continue
            elif res == 'quit':
                raise command.Abort()
            elif res == 'all':
                try:
                    res = self.all()
                except self.Abort:
                    raise
                except Exception as ex:
                    self.print(f'\nException: {ex}')
                    self.failed += self.todo
                else:
                    self.done += self.todo
                    self.print(
                        'All were applied successfully. Bye.'
                    )
                    self.counts()
                    break
            elif res == 'edit':
                ddl = self.edit(ddl=ddl)
                try:
                    self.exec(ddl=ddl)
                except self.Abort:
                    raise
                except MySQLdb.MySQLError as ex:
                    self.skipped += e
                except Exception as ex:
                    self.print(f'\nException: {ex}')
                    self.failed += self.todo
                else:
                    self.done += e

# A user-friendly alias
mig = migration

'''
Show environmental information on startup
'''
cfg = config()
acct = db.connections.getinstance().default.account

if cfg.inproduction:
    print("You are in a production environment".upper())
else:
    try:
        print('Environment: {}'.format(cfg.environment))
    except KeyError:
        print('Environment not set'.upper())


print("""
    Connected to:
        Host:     {}
        Username: {}
        Database: {}
        Port:     {}
    """.format(acct.host,
               acct.username,
               acct.database,
               acct.port)
)

