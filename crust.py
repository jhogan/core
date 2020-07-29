#!/usr/bin/python3 -i
# vim: set et ts=4 sw=4 fdm=marker

# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2019

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
def ask(msg, yesno=True, default=undef, **kwargs):
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

class process:
    def say(msg):
        print(msg)
    
class mig(process):
    def __init__(self):
        self._done = orm.ormclasseswrapper()
        self._todo = orm.ormclasseswrapper()
        self._isscaned = False

    class exec(self):
        def run(self):
            # Execute the edited ALTER TABLE statement
            try:
                orm.orm.exec(at)
            except Exception as ex:
                say(f'\n{ex}\n\n')
                res = ask(
                    'Press re[e]dit, [i]gnore or [q]uit...',
                    edit='e', ignore='i', quit='q'
                )
                if res == 'ignore':
                    break
                elif res == 'quit':
                    return
            else:
                break

    class all(process):
        def run(self):
            ddl = str()
            for j, e in enumerate(es[i:]):
                at = e.orm.altertable
                ddl += f'{at}\n\n'

            res = ask(f'{ddl}\nExecute the above DDL? [Yn]')
            if res == 'yes':
                say('executing...')
                return 'done'
            elif res == 'no':
                return 'abort'
    class edit(process):
        def __init__(self):
            self._tmp = None

        @property
        def tmp(self):
            # Create a tmp file
            if not self._tmp:
                _, self._tmp = tempfile.mkstemp()
            return self._tmp

        @property
        def editor(self):
            # Get an editor that the user likes
            editor = os.getenv('EDITOR') or '/usr/bin/vim'

        def edit(self):
            basename = os.path.basename(self.editor)
            
            flags = ''
            if basename in ('vi', 'vim'):
                flags = '-c "set syn=sql"'
            if flags:
                flags = f' {flags} '

            os.system(f'{editor}{flags}{tmp}')

        def run(self):
            # Write the ALTER TABLE to the tmp file
            with open(tmp, 'w') as f:
                f.write(
                    f'{at}\n\n'
                    f'/* Model-to-table comparison: \n{tbl}\n*/'
                )

            self.edit()

            # Read back in the edited file
            with open(tmp, mode='r') as f:
                at = f.read()

            self.processes.process('exec', at)



    def usage():
        print(textwrap.dedent("""
        y - yes, apply DDL
        n - no, do not apply DDL
        q - quit migration
        a - apply this DDL and all later DLL
        e - manually edit the current DDL
        h - print help
        """))

    def scan(self):
        tmp = None
        if not self._isscaned:
            self._todo += orm.migration().entities

            self.say('Scanning for entities to migrate ...\n')

            es = self.todo
            if es.count:
                self.say(f'There are {es.count} entities to migrate:')

            for e in es:
                say(f'    - {e.__module__}.{e.__name__}')

    @property
    def done(self):
        return self._done

    @property
    def todo(self):
        scan()
        return self._todo

    def run():
        start = ask(
            '\nWould you like to start [Yn]?', yesno=True, default='yes'
        )

        if start != 'yes':
            return

        scan()

        es = self.todo
        for i, e in es.enumerate():
            at = e.orm.altertable
            tbl = e.orm.migration.table
            print(f'{tbl!s}\n{at}\n')

            while True:
                res = ask(
                    'Apply this DDL [y,n,q,a,e,h]?', yesno=True, 
                    quit='q', all='a', edit='e', help='h'
                )

                if res in ('yes', 'no', 'quit', 'all', 'edit'):
                    break

                if res == 'help':
                    usage()

            if res == 'all':
                res = self.processes.process('all')
                if res == 'abort':
                    continue
            elif res == 'quit':
                return

            elif res == 'edit':
                res = self.processes.process('edit')
    except Exception as ex:
        print(f'\n{ex}\n')
    finally:
        if tmp:
            os.remove(tmp)

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
