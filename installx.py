#!/usr/bin/env python3
"""
installs in-dir exe files and symlinks, or all .rclinks, to [homedir]

  installx: cp exefiles and symlinks to in-dir exes: ${1:-./} -> ${2:-~/bin/}
  installrc: cp .rclinks as: ${1:-.}/.rclink -> ${2:-~/${PWD##*/}}/target

"""
__url__     = 'http://smemsh.net/src/utilpy/'
__author__  = 'Scott Mcdermott <scott@smemsh.net>'
__license__ = 'GPL-2.0'

###

import argparse

from sys import argv, stdin, stdout, stderr, exit
from os import environ, getcwd, chdir, getenv, makedirs, access, W_OK
from os.path import isdir

from termios import tcgetattr, tcsetattr, TCSADRAIN
from tty import setraw

from os import EX_OK as EXIT_SUCCESS
from os import EX_SOFTWARE as EXIT_FAILURE

from os.path import basename

#

def err(*args, **kwargs):
    print(*args, file=stderr, **kwargs)

def bomb(*args):
    err(*args)
    exit(EXIT_FAILURE)

###

def process_args():

    global args

    def addflag(parser, flagchar, longopt, **kwargs):
        options = list(("-%s --%s" % (flagchar, longopt)).split())
        parser.add_argument(*options, action='store_true', **kwargs)

    def addarg(parser, varname, vardesc):
        parser.add_argument(varname, nargs='?', metavar=vardesc)

    def getchar():
        fd = stdin.fileno()
        tattrs = tcgetattr(fd)
        setraw(fd)
        c = stdin.buffer.raw.read(1).decode(stdin.encoding)
        tcsetattr(fd, TCSADRAIN, tattrs)
        return c

    p = argparse.ArgumentParser(
        prog            = invname,
        description     = __doc__.strip(),
        allow_abbrev    = False,
        formatter_class = argparse.RawTextHelpFormatter,
    )
    addflag (p, 'n', 'test', dest='dryrun')
    addflag (p, 'q', 'quiet')
    addflag (p, 'f', 'force')
    addarg  (p, 'src', 'srcdir')
    addarg  (p, 'dest', 'destdir')

    args = p.parse_args(args)

    args.ask = True if not args.force else False

    if args.quiet and args.ask:
        bomb("quiet mode cannot be interactive")
    if args.dryrun and args.force:
        bomb("the force is not with you")

    src = args.src if args.src else getcwd()
    dst = args.dest if args.dest else getenv('HOME')
    src = src[:-1] if src[-1] == '/' else src
    dst = dst[:-1] if dst[-1] == '/' else dst

    if invname == 'installx' and not args.dest:
        dst = dst + '/bin'

    if args.ask:
        print(f"overwrite in '{dst}/' with '{src}/*' (y/n)? ", end='')
        stdout.flush()
        yn = getchar(); print()
        if yn != 'y': bomb('aborting')

    return src, dst


def check_sanity(src, dst):

    if not isdir(dst):
        try: makedirs(dst, exist_ok=True)
        except: bomb(f"dest '{dst}' dns or bad mkdir")

    if not isdir(src):
        bomb("source dir invalid")

    if not access(dst, W_OK):
        bomb(f"cannot write to destdir '{dst}'")


def main():

    src, dst = process_args()
    check_sanity(src, dst)

    try: chdir(src)
    except: bomb(f"cannot change directory to '{src}'")

    try: globals()[invname](src, dst)
    except (KeyError, TypeError):
        bomb(f"unimplemented command '{invname}'")

if (__name__ == "__main__"):

    invname = basename(argv[0])
    args = argv[1:]
    nargs = len(args)

    try:
        if (bool(environ['DEBUG'])):
            debug = True
            breakpoint()
            err('debug-mode-enabled')
        else:
            raise KeyError

    except KeyError:
        debug = False

    main()
