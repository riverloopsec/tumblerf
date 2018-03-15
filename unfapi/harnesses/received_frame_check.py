import threading
from collections import deque

from .base import BaseHarness
# TODO: Clean up this import:
try:
    from ..interfaces.base import BaseInterface
except ValueError:
    from interfaces.base import BaseInterface

# TODO: Make it more flexible as to what the RX interface type could be:
try:
    from ..interfaces.interface_killerbee import KillerBeeInterface
except ValueError:
    from interfaces.interface_killerbee import KillerBeeInterface


class ReceivedFrameHarness(BaseHarness):
    """
    This harness listens on an RF interface for frames to indicate if the expected frames are being received
    or not by the radio.
    """
    def __init__(self):
        BaseHarness.__init__(self)
        self.__interface = None
        self.__expectation = None
        self.__pending_packets = deque()
        self.access_interface_event = threading.Event()
        self.processing_thread_shutdown = threading.Event()
        self.processing_thread = threading.Thread(target=self.__process_input_thread,
                                                  args=(self.processing_thread_shutdown,))

    def open(self):
        if not self.__interface.rx_start():
            return False
        self.processing_thread.start()

    def close(self):
        self.__interface.rx_stop()
        self.processing_thread_shutdown.set()
        self.processing_thread.join()

    def set_interface(self, interface):
        """
        Set the interface that will be used to receive information.
        If validation checks on the given interface fail, a ValueError is thrown.
        Once setup, it will start the input processing thread.
        :param interface: An object implementing the BaseInterface class.
        :return: bool
        """
        if not isinstance(interface, BaseInterface):
            raise ValueError("Interface given was of type {}.".format(type(interface)))
        if not interface.implements_rx():
            raise ValueError("Interface given ({}) does not implement receive.".format(interface))
        self.__interface = interface
        if not self.__interface.open():
            return False
        return True

    def add_subparser(self, subparsers):
        parser = subparsers.add_parser(self.__class__.__name__, help='Argument parser for interface')
        parser.add_argument('--rx_iface_device', action='store', default=None)
        return self.make_simple_help(parser)

    def process_cli(self, parser, argv):
        argv.insert(0, self.__class__.__name__)  # We add this as a convention to get the data to the right subparser.
        args, _ = parser.parse_known_args(argv)  # We may have options in argv meant for other tools, so we allow ignoring.
        rx_interface = KillerBeeInterface()
        rx_interface.set_device_string(args.rx_iface_device)
        if args.channel is not None:
            rx_interface.set_channel(args.channel)
        # TODO: Restore this check
        #if rx_interface.unique_id == tx_interface.unique_id:
        #    raise Exception("ERROR: Must have a different interface for the receive handler than for TX.")
        if not self.set_interface(rx_interface):
            raise Exception("ERROR: Can't set interface for the harness.")
        print("INFO: For receive, we will use {}".format(rx_interface))

    def do_reset(self):
        # During the reset we lock the thread to keep it from trying to read.
        self.access_interface_event.set()
        self.__interface.rx_stop()
        if self.__interface.close():
            if self.__interface.open():
                self.__interface.rx_start()
                self.access_interface_event.clear()
                return True
        return False

    def set_expected_packet(self, packet):
        print("Setting expected packet to:\t{}".format(packet.encode('hex')))
        self.__expectation = packet

    def __process_input_thread(self, shutdown_event):
        print("Thread started up.")
        while not shutdown_event.wait(self.timeout / 1000.0): # wait() takes time in seconds, this defaults to 0.05 secs
            if self.access_interface_event.isSet():
                print("Process input in thread skipping.")
            else:
                self.__process_input()
        print("Shutdown received in thread.")
        return

    def __process_input(self, verbose=False):
        """
        This processes all the waiting packets and updates an internal state list.
        :return: bool
        """
        if self.access_interface_event.isSet():
            if verbose:
                print("WARN: Called process input when RF interface was already marked in use, failing.")
            return False
        try:
            self.access_interface_event.set()
            if verbose:
                print("Set interface access event")
            pkt = self.__interface.rx_poll()
            if pkt is not None:  # TODO add "verbose and" check
                print("Got packet: {}".format(pkt.encode('hex')))
            while pkt is not None:
                self.__pending_packets.append(pkt)
                pkt = self.__interface.rx_poll()
                if pkt is not None:
                    print("Loop got packet: {}".format(pkt.encode('hex') if pkt is not None else None))
            # print("Read done, got:", type(data), data)
            self.access_interface_event.clear()
            # print("Read done, got:", data)
            if verbose:
                print("Cleared interface access event")
            return True
        except Exception as e:
            print("ERROR: Processing input: {}".format(e))
            self.access_interface_event.clear()
            return False

    def is_valid(self):
        """
        This function returns True if a matched packet was received.
        :return: boolean or None
        """
        if self.__expectation is None:
            raise ValueError("Must call set_expected_packet() on harness.")
        self.__process_input() # make sure we're fully up-to-date reading packets
        try:
            while True:
                pkt = self.__pending_packets.popleft()
                if pkt in self.__expectation:  # Substring check to get around presence of PHY
                    # We return when we find a match, leaving other pending packets in the queue for future use
                    return True
                #else:
                #    print("DEBUG: Compared to:\t\t{}".format(pkt.encode('hex')))
        except IndexError:
            # This tells us that the __pending_packets dequeue is empty so we have no more packets to process.
            pass
        return False

    def is_invalid(self):
        """
        In this simple harness, this is simply the inverse of is_valid() as the check is reliable.
        :return: boolean or None
        """
        is_valid = self.is_valid()
        return None if is_valid is None else not is_valid
