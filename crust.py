#!/usr/bin/python3 -i
# vim: set et ts=4 sw=4 fdm=marker

# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2019

import pygments
import pygments.lexers
import pygments.formatters
import party
import product
import order
import ship
import effort
from configfile import configfile
from dbg import B
import pathlib
import db
import orm
from config import config
import tempfile
import os
import textwrap
from func import enumerate

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

    def print(self, msg, lang=None):
        if lang:
            if lang not in ('sql',):
                raise ValueError("Supported languages: 'sql'")

            if lang == 'sql':
                lex = self.mysqllexer

            msg = pygments.highlight(msg, lex, self.formatter)

        print(msg)

    def say(self, msg):
        print(msg)

    def ask(self, msg, yesno=True, default=undef, **kwargs):
        res = None
        while not res:
            res = input(f'{msg} ').lower()
            if not res and default is not undef:
                return default

        if yesno:
            if res in ('y', 'yes'):
                return 'yes'
            elif res in ('n', 'no'):
                return 'no'

        for k, v in kwargs.items():
            if res == v:
                return k

        return res
    
class mig(process):
    def __init__(self):
        self._done = orm.ormclasseswrapper()
        self._failed = orm.ormclasseswrapper()
        self._todo = orm.ormclasseswrapper()
        self._isscaned = False
        self._tmp = None
        try:
            self()
        except process.Abort:
            pass
        except:
            raise
        finally:
            self.destructor()
    
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

    def exec_alter_table(self, e=None, at=None):
        try:
            at = at or e.orm.altertable
            orm.orm.exec(at)
        except Exception as ex:
            self.say(f'\n{ex}\n\n')
            res = self.ask(
                'Press [e]dit, [i]gnore or [q]uit...',
                edit='e', ignore='i', quit='q'
            )
            if res == 'edit':
                self.edit_alter_table(at=at)

            elif res == 'ignore':
                raise
            elif res == 'quit':
                raise self.Abort()

    def exec_edited_alter_table(self, e):
        at = None
        while True:
            # Execute the edited ALTER TABLE statement
            at = self.edit_alter_table(e, at)

            try:
                orm.orm.exec(at)
            except Exception as ex:
                self.say(f'\n{ex}\n\n')
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
        ddl = str()
        for e in self.todo:
            at = e.orm.altertable
            ddl += f'{at}\n\n'

        self.print(ddl, lang='sql')
        res = self.ask(
            f'Execute the above DDL? [Yn]', yesno=True, default='yes'
        )
        if res == 'yes':
            self.exec_alter_table(at=ddl)
        elif res == 'no':
            B()
            return 'abort'

    def edit_alter_table(self, e, at=None):
        if not at:
            at = e.orm.altertable
            tbl = e.orm.migration.table
            at = (
                f'{at}\n\n'
                f'/* Model-to-table comparison: \n{tbl}\n*/'
            )
        
        # Write the ALTER TABLE to the tmp file
        with open(self.tmp, 'w') as f:
            f.write(at)

        flags = ''
        basename = os.path.basename(self.editor)
        if basename in ('vi', 'vim'):
            flags = '-c "set syn=sql"'
        if flags:
            flags = f' {flags} '

        os.system(f'{self.editor}{flags}{self.tmp}')

        # Read back in the edited file
        with open(self.tmp, mode='r') as f:
            at = f.read()

        return at

    def scan(self):
        if not self._isscaned:
            self.say('Scanning for entities to migrate ...\n')

            try:
                self._todo += orm.migration().entities
            except:
                raise
            finally:
                self._isscaned = True


            es = self.todo
            if es.count:
                self.say(f'There are {es.count} entities to migrate:')

            for e in es:
                self.say(f'    - {e.__module__}.{e.__name__}')

    @property
    def done(self):
        return self._done

    @done.setter
    def done(self, v):
        self._done = v

    @property
    def failed(self):
        return self._failed

    @failed.setter
    def failed(self, v):
        self._failed = v

    @property
    def todo(self):
        self.scan()
        return self._todo - self.done - self.failed

    def __call__(self):
        def usage():
            print(textwrap.dedent("""
            y - yes, apply DDL
            n - no, do not apply DDL
            q - quit migration
            a - apply this DDL and all later DLL
            e - manually edit the current DDL
            h - print help
            """))

        start = self.ask(
            '\nWould you like to start [Yn]?', yesno=True, default='yes'
        )

        if start != 'yes':
            return

        self.scan()


        def show(e):
            at = e.orm.altertable
            tbl = e.orm.migration.table

            self.print(f'\n{tbl!s}')
            self.print(at, lang='sql')

        es = self.todo
        for i, e in es.enumerate():
            show(e)

            while True:
                res = self.ask(
                    'Apply this DDL [y,n,q,a,e,s,h]?', yesno=True, 
                    quit='q', all='a', edit='e', show='s', help='h'
                )

                if res == 'show':
                    show(e)
                elif res == 'help':
                    usage()
                else:
                    break

            if res == 'yes':
                try:
                    self.exec_alter_table(e)
                except:
                    self.failed += e
                else:
                    self.done += e

            elif res == 'no':
                continue
            elif res == 'quit':
                raise process.Abort()
            elif res == 'all':
                res = self.process_all()
                if res == 'abort':
                    continue
            elif res == 'edit':
                res = self.processes.process('edit')


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
