import serial
import threading
import time
from binascii import hexlify
from re import _pattern_type as RE_PATTERN_TYPE

from .base import BaseHarness

class SerialCheckHarness(BaseHarness):
    """
    This harness leverages an Arduino to interface with the target's serial console.
    Ensure that the voltage of the Arduino matches that of the target device!
    Assuming you are using the defaults in the `serial_monitor_arduino_sketch.ino` sketch included, wire to the target as follows:
    - Harness D2 -> Target TX
    - Harness D3 -> Target RX
    - Harness D5 -> Target Reset Pin (will be brought LOW to tell target to reset)
    - Harness D6 -> Target Signal Monitor Pin (connect to some pin that is LOW during abnormal operation, else HIGH)
    """
    def __init__(self, port, baud=115200):
        """
        Create the harness using an Arduino flashed with `arduino_sketch.ino` on the given port (at given baud rate),
        and prepare a thread which will start looking for input as soon as the regexs are set.
        :param port: Full path to the port with the Arduino, e.g. /dev/ttyUSB0 or /dev/tty.usbserial-A700eBXX (OSX)
            To see the list of available ports, you can use `python -m serial.tools.list_ports`.
        :param baud: Baud rate, as an integer, e.g. 115200 or 9600
        """
        BaseHarness.__init__(self)
        try:
            self.serial = serial.Serial(port, baudrate=baud, timeout=1)
        except serial.SerialException as e:
            raise ValueError("Error initializing serial port: {}".format(e))
        self.status_valid_regex = None
        self.status_invalid_regex = None
        self.last_seen_valid = None
        self.access_serial_event = threading.Event()
        self.processing_thread_shutdown = threading.Event()
        self.processing_thread = threading.Thread(target=self.__process_input_thread,
                                                  args=(self.processing_thread_shutdown,))

    def set_timeout(self, timeout_ms):
        self.serial.timeout = timeout_ms/1000.0  # serial expects timeout in seconds

    def close(self):
        self.processing_thread_shutdown.set()
        self.processing_thread.join()
        self.serial.close()

    def do_reset(self):
        """
        Reset the device to a clean state via reboot or other means. Returns True if succeeded, otherwise False.
        :return: boolean
        """
        self.serial.write(b'\x01')
        self.serial.flushOutput()
        print("Reset requested.")
        print(self.serial.read(255))
        print("Reset completed.")

    def set_is_valid_regex(self, regex):
        """
        Set the regex used to look in serial output to see if the state is valid.
        If both regexs are then set, start the input monitoring thread.
        :param regex: A Python compiled regex that will be searched against the process list on the target.
            Construct via "re.compile(pattern)" or similar.
        :return:
        """
        if not isinstance(regex, RE_PATTERN_TYPE):
            raise ValueError("Invalid type passed in for regex argument.")
        self.status_valid_regex = regex
        if self.__regexs_ready():
            self.processing_thread.start()

    def set_is_invalid_regex(self, regex):
        """
        Set the regex used to look in serial output to see if the state is _in_valid.
        If both regexs are then set, start the input monitoring thread.
        :param regex: A Python compiled regex that will be searched against the process list on the target.
            Construct via "re.compile(pattern)" or similar.
        :return:
        """
        if not isinstance(regex, RE_PATTERN_TYPE):
            raise ValueError("Invalid type passed in for regex argument.")
        self.status_invalid_regex = regex
        if self.__regexs_ready():
            self.processing_thread.start()

    def __regexs_ready(self):
        return self.status_valid_regex is not None and self.status_invalid_regex is not None

    def __process_input_thread(self, shutdown_event):
        print("Thread started up.")
        while not shutdown_event.wait(self.serial.timeout):
            if self.access_serial_event.isSet():
                print("Process input in thread skipping.")
            else:
                print("Process input in thread.")
                self.__process_input()
        print("Shutdown received in thread.")
        return

    def __process_input(self, verbose=False):
        """
        Note that this implementation expects EOL characters to be transmitted by the target.
        This processes all the waiting data and updates an internal state.
        :return:
        """
        if self.access_serial_event.isSet():
            print("WARN: Called process input when serial was already marked in use, failing.")
            return False
        try:
            self.access_serial_event.set()
            if verbose:
                print("Read start with {} bytes waiting".format(self.serial.in_waiting))
            data = self.serial.read(max(255, self.serial.in_waiting))
            #print("Read done, got:", type(data), data)
            self.access_serial_event.clear()
            data = data.split(b'\n')
            #print("Read done, got:", data)
            if verbose:
                print("Cleared serial event")
            for line in data:
                # Try to get text, skip the data if it isn't decodable as UTF-8
                try:
                    line = line.strip().decode("utf-8")
                except UnicodeDecodeError as e:
                    print("Issue decoding line ({}), skipping: {}".format(e, line))
                    continue
                # Skip lines that are harness output:
                if line.find("[HARNESS]") == 0:
                    if verbose:
                        print("Skip:", line)
                    continue
                # Evaluate to see if we have info from the target we want to act on:
                print("Processing:\t{}\t{}".format(hexlify(line.encode('utf-8'))[:8], line))
                if self.status_valid_regex.search(line) is not None:
                    self.last_seen_valid = True
                    if verbose:
                        print("State set: {}".format(self.last_seen_valid))
                elif self.status_invalid_regex.search(line) is not None:
                    self.last_seen_valid = False
                    if verbose:
                        print("State set: {}".format(self.last_seen_valid))
        except serial.SerialException as e:
            print(e)
            self.access_serial_event.clear()
            return False

    def is_valid(self):
        """
        This function connects to the device via SSH and checks to see if the expected process is running.
        :return: boolean or None
        """
        if not self.__regexs_ready():
            raise ValueError("Must call set_is_valid_regex() and set_is_invalid_regex() on harness.")
        self.__process_input()
        # TODO: Consider what to return as state if last message hasn't been seen for a while and is thus stale.
        return self.last_seen_valid

    def is_invalid(self):
        """
        In this simple harness, this is simply the inverse of is_valid() as the check is reliable.
        :return: boolean or None
        """
        is_valid = self.is_valid()
        return None if is_valid is None else not is_valid
