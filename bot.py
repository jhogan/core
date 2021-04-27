#!/usr/bin/python3
# vim: set et ts=4 sw=4 fdm=marker

########################################################################
# Copyright (C) Jesse Hogan - All Rights Reserved                      #
# Unauthorized copying of this file, via any medium is strictly        #
# prohibited                                                           #
# Proprietary and confidential                                         #
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2021                 #
########################################################################

from config import config
from entities import classproperty
from func import B
import ecommerce
import message
import os
import third
import time
import orm

class bots(ecommerce.agents):
    @classproperty
    def bots(cls):
        """ Return each class that inherits from directly or indirectly
        from ``bot``.
        """

        r = list()

        # Iterate over direct sub classes
        for sub in cls.orm.entity.__subclasses__():
            r.append(sub)

            # Recurse into indirect subclasses, thus collecting the
            # whole heirarchy. (Note, at the time of this writing, there
            # are no indirect subclasses. This is for future-proofing.)
            r.extend(sub.orm.entities.bots)

        return r

class bot(ecommerce.agent):
    def __init__(self, *args, **kwargs):
        self._iterations = kwargs.pop('iterations', None)
        super().__init__(*args, **kwargs)
        self.name = type(self).__name__

    @orm.attr(int)
    def pid(self):
        return os.getpid()

    @property
    def iterations(self):
        if self._iterations is not None:
            self._iterations = int(self._iterations)
        return self._iterations

    def __call__(self):
        raise NotImplementedError('Implement in subentity')

class sendbots(bots):
    pass

class sendbot(bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __call__(self, exsimulate=False):
        iter = self.iterations
        i = 0
        while True:
            self._dispatch(exsimulate=exsimulate)
            time.sleep(.001)

            if iter is None:
                continue

            i = i + 1

            if i == iter:
                break

    def _dispatch(self, exsimulate=False):
        log = config().logs.first
        diss = message.dispatches(status='queued')

        for dis in diss:
            # TODO:f4a2e3e2 Don't dispatch usless
            # now >= dis.message.postdate.  Also, dispatcher.dispatch
            # should raise an exception if this were not the case.
            dispatcher = third.dispatcher.create(dis)

            try:
                if exsimulate:
                    with dispatcher.exsimulate():
                        dispatcher.dispatch(dis)
                else:
                    dispatcher.dispatch(dis)
            except third.api.Error as ex:
                # NOTE The dispatcher will log the error as a
                # ``message.status`` in ``dis.statuses``.

                # TODO:4d723428 (fix logging api)
                log.exception(
                    f'API Error with dispatch {dis.id} ({ex}) - '
                    'Continuing...'
                )
                continue

            # TODO We may want to catch network errors here. For
            # example, if the network is down, we may want to give up
            # for the moment.
            except Exception as ex:
                log.exception(
                    f'Error with dispatch {dis.id} ({ex}) - '
                    'Continuing...'
                )
                continue

if __name__ == '__main__':
    import argparse
    prs = argparse.ArgumentParser(
        description="Runs a bot",
        epilog = (
            'Bots are typically run in the background, managed by '
            'systemd for example. Alternatively, a bot can be run in '
            'the foreground, such as when debugging.'
        )
    )

    prs.add_argument(
        'bot', 
        help = 'Name of the bot to invoke',
        choices = [x.__name__ for x in bots.bots]
    )

    prs.add_argument(
        'args', 
        nargs = "*",
        help = "Arguments to pass to the bot's constructor",
    )

    args = prs.parse_args()

    for bot in bots.bots:
        if bot.__name__ == args.bot:
            bot(*args.args)()
            break
