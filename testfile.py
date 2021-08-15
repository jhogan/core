#! /usr/bin/python3

# vim: set et ts=4 sw=4 fdm=marker

########################################################################
# Copyright (C) Jesse Hogan - All Rights Reserved                      #
# Unauthorized copying of this file, via any medium is strictly        #
# prohibited                                                           #
# Proprietary and confidential                                         #
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2021                 #
########################################################################

from func import enumerate, getattr, B
from uuid import uuid4
import asset
import base64
import dom
import ecommerce
import entities
import file
import hashlib
import orm
import os.path
import party
import pom
import tester
import uuid
import pom
import db

_ford = None
def ford():
    global _ford
    if not _ford:
        _ford = party.company(name='Ford Motor Company')
    return _ford

def clean():
    store = file.inode.store

    # Make sure `store` is a directory underneath /var/www/core. We
    # don't want `store` to be something else (like '') because we
    # may end up deleting things we don't want.
    assert store.startswith('/var/www/core') 
    assert len([x for x in store.split('/') if x]) > 3
    assert 'production' not in store

    # Delete the contents of the store directory, but not the
    # directory itself. There doesn't seem to be an easy way to do
    # this in Python so we just shell out:
    #
    #    rm -rf /var/www/core/development/*
    ret = os.system('rm -rf ' + os.path.join(store, '*'))

    # Make sure `rm` was successful
    assert ret == 0

class foonets(pom.sites): pass
class foonet(pom.site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        ''' Metadata '''
        self.lang = 'es'
        self.charset = 'iso-8859-1'

        self.host = 'foo.net'
        self.name = 'foo.net'

class dom_file(tester.tester):
    """ Test interoperability between DOM objects and the ``file``
    entity.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        clean()

        orm.security().override = True

        if self.rebuildtables:
            orm.orm.recreate(
                ecommerce.user,  ecommerce.urls,  file.files,
                file.resources,  file.directory,  file.inodes,
                pom.site,        foonet,          asset.asset
            )

        orm.security().owner = ecommerce.users.root

        # Proprietor
        com = ford()
        orm.security().proprietor = com
        com.save()

    def it_adds_js_files_to_site(self):
        ws = foonet()

        ws.resources += file.resource(
            url = 'https://cdnjs.cloudflare.com/ajax/libs/xterm/3.14.5/xterm.min.js',
            integrity = 'sha512-2PRgAav8Os8vLcOAh1gSaDoNLe1fAyq8/G3QSdyjFFD+OqNjLeHE/8q4+S4MEZgPsuo+itHopj+hJvqS8XUQ8A==',
            local = True,
        )

        ws.resources += file.resource(
            url = 'https://cdnjs.cloudflare.com/ajax/libs/xterm/3.14.5/xterm.min.js',
            integrity = 'sha512-2PRgAav8Os8vLcOAh1gSaDoNLe1fAyq8/G3QSdyjFFD+OqNjLeHE/8q4+S4MEZgPsuo+itHopj+hJvqS8XUQ8A==',
            local = True,
        )

        ws.resources += file.resource(
            url = 'https://cdnjs.cloudflare.com/ajax/libs/xterm/3.14.5/addons/attach/attach.min.js',
            integrity = 'sha512-43J76SR5UijcuJTzs73z8NpkyWon8a8EoV+dX6obqXW7O26Yb268H2vP6EiJjD7sWXqxS3G/YOqPyyLF9fmqgA==',
            local = True,
        )

        ws.save()

        ws1 = ws.orm.reloaded()

        self.eq(ws.id, ws1.id)

        ress = ws.resources.sorted()
        ress1 = ws1.resources.sorted()

        self.three(ress)
        self.three(ress1)

        for res, res1 in zip(ress, ress1):
            self.eq(res.id, res1.id)
            self.eq(str(res.url), str(res1.url))
            self.eq(res.integrity, res1.integrity)

    def it_adds_js_files_to_page(self):
        class index(pom.page):
            def main(self):
                # Add page-level resources
                self.resources += file.resource(
                    url='https://code.jquery.com/jquery-3.5.1.js',
                )

                self.resources += file.resource(
                    url='https://cdnjs.cloudflare.com/ajax/libs/shell.js/1.0.5/js/shell.min.js',
                    integrity='sha512-8eOGNKVqI8Bg/SSXAQ/HvctEwRB45OQWwgHCNT5oJCDlSpKrT06LW/uZHOQYghR8CHU/KtNFcC8mRkWRugLQuw=='
                )

                self.resources += file.resource(
                    url='https://cdnjs.cloudflare.com/ajax/libs/vega/5.14.0/vega.min.js',
                    crossorigin='use-credentials',
                )

                self.main += dom.h1('Home page')

        # Set up site
        ws = foonet()
        ws.pages += index()

        # Add site-wide resources
        ws.resources += file.resource(
            url = 'https://cdnjs.cloudflare.com/ajax/libs/unicorn.js/1.0/unicorn.min.js',
            integrity = 'sha512-PSVbJjLAriVtAeinCUpiDFbFIP3T/AztPw27wu6MmtuKJ+uQo065EjpQTELjfbSqwOsrA1MRhp3LI++G7PEuDg==',
        )

        # GET the /en/files page
        tab = self.browser().tab()
        res = tab.get('/en/index', ws)

        self.status(200, res)

        scripts = res['html head script']
        self.four(scripts)

        # Test site-level resource
        self.eq(
            'https://cdnjs.cloudflare.com/ajax/libs/unicorn.js/1.0/unicorn.min.js',
            scripts.first.src
        )
        self.eq(
            'sha512-PSVbJjLAriVtAeinCUpiDFbFIP3T/AztPw27wu6MmtuKJ+uQo065EjpQTELjfbSqwOsrA1MRhp3LI++G7PEuDg==', 
            scripts.first.integrity
        )
        self.eq('anonymous', scripts.first.crossorigin)

        # Test page-level resources
        self.eq(
            'https://code.jquery.com/jquery-3.5.1.js',
            scripts.second.src
        )
        self.eq(None, scripts.second.integrity)
        self.eq('anonymous', scripts.second.crossorigin)

        self.eq(
            'https://cdnjs.cloudflare.com/ajax/libs/shell.js/1.0.5/js/shell.min.js',
            scripts.third.src
        )
        self.eq(
            'sha512-8eOGNKVqI8Bg/SSXAQ/HvctEwRB45OQWwgHCNT5oJCDlSpKrT06LW/uZHOQYghR8CHU/KtNFcC8mRkWRugLQuw==',
            scripts.third.integrity
        )
        self.eq('anonymous', scripts.third.crossorigin)

        self.eq(
            'https://cdnjs.cloudflare.com/ajax/libs/vega/5.14.0/vega.min.js',
            scripts.fourth.src
        )

        self.eq(None, scripts.fourth.integrity)
        self.eq('use-credentials', scripts.fourth.crossorigin)

        for script in scripts:
            # We aren't caching these resources (`local is True`) so we
            # shouldn't expect any to be in the database
            url = ecommerce.url(address=script.src)
            self.zero(url.resources)

    def it_posts_file_in_a_users_file_system(self):
        class avatar(pom.page):
            def main(self, uid: uuid.UUID):
                if req.isget:
                    return

                # Populate the form with data from the request's payload
                if req.files.isempty:
                    raise BadRequestError(
                        'No avatar image file provided'
                    )

                if not req.files.hasone:
                    raise BadRequestError(
                        'Multiple avatar images were given'
                    )
                
                usr = ecommerce.user(uid)
                f = req.files.first

                default = usr.directory.file('/var/avatars/default.gif')
                default.body = f.body
                usr.save()
                res.status = 201

        # Set up site
        ws = foonet()
        ws.pages += avatar()
        ws.save()
        

        # Get a browser tab
        tab = self.browser().tab()

        # Create a file called my-avatar to POST to server
        f = file.file(name='my-avatar.gif')

        # Assign 1x1 pixel GIF to the file's body property
        f.body = base64.b64decode(
            'R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7'
        )

        # Create a save a user
        usr = ecommerce.user(name='luser')
        usr.save()

        # Post the file. Reference the user's id in the URL.
        res1 = tab.post(f'/en/avatar?uid={usr.id}', ws, files=f)
        self.status(201, res1)

        usr = usr.orm.reloaded()
        f1 = usr.directory['var/avatars/default.gif']
        f1 = f1.orm.cast(file.file)
        self.eq(f.body, f1.body)

    def it_caches_js_files(self):
        class index(pom.page):
            def main(self):
                self.main += dom.h1('Home page')

        # Set up site
        ws = foonet()
        ws.pages += index()

        resx = file.resource(
            url = 'https://code.jquery.com/jquery-3.5.1.js',
            local = True
        )

        ws.resources += resx

        def f():
            ws.pages.last.resources += file.resource(
                url        =  'https://cdnjs.cloudflare.com/ajax/libs/shell.js/1.0.5/js/shell.min.js',
                integrity  =  'sha512-8eOGNKVqI8Bg/SSXAQ/HvctEwRB45OQWwgHCNT5oJCDlSpKrT06LW/uZHOQYghR8CHU/KtNFcC8mRkWRugLQuw==',
                local      =  True
            )

        # We should be forbidden from setting local=True when creating
        # file.resources and appending them to pages. A page does not
        # need a seperate directory for its own JS, CSS, etc files.
        # That would lead to clutter and duplication. If a page needs
        # its own resources that are unique from other pages, we can add
        # a non-local resource.
        self.expect(ValueError, f)

        ws.save()

        # GET the /en/files page
        tab = self.browser().tab()
        res = tab.get('/en/index', ws)

        self.status(200, res)

        scripts = res['html head script']
        self.one(scripts)

        self.eq(
            (
                f'/{file.directory.radix.name}'
                f'/pom/site/{ws.id.hex}/resources/jquery-3.5.1.js'
            ),
            scripts.first.src
        )
        self.eq(None, scripts.first.integrity)
        self.eq('anonymous', scripts.first.crossorigin)

        self.one(file.resources.orm.all)

        # Load and test first: jquery
        rcs = ecommerce.urls(
            'address', 'https://code.jquery.com/jquery-3.5.1.js'
        ).first.resources

        self.one(rcs)
        self.none(rcs.first.integrity)
        self.eq('anonymous', rcs.first.crossorigin)

class file_file(tester.tester):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        orm.security().override = True

        # Delete files
        clean()

        if self.rebuildtables:
            # Recreate tables
            orm.orm.recreate(
                ecommerce.user,
                file.files,
                file.resources,
                file.directory,
                file.inodes,
            )

        # Create an owner and get the root user
        own = ecommerce.user(name='hford')
        root = ecommerce.users.root

        # Save the owner, the root user will be the owner's owner.
        orm.security().owner = root
        own.owner = root
        own.save()

        # Going forward, `own` will be the owner of all future records
        # created.
        orm.security().owner = own

        # Create a company to be the propritor.
        com = ford()
        com.save()

        # Set the company as the proprietory
        orm.security().proprietor = com

        # Update the owner (hford) so that the company (Ford Motor
        # Company) is the proprietor.
        own.proprietor = com
        own.save()

        orm.security().owner = ecommerce.users.root

    def it_creates_with_name_kwarg(self):
        f = file.file(name='test')
        f1 = file.file(name='test')
        self.isnot(f, f1)

        # XXX Complete. See it_creates_empty_file

    def it_deletes(self):
        ''' Delete a cached-only file '''
        # Create non-persisted, though cached, file
        f = file.file('/tmp/rm-me')

        # It will obviously be in the radix cached
        self.true(f in file.directory.radix)

        # Deleting here only means: remove from radix cache
        f.delete()

        # Ensure the delete file is removed from the radix cache
        self.false(f in file.directory.radix)

        ''' Delete a cached and saved file that has no body'''
        # Recreate and save
        f = file.file('/tmp/rm-me')

        # Don't add a body. This test is for files that don't get stored
        # to the HDD, and without a body, there is no need to store the
        # file to the HDD.
        ## f.body = 'hot'

        # Persist file
        f.save()

        # It will be back in the radix cached
        self.true(f in file.directory.radix)

        # It will be in the database
        self.expect(None, f.orm.reloaded)

        # It won't exist in the HDD because the body is empty
        self.false(f.exists)

        # Now delete it
        f.delete()

        # It will be removed from the cache
        self.false(f in file.directory.radix)

        # It will no longer be in the database
        self.expect(db.RecordNotFoundError, f.orm.reloaded)

        # It will continue to not exist on the HDD.
        self.false(f.exists)

        ''' Delete a cached and saved file that has a body'''
        # Recreate and save
        f = file.file('/tmp/rm-me')

        # Add that body
        f.body = 'hot'

        f.save()

        # It will be back in the radix cached
        self.true(f in file.directory.radix)

        # It will be in the database
        self.expect(None, f.orm.reloaded)

        # It will exist in the HDD
        self.true(f.exists)

        # Now delete it
        f.delete()

        # It will be removed from the cache
        self.false(f in file.directory.radix)

        # It will no longer be in the database
        self.expect(db.RecordNotFoundError, f.orm.reloaded)

        # It will not exist on the HDD.
        self.false(f.exists)

    def it_caches_floaters(self):
        f = file.file('test')
        f1 = file.file('test')
        f2 = file.file('TEST')
        self.is_(f, f1)
        self.isnot(f, f2)

        for nd in (f, f1, f2):
            self.type(file.file, nd)
            self.true(nd in file.directory.floaters)

        ''' Nested '''
        f = file.file('berp/derp/flerp/herp/gerp/slerp')

        flts = file.directory.floaters

        self.is_(f, flts['berp/derp/flerp/herp/gerp/slerp'])

        f = f.inode
        self.is_(f, flts['berp/derp/flerp/herp/gerp'])

        f = f.inode
        self.is_(f, flts['berp/derp/flerp/herp'])

        f = f.inode
        self.is_(f, flts['berp/derp/flerp'])

        f = f.inode
        self.is_(f, flts['berp/derp'])

        f = f.inode
        self.is_(f, flts['berp'])

        self.is_(flts, f.inode)

    def it_appends_floaters(self):
        ''' Shallow '''
        flts = file.directory.floaters

        f = file.file('test')

        log = file.directory('/var/log')

        # Verify f is in floaters
        self.true(f in flts)

        # Add to /var/log
        log += f

        # Make sure the floater was added to /var/log
        self.is_(log.inodes.last, f)

        # Make sure the floater is removed from the floaters cache
        self.false(f in flts)

        ''' Nested '''
        f = file.file('20000/leagues/under/the/herp/derp')

        flts['20000/leagues/under/the/herp/derp']

        derp = f
        herp = f.inode
        the = f.inode.inode
        under = f.inode.inode.inode

        for nd in (derp, herp, the):
            self.true(nd in flts)

        # Verify we have the right directory
        self.eq('the', the.name)

        share = file.directory('/usr/share')

        share += the

        # Make sure 'the/herp/derp' was moved under share
        self.is_(share['the'], the)
        self.is_(share['the/herp'], herp)
        self.is_(share['the/herp/derp'], derp)

        # Make sure the/herp/derp is gone from the floaters cache
        self.none(flts('20000/leagues/under/the/herp/derp'))
        self.none(flts('20000/leagues/under/the/herp'))

        self.none(flts('20000/leagues/under/the'))
        self.is_(under, flts['20000/leagues/under'])

    def it_wont_save_floaters(self):
        flt = file.file('we/are/all/floaters')

        self.four(flt.brokenrules)
        self.four(flt.inode.brokenrules)
        self.four(flt.inode.inode.brokenrules)
        self.four(flt.inode.inode.inode.brokenrules)

        self.ge(file.directory.floaters.brokenrules.count, 4)

    def it_moves_cached_files(self):
        vim = file.file('/usr/bin/vim')
        bin = file.directory('/usr/local/bin')

        bin += vim

        radix = file.directory.radix
        self.none(radix('usr/bin/vim'))
        self.is_(vim, radix('usr/local/bin/vim'))

    def it_caches_new_files_at_radix(self):
        # Simple file at radix

        f = file.file('/etc/hosts')
        # Nested file at radix
        f1 = file.file('/etc/hosts')
        f2 = file.file('/etc/HOSTS')
        self.is_(f, f1)
        self.isnot(f, f2)
        for nd in (f, f1, f2):
            self.type(file.file, nd)
            self.type(file.directory, nd.inode)

        # Deeply nested.produce file at radix 
        f = file.file('/var/log/syslog')
        f1 = file.file('/var/log/syslog')
        f2 = file.file('/var/log/auth.log')
        self.is_(f, f1)
        self.isnot(f, f2)
        for nd in (f, f1, f2):
            self.type(file.file, nd)
            self.type(file.directory, nd.inode)

    def it_creates_empty_file(self):
        ''' Instatiate file '''

        name = uuid4().hex
        path = f'/tmp/{name}'
        radix = file.directory.radix.name
        head = os.path.join(file.inode.store, radix, 'tmp')

        f = file.file(path)
        self.eq(head, f.head)
        self.eq(f.path, os.path.join(head, name))
        self.false(f.exists)
        self.false(os.path.exists(f.path))
        self.eq(name, f.name)
        self.is_(file.directory.radix, f.inode.inode)
        self.none(f.inode.inode.inode)
        self.expect(AttributeError, lambda: f.inodes)
        self.none(f.body)
        self.none(f.mime)

        ''' Saving the file with no body set '''
        f.save()
        self.eq(head, f.head)
        self.eq(f.path, os.path.join(head, name))

        # Since there is no body, there will be no corresponding file
        # saved
        self.false(f.exists)
        self.false(os.path.exists(f.path))

        self.eq(name, f.name)
        self.none(f.inode.inode.inode)
        self.expect(AttributeError, lambda: f.inodes)
        self.none(f.body)
        self.none(f.mime)

        f1 = f.orm.reloaded()
        self.eq(f.store, f1.store)
        self.eq(f.head, f1.head)
        self.eq(f.path, f1.path)

        # Since there is no body, there will be no corresponding file
        # saved
        self.false(f1.exists)
        self.false(os.path.exists(f1.path))

        self.eq(name, f1.name)
        self.none(f1.inode.inode.inode)
        self.expect(AttributeError, lambda: f.inodes)
        self.none(f1.body)
        self.none(f.mime)

    def it_creates_text_file(self):
        ''' Instatiate file '''
        f = file.file('/etc/modules')

        body = self.dedent('''
        # This file contains the names of kernel modules that should be loaded
        # at boot time, one per line. Lines beginning with "#" are ignored.
        ''')

        f.body = body
        self.eq(body, f.body)
        self.eq('text/plain', f.mime)
        self.true(isinstance(f.body, str))

        ''' Saving the file with '''
        f.save()
        path = os.path.join(
            f.store, file.directory.radix.name, 'etc/modules'
        )
        self.eq(f.path, path)
        self.true(f.exists)
        self.true(os.path.exists(f.path))
        self.true(isinstance(f.body, str))
        self.eq('text/plain', f.mime)

        self.eq('modules', f.name)
        self.none(f.inode.inode.inode)
        self.expect(AttributeError, lambda: f.inodes)
        self.eq(body, f.body)

        f1 = f.orm.reloaded()
        self.eq(f.body, f1.body)
        self.true(isinstance(f1.body, str))
        self.eq('text/plain', f1.mime)
        self.true(f1.exists)
        self.true(os.path.exists(f1.path))

    def it_creates_binary_file(self):
        ''' Instatiate file '''
        f = file.file('/var/lib/mlocate/mlocate.db')

        body = base64.b64decode(
            'R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7'
        )

        f.body = body
        self.eq(body, f.body)
        self.eq('application/octet-stream', f.mime)
        self.true(isinstance(f.body, bytes))

        ''' Saving the file '''
        f.save()
        path = os.path.join(
            file.inode.store, 
            f.relative.lstrip('/')
        )
        self.eq(f.path, path)
        self.true(f.exists)
        self.true(os.path.exists(f.path))
        self.eq('application/octet-stream', f.mime)
        self.true(isinstance(f.body, bytes))

        self.eq('mlocate.db', f.name)
        self.none(f.inode.inode.inode.inode.inode)
        self.expect(AttributeError, lambda: f.inodes)
        self.eq(body, f.body)

        f1 = f.orm.reloaded()
        self.eq(f.body, f1.body)
        self.eq('application/octet-stream', f.mime)
        self.true(isinstance(f.body, bytes))
        self.true(f1.exists)
        self.true(os.path.exists(f1.path))

    def it_creates_within_a_directory(self):
        ''' Instatiate file with `path` off radix '''

        f = file.file('/swapfile')

        body = self.dedent('''
        Line 1
        Line 2
        ''')

        f.body = body
        self.eq(body, f.body)

        f.save()

        path = os.path.join(
            file.inode.store, 
            f.relative.lstrip('/')
        )
        self.eq(f.path, path)
        self.true(f.exists)
        self.true(os.path.exists(f.path))

        self.eq('swapfile', f.name)
        self.none(f.inode.inode)
        self.eq(body, f.body)

        f1 = f.orm.reloaded()
        self.eq(f.body, f1.body)
        self.true(f1.exists)
        self.true(os.path.exists(f1.path))
        with open(f.path, 'r') as f1:
            self.eq(f1.read(), f.body)

        ''' Instatiate file with `path` off within a new directory '''
        path = '/usr/share/perl5/URI.pm'

        # This will create the file off the radix
        f = file.file(path)

        body = self.dedent('''
        package URI;

        use strict;
        use warnings;
        ''')

        f.body = body
        self.eq(body, f.body)

        f.save()
        path = os.path.join(
            file.inode.store, 
            f.relative.lstrip('/')
        )
        self.eq(f.path, path)
        self.true(f.exists)
        self.true(os.path.exists(f.path))

        self.eq('URI.pm', f.name)
        self.eq('perl5', f.inode.name)
        self.eq('share', f.inode.inode.name)
        self.eq('usr', f.inode.inode.inode.name)
        self.true(f.inode.inode.inode.inode.isradix)
        with open(f.path, 'r') as f1:
            self.eq(f1.read(), f.body)

        f1 = f.orm.reloaded()
        self.eq(f.body, f1.body)
        self.true(f1.exists)
        self.true(os.path.exists(f1.path))

    def it_loads_within_a_directory(self):
        ''' Create file within new directory '''
        path = '/var/backups/alternatives.tar.0'
        f = file.file(path)
        body = base64.b64decode(
            'R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7'
        )
        f.body = body
        self.eq('alternatives.tar.0', f.name)

        path = os.path.join(
            file.inode.store, 
            f.relative.lstrip('/')
        )
        self.eq(path, f.path)
        self.false(f.exists)
        self.eq((True, False, False), f.orm.persistencestate)

        backups = f.inode
        self.eq('backups', backups.name)
        path = os.path.join(
            backups.inode.store, 
            backups.relative.lstrip('/')
        )
        self.eq(path, backups.path)
        self.false(backups.exists)
        self.eq((True, False, False), backups.orm.persistencestate)

        var = backups.inode
        self.eq('var', var.name)
        path = os.path.join(
            var.inode.store, 
            var.relative.lstrip('/')
        )
        self.eq(path, var.path)

        # Commenting out these var testes. /var is so common that it
        # will probably already exist because it will have been created
        # by another test by the time we get here.
        # self.false(var.exists)
        # self.eq((True, False, False), var.orm.persistencestate)
        self.true(var.inode.isradix)

        f.save()

        self.eq('alternatives.tar.0', f.name)
        path = os.path.join(
            file.inode.store, 
            f.relative.lstrip('/')
        )
        self.eq(path, f.path)
        self.eq((False, False, False), f.orm.persistencestate)
        self.true(f.exists)

        backups = f.inode
        self.eq('backups', backups.name)
        path = os.path.join(
            file.inode.store, 
            backups.relative.lstrip('/')
        )
        self.eq(path, backups.path)
        self.eq((False, False, False), backups.orm.persistencestate)
        self.true(backups.exists)

        var = backups.inode
        self.eq('var', var.name)
        path = os.path.join(
            var.inode.store, 
            var.relative.lstrip('/')
        )
        self.eq(path, var.path)
        self.true(var.exists)
        self.eq((False, False, False), var.orm.persistencestate)
        self.true(var.inode.isradix)
        self.true(var.exists)

    def it_sets_mime(self):
        ''' Text file '''
        f = file.file('/home/eboetie/var/www/index.html')
        f.body = self.dedent('''
        <html>
            <head>
                <title>Some HTML</title>
            </head>
            <body>
                <p>
                    Herp Derp
                </p>
            </body>
        </html>
        ''')

        f.mime = 'text/html'
        self.eq('text/html', f.mime)
        self.eq('text', f.mimetype)

        f.save()
        f = f.orm.reloaded()
        self.eq('text/html', f.mime)
        self.eq('text', f.mimetype)

        ''' Binary file '''
        f = file.file('/home/eboetie/var/www/my.gif')
        f.body = base64.b64decode(
            'R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7'
        )
        f.mime = 'image/gif'
        self.eq('image/gif', f.mime)
        self.eq('image', f.mimetype)

        f.save()
        f = f.orm.reloaded()
        self.eq('image/gif', f.mime)
        self.eq('image', f.mimetype)

    def it_cant_save_duplicate_file_name(self):
        ''' Try to create duplicate by name '''

        # XXX There is some confusion here. When creating a file
        # that already exist, the assumption was that we would be
        # creating a duplicate. However, I think the correct assumption
        # is that we are trying to clobber the file. We would need to
        # remove the broknerule that checks the database to see if we
        # have a duplicate, and instead rename and reimplement this unit
        # test to ensure that clobbering is possible and that there is
        # no problem "recreating" (i.e., not caring that they alreay
        # exist) directories.

        f = file.file('/home/eboetie/dup.txt')
        self.expect(None, f.save)

        # These lines dereference the radix directory's inodes
        # collection. We are tying to create the condition where the
        # above line created a file (along with the path) but it isn't
        # currently cached by the current process. In this case, we want
        # there to be no problem clobbering it.
        radix = file.directory.radix
        nd = radix.orm.super

        # Save a reference to radix's existing inodes collection so we can
        # restore it later. Future tests will depend on the inodes in
        # the cache making sense with what's in the database.
        nds = nd.orm.mappings['inodes']._value
        try:
            nd.orm.mappings['inodes']._value = file.inodes()

            f = file.file('/home/eboetie/dup.txt')
            
            
            self.one(f.brokenrules)
            self.expect(entities.BrokenRulesError, lambda: f.save())
        finally:
            # Restore old inodes collection to radix
            nd.orm.mappings['inodes']._value = nds

        return # XXX

        ''' Try to create duplicate by path '''
        f = file.file(path='/my/dir/dup.txt')
        self.expect(None, f.save)

        my = file.directory(path='/my/dir')
        dir = my['dir']
        f = file.file(name='dup.txt')
        dir += f
        self.one(f.brokenrules)
        self.expect(entities.BrokenRulesError, my.save)

    def it_raises_AttributeError_on_file_inodes(self):
        f = file.file('/850cad31/498c/4584')
        self.expect(AttributeError, lambda: f.inodes)

    def it_ensures_name_cant_have_slashes(self):
        return
        # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        # XXX This is a security issue. 'name' is being set in the
        # constructor. This should be accepted functionality but the
        # slashes should't be allowed. What's really bad though is this
        # is actually causing the real /var/log/kern.log to be open.
        # It's not being opened and clobber only because we are running
        # the tests as radix. This is bad.
        # 💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
        f = file.file(name='/var/log/kern.log')
        f.body = '1 2 3'
        f.save()

    def it_becomes_dirty_when_body_is_changed(self):
        f = file.file('/var/log/kern.log')
        f.body = '1 2 3'

        self.true(f.orm.isnew)
        self.false(f.orm.isdirty)

        f.save()

        self.false(f.orm.isnew)
        self.false(f.orm.isdirty)

        f.body = '4 5 6'

        self.false(f.orm.isnew)
        self.true(f.orm.isdirty)

        f.save()

        self.false(f.orm.isnew)
        self.false(f.orm.isdirty)

        f = f.orm.reloaded()
        self.eq('4 5 6', f.body)

    def it_body_doesnt_get_trimmed(self):
        # TODO What mode should we save and load files as. An .bat file
        # is considered an application/x-msdos-program, not a text/*
        # mimetype. But an application/* suggests binary.
        body = '    @ECHO\nOFF\nCLS\nDATE\nTIME\nVER    '
        f = file.file('/c/autoexec.bat')
        f.body = body

        self.eq(body, f.body)

        f.save()

        self.eq(body, f.body)

        f = f.orm.reloaded()

        self.eq(body, f.body.decode('ascii'))

class file_directory(tester.tester):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        orm.security().override = True
        clean()

        if self.rebuildtables:
            orm.orm.recreate(
                ecommerce.user, file.files, file.resources,
                file.directory, file.inodes,
            )

        file.directory.radix.delete()


        # Create an owner and get the root user
        own = ecommerce.user(name='hford')
        root = ecommerce.users.root

        # Save the owner, the root user will be the owner's owner.
        orm.security().owner = root
        own.owner = root
        own.save()

        # Going forward, `own` will be the owner of all future records
        # created.
        orm.security().owner = own

        # Create a company to be the propritor.
        com = ford()
        com.save()

        # Set the company as the proprietory
        orm.security().proprietor = com

        # Update the owner (hford) so that the company (Ford Motor
        # Company) is the proprietor.
        own.proprietor = com
        own.save()

        orm.security().owner = ecommerce.users.root

    def it_deletes(self):
        # XXX Test when deleting a floater

        ''' Delete a cached-only directory '''
        # Create non-persisted, though cached, directory
        rm_me = file.directory('/tmp/rm-me')

        # It will obviously be in the radix cached
        self.true(rm_me in file.directory.radix)

        # Deleting here only means: remove from radix cache
        rm_me.delete()

        # Ensure the delete directory is removed from the radix cache
        self.false(rm_me in file.directory.radix)

        ''' Delete a cached-only directory with an empty file '''
        # Recreate non-persisted, though cached, directory
        file_dat = file.file('/tmp/rm-me/file.dat')

        rm_me = file_dat.inode

        # rm_me and file_dat wil obvisoly be in the cache
        self.true(file_dat in file.directory.radix)
        self.true(rm_me in file.directory.radix)

        # Deleting here only means: remove from radix cache
        rm_me.delete()

        # Ensure the delete directory and file are removed from the
        # radix cache
        self.false(file_dat in file.directory.radix)
        self.false(rm_me in file.directory.radix)

        ''' Remove directory with a file '''
        # Recreate non-persisted, though cached, directory
        file_dat = file.file('/tmp/rm-me/file.dat')

        rm_me = file_dat.inode

        file_dat.save()

        # Inodes will obviously be in database
        self.expect(None, file_dat.orm.reloaded)
        self.expect(None, rm_me.orm.reloaded)

        # Inodes will are not expected to exist on HDD because file_dat
        # has no body.
        self.false(file_dat.exists)
        self.false(rm_me.exists)

        # Delete. We will expect to see the files removed from the cache
        # and the database
        rm_me.delete()

        # Ensure the delete directory and file are removed from the
        # radix cache
        self.false(file_dat in file.directory.radix)
        self.false(rm_me in file.directory.radix)

        # Inodes will be removed from database
        self.expect(db.RecordNotFoundError, file_dat.orm.reloaded)
        self.expect(db.RecordNotFoundError, rm_me.orm.reloaded)

        # Inodes will are not expected to exist on HDD because file_dat
        # has no body.
        self.false(file_dat.exists)
        self.false(rm_me.exists)

        ''' Remove directory with a file '''
        # Recreate non-persisted, though cached, directory
        file_dat = file.file('/tmp/rm-me/file.dat')
        file_dat.body = 'derp'

        rm_me = file_dat.inode

        file_dat.save()

        # Inodes will obviously be in database
        self.expect(None, file_dat.orm.reloaded)
        self.expect(None, rm_me.orm.reloaded)

        # Inodes expected to exist on HDD
        self.true(file_dat.exists)
        self.true(rm_me.exists)

        # Delete. We will expect to see the files removed from the cache
        # and the database
        rm_me.delete()

        for nd in (file_dat, rm_me):
            name = nd.name

            # Ensure the delete directory and file are removed from the
            # radix cache
            self.false(nd in file.directory.radix, name)

            # Inodes will be removed from database
            self.expect(db.RecordNotFoundError, nd.orm.reloaded, name)

            # Inodes should be removed from HDD
            self.false(nd.exists, nd.path)

        ''' Remove directory n-level deep '''
        # Recreate non-persisted, though cached, directory
        file_dat = file.file('/tmp/rm-me/file.dat')
        file_dat.body = 'derp'

        rm_me = file_dat.inode

        file1_dat = file.file('file2.dat')
        file1_dat.body = 'herp'

        rm_me += file1_dat

        tmp = rm_me.inode

        file2_dat = file.file('file2.dat')
        file2_dat.body = 'gerp'

        tmp += file2_dat

        tmp.save()

        nds = tmp, rm_me, file_dat, file1_dat, file2_dat

        # Inodes will obviously be in database
        for nd in nds:
            self.expect(None, nd.orm.reloaded)

        # Inodes expected to exist on HDD
        for nd in nds:
            self.true(nd.exists, nd.name)

        # Delete. We will expect to see the files removed from the cache
        # and the database
        tmp.delete()

        for nd in nds:
            name = nd.name

            # Ensure the delete inodes are removed from the radix cache
            self.false(nd in file.directory.radix, name)

            # Inodes will be removed from database
            self.expect(db.RecordNotFoundError, nd.orm.reloaded, name)

            # Inodes should be removed from HDD
            self.false(nd.exists, nd.path)

    def it_caches_new_directories_at_root(self):
        ''' Simple directory production at root '''
        d = file.directory('/usr')
        d1 = file.directory('/usr')
        d2 = file.directory('/USR')
        self.is_(d, d1)
        self.isnot(d, d2)
        usr, USR = d, d2

        for dir in (d, d1, d2):
            self.type(file.directory, dir)

        ''' Nested directory production '''
        d = file.directory('/usr/local')
        d1 = file.directory('/usr/local')
        d2 = file.directory('/USR/local')

        for nd in (d, d1, d2):
            self.eq('local', nd.name)

            if nd is d2:
                self.eq('USR', nd.inode.name)
            else:
                self.eq('usr', nd.inode.name)

        # Compare directories to each other
        self.is_(d, d1)
        self.is_(d.inode, d1.inode)
        self.isnot(d.inode, d2.inode)
        self.isnot(d, d2)

        # Compare to the simple directory production above
        self.is_(usr, d.inode)
        self.is_(USR, d2.inode)

        local, USR_local = d, d2

        ''' Deeply nested directory production '''
        d = file.directory('/usr/local/bin')
        d1 = file.directory('/usr/local/bin')
        d2 = file.directory('/USR/local/bin')

        for nd in (d, d1, d2):
            self.eq('bin',    nd.name)
            self.eq('local',  nd.inode.name)

            if nd is d2:
                self.eq('USR', nd.inode.inode.name)
            else:
                self.eq('usr', nd.inode.inode.name)

        self.is_(d, d1)
        self.is_(d.inode, d1.inode)
        self.is_(d.inode.inode, d1.inode.inode)

        self.isnot(d, d2)
        self.isnot(d.inode, d2.inode)
        self.isnot(d.inode.inode, d2.inode.inode)

        self.is_(local, d.inode)
        self.is_(usr, d.inode.inode)
        self.is_(USR_local, d2.inode)
        self.is_(USR, d2.inode.inode)

    def it_creates_off_radix(self):
        dir = file.directory('/mnt')
        self.eq('mnt', dir.name)
        self.is_(file.directory.radix, dir.inode)
        self.none(dir.inode.inode)
        self.zero(dir.inodes)
        self.eq((True, False, False), dir.orm.persistencestate)

        dir.save()
        self.eq('mnt', dir.name)
        self.is_(file.directory.radix, dir.inode)
        self.none(dir.inode.inode)
        self.zero(dir.inodes)
        self.eq((False, False, False), dir.orm.persistencestate)

        dir = dir.orm.reloaded()
        self.eq('mnt', dir.name)
        self.eq(file.directory.radix.id, dir.inode.id)
        self.none(dir.inode.inode)
        self.zero(dir.inodes)
        self.eq((False, False, False), dir.orm.persistencestate)

    def it_creates_nested_directories(self):
        dir0 = file.directory('/abc')
        dir1 = file.directory('def')
        dir2 = file.directory('ghi')

        dir0 += dir1
        dir1 += dir2

        join = os.path.join
        self.eq(dir0.path, join(dir0.store, 'radix/abc'))
        self.eq(dir1.path, join(dir0.store, 'radix/abc/def'))
        self.eq(dir2.path, join(dir0.store, 'radix/abc/def/ghi'))

        self.eq(dir0.name, dir1.inode.name)
        self.eq(dir1.name, dir2.inode.name)
        return

        for dir in (dir0, dir1, dir2):
            self.eq((True, False, False), dir.orm.persistencestate)
            self.false(dir.exists)

        dir0.save()

        dir = dir0.orm.reloaded()

        # We haven't created a file in this directory yet, so there is
        # no reason it should `exists` on the HDD.
        self.false(dir.exists)
        self.none(dir.inode)
        self.eq(dir.path, join(dir.store, 'abc'))
        self.one(dir.inodes)

        dir = dir.inodes.first
        self.false(dir.exists)
        self.eq(dir0.id, dir.inode.id)
        self.eq(dir.path, join(dir.store, 'abc/def'))
        self.one(dir.inodes)

        dir = dir.inodes.first
        self.false(dir.exists)
        self.eq(dir1.id, dir.inode.id)
        self.eq(dir.path, join(dir.store, 'abc/def/ghi'))
        self.zero(dir.inodes)

    def it_updates_with_file(self):
        """ TODO Test creating a directory then later adding multiple files
        to it.
        """

    def it_cant_save_duplicate_directory_name(self):
        ''' Try to create duplicate by name '''
        dir = file.directory('/var/snowflake')
        self.expect(None, dir.save)

        var = dir.inode
        nds = var.orm.super.orm.mappings['inodes'].value

        try:
            var.orm.super.orm.mappings['inodes'].value = file.inodes()
            dir = file.directory('/var/snowflake')
            self.one(dir.brokenrules)
            self.one(dir.orm.super.brokenrules)
            self.expect(entities.BrokenRulesError, lambda: dir.save())
        finally:
            var.orm.super.orm.mappings['inodes'].value = nds

    def it_fails_to_append_a_duplicate(self):
        # XXX
        return
        apple = file.file('apple')
        tree = file.directory('/var/tree')

        tree += apple

        apple = file.file('apple')
        
        # We shouldn't be able to add a float with the same name
        # twice.
        def f():
            tree += apple
        self.expect(ValueError, f)

    def it_calls__iter__(self):
        dir = file.directory('/lib/dir100')
        dir += file.directory(name='dir200')
        dir += file.file(name='f100')
        dir += file.file(name='f200')

        for i, nd in enumerate(dir):
            if i == 0:
                self.eq('dir200', nd.name)
            elif i == 1:
                self.eq('f100', nd.name)
            elif i == 2:
                self.eq('f200', nd.name)
            elif i == 3:
                assert False

class file_resource(tester.tester):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        clean()

        orm.security().override = True

        if self.rebuildtables:
            orm.orm.recreate(
                ecommerce.user,  ecommerce.url,   file.files,
                file.resources,  file.directory,  file.inodes,
            )

        orm.security().owner = ecommerce.users.root

        # Proprietor
        com = party.company(name='Carapacian')
        orm.security().proprietor = com
        com.save()

    def it_deletes(self):
        ''' Delete a cached-only resource '''
        # Create non-persisted, though cached, resource
        f = file.resource(
            url = 'https://cdnjs.cloudflare.com/ajax/libs/data-layer-helper/0.1.0/data-layer-helper.min.js',
            integrity = 'sha512-X6gG74CAp34IpZcOyb1DR6leynod2ELiXbCtfkkPVfvxsFWVPqVa+BdiJd2doL7zEAKp5PtUE9YHBq0fc3b3yQ==',
            local = True,
        )

        # It will obviously be in the radix cached
        self.true(f in file.directory.radix)

        # Deleting here only means: remove from radix cache
        f.delete()

        # It will be removed from the radix cache
        self.false(f in file.directory.radix)

        ''' Delete a cached and saved resource '''
        # Recreate and save
        f = file.resource(
            url = 'https://cdnjs.cloudflare.com/ajax/libs/data-layer-helper/0.1.0/data-layer-helper.min.js',
            integrity = 'sha512-X6gG74CAp34IpZcOyb1DR6leynod2ELiXbCtfkkPVfvxsFWVPqVa+BdiJd2doL7zEAKp5PtUE9YHBq0fc3b3yQ==',
            local = True,
        )

        # Persist resource
        f.save()

        # It will be back in the radix cached
        self.true(f in file.directory.radix)

        # It will be in the database
        self.expect(None, f.orm.reloaded)

        # It wil exist in the HDD
        self.true(f.exists)

        # Now delete it
        f.delete()

        # It will be removed from the cache
        self.false(f in file.directory.radix)

        # It will no longer be in the database
        self.expect(db.RecordNotFoundError, f.orm.reloaded)

        # It will continue to not exist on the HDD.
        self.false(f.exists)
        return

        ''' Delete a cached and saved resource that has a body'''
        # Recreate and save
        f = file.resource('/tmp/rm-me')

        # Add that body
        f.body = 'hot'

        f.save()

        # It will be back in the radix cached
        self.true(f in file.directory.radix)

        # It will be in the database
        self.expect(None, f.orm.reloaded)

        # It will exist in the HDD
        self.true(f.exists)

        # Now delete it
        f.delete()

        # It will be removed from the cache
        self.false(f in file.directory.radix)

        # It will no longer be in the database
        self.expect(db.RecordNotFoundError, f.orm.reloaded)

        # It will not exist on the HDD.
        self.false(f.exists)
        # XXX
        # Ensure we:
        #     Delete from HDD. Note that resources don't always have
        #     resources stored on HDD.
        #     Delete from DB
        #     Remove from radix cache
        ...

    def it_passes_integrity_check(self):
        def get():
            file.resource(
                url='https://cdnjs.cloudflare.com/ajax/libs/shell.js/1.0.5/js/shell.min.js',
                integrity = 'sha512-8eOGNKVqI8Bg/SSXAQ/HvctEwRB45OQWwgHCNT5oJCDlSpKrT06LW/uZHOQYghR8CHU/KtNFcC8mRkWRugLQuw==',
                local = True
            )

        self.expect(None, get)

    def it_calls_url(self):
        url = 'https://cdnjs.cloudflare.com/ajax/libs/shell.js/1.0.5/js/shell.min.js'
        resx = file.resource(
            url = url,
            integrity = 'sha512-8eOGNKVqI8Bg/SSXAQ/HvctEwRB45OQWwgHCNT5oJCDlSpKrT06LW/uZHOQYghR8CHU/KtNFcC8mRkWRugLQuw==',
            local = True
        )
        self.eq(url, str(resx.url))

    def it_fails_integrity_check(self):
        tegridy = hashlib.sha512()
        tegridy.update(
            b"If you're gonna fight for your tegridy, don't forget "
            b'to bring a towel.'
        )
        tegridy = base64.b64encode(tegridy.digest()).decode('ascii')
        tegridy = f'sha512-{tegridy}'
        integrity = 'sha512-9h1vJw44WPVSKRzUsjHzwVatBzphLo8dd4Hj1xxgr3xBO3Wbs2Z2y8dDXQCOMIBzs9qT6n8HcVvnxWKJj4uWyQ=='

        path = os.path.join(
            file.inode.store, 
            'resources/cdnjs.cloudflare.com/ajax/libs/mathjs/7.5.1/math.js'
        )

        def get(integrity):
            return file.resource(
                url = 'https://cdnjs.cloudflare.com/ajax/libs/mathjs/7.5.1/math.js',
                integrity = integrity,
                local = True
            )

        # `get()` with `tegridy`. We should get an IntegrityError
        # because `tegridy` is the wrong digest.

        # XXX The below code was working fine until I started reworking
        # file.resources.
        return
        res = self.expect(file.IntegrityError, lambda : get(tegridy))
        self.false(os.path.exists(path))

        # `get()` with `integrity`. We should get no errors because
        # `integrity` is the correct digest.
        self.expect(None, lambda : get(integrity))
        self.true(os.path.exists(path))

    def it_doesnt_caches_non_local(self):
        f = file.resource(
            url="https://cdnjs.cloudflare.com/ajax/libs/geocomplete/1.7.0/jquery.geocomplete.min.js",
            integrity="sha512-4bp4fE4hv0i/1jLM7d+gXDaCAhnXXfGBKdHrBcpGBgnz7OlFMjUgVH4kwB85YdumZrZyryaTLnqGKlbmBatCpQ==",
            local = False
        )

        f1 = file.resource(
            url="https://cdnjs.cloudflare.com/ajax/libs/geocomplete/1.7.0/jquery.geocomplete.min.js",
            integrity="sha512-4bp4fE4hv0i/1jLM7d+gXDaCAhnXXfGBKdHrBcpGBgnz7OlFMjUgVH4kwB85YdumZrZyryaTLnqGKlbmBatCpQ==",
            local = False
        )

        f2 = file.resource(
            url="https://cdnjs.cloudflare.com/ajax/libs/geocomplete/1.7.0/jquery.geocomplete.min.js",
            integrity="sha512-4bp4fE4hv0i/1jLM7d+gXDaCAhnXXfGBKdHrBcpGBgnz7OlFMjUgVH4kwB85YdumZrZyryaTLnqGKlbmBatCpQ==",
            local = False
        )

        self.isnot(f, f1)
        self.isnot(f, f2)
        for nd in (f, f1, f2):
            self.true(nd not in file.directory.radix)
            self.true(nd not in file.directory._floaters)

    def it_caches_new_at_radix(self):
        f = file.resource(
            url="https://cdnjs.cloudflare.com/ajax/libs/gentelella/1.4.0/s/custom.min.js",
            integrity="sha512-ewZCd7YtttrXYKwKg3O0/ryrmq6lAQtLknQUdJpQO6FewqxRnTR4CV+e/XKfehvJIUvBwMuKJaoWd2owapsYYA==",
            local = True
        )

        f1 = file.resource(
            url="https://cdnjs.cloudflare.com/ajax/libs/gentelella/1.4.0/s/custom.min.js",
            integrity="sha512-ewZCd7YtttrXYKwKg3O0/ryrmq6lAQtLknQUdJpQO6FewqxRnTR4CV+e/XKfehvJIUvBwMuKJaoWd2owapsYYA==",
            local = True
        )

        f2 = file.resource(
            url="https://cdnjs.cloudflare.com/ajax/libs/gentelella/1.4.0/s/CUSTOM.MIN.JS",
            integrity="sha512-ewZCd7YtttrXYKwKg3O0/ryrmq6lAQtLknQUdJpQO6FewqxRnTR4CV+e/XKfehvJIUvBwMuKJaoWd2owapsYYA==",
            local = True
        )

        self.is_(f, f1)
        self.isnot(f, f2)
        for nd in (f, f1, f2):
            self.type(file.resource, nd)
            self.type(file.directory, nd.inode)
            self.true(nd in file.directory.radix)

if __name__ == '__main__':
    tester.cli().run()
