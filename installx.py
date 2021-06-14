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

from termios import tcgetattr, tcsetattr, TCSADRAIN
from shutil import copy
from sys import argv, stdin, stdout, stderr, exit
from tty import setraw
from re import search

from os.path import isdir, isfile
from os.path import basename, relpath, realpath

from os import (
    getcwd, chdir,
    environ, getenv,
    makedirs, scandir,
    readlink, unlink, symlink,
    access, W_OK, X_OK,
    EX_OK as EXIT_SUCCESS,
    EX_SOFTWARE as EXIT_FAILURE,
)

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
        action = 'testmode install' if args.dryrun else 'overwrite'
        print(f"{action} in '{dst}/' with '{src}/*' (y/n)? ", end='')
        stdout.flush()
        yn = getchar(); print(yn)
        if yn != 'y': bomb('aborting')

    return src, dst


def check_sanity(src, dst):

    if not isdir(src):
        bomb("source dir invalid")

    if not exists(dst):
        try: makedirs(dst)
        except: bomb(f"dest '{dst}' dns or bad mkdir")

    elif not isdir(dst):
        bomb(f"refusing overwrite of '{dst}' (not a directory)")

    if not access(dst, W_OK):
        bomb(f"cannot write to destdir '{dst}'")


def print_execution_stats(src, dst, cnt):

    src = f"{src}/"
    dst = f"{dst}/"

    if search(r'[^a-zA-Z0-9_/.+,:@-]', src + dst):
        src = f"\"{src}\""; dst = f"\"{dst}\""
    prefix = 'testmode: ' if args.dryrun else ''
    print(f"{prefix}installed {cnt}")


def find_candidates():

    scripts = []; exelinks = []; rclinks = []
    targets = {}


    for f in scandir('.'):
        if f.is_file() and access(f.name, X_OK):
            scripts.append(f)
        elif f.is_symlink():
            target = readlink(f.name)
            targets[f.name] = target
            if isfile(target) and '/' not in target:
                if access(f.name, X_OK):
                    exelinks.append(f)
                elif f.name[0] == '.':
                    rclinks.append(f)

    installx = [f.name for f in (scripts + exelinks)]
    installrc = [f.name for f in rclinks], targets

    return locals()[invname]


###

def installx(dst):

    count = 0
    for file in find_candidates():
        count += 1
        if args.dryrun:
            print(f"testmode: {dst}/{file}")
            continue
        try: unlink(f"{dst}/{file}") # always set our own perms
        except FileNotFoundError: pass

        copy(file, dst)

    return count


def installrc(dst):

    symlinks, targets = find_candidates()
    count = 0
    src = getcwd()

    for link in symlinks:
        count += 1
        ref = targets[link]
        reltarget = relpath(f"{src}/{ref}", start=realpath(dst))
        linkpath = f"{dst}/{link}"

        if args.dryrun:
            print(f"testmode: {dst}/{link} -> {reltarget}")
            continue

        try: unlink(linkpath)
        except FileNotFoundError: pass

        symlink(reltarget, linkpath)

    return count


def main():

    src, dst = process_args()
    check_sanity(src, dst)

    try: chdir(src)
    except: bomb(f"cannot change directory to '{src}'")

    try: subprogram = globals()[invname]
    except (KeyError, TypeError):
        bomb(f"unimplemented command '{invname}'")

    ninstalled = subprogram(dst)

    if not args.quiet:
        print_execution_stats(src, dst, ninstalled)


if __name__ == "__main__":

    invname = basename(argv[0])
    args = argv[1:]
    nargs = len(args)

    try:
        if (bool(environ['DEBUG'])):
            debug = True
            err('debug-mode-enabled')
        else:
            raise KeyError

    except KeyError:
        debug = False

    if debug: breakpoint()

    main()
