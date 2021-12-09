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

from func import enumerate
from dbg import B
import third
import message
import tester
import orm
import ecommerce
import party
import third
import www

class test_postmark(tester.tester):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        orm.security().override = True

        if self.rebuildtables:
            es = orm.orm.getentityclasses(includeassociations=True)
            for e in es:
                if e.__module__ in ('third', 'message'):
                    e.orm.recreate()

    def it_sends_sucessfully(self):
        msg = message.message.email(
            from_    =  'from@example.com',
            replyto  =  'replyto@example.com',
            to       =  'jhogan@carapacian.com',
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

        res = pm.dispatch(dis)

        self.eq('Test job accepted', res['Message'])
        self.eq('jhogan@carapacian.com', res['To'])
        self.uuid(res['MessageID'])

        self.one(dis.statuses)
        self.eq(
            'postmarked',
            dis.statuses.first.statustype.name
        )

        self.uuid(dis.externalid)

        # Ensure the externalid was saved
        dis = dis.orm.reloaded()
        self.uuid(dis.externalid)
        self.one(dis.statuses)
        self.eq(
            'postmarked',
            dis.statuses.first.statustype.name
        )

    def it_send_from_a_bad_email_address(self):
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
        ex = None
        
        # NOTE Exsimulate in order to use the real API to cause a real
        # bounce. This should be done with care:
        # https://postmarkapp.com/support/article/1213-best-practices-for-testing-your-emails-through-postmark
        with pm.exsimulate():
            try:
                pm.dispatch(dis)
            except third.api.Error as ex:
                self.type(www.UnprocessableEntityError, ex.inner)
                self.eq(400, ex.code)

                msg = (
                "The 'From' address you supplied "
                "(badfrom@carapacian.com) is not a Sender Signature on "
                "your account. Please add and confirm this address in "
                "order to be able to use it in the 'From' field of "
                "your messages."
                )

                self.status(422, ex.inner)
                self.eq(msg, ex.message)
                self.none(dis.externalid)
                self.one(dis.statuses)
                self.eq(
                    'hard-bounce',
                    dis.statuses.first.statustype.name
                )

                # Ensure the externalid was saved
                dis = dis.orm.reloaded()
                self.none(dis.externalid)
                self.one(dis.statuses)
                self.eq(
                    'hard-bounce',
                    dis.statuses.first.statustype.name
                )
            except Exception as ex:
                self.fail(f'Incorrect exception type {ex}')
            else:
                self.fail('No exception was thrown')


if __name__ == '__main__':
    tester.cli().run()
