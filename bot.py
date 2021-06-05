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
from func import B, enumerate
import io
import apriori
import argparse
import db
import ecommerce
import entities
import inspect
import message
import orm
import os
import party
import sys
import third
import time
import uuid
import itertools

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
        iterations to only a few.

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
        self.iteration = None

    @orm.attr(apriori.logs)
    def logs(self):
        # HACK:8210b80c We want ``bot`` to have a ``logs`` constituent
        # that we can add to but we don't want to load every log the bot
        # has ever recorded. So set .isloaded = True to prevent that. A
        # better solution to this problem is discussed in a TODO with
        # the 8210b80c identifier.

        if type(self) is not bot:
            b = self
            while type(b) is not bot:
                b = b.orm.super
            return b.logs

        if not hasattr(self, '_logs'):
            map = self.orm.mappings['logs']

            map.value = apriori.logs('botid', self.id)

            # Disallow loading
            map.value.orm.isloaded = True

            def onadd(src, eargs):
                eargs.entity.bot = self

            map.value.onadd += onadd

            self._logs = map.value

        return self._logs

    @classproperty
    def user(cls):
        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        
        if isinstance(cls, type):
            self = None
        else:
            self, cls = cls, type(cls)

        if cls is bot:
            raise NotImplementedError(
                'user is only available to concrete classes'
            )

        if (not hasattr(cls, '_user')) or cls._user is None:
            if not hasattr(cls, 'UserId'):
                raise ValueError('bot must have UserId constant set')

            id = uuid.UUID(cls.UserId)

            with orm.sudo(), orm.proprietor(party.company.carapacian):
                try:
                    cls._user = ecommerce.user(id)
                except db.RecordNotFoundError:
                    if not self:
                        self = cls()

                    cls._user = ecommerce.user(
                        id   = id,
                        name = cls.__name__,
                        party  = self,
                    )
                    cls._user.save()

        return cls._user

    @property
    def onbeforeiteration(self):
        if not hasattr(self, '_onbeforeiteration'):
            self._onbeforeiteration = entities.event()

        return self._onbeforeiteration

    @onbeforeiteration.setter
    def onbeforeiteration(self, v):
        self._onbeforeiteration = v

    @property
    def onafteriteration(self):
        if not hasattr(self, '_onafteriteration'):
            self._onafteriteration = entities.event()

        return self._onafteriteration

    @onbeforeiteration.setter
    def onbeforeiteration(self, v):
        self._onbeforeiteration = v

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

        msg += end

        try:
            # Sometimes, empty debug messages will be used cause a line
            # feed. No need to log those. Logs with empty message
            # attributes are invalid anyway.
            if msg.strip():
                log = apriori.log(
                    message = msg,
                    logtype = apriori.logtype(name=lvl)
                )

                self.logs += log

                self.logs.save()
        finally:
            # In case there is a database/ORM issue, we can raise
            # the onlog event which will probably be handle something
            # that prints to a device like stdout our a file.
            eargs = addlogeventargs(msg=msg, lvl=lvl)
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
        with orm.sudo():
            # Use sudo because setting the proprietor may require
            # retriving the current proprietor for comparison. Since the
            # loggedi in user is the bot, and bots can't retrieve
            # carapacian (at least, not at the moment), we should become
            # sudo. 
            orm.security().proprietor = cara

        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # Set the bot's proprietor to the Carapacian company. 
        #
        # (Override accessibilty controls because setting proprietor
        # causes the current proprietor to be loaded, which causes
        # party.retrievability to be called, which, itself caluse
        # proprietor to beloaded leading to infinite recursion.)
        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        with orm.override():
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

            if self.iterations is None:
                # Infinite generator
                iter = itertools.count()
            else:
                iter = range(self.iterations)

            for self.iteration in iter:
                eargs = iterationeventargs(
                    self.iteration + 1, self.iterations
                )

                self.onbeforeiteration(self, eargs)

                if eargs.cancel:
                    break

                try:
                    self._call(exsimulate=exsimulate)
                finally:
                    self.onafteriteration(self, eargs)

    @property
    def retrievability(self):
        vs = orm.violations()

        if type(self) is bot:
            usr = self.orm.leaf.user
        else:
            usr = self.user

        if orm.security().user.id != usr.id:
            vs += 'Bots can only be accessed by their users'

        return vs

    @property
    def updatability(self):
        vs = super().updatability()

        b = self
        while b:
            try:
                usr = b.user
            except NotImplementedError:
                pass
            else:
                if usr.id == orm.security().user.id:
                    break

            b = b.orm.sub
        else:
            vs += 'Current user cannot update bot'

        return vs

class sendbots(bots):
    pass

class sendbot(bot):
    Id      =  'fdcf21b2-dc0b-40ef-934f-ffbca49c915c'
    UserId  =  'cfd67652-de34-4ffc-99a0-5acd29ff89d4'

    _isin__new__ = False
    def __new__(cls, *args, **kwargs):
        
        # TODO Much of this logic is to implement a data-singleton
        # pattern, and will likely be of universal interest. When the
        # time is right, we can consolidate this logic to make
        # implementing the data-singleton pattern easy.

        ''' Protect against infinite recursion. '''
        # First, ensure that this instantiation isn't a result of a
        # prior instantiation. Without this check, instantiations end up
        # being infinitly recursive (see orm.leaf).

        # For each frame in the stack
        for i, fi in enumerate(inspect.stack()):
            # The first and second frame will be this method, and are
            # therefore not indicative of a prior instantiation.
            if i.first or i.second:
                continue

            # Get the frame object from the FrameInfo object
            frm = fi.frame

            try:
                # Dose the frame contain the magic constant __class__
                cls1 = frm.f_locals['__class__']
            except KeyError:
                # If not, continue to the next frame
                continue
            else:
                # We are here because the frame contains the magic
                # keyword __class__.

                # Is the frame's class the same as this class
                if cls is cls1:
                    # Is the frame's function name __new__
                    if fi.function == '__new__':
                        raise entities.InProgressError(
                            'Refusing to instatiate because '
                            'instantiation is already in progress.'
                        )

        try:
            cls._isin__new__ = True
            try:
                kwargs['from__new__']
            except KeyError:
                id = uuid.UUID(cls.Id)

                cara = party.company.carapacian
                with orm.proprietor(cara):

                    try:
                        kwargs['from__new__'] = None
                        b = sendbot(id, **kwargs)
                    except db.RecordNotFoundError:
                        b = sendbot(**kwargs)
                        b.id = id
                        b.name = cls.__name__
                        b.save()
            else:
                return super(sendbot, cls).__new__(cls)

            return b
        finally:
            cls._isin__new__ = False

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
        # TODO The docstring should be at the class level
        # TODO Do we need to delet this contructor

        try:
            kwargs.pop('from__new__')
        except KeyError:
            pass
        else:
            super().__init__(*args, **kwargs)

    def _call(self, exsimulate=False):
        if self.iteration == 0:
            self.info('dispatching:')

        if self.iteration % 80 == 0:
            self.debug('')

        self.debug('.', end='')

        self._dispatch(exsimulate=exsimulate)

        if self.iteration != self.iterations:
            time.sleep(1)

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

class iterationeventargs(entities.eventargs):
    def __init__(self, iter, of):
        self.iteration = iter
        self.of = of
        self.cancel = False

class InputError(ValueError):
    pass

class TerminateError(Exception):
    def __init__(self, st, msg):
        super().__init__(msg)
        self.status = st

class argumentparser(argparse.ArgumentParser):
    def exit(self, *args, **kwargs):
        if __name__ == '__main__':
            super().exit(*args, **kwargs)
        else:
            st, msg = args
            raise TerminateError(msg=msg, st=st)

    def error(self, *args, **kwargs):
        if __name__ == '__main__':
            super().error(*args, **kwargs)
        else:
            message, = args
            args = {'prog': self.prog, 'message': message}
            msg = ('%(prog)s: error: %(message)s\n') % args
            raise self.exit(2, msg)

class panel:
    def __init__(self, args=None, dodisplay=True):
        # Command line arguments
        self._args = args

        # Result of argparse
        self._cli = None

        # The instatiated bot 
        self._bot = None

        if dodisplay:
            self.display = panel._display(self)
        else:
            self.display = None

    def print(self, msg, end=None, stm=sys.stdout):
        if end:
            msg += end

        if self.display:
            self.display.print(msg, stm=stm)

        self.onafterprint(self, panel.printeventargs(msg))

    def __call__(self):
        # Override just long enough to ensure that, when called,
        # root will be created if it doesn't already exist.
        with orm.override():
            ecommerce.users.root

        self.bot()

    @property
    def _arguments(self):
        if not self._cli:
            doc = self._parse(bot.__init__.__doc__)
            prs = argumentparser(
                description="Runs a bot.",
                epilog = (
                    'Bots are typically run in the background, managed by '
                    'systemd for example. Alternatively, a bot can be run in '
                    'the foreground, such as when debugging.'
                )
            )

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
                doc = self._parse(b.__init__.__doc__)
                subprss = subprss.add_parser(b.__name__, help=doc['text'])

            # prs.parse_args() needs the arguments in a list()
            if self._args:
                args = self._args.split()
            else:
                args = None

            self._cli = prs.parse_args(args=args)

        return self._cli

    @property
    def _kwargs(self):
        args = self._arguments

        attrs = [x for x in dir(args) if not x.startswith('_')][1:]

        kwargs = dict()
        for attr in attrs:
            kwargs[attr] = getattr(args, attr)

        return kwargs

    @property
    def bot(self):
        if not self._bot:
            args = self._arguments
            for b in bots.bots:
                if b.__name__ == args.bot:
                    try:
                        with orm.sudo():
                            self._bot = b(
                                onlog=self.onlog, **self._kwargs
                            )
                    except InputError as ex:
                        self.print(prs.format_usage())
                        self.print(f'{__file__.strip("./")}: error: {ex}')
                    break
        return self._bot

    @staticmethod
    def _parse(doc):
        r = dict()
        params = list()
        param = None
        text= str()
        for ln in io.StringIO(doc):
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

    @property
    def onafterprint(self):
        if not hasattr(self, '_onafterprint'):
            self._onafterprint = entities.event()
        return self._onafterprint

    @onafterprint.setter
    def onafterprint(self, v):
        self._onafterprint = v

    def onlog(self, src, eargs):
        msg = eargs.message
        lvl = eargs.level
        if lvl in ('debug', 'info'):
            stm = sys.stdout
        else:
            stm = sys.stderr

        self.print(msg, stm=stm)

    class _display:
        def __init__(self, pnl):
            self.messages = list()
            self.panel = pnl

        def print(self, msg, stm=sys.stdout):
            self.messages.append(msg.strip())
            stm.write(msg)
            stm.flush()

    class printeventargs(entities.eventargs):
        def __init__(self, msg):
            self.message = msg

if __name__ == '__main__':
    pnl = panel()
    pnl()
