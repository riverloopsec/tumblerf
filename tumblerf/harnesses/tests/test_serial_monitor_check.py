import pytest
import re
import time

from ..serial_monitor_check import SerialCheckHarness

class TestSerialMonitorHarness(object):
    """
    This test requires a flashed Arduino to be plugged in and running the `test_arduino_sketch.ino` ("Target") code,
    in addition to the typical Arduino harness device running `serial_monitor_arduino_sketch.ino` ("Harness") code.

    The wiring between them should be as follows:
    - Harness D2 -> Target TX (D1)
    - Harness D3 -> Target RX (D0)
    - Harness D5 -> Target D5 ("soft reset" pin used to tell target to reset)
    - Harness D6 -> Target D6 ("signal" pin used to see if target is in a valid state or not)
    - Harness D7 -> Target D7 ("switch" pin used to trigger invalid in the test suite)

    The below serial_port variable MUST be set correctly to the device running the harness sketch.
    """
    serial_port = "/dev/tty.usbserial-A700eBUj"

    @pytest.fixture
    def serial_harness(self, request):
        print("=== Setup SerialCheckHarness (for {})".format(request.function.__name__))
        try:
            harness = SerialCheckHarness(self.serial_port, 115200)
        except ValueError as e:
            print("WARN: Skipping test as unable to initialize SerialCheckHarness: {}".format(e))
            pytest.skip()
            return
        harness.set_timeout(5000)
        time.sleep(1)  # appears to need a moment to get started
        yield harness
        print("=== Shutdown SerialCheckHarness (for {})".format(request.function.__name__))
        harness.do_reset()
        harness.close()

    def __cause_test_fault(self, serial_harness):
        # Now we trigger it to a bad state by sending a serial command, which
        # is recognized by the harness and it pulls a pin low to tell the test Arduino target to "fault".
        serial_harness.serial.write(b'\x02')  # TEST_SWITCH_CMD
        time.sleep(2)

    def Xtest_stable_prefixmatch(self, serial_harness):
        #TODO: With the Arduino harness, we are getting a 0x02 byte prefixed at start of line sometimes, meaning this
        # is unable to match. Disabling for now.
        serial_harness.set_is_valid_regex(re.compile(r"^\[INFO\]"))
        serial_harness.set_is_invalid_regex(re.compile(r"^\[WARN\]"))
        assert serial_harness.is_valid()

    def test_stable_snippetmatch(self, serial_harness):
        serial_harness.set_is_valid_regex(re.compile(r"normal operation"))
        serial_harness.set_is_invalid_regex(re.compile(r"Failure"))
        time.sleep(2)
        assert serial_harness.is_valid()

    def test_trigger_failure(self, serial_harness):
        serial_harness.set_is_valid_regex(re.compile(r"normal operation"))
        serial_harness.set_is_invalid_regex(re.compile(r"Failure|\[ERROR\]"))
        assert serial_harness.is_valid()
        self.__cause_test_fault(serial_harness)
        assert serial_harness.is_invalid()

    def test_trigger_reset(self, serial_harness):
        serial_harness.set_is_valid_regex(re.compile(r"normal operation"))
        serial_harness.set_is_invalid_regex(re.compile(r"Failure|\[ERROR\]"))
        assert serial_harness.is_valid()
        self.__cause_test_fault(serial_harness)
        assert serial_harness.is_invalid()
        serial_harness.do_reset()
        time.sleep(2)
        assert serial_harness.is_valid()
