#!/usr/bin/env python3
#
# passgen
#   output random 128-bit password from [[:alnum:]] ^ [0Ol1I]
#
# desc:
#   - generates a 22 char password (~128 bits entropy)
#   - chars: a-z, A-Z, 0-9, except: 0, O, l, 1, I (== 57 possible)
#   - uses python random.SystemRandom (on linux, os.urandom())
#   - uses random.choice() to map into range of suitable characters
#
# calc:
#   - passlen = 22
#   - setsize = len([[:alnum:]]) - 5 # ([^0Ol1I])
#             = 26 + 26 + 10 - 5 = 57
#   - entropy = log2(setsize^passlen)
#             = log2(setsize) * passlen
#             = passlen * (ln(setsize) / ln(2))
#             = 22 * (ln(57) / ln(2))
#             = 128.3235803212
# also:
#   - https://en.wikipedia.org/wiki/Password_strength
#
# todo:
#   - variable length if given (nchars)
#   - specify length in terms of entropy bits
#
# scott@smemsh.net
# http://smemsh.net/src/utilpy/
# http://spdx.org/licenses/GPL-2.0
#
##############################################################################
"""
print random password
    chars: a-z, A-Z, 0-9; exclude: 0, O, l, 1, I; total: 57
    length: 22 chars; entropy: ~128 bits
    takes no arguments
"""

from sys import argv, stdout
from os import environ
from os.path import realpath, basename

from random import SystemRandom as Rng
from string import ascii_letters as letters
from string import digits

#
PASSLEN = 22
CHARSET = set(letters + digits) ^ set("0Ol1I")

#
def usagex():

    print("{}:".format(invname), __doc__.strip())
    quit()

###

def passgen(random, charset, length):

    s = str()
    for _ in range(length):
        s += random.choice(list(charset))

    return s

###

def main():

    if (nargs != 0):
        usagex()

    rng = Rng()
    password = passgen(rng, CHARSET, PASSLEN)

    print(password, end='')
    if (stdout.isatty()):
        print()

###

if (__name__ == "__main__"):

    try:
        if (bool(environ['DEBUG'])):
            debug = True
            import pdb
            from pprint import pprint as pp
            pp('debug-mode-enabled')
            pdb.set_trace()
        else:
            raise KeyError

    except KeyError:
        debug = False

    invname = basename(realpath(argv[0]))
    nargs = len(argv) - 1

    main()
#
