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
from pprint import pprint
import inspect
import sys
import signal
import json

import interfaces
import generators
import harnesses

__doc__="""
Command line interface to drive fuzzing cases and measurements.
Copyright (C) 2018 Ryan Speers & Matt Knight
"""


def show_class_members(class_type):
    print("Available {}:".format(class_type.__name__))
    for name, obj in inspect.getmembers(class_type, inspect.isclass):
        print("\t{}".format(obj.__name__))

def validate_name(class_type, class_name):
    available_classes = map(lambda x: x[0], inspect.getmembers(class_type, inspect.isclass))
    return class_name in available_classes

def string_to_class(class_type, class_name):
    matched_class = filter(lambda x: x[0]==class_name, inspect.getmembers(class_type, inspect.isclass))[0]
    return matched_class[1]

def exit_handler(signal, frame):
    print("INFO: Exiting due to interrupt {}".format(signal))
    sys.exit(1)

def epilog_text():
    return "Additional arguments exist depending on the -I/-G/-H options selected."

if __name__ == '__main__':
    signal.signal(signal.SIGINT, exit_handler)
    parser = argparse.ArgumentParser(description=__doc__, add_help=False,
                                     epilog=epilog_text())
    parser.add_argument('-I', '--tx_iface', action='store', default=None)
    parser.add_argument('-G', '--gen', action='store', default=None)
    parser.add_argument('-H', '--harness', action='store', default=None)
    parser.add_argument('-c', '--channel', action='store', type=int, default=None)
    parser.add_argument('--iterations', action='store', type=int, default=1)
    parser.add_argument('-f', '--results_file', action='store', type=argparse.FileType('w'), default=sys.stdout)
    parser.add_argument('-h', '--help', action='store_true')
    args, argv = parser.parse_known_args()

    # We handle help manually for more flexibility.
    if args.help:
        parser.print_help()

    if args.tx_iface is None or not validate_name(interfaces, args.tx_iface):
        show_class_members(interfaces)
        sys.exit(-1)
    if args.gen is None or not validate_name(generators, args.gen):
        show_class_members(generators)
        sys.exit(-2)
    if args.harness is None or not validate_name(harnesses, args.harness):
        show_class_members(harnesses)
        sys.exit(-3)

    # NOTE: Subparsers are being used (poorly) to allow each class to process arguments that it wants to set
    #       internal state of themselves. Plugin classes can register CLI flags and handle the CLI if desired.
    subparsers = parser.add_subparsers(dest="subparser_name")

    tx_interface = string_to_class(interfaces, args.tx_iface)()
    if args.channel is not None:
        tx_interface.set_channel(args.channel)
    usage_interface = tx_interface.add_subparser(subparsers)
    if args.help:
        print(usage_interface)
    else:
        tx_interface.process_cli(parser, argv)
        tx_interface.open()
        print("INFO: Transmit Interface is {}".format(tx_interface))

    generator = string_to_class(generators, args.gen)()
    gen_usage = generator.add_subparser(subparsers)
    if args.help:
        print(gen_usage)
    else:
        generator.process_cli(parser, argv)
        print("INFO: Generator is {}".format(generator))

    harness = string_to_class(harnesses, args.harness)()
    usage_harness = harness.add_subparser(subparsers)
    if args.help:
        print(usage_harness)
    else:
        harness.process_cli(parser, argv)
        harness.open()
        print("INFO: Harness is {}".format(harness))

    # If we are doing help, we will quit without actually running the test:
    if args.help:
        sys.exit(0)

    # TODO: Expose the test cases available as command line flags to remove this hardcoding.
    from cases.alternator import AlternatorCaseRxFrame
    case = AlternatorCaseRxFrame(tx_interface, harness, generator)
    # /TODO

    try:
        results = case.run_test(args.iterations)
        json.dump(results.serializable(), args.results_file, indent=4)
    except Exception as e:
        # If we get an exception we want to shut things down nicely
        print("ERROR: Exception generated from running test, shutting down test: {}".format(e))
        # Uncomment the below for help debugging:
        #import traceback
        #traceback.print_exc(file=sys.stdout)
    finally:
        tx_interface.close()
        harness.close()
