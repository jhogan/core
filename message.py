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
    # TODO Add CCs BCCs; change the 'destination' type to 'to' to
    # distinguish between CCs and BCCs
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
            if type.name == 'from':
                return cmm.contactmechanism

    def _getcms(self, name):
        r = party.contactmechanisms()
        for cmm in self.contactmechanism_messages:
            type1 = cmm.contactmechanism_messagetype
            if type1.name == name:
                r += cmm.contactmechanism

        return r

    def gettos(self, type):
        r = type.orm.entities()
        for cmm in self.contactmechanism_messages:
            cm = cmm.contactmechanism
            if builtins.type(cm) is not type:
                continue

            type1 = cmm.contactmechanism_messagetype
            if type1.name == 'to':
                r += cmm.contactmechanism

        return r

    @property
    def ccs(self):
        return self._getcms('cc') 

    @property
    def bccs(self):
        return self._getcms('bcc') 

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

        src   = contactmechanism_messagetype(name='from')
        dest  = contactmechanism_messagetype(name='to')

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
        ccs = party.emails()
        bccs = party.emails()
        for cmm in self.contactmechanism_messages:
            type = cmm.contactmechanism_messagetype
            cm = cmm.contactmechanism
            if type.name == 'from':
                from_ = cm
            elif type.name == 'to':
                tos += cm
            elif type.name == 'cc':
                ccs += cm
            elif type.name == 'bcc':
                bccs += cm

        hdr = textwrap.dedent(f'''
        From: {from_}
        To: {tos}
        ''')

        if ccs.count:
            hdr += f'CC: {ccs}\n'

        if bccs.count:
            hdr += f'BCC: {bccs}\n'

        hdr = hdr.strip()
            
        hdr += textwrap.dedent(f'''
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
