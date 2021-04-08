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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self.orm.initing = True
            self.onadd += self._self_onadd 
        finally:
            self.orm.initing = False

    def _self_onadd(self, src, eargs):
        if not self.orm.isloading:
            st = eargs.entity
            st.dispatch.status = st.statustype.name
        
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
    def replyto(self):
        replytos = self.getcontactmechanisms(
            type=party.email,
            name='replyto'
        )
        return replytos(0)

    @property
    def from_(self):
        for cmm in self.contactmechanism_messages:
            type = cmm.contactmechanism_messagetype
            if type.name == 'from':
                return cmm.contactmechanism

    def getcontactmechanisms(self, type, name):
        r = type.orm.entities()
        for cmm in self.contactmechanism_messages:
            cm = cmm.contactmechanism
            if builtins.type(cm) is not type:
                continue

            type1 = cmm.contactmechanism_messagetype
            if type1.name == name:
                r += cmm.contactmechanism

        return r

    @property
    def cc(self):
        return self._getcms('cc') 

    @property
    def bcc(self):
        return self._getcms('bcc') 

    @staticmethod
    def email(
        from_,         to,            cc=None,    bcc=None,
        replyto=None,  subject=None,  html=None,  text=None,
        postdate=None
    ):
        msg = message(
            html      =  html,
            text      =  text,
            postdate  =  postdate,
            subject   =  subject,
        )

        for k in ('from_', 'to', 'cc', 'bcc', 'replyto'):
            v = locals()[k]
            if isinstance(v, str):
                ems = party.emails()
                for name in v.split(','):
                    ems += party.email(name=name)
            elif isinstance(v, party.email):
                ems = v.orm.collectivize()
            elif isinstance(v, party.emails):
                ems = v
            elif v is None:
                continue
            else:
                raise TypeError(f'Invalid type for {k}')

            type = contactmechanism_messagetype(name=k.rstrip('_'))

            for em in ems:
                msg.contactmechanism_messages += contactmechanism_message(
                    contactmechanism              =  em,
                    contactmechanism_messagetype  =  type,
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
    # The external message id. When a message is dispatched to an
    # a third party for delivery, the third party may or may not have
    # its own identifier for the message.
    externalid = str
    statuses = statuses
    status = str

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.orm.default('externalid', None)
        self.orm.default('status', 'queued')

class dispatchtype(apriori.type):
    """ Email, sms, etc.
    """
    dispatches = dispatches
    
class status(orm.entity):
    """ A status entry for a dispatch. The description for the status is
    found in the implicit `status.statustype.name` property.
    """

    # The datetime the event described by the status entity occured.
    begin = datetime

class statustype(apriori.type):
    """ Records the type of status.
    
    Values for the ``name`` attribute:
        
        * 'postmarked': The message has been dispatched to a third party
        provider.

        * 'hard-bounce': The dispatch failed and any attempt to
        dispatch the message again will fail.

        * 'soft-bounce': The dispatch failed, and another dispatch
        * entity should be created so the message can be attempted again
        * at a later date.

        * 'viewed' The user has opened the email.
    """
    # The collection of statuses belonging to this type
    statuses = statuses
