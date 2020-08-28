# vim: set et ts=4 sw=4 fdm=marker

# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2020

""" This module contains class to help deal with files in a web context. 

Examples:
    See test.py:dom_files for examples.

Todo:
"""

from datetime import datetime, date
from dbg import B
import orm
import os.path
import pathlib
import textwrap
import urllib.request
import shutil
import contextlib

class files(orm.entities):
    pass

class resources(files):
    pass

class file(orm.entity):
    body = bytes
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

    # FIXME This should be a static property
    @property
    def directory(self):
        # TODO Make this configurable
        #dir = config().filestore
        dir = '/var/www/development'

        pathlib.Path(dir).mkdir(
            parents=True, exist_ok=True
        )
        return dir

    @property 
    def store(self):
        dir = f'{self.directory}/file/store'
        pathlib.Path(dir).mkdir(
            parents=True, exist_ok=True
        )
        return dir

    @property
    def file(self):
        return f'{self.store}/{self.id.hex}'

    @property
    def exists(self):
        return os.path.isfile(self.file)

    # FIXME This should be a static property
    @property
    def publicdir(self):
        # TODO:52612d8d Make this configurable
        #dir = config().public
        dir = '/var/www/development/public'

        try:
            pathlib.Path(dir).mkdir(
                parents=True, exist_ok=True
            )
        except PermissionError as ex:
            raise PermissionError(
                f'The public directory ({dir}) needs to be created '
                'for the environment and given the appropriate '
                f'permissions ({ex})'
            )
        return dir

    @property
    def symlink(self):
        return f'{self.publicdir}/{os.path.basename(self.url)}'

    @property
    def public(self):
        return self.symlink

class resource(file):
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

    def __init__(self, local=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.orm.default('crossorigin', 'anonymous')
        self.orm.default('integrity', None)
        self.local = local

        if local:
            if self.orm.isnew:
                self.save()
            elif not self.exists:
                self.write()
                
    def _self_onaftersave(self, *args, **kwargs):
        """ After the ``resource`` has been saved to the database, write
        the resource file to the file system along with a symlink. If
        there is an Exception caused during the file system interaction,
        the Exception will be allowed to bubble up - causing the the
        database transaction to be rolled back.
        """
        self.write()
        super()._self_onaftersave(*args, **kwargs)

    def write(self):
        # Get the file and the symlink
        file = self.file
        ln = self.symlink

        try:
            try:
                # Write the file to the file system
                urlopen = urllib.request.urlopen
                with urlopen(self.url) as req, open(file, 'wb') as f:
                    # TODO Test integrity before saving
                    shutil.copyfileobj(req, f)

            except urllib.error.HTTPError as ex:
                # We won't be able to cache, but that shouldn't be a show
                # stopper. We may want to log, though.
                pass
            else:
                # Delete the symlink if it exists
                with contextlib.suppress(FileNotFoundError):
                    os.unlink(ln)

                # Create the symlink
                os.symlink(self.file, ln)
        except Exception as ex:
            # Remove the file and symlink if there was an exception
            with contextlib.suppress(Exception):
                os.remove(file)
                os.remove(ln)
            
            # Allow the exception to bubble up to the ORM's persistence
            # logic - allowing it to rollback the transaction.
            raise

