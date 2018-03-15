import pytest
import time
import os

from ..received_frame_check import ReceivedFrameHarness

from ...interfaces.base import BaseInterface
from ...generators.dot15d4_isotope_preamblelength import Dot15d4PreambleLengthGenerator

class MockRxInterface(BaseInterface):
    def __init__(self):
        BaseInterface.__init__(self, log_name="Mock Interface")
        self.__rx_on = False
        self.__open = False
        dot15d4_generator = Dot15d4PreambleLengthGenerator()
        for packet_bytes in dot15d4_generator.yield_control_case():
            self.__control_case = packet_bytes
        self.__test_cases = dot15d4_generator.get_test_cases(1, { 'preamb_len': 5 })
        self.__sending_control = True
        self.__packets_to_send_count = 0
        self.__test_cases_return_junk = False

    def open(self):
        self.__open = True
        return True

    def close(self):
        self.__open = False
        return True

    def rx_start(self):
        self.__rx_on = True
        return True

    def rx_stop(self):
        self.__rx_on = False
        return True

    def test_will_return_packet(self):
        """
        Returns a tuple of if a control case will be next returned by rx_query, as well as the packet
        which will next be returned. This is for test use only.
        If return junk test frames is on, this will still return what _should_ come back, not the junk frame that will.
        :return:
        """
        return (self.__sending_control, self.__control_case if self.__sending_control else self.__test_cases[0])

    def test_set_packets_to_produce(self, count):
        """
        In testing, we need to "let out" packets in a controlled fashion.
        :param count: How many additional packets to let come out of rx_query().
        """
        self.__packets_to_send_count += count

    def test_return_junk_test_frames(self, on):
        """
        For test use only, this allows us to tell the interface to start not yielding the planned frames.
        :param on: True to enable junk frames, False to disable and return to normal sequence.
        """
        self.__test_cases_return_junk = on

    def rx_poll(self):
        """
        Alternates between returning a control case and a test case packet.
        :return:
        """
        if self.__packets_to_send_count > 0:
            self.__packets_to_send_count -= 1
            if self.__sending_control:
                self.__sending_control = False
                return self.__control_case
            else:
                self.__sending_control = True
                if self.__test_cases_return_junk:
                    # Make a junk frame from overwriting the end of the control case with random.
                    return self.__control_case[:len(self.__control_case)/2] + os.urandom(len(self.__control_case)/2)
                elif len(self.__test_cases) > 0:
                    return self.__test_cases.pop(0)
                else:
                    return None
        else:
            return None


class TestReceivedFrameHarness(object):
    """
    This test mocks an interface for easy testing.
    """

    @pytest.fixture
    def if_harness(self, request):
        print("=== Setup ReceivedFrameHarness (for {})".format(request.function.__name__))
        interface = MockRxInterface()
        harness = ReceivedFrameHarness()
        harness.set_interface(interface)
        yield (interface, harness)
        print("=== Shutdown ReceivedFrameHarness (for {})".format(request.function.__name__))
        harness.do_reset()
        harness.close()

    @staticmethod
    def fill_harness(test_interface):
        expected_pkts = []
        for i in range(5):
            test_interface.test_set_packets_to_produce(1)
            next_is_control_case, expected_pkt = test_interface.test_will_return_packet()
            assert next_is_control_case is (i % 2 == 0)
            expected_pkts.append(expected_pkt)
            time.sleep(0.1)
        return expected_pkts

    def test_normal_state_control(self, if_harness):
        test_interface, rx_harness = if_harness
        next_is_control_case, next_packet_bytes = test_interface.test_will_return_packet()
        assert next_is_control_case is True
        rx_harness.set_expected_packet(next_packet_bytes)
        test_interface.test_set_packets_to_produce(1)
        assert rx_harness.is_valid()

    def test_normal_state_test(self, if_harness):
        test_interface, rx_harness = if_harness
        test_interface.test_set_packets_to_produce(1)
        time.sleep(1) # Let us eat up the control packet in the rx_harness thread
        next_is_control_case, next_packet_bytes = test_interface.test_will_return_packet()
        assert next_is_control_case is False
        rx_harness.set_expected_packet(next_packet_bytes)
        test_interface.test_set_packets_to_produce(1)
        assert rx_harness.is_valid()

    def test_normal_state_check_in_order(self, if_harness):
        test_interface, rx_harness = if_harness
        expected_pkts = self.fill_harness(test_interface)
        # Now the harnesses internal queue should have the 5 expected packets in order
        for i, expected_pkt in enumerate(expected_pkts):
            rx_harness.set_expected_packet(expected_pkt)
            assert rx_harness.is_valid()

    def test_invalid_state_1(self, if_harness):
        test_interface, rx_harness = if_harness
        test_interface.test_set_packets_to_produce(1)
        time.sleep(1)  # Let us eat up the control packet in the rx_harness thread
        test_interface.test_return_junk_test_frames(True) # turn on returning junk test frames
        next_is_control_case, next_packet_bytes = test_interface.test_will_return_packet()
        assert next_is_control_case is False
        rx_harness.set_expected_packet(next_packet_bytes)
        test_interface.test_set_packets_to_produce(1)
        assert not rx_harness.is_valid()
