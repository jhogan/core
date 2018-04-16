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
from diff_match_patch import diff_match_patch
from entities import entity
from pdb import set_trace; B=set_trace

# TODO Write test
class diff(entity):
    def __init__(self, data1, data2):
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
            diffs = dmp.diff_main(self._data1, self._data2)
            dmp.diff_cleanupSemantic(diffs)
            self._ps = dmp.patch_make(diffs)
        return self._ps

    def apply(self, data):
        return patch_apply(self._patches, data)[0]

    def __str__(self):
        dmp = self._diff_match_patch
        return dmp.patch_toText(self._patches) 

