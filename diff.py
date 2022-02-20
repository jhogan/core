# vim: set et ts=4 sw=4 fdm=marker

# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2022

from diff_match_patch import diff_match_patch
from entities import entity

# TODO Write test
class diff(entity):
    def __init__(self, data1, data2=None):
        # If data2 is None, data1 is assumed to be a text-based version of the
        # patch
        self._data1 = data1
        self._data2 = data2
        self._ps = None
        self._dmp = None

    @property
    def _diff_match_patch(self):
        if not self._dmp:
            self._dmp = diff_match_patch()
        return self._dmp;

    @property
    def _patches(self):
        if self._ps == None:
            dmp = self._diff_match_patch
            if self._data2:
                diffs = dmp.diff_main(self._data1, self._data2)
                dmp.diff_cleanupSemantic(diffs)
                self._ps = dmp.patch_make(diffs)
            else:
                self._ps = dmp.patch_fromText(self._data1)
        return self._ps

    def applyto(self, data):
        dmp = self._diff_match_patch
        return dmp.patch_apply(self._patches, data)[0]

    def __str__(self):
        dmp = self._diff_match_patch
        return dmp.patch_toText(self._patches) 

