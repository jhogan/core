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

def ask(msg, yesno=True, default=None, **kwargs):
    res = None
    while not res:
        res = input(f'{msg} ').lower()
        if not res and default:
            return default

    if yesno:
        if res in ('y', 'yes'):
            return 'yes'
        elif res in ('n', 'no'):
            return 'no'

    for k, v in kwargs.items():
        if res == v:
            return k
    return None

def say(msg):
    print(msg)

def mig():
    def usage():
        print("""
        y - yes, apply DDL
        n - no, do not apply DDL
        q - quit migration
        a - apply this DDL and all later DLL
        e - manually edit the current DDL
        ? - print help
        """)
        
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

    # Stage this hunk [y,n,q,a,d,s,e,?]?
    for e in orm.migration().entities:
        at = e.orm.altertable
        print(f'{e.orm.migration!r}\n{at}')
        res = ask(
            'Apply this DDL [y,n,q,a,e,?]?', yesno=True, 
            quit='q', all='a', edit='e', help='?')
        if res == 'quit':
            return
        elif res == 'help':
            usage()
        elif res == 'yes':
            print('applying ...')
            B()
            orm.orm.exec(at)

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
