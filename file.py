# vim: set et ts=4 sw=4 fdm=marker

# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2020

""" TODO

Examples:
    TODO

Todo:
"""

from datetime import datetime, date
from dbg import B
import orm
import os.path
import textwrap
import pathlib

class files(orm.entities):
    pass

class resources(files):
    pass

class file(orm.entity):
    path = str

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.body = None

    @property
    def basename(self):
        return os.path.basename(self.path)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        dir = self.directory
        try:
            pathlib.Path(dir).mkdir(parents=True, exist_ok=True)
        except PermissionError as ex:
            raise PermissionError(
                'The file store needs to be created for the environment '
                f'and given the appropriate permissions ({ex})'
            )

    @property
    def directory(self):
        # TODO Make this configurable
        #dir = config().filestore
        dir = '/var/www/development/'

        dirs = textwrap.wrap(self.id.hex, 2)

        dirs.pop()

        dir = dir + '/'.join(dirs)
        return dir

class resource(file):
    def __init__(self, local=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.orm.default('crossorigin', 'anonymous')
        self.orm.default('integrity', None)

        if local:
            self.save()

    url        =  str
    integrity  =  str

    # The crossorigin attribute is analogous to the 'crossorigin'
    # attribute in <script>.
    #
    # Here are the possible values:
    #     'anonymous' - CORS requests for the script element will
    #     have the credentials flag set to 'same-origin'. (default)
    #
    #     'use-credentials' - CORS requests for this element will
    #     have the credentials flag set to 'include'.
    crossorigin  =  str

    def _self_onbeforesave(self, *args, **kwargs):
        import sys
        '''
        l = sys.path[0]
        del sys.path[0]
        del sys.modules['http']
        '''

        import urllib.request
        url = 'https://code.jquery.com/jquery-3.5.1.js'
        with urllib.request.urlopen(url) as f:
            print(f.read(200))


        super()._self_onbeforesave(*args, **kwargs)


