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
from configfile import configfile
import logging
from logging import handlers

class log(entity):

    _instance = None

    def __init__(self):
        super().__init__()
        # TODO Add configuration

        ### CONFIG     ###
        serv = 'localhost'
        port = logging.handlers.SYSLOG_UDP_PORT
        addr = '/dev/log'
        addr = (serv, port)
        fac = logging.handlers.SysLogHandler.LOG_LOCAL0
        tag = 'TINC'
        fmt = 'TagName: %(message)s'
        ### END CONFIG ###
        log = logging.getLogger()
        hnd = logging.handlers.SysLogHandler(addr, fac)
        fmt = logging.Formatter()
        log.setLevel(logging.NOTSET)
        hnd.setFormatter(fmt)
        log.addHandler(hnd)
        self._log = log

    @classmethod
    def getinstance(cls):
        if cls._instance == None:
            cls._instance = log()
        return cls._instance

    def debug(self, msg, *args, **kwargs):
        self._log.debug(msg)

    def info(self, msg, *args, **kwargs):
        self._log.info(msg)

    def warning(self, msg, *args, **kwargs):
        self._log.warning(msg)

    def error(self, msg, *args, **kwargs):
        self._log.error(msg)

    def critical(self, msg, *args, **kwargs):
        self._log.critical(msg)


    @property
    def default(self):
        # TODO Add config
        return self
