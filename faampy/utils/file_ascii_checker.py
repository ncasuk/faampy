#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Checks a file for non-ASCII characters line by line. If non-ASCII charachters
are found the line number and the line content are printed to stdout.

"""

import sys

def contains_non_ascii(ifile):
    f = open(ifile, 'r')
    lines = f.readlines()
    f.close()

    result = []

    for i, line in enumerate(lines):
        asc = [ord(c) for c in line]
    if ((min(asc) >= 0) and (max(asc) <= 127)):
        pass
    else:
        result.append((i, line))
    return result


def _argparser():
    import argparse
    sys.argv.insert(0, 'faampy ascii_file_checker')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input_file', action="store", type=str,
                        help='File that is checked for non-ascii characters')
    return parser


def main():
    parser = _argparser()
    args = parser.parse_args()
    check = contains_non_ascii(args.input_file)
    if check:
        for c in check:
            sys.stdout.write('File contains non-ASCII characters\n')
            sys.stdout.write('line %i: %s' % c)
    else:
        sys.stdout.write('File contains only ASCII characters ...\n')


if __name__ == '__main__':
    main()
