# vim: set et ts=4 sw=4 fdm=marker

########################################################################
# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2021
########################################################################

""" This module contains all classes related to sending and queueing
messages such as email, SMS, chat, etc.

The main entity in the class is ``message``. A ``message`` represents
any type of message such an an email, snail mail, a text message.
``message`` entities and can be associated with zero or more contact
mechanisms (``party.contactmechanism``). Usually a ``message`` will be
associated with a *from* address and at least one *to* address.

A ``message`` can have zero or more ``dispatch`` objects. A ``dispatch``
object schedules a ``message`` to be sent to an external resource, such
as a third party email or SMS provider. Multiple ``dispatch`` objects
can be used to send the same ``message`` to multiple places, such as in
the case when the collection of destinations contact mechanisms includes
email addresses and SMS addresses, thus requiring two seperate third
party provier interactions to deliver the ``message``. Additional
``dispatch`` objects can be created for hard-bounce situations such as
when there is an unresloved problem with the first ``dispatch`` thus
necessitating the creation of an additional ``dispatch`` for the same
message. A ``message`` may not need a ``dispatch`` entity such as when a
it is intended for an internal contact mechanism such as for use in an
internal messaging or chat system.

A ``dispatch`` can have zero or more ``status`` entities. These keep track
of when the ``dispatch`` enters into different states such as 'queued', 'in
progress' or 'completed'.

``sendbot`` in the bot.py module will monitor the database for 'queued'
``dispatches``. It will process the ``dispatch`` by using logic in the
third.py module ("third" as in third-party) to send the ``message`` to a
third party provider.

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
    """ A collection of ``message`` objects.
    """

class dispatches(orm.entities):
    """ A collection of ``dispatch`` objects.
    """

class contactmechanism_messages(orm.associations):
    """ A collection of contact mechanism to message associations.
    """

class contactmechanism_messagetypes(apriori.types):
    """ A collection of contact-mechanism-to-message types.
    """

class statuses(orm.entities):
    """ A collection of ``dispatch`` status entites.
    """

    def __init__(self, *args, **kwargs):
        """ Creates a statuses collection.
        """

        super().__init__(*args, **kwargs)
        try:
            # Manages the initing boolean to prevent the collection from
            # loading automatically.
            self.orm.initing = True

            # Subscribe the self._self_onadd handler to the self.onadd
            # event so we can capture the ``status`` objects as they are
            # added to the collection.
            self.onadd += self._self_onadd 
        finally:
            self.orm.initing = False

    def _self_onadd(self, src, eargs):
        """ An event handler to capture ``status`` objects when they are
        added to the collection.

        This handler updates the dispatch object with the name of the
        last status object that was added. Storing the name of the
        last status object in the dispatch entity makes it easy to query
        the dispatches table for incomplete dispatches. 
        """

        # TODO:9b4b0ce0 This handler is a hack to work around the fact
        # that the ORM doesn't yet support correlated subqueries. The
        # question we want to ask the database when quering for
        # incomplete dispatches is: select all dispatches that don't
        # have a status record of complete. We should be able to express
        # that like this:
        #
        #     diss = dispatches("'completed' not in statuses.name'")
        #
        # Resulting in a query like this:
        #
        #     SELECT *
        #     FROM dispatches AS dis
        #     WHERE 'completed' NOT IN (
        #                          SELECT name
        #                          FROM statuses AS st
        #                          WHERE dis.id = st.dispatchid
        #                      )

        # When loading status objects from the database, this handler
        # will be called. When loading, we don't want to do anything
        # here.
        if not self.orm.isloading:

            # Ensure the 'dispatch.status' property always has the name
            # of the last status entity to be added .
            st = eargs.entity
            st.dispatch.status = st.statustype.name
        
class statustypes(apriori.types):
    """ A collection of ``statustype`` objects.
    """

class dispatchtypes(apriori.types):
    """ A collection of ``dispatchtype`` objects.
    """

class message(orm.entity):
    """ Represents a message. ``messages`` can dispatched to email
    accounts, SMS numbers, text messaging systems, postal addresses,
    telegraph receivers, etc.

    ``messages`` have a many-to-many relationship with contact
    mechanisms (see party.contactmechanisms for more about contact
    mechanisms) via the ``contactmechanism_message`` associaton. This
    allow a message to be address to multiple recipients where each of
    the recipients could potentially use different contact mechanisms.
    For example, a message my be addressed to an email account, an SMS
    number, and a postal address at the same time (currently, only email
    is implemented).

    A message can have an HTML representation and a text representation
    simultaneously. This is useful for multipart emails which need to
    have both an HTML part, and a text part which text-based email
    clients can fall back on. 

    A message can have zero or more ``dispatches``. These entities are
    used to schedule the delivery of the message to external systems
    such as an SMTP server or third-party RESTful APIs. (``sendbot`` is
    responsible for processing these messages.) For internal messages,
    such as a user's personal inbox, a ``dispatch`` wouldn't be
    necessary.
    """

    # The HTML representation of the message.
    html = text

    # A text representation of the message
    text = text

    # Indicates that messages should be delivered at a future time
    # (currently not implemented).
    postdate = datetime

    # The subject line of the message. For emails, this would obviously
    # be the subject of the email.
    subject = str

    # A collection of dispatch objects.
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
