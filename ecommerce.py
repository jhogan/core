# vim: set et ts=4 sw=4 fdm=marker

# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2021

""" This module contains ``orm.entity`` objects related to the tracking
of ecommerce data.

The object models within this module are focused on the unique data
model constructs needed to maintain e-commerce specific information.
Perhaps the most important are those that capture the information
requirements about the ``visitor``, ``content``, ``user``,
``subscription``, ``visit``, and server ``hit`` entities.

These entity objects are based on the "E-Commerce Models" chapter of "The
Data Model Resource Book Volume 2".

Examples:
    See testecommerce.py for examples. 

TODO:
    
    TODO Enfore the rule that user.name's must be unique
"""

from datetime import datetime, date
from dbg import B
from decimal import Decimal as dec
from entities import classproperty
from orm import text, timespan, datespan
import apriori
import entities
import file
import hashlib
import ipaddress
import order
import orm
import os
import party
import primative
import product
import urllib
import user_agents
import urllib.parse
import uuid

class agents(party.parties):                                  pass
class webmasters(party.personals):                            pass
class isps(party.organizationals):                            pass
class visitors(party.consumers):                              pass
class subscribers(party.consumers):                           pass
class referrers(party.roles):                                 pass
class agentroles(party.roles):                                pass
class hostingservers(agentroles):                             pass
class webmasterassignments(party.role_roles):                 pass
class visitorisps(party.role_roles):                          pass
class hostservervisitors(party.role_roles):                   pass
class contents(orm.entities):                                 pass
class content_contents(orm.associations):                     pass
class contenttypes(apriori.types):                            pass
class contentroles(orm.entities):                             pass
class contentstatustypes(apriori.types):                      pass
class users(orm.entities):
    RootUserId = uuid.UUID('93a7930b-2ae4-402a-8c77-011f0ffca9ce')

    @classproperty
    def root(cls):
        if not hasattr(cls, '_root') or not cls._root:
            from pom import site
            for map in users.orm.mappings.foreignkeymappings:
                if map.entity is site:
                    break
            else:
                raise ValueError(
                    'Could not find site foreign key'
                )
                
            usrs = users(
                f'name = %s and {map.name} is %s', 'root', None
            )

            if usrs.isplurality:
                raise ValueError('Multiple roots found')

            if usrs.issingular:
                cls._root = usrs.first
            else:
                cls._root = user(id=cls.RootUserId, name='root')

                with orm.override():
                    cls._root.save()

        return cls._root
        
class histories(orm.entities):                                pass
class preferences(orm.entities):                              pass
class urls(orm.entities):                                     pass
class objects(orm.entities):                                  pass
class texts(objects):                                         pass
class images(objects):                                        pass
class others(objects):                                        pass
class object_products(orm.associations):                      pass
class feature_objects(orm.associations):                      pass
class party_objects(orm.associations):                        pass
class content_objects(orm.associations):                      pass
class purposetypes(apriori.types):                            pass
class object_purposes(orm.associations):                      pass
class objecttypes(apriori.types):                             pass
class subscriptions(orm.entities):                            pass
class subscriptiontypes(apriori.types):                       pass
class subscriptionactivities(orm.entities):                   pass
class subscription_subscriptionactivities(orm.associations):  pass

class visits(orm.entities):
    @property
    def current(self):
        """ Return the first ``visit`` in this collection that is
        current. If none of the ``visits`` are current, return None.
        """
        for vis in self:
            if vis.iscurrent:
                break
        else:
            return None

        return vis

class hits(orm.entities):                                     pass
class hitstatustypes(apriori.types):                          pass
class electronicaddresses(party.contactmechanisms):           pass
class ips(electronicaddresses):                               pass
class useragents(orm.entities):                               pass
class useragenttypes(apriori.types):                          pass
class platformtypes(apriori.types):                           pass
class devicetypes(apriori.types):                             pass
class browsertypes(apriori.types):                            pass
class protocols(apriori.types):                               pass
class methods(apriori.types):                                 pass

class logs(orm.entities):
    def write(self, msg):
        self += log(
            datetime = primative.datetime.utcnow(),
            message = msg,
        )

class agent(party.party):
    """ Tracks the activities of automated entities such as spiders, web
    servers, and other automations that are involved in interactin on
    the Internet.

    Note that this is modeled after the AUTOMATED AGENT entity in "The
    Data Model Resource Book Volume 2".
    """

class webmaster(party.personal):
    ...
    
class isp(party.organizational):
    """ The role of internet service provider.

    An ISP (internet service provider) can be important to track, as
    you may be able to track visitors back to their ISPs. This
    information can be very useful to targeting marketing and
    advertising campaigns at certain ISPs of consequence (where most of
    you visitors may come from).
    """

class visitor(party.consumer):
    """ The role a party plays when visiting a site. A visitor can also
    be a customer``, ``propspect``, or some other subtype of
    ``party.consumer``.
    """
    visits = visits

class subscriber(party.consumer):
    """ A ``subscriber`` may be a ``party`` who has subscribed to a
    newsletter, service, or other ongoing request. This is especially
    useful if the subscription is for a newsletter that the visitor
    registered for based on his or her interests. This allows the
    enterprise to target an interested customer base with information
    and specials tailored to the visitor's interests.
    """

class referrer(party.role):
    """ The source from which a party was referred to the web site.

    A referrer is important to track, as this will tell you from which
    site parties are coming. If the enterprise dose Internet marketing
    campaigns, it can track the effectiveness of these campaigns by
    tracking what search engines visitors have come from or from what
    banner ad on what site did the visitor click.
    """

class agentrole(party.role):
    """
    Note that this is modeled after the AUTOMATED AGENT ROLE entity in
    "The Data Model Resource Book Volume 2".
    """

class hostingserver(agentrole):
    """ The web server that hosts web pages.

    Hosting servers can be used to keep track of what things are on what
    server, which can be handy if there is a need to have different
    servers for different parts of the enterprise.
    """

class webmasterassignment(party.role_role):
    """ Defines who is managing the website.
    """
    
class visitorisp(party.role_role):
    """ The ISP of the party that is visiting a site.
    """

class hostservervisitor(party.role_role):
    """ The relationship betwenn the visitor and the server that is
    hosting the site.
    """

class content(orm.entity):
    """ Represents pieces of information that are on the internet.

    Note that this entity is based on the WEB CONTENT entity in "The
    Data Model Resource Book Volume 2".
    """
    # Summarizes what is stored.
    description = text

    # Stores the path name for the actual file that stores the web
    # content.
    path = str

    contentroles = contentroles

    hits = hits

class content_content(orm.association):
    """ Associates one web ``content`` with another.
    Web ``content`` is often related to other web ``content``. For
    instance, a textual web-based product description ``content`` may be
    related to severeral ``content`` images, which are used within the
    product description.

    Note that this entity is based on the WEB CONTENT entity in "The
    Data Model Resource Book Volume 2".
    """

    subject = content
    object  = content

class contenttype(apriori.type):
    """ Categorizes the types of web ``contents`` that exist such as
    "articles", "product descriptions", "company information", and so
    on.

    Note that this entity is based on the WEB CONTENT TYPE entity
    in "The Data Model Resource Book Volume 2".
    """
    contents = contents

class contentrole(orm.entity):
    """ Web ``content`` entities may have many web ``contentroles`` of a
    web ``contentroletype``. For instance, the party that createh the
    web ``content`` would be the "author", the party that was
    responsible for putting the content on the web is usually the
    "webmaster" and the party that updates the content may be state as
    "updater".

    Note that this entity is based on the WEB CONTENT ROLE entity in
    "The Data Model Resource Book Volume 2".
    """

    span = datespan

class contentstatustype(apriori.type):
    """ Indicates whether the content is currently on the site, pending,
    or was peviously stored on a site.

    Note that this entity is based on the WEB CONTENT STATUS TYPE entity
    in "The Data Model Resource Book Volume 2".
    """
    contents = contents

class user(orm.entity):
    """ Represents the login account a ``party.party`` uses to log in to
    a website.

    Note that this entity is based on the USER LOGIN entity
    in "The Data Model Resource Book Volume 2".
    """

    def __init__(self, *args, **kwargs):
        self._password = None
        super().__init__(*args, **kwargs)

    name = str

    # TODO Hash is declared twice, once here, as a declarative
    # attribute, and below an imperative attribute. We we'll want to
    # remove the former and keep the later.
    hash = bytes(32)

    party = party.party

    histories = histories
    preferences = preferences
    hits = hits

    @orm.attr(file.directory)
    def directory(self):
        dir = attr()
        if dir is None:
            dir = file.directory(f'/ecommerce/user/{self.id.hex}')
            attr(dir)
        return dir
    
    @orm.attr(bytes, 16, 16)
    def salt(self):
        self._sethash()
        return attr()

    @orm.attr(bytes, 32, 32)
    def hash(self):
        self._sethash()
        return attr()

    def _sethash(self):
        hash = self.orm.mappings['hash']
        salt = self.orm.mappings['salt']

        if hash.value and salt.value:
            return

        hash.value, salt.value = self._gethash()

    def _gethash(self, pwd=None):
        if not pwd:
            pwd = self.password

        if not pwd:
            return None, None

        salt = self.orm.mappings['salt'].value

        if not salt:
            salt = os.urandom(16)

        pwd  = bytes(pwd, 'utf-8')
        algo = 'sha256'
        iter = 100000
        fn   = hashlib.pbkdf2_hmac

        hash = fn(algo, pwd, salt, iter)
        return hash, salt

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, v):
        self.hash = self.salt = None
        self._password = v

    def ispassword(self, pwd):
        # Ensure self._salt is set so _gethash doesn't make one up
        self._sethash()
        hash, _ = self._gethash(pwd)
        return hash == self.hash

    @property
    def isroot(self):
        # TODO:887c6605 Change this to:
        #
        #    return self.id = '93a7930b-2ae4-402a-8c77-011f0ffca9ce'.
        #
        # I think we can get rid of the self.site test.
        return self.name == 'root' and self.site is None

    @property
    def brokenrules(self):
        brs = entities.brokenrules()

        # Get site foreignkey name
        from pom import site
        for map in users.orm.mappings.foreignkeymappings:
            if map.entity is site:
                break
        else:
            raise ValueError(
                'Could not find site foreign key'
            )

        if self.orm.isnew and self.isroot:
            usrs = users(
                f'name = %s and {map.name} is %s', 'root', None
            )
            if usrs.count:
                brs += entities.brokenrule(
                    'Root already exists', 'name', 'valid', self
                )

        return brs

    def su(self):
        """ A context manager to switch current user to self.

            The following do the same::

                with orm.su(luser):
                    ...

                with luser.su():
                    ...
        """
        return orm.su(self)
        
    @property
    def retrievability(self):
        vs = orm.violations()
        sec = orm.security()
        usr = sec.user
        msgs = list()

        if usr:
            if usr.id != self.id:
                msgs.append(
                    'Current user is not the user being retrieved'
                )
        else:
            msgs.append(
                'Current user must be authenticated'
            )

        if vs.isempty:
            vs += msgs

        return vs

class history(orm.entity):
    """ Used to store a history of the logins and passwords.

    Note that this entity is based on the LOGIN ACCOUNT HISTORY entity
    in "The Data Model Resource Book Volume 2".
    """
    span = timespan
    name = str
    hash = bytes(32)
    
class preference(orm.entity):
    """ ``user`` logins have zero or more user ``preferences`` of
    ``proferencetype`` in order to provide customized services for each
    user login.

    Note that this entity is based on the WEB USER PREFERENCE entity in
    "The Data Model Resource Book Volume 2".
    """
    key = str
    value = str
    
class url(orm.entity):
    """ Represents a URL. Note that url addresses are
    ensured to exist, i.e., they are automatically saved in the
    database if they don't already exist.

        url = url(address='www.google.com')
        assert not url.orm.isnew

        url1 = url(address='www.google.com')

        assert url.id == url1.id
        assert 'www.google.com' == url.address
        assert 'www.google.com' == url1.address

    Note that this entity is based on the WEB ADDRESS entity in
    "The Data Model Resource Book Volume 2".
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Ensure address exists in database. URL paths are
        # case-sensitive, so set issensitive to True.
        self.orm.ensure(
            expects=('address', ), issensitive=True, **kwargs
        )

    # TODO Change address to name.
    address = str

    # TODO Why do urls have users?
    users = users

    # The web `hits` where this ``url`` acts as an http_referer
    hits = hits

    resources = file.resources

    def __str__(self):
        return self.address

    def __truediv__(self, other):
        """ Overrides the / operator to allow for path joining

            wiki = url(name='https://www.wikipedia.org/') 
            py = wiki / 'wiki/Python'

            assert py.name == 'https://www.wikipedia.org/wiki/Python'
        """
        addr = self.address
        addr = os.path.join(addr, other)

        # TODO Why is ecommerce being imported here? Can we remove it.
        import ecommerce
        return ecommerce.url(address=addr)

    @property
    def scheme(self):
        """ Returns the scheme (sometimes refered to as the protocol)
        portion of the URL. 

        Given the URL "scheme://netloc/path;parameters?query#fragment",
        "scheme" would be returned.
        """
        return urllib.parse.urlparse(self.address).scheme

    @property
    def host(self):
        """ Returns the hostname portion of the URL. 

        Given the URL "scheme://netloc/path;parameters?query#fragment",
        "netloc" would be returned.
        """
        return urllib.parse.urlsplit(self.address).hostname

    @property
    def port(self):
        """ Returns the port portion of the URL as an int.

        Given the URL "scheme://netloc:1234/path;parameters?query#fragment",
        1234 would be returned.
        """
        return urllib.parse.urlparse(self.address).port

    @property
    def paths(self):
        """ Returns a list of path elements in the URL.

        Given the URL:
        
             scheme://netloc:1234/path/to/resource?query#fragment
        
        The return would be:
       
            ['path', 'to', 'resource']
        """

        return [x for x in self.path.split(os.sep) if x]

    @property
    def path(self):
        """ Returns the path portion of the URL.

        Given the URL:
            scheme://netloc:1234/path/to/resource;parameters?query#fragment

        returns: '/path/to/resource;parameters'
        """
        return urllib.parse.urlparse(self.address).path

    @property
    def creatability(self):
        # NOTE:7a67115c I suppose anyone should be able to access a URL
        # in most cases. However, associations between ``urls`` and
        # other entity objects would work differently. But those
        # accessibilty restrictions  would be enforced in the
        # association objects.  For now, permit readability to all
        # (within the current tenant (orm.proprietor) of course).
        return orm.violations.empty

    @property
    def retrievability(self):
        # NOTE:7a67115c
        return orm.violations.empty

class object(orm.entity):
    """ Stores electronic images, such as ``text`` (i.e. an HTML
    document), ``image`` (graphical electronic represenation),
    and ``other``, such as appletes, sound file, video clips, and
    so on.
    """
    name = str
    path = str

class text(object):
    """ An electronic, textual image.

    Note that this is modeled after the ELECTRONIC TEXT entity in "The
    Data Model Resource Book Volume 2".
    """
    text = str

class image(object):
    """ An electronic, textual image.

    Note that this is modeled after the IMAGE OBJECT entity in "The Data
    Model Resource Book Volume 2".
    """
    body = bytes

class other(object):
    """ Miscallanious object types such as applets, sound files video
    clips and so on.

    Note that this is modeled after the OTHER OBJECT entity in "The
    Data Model Resource Book Volume 2".
    """
    body = bytes

class object_product(orm.association):
    """ Associates a ``product`` with an ``object``.

    Note that this is modeled after the PRODUCT OBJECT entity in "The
    Data Model Resource Book Volume 2".
    """

    product = product.product
    object = object
    
class feature_object(orm.association):
    """ Associates a product ``feature`` with an ``object``.

    Note that this is modeled after the FEATURE OBJECT entity in "The
    Data Model Resource Book Volume 2".
    """

    feature = product.feature
    object = object

class party_object(orm.association):
    """ Associates a product ``product`` with an ``object``.

    Note that this is modeled after the PARTY OBJECT entity in "The
    Data Model Resource Book Volume 2".
    """

    party = party.party
    object = object

class content_object(orm.association):
    """ Associates a product web ``content`` with an ``object``.

    Note that this is modeled after the OBJECT USAGE entity in "The Data
    Model Resource Book Volume 2".
    """

    span = datespan
    content = content
    object = object

class purposetype(apriori.type):
    """ The purpose of an ``object``.

    Note that this is modeled after the PURPOSE TYPE entity in "The Data
    Model Resource Book Volume 2".
    """

class object_purpose(orm.association):
    """ Associates an ``object`` with a ``purposetype``.

    Note that this is modeled after the OBJECT PURPOSE entity in "The
    Data Model Resource Book Volume 2".
    """

    purposetype = purposetype
    object = object

class objecttype(apriori.type):
    """ Each object may be of a particular type, such a "HTML document",
    "JPEG image", "GIF", "streaming video", "sound clip", 'JAVA applet",
    and so on.

    Note that this is modeled after the OBJECT PURPOSE entity in "The
    Data Model Resource Book Volume 2".
    """
    objects = objects

class subscription(orm.entity):
    """ A subscription that a subscriber (``subscriber``) has
    concerning a product (``product.product``), ``product.category``, or
    certain party.needs.

    Subscriptions may be subtyped to ``newsgroup``,
    ``productinformation``, ``usergroup``, or ``othersubscirption``
    which would account for additional types as maintained in the
    ``subscriptiontype`` entity.
    """

    span = datetime
    needs = party.needs
    communication = party.communication
    contactmechanism = party.contactmechanism
    subscriber = subscriber
    needtype = party.needtype
    category = product.category
    product = product.product
    items = order.items

class subscriptiontype(apriori.type):
    """
    Note that this is modeled after the SUBSCRIBER TYPE entity in "The
    Data Model Resource Book Volume 2".
    """
    subscriptions = subscriptions

class subscriptionactivity(orm.entity):
    sent = datetime
    comment = text

class subscription_subscriptionactivity(orm.association):
    """ Tracks the sending of ongonig information.  Note that this is
    modeled after the SUBSCRIPTION FULFILLMENT PIECE entity in "The Data
    Model Resource Book Volume 2".
    """

class visit(orm.entity):
    """ A ``visit`` is a session on a web site that consists of
    a collection of server ``hits`` that ar related via the information
    and rules surrounding a ``visit``. 

    A visit may result in one or more orders.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.orm.default('cookie', None)

    # TODO What defines the `end` of the span. Perhaps when the `visit`
    # is no longer current (`iscurrent`), the last `hit` the `visit` was
    # involved in will have the `end` datetime that should be the
    # `visit`'s `end.

    # The span of time in which the visit takes place.
    span = timespan

    # A string that helps identify the machine that was used for the
    # connection.
    cookie = str

    hits = hits

    @property
    def iscurrent(self):
        """ Returns True if the ``visit`` is current, False otherwise.

        A ``visit`` is current if it has not ended (``end` datetime is
        None), and it hasn't been inactive for more than 30 minutes (30
        minutes have not elapsed between the start of the visit
        (``begin``) and the current time).
        """
        # The number of seconds that can elapse between the start of the
        # visit and the current time for the `visit` to be considered
        # "current".
        Seconds = 1800  # 30 minute

        if self.end is not None:
            return False

        now = primative.datetime.utcnow()
        begin = self.begin

        delta = now - begin
        return delta.seconds < Seconds

class log(orm.entity):
    """ A log entry a user can add to the hit entity.

        class mypage(pom.page):
            def main(self):
                hit.logs += log(message='Started mypage')

                ..

                hit.logs += log(message='Ending mypage')

    """

    # The time the log written
    datetime = datetime

    # The log message
    message = str

class hit(orm.entity):
    """ Records details about a web hit such a the path of the page
    being accessed, the HTTP method being used (GET, POST, etc.), the
    HTTP status number, and other data related to the HTTP request and
    response.

    Note that this is modeled after the SERVER HIT entity in "The Data
    Model Resource Book Volume 2".
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.orm.default('qs', None)

    # NOTE The implicit attribute `url` is the referrer (http_referer)
    # of the web request.

    # The timespan of the request
    span = timespan

    # The query string
    qs = str

    # The path to the page being requested
    path = str

    # The request method (GET, POST, DELETE, etc)
    method = str

    # Whether or not the hit was a traditional HTTP request or an
    # XHR/AJAX request.
    isxhr = bool

    # The language the page is being requested in, i.e., the 'en' in
    # 'www.mysite.com/en/path/to/page.html'
    language = str

    # The size, in bytes, of the response. 
    size = int

    # The HTTP status code
    status = int

    # The logs the web developer may write for the hit.
    logs = logs

    # Was a valid JWT sent
    isjwtvalid = bool

    @property
    def inprogress(self):
        """ Return True if the web ``hit`` has started but has not yet
        finished.
        """
        return self.begin and not self.end

class hitstatustype(apriori.type):
    """ Records status information about the ``hit`` - for example if a
    requested file if a server ``hit`` was sucessfully retrieved or if
    the file was not found.

    Note that this is modeled after the SERVER HIT STATUS TYPE entity in
    "The Data Model Resource Book Volume 2".
    """

    hits = hits

class electronicaddress(party.contactmechanism):
    pass

class ip(electronicaddress):
    """ Records the address of a web client. Note that ip addresses are
    ensured to exist, i.e., they are automatically saved in the
    database if they don't already exist::

        ip = ip(address='127.0.0.2')
        assert not ip.orm.isnew

        ip1 = ip(address='127.0.0.2')

        assert ip.id == ip1.id
        assert 127.0.0.2 == ip.address
        assert 127.0.0.2 == ip1.address

    Note that this is modeled after the IP ADDRESS entity in "The Data
    Model Resource Book Volume 2".
    """

    address = str

    hits = hits

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.orm.ensure(expects=('address', ), **kwargs)

    def __str__(self):
        return self.address

class useragent(orm.entity):
    """ Describes the mechanism, such as protocol, platform, browser,
    and operating system, that is used in a server ``hit``.

    Note that this is modeled after the USER AGENT entity in "The Data
    Model Resource Book Volume 2".
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @orm.attr(str)
    def string(self, v):
        if not v:
            raise ValueError(
                'Empty useragent string'
            )

        attr(v)
        ua = self._useragent

        brw = ua.browser
        self.browsertype = browsertype(
            name    = brw.family,
            version = brw.version,
        )

        dev = ua.device
        self.devicetype = devicetype(
            name  = dev.family,
            brand = dev.brand,
            model = dev.model,
        )

        os = ua.os
        self.platformtype = platformtype(
            name  = os.family,
            version = os.version_string,
        )

    @property
    def _useragent(self):
        return user_agents.parse(self.string)

    @property
    def ismobile(self):
        return self.is_mobile

    @property
    def istablet(self):
        return self.is_tablet

    @property
    def istouch(self):
        return self.is_touch_capable

    @property
    def ispc(self):
        return self.is_pc

    @property
    def isbot(self):
        return self.is_bot

    def __getattr__(self, attr):
        if not self._useragent:
            raise ValueError(
                'No user_agent object has been set'
            )

        return getattr(self._useragent, attr)
        
    hits = hits

    def __str__(self):
        return self.string

class useragenttype(apriori.type):
    """
    Note that this is modeled after the USER AGENT TYPE entity in "The
    Data Model Resource Book Volume 2".
    """
    useragents = useragents

class platformtype(apriori.type):
    """ Defines the version of what operating system the ``useragent``
    is running on such as "Windows 98", "Windows 2000" or "Unix".

    Note that this is modeled after the PLATFORM TYPE entity in "The
    Data Model Resource Book Volume 2".
    """
    version = str

    useragents = useragents

class devicetype(apriori.type):
    """ Defines the type of device of a ``useragent``.
    """
    useragents = useragents
    brand = str
    model = str

    def __init__(self, *args, **kwargs):
        super().__init__(
            expects = ('name', 'brand', 'model'), *args, **kwargs
        )

class browsertype(apriori.type):
    """ The ``browsertype`` reveals the name and version of the browser
    (i.e., Netscape, Internet Explorer, Infobot, etc.). 

    Note that this is modeled after the BROWSER TYPE entity in "The
    Data Model Resource Book Volume 2".
    """
    def __init__(self, *args, **kwargs):
        try:
            ver = kwargs['version']
        except KeyError:
            pass
        else:
            kwargs['version'] = self._normalize(ver)
            
        super().__init__(expects=('name', 'version'), *args, **kwargs)

    @staticmethod
    def _normalize(ver):
        """ Convert the version into a standard string format, e.g.,
        '1.2.3'. (ua-parser will give us a tuple though a str would
        be preferable).
        """
        if isinstance(ver, tuple):
            ver = '.'.join(str(x) for x in ver)

        return ver

    version = str

    useragents = useragents

class protocol(apriori.type):
    """ The protocol used in a server ``hit``. Examples would include
    HTTP, HTTPS, FTP.

    Note that this is modeled after the PROTOCOL TYPE entity in "The
    Data Model Resource Book Volume 2".
    """

    # NOTE This probably won't be used because we will probably always
    # use HTTPS. If not, we will just use the strings "HTTPS", "HTTP",
    # etc.
    useragents = useragents

class method(apriori.type):
    """ The HTTP method used in the server hit. Example include GET,
    POST and DELETE.

    Note that this is modeled after the USER AGENT METHOD TYPE entity in
    "The Data Model Resource Book Volume 2".
    """

    # NOTE This probably won't be used because its easier to just use
    # the strings "GET", "POST", etc.

    useragents = useragents
