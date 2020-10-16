# vim: set et ts=4 sw=4 fdm=marker

# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2020

""" This module contains class to help deal with files in a web context. 

File (and directory) metadata are stored in the database (this is why
the ``file`` and ``directory`` classes inherit from ``orm.entity``). If
a ``file`` object contains data in its ``body`` attribute, the file will
be written to disk. ``file`` and ``directory`` both inherit from
``inode`` which is a recursive entity allowing for a virtually infinite
hierchical depth (as one would expect in any file system).

Examples:

    # Create a directory in memory
    dir = directory(path='/my/directory')

    # Add a file to the directory (nothing has been written to disk at
    # this moment)
    dir += file(name='my.file')

    # Save three entries to the database: one for both the 'my' and
    # 'directory' directories, and one for the 'my.file' file. Since the
    # 'my.file' object no data in it's body property, a file won't be
    # saved to the HDD. Since ``directory`` is a recursive entity, the
    # save will be recursive.
    dir.save()

    # Get my file from dir's indexor
    f = dir['directory/my.file']

    # Set the body 
    f.body = 'My text file'

    assert f.mime == 'text/plain'

    f.save()

    # The file will now exist on the HDD
    assert f.exists

    # The file will be located under ``inode.store``
    assert f.path == inode.store + '/my/directory/my.file'

    # Again, the file will exist
    assert os.path.exists(f.path)


See tfile.py for more examples.
"""

from datetime import datetime, date
from dbg import B
from func import enumerate, getattr, B
import contextlib
import db
import mimetypes
import orm
import os.path
import pathlib
import shutil
import textwrap
import urllib.request
import hashlib
import base64

class inodes(orm.entities):
    """ Represents a collection of ``inode`` entities.
    """
    def __getitem__(self, key):
        """ Return an inode (file or directory) underneath the directory
        by a ``key`` name, if the argument is a str::
            
            usr = directory(name='/usr')
            words = usr['share/dict/words']

        If ``key`` is not a str, the default behavior is used.
        """
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
    """ The abstract class from which ``file`` and ``directory``
    inherit. ``inode`` has a ``name`` property used for the file or
    directory name. ``inodes`` are recursive. This gives the
    ``directory`` class an ``inodes`` collection which contains the
    files and directories in that directory. ``files`` and
    ``directories`` also contain an ``inode`` attribute which refers to
    their parent ``directory``.

    The name "inode" was chosen after the Unix-style data structure used
    to describe file system object (files and directories).
    ``filesystemobjects`, though more descriptive,` was considered too
    long to make a good class name.
    """

    # The name attribute of the file sytem object
    name = str

    # The collection of inodes each inode will have. This line make
    # inodes recursive (self-referencing).
    inodes = inodes

    # TODO Make this configurable
    #store = config().filestore

    # This is the directory under which all the directories and files
    # will be stored.
    store = '/var/www/core/development'

    def __init__(self, *args, **kwargs):
        """ Init the ``inode``. If a ``path`` argument is given in
        ``kwargs``, we can use the path to create or load files and
        directories::

            f = file(path='/path/to/my/file')
        """
        try:
            path = kwargs['path']
        except KeyError:
            super().__init__(*args, **kwargs)
        else:
            del kwargs['path']

            # If a path was given in the kwargs, we can use it to load
            # or create a path for the directory or file.
            super().__init__(*args, **kwargs)

            dir = self._getdirectory(path=path)

            if isinstance(self, directory):
                # Get the root directory
                while True:
                    if dir.inode:
                        dir = dir.inode
                    else:
                        break

                # Set self's attribute to those of the root directory
                for attr in ('id', 'name'):
                    setattr(self, attr, getattr(dir, attr))

                # Move the inode objcet from the root directories'
                # inodes collection into that of self's
                for nd in dir.inodes:
                    st = nd.orm.persistencestate
                    self.inodes += nd
                    e = nd

                    # Adjust the persistencestate so self is that of
                    # what was loaded or created
                    while e:
                        e.orm.persistencestate = st
                        e = e.orm._super

                # Adjust the persistencestate so self is that of
                # what was loaded or created.
                e = self
                while e:
                    e.orm.persistencestate = dir.orm.persistencestate
                    e = e.orm._super

            if isinstance(self, file):
                # Load/create the file
                _, name = os.path.split(path)
                f = self._getfile(name=name, dir=dir)
                if f:
                    # Set attributes of the file to those of self
                    for attr in ('id', 'name', 'mime'):
                        setattr(self, attr, getattr(f, attr))

                    # The record isn't new or dirty so set all peristance state
                    # variables to false.
                    st = f.orm.persistencestate
                else:
                    st = self.orm.persistencestate
                    self.name = name

                # If dir was loaded/created above, put self underneath
                if dir:
                    dir += self

                # Adjust persistencestate
                e = self
                while e:
                    e.orm.persistencestate = st
                    e = e.orm._super

    def _getfile(self, name, dir=None):
        """ Load and return a file by name which is under ``dir``.
        """
        id = dir.id if dir else None
        op = '=' if id else 'is'

        nds = inodes(f'name = %s and inodeid {op} %s', name, id)

        if nds.hasone:
            nd = nds.first
            return file(nd.id)

        return None

    def _getdirectory(self, path):
        """ Load or create a file given a ``path``.
        """
        if isinstance(self, file):
            head, tail = os.path.split(path)
        else:
            head, tail = path, None

        names = [x for x in head.split('/') if x]

        dir = None

        # Iterate over each directory name
        search = True
        for i, name in enumerate(names):
            id = dir.id if dir else None
            op = '=' if id else 'is'

            if search:
                # Search for the inode record of the directory
                nds = inodes(
                    f'name = %s and inodeid {op} %s', name, id
                )

                if nds.hasone:
                    # Downcast the inode to a directory
                    try:
                        dir1 = directory(nds.first.id)
                    except db.RecordNotFoundError:
                        # inode exists but directory doesn't. Unless
                        # there is a data integrity issue, the user
                        # is attempting to create a `directory`
                        # where a `file` already exists. Add a new
                        # `file` entity and depend on the validation
                        # logic to report this issue.

                        dir1 = file(nds.first.id)
                elif nds.isempty:
                    # If the directory couldn't be found, stop
                    # searching and begin creating new ones.
                    search = False
                    dir1 = directory(name=name)

                else:
                    raise ValueError(
                        f'Name matches multiple inodes: {name}'
                    )
            else:
                dir1 = directory(name=name)

            if dir:
                # Maintain one directory tree by setting/appending
                # the new/existing directory to the parent trees
                # inodes collection.
                for i, nd in enumerate(dir.inodes):
                    if nd.name == dir1.name:
                        dir.inodes[i] = dir1
                        break
                else:
                    dir.inodes += dir1
                # FIXME:349f4355 The below assignment is a
                # hack to work around the fact tha
                # currently, `inode` (the recursive parent)
                # loads as an inode instead of downcasting
                # to its most specialized class.  When this
                # is corrected in the ORM, we can remove
                # this assignment.
                st = dir1.orm.persistencestate
                dir1.inode = dir
                e = dir1
                while e:
                    e.orm.persistencestate = st
                    e = e.orm._super
            else:
                if not search:
                    dir1 = directory(name=name)

            dir = dir1

        return dir

    def __getitem__(self, key):
        """ Delegate indexing for a directory to inode's indexor.
        """
        return self.inodes[key]

    def __iadd__(self, e):
        """ Overload +=.
        """
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
        """ Return the path the file is (or would be) on the HDD.
        """
        return os.path.join(self.head, self.name)

    @property
    def exists(self):
        """ Return True if the file or directory currently exists on the
        HDD; False otherwise
        """
        return os.path.exists(self.path)

    def getbrokenrules(self, *args, **kwargs):
        """ Return broken validation rules.
        """
        brs = super().getbrokenrules(*args, **kwargs)
        id = self.inode.id if self.inode else None
        op = '=' if id else 'is'
        nds = inodes(f'name = %s and inodeid {op} %s', self.name, id)

        if nds.ispopulated and self.id != nds.first.id:
            msg = f'Cannot create "{self.name}": inode exist'

            # FIXME:acad30cc Because of the way brokenrules currently
            # works, this method ends up getting called multiple times.
            # Until this is fixed, we have to make sure the rule has not
            # already been added.
            if msg not in brs.pluck('message'):
                brs += msg

        return brs

class files(inodes):
    """ Represents a collection of ``file`` objects.
    """
    pass

class file(inode):
    """ Represents a file in the DB and on the HDD.
    """

    @orm.attr(str)
    def mime(self):
        """ The mime type of the file, e.g., text/plain. The mimetype
        attribute can be set by the user. If it is not set, the
        accessor will try to guess what it should be given the ``body``
        attribute and the ``file.name``.
        """
        # TODO:545a5261 Use Pythons mimetypes library to guess based on
        # path/url/extension
        if not attr():
            mime = mimetypes.guess_type(self.path, strict=False)[0]
            if mime is not None:
                attr(mime)
            elif isinstance(self._body, str):
                attr('text/plain')
            elif isinstance(self._body, bytes):
                attr('application/octet-stream')
            elif self._body is None:
                attr(None)
        return attr()

    @property
    def inodes(self):
        """ Raise an AttributeError because a file would obviously never
        have files or directories underneath it. 
        
        Note we are using the `orm` modules version of AttributeError
        because there are issues raising builtins.AttributeError from
        ORM attributes (see orm.py for more). Also note that the calling
        code will receive a regular builtins.AttributeError and not an
        orm.AttributeError so the client code doesn't have to deal with
        this awkwardness.
        """
        raise orm.AttributeError(
            "file entities don't have inodes"
        )

    def __init__(self, *args, **kwargs):
        """ Init a file entity.
        """
        self._body = None
        super().__init__(*args, **kwargs)

    @property
    def mimetype(self):
        """ Returns the **type** portion of the mime string. For
        example, if ``self.mime`` is:
                
            image/jpeg

        only the string 'image' will be returned.
        """
        mime = self.mime
        if mime:
            return mime.split('/')[0]
        return None

    def _self_onaftersave(self, src, eargs):
        """ This is the event handler that gets called immediately after
        the file has been saved to the database. If ``file.body``
        contains data, the file will be written to the disk. If the file
        looks like a text file given its ``mime`` type, it will be
        written as a text (mode='wt'); otherwise, it will be written as
        a binary file (mode='wb').
        """

        if self._body:
            # First ensure the directory exists
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

            # Decide on the mode
            if self.mimetype == 'text':
                mode = 'wt'
            else:
                mode = 'wb'

            # Write the data
            with open(self.path, mode) as f:
                f.write(self.body)

        # Ensure the event handler at orm.entity is called.
        super()._self_onaftersave(src, eargs)

    @property
    def body(self):
        """ Returns the contens of the file. 
        
        The property will read the contents into a private varable if
        they have not already been memoized. Subsequent calls to body
        wll return the contents of the private variable.
        """
        path = self.path
        if self._body is None and os.path.isfile(path):
            mode = 'rt' if self.mimetype == 'text' else 'rb'
            with open(path, mode) as f:
                self._body = f.read()
        
        return self._body

    @body.setter
    def body(self, v):
        """ Sets the contents of the file::
            
            # Create the file
            f = file(name='myfile.txt')

            # Set the body attribute
            f.body = 'My Body'

            # A call to save() write the metadata to the database first
            # then write the ``body`` to the file (stored at f.path.
            f.save()

            # Reload
            f1 = file(f.id)

            # The reloaded entity contains the same body text
            assert f.body == f1.body
        """
        # TODO Changing the `body` should make the file `isdirty`
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
        # TODO This should use self.store, not self.publicdir.
        # ``publicdir`` can be removed.
        return f'{self.publicdir}/{os.path.basename(self.url)}'

    @property
    def public(self):
        # TODO Investigate whether we should be using symlinks
        return self.symlink

class resources(files):
    """ Represents a collection of ``resource`` entities.
    """
    pass

class resource(file):
    """ Represent a resource. A ``resource`` is a type of file routinely
    used by websites to act as third-party resources such a JavaScript
    libraries, CSS files and fonts.

    Resources are special files in that they can be defined as
    originating from an external source such as a CDN. This class can be
    configured to pull from the CDN and stored locally, eliminating the
    need for a developer to manually manage the resource file on the
    hard drive.
    """

    # The external location of the resources.
    url        =  str

    # A cryptigraphic hash that the external resource is assumed to
    # have. This will often match the hash found in a <script>'s
    # `integrity` attribute:
    #
    #     <script src="https://example.com/example-framework.js"
    #         integrity="sha384-oqVuAfXRKap7fdgcCY5uykM6+R9GqQ8K/uxy9rx7HNQlGYl1kPzQho1wx4JwY8wC"
    #         crossorigin="anonymous">
    #     </script>
    #
    integrity  =  str

    # The crossorigin attribute is analogous to the 'crossorigin'
    # attribute in <script>.
    #
    # Possible values
    #     'anonymous' - CORS requests for the script element will
    #     have the credentials flag set to 'same-origin'. (default)
    #
    #     'use-credentials' - CORS requests for this element will
    #     have the credentials flag set to 'include'.
    crossorigin  =  str

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.orm.default('crossorigin', 'anonymous')
        self.orm.default('integrity', None)

        try:
            self.local = kwargs['local']
        except KeyError:
            self.local = False

        if self.local:
            urlparts = urllib.parse.urlsplit(self.url)
            dirs = ['resources', urlparts.netloc]
            dirs.extend([x for x in urlparts.path.split('/') if x])
            self.name = dirs.pop()
            path = '/'.join(dirs)

            res = directory(path=path)

            # TODO:545a5261 When mimetypes is used, we can let it
            # determine the mimetype.
            self.mime = 'text/plain'

            last = res['/'.join(dirs[1:])]
            last += self

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
                with urlopen(req) as req:
                    # TODO Test integrity before saving
                    body = req.read()
                    algo, digest = self.integrity.split('-')
                    digest = base64.b64decode(digest)
                    algo = getattr(hashlib, algo.lower())()
                    algo.update(body)
                    if algo.digest() != digest:
                        raise IntegrityError(
                            f'Invalid digest: {self.url}'
                        )

                # TODO Use the correct mode based on mimetype
                with open(path, 'wb') as f:
                    f.write(body)

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
    """ Represents a collection of ``directory`` entities.
    """
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
                # TODO Ensure that if `dir` happens to be a `file`, an # appropriate Exception is raised.
            except IndexError:
                nd = directory(name=dir)
                nds += nd
            
            nds = nd.inodes

        return nd

    def __iter__(self):
        for nd in self.inodes:
            yield nd

class IntegrityError(ValueError):
    pass

