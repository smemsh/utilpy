utilpy
==============================================================================

Collection of shell utilities, written in Python.

(once they become large or more useful, they will probably get moved to
their own repositories)

| Scott Mcdermott <scott@smemsh.net>
| https://github.com/smemsh/utilpy/
| https://spdx.org/licenses/GPL-2.0

____

.. contents::

____


passgen
------------------------------------------------------------------------------

output random password from [[:alnum:]] ^ [0Ol1I], default 128 bits

- generates a random password with specifiable entropy
- chars: a-z, A-Z, 0-9, except: 0, O, l, 1, I (== 57 possible)
- default 22 char password (~128 bits entropy using our charset)
- uses python random.SystemRandom (on linux, os.urandom())
- uses random.choice() to map into range of suitable characters

args:

- arg1: number of bits of entropy the secret should have, default 128

calculation::

 passlen = 22
 setsize = len([[:alnum:]]) - 5 # ([^0Ol1I])
         = 26 + 26 + 10 - 5 = 57
 entropy = log2(setsize^passlen)
         = log2(setsize) * passlen
         = passlen * (ln(setsize) / ln(2))
         = 22 * (ln(57) / ln(2))
         = 128.3235803212

todo:

- allow to specify length instead of computing by entropy
- allow to specify character set

also:

https://en.wikipedia.org/wiki/Password_strength


yamldump
------------------------------------------------------------------------------

Pretty prints yaml files as python objects.

| args: any number of yaml files to print
| todo: optionally pre-pass through jinja2


count
------------------------------------------------------------------------------

Counts lines in the standard input, or the given files.

- equivalent to `wc -l` (different output format if files given)
- 5x slower than C version (`wc -l`) in measurements, python-3.9.5


hostfill
------------------------------------------------------------------------------

Looks for ipv4 addresses in the input and replaces with their
looked up name from `gethostbyaddr()` in the output.


lensort
------------------------------------------------------------------------------

Sorts the input by line length, with a configurable filter length.


urlcode
------------------------------------------------------------------------------

Provides the `urlencode` and `urldecode` commands, which take
all lines of standard input, and all words given in their
argument vector, and either encode or decode them for the http
url schemes, according to the rules specified in RFC3986 (via
`urllib.parse`).


pypath
------------------------------------------------------------------------------

Prints ``sys.path`` on separate lines, using interpreter as given in
invocation (``python``, ``python2`` or ``python3`` for ``pypath``,
``py2path``, and ``py3path``, respectively).

example::

 $ py3path
 /home/scott/bin
 /opt/python-3.12.6/lib/python312.zip
 /opt/python-3.12.6/lib/python3.12
 /opt/python-3.12.6/lib/python3.12/lib-dynload
 /home/scott/.local/lib/python3.12/site-packages
 /opt/python-3.12.6/lib/python3.12/site-packages

..
