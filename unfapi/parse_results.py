#!/usr/bin/env python

# Copyright (C) 2018 Ryan Speers & Matt Knight
#
# This program is dual-licensed: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3, or
# under a commercial license from the copyright holders.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# LICENSE.md file for more details.

import argparse
import glob
import os.path
import json

__doc__ = """
Command line interface to analyze/view measurements.
Copyright (C) 2018 Ryan Speers & Matt Knight
"""


def files_from_arg(args_path):
    full_paths = [os.path.join(os.getcwd(), path) for path in args_path]
    files = set()
    for path in full_paths:
        if os.path.isfile(path):
            files.add(path)
        else:
            files |= set(glob.glob(path + '/*'))
    return files


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', nargs='+', help='Path of a file or a folder of result files.')
    args = parser.parse_args()

    data_set = {}
    for filename in files_from_arg(args.path):
        testname = os.path.basename(filename)
        print("Loading from {} as {}.".format(filename, testname))
        with open(filename, 'r') as fh:
            data_set[testname] = json.load(fh)

    for testname, data in data_set.iteritems():
        print("Test: {} (using {})".format(testname, data.get("generator").get("name")))
        sorted_results = sorted(data.get('results').iteritems(), key=lambda (k, v): (v, k))
        for casenum, case in sorted_results:
            count_valid = 0
            count_invalid = 0
            for result in case:
                if result.get("valid", False):
                    count_valid += 1
                else:
                    count_invalid += 1
            print("\tCase {}: {} valid, {} invalid\texample case: {}".format(
                casenum, count_valid, count_invalid, case[0].get('raw').get('test_case')
            ))

