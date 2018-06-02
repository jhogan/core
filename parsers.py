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
from html.parser import HTMLParser
from pdb import set_trace; B=set_trace
from itertools import zip_longest

class htmlparser(HTMLParser):
    def __init__(self, html=None):
        super().__init__()
        self._html = html
        self._starttags = []
        self._endtags = []

    def demandbalance(self):
        self.feed(self._html)
        starttags = self._starttags
        endtags = self._endtags
        for tags in zip_longest(starttags, reversed(endtags), fillvalue=None):
            starttag, endtag = tags
            if starttag != endtag:
                if starttag == None:
                    msg = 'No start tag found for end tag <' + endtag + '>'
                elif endtag == None:
                    msg = 'No end tag found for start tag <' + starttag + '>'
                else:
                    msg = 'Start tag <' + starttag + '> doesn\'t match end tag <' + endtag + '>'
                raise Exception(msg)

    def handle_starttag(self, tag, attrs):
        self._starttags.append(tag)

    def handle_endtag(self, tag):
        self._endtags.append(tag)

