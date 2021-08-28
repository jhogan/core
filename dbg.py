# vim: set et ts=4 sw=4 fdm=marker

# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2021

""" This module provides debugging facilities for developing the core
framework.
"""

# Set conditional break points
from IPython.core.debugger import Tracer; 
import sys
import pdb

# Set conditional break points
def B(x=True):
    """ Breaks execution of the code effectively setting a breakpoint in
    the code::
        
        from dbg import B

        x, y = 1, 2
        print('We are entering the debugger... now.')

        B()

        print('exiting program')
        import sys; sys.exit(0)

    If the above were run, program execution would stop after x and
    y were set and we would enter debug mode (pdb). At this point, we
    could examing and change x and y, navigate the framestack, and do
    all the other things supported by pdb. See the Debugger Commands
    section at https://docs.python.org/3/library/pdb.html for details.

    Invoking pdb with this function is an extremely powerful debugging
    feature and should be used during virtually any nontrivial
    programming session.  Just remember to remove the B() calls before
    merging back to 'main'.

    :param: x bool: If True (default) execution will break. If False
    nothing will happen::
        # Only break into the debugger if x equals 1.
        B(x==1)
        ...
    """
    if x: 
        pdb.Pdb().set_trace(sys._getframe().f_back)
        return

        # NOTE We are probably moving away from IPython. It's not as nice as
        # it sounded. We could offer the option of using it (perhaps by
        # way of a configuration setting) instead if there is interest
        # by developers.
        from IPython.core.debugger import Tracer; 
        Tracer().debugger.set_trace(sys._getframe().f_back)

def PM(ex):
    import pdb
    pdb.post_mortem(ex.__traceback__)
