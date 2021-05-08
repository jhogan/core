# vim: set et ts=4 sw=4 fdm=marker

# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2021

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

    # Get my file from dir's indexer
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

See testfile.py for more examples.
"""

from config import config
from datetime import datetime, date
from dbg import B
from func import enumerate, getattr, B
from entities import classproperty
import base64
import entities
import contextlib
import db
import hashlib
import mimetypes
import orm
import os.path
import pathlib
import shutil
import textwrap
import urllib.request
import uuid

class cache:
    _instance = None
    def __new__(cls):
        if not cls._instance:
            sup = super(cache, cls)
            cls._instance = sup.__new__(cls)
            cls._instance._inodes = dict()

        return cls._instance

    def __getitem__(self, path):

        if isinstance(path, inode):
            nd = path
            for k, v in self._inodes.items():
                if v is nd:
                    return k
            else:
                raise KeyError(
                    f'Could not find key for "{nd!r}"'
                )

        return self._inodes[path]

    def __setitem__(self, path, v):
        self._inodes[path] = v

    def _cache(self, nd, rent):
        path = rent + nd
        self._inodes[path] = nd

    def clear(self):
        self._inodes.clear()

class inodes(orm.entities):
    """ Represents a collection of ``inode`` entities.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.onadd += self._self_onadd

    def _self_onadd(self, src, eargs):
        return
        B(self.orm.isloading)

        if self.orm.isloading:
            return

        def replace(nd, ndadd):
            if nd is not ndadd:
                if nd.name == ndadd.name:
                    if nd.inode is ndadd.inode:
                        # TODO Determine how to replace
                        preserve = True
                        if preserve:
                            rent = nd.inode

                            if rent:
                                ...
                            else:
                                # nd is at the root
                                ...

                            nds[i] = ndadd
                        else:
                            inode = eargs.inode
                            if inode:
                                rent[x] = nd
                            else:
                                ...
                        return

            if not isinstance(nd, file):
                for nd1 in nd.inodes:
                    replace(nd1, ndadd)

            if not isinstance(ndadd, file):
                for ndadd1 in ndadd.inodes:
                    replace(nd, ndadd1)

        for nd in self:
            replace(nd.root, eargs.entity.root)
                    

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
                            f"Can't find node: {name}"
                        )
                    else:
                        if isinstance(nd, directory):
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
    (``filesystemobjects`, though more descriptive,` was considered too
    long to make a good class name.)
    """

    # The name attribute of the file sytem object
    name = str

    # The collection of inodes each inode will have. This line makes
    # inodes recursive (self-referencing).
    inodes = inodes

    @classmethod
    def produce(cls, path):
        if not path.startswith('/'):
            path = '/' + path
        
        try:
            return cache()[path]
        except KeyError:
            pass

        # Get head and tail portion of path
        head, tail = os.path.split(path)

        # Create new directory path
        heads = [x for x in os.path.split(head) if x]

        prev = None
        for i, dir in enumerate(heads):
            # Create a string to uniquely identify dir
            ix = os.path.join(*heads[:i + 1])
            try:
                dir = cache()[ix]
            except KeyError:
                dir = directory(name=dir)

            if prev:
                prev += dir
                B()
                cache()[ix] = dir

            prev = dir

        # Create tailing file, directory, resource, etc.
        tail = cls(name=tail)

        # Append tail to previous directory
        if prev:
            prev += tail

        # Cache tail
        cache()[path] = tail

        return tail

    @classproperty
    def store(cls):
        return config().store

    @property
    def root(self):
        nd = self
        while True:
            if nd.inode:
                nd = nd.inode
            else:
                return nd

    @staticmethod
    def _getfile(name, dir=None):
        """ Load and return a file by name which is under ``dir``.
        """
        id = dir.id if dir else None
        op = '=' if id else 'is'

        nds = inodes(f'name = %s and inodeid {op} %s', name, id)

        if nds.hasone:
            nd = nds.first
            # TODO We can just return nd now
            return file(nd.id)

        return None

    def _getdirectory(self, path):
        """ Load or create a file given a ``path``.
        """
        if isinstance(self, file):
            head, tail = os.path.split(path)
        else:
            head, tail = path, None

        dir = None
        if head:
            # Create directory
           
            names = [x for x in head.split('/') if x]

            name = names.pop(0)

            nds = inodes(
                f'name = %s and inodeid is %s', name, None
            )

            if nds.hasone:
                dir = nds.first
            elif nds.isempty:
                dir = directory(name=name)

            for name in names:
                if dir.orm.isnew:
                    dir += directory(name=name)
                    dir = dir.inodes.last
                else:
                    try:
                        dir = dir.inodes[name]
                    except IndexError:
                        dir += directory(name=name)
                        dir = dir.inodes.last

        return dir

    def __getitem__(self, key):
        """ Return a (file or directory) underneath this inode by a
        ``key`` name, if the argument is a str. If ``key`` is not a str,
        the default behavior for entiteis is used.
        """

        # Delegate indexing for a directory to inode's indexer.
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
        borrowed terminology from os.path.split()
        """
        dir = inode.store

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
        """ Return the path of the file as located within the HDD's
        filesystem.
        """
        return os.path.join(self.head, self.name)

    @property
    def relative(self):
        """ The path of the file with the ``store`` portion remove.
        """
        names = list()
        names.append(self.name)

        dir = self.inode

        while dir:
            names.append(dir.name)
            dir = dir.inode

        return '/' + '/'.join(reversed(names))

    @property
    def exists(self):
        """ Return True if the file or directory currently exists on the
        HDD; False otherwise
        """
        return os.path.exists(self.path)

    @property
    def brokenrules(self):
        """ Return broken validation rules.
        """
        brs = entities.brokenrules()

        id = self.inode.id if self.inode else None
        op = '=' if id else 'is'
        nds = inodes(f'name = %s and inodeid {op} %s', self.name, id)
        if nds.ispopulated and self.id != nds.first.id:
            msg = f'Cannot create "{self.name}": inode exist'

            # FIXME:acad30cc Because of the way brokenrules
            # currently works, this method ends up getting called
            # multiple times.  Until this is fixed, we have to make
            # sure the rule has not already been added.
            if msg not in brs.pluck('message'):
                brs += msg

        return brs

class files(inodes):
    """ Represents a collection of ``file`` objects.
    """
    def append(self, e, *args, **kwargs):
        comp = ws = path = None

        # Get the composite (website) of the files collection if there
        # is one.
        try:
            ws = self.site
        except AttributeError:
            try:
                ws = self.page.site
            except AttributeError:
                pass
            else:
                comp = ws
        else:
            comp = ws

        if comp:
            path = f'/{comp.id.hex}'
            try:
                uuid.UUID(hex=e.root.name)
            except ValueError as ex:
                # The root directory's name is not a UUID
                pass
            else:
                # If the root name and the composite's name are the
                # same, then set `path` to None so the directory isn't
                # prepended below.
                if e.root.name == comp.id.hex:
                    path = None

        if path:
            dir = directory(path=path)
            dir += e.root

        super().append(obj=e, *args, **kwargs)

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
        # TODO We need to find a better way to do this. The user should
        # not have to use a specialized AttributeError.
        raise orm.AttributeError(
            "file entities don't have inodes"
        )

    def __init__(self, *args, **kwargs):
        """ Init the ``inode``. If a ``path`` argument is given in
        ``kwargs``, we can use the path to create or load files and
        directories::

            f = file(path='/path/to/my/file')
        """

        self._body = None

        # If a path was given in the kwargs, we can use it to load
        # or create a path for the file.
        path = kwargs.pop('path', None)

        super().__init__(*args, **kwargs)

        if not path:
            return

        dir = self._getdirectory(path=path)

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
            modes = 'wb', 'wt'
            if self.mimetype == 'text':
                modes = reversed(modes)

            # Write the data
            for i, mode in enumerate(modes):
                try:
                    with open(self.path, mode) as f:
                        f.write(self.body)
                except TypeError as ex:
                    if not i.first:
                        raise ex
                else:
                    break

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
            # then write the ``body`` to the file (stored at f.path).
            f.save()

            # Reload
            f1 = file(f.id)

            # The reloaded entity contains the same body text
            assert f.body == f1.body
        """
        self._setvalue('_body', v, '_body', strip=False)
        
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

    def __init__(self, *args, **kwargs):
        """ Initialize a resource.

        :param: url str|ecommerce.url: The URL of the external resource.

        :param: local bool: If True, persist the resource's metadata in
        the database duing a `resource.save()` call and cache the file
        data to the local hard drive located under the `inode.store`
        directory. 
        
        Allowing `local` to default to False causes no persistence to
        ever happen. This can be useful if you only want to use the
        ``resource`` object as a data structure for HTML authoring, such
        as when you want to reference a CDN's URL for a JavaScript or
        CSS library - causing the user's browser to download the
        resource from the CDN rather than the webserver.
        """
        try:
           url = kwargs['url']
        except KeyError:
            pass
        else:
            if isinstance(url, str):
                import ecommerce
                kwargs['url'] = ecommerce.url(address=url)
            
        super().__init__(*args, **kwargs)
        self.orm.default('crossorigin', 'anonymous')
        self.orm.default('integrity', None)
        self.onbeforesave += self._entity_onbeforesave

        self.local = kwargs.get('local', False)

        # The following code depends on a url being present
        if not self.url:
            return

        # The below comments will assume a url of:
        # https://cdnjs.cloudflare.com/ajax/libs/shell.js/1.0.5/js/shell.min.js

        # Create list with hostname and all paths, e.g., 
        #
        #     [
        #         'cdnjs.cloudflare.com', 'ajax', 'libs', 
        #         'shell.js', '1.0.5', 'js', 'shell.min.js'
        #    ]
        dirs = [self.url.host, *self.url.paths]

        # The last in the list ('shell.min.js') will be the name of the
        # resource file (shell.min.js)
        self.name = dirs.pop()

        # Create a path with the remaining elements then create a
        # `directory` e.g., 
        #
        #     'cdnjs.cloudflare.com/ajax/libs/shell.js/1.0.5/js'
        path = os.sep.join(dirs)
        dir = directory(path=path)

        # Get the last directory in the path
        # (ajax/libs/shell.js/1.0.5/js) and assign it to dir
        path = os.sep.join(dirs[1:])
        if path:
            dir = dir.inodes[path]

        # Add the new `resource` underneath the directory, e.g., add the
        # shell.min.js resource under the js directory.
        dir += self

    def _entity_onbeforesave(self, src, eargs):
        # Cancel saving resource to database if local is False. See the
        # comments for the ``local`` paramenter in the docstring for
        # resource.__init__.
        eargs.cancel = not self.local

    # A cryptographic hash that the external resource is assumed to
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

    def __str__(self):
        return self.url

    def _self_onaftersave(self, *args, **kwargs):
        """ After the ``resource`` has been saved to the database, write
        the resource file to the file system. If there is an Exception
        caused during the file system interaction, the Exception will be
        allowed to bubble up - causing the the database transaction to
        be rolled back.
        """
        self._write()
        super()._self_onaftersave(*args, **kwargs)

    def _write(self):
        # Get the file
        path = self.path

        try:
            os.makedirs(self.head, exist_ok=True)
            try:
                urlopen = urllib.request.urlopen

                # Create a request that has a spoofed user-agent. Some
                # CDN's will return a 403 Forbidden if they think Python
                # is making the request.


                # TODO When www.request and www.browser become mature,
                # let's use that to download files.
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
                    body = req.read()

                    # Raise exception if the file downloaded does have
                    # the same digest as the one stored in
                    # `self.integrity`. 
                    if self.integrity:
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
        except Exception as ex:
            # Remove the file if there was an exception
            with contextlib.suppress(Exception):
                os.remove(path)
            
            # Allow the exception to bubble up to the ORM's persistence
            # logic - allowing it to rollback the transaction.
            raise

class directories(inodes):
    """ Represents a collection of ``directory`` entities.
    """

class directory(inode):
    def __init__(self, *args, **kwargs):
        """ Init the ``directory``. If a ``path`` argument is given in
        ``kwargs``, we can use the path to create or load files and
        directories::

            f = file(path='/path/to/my/file')
        """
        # If a path was given in the kwargs, we can use it to load
        # or create a the directory.
        path = kwargs.pop('path', None)
        super().__init__(*args, **kwargs)
        if not path:
            return

        dir = self._getdirectory(path=path)
        root = dir.root

        # Set self's attribute to those of the root directory
        for attr in ('id', 'name'):
            setattr(self, attr, getattr(root, attr))

        # Move the inode object from the root directories'
        # inodes collection into that of self's
        for nd in root.inodes:
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
            e.orm.persistencestate = root.orm.persistencestate
            e = e.orm._super

    def file(self, path):
        """ Create a new file underneath `self` in the hierarchy and
        return the file:
            
            etc = directory(path='/etc')
            passwd = etc.file('passwd')

        Above, we used the name 'passwd' for the file name, but we could
        have specified a whole path::

            my = directory(path='/my')
            txt = my.file('path/to/file.txt')

        Now, txt represents the file::

            {inode.store}/my/path/to/file.txt
        """
        f = file(path=path)

        dir = f.inode
        while dir.inode:
            dir = dir.inode

        if dir:
            self += dir
        else:
            self += f

        return f

    def __iter__(self):
        """ Allows us it iterate over the ``directory`` object instead
        of its ``inodes`` collection::

            dir = directory(name='/etc')
            
            # Print contents of /etc
            for nd in dir:
                print(nd.name)
        """
        for nd in self.inodes:
            yield nd

class IntegrityError(ValueError):
    """ An exception that indicates there was an error comparing the
    digest stored in the database with the digest computer from a file's
    contents (``file.body``). 
    """
