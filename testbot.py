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

class test_bot(tester.tester):

    def it_raise_on__call__(self):
        # TODO
        ...

class test_sendbot(tester.tester):
    def it__calls__(self):
        msg = message.email(
            type = 'email',
            from_ = 'from@example.com',
            to = 'to@example.com',
            html = self.dedent('''
            <p>
                This is a test message.
            </p>
            '''),
            text = 'This is a test message',
        )

        
tester.cli().run()
