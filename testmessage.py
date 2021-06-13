#!/usr/bin/python3
# vim: set et ts=4 sw=4 fdm=marker

########################################################################
# Copyright (C) Jesse Hogan - All Rights Reserved                      #
# Unauthorized copying of this file, via any medium is strictly        #
# prohibited                                                           #
# Proprietary and confidential                                         #
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2021                 #
########################################################################

import apriori; apriori.model()

from func import enumerate, B
import bot
import ecommerce
import message
import orm
import party
import primative
import tester
import third
import uuid

class test_message(tester.tester):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        orm.security().override = True

        if self.rebuildtables:
            es = orm.orm.getentitys(includeassociations=True)
            for e in es:
                if e.__module__ in ('message', 'apriori', 'party'):
                    e.orm.recreate()

        orm.security().owner = ecommerce.users.root

        com = party.company(name='Carapacian')
        orm.security().proprietor = com
        com.save(com)

    def it_creates(self):
        msg = message.message(
            subject = 'Hello!!!',
            html = '<p>Hello, world</p>',
            text = 'Hello, world',
        )

        emails = (
            'replyto@example.com', 
            'from@example.com', 
            'to@example.com', 
            'to1@example.com',
            'cc@example.com', 
            'cc1@example.com',
            'bcc@example.com', 
            'bcc1@example.com',
        )

        for email in emails:
            if email.startswith('replyto'):
                name = 'replyto'
            if email.startswith('from'):
                name = 'from'
            elif email.startswith('to'):
                name = 'to'
            elif email.startswith('cc'):
                name = 'cc'
            elif email.startswith('bcc'):
                name = 'bcc'

            type = message.contactmechanism_messagetype(name=name)

            cm = message.contactmechanism_message(
                contactmechanism = party.email(name=email),
                contactmechanism_messagetype = type,
            )

            msg.contactmechanism_messages += cm 
        msg.save()

        msg1 = msg.orm.reloaded()

        self.eq(msg.id,    msg1.id)
        self.eq(msg.html,  msg1.html)
        self.eq(msg.text,  msg1.text)

        self.none(msg.postdate)
        self.none(msg1.postdate)

        cmms = msg.contactmechanism_messages.sorted()
        cmms1 = msg1.contactmechanism_messages.sorted()

        self.eight(cmms)
        self.eight(cmms1)

        for cmm, cmm1 in zip(cmms, cmms1):
            self.eq(cmm.id,                   cmm1.id)

            type = cmm.contactmechanism_messagetype
            type1 = cmm1.contactmechanism_messagetype

            msg = cmm.message
            msg1 = cmm1.message

            cm = cmm.contactmechanism
            cm1 = cmm1.contactmechanism

            self.eq(type.id, type1.id)
            self.eq(type.name, type1.name)

            self.eq(msg.id, msg1.id)
            self.eq(msg.html, msg1.html)
            self.eq(msg.text, msg1.text)

            self.eq(cm.id, cm1.id)
            self.eq(cm.name, cm1.name)

            if type1.name == 'from':
                self.startswith('from', cm1.name)
            elif type1.name == 'replyto':
                self.startswith('replyto', cm1.name)
            elif type1.name == 'to':
                self.startswith('to', cm1.name)
            elif type1.name == 'ccs':
                self.startswith('ccs', cm1.name)
            elif type1.name == 'bcc':
                self.startswith('bcc', cm1.name)

    def it_calls_email(self):
        def compare_messages(msg, msg1, cmmscnt):
            self.eq(msg.id,    msg1.id)
            self.eq(msg.html,  msg1.html)
            self.eq(msg.text,  msg1.text)

            self.eq(msg.postdate, msg1.postdate)

            cmms = msg.contactmechanism_messages.sorted()
            cmms1 = msg1.contactmechanism_messages.sorted()

            self.count(cmmscnt, cmms)
            self.count(cmmscnt, cmms1)

            for cmm, cmm1 in zip(cmms, cmms1):
                self.eq(cmm.id,                   cmm1.id)

                type = cmm.contactmechanism_messagetype
                type1 = cmm1.contactmechanism_messagetype

                msg = cmm.message
                msg1 = cmm1.message

                cm = cmm.contactmechanism
                cm1 = cmm1.contactmechanism

                self.eq(type.id, type1.id)
                self.eq(type.name, type1.name)

                self.eq(msg.id, msg1.id)
                self.eq(msg.html, msg1.html)
                self.eq(msg.text, msg1.text)

                self.eq(cm.id, cm1.id)
                self.eq(cm.name, cm1.name)

                if type1.name == 'from':
                    self.startswith('from', cm1.name)
                elif type1.name == 'to':
                    self.startswith('to', cm1.name)

        ''' Single `to` '''
        strto = 'to@example.com'
        objto = party.email(name='to@example.com')

        for to in (strto, objto):
            msg = message.message.email(
                from_     =  'from@example.com',
                to        =  to,
                html      =  '<p>html</p>',
                text      =  'text',
                postdate  =  '2020-02-02 02:02:02',
            )

            compare_messages(msg, msg.orm.reloaded(), 2)

        ''' Multiple `to`'s '''
        strtos = 'to1@example.com, to2@example.com'
        objtos = party.emails(
            initial = [
                party.email(name='to1@example.com'),
                party.email(name='to2@example.com')
            ]
        )

        for tos in (strtos, objtos):
            msg = message.message.email(
                from_     =  'from@example.com',
                to        =  tos,
                html      =  '<p>html</p>',
                text      =  'text',
                postdate  =  '2020-02-02 02:02:02',
            )

            compare_messages(msg, msg.orm.reloaded(), 3)

        ''' party.email as from '''
        from_ = party.email(name='from@example.com')
        msg = message.message.email(
            from_     =  from_,
            to        =  tos,
            html      =  '<p>html</p>',
            text      =  'text',
            postdate  =  '2020-02-02 02:02:02',
        )
        self.eq(from_.name, msg.from_.name)

        compare_messages(msg, msg.orm.reloaded(), 3)


        ''' party.email with ccs, bcc and replyto'''
        msg = message.message.email(
            replyto   = 'replyto@example.com',
            from_     = 'from@example.com',
            to        =  tos,
            cc        = 'ccs@example.com, ccs1@example.com',
            bcc       = 'bcc@example.com, bcc1@example.com',
            html      =  '<p>html</p>',
            text      =  'text',
            postdate  =  '2020-02-02 02:02:02',
        )
        self.eq(from_.name, msg.from_.name)

        compare_messages(msg, msg.orm.reloaded(), 8)

    def it_calls_from_(self):
        from_ = party.email(name='from@example.com')
        msg = message.message.email(
            from_     =  from_,
            to        =  'to@example.com',
            html      =  '<p>html</p>',
            text      =  'text',
            postdate  =  '2020-02-02 02:02:02',
        )

        self.eq(from_.id, msg.from_.id)
        self.eq(from_.name, msg.from_.name)

    def it_calls_status(self):
        msg = message.message.email(
            from_    =  'from@example.com',
            replyto  =  'replyto@example.com',
            to       =  'jhogan@gmail.com',
            subject  =  'Test email',
            text     =  'Test message',
            html     =  '<p>Test message</p>',
        )

        dis = msg.dispatch(
            dispatchtype = message.dispatchtype(name='email')
        )

        for i in range(2):
            name = uuid.uuid4().hex
            dis.statuses += message.status(
                begin = primative.datetime.utcnow(),
                statustype = message.statustype(
                    name = name
                )

            )
            dis.save()

            self.eq(name, dis.status)

            dis = dis.orm.reloaded()

    def it_calls_creatability(self):
        """ Any user can create a message.
        """
        with orm.override():
            name = uuid.uuid4().hex
            with orm.sudo():
                usr = ecommerce.user(name=name)
                usr.save()

        # Any user can create any message
        with orm.override(False):
            with orm.su(usr):
                msg = message.message(
                    subject = 'Test Message',
                    html = '<p>Hello World</p>',
                    text = 'Hello World',
                )
                self.expect(None, msg.save)

    def it_calls_retrievability(self):
        """ Any user can retrieve a message they created.
        """
        with orm.override():
            with orm.sudo():
                usr = ecommerce.user(name='creator')
                usr1 = ecommerce.user(name='other')
                usr.save(usr1)

        # Any user can retrieve any message
        with orm.override(False):
            with orm.su(usr):
                msg = message.message(
                    subject = 'Test Message',
                    html = '<p>Hello World</p>',
                    text = 'Hello World',
                )
                msg.save()

                self.expect(None, msg.orm.reloaded)

            with orm.su(usr1):
                self.expect(orm.AuthorizationError, msg.orm.reloaded)

class test_contactmechanism_message(tester.tester):
    def it_calls_creatability(self):
        with orm.override():
            with orm.sudo():
                usr = ecommerce.user(name='creator')
                usr1 = ecommerce.user(name='other')
                usr.save(usr1)

        with orm.override(False):
            with orm.su(usr):
                msg = message.message(
                    subject = 'Test Message',
                    html = '<p>Hello World</p>',
                    text = 'Hello World',
                )
                msg.save()

            with orm.su(usr):
                type = message.contactmechanism_messagetype(name='from')

                name = 'to@example.com'
                cm = message.contactmechanism_message(
                    contactmechanism = party.email(name=name),
                    type = type
                )

                msg.contactmechanism_messages += cm

                self.expect(
                    None, msg.contactmechanism_messages.last.save
                )

            with orm.su(usr1):
                name = 'to1@example.com'
                cm = message.contactmechanism_message(  
                    contactmechanism = party.email(name=name),
                    type = type
                )

                msg.contactmechanism_messages += cm

                self.expect(
                    orm.AuthorizationError, 
                    msg.contactmechanism_messages.last.save
                )

    def it_calls_retrievability(self):
        with orm.override():
            with orm.sudo():
                usr = ecommerce.user(name='creator')
                usr1 = ecommerce.user(name='other')
                usr.save(usr1)

        with orm.override(False):
            with orm.su(usr):
                # Create message
                msg = message.message(
                    subject = 'Test Message',
                    html = '<p>Hello World</p>',
                    text = 'Hello World',
                )
                msg.save()

                # Create contact mechanisms and association between
                # contact mechanisms and message
                type = message.contactmechanism_messagetype(name='from')
                name = 'to@example.com'
                cm = message.contactmechanism_message(
                    contactmechanism = party.email(name=name),
                    type = type
                )

                msg.contactmechanism_messages += cm

                self.expect(
                    None, msg.contactmechanism_messages.last.save
                )

            # To keep lines short, assign .reloaded method to `reloaded`
            reloaded = msg.contactmechanism_messages.last.orm.reloaded

            # Create should be able to retrieve
            with orm.su(usr):
                self.expect(None, reloaded)

            # Non-creator shouldn't be able to retrieve
            with orm.su(usr1):
                self.expect(orm.AuthorizationError, reloaded)

            # Sendbot should be able to retrieve
            with orm.sudo():
                sb = bot.sendbot().user

            with orm.su(sb):
                self.expect(None, reloaded)

class test_dispatch(tester.tester):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        with orm.sudo():
            orm.security().proprietor = party.company.carapacian

    def it_calls_creatability(self):
        with orm.sudo():
            usr = ecommerce.user(name='creator')
            usr1 = ecommerce.user(name='other')
            usr.save(usr1)

        with orm.override(False):
            with orm.su(usr):
                msg = message.message(
                    subject = 'Test Message',
                    html = '<p>Hello World</p>',
                    text = 'Hello World',
                )
                msg.save()

            # The message owner should not be able to create a dispatch
            # for the message.
            with orm.su(usr):
                dis = msg.dispatch(
                    dispatchtype = message.dispatchtype(name='email')
                )

                self.expect(orm.AuthorizationError, dis.save)

            # Other users should not be able to create dispatches for
            # messages they don't own
            with orm.su(usr1):
                dis = msg.dispatch(
                    dispatchtype = message.dispatchtype(name='email')
                )

                self.expect(orm.AuthorizationError, dis.save)

            # Only root should be able to create a dispatch
            msg.dispatches.clear()
            with orm.sudo():
                dis = msg.dispatch(
                    dispatchtype = message.dispatchtype(name='email')
                )

                self.expect(None, dis.save)
        
    def it_calls_retrievability(self):
        with orm.sudo():
            usr = ecommerce.user(name='creator')
            usr1 = ecommerce.user(name='other')
            usr.save(usr1)

        with orm.override(False):
            with orm.su(usr):
                msg = message.message(
                    subject = 'Test Message',
                    html = '<p>Hello World</p>',
                    text = 'Hello World',
                )

                msg.save()

        with orm.sudo():
            dis = msg.dispatch(
                dispatchtype = message.dispatchtype(name='email')
            )

            dis.save()

        # Only sendbot should be able to retrieve a dispatch.
        # (Although, in the future, sysadmins would be interested in
        # the status of of dispatches.)
        with orm.override(False):
            with orm.su(usr):
                self.expect(orm.AuthorizationError, dis.orm.reloaded)

            with orm.su(usr1):
                self.expect(orm.AuthorizationError, dis.orm.reloaded)

            with orm.sudo():
                sb = bot.sendbot().user

            with orm.su(sb):
                self.expect(None, dis.orm.reloaded)

    def it_calls_updatability(self):
        """ Only sendbot can update a dispatch.
        """

        with orm.sudo():
            usr = ecommerce.user(name='creator')
            usr1 = ecommerce.user(name='other')
            usr.save(usr1)

        with orm.override(False):
            with orm.su(usr):
                msg = message.message(
                    subject = 'Test Message',
                    html = '<p>Hello World</p>',
                    text = 'Hello World',
                )

                msg.save()

            with orm.sudo():
                dis = msg.dispatch(
                    dispatchtype = message.dispatchtype(name='email')
                )
                dis.save()

            dis.status += '-addendum'

            with orm.su(usr):
                self.expect(orm.AuthorizationError, dis.save)

            with orm.su(usr1):
                self.expect(orm.AuthorizationError, dis.save)

            with orm.sudo():
                sb = bot.sendbot().user

            with orm.su(sb):
                self.expect(None, dis.save)

class test_status(tester.tester):
    def it_calls_creatability(self):
        with orm.sudo():
            with orm.proprietor(party.company.carapacian):
                pass

        with orm.proprietor(party.company.carapacian):
            with orm.override():
                with orm.sudo():
                    usr = ecommerce.user(name='creator')
                    usr.save()

            with orm.override(False):
                with orm.su(usr):
                    msg = message.message.email(
                        from_    =  'from@example.com',
                        replyto  =  'replyto@example.com',
                        to       =  'jhogan@carapacian.com',
                        subject  =  'Test email',
                        text     =  'Test message',
                        html     =  '<p>Test message</p>',
                    )
                    msg.save()

                with orm.sudo():
                    dis = msg.dispatch(
                        dispatchtype = message.dispatchtype(name='email')
                    )
                    dis.save()

                sts = dis.statuses
                self.zero(sts)
                dispatcher = third.dispatcher.create(dis)

                with orm.su(bot.sendbot.user):
                    # Create status objects in dis.status
                    dispatcher.dispatch(dis)
                    self.multiple(sts)

                with orm.su(usr):
                    msg = message.message.email(
                        from_    =  'from@example.com',
                        replyto  =  'replyto@example.com',
                        to       =  'jhogan@carapacian.com',
                        subject  =  'Test email',
                        text     =  'Test message',
                        html     =  '<p>Test message</p>',
                    )
                    msg.save()

                with orm.sudo():
                    dis = msg.dispatch(
                        dispatchtype = message.dispatchtype(name='email')
                    )
                    dis.save()

                dispatcher = third.dispatcher.create(dis)
                with orm.su(usr):
                    self.expect(
                        orm.AuthorizationError,
                        lambda: dispatcher.dispatch(dis)
                    )

    def it_calls_retrievability(self):
        with orm.sudo():
            with orm.proprietor(party.company.carapacian):
                pass

        with orm.proprietor(party.company.carapacian):
            with orm.override():
                with orm.sudo():
                    usr = ecommerce.user(name='creator')
                    usr.save()

            with orm.override(False):
                with orm.su(usr):
                    msg = message.message.email(
                        from_    =  'from@example.com',
                        replyto  =  'replyto@example.com',
                        to       =  'jhogan@carapacian.com',
                        subject  =  'Test email',
                        text     =  'Test message',
                        html     =  '<p>Test message</p>',
                    )
                    msg.save()

                with orm.sudo():
                    dis = msg.dispatch(
                        dispatchtype = message.dispatchtype(name='email')
                    )
                    dis.save()

                    dispatcher = third.dispatcher.create(dis)

                with orm.su(bot.sendbot.user):
                    # Create status objects in dis.status
                    dispatcher.dispatch(dis)

                reloaded = dis.statuses.first.orm.reloaded
                with orm.su(usr):
                    self.expect(orm.AuthorizationError, reloaded)

                with orm.su(bot.sendbot.user):
                    self.expect(None, reloaded)

if __name__ == '__main__':
    tester.cli().run()
