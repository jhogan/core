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
import tester
import bot
import message
import orm
import ecommerce
import party
from config import config
from contextlib import redirect_stdout, redirect_stderr

class test_bot(tester.tester):
    def it_logs(self):
        recs = list()
        def onlog(src, eargs):
            recs.append(eargs.record)
        
        msgs = ['d', 'i', 'w', 'e', 'c', 'e']
        levels = [
            'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL', 'ERROR'
        ]

        # Redirect stdout/stderr to /dev/null (so to speak)
        with redirect_stdout(None), redirect_stderr(None):
            for v in range(5, -1, -1):
                recs = list()

                b = bot.bot(iterations=0, verbosity=v) 
                b.onlog += onlog
                b.log('d', level='debug')
                b.log('i') # level default to 'info'
                b.log('w', level='warning')
                b.log('e', level='error')
                b.log('c', level='critical')
                b.log('e', level='exception')
                self.eq(msgs[5-v:], [x.message for x in recs])
                self.eq(levels[5-v:], [x.levelname for x in recs])

class test_sendbot(tester.tester):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        orm.security().override = True

        if self.rebuildtables:
            es = orm.orm.getentitys(includeassociations=True)
            for e in es:
                if e.__module__ in ('bot', 'message'):
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

    def it_calls__call__(self):
        message.dispatches.orm.truncate()

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

        msg.save()

        sb = bot.sendbot(iterations=1)
        sb()

        dis = dis.orm.reloaded()

        self.eq('postmarked', dis.status)

        sts = dis.statuses

        self.one(sts)
        self.eq('postmarked', sts.last.statustype.name)

        ''' Send a bad email '''
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
        
        msg.save()

        sb(exsimulate=True)

        dis = dis.orm.reloaded()
        self.none(dis.externalid)
        self.one(dis.statuses)
        self.eq('hard-bounce', dis.status)
        self.eq(
            'hard-bounce',
            dis.statuses.first.statustype.name
        )

if __name__ == '__main__':
    tester.cli().run()
