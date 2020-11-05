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
    ...

class visitor(party.consumer):
    """ The role a party plays when visiting a site.
    """

class referrer(party.role):
    """ The source from which a party was referred to the web site.
    """

class agentrole(party.role):
    """
    Note that this is modeled after the AUTOMATED AGENT ROLE entity in
    "The Data Model Resource Book Volume 2".
    """

class hostingservice(agentrole):
    """ The web server that hosts web pages.
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
