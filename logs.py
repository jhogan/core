# vim: set et ts=4 sw=4 fdm=marker

# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2021

# TODO Add Tests
from entities import *
from pdb import set_trace; B=set_trace
import logging
from logging import handlers, Handler

class logs(entities):
    _instance = None

    def __init__(self):
        super().__init__()

    @classmethod
    def getinstance(cls):
        if cls._instance == None:
            cls._instance = logs()
        return cls._instance

    @property
    def default(self):
        return self.first

class log(entity):
    def __init__(self, addr, fac, tag, fmt, lvl):
        super().__init__()

        # NOTE .getLogger() always returns the same 'logger'
        self._logger = logging.getLogger()

        self.onlog = event()

        # No handlers means we haven't set the logger up
        if not len(self._logger.handlers):
            fmt = tag + fmt
            fmt = logging.Formatter(fmt)
            self._logger.setLevel(getattr(logging, lvl))

            hnd = logging.handlers.SysLogHandler(addr, fac)
            hnd.setFormatter(fmt)
            self._logger.addHandler(hnd)

            hnd = log.callbackhandler(self.callback)
            self._logger.addHandler(hnd)

    def _self_onlog(self, src, eargs):
        # TODO Is this dead code?
        pass

    class callbackhandler(Handler):
        def __init__(self, callback):
            super().__init__()
            self.callback = callback
            
        def emit(self, rec):
            self.callback(rec)

    def callback(self, rec):
        eargs = log.addlogeventargs(rec)
        self.onlog(self, eargs)

    class addlogeventargs(eventargs):
        def __init__(self, rec):
            self.record = rec

    # Use properties to expose the direct logger methods. Doings so
    # allows %(lineno)d LogRecord attribute to display the line number
    # where the method was actually invoked.
    @property
    def debug(self):
        return self._logger.debug

    @property
    def info(self):
        return self._logger.info

    @property
    def warning(self):
        return self._logger.warning

    @property
    def error(self):
        return self._logger.error

    @property
    def critical(self):
        return self._logger.critical

    @property
    def exception(self):
        return self._logger.exception

    @staticmethod
    def create(d):
        addr = d['address']
        fac = getattr(logging.handlers.SysLogHandler, d['facility'])
        tag = d['tag']
        fmt = d['format']
        lvl = d['level']
        return log(addr, fac, tag, fmt, lvl)

