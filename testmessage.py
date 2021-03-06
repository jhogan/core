#!/usr/bin/python3
# vim: set et ts=4 sw=4 fdm=marker

########################################################################
# Copyright (C) Jesse Hogan - All Rights Reserved                      #
# Unauthorized copying of this file, via any medium is strictly        #
# prohibited                                                           #
# Proprietary and confidential                                         #
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2021                 #
########################################################################

from func import enumerate, B
import apriori
import message
import party
import tester
import orm
import ecommerce

class test_message(tester.tester):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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
            html = '<p>Hello, world</p>',
            text = 'Hello, world',
        )

        emails = (
            'source@example.com', 
            'destination@example.com', 
            'destination1@example.com'
        )

        for i, email in enumerate(emails):
            if i.first:
                type = message.contactmechanism_messagetype(
                    name = 'source'
                )
            else:
                type = message.contactmechanism_messagetype(
                    name = 'destination'
                )


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

        self.three(cmms)
        self.three(cmms1)

        for cmm, cmm1 in zip(cmms, cmms1):
            self.eq(cmm.id,                   cmm1.id)

            type = cmm.contactmechanism_messagetype
            type1 = cmm1.contactmechanism_messagetype

            msg = cmm.message
            msg1 = cmm1.message

            cm = cmm.contactmechanism
            cm1 = cmm1.contactmechanism

            # TODO This won't be necessary once this get's specialized
            cm1 = party.email(cm1)

            self.eq(type.id, type1.id)
            self.eq(type.name, type1.name)

            self.eq(msg.id, msg1.id)
            self.eq(msg.html, msg1.html)
            self.eq(msg.text, msg1.text)

            self.eq(cm.id, cm1.id)
            self.eq(cm.name, cm1.name)

            if type1.name == 'source':
                self.startswith('source', cm1.name)
            elif type1.name == 'destination':
                self.startswith('destination', cm1.name)

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

                # TODO This won't be necessary once this get's specialized
                cm1 = party.email(cm1)

                self.eq(type.id, type1.id)
                self.eq(type.name, type1.name)

                self.eq(msg.id, msg1.id)
                self.eq(msg.html, msg1.html)
                self.eq(msg.text, msg1.text)

                self.eq(cm.id, cm1.id)
                self.eq(cm.name, cm1.name)

                if type1.name == 'source':
                    self.startswith('source', cm1.name)
                elif type1.name == 'destination':
                    self.startswith('destination', cm1.name)

        ''' Single `to` '''
        strto = 'destination@example.com'
        objto = party.email(name='destination@example.com')

        for to in (strto, objto):
            msg = message.message.email(
                from_     =  'source@example.com',
                to        =  to,
                html      =  '<p>html</p>',
                text      =  'text',
                postdate  =  '2020-02-02 02:02:02',
            )

            compare_messages(msg, msg.orm.reloaded(), 2)


                


        

if __name__ == '__main__':
    tester.cli().run()
