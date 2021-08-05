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
from stat import S_IFLNK
from hashlib import sha256

from os.path import (
    join, expanduser,
    basename, dirname,
    isdir, isfile, exists,
    relpath, realpath, abspath, normpath, commonpath,
)
from os import (
    stat, lstat,
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

    def addflag(p, flagchar, longopt, help=None, /, **kwargs):
        options = list(("-%s --%s" % (flagchar, longopt)).split())
        p.add_argument(*options, action='store_true', help=help, **kwargs)

    def addarg(p, vname, vdesc, help=None, /, **kwargs):
        p.add_argument(vname, nargs='?', metavar=vdesc, help=help, **kwargs)

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
    addflag (p, 'n', 'test', "only show intended actions", dest='dryrun')
    addflag (p, 'q', 'quiet', "no output for most actions")
    addflag (p, 'f', 'force', "don't ask confirmation of source and dest")
    addflag (p, 'u', 'unchanged', "overwrite unchanged files", dest='nocheck')
    addarg  (p, 'src', 'srcdir', "install from [cwd]")
    addarg  (p, 'dest', 'destdir', f"install to [{defaultdest[invname]}]")

    args = p.parse_args(args)

    args.ask = True if not args.force else False

    if args.quiet and args.ask:
        bomb("quiet mode cannot be interactive")
    if args.dryrun and args.force:
        bomb("the force is not with you")

    src = args.src if args.src else getcwd()
    dst = defaultdest[invname] if not args.dest else args.dest
    for d in ['src', 'dst']: exec(f"{d} = {d}.rstrip('/')")

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
    if type(cnt) == list:
        cnt = \
            f"{cnt[0]} scripts, " \
            f"{cnt[1]} exelinks, " \
            f"{cnt[2]} skipped"
    else:
        cnt = f"{cnt} rclinks"

    if search(r'[^a-zA-Z0-9_/.+,:@-]', src + dst):
        src = f"\"{src}\""; dst = f"\"{dst}\""

    prefix = 'testmode: ' if args.dryrun else ''
    if not args.dryrun:
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


def files_differ(file1, file2):

    def filetype(file):
        try:
            st = lstat(file)
            return st.st_mode >> 9
        except FileNotFoundError:
            return 0

    def gethash(file):
        with open(file, "rb") as f:
            return sha256(f.read()).hexdigest()

    ft1 = filetype(file1)
    ft2 = filetype(file2)

    if ft1 != ft2:
        return True

    if ft1 == S_IFLNK >> 9:
        if readlink(file1) == readlink(file2): return False
        else: return True

    if gethash(file1) == gethash(file2): return False
    else: return True


###

def entilde(path):
    userhome = expanduser('~')
    if path.startswith(userhome):
        path = f"~{path[len(userhome):]}"
    return path


def installx(src, dst):

    counts = [0, 0, 0] # scripts, exelinks, skips
    cntidx = 0
    skipped = 0

    (scripts, exelinks), targets = find_candidates(src, dst)
    for lst in [scripts, exelinks]:
        for file in lst:
            destfile = f"{dst}/{file}"
            same = not files_differ(file, destfile)
            skipped += 0 if not same else 1
            counts[cntidx] += 0 if same else 1
            if args.dryrun:
                if targets.get(file):
                    linktext = f" -> {basename(targets[file][1])}"
                else:
                    linktext = ''
                print(
                    f"testmode: {entilde(dst)}/{file}{linktext}" \
                    f"{' (skipped)' if same else ''}")
            else:
                if same and not args.nocheck: continue
                try: unlink(destfile) # always set our own perms
                except FileNotFoundError: pass
                copy(file, dst, follow_symlinks=False)
        cntidx += 1

    counts[2] = skipped
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

        count += linkcnt - 1

    return count

###

def main():

    if debug: breakpoint()

    src, dst = process_args()
    check_sanity(src, dst)

    try: chdir(src)
    except: bomb(f"cannot change directory to '{src}'")

    try: subprogram = globals()[invname]
    except (KeyError, TypeError):
        bomb(f"unimplemented command '{invname}'")

    counts = subprogram(src, dst)

    if not args.quiet:
        print_execution_stats(src, dst, counts)

###

if __name__ == "__main__":

    from sys import version_info as pyv
    if pyv.major < 3 or pyv.major == 3 and pyv.minor < 9:
        bomb("minimum python 3.9")

    invname = basename(argv[0])
    args = argv[1:]

    try:
        from bdb import BdbQuit
        if bool(environ['DEBUG']):
            from pprint import pprint as pp
            debug = True
            err('debug-mode-enabled')
        else:
            raise KeyError

    except KeyError:
        debug = False

    try: main()
    except BdbQuit: bomb("debug-stop")
