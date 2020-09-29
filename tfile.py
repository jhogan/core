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
from func import enumerate, getattr, B

class foonet(pom.site):
    def __init__(self, host='foo.net'):
        super().__init__(host)

        ''' Metadata '''
        self.lang = 'es'
        self.charset = 'iso-8859-1'

class dom_files(tester.tester):
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
        dir = '/var/www/development/public'

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

    def it_creates_text_file(self):
        ''' Instatiate file '''
        f = file.file(name='myfile')

        body = self.dedent('''
        Line 1
        Line 2
        ''')

        f.body = body
        self.eq(body, f.body)

        ''' Saving the file with no body set '''
        f.save()
        self.eq(f.path, os.path.join(f.store, 'myfile'))
        self.true(f.exists)
        self.true(os.path.exists(f.path))

        self.eq('myfile', f.name)
        self.none(f.inode)
        self.zero(f.inodes)
        self.eq(body, f.body)

        f1 = f.orm.reloaded()
        self.eq(f.body, f1.body)
        self.true(f1.exists)
        self.true(os.path.exists(f1.path))

if __name__ == '__main__':
    tester.cli().run()
