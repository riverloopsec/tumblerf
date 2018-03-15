"""
Generators are where you implement the fuzzing technique that you want to try against a target.
Typically you must only implement the `yield_test_case` and `yield_control_case` functions
 (plus any initialization code you need) in your class.
"""

try:
    from dot15d4_payload_random import Dot15d4RandomPayloadGenerator
except ImportError as e:
    print("WARN: Unable to load Dot15d4RandomPayloadGenerator due to {}.".format(e))

try:
    from dot15d4_isotope_preamblelength import Dot15d4PreambleLengthGenerator
except ImportError as e:
    print("WARN: Unable to load Dot15d4PreambleLengthGenerator due to {}.".format(e))

try:
    from dot15d4_isotope_franconiannotch import Dot15d4FranconianNotchGenerator
except ImportError as e:
    print("WARN: Unable to load Dot15d4FranconianNotchGenerator due to {}.".format(e))
