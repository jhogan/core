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
import cProfile
import pdb
import pstats
import sys

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
    """ This function can be called from within an exception to take
    your pdb debugger to the source of an exception::

        try:
            problematic()
        except Exception as ex:
            # XXX There is some sort of issue with the function
            # `problematic` so I am going to see exactly where the
            # exception is being raised:
            import dbg
            dbg.PM(ex)

    This is just a thin wrapper around pdb.post_mortem. Here is its
    documentation::

        pdb.post_mortem(traceback=None)

            Enter post-mortem debugging of the given traceback object. If no
            traceback is given, it uses the one of the exception that is
            currently being handled (an exception must be being handled if
            the default is to be used).
    """
    import pdb
    pdb.post_mortem(ex.__traceback__)

def profile(callable):
    """ Run callable under Python's builtin deterministic profiler
    (cProfile), and print the top 10 most time-consuming methods
    used during the invocation of callable. 

    Calling this method is intended for debugging performance
    issues. Calls to this method shouldn't be committed to source
    control.

    As a convenience, the top 10 are printed to stdout. Then the program
    breaks into the debugger so the user is able to analyse the
    pstats.Stats object further.

    :param: callable callable: The callable to be profiled.
    """

    # Profile the callable
    with cProfile.Profile() as p:
        callable()

    # Create a Stats object and sort the results by cumulitive time.
    # This puts the most time consuming methods at the top of the
    # list when printing out.
    p = pstats.Stats(p)
    p.strip_dirs()
    p.sort_stats(pstats.SortKey.CUMULATIVE)
    p.print_stats(10)

    B()

PR = profile
