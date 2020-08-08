#!/usr/bin/python3 -i
# vim: set et ts=4 sw=4 fdm=marker

# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2019

from config import config
from configfile import configfile
from dbg import B
from func import enumerate
import db
import effort
import entities
import _mysql_exceptions
import order
import orm
import os
import party
import pathlib
import product
import pygments
import pygments.formatters
import pygments.lexers
import ship
import tempfile
import textwrap

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

class undef: pass

class process:
    class onaskeventargs(entities.eventargs):
        def __init__(self, msg, yesno, default, **kwargs):
            self.message   =  msg
            self.yesno     =  yesno
            self.default   =  default
            self.kwargs    =  kwargs
            self.response  =  None

    def __init__(self):
        self.onask = entities.event()
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

    class Abort(Exception): pass

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

class migration(process):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._done      =  entities.entities()
        self._skipped   =  entities.entities()
        self._failed    =  entities.entities()
        self._todo      =  entities.entities()
        self._isscaned  =  False
        self._tmp       =  None

        try:
            self()
        except process.Abort:
            pass
        except:
            raise
        finally:
            self.destructor()

    def counts(self, e=None):
        self.print()
        def show(es):
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
                    f'{self.getoperation(e1)} '
                    f'{self.getname(e1)}',
                )

            self.print()

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
        if self._tmp is not None:
            os.remove(self._tmp)

    @property
    def tmp(self):
        # Create a tmp file
        if not self._tmp:
            _, self._tmp = tempfile.mkstemp()
        return self._tmp

    @property
    def editor(self):
        # Get an editor that the user likes
        return os.getenv('EDITOR') or '/usr/bin/vim'

    @staticmethod
    def getddl(e):
        if isinstance(e, db.table):
            return f'DROP TABLE `{e.name}`;'
        else:
            ddl = e.orm.altertable
            if ddl:
                return ddl
            else:
                return e.orm.createtable

    def exec(self, e=None, ddl=None):
        while True:
            try:
                ddl = ddl or self.getddl(e)
                orm.orm.exec(ddl)
            except Exception as ex:
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

    def exec_edited_alter_table(self, e):
        at = None
        while True:
            # Execute the edited ALTER TABLE statement
            at = self.edit(e, at)

            try:
                orm.orm.exec(at)
            except Exception as ex:
                self.print(f'\n{ex}\n\n')
                res = self.ask(
                    'Press [e]dit, [i]gnore or [q]uit...',
                    edit='e', ignore='i', quit='q'
                )
                if res == 'ignore':
                    return
                elif res == 'quit':
                    raise process.Abort()
            else:
                break

    def process_all(self):
        def usage():
            self.print(textwrap.dedent("""
            y - yes, apply DDL
            n - no, do not apply DDL
            q - quit migration
            e - manually edit the current DDL
            h - print help
            """))

        def abort():
            self.print('You have chosen to ignore. Bye.')
            self.skipped += self.todo
            self.counts()
            raise self.Abort()

        ddls = str()
        for e in self.todo:
            ddl = self.getddl(e)
            if ddl.startswith('ALTER'):
                ddls += f'\n/*\n{e.orm.migration.table!s}*/\n\n'
            else:
                ddls += '\n'

            ddls += ddl

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
                    # and exit the process.
                    abort()
                return
            elif res == 'quit':
                raise self.Abort()
            elif res == 'help':
                usage()

    def edit(self, e=None, ddl=None):
        if not ddl:
            ddl = self.getddl(e)

            if ddl.startswith('ALTER'):
                tbl = e.orm.migration.table
                ddl += f'\n\n/* Model-to-table comparison: \n{tbl}\n*/'
        
        # Write the ALTER TABLE to the tmp file
        with open(self.tmp, 'w') as f:
            f.write(ddl)

        flags = ''
        basename = os.path.basename(self.editor)
        if basename in ('vi', 'vim'):
            flags = '-c "set syn=sql"'
        if flags:
            flags = f' {flags} '

        os.system(f'{self.editor}{flags}{self.tmp}')

        # Read back in the edited file
        with open(self.tmp, mode='r') as f:
            ddl = f.read()

        return ddl

    def scan(self):
        if not self._isscaned:
            self.print('Scanning for entities to migrate ...\n')

            try:
                self._todo += orm.migration().entities
            except:
                raise
            finally:
                self._isscaned = True

            es = self.todo

            self.sort(es)

            if es.count:
                self.print(f'There are {es.count} entities to migrate:')

            for e in es:
                self.print(
                    f'    {self.getoperation(e)} {self.getname(e)}'
                )

            self.print()

    @staticmethod
    def getname(e):
        if isinstance(e, db.table):
            return e.name
        else:
            return f'{e.__module__}.{e.__name__}'

    @staticmethod
    def getoperation(e):
        if isinstance(e, db.table):
            return 'D'
        else:
            return 'A' if e.orm.dbtable else 'C'

    def _key(e):
        if isinstance(e, db.table):
            return 0
        else:
            return 1 if e.orm.dbtable else 2

    @staticmethod
    def sort(es):
        return es.sort(key=mig._key)

    @staticmethod
    def sorted(es):
        return es.sorted(key=mig._key)

    @property
    def todo(self):
        self.scan()
        es = self._todo - self.done - self.failed - self.skipped
        self.sort(es)
        return es

    @property
    def done(self):
        return self._done

    @done.setter
    def done(self, v):
        self._done = v
        
    @property
    def skipped(self):
        return self._skipped

    @skipped.setter
    def skipped(self, v):
        self._skipped = v

    @property
    def failed(self):
        return self._failed

    @failed.setter
    def failed(self, v):
        self._failed = v

    def __call__(self):
        def usage():
            print(textwrap.dedent("""
            y - yes, apply DDL
            n - no, do not apply DDL
            q - quit migration
            a - apply this DDL and all later DLL
            e - manually edit the current DDL
            s - show current DDL
            c - show counts
            h - print help
            """))

        self.scan()

        def show(e):
            ddl = self.getddl(e)
            if ddl.startswith('ALTER'):
                self.print(f'\n{e.orm.migration.table!s}')
            else:
                self.print()

            self.print(ddl, lang='sql')

            return ddl

        es = self.todo
        for i, e in es.enumerate():
            ddl = show(e)

            while True:
                res = self.ask(
                    'Apply this DDL [y,n,q,a,e,s,c,h]?', yesno=True, 
                    quit='q', all='a', edit='e', show='s', help='h',
                    counts='c',
                )

                if res == 'show':
                    show(e)
                elif res == 'help':
                    usage()
                elif res == 'counts':
                    self.counts(e)
                else:
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
                raise process.Abort()
            elif res == 'all':
                try:
                    res = self.process_all()
                except self.Abort:
                    raise
                except Exception as ex:
                    self.print(f'\nException: {ex}')
                    self.failed += self.todo
            elif res == 'edit':
                ddl = self.edit(ddl=ddl)
                try:
                    self.exec(ddl=ddl)
                except self.Abort:
                    raise
                except _mysql_exceptions.MySQLError as ex:
                    self.skipped += e
                except Exception as ex:
                    self.print(f'\nException: {ex}')
                    self.failed += self.todo
                else:
                    self.done += e


# A user-friendly alias
mig = migration

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
mig()
