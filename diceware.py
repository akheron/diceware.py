#!/usr/bin/env python

"""Diceware passphrase generator

Diceware passphrase generator generates passphrases by reading random
data from the operating system random number generator and using it to
index the Diceware word list, supplied by user or automatically
downloaded from the Diceware web page. For more information on
Diceware, see the Diceware web page:
http://world.std.com/~reinhold/diceware.html

"""

__license__ = """
Copyright (c) 2008, 2009 Petri Lehtinen <petri@digip.org>

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
    "fi": "http://users.ics.aalto.fi/kaip/noppaware/noppaware.txt",
    "it": "https://raw.github.com/taringamberini/diceware_word_list_it-IT/"
          "master/diceware/wordlist/word_list_diceware_it-IT-1.0.11.txt",
    "se": "http://x42.com/diceware/diceware-sv.txt",
    "tr": "http://dicewaretr.110mb.com/diceware_tr.txt",
    "nl": "http://theworld.com/~reinhold/DicewareDutch.txt",
}

def generate_grid(word_list, words=5, specials=0):
    longest_word_length = 0
    result = []
    for _ in range(words):
        word_row, with_specials = generate(word_list, words, specials)
        if specials:
            result.append(with_specials)
        else:
            result.append(word_row)

        # Assume word_row and with_specials contain equal length words
        long_word_length = max(len(x) for x in word_row)
        longest_word_length = max(long_word_length, longest_word_length)

    return result, longest_word_length

def generate(word_list, words=5, specials=0):
    rnd = SystemRandom()
    words = [ rnd.choice(word_list) for _ in range(words) ]

    # Insert at most options.special special characters. This is not
    # exactly the procedure described in the Diceware web page, because
    # this handles the case where there are more than 6 words in the
    # passphrase and more than 6 characters in the word.
    if specials:
        split_words = [ map(None, x) for x in words ]
        for _ in range(specials):
            # i is the index of the word in which the special character
            # replacement takes place.
            i = rnd.randrange(len(split_words))

            # j is the index of the character to be replaced with a special
            # character.
            j = rnd.randrange(len(split_words[i]))

            # k is the index of the special character
            k = rnd.randrange(len(SPECIAL_CHARS))

            # Split to individual characters, replace the k'th char, unsplit
            split_words[i][j] = SPECIAL_CHARS[k]

        with_specials = [ "".join(x) for x in split_words ]
    else:
        with_specials = words

    return words, with_specials


def read_word_list(fobj):
    # Read the word list skipping lines which do not start with 5 digits
    # and a white space character and removing the 5 digits
    word_list = [ line[6:].strip() for line in fobj
                 if line[0:5].isdigit() and line[5].isspace() ]

    # A valid Diceware word list has exactly 6**5 = 7776 words
    if len(word_list) != 7776:
        raise ValueError("invalid word list format")

    return word_list


def get_word_list(cache_dir, lang="en"):
    assert lang in WORD_LIST_URLS.keys()

    # Read the cached word list
    word_list_path = os.path.join(cache_dir, lang)
    try:
        fobj = open(word_list_path)
    except IOError:
        # The word list does not exist => cache it
        word_list_url = WORD_LIST_URLS[lang]
        urllib.urlretrieve(word_list_url, word_list_path)
        fobj = open(word_list_path)

    return read_word_list(fobj)


def main():
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


    def config_default(config, section, option, default):
        """Set default values for options that do not have a value."""
        try:
            config.get(section, option)
        except NoSectionError:
            config.add_section(section)
            config.set(section, option, default)
        except NoOptionError:
            config.set(section, option, default)


    config_dir = ensure_dir(os.path.expanduser("~/.diceware.py"))
    cache_dir = ensure_dir(os.path.join(config_dir, "cache"))

    # Parse config file
    config_file = os.path.join(config_dir, "config")
    config = SafeConfigParser()
    config.read(config_file)

    config_default(config, "defaults", "lang", "en")
    config_default(config, "defaults", "words", "5")
    config_default(config, "defaults", "special", "0")
    config_default(config, "defaults", "file", "")
    config_default(config, "defaults", "separator", " ")

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
    parser.add_option("-g", "--grid", dest="grid", action="store_true",
                      help="Instead of a single line, generate NxN grid of "+
                      "words. This makes eavesdropping harder")
    parser.add_option("-n", "--words", dest="words", type="int", metavar="N",
                      help="generate N words (default: %default)",
                      default=config.getint("defaults", "words"))
    parser.add_option("-s", "--special", dest="special", type="int", metavar="M",
                      help="insert M special characters (default: %default)",
                      default=config.getint("defaults", "special"))
    parser.add_option("-f", "--file", dest="file", metavar="FILE",
                      help="override the `lang' option and read the word list " +
                      "from FILE", default=config.get("defaults", "file"))
    parser.add_option("-p", "--separator", dest="separator", type="string", metavar="P",
                      help="specify the separator between words (default: %default)",
                      default=config.get("defaults", "separator"))
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
        try:
            fobj = open(options.file)
        except IOError:
            print("error: unable to open word list file '%s'" % options.file)
            sys.exit(1)
        try:
            word_list = read_word_list(fobj)
        except ValueError, e:
            print("error: %s" % e)
            sys.exit(1)
    else:
        word_list = get_word_list(cache_dir, options.lang)

    if not options.grid:
        words, with_specials = generate(word_list, options.words,
                                        options.special)
        print("passphrase   : %s" % options.separator.join(words))
        if options.special > 0:
            print("with specials: %s" % options.separator.join(with_specials))
    else:
        words, length = generate_grid(word_list, options.words,
                                            options.special)
        for word_row in words:
            print " ".join([word.ljust(length) for word in word_row])

if __name__ == "__main__":
    main()
