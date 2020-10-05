#! /usr/bin/python3

# vim: set et ts=4 sw=4 fdm=marker

########################################################################
# Copyright (C) Jesse Hogan - All Rights Reserved                      #
# Unauthorized copying of this file, via any medium is strictly        #
# prohibited                                                           #
# Proprietary and confidential                                         #
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2020                 #
########################################################################

import tester
import file
import orm
import party
import pom
import dom
import uuid
import base64
import os.path
import entities
from func import enumerate, getattr, B

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

class foonet(pom.site):
    def __init__(self, host='foo.net'):
        super().__init__(host)

        ''' Metadata '''
        self.lang = 'es'
        self.charset = 'iso-8859-1'

class dom_file(tester.tester):
    """ Test interoperability between DOM objects and the ``file``
    entity.
    """
    def __init__(self):
        super().__init__()
        orm.orm.recreate(
            party.user,
            file.files,
            file.resources,
            file.directory,
            file.inodes,
        )

    def it_links_to_js_files(self):
        file.file.orm.truncate()
        class index(pom.page):
            def main(self):
                head = self['html head'].first

                head += dom.script(
                    file.resource(
                        url='https://code.jquery.com/jquery-3.5.1.js',
                    )
                )

                head += dom.script(
                    file.resource(
                        url='https://cdnjs.cloudflare.com/ajax/libs/shell.js/1.0.5/js/shell.min.js',
                        integrity='sha512-8eOGNKVqI8Bg/SSXAQ/HvctEwRB45OQWwgHCNT5oJCDlSpKrT06LW/uZHOQYghR8CHU/KtNFcC8mRkWRugLQuw=='
                    )
                )

                head += dom.script(
                    file.resource(
                        url='https://cdnjs.cloudflare.com/ajax/libs/vega/5.14.0/vega.min.js',
                        crossorigin='use-credentials',
                    )
                )

                self.main += dom.h1('Home page')

        # Set up site
        ws = foonet()
        ws.pages += index()

        # GET the /en/files page
        tab = self.browser().tab()
        res = tab.get('/en/index', ws)

        self.status(200, res)

        scripts = res['html head script']
        self.three(scripts)

        self.eq(
            'https://code.jquery.com/jquery-3.5.1.js',
            scripts.first.src
        )
        self.eq(None, scripts.first.integrity)
        self.eq('anonymous', scripts.first.crossorigin)

        self.eq(
            'https://cdnjs.cloudflare.com/ajax/libs/shell.js/1.0.5/js/shell.min.js',
            scripts.second.src
        )
        self.eq(
            'sha512-8eOGNKVqI8Bg/SSXAQ/HvctEwRB45OQWwgHCNT5oJCDlSpKrT06LW/uZHOQYghR8CHU/KtNFcC8mRkWRugLQuw==',
            scripts.second.integrity
        )
        self.eq('anonymous', scripts.second.crossorigin)

        self.eq(
            'https://cdnjs.cloudflare.com/ajax/libs/vega/5.14.0/vega.min.js',
            scripts.third.src
        )

        self.eq(None, scripts.third.integrity)
        self.eq('use-credentials', scripts.third.crossorigin)

        for script in scripts:
            # We aren't caching these resources so we should expect any to
            # be in the database
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

                dir = usr.directory
                avatars = dir.mkdir('/var/avatars/')
                default = avatars.file('default.gif')
                default.body = f.body
                usr.save()
                res.status = 201

        # Set up site
        ws = foonet()
        ws.pages += avatar()

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
        file.resource.orm.truncate()
        class index(pom.page):
            def main(self):
                head = self['html head'].first

                head += dom.script(
                    file.resource(
                        url = 'https://code.jquery.com/jquery-3.5.1.js',
                        local = True
                    )
                )

                head += dom.script(
                    file.resource(
                        url = 'https://cdnjs.cloudflare.com/ajax/libs/shell.js/1.0.5/js/shell.min.js',
                        integrity = 'sha512-8eOGNKVqI8Bg/SSXAQ/HvctEwRB45OQWwgHCNT5oJCDlSpKrT06LW/uZHOQYghR8CHU/KtNFcC8mRkWRugLQuw==',
                        local = True
                    )
                )

                head += dom.script(
                    file.resource(
                        url = 'https://cdnjs.cloudflare.com/ajax/libs/vega/5.14.0/vega.min.js',
                        crossorigin = 'use-credentials',
                        local = True,
                    )
                )

                # This url will 404 so it can't be saved locally.
                # dom.script will nevertheless use the external url for
                # the `src` attribute instead of the local url. This
                # should happen any time there is an issue downloading
                # an external resource.
                head += dom.script(
                    file.resource(
                        url =
                        'https://cdnjs.cloudflare.com/ajax/libs/55439c02/1.1/idontexit.min.js',
                        crossorigin = 'use-credentials',
                        local = True,
                    )
                )

                self.main += dom.h1('Home page')

        # Set up site
        ws = foonet()
        ws.pages += index()

        # GET the /en/files page
        tab = self.browser().tab()
        res = tab.get('/en/index', ws)

        self.status(200, res)

        scripts = res['html head script']
        self.four(scripts)

        # TODO:52612d8d Make a configuration option
        #dir = config().public
        dir = os.path.join(file.file.store, 'public')

        self.eq(
            f'{dir}/jquery-3.5.1.js',
            scripts.first.src
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
        self.zero(f.inodes)
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
        self.zero(f.inodes)
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
        self.zero(f1.inodes)
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
        self.zero(f.inodes)
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
        self.zero(f.inodes)
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

        # TODO --------------------------
        return

        path = '/var/db/my.db'

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
        f = file.file(name='dup.txt')
        self.expect(None, lambda: f.save())

        f = file.file(name='dup.txt')
        self.expect(entities.BrokenRulesError, lambda: f.save())

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

        # TODO Test using one directory (file.directory(path='/tmp'))
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

if __name__ == '__main__':
    tester.cli().run()
