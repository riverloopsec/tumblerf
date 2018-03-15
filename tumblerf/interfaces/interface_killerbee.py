import killerbee

from .base import BaseInterface


class KillerBeeInterface(BaseInterface):
    def __init__(self, log_name="KillerBee Interface", generate_phy=False, generate_mac=True):
        BaseInterface.__init__(self, log_name=log_name, generate_phy=generate_phy, generate_mac=generate_mac)

        self.name = "802.15.4 KillerBee Interface"
        self.__devstring = None

        self.channel = 11
        self.freq = 2405e6

        self.preamble = '\x00\x00\x00\x00'
        self.sfd = '\xA7'

        self.driver = None
        self.set_channel(self.channel)
        self._running = False

    def set_device_string(self, device_string):
        """
        Set which interface should be used, which can be seen from the first column of running `sudo zbid`.
        :param device_string:
        """
        self.__devstring = device_string

    def __repr__(self):
        if self.driver is not None:
            dev_port, dev_type, _ = self.driver.get_dev_info()
            return "{}({} on {})".format(self.name, dev_type, dev_port)
        else:
            return "{}(Not Available)".format(self.name)

    @property
    def unique_id(self):
        return '/'.join(self.driver.get_dev_info()) if self.driver is not None else "NotAvailable"

    def add_subparser(self, subparsers):
        parser = subparsers.add_parser(self.__class__.__name__, help='Argument parser for interface')
        parser.add_argument('-i', '--tx_iface_device', action='store', default=None)
        return self.make_simple_help(parser)

    def process_cli(self, parser, argv):
        argv.insert(0, self.__class__.__name__)  # We add this as a convention to get the data to the right subparser.
        args, _ = parser.parse_known_args(argv)  # We may have options in argv meant for other tools, so we allow ignoring.
        self.set_device_string(args.tx_iface_device)

    def open(self):
        if not self._running:
            try:
                self.driver = killerbee.KillerBee(device=self.__devstring)
                # NOTE: The sniffer_on() in rx_start() sets autocrc off and promiscus on for ApiMote.
            except:
                self.logger.error("Error when starting, unable to open KillerBee interface.")
                return False
        if self.driver is None:
            self.logger.error("Error when initializing KillerBee interface.")
            return False
        self._running = True
        return self._running

    def close(self):
        if self._running:
            try:
                self.driver.close()
            except:
                self.logger.error("Error when exiting, unable to close KillerBee interface.")
                return False

        self._running = False
        return True

    def is_valid_channel(self, channel):
        if not channel:
            return False
        if (channel < 11) or (channel > 26):
            return False

        return True

    def set_channel(self, channel):
        if not self.is_valid_channel(channel):
            return NotImplementedError

        freq = (2400 + 5 * (channel - 10)) * 1e6

        if self._running:
            try:
                self.driver.set_channel(channel)
            except:
                self.logger.error("Unable to retune KillerBee!")
                return False

        self.channel = channel
        self.freq = freq

        return channel

    def get_channel(self):
        return self.channel

    def set_preamble(self, preamble):
        if not self.driver.check_capability(killerbee.KBCapabilities.SET_SYNC):
            self.logger.error("Usage: KillerBee interface does not support configuring the PHY Header.")
            return False

        self.preamble = preamble
        return True

    def get_preamble(self):
        return self.preamble

    def set_sfd(self, sfd):
        if not self.driver.check_capability(killerbee.KBCapabilities.SET_SYNC):
            self.logger.error("Usage: KillerBee interface does not support configuring the PHY Header.")
            return False

        self.sfd = sfd
        return True

    def get_sfd(self):
        return self.sfd

    def tx(self, packet, channel=None, count=1, delay=0):
        if not self._running:
            return False

        if not self.driver.check_capability(killerbee.KBCapabilities.INJECT):
            self.logger.error("Usage: KillerBee interface does not support injection.")
            return False

        if self.driver.check_capability(killerbee.KBCapabilities.SET_SYNC):
            # Corrupt sync to send arbitrary PHY header via packet in packet
            self.driver.set_sync(0xffff)

            padding = '\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff' # MAGIC 

            # Compose 802.15.4 PHY frame using software-configured header values
            frame = padding + preamble + sync + chr(len(packet) + 2) + packet + killerbee.makeFCS(packet)
            self.driver.inject(frame)
            self.driver.set_sync('\xa700')
        else:
            frame = packet + killerbee.makeFCS(packet)
            self.driver.inject(frame)

        return True

    def rx_start(self):
        self.driver.sniffer_on()
        return True

    def rx_stop(self):
        self.driver.sniffer_off()
        return True

    def rx_poll(self):
        pdict = self.driver.pnext()

        packet = None

        if pdict is not None:
            packet = pdict['bytes']

        return packet
