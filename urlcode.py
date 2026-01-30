#!/usr/bin/env python3
"""
urlcode, urlencode, urldecode
  command line encode/decode of strings to clean http refs for urls

desc:
  - invoke as urlencode or urldecode
  - send as lines on stdin, or pass as cli args, or both
  - result each of each xcoded written as line on stdout
  - uses '%20', not '+', for spaces

"""
__url__     = 'https://github.com/smemsh/devskel/'
__author__  = 'Scott Mcdermott <scott@smemsh.net>'
__license__ = 'GPL-2.0'
__devskel__ = '0.8.1'

from sys import exit, hexversion
if hexversion < 0x030900f0: exit("minpython: %s" % hexversion)

import argparse

from sys import argv, stdin, stdout, stderr
from select import select

from urllib.parse import quote, unquote
from functools import wraps

from os.path import basename
from os import (
    getenv, unsetenv,
    isatty, dup,
    close as osclose,
    EX_OK as EXIT_SUCCESS,
    EX_SOFTWARE as EXIT_FAILURE,
)

###

def err(*args, **kwargs):
    print(*args, file=stderr, **kwargs)

def bomb(*args, **kwargs):
    err(*args, **kwargs)
    exit(EXIT_FAILURE)

###

def process_args():

    global args

    def usagex(*args, **kwargs):
        nonlocal p
        p.print_help(file=stderr)
        print(file=stderr)
        bomb(*args, **kwargs)

    # parse_args() gives escaped strings
    def unesc(s):
        if s is None: return
        else: return s.encode('raw-unicode-escape').decode('unicode-escape')

    def addarg(p, vname, help=None, /, **kwargs):
        p.add_argument(vname, help=help, **kwargs)

    def addargs(*args, **kwargs):
        addarg(*args, nargs='*', **kwargs)

    p = argparse.ArgumentParser(
        prog            = invname,
        description     = __doc__.strip(),
        allow_abbrev    = False,
        formatter_class = argparse.RawTextHelpFormatter,
    )

    addargs(p, 'strings', 'string1, string2, ...', metavar='string')
    args = p.parse_args(args)

    return [unesc(s) for s in args.strings]


###

urlencode = lambda s: urlcode(s, quote)
urldecode = lambda s: urlcode(s, unquote)
def urlcode(strings, callback):
    for s in strings:
        print(callback(s))


# todo: for query params, .quote_plus() should be used, will need option
# todo: newline at end [verify?]; perhaps we should only if isatty?
#
def main():

    if debug == 1:
        breakpoint()

    strings = process_args()
    if globals().get('infile'):
        strings += [line.removesuffix('\n') for line in infile.readlines()]

    try: subprogram = globals()[invname]
    except (KeyError, TypeError):
        from inspect import trace
        if len(trace()) == 1: bomb("unimplemented")
        else: raise

    return subprogram(strings)

###

if __name__ == "__main__":

    invname = basename(argv[0])
    args = argv[1:]

    # move stdin, pdb needs stdio fds itself
    stdinfd = stdin.fileno()
    if not isatty(stdinfd):
        try:
            if select([stdin], [], [])[0]:
                infile = open(dup(stdinfd))
                osclose(stdinfd)  # cpython bug 73582
                try: stdin = open('/dev/tty')
                except: pass  # no ctty, but then pdb would not be in use
        except KeyboardInterrupt:
            bomb("interrupted")

    from bdb import BdbQuit
    if debug := int(getenv('DEBUG') or 0):
        import pdb
        from pprint import pp
        err('debug: enabled')
        unsetenv('DEBUG')  # otherwise forked children hang

    try: main()
    except BdbQuit: bomb("debug: stop")
    except SystemExit: raise
    except KeyboardInterrupt: bomb("interrupted")
    except:
        from traceback import print_exc
        print_exc(file=stderr)
        if debug: pdb.post_mortem()
        else: bomb("aborting...")
    finally:  # cpython bug 55589
        try: stdout.flush()
        finally:
            try: stdout.close()
            finally:
                try: stderr.flush()
                except: pass
                finally: stderr.close()
