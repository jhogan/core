#! /usr/bin/python3

# vim: set et ts=4 sw=4 fdm=marker

########################################################################
# Copyright (C) Jesse Hogan - All Rights Reserved                      #
# Unauthorized copying of this file, via any medium is strictly        #
# prohibited                                                           #
# Proprietary and confidential                                         #
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2020                 #
########################################################################

from func import enumerate, getattr, B
import asset
import base64
import dom
import entities
import file
import hashlib
import orm
import os.path
import party
import pom
import tester
import uuid

# TODO Ensure that integrity can be None

def clean():
    store = file.file.store

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
    def __init__(self):
        super().__init__()
        orm.orm.recreate(
            party.user,      file.files,   file.resources,
            file.directory,  file.inodes,  pom.site, foonet, asset.asset
        )

    def it_adds_js_files_to_site(self):
        for e in ('inode', 'resource', 'resource'):
            getattr(file, e, 'orm.truncate')()

        ws = foonet()

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

        self.two(ress)
        self.two(ress1)

        for res, res1 in zip(ress, ress1):
            self.eq(res.id, res1.id)
            self.eq(res.url, res1.url)
            self.eq(res.integrity, res1.integrity)

    def it_adds_js_files_to_page(self):
        for e in ('inode', 'resource', 'resource'):
            getattr(file, e, 'orm.truncate')()

        class index(pom.page):
            def main(self):
                head = self['html head'].first

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
            # We aren't caching these resources (`local = True`) so we
            # should expect any to be in the database
            self.zero(file.resources(url=script.src))

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
                
                usr = party.user(uid)
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
        usr = party.user(name='luser')
        usr.save()

        # Post the file. Reference the user's id in the URL.
        res1 = tab.post(f'/en/avatar?uid={usr.id}', ws, files=f)
        self.status(201, res1)

        usr = usr.orm.reloaded()
        f1 = usr.directory['var/avatars/default.gif']
        f1 = f1.orm.cast(file.file)
        self.eq(f.body, f1.body)

    def it_caches_js_files(self):
        # TODO:34080104 I've decided we need to correct a number of
        # problems in the ORM before completing this test and
        # file.resources in general. The problem with this test is that
        # .append() overrides (see 34080104) want to prepend
        # ``directory`` entities named after the `pom.site.id`. This is
        # causing issues because the `inode.inode` returns the general
        # object (inode) instead of the special object (directory). 
        #
        # A similar issue that I have had to work around for this is the
        # issues where collection attributes load only general objects.
        # For example:
        #
        #     dir = directory(id):
        #     for nd in dir.inodes:
        #         assert type(nd) is inode
        #
        # The above will always be true, but dir.inodes should only
        # contain file and directory objects; never `inode` objects
        # because `inodes` are abstract entities and there are always
        # more specialized versions.
        #
        # It would also be desirable to have `directories` and `files`
        # attributes in addition to inodes:
        #
        #     dir = directory(id):
        #     assert dir.inodes.count == 10
        #     assert dir.files.count == 3
        #     assert dir.directories.count == 4
        #     assert dir.resources.count == 3
        return


        file.resource.orm.truncate()
        class index(pom.page):
            def main(self):
                self.resources += file.resource(
                    url = 'https://cdnjs.cloudflare.com/ajax/libs/shell.js/1.0.5/js/shell.min.js',
                    integrity = 'sha512-8eOGNKVqI8Bg/SSXAQ/HvctEwRB45OQWwgHCNT5oJCDlSpKrT06LW/uZHOQYghR8CHU/KtNFcC8mRkWRugLQuw==',
                    local = True
                )

                self.resources += file.resource(
                    url = 'https://cdnjs.cloudflare.com/ajax/libs/vega/5.14.0/vega.min.js',
                    crossorigin = 'use-credentials',
                    local = True,
                )

                # This url will 404 so it can't be saved locally.
                # dom.script will nevertheless use the external url for
                # the `src` attribute instead of the local url. This
                # should happen any time there is an issue downloading
                # an external resource.
                self.resources += file.resource(
                    url = 'https://cdnjs.cloudflare.com/ajax/libs/55439c02/1.1/idontexit.min.js',
                    crossorigin = 'use-credentials',
                    local = True,
                )

                self.resources.save()

                self.main += dom.h1('Home page')

        # Set up site
        ws = foonet()
        ws.pages += index()

        ws.resources += file.resource(
            url = 'https://code.jquery.com/jquery-3.5.1.js',
            local = True
        )

        ws.save()

        # GET the /en/files page
        tab = self.browser().tab()
        res = tab.get('/en/index', ws)

        self.status(200, res)

        scripts = res['html head script']
        self.four(scripts)

        # TODO:52612d8d Make a configuration option
        #dir = config().public
        dir = file.file.store

        self.eq(
            f'/{ws.id.hex}/cdnjs.cloudflare.com/ajax/libs/shell.js/1.0.5/js/shell.min.js',
            scripts.second.src
        )
        self.eq(None, scripts.first.integrity)
        self.eq('anonymous', scripts.first.crossorigin)

        self.eq(
            f'{dir}/shell.min.js',
            scripts.second.src
        )
        self.eq(
            'sha512-8eOGNKVqI8Bg/SSXAQ/HvctEwRB45OQWwgHCNT5oJCDlSpKrT06LW/uZHOQYghR8CHU/KtNFcC8mRkWRugLQuw==',
            scripts.second.integrity
        )
        self.eq('anonymous', scripts.second.crossorigin)

        self.eq(
            f'{dir}/vega.min.js',
            scripts.third.src
        )
        self.eq(None, scripts.third.integrity)
        self.eq('use-credentials', scripts.third.crossorigin)

        self.eq(
            'https://cdnjs.cloudflare.com/ajax/libs/55439c02/1.1/idontexit.min.js',
            scripts.fourth.src
        )
        self.none(scripts.fourth.integrity)
        self.eq('use-credentials', scripts.fourth.crossorigin)

        self.four(file.resources.orm.all)

        rcs = file.resources(
            'url', 'https://code.jquery.com/jquery-3.5.1.js'
        )
        self.one(rcs)
        self.none(rcs.first.integrity)
        self.eq('anonymous', rcs.first.crossorigin)

        rcs = file.resources(
            'url', 'https://cdnjs.cloudflare.com/ajax/libs/shell.js/1.0.5/js/shell.min.js'
        )
        self.one(rcs)
        self.eq('sha512-8eOGNKVqI8Bg/SSXAQ/HvctEwRB45OQWwgHCNT5oJCDlSpKrT06LW/uZHOQYghR8CHU/KtNFcC8mRkWRugLQuw==', rcs.first.integrity)
        self.eq('anonymous', rcs.first.crossorigin)

        rcs = file.resources(
            'url', 'https://cdnjs.cloudflare.com/ajax/libs/vega/5.14.0/vega.min.js'
        )

        self.one(rcs)
        self.none(rcs.first.integrity)
        self.eq('use-credentials', rcs.first.crossorigin)

        rcs = file.resources(
            'url', 'https://cdnjs.cloudflare.com/ajax/libs/55439c02/1.1/idontexit.min.js'
        )

        self.one(rcs)
        self.none(rcs.first.integrity)
        self.eq('use-credentials', rcs.first.crossorigin)
        self.false(rcs.first.exists)

class file_file(tester.tester):
    def __init__(self):
        super().__init__()
        clean()

        orm.orm.recreate(
            party.user,
            file.files,
            file.resources,
            file.directory,
            file.inodes,
        )

    def it_creates_empty_file(self):
        ''' Instatiate file '''
        f = file.file(name='myfile')
        self.eq(f.store, f.head)
        self.eq(f.path, os.path.join(f.store, 'myfile'))
        self.false(f.exists)
        self.false(os.path.exists(f.path))
        self.eq('myfile', f.name)
        self.none(f.inode)
        self.expect(AttributeError, lambda: f.inodes)
        self.none(f.body)
        self.none(f.mime)

        ''' Saving the file with no body set '''
        f.save()
        self.eq(f.store, f.head)
        self.eq(f.path, os.path.join(f.store, 'myfile'))

        # Since there is no body, there will be no corresponding file
        # saved
        self.false(f.exists)
        self.false(os.path.exists(f.path))

        self.eq('myfile', f.name)
        self.none(f.inode)
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

        self.eq('myfile', f1.name)
        self.none(f1.inode)
        self.expect(AttributeError, lambda: f.inodes)
        self.none(f1.body)
        self.none(f.mime)

    def it_creates_text_file(self):
        ''' Instatiate file '''
        f = file.file(name='myfile.txt')

        body = self.dedent('''
        Line 1
        Line 2
        ''')

        f.body = body
        self.eq(body, f.body)
        self.eq('text/plain', f.mime)
        self.true(isinstance(f.body, str))

        ''' Saving the file with '''
        f.save()
        self.eq(f.path, os.path.join(f.store, 'myfile.txt'))
        self.true(f.exists)
        self.true(os.path.exists(f.path))
        self.true(isinstance(f.body, str))
        self.eq('text/plain', f.mime)

        self.eq('myfile.txt', f.name)
        self.none(f.inode)
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
        f = file.file(name='myfile.bin')

        body = base64.b64decode(
            'R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7'
        )

        f.body = body
        self.eq(body, f.body)
        self.eq('application/octet-stream', f.mime)
        self.true(isinstance(f.body, bytes))

        ''' Saving the file '''
        f.save()
        self.eq(f.path, os.path.join(f.store, 'myfile.bin'))
        self.true(f.exists)
        self.true(os.path.exists(f.path))
        self.eq('application/octet-stream', f.mime)
        self.true(isinstance(f.body, bytes))

        self.eq('myfile.bin', f.name)
        self.none(f.inode)
        self.expect(AttributeError, lambda: f.inodes)
        self.eq(body, f.body)

        f1 = f.orm.reloaded()
        self.eq(f.body, f1.body)
        self.eq('application/octet-stream', f.mime)
        self.true(isinstance(f.body, bytes))
        self.true(f1.exists)
        self.true(os.path.exists(f1.path))

    def it_creates_within_a_directory(self):
        ''' Instatiate file with `path` off root '''

        path = 'myotherfile'

        # This will create the file off the root
        f = file.file(path=path)

        body = self.dedent('''
        Line 1
        Line 2
        ''')

        f.body = body
        self.eq(body, f.body)

        f.save()
        self.eq(f.path, os.path.join(f.store, path))
        self.true(f.exists)
        self.true(os.path.exists(f.path))

        self.eq(path, f.name)
        self.none(f.inode)
        self.eq(body, f.body)

        f1 = f.orm.reloaded()
        self.eq(f.body, f1.body)
        self.true(f1.exists)
        self.true(os.path.exists(f1.path))

        ''' Instatiate file with `path` off within a new directory '''
        path = '/usr/share/file'

        # This will create the file off the root
        f = file.file(path=path)

        body = self.dedent('''
        Line 1
        Line 2
        ''')

        f.body = body
        self.eq(body, f.body)

        f.save()
        path = path.lstrip('/')
        self.eq(f.path, os.path.join(f.store, path))
        self.true(f.exists)
        self.true(os.path.exists(f.path))

        self.eq(os.path.split(path)[1], f.name)
        self.eq('share', f.inode.name)
        self.eq('usr', f.inode.inode.name)
        self.eq(body, f.body)

        f1 = f.orm.reloaded()
        self.eq(f.body, f1.body)
        self.true(f1.exists)
        self.true(os.path.exists(f1.path))

    def it_loads_within_a_directory(self):
        ''' Create file in root '''

        path = 't.txt'

        # This will create the file off the root
        f = file.file(path=path)

        body = self.dedent('''
        Line 1
        Line 2
        ''')

        f.body = body
        f.save()

        # Reload using `path`
        f1 = file.file(path=path)
        self.eq(body, f1.body)

        ''' Create file within new directory '''
        path = '/var/db/my.db'
        f = file.file(path=path)
        f.body = body
        self.eq('my.db', f.name)
        self.eq(os.path.join(f.store, 'var/db/my.db'), f.path)
        self.false(f.exists)
        self.eq((True, False, False), f.orm.persistencestate)

        dir = f.inode
        self.eq('db', dir.name)
        self.eq(os.path.join(dir.store, 'var/db'), dir.path)
        self.false(dir.exists)
        self.eq((True, False, False), dir.orm.persistencestate)

        dir = dir.inode
        self.eq('var', dir.name)
        self.eq(os.path.join(dir.store, 'var'), dir.path)
        self.false(dir.exists)
        self.eq((True, False, False), dir.orm.persistencestate)
        self.none(dir.inode)

        f.save()

        self.eq('my.db', f.name)
        self.eq(os.path.join(f.store, 'var/db/my.db'), f.path)
        self.true(f.exists)
        self.eq((False, False, False), f.orm.persistencestate)

        dir = f.inode
        self.eq('db', dir.name)
        self.eq(os.path.join(dir.store, 'var/db'), dir.path)
        self.true(dir.exists)
        self.eq((False, False, False), dir.orm.persistencestate)

        dir = dir.inode
        self.eq('var', dir.name)
        self.eq(os.path.join(dir.store, 'var'), dir.path)
        self.true(dir.exists)
        self.eq((False, False, False), dir.orm.persistencestate)
        self.none(dir.inode)

        ''' Reload using `path` '''
        f = file.file(path=path)
        self.eq(body, f.body)
        self.eq('my.db', f.name)
        self.eq(os.path.join(f.store, 'var/db/my.db'), f.path)
        self.true(f.exists)
        self.eq((False, False, False), f.orm.persistencestate)

        dir = f.inode
        self.eq('db', dir.name)
        self.eq(os.path.join(dir.store, 'var/db'), dir.path)
        self.true(dir.exists)
        self.eq((False, False, False), dir.orm.persistencestate)

        dir = dir.inode
        self.eq('var', dir.name)
        self.eq(os.path.join(dir.store, 'var'), dir.path)
        self.true(dir.exists)
        self.eq((False, False, False), dir.orm.persistencestate)
        self.none(dir.inode)

    def it_sets_mime(self):
        ''' Text file '''
        f = file.file(name='index.html')
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
        f = file.file(name='my.gif')
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
        f = file.file(name='dup.txt')
        self.expect(None, lambda: f.save())

        f = file.file(name='dup.txt')
        self.one(f.brokenrules)
        self.expect(entities.BrokenRulesError, lambda: f.save())

        ''' Try to create duplicate by path '''
        f = file.file(path='/my/dir/dup.txt')
        self.expect(None, lambda: f.save())

        my = file.directory(path='/my/dir')
        dir = my['dir']
        f = file.file(name='dup.txt')
        dir += f
        self.one(my.brokenrules)
        self.expect(entities.BrokenRulesError, lambda: my.save())

    def it_raises_AttributeError_on_file_inodes(self):
        f = file.file(path='/850cad31/498c/4584')
        self.expect(AttributeError, lambda: f.inodes)

    def it_becomes_dirty_when_body_is_changed(self):
        f = file.file(name='minecraft.dat')
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
        f = file.file(name='autoexec.bat')
        f.body = body

        self.eq(body, f.body)

        f.save()

        self.eq(body, f.body)

        f = f.orm.reloaded()

        self.eq(body, f.body.decode('ascii'))

class file_directory(tester.tester):
    def __init__(self):
        super().__init__()
        clean()

        orm.orm.recreate(
            party.user, file.files, file.resources,
            file.directory, file.inodes,
        )

    def it_creates_off_root(self):
        dir = file.directory(name='mydir')
        self.eq('mydir', dir.name)
        self.none(dir.inode)
        self.zero(dir.inodes)
        self.eq((True, False, False), dir.orm.persistencestate)

        dir.save()
        self.eq('mydir', dir.name)
        self.none(dir.inode)
        self.zero(dir.inodes)
        self.eq((False, False, False), dir.orm.persistencestate)

        dir = dir.orm.reloaded()
        self.eq('mydir', dir.name)
        self.none(dir.inode)
        self.zero(dir.inodes)
        self.eq((False, False, False), dir.orm.persistencestate)

    def it_creates_nested_directories(self):
        dir0 = file.directory(name='abc')
        dir1 = file.directory(name='def')
        dir2 = file.directory(name='ghi')

        dir0 += dir1
        dir1 += dir2

        join = os.path.join
        self.eq(dir0.path, join(dir0.store, 'abc'))
        self.eq(dir1.path, join(dir0.store, 'abc/def'))
        self.eq(dir2.path, join(dir0.store, 'abc/def/ghi'))

        self.eq(dir0.name, dir1.inode.name)
        self.eq(dir1.name, dir2.inode.name)

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

    def it_creates_using_path(self):
        join = os.path.join

        ''' Test using one directory off the root '''
        dir = file.directory(path='/etc')

        self.eq('etc', dir.name)
        self.type(file.directory, dir)
        self.false(dir.exists)
        self.none(dir.inode)
        self.eq(dir.path, join(dir.store, 'etc'))
        self.zero(dir.inodes)
        self.eq((True, False, False), dir.orm.persistencestate)

        dir.save()

        self.eq('etc', dir.name)
        self.false(dir.exists)
        self.none(dir.inode)
        self.eq(dir.path, join(dir.store, 'etc'))
        self.zero(dir.inodes)
        self.eq((False, False, False), dir.orm.persistencestate)

        ''' Testing using two directories '''
        dir = file.directory(path='/tmp/test')

        tmp = dir

        self.eq('tmp', dir.name)
        self.type(file.directory, dir)
        self.false(dir.exists)
        self.none(dir.inode)
        self.eq(dir.path, join(dir.store, 'tmp'))
        self.one(dir.inodes)
        self.eq((True, False, False), dir.orm.persistencestate)

        dir = dir.inodes.first
        self.type(file.directory, dir)
        self.false(dir.exists)
        self.eq('tmp', dir.inode.name)
        self.eq(dir.path, join(dir.store, 'tmp/test'))
        self.zero(dir.inodes)
        self.eq((True, False, False), dir.orm.persistencestate)

        dir = tmp

        dir.save()

        self.eq('tmp', dir.name)
        self.false(dir.exists)
        self.none(dir.inode)
        self.eq(dir.path, join(dir.store, 'tmp'))
        self.one(dir.inodes)
        self.eq((False, False, False), dir.orm.persistencestate)

        dir = dir.inodes.first
        self.false(dir.exists)
        self.eq('tmp', dir.inode.name)
        self.eq(dir.path, join(dir.store, 'tmp/test'))
        self.zero(dir.inodes)
        self.eq((False, False, False), dir.orm.persistencestate)

        ''' Load existing directory '''
        dir = file.directory(path='/tmp/test')

        self.eq('tmp', dir.name)
        self.type(file.directory, dir)
        self.false(dir.exists)
        self.none(dir.inode)
        self.eq(dir.path, join(dir.store, 'tmp'))
        self.one(dir.inodes)
        self.eq((False, False, False), dir.orm.persistencestate)

        dir = dir.inodes.first
        self.false(dir.exists)
        self.eq('tmp', dir.inode.name)
        self.eq(dir.path, join(dir.store, 'tmp/test'))
        self.zero(dir.inodes)
        self.eq((False, False, False), dir.orm.persistencestate)

        ''' Create new directory under existing directory '''
        dir = file.directory(path='/tmp/test1')

        self.eq('tmp', dir.name)
        self.type(file.directory, dir)
        self.false(dir.exists)
        self.none(dir.inode)
        self.eq(dir.path, join(dir.store, 'tmp'))
        self.two(dir.inodes)
        self.eq((False, False, False), dir.orm.persistencestate)

        for dir in dir.inodes:
            self.false(dir.exists)
            self.eq('tmp', dir.inode.name)
            self.zero(dir.inodes)
            if dir.name == 'test':
                self.eq(dir.path, join(dir.store, 'tmp/test'))
                self.eq((False, False, False), dir.orm.persistencestate)
            elif dir.name == 'test1':
                self.eq(dir.path, join(dir.store, 'tmp/test1'))
                self.eq((True, False, False), dir.orm.persistencestate)
            else:
                assert False

    def it_updates_with_file(self):
        """ TODO Test creating a directory then later adding multiple files
        to it.
        """

    def it_cant_save_duplicate_directory_name(self):
        ''' Try to create duplicate by name '''
        dir = file.directory(name='dup')
        self.expect(None, lambda: dir.save())

        dir = file.directory(name='dup')
        self.one(dir.brokenrules)
        self.expect(entities.BrokenRulesError, lambda: dir.save())

        ''' Try to create duplicate by path '''
        dir = file.directory(path='/herp/derp')
        self.expect(None, lambda: dir.save())

        dir = file.directory(path='/herp')
        dir += file.directory(name='derp')
        self.one(dir.brokenrules)
        self.expect(entities.BrokenRulesError, lambda: dir.save())

    def it_calls__iter__(self):
        dir = file.directory(path='/lib/dir100')
        dir += file.directory(name='dir200')
        dir += file.file(name='f100')
        dir += file.file(name='f200')

        for i, nd in enumerate(dir):
            if i == 0:
                self.eq('dir100', nd.name)
            elif i == 1:
                self.eq('dir200', nd.name)
            elif i == 2:
                self.eq('f100', nd.name)
            elif i == 3:
                self.eq('f200', nd.name)
            else:
                assert False

class file_resource(tester.tester):
    def __init__(self):
        super().__init__()
        clean()

        orm.orm.recreate(
            party.user, file.files, file.resources,
            file.directory, file.inodes,
        )

    def it_passes_integrity_check(self):
        def get():
            file.resource(
                url='https://cdnjs.cloudflare.com/ajax/libs/shell.js/1.0.5/js/shell.min.js',
                integrity = 'sha512-8eOGNKVqI8Bg/SSXAQ/HvctEwRB45OQWwgHCNT5oJCDlSpKrT06LW/uZHOQYghR8CHU/KtNFcC8mRkWRugLQuw==',
                local = True
            )

        self.expect(None, get)

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

        # TODO The below code was working fine until I started reworking
        # file.resources.
        return
        res = self.expect(file.IntegrityError, lambda : get(tegridy))
        self.false(os.path.exists(path))

        # `get()` with `integrity`. We should get no errors because
        # `integrity` is the correct digest.
        self.expect(None, lambda : get(integrity))
        self.true(os.path.exists(path))

if __name__ == '__main__':
    tester.cli().run()
