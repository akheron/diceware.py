#!/usr/bin/env python

"""Diceware passphrase generator
Copyright (c) 2008 Petri Lehtinen <petri@digip.org>

Diceware passphrase generator generates passphrases by reading random
data from the operating system random number generator and using it to
index the Diceware word list, supplied by user or automatically
downloaded from the Diceware web page. For more information on
Diceware, see the Diceware web page:
http://world.std.com/~reinhold/diceware.html

"""

__license__ = """
Permission is hereby granted, free of charge, to any person
obtaining a copy of this software and associated documentation files
(the "Software"), to deal in the Software without restriction,
including without limitation the rights to use, copy, modify, merge,
publish, distribute, sublicense, and/or sell copies of the Software,
and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

"""

from math import log, ceil
from optparse import OptionParser
import time
import sys
import os
import os.path
import urllib


SPECIAL_CHARS = "~!#$%^&*()-=+[]\{}:;\"'<>?/0123456789"

WORD_LIST_URLS = {
    "en": "http://world.std.com/~reinhold/diceware.wordlist.asc",
    "fi": "http://www.iki.fi/kaip/noppaware/noppaware.txt",
    "it": "http://www.taringamberini.com/download/diceware_it_IT/" +
          "word_list_diceware_in_italiano.txt",
    "pl": "http://drfugazi.eu.org/download/dicelist-pl.txt.asc",
    "se": "http://x42.com/diceware/diceware-sv.txt",
    "tr": "http://dicewaretr.110mb.com/diceware_tr.txt",
}


class RandomSource(object):
    """Generate random numbers from operating system random source."""

    def __init__(self):
        # self.b is an integer of length self.n bits
        self.b = self.n = 0

    def read(self, n=1):
        """Read n bits from the random source and convert to integer.

        Parameters:
          n   The number of bits to read

        Return value:
          An n-bit nonnegative integer

        The first bit read is the LSB and the last bit read is the
        MSB of the returned integer.

        """
        r = 0
        for i in xrange(n):
            if self.n == 0:
                try:
                    self.b = ord(os.urandom(1))
                except NotImplementedError:
                    print("error: this operating system has no randomness source")
                    sys.exit(1)
                self.n = 8
            r += (self.b & 1) << i
            i += 1
            self.b >>= 1
            self.n -= 1
        return r

    def rand(self, n):
        """Generate a random integer between 0 and n-1.

        Parameters:
          n   integer > 0.

        Return value:
          A random integer between 0 and n-1

        """
        assert(isinstance(n, int) and n > 0)
        if n == 1:
            return 0
        else:
            # Number of bits needed
            b = int(ceil(log(n, 2)))
            i = self.read(b)
            while i >= n:
                i = self.read(b)
            return i


# Parse command line arguments
parser = OptionParser()
parser.add_option("-n", "--words", dest="words", type="int", metavar="N",
                  help="generate N words (default: %default)",
                  default=5)
parser.add_option("-s", "--special", dest="special", type="int", metavar="M",
                  help="insert M special characters (default: %default)",
                  default=0)
parser.add_option("-f", "--file", dest="file", metavar="FILE",
                  help="read the word list from FILE")
linguas = WORD_LIST_URLS.keys()
linguas.sort()
parser.add_option("-l", "--lang", dest="lang", metavar="LANG",
                  type="choice", choices=linguas,
                  help="use the word list for LANG (" + ", ".join(linguas) +
                  ") (default: %default)", default="en")
del linguas

options, args = parser.parse_args()
if args or options.words < 1 or options.special < 0:
    parser.print_help()
    sys.exit(0)

parser.destroy()
del parser, args

# --file has higher precedence than --lang
if options.file:
    try: fobj = open(options.file)
    except IOError:
        print("error: unable to open word list file '%s'" % options.file)
        sys.exit(1)
else:
    # Read the cached word list
    word_list_dir = os.path.expanduser("~/.diceware.py/cache")
    word_list_path = os.path.join(word_list_dir, options.lang)
    try:
        fobj = open(word_list_path)
    except IOError:
        # The word list does not exist => cache it
        word_list_url = WORD_LIST_URLS[options.lang]
        if not os.path.exists(word_list_dir):
            os.makedirs(word_list_dir)
        try: urllib.urlretrieve(word_list_url, word_list_path)
        except IOError:
            print("error: unable to open remote word list '%s'" % word_list_url)
            sys.exit(1)
        fobj = open(word_list_path)


# Read the word list skipping lines which do not start with 5 digits
# and a white space character and removing the 5 digits
word_list = [ line[6:].strip() for line in fobj
             if line[0:5].isdigit() and line[5].isspace() ]
fobj.close()

# A valid Diceware word list has exactly 6**5 = 7776 words
if len(word_list) != 7776:
    print("error: invalid word list format")
    sys.exit(1)

# Initialize the random source
rnd = RandomSource()

# Generate passphrase
words = [ word_list[rnd.rand(7776)] for _ in xrange(options.words) ]
print("passphrase   : %s" % " ".join(words))

# Insert at most options.special special characters. This is not
# exactly the procedure described in the Diceware web page, because
# this handles the case where there are more than 6 words in the
# passphrase and more than 6 characters in the word.
for _ in xrange(options.special):
    # i is the index of the word in which the special character
    # replacement takes place.
    i = rnd.rand(options.words)

    # j is the index of the character to be replaced with a special
    # character.
    j = rnd.rand(len(words[i]))

    # k is the index of the special character
    k = rnd.rand(36)

    # Split to individual characters, replace the k'th char, unsplit
    word = map(None, words[i])
    word[j] = SPECIAL_CHARS[k]
    words[i] = "".join(word)

if options.special > 0:
    print("with specials: %s" % " ".join(words))
