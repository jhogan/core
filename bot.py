#!/usr/bin/python3
# vim: set et ts=4 sw=4 fdm=marker

########################################################################
# Copyright (C) Jesse Hogan - All Rights Reserved                      #
# Unauthorized copying of this file, via any medium is strictly        #
# prohibited                                                           #
# Proprietary and confidential                                         #
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2021                 #
########################################################################

import ecommerce
import message
import third
from func import B

class bots(ecommerce.agents):
    pass

class bot(ecommerce.agent):
    def __call__(self):
        raise NotImplementedError('Implement in subentity')

class sendbots(bots):
    pass

class sendbot(bot):
    def __call__(self):
        while True:
            self._dispatch()

    def _dispatch(self):
        diss = message.dispatches(status = 'queued')

        for dis in diss:
            dispacher = third.dispatcher.create(dis)

            try:
                dispacher.dispatch(dis)
            except third.api.Error as ex:
                # Get the emailer service's code and message for the
                # error. This is distinct from the HTTP status code and
                # reason/phrase.
                code = ex.code
                msg  = ex.message

            # TODO We may want to catch network errors here. For
            # example, if the network is down, we may want to give up
            # for the moment.
            except Exception as ex:
                # TODO Log and continue
                ...


