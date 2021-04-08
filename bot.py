#!/usr/bin/python3
# vim: set et ts=4 sw=4 fdm=marker

########################################################################
# Copyright (C) Jesse Hogan - All Rights Reserved                      #
# Unauthorized copying of this file, via any medium is strictly        #
# prohibited                                                           #
# Proprietary and confidential                                         #
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2021                 #
########################################################################

from func import B
import ecommerce
import message
import third
import time

class bots(ecommerce.agents):
    pass

class bot(ecommerce.agent):
    def __call__(self):
        raise NotImplementedError('Implement in subentity')

class sendbots(bots):
    pass

class sendbot(bot):
    def __call__(self, iterations=None, exsimulate=False):
        i = 0
        while True:
            self._dispatch(exsimulate=exsimulate)
            time.sleep(.001)

            if iterations is None:
                continue

            i = i + 1

            if i == iterations:
                break

    def _dispatch(self, exsimulate=False):
        diss = message.dispatches(status='queued')

        for dis in diss:
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

                # TODO Log
                continue

            # TODO We may want to catch network errors here. For
            # example, if the network is down, we may want to give up
            # for the moment.
            except Exception as ex:
                # TODO Log
                continue


