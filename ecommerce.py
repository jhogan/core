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
