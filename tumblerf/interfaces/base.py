import logging
import time

class BaseInterface():
    def __init__(self, log_name=None, generate_phy=False, generate_mac=False):
        self.driver = None
        self.name = "BaseInterface"

        self._generate_phy = generate_phy
        self._generate_mac = generate_mac

        self.logger = None
        if log_name:
            logging.basicConfig(level=logging.DEBUG)
            self.logger = logging.getLogger(time.ctime() + " " + log_name)
            self.logger.setLevel(logging.DEBUG)

        self.channel = None
        self.freq = None
        self.tx_gain = None

        self.preamble = None
        self.sfd = None

        self._running = False

    #def __del__(self):
    #    self.close()

    def __repr__(self):
        return self.name + ", Status=", + self._running

    @property
    def unique_id(self):
        """
        Provides a unique ID for the interface device, e.g. based on port or serial number, to allow for deconfliction.
        :return: str
        """
        raise NotImplementedError

    def add_subparser(self, subparsers):
        """
        Register additional arguments that the interface needs to get from a command line tool.
        Optional to implement, but if it is implemented it must follow the example behaviors closely.
        :param subparsers: Subparser object created by argparse's parser.add_subparsers call.
        """
        return None

    def process_cli(self, parser, argv):
        """
        Parses available options at the command line and uses them to update internal options.
        :param parser: argparse.ArgumentParser object
        :param argv: Array of command line options
        """
        #argv.insert(0, self.__class__.__name__)  # We add this as a convention to get the data to the right subparser.
        #args, _ = parser.parse_known_args(argv)  # We may have options in argv meant for other tools, so we allow ignoring.
        # TODO: In your interface, override this function and use args to set internal state.

    def open(self):
        """
        Opens/starts the interface
        """
        raise NotImplementedError

    def close(self):
        """
        Closes/terminates the interface
        """
        return NotImplementedError

    def log(self, msg):
        """
        Info-level debugging
        """
        if self.logger is not None:
            self.logger.info(msg)

    def status(self):
        """
        Prints some basic information about the interface; returns a Bool and dict reflecting said information
        """
        self.logger.info("Interface Name: {}".format(self.name))
        self.logger.info("        Driver: {}".format(self.driver))
        self.logger.info("        Status: {}".format(self._running))

        status_obj = {}
        status_obj['name'] = self.name
        status_obj['driver'] = repr(self.driver)
        status_obj['status'] = self._running
        status_obj['channel'] = self.channel
        status_obj['freq'] = self.freq
        status_obj['tx_gain'] = self.tx_gain

        return self._running, status_obj

    def is_valid_channel(self, channel):
        """
        Returns True if the specified channel is valid; else False
        """
        return NotImplementedError

    def set_channel(self, channel):
        """
        Calls into the driver to set the device's channel or frequency.
        The function this performs is determined by the driver.
        """
        return NotImplementedError

    def get_channel(self):
        """
        Returns the currently tuned channel or frequency.
        """
        return NotImplementedError

    def set_preamble(self, preamble):
        """
        Sets the preamble sequence used by the RF physical layer.
        """
        self.preamble = preamble
        return True

    def get_preamble(self):
        """
        Returns the currently set preamble sequence.
        """
        return self.preamble

    def set_sfd(self, sfd):
        """
        Sets the start of frame delimiter sequence used by the RF physical layer.
        """
        self.sfd = sfd
        return True

    def get_sfd(self):
        """
        Returns the currently set start of frame delimiter sequence.
        """
        return self.sfd

    def tx(self, packet, channel=None, count=1, delay=0):
        """
        Transmit the provided packet. Optional arguments allow setting the channel and re-sending the packet multiple times.
        """
        return NotImplementedError

    def rx_start(self):
        """
        Non-blocking call to enable the RF receiver.
        """
        return NotImplementedError

    def rx_stop(self):
        """
        Disable the RF receiver.
        """
        return NotImplementedError

    def rx_poll(self):
        """
        Non-blocking call to query for received packets.  Returns the next packet object if one is available, otherwise None.
        """
        return NotImplementedError

    def implements_rx(self):
        """
        Returns true if the subclass implements rx_poll(), thus indicating it can provide receive functionality.
        :return: bool
        """
        rx_poll_attr = getattr(self, "rx_poll", None)
        rx_poll_base = getattr(BaseInterface, "rx_poll", None)
        if callable(rx_poll_attr) and rx_poll_attr.__func__ != rx_poll_base.__func__:
            return True
        return False

    def make_simple_help(self, parser):
        message = parser.format_usage()
        message = message.split(self.__class__.__name__, 2)[1]
        return "\t{}:\t{}".format(self.__class__.__name__, message)
