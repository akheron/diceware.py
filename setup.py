#!/usr/bin/env python

from distutils.core import setup

setup(name='diceware.py',
      version='1.0a1',
      description='Diceware passphrase generator',
      long_description='''\
Diceware passphrase generator generates passphrases by reading random
data from the operating system random number generator and using it to
index the Diceware word list, supplied by user or automatically
downloaded from the Diceware web page. For more information on
Diceware, see the Diceware web page:
http://world.std.com/~reinhold/diceware.html''',
      author='Petri Lehtinen',
      author_email='petri@digip.org',
      url='http://github.com/akheron/diceware.py/',
      license='BSD',
      scripts=['diceware.py'],
      )
