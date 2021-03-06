# vim: set et ts=4 sw=4 fdm=marker

########################################################################
# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2021
########################################################################

""" This module contains all classes related to sending and queueing
messages such as email, SMS and the like.

TODOs:
"""
from datetime import datetime, date
from func import B
import apriori
from orm import text
import orm
import party

class messages(orm.entities):
    pass

class contactmechanism_messages(orm.associations):
    pass

class contactmechanism_messagetypes(apriori.types):
    pass

class message(orm.entity):
    html = text
    text = text
    postdate = datetime

    @staticmethod
    def email(from_, to, html=None, text=None, postdate=None):
        if isinstance(from_, str):
            from_ = party.email(name=from_)
        else:
            # TODO
            raise NotImplementedError()

        if isinstance(to, str):
            tos = party.emails()
            for to in to.split(';'):
                tos += party.email(name=to)
        elif isinstance(to, orm.entity):
            tos = to.orm.collectivize()
        else:
            raise TypeError('Invalid type for `to`')

        msg = message(
            html      =  html,
            text      =  text,
            postdate  =  postdate,
        )

        src   = contactmechanism_messagetype(name='source')
        dest  = contactmechanism_messagetype(name='destination')

        cm = contactmechanism_message(
            contactmechanism              =  from_,
            contactmechanism_messagetype  =  src,
        )

        msg.contactmechanism_messages += cm

        for to in tos:
            msg.contactmechanism_messages += contactmechanism_message(
                contactmechanism              =  to,
                contactmechanism_messagetype  =  dest,
            )

        msg.save()

        return msg

class contactmechanism_messagetype(apriori.type):
    messages = contactmechanism_messages

class contactmechanism_message(orm.association):
    contactmechanism = party.contactmechanism
    message = message






