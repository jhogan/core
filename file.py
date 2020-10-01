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
import contextlib
import db
import orm
import os.path
import pathlib
import shutil
import textwrap
import urllib.request
from func import enumerate, getattr, B

class inodes(orm.entities):
    def __getitem__(self, key):
        if isinstance(key, str):
            if '/' in key:
                nds = self
                for name in key.split('/'):
                    try:
                        nd = nds[name]
                    except IndexError:
                        raise IndexError(
                            "Can't find node: {name}"
                        )
                    else:
                        nds = nd.inodes
                return nd
        return super().__getitem__(key)

class inode(orm.entity):
    name = str
    inodes = inodes

    # TODO Make this configurable
    #store = config().filestore
    store = '/var/www/core/development'

    def __init__(self, *args, **kwargs):
        try:
            path = kwargs['path']
        except KeyError:
            super().__init__(*args, **kwargs)
        else:
            del kwargs['path']
            # TODO:61b43c12 Implement code that for `path` variables
            # that contain  '/':
            #
            #      /var/my/path

            super().__init__(*args, **kwargs)
            head, tail = os.path.split(path)
            names = [x for x in head.split('/') if x]

            for i, name in enumerate(names):
                if i.first:
                    dir = directory(name=name)
                else:
                    dir.inodes += directory(name=name)
                    dir = dir.inodes.last

            nds = inodes('name = %s and inodeid is %s', path, None)

            if nds.hasone:
                # TODO The below code is completely untested
                nd = nds.first
                self.id = nd.id
                self.name = nd.name
                try:
                    f = file(nd.id)
                except db.RecordNotFoundError:
                    pass
                else:
                    self.mime = f.mime

                for k, v in kwargs.items():
                    setattr(self.instance, k, getattr(nd, k))

                # The record isn't new or dirty so set all peristance state
                # variables to false.
                e = self
                while e:
                    e.orm.persistencestate = (False,) * 3
                    e = e.orm._super
            else:
                # TODO:61b43c12
                self.name = tail

            if head:
                dir += self

    def __getitem__(self, key):
        return self.inodes[key]

    def __iadd__(self, e):
        self.inodes.append(e)
        return self

    @property
    def head(self):
        """ A string representing the directory portion of the path.

        Note this property would have been called `directory`. However,
        the ORM wants to use `directory` for something else so we
        terminology borrowed from os.path.split()
        """
        dir = self.store

        dirs = list()
        nd = self
        while nd:
            if nd is not self:
                dirs.append(nd.name)
            nd = nd.inode

        dirs = '/'.join(reversed(dirs))

        if dirs:
            r = os.path.join(dir, dirs)
        else:
            r = dir
        
        return r

    @property
    def path(self):
        return os.path.join(self.head, self.name)

    @property
    def exists(self):
        return os.path.exists(self.path)

class files(inodes):
    pass

class file(inode):
    @orm.attr(str)
    def mime(self):
        if not attr():
            if isinstance(self._body, str):
                attr('text/plain')
            elif isinstance(self._body, bytes):
                attr('application/octet-stream')
            elif self._body is None:
                attr(None)
        return attr()

    # TODO Ensure a call to inodes results in an AttributeError
    def __init__(self, *args, **kwargs):
        self._body = None
        super().__init__(*args, **kwargs)

    @property
    def mimetype(self):
        """ Returns the **type** portion of the mime string. For
        example, if ``self.mime`` is:
                
            image/jpeg

        only the string 'image' will be returned.
        """
        # TODO Implemente a complimentary `mimesubtype` property 

        return self.mime.split('/')[0]

    def _self_onaftersave(self, src, eargs):
        if self._body:
            try:
                pathlib.Path(self.head).mkdir(
                    parents=True, exist_ok=True
                )
            except PermissionError as ex:
                raise PermissionError(
                    'The file store needs to be created for the '
                    'environment and given the appropriate '
                    f'permissions ({ex})'
                )

            if self.mimetype == 'text':
                mode = 'wt'
            else:
                mode = 'wb'

            with open(self.path, mode) as f:
                f.write(self.body)

        super()._self_onaftersave(src, eargs)

    @property
    def body(self):
        path = self.path
        if self._body is None and os.path.isfile(path):
            mode = 'rt' if self.mimetype == 'text' else 'rb'
            with open(path, mode) as f:
                self._body = f.read()
        
        return self._body

    @body.setter
    def body(self, v):
        self._body = v
        
    # FIXME This should be a static property
    @property
    def publicdir(self):
        dir = os.path.join(self.store, 'public')

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

class resources(files):
    pass

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
            urlparts = urllib.parse.urlsplit(self.url)
            dirs = [x for x in urlparts.path.split('/') if x]
            self.name = dirs.pop()
            path = os.path.join(
                urlparts.netloc, *dirs
            )

            res = directory(path='resources')
            dir = res.mkdir(path)
            self.mime = 'text/plain'
            dir += self

            if self.orm.isnew:
                res.save()
            elif not self.exists:
                self.write()

    def _self_onaftersave(self, *args, **kwargs):
        """ After the ``resource`` has been saved to the database, write
        the resource file to the file system along with a symlink. If
        there is an Exception caused during the file system interaction,
        the Exception will be allowed to bubble up - causing the the
        database transaction to be rolled back.
        """

        self._write()
        super()._self_onaftersave(*args, **kwargs)

    def _write(self):
        # Get the file and the symlink
        path = self.path
        ln = self.symlink

        try:
            os.makedirs(self.head, exist_ok=True)
            try:
                urlopen = urllib.request.urlopen

                # Create a request that has a spoofed user-agent. Some
                # CDN's will return a 403 Forbidden if they think Python
                # is making the request.
                req = urllib.request.Request(
                    self.url, 
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel '
                        'Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, '
                        'like Gecko) Chrome/35.0.1916.47 '
                        'Safari/537.36'
                    }
                )

                # Write the file to the file system
                with urlopen(req) as req, open(path, 'wb') as f:
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
                os.symlink(path, ln)
        except Exception as ex:
            # Remove the file and symlink if there was an exception
            with contextlib.suppress(Exception):
                os.remove(path)
                os.remove(ln)
            
            # Allow the exception to bubble up to the ORM's persistence
            # logic - allowing it to rollback the transaction.
            raise

class directories(inodes):
    pass

class directory(inode):
    # TODO Remove below line when the branch is merged back into ev orm
    # master. This line was written before inflect's pluralization was
    # introduced.
    entities = directories

    def file(self, name):
        nd = self(name)
        if not nd:
            f = file(name=name)
            self += f
            return f

        # NOTE The code below is untested
        try:
            f = file(nd)
        except RecordNotFoundError:
            return directory(nd)
        else:
            return f

    def mkdir(self, name):
        # TODO Implement `parents` and test
        nds = self.inodes
        for dir in name.split('/'):
            if not dir:
                continue

            try:
                nd = nds[dir]
                # TODO Ensure that if `dir` happens to be a `file`, an
                # appropriate Exception is raised.
            except IndexError:
                nd = directory(name=dir)
                nds += nd
            
            nds = nd.inodes

        return nd



            

