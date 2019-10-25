#!/usr/bin/env python3
#
# yamldump
#   pretty prints yaml files as python objects
#
# args:
#   - any number of yaml files to print
#
# todo:
#   - optionally pre-pass through jinja2
#
# http://smemsh.net/src/utilsh/
# http://spdx.org/licenses/GPL-2.0
# scott@smemsh.net
#
##############################################################################
"""
parse and dump a yaml file
    args: filenames to dump"
"""

from sys import argv

from pprint import pprint as pp
import yaml

###

def usagex():
    print("{}:".format(invname), __doc__.strip())
    quit()

###

def main():

    if (nargs == 0):
        usagex()

    for filename in args:
        try:
            with open(filename, "r") as f:
                contents = f.read()
            yamlstr = yaml.safe_load(contents)
            pp(yamlstr)

        except FileNotFoundError:
            print("{}: {}: nsfod".format(invname, filename))
            quit()

        except:
            print("{}: unhandled exception".format(invname))
            raise

###

if (__name__ == "__main__"):

    invname = argv[0]
    args = argv[1:]
    nargs = len(args)

    main()
#
