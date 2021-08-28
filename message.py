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
import uuid

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
    # (currently not implemented). TODO:1fb03626 Implement
    postdate = datetime

    # The subject line of the message. For emails, this would obviously
    # be the subject of the email.
    subject = str

    # A collection of dispatch objects.
    dispatches = dispatches

    def dispatch(self, *args, **kwargs):
        """ Creates a new dispatch entity, appends it to the
        ``message``'s ``dispatches collection, and returns the dispatch
        instance..
        """
        dis = dispatch(*args, **kwargs)
        self.dispatches += dis
        return dis

    @property
    def replyto(self):
        """ Searches the contact mechanisms (party.contactmechanisms)
        associated with this message for the 'replyto' email and returns
        it. If one is not found, None is returned.
        """
        replytos = self.getcontactmechanisms(
            type=party.email,
            name='replyto'
        )
        return replytos(0)

    @property
    def from_(self):
        """ Searches the contact mechanisms (party.contactmechanisms)
        associated with this message for the 'from' contact mechanism
        and returns it. If one is not found, None is returned.
        """
        for cmm in self.contactmechanism_messages:
            type = cmm.contactmechanism_messagetype
            if type.name == 'from':
                return cmm.contactmechanism

    def getcontactmechanisms(self, type, name):
        """ Searches the collection of contact mechanisms
        (party.contactmechanisms) associated with this message and
        return the one that matches the ``name`` and is of the type
        ``type``.

        :param: type type: A subclass of ``party.contactmechanim`` to
        scan for.

        :param: name str: The name of the contact mechanism as it is
        associated with the message (e.g., 'replyto', 'from', 'to',
        'cc', 'bcc', etc.)
        """
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
        # TODO Remove I don't think this is used any more
        return self._getcms('cc') 

    @property
    def bcc(self):
        # TODO Remove I don't think this is used any more
        return self._getcms('bcc') 

    @staticmethod
    def email(
        from_,         to,            cc=None,    bcc=None,
        replyto=None,  subject=None,  html=None,  text=None,
        postdate=None
    ):
        """ A static method that makes creating an email easy. The
        method is permissive about the inputs it accepts, for example,
        the email address parameters, such as ``to``, can be of type
        party.email, party.email, an email address in string format or a
        comma-seperated string of emails. Note that currently, the
        method does not generate a ``dispatch`` object.

        :param: from_ str|party.email|party.emails: The From email
        address.

        :param: to str|party.email|party.emails: The To email
        address.

        :param: cc str|party.email|party.emails: The cc email
        address.

        :param: bcc str|party.email|party.emails: The bcc email
        address.

        :param: replyto str|party.email|party.emails: The replyto email
        address.

        :param: subject str: The subject of the email.

        :param: html str: The HTML body.

        :param: text str: The text body (used as a fallback for email
        clients that can't render HTML

        :param: postdate datetime: The date when the messages should be
        dispatched (currently not implemented: 1fb03626)
        """

        # TODO Shouldn't we be creating a dispatch object in this
        # method. If not, explain why in docstring.

        # Create the message object
        msg = message(
            html      =  html,
            text      =  text,
            postdate  =  postdate,
            subject   =  subject,
        )

        # Create/retrieve the party.email instance for each of the
        # email addresses passed in and associate the party.emails with
        # the message through the contactmechanism_message association.

        # TODO We should support any iterable here such as lists and
        # tuples. dicts could also be supported::
        #     {'Jesse Hogan': 'jhogan@mail.com'}

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

            # Associate message with party.contactmechanism. Name the
            # association ``k``
            type = contactmechanism_messagetype(name=k.rstrip('_'))
            for em in ems:
                msg.contactmechanism_messages += contactmechanism_message(
                    contactmechanism              =  em,
                    contactmechanism_messagetype  =  type,
                )

        # Save message object to database along with
        # contactmechanisms and their associations.
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

    @property
    def creatability(self):
        """ Anyone should be able to create a message.
        """
        return orm.violations.empty
        
    @property
    def retrievability(self):
        # NOTE Obviously, the message's recepients should be able to
        # retrieve their message. However, at the moment we will focus
        # on allowing owner of the message to retrieve messages. We will
        # also allow sendbot accesses to the messages for dispatching.
        usr = orm.security().user

        if usr.id == self.owner.id:
            return orm.violations.empty

        import bot
        if usr.id == bot.sendbot.user.id:
            return orm.violations.empty

        vs = orm.violations()
        vs += 'User must own the message or be sendbot'

        return vs

class contactmechanism_messagetype(apriori.type):
    """ Represents the type of association a ``message`` has with a
    ``party.contactmechanism``.

    The name property, inherited from apriori.type, can contain values
    such as 'replyto', 'from', 'to', 'cc', 'bcc', etc..
    """

    # The collection of contactmechanism_messages associations this type
    # applies to.
    messages = contactmechanism_messages

class contactmechanism_message(orm.association):
    """ Associates a ``messages`` with a ``party.contactmechanism``. Via
    this associations, a message can a contact mechanism as the sender,
    and multiple contact mechanism (of different types; see
    contactmechanism_messagetype) as recipients.
    """

    # The party.contactmechanism. This will typically be a subentity
    # such as party.email or party.address (postal address).
    contactmechanism = party.contactmechanism

    # The message object associated with the ``contactmechanism``
    message = message

    @property
    def creatability(self):
        """ The user who owns the message may create associations to
        contact mechanisms (recipients, From: address, ReplyTo:, etc.).
        """
        vs = orm.violations()

        if self.message.owner.id != orm.security().user.id:
            vs += 'Current user must be the message owner'
        
        return vs

    @property
    def retrievability(self):
        # NOTE Obviously, the message's sender and recepients should be
        # able to retrieve a their message. However, at the moment we
        # will focus on allowing sendbot to retrieve messages for
        # dispatching and allow the message owner (which would usually
        # be the sender) the ability to retrieve.

        with orm.sudo():
            msg = self.message
            own = msg.owner

        usr = orm.security().user

        if own.id == usr.id:
            return orm.violations.empty

        import bot
        if usr.id == uuid.UUID(hex=bot.sendbot.UserId):
            return orm.violations.empty

        vs = orm.violations()
        vs += 'User must own the message or be sendbot'

        return vs

class dispatch(orm.entity):
    """ An object used to schedule a ``message`` for delivery.

    Each ``message`` has zero or more ``dispatches``. If a ``message``
    needs to be schedule for delivery to an external system (such as an
    SMPT server or a third party RESTful API) at least one ``dispatch``
    entry needs to be added to its ``dispatch`` collection.

    A ``dispatch`` has an implicit attribute called ``dispatchtype``
    (see the ``dispatchtype`` entity). This entity has a name property
    which indicates the general type of dispatch required ('email',
    'SMS', 'postal', etc). For messages that are destined for multiple
    contact mechanism (email addresses, SMS numbers, etc.), a dispatch
    should be created for each dispatchtype. If a dispatch fails and
    needs to be marked as dead for some reason, a dispatch can be
    cloned, allowing the system to keep trying.

    A dispatch has a collection of ``statuses``. ``status`` objects
    contain the datetime a ``dispatch`` enters into a new status.

    ``sendbot`` will scan dispatches that are not in a completed state,
    and will work to deliver the message's contents to the proper
    external system. ``sendbot`` will use entities in the third.py
    module to handle the actual interaction with third-party systems.
    """
    # The external message id. When a message is dispatched to 
    # a third party for delivery, the third party may or may not have
    # its own identifier for the message.
    externalid = str

    # A collection of status entities which detail when a dispatch
    # enters into different states
    statuses = statuses

    # A string representation of the last state that the dispatched
    # entered into. This is here only because it makes it easier for
    # sendbot to query the dispatches table by status. (Note that this
    # is a bit of a hack that we are using until correlated subqueries
    # are supported by the ORM. See 9b4b0ce0.)
    status = str

    def __init__(self, *args, **kwargs):
        """ Instantiate a dispatch object.
        """
        super().__init__(*args, **kwargs)
        self.orm.default('externalid', None)
        self.orm.default('status', 'queued')

    @property
    def creatability(self):
        """ The message owner my create a dispatch for the message.
        """
        vs = orm.violations(entity=self)
        vs.demand_root()

        return vs

    @property
    def retrievability(self):
        vs = orm.violations(entity=self)

        import bot
        vs.demand_user_is(bot.sendbot.user)

        return vs

    @property
    def updatability(self):
        vs = orm.violations(entity=self)

        import bot
        vs.demand_user_is(bot.sendbot.user)
        return vs

class dispatchtype(apriori.type):
    """ Each ``dispatch`` is described by one ``dispatchtype`` entity.
    The ``dispatchtype`` has a ``name`` attribute that describes the
    general type of dispatch. Common dispatches types include "email",
    "sms", "postal", etc.
    """
    dispatches = dispatches
    
class status(orm.entity):
    """ Each ``dispatch`` has a collection of ``status`` entites. These
    indicate the time a dispatch enters into a state. Common states are
    "queued", "in process", "completed", "failed".
    """

    # The datetime the event described by the status entity occured.
    begin = datetime

    @property
    def creatability(self):
        import bot
        vs = orm.violations()
        vs.demand_user_is(bot.sendbot.user)
        return vs

    @property
    def retrievability(self):
        """ sendbot may retrieve a dispatch's status.
        """
        import bot
        vs = orm.violations()
        vs.demand_user_is(bot.sendbot.user)
        return vs

class statustype(apriori.type):
    """ Records the type of status.
    
    Values for the ``name`` attribute:
        
        * 'postmarked': The message has been dispatched to a third party
        provider.

        * 'hard-bounce': The dispatch failed and any attempt to
        dispatch the message again will fail.

        * 'soft-bounce': The dispatch failed, and another dispatch
        entity should be created so the message can be attempted again
        at a later date.

        * 'viewed' The user has opened the email.
    """
    # The collection of statuses belonging to this type
    statuses = statuses
