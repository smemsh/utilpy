#!/usr/bin/env python3
"""
installs in-dir exe files and symlinks, or all .rclinks, to [homedir]

  installx:
    cp exefiles, and symlinks to in-dir exes, from ${1:-.}/ to ${2:-~/bin}/

  installrc:
    recreate using relative links in ${2:-~}/, all .rclinks in ${1:-.}/ which
    target exes in {$1:-.}/, including any intermediate links (with needed
    mkdirs) in chains of multi-level symlinks, as long as all levels are
    descendants of ${1:-.}/ and the end target is in ${1:-.}/

"""
__url__     = 'http://smemsh.net/src/utilpy/'
__author__  = 'Scott Mcdermott <scott@smemsh.net>'
__license__ = 'GPL-2.0'

import argparse

from termios import tcgetattr, tcsetattr, TCSADRAIN
from shutil import copy
from sys import argv, stdin, stdout, stderr, exit
from tty import setraw
from re import search

from os.path import (
    join, expanduser,
    basename, dirname,
    isdir, isfile, exists,
    relpath, realpath, abspath, normpath, commonpath,
)
from os import (
    getcwd, chdir,
    environ, getenv,
    makedirs, scandir,
    readlink, unlink, symlink,
    access, W_OK, X_OK,
    EX_OK as EXIT_SUCCESS,
    EX_SOFTWARE as EXIT_FAILURE,
)

###

defaultdest = {
    'installrc': getenv('HOME'),
    'installx': getenv('HOME') + '/bin',
}

###

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

    def addarg(parser, varname, vardesc, **kwargs):
        parser.add_argument(varname, nargs='?', metavar=vardesc, **kwargs)

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
    dst = defaultdest[invname] if not args.dest else args.dest
    src = src[:-1] if src[-1] == '/' else src
    dst = dst[:-1] if dst[-1] == '/' else dst

    if args.ask:
        action = 'testmode install' if args.dryrun else 'overwrite'
        print(f"{action} in '{dst}/' with '{src}/*' (y/n)? ", end='')
        stdout.flush()
        yn = getchar(); print(yn)
        if yn != 'y': bomb('aborting')

    return abspath(src), abspath(dst)


def check_sanity(src, dst):

    if not isdir(src):
        bomb("source dir invalid")

    if not exists(dst):
        try: makedirs(dst)
        except: bomb(f"dest '{dst}' dne or bad mkdir")

    elif not isdir(dst):
        bomb(f"refusing overwrite of '{dst}' (not a directory)")

    if not access(dst, W_OK):
        bomb(f"cannot write to destdir '{dst}'")


def print_execution_stats(src, dst, cnt):

    src = f"{src}/"
    dst = f"{dst}/"
    cnt = f"{cnt[0]} scripts, {cnt[1]} exelinks" \
          if type(cnt) == list \
          else f"{cnt} rclinks"

    if search(r'[^a-zA-Z0-9_/.+,:@-]', src + dst):
        src = f"\"{src}\""; dst = f"\"{dst}\""
    prefix = 'testmode: ' if args.dryrun else ''
    print(f"{prefix}{entilde(src)} -> {entilde(dst)}")
    print(f"{prefix}installed {cnt}")


def find_candidates(src, dst):

    scripts = []; exelinks = []; rclinks = []
    targets = {}

    def abspathdst(path):
        return join(dst, relpath(path, start=src))

    for f in scandir('.'):

        if f.is_file(follow_symlinks=False) and access(f.name, X_OK):
            scripts.append(f)

        elif f.is_symlink():

            endtarget = realpath(f.name)
            if not isfile(endtarget):
                continue
            if dirname(endtarget) != src:
                continue

            linkchain = []
            linkname = abspath(f.name)
            linkchain.append(abspathdst(linkname))

            while True:
                tdir = dirname(linkname)
                tlink = readlink(linkname)
                target = normpath(join(tdir, tlink))
                if not commonpath([src, target]).startswith(src):
                    err(f"skipping link {f.name} with component outside {src}")
                    linkchain = None
                    break
                if target == endtarget:
                    linkchain.append(target)
                    break
                else:
                    linkchain.append(abspathdst(target))
                    linkname = target
            if not linkchain:
                continue

            if access(f.name, X_OK) and len(linkchain) == 2:
                exelinks.append(f)
            elif f.name[0] == '.':
                rclinks.append(f)

            targets[f.name] = linkchain

    installrc = ([f.name for f in rclinks], targets)
    installx = ([f.name for f in l] for l in [scripts, exelinks]), targets

    return locals()[invname]

###

def entilde(path):
    userhome = expanduser('~')
    if path.startswith(userhome):
        path = f"~{path[len(userhome):]}"
    return path


def installx(src, dst):

    counts = [0, 0] # track scripts, exelinks but return one value
    cntidx = 0

    (scripts, exelinks), targets = find_candidates(src, dst)
    for lst in [scripts, exelinks]:
        for file in lst:
            counts[cntidx] += 1
            if args.dryrun:
                symlinktext = \
                    f"\x20-> {basename(targets[file][1])}" \
                    if targets.get(file) \
                    else ''
                print(f"testmode: {entilde(dst)}/{file}{symlinktext}")
            else:
                try: unlink(f"{dst}/{file}") # always set our own perms
                except FileNotFoundError: pass
                copy(file, dst, follow_symlinks=False)
        cntidx += 1

    return counts


def installrc(src, dst):

    symlinks, targets = find_candidates(src, dst)
    count = 0

    for link in symlinks:

        linkchain = targets[link]
        linkcnt = len(linkchain)

        for i in range(linkcnt - 1):
            linkto = linkchain[i+1]
            linkfrom = linkchain[i]
            dirfrom = dirname(linkfrom)
            if dirfrom.removeprefix(dst):
                if args.dryrun:
                    print(f"testmode: {entilde(dirfrom)} [makedirs]")
                else:
                    try: makedirs(dirfrom, exist_ok=True)
                    except: bomb(f"failed makedirs for '{dirfrom}'")
            else:
                dirfrom = dst
            reltarget = relpath(linkto, start=dirfrom)
            if args.dryrun:
                print(f"testmode: {entilde(linkfrom)} -> {reltarget}")
                continue
            try: unlink(linkfrom)
            except FileNotFoundError: pass
            symlink(reltarget, linkfrom)

        count += linkcnt

    return count

###

def main():

    src, dst = process_args()
    check_sanity(src, dst)

    try: chdir(src)
    except: bomb(f"cannot change directory to '{src}'")

    try: subprogram = globals()[invname]
    except (KeyError, TypeError):
        bomb(f"unimplemented command '{invname}'")

    instcnt = subprogram(src, dst)

    if not args.quiet:
        print_execution_stats(src, dst, instcnt)

###

if __name__ == "__main__":

    from sys import version_info as pyv
    if pyv.major < 3 or pyv.major == 3 and pyv.minor < 9:
        bomb("minimum python 3.9")

    invname = basename(argv[0])
    args = argv[1:]

    try:
        if bool(environ['DEBUG']):
            from pprint import pprint as pp
            debug = True
            err('debug-mode-enabled')
        else:
            raise KeyError

    except KeyError:
        debug = False

    if debug: breakpoint()

    main()
