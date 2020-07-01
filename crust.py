#!/usr/bin/python3 -i
# vim: set et ts=4 sw=4 fdm=marker

# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2019

from articles import *
from parties import *
from configfile import configfile
from entities import BrokenRulesError
from MySQLdb.constants.ER import BAD_TABLE_ERROR, DUP_ENTRY
from pdb import set_trace
from tester import *
from uuid import uuid4
import MySQLdb
import re
import pathlib
from getpass import getpass
import db
import orm

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

# Given a blog object and a file path, use blog.import_() to import a WXR file
# into the system.
def importblog(bl, path):

    def local_onimportstatuschange(src, eargs):
        # Show precentage complete
        per = str(round(eargs.lineno / linecount * 100, 0)) + '%'
        firstinvocation = not hasattr(local_onimportstatuschange, 'per')

        if firstinvocation or local_onimportstatuschange.per != per:
            print('(' + per + ')')

        local_onimportstatuschange.per = per

    def local_onrequestauthormap(src, eargs):
        # Map creators found in WXR to user in the system
        importpersons = eargs.importpersons
        creators      = eargs.creators
        
        for p in importpersons:
            uid = p.users.first.name
            msg = 'Map user "{}" <{}> to local user. [s]elect or [c]reate? \n'
            msg = msg.format(p.fullname, uid)

            create = None
            while create is None:
                r = input(msg)
                if r == 's':
                    create = False
                elif r == 'c':
                    create = True
                else:
                    continue
                
                uid = None
                while not uid:
                    uid = input('Username: ')

                srv = None
                while not srv:
                    srv = input('Service: ')

                if create:
                    pwd = None
                    while not pwd:
                        pwd = getpass()
                        if pwd:
                            if pwd != getpass('Re-enter: '):
                                print("Passwords don't match")
                                pwd = None
                                continue
                    u = user()
                    u.name = uid
                    u.service = srv
                    u.password = pwd
                else: # select
                    print()
                    u = user.load(uid, srv)
                    if not u:
                        print("Can't find user {} (service: '{}')".format(uid, srv))
                        create = None
                        msg = '[s]elect or [c]reate? \n'
                        continue
                    else:
                        print('User found:')
                
                print()
                print(u)
                r = None
                while not r or r not in ['y', 'n']:
                    r = input('\nIs this correct? ')
                
                if r != 'y':
                    msg = '[s]elect or [c]reate? \n'
                    create = None
                    continue
                
                creators += u

        tbl = table()

        # Header
        r = tbl.newrow()
        r.newfield('wxr.name')
        r.newfield('local.name')

        # Body
        for p, u in zip(importpersons, creators):
            r = tbl.newrow()
            r.newfield(p.fullname + ' <' + p.users.first.name + '>')
            r.newfield(u.name)
        
        print(tbl)
        input('If this is correct press <enter>. Otherwise hit ctrl-c to abort.')
        creators.save()

            
                        

    def local_onitemimport(src, eargs):
        # Display articles that were imported
        print('IMPORTED: "{}"'.format(eargs.item.title))

    def local_onitemimporterror(src, eargs):
        # Show articles that couldn't be imported due to an error 
        art = eargs.item
        ex = eargs.exception

        print('"{}"'.format(art.title))

        if ex:
            if type(ex) == MySQLdb.IntegrityError and ex.args[0] == DUP_ENTRY:
                print('(This articles has already been imported)')
            else:
                print('(EXCEPTION: ' + str(eargs.exception) + ')')
        elif not art.isvalid:
            print('INVALID: \n'   + str(art.brokenrules))
            
    # Subscribe to eventns
    bl.onimportstatuschange  +=  local_onimportstatuschange
    bl.onrequestauthormap    +=  local_onrequestauthormap
    bl.onitemimport          +=  local_onitemimport
    bl.onitemimporterror     +=  local_onitemimporterror

    # Get the line count of the file. This is used by
    # local_onimportstatuschange to calculate the % done.
    linecount = rf(path).count('\n')
    bl.import_(path)

cfg = configfile().getinstance()
dbacct = db.connections.getinstance().default.account

if cfg.inproduction:
    print("You are in a production environment".upper())
else:
    try:
        print('Environment: {}'.format(cfg['environment']))
    except KeyError:
        print('Environment not set'.upper())


print("Configfile: {}".format(cfg.file))
connectedto = """
Connected to:
    Host:     {}
    Username: {}
    Database: {}
    Port:     {}
""".format(dbacct.host,
           dbacct.username,
           dbacct.database,
           dbacct.port)
print(connectedto)
