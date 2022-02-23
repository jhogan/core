# vim: set et ts=4 sw=4 fdm=marker

# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2022

""" This module has classes that handle logging to files - typically
syslog (technically a service).

Most logging of data in Core uses database tables (see ``apriori.log``).
However, when there is an issue connecting to the database, or some
other such abnormality, we can use these logging classes to log straight
to syslogd.
"""

# TODO Add Tests
from dbg import B
from logging import handlers, Handler
import config
import entities
import logging

class log(entities.entity):
    def __init__(self, *args, **kwargs):
        """ Set up the log class.
        """
        super().__init__(*args, **kwargs)

        # Get syslog config data
        cfg = config.config().log

        # NOTE .getLogger() always returns the same 'logger'
        self._logger = logging.getLogger()

        # Create the onlog event
        self.onlog = entities.event()

        # No handlers means we haven't set the logger up
        if len(self._logger.handlers):
            # Clear the logger handler
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

    # TODO These should probably be prefixed by a _ to indicate they are
    # private.
    class callbackhandler(logging.Handler):
        """ A subclass of Handler.
        """
        def __init__(self, callback):
            super().__init__()
            self.callback = callback
            
        def emit(self, rec):
            self.callback(rec)

    def callback(self, rec):
        """ Ultimately invoked by Python's logging classes to indicate a
        log has been written. We can use this event to trigger the
        ``log.onlog`` event so handlers in Core can be subscribed and
        made aware of logging events.
        """
        eargs = addlogeventargs(rec)
        self.onlog(self, eargs)

    # Use properties to expose the direct logger methods. Doings so
    # allows %(lineno)d LogRecord attribute to display the line number
    # where the method was actually invoked.
    @property
    def debug(self):
        """ Return the `debug` method. """
        return self._logger.debug

    @property
    def info(self):
        """ Return the `info` method. """
        return self._logger.info

    @property
    def warning(self):
        """ Return the `warning` method. """
        return self._logger.warning

    @property
    def error(self):
        """ Return the `error` method. """
        return self._logger.error

    @property
    def critical(self):
        """ Return the `critical` method. """
        return self._logger.critical

    @property
    def exception(self):
        """ Return the `exception` method. """
        return self._logger.exception

class addlogeventargs(entities.eventargs):
    """ An eventsarg class used to pass the log record to handlers that
    are subscribed to the onlog event.
    """
    def __init__(self, rec):
        """ Create the eventarg.
        """
        self.record = rec

# When the ``logs`` module is imported, we instatiate the ``log`` class,
# then set its ``logger`` object at the module level. With that, we set
# the logging methods at the module level, as well. That way, we can
# call the logging function directly off the module:
#
#     import log
#     log.debug('derp')
#
_logger = log()._logger

debug      =  _logger.debug
info       =  _logger.info
warning    =  _logger.warning
error      =  _logger.error
critical   =  _logger.critical
exception  =  _logger.exception

