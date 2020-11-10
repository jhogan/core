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
import party

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

class contenttype(apriori.status):
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

class contentstatustype(apriori.status):
    """ Indicates whether the content is currently on the site, pending,
    or was peviously stored on a site.

    Note that this entity is based on the WEB CONTENT STATUS TYPE entity
    in "The Data Model Resource Book Volume 2".
    """
    contents = contents
