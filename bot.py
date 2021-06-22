#!/usr/bin/python3
# vim: set et ts=4 sw=4 fdm=marker

########################################################################
# Copyright (C) Jesse Hogan - All Rights Reserved                      #
# Unauthorized copying of this file, via any medium is strictly        #
# prohibited                                                           #
# Proprietary and confidential                                         #
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2021                 #
########################################################################

""" The bot.py module encapsulates the logic for all bot activity. 

Bots are autonomous programs typically run as background process.

All bots inherit from the ``bot`` class. Currently, one class called
``sendbot`` has been implemented. It is intended to run as a background
process which monitors the message dispatch queue. When a dispatch is
placed in the queue, sendbot picks it up and sends it to the
``dispatcher`` effectively sending the message out to the recipients.

At the moment, other bots are planned, such as a sysadmin bot which
will monitor production and development environments, and a
configuration manager bot which will automate the task of setting up
environments and deploying code to production.

A ``bot`` is an ``ecommerce.agents`` and therefore ultimately derives
from ``party.party``. Bots have their own user account (bot.user) under
which most of their activities are run.

Bots log their activity to the database via the apriori.log entity. The
``verbosity`` argument controls how much is logged.

Bots are intended to be run as their own process, typically through
systemd, so they are invoked like any other program, e.g., 

    ./bot.py --iterations 1 --verbosity 5 sendbot

Here, the bot.py binary is being run. At the end, we can see that
'sendbot' is being run. The global argument --iteration is set to 1,
meaning the sendbot will check and process the dispatch queue 1 time and
then exit. This is typical for debugging purposes; in production we
would not set iterations in order that sendobt iterates continuously.
The verbosity is set to 5 because we want to see all the output. In
production, that much logging may be unnecessary. Note that when
logging, the bot will print log messages to the screen and record them
to the database at the same time.
"""

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
    """ An eventargs subclass to capture a message and log level of a
    log event.
    """
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
    """ Bots are autonomous programs typically run as background
    process. All bots inherit from the ``bot`` class. 

    A ``bot`` is an ``ecommerce.agents`` and therefore ultimately derives
    from ``party.party``. Bots have their own user account (bot.user) under
    which most of their activities are run.

    Bots log their activity to the database via the apriori.log entity. The
    ``verbosity`` argument controls how much is logged.

    Bots are intended to be run as their own process, typically through
    systemd, so they are invoked like any other program, e.g., 

        ./bot.py --iterations 1 --verbosity 5 sendbot
    """

    # Log levels
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

        # The event handler for the onlog event
        onlog = kwargs.pop('onlog', None)

        # The number of iterations.
        iterations = kwargs.pop('iterations', None)

        # The logging verbosity
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
        """ The collection of logs for this bot. 
        
        Note that, when called, the logs collection will not contain
        prior logs, but will be ready for additional logs to be
        appended. This is intended to prevent a huge but unnecessary
        load of logs from the database.
        """
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
        """ !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        The user object that the bot will run under. This user will
        typically have a hardcoded id.
        !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        """
        
        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # Treat cls as an instance of bot so ``user`` can be used as
        # both a @classproperty and a "@staticproperty" at the same
        # time.
        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        if isinstance(cls, type):
            self = None
        else:
            self, cls = cls, type(cls)

        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # Bot is abstract. Make sure we are only calling user if we are
        # a concrete class.
        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        if cls is bot:
            raise NotImplementedError(
                'user is only available to concrete classes'
            )

        if (not hasattr(cls, '_user')) or cls._user is None:
            if not hasattr(cls, 'UserId'):
                raise ValueError('bot must have UserId constant set')

            id = uuid.UUID(cls.UserId)

            # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            # Create in (or retrieve from) the database as root and as
            # the Carapacian proprietor.
            # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            with orm.sudo(), orm.proprietor(party.company.carapacian):
                try:
                    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                    # Retrieve
                    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                    cls._user = ecommerce.user(id)

                except db.RecordNotFoundError:
                    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                    # Ensure self is an instance of cls
                    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                    if not self:
                        self = cls()

                    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                    # Create
                    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                    cls._user = ecommerce.user(
                        id   = id,
                        name = cls.__name__,
                        party  = self,
                    )

                    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                    # Save
                    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                    cls._user.save()

        return cls._user

    @property
    def onbeforeiteration(self):
        """ The event that is raised before a bot iterates.
        """
        if not hasattr(self, '_onbeforeiteration'):
            self._onbeforeiteration = entities.event()

        return self._onbeforeiteration

    @onbeforeiteration.setter
    def onbeforeiteration(self, v):
        self._onbeforeiteration = v

    @property
    def onafteriteration(self):
        """ The event that is raised after a bot iterates.
        """
        if not hasattr(self, '_onafteriteration'):
            self._onafteriteration = entities.event()

        return self._onafteriteration

    @onbeforeiteration.setter
    def onbeforeiteration(self, v):
        self._onbeforeiteration = v

    @property
    def onlog(self):
        """ The event that is raised when a bot records a log message.
        """
        if not self._onlog:
            self._onlog = entities.event()
        return self._onlog

    @onlog.setter
    def onlog(self, v):
        self._onlog = v

    @property
    def level(self):
        """ The level of logging verbosity the bot as been set to.
        """
        return self.Levels[5 - self.verbosity:][0]

    @property
    def levels(self):
        """ Returns a list of logging levels that the bot has been
        set to given its ``verbosity`` property.
        """
        if self.verbosity is None:
            return list()

        return self.Levels[5 - self.verbosity:]

    def debug(self, msg, end='\n'):
        """ Log a debug-level message.
        """
        f = inspect.stack()[0].function
        self._log(msg=msg, lvl=f, end=end)

    def info(self, msg, end='\n'):
        """ Log a info-level message.
        """
        f = inspect.stack()[0].function
        self._log(msg=msg, lvl=f, end=end)

    def warning(self, msg, end='\n'):
        """ Log a warning-level message.
        """
        f = inspect.stack()[0].function
        self._log(msg=msg, lvl=f, end=end)

    def error(self, msg, end='\n'):
        """ Log a error-level message.
        """
        f = inspect.stack()[0].function
        self._log(msg=msg, lvl=f, end=end)

    def critical(self, msg, end='\n'):
        """ Log a critical-level message.
        """
        f = inspect.stack()[0].function
        self._log(msg=msg, lvl=f, end=end)

    def exception(self, msg, end='\n'):
        """ Log a except-level message.
        """
        f = inspect.stack()[0].function
        self._log(msg=msg, lvl=f, end=end)

    def _log(self, msg, lvl='info', end='\n'):
        """ Records a log entry to apriori.log.
        """

        if lvl not in self.Levels:
            raise ValueError(f'Invalid level: "{lvl}"')

        # Get the list of levels that the bot should log for
        lvls = self.levels

        # Abort if the log level should be ignored (see bot.verbosity)
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
            # Raise the onlog event. This is typically handled by
            # something that will print the message to a screen.
            eargs = addlogeventargs(msg=msg, lvl=lvl)
            self.onlog(self, eargs)

    # TODO Remove: Dead code
    @orm.attr(int)
    def pid(self):
        return os.getpid()

    @property
    def iterations(self):
        """ The number of iterations a bot should do before completion.
        In productions, bots may iterate indefinately. In testing, only
        a single iteration may be required.
        """
        return self._iterations

    @property
    def verbosity(self):
        """ The verbosity for logging.
        """
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
        """ Implement __call__ to allow bots to be started::

            # Instatiate sendbot
            b = sendbot()
            
            # Start iterating sendbot
            b()  # Same as b.__call__

        Principles, such as the bot's user accounts, a proprietor and
        the bot itself are created in the database here if they have not
        already been. The concrete bot's _call method will be called
        iteratively to invoke its functionality.

        :param: exsimulate bool: A flag that can be set to True in
        certain tests to indicate a desire to break out of a simulated
        test environment, such as one provided by a third party API.
        """
        cara = party.company.carapacian

        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # Set the ORM's owner to the bot's user object. We want all
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
            # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            # Use sudo because setting the proprietor may require
            # retrieving the current proprietor for comparison. Since
            # the logged-in user is the bot, and bots can't retrieve
            # carapacian (at least, not at the moment), we should become
            # sudo. 
            # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            orm.security().proprietor = cara

        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # Override accessibilty controls because setting proprietor
        # causes the current proprietor to be loaded, which causes
        # party.retrievability to be called, which, itself causes
        # proprietor to be loaded leading to infinite recursion.
        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        with orm.override():
            try:
                self.proprietor = cara
            except db.RecordNotFoundError as ex:
                # NOTE:d8938682 that in test environments, this error is
                # often caused by the the bot's record in the bots.bots
                # subtable not having corresponding records in the
                # supertables - usually party.parties. 
                # This is due to the fact that tests sometimes delete
                # table data, but end up leaving the database in an
                # inconsistent state.  You may want to delete all bots
                # record and all corresponding records up the
                # inheritance tree to correct this. Tables to consider:
                #
                #   bot_sendbots <the subtable>
                #   bot_bots
                #   ecommerce_agents
                #   party_parties
                # )
                raise db.RecordNotFoundError(
                    'See NOTE:d8938682' # See comment above
                ) from ex

        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # Ensure the bot itself is in the database and that root is the
        # owner.
        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        with orm.sudo():
            self.save()

        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # Set the user to the bot's user
        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        with orm.su(self.user):
            # Log some initial messages
            self.info(f'{type(self).__name__} is alive')
            self.info(f'Log levels: {" | ".join(self.levels)}')

            if self.iterations is None:
                # Infinite generator
                iter = itertools.count()
            else:
                iter = range(self.iterations)

            # Iterate for as many times as defined by iter (see above).
            # self.iteration is a property that can be used by the
            # subclass to see how many iterations have been done so far.
            for self.iteration in iter:

                # Raise the onbeforeiteration event
                eargs = iterationeventargs(
                    self.iteration + 1, self.iterations
                )

                self.onbeforeiteration(self, eargs)

                # Break if an event handler for onbeforeiteration wants
                # the bot to stop
                if eargs.cancel:
                    break

                try:
                    # Call the subclass's (the concrete bot's) _call
                    # method to begin iteration.
                    self._call(exsimulate=exsimulate)
                finally:
                    # Raise the onafteriteration event
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
    # TODO Use UUID classes here instead of strings
    Id      =  'fdcf21b2-dc0b-40ef-934f-ffbca49c915c'
    UserId  =  'cfd67652-de34-4ffc-99a0-5acd29ff89d4'

    _isin__new__ = False
    def __new__(cls, *args, **kwargs):
        # TODO Much of this logic is to implement a data-singleton
        # pattern, and will likely be of universal interest. When the
        # time is right, we can consolidate this logic to make
        # implementing the data-singleton pattern easy.

        # Make sure that if something tries to instantiate sendbot with
        # a uuid that is not sendbot's uuid, then a RecordNotFoundError
        # is thrown.
        try:
            id = args[0]
        except IndexError:
            pass
        else:
            if isinstance(id, uuid.UUID):
                if id != uuid.UUID(cls.Id):
                    raise db.RecordNotFoundError(
                        'Record not found for sendbot'
                    )

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
                with orm.proprietor(cara), orm.sudo():

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
