# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2020

import primative

class stopwatch():
    def __init__(self):
        self._start = None
        self._stop = None
        self.start()

    def start(self):
        self._start = primative.datetime.now()
        self._stop = None

    def stop(self):
        if self._start is None:
            raise ValueError('Call start before stop')

        self._stop = primative.datetime.now()

    @property
    def timedelta(self):
        if self._start is None:
            raise ValueError('Stop watch has not been started')

        stop = self._stop or primative.datetime.now()
        return stop - self._start

    @property
    def milliseconds(self):
        return int(self.timedelta.total_seconds() * 1000)

    def __str__(self):
        return str(self.timedelta)
        
        
        
        
