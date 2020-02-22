# vim: set et ts=4 sw=4 fdm=marker

#######################################################################
# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2020
########################################################################

import entities
class traces(entities.entities):
    def __init__(self, ex, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.exception = ex

        tb = ex.__traceback__
        while tb:
            self += trace(tb)
            tb = tb.tb_next

class trace(entities.entity):
    def __init__(self, tb):
        frame = tb.tb_frame
        co = frame.f_code

        self.lineno = tb.tb_lineno
        self.file = co.co_filename
        self.name = co.co_name

    def __repr__(self):
        args =  (self.file, self.lineno, self.name)
        return 'File "%s" line %s in %s' % args

    def __str__(self):
        return repr(self)
