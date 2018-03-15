from .base import BaseTestCaseGenerator
from .dot15d4_isotope_preamblelength import Dot15d4PreambleLengthGenerator
from scapy.layers.dot15d4 import Dot15d4FCS, Dot15d4Cmd
import struct

SFD = "\xa7"


class Dot15d4FranconianNotchGenerator(Dot15d4PreambleLengthGenerator, BaseTestCaseGenerator):
    def __init__(self):
        BaseTestCaseGenerator.__init__(self, includes_phy=True, includes_mac=True)
        self.__target_pan_id = 0xFFFF
        self.__target_short_addr = 0x0000
        self.__start_seqnum = 0

    # The following should be able to be provided by Dot15d4PreambleLengthGenerator:
    # set_target(self, pan_id, short_addr)
    # set_start_seqnum(self, value)
    def set_target(self, pan_id, short_addr):
        self.__target_pan_id = pan_id
        self.__target_short_addr = short_addr

    def set_start_seqnum(self, value):
        if value >= 0 and value <= 0xff:
            self.__start_seqnum = value
        else:
            raise ValueError("Sequence number must be between 0x00 and 0xFF.")

    def get_target_pan_id(self):
        return self.__target_pan_id

    # TODO: Debug and remove the above from this class as they should not need duplication.

    def yield_control_case(self, count=1):
        for case in self.yield_test_case(count, {
            'max_fill': 0  # we want 0 nibbles filled
        }):
            yield case

    def yield_test_case(self, count, constraints=None):
        """
        Is a Python generator which yields potential test cases to use.
        :param constraints: Dictionary of constraints to apply, which:
            Optionally have the key 'max_fill' set to an integer, indicating the maximum number of nibbles to turn to fill. Deafult=8.
            Optionally the key 'min_fill' to fix a minimum number of nibbles to turn to fill. Default=0.
            Optionally have the key 'fill_byte' to specify a byte (as a string) to fill with. Default="\xff"
        :yield: A byte array generated as a possible test case.
        """
        if constraints is None:
            max_fill = 8
            min_fill = 0
            fill_byte = "\xff"
        else:
            max_fill = constraints.get('max_fill', 8)
            if type(max_fill) is not int or max_fill > 8:
                raise ValueError("If provide a constraint with key 'preamb_len' set to an integer < 8.")
            min_fill = constraints.get('min_fill', 0)
            if type(min_fill) is not int:
                raise ValueError("If provide a constraint with key 'min_fill', it must be an integer.")
            fill_byte = constraints.get('fill_byte', "\xff")
            if type(fill_byte) is not str or len(fill_byte) != 1:
                raise ValueError("If provide a constraint with key 'fill_byte', it must be an single-byte string.")

        for i in range(count):
            for f_len in range(min_fill, max_fill+1):
                # Create a beacon request frame:
                pkt = Dot15d4FCS(seqnum=self.__start_seqnum, fcf_ackreq=True) / \
                      Dot15d4Cmd(dest_panid=self.__target_pan_id, dest_addr=self.__target_short_addr, cmd_id=7)
                self.__start_seqnum = (self.__start_seqnum + 1) % (0xFF + 1)
                # This will contain the FCS due to Dot15d4FCS:
                syncpkt = str(pkt)
                # As we are providing the PHY items, we add the SFD and length of the packet to the front:
                syncpkt = SFD + struct.pack('b', len(syncpkt)) + syncpkt
                #print("Beacon Request Formed: {}".format(syncpkt.encode('hex')))
                #Dot15d4FCS(syncpkt).show()

                if (f_len%2) != 0:
                    fb = ord(fill_byte)
                    fb = (((fb >> 4)) << 4)  # move symbol to high nibble so sent last, clear low
                    fb = struct.pack('B', fb)
                    preamble = ("\x00" * ((8 - f_len - 1) / 2)) + fb + (fill_byte * (f_len/2))
                else:
                    preamble = ("\x00" * ((8 - f_len) / 2)) + (fill_byte * (f_len/2))

                yield preamble+syncpkt

