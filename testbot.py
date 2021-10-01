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

from config import config
from contextlib import redirect_stdout, redirect_stderr
from dbg import B
from func import enumerate
import bot
import ecommerce
import message
import orm
import party
import tester

def clear():
    for p in party.party.orm.getsubentities(accompany=True):
        p.orm.truncate()

    party.company._carapacian = None

class test_bot(tester.tester):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.rebuildtables:
            es = orm.orm.getentitys(includeassociations=True)
            mods = 'bot', 'message', 'apriori', 'party', 'ecommerce',
            for e in es:
                if e.__module__ in mods:
                    e.orm.recreate()
        else:
            self._clear()
            party.company._carapacian = None

    @staticmethod
    def _clear():
        clear()

    def it_raises_onlog_event(self):
        def onlog(src, eargs):
            eargss.append(eargs)
        
        msgs = ['d', 'i', 'w', 'e', 'cr', 'ex']
        b = bot.sendbot()
        with orm.proprietor(party.company.carapacian), orm.su(b.user):
            for v in range(5, -1, -1):
                eargss = list()

                b = bot.sendbot(iterations=0, verbosity=v) 
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
        with orm.sudo():
            b = bot.sendbot(iterations=0, verbosity=5) 

        with orm.proprietor(party.company.carapacian), orm.su(b.user):
            # Create an abstract bot

            # Log two info's. The calls to the log methods will result
            # in immediate saves of the logs to the database.
            b.debug('d')
            b.info('i')
            b.warning('w')
            b.error('e')
            b.critical('cr')
            b.exception('ex')

            # Test the logs
            self.six(b.logs)

            self.eq(bot.bot.Levels, b.logs.pluck('logtype.name'))

            # Save the bot. The bot's logs have already been save; this
            # just persists the bot itself
            b.save()

            # Reload bot
            b1 = bot.sendbot(b.id)

            # Ensure it does not lazy load prior logs. This is important
            # because we want to be able to use the ``logs`` property to
            # append new logs to the database, but we don't want the
            # call to logs to load every log every commited because that
            # would take to log. (NOTE This is currently accomplished
            # through a HACK:8210b80c that has a corresponding TODO).
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
                b = bot.sendbot(iterations=0, verbosity=v) 
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

    def it_uses_carapacian_as_proprietor(self):
        self._clear()

        cara = party.company.carapacian

        sb = bot.sendbot(iterations=1, verbosity=5)
        sb()

        self.multiple(sb.logs)

        for log in sb.logs:
            self.is_(cara, log.proprietor)
            
            log = log.orm.reloaded()

            # sudo to retrieve proprietor (carapacian)
            with orm.sudo():
                propr = log.proprietor

            self.eq(cara.id, propr.id)

    def it_owns_what_it_creates(self):
        self._clear()

        sb = bot.sendbot(iterations=1, verbosity=5)
        sb()
        usr = sb.user

        self.multiple(sb.logs)

        for log in sb.logs:
            self.is_(usr, log.owner)
            self.eq(usr.id, log.orm.reloaded().owner.id)

    def it_calls_user(self):
        self._clear()
        ecommerce.users.orm.truncate()
        bot.sendbot._user = None

        sb = bot.sendbot(iterations=1, verbosity=5)
        sb()

        usr = sb.user
        self.is_(sb.user, usr)
        self.is_(sb, usr.party)
        self.eq('sendbot', usr.name)
        self.false(usr.orm.isnew)
        self.false(usr.orm.isdirty)
        self.false(usr.orm.ismarkedfordeletion)

        usr1 = usr.orm.reloaded()
        self.eq(sb.user.id, usr1.id)
        self.eq(sb.id, usr1.party.id)
        self.eq('sendbot', usr1.name)

class test_sendbot(tester.tester):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.rebuildtables:
            es = orm.orm.getentitys(includeassociations=True)
            mods = 'bot', 'message', 'party', 'ecommerce'
            for e in es:
                if e.__module__ in mods:
                    e.orm.recreate()
            self.recreateprinciples()
        else:
            self._clear()
            ecommerce.user.orm.truncate()

    @staticmethod
    def _clear():
        clear()

    def it_calls__call__(self):
        message.dispatches.orm.truncate()
        bot.sendbot._user = None

        b = bot.sendbot(iterations=1)
        with orm.proprietor(party.company.carapacian), orm.su(b.user):
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

            b()

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

            msg.save()

            with orm.sudo():
                dis = msg.dispatch(
                    dispatchtype = message.dispatchtype(name='email')
                )

                dis.save()
            

            b(exsimulate=True)

            dis = dis.orm.reloaded()
            self.none(dis.externalid)
            self.one(dis.statuses)
            self.eq('hard-bounce', dis.status)
            self.eq(
                'hard-bounce',
                dis.statuses.first.statustype.name
            )

            ''' Remove principles first '''
            self._clear()
            ecommerce.users.orm.truncate()
            bot.sendbot._user = None

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


            sec = orm.security()
            sec.proprietor = None
            sec.owner = None
            with orm.sudo():
                sb = bot.sendbot(iterations=1)

            bot.sendbot._user = None
            sb()


            cara = party.company.carapacian
            self.is_(cara, orm.security().proprietor)

            self.is_(sb.user, orm.security().owner)

            dis = dis.orm.reloaded()
            self.eq('postmarked', dis.status)
            self.one(dis.statuses)

    def it_invokes_with_iterations(self):
        eargss = list()
        def bot_onbeforeiteration(src, eargs):
            eargss.append(eargs)

        args = '--verbosity 5 --iterations=2 sendbot'
        pnl = bot.panel(args=args, dodisplay=False)
        usr = pnl.bot.user
        with orm.proprietor(party.company.carapacian), orm.su(usr):
            pnl.bot.onbeforeiteration += bot_onbeforeiteration
            pnl()

            for i, eargs in enumerate(eargss, 1):
                self.eq(i, eargs.iteration)
                self.eq(2, eargs.of)
            
    def it_invokes_with_no_iterations(self):
        eargss = list()
        def bot_onbeforeiteration(src, eargs):
            if len(eargss) == 5:
                eargs.cancel = True
                return

            eargss.append(eargs)

        args = '--verbosity 5 sendbot'
        pnl = bot.panel(args=args, dodisplay=False)
        usr = pnl.bot.user

        with orm.proprietor(party.company.carapacian), orm.su(usr):
            pnl.bot.onbeforeiteration += bot_onbeforeiteration
            pnl()

            self.five(eargss)
            for i, eargs in enumerate(eargss, 1):
                self.eq(i, eargs.iteration)
                self.none(eargs.of)

    def it_invokes_with_no_bot_argument(self):
        args = '--verbosity 5'

        pnl = bot.panel(args=args, dodisplay=False)
        with orm.proprietor(party.company.carapacian):
            try:
                pnl()
            except bot.TerminateError as ex:
                self.endswith(
                    ': error: the following arguments are '
                    'required: bot\n', str(ex)
                )
                
                self.eq(2, ex.status)

    def it_is_data_singleton(self):
        """ Ensure each time bot.sendbot is instatiated, the same
        data from the same row in the database.
        """

        # Clear the sendbot table and all super tables. The first
        # instantiation will create the row. The second will retrieve
        # it.
        self._clear()

        # This instatiation will create the record in the sendbot table.
        sb = bot.sendbot(iterations=0, verbosity=2)

        with orm.proprietor(party.company.carapacian), orm.su(sb.user):
            # This instatiated will retrieve the record from the sendbot
            # table
            sb1 = bot.sendbot(iterations=1, verbosity=3)

            # Though the id should be the same, the identity shouldn't
            # be because we want to be able to have alternate
            # configurations (``iterations``, ``verbosity``, etc)
            self.eq(sb.id, sb1.id)
            self.eq(0, sb.iterations)
            self.eq(1, sb1.iterations)
            self.eq(2, sb.verbosity)
            self.eq(3, sb1.verbosity)

            for b in (sb, sb1):
                self.false(b.orm.isnew)
                self.false(b.orm.isdirty)
                self.false(b.orm.ismarkedfordeletion)
                
                # The name of the bot, particularly at the
                # ``party.party`` super, was a little problematic. So
                # make sure it gets set correctly in all supers. The
                # name shouldn't be set in the contructor.
                while b:
                    self.eq('sendbot', b.name)
                    b = b.orm.super

if __name__ == '__main__':
    tester.cli().run()
