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
    def __init__(self, iterations=None, verbosity=0, *args, **kwargs):
        """
        An abstract class that represents a bot. 
        
        Concrete bots will inherit from this class to implement their
        specific functions.

        :param: iterations int: The number of iterations to make before
        exiting. Most bots will be in an infinite loop. However, for
        debugging purposes, a developer may want to limit the number of
        iterations to 1.

        :param: verbosity int: The level of status output the bot should
        generate. Status output will be sent to a log file. It will also be
        sent to stdout.
        """
        super().__init__(*args, **kwargs)
        self._iterations = iterations
        self.verbosity = verbosity
        self.name = type(self).__name__
        self._onlog = None
        self._log = config().logs.first
        self._log.onlog += self._log_onlog 

    @property
    def onlog(self):
        if not self._onlog:
            self._onlog = entities.event()
        return self._onlog

    @onlog.setter
    def onlog(self, v):
        self._onlog = v

    def _log_onlog(self, src, eargs):
        self.onlog(src, eargs)

    def log(self, msg, level='info', end='\n'):
        levels = [
            'debug',  'info',      'warning',
            'error',  'critical',  'exception'
        ]

        if level not in levels:
            raise ValueError(f'Invalid level: "{level}"')

        levels = levels[5 - self.verbosity:]

        if level not in levels:
            return

        if level in ('debug', 'info'):
            stm = sys.stdout
        else:
            stm = sys.stderr

        try:
            stm.write(msg + end)
        except AttributeError:
            pass
        else:
            stm.flush()

        getattr(self._log, level)(msg)

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
        self.log('dipatching ...', 'debug')
        while True:
            self.log('.', 'debug', end='')
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
                self.log(
                    f'API Error with dispatch {dis.id} ({ex}) - '
                    'Continuing...', 'exception'
                )
                continue

            # TODO We may want to catch network errors here. For
            # example, if the network is down, we may want to give up
            # for the moment.
            except Exception as ex:
                self.log(
                    f'Error with dispatch {dis.id} ({ex}) - '
                    'Continuing...', 'exception'
                )
                continue

if __name__ == '__main__':
    def main():
        import argparse
        import inspect
        from io import StringIO

        def get_params(doc):
            params = list()
            param = None
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

            for param in params:
                param['description'] = param['description'].strip()

            return params

        prs = argparse.ArgumentParser(
            description="Runs a bot.",
            epilog = (
                'Bots are typically run in the background, managed by '
                'systemd for example. Alternatively, a bot can be run in '
                'the foreground, such as when debugging.'
            )
        )

        params = inspect.signature(bot.__init__).parameters
        docparams = get_params(bot.__init__.__doc__)

        for param in params:
            if param in ('self', 'args', 'kwargs'):
                continue

            docparam = [x for x in docparams if x['name'] == param][0]
            param = params[param]
            help = docparam['description']
            type = docparam['type']
            prs.add_argument(
                f'--{param.name}', type=int, help=help)


        subprss = prs.add_subparsers(help='subcommand help', dest='bot')
        subprss.required = True

        for b in bots.bots:
            subprss = subprss.add_parser(b.__name__)

        args = prs.parse_args()

        attrs = [x for x in dir(args) if not x.startswith('_')][1:]

        kwargs = dict()
        for attr in attrs:
            kwargs[attr] = getattr(args, attr)


        for b in bots.bots:
            if b.__name__ == args.bot:
                b(**kwargs)()
                break
    main()
