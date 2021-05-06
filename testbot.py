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
import apriori
from config import config
from contextlib import redirect_stdout, redirect_stderr

class test_bot(tester.tester):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        orm.security().override = True

        if self.rebuildtables:
            es = orm.orm.getentitys(includeassociations=True)
            for e in es:
                if e.__module__ in ('bot', 'message', 'apriori'):
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

    def it_raises_onlog_event(self):
        def onlog(src, eargs):
            eargss.append(eargs)
        
        msgs = ['d', 'i', 'w', 'e', 'cr', 'ex']
        # Redirect stdout/stderr to /dev/null (so to speak)
        with redirect_stdout(None), redirect_stderr(None):
            for v in range(5, -1, -1):
                eargss = list()

                b = bot.bot(iterations=0, verbosity=v) 
                b.onlog += onlog
                b.debug('d')
                b.info('i')
                b.warning('w')
                b.error('e')
                b.critical('cr')
                b.exception('ex')

                msgs1 = [x.message.strip() for x in eargss]
                lvls = [x.level for x in eargss]

                self.eq(bot.bot.Levels[5-v:], lvls)
                self.eq(msgs[5-v:], msgs1)

    def it_logs_to_database(self):
        # Create an abstract bot
        b = bot.bot(iterations=0, verbosity=5) 

        # Log two info's. The calls to the log methods will result in
        # immediate saves of the logs to the database.
        b.debug('d')
        b.info('i')
        b.warning('w')
        b.error('e')
        b.critical('cr')
        b.exception('ex')

        # Test the logs
        self.six(b.logs)

        self.eq(bot.bot.Levels, b.logs.pluck('logtype.name'))

        # Save the bot. The bot's logs have already been save; this just
        # persists the bot itself
        b.save()

        # Reload bot
        b1 = bot.bot(b.id)

        # Ensure it does not lazy load prior logs. This is important
        # because we want to be able to use the ``logs`` property
        # to append new logs to the database, but we don't want the call
        # to logs to load every log every commited because that would
        # take to log. (NOTE This is currently accomplished through a
        # HACK:8210b80c that has a corresponding TODO).
        self.zero(b1.logs)

        for log in b.logs:
            # Each of the logs should be in the database
            log1 = self.expect(None, lambda: apriori.log(log))

            # The logs should reference the bot they were logged for
            self.eq(b.id, log1.bot.id)

        msgs = ['d', 'i', 'w', 'e', 'c', 'e']
        levels = bot.bot.Levels

        # Redirect stdout/stderr to /dev/null (so to speak)
        #with redirect_stdout(None), redirect_stderr(None):
        for v in range(5, -1, -1):
            b = bot.bot(iterations=0, verbosity=v) 
            b.debug('d')
            b.info('i')
            b.warning('w')
            b.error('e')
            b.critical('c')
            b.exception('e')

            b.save()

            self.zero(b.orm.reloaded().logs)

            self.eq(v + 1, b.logs.count)

            msgs1 = b.logs.pluck('message')
            lvls = b.logs.pluck('logtype.name')

            self.eq(bot.bot.Levels[5-v:], lvls)
            self.eq(msgs[5-v:], msgs1)

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
