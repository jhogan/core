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
import third
import message
import tester
import orm
import ecommerce
import party

class test_postmark(tester.tester):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        orm.security().override = True

        if self.rebuildtables:
            es = orm.orm.getentitys(includeassociations=True)
            for e in es:
                if e.__module__ in ('third', 'message'):
                    e.orm.recreate()

        # Create an owner and get the root user
        own = ecommerce.user(name='hford')
        root = ecommerce.users.root

        # Save the owner, the root user will be the owner's owner.
        with orm.sudo():
            own.owner = root
            own.save()

        # Going forward, `own` will be the owner of all future records
        # created.
        orm.security().owner = own

        # Create a company to be the propritor.
        com = party.company(name='Ford Motor Company')
        com.save()

        # Set the company as the proprietory
        orm.security().proprietor = com

        # Update the owner (hford) so that the company (Ford Motor
        # Company) is the proprietor.
        own.proprietor = com
        own.save()

    def it_sends_sucessfully(self):
        msg = message.message.email(
            from_    =  'from@example.com',
            replyto  =  'replyto@example.com',
            to       =  'to@example.com',
            cc       =  'cc@example.com',
            bcc      =  'bcc@example.com',
            subject  =  'Test email',
            text     =  'Test message',
            html     =  '<p>Test message</p>',
        )

        msg = message.message.email(
            from_    =  'from@example.com',
            replyto  =  'replyto@example.com',
            to       =  'jessehogan0@gmail.com',
            subject  =  'Test email',
            text     =  'Test message',
            html     =  '<p>Test message</p>',
        )

        dis = msg.dispatch(
            dispatchtype = message.dispatchtype(name='email')
        )

        pm = third.postmark()
        
        if pm.key != 'POSTMARK_API_TEST':
            raise ValueError(
                'postmark class is not using POSTMARK_API_TEST for '
                'tests'
            )

        res = pm.send(dis)

        self.eq('Test job accepted', res['Message'])
        self.eq('jessehogan0@gmail.com', res['To'])
        self.uuid(res['MessageID'])

        self.uuid(dis.externalid)

        # Ensure the externalid was saved
        dis = dis.orm.reloaded()
        self.uuid(dis.externalid)

    def it_sends_to_a_bad_address(self):
        msg = message.message.email(
            from_    =  'badfrom@carapacian.com',
            to       =  'test@blackhole.postmarkapp.com',
            subject  =  'Test email',
            text     =  'Test message',
            html     =  '<p>Test message</p>',
        )

        dis = msg.dispatch(
            dispatchtype = message.dispatchtype(name='email')
        )

        pm = third.postmark()
        
        # NOTE Desimulate in order to use the real API to cause a real
        # bounce. This should be done with care:
        # https://postmarkapp.com/support/article/1213-best-practices-for-testing-your-emails-through-postmark
        with pm.exsimulate():
            res = pm.send(dis)

            self.eq('Test job accepted', res['Message'])
            self.eq('jessehogan0@gmail.com', res['To'])
            self.uuid(res['MessageID'])

            self.uuid(dis.externalid)

            # Ensure the externalid was saved
            dis = dis.orm.reloaded()
            self.uuid(dis.externalid)



if __name__ == '__main__':
    tester.cli().run()
