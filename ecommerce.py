# vim: set et ts=4 sw=4 fdm=marker

# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2020

""" This module contains ``orm.entity`` objects related to the tracking
of ecommerce data.

These entity objects are based on the "E-Commerce Models" chapter of "The
Data Model Resource Book Volume 2".

Examples:
    See test-ecommerce.py for examples. 

TODO:
    
    ...
"""

from datetime import datetime, date
from dbg import B
from decimal import Decimal as dec
from orm import text, timespan, datespan
import orm
import party, apriori

class agents(party.parties):                   pass
class webmasters(party.personals):             pass
class isps(party.organizationals):             pass
class visitors(party.consumers):               pass
class subscribers(party.consumers):            pass
class referrers(party.roles):                  pass
class agentroles(party.roles):                 pass
class hostingservers(agentroles):              pass
class webmasterassignments(party.role_roles):  pass
class visitorisps(party.role_roles):           pass
class hostservervisitors(party.role_roles):    pass
class contents(orm.entities):                  pass
class content_contents(orm.associations):      pass
class contenttypes(apriori.types):          pass
class contentroles(orm.entities):              pass
class contentstatustypes(apriori.types):       pass
class users(orm.entities):                     pass
class histories(orm.entities):                 pass
class preferences(orm.entities):               pass
class addresses(orm.entities):                pass
class objects(orm.entities):                pass

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
    name = str
    hash = bytes(32)

    party = party.party

    histories = histories
    preferences = preferences

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
    
class address(orm.entity):
    """ Represents a URL which itself represents a website.

    Note that this entity is based on the WEB ADDRESS entity in
    "The Data Model Resource Book Volume 2".
    """
    url = str

    users = users

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

class images(object):
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

class product_object(orm.association):
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

class content_usage(orm.association):
    """ Associates a product web ``content`` with an ``object``.

    Note that this is modeled after the OBJECT USAGE entity in "The Data
    Model Resource Book Volume 2".
    """

    span = date
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
