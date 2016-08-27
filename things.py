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

class things(object):
    def __init__(self):
        self.clear()

    def clear(self):
        self.list=[]

    def __iter__(self):
        for t in self.list:
            yield t

    def append(self, t):
        self.list.append(t)

    def __iadd__(self, t):
        self.append(t)
        return self

    @property
    def count(self):
        return len(self.list)

    @property
    def isempty(self):
        return self.count == 0

    def __str__(self):
        if not self.isempty:
            r=''
            for t in self:
                r += str(t) + "\n"
            return r
        else:
            return "No failures to report.\n"

class thing(object):
    def __init__(self):
        pass


