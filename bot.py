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
        'DEBUG',  'INFO',      'WARNING',
        'ERROR',  'CRITICAL',  'EXCEPTION'
    ]
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
        sent to stdout. Valid values: 5=debug and up, 4=info and up,
        3=warning and up, 2=error and up, 1=critical and up, 0=only
        exceptions. 'debug' and 'info' go to stdout; all other output
        goes to stderr.
        """
        super().__init__(*args, **kwargs)
        self._onlog = None

        self._iterations = iterations
        self.verbosity = verbosity
        self.name = type(self).__name__

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

    @property
    def level(self):
        return self.Levels[5 - self.verbosity:][0]

    @property
    def levels(self):
        return self.Levels[5 - self.verbosity:]

    def debug(self, msg, end='\n'):
        f = inspect.stack()[0].function.upper()
        self._logger(msg=msg, level=f, end=end)

    def info(self, msg, end='\n'):
        f = inspect.stack()[0].function.upper()
        self._logger(msg=msg, level=f, end=end)

    def exception(self, msg, end='\n'):
        f = inspect.stack()[0].function.upper()
        self._logger(msg=msg, level=f, end=end)

    def _logger(self, msg, level='info', end='\n'):
        if level not in self.Levels:
            raise ValueError(f'Invalid level: "{level}"')

        '''
        levels = levels[5 - self.verbosity:]

        if level not in levels:
            return
        '''

        getattr(self._log, level.lower())(msg + end)

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
    def __init__(self, onlog=None, *args, **kwargs):
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

        self._log = config().logs.first
        self._log._logger.setLevel(self.level)
        self._log.onlog += self._log_onlog 

        if onlog:
            self.onlog += onlog

        self.info(f'{type(self).__name__} is alive')
        self.info(f'Log levels: {" | ".join(self.levels)}')

    def __call__(self, exsimulate=False):
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

        params = inspect.signature(bot.__init__).parameters
        doc = parse_docstring(bot.__init__.__doc__)

        for param in params:
            if param in ('self', 'args', 'kwargs'):
                continue

            param = [x for x in doc['params'] if x['name'] == param][0]
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
            rec = eargs.record
            msg = rec.message
            lvl = rec.levelname.lower()
            if lvl in ('debug', 'info'):
                stm = sys.stdout
            else:
                stm = sys.stderr

            try:
                stm.write(msg)
            except AttributeError:
                pass
            else:
                stm.flush()


        for b in bots.bots:
            if b.__name__ == args.bot:
                b = b(onlog=onlog, **kwargs)
                b()
                break
    main()
