# vim: set et ts=4 sw=4 fdm=marker

#######################################################################
# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2021
########################################################################

""" This module contains classes that make it easier to work with
exceptions and their related objects such as tracebacks.
"""
import entities
class traces(entities.entities):
    """ Contains a collection of ``trace`` objects. 
    """
    def __init__(self, ex, *args, **kwargs):
        """ Creates the traces collection.

        :param: ex Exception: The exception which contains the
        __traceback__ that will be used to build the collection.
        """
        super().__init__(*args, **kwargs)

        self.exception = ex

        # Go through each trackback and create a ``trace`` object for
        # each one.
        tb = ex.__traceback__
        while tb:
            self += trace(tb)
            tb = tb.tb_next

class trace(entities.entity):
    """ Represents a trackback object.
    """
    def __init__(self, tb):
        """ Create the ``trace`` object.

        :param: tb trackback: The trackback object that this object
        encapsulates.
        """
        frame = tb.tb_frame
        co = frame.f_code

        self.lineno = tb.tb_lineno
        self.file = co.co_filename
        self.name = co.co_name

    def __repr__(self):
        """ Returns a string representation of the trace.
        """
        args =  (self.file, self.lineno, self.name)
        return 'File "%s" line %s in %s' % args

    def __str__(self):
        """ Returns a string representation of the trace.
        """
        return repr(self)
