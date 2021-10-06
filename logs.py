# vim: set et ts=4 sw=4 fdm=marker

# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2021

# TODO Add Tests
from dbg import B
import logging
from logging import handlers, Handler
import config
import entities

class log(entities.entity):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        cfg = config.config().log

        # NOTE .getLogger() always returns the same 'logger'
        self._logger = logging.getLogger()

        self.onlog = entities.event()

        # No handlers means we haven't set the logger up
        if len(self._logger.handlers):
            self._logger.handlers.pop()
        else:
            # Set up formatter
            fmt = cfg['tag'] + cfg['fmt']
            fmt = logging.Formatter(fmt)

            # Set log level
            self._logger.setLevel(getattr(logging, cfg['lvl']))

            # Setup syslog handler
            hnd = logging.handlers.SysLogHandler(cfg['addr'], cfg['fac'])
            hnd.setFormatter(fmt)
            self._logger.addHandler(hnd)

        # Handle callback
        hnd = log.callbackhandler(self.callback)
        self._logger.addHandler(hnd)

    def _self_onlog(self, src, eargs):
        B()
        # TODO Is this dead code?
        pass

    # TODO These should probably be prefixed by a _ to indicate they are
    # private.
    class callbackhandler(Handler):
        def __init__(self, callback):
            super().__init__()
            self.callback = callback
            
        def emit(self, rec):
            self.callback(rec)

    def callback(self, rec):
        eargs = addlogeventargs(rec)
        self.onlog(self, eargs)

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

class addlogeventargs(entities.eventargs):
    def __init__(self, rec):
        self.record = rec

_logger = log()._logger

debug      =  _logger.debug
info       =  _logger.info
warning    =  _logger.warning
error      =  _logger.error
critical   =  _logger.critical
exception  =  _logger.exception

