# vim: set et ts=4 sw=4 fdm=marker
"""
MIT License

Copyright (c) 2016 Jesse Hogan

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
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
        self._logger = logging.getLogger()
        fmt = tag + fmt
        fmt = logging.Formatter(fmt)
        self._logger.setLevel(getattr(logging, lvl))

        hnd = logging.handlers.SysLogHandler(addr, fac)
        hnd.setFormatter(fmt)
        self._logger.addHandler(hnd)

        hnd = log.callbackhandler(self.callback)
        self._logger.addHandler(hnd)

        self.onlog = event()

    def _self_onlog(self, src, eargs):
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

    # Use properties to expose the direct logger methods. Doings so allows
    # %(lineno)d LogRecord attribute to display the line number where the
    # method was actually invoked.
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

