# vim: set et ts=4 sw=4 fdm=marker

########################################################################
# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2021
########################################################################

""" This module contains all classes related to sending and queueing
messages such as email, SMS and the like.

TODOs:
"""
from datetime import datetime, date
from func import B
from orm import text
import apriori
import orm
import party
import textwrap
import builtins
from uuid import uuid4

class messages(orm.entities):
    pass

class dispatches(orm.entities):
    pass

class contactmechanism_messages(orm.associations):
    pass

class contactmechanism_messagetypes(apriori.types):
    pass

class statuses(orm.entities):
    pass

class statustypes(apriori.types):
    pass

class dispatchtypes(apriori.types):
    pass

class message(orm.entity):
    html = text
    text = text
    postdate = datetime
    subject = str
    dispatches = dispatches

    def dispatch(self, *args, **kwargs):
        dis = dispatch(*args, **kwargs)
        self.dispatches += dis
        return dis

    @property
    def from_(self):
        for cmm in self.contactmechanism_messages:
            type = cmm.contactmechanism_messagetype
            if type.name == 'source':
                return cmm.contactmechanism

    def gettos(self, type):
        r = type.orm.entities()
        for cmm in self.contactmechanism_messages:
            cm = cmm.contactmechanism
            if builtins.type(cm) is not type:
                continue

            type1 = cmm.contactmechanism_messagetype
            if type1.name == 'destination':
                r += cmm.contactmechanism

        return r

    @staticmethod
    def email(from_, to, subject=None, html=None, text=None, postdate=None):
        if isinstance(from_, str):
            from_ = party.email(name=from_)
        elif isinstance(from_, party.email):
            pass
        else:
            raise TypeError('Invalid type for from_')

        if isinstance(to, str):
            tos = party.emails()
            for to in to.split(';'):
                tos += party.email(name=to)
        elif isinstance(to, party.email):
            tos = to.orm.collectivize()
        elif isinstance(to, party.emails):
            tos = to
        else:
            raise TypeError('Invalid type for `to`')

        msg = message(
            html      =  html,
            text      =  text,
            postdate  =  postdate,
            subject   =  subject,
        )

        src   = contactmechanism_messagetype(name='source')
        dest  = contactmechanism_messagetype(name='destination')

        cm = contactmechanism_message(
            contactmechanism              =  from_,
            contactmechanism_messagetype  =  src,
        )

        msg.contactmechanism_messages += cm

        for to in tos:
            msg.contactmechanism_messages += contactmechanism_message(
                contactmechanism              =  to,
                contactmechanism_messagetype  =  dest,
            )

        msg.save()

        return msg

    def __str__(self):
        boundry = uuid4().hex

        tos = party.emails()
        for cmm in self.contactmechanism_messages:
            type = cmm.contactmechanism_messagetype
            cm = cmm.contactmechanism
            if type.name == 'source':
                from_ = cm
            elif type.name == 'destination':
                tos += cm

        hdr = textwrap.dedent(f'''
        From: {from_}
        To: {tos}
        Subject: {self.subject}
        Date: {self.createdat or ''}
        Content-Type: multipart/alternative
        boundry="=_{boundry}"
        MIME-Version: 1.0
        ''')

        r = hdr

        txt = self.text
        if txt:
            r += textwrap.dedent(f'''
            --={boundry}
            Content-Type: text/plain; charset=UTF-8
            Content-Transfer-Encoding: quoted-printable
            {txt}
            ''')

        html = self.html
        if html:
            r += textwrap.dedent(f'''
            --={boundry}
            Content-Type: text/plain; charset=UTF-8
            Content-Transfer-Encoding: quoted-printable
            {txt}
            ''')
            r += f'{html}\n'

        return r.strip()
        B()

    def __repr__(self):
        return str(self)

class contactmechanism_messagetype(apriori.type):
    messages = contactmechanism_messages

class contactmechanism_message(orm.association):
    contactmechanism = party.contactmechanism
    message = message

class dispatch(orm.entity):
    statuses = statuses

class dispatchtype(apriori.type):
    """ Email, sms, etc.
    """
    dispatches = dispatches
    
class status(orm.entity):
    begin = datetime
    dispatches = dispatches

class statustype(apriori.type):
    """ Records the type of status. Typical values for the ``name``
    attribute include: "sending", "sent" and "viewed".
    """
    # The collection of statuses belonging to this type
    statuses = statuses
