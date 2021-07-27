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


        #XXX
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
                                # nd is at the radix
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

    The name "inode" was chosen after the Unix-style data structure used
    to describe file system object (files and directories).
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
        if path == '/':
            return ['/']

        names = path.split('/')

        if path.startswith('/'):
            names[0] = '/'

        return names

    def __new__(cls, *args, **kwargs):
        try:
            kwargs['from__new__']
        except KeyError:
            kwargs['from__new__'] = None
        else:
            return super(inode, cls).__new__(cls)

        try:
            id = args[0]
        except IndexError:
            try:
                id = kwargs['id']
            except KeyError:
                id = None

        if isinstance(id, str):
            try:
                # See if we were given a uuid as a str
                id = uuid.UUID(hex=id)
            except ValueError:
                # The str id wil be considered a path
                pass

        if isinstance(id, str):
            # If id is still a str it must be a file path so call it
            # what it is, search the cache. Return if its there,
            # otherwise, instantiate.
            path = id

            # If path starts at radix, search the radix cache,
            # otherwise, search the floaters cache (floaters are cached
            # inodes that aren't anchored to the radix yet, though
            # presumably will be).
            if path[0] == '/':
                path = path.lstrip('/')
                
                dir = directory.radix
            else:
                dir = directory.floaters

            # Create a net object to capture the details of the find
            # operation.
            net = directory.net()
            dir.find(path, net)

            # If we found the path, return the tail, i.e., the last
            # element of the path: /not-tail/also-not-tail/the-tail
            if net.isfound:
                return net.tail

            # We didn't find the path in the cache but likely found a
            # portion of it, we can used the `wanting` property of `net`
            # to instantiate everything that wasn't found.

            # Start with tail. If nothing was found, tail would be the
            # radix directory which always exists
            nd = net.tail

            # Iterate over the wanting inodes' names
            for i, name in enumerate(net.wanting):
                if i.last:
                    # If we are at the last wanting inode name, cls may
                    # be a file or a directory, so use it to
                    # instantiate, consider: /dir/dir/file-or-dir
                    nd += cls(name=name, **kwargs)
                else:
                    # If we are not ate the last one, the wanting inode
                    # will be a directory (they last one may or may not
                    # be a file inode name). Add to heirarchy.
                    nd += directory(
                        name=name, kwargs={'from__new__': None}
                    )

                # nd becomes the last inode append above
                nd = nd.inodes.last

            # Return the last inode appended above
            return nd
        elif isinstance(id, uuid.UUID):
            return cls(*args, **kwargs)
        elif isinstance(id, type(None)):
            return cls(*args, **kwargs)
            
        else:
            raise TypeError(f'Unsupported type {type(id)}')

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
        return config().store

    @property
    def isfloater(self):
        return self in directory.floaters

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

            # XXX Didn't we fix this? Shouldn't this comment be removed.
            # FIXME:acad30cc Because of the way brokenrules
            # currently works, this method ends up getting called
            # multiple times.  Until this is fixed, we have to make
            # sure the rule has not already been added.
            if msg not in brs.pluck('message'):
                brs += msg

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
        self._body = None

        super().__init__(*args, **kwargs)

        return
        # XXX

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

    def __new__(cls, *args, **kwargs):
        try:
            kwargs['from__new__']
        except KeyError:
            pass
        else:
            B()
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
            args = list(args)
            args.insert(0, os.sep.join(dirs))
            
        return super().__new__(cls, *args, **kwargs)

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
            
        super().__init__(*args, **kwargs)
        self.orm.default('crossorigin', 'anonymous')
        self.orm.default('integrity', None)
        self.onbeforesave += self._entity_onbeforesave

        self.local = kwargs.get('local', False)

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
    RadixId = uuid.UUID(hex='2007d124039f4cefac2cbdf1c8d1001b')
    FloatersId = uuid.UUID(hex='f1047325d07c467f9abef26bbd9ffd27')

    def __contains__(self, nd):
        # XXX Write tests
        for nd1 in self:
            if nd.id == nd1.id:
                return True

            if isinstance(nd1, directory):
                if nd in nd1:
                    return True

        return False

    class net:                                                                                                                                                                                                                                                                                                              
        def __init__(self):
            self.found = list()
            self.wanting = list()

        @property
        def isfound(self):
            return bool(self.found) and not self.wanting

        @property
        def tail(self):
            try:
                return self.found[-1]
            except IndexError:
                return None

        def __repr__(self):
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
        if isinstance(key, list):
            pass
        elif isinstance(key, str):
            key = self._split(key)
        else:
            raise TypeError('Path is wrong type')

        if not recursing:
            if not net:
                net = self.net()
            if not net.found:
                net.found.append(self)

        name = key[0]

        try:
            nd = self.inodes[name]
        except IndexError as ex:
            net.wanting.extend(key)
            return None
        else:
            net.found.append(nd)
            if len(key) > 1:
                nd.find(key[1:], net, recursing=True)

        return net.tail

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

    @classproperty
    def radix(cls):
        if not hasattr(cls, '_radix'):
            cls._radix = cls(id=cls.RadixId, name='radix')
            cls._radix.save()
        return cls._radix
    
    @property
    def isradix(self):
        return self.id == self.RadixId and self.inode is None

    # XXX This should be private (_floaters)
    @classproperty
    def floaters(cls):
        if not hasattr(cls, '_floaters'):
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
