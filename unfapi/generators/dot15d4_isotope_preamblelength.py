import bitstring
import struct
from scapy.layers.dot15d4 import Dot15d4FCS, Dot15d4Cmd

from .base import BaseTestCaseGenerator

SFD = "\xa7"


class Dot15d4PreambleLengthGenerator(BaseTestCaseGenerator):
    def __init__(self):
        BaseTestCaseGenerator.__init__(self, includes_phy=True, includes_mac=True)
        self.__target_pan_id = 0xFFFF
        self.__target_short_addr = 0x0000
        self.__start_seqnum = 0

    def set_target(self, pan_id, short_addr):
        self.__target_pan_id = pan_id
        self.__target_short_addr = short_addr

    def set_start_seqnum(self, value):
        if value >= 0 and value <= 0xff:
            self.__start_seqnum = value
        else:
            raise ValueError("Sequence number must be between 0x00 and 0xFF.")

    def add_subparser(self, subparsers):
        parser = subparsers.add_parser(self.__class__.__name__, help='Argument parser for generator')
        parser.add_argument('--max_preamb_len', action='store', type=int, default=10)
        parser.add_argument('--min_preamb_len', action='store', type=int, default=0)
        parser.add_argument('--start_seqnum', action='store', type=int, default=0)
        return self.make_simple_help(parser)

    def process_cli(self, parser, argv):
        argv.insert(0, self.__class__.__name__)  # We add this as a convention to get the data to the right subparser.
        args, _ = parser.parse_known_args(argv)  # We may have options in argv meant for other tools, so we allow ignoring.
        self.set_default_constraint('preamb_len', args.max_preamb_len)
        self.set_default_constraint('min_preamb_len', args.min_preamb_len)
        self.set_start_seqnum(args.start_seqnum)

    def yield_control_case(self, count=1):
        for case in self.yield_test_case(count, {
            'min_preamb_len': 8,  # nibbles
            'preamb_len': 9       # to only produce at 8
        }):
            yield case

    def yield_test_case(self, count, constraints=None):
        """
        Is a Python generator which yields potential test cases to use.
        :param constraints: Dictionary of constraints to apply, which must have the key preamb_len set to an integer.
            Optionally the key 'min_preamb_len' to fix a minimum length of the preamble.
        :yield: A byte array generated as a possible test case.
        """
        max_preamb_len = constraints.get('preamb_len') if constraints is not None else None
        if max_preamb_len is not None and type(max_preamb_len) is not int:
            raise ValueError("If provide a constraint with key 'preamb_len', it must be an integer.")
        elif max_preamb_len is None and self.get_default_constraint('preamb_len', int) is not None:
            max_preamb_len = self.get_default_constraint('preamb_len', int)
        if max_preamb_len is None:
            raise ValueError("Must provide constraints with key 'preamb_len' set to an integer.")

        min_preamb_len = constraints.get('min_preamb_len') if constraints is not None else None
        if min_preamb_len is not None and type(min_preamb_len) is not int:
            raise ValueError("If provide a constraint with key 'min_preamb_len', it must be an integer.")
        elif min_preamb_len is None and self.get_default_constraint('min_preamb_len', int) is not None:
            min_preamb_len = self.get_default_constraint('min_preamb_len', int)
        if min_preamb_len is None:
            min_preamb_len = 0 # default value

        for i in range(count):
            for preamb_len in range(min_preamb_len, max_preamb_len):
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
                if (preamb_len % 2) != 0:
                    pkt_bytes = ("\x00" * (preamb_len / 2)) + NibbleTools.insert_first_last(syncpkt, "\x0f")
                else:
                    pkt_bytes = ("\x00" * (preamb_len / 2)) + syncpkt
                yield pkt_bytes


class NibbleTools():
    @staticmethod
    def insert_first_last(s, i):
        #first nibble of i goes at beginning
        #last nibble of i goes at end
        b = bitstring.BitArray(bytes=s)

        #swap
        swapped = NibbleTools.nibble_swap(b)
        i = bitstring.BitArray(bytes=i)
        swapped.prepend(i[0:4])
        swapped.append(i[4:8])
        return NibbleTools.nibble_swap(swapped).tobytes()

    @staticmethod
    def nibble_swap(b):
        # assumes b is a bitstring
        l = len(b)
        for i in [n*8 for n in range(0,l/8)]:
            first = b[i:i+4]
            b[i:i+4] = b[i+4:i+8]
            b[i+4:i+8] = first
        return b
