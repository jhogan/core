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

TODOs:
    TODO Implement and test the deletion of inodes collection, e.g.,:
        inodes.delete()
        directories.delete()
        files.delete()

    XXX Ensure that radix and _floaters are always have carapacian as
    their proprietors. This should be implemented after 'main' is merged
    into this branch since it contains party.carapacian.
"""

from config import config
from datetime import datetime, date
from dbg import B, PM
from func import enumerate, getattr
from entities import classproperty
from contextlib import suppress
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

class inodes(orm.entities):
    """ Represents a collection of ``inode`` entities.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.onbeforeadd += self._self_onbeforeadd

    def _self_onbeforeadd(self, src, eargs):
        flts = directory.floaters
        radix = directory.radix
        nd = eargs.entity

        # The search through the floaters directory (`nd in flts`) cause
        # a load of the directory structure and sets the composite of nd
        # back to flts. Capture the composite here and reassign later.
        comp = nd.inode

        # If the node being added is within the floaters directory
        # XXX Why are we testing if nd is in radix? Add comment
        # explaining.
        if nd in flts or nd in radix:
            # Remove it from the floaters directory
            nd.inode.inodes.remove(nd, trash=False)

            # Reset nd's comp
            while nd:
                with suppress(KeyError):
                    # Just delete the monkey match reference
                    del nd.__dict__['inode']

                if type(nd) is inode:
                    nd.orm.mappings['inode'].value = comp
                    nd.orm.mappings['inodeid'].value = comp.id

                # Repeat with al supers
                nd = nd.orm.super

    def __call__(self, key):
        try:
            return self[key]
        except IndexError:
            return None

    def __getitem__(self, key):
        """ Return an inode (file or directory) underneath the directory
        by a ``key`` name, if the argument is a str::
            
            usr = directory(name='/usr')
            words = usr['share/dict/words']

        If ``key`` is not a str, the default behavior is used.
        """

        # XXX:bda97447 If we can't find an inode memoized, I think we
        # should go ahead and search the database here.
        if isinstance(key, str):
            nds = self
            names = key.split('/')
            if len(names) == 1:
                return super().__getitem__(names[0])
            else:
                nd = nds[names[0]]
                if isinstance(nd, directory):
                    nds = nd.inodes
                    return nds['/'.join(names[1:])]
                elif isinstance(nd, file):
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

    inodes act as data singletons. This is to say that, when
    instantiated by path, the inode will be created, cached and
    returned. Additional call with the same path will result in the same
    inode being returned::

        assert directory('/etc') is directory('/etc')
        assert file('/etc/password') is file('/etc/password')

    See the overload of __new__ for details.

    Etymology
    ---------
    This entity was named after the Unix-style data structure used to
    describe file system object (files and directories).
    ``filesystemobjects`, though more descriptive, was considered too
    long to make a good class name.
    """

    # The name attribute of the file sytem object
    name = str

    # The collection of inodes each inode will have. This line makes
    # inodes recursive (self-referencing).
    inodes = inodes

    @staticmethod
    def _split(path):
        """ A private static method that takes a path a splits it over
        the '/' character. Deals with leading '/' more predictably than
        Python's builtin path splitting algorithms.
        """
        if path == '/':
            return ['/']

        names = path.split('/')

        if path.startswith('/'):
            names[0] = '/'

        return names

    def __new__(cls, *args, **kwargs):
        """ Ensure that when instantiating, we return the cached version
        of an inode object if one exists. If one doesn't exist, create,
        cache and return::

            assert directory('/etc') is directory('/etc')
            assert file('/etc/password') is file('/etc/password')
        """

        # from__new__ is a flag that, if set (to None), we arrived here
        # from a __new__ method.
        try:
            # Is the flag set
            kwargs['from__new__']
        except KeyError:
            # Set the flog
            kwargs['from__new__'] = None
        else:
            # If from__new__, instantiate and return
            return super(inode, cls).__new__(cls)

        # Get the inodes ID. This could be a str containing the path
        # ('/etc/passwd') or the UUID for the inode's primary key in the
        # database.
        try:
            id = args[0]
        except IndexError:
            try:
                id = kwargs['id']
            except KeyError:
                id = None

        # If id is a str...
        if isinstance(id, str):
            try:
                # See if str is a UUID, i.e., the inode's primary key
                id = uuid.UUID(hex=id)
            except ValueError:
                # The str id wil be considered a path
                pass

        if isinstance(id, str):
            # If id is still a str, it must be a file path so call it
            # what it is: `path`; and search the cache. Return if its in
            # the cache; otherwise, instantiate.
            path = id

            local = kwargs.get('local', False)

            # If resource and `local` is False, don't cache, i.e.,
            # don't anchor to radix or floaters (see resource.local).
            if resource in cls.mro() and not local:
                nds = [x for x in path.split('/') if x]

                if len(nds) > 1:
                    # Create the top-most directory. We will append the
                    # other inodes later.
                    nd = directory(
                        name=nds.pop(0), kwargs={'from__new__': None}
                    )
                elif len(nds) == 1:
                    # Just return the resource instance
                    return cls(*args, **kwargs)
                else:
                    raise ValueError('Invalid resource path')
            else:
                # If path starts at radix, search the radix cache,
                # otherwise, search the floaters cache (floaters are
                # cached inodes that aren't anchored to the radix yet,
                # though presumably will be).
                if path[0] == '/':
                    path = path.lstrip('/')
                    
                    dir = directory.radix
                else:
                    dir = directory.floaters

                # Create a net object to capture the details of the find
                # operation.
                net = directory.net()

                # Search cache
                dir.find(path, net)

                # If we found the path, return the tail, i.e., the last
                # element of the path: /not-tail/also-not-tail/the-tail
                if net.isfound:
                    return net.tail

                # We didn't find the path in the cache but likely found
                # a portion of it, we can used the `wanting` property of
                # `net` to instantiate everything that wasn't found.

                # Start with tail. If nothing was found, tail would be
                # the radix directory which always exists
                nd = net.tail

                nds = net.wanting

            # Iterate over the wanting inodes' names
            for i, name in enumerate(nds):
                if i.last:
                    # If we are at the last wanting inode name, cls may
                    # be a file or a directory, so use it to
                    # instantiate, consider: /dir/dir/file-or-dir
                    nd += cls(name=name, **kwargs)
                else:
                    # If we are not at the last one, the wanting inode
                    # will be a directory (the last one may or may not
                    # be a file inode name). Add to heirarchy.
                    nd += directory(
                        name=name, kwargs={'from__new__': None}
                    )

                # nd becomes the last inode appended above
                nd = nd.inodes.last

            # Return the last inode appended above
            return nd
        elif isinstance(id, uuid.UUID):
            # Perform a database lookup using the primary key
            return cls(*args, **kwargs)

        elif isinstance(id, type(None)):
            # Create new inode
            return cls(*args, **kwargs)
        else:
            raise TypeError(f'Unsupported type {type(id)}')

        # TODO Could we ever get here? We should probably remove.
        return None

    def __init__(self, *args, **kwargs):
        # Don't call super's init if it has already been called.
        if not self.orm.isinstance:
            # In __new__, we instantiate the inode. However, when the
            # instantiated inode returns from __new__, it is passed to
            # __init__. We don't want to call orm.entity.__init__ a
            # second time on the object if that is the case.
            super().__init__(*args, **kwargs)

    @classproperty
    def store(cls):
        """ Returns a physical file system path as a string containing
        the root directory where all files should be stored, e.g.,

             '/var/www/core/development'

        The environment determines the path. Above, the path is clearly
        for a development environment. config.py contains the actual
        path that will be returned.
        """
        return config().store

    @property
    def inradix(self):
        """ Returns True if this inode is currently in the radix cache.
        """

        # TODO This is dead and untested but may be useful
        nd = self
        radix = directory.radix

        while nd:
            if nd is radix:
                return True
            nd = nd.orm.inode
        else:
            return False

    def delete(self):
        """ Removes the inode from the HDD, database and the radix
        cache. 
        """
        # Remove from radix cache
        rent = self.inode
        if rent:
            nds = rent.inodes
            nds.remove(self, trash=False)
        else:
            nds = None

        try:
            # Don't care if it dosn't exist
            with suppress(FileNotFoundError):
                # Delete inode from HDD
                if isinstance(self, directory):
                    shutil.rmtree(self.path)
                elif isinstance(self, file):
                    os.unlink(self.path)
                else:
                    raise TypeError('Incorrect inode type')
        except Exception as ex:
            # Add back to cache if we can't unlink
            if nds:
                nds += self
            raise
        else:
            try:
                # Delete from db
                super().delete()
            except Exception as ex:
                # Add back to cache if we delete
                if nds:
                    nds += self
                raise

    @property
    def isfloater(self):
        """ Returns True if the inode is in the floater cache.
        """
        return self in directory.floaters

    @property
    def root(self):
        """ Return the root inode.
        """
        nd = self
        while True:
            if nd.inode:
                nd = nd.inode
            else:
                return nd

    def __getitem__(self, key):
        """ Return a (file or directory) underneath this inode by a
        ``key`` name, if the argument is a str. If ``key`` is not a str,
        the default behavior for entities is used.
        """

        # Delegate indexing for a directory to inode's indexer.
        return self.inodes[key]

    def __iadd__(self, e):
        """ Overload +=
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
        """ Return the path of the file (as str) as located within the
        HDD's filesystem.
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

        for nd in nds:
            if self.id != nd.id and nd.name == self.name:
                brs += f'Cannot create "{self.name}": inode exist'
                break

        # XXX Create brokenrules object via instatiation so we know
        # which inode has the brokenrule. Also update tests for these.
        if self.isfloater:
            brs += f'"{self.name}" is a floater'

        return brs

class files(inodes):
    """ Represents a collection of ``file`` objects.
    """
    def append(self, e, *args, **kwargs):
        comp = ws = path = None

        # Get the composite (website) of the files collection if there
        # is one.
        
        # XXX I'm not sure why I hard-coded site here. Why don't we use
        # self.orm.composite, or have ``site`` subscribe to the onadd
        # event. Try to explain with a TODO, if not correct it all
        # together.
        # 
        # UPDATE: I think this has been corrected by the addition of
        # pom.site.directory and pom.site.resource. We can probably
        # remove all this.
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
            dir = directory(path)
            dir += e.root

        super().append(obj=e, *args, **kwargs)

class file(inode):
    """ Represents a file in the DB and on the HDD.
    """

    @orm.attr(str)
    def mime(self):
        """ The mime type of the file (as str), e.g., 'text/plain'. The
        mimetype attribute can be set by the user. If it is not set, the
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
        """ The super()'s implemention is to return the child inodes
        under this inode. However, since this is a file, we want to
        raise an AttributeError because a file would obviously never
        have files or directories underneath it. 
        
        Note we are using the `orm` modules version of AttributeError
        because there are issues raising builtins.AttributeError from
        ORM attributes (see orm.py for more). Also, note that the
        calling code will receive a regular builtins.AttributeError and
        not an orm.AttributeError so the client code doesn't have to
        deal with this awkwardness.
        """
        # TODO We need to find a better way to do this. The user should
        # not have to use a specialized AttributeError.
        raise orm.AttributeError(
            "file entities don't have inodes"
        )

    def __init__(self, *args, **kwargs):
        """ Initializes a file object.

        Note that all inodes are cached based on their path. Read the
        docstring at inode.__new__ for details.
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

        # If there is a body to the file, we want to save it. Otherwise
        # there is no point. If eargs.op == 'delete', that means the
        # save was actually a delete. In that case, we don't want to
        # save the file to the HDD.
        if self._body and eargs.op != 'delete':
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
        """ Returns the contents of the file. 
        
        The property will read the contents into a private varable if
        they have not already been memoized. Subsequent calls to body
        will return the contents of the private variable.
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

            # A call to save() writes the metadata to the database first
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

class resource(file):
    """ Represents a resource. A ``resource`` is a type of file routinely
    used by websites to act as third-party resources such a JavaScript
    libraries, CSS files and fonts.

    Resources are special files in that they can be defined as
    originating from an external source such as a CDN. This class can be
    configured to pull from the CDN and store locally, eliminating the
    need for a developer to manually manage the resource file on the
    hard drive.
    """

    def __new__(cls, *args, **kwargs):
        try:
            kwargs['from__new__']
        except KeyError:
            pass
        else:
            return super(inode, cls).__new__(cls)

        try:
           url = kwargs['url']
        except KeyError:
            pass
        else:
            if isinstance(url, str):
                import ecommerce
                kwargs['url'] = ecommerce.url(address=url)

        # The following code depends on a url being present
        try:
            url = kwargs['url']
        except KeyError:
            pass
        else:
            # The below comments will assume a url of:
            # https://cdnjs.cloudflare.com/ajax/libs/shell.js/1.0.5/js/shell.min.js
            # Create list with hostname and all paths, e.g., 
            #
            #     [
            #         'cdnjs.cloudflare.com', 'ajax', 'libs', 
            #         'shell.js', '1.0.5', 'js', 'shell.min.js'
            #    ]
            dirs = [url.host, *url.paths]

            # Create a path with the remaining elements then create a
            # `directory`, e.g., 
            #
            #     'cdnjs.cloudflare.com/ajax/libs/shell.js/1.0.5/js'
            args = ['/' + os.sep.join(dirs), *args]

            
        return super().__new__(cls, *args, **kwargs)

    def __init__(self, *args, **kwargs):
        """ Initialize a resource.

        :param: url str|ecommerce.url: The URL of the external resource.

        :param: local bool: If True, persist the resource's metadata in
        the database during a `resource.save()` call and cache the file
        data to the local hard drive located under the `inode.store`
        directory. 
        
        Allowing `local` to default to False causes no persistence to
        ever happen. This can be useful if you only want to use the
        ``resource`` object as a data structure for HTML authoring, such
        as when you want to reference a CDN's URL for a JavaScript or
        CSS library - causing the user's browser to download the
        resource from the CDN rather than the webserver.
        """
            
        super().__init__(*args, **kwargs)
        self.orm.default('crossorigin', 'anonymous')
        self.orm.default('integrity', None)
        self.onbeforesave += self._entity_onbeforesave

        self.local = kwargs.get('local', False)

    def _entity_onbeforesave(self, src, eargs):
        """ This event handler is called before the resource is saved to
        the database.
        """
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
        """ Returns the URL of the resource as a string.
        """
        return str(self.url)

    def _self_onaftersave(self, src, eargs):
        """ The event handler called after the resource has been saved
        to the database.

        After the ``resource`` has been saved to the database, the
        resource file is written to the file system. If there is an
        Exception caused during the file system interaction, the
        Exception will be allowed to bubble up - causing the the
        database transaction to be rolled back.
        """
        if eargs.op != 'delete':
            self._write()
        super()._self_onaftersave(src, eargs)

    def _write(self):
        """ Downloads the resource file from the CDN (or whatever) and
        save to local hard drive.

        Basically we download the URL at self.url to self.path.
        If self.integrity was set, it is used to validate the file. If
        the integrity check fails, an IntegrityError is raised.
        """
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
    """ Represents a directory in a file system.
    """

    # The primary key for the radix directory
    RadixId = uuid.UUID(hex='2007d124039f4cefac2cbdf1c8d1001b')

    # The primary key for the floaters directory
    FloatersId = uuid.UUID(hex='f1047325d07c467f9abef26bbd9ffd27')

    def __contains__(self, nd):
        """ Overides the `in` operator to recursively search the file
        system, starting at self, for a directory with the same primary
        key::

            usr = directory('/usr')
            bin = directory('/usr/bin')
            ls = file('/usr/bin/ls')

            assert ls in usr
            assert bin in usr
        """
        # XXX Write tests
        for nd1 in self:
            if nd.id == nd1.id:
                return True

            if isinstance(nd1, directory):
                if nd in nd1:
                    return True

        return False

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)

        if self.isradix:
            del directory._radix

    class net:
        """ An inner class used as an argument to directory.find to
        indicate search results. The ``found`` property indicates which
        part of the path was found and the ``wanting`` property
        indicates which part of the path is wanting.
        """

        def __init__(self):
            """ Create the found and wanting lists.
            """
            self.found = list()
            self.wanting = list()

        @property
        def isfound(self):
            """ Indicates that the complete path was found; no portion
            of the path was found wanting.
            """
            return bool(self.found) and not self.wanting

        @property
        def tail(self):
            """ The last found inode.
            """
            try:
                return self.found[-1]
            except IndexError:
                return None

        def __repr__(self):
            """ A string representation of the search results.
            """
            r = type(self).__name__
            r += '('
            r += f'isfound={self.isfound}, '
            r += f'found={self.found}, '
            r += f'wanting={self.wanting}, '
            r += f'tail={self.tail!r}'
            r += ')'
            return r

    # XXX We may be able to rename this __getitem__
    def find(self, key, net=None, recursing=False):
        """ Recursively search for a path starting at self.

            # Create a net object to capture results
            net = self.net()

            # Get a directory to search in
            usr = directory('/usr')

            # Use find to search within usr
            usr.find('bin/ls'), net)

            # Check `net` for results

            # Looks like `ls` is in /usr/bin
            assert net.isfound 
            assert net.found[0] == 'ls'
            assert net.wanting = []
            assert net.tail.name == 'ls'

            # Search again for a file that dosen't exist
            net = self.net()
            usr.find('bin/init'), net)

            # Hmm, `/usr/bin/init` was not found
            assert not net.isfound

            # `bin` was found, though
            assert net.found[0].name == 'bin'

            # But `init` was not found. Must be in /usr/sbin
            assert net.wanting[0].name == 'init'
        """
        if isinstance(key, list):
            # Key must be the path structured as a list, which is what
            # we want.
            pass
        elif isinstance(key, str):
            # Assume key is a path ('/etc/passwd') and split it to make
            # key a list.
            key = self._split(key)
        else:
            raise TypeError('Path is wrong type')

        # `recursing` will be True if are entering find() for the first
        # time.
        if not recursing:
            # Create a net object if we don't have one to store results
            # of search
            if not net:
                net = self.net()

            # If nothing has been found in the search, we can at least
            # say that self has been found.
            if not net.found:
                net.found.append(self)

        # Get the name of the inode to search for
        name = key[0]

        # Search for path
        try:
            # Search for name in immediate children
            nd = self.inodes[name]
        except IndexError as ex:
            # Couldn't find the inode in immediate children so add the
            # remaining inode names to `wanting` to record the part of
            # the path we were not able to find. Return None because
            # that concludes our search.
            net.wanting.extend(key)
            return None
        else:
            # The inode was found so append to the net's found.
            # Contining searching for the rest of the path by recursing
            # into the found inode.
            net.found.append(nd)
            if len(key) > 1:
                nd.find(key[1:], net, recursing=True)

        # If we are here, we found the entire path. Return the tail
        # (i.e., the last element in a path).
        return net.tail

    def file(self, path):
        """ Create a new file underneath `self` in the hierarchy and
        return the file:
            
            etc = directory('/etc')
            passwd = etc.file('passwd')

        Above, we used the name 'passwd' for the file name, but we could
        have specified a whole path::

            my = directory(path='/my')
            txt = my.file('path/to/file.txt')

        Now, txt represents the physical file::

            {inode.store}/my/path/to/file.txt
        """
        path = path.lstrip('/')
        f = file(path)

        # Append the inode right beneath the file's floaters to self,
        # this might be the file itself.
        nd = f
        while nd:
            if nd.inode is directory._floaters:
                self += nd
                break

            nd = nd.inode
        else:
            raise ValueError('Radix not found')

        return f

    @classproperty
    def radix(cls):
        """ Returns the radix directory.

        The radix directory is the root directory of all inodes that are
        properly stored in the syste (as opposed to floaters). radix is
        memoized here because, through it, we keep the entire file
        system tree in memory.

        If the radix directory does not exist in the database, it is
        created in the database and in the file system.

        Etymology
        ---------
        radix is just another word for root. Since inode is a recursive
        entity, 'root' is already taken as a @property name. 
        """
        if not hasattr(cls, '_radix'):
            # TODO:3d0fe827 Shouldn't we be instantiating a
            # ``directory`` here, instead of cls. cls will almost always
            # be ``directoy`` but there is no reason it should be
            # varient.

            # TODO Write test to ensure radix is always owned by root.
            
            import party
            with orm.sudo():
                with orm.proprietor(party.company.carapacian):
                    cls._radix = cls(id=cls.RadixId, name='radix')
                    cls._radix.save()

        return cls._radix
    
    @property
    def isradix(self):
        """ Returns True if this directory is the radix directory; False
        otherwise.
        """
        return self.id == self.RadixId and self.inode is None

    # XXX This should be private (_floaters)
    @classproperty
    def floaters(cls):
        """ Returns a directory to store inodes under until they are
        ready to be attached to the the radix cache. 

        Consider the following file::
            
            f = file('myfile')

        Since it wasn't created off the root (it doesn't start with a
        /), it isn't attached to the radix. It just floats in the
        floaters cache. 

            assert f in directory.floaters
            assert f not in directory.radix

        This is fine, but to get the file properly in the
        file system, we need to attach it to the radix/root.

            d = directory('/mydirectory')
            d += f

        /mydirectory, since it was started with a /, is in the
        radix cache. Attaching f to mydirectory will ensure the myfile
        is put under mydirectory and thus a part of the radix cache. It
        will also be removed from the floaters cache.

            assert f not in directory.floaters
            assert f in directory.radix

        Now we can save f:

            f.save()
        """
        if not hasattr(cls, '_floaters'):
            # TODO:3d0fe827 Shouldn't we be instantiating a
            # ``directory`` here, instead of cls. cls will almost always
            # be ``directoy`` but there is no reason it should be
            # varient.

            # TODO Write test to ensure floaters is always owned by
            # root.
            with orm.sudo():
                try:
                    cls._floaters = cls(cls.FloatersId)
                except db.RecordNotFoundError:
                    cls._floaters = cls(id=cls.FloatersId, name='.floaters')
                    cls._floaters.save()
        return cls._floaters

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
