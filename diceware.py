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
from ConfigParser import SafeConfigParser, NoOptionError, NoSectionError
from random import SystemRandom
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


def ensure_dir(path):
    """Ensure that path is a directory creating it if necessary.

    If path already exists and is not a directory, print an error
    message and quit with sys.exit().

    Parameters:
      path   String specifying the path to ensure

    Return value:
      path
    
    """
    if not os.path.exists(path):
        os.makedirs(path)
    elif not os.path.isdir(path):
        print("error: '%s' is not a directory" % path)
        sys.exit(1)
    return path


config_dir = ensure_dir(os.path.expanduser("~/.diceware.py"))
cache_dir = ensure_dir(os.path.join(config_dir, "cache"))

# Parse config file
config_file = os.path.join(config_dir, "config")
config = SafeConfigParser()
config.read(config_file)

def config_default(config, section, option, default):
    """Set default values for options that do not have a value."""
    try:
        config.get(section, option)
    except NoSectionError:
        config.add_section(section)
        config.set(section, option, default)
    except NoOptionError:
        config.set(section, option, default)

config_default(config, "defaults", "lang", "en")
config_default(config, "defaults", "words", "5")
config_default(config, "defaults", "special", "0")
config_default(config, "defaults", "file", "")

# Sanity checks for config options
if config.get("defaults", "lang") not in WORD_LIST_URLS.keys():
    print("error: '%s' is not a valid value for option 'lang'"
          % config.get("defaults", "lang"))
    sys.exit(1)
try:
    config.getint("defaults", "words")
    config.getint("defaults", "special")
except ValueError:
    print("error: 'words' and 'special' options must have integer values")
    sys.exit(1)


# Parse command line arguments
parser = OptionParser()
parser.add_option("-n", "--words", dest="words", type="int", metavar="N",
                  help="generate N words (default: %default)",
                  default=config.getint("defaults", "words"))
parser.add_option("-s", "--special", dest="special", type="int", metavar="M",
                  help="insert M special characters (default: %default)",
                  default=config.getint("defaults", "special"))
parser.add_option("-f", "--file", dest="file", metavar="FILE",
                  help="override the `lang' option and read the word list " +
                  "from FILE", default=config.get("defaults", "file"))
linguas = sorted(WORD_LIST_URLS.keys())
parser.add_option("-l", "--lang", dest="lang", metavar="LANG",
                  type="choice", choices=linguas,
                  help="use the word list for LANG (" + ", ".join(linguas) +
                  ") (default: %default)", default=config.get("defaults", "lang"))

options, args = parser.parse_args()
if args or options.words < 1 or options.special < 0:
    parser.print_help()
    sys.exit(0)

parser.destroy()

# --file has higher precedence than --lang
if options.file:
    try: fobj = open(options.file)
    except IOError:
        print("error: unable to open word list file '%s'" % options.file)
        sys.exit(1)
else:
    # Read the cached word list
    word_list_path = os.path.join(cache_dir, options.lang)
    try:
        fobj = open(word_list_path)
    except IOError:
        # The word list does not exist => cache it
        word_list_url = WORD_LIST_URLS[options.lang]
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
rnd = SystemRandom()

# Generate passphrase
words = [ rnd.choice(word_list) for _ in range(options.words) ]
print("passphrase   : %s" % " ".join(words))

# Insert at most options.special special characters. This is not
# exactly the procedure described in the Diceware web page, because
# this handles the case where there are more than 6 words in the
# passphrase and more than 6 characters in the word.
for _ in range(options.special):
    # i is the index of the word in which the special character
    # replacement takes place.
    i = rnd.randrange(options.words)

    # j is the index of the character to be replaced with a special
    # character.
    j = rnd.randrange(len(words[i]))

    # k is the index of the special character
    k = rnd.randrange(36)

    # Split to individual characters, replace the k'th char, unsplit
    word = map(None, words[i])
    word[j] = SPECIAL_CHARS[k]
    words[i] = "".join(word)

if options.special > 0:
    print("with specials: %s" % " ".join(words))
