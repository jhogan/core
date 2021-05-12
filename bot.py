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
import entities
import message
import orm
import os
import inspect
import sys
import third
import time
import apriori
import party
import db
import uuid

class addlogeventargs(entities.eventargs):
    def __init__(self, msg, lvl):
        self.message = msg
        self.level = lvl

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
    Levels = [
        'debug',  'info',      'warning',
        'error',  'critical',  'exception'
    ]

    def __init__(self, *args, **kwargs):
        """ An abstract class that represents a bot. 
        
        Concrete bots will inherit from this class to implement their
        specific functions.

        :param: iterations int: The number of iterations to make before
        exiting. Most bots will be in an infinite loop. However, for
        debugging purposes, a developer may want to limit the number of
        iterations to 1.

        :param: verbosity int: The level of status output the bot should
        generate. Status output will be sent to a log file. It will also be
        sent to stdout. Valid values: 5=debug and up, 4=info and up,
        3=warning and up, 2=error and up, 1=critical and up, 0=only
        exceptions. 'debug' and 'info' go to stdout; all other output
        goes to stderr.
        """

        onlog = kwargs.pop('onlog', None)
        iterations = kwargs.pop('iterations', None)
        verbosity = kwargs.pop('verbosity', 0)

        super().__init__(*args, **kwargs)

        self._onlog = None
        if onlog:
            self.onlog += onlog

        self._iterations = iterations
        self.verbosity = verbosity
        self.name = type(self).__name__
        self._user = None

    @orm.attr(apriori.logs)
    def logs(self):
        # HACK:8210b80c We want ``bot`` to have a ``logs`` constiuent that
        # we can add to but we don't want to load every log the bot has
        # ever recorded. So set .isloaded = True to prevent that. A
        # better solution to this problem is discussed in a TODO with
        # the 8210b80c identifier.

        if not hasattr(self, '_logs'):
            b = self
            while b:
                try:
                    map = b.orm.mappings['logs']
                except IndexError:
                    b = b.orm.super
                    continue
                else:
                    break

            map.value = apriori.logs('botid', self.id)

            # Disallow loading
            map.value.orm.isloaded = True

            self._logs = map.value

        return self._logs

    @property
    def user(self):
        if type(self) is bot:
            raise NotImplementedError(
                'user is only available to concrete classes'
            )

        if not self._user:
            if not hasattr(self, 'Id'):
                raise ValueError('bot must have Id constant set')

            id = uuid.UUID(self.Id)

            with orm.sudo():
                try:
                    self._user = ecommerce.user(id)
                except db.RecordNotFoundError:
                    self._user = ecommerce.user(
                        id   = id,
                        name = type(self).__name__,
                        party  = self,
                    )
                    self._user.save()

        return self._user

    @property
    def onlog(self):
        if not self._onlog:
            self._onlog = entities.event()
        return self._onlog

    @onlog.setter
    def onlog(self, v):
        self._onlog = v

    @property
    def level(self):
        return self.Levels[5 - self.verbosity:][0]

    @property
    def levels(self):
        if self.verbosity is None:
            return list()

        return self.Levels[5 - self.verbosity:]

    def debug(self, msg, end='\n'):
        f = inspect.stack()[0].function
        self._log(msg=msg, lvl=f, end=end)

    def info(self, msg, end='\n'):
        f = inspect.stack()[0].function
        self._log(msg=msg, lvl=f, end=end)

    def warning(self, msg, end='\n'):
        f = inspect.stack()[0].function
        self._log(msg=msg, lvl=f, end=end)

    def error(self, msg, end='\n'):
        f = inspect.stack()[0].function
        self._log(msg=msg, lvl=f, end=end)

    def critical(self, msg, end='\n'):
        f = inspect.stack()[0].function
        self._log(msg=msg, lvl=f, end=end)

    def exception(self, msg, end='\n'):
        f = inspect.stack()[0].function
        self._log(msg=msg, lvl=f, end=end)

    def _log(self, msg, lvl='info', end='\n'):
        if lvl not in self.Levels:
            raise ValueError(f'Invalid level: "{lvl}"')

        lvls = self.levels

        if lvl not in lvls:
            return

        try:
            self.logs += apriori.log(
                message = msg,
                logtype = apriori.logtype(name=lvl)
            )

            self.logs.save()
        finally:
            # In case there is a database/ORM issue, we can raise
            # the onlog event which will probably be handle something
            # that prints to a device like stdout our a file.
            eargs = addlogeventargs(msg=msg + end, lvl=lvl)
            self.onlog(self, eargs)

    @orm.attr(int)
    def pid(self):
        return os.getpid()

    @property
    def iterations(self):
        return self._iterations

    @property
    def verbosity(self):
        return self._verbosity

    @verbosity.setter
    def verbosity(self, v):
        possible = list(range(7)) + [None]
        if v not in possible:
            possible = [str(x) for x in possible]
            raise InputError(
                f'Value for verbosity must be {",".join(possible)}'
            )
        self._verbosity = v

    def __call__(self, exsimulate=False):
        cara = party.company.carapacian

        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # Set the ORM's owner to the bot's user object. We won't all
        # future accessibilty to consider the bot's user as the owner,
        # and all new records, such as log records, to be owned by the
        # bot's user.
        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        orm.security().owner = self.user

        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # Set ORM's proprietor to Carapacian for all ORM database
        # interactions.
        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        orm.security().proprietor = cara

        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # Set the bot's proprietor to the Carapacian company
        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        self.proprietor = cara

        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # Ensure the bot itself is in the database and that root is the
        # owner.
        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        with orm.sudo():
            self.save()

        with orm.su(self.user):
            self.info(f'{type(self).__name__} is alive')
            self.info(f'Log levels: {" | ".join(self.levels)}')

            return self._call(exsimulate=exsimulate)

class sendbots(bots):
    pass

class sendbot(bot):
    Id = 'fdcf21b2-dc0b-40ef-934f-ffbca49c915c'
    def __init__(self, *args, **kwargs):
        """ ``sendbot`` finds incomplete (queued) ``dispatch`` entities
        for messsages and sends them to external sytems.

        ``sendbot`` is responsible for ensuring that email, SMS, text
        messages, and so on leave the core system and are delivered to
        their intended recipients. ``sendbot`` continually polls the
        database for new dispatches. However, if the ``interations``
        argument is given, it will only poll the database for that
        many ``iterations``.
        """
        super().__init__(*args, **kwargs)

    def _call(self, exsimulate=False):
        iter = self.iterations
        i = j = 0
        self.info('dispatching:')
        while True:
            j = j + 1
            self.debug('.', end='')

            if j % 80 == 0:
                self.debug('')

            self._dispatch(exsimulate=exsimulate)
            time.sleep(1)

            if iter is None:
                continue

            i = i + 1

            if i == iter:
                break

    def _dispatch(self, exsimulate=False):
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
                self.exception(
                    f'API Error with dispatch {dis.id} ({ex}) - '
                    'Continuing...'
                )
                continue

            # TODO We may want to catch network errors here. For
            # example, if the network is down, we may want to give up
            # for the moment.
            except Exception as ex:
                self.exception(
                    f'Error with dispatch {dis.id} ({ex}) - '
                    'Continuing...'
                )
                continue

class InputError(ValueError):
    pass

if __name__ == '__main__':
    def main():
        import argparse
        import inspect
        from io import StringIO

        def parse_docstring(doc):
            r = dict()
            params = list()
            param = None
            text= str()
            for ln in StringIO(doc):
                ln = ln.strip()

                if ln == '':
                    param = None

                if param is not None:
                    param['description'] += ln + ' '

                if ln.startswith(':param:'):
                    param = dict()
                    params.append(param)

                    ln = ln.split(':', maxsplit=3)
                    name, type = [x.strip() for x in ln[2].split()]
                    param['name'], param['type'] = name, type
                    param['description'] = ln[3].strip() + ' '

                if not param:
                    if ln:
                        text += ' ' + ln
                    else:
                        text += ' ¶'  

            for param in params:
                param['description'] = param['description'].strip()

            r['text'] = text.rstrip(' ¶')
            r['params'] = params

            return r

        prs = argparse.ArgumentParser(
            description="Runs a bot.",
            epilog = (
                'Bots are typically run in the background, managed by '
                'systemd for example. Alternatively, a bot can be run in '
                'the foreground, such as when debugging.'
            )
        )

        doc = parse_docstring(bot.__init__.__doc__)

        for param in doc['params']:
            help = param['description']
            type = param['type']
            prs.add_argument(
                f'--{param["name"]}', type=int, help=help
            )

        subprss = prs.add_subparsers(
            help = 'The list of bots from which to select', 
            dest = 'bot'
        )

        subprss.required = True

        for b in bots.bots:
            doc = parse_docstring(b.__init__.__doc__)
            subprss = subprss.add_parser(b.__name__, help=doc['text'])

        args = prs.parse_args()

        attrs = [x for x in dir(args) if not x.startswith('_')][1:]

        kwargs = dict()
        for attr in attrs:
            kwargs[attr] = getattr(args, attr)

        def onlog(src, eargs):
            msg = eargs.message
            lvl = eargs.level
            if lvl in ('debug', 'info'):
                stm = sys.stdout
            else:
                stm = sys.stderr

            try:
                stm.write(msg)
            finally:
                stm.flush()

        for b in bots.bots:
            if b.__name__ == args.bot:
                try:
                    with orm.sudo():
                        b = b(onlog=onlog, **kwargs)
                    b()
                except InputError as ex:
                    prs.print_usage()
                    print(f'{__file__.strip("./")}: error: {ex}')
                break
    main()
