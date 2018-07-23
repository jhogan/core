#!/usr/bin/python3 -i
# vim: set et ts=4 sw=4 fdm=marker
"""
MIT License

Copyright (c) 2018 Jesse Hogan

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
from articles import *
from parties import *
from configfile import configfile
from entities import brokenruleserror
from MySQLdb.constants.ER import BAD_TABLE_ERROR, DUP_ENTRY
from pdb import set_trace; B=set_trace
from tester import *
from uuid import uuid4
import MySQLdb
import re
import pathlib

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

def importblog(bl, path):

    def local_onimportstatuschange(src, eargs):
        per = str(round(eargs.lineno / linecount * 100, 0)) + '%'
        firstinvocation = not hasattr(local_onimportstatuschange, 'per')

        if firstinvocation or local_onimportstatuschange.per != per:
            print('(' + per + ')')

        local_onimportstatuschange.per = per

    def local_onrequestauthormap(src, eargs):
        importpersons = eargs.importpersons
        creators      = eargs.creators
        
        for p in importpersons:
            u = user.load(p.users.first.name, 'carapacian')
            if not u:
                u = user()
                u.name = p.users.first.name
                u.service = 'carapacian'
                u.password = uuid4().hex
                u.save()
            creators += u

    def local_onitemimport(src, eargs):
        print(eargs.item.title)

    def local_onitemimporterror(src, eargs):
        art = eargs.item
        print(art.title)
        if eargs.exception:
            print('(EXCEPTION: ' + str(eargs.exception) + ')')
        elif not art.isvalid:
            print('INVALID: \n'   + str(art.brokenrules))
            
    bl.onimportstatuschange  +=  local_onimportstatuschange
    bl.onrequestauthormap    +=  local_onrequestauthormap
    bl.onitemimport          +=  local_onitemimport
    bl.onitemimporterror     +=  local_onitemimporterror

    linecount = rf(path).count('\n')
    bl.import_(path)


try:
    blogs().RECREATE()
    tags().RECREATE()
    bl = blog()
    bl.slug = 'imported-blog'
    bl.description = 'This blog contains blogposts and articles imported from a WXR file'
    bl.save()
    importblog(bl, '/usr/local/lib/python3.5/www/qa/epiphenomenon-py/testdata/blog-import-file.xml')
except Exception as ex:
    print(ex)
    pdb.post_mortem(ex.__traceback__)

