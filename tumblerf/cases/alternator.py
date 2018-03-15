from time import sleep

from .base import BaseCase
from .result import TestResult, TestResultWrapper

"""
Implements a simple test setup which alternates between test cases and control cases.
Between each test case that it runs from the given generator, it runs a check of the harness
 to determine if the state is still valid, and uses this to note the state of the system.
"""


class AlternatorCase(BaseCase):

    def does_control_case_pass(self, tr):
        print("INFO: Running control case.")
        control_case = self.__generator.get_control_case()
        tr.add_raw_data("control_case", control_case.encode('hex'))
        self.__interface.tx(control_case)
        return self.__harness.is_valid()

    def throw_test_case(self, tc_str, tr):
        raise NotImplementedError

    def run_test(self, iterations=5):
        results = TestResultWrapper(self.interface, self.harness, self.generator)
        for iteration in range(iterations):
            case_num = 0
            for tc in self.generator.yield_test_case(1):
                tr = TestResult(case_num)
                while not self.does_control_case_pass(tr):
                    if self.harness.implements_reset():
                        print("WARN: Control case didn't pass, check device state.")
                    else:
                        print("WARN: Control case didn't pass, resetting device via harness.")
                        reset_result = self.harness.do_reset()
                        print("INFO: Reset succeeded = {}".format(reset_result))
                print("INFO: Running test case.")
                if self.throw_test_case(tc, tr):
                    print("INFO: Test case received packet: {}".format(tc.encode('hex')))
                    tr.set_valid(True)
                else:
                    print("INFO: Test case missed packet:   {}".format(tc.encode('hex')))
                    tr.set_valid(False)
                results.add_test_result(tr)
                case_num += 1
        results.set_end_now()
        return results


class AlternatorCaseRxFrame(AlternatorCase):
    """
    This is a variant that expects the Harness be of type ReceivedFrameHarness to function properly.
    """
    def does_control_case_pass(self, tr):
        print("INFO: Running control case.")
        control_case = self.generator.get_control_case()
        self.harness.set_expected_packet(control_case)
        tr.add_raw_data("control_case", control_case.encode('hex'))
        self.interface.tx(control_case)
        sleep(0.5) # TODO: Adjust down, set high to ensure packet RX to start.
        return self.harness.is_valid()

    def throw_test_case(self, tc_str, tr):
        print("INFO: Running test case: {}.".format(tc_str.encode('hex')))
        self.harness.set_expected_packet(tc_str)
        tr.add_raw_data("test_case", tc_str.encode('hex'))
        self.interface.tx(tc_str)
        sleep(0.5)  # TODO: Adjust down, set high to ensure packet RX to start.
        return self.harness.is_valid()
