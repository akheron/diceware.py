#!/usr/bin/env python

"""Diceware passphrase generator
Copyright (c) 2008 Petri Lehtinen <petri@digip.org>

Diceware passphrase generator generates passphrases by reading random
bits from the Linux random number generator /dev/random and using them
to index the Diceware word list, supplied by user or automatically
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

from urllib2 import urlopen, URLError
from math import log, ceil
import sys

DEFAULT_WORDLIST = "http://world.std.com/~reinhold/diceware.wordlist.asc"
SPECIAL_CHARS = "~!#$%^&*()-=+[]\{}:;\"'<>?/0123456789"


def usage():
    print(__doc__)
    sys.exit(1)


class LinuxRandomSource(object):
    """Read random numbers from Linux random devices."""

    def __init__(self, rndfile="/dev/random"):
        # File object
        self.fobj = open(rndfile)

        # self.b has self.n bits left
        self.b = ord(self.fobj.read(1))
        self.n = 8

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
                self.b = ord(self.fobj.read(1))
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


# Check the command line arguments
argc = len(sys.argv)

if argc > 4:
    usage()

# The Diceware author recommends a 5 word passphrase for most users.
if argc <= 1: N = 5
else:
    try: N = int(sys.argv[1])
    except ValueError: usage()

# No special characters as default
if argc <= 2: M = 0
else:
    try: M = int(sys.argv[2])
    except ValueError: usage()

if N < 0 or M < 0:
    usage()

if argc <= 3: fp = urlopen(DEFAULT_WORDLIST)
else:
    filename = sys.argv[3]
    if filename.startswith("http://") or filename.startswith("ftp://"):
        try: fp = urlopen(filename)
        except URLError:
            print("Error: Unable to open the word list")
            sys.exit(1)
    elif filename == "-":
        fp = sys.stdin
    else:
        try: fp = open(filename)
        except IOError:
            print("Error: Unable to open the word list")
            sys.exit(1)

# Read the wordlist skipping lines which do not start with 5 digits
# and a white space character and removing the 5 digits
wordlist = [ line[6:].strip() for line in fp
             if line[0:5].isdigit() and line[5].isspace() ]
fp.close()

# A valid Diceware wordlist has exactly 5**6 = 7776 words
if len(wordlist) != 7776:
    print("Error: Invalid word list")
    sys.exit(1)

# Initialize the random source
rnd = LinuxRandomSource()

# Generate N words
words = [ wordlist[rnd.rand(7776)] for _ in xrange(N) ]
print("Passphrase   : %s" % " ".join(words))

# Insert at most M special characters. This is not exactly the
# procedure described in the Diceware web page, because this handles
# the case where there are more than 6 words in the passphrase and
# more than 6 characters in the word.
for _ in xrange(M):
    # i is the index of the word in which the special character
    # replacement takes place.
    i = rnd.rand(N)

    # j is the index of the character to be replaced with a special
    # character.
    j = rnd.rand(len(words[i]))

    # k is the index of the special character
    k = rnd.rand(36)

    # Split to individual characters, replace the k'th char, unsplit
    word = map(None, words[i])
    word[j] = SPECIAL_CHARS[k]
    words[i] = "".join(word)

if M > 0:
    print("With specials: %s" % " ".join(words))
