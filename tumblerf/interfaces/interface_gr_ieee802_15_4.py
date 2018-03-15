import socket
from killerbee import makeFCS

from gr_ieee802_15_4.transceiver_OQPSK_headerless import transceiver_OQPSK_headerless
from .base import BaseInterface


class GR_IEEE802_15_4(BaseInterface):
    def __init__(self, log_name="gr-ieee802-15-4 Mutable SDR Injector", generate_phy=False, generate_mac=False):
        BaseInterface.__init__(self, log_name=log_name, generate_phy=generate_phy, generate_mac=generate_mac)

        self.name = "802.15.4 Mutable SDR Injector"

        self.tx_ip = '127.0.0.1'
        self.tx_port = 52001

        self.channel = 11
        self.freq = 2405e6
        self.tx_gain = 50

        self.preamble = '\x00\x00\x00\x00'
        self.sfd = '\xa7'

        self.driver = transceiver_OQPSK_headerless(freq=self.freq, tx_gain=self.tx_gain, tx_ip=self.tx_ip, tx_port=str(self.tx_port))

        self.tx_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.open()

    #def __del__(self):
    #   self.close()

    def __repr__(self):
        return "{}({}:{})".format(self.name, self.tx_ip, self.tx_port)

    @property
    def unique_id(self):
        return '/'.join([self.tx_ip, str(self.tx_port)])

    def open(self):
        if not self._running:
            try:
                self.driver.start()
            except:
                self.logger.error("Error when starting, unable to start 802.15.4 GNU Radio flowgraph.")
                return False

        self._running = True
        return self._running

    def close(self):
        if self._running:
            try:
                self.driver.stop()
            except:
                self.logger.error("Error when exiting, unable to stop 802.15.4 GNU Radio flowgraph.")
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

        #if self._running:
        try:
            self.driver.set_freq(freq)
        except:
            self.logger.error("Unable to retune SDR!")
            return False

        self.channel = channel
        self.freq = freq

        return channel

    def get_channel(self):
        return self.channel

    def set_preamble(self, preamble):
        self.preamble = preamble
        return True

    def get_preamble(self):
        return self.preamble

    def set_sfd(self, sfd):
        self.sfd = sfd
        return True

    def get_sfd(self):
        return self.sfd

    def tx(self, packet, channel=None, count=1, delay=0):
        if not self._running:
            return False

        frame = packet

        # Make PHY and MAC
        if self._generate_phy and self._generate_mac:
            # Compose 802.15.4 PHY frame using software-configured header values
            frame = self.preamble + self.sfd + chr(len(packet) + 2) + packet + makeFCS(packet)

        # Make MAC, but not PHY
        elif not self._generate_phy and self._generate_mac:
            # Packet input contains PHY header, but expects the MAC CRC to be populated here -- this function doesn't have enough state awareness to do that currently
            raise NotImplementedError

        # Make PHY, but not MAC
        elif self._generate_phy and not self._generate_mac:
            frame = self.preamble + self.sfd + chr(len(packet)) + packet  # No +2 to length because FCS is pre-populated

        # print frame.encode('hex')

        # Send frame to GNU Radio thread
        bsent = self.tx_socket.sendto(frame, (self.tx_ip, self.tx_port))

        return True if bsent else False
