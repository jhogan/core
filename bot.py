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

class bots(ecommerce.agents):
    pass

class bot(ecommerce.agent):
    def __call__(self):
        raise NotImplementedError('Implement in subentity')

class sendbots(bots):
    ...

class sendbot(bot):
    ...

