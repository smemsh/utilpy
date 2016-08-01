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

import yaml
import sys
from pprint import pprint as pp


###

def usagex():
    print("{}:".format(invname), __doc__.strip())
    quit()

###

def main():

    invname = sys.argv.pop(0)
    args = sys.argv
    if not len(args) >= 1:
        usage(invname)

    for filename in args:
        try:
            with open(filename, "r") as f:
                contents = f.read()
            yamlstr = yaml.load(contents)
            pp(yamlstr)

        except FileNotFoundError:
            print("{}: {}: nsfod"
                  .format(invname, filename))
            quit()

        except:
            print("{}: unhandled exception".format(invname))
            raise


if __name__ == "__main__":
    main()
