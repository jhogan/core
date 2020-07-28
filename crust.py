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

def say(msg):
    print(msg)

def mig():
    tmp = None
    def usage():
        print(textwrap.dedent("""
        y - yes, apply DDL
        n - no, do not apply DDL
        q - quit migration
        a - apply this DDL and all later DLL
        e - manually edit the current DDL
        h - print help
        """))
        
    try:
        say('Scanning for entities to migrate ...\n')

        es = orm.migration().entities
        if es.count:
            say(f'There are {es.count} entities to migrate:')

        for e in es:
            say(f'    - {e.__module__}.{e.__name__}')

        start = ask(
            '\nWould you like to start [Yn]?', yesno=True, default='yes'
        )

        if start != 'yes':
            return

        # Stage this hunk [y,n,q,a,d,s,e,h]?
        for e in orm.migration().entities:
            at = e.orm.altertable
            print(f'{e.orm.migration!r}\n{at}')

            while True:
                res = ask(
                    'Apply this DDL [y,n,q,a,e,h]?', yesno=True, 
                    quit='q', all='a', edit='e', help='h'
                )

                if res in ('yes', 'no', 'quit', 'all', 'edit'):
                    break

                if res == 'help':
                    usage()

            if res == 'quit':
                return
            elif res == 'edit':
                # Create a tmp file
                if not tmp:
                    _, tmp = tempfile.mkstemp()

                # Write the ALTER TABLE to the tmp file
                with open(tmp, 'w') as f:
                    f.write(at)

                # Get an editor that the user likes
                editor = os.getenv('EDITOR') or '/usr/bin/vim'

                while True:
                    # Prompt the user to edit the file
                    os.system(f'{editor} {tmp}')

                    # Read back in the edited file
                    with open(tmp, mode='r') as f:
                        at = f.read()

                    # Execute the edited ALTER TABLE statement
                    try:
                        orm.orm.exec(at)
                    except Exception as ex:
                        res = ask(
                            f'\n{ex}\n\nPress any key to continue...',
                            default = None
                        )
                        if res and res.lower() in ('q', 'quit', 'exit'):
                            return
                    else:
                        break
            
            elif res == 'yes':
                print('applying ...')
                B()
                orm.orm.exec(at)
    except Exception as ex:
        print(f'\n{ex}\n')
    finally:
        if tmp:
            B()
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
